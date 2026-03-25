#!/usr/bin/env python3
"""
Memory System Usage Examples

This script demonstrates how to use the new multi-layered memory system
with Entity Memory, Summary Memory, and Vector Memory.

Run the backend first:
    python -m uvicorn backend.main:app --reload
    
Then run this script:
    python examples/examples_memory_usage.py
"""

import requests
import json
from typing import Dict, List

BASE_URL = "http://localhost:8000"


def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


class MemorySystemDemo:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.students = {}

    # ========== Entity Memory Examples ==========

    def demo_create_student_entity(self):
        """Demo: Create and update entity memory for a new student"""
        print_section("DEMO 1: Entity Memory - Creating Student Profile")

        student_id = "student_001"
        conversation_id = "conv_001"

        # Simulate first interaction where student introduces themselves
        message = "Hi, my name is Priya Sharma. I'm an MSc student in Computer Science, currently in my 1st year at the CS department. I'm really interested in Machine Learning and artificial intelligence. My main issue right now is selecting the right electives for next semester."

        print(f"Student Message: {message}\n")

        response = requests.post(
            f"{self.base_url}/chat/",
            json={
                "user_id": student_id,
                "conversation_id": conversation_id,
                "message": message,
                "end_conversation": False,
            },
        )

        print(f"Assistant Response: {response.json()['response']}\n")

        # Retrieve the student profile to see extracted entity memory
        print("Student Profile (Entity Memory Extracted):")
        profile = requests.get(f"{self.base_url}/chat/student/{student_id}/profile")
        print(json.dumps(profile.json()["entity"], indent=2))

    def demo_manual_entity_update(self):
        """Demo: Manually update student entity information"""
        print_section("DEMO 2: Entity Memory - Manual Update")

        student_id = "student_002"

        # Manually create/update student profile
        updates = {
            "name": "Rajesh Kumar",
            "program": "BTech",
            "year": "2nd",
            "department": "Electrical Engineering",
            "ongoing_issues": ["lab_equipment_access", "report_writing"],
            "courses_interested": ["Power Systems", "Control Systems", "VLSI"],
        }

        print(f"Updating student profile with: {json.dumps(updates, indent=2)}\n")

        response = requests.post(
            f"{self.base_url}/chat/student/{student_id}/entity", json=updates
        )

        print(f"Update Response: {json.dumps(response.json(), indent=2)}")

    # ========== Summary Memory Examples ==========

    def demo_multi_turn_conversation(self):
        """Demo: Multi-turn conversation that gets summarized"""
        print_section(
            "DEMO 3: Summary Memory - Multi-turn Conversation & Summarization"
        )

        student_id = "student_003"
        conversation_id = "conv_003"

        messages = [
            "Hi! I'm Arun, 1st year MSc student in Data Science. I want to discuss my course selection.",
            "Should I take Deep Learning or NLP as my main elective?",
            "I'm more interested in practical applications. Which one has better project opportunities?",
            "What about doing both? Is that possible in the curriculum?",
            "Okay, I'll go with Deep Learning then. Thanks for the guidance!",
        ]

        print("Simulating multi-turn conversation:")
        print("-" * 40)

        for i, msg in enumerate(messages, 1):
            print(f"\nTurn {i} - Student: {msg}")

            response = requests.post(
                f"{self.base_url}/chat/",
                json={
                    "user_id": student_id,
                    "conversation_id": conversation_id,
                    "message": msg,
                    "end_conversation": (i == len(messages)),  # End on last message
                },
            )

            print(f"Assistant: {response.json()['response'][:100]}...")
            print(
                f"Conversation Processed: {response.json()['conversation_processed']}"
            )

        print("\n" + "-" * 40)
        print("\nRetrieving Conversation Summaries:")
        summaries = requests.get(
            f"{self.base_url}/chat/student/{student_id}/summaries"
        )
        print(json.dumps(summaries.json()["summaries"], indent=2))

    # ========== Vector Memory Examples ==========

    def demo_vector_memory_doubts(self):
        """Demo: Extract and retrieve student doubts from vector memory"""
        print_section("DEMO 4: Vector Memory - Previous Doubts")

        student_id = "student_004"
        conversation_id = "conv_004"

        print("Conversation with multiple doubts:")
        print("-" * 40)

        doubts_conversation = [
            "Hi, I'm studying ML algorithms and I'm confused about gradient descent optimization.",
            "How do backpropagation work in neural networks?",
            "What's the difference between supervised and unsupervised learning?",
            "Should I learn TensorFlow or PyTorch first?",
        ]

        for i, msg in enumerate(doubts_conversation, 1):
            print(f"\nTurn {i}: {msg}")

            response = requests.post(
                f"{self.base_url}/chat/",
                json={
                    "user_id": student_id,
                    "conversation_id": conversation_id,
                    "message": msg,
                    "end_conversation": (i == len(doubts_conversation)),
                },
            )

        # Retrieve extracted doubts
        print("\n" + "-" * 40)
        print("\nExtracted Doubts (Vector Memory):")
        doubts = requests.get(
            f"{self.base_url}/chat/student/{student_id}/doubts"
        )
        for doubt in doubts.json()["doubts"]:
            print(f"  • {doubt['content']}")
            print(f"    Topics: {doubt['metadata'].get('topic', [])}\n")

    def demo_vector_memory_interests(self):
        """Demo: Extract and retrieve student interests from vector memory"""
        print_section("DEMO 5: Vector Memory - Academic Interests")

        student_id = "student_005"
        conversation_id = "conv_005"

        print("Conversation revealing academic interests:")
        print("-" * 40)

        interests_conversation = [
            "I'm very passionate about Natural Language Processing and its applications in chatbots.",
            "I'm also interested in Computer Vision, especially for medical image analysis.",
            "Deep Learning is something I want to specialize in.",
            "I'd love to work on recommendation systems using AI.",
        ]

        for i, msg in enumerate(interests_conversation, 1):
            print(f"\nTurn {i}: {msg}")

            response = requests.post(
                f"{self.base_url}/chat/",
                json={
                    "user_id": student_id,
                    "conversation_id": conversation_id,
                    "message": msg,
                    "end_conversation": (i == len(interests_conversation)),
                },
            )

        # Retrieve extracted interests
        print("\n" + "-" * 40)
        print("\nExtracted Interests (Vector Memory):")
        interests = requests.get(
            f"{self.base_url}/chat/student/{student_id}/interests"
        )
        for interest in interests.json()["interests"]:
            print(f"  • {interest['content']}")
            print(f"    Topics: {interest['metadata'].get('topic', [])}\n")

    def demo_semantic_search(self):
        """Demo: Use semantic search to find relevant memories"""
        print_section("DEMO 6: Vector Memory - Semantic Search")

        student_id = "student_006"
        conversation_ids = ["conv_006_a", "conv_006_b", "conv_006_c"]

        # Simulate conversations with various topics
        conversations = [
            ["I'm interested in artificial intelligence applications"],
            ["How can I prepare for machine learning interviews?"],
            ["Tell me about the latest AI research in computer vision"],
        ]

        print("Storing multiple conversations with different topics:")
        for conv_id, conv_messages in zip(conversation_ids, conversations):
            for msg in conv_messages:
                requests.post(
                    f"{self.base_url}/chat/",
                    json={
                        "user_id": student_id,
                        "conversation_id": conv_id,
                        "message": msg,
                        "end_conversation": True,
                    },
                )

        # Now search for similar interests
        print("\nSearching for memories related to 'deep learning applications':")
        profile = requests.get(f"{self.base_url}/chat/student/{student_id}/profile")
        print(f"Found {len(profile.json()['academic_interests'])} interests")

    def demo_complete_context(self):
        """Demo: Get complete student context from all memory types"""
        print_section("DEMO 7: Complete Student Context")

        student_id = "student_007"

        # Set up student with entity info
        requests.post(
            f"{self.base_url}/chat/student/{student_id}/entity",
            json={
                "name": "Neha Singh",
                "program": "MBA",
                "year": "1st",
                "department": "Management",
                "ongoing_issues": ["business_analytics", "market_research"],
                "courses_interested": ["Data Analytics", "Business Intelligence"],
            },
        )

        # Have a conversation
        requests.post(
            f"{self.base_url}/chat/",
            json={
                "user_id": student_id,
                "conversation_id": "conv_007",
                "message": "I'm interested in understanding business analytics and how to apply data science in strategic decision making.",
                "end_conversation": True,
            },
        )

        # Retrieve complete profile
        print("Complete Student Profile:")
        profile = requests.get(f"{self.base_url}/chat/student/{student_id}/profile")
        print(json.dumps(profile.json(), indent=2))

    def run_all_demos(self):
        """Run all demonstration examples"""
        print("\n" + "=" * 60)
        print("MEMORY SYSTEM DEMONSTRATION")
        print("=" * 60)
        print("\nThis demo shows all features of the multi-layered memory system:")
        print("1. Entity Memory (Student Information)")
        print("2. Summary Memory (Conversation Summaries)")
        print("3. Vector Memory (Doubts, Interests, Electives)")

        try:
            self.demo_create_student_entity()
            self.demo_manual_entity_update()
            self.demo_multi_turn_conversation()
            self.demo_vector_memory_doubts()
            self.demo_vector_memory_interests()
            self.demo_semantic_search()
            self.demo_complete_context()

            print_section("All Demos Complete!")
            print(
                "✓ Entity Memory demonstrated\n"
                "✓ Summary Memory demonstrated\n"
                "✓ Vector Memory (Doubts) demonstrated\n"
                "✓ Vector Memory (Interests) demonstrated\n"
                "✓ Semantic Search demonstrated\n"
                "✓ Complete Context demonstrated"
            )

        except requests.exceptions.ConnectionError:
            print("\n❌ Error: Could not connect to the API server")
            print("Make sure to start the backend first:")
            print("  python -m uvicorn backend.main:app --reload")
        except Exception as e:
            print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    demo = MemorySystemDemo()
    demo.run_all_demos()
