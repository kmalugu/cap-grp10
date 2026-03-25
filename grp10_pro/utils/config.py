import os

from dotenv import load_dotenv

load_dotenv()

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
MODEL_NAME = GEMINI_MODEL
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
)
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.2"))

# Paths
RAG_DOCS_PATH = "data/rag_docs/"
FAISS_PATH = "models/faiss_index/"
CHROMA_PATH = "models/chroma_db"
VECTOR_MEMORY_COLLECTION = "student_long_term_memory_hf"
