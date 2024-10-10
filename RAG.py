import os
from dotenv import load_dotenv
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import PromptTemplate
#from langchain_mistralai import MistralAIEmbeddings
from langchain_mistralai.chat_models import ChatMistralAI
from langchain_cohere import ChatCohere
from langchain_milvus import Milvus
from langchain_community.document_loaders import WebBaseLoader, RecursiveUrlLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.chains import create_retrieval_chain
from langchain_huggingface import HuggingFaceEmbeddings
from pymilvus import connections, utility

load_dotenv()
MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY")
COHERE_API_KEY = os.environ.get("COHERE_API_KEY")
print(MISTRAL_API_KEY)
if MISTRAL_API_KEY is None:
    try:
        with open("../run/secrets/MISTRAL_API_KEY") as f:
            for l in f:
                print(l, " from secrets")
    except OSError:
        print("No Mistral API key found")

MILVUS_URI = "./milvus/milvus_vector.db"
MODEL_NAME = "sentence-transformers/all-MiniLM-L12-v2"


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
    model = ChatMistralAI(model='open-mistral-7b')
    print("Model Loaded")

    prompt = create_prompt()

    # Load the vector store and create the retriever
    vector_store = load_exisiting_db(uri=MILVUS_URI)
    retriever = vector_store.as_retriever()

    document_chain = create_stuff_documents_chain(model, prompt)
    print("Document Chain Created")

    retrieval_chain = create_retrieval_chain(retriever, document_chain)
    print("Retrieval Chain Created")

    # Generate a response to the query
    repsonse = retrieval_chain.invoke({"input": f"{query}"})
    print("Response Generated")

    return repsonse["answer"]


def create_prompt():
    """
    Create a prompt template for the RAG model

    Returns:
        PromptTemplate: The prompt template for the RAG model
    """
    # Define the prompt template
    PROMPT_TEMPLATE = """
    Human: You are an AI assistant, and provides answers to questions by using fact based and statistical information when possible.
    Use the following pieces of information to provide a concise answer to the question enclosed in <question> tags.
    Only use the information provided in the <context> tags.
    If you don't know the answer, just say that you don't know, don't try to make up an answer.
    <context>
    {context}
    </context>

    <question>
    {input}
    </question>

    The response should be specific and use statistics or numbers when possible.

    Assistant:"""

    # Create a PromptTemplate instance with the defined template and input variables
    prompt = PromptTemplate(
        template=PROMPT_TEMPLATE, input_variables=["context", "question"]
    )
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
    embeddings = get_embedding_function()
    print("Embeddings Loaded")
    documents = load_documents_from_web()
    print("Documents Loaded")

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
    loader = WebBaseLoader(web_paths=
        ["https://www.csusb.edu/its/" #, add more webpages in the future 
        ],
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


def create_vector_store(docs, embeddings, uri):
    """
    This function initializes a vector store using the provided documents and embeddings.
    It connects to a local Milvus database specified by the URI. If a collection named "IT_support" already exists,
    it loads the existing vector store; otherwise, it creates a new vector store and drops any existing one.

    Args:
        docs (list): A list of documents to be stored in the vector store.
        embeddings : A function or model that generates embeddings for the documents.
        uri (str): Path to the local milvus db

    Returns:
        vector_store: The vector store created
    """
    # Create the directory if it does not exist
    head = os.path.split(uri)
    os.makedirs(head[0], exist_ok=True)

    # Connect to the Milvus database
    connections.connect("default",uri=uri)

    # Check if the collection already exists
    if utility.has_collection("IT_support"):
        print("Collection already exists. Loading existing Vector Store.")
        # loading the existing vector store
        vector_store = Milvus(
            collection_name="IT_support",
            embedding_function=get_embedding_function(),
            connection_args={"uri": uri}
        )
    else:
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


def load_exisiting_db(uri=MILVUS_URI):
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