# Caching Service for Chat Responses

from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import json
import hashlib


class CacheEntry:
    """Single cache entry with TTL support"""
    def __init__(self, content: Dict, ttl_seconds: int = 3600):
        self.content = content
        self.created_at = datetime.now()
        self.ttl = timedelta(seconds=ttl_seconds)
        self.access_count = 0
        self.last_accessed = datetime.now()

    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        return datetime.now() - self.created_at > self.ttl

    def access(self) -> Dict:
        """Get content and update access info"""
        self.access_count += 1
        self.last_accessed = datetime.now()
        return self.content


class ConversationCache:
    """Cache for conversation history and responses"""
    def __init__(self):
        self.conversations: Dict[str, list] = {}  # user_id -> list of messages
        self.response_cache: Dict[str, CacheEntry] = {}  # query hash -> cached response

    def add_conversation_turn(self, user_id: str, role: str, content: str):
        """Add a turn to conversation history"""
        if user_id not in self.conversations:
            self.conversations[user_id] = []
        
        self.conversations[user_id].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })

    def get_conversation_history(self, user_id: str) -> list:
        """Get conversation history for a user"""
        return self.conversations.get(user_id, [])

    def clear_conversation(self, user_id: str):
        """Clear conversation history for a user"""
        if user_id in self.conversations:
            del self.conversations[user_id]

    def get_cached_response(self, query: str, user_id: str) -> Optional[Dict]:
        """Get cached response if available and not expired"""
        query_hash = self._hash_query(query, user_id)
        
        if query_hash in self.response_cache:
            entry = self.response_cache[query_hash]
            if not entry.is_expired():
                return entry.access()
            else:
                # Remove expired entry
                del self.response_cache[query_hash]
        
        return None

    def cache_response(self, query: str, user_id: str, response: Dict, ttl_seconds: int = 3600):
        """Cache a response"""
        query_hash = self._hash_query(query, user_id)
        self.response_cache[query_hash] = CacheEntry(response, ttl_seconds)

    def _hash_query(self, query: str, user_id: str) -> str:
        """Create hash of query + user_id for caching"""
        combined = f"{user_id}:{query.lower().strip()}"
        return hashlib.md5(combined.encode()).hexdigest()

    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        total_entries = len(self.response_cache)
        active_entries = sum(1 for entry in self.response_cache.values() if not entry.is_expired())
        total_accesses = sum(entry.access_count for entry in self.response_cache.values())
        
        return {
            "total_entries": total_entries,
            "active_entries": active_entries,
            "expired_entries": total_entries - active_entries,
            "total_accesses": total_accesses,
            "conversations": len(self.conversations)
        }

    def clear_expired(self):
        """Remove all expired entries"""
        expired_keys = [
            key for key, entry in self.response_cache.items()
            if entry.is_expired()
        ]
        for key in expired_keys:
            del self.response_cache[key]
        return len(expired_keys)


# Global conversation cache instance
_conversation_cache = None


def get_conversation_cache() -> ConversationCache:
    """Get or create conversation cache instance"""
    global _conversation_cache
    if _conversation_cache is None:
        _conversation_cache = ConversationCache()
    return _conversation_cache
