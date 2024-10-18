import streamlit as st
from uuid import uuid4
import os
import subprocess
from RAG import *

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

def handle_feedback(assistant_message_id):
    """
    Handle feedback for a message.

    Args:
        id (str): The unique ID of the message
    """
    feedback = st.session_state.get(f"feedback_{assistant_message_id}", None)
    if feedback == 1:
        st.session_state.messages[assistant_message_id]["feedback"] = "like"
    elif feedback == 0:
        st.session_state.messages[assistant_message_id]["feedback"] = "dislike"
    else:
        st.session_state.messages[assistant_message_id]["feedback"] = None


def main():
    """Main Streamlit app logic."""

    header = st.container()
    header.write("""<div class='chat-title'>Team 1 Support Chatbot</div>""", unsafe_allow_html=True)
    header.write("""<div class='fixed-header'/>""", unsafe_allow_html=True)

    # Load the CSS file
    load_css("assets/style.css")

    # Sidebar for chat history and statistics
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
                key = f"feedback_{message_id}",
                on_change= handle_feedback(message_id),
            )
        else:
            st.markdown(f"<div class='user-message'>{message['content']}</div>", unsafe_allow_html=True)
            
    # Handle user input
    if prompt := st.chat_input("Message Team1 support chatbot"):
        # creating user_message_id and assistant_message_id with the same unique "id" because 
        # in future when we implement feedback related changes on backend side,
        # we can use this "id" to know which question/response it belongs to
        unique_id = str(uuid4())
        user_message_id = f"user_message_{unique_id}"
        assistant_message_id = f"assistant_message_{unique_id}"

        st.session_state.messages[user_message_id] = {"role": "user", "content": prompt}    
        st.markdown(f"<div class='user-message'>{prompt}</div>", unsafe_allow_html=True)

        response_placeholder = st.empty()

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
        subprocess.run(["jupyter", "notebook", "--ip=0.0.0.0", "--port=6001", "--no-browser", "--allow-root", "--NotebookApp.base_url=/jupyter"])