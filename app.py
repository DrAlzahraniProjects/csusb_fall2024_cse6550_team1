import streamlit as st
from uuid import uuid4
import os
import subprocess
from RAG import initialize_milvus, query_rag
import pandas as pd
from chatbot_statistics import DatabaseClient  # Import the DatabaseClient class
from ddos_protection import handle_rate_limiting  # Importing the rate-limiting function

db_client = DatabaseClient()

# Answerable and Unanswerable questions
answerable_questions = {
        "How can I contact ITS?",
        "How can I connect to the campus Wi-Fi?",
        "Who are the Co-Chairs for the 2024/2025 Committee?",
        "Where are all the printers located?",
        "What are the CoyoteLabs virtual computer labs?",
        "Is Adobe Creative Cloud available as student software?",
        "Does CSUSB have accessible technology?",
        "How do I enable multi-factor authentication?",
        "What are Coyote OneCard benefits?",
        "Why can't I get access for wireless prints through my phone?",
    }
answerable_questions = {q.lower() for q in answerable_questions}
unanswerable_questions = {
        "How do I connect to Starbucks Wi-Fi?",
        "What is a smart contract?",
        "Can you write code for a basic Python script?",
        "Who is the dean of CSUSB?",
        "What class does Dr. Alzahrani teach?",
        "Who is Hironori Washizaki?",
        "When was CSUSB built?",
        "What is the future impact of AI on software quality standards?",
        "What is regression testing?",
        "Can a student apply for a part-time job in IT support? If so, what is the process?",
    }
unanswerable_questions = {q.lower() for q in unanswerable_questions}

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


def display_performance_metrics():
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
    result = db_client.get_performance_metrics()
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
    styled_df = df.style.map(lambda x: ";".join(f"{k}:{v}" for k, v in color_cells(x).items()))

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
        db_client.reset_performance_metrics()
        st.rerun()


def handle_feedback(assistant_message_id):
    """
    Handle feedback for a message.

    Args:
        id (str): The unique ID of the message
    """
    previous_feedback = st.session_state.messages[assistant_message_id].get("feedback", None)
    feedback = st.session_state.get(f"feedback_{assistant_message_id}", None)
    user_message_id = assistant_message_id.replace("assistant_message", "user_message", 1)
    question = st.session_state.messages[user_message_id]["content"]

    if question.lower().strip() in answerable_questions:
        if feedback == 1:
            if previous_feedback == None:
                db_client.increment_performance_metric("true_positive")
            elif previous_feedback == "dislike":
                db_client.increment_performance_metric("false_negative", -1)
                db_client.increment_performance_metric("true_positive")
            st.session_state.messages[assistant_message_id]["feedback"] = "like"
        elif feedback == 0:
            if previous_feedback == None:
                db_client.increment_performance_metric("false_negative")
            elif previous_feedback == "like":
                db_client.increment_performance_metric("true_positive", -1)
                db_client.increment_performance_metric("false_negative")
            st.session_state.messages[assistant_message_id]["feedback"] = "dislike"
        else:
            if previous_feedback == "like":
                db_client.increment_performance_metric("true_positive", -1)
            elif previous_feedback == "dislike":
                db_client.increment_performance_metric("false_negative", -1)
            st.session_state.messages[assistant_message_id]["feedback"] = None
    elif question.lower().strip() in unanswerable_questions:
        if feedback == 1:
            if previous_feedback == None:
                db_client.increment_performance_metric("true_negative")
            elif previous_feedback == "dislike":
                db_client.increment_performance_metric("false_positive", -1)
                db_client.increment_performance_metric("true_negative")
            st.session_state.messages[assistant_message_id]["feedback"] = "like"
        elif feedback == 0:
            if previous_feedback == None:
                db_client.increment_performance_metric("false_positive")
            elif previous_feedback == "like":
                db_client.increment_performance_metric("true_negative", -1)
                db_client.increment_performance_metric("false_positive")
            st.session_state.messages[assistant_message_id]["feedback"] = "dislike"
        else:
            if previous_feedback == "like":
                db_client.increment_performance_metric("true_negative", -1)
            elif previous_feedback == "dislike":
                db_client.increment_performance_metric("false_positive", -1)
            st.session_state.messages[assistant_message_id]["feedback"] = None
            
    db_client.update_performance_metrics()


