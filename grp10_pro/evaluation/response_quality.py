"""
Response Quality Tests
Evaluates response quality using ROUGE-L and BERTScore
"""

from typing import List, Tuple


def rouge_l_score(reference: str, generated: str) -> float:
    """
    Simple ROUGE-L score (LCS-based)
    Measures longest common subsequence overlap
    Returns: 0-100 (percentage)
    """
    ref_words = reference.lower().split()
    gen_words = generated.lower().split()
    
    # Calculate LCS length
    def lcs_length(a, b):
        m, n = len(a), len(b)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if a[i-1] == b[j-1]:
                    dp[i][j] = dp[i-1][j-1] + 1
                else:
                    dp[i][j] = max(dp[i-1][j], dp[i][j-1])
        
        return dp[m][n]
    
    lcs = lcs_length(ref_words, gen_words)
    max_len = max(len(ref_words), len(gen_words))
    
    score = (lcs / max_len * 100) if max_len > 0 else 0
    return min(100, score)


def bertscore_similarity(reference: str, generated: str) -> float:
    """
    Simplified BERTScore-like similarity
    Measures word overlap and semantic similarity
    Returns: 0-100 (percentage)
    """
    ref_words = set(reference.lower().split())
    gen_words = set(generated.lower().split())
    
    if not ref_words or not gen_words:
        return 0
    
    # Jaccard similarity
    intersection = len(ref_words & gen_words)
    union = len(ref_words | gen_words)
    
    similarity = (intersection / union * 100) if union > 0 else 0
    return min(100, similarity)


def evaluate_response_quality(test_cases: List[dict]) -> dict:
    """
    Evaluate response quality for multiple test cases
    
    test_cases format:
    [
        {
            "reference": "Expected response",
            "generated": "Model's generated response",
            "name": "Test case name"
        }
    ]
    """
    
    results = []
    
    print("\n" + "="*70)
    print("RESPONSE QUALITY EVALUATION")
    print("Metrics: ROUGE-L | BERTScore")
    print("="*70 + "\n")
    
    for test in test_cases:
        reference = test.get("reference", "")
        generated = test.get("generated", "")
        name = test.get("name", "Test")
        
        rouge_l = rouge_l_score(reference, generated)
        bertscore = bertscore_similarity(reference, generated)
        
        avg_score = (rouge_l + bertscore) / 2
        
        result = {
            'name': name,
            'rouge_l': round(rouge_l, 2),
            'bertscore': round(bertscore, 2),
            'avg': round(avg_score, 2)
        }
        results.append(result)
        
        print(f"[{name}]")
        print(f"  Reference: {reference[:60]}...")
        print(f"  Generated: {generated[:60]}...")
        print(f"  ROUGE-L: {rouge_l:.2f}/100")
        print(f"  BERTScore: {bertscore:.2f}/100")
        print(f"  Avg Score: {avg_score:.2f}/100\n")
    
    # Summary
    print("="*70)
    print("SUMMARY")
    print("="*70)
    avg_rouge = sum(r['rouge_l'] for r in results) / len(results)
    avg_bert = sum(r['bertscore'] for r in results) / len(results)
    avg_overall = sum(r['avg'] for r in results) / len(results)
    
    print(f"Avg ROUGE-L: {avg_rouge:.2f}/100")
    print(f"Avg BERTScore: {avg_bert:.2f}/100")
    print(f"Avg Overall: {avg_overall:.2f}/100")
    print("="*70)
    
    return results


def run_response_quality_tests():
    """Run response quality tests"""
    
    test_cases = [
        {
            "name": "Course Prerequisites",
            "reference": "DS201 requires CS101 and MATH201 prerequisites",
            "generated": "To enroll in DS201, you must complete CS101 and MATH201"
        },
        {
            "name": "Registration Deadline",
            "reference": "Fall semester registration deadline is August 15",
            "generated": "The registration closes on August 15 for the fall term"
        },
        {
            "name": "Library Hours",
            "reference": "The library is open 8am to 10pm Monday through Friday",
            "generated": "Library hours are Monday-Friday from 8 to 10 in the morning and evening"
        },
    ]
    
    return evaluate_response_quality(test_cases)


if __name__ == "__main__":
    run_response_quality_tests()
