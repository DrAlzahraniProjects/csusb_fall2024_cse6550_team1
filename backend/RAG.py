CORPUS_SOURCE = 'https://www.csusb.edu/its'

import hashlib
import os
import streamlit as st
import time
import re
import numpy as np
import hashlib
import asyncio
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.schema import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_mistralai.chat_models import ChatMistralAI
from langchain_community.document_loaders import RecursiveUrlLoader
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pymilvus import connections, utility, Collection, CollectionSchema, FieldSchema, DataType
from httpx import HTTPStatusError
from backend.retriever import ScoreThresholdRetriever


load_dotenv()
MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY")
MILVUS_URI = "/app/milvus/milvus_vector.db"
MODEL_NAME = "sentence-transformers/all-MiniLM-L12-v2"
MAX_TEXT_LENGTH = 5000
EMBEDDING_MODEL = None

def get_embedding_model():
    """
    Get the embedding model for the RAG model

    Returns:
        SentenceTransformer: The embedding model
    """
    global EMBEDDING_MODEL
    if EMBEDDING_MODEL is None:
        EMBEDDING_MODEL = SentenceTransformer(MODEL_NAME)
    return EMBEDDING_MODEL

def is_filtered_query(query):
    patterns = [
        r"\b(hi|hello|hey|hiya|howdy|greetings|yo)\b", # Common greetings
        r"who (are|r) you\??", # Identity questions
        r"what('?s| is) your name\??", # Name questions
        r"(hi|hello|hey|yo),? (who are you|what('?s| is) your name)\??", # Greeting + identity
        r"(hi|hello|hey|yo),? (what do you do|what can you do)\??", # Greeting + capability
        r"good (morning|afternoon|evening),? (who are you|what('?s| is) your role)\??", # Polite intros
        r"(can you help me|what can you do for me)\??" # Informal assistance questions
    ]
    normalized = query.strip().lower()
    for pattern in patterns:
        if re.search(pattern, normalized):
            return True
    return False

def query_rag(query):
    """
    Entry point for the RAG model to generate an answer to a given query

    This function initializes the RAG model, sets up the necessary components such as the prompt template, vector store, 
    retriever, document chain, and retrieval chain, and then generates a response to the provided query.

    Args:
        query (str): The query string for which an answer is to be generated.
    
    Returns:
        str: The answer to the query
        str: The source of the information
    """
    try:
        # Check if the query is a filtered query and it is the first or second message
        if is_filtered_query(query):
            if CORPUS_SOURCE == 'https://www.csusb.edu/its':
                return "Hi there! I am an ITS Support Chatbot. I can help you with your ITS related queries. How can I assist you today?", "Unknown"
            return f"Hi there! I'm an AI assistant powered by {CORPUS_SOURCE}. I'm here to help with any questions you might have. How can I assist you today?", "Unknown"
        
        # Define the model
        chat_model = ChatMistralAI(model='open-mistral-7b', temperature = 0.2)
        print("Model Loaded")

        # Create the prompt and components for the RAG model
        prompt = create_prompt()
        print("Before embedding model")
        model = get_embedding_model()
        print("After embedding model")
        retriever = ScoreThresholdRetriever(score_threshold=0.7, k=3)
        document_chain = create_stuff_documents_chain(chat_model, prompt)
        query_embedding = np.array(model.encode(query), dtype=np.float32).tolist()
        collection = Collection(re.sub(r'\W+', '', CORPUS_SOURCE))
        # Retrieve the most relevant document based on the query
        retrieved_documents = retriever.get_related_documents(query_embedding, collection=collection)

        if not retrieved_documents:
            print("No Relevant Documents Retrieved, so sending default response")
            if CORPUS_SOURCE == 'https://www.csusb.edu/its':
                return "I am an ITS Support Chatbot. I can only answer ITS related questions. Do you have a different question?", "Unknown"
            return f"I'm an AI assistant powered by {CORPUS_SOURCE}. I can only answer questions related to {CORPUS_SOURCE}. Do you have a different question?", "Unknown"

        # Extract metadata from the most relevant document
        most_relevant_document = retrieved_documents[0]
        source = most_relevant_document.metadata.get("source", "Unknown")
        title = most_relevant_document.metadata.get("title", "Untitled").replace("\n", " ")

        print("Most Relevant Document Retrieved")

        # Generate a response using retrieval chain
        response = document_chain.invoke({
            "input": query,
            "context": retrieved_documents
        })

        # Add the source to the response if available
        if isinstance(source, str) and source != "Unknown":
            response += f"\n\nSource: [{title}]({source})"
            print("Response Generated")
        
        return response, source
            
    except HTTPStatusError as e:
        print(f"HTTPStatusError: {e}")
        if e.response.status_code == 429:
            return "I am currently experiencing high traffic. Please try again later.", None
        return f"I am unable to answer this question at the moment. Please try again later. Error: {e}", None
    
