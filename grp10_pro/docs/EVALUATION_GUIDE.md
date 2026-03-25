# Evaluation Guide

Complete guide to running all evaluation tests for the University AI Assistant.

## Quick Start

### Run All Evaluations
```bash
python evaluation/run_all_evaluations.py
```

### Run Individual Tests

#### A. RAG Evaluation
Test document retrieval quality (Precision@k, Recall@k, Hit Rate)
```bash
python evaluation/rag_evaluation.py
```

**What it measures:**
- Precision@1, @3, @5: How many retrieved docs are relevant
- Recall@1, @3, @5: What percentage of relevant docs are retrieved
- Hit Rate: Whether any relevant doc is in top k

**Example output:**
```
Query: 'What are prerequisites for DS201?'
  @1: Precision=1.000 | Recall=0.500 | Hit=1
  @3: Precision=0.667 | Recall=1.000 | Hit=1
  @5: Precision=0.400 | Recall=1.000 | Hit=1
```

---

#### B. Advising Quality Evaluation
Test response quality across multiple dimensions
```bash
python evaluation/advising_quality_simple.py
```

**Dimensions evaluated (0-100):**
- **Relevance**: Does response answer the query?
- **Correctness**: Are facts accurate?
- **Personalization**: Does it consider student context?
- **Non-Hallucination**: No invented facts?
- **Policy Adherence**: Follows university policies?

**Overall Score**: Weighted average of all dimensions

**Example output:**
```
Query: "What are prerequisites for DS201?"
  Relevance: 85.50/100
  Correctness: 100.00/100
  Personalization: 50.00/100
  Non-Hallucination: 95.00/100
  Policy Adherence: 80.00/100
  >>> OVERALL: 84.10/100
```

---

#### C. Response Quality Tests
Test response similarity to reference answers
```bash
python evaluation/response_quality.py
```

**Metrics:**
- **ROUGE-L**: Longest common subsequence overlap (0-100)
- **BERTScore**: Word and semantic similarity (0-100)

**Example output:**
```
[Course Prerequisites]
  ROUGE-L: 75.50/100
  BERTScore: 82.30/100
  Avg Score: 78.90/100
```

---

#### D. Latency Tests
Measure response time for critical operations
```bash
python evaluation/latency_tests.py
```

**Operations tested:**
- Timetable query
- Course lookup
- RAG document retrieval
- LLM chat response

**Example output:**
```
✅ timetable_query: 145.23ms
✅ course_lookup: 89.50ms
✅ rag_retrieval: 234.67ms
✅ llm_response: 1245.34ms

Stats (successful only):
  Min: 89.50ms
  Max: 1245.34ms
  Avg: 628.94ms
```

---

## Requirements

Make sure backend is running:
```bash
# Terminal 1
uvicorn backend.main:app --reload

# Terminal 2
python evaluation/rag_evaluation.py
```

## Test Data

All tests include sample queries and responses. Modify `test_cases` in each file to use your own data.

### RAG Evaluation Test Queries
```python
test_queries = [
    ("What are prerequisites for DS201?", ["course_ds201", "prerequisites"]),
    ("When does registration close?", ["registration_deadline", "academic_calendar"]),
    ("Library opening hours", ["library_hours"]),
]
```

### Advising Quality Test Cases
```python
test_cases = [
    {
        "query": "What are prerequisites for DS201?",
        "response": "DS201 requires CS101 and MATH201...",
        "student_context": {"program": "Computer Science", "year": 2},
        "facts_correct": {"DS201 needs CS101": True, ...}
    }
]
```

---

## Understanding Scores

### RAG Evaluation
- **Precision@k**: How many top-k results are correct (focus on quality)
- **Recall@k**: What % of all relevant results are in top-k (focus on coverage)
- **Hit Rate@k**: Binary - did we find ANY relevant result in top-k

**Good targets:**
- Precision@1 > 0.7 (most relevant is correct)
- Recall@3 > 0.8 (find ~80% of relevant results)
- Hit Rate@5 = 1.0 (always find at least one in top 5)

### Advising Quality
**Weight breakdown:**
- Relevance: 25%
- Correctness: 25%
- Personalization: 15%
- Non-Hallucination: 20%
- Policy Adherence: 15%

**Score interpretation:**
- 90-100: Excellent
- 80-89: Good
- 70-79: Fair
- < 70: Needs improvement

### Response Quality
**ROUGE-L:**
- Measures word overlap and order
- > 75: Good similarity
- > 85: Excellent similarity

**BERTScore:**
- Measures semantic similarity
- > 75: Good match
- > 85: Excellent match

### Latency
**Acceptable ranges:**
- Timetable query: < 200ms
- Course lookup: < 150ms
- RAG retrieval: < 300ms
- LLM response: < 2000ms

---

## Running Tests in Sequence

```bash
# 1. Start backend
uvicorn backend.main:app --reload

# 2. In another terminal, run evaluations
python evaluation/rag_evaluation.py
python evaluation/advising_quality_simple.py
python evaluation/response_quality.py
python evaluation/latency_tests.py
```

Or create a batch script to run all:

**run_evaluations.sh (Linux/Mac)**
```bash
#!/bin/bash
echo "Running all evaluations..."
python evaluation/rag_evaluation.py
echo ""
python evaluation/advising_quality_simple.py
echo ""
python evaluation/response_quality.py
echo ""
python evaluation/latency_tests.py
```

## Troubleshooting

### Connection error to backend
```
Error: Cannot connect to localhost:8000
```
**Solution**: Make sure backend is running with `uvicorn backend.main:app --reload`

### No retrieval results in RAG evaluation
```
Retrieved 0 documents for query
```
**Solutions:**
1. Check if RAG documents are indexed: `python create_index.py`
2. Verify document files exist in `data/rag_docs/`
3. Check FAISS index in `models/faiss_index/`

### Low quality scores
- Check if test cases match your actual use cases
- Modify test data to be more realistic
- Adjust weights in evaluation functions

---

## Customizing Evaluations

Edit test cases in each file:

**rag_evaluation.py**:
```python
test_queries = [
    ("Your query here", ["relevant_doc1", "relevant_doc2"]),
]
```

**advising_quality_simple.py**:
```python
test_cases = [
    {
        "query": "Your question",
        "response": "Your response",
        "expected_topics": ["topic1", "topic2"],
        "facts_correct": {"fact1": True, "fact2": False},
    }
]
```

**latency_tests.py**:
```python
tester.test_timetable_query("your_student_id")
tester.test_course_lookup("YOUR_COURSE_CODE")
```

---

## Output Files

Evaluations print results to console. To save results:

```bash
# Redirect to file
python evaluation/rag_evaluation.py > results/rag_eval.txt

# Or modify the code to write to CSV/JSON
```

---

## Summary of Evaluation Types

| **Type** | **Measures** | **Run** | **Time** |
|----------|------------|--------|----------|
| RAG | Document retrieval quality | `rag_evaluation.py` | ~30s |
| Advising | Response quality dimensions | `advising_quality_simple.py` | ~5s |
| Quality | Similarity to references | `response_quality.py` | ~2s |
| Latency | Response times | `latency_tests.py` | ~10s |

**Total evaluation time: ~1 minute**

---

**All evaluations are complete and ready to use!** ✅
