from bs4 import BeautifulSoup
import requests
from langchain.schema import Document
from langchain.document_loaders import RecursiveUrlLoader

CORPUS_SOURCE = 'https://www.csusb.edu/its'

def load_documents_from_web():
    """Load and clean documents from a web source using RecursiveUrlLoader."""
    loader = RecursiveUrlLoader(
        url=CORPUS_SOURCE,
        prevent_outside=True,  # Added missing argument
        base_url=CORPUS_SOURCE # Added missing argument
    )
    raw_documents = loader.load()

    # Ensure documents are cleaned
    cleaned_documents = []
    for doc in raw_documents:
        cleaned_text = clean_text_from_html(doc.page_content)
        cleaned_documents.append(Document(page_content=cleaned_text, metadata=doc.metadata))

    return cleaned_documents

def clean_text_from_html(html_content):
    """Clean HTML content to extract main text."""
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
    """Further clean the text by removing extra whitespace and new lines."""
    lines = (line.strip() for line in text.splitlines())
    cleaned_lines = [line for line in lines if line]
    return '\n'.join(cleaned_lines)

# Example usage
if __name__ == "__main__":
    documents = load_documents_from_web()
    for doc in documents:
        print(doc.page_content)
