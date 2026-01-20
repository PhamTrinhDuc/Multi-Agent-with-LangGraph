import streamlit as st
import requests
from datetime import datetime
import uuid

# Configuration
API_URL = "http://localhost:8000"

# Page config
st.set_page_config(
    page_title="E-commerce Chatbot",
    page_icon="🛒",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        background-color: #f5f5f5;
    }
    .stTextInput > div > div > input {
        background-color: white !important;
        color: #000000 !important;
        border: 2px solid #1976d2 !important;
        padding: 0.75rem !important;
        font-size: 1rem !important;
    }
    .stTextInput > div > div > input::placeholder {
        color: #999999 !important;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .user-message {
        background-color: #e3f2fd;
        margin-left: 20%;
    }
    .assistant-message {
        background-color: #ffffff;
        margin-right: 20%;
        border: 1px solid #e0e0e0;
    }
    .message-header {
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .timestamp {
        font-size: 0.75rem;
        color: #666;
        margin-top: 0.25rem;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'user_id' not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'conversation_loaded' not in st.session_state:
    st.session_state.conversation_loaded = False

def load_conversation_history():
    """Load conversation history from API"""
    try:
        response = requests.get(f"{API_URL}/conversation/{st.session_state.user_id}")
        if response.status_code == 200:
            data = response.json()
            st.session_state.messages = data.get('messages', [])
        return True
    except Exception as e:
        st.error(f"Không thể tải lịch sử hội thoại: {str(e)}")
        return False

def send_message(question: str):
    """Send message to chatbot API"""
    try:
        response = requests.post(
            f"{API_URL}/chat",
            json={
                "user_id": st.session_state.user_id,
                "question": question
            }
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Lỗi: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Không thể kết nối với server: {str(e)}")
        return None

def clear_conversation():
    """Clear conversation history"""
    try:
        response = requests.delete(f"{API_URL}/conversation/{st.session_state.user_id}")
        if response.status_code == 200:
            st.session_state.messages = []
            st.success("Đã xóa lịch sử hội thoại!")
        else:
            st.error("Không thể xóa lịch sử hội thoại")
    except Exception as e:
        st.error(f"Lỗi: {str(e)}")

def display_message(message):
    """Display a single message"""
    role = message.get('role', 'user')
    content = message.get('content', '')
    timestamp = message.get('timestamp', '')
    
    if role == 'user':
        st.markdown(f"""
            <div class="chat-message user-message">
                <div class="message-header">🙋 Bạn</div>
                <div>{content}</div>
                <div class="timestamp">{timestamp}</div>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
            <div class="chat-message assistant-message">
                <div class="message-header">🤖 Trợ lý</div>
                <div>{content}</div>
                <div class="timestamp">{timestamp}</div>
            </div>
        """, unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("⚙️ Cài đặt")
    
    st.markdown("---")
    st.markdown(f"**User ID:** `{st.session_state.user_id[:8]}...`")
    
    if st.button("🔄 Tải lại hội thoại", use_container_width=True):
        with st.spinner("Đang tải..."):
            if load_conversation_history():
                st.success("Đã tải lại!")
    
    if st.button("🗑️ Xóa lịch sử", use_container_width=True):
        clear_conversation()
    
    if st.button("🆕 Tạo phiên mới", use_container_width=True):
        st.session_state.user_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.session_state.conversation_loaded = False
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 📋 Hướng dẫn sử dụng")
    st.markdown("""
    - **Tìm kiếm sản phẩm**: "Bên bạn có tai nghe không?"
    - **So sánh sản phẩm**: "So sánh Sony với Apple"
    - **Đặt hàng**: "Tôi muốn đặt sản phẩm này"
    """)

# Main content
st.title("🛒 E-commerce Chatbot")
st.markdown("Chào mừng bạn đến với trợ lý mua sắm thông minh!")

# Load conversation history on first run
if not st.session_state.conversation_loaded:
    load_conversation_history()
    st.session_state.conversation_loaded = True

# Display chat history
chat_container = st.container()
with chat_container:
    if st.session_state.messages:
        for message in st.session_state.messages:
            display_message(message)
    else:
        st.info("👋 Bắt đầu cuộc trò chuyện bằng cách nhập câu hỏi bên dưới!")

# Chat input
st.markdown("---")
col1, col2 = st.columns([5, 1])

with col1:
    user_input = st.text_input(
        "Nhập câu hỏi của bạn:",
        key="user_input",
        placeholder="Ví dụ: Bên bạn có tai nghe không?",
        label_visibility="collapsed"
    )

with col2:
    send_button = st.button("📤 Gửi", use_container_width=True)

# Handle message sending
if send_button and user_input:
    with st.spinner("Đang xử lý..."):
        response = send_message(user_input)
        if response:
            # Add messages to session state
            timestamp = response.get('timestamp', datetime.now().isoformat())
            st.session_state.messages.append({
                "role": "user",
                "content": user_input,
                "timestamp": timestamp
            })
            st.session_state.messages.append({
                "role": "assistant",
                "content": response.get('answer', ''),
                "timestamp": timestamp
            })
            st.rerun()

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>Powered by LangGraph & FastAPI</div>",
    unsafe_allow_html=True
)
