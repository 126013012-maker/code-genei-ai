import streamlit as st
import requests
from datetime import datetime

# ---------------- Page Config ----------------
st.set_page_config(page_title="Chatbot with Ollama", layout="wide")

# ---------------- Sidebar ----------------
# ---------------- Sidebar ----------------
st.sidebar.title("⚙️ Settings")

# Installed models on your system
model_options = ["deepseek-r1:1.5b", "llama3.2:1b", "mario:latest", "llama3.1:8b"]
MODEL_NAME = st.sidebar.selectbox("Choose a model", model_options, index=0)


# Clear chat button
if st.sidebar.button("🗑 Clear Chat"):
    st.session_state.messages = []

# Chat history (timestamps)
st.sidebar.markdown("---")
st.sidebar.subheader("📜 Chat History")
if "messages" in st.session_state and st.session_state.messages:
    for idx, msg in enumerate(st.session_state.messages):
        role_icon = "🧑" if msg["role"] == "user" else "🤖"
        st.sidebar.markdown(f"{role_icon} **{msg['role']}** ({msg.get('timestamp','')})")
        st.sidebar.caption(msg["content"][:40] + ("..." if len(msg["content"]) > 40 else ""))
else:
    st.sidebar.caption("No conversation yet.")

st.sidebar.markdown("---")
st.sidebar.markdown("**Local Chatbot Powered by Ollama**")
st.sidebar.caption("Built with Streamlit 💙")

# ---------------- Custom CSS ----------------
st.markdown("""
<style>
.chat-title {
    font-size: 2.3rem;
    font-weight: 700;
    text-align: center;
    margin-bottom: 1.5rem;
    color: #4A90E2;
}
.chat-container {
    display: flex;
    flex-direction: column;
    max-height: 70vh;
    overflow-y: auto;
    padding: 10px;
    background-color: #f9f9f9;
    border-radius: 12px;
    box-shadow: 0px 4px 12px rgba(0,0,0,0.05);
}
.chat-bubble-user {
    align-self: flex-end;
    background-color: #DCF8C6;
    color: #000;
    padding: 12px;
    border-radius: 12px;
    margin: 5px 0;
    max-width: 80%;
}
.chat-bubble-assistant {
    align-self: flex-start;
    background-color: #ffffff;
    color: #000;
    padding: 12px;
    border-radius: 12px;
    margin: 5px 0;
    max-width: 80%;
    border: 1px solid #ddd;
}
</style>
""", unsafe_allow_html=True)

# ---------------- Title ----------------
st.markdown("<div class='chat-title'>💬 Chatbot with Ollama</div>", unsafe_allow_html=True)

# ---------------- Initialize Session ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------- Chat UI ----------------
with st.container():
    st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
    for m in st.session_state.messages:
        role_class = "chat-bubble-user" if m["role"] == "user" else "chat-bubble-assistant"
        st.markdown(f"<div class='{role_class}'>{m['content']}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- Input ----------------
user_input = st.chat_input("Type your message...")

if user_input:
    # Add user message
    st.session_state.messages.append({
        "role": "user",
        "content": user_input,
        "timestamp": datetime.now().strftime("%H:%M")
    })

    # Send to Ollama
    try:
        response = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": MODEL_NAME,
                "messages": [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                "stream": False
            }
        )
        if response.status_code == 200:
            reply = response.json()["message"]["content"]
        else:
            reply = "⚠ Error: Could not connect to local model."
    except Exception as e:
        reply = f"⚠ Exception: {str(e)}"

    # Add assistant reply
    st.session_state.messages.append({
        "role": "assistant",
        "content": reply,
        "timestamp": datetime.now().strftime("%H:%M")
    })

    st.rerun()
