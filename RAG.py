CORPUS_SOURCE = 'https://www.csusb.edu/its'

import os
import time
import asyncio
from dotenv import load_dotenv
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.schema import Document
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
#from langchain_mistralai import MistralAIEmbeddings
from langchain_mistralai.chat_models import ChatMistralAI
#from langchain_cohere import ChatCohere
from langchain_milvus import Milvus
from langchain_community.document_loaders import WebBaseLoader, RecursiveUrlLoader
from bs4 import BeautifulSoup
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from pymilvus import connections, utility
from requests.exceptions import HTTPError
from httpx import HTTPStatusError
from retriever import ScoreThresholdRetriever

load_dotenv()
MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY")

MILVUS_URI = "milvus/milvus_vector.db"
MODEL_NAME = "sentence-transformers/all-MiniLM-L12-v2"

def get_embedding_function():
    """
    returns embedding function for the model

    Returns:
        embedding function
    """
    embedding_function = HuggingFaceEmbeddings(model_name=MODEL_NAME)
    return embedding_function

async def query_rag(query):
    """
    Entry point for the RAG model to generate an answer to a given query

    This function initializes the RAG model, sets up the necessary components such as the prompt template, vector store, 
    retriever, document chain, and retrieval chain, and then generates a response to the provided query.

    Args:
        query (str): The query string for which an answer is to be generated.
    
    Returns:
        str: The answer to the query
    """
    # Without execution time calculation
    try:
        # Load vector store asynchronously
        async def load_vector_store():
            return load_existing_db(uri=MILVUS_URI)

        # Start loading vector store asynchronously
        vector_store_future = asyncio.create_task(load_vector_store())

        # Wait for vector store and initialize retriever
        vector_store = await vector_store_future
        retriever = ScoreThresholdRetriever(vector_store=vector_store, score_threshold=0.2, k=5)

        # Define the model
        model = ChatMistralAI(model='open-mistral-7b', temperature=0.2)
        print("Model Loaded")

        # Create the prompt and components for the RAG model
        prompt = create_prompt()

        document_chain = create_stuff_documents_chain(model, prompt)

        # Retrieve the most relevant document based on the query
        retrieved_documents = retriever.get_relevant_documents(query)

        if not retrieved_documents:
            print("No Relevant Documents Retrieved, so sending default response")
            return "I don't have enough information to answer this question.", "Unknown"

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
        # response_text = response.get("answer", "I couldn't generate a response.")

        # Add the source to the response if available
        if isinstance(source, str) and source != "Unknown":
            response += f"\n\nSource: [{title}]({source})"
            print("Response Generated")

        return response, source

    except HTTPStatusError as e:
        print(f"HTTPStatusError: {e}")
        if e.response.status_code == 429:
            return "I am currently experiencing high traffic. Please try again later.", None
        return "I am unable to answer this question at the moment. Please try again later.", None

    # Calculating execution time of each sub-task

    # try:
    #     # Load vector store asynchronously
    #     async def load_vector_store():
    #         return load_existing_db(uri=MILVUS_URI)
    #
    #     # Start loading vector store asynchronously
    #     start_time = time.time()
    #     vector_store_future = asyncio.create_task(load_vector_store())
    #     vector_store_time = time.time() - start_time
    #     print(f"Time taken to load vector store: {vector_store_time:.6f} seconds")
    #
    #     # Wait for vector store and initialize retriever
    #     vector_store = await vector_store_future
    #     start_time = time.time()
    #     retriever = ScoreThresholdRetriever(vector_store=vector_store, score_threshold=0.2, k=5)
    #     retriever_time = time.time() - start_time
    #     print(f"Time taken to create retriever: {retriever_time:.6f} seconds")
    #
    #     # Define the model
    #     start_time = time.time()
    #     model = ChatMistralAI(model='open-mistral-7b', temperature=0.2)
    #     model_time = time.time() - start_time
    #     print(f"Time taken to load the model: {model_time:.6f} seconds")
    #     print("Model Loaded")
    #
    #     # Create the prompt and components for the RAG model
    #     start_time = time.time()
    #     prompt = create_prompt()
    #     prompt_time = time.time() - start_time
    #     print(f"Time taken to create prompt: {prompt_time:.6f} seconds")
    #
    #     start_time = time.time()
    #     document_chain = create_stuff_documents_chain(model, prompt)
    #     document_chain_time = time.time() - start_time
    #     print(f"Time taken to create document chain: {document_chain_time:.6f} seconds")
    #
    #     # Retrieve the most relevant document based on the query
    #     start_time = time.time()
    #     retrieved_documents = retriever.get_relevant_documents(query)
    #     retrieval_time = time.time() - start_time
    #     print(f"Time taken to retrieve documents: {retrieval_time:.6f} seconds")
    #
    #     if not retrieved_documents:
    #         print("No Relevant Documents Retrieved, so sending default response")
    #         return "I don't have enough information to answer this question.", "Unknown"
    #
    #     # Extract metadata from the most relevant document
    #     most_relevant_document = retrieved_documents[0]
    #     source = most_relevant_document.metadata.get("source", "Unknown")
    #     title = most_relevant_document.metadata.get("title", "Untitled").replace("\n", " ")
    #
    #     print("Most Relevant Document Retrieved")
    #
    #     # Generate a response using retrieval chain
    #     start_time = time.time()
    #     response = document_chain.invoke({
    #         "input": query,
    #         "context": retrieved_documents
    #     })
    #     invoke_time = time.time() - start_time
    #     print(f"Time taken to invoke : {invoke_time:.6f} seconds")
    #     # response_text = response.get("answer", "I couldn't generate a response.")
    #
    #
    #     # Add the source to the response if available
    #     if isinstance(source, str) and source != "Unknown":
    #         response += f"\n\nSource: [{title}]({source})"
    #         print("Response Generated")
    #
    #     return response, source
    #
    # except HTTPStatusError as e:
    #     print(f"HTTPStatusError: {e}")
    #     if e.response.status_code == 429:
    #         return "I am currently experiencing high traffic. Please try again later.", None
    #     return "I am unable to answer this question at the moment. Please try again later.", None
    