def create_prompt():
    """
    Create a prompt template for the RAG model

    Returns:
        PromptTemplate: The prompt template for the RAG model
    """
    # Define the prompt template
    # PROMPT_TEMPLATE = """
    # You are an AI assistant that provides answers strictly based on the provided context. Adhere to these guidelines:
    #  - Only answer questions based on the content within the <context> tags.
    #  - If the <context> does not contain information related to the question, respond only with: "I don't have enough information to answer this question."
    #  - For unclear questions or questions that lack specific context, request clarification from the user.
    #  - Provide specific, concise answers. Where relevant information includes statistics or numbers, include them in the response.
    #  - Avoid adding any information, assumption, or external knowledge. Answer accurately within the scope of the given context and do not guess.
    #  - If information is missing, respond only with: "I don't have enough information to answer this question."
    # """
    # PROMPT_TEMPLATE = """
    # You are an AI assistant that strictly provides answers based only on the provided context. Follow these rules without exception:
    # 1. Only answer questions based on the information contained within the <context> tags.
    # 2. If the <context> does not have information related to the question, respond only with: "The context does not contain enough information to answer this question."
    # 3. Do not attempt to infer, guess, or provide any information outside the <context>. If the question is unrelated to the <context>, explicitly state that you cannot provide an answer.
    # 4. For unclear or incomplete questions, respond with: "Could you please clarify your question?"
    # 5. Keep all responses concise and relevant. Do not elaborate beyond the context.
    # """
    PROMPT_TEMPLATE = """
    You are an AI assistant that provides answers strictly based on the provided context. Follow these rules without exception:
    1. Answer only questions that have directly relevant information within the <context> tags.
    2. If the <context> does not contain relevant information, respond only with: "The context does not contain enough information to answer this question."
    3. Do not elaborate, provide external suggestions, or reference any information outside the <context>.
    4. For unclear or incomplete questions, respond only with: "Could you please clarify your question?"
    5. Keep responses short and strictly factual based on the <context>.
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", PROMPT_TEMPLATE),
        ("human", "<question>{input}</question>\n\n<context>{context}</context>"),
    ])
    print("Prompt Created")

    return prompt

def get_existing_hashes_from_db(collection: Collection):
    """
    Get the existing hashed values from the database

    Args:
        collection (Collection): The collection to query

    Returns:
        set: The set of existing hashed values
    """
    existing_hashes = set()
    query_results = collection.query(expr="hash_id != ''", output_fields=["hash_id"])

    for results in query_results:
        existing_hashes.add(results["hash_id"])

    return existing_hashes

async def _load_documents_from_web_and_db(collection: Collection):
    """
    Load the documents from the web and the database and the embedding model simultaneously

    Args:
        collection (Collection): The collection to query

    Returns:
        list: The documents loaded from the web
        set: The set of existing hashed values
    """
    with ThreadPoolExecutor() as pool:
        loop = asyncio.get_event_loop()
        documents_future = loop.run_in_executor(pool, load_documents_from_web)

        hashes_future = loop.run_in_executor(pool, get_existing_hashes_from_db, collection)

        model_future = loop.run_in_executor(pool, get_embedding_model)

        documents, existing_hashes, _ = await asyncio.gather(documents_future, hashes_future, model_future)

        return documents, existing_hashes

def initialize_milvus(uri: str=MILVUS_URI):
    """
    Initialize the Milvus database with the vector store

    Args:
        uri (str, optional): The URI of the Milvus database. Defaults to MILVUS_URI.
    """
    connections.connect("default",uri=MILVUS_URI)
    
    if os.environ.get("vector_store_initialized", False):
        # passing an empty list to just load the vector store
        create_vector_store([])
        return
    if vector_store_check(uri):
        spinner_placeholder = st.empty()
        collection = Collection(re.sub(r'\W+', '', CORPUS_SOURCE))

        spinner_placeholder.markdown("Retrieving documents from website...")
        documents, existing_hashes = asyncio.run(_load_documents_from_web_and_db(collection))
        spinner_placeholder.markdown(f"{len(documents)} documents loaded from the website")
        time.sleep(0.3)
        spinner_placeholder.markdown("Retrieving documents from website... Done")

        # Split the documents into chunks
        spinner_placeholder.markdown("Splitting documents into chunks...")
        time.sleep(0.3)
        docs = split_documents(documents=documents)
        spinner_placeholder.markdown("Splitting documents into chunks... Done")
        time.sleep(0.3)

        # Initialize sets to store common hashes and documents to insert
        common_hashes = set()
        documents_to_insert = []
        # Check if the documents from the website are already in the database
        spinner_placeholder.markdown("Checking for existing documents...")
        for doc in docs:
            text = doc.page_content[:MAX_TEXT_LENGTH]
            hashed_text = hash_text(text)
            if hashed_text in existing_hashes:
                # Remove the hash from the existing hashes
                common_hashes.add(hashed_text)
            else:
                # Add the document to the list of documents to insert
                print("Hashed Text insert", hashed_text)
                documents_to_insert.append(doc)
        
        existing_hashes = existing_hashes - common_hashes
        print("Existing Hashes", existing_hashes)
        print("Documents to Insert", documents_to_insert)
        if existing_hashes:
            number_of_existing_hashes = len(existing_hashes)
            spinner_placeholder.markdown(f"Deleting {number_of_existing_hashes} outdated documents...")
            time.sleep(0.3)
            count = 1
            for hash_to_delete in existing_hashes:
                spinner_placeholder.markdown(f"Deleting {count}/{number_of_existing_hashes} outdated documents...")
                collection.delete(expr = f"hash_id == '{hash_to_delete}'")
                count += 1
            print("Deleted outdated documents")
            spinner_placeholder.markdown("Deleted outdated documents")
            time.sleep(0.3)
        spinner_placeholder.empty()
        create_vector_store(documents_to_insert)
    else:
        spinner_placeholder = st.empty()

        spinner_placeholder.markdown("Retrieving documents from website...")
        documents = load_documents_from_web()
        spinner_placeholder.markdown(f"{len(documents)} documents loaded from the website")
        time.sleep(0.3)
        spinner_placeholder.markdown("Retrieving documents from website... Done")
        print("Documents Loaded")

        # Split the documents into chunks
        spinner_placeholder.markdown("Splitting documents into chunks...")
        docs = split_documents(documents=documents)
        spinner_placeholder.markdown("Splitting documents into chunks... Done")
        time.sleep(0.3)
        spinner_placeholder.empty()
        create_vector_store(docs)


def load_documents_from_web():
    """
    Load the documents from the web and store the page contents

    Returns:
        list: The documents loaded from the web
    """
    loader = RecursiveUrlLoader(
        url=CORPUS_SOURCE,
        prevent_outside=True,
        base_url=CORPUS_SOURCE
        )
    raw_documents = loader.load()

    # Ensure documents are cleaned
    cleaned_documents = []
    for doc in raw_documents:
        cleaned_text = clean_text_from_html(doc.page_content)
        cleaned_documents.append(Document(page_content=cleaned_text, metadata=doc.metadata))

    return cleaned_documents

def clean_text_from_html(html_content):
    """
    Clean the text from the HTML content

    Args:
        html_content (str): The HTML content to clean

    Returns:
        str: The cleaned text
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove unnecessary elements
    for script_or_style in soup(['script', 'style', 'header', 'footer', 'nav']):
        script_or_style.decompose()

    main_content = soup.find('main')
    if main_content:
        content = main_content.get_text(separator='\n')
    else:
        content = soup.get_text(separator='\n')

    return clean_text(content)

