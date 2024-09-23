import streamlit as st
import random

# Set the title of the app
st.set_page_config(page_title="Team1ChatBot", layout="wide")

# Team1 Chatbot Heading
st.title("Team1 SupportChatbot")

# Sidebar header for static report metrics
st.sidebar.header("10 Statistics Report")

# Sidebar 10 statistics
total_questions = st.sidebar.write("Number of Questions")
correct_answers = st.sidebar.write("Number of Correct Answers")
incorrect_answers = st.sidebar.write("Number of Incorrect Answers")
user_engagement = st.sidebar.write("User Engagement Metrics")
avg_response_time = st.sidebar.write("Avg Response Time (s)")
accuracy_rate = st.sidebar.write("Accuracy Rate (%)")
common_topics = st.sidebar.write("Common Topics or Keywords")
user_satisfaction = st.sidebar.write("User Satisfaction Ratings (1-5)")
improvement_over_time = st.sidebar.write("Improvement Over Time")
feedback_summary = st.sidebar.write("Feedback Summary")
daily_statistics = st.sidebar.write("Daily Statistics")

# Initialize session state if it doesn't exist
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Function to handle user input
def handle_user_input(user_input):
    # Append user input to chat history
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    
    # Simulate a chatbot response with predefined messages
    responses = [
        "That's an interesting question! Can you elaborate?",
        "I’m here to assist you. What else would you like to know?",
        "Could you clarify what you mean by that?",
        "I can help with that! What specific information do you need?",
        "Thank you for your question! Let's dive deeper into it.",
        "I'm still learning, but I can provide insights on that.",
        "Let me see how I can assist you further with this topic.",
        "Here’s what I can tell you about that...",
    ]
    
    # Randomly select a response
    bot_response = random.choice(responses)
    st.session_state.chat_history.append({"role": "bot", "content": bot_response})

# Display chat history
for message in st.session_state.chat_history:
    if message['role'] == 'user':
        st.markdown(f"<div style=' text-align: right;background-color: #3C3C3C;color: #FFFFFF;border: 1px solid #3C3F41;border-radius: 10px;padding: 10px 15px;margin: 5px;display: inline-block;max-width: 70%;float: right;clear: both;'>{message['content']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div style='text-align: left;background-color: #2B2B2B;color: #FFFFFF;border: 1px solid #3C3F41;border-radius: 10px;padding: 10px 15px;margin: 5px;display: inline-block;max-width: 70%;float: left;clear: both;'>{message['content']}</div>", unsafe_allow_html=True)
        st.markdown(
            "<div style='text-align: left; margin: 5px;'>"
            "<button style='background: none; border: none; cursor: pointer; font-size: 24px;' onclick='alert(\"Liked!\")'>👍</button>"
            "<button style='background: none; border: none; cursor: pointer; font-size: 24px;' onclick='alert(\"Disliked!\")'>👎</button>"
            "</div>",
            unsafe_allow_html=True
        )

# Chat input box for user
user_input = st.chat_input("Enter your question here")

# Process input if user has entered a message
if user_input:
    handle_user_input(user_input)
