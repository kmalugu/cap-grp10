# Vector Search Logic

import os

from langchain_community.vectorstores import FAISS

from utils.config import FAISS_PATH
from utils.embeddings import get_embeddings


# Cache vectorstore to avoid reloading
_vectorstore_cache = None


def load_vectorstore():
    """
    Load FAISS vector DB  
    """
    global _vectorstore_cache
    
    if _vectorstore_cache is not None:
        return _vectorstore_cache
    
    try:
        if not os.path.exists(FAISS_PATH):
            print(f"Warning: FAISS index not found at {FAISS_PATH}")
            return None
        
        embeddings = get_embeddings()
        db = FAISS.load_local(FAISS_PATH, embeddings, allow_dangerous_deserialization=True)
        _vectorstore_cache = db
        return db
    except Exception as e:
        print(f"Error loading vectorstore: {e}")
        return None


def retrieve_documents(query, k=3):
    """
    Retrieve top-k relevant documents
    """
    try:
        db = load_vectorstore()
        if db is None:
            return []
        docs = db.similarity_search(query, k=k)
        return docs
    except Exception as e:
        print(f"Error retrieving documents: {e}")
        return []