def create_prompt():
    """
    Create a prompt template for the RAG model

    Returns:
        PromptTemplate: The prompt template for the RAG model
    """
    # Define the prompt template
    PROMPT_TEMPLATE = """
    You are an AI assistant that provides answers strictly based on the provided context. Adhere to these guidelines:
     - Only answer questions based on the content within the <context> tags.
     - If the <context> does not contain information related to the question, respond only with: "I don't have enough information to answer this question."
     - For unclear questions or questions that lack specific context, request clarification from the user.
     - Provide specific, concise ansewrs. Where relevant information includes statistics or numbers, include them in the response.
     - Avoid adding any information, assumption, or external knowledge. Answer accurately within the scope of the given context and do not guess.
     - If information is missing, respond only with: "I don't have enough information to answer this question."
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", PROMPT_TEMPLATE),
        ("human", "<question>{input}</question>\n\n<context>{context}</context>"),
    ])
    print("Prompt Created")

    return prompt


def initialize_milvus(uri: str=MILVUS_URI):
    """
    Initialize the vector store for the RAG model

    Args:
        uri (str, optional): Path to the local milvus db. Defaults to MILVUS_URI.

    Returns:
        vector_store: The vector store created
    """
    if vector_store_check(uri):
        vector_store = load_existing_db(uri)
    else:
        embeddings = get_embedding_function()
        print("Embeddings Loaded")
        documents = load_documents_from_web()
        print("Documents Loaded")
        print(len(documents))

        # Split the documents into chunks
        docs = split_documents(documents=documents)
        print("Documents Splitting completed")

        vector_store = create_vector_store(docs, embeddings, uri)

    return vector_store

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
        chunk_size=1000,  # Split the text into chunks of 1000 characters
        chunk_overlap=300,  # Overlap the chunks by 300 characters
        is_separator_regex=False,  
    )
    # Split the documents into chunks
    docs = text_splitter.split_documents(documents)
    return docs

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
    
    # Connect to the Milvus database
    connections.connect("default",uri=uri)

    # Return True if exists, False otherwise
    return utility.has_collection("IT_support")

def create_vector_store(docs, embeddings, uri):
    """
    This function initializes a vector store using the provided documents and embeddings.

    Args:
        docs (list): A list of documents to be stored in the vector store.
        embeddings : A function or model that generates embeddings for the documents.
        uri (str): Path to the local milvus db

    Returns:
        vector_store: The vector store created
    """
    # Create a new vector store and drop any existing one
    vector_store = Milvus.from_documents(
        documents=docs,
        embedding=embeddings,
        collection_name="IT_support",
        connection_args={"uri": uri},
        drop_old=True,
    )
    print("Vector Store Created")
    return vector_store


def load_existing_db(uri=MILVUS_URI):
    """
    Load an existing vector store from the local Milvus database specified by the URI.

    Args:
        uri (str, optional): Path to the local milvus db. Defaults to MILVUS_URI.

    Returns:
        vector_store: The vector store created
    """
    # Load an existing vector store
    vector_store = Milvus(
        collection_name="IT_support",
        embedding_function = get_embedding_function(),
        connection_args={"uri": uri},
    )
    print("Vector Store Loaded")
    return vector_store

if __name__ == '__main__':
    pass