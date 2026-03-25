"""
Simple Advising Quality Evaluation
Evaluates: Relevance, Correctness, Personalization, Non-hallucination, Policy Adherence
"""


def score_relevance(query, response, expected_topics=None):
    """Score relevance (0-100)"""
    expected_topics = expected_topics or []
    
    query_words = set(query.lower().split())
    response_lower = response.lower()
    
    # Coverage of query terms
    coverage = sum(1 for word in query_words if word in response_lower) / len(query_words) if query_words else 0
    
    # Coverage of expected topics
    topic_coverage = sum(1 for topic in expected_topics if topic.lower() in response_lower) / len(expected_topics) if expected_topics else 0.5
    
    score = (coverage * 0.5 + topic_coverage * 0.5) * 100
    return min(100, max(0, score))


def score_correctness(response, facts_correct):
    """Score correctness (0-100)"""
    if not facts_correct:
        return 50
    
    correct = sum(1 for is_correct in facts_correct.values() if is_correct)
    return (correct / len(facts_correct)) * 100


def score_personalization(response, student_context=None):
    """Score personalization (0-100)"""
    student_context = student_context or {}
    
    mentions = 0
    for key, value in student_context.items():
        if value and str(value).lower() in response.lower():
            mentions += 1
    
    # Bonus for personal pronouns
    personal_words = ['your', 'you', 'based on your']
    mentions += sum(1 for word in personal_words if word in response.lower())
    
    total_possible = len(student_context) + 3
    return (mentions / total_possible * 100) if total_possible > 0 else 50


def score_non_hallucination(response, verified_facts=None):
    """Score non-hallucination (0-100)"""
    verified_facts = verified_facts or []
    
    hallucination_flags = ['always', 'never', 'guaranteed', 'definitely will']
    penalties = sum(1 for flag in hallucination_flags if flag in response.lower())
    
    # Bonus for uncertainty markers
    uncertainty = ['might', 'could', 'may', 'suggests', 'appears']
    bonus = sum(1 for word in uncertainty if word in response.lower()) * 5
    
    score = 100 - (penalties * 20) + bonus
    return min(100, max(0, score))


def score_policy_adherence(response, policy_keywords=None):
    """Score policy adherence (0-100)"""
    policy_keywords = policy_keywords or []
    
    mentions = sum(1 for keyword in policy_keywords if keyword.lower() in response.lower())
    score = (mentions / len(policy_keywords) * 100) if policy_keywords else 75
    
    # Bonus for official references
    official_refs = ['official', 'registrar', 'advising office', 'policy handbook']
    if any(ref in response.lower() for ref in official_refs):
        score = min(100, score + 10)
    
    return score


def evaluate_response(query, response, expected_topics=None, facts_correct=None, 
                     student_context=None, verified_facts=None, policy_keywords=None):
    """Evaluate a single response"""
    
    relevance = score_relevance(query, response, expected_topics)
    correctness = score_correctness(response, facts_correct)
    personalization = score_personalization(response, student_context)
    non_hallucination = score_non_hallucination(response, verified_facts)
    policy_adherence = score_policy_adherence(response, policy_keywords)
    
    # Weighted average
    overall = (
        relevance * 0.25 +
        correctness * 0.25 +
        personalization * 0.15 +
        non_hallucination * 0.20 +
        policy_adherence * 0.15
    )
    
    return {
        'relevance': round(relevance, 2),
        'correctness': round(correctness, 2),
        'personalization': round(personalization, 2),
        'non_hallucination': round(non_hallucination, 2),
        'policy_adherence': round(policy_adherence, 2),
        'overall': round(overall, 2)
    }


def evaluate_advising():
    """Evaluate advising responses"""
    
    test_cases = [
        {
            "query": "What are prerequisites for DS201?",
            "response": "DS201 requires CS101 and MATH201. You should have basic Python knowledge.",
            "expected_topics": ["prerequisites", "CS101", "MATH201"],
            "facts_correct": {"DS201 needs CS101": True, "DS201 needs MATH201": True},
            "student_context": {"program": "Computer Science", "year": 2},
            "verified_facts": ["CS101", "MATH201"],
            "policy_keywords": ["prerequisites", "requirements"]
        },
        {
            "query": "When does registration close?",
            "response": "Fall registration closes on August 15th. International students have until August 20th.",
            "expected_topics": ["deadline", "registration", "date"],
            "facts_correct": {"August 15": True, "International Aug 20": True},
            "student_context": {"name": "John"},
            "verified_facts": ["August 15", "Registrar"],
            "policy_keywords": ["deadline", "registration"]
        },
    ]
    
    print("\n" + "="*70)
    print("ADVISING QUALITY EVALUATION")
    print("Metrics: Relevance | Correctness | Personalization | Non-Hallucination | Policy")
    print("="*70 + "\n")
    
    all_scores = []
    
    for i, test in enumerate(test_cases, 1):
        print(f"[{i}] Query: {test['query']}")
        print(f"    Response: {test['response'][:80]}...\n")
        
        scores = evaluate_response(**test)
        all_scores.append(scores)
        
        print(f"    Relevance: {scores['relevance']}/100")
        print(f"    Correctness: {scores['correctness']}/100")
        print(f"    Personalization: {scores['personalization']}/100")
        print(f"    Non-Hallucination: {scores['non_hallucination']}/100")
        print(f"    Policy Adherence: {scores['policy_adherence']}/100")
        print(f"    >>> OVERALL: {scores['overall']}/100\n")
    
    # Summary
    print("="*70)
    print("SUMMARY")
    print("="*70)
    avg_scores = {}
    for key in ['relevance', 'correctness', 'personalization', 'non_hallucination', 'policy_adherence', 'overall']:
        avg = sum(s[key] for s in all_scores) / len(all_scores)
        avg_scores[key] = avg
        print(f"{key.title()}: {avg:.2f}/100")


if __name__ == "__main__":
    evaluate_advising()
