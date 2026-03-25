"""
Simple RAG Evaluation Module
Evaluates: Precision@k, Recall@k, Hit Rate for document retrieval
"""

try:
    from backend.services.retriever import retrieve_documents
    # Try a quick test to see if backend is really available
    BACKEND_AVAILABLE = True
except Exception:
    BACKEND_AVAILABLE = False


def evaluate_rag():
    """Evaluate RAG system with test queries"""
    
    test_queries = [
        ("What are prerequisites for DS201?", ["prerequisite", "ds201"]),
        ("When does registration close?", ["registration", "deadline"]),
        ("Library opening hours", ["library", "hours"]),
        ("How to pay fees?", ["fees", "payment"]),
        ("PhD requirements", ["phd", "requirement"]),
    ]
    
    print("\n" + "="*70)
    print("RAG EVALUATION - PRECISION@K, RECALL@K, HIT RATE")
    print("="*70 + "\n")
    
    all_metrics = {"@1": [], "@3": [], "@5": []}
    
    # Check if backend is actually available
    backend_available = BACKEND_AVAILABLE
    if backend_available:
        print("Using live RAG backend...\n")
    else:
        print("Backend not available - using mock data\n")
    
    for query, relevant_keywords in test_queries:
        print(f"Query: '{query}'")
        print(f"Looking for: {relevant_keywords}")
        
        # Retrieve documents
        retrieved = []
        if backend_available:
            try:
                retrieved = retrieve_documents(query, k=5)
            except Exception as e:
                print(f"  Error retrieving from backend: {e}")
                print(f"  Falling back to mock data")
                backend_available = False
        
        if not retrieved and not backend_available:
            # Mock data for testing when backend isn't available
            try:
                from langchain_core.documents import Document
            except ImportError:
                from langchain.schema import Document
            
            retrieved = [
                Document(page_content=f"Sample result {i} for query: {query}", metadata={"source": f"doc_{i}"})
                for i in range(5)
            ]
        
        if not retrieved:
            print(f"  No documents retrieved\n")
            continue
        
        # Extract text from documents for keyword matching
        retrieved_text = " ".join([doc.page_content.lower() for doc in retrieved])
        
        # Check how many relevant keywords are in retrieved documents
        keywords_found = sum(1 for keyword in relevant_keywords if keyword.lower() in retrieved_text)
        
        # Calculate metrics
        for k in [1, 3, 5]:
            # For simplified evaluation: check if any keyword in top-k docs
            top_k_text = " ".join([doc.page_content.lower() for doc in retrieved[:k]])
            keywords_in_topk = sum(1 for keyword in relevant_keywords if keyword.lower() in top_k_text)
            
            # Simple metrics - all based on keyword presence
            p = 1.0 if keywords_in_topk > 0 else 0.0  # Precision
            r = keywords_in_topk / len(relevant_keywords) if relevant_keywords else 0  # Recall
            h = 1 if keywords_in_topk > 0 else 0  # Hit rate
            
            all_metrics[f"@{k}"].append((p, r, h))
            print(f"  @{k}: Precision={p:.3f} | Recall={r:.3f} | Hit={h}")
        
        print()
    
    # Print summary
    print("="*70)
    print("SUMMARY")
    print("="*70)
    for k in ["@1", "@3", "@5"]:
        if all_metrics[k]:
            precisions, recalls, hits = zip(*all_metrics[k])
            print(f"{k}: Avg Precision={sum(precisions)/len(precisions):.3f} | "
                  f"Avg Recall={sum(recalls)/len(recalls):.3f} | "
                  f"Avg Hit={sum(hits)/len(hits):.3f}")
        else:
            print(f"{k}: No results")


if __name__ == "__main__":
    evaluate_rag()
