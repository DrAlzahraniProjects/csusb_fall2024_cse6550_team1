import streamlit as st
import os
import subprocess

def main():
    """Main Streamlit app logic."""
    st.set_page_config(layout="wide")

    st.title("Team 1 Chatbot")

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

    load_display_chat()
    
    if prompt := st.chat_input("Message Team1 Chatbot"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar=None):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            st.write(f"You entered: {prompt}")
        st.session_state.messages.append({"role": "assistant", "content": f"You entered: {prompt}"})
      
def load_display_chat():
    """
    Load and display all the messages in the current session
    """

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

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
