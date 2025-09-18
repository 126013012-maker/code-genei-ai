import streamlit as st
import requests

#  Page setup
st.set_page_config(page_title="Ollama Chatbot", page_icon="🤖")
st.title("Chatbot with Ollama")
st.write("Choose a model and start chatting!")

#  List of your installed models
models = ["deepseek-r1:1.5b", "llama3.2:1b", "mario:latest", "llama3.1:8b"]

#  Dropdown for model selection
selected_model = st.selectbox("Select a model:", models)

#  Store chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

#  Display past messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Type your message here..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    #  Send to Ollama API with selected model
    response = requests.post(
        "http://localhost:11434/api/chat",
        json={
            "model": selected_model,  # 👈 dynamic model choice
            "messages": [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
            "stream": False
        }
    )

    if response.status_code == 200:
        bot_reply = response.json()["message"]["content"]
    else:
        bot_reply = "Error: " + response.text

    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
    with st.chat_message("assistant"):
        st.markdown(bot_reply)