def clean_text(text):
    """
    Clean the text by removing extra spaces and empty lines

    Args:
        text (str): The text to clean

    Returns:
        str: The cleaned text
    """
    lines = (line.strip() for line in text.splitlines())
    cleaned_lines = [line for line in lines if line]
    return '\n'.join(cleaned_lines)

def split_documents(documents):
    """
    Split the documents into chunks

    Args:
        documents (list): The documents to split

    Returns:
        list: list of chunks of documents
    """
    # Create a text splitter to split the documents into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,  # Split the text into chunks of 1000 characters
        chunk_overlap=200,  # Overlap the chunks by 300 characters
        is_separator_regex=False,
    )
    # Split the documents into chunks
    docs = text_splitter.split_documents(documents)
    unique_docs = remove_duplicates(docs)
    return unique_docs

def remove_duplicates(documents):
    """
    Remove duplicate documents based on the page content

    Args:
        documents (list): The list of documents to remove duplicates from

    Returns:
        list: The list of unique documents
    """
    seen_content = set()
    unique_documents = []
    for doc in documents:
        if doc.page_content not in seen_content:
            seen_content.add(doc.page_content)
            unique_documents.append(doc)
    return unique_documents

def vector_store_check(uri):
    """
    Check if the vector store exists in the local Milvus database specified by the URI.

    Args:
        uri (str): Path to the local milvus db

    Returns:
        bool: True if the vector store exists, False otherwise
    """
    head = os.path.split(uri)
    os.makedirs(head[0], exist_ok=True)

    # Return True if exists, False otherwise
    return utility.has_collection(re.sub(r'\W+', '', CORPUS_SOURCE))

