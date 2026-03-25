# Memory Handling Service with Entity, Summary, and Vector Memory

import json
import os
from datetime import datetime
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from utils.config import CHROMA_PATH, EMBEDDING_MODEL, VECTOR_MEMORY_COLLECTION

MEMORY_FILE = "data/memory/student_memory.json"

# Initialize Chroma client for vector memory
chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
chroma_embedding_function = SentenceTransformerEmbeddingFunction(
    model_name=EMBEDDING_MODEL
)


def _sanitize_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Chroma metadata only supports primitive values, so serialize richer data."""
    sanitized = {}
    for key, value in metadata.items():
        if isinstance(value, (str, int, float, bool)) or value is None:
            sanitized[key] = value
        else:
            sanitized[key] = json.dumps(value)
    return sanitized


def _restore_metadata(metadata: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    restored = {}
    for key, value in (metadata or {}).items():
        if not isinstance(value, str):
            restored[key] = value
            continue

        try:
            restored[key] = json.loads(value)
        except json.JSONDecodeError:
            restored[key] = value

    return restored


@dataclass
class StudentEntityMemory:
    """Structured entity memory for student information"""
    student_id: str
    name: Optional[str] = None
    program: Optional[str] = None  # MSc, BTech, MBA
    year: Optional[str] = None  # 1st, 2nd, final year
    department: Optional[str] = None
    ongoing_issues: List[str] = None
    courses_interested: List[str] = None
    created_at: str = None
    updated_at: Optional[str] = None

    def __post_init__(self):
        if self.ongoing_issues is None:
            self.ongoing_issues = []
        if self.courses_interested is None:
            self.courses_interested = []
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.updated_at is None:
            self.updated_at = datetime.now().isoformat()

    def to_dict(self):
        return asdict(self)


@dataclass
class SummaryMemory:
    """Keep conversations manageable with summaries"""
    student_id: str
    conversation_id: str
    summary: str
    key_topics: List[str]
    timestamp: str
    conversation_length: int  # number of turns
    last_updated: str = None

    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now().isoformat()

    def to_dict(self):
        return asdict(self)


class MemoryManager:
    """Manages all three types of memory: Entity, Summary, and Vector"""

    def __init__(self):
        # Create or get vector memory collection
        self.vector_collection = chroma_client.get_or_create_collection(
            name=VECTOR_MEMORY_COLLECTION,
            metadata={"hnsw:space": "cosine"},
            embedding_function=chroma_embedding_function,
        )

    def load_memory(self) -> Dict:
        """Load student memory JSON"""
        if not os.path.exists(MEMORY_FILE):
            return {}
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)

    def save_memory(self, data: Dict):
        """Save updated memory"""
        os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)
        with open(MEMORY_FILE, "w") as f:
            json.dump(data, f, indent=4)

    # ========== ENTITY MEMORY ==========
    def get_entity_memory(self, student_id: str) -> Optional[StudentEntityMemory]:
        """Retrieve student entity memory"""
        memory = self.load_memory()
        if student_id in memory and "entity" in memory[student_id]:
            data = memory[student_id]["entity"]
            return StudentEntityMemory(**data)
        return None

    def create_entity_memory(self, student_id: str, name: str) -> StudentEntityMemory:
        """Create new entity memory for student"""
        entity = StudentEntityMemory(student_id=student_id, name=name)
        memory = self.load_memory()
        if student_id not in memory:
            memory[student_id] = {}
        memory[student_id]["entity"] = entity.to_dict()
        self.save_memory(memory)
        return entity

    def update_entity_memory(self, student_id: str, **kwargs) -> StudentEntityMemory:
        """Update specific fields in entity memory"""
        entity = self.get_entity_memory(student_id) or StudentEntityMemory(
            student_id=student_id
        )
        for key, value in kwargs.items():
            if hasattr(entity, key):
                if key in ["ongoing_issues", "courses_interested"] and isinstance(
                    value, list
                ):
                    setattr(entity, key, value)
                elif key not in ["ongoing_issues", "courses_interested"]:
                    setattr(entity, key, value)
        entity.updated_at = datetime.now().isoformat()
        memory = self.load_memory()
        if student_id not in memory:
            memory[student_id] = {}
        memory[student_id]["entity"] = entity.to_dict()
        self.save_memory(memory)
        return entity

    # ========== SUMMARY MEMORY ==========
    def get_conversation_summary(
        self, student_id: str, conversation_id: str
    ) -> Optional[SummaryMemory]:
        """Retrieve conversation summary"""
        memory = self.load_memory()
        if (
            student_id in memory
            and "summaries" in memory[student_id]
            and conversation_id in memory[student_id]["summaries"]
        ):
            data = memory[student_id]["summaries"][conversation_id]
            return SummaryMemory(**data)
        return None

    def save_conversation_summary(
        self,
        student_id: str,
        conversation_id: str,
        summary: str,
        key_topics: List[str],
        conversation_length: int,
    ) -> SummaryMemory:
        """Save conversation summary after conversation ends"""
        summary_obj = SummaryMemory(
            student_id=student_id,
            conversation_id=conversation_id,
            summary=summary,
            key_topics=key_topics,
            timestamp=datetime.now().isoformat(),
            conversation_length=conversation_length,
        )
        memory = self.load_memory()
        if student_id not in memory:
            memory[student_id] = {}
        if "summaries" not in memory[student_id]:
            memory[student_id]["summaries"] = {}
        memory[student_id]["summaries"][conversation_id] = summary_obj.to_dict()
        self.save_memory(memory)
        return summary_obj

    def get_all_summaries(self, student_id: str) -> List[SummaryMemory]:
        """Get all conversation summaries for a student"""
        memory = self.load_memory()
        summaries = []
        if student_id in memory and "summaries" in memory[student_id]:
            for summary_data in memory[student_id]["summaries"].values():
                summaries.append(SummaryMemory(**summary_data))
        return summaries

    # ========== VECTOR MEMORY ==========
    def add_to_vector_memory(
        self,
        student_id: str,
        content: str,
        metadata_type: str,  # "doubt", "interest", "elective"
        metadata: Optional[Dict] = None,
    ) -> str:
        """Store content in vector memory with semantic search capability"""
        if metadata is None:
            metadata = {}
        metadata["student_id"] = student_id
        metadata["type"] = metadata_type
        metadata["timestamp"] = datetime.now().isoformat()
        metadata = _sanitize_metadata(metadata)

        doc_id = f"{student_id}_{metadata_type}_{int(datetime.now().timestamp())}"
        self.vector_collection.add(
            ids=[doc_id],
            documents=[content],
            metadatas=[metadata],
        )
        return doc_id

    def search_vector_memory(
        self, student_id: str, query: str, n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Search student's long-term vector memory"""
        try:
            results = self.vector_collection.query(
                query_texts=[query],
                where={"student_id": student_id},
                n_results=n_results,
            )

            if not results["documents"] or not results["documents"][0]:
                return []

            formatted_results = []
            for i, doc in enumerate(results["documents"][0]):
                formatted_results.append(
                    {
                        "content": doc,
                        "metadata": (
                            _restore_metadata(results["metadatas"][0][i])
                            if results["metadatas"]
                            else {}
                        ),
                        "distance": (
                            results["distances"][0][i] if results["distances"] else 0
                        ),
                    }
                )
            return formatted_results
        except Exception as e:
            print(f"Error searching vector memory: {e}")
            return []

    def get_vector_memory_by_type(
        self, student_id: str, memory_type: str
    ) -> List[Dict[str, Any]]:
        """Get all vector memories of specific type for a student"""
        try:
            results = self.vector_collection.get(
                where={"$and": [{"student_id": student_id}, {"type": memory_type}]}
            )
            if not results["documents"]:
                return []

            formatted_results = []
            for i, doc in enumerate(results["documents"]):
                formatted_results.append(
                    {
                        "id": results["ids"][i],
                        "content": doc,
                        "metadata": (
                            _restore_metadata(results["metadatas"][i])
                            if results["metadatas"]
                            else {}
                        ),
                    }
                )
            return formatted_results
        except Exception as e:
            print(f"Error retrieving vector memory: {e}")
            return []

    def get_complete_context(self, student_id: str) -> Dict[str, Any]:
        """Get complete memory context for a student"""
        entity = self.get_entity_memory(student_id)
        summaries = self.get_all_summaries(student_id)
        vector_interests = self.get_vector_memory_by_type(student_id, "interest")
        vector_doubts = self.get_vector_memory_by_type(student_id, "doubt")

        return {
            "entity": entity.to_dict() if entity else None,
            "summaries": [s.to_dict() for s in summaries],
            "academic_interests": vector_interests,
            "previous_doubts": vector_doubts,
        }


# Singleton instance
_memory_manager = None


def get_memory_manager() -> MemoryManager:
    """Get or create memory manager instance"""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager
