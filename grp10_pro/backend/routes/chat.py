from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List, Dict
from backend.services.llm import get_llm
from backend.services.memory import get_memory_manager
from backend.services.memory_graph import process_conversation_for_memory
from backend.services.cache import get_conversation_cache
from backend.services.retriever import retrieve_documents
from backend.guardrails import get_guardrails_manager, check_user_input
import json

router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatRequest(BaseModel):
    user_id: str
    conversation_id: str
    message: str
    end_conversation: Optional[bool] = False


class ContextSettings(BaseModel):
    """Context window settings"""
    context_length: int = 5  # Number of previous messages to include
    rag_enabled: bool = True
    memory_enabled: bool = True
    use_cache: bool = True


class ChatResponse(BaseModel):
    response: str
    student_context: Optional[Dict] = None
    conversation_processed: bool = False
    source: str  # "cache", "memory", "rag", or "model"
    is_from_docs: bool  # Whether answer came from documentation


conversation_cache = {}  # Temp cache for multi-turn conversations
context_settings: Dict[str, ContextSettings] = {}  # user_id -> settings


@router.post("/")
def chat(req: ChatRequest) -> ChatResponse:
    """
    Enhanced chat endpoint with intelligent pipeline:
    User Prompt → Cache → Memory → RAG → Model (with disclaimer if not found)
    """
    # ========== STEP 0: CHECK GUARDRAILS ==========
    guardrails = get_guardrails_manager()
    is_violation, violation_message = check_user_input(req.message)
    
    if is_violation:
        print(f"🚫 GUARDRAIL VIOLATION: {violation_message[:80]}")
        return ChatResponse(
            response=violation_message,
            source="guardrail",
            is_from_docs=False
        )
    
    llm = get_llm()
    memory_manager = get_memory_manager()
    conv_cache = get_conversation_cache()

    # Load or use default settings for this user
    if req.user_id not in context_settings:
        context_settings[req.user_id] = ContextSettings()
    user_settings = context_settings[req.user_id]

    # Initialize conversation cache if needed
    if req.conversation_id not in conversation_cache:
        conversation_cache[req.conversation_id] = []

    # ========== STEP 1: CHECK CACHE ==========
    source = "cache"
    is_from_docs = False
    cached_response = None

    if user_settings.use_cache:
        cached_response = conv_cache.get_cached_response(req.message, req.user_id)
        if cached_response:
            conv_cache.add_conversation_turn(req.user_id, "user", req.message)
            conv_cache.add_conversation_turn(req.user_id, "assistant", cached_response["response"])
            return ChatResponse(
                response=cached_response["response"],
                source="cache",
                is_from_docs=cached_response.get("is_from_docs", False)
            )

    # ========== STEP 2: LOAD STUDENT CONTEXT ==========
    source = "memory"
    entity_memory = memory_manager.get_entity_memory(req.user_id)
    relevant_vector_memories = memory_manager.search_vector_memory(
        req.user_id, req.message, n_results=3
    )

    # Build context for LLM
    student_context = f"""Student Information:"""
    if entity_memory:
        student_context += f"""
Name: {entity_memory.name}
Program: {entity_memory.program}
Year: {entity_memory.year}
Department: {entity_memory.department}
Current Issues: {', '.join(entity_memory.ongoing_issues) if entity_memory.ongoing_issues else 'None'}
Interested Courses: {', '.join(entity_memory.courses_interested) if entity_memory.courses_interested else 'None'}"""
    else:
        student_context += "(New student - no previous information)"

    # Add relevant past context
    if relevant_vector_memories:
        student_context += "\n\nRelevant Past Interactions:"
        for i, memory in enumerate(relevant_vector_memories, 1):
            mem_type = memory["metadata"].get("type", "unknown")
            student_context += f"\n{i}. [{mem_type.upper()}] {memory['content']}"

    # ========== STEP 3: TRY RAG ==========
    rag_context = ""
    rag_documents = []
    
    if user_settings.rag_enabled:
        try:
            rag_documents = retrieve_documents(req.message, k=5)
            if rag_documents:
                rag_context = "\n\nDocumentation Context:\n"
                for doc in rag_documents:
                    rag_context += f"\n- {doc.page_content[:300]}\n"
                source = "rag"
                is_from_docs = True
                print(f"✅ RAG found {len(rag_documents)} documents for query: {req.message[:50]}")
            else:
                print(f"❌ RAG found 0 documents for query: {req.message[:50]}")
        except Exception as e:
            print(f"❌ RAG retrieval error: {e}")
            rag_documents = []

    # ========== STEP 4: BUILD RESPONSE WITH CONTEXT ==========
    conversation_cache[req.conversation_id].append(
        {"role": "user", "content": req.message}
    )

    # Build the prompt
    if rag_context and rag_documents:
        # Found documentation - PRIORITY: use documentation
        prompt = f"""You are a helpful university assistant. Answer ONLY from the provided documentation.

{student_context}

{rag_context}

Question: {req.message}

Instructions:
- Answer DIRECTLY from the documentation above
- If the answer is in the documentation, provide it clearly
- Do NOT use generic knowledge
- Be specific and cite the documentation

Answer:"""
        try:
            response = llm.invoke(prompt)
            source = "rag"
            is_from_docs = True
            print(f"✅ Generated response from RAG documentation")
        except Exception as e:
            print(f"❌ LLM error: {e}")
            response = "Sorry, I encountered an error processing your question. Please try again."
    else:
        # No documentation found - use model with disclaimer
        prompt = f"""You are a helpful university assistant. The student is asking about something not found in our documentation.

{student_context}

Question: {req.message}

Important: This answer is NOT from our official documentation. 

Start your response with:
"📌 This information is not in our official documentation, but I can say:"

Then provide your response based on general knowledge only.

Answer:"""
        try:
            response = llm.invoke(prompt)
            source = "model"
            is_from_docs = False
            print(f"✅ Generated response from LLM (not in docs)")
        except Exception as e:
            print(f"❌ LLM error: {e}")
            response = "Sorry, I encountered an error processing your question. Please try again."

    # Add assistant response to conversation
    conversation_cache[req.conversation_id].append(
        {"role": "assistant", "content": response}
    )

    # Add to cache for future use
    if user_settings.use_cache:
        conv_cache.cache_response(
            req.message, 
            req.user_id,
            {
                "response": response,
                "source": source,
                "is_from_docs": is_from_docs
            },
            ttl_seconds=3600
        )

    # Process conversation and store memories if conversation ends or reaches threshold
    processed = False
    memory_info = ""
    
    # Process memory more aggressively - after every 2-4 messages or on end
    messages_count = len(conversation_cache[req.conversation_id])
    should_process = (
        req.end_conversation or 
        messages_count >= 4  # Process after 2 exchanges (4 messages)
    )
    
    if should_process and messages_count > 0:
        try:
            process_result = process_conversation_for_memory(
                student_id=req.user_id,
                conversation_id=req.conversation_id,
                messages=conversation_cache[req.conversation_id],
            )
            processed = True
            
            # Build memory info for logging
            if process_result.get("extracted_entities"):
                entities = [k for k, v in process_result["extracted_entities"].items() if v]
                if entities:
                    memory_info = f"✅ Stored: {', '.join(entities)}"
            
            print(f"📝 MEMORY PROCESSED for {req.user_id}: {memory_info}")
            
            # Clear conversation cache after processing
            if req.end_conversation:
                del conversation_cache[req.conversation_id]
        except Exception as e:
            print(f"❌ Memory processing error: {e}")
            memory_info = f"Error: {str(e)[:50]}"

    return ChatResponse(
        response=response,
        student_context={"entity": entity_memory.to_dict() if entity_memory else None},
        conversation_processed=processed,
        source=source,
        is_from_docs=is_from_docs,
    )


