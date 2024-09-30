import streamlit as st
import os
import subprocess

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
                    I'm still learning, but I can repeat what you're saying! {message['content']}
                </div>
            """, unsafe_allow_html=True)
            # Display like and dislike buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("👍 Like", key=f"like_{idx}"):
                    handle_feedback(idx, "like")
            with col2:
                if st.button("👎 Dislike", key=f"dislike_{idx}"):
                    handle_feedback(idx, "dislike")
        else:
            st.markdown(f"<div class='user-message'>{message['content']}</div>", unsafe_allow_html=True)

    # Handle user input
    if prompt := st.chat_input("Message Team1 support chatbot"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.messages.append({"role": "assistant", "content": prompt})

        st.markdown(f"<div class='user-message'>{prompt}</div>", unsafe_allow_html=True)
        st.markdown(f"""
            <div class='assistant-message'>
                I'm still learning, but I can repeat what you're saying! {prompt}
            </div>
        """, unsafe_allow_html=True)

        # Add like and dislike buttons for the newly generated assistant message
        col1, col2 = st.columns(2)
        with col1:
            if st.button("👍 Like", key=f"like_new"):
                handle_feedback(len(st.session_state.messages) - 1, "like")
        with col2:
            if st.button("👎 Dislike", key=f"dislike_new"):
                handle_feedback(len(st.session_state.messages) - 1, "dislike")


if __name__ == "__main__":
    # If streamlit instance is running
    if os.environ.get("STREAMLIT_RUNNING") == "1":
        main()
    else:
        os.environ["STREAMLIT_RUNNING"] = "1"  # Set the environment variable to indicate Streamlit is running
		#if multiple processes are being started, you must use Popen followed by run subprocess!
        subprocess.run(["streamlit", "run", __file__, "--server.port=5001", "--server.address=0.0.0.0", "--server.baseUrlPath=/team1"])
        #subprocess.run(["jupyter", "notebook", "--ip=0.0.0.0", "--port=6001", "--no-browser", "--allow-root"])