def main():
    """
    Main function to run the app
    """
    header = st.container()
    header.write("""<div class='chat-title'>ITS Support Chatbot</div>""", unsafe_allow_html=True)
    header.write("""<div class='fixed-header'/>""", unsafe_allow_html=True)

    # Load the CSS file
    load_css("assets/style.css")
    
    if "messages" not in st.session_state:
        st.session_state.messages = {}
        with st.spinner("Initializing, Please Wait..."):
            db_client.create_performance_metrics_table()
            db_client.insert_default_performance_metrics()
            vector_store = initialize_milvus()
            
    # Render existing messages
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
                key = f"feedback_{message_id}",
                on_change = handle_feedback(message_id),
            )
        else:
            st.markdown(f"<div class='user-message'>{message['content']}</div>", unsafe_allow_html=True)
    
    # displays the performance metrics in the sidebar   
    display_performance_metrics()
    
    # Handle user input
    if prompt := st.chat_input("Ask ITS support chatbot"):
        
        # creating user_message_id and assistant_message_id with the same unique "id" because they are related
        unique_id = str(uuid4())
        user_message_id = f"user_message_{unique_id}"
        assistant_message_id = f"assistant_message_{unique_id}"

        # save the user message in the session state
        st.session_state.messages[user_message_id] = {"role": "user", "content": prompt}
        st.markdown(f"<div class='user-message'>{prompt}</div>", unsafe_allow_html=True)
        handle_rate_limiting()
        response_placeholder = st.empty()
        with response_placeholder.container():
            with st.spinner('Generating Response...'):
                # generate response from RAG model
                answer, source = None, None
                if not st.session_state.get("QUERY_RUNNING", None):
                    st.session_state["QUERY_RUNNING"] = user_message_id
                    answer, source = query_rag(prompt)

            if source is None:
                st.error(f"{answer}")
            else:
                st.session_state.messages[assistant_message_id] = {"role": "assistant", "content": answer, "source": source}
                del st.session_state["QUERY_RUNNING"]
                st.rerun()

    # Handle the case where the query is still running but interrupted due to feedback buttons
    if st.session_state.get("QUERY_RUNNING", None):
        response_placeholder = st.empty()
        answer, source = None, None
        with response_placeholder.container():
            with st.spinner('Generating Response...'):
                user_message_id = st.session_state.get("QUERY_RUNNING")
                assistant_message_id = user_message_id.replace("user", "assistant", 1)
                prompt = st.session_state.messages[user_message_id]["content"]
                # generate response from RAG model
                answer, source = query_rag(prompt)
        if source is None:
            st.error(f"{answer}")
        else:
            st.session_state.messages[assistant_message_id] = {"role": "assistant", "content": answer, "source": source}
            del st.session_state["QUERY_RUNNING"]
            st.rerun()


if __name__ == "__main__":
    # If streamlit instance is running
    if os.environ.get("STREAMLIT_RUNNING") == "1":
        main()
    else:
        os.environ["STREAMLIT_RUNNING"] = "1"  # Set the environment variable to indicate Streamlit is running
        #if multiple processes are being started, you must use Popen followed by run subprocess!
        with open('/app/logs/app.log', 'w') as file:
            file.write('')
        subprocess.Popen(["streamlit", "run", __file__, "--server.port=5001", "--server.address=0.0.0.0", "--server.baseUrlPath=/team1"])
        subprocess.run(["jupyter", "notebook", "--ip=0.0.0.0", "--port=6001", "--no-browser", "--allow-root", "--NotebookApp.base_url=/team1/jupyter"])