@router.get("/student/{student_id}/profile")
def get_student_profile(student_id: str):
    """Get complete memory profile for a student"""
    memory_manager = get_memory_manager()
    complete_context = memory_manager.get_complete_context(student_id)
    return complete_context


@router.post("/student/{student_id}/entity")
def update_student_entity(student_id: str, updates: Dict):
    """Manually update student entity memory"""
    memory_manager = get_memory_manager()
    updated = memory_manager.update_entity_memory(student_id, **updates)
    return {"status": "updated", "entity": updated.to_dict()}


@router.get("/student/{student_id}/summaries")
def get_student_summaries(student_id: str):
    """Get all conversation summaries for a student"""
    memory_manager = get_memory_manager()
    summaries = memory_manager.get_all_summaries(student_id)
    return {"summaries": [s.to_dict() for s in summaries]}


@router.get("/student/{student_id}/interests")
def get_student_interests(student_id: str):
    """Get student's academic interests from vector memory"""
    memory_manager = get_memory_manager()
    interests = memory_manager.get_vector_memory_by_type(student_id, "interest")
    return {"interests": interests}


@router.get("/student/{student_id}/doubts")
def get_student_doubts(student_id: str):
    """Get student's previous doubts from vector memory"""
    memory_manager = get_memory_manager()
    doubts = memory_manager.get_vector_memory_by_type(student_id, "doubt")
    return {"doubts": doubts}


# ========== CONTEXT WINDOW & CACHE MANAGEMENT ==========

@router.get("/user/{user_id}/conversation-history")
def get_conversation_history(user_id: str):
    """Get conversation history for a user (all turns)"""
    conv_cache = get_conversation_cache()
    history = conv_cache.get_conversation_history(user_id)
    return {"user_id": user_id, "conversation_history": history}


@router.post("/user/{user_id}/clear-conversation")
def clear_user_conversation(user_id: str):
    """Clear conversation history for a user"""
    conv_cache = get_conversation_cache()
    conv_cache.clear_conversation(user_id)
    return {"status": "cleared", "user_id": user_id}


@router.get("/user/{user_id}/context-settings")
def get_context_settings(user_id: str):
    """Get context window settings for a user"""
    if user_id not in context_settings:
        context_settings[user_id] = ContextSettings()
    
    settings = context_settings[user_id]
    return {
        "user_id": user_id,
        "context_length": settings.context_length,
        "rag_enabled": settings.rag_enabled,
        "memory_enabled": settings.memory_enabled,
        "use_cache": settings.use_cache,
    }


