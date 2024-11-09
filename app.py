import streamlit as st
from uuid import uuid4
import os
import subprocess
from RAG import initialize_milvus, query_rag
import time
import yake
import pandas as pd
from chatbot_statistics import DatabaseClient  # Import the DatabaseClient class

db_client = DatabaseClient()

answerable_questions = {
        "How can I contact ITS?".lower(),
        "How can I connect to the campus Wi-Fi?".lower(),
        "Who are the Co-Chairs for the 2024/2025 Committee?".lower(),
        "Where are all the printers located?".lower(),
        "What are the CoyoteLabs virtual computer lab?".lower(),
        "What are the CoyoteLabs virtual computer lab?".lower(),
        "Is Adobe Creative Cloud available as student software?".lower(),
        "Does CSUSB have accessible technology?".lower(),
        "How do I enable multi-factor authentication?".lower(),
        "What are Coyote OneCard benefits?".lower(),
        "why can't i get access for wireless prints through phone?".lower(),
    }
unanswerable_questions = {
        "How do I connect to Starbucks Wi-Fi?".lower(),
        "What is a smart contract?".lower(),
        "Can you write code for a basic python script?".lower(),
        "Who is the dean of CSUSB?".lower(),
        "What class does Dr. Alzahrani teach?".lower(),
        "Who is Hironori Washizaki?".lower(),
        "When was CSUSB built?".lower(),
        "What is the future impact of AI on software quality standards?".lower(),
        "What is regression testing?".lower(),
        "Can a student apply a part time job in IT support if so what is the process?".lower(),
    }

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
    kw_extractor = yake.KeywordExtractor(lan="en", n=1, top=10, features=None, dedupLim=0.9, dedupFunc='seqm', windowsSize=1)
    ignore_words = set(["context", "question", "answer", "source", "question", "provided", "information","based", "csusb", "article", "knowledge"])
    keywords = kw_extractor.extract_keywords(text)
    keywords_list = [keyword.lower() for keyword, _ in keywords if keyword.lower() not in ignore_words]
    # db_client.insert_common_keywords(keywords_list)

def color_cells(val):
    """
    Apply color based on cell content or other logic.

    Args:
        val (str): The value in the cell

    Returns:
        str : The color to apply to the cell
    """
    if "TP" in val:
        return "background-color: #f1f1f1;color:#444444"
    elif "TN" in val:
        return "background-color: #f1f1f1;color:#444444"
    return "background-color: #f9f9f9;color:#444444"  # Default color

        
def display_performance_metrics():
    """
    Display performance metrics in the sidebar.
    """
    st.sidebar.title("Confusion Matrix")
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
        'Actual Ans': {
            'Pred. Ans': f"{result['true_positive']} (TP)",
            'Pred. Unans': f"{result['false_negative']} (FN)"
        },
        'Actual Unans': {
            'Pred. Ans': f"{result['false_positive']} (FP)",
            'Pred. Unans': f"{result['true_negative']} (TN)"
        },
    }
    df = pd.DataFrame(data).transpose()
    # Apply the coloring function to each cell in the DataFrame
    styled_df = df.style.map(color_cells)
    st.sidebar.write(styled_df)


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
    # # Display performance metrics in the sidebar
    # for metric_name, metric in performance_metrics:
    #     st.sidebar.write(f"{metric_name}: {result[metric]}")
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
    header.write("""<div class='chat-title'>Team 1 Support Chatbot</div>""", unsafe_allow_html=True)
    header.write("""<div class='fixed-header'/>""", unsafe_allow_html=True)

    # Load the CSS file
    load_css("assets/style.css")
    
    if "messages" not in st.session_state:
        st.session_state.messages = {}
        with st.spinner("Initializing, Please Wait..."):
            # db_client.create_stats_table()
            # db_client.create_common_keywords_table()
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
    if prompt := st.chat_input("Message Team1 support chatbot"):

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
                if not os.environ.get("QUERY_RUNNING", None):
                    os.environ["QUERY_RUNNING"] = user_message_id
                    answer, sources = query_rag(prompt)

            # removing the sources from the answer for keyword extraction
            # main_answer = answer.split("\n\nSources:")[0].strip()
            # total_text = prompt + " " + main_answer
            # extract_keywords(total_text)

            if sources == []:
                st.error(f"{answer}")
            else:
                st.session_state.messages[assistant_message_id] = {"role": "assistant", "content": answer, "sources": sources}
                del os.environ["QUERY_RUNNING"]
                st.rerun()
    
    if os.environ.get("QUERY_RUNNING", None):
        response_placeholder = st.empty()
        with response_placeholder.container():
            with st.spinner('Generating Response...'):
                user_message_id = os.environ.get("QUERY_RUNNING")
                assistant_message_id = user_message_id.replace("user", "assistant", 1)
                prompt = st.session_state.messages[user_message_id]["content"]
                # generate response from RAG model
                answer, sources = query_rag(prompt)
        if sources == []:
            st.error(f"{answer}")
        else:
            st.session_state.messages[assistant_message_id] = {"role": "assistant", "content": answer, "sources": sources}
            del os.environ["QUERY_RUNNING"]
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