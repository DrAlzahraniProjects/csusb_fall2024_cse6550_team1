import os
from dotenv import load_dotenv
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import PromptTemplate
#from langchain_mistralai import MistralAIEmbeddings
#from langchain_mistralai.chat_models import ChatMistralAI
from langchain_cohere import ChatCohere
from langchain_milvus import Milvus
from langchain_community.document_loaders import WebBaseLoader, RecursiveUrlLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.chains import create_retrieval_chain
from langchain_community.embeddings import HuggingFaceEmbeddings

load_dotenv()
MISTRAL_API_KEY=os.environ.get("MISTRAL_API_KEY")
COHERE_API_KEY=os.environ.get("COHERE_API_KEY")

# Main functions, calls all other functions to get an answer
def RAG_answer(query):
    # Defines Cohere Model (MistralAI would not work with WEB loaded data)
    model = ChatCohere()

    prompt = create_prompt()

    """
    ideally vector_store shouldn't get initialized everytime the answer is requested, will be changed later
    """
    vector_store = initialize_milvus()

    retriever = vector_store.as_retriever()

    document_chain = create_stuff_documents_chain(model, prompt)
    retrieval_chain = create_retrieval_chain(retriever, document_chain)
    repsonse = retrieval_chain.invoke({"input": f"{query}"})

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

    return prompt

# Initialize and creates the vector_store through milvus
def initialize_milvus(model_name: str="sentence-transformers/all-MiniLM-L6-v2", URI: str='./milvus/milvus_vector.db'):
    # Create the embeddings (THIS METHOD IS DEPRECATED UPDATE TO USE LANGCHAIN-HUGGINGFACE INSTEAD OF LANGCHAIN_COMMUNITY)
    # Look into using a special embedding for COHERE, but for now the 'sentence-transformers/all-MiniLM-L6-v2' works fine
    embeddings = HuggingFaceEmbeddings(model_name=model_name)

    documents = load_documents_from_web()

    docs = split_documents(documents=documents)

    vector_store = create_vector_store(docs, embeddings, URI)

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
    text_splitter = RecursiveCharacterTextSplitter()
    docs = text_splitter.split_documents(documents)
    return docs

# creates vector store
def create_vector_store(docs, embeddings, URI):
    vector_store = Milvus.from_documents(
        documents=docs,
        embedding=embeddings,
        collection_name="IT_support",
        connection_args={"uri": URI},
        drop_old=True,
    )

    return vector_store

if __name__ == '__main__':
    pass