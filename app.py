import streamlit as st
import os
import subprocess

def main():
    """Main Streamlit app logic."""
    st.set_page_config(layout="wide")

    st.title("Hello from Team 1")

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

    # Chat history
    if 'chat_history' not in st.session_state:
        st.session_state['chat_history'] = []

    # Display chat history
    st.subheader("Chat History")

    # Text input field and submit button logic
    if 'user_input' not in st.session_state:
        st.session_state['user_input'] = ""

    # Display the entered text in a text area above the input field if text exists
    if st.session_state['user_input']:
        st.text_area("Your input:", value=st.session_state['user_input'], height=100, disabled=True)


    # Handle button click event
    if prompt := st.chat_input("Text here"):
        # Update session state with the new input
        st.session_state['user_input'] = prompt
        
        # Simulating a bot response (you can replace this with actual bot logic)
        bot_response = f"Bot's response to: {prompt}"

        # Append the conversation to chat history
        st.session_state['chat_history'].append({"user": prompt, "bot": bot_response})

        # Clear the input field after submission
        st.session_state['user_input'] = ""

    for chat in st.session_state['chat_history']:
        st.write(f"You: {chat['user']}")
        st.write(f"Bot: {chat['bot']}")
        st.write("---")

if __name__ == "__main__":
    # If streamlit instance is running
    if os.environ.get("STREAMLIT_RUNNING") == "1":
        main()

    # If streamlit is not running
    else:
        os.environ["STREAMLIT_RUNNING"] = "1"  # Set the environment variable to indicate Streamlit is running
        subprocess.Popen(["streamlit", "run", __file__, "--server.port=5001", "--server.address=0.0.0.0"])
        subprocess.Popen(["service", "nginx", "start"])
        subprocess.run(["jupyter", "notebook", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"])
