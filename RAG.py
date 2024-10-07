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

MILVUS_URI = './milvus/milvus_vector.db'
MODEL_NAME = "sentence-transformers/all-mpnet-base-v2"

# Get the embedding function
def get_embedding_function():
    return HuggingFaceEmbeddings(model_name=MODEL_NAME)

# Main functions, calls all other functions to get an answer
def RAG_answer(query):
    # Defines Cohere Model (MistralAI would not work with WEB loaded data)
    #model = ChatCohere()
    model = ChatMistralAI(model='open-mistral-7b')
    print("Model Loaded")

    prompt = create_prompt()

    """
    ideally vector_store shouldn't get initialized everytime the answer is requested, will be changed later
    """

    vector_store = load_exisiting_db(uri=MILVUS_URI)

    retriever = vector_store.as_retriever()

    document_chain = create_stuff_documents_chain(model, prompt)
    print("Document Chain Created")

    retrieval_chain = create_retrieval_chain(retriever, document_chain)
    print("Retrieval Chain Created")
    
    repsonse = retrieval_chain.invoke({"input": f"{query}"})
    print("Response Generated")

    return repsonse["answer"]

# Creates the PromptTemplate for the AI model
def create_prompt():
    # Defines the prompt template text
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

# Initialize and creates the vector_store through milvus
def initialize_milvus(uri: str=MILVUS_URI):
    # Create the embeddings (THIS METHOD IS DEPRECATED UPDATE TO USE LANGCHAIN-HUGGINGFACE INSTEAD OF LANGCHAIN_COMMUNITY)
    # Look into using a special embedding for COHERE, but for now the 'sentence-transformers/all-MiniLM-L6-v2' works fine
    embeddings = get_embedding_function()
    print("Embeddings Loaded")

    documents = load_documents_from_web()
    print("Documents Loaded")

    docs = split_documents(documents=documents)
    print("Documents Splitting completed")

    vector_store = create_vector_store(docs, embeddings, uri)

    return vector_store

# Load webpages and store the page contents
def load_documents_from_web():
    loader = WebBaseLoader(web_paths=
        ["https://www.csusb.edu/its/" #, add more webpages in the future 
        ],
        )
    documents = loader.load()
    
    return documents

# Split doucments into chunks
def split_documents(documents):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,  # Split the text into chunks of 1000 characters
        chunk_overlap=300,  # Overlap the chunks by 300 characters
        is_separator_regex=False,  # Don't split on regex
    )
    docs = text_splitter.split_documents(documents)
    return docs

# creates vector store
def create_vector_store(docs, embeddings, uri):

    head = os.path.split(uri)
    os.makedirs(head[0], exist_ok=True)

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