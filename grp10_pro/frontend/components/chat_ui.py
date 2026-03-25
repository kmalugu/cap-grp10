# Enhanced Chat UI Component with Conversation History & Context Settings

import streamlit as st
import requests
from datetime import datetime

API_URL = "http://127.0.0.1:8000"

def get_source_badge(source: str, is_from_docs: bool) -> str:
    """Get a visual badge for the response source"""
    badges = {
        "cache": "⚡ From Cache",
        "memory": "🧠 Memory",
        "rag": "📚 From Docs",
        "model": "🤖 AI Generated",
        "guardrail": "🚫 Blocked",
    }
    
    return badges.get(source, "System")


def init_session_state():
    """Initialize session state variables"""
    if "user_id" not in st.session_state:
        st.session_state.user_id = "student_001"
    if "conversation_id" not in st.session_state:
        st.session_state.conversation_id = f"conv_{int(datetime.now().timestamp())}"
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "context_settings" not in st.session_state:
        st.session_state.context_settings = {
            "context_length": 5,
            "rag_enabled": True,
            "memory_enabled": True,
            "use_cache": True,
        }
    if "show_settings" not in st.session_state:
        st.session_state.show_settings = False


def load_conversation_history(user_id: str):
    """Load conversation history from backend"""
    try:
        response = requests.get(f"{API_URL}/chat/user/{user_id}/conversation-history")
        if response.status_code == 200:
            return response.json().get("conversation_history", [])
    except Exception as e:
        st.warning(f"Could not load conversation history: {e}")
    return []


def load_context_settings(user_id: str):
    """Load context settings from backend"""
    try:
        response = requests.get(f"{API_URL}/chat/user/{user_id}/context-settings")
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.warning(f"Could not load context settings: {e}")
    return None


def save_context_settings(user_id: str, settings: dict):
    """Save context settings to backend"""
    try:
        response = requests.post(
            f"{API_URL}/chat/user/{user_id}/context-settings",
            json=settings
        )
        return response.status_code == 200
    except Exception as e:
        st.error(f"Could not save settings: {e}")
    return False


def clear_conversation(user_id: str):
    """Clear conversation history"""
    try:
        response = requests.post(f"{API_URL}/chat/user/{user_id}/clear-conversation")
        return response.status_code == 200
    except Exception as e:
        st.error(f"Could not clear conversation: {e}")
    return False


