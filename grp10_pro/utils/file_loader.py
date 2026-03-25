import os
from langchain_community.document_loaders import TextLoader, PyPDFLoader

def load_documents(folder_path):
    """
    Load all txt and pdf documents from rag_docs folder
    """
    documents = []

    for file in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file)

        if file.endswith(".txt"):
            loader = TextLoader(file_path, encoding="utf-8")
            documents.extend(loader.load())

        elif file.endswith(".pdf"):
            loader = PyPDFLoader(file_path)
            documents.extend(loader.load())

    return documents