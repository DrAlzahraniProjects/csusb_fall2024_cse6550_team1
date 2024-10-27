import streamlit as st
from uuid import uuid4
import os
import subprocess
from RAG import *
import time
from statistics import DatabaseClient  # Import the DatabaseClient class
from statistics import datetime

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
        
def display_statistics():
    """Display the current statistics in the sidebar."""
    st.sidebar.title("10 Statistics Reports")

    # List of statistics to display
    statistics = [
        "Number of questions",
        "Number of correct answers",
        "Number of incorrect answers",
        "User engagement metrics",
        "Response time analysis",
        "Accuracy rate",
        "Common topics or keywords",
        "User satisfaction ratings",
        "Improvement over time",
        "Feedback summary",
        "Statistics per day and overall"
    ]

    # Display statistics in the sidebar
    for stat in statistics:
        stat_value = db_client.get_latest_stat(stat)
        st.sidebar.write(f"{stat}: {stat_value}")
        
def handle_feedback(assistant_message_id, feedback):
    """
    Handle feedback for a message.

    Args:
        id (str): The unique ID of the message
    """
    #feedback = st.session_state.get(f"feedback_{assistant_message_id}", None)
 
    previous_feedback = st.session_state.get(f"feedback_{assistant_message_id}", None)

    # Check if feedback has already been submitted
    if previous_feedback == "like":
        if feedback == "dislike":  # Change from like to dislike
            db_client.increment_statistic("Number of incorrect answers")  # Increment dislike
            db_client.increment_statistic("Number of correct answers", -1)  # Decrement like
            st.session_state[f"feedback_{assistant_message_id}"] = "dislike"
    elif previous_feedback == "dislike":
        if feedback == "like":  # Change from dislike to like
            db_client.increment_statistic("Number of correct answers")  # Increment like
            db_client.increment_statistic("Number of incorrect answers", -1)  # Decrement dislike
            st.session_state[f"feedback_{assistant_message_id}"] = "like"
    else:
        if feedback == "like":  # First-time like
            db_client.increment_statistic("Number of correct answers")
            st.session_state[f"feedback_{assistant_message_id}"] = "like"
        elif feedback == "dislike":  # First-time dislike
            db_client.increment_statistic("Number of incorrect answers")
            st.session_state[f"feedback_{assistant_message_id}"] = "dislike"
            
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
            feedback = st.session_state.get(f"feedback_{message_id}", None)
            with st.container():
                col1, col2, col3, col4 = st.columns([0.2, 0.2, 1, 1])  # Create two columns for buttons, other two columns are blank for button spacing/does not work with only two columns
                with col1:
                    st.markdown("<div class='feedback-container'>", unsafe_allow_html=True)
                    if st.button("👍", key=f"like_{message_id}", help="Like this response"):
                        if feedback != "like":  # Only handle if not already liked
                            handle_feedback(message_id, "like")
                    st.markdown("</div>", unsafe_allow_html=True)
                with col2:
                    st.markdown("<div class='feedback-container'>", unsafe_allow_html=True)
                    if st.button("👎", key=f"dislike_{message_id}", help="Dislike this response"):
                        if feedback != "dislike":  # Only handle if not already disliked
                            handle_feedback(message_id, "dislike")
                    st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='user-message'>{message['content']}</div>", unsafe_allow_html=True)
    
    # displays the 10 statistics        
    display_statistics()
    
    # Handle user input
    if prompt := st.chat_input("Message Team1 support chatbot"):
        # creating user_message_id and assistant_message_id with the same unique "id" because 
        # in future when we implement feedback related changes on backend side,
        # we can use this "id" to know which question/response it belongs to
        unique_id = str(uuid4())
        user_message_id = f"user_message_{unique_id}"
        assistant_message_id = f"assistant_message_{unique_id}"

        # Increment the number of questions asked
        db_client.increment_statistic("Number of questions")
        
        st.session_state.messages[user_message_id] = {"role": "user", "content": prompt}
        st.markdown(f"<div class='user-message'>{prompt}</div>", unsafe_allow_html=True)

        response_placeholder = st.empty()

        # Record the response time
        start_time = time.time()
        answer, sources = query_rag(prompt)
        response_time = time.time() - start_time
        db_client.add_statistic("Response time analysis", response_time)
        
        with response_placeholder.container():
            with st.spinner('Generating Response...'):
                # generate response from RAG model
                answer, sources = query_rag(prompt)
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