def chat_ui():
    """Enhanced chat UI with conversation history and context settings"""
    st.subheader("💬 Enhanced Chat Assistant")
    
    init_session_state()

    # ========== SIDEBAR CONTROLS ==========
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # User ID input
        new_user_id = st.text_input(
            "User ID",
            value=st.session_state.user_id,
            help="This maintains persistent memory across conversations"
        )
        
        if new_user_id != st.session_state.user_id:
            st.session_state.user_id = new_user_id
            st.session_state.conversation_id = f"conv_{int(datetime.now().timestamp())}"
            st.session_state.messages = []
            st.rerun()

        st.divider()

        # Context Window Settings
        st.subheader("🎯 Context Settings")
        
        with st.expander("⚙️ Configure", expanded=st.session_state.show_settings):
            st.markdown("**Enable/Disable Features:**")
            
            rag_enabled = st.checkbox(
                "📚 Use RAG (Documentation Search)",
                value=st.session_state.context_settings['rag_enabled']
            )
            
            memory_enabled = st.checkbox(
                "🧠 Use Student Memory",
                value=st.session_state.context_settings['memory_enabled']
            )
            
            use_cache = st.checkbox(
                "⚡ Use Response Cache",
                value=st.session_state.context_settings['use_cache']
            )
            
            context_length = st.slider(
                "📏 Context Window Length",
                min_value=1,
                max_value=20,
                value=st.session_state.context_settings['context_length'],
                help="Number of recent messages to keep in context"
            )

            # Save button
            if st.button("💾 Save Settings", use_container_width=True):
                new_settings = {
                    "context_length": context_length,
                    "rag_enabled": rag_enabled,
                    "memory_enabled": memory_enabled,
                    "use_cache": use_cache,
                }
                
                if save_context_settings(st.session_state.user_id, new_settings):
                    st.session_state.context_settings = new_settings
                    st.success("✅ Settings updated!")
                else:
                    st.error("❌ Failed to save settings")

        # Display current settings
        st.markdown("**Current Settings:**")
        st.markdown(f"""
- **RAG**: {'✅' if st.session_state.context_settings['rag_enabled'] else '❌'}
- **Memory**: {'✅' if st.session_state.context_settings['memory_enabled'] else '❌'}
- **Cache**: {'✅' if st.session_state.context_settings['use_cache'] else '❌'}
- **Context**: {st.session_state.context_settings['context_length']} msgs
        """)

        st.divider()

        # Conversation controls
        st.subheader("💬 Conversation")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("➕ New", key="new_conv_button"):
                st.session_state.conversation_id = f"conv_{int(datetime.now().timestamp())}"
                st.session_state.messages = []
                st.success("New conversation started!")
                st.rerun()

        with col2:
            if st.button("🗑️ Clear", key="clear_button"):
                if clear_conversation(st.session_state.user_id):
                    st.session_state.messages = []
                    st.success("History cleared!")
                    st.rerun()

        st.divider()

        # Cache stats
        st.subheader("📊 Cache Stats")
        try:
            response = requests.get(f"{API_URL}/chat/cache-stats")
            if response.status_code == 200:
                stats = response.json()
                st.metric("Cache Entries", stats.get("active_entries", 0))
                st.metric("Conversations", stats.get("conversations", 0))
                st.metric("Total Access", stats.get("total_accesses", 0))
        except Exception as e:
            st.warning(f"Could not load stats: {e}")

    # ========== MAIN CHAT AREA ==========
    st.markdown(f"### Chat with {st.session_state.user_id}")

    # Display conversation history
    chat_container = st.container(border=True, height=400)

    with chat_container:
        if st.session_state.messages:
            for msg in st.session_state.messages:
                if msg["role"] == "user":
                    with st.chat_message("user", avatar="👤"):
                        st.markdown(msg["content"])
                        st.caption(f"*{msg.get('timestamp', 'unknown time')}*")
                else:
                    with st.chat_message("assistant", avatar="🤖"):
                        st.markdown(msg["content"])
                        
                        # Show source badge if available
                        if "source" in msg:
                            source_badge = get_source_badge(
                                msg.get("source", "model"),
                                msg.get("is_from_docs", False)
                            )
                            st.caption(f"📍 {source_badge}")
                        
                        st.caption(f"*{msg.get('timestamp', 'unknown time')}*")
        else:
            st.info("💭 No messages yet. Start a conversation below!")

    st.divider()

    # ========== MESSAGE INPUT ==========
    st.markdown("**Your Message:**")
    col1, col2 = st.columns([5, 1])
    
    with col1:
        user_input = st.text_input(
            "message",
            placeholder="Ask me anything about the university...",
            label_visibility="collapsed"
        )

    with col2:
        send_button = st.button("📤 Send", use_container_width=True, type="primary")

    # Process message
    if send_button and user_input.strip():
        # Add user message to display
        user_msg = {
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }
        st.session_state.messages.append(user_msg)

        # Show thinking indicator
        with st.spinner("🤔 Thinking..."):
            try:
                # Send to backend
                payload = {
                    "user_id": st.session_state.user_id,
                    "conversation_id": st.session_state.conversation_id,
                    "message": user_input,
                    "end_conversation": False,
                }

                response = requests.post(
                    f"{API_URL}/chat/",
                    json=payload
                )
                response.raise_for_status()
                result = response.json()

                # Add assistant message with metadata
                assistant_msg = {
                    "role": "assistant",
                    "content": result.get("response", "No response received"),
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "source": result.get("source", "model"),
                    "is_from_docs": result.get("is_from_docs", False),
                }
                st.session_state.messages.append(assistant_msg)

                st.success("✅ Response received!")
                st.rerun()

            except requests.exceptions.ConnectionError:
                st.error(
                    "❌ Cannot connect to backend.\n\n"
                    "Make sure the backend is running:\n"
                    "`python -m uvicorn backend.main:app --reload`"
                )
            except requests.exceptions.Timeout:
                st.error("❌ Backend request timed out. Please try again.")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

    # ========== FOOTER ==========
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        st.caption(f"**ID**: {st.session_state.conversation_id[:15]}... | **User**: {st.session_state.user_id}")
    with col2:
        st.caption(f"**Messages**: {len(st.session_state.messages)}")
