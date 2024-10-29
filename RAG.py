CORPUS_SOURCE = 'https://www.csusb.edu/its'

import os
from dotenv import load_dotenv
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.schema import Document
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
#from langchain_mistralai import MistralAIEmbeddings
from langchain_mistralai.chat_models import ChatMistralAI
#from langchain_cohere import ChatCohere
from langchain_milvus import Milvus
from langchain_community.document_loaders import WebBaseLoader, RecursiveUrlLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.chains import create_retrieval_chain
from langchain_huggingface import HuggingFaceEmbeddings
from pymilvus import connections, utility
from requests.exceptions import HTTPError
from httpx import HTTPStatusError

load_dotenv()
MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY")

# MILVUS_URI = "./milvus/milvus_vector.db"
MILVUS_URI = "milvus/milvus_vector.db"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

def get_embedding_function():
    """
    returns embedding function for the model

    Returns:
        embedding function
    """
    embedding_function = HuggingFaceEmbeddings(model_name=MODEL_NAME)
    return embedding_function


def query_rag(query):
    """
    Entry point for the RAG model to generate an answer to a given query

    This function initializes the RAG model, sets up the necessary components such as the prompt template, vector store, 
    retriever, document chain, and retrieval chain, and then generates a response to the provided query.

    Args:
        query (str): The query string for which an answer is to be generated.
    
    Returns:
        str: The answer to the query
    """
    # Define the model
    model = ChatMistralAI(model='open-mistral-7b', temperature = 0)
    print("Model Loaded")

    prompt = create_prompt()

    # Load the vector store and create the retriever
    vector_store = load_existing_db(uri=MILVUS_URI)
    retriever = vector_store.as_retriever(search_type="mmr", search_kwargs={"score_threshold": 0.7, "k":5})
    try:
        document_chain = create_stuff_documents_chain(model, prompt)
        print("Document Chain Created")

        retrieval_chain = create_retrieval_chain(retriever, document_chain)
        print("Retrieval Chain Created")
    
        # Generate a response to the query
        response = retrieval_chain.invoke({"input": f"{query}"})
    except HTTPStatusError as e:
        print(f"HTTPStatusError: {e}")
        if e.response.status_code == 429:
            return "I am currently experiencing high traffic. Please try again later.", []
        return "I am unable to answer this question at the moment. Please try again later.", []
    
    # logic to add sources to the response
    max_relevant_sources = 4 # number of sources at most to be added to the response
    all_sources = ""
    sources = []
    count = 1
    for i in range(max_relevant_sources):
        try:
            source = response["context"][i].metadata["source"]
            # check if the source is already added to the list
            if source not in sources:
                sources.append(source)
                all_sources += f"[Source {count}]({source}), "
                count += 1
        except IndexError: # if there are no more sources to add
            break
    all_sources = all_sources[:-2] # remove the last comma and space
    response["answer"] += f"\n\nSources: {all_sources}"
    print("Response Generated")

    return response["answer"], sources



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

    # Create a PromptTemplate instance with the defined template and input variables
    # prompt = PromptTemplate(
    #     template=PROMPT_TEMPLATE, input_variables=["context", "question"]
    # )

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
    documents = loader.load()
    
    return documents

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
        is_separator_regex=False,  # Don't split on regex
    )
    # Split the documents into chunks
    docs = text_splitter.split_documents(documents)
    return docs

def vector_store_check(uri):
    # Create the directory if it does not exist
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
