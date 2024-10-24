import streamlit as st
from uuid import uuid4
import os
import subprocess
from datetime import datetime
from RAG import *
import re

# Initialize global statistics for daily and overall tracking
def initialize_statistics():
    return {
        "num_questions": 0,
        "num_correct": 0,
        "num_incorrect": 0,
        "total_response_time": 0,  # for tracking average response time
        "user_engagement": 0,  # Total time users spend interacting
        "common_topics": set(),
        "feedback_ratings": [],  # To calculate satisfaction rate
    }

def load_css(file_name):
    """Load a CSS file to style the app."""
    try:
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"css file '{file_name}' not found.")

def handle_feedback(assistant_message_id):
    """Handle feedback for a message."""
    feedback = st.session_state.get(f"feedback_{assistant_message_id}", None)
    if feedback == 1:
        st.session_state.stats["num_correct"] += 1
        st.session_state.messages[assistant_message_id]["feedback"] = "like"
    elif feedback == 0:
        st.session_state.stats["num_incorrect"] += 1
        st.session_state.messages[assistant_message_id]["feedback"] = "dislike"
    else:
        st.session_state.messages[assistant_message_id]["feedback"] = None
    st.session_state.stats["feedback_ratings"].append(feedback)

def calculate_statistics():
    """Calculate accuracy rate, satisfaction rate, and average response time."""
    num_questions = st.session_state.stats["num_questions"]
    num_correct = st.session_state.stats["num_correct"]
    num_incorrect = st.session_state.stats["num_incorrect"]
    total_feedback = len(st.session_state.stats["feedback_ratings"])

    if num_questions > 0:
        accuracy_rate = (num_correct / num_questions) * 100
    else:
        accuracy_rate = 0

    if total_feedback > 0:
        satisfaction_rate = (
            st.session_state.stats["feedback_ratings"].count(1) / total_feedback
        ) * 100
    else:
        satisfaction_rate = 0

    avg_response_time = (
        st.session_state.stats["total_response_time"] / num_questions
        if num_questions > 0
        else 0
    )

    return {
        "accuracy_rate": accuracy_rate,
        "satisfaction_rate": satisfaction_rate,
        "avg_response_time": avg_response_time,
    }

def extract_keywords(text):
    """Extract common keywords from user input."""
    # Simple example using regex to extract words longer than 3 letters (can be replaced with NLP models)
    keywords = re.findall(r'\b\w{4,}\b', text.lower())
    return keywords

def main():
    """Main Streamlit app logic."""
    header = st.container()
    header.write("""<div class='chat-title'>Team 1 Support Chatbot</div>""", unsafe_allow_html=True)
    header.write("""<div class='fixed-header'/>""", unsafe_allow_html=True)

    # Load the CSS file
    load_css("assets/style.css")

    # Initialize statistics if not present in session state
    if "stats" not in st.session_state:
        st.session_state.stats = initialize_statistics()

    # Sidebar for chat history and statistics
    st.sidebar.title("10 Statistics Reports")

    # Calculate statistics
    calc_stats = calculate_statistics()

    # Display statistics in the sidebar
    statistics = [
        f"Number of questions: {st.session_state.stats['num_questions']}",
        f"Number of correct answers: {st.session_state.stats['num_correct']}",
        f"Number of incorrect answers: {st.session_state.stats['num_incorrect']}",
        f"User engagement metrics: {st.session_state.stats['user_engagement']} seconds",
        f"Response time analysis: {calc_stats['avg_response_time']:.2f} seconds",
        f"Accuracy rate: {calc_stats['accuracy_rate']:.2f}%",
        f"Satisfaction rate: {calc_stats['satisfaction_rate']:.2f}%",
        f"Common topics or keywords: {', '.join(st.session_state.stats['common_topics'])}",
        "Improvement over time",  # Placeholder for future feature
        f"Feedback summary: {st.session_state.stats['feedback_ratings'].count(1)} positive, {st.session_state.stats['feedback_ratings'].count(0)} negative",
    ]

    for stat in statistics:
        st.sidebar.write(stat)

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
                key=f"feedback_{message_id}",
                on_change=lambda id=message_id: handle_feedback(id),
            )
        else:
            st.markdown(f"<div class='user-message'>{message['content']}</div>", unsafe_allow_html=True)

    # Handle user input
    if prompt := st.chat_input("Message Team1 support chatbot"):
        # Increment number of questions
        st.session_state.stats["num_questions"] += 1
        st.session_state.stats["user_engagement"] += 5  # Assume some engagement duration for example purposes

        # Extract keywords from the user's prompt and update common topics
        keywords = extract_keywords(prompt)
        st.session_state.stats["common_topics"].update(keywords)

        # Creating user_message_id and assistant_message_id with the same unique "id"
        unique_id = str(uuid4())
        user_message_id = f"user_message_{unique_id}"
        assistant_message_id = f"assistant_message_{unique_id}"

        st.session_state.messages[user_message_id] = {"role": "user", "content": prompt}
        st.markdown(f"<div class='user-message'>{prompt}</div>", unsafe_allow_html=True)

        response_placeholder = st.empty()

        with response_placeholder.container():
            with st.spinner('Generating Response...'):
                start_time = datetime.now()  # Track start time
                # generate response from RAG model
                answer, sources = query_rag(prompt)
                end_time = datetime.now()  # Track end time
                response_time = (end_time - start_time).total_seconds()

            # Add response time to stats
            st.session_state.stats["total_response_time"] += response_time

            if sources == []:
                st.error(f"{answer}")
            else:
                st.session_state.messages[assistant_message_id] = {"role": "assistant", "content": answer, "sources": sources}
                st.rerun()

if __name__ == "__main__":
    if os.environ.get("STREAMLIT_RUNNING") == "1":
        main()
    else:
        os.environ["STREAMLIT_RUNNING"] = "1"  # Set the environment variable to indicate Streamlit is running
        subprocess.Popen(["streamlit", "run", __file__, "--server.port=5001", "--server.address=0.0.0.0", "--server.baseUrlPath=/team1"])
        subprocess.run(["jupyter", "notebook", "--ip=0.0.0.0", "--port=6001", "--no-browser", "--allow-root", "--NotebookApp.base_url=/team1/jupyter"])
