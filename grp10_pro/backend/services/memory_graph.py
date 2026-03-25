# LangGraph Workflow for Intelligent Memory Management

from typing import Dict, Any, List, TypedDict
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage
from backend.services.memory import get_memory_manager, StudentEntityMemory
from backend.services.llm import get_llm
import json


class ConversationState(TypedDict):
    """TypedDict state for LangGraph workflow"""
    student_id: str
    conversation_id: str
    messages: List[Dict[str, str]]
    current_turn: int
    extracted_entities: Dict[str, Any]
    conversation_topics: List[str]
    summary: str
    vector_memories_to_store: List[Dict[str, Any]]


def create_memory_graph():
    """Create LangGraph workflow for memory management"""

    llm = get_llm()
    memory_manager = get_memory_manager()

    # ========== NODES ==========

    def extract_entity_information(state: ConversationState) -> Dict[str, Any]:
        """Extract student entity information from conversation"""
        # Combine all messages for analysis
        conversation_text = "\n".join(
            [f"{msg['role']}: {msg['content']}" for msg in state["messages"]]
        )

        extraction_prompt = f"""
        Analyze this conversation and extract ANY student information mentioned, even if partial.
        Look for:
        - Student name (if mentioned)
        - Program (MSc, BTech, MBA, etc.)
        - Year (1st, 2nd, final year)
        - Department
        - Ongoing academic issues
        - Courses student is interested in
        - Any preferences or concerns mentioned
        
        Important: Extract EVERYTHING mentioned, even incomplete info. Use null only if truly not mentioned.
        
        Conversation:
        {conversation_text}
        
        Return ONLY valid JSON with these keys (use null for missing info):
        {{
            "name": null,
            "program": null,
            "year": null,
            "department": null,
            "ongoing_issues": [],
            "courses_interested": []
        }}
        """

        extracted_entities = {
            "name": None,
            "program": None,
            "year": None,
            "department": None,
            "ongoing_issues": [],
            "courses_interested": [],
        }

        try:
            response = llm.invoke(extraction_prompt)

            # Extract JSON from response - handle text before/after JSON
            json_str = response.strip()
            
            # Try to find JSON in markdown code blocks first
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()
            
            # Try to extract JSON if it's embedded in text
            if not json_str.startswith("{"):
                # Find the first { and last }
                start = json_str.find("{")
                end = json_str.rfind("}") + 1
                if start != -1 and end > start:
                    json_str = json_str[start:end].strip()

            extracted = json.loads(json_str)
            extracted_entities = extracted
            print(f"✅ Extracted entities: {extracted}")
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse entity extraction JSON | Error: {e}")
            print(f"   Response: {response[:200]}")
        except Exception as e:
            print(f"❌ Entity extraction error: {e}")

        return {"extracted_entities": extracted_entities}

    def identify_conversation_topics(state: ConversationState) -> Dict[str, Any]:
        """Identify main topics discussed"""
        conversation_text = "\n".join(
            [f"{msg['role']}: {msg['content']}" for msg in state["messages"]]
        )

        topic_prompt = f"""
        Identify the main topics/subjects discussed in this conversation.
        List them as a JSON array of strings, even if just one topic.
        
        Conversation:
        {conversation_text}
        
        Return ONLY valid JSON array like: ["topic1", "topic2", "topic3"]
        """

        conversation_topics = ["General"]

        try:
            response = llm.invoke(topic_prompt)

            json_str = response.strip()
            
            # Try to find JSON in markdown code blocks first
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()
            
            # Try to extract JSON if it's embedded in text
            if not json_str.startswith("["):
                # Find the first [ and last ]
                start = json_str.find("[")
                end = json_str.rfind("]") + 1
                if start != -1 and end > start:
                    json_str = json_str[start:end].strip()

            parsed_topics = json.loads(json_str)
            # Handle nested arrays - flatten if needed
            if isinstance(parsed_topics, list) and len(parsed_topics) > 0:
                if isinstance(parsed_topics[0], list):
                    # Flatten nested arrays
                    conversation_topics = [item for sublist in parsed_topics for item in sublist if item]
                else:
                    conversation_topics = parsed_topics
            
            if conversation_topics:
                print(f"✅ Identified topics: {conversation_topics}")
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse topics JSON | Error: {e}")
            print(f"   Response: {response[:200]}")
            # Extract topics manually from conversation
            if "library" in conversation_text.lower():
                conversation_topics = ["Library"]
            elif "course" in conversation_text.lower():
                conversation_topics = ["Courses"]
            else:
                conversation_topics = ["General"]
        except Exception as e:
            print(f"❌ Topic identification error: {e}")
            conversation_topics = ["General"]

        return {"conversation_topics": conversation_topics}

    def generate_conversation_summary(state: ConversationState) -> Dict[str, Any]:
        """Generate concise summary of conversation for manageable context"""
        conversation_text = "\n".join(
            [f"{msg['role']}: {msg['content']}" for msg in state["messages"]]
        )

        summary_prompt = f"""
        Briefly summarize this student advising conversation in 2-3 sentences.
        Focus on what the student asked and key advice given.
        
        Conversation:
        {conversation_text}
        
        Summary:
        """

        summary = "Student consultation"
        
        try:
            response = llm.invoke(summary_prompt).strip()
            summary = response if response else "Student consultation"
            print(f"✅ Generated summary: {summary[:100]}...")
        except Exception as e:
            print(f"❌ Summary generation error: {e}")
            summary = f"Conversation about {', '.join(state.get('conversation_topics', ['general topics']))}"

        return {"summary": summary}

    def extract_and_store_vector_memories(
        state: ConversationState,
    ) -> Dict[str, Any]:
        """Extract doubts, interests, and preferences for vector storage"""
        conversation_text = "\n".join(
            [f"{msg['role']}: {msg['content']}" for msg in state["messages"]]
        )

        vector_extraction_prompt = f"""
        Extract from this conversation:
        1. Academic doubts/questions asked (each as separate item)
        2. Academic interests mentioned
        3. Preferred electives or courses mentioned
        4. Any concerns or issues mentioned
        
        Conversation:
        {conversation_text}
        
        Return ONLY valid JSON:
        {{
            "doubts": ["doubt1", "doubt2"],
            "interests": ["interest1", "interest2"],
            "electives": ["elective1", "elective2"]
        }}
        """

        vector_memories_to_store = []

        try:
            response = llm.invoke(vector_extraction_prompt)

            json_str = response.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]

            extracted = json.loads(json_str)

            # Store each doubt, interest, and elective in vector memory
            for doubt in extracted.get("doubts", []):
                if doubt.strip():
                    vector_memories_to_store.append(
                        {
                            "content": doubt,
                            "type": "doubt",
                            "metadata": {"topic": state.get("conversation_topics", [])},
                        }
                    )

            for interest in extracted.get("interests", []):
                if interest.strip():
                    vector_memories_to_store.append(
                        {
                            "content": interest,
                            "type": "interest",
                            "metadata": {"topic": state.get("conversation_topics", [])},
                        }
                    )

            for elective in extracted.get("electives", []):
                if elective.strip():
                    vector_memories_to_store.append(
                        {
                            "content": elective,
                            "type": "elective",
                            "metadata": {"topic": state.get("conversation_topics", [])},
                        }
                    )

            if vector_memories_to_store:
                print(f"✅ Prepared {len(vector_memories_to_store)} vector memories")

        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse vector memories: {response} | Error: {e}")
        except Exception as e:
            print(f"❌ Vector memory extraction error: {e}")

        return {"vector_memories_to_store": vector_memories_to_store}

    def persist_all_memories(state: ConversationState) -> Dict[str, Any]:
        """Persist all extracted memories to the database"""
        try:
            # Update entity memory
            if any(state.get("extracted_entities", {}).values()):
                try:
                    memory_manager.update_entity_memory(
                        state["student_id"], **state.get("extracted_entities", {})
                    )
                    print(f"✅ Updated entity memory for {state['student_id']}")
                except Exception as e:
                    print(f"❌ Failed to update entity memory: {e}")

            # Save conversation summary
            if state.get("summary"):
                try:
                    memory_manager.save_conversation_summary(
                        student_id=state["student_id"],
                        conversation_id=state["conversation_id"],
                        summary=state.get("summary"),
                        key_topics=state.get("conversation_topics", []),
                        conversation_length=len(state.get("messages", [])),
                    )
                    print(f"✅ Saved conversation summary for {state['student_id']}")
                except Exception as e:
                    print(f"❌ Failed to save summary: {e}")

            # Store vector memories
            vector_memories = state.get("vector_memories_to_store", [])
            if vector_memories:
                stored_count = 0
                for memory in vector_memories:
                    try:
                        memory_manager.add_to_vector_memory(
                            student_id=state["student_id"],
                            content=memory["content"],
                            metadata_type=memory["type"],
                            metadata=memory.get("metadata", {}),
                        )
                        stored_count += 1
                    except Exception as e:
                        print(f"❌ Failed to store vector memory: {e}")
                
                if stored_count > 0:
                    print(f"✅ Stored {stored_count} vector memories for {state['student_id']}")
            else:
                print(f"⚠️  No vector memories to store for {state['student_id']}")

        except Exception as e:
            print(f"❌ Error in persist_all_memories: {e}")

        return {}

    # ========== BUILD GRAPH ==========
    workflow = StateGraph(ConversationState)

    workflow.add_node("extract_entities", extract_entity_information)
    workflow.add_node("identify_topics", identify_conversation_topics)
    workflow.add_node("summarize", generate_conversation_summary)
    workflow.add_node("extract_vectors", extract_and_store_vector_memories)
    workflow.add_node("persist", persist_all_memories)

    # Define edges
    workflow.set_entry_point("extract_entities")
    workflow.add_edge("extract_entities", "identify_topics")
    workflow.add_edge("identify_topics", "summarize")
    workflow.add_edge("summarize", "extract_vectors")
    workflow.add_edge("extract_vectors", "persist")
    workflow.add_edge("persist", END)

    return workflow.compile()


# Create the graph once at module load
memory_graph = create_memory_graph()


def process_conversation_for_memory(
    student_id: str,
    conversation_id: str,
    messages: List[Dict[str, str]],
) -> Dict[str, Any]:
    """
    Process a conversation to extract and store all types of memories.

    Args:
        student_id: ID of the student
        conversation_id: Unique conversation ID
        messages: List of messages in format [{"role": "user"/"assistant", "content": "..."}, ...]

    Returns:
        ProcessingResult with extracted memories
    """
    initial_state: ConversationState = {
        "student_id": student_id,
        "conversation_id": conversation_id,
        "messages": messages,
        "current_turn": 0,
        "extracted_entities": {},
        "conversation_topics": [],
        "summary": "",
        "vector_memories_to_store": [],
    }

    final_state = memory_graph.invoke(initial_state)

    return {
        "student_id": final_state.get("student_id"),
        "extracted_entities": final_state.get("extracted_entities", {}),
        "conversation_topics": final_state.get("conversation_topics", []),
        "summary": final_state.get("summary", ""),
        "vector_memories_stored": final_state.get("vector_memories_to_store", []),
    }
