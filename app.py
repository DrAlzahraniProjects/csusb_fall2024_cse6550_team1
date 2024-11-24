import streamlit as st
from uuid import uuid4
# import time
import os
import subprocess
from RAG import initialize_milvus, query_rag
from collections import defaultdict
import pandas as pd
from chatbot_statistics import DatabaseClient  # Import the DatabaseClient class
from ddos_protection import handle_rate_limiting  # Importing the rate-limiting function


def initialize_vector_store():
    if not hasattr(st.session_state, "vector_store_initialized"):
        initialize_milvus()
        st.session_state.vector_store_initialized = True


class StreamlitApp:

    def __init__(self, session_state=st.session_state):
        self.db_client = DatabaseClient()
        if "app_initialized" not in st.session_state:
            st.session_state.app_initialized = False
        if not st.session_state.app_initialized:
            with st.spinner("Initializing ITS Support Chatbot: May take up to 2 minutes..."):
                if 'user_requests' not in st.session_state:
                    st.session_state.user_requests = defaultdict(list)
                    st.session_state.current_user = None
                if 'lockout_time' not in st.session_state:
                    st.session_state.lockout_time = defaultdict(lambda: 0)
                if "messages" not in session_state:
                    self.db_client.create_performance_metrics_table()
                    self.db_client.insert_default_performance_metrics()
                    initialize_vector_store()
                    st.session_state.messages = {}
                    st.session_state.app_initialized = True
        # Answerable and Unanswerable questions
        self.answerable_questions = {
            "How can I contact ITS",
            "How can I connect to the campus WiFi",
            "What are the available free software for a student",
            "Where are all the printers located",
            "What are the CoyoteLabs virtual computer labs",
            "Is Adobe Creative Cloud available as student software",
            "What is information security awareness",
            "How do I enable multi-factor authentication",
            "What are Coyote OneCard benefits",
            "What if i lost my campus laptop charger",
        }
        self.answerable_questions = {q.lower() for q in self.answerable_questions}
        self.unanswerable_questions = {
            "What are the campus gym timings",
            "What is a smart contract",
            "Can you write code for a basic Python script",
            "What is the CGI phone number or email",
            "What class does Dr. Alzahrani teach",
            "Who is Hironori Washizaki",
            "How can I make a payment for the tuition fee",
            "What is the future impact of AI on software quality standards",
            "What is regression testing",
            "How much does parking cost for one semester",
        }
        self.unanswerable_questions = {q.lower() for q in self.unanswerable_questions}

    @staticmethod
    def remove_special_characters(input_string):
        special_characters = "?!@#$%^&*()-_=+[]{}\\|;:'\",<>/`~"
        return input_string.translate(str.maketrans("", "", special_characters)).lower().strip()


    @staticmethod
    def load_css(file_name):
        """
        Load a CSS file to style the app.

        Args:
            file_name (str): css file path
        """
        try:
            with open(file_name) as f:
                st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
        except FileNotFoundError:
            st.error(f"css file '{file_name}' not found.")

    @staticmethod
    def color_cells(val):
        """
        Apply background and text color based on cell content.

        Args:
            val (str): The value in the cell.

        Returns:
            dict: A dictionary of CSS properties to style the cell.
        """
        if "TP" in val and val[0] != '0' or "TN" in val and val[0] != '0':
            return {
                "background-color": "#90f7aa",  # Light green for correct predictions
                "color": "#013b0f"  # Dark green text
            }
        elif "FP" in val and val[0] != '0' or "FN" in val and val[0] != '0':
            return {
                "background-color": "#fbc5ca",  # Light red for incorrect predictions
                "color": "#4b0007"  # Dark red text
            }
        return {
            "background-color": "transparent",  # Default white background
            "color": "#000000"  # Default black text
        }

    def display_performance_metrics(self):
        """
        Display performance metrics in the sidebar.
        """
        st.sidebar.markdown(
            """
            <h1 style="font-size:24px; margin:0; text-decoration:none;">
                <a href="https://github.com/DrAlzahraniProjects/csusb_fall2024_cse6550_team1/wiki/SQA-Questions#answerable-vs-unanswerable-questions" style="text-decoration:none; color:inherit;">Confusion Matrix</a>
            </h1>
            """,
            unsafe_allow_html=True
        )
        important_metrics = [
            ("Sensitivity", "sensitivity"),
            ("Specificity", "specificity"),
        ]
        result = self.db_client.get_performance_metrics()
        imp_container = st.sidebar.empty()
        with imp_container.container():
            for metric_name, metric in important_metrics:
                st.markdown(f"<div class='important-metrics'>{metric_name}: {result[metric]}</div>", unsafe_allow_html=True)
        st.sidebar.write("")
        # table for confusion matrix
        data = {
            'Actual +': {
                'Predicted +': f"{result['true_positive']} (TP)",
                'Predicted -': f"{result['false_negative']} (FN)"
            },
            'Actual -': {
                'Predicted +': f"{result['false_positive']} (FP)",
                'Predicted -': f"{result['true_negative']} (TN)"
            },
        }
        # Transpose the DataFrame
        df = pd.DataFrame(data).transpose()

        # Apply color styling to the DataFrame
        styled_df = df.style.map(lambda x: ";".join(f"{k}:{v}" for k, v in self.color_cells(x).items()))

        # Render the styled DataFrame with the custom CSS
        st.sidebar.write(styled_df.to_html(), unsafe_allow_html=True)

        # Normal metrics
        performance_metrics = [
            ("Accuracy", "accuracy"),
            ("Precision", "precision"),
            ("F1 Score", "f1_score")
        ]
        normal_container = st.sidebar.empty()
        with normal_container.container():
            for metric_name, metric in performance_metrics:
                st.markdown(f"<div class='normal-metrics'>{metric_name}: {result[metric]}</div>", unsafe_allow_html=True)
        # Reset Button
        if st.sidebar.button("Reset"):
            self.db_client.reset_performance_metrics()
            # st.rerun()

    def handle_feedback(self, assistant_message_id):
        """
        Handle feedback for a message.

        Args:
            assistant_message_id (str): The unique ID of the message
        """
        previous_feedback = st.session_state.messages[assistant_message_id].get("feedback", None)
        feedback = st.session_state.get(f"feedback_{assistant_message_id}", None)
        user_message_id = assistant_message_id.replace("assistant_message", "user_message", 1)
        question = st.session_state.messages[user_message_id]["content"]
        plain_question = self.remove_special_characters(question)

        if plain_question in self.answerable_questions:
            if feedback == 1:
                if previous_feedback is None:
                    self.db_client.increment_performance_metric("true_positive")
                elif previous_feedback == "dislike":
                    self.db_client.increment_performance_metric("false_negative", -1)
                    self.db_client.increment_performance_metric("true_positive")
                st.session_state.messages[assistant_message_id]["feedback"] = "like"
            elif feedback == 0:
                if previous_feedback is None:
                    self.db_client.increment_performance_metric("false_negative")
                elif previous_feedback == "like":
                    self.db_client.increment_performance_metric("true_positive", -1)
                    self.db_client.increment_performance_metric("false_negative")
                st.session_state.messages[assistant_message_id]["feedback"] = "dislike"
            else:
                if previous_feedback == "like":
                    self.db_client.increment_performance_metric("true_positive", -1)
                elif previous_feedback == "dislike":
                    self.db_client.increment_performance_metric("false_negative", -1)
                st.session_state.messages[assistant_message_id]["feedback"] = None
        elif plain_question in self.unanswerable_questions:
            if feedback == 1:
                if previous_feedback is None:
                    self.db_client.increment_performance_metric("true_negative")
                elif previous_feedback == "dislike":
                    self.db_client.increment_performance_metric("false_positive", -1)
                    self.db_client.increment_performance_metric("true_negative")
                st.session_state.messages[assistant_message_id]["feedback"] = "like"
            elif feedback == 0:
                if previous_feedback is None:
                    self.db_client.increment_performance_metric("false_positive")
                elif previous_feedback == "like":
                    self.db_client.increment_performance_metric("true_negative", -1)
                    self.db_client.increment_performance_metric("false_positive")
                st.session_state.messages[assistant_message_id]["feedback"] = "dislike"
            else:
                if previous_feedback == "like":
                    self.db_client.increment_performance_metric("true_negative", -1)
                elif previous_feedback == "dislike":
                    self.db_client.increment_performance_metric("false_positive", -1)
                st.session_state.messages[assistant_message_id]["feedback"] = None
                
        self.db_client.update_performance_metrics()

    def display_all_messages(self):
        for message_id, message in st.session_state.messages.items():
            if message["role"] == "assistant":
                st.markdown(f"""
                    <div class='assistant-message'>
                        {message['content']}
                    </div>
                """, unsafe_allow_html=True)

                # Feedback Buttons
                st.feedback(
                    "thumbs",
                    key=f"feedback_{message_id}",
                    on_change=self.handle_feedback(message_id),
                )
            else:
                st.markdown(f"<div class='user-message'>{message['content']}</div>", unsafe_allow_html=True)

    @staticmethod
    def run_query(prompt=None, user_message_id=None, assistant_message_id=None):
        """
        Run a query and generate a response.

        Args:
            prompt (str): The user query.

        Returns:
            str: The response to the user query.
        """
        # Generate a response based on the user query
        if user_message_id is None:
            user_message_id = st.session_state.get("QUERY_RUNNING")
        if prompt is None:
            prompt = st.session_state.messages[user_message_id]["content"]
        response_placeholder = st.empty()
        with response_placeholder.container():
            with st.spinner('Generating Response...'):
                # answer, source = None, None
                # if not st.session_state.get("QUERY_RUNNING", None):
                if len(st.session_state.messages) > 1:
                    st.session_state["QUERY_RUNNING"] = user_message_id
                answer, source = query_rag(prompt)

            if source is None:
                st.error(f"{answer}")
                return False
            else:
                if assistant_message_id is None:
                    assistant_message_id = user_message_id.replace("user_message", "assistant_message", 1)
                st.session_state.messages[assistant_message_id] = {"role": "assistant", "content": answer, "source": source}
                if "QUERY_RUNNING" in st.session_state:
                    del st.session_state["QUERY_RUNNING"]
        return True
    
    def main(self):
        """
        Main function to run the app
        """
        
        header = st.container()
        header.write("""<div class='chat-title'>ITS Support Chatbot</div>""", unsafe_allow_html=True)
        header.write("""<div class='fixed-header'/>""", unsafe_allow_html=True)

        # Load the CSS file
        self.load_css("assets/style.css")
                
        # Render existing messages
        self.display_all_messages()
        
        # displays the performance metrics in the sidebar   
        self.display_performance_metrics()

        # Handle user input
        if prompt := st.chat_input("Ask ITS support chatbot"):
            is_server_free = handle_rate_limiting()
            if not is_server_free:
                st.error("You've reached the limit of 10 questions per minute because the server has limited resources. Please try again in 3 minutes.")
                st.stop()  # Stop further processing of the app
            # creating user_message_id and assistant_message_id with the same unique "id" because they are related
            unique_id = str(uuid4())
            user_message_id = f"user_message_{unique_id}"
            assistant_message_id = f"assistant_message_{unique_id}"

            # save the user message in the session state
            st.session_state.messages[user_message_id] = {"role": "user", "content": prompt}
            st.markdown(f"<div class='user-message'>{prompt}</div>", unsafe_allow_html=True)
            response = self.run_query(prompt=prompt, user_message_id=user_message_id, assistant_message_id=assistant_message_id)
            if response:
                st.rerun()
            else:
                st.stop()  # Stop further processing of the app
            
        # Handle the case where the query is still running but interrupted due to feedback buttons
        if st.session_state.get("QUERY_RUNNING", None):
            user_message_id = st.session_state.get("QUERY_RUNNING")
            response = self.run_query(user_message_id=user_message_id)
            if response:
                st.rerun()
            else:
                st.stop()  # Stop further processing of the app


if __name__ == "__main__":
    # If streamlit instance is running
    if os.environ.get("STREAMLIT_RUNNING") != "1":
        os.environ["STREAMLIT_RUNNING"] = "1"
        with open('/app/logs/app.log', 'w') as file:
            file.write('')
        subprocess.Popen(["streamlit", "run", __file__, "--server.port=5001", "--server.address=0.0.0.0", "--server.baseUrlPath=/team1"])
        subprocess.run(["jupyter", "notebook", "--ip=0.0.0.0", "--port=6001", "--no-browser", "--allow-root", "--NotebookApp.base_url=/team1/jupyter"])
    else:
        app = StreamlitApp(st.session_state)
        app.main()
