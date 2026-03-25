# RAG Pipeline Logic (LangChain + FAISS)
from backend.services.llm import get_llm
from backend.services.retriever import retrieve_documents


def build_prompt(context, query):
    return f"""
You are an intelligent university assistant.

Answer ONLY from the provided context.
If answer is not found, say "I don't know based on available data."

Context:
{context}

Question:
{query}

Answer:
"""


def rag_answer(query):
    """
    Full RAG pipeline:
    1. Retrieve docs
    2. Build context
    3. Generate answer
    """
    llm = get_llm()

    # Step 1: Retrieve docs
    docs = retrieve_documents(query)

    # Step 2: Build context
    context = "\n\n".join([doc.page_content for doc in docs])

    # Step 3: Prompt
    prompt = build_prompt(context, query)

    # Step 4: LLM response
    response = llm.invoke(prompt)

    return response