@router.post("/user/{user_id}/context-settings")
def update_context_settings(user_id: str, settings: ContextSettings):
    """Update context window settings for a user"""
    context_settings[user_id] = settings
    return {
        "status": "updated",
        "user_id": user_id,
        "settings": {
            "context_length": settings.context_length,
            "rag_enabled": settings.rag_enabled,
            "memory_enabled": settings.memory_enabled,
            "use_cache": settings.use_cache,
        }
    }


@router.get("/cache-stats")
def get_cache_statistics():
    """Get cache statistics"""
    conv_cache = get_conversation_cache()
    return conv_cache.get_cache_stats()


@router.post("/clear-expired-cache")
def clear_expired_cache():
    """Clear expired cache entries"""
    conv_cache = get_conversation_cache()
    cleared = conv_cache.clear_expired()
    return {"status": "success", "cleared_entries": cleared}


# ========== DEBUG ENDPOINTS ==========

@router.post("/debug/test-rag")
def debug_test_rag(query: str):
    """Test RAG retrieval directly"""
    try:
        docs = retrieve_documents(query, k=5)
        return {
            "query": query,
            "documents_found": len(docs),
            "documents": [
                {
                    "content": doc.page_content[:200],
                    "full_content": doc.page_content,
                    "metadata": doc.metadata if hasattr(doc, 'metadata') else {}
                }
                for doc in docs
            ]
        }
    except Exception as e:
        return {
            "query": query,
            "error": str(e),
            "documents_found": 0,
            "documents": []
        }


@router.post("/debug/test-full-pipeline")
def debug_test_pipeline(req: ChatRequest):
    """Test the full chat pipeline with debug info"""
    llm = get_llm()
    memory_manager = get_memory_manager()
    conv_cache = get_conversation_cache()
    
    # Step 3: RAG
    rag_docs = retrieve_documents(req.message, k=5)
    rag_context = ""
    if rag_docs:
        rag_context = "\n\nDocumentation Context:\n"
        for doc in rag_docs:
            rag_context += f"\n- {doc.page_content[:300]}\n"
    
    return {
        "query": req.message,
        "rag_documents_found": len(rag_docs),
        "rag_context_generated": len(rag_context) > 0,
        "rag_context_preview": rag_context[:500] if rag_context else "No context",
        "documents": [
            {
                "preview": doc.page_content[:100].replace('\n', ' '),
                "full": doc.page_content
            }
            for doc in rag_docs
        ]
    }


# ========== MEMORY DEBUG ENDPOINTS ==========

@router.get("/debug/memory/{student_id}")
def debug_get_student_memory(student_id: str):
    """Get complete memory for a student (debug)"""
    memory_manager = get_memory_manager()
    try:
        complete_context = memory_manager.get_complete_context(student_id)
        return {
            "student_id": student_id,
            "entity_memory": complete_context.get("entity"),
            "summaries": complete_context.get("summaries"),
            "academic_interests": complete_context.get("academic_interests"),
            "previous_doubts": complete_context.get("previous_doubts"),
        }
    except Exception as e:
        return {
            "student_id": student_id,
            "error": str(e),
            "entity_memory": None,
            "summaries": [],
            "academic_interests": [],
            "previous_doubts": [],
        }


@router.post("/debug/memory/{student_id}/update")
def debug_update_student_memory(student_id: str, name: str = None, program: str = None, year: str = None, department: str = None):
    """Manually update student memory (debug)"""
    memory_manager = get_memory_manager()
    try:
        updates = {}
        if name:
            updates["name"] = name
        if program:
            updates["program"] = program
        if year:
            updates["year"] = year
        if department:
            updates["department"] = department
        
        if updates:
            entity = memory_manager.update_entity_memory(student_id, **updates)
            return {
                "status": "success",
                "student_id": student_id,
                "updated_fields": list(updates.keys()),
                "entity": entity.to_dict()
            }
        else:
            return {
                "status": "error",
                "message": "No fields to update"
            }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@router.post("/debug/memory/{student_id}/add-vector")
def debug_add_vector_memory(student_id: str, content: str, memory_type: str = "doubt"):
    """Manually add vector memory (debug)"""
    memory_manager = get_memory_manager()
    try:
        doc_id = memory_manager.add_to_vector_memory(
            student_id=student_id,
            content=content,
            metadata_type=memory_type
        )
        return {
            "status": "success",
            "student_id": student_id,
            "memory_type": memory_type,
            "doc_id": doc_id,
            "content": content
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@router.get("/debug/memory/{student_id}/raw-file")
def debug_get_raw_memory_file(student_id: str):
    """Get raw memory JSON file (debug)"""
    memory_manager = get_memory_manager()
    try:
        all_memory = memory_manager.load_memory()
        if student_id in all_memory:
            return {
                "status": "found",
                "student_id": student_id,
                "memory": all_memory[student_id]
            }
        else:
            return {
                "status": "not_found",
                "student_id": student_id,
                "memory": None
            }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }