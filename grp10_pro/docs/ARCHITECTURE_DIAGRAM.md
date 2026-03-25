# Visual Architecture & Data Flow

## Complete System Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                          STUDENT CHAT INTERFACE                              │
│                         (Enhanced Streamlit App)                             │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │ Student ID: [student_001_______]  Conversation ID: conv_123...    │    │
│  ├────────────────────────────────────────────────────────────────────┤    │
│  │                                                                    │    │
│  │ 👤 User: "What are the course prerequisites?"      [10:15 AM]   │    │
│  │                                                                    │    │
│  │ 🤖 Assistant: "Based on our documentation..."      [📚 From Doc]  │    │
│  │    The prerequisites are...                         [10:15:30 AM] │    │
│  │                                                                    │    │
│  │ 👤 User: "What about scholarships?"               [10:20 AM]    │    │
│  │                                                                    │    │
│  │ 🤖 Assistant: "We offer several scholarships..."  [⚡ Cached]    │    │
│  │    Including...                                    [10:20:15 AM]  │    │
│  │                                                                    │    │
│  │ [Input: What courses can I take?____] [📤 Send]                 │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌── SIDEBAR ─────────────────────┐                                         │
│  │ ⚙️ Settings                    │                                         │
│  │  [📚 RAG: ON]                 │                                         │
│  │  [🧠 Memory: ON]              │                                         │
│  │  [⚡ Cache: ON]               │                                         │
│  │  [Context: 5]                 │                                         │
│  │                                │                                         │
│  │ 💬 Conversation               │                                         │
│  │  [➕ New]  [🗑️ Clear]          │                                         │
│  │                                │                                         │
│  │ 📊 Cache Stats                │                                         │
│  │  Active: 35                    │                                         │
│  │  Conversations: 8              │                                         │
│  └────────────────────────────────┘                                         │
└──────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ HTTP Request
                                      │ {user_id, conv_id, message}
                                      ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                             BACKEND API LAYER                                │
│                        (/chat/ endpoint with pipeline)                       │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────┐       │
│  │ STEP 1: CHECK CACHE                                              │       │
│  │ ─────────────────────────────────────────────────────────────    │       │
│  │                                                                  │       │
│  │  Query Hash = MD5(user_id + query.lower())                      │       │
│  │  if hash in cache AND not expired:                              │       │
│  │    ├─ Return cached response           ⚡ < 100ms               │       │
│  │    └─ Add to conversation history                               │       │
│  │  else:                                                           │       │
│  │    └─ Continue to Step 2                                        │       │
│  └──────────────────────────────────────────────────────────────┘       │
│           │                                                              │
│           │ Cache Miss or disabled                                       │
│           ▼                                                              │
│  ┌──────────────────────────────────────────────────────────────┐       │
│  │ STEP 2: LOAD STUDENT CONTEXT                                 │       │
│  │ ─────────────────────────────────────────────────────────────│       │
│  │                                                               │       │
│  │  MemoryManager:                                              │       │
│  │    ├─ Entity Memory 🧠                                        │       │
│  │    │  ├─ Name: John Doe                                       │       │
│  │    │  ├─ Program: MSc                                         │       │
│  │    │  ├─ Year: 1st                                            │       │
│  │    │  ├─ Department: Computer Science                         │       │
│  │    │  ├─ Issues: [course_selection]                           │       │
│  │    │  └─ Interests: [AI, ML]                                  │       │
│  │    │                                                           │       │
│  │    └─ Vector Memory 📊                                        │       │
│  │       ├─ Top 3 similar doubts                                 │       │
│  │       └─ Top 3 similar interests                              │       │
│  │                                                               │       │
│  │  Result: Student Context String                              │       │
│  └──────────────────────────────────────────────────────────────┘       │
│           │                                                              │
│           │ Student context loaded                                       │
│           ▼                                                              │
│  ┌──────────────────────────────────────────────────────────────┐       │
│  │ STEP 3: RETRIEVE FROM DOCUMENTATION (RAG)                    │       │
│  │ ─────────────────────────────────────────────────────────────│       │
│  │                                                               │       │
│  │  Retriever Service:                                          │       │
│  │    ├─ Search FAISS/Vector DB                                 │       │
│  │    ├─ Retrieve top 5 documents                               │       │
│  │    └─ Check relevance                                        │       │
│  │                                                               │       │
│  │  if rag_enabled AND docs_found:                              │       │
│  │    ├─ Build RAG context ✅                                    │       │
│  │    └─ Set source = "rag"                                      │       │
│  │  else:                                                        │       │
│  │    └─ Continue to Step 4                                      │       │
│  └──────────────────────────────────────────────────────────────┘       │
│           │                                                              │
│           ├──────────────────┬─────────────────────┐                    │
│           │ RAG Found ✅     │   RAG Not Found ❌   │                    │
│           ▼                  ▼                     │                    │
│  ┌───────────────────┐  ┌──────────────────────┐ │                    │
│  │ Use RAG Context   │  │ Step 4: Generate     │ │                    │
│  │ 📚 FROM DOCS      │  │ with Disclaimer      │ │                    │
│  │ Set:              │  │ 🤖 AI GENERATED      │ │                    │
│  │ source="rag"      │  │ Set:                 │ │                    │
│  │ is_from_docs=true │  │ source="model"       │ │                    │
│  └───────────────────┘  │ is_from_docs=false   │ │                    │
│           │             └──────────────────────┘ │                    │
│           └──────────────────┬──────────────────┘ │                    │
│                              │                    │                    │
│                              ▼                    │                    │
│  ┌────────────────────────────────────────────────────────────┐       │
│  │ STEP 4: GENERATE RESPONSE (LLM)                            │       │
│  │ ─────────────────────────────────────────────────────────  │       │
│  │                                                             │       │
│  │  if rag_context exists:                                    │       │
│  │    prompt = "Answer based on documentation:"               │       │
│  │              + rag_context                                 │       │
│  │  else:                                                      │       │
│  │    prompt = "This is not in documentation, but I can say:" │       │
│  │              + "📌 [DISCLAIMER]"                           │       │
│  │                                                             │       │
│  │  response = llm.invoke(prompt)                             │       │
│  │  time: 2-30 seconds (depending on query)                   │       │
│  └────────────────────────────────────────────────────────────┘       │
│           │                                                              │
│           │ Response generated                                          │
│           ▼                                                              │
│  ┌────────────────────────────────────────────────────────────┐       │
│  │ STEP 5: CACHE THE RESPONSE                                 │       │
│  │ ─────────────────────────────────────────────────────────  │       │
│  │                                                             │       │
│  │  cache_entry = {                                           │       │
│  │    "response": "The fees are...",                          │       │
│  │    "source": "rag",                                        │       │
│  │    "is_from_docs": true,                                  │       │
│  │    "created_at": timestamp,                               │       │
│  │    "ttl": 3600 seconds,  # 1 hour                          │       │
│  │    "access_count": 0                                       │       │
│  │  }                                                          │       │
│  │                                                             │       │
│  │  cache.add(hash, cache_entry)                              │       │
│  │  cache.add_conversation_turn(user_id, "assistant", resp)   │       │
│  └────────────────────────────────────────────────────────────┘       │
│           │                                                              │
│           │ Response cached                                            │
│           ▼                                                              │
│  ┌────────────────────────────────────────────────────────────┐       │
│  │ RETURN ChatResponse                                        │       │
│  │ ─────────────────────────────────────────────────────────  │       │
│  │  {                                                         │       │
│  │    "response": "The fees are...",                         │       │
│  │    "source": "rag",                   # 📚 📚 from docs    │       │
│  │    "is_from_docs": true,                                 │       │
│  │    "student_context": {...},                              │       │
│  │    "conversation_processed": false                        │       │
│  │  }                                                         │       │
│  └────────────────────────────────────────────────────────────┘       │
└──────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ JSON Response
                                      │ {response, source, is_from_docs}
                                      ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                      UI: Display with Source Badge                            │
│                                                                              │
│  🤖 Assistant: "The fees are..."                                            │
│     📚 From Official Documentation ← Source Badge                           │
│     [Timestamp: 10:21 AM]                                                  │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Cache System Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    CACHE SYSTEM OPERATION                       │
└─────────────────────────────────────────────────────────────────┘

┌─ QUERY HASHING ─────────────────┐
│ Input: user_id + query          │
│ → "student_001:what are fees?"  │
│ → MD5 Hash                       │
│ → "a3f8c9d2e1b4c7f6..."         │
└─────────────────────────────────┘

┌─ CACHE LOOKUP ──────────────────┐
│ Hash in cache? YES               │
│ ├─ is_expired()? NO              │
│ │  └─ Return entry              │
│ │     ⚡ <100ms                  │
│ ├─ is_expired()? YES             │
│ │  ├─ Delete entry              │
│ │  └─ Cache MISS                │
│ └─ Hash NOT found               │
│    └─ Cache MISS                │
└─────────────────────────────────┘

┌─ CACHE STATISTICS ──────────────┐
│ Entry = {                        │
│   content: JSON response,        │
│   created_at: datetime,          │
│   ttl: 3600 seconds,             │
│   access_count: 5,               │
│   last_accessed: datetime        │
│ }                                │
│                                  │
│ Every access updates:            │
│ - access_count++                 │
│ - last_accessed = now            │
└─────────────────────────────────┘

┌─ EXPIRATION CHECK ──────────────┐
│ Background task (optional):      │
│ for each entry:                  │
│   if now - created_at > ttl:    │
│     delete entry                 │
│                                  │
│ Manual cleanup endpoint:         │
│ POST /clear-expired-cache        │
└─────────────────────────────────┘
```

---

## User Journey Map

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      STUDENT USER JOURNEY                                    │
└─────────────────────────────────────────────────────────────────────────────┘

STEP 1: SIDEBAR SETUP
┌────────────────────────────────────────────┐
│ 👤 Enter User ID: student_001              │
│ ↓                                          │
│ [System loads history and settings]        │
│ ✓ Conversation history loaded              │
│ ✓ Previous settings loaded                 │
│ ✓ Cache statistics display                 │
└────────────────────────────────────────────┘

STEP 2: VIEW CONVERSATION
┌────────────────────────────────────────────┐
│ 💬 Previous messages displayed:            │
│ ├─ 👤 User: "What's the fee?"   [9:00]    │
│ ├─ 🤖 Assistant: "Fees are..."   [📚 Doc]  │
│ │   [9:00:30]                             │
│ ├─ 👤 User: "Any scholarships?"  [9:05]   │
│ └─ 🤖 Assistant: "Yes, we have..."[⚡ Cache]│
│    [9:05:15]                              │
└────────────────────────────────────────────┘

STEP 3: (OPTIONAL) OPEN SETTINGS
┌────────────────────────────────────────────┐
│ 🎯 Context Window Settings Modal:          │
│ ├─ ☑️  RAG: Documentation Search           │
│ ├─ ☑️  Memory: Student Context             │
│ ├─ ☑️  Cache: Response Caching             │
│ └─ 📏 Context Length: [1━━━━━━━━━5━━━━] 5  │
│                       [💾 Save] [✕ Close]  │
│                                            │
│ [Setting saved automatically on change]   │
└────────────────────────────────────────────┘

STEP 4: ASK A QUESTION
┌────────────────────────────────────────────┐
│ 📝 Input: "Can I change my program?"       │
│ 📤 [Send Button]                          │
│                                            │
│ [System processes request through pipeline]│
└────────────────────────────────────────────┘

STEP 5: VIEW RESPONSE
┌────────────────────────────────────────────┐
│ 👤 You: "Can I change my program?"[10:20] │
│ 🤖 Assistant: "Yes, you can, but..."       │
│    "Contact admission office..."           │
│    ⚠️ NOT in Documentation - AI Generated  │
│    [10:20:45]                              │
│                                            │
│ [Note: Shows disclaimer for AI answers]   │
└────────────────────────────────────────────┘

STEP 6: OPTIONAL ACTIONS
┌──────────────────────────┬─────────────────┐
│ New Conversation        │ Start fresh ID  │
│ ├─ [➕ New]             │ └─ conv_123...  │
│ └─ Clear History        │                 │
│    [🗑️ Clear]          │ Refresh         │
│                        │ [🔄 Refresh]    │
│ Cache Stats            │                  │
│ ├─ Active: 35          │ Sidebar Updates: │
│ │ Convs: 8             │ ✓ Real-time     │
│ └─ Accesses: 156       │ ✓ Auto-refresh  │
└──────────────────────────┴─────────────────┘
```

---

## Memory System Integration

```
┌──────────────────────────────────────────────────────────────────┐
│                  MEMORY SYSTEM INTEGRATION                       │
└──────────────────────────────────────────────────────────────────┘

ENTITY MEMORY (Structured)
───────────────────────────
student_001:
  ├─ Name: John Doe
  ├─ Program: MSc Computer Science
  ├─ Year: 1st
  ├─ Department: CS
  ├─ Issues: [course_selection, thesis_guidance]
  └─ Interests: [AI, Machine Learning, NLP]

                             ↓[Loaded in Step 2]
                             
                    CHAT PIPELINE CONTEXT

VECTOR MEMORY (Semantic)
────────────────────────
student_001_doubts:
  ├─ "How to approach thesis topics?"
  ├─ "What prerequisites for advanced ML?"
  └─ "Best practices for research ethics?"

student_001_interests:
  ├─ "Natural Language Processing applications"
  ├─ "Deep Learning frameworks and libraries"
  └─ "Career paths in AI research"

                             ↓[Searched in Step 2]
                             
                    RELEVANT PAST CONTEXT

SUMMARY MEMORY (Historical)
──────────────────────────
Conv_001: "Discussed course prerequisites and registration"
Conv_002: "Talked about thesis topics and research methodologies"
Conv_003: "Explored career opportunities in AI field"

                             ↓[Available for reference]
                             
                    CONVERSATION CONTINUITY
```

---

## Response Types Visualization

```
TYPE 1: CACHE HIT ⚡
───────────────
Question: "What are the fees?"
  ↓
Found in cache (< 1 hour old)
  ↓
Response: "The fees are..." 
Source: ⚡ From Cache (Cached)
Time: <100ms

TYPE 2: FROM DOCUMENTATION 📚
──────────────────────
Question: "What are course prerequisites?"
  ↓
RAG retrieval successful
Documents found in university database
  ↓
Response: "Based on official documentation..."
Source: 📚 From Official Documentation
Time: 2-10s

TYPE 3: AI GENERATED ⚠️
────────────────────
Question: "How do I write a better thesis?"
  ↓
No relevant documentation found
No cache entry
  ↓
Response: "📌 This information is not in our official documentation,
          but I can say: [AI Generated Content]"
Source: ⚠️ NOT in Documentation - AI Generated Response
Time: 5-30s
Not cached (since not from docs)

TYPE 4: FROM MEMORY 🧠
──────────────────
Question: "[Personalization Based on Student Context]"
  ↓
Uses entity memory + vector memory
Student interests + past doubts loaded
  ↓
Response: "Based on your interests in AI..."
Source: 🧠 From Memory (With Student Context)
Time: 1-5s
```

---

**Total Integration:** 3 major systems working together seamlessly!  
**User Experience:** Enhanced with intelligent caching and context awareness
