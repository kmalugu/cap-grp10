# Embeddings Utility

from functools import lru_cache

from langchain_huggingface import HuggingFaceEmbeddings

from utils.config import EMBEDDING_MODEL


@lru_cache(maxsize=1)
def get_embeddings():
    """
    Load embedding model
    """
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
