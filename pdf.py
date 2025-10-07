import streamlit as st
from PIL import Image
import pytesseract
from datetime import datetime
import requests
import fitz  # PyMuPDF for PDF extraction
import io

# ============ CONFIG ============
st.set_page_config(page_title="Smart OCR Chat", layout="wide", page_icon="🤖")

# Tesseract path (adjust if needed)
try:
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
except:
    pass

# ============ SESSION STATE ============
if "messages" not in st.session_state:
    st.session_state.messages = []
if "extracted_text" not in st.session_state:
    st.session_state.extracted_text = ""

# ============ STYLING ============
st.markdown("""
<style>
    .main {padding: 1rem;}
    .chat-message {padding: 1rem; border-radius: 10px; margin-bottom: 1rem; animation: fadeIn 0.3s;}
    .user-message {background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; margin-left: 20%;}
    .assistant-message {background: #f7f7f8; color: #1a1a1a; margin-right: 20%; border-left: 4px solid #667eea;}
    .ocr-message {background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; border-radius: 15px; padding: 1.5rem;}
    @keyframes fadeIn {from {opacity: 0; transform: translateY(10px);} to {opacity: 1; transform: translateY(0);}}
    .stSpinner > div {border-top-color: #667eea !important;}
    .upload-text {text-align: center; color: #666; padding: 2rem; border: 2px dashed #ccc; border-radius: 10px; background: #fafafa; transition: all 0.3s;}
    .upload-text:hover {border-color: #667eea; background: #f0f0ff;}
    .sidebar .sidebar-content {background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);}
    .stCodeBlock {background: #1e1e1e !important; border-radius: 8px !important;}
    .stTextInput > div > div > input {border-radius: 20px; border: 2px solid #e0e0e0; padding: 0.75rem 1rem;}
    .stTextInput > div > div > input:focus {border-color: #667eea; box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);}
</style>
""", unsafe_allow_html=True)

# ============ HELPER FUNCTIONS ============
def extract_text_from_image(image):
    """Extract text from PIL Image"""
    return pytesseract.image_to_string(image).strip()

def extract_text_from_pdf(pdf_file):
    """Extract text and images from PDF"""
    pdf_bytes = pdf_file.read()
    pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
    all_text = []
    images = []
    
    for page_num in range(pdf_document.page_count):
        page = pdf_document[page_num]
        text = page.get_text()
        if text.strip():
            all_text.append(f"--- Page {page_num + 1} ---\n{text}")
        image_list = page.get_images()
        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = pdf_document.extract_image(xref)
            image_bytes = base_image["image"]
            image = Image.open(io.BytesIO(image_bytes))
            images.append(image)
            ocr_text = extract_text_from_image(image)
            if ocr_text:
                all_text.append(f"--- Page {page_num + 1} (Image {img_index + 1}) ---\n{ocr_text}")
    
    pdf_document.close()
    return "\n\n".join(all_text), images

def stream_ollama_response(prompt, extracted_context=""):
    """Stream response from Ollama in real-time"""
    try:
        full_prompt = prompt
        if extracted_context:
            full_prompt = f"""Based on this extracted text:

{extracted_context}

User question: {prompt}

Please provide a helpful response."""
        
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "llama3.2:1b", "prompt": full_prompt, "stream": True},
            stream=True
        )
        
        if response.status_code == 200:
            full_response = ""
            placeholder = st.empty()
            for line in response.iter_lines():
                if line:
                    import json
                    chunk = json.loads(line)
                    if "response" in chunk:
                        full_response += chunk["response"]
                        placeholder.markdown(full_response + "▌")
            placeholder.markdown(full_response)
            return full_response
        else:
            return "❌ Error: Cannot connect to Ollama. Make sure it's running!"
            
    except Exception as e:
        return f"❌ Error: {str(e)}"

