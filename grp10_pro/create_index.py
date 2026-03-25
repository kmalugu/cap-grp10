from utils.file_loader import load_documents
from utils.text_splitter import split_documents
from utils.embeddings import get_embeddings
from utils.config import RAG_DOCS_PATH, FAISS_PATH

from langchain_community.vectorstores import FAISS

# 1. Load documents
docs = load_documents(RAG_DOCS_PATH)

# 2. Split into chunks
chunks = split_documents(docs)

# 3. Create embeddings
embeddings = get_embeddings()

# 4. Create FAISS index
db = FAISS.from_documents(chunks, embeddings)

# 5. Save index
db.save_local(FAISS_PATH)

print("✅ FAISS index created successfully!")