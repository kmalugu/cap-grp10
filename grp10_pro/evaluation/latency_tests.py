"""
Latency Tests
Measures response time for various operations:
- Timetable query time
- Course lookup speed
- RAG retrieval latency
- LLM response latency
"""

import time
import requests
from typing import Dict, List


class LatencyTester:
    """Tests system latency"""
    
    def __init__(self, api_url="http://127.0.0.1:8000"):
        self.api_url = api_url
        self.results = []
    
    def test_timetable_query(self, student_id: str) -> Dict:
        """Measure timetable query latency"""
        print("Testing timetable query latency...")
        
        start = time.time()
        try:
            response = requests.get(f"{self.api_url}/timetable/{student_id}")
            latency = time.time() - start
            success = response.status_code == 200
        except Exception as e:
            latency = time.time() - start
            success = False
            print(f"  Error: {e}")
        
        result = {
            'test': 'timetable_query',
            'latency_ms': round(latency * 1000, 2),
            'success': success
        }
        self.results.append(result)
        print(f"  Latency: {result['latency_ms']}ms")
        return result
    
    def test_course_lookup(self, course_code: str) -> Dict:
        """Measure course lookup latency"""
        print("Testing course lookup latency...")
        
        start = time.time()
        try:
            response = requests.get(f"{self.api_url}/course/{course_code}")
            latency = time.time() - start
            success = response.status_code == 200
        except Exception as e:
            latency = time.time() - start
            success = False
            print(f"  Error: {e}")
        
        result = {
            'test': 'course_lookup',
            'latency_ms': round(latency * 1000, 2),
            'success': success
        }
        self.results.append(result)
        print(f"  Latency: {result['latency_ms']}ms")
        return result
    
    def test_rag_retrieval(self, query: str) -> Dict:
        """Measure RAG retrieval latency"""
        print(f"Testing RAG retrieval latency for: '{query}'...")
        
        start = time.time()
        try:
            response = requests.post(
                f"{self.api_url}/rag/search",
                json={"query": query}
            )
            latency = time.time() - start
            success = response.status_code == 200
        except Exception as e:
            latency = time.time() - start
            success = False
            print(f"  Error: {e}")
        
        result = {
            'test': 'rag_retrieval',
            'latency_ms': round(latency * 1000, 2),
            'success': success
        }
        self.results.append(result)
        print(f"  Latency: {result['latency_ms']}ms")
        return result
    
    def test_chat_response(self, user_id: str, message: str) -> Dict:
        """Measure chat/LLM response latency"""
        print(f"Testing LLM response latency for: '{message}'...")
        
        payload = {
            "user_id": user_id,
            "conversation_id": f"test_{int(time.time())}",
            "message": message
        }
        
        start = time.time()
        try:
            response = requests.post(f"{self.api_url}/chat/", json=payload)
            latency = time.time() - start
            success = response.status_code == 200
        except Exception as e:
            latency = time.time() - start
            success = False
            print(f"  Error: {e}")
        
        result = {
            'test': 'llm_response',
            'latency_ms': round(latency * 1000, 2),
            'success': success
        }
        self.results.append(result)
        print(f"  Latency: {result['latency_ms']}ms")
        return result
    
    def print_summary(self):
        """Print latency test summary"""
        if not self.results:
            print("No results to summarize")
            return
        
        print("\n" + "="*70)
        print("LATENCY TEST SUMMARY")
        print("="*70 + "\n")
        
        for result in self.results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}: {result['latency_ms']}ms")
        
        # Calculate stats
        successful = [r for r in self.results if r['success']]
        if successful:
            latencies = [r['latency_ms'] for r in successful]
            avg_latency = sum(latencies) / len(latencies)
            max_latency = max(latencies)
            min_latency = min(latencies)
            
            print(f"\nStats (successful only):")
            print(f"  Min: {min_latency}ms")
            print(f"  Max: {max_latency}ms")
            print(f"  Avg: {avg_latency:.2f}ms")


def run_latency_tests():
    """Run all latency tests"""
    
    print("\n" + "="*70)
    print("LATENCY TESTING")
    print("Measuring response times for key operations")
    print("="*70 + "\n")
    
    tester = LatencyTester()
    
    # Check if API is available
    print("Checking if API is available at http://127.0.0.1:8000...")
    try:
        requests.get("http://127.0.0.1:8000/", timeout=2)
        api_available = True
    except Exception:
        api_available = False
        print("⚠️  API is not running. Skipping live latency tests.")
        print("    To run these tests, start the backend with: python backend/main.py\n")
    
    if api_available:
        # Run tests
        tester.test_timetable_query("student_001")
        print()
        
        tester.test_course_lookup("CS101")
        print()
        
        tester.test_rag_retrieval("What are prerequisites for Data Science?")
        print()
        
        tester.test_chat_response("student_001", "What are the library hours?")
        print()
        
        tester.print_summary()
    else:
        print("="*70)
        print("LATENCY TEST SUMMARY")
        print("="*70)
        print("\nNo tests run (API unavailable)")
        print("\nTo run latency tests:")
        print("  1. Start the backend: python backend/main.py")
        print("  2. Run this script: python evaluation/latency_tests.py")
    
    return tester.results if api_available else []


if __name__ == "__main__":
    run_latency_tests()
