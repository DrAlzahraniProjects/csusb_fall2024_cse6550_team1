import streamlit as st
import os
import subprocess
from RAG import *


def main():
    """Main Streamlit app logic."""
    header = st.container()

    def load_css(file_name):
        try:
            with open(file_name) as f:
                st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
        except FileNotFoundError:
            st.error(f"css file '{file_name}' not found.")

    # Load the CSS file
    load_css("assets/style.css")

    # Add custom CSS for buttons and alignment
    st.markdown("""
        <style>
        .assistant-message {
            margin-bottom: 0; /* Remove extra space below the message */
        }
        .feedback-buttons {
            display: inline-flex;  /* Make buttons inline */
            gap: 5px;  /* Reduce gap between buttons */
            margin-top: 5px;  /* Minimize vertical gap */
        }
        button[aria-label="👍 Like"], button[aria-label="👎 Dislike"] {
            background-color: transparent;
            border: none;
            cursor: pointer;
            font-size: 20px;
        }
        button[aria-label="👍 Like"]:hover::after {
            content: 'Like';  /* Display "Like" without emoji on hover */
            font-size: 14px;
            color: #000;
            position: absolute;
            top: 40px; /* Position text below the button */
        }
        button[aria-label="👎 Dislike"]:hover::after {
            content: 'Dislike';  /* Display "Dislike" without emoji on hover */
            font-size: 14px;
            color: #000;
            position: absolute;
            top: 40px; /* Position text below the button */
        }
        </style>
    """, unsafe_allow_html=True)

    header.write("""<div class='chat-title'>Team 1 Support Chatbot</div>""", unsafe_allow_html=True)
    header.write("""<div class='fixed-header'/>""", unsafe_allow_html=True)

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
        st.session_state.messages = []
        with st.spinner("Initializing, Please Wait..."):
            vector_store = initialize_milvus()


    # Handle feedback for each message
    def handle_feedback(message_index, feedback_type):
        if feedback_type == "like":
            st.session_state.messages[message_index]["feedback"] = "like"
        elif feedback_type == "dislike":
            st.session_state.messages[message_index]["feedback"] = "dislike"

    # Render existing messages
    for idx, message in enumerate(st.session_state.messages):
        if message["role"] == "assistant":
            st.markdown(f"""
                <div class='assistant-message'>
                    {message['content']}
                </div>
            """, unsafe_allow_html=True)

            # Like and Dislike buttons placed next to each other
            st.markdown("""
                <div class='feedback-buttons'>
                    <button aria-label="👍 Like" onclick="window.location.reload()">👍</button>
                    <button aria-label="👎 Dislike" onclick="window.location.reload()">👎</button>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='user-message'>{message['content']}</div>", unsafe_allow_html=True)
            
    # Handle user input
    if prompt := st.chat_input("Message Team1 support chatbot"):      
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.markdown(f"<div class='user-message'>{prompt}</div>", unsafe_allow_html=True)

        response_placeholder = st.empty()

        with response_placeholder.container():
            with st.spinner('Generating Response'):

                # generate response from RAG model
                answer = query_rag(prompt)
            st.session_state.messages.append({"role": "assistant", "content": answer})
            response_placeholder.markdown(f"""
                <div class='assistant-message'>
                    {answer}
                </div>
            """, unsafe_allow_html=True)

        # Add like and dislike buttons for the newly generated assistant message
        st.markdown("""
            <div class='feedback-buttons'>
                <button aria-label="👍 Like" onclick="window.location.reload()">👍</button>
                <button aria-label="👎 Dislike" onclick="window.location.reload()">👎</button>
            </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    # If streamlit instance is running
    if os.environ.get("STREAMLIT_RUNNING") == "1":
        main()
    else:
        os.environ["STREAMLIT_RUNNING"] = "1"  # Set the environment variable to indicate Streamlit is running
		#if multiple processes are being started, you must use Popen followed by run subprocess!
        subprocess.run(["streamlit", "run", __file__, "--server.port=5001", "--server.address=0.0.0.0", "--server.baseUrlPath=/team1"])
        #subprocess.run(["jupyter", "notebook", "--ip=0.0.0.0", "--port=6001", "--no-browser", "--allow-root"])