def hash_text(text):
    """
    Hash the text using MD5 algorithm

    Args:
        text (str): The text to hash

    Returns:
        str: The hashed text
    """
    return hashlib.md5(text.encode()).hexdigest()

def create_vector_store(docs):
    """
    Create a vector store in the local Milvus database

    Args:
        docs (list): The list of documents to insert into the vector store
    """
    if docs == []:
        spinner_placeholder = st.empty()
        collection = Collection(re.sub(r'\W+', '', CORPUS_SOURCE))

        spinner_placeholder.markdown("Loading the vector store...")
        time.sleep(0.3)
        collection.load()
        spinner_placeholder.markdown("Vectore store Initialization complete!")
        spinner_placeholder.empty()
        return
    spinner_placeholder = st.empty()
    # Create a new vector store and drop any existing one
    fields = [
        FieldSchema(name="hash_id", dtype=DataType.VARCHAR, max_length=32, is_primary=True),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=384),
        FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=5000),
        FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=200),
        FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=200),
    ]
    schema = CollectionSchema(fields, description="Collection Schema for the Vector Store")
    print("Before Collection")
    collection = Collection(name=re.sub(r'\W+', '', CORPUS_SOURCE), schema=schema)
    print("After Collection")
    print("Before Index")
    index_params = {
            "index_type": "HNSW",
        "metric_type": "IP",
        "params": {"M": 16, "efConstruction": 200}
    }
    collection.create_index(field_name="embedding", index_params=index_params)
    print("After Index")

    model = get_embedding_model()
    count = 1
    number_of_docs = len(docs)
    spinner_placeholder.markdown(f"Inserting {number_of_docs} new documents...")
    time.sleep(0.3)
    for doc in docs:
        print(f"Inserting Document {count}", doc)
        spinner_placeholder.markdown(f"Inserting {count}/{number_of_docs} new documents...")
        text = doc.page_content[:MAX_TEXT_LENGTH]
        hash_id = hash_text(text)
        embedding = model.encode(text)
        title = doc.metadata.get("title", "Untitled")
        source = doc.metadata.get("source", "Unknown")
        collection.insert([[hash_id], [embedding], [text], [title], [source]])
        count += 1
    
    spinner_placeholder.markdown("Insertion compeleted. Loading the vector store...")
    time.sleep(0.3)
    collection.load()
    spinner_placeholder.markdown("Vectore store Initialization complete!")
    print("Vector Store Created")
    spinner_placeholder.empty()


if __name__ == '__main__':
    pass