# ============ SIDEBAR ============
with st.sidebar:
    st.markdown("### 🎯 Smart OCR Chat")
    st.markdown("---")
    
    if st.session_state.extracted_text:
        st.markdown("### 📄 Extracted Content")
        with st.expander("View Text", expanded=False):
            st.text_area("", value=st.session_state.extracted_text, height=200, disabled=True, key="sidebar_text")
    
    # Show chat history in sidebar
    if st.session_state.messages:
        st.markdown("---")
        st.markdown("### 💬 Chat History")
        with st.expander("View History", expanded=False):
            for i, chat in enumerate(st.session_state.messages):
                role_emoji = "👤" if chat["role"] == "user" else "🤖"
                timestamp = chat.get("timestamp", "")
                st.markdown(f"**{role_emoji} {chat['role'].title()}** _{timestamp}_")
                st.markdown(f"{chat['content']}")
                if i < len(st.session_state.messages) - 1:
                    st.markdown("---")
        
        if st.button("🗑️ Clear", key="clear_text"):
            st.session_state.extracted_text = ""
            st.rerun()
    
    st.markdown("---")
    st.markdown("### ⚙️ Settings")
    ocr_lang = st.selectbox("OCR Language", ["eng", "fra", "deu", "spa", "chi_sim"], index=0)
    
    st.markdown("---")
    if st.button("🗑️ Clear All Chat"):
        st.session_state.messages = []
        st.session_state.extracted_text = ""
        st.rerun()

# ============ MAIN INTERFACE ============
st.title("🤖 Smart OCR Chatbot")
st.markdown("Upload images or PDFs, extract text instantly, and chat with AI!")

# File upload
uploaded_file = st.file_uploader("📎 Drop your file here (Image or PDF)", type=["png", "jpg", "jpeg", "pdf"])

# Process uploaded file
if uploaded_file:
    file_type = uploaded_file.type
    with st.spinner("🔍 Extracting text..."):
        if "pdf" in file_type:
            text, images = extract_text_from_pdf(uploaded_file)
            st.session_state.extracted_text = text
            st.markdown(f'<div class="chat-message ocr-message">📄 <strong>PDF Processed!</strong><br>Extracted from: {uploaded_file.name}<br>Pages analyzed with OCR on embedded images</div>', unsafe_allow_html=True)
        else:
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Image", use_column_width=True)
            text = extract_text_from_image(image)
            st.session_state.extracted_text = text
            st.markdown(f'<div class="chat-message ocr-message">🖼️ <strong>Text Extracted!</strong><br>From: {uploaded_file.name}</div>', unsafe_allow_html=True)
    
    if st.session_state.extracted_text:
        with st.expander("📝 View Extracted Text"):
            st.code(st.session_state.extracted_text, language="text")
        
        st.markdown("### 🤖 AI Analysis")
        with st.spinner("Analyzing..."):
            analysis_prompt = "Analyze this text briefly. What is it about? Summarize key points in 3-4 sentences."
            analysis = stream_ollama_response(analysis_prompt, st.session_state.extracted_text)
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"📊 **Analysis:** {analysis}",
                "timestamp": datetime.now().strftime("%H:%M")
            })
    else:
        st.warning("⚠️ No text found in the file. Try a clearer image or different PDF.")

# Display chat messages in main area
st.markdown("---")
st.markdown("### 💬 Conversation")
for chat in st.session_state.messages:
    role = "user" if chat["role"] == "user" else "assistant"
    with st.chat_message(role):
        st.write(chat["content"])

# Chat input
user_input = st.chat_input("Ask anything about the extracted text...")
if user_input:
    # Add user message
    st.session_state.messages.append({
        "role": "user",
        "content": user_input,
        "timestamp": datetime.now().strftime("%H:%M")
    })
    
    # Display user message
    with st.chat_message("user"):
        st.write(user_input)
    
    # Generate and display assistant response
    with st.chat_message("assistant"):
        response = stream_ollama_response(user_input, st.session_state.extracted_text)
    
    # Add assistant message to history
    st.session_state.messages.append({
        "role": "assistant",
        "content": response,
        "timestamp": datetime.now().strftime("%H:%M")
    })
    
    st.rerun()

# Instructions
with st.expander("ℹ️ How to Use"):
    st.markdown("""
    **Quick Guide:**
    1. **Upload** an image (PNG/JPG) or PDF file
    2. **Extract** - Text is automatically extracted using OCR
    3. **AI analyzes** the content in real-time (streaming response)
    4. **Chat** - Ask questions about the extracted content
    5. **PDF Support** - Extracts text from PDF pages AND images within PDFs
    
    **Features:**
    - ✨ Real-time streaming AI responses
    - 📄 PDF text extraction + OCR on PDF images
    - 🖼️ Direct image OCR
    - 💬 Context-aware chat
    - 🎨 Modern, animated UI
    - 📜 Chat history in sidebar
    
    **Requirements:**
    - Tesseract OCR installed
    - Ollama running locally (port 11434)
    - PyMuPDF: `pip install PyMuPDF`
    """)