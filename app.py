import streamlit as st
from uuid import uuid4
import os
import subprocess
from RAG import initialize_milvus, query_rag
import time
import yake
from chatbot_statistics import DatabaseClient  # Import the DatabaseClient class

db_client = DatabaseClient()

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

def extract_keywords(text):
    """
    Extract keywords from a text.

    Args:
        text (str): The text to extract keywords from

    Returns:
        list: A list of keywords
    """
    kw_extractor = yake.KeywordExtractor(lan="en", n=1, top=10)
    keywords = kw_extractor.extract_keywords(text)
    keywords_list = [keyword for keyword, _ in keywords]
    db_client.insert_common_keywords(keywords_list)

        
def display_statistics():
    """Display the current statistics in the sidebar."""
    st.sidebar.title("10 Statistics Reports")

    # Define the statistics to display and their corresponding database keys
    statistics = [
        ("Number of questions", "questions"),
        ("Number of correct answers", "correct_answers"),
        ("Number of incorrect answers", "incorrect_answers"),
        ("User engagement metrics", "user_engagement_metrics"),
        ("Response time analysis", "response_time"),
        ("Accuracy rate", "accuracy_rate"),
        ("Common topics or keywords", "common_keywords"),
        ("User satisfaction ratings", "user_satisfaction_ratings"),
        ("Improvement over time", "improvement_over_time"),
        ("Feedback summary", "feedback_summary"),
        ("Statistics per day and overall", "statistics_per_day_and_overall")
    ]

    # Display statistics in the sidebar
    for stat_name, stat in statistics:
        stat_value = db_client.get_latest_stat(stat)
        st.sidebar.write(f"{stat_name}: {stat_value}")
        
def handle_feedback(assistant_message_id):
    """
    Handle feedback for a message.

    Args:
        id (str): The unique ID of the message
    """
    previous_feedback = st.session_state.messages[assistant_message_id].get("feedback", None)
    feedback = st.session_state.get(f"feedback_{assistant_message_id}", None)

    if feedback == 1:
        if previous_feedback == None:
            db_client.increment_statistic("correct_answers")  # Increment like
        elif previous_feedback == "dislike":
            db_client.increment_statistic("incorrect_answers", -1)  # Decrement dislike
            db_client.increment_statistic("correct_answers")  # Increment like
        st.session_state.messages[assistant_message_id]["feedback"] = "like"
    elif feedback == 0:
        if previous_feedback == None:
            db_client.increment_statistic("incorrect_answers")  # Increment dislike
        elif previous_feedback == "like":
            db_client.increment_statistic("correct_answers", -1)  # Decrement like
            db_client.increment_statistic("incorrect_answers")  # Increment dislike
        st.session_state.messages[assistant_message_id]["feedback"] = "dislike"
    else:
        if previous_feedback == "like":
            db_client.increment_statistic("correct_answers", -1)  # Decrement like
        elif previous_feedback == "dislike":
            db_client.increment_statistic("incorrect_answers", -1)  # Decrement dislike
        st.session_state.messages[assistant_message_id]["feedback"] = None
 
            
def main():
    """Main Streamlit app logic."""
    header = st.container()
    header.write("""<div class='chat-title'>Team 1 Support Chatbot</div>""", unsafe_allow_html=True)
    header.write("""<div class='fixed-header'/>""", unsafe_allow_html=True)

    # Load the CSS file
    load_css("assets/style.css")
    
    if "messages" not in st.session_state:
        st.session_state.messages = {}
        with st.spinner("Initializing, Please Wait..."):
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
    
    # displays the 10 statistics        
    display_statistics()
    
    # Handle user input
    if prompt := st.chat_input("Message Team1 support chatbot"):
        
        # Increment the number of questions asked
        db_client.increment_statistic("questions")

        # creating user_message_id and assistant_message_id with the same unique "id" because they are related
        unique_id = str(uuid4())
        user_message_id = f"user_message_{unique_id}"
        assistant_message_id = f"assistant_message_{unique_id}"

        # save the user message in the session state
        st.session_state.messages[user_message_id] = {"role": "user", "content": prompt}
        st.markdown(f"<div class='user-message'>{prompt}</div>", unsafe_allow_html=True)

        response_placeholder = st.empty()
        with response_placeholder.container():
            with st.spinner('Generating Response...'):
                # generate response from RAG model
                start_time = time.time()
                answer, sources = query_rag(prompt)
                end_time = time.time()
                # calculate response time
                response_time = round(end_time - start_time, 3)

            # removing the sources from the answer for keyword extraction
            main_answer = answer.split("\n\nSources:")[0].strip()
            total_text = prompt + " " + main_answer
            extract_keywords(total_text)
            
            # adding response time to the statistics
            db_client.add_statistic("response_time", response_time)
            if sources == []:
                st.error(f"{answer}")
            else:
                st.session_state.messages[assistant_message_id] = {"role": "assistant", "content": answer, "sources": sources}
                st.rerun()

if __name__ == "__main__":
    # If streamlit instance is running
    if os.environ.get("STREAMLIT_RUNNING") == "1":
        main()
    else:
        os.environ["STREAMLIT_RUNNING"] = "1"  # Set the environment variable to indicate Streamlit is running
        #if multiple processes are being started, you must use Popen followed by run subprocess!
        subprocess.Popen(["streamlit", "run", __file__, "--server.port=5001", "--server.address=0.0.0.0", "--server.baseUrlPath=/team1"])
        subprocess.run(["jupyter", "notebook", "--ip=0.0.0.0", "--port=6001", "--no-browser", "--allow-root", "--NotebookApp.base_url=/team1/jupyter"])