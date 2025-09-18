import streamlit as st
from PIL import Image
import pytesseract
from datetime import datetime
import requests
import re

# ------------------ Config ------------------
st.set_page_config(page_title="OCR + Chatbot", layout="wide", page_icon="🤖")

# Tesseract path
# IMPORTANT: Make sure this path is correct for your installation.
# If Tesseract is in your system's PATH, you might not need this line.
try:
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
except pytesseract.TesseractNotFoundError:
    st.warning("Tesseract is not installed or not in your PATH. Please install Tesseract OCR.")
    # You might want to exit or disable OCR functionality here if Tesseract is critical.

# ------------------ Initialize session states ------------------
if "ocr_history" not in st.session_state:
    st.session_state.ocr_history = []

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "user_input" not in st.session_state:
    st.session_state.user_input = ""

if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None

if "current_ocr_text" not in st.session_state:
    st.session_state.current_ocr_text = ""

if "conversation_context" not in st.session_state:
    st.session_state.conversation_context = []

if "extracted_code" not in st.session_state:
    st.session_state.extracted_code = ""

if "code_language" not in st.session_state:
    st.session_state.code_language = "python"

# ------------------ Helper Functions ------------------
def detect_code_language(text):
    """Detect programming language from extracted text"""
    text_lower = text.lower()
    
    # Python keywords and patterns
    python_patterns = ['def ', 'import ', 'from ', 'class ', 'if __name__', 'print(', '.py', 'import numpy', 'import pandas', 'from sklearn']
    # JavaScript patterns  
    js_patterns = ['function ', 'var ', 'let ', 'const ', 'console.log', '.js', 'import ', 'export ']
    # Java patterns
    java_patterns = ['public class', 'public static void main', 'System.out.', '.java', 'import java.']
    # C++ patterns
    cpp_patterns = ['#include', 'using namespace', 'cout <<', '.cpp', '.h', 'std::cout']
    
    # Assign higher scores to more specific patterns
    scores = {
        'python': sum(1 for pattern in python_patterns if pattern in text_lower) * 2,
        'javascript': sum(1 for pattern in js_patterns if pattern in text_lower) * 1.5,
        'java': sum(1 for pattern in java_patterns if pattern in text_lower) * 1.8,
        'cpp': sum(1 for pattern in cpp_patterns if pattern in text_lower) * 1.7
    }
    
    detected_lang = max(scores, key=scores.get)
    
    # Only return a language if the score is significant enough to avoid false positives
    return detected_lang if scores[detected_lang] > 1 else 'unknown'

def save_code_temporarily(code, language="python"):
    """Save extracted code to temporary storage"""
    st.session_state.extracted_code = code
    st.session_state.code_language = language
    
    # Also save to a temporary file-like structure
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"extracted_code_{timestamp}.{language}"
    
    return {
        "filename": filename,
        "code": code,
        "language": language,
        "timestamp": timestamp,
        "line_count": len(code.split('\n'))
    }

def analyze_ocr_text(text):
    """Analyze and explain the OCR extracted text"""
    analysis_prompt = f"""Please analyze this text that was extracted from an image using OCR:

TEXT:
{text}

Please provide:
1. A brief summary of what this text appears to be (document type, content, etc.)
2. Key information or points mentioned
3. Any notable details or observations
4. Potential questions someone might want to ask about this content

Keep your response informative but concise (4-6 sentences)."""
    
    return get_ollama_response(analysis_prompt, use_context=False)

def get_ollama_response(prompt, use_context=False):
    """Get response from Ollama with optional context"""
    try:
        if use_context and st.session_state.current_ocr_text:
            # Include OCR context in the conversation
            context_prompt = f"""You are having a conversation about this extracted text from an image:

EXTRACTED TEXT:
{st.session_state.current_ocr_text}

Please answer the following question in context of this extracted text:
{prompt}

If the question is not related to the extracted text, you can answer generally but try to relate it back to the extracted text when possible.
Respond concisely."""
            
            response = requests.post(
                "http://localhost:11434/api/generate", # Ensure Ollama is running and accessible
                json={
                    "model": "llama3.2:1b", # Or your preferred Ollama model
                    "prompt": context_prompt,
                    "stream": False
                }
            )
        else:
            # Regular chat without specific OCR context
            # For chat, we might want to pass the conversation history to Ollama
            # For simplicity here, we're sending just the current prompt.
            # A more robust chatbot would manage the conversation history.
            messages = [{"role": "user", "content": prompt}]
            # If you have past chat history to send:
            # for chat_entry in st.session_state.chat_history:
            #     if chat_entry["role"] != "system" and chat_entry["role"] != "analysis" and chat_entry["role"] != "ocr":
            #         messages.append({"role": chat_entry["role"], "content": chat_entry["message"]})

            response = requests.post(
                "http://localhost:11434/api/chat", # Ensure Ollama is running and accessible
                json={
                    "model": "llama3.2:1b", # Or your preferred Ollama model
                    "messages": messages,
                    "stream": False
                }
            )
        
        if response.status_code == 200:
            data = response.json()
            if use_context:
                reply = data.get("response") or str(data)
            else:
                reply = data.get("message", {}).get("content") or str(data)
            reply = re.sub(r"<.*?>", "", reply) # Clean up any stray HTML tags
            return reply
        else:
            return f"⚠ Error {response.status_code}: Could not connect to Ollama. Please ensure Ollama is running and the model is available. Response: {response.text}"
    except requests.exceptions.ConnectionError:
        return "⚠ Error: Could not connect to Ollama. Please ensure Ollama is running on http://localhost:11434."
    except Exception as e:
        return f"⚠ Exception: {str(e)}"

# ------------------ Sidebar ------------------
st.sidebar.title("Settings & History")

# OCR Settings
st.sidebar.subheader("OCR Settings")
# Added more common languages, but ensure Tesseract has them installed
languages = ["eng", "fra", "deu", "spa", "chi_sim", "jpn", "kor"] 
lang_choice = st.sidebar.selectbox("Select OCR Language", languages, index=0)

# Show current extracted code if available
if st.session_state.extracted_code:
    st.sidebar.markdown("---")
    st.sidebar.subheader("💾 Extracted Code")
    st.sidebar.text(f"Language: {st.session_state.code_language.upper()}")
    st.sidebar.text(f"Lines: {len(st.session_state.extracted_code.split('\\n'))}")
    
    with st.sidebar.expander("View Code"):
        st.code(st.session_state.extracted_code, language=st.session_state.code_language)
    
    if st.sidebar.button("📋 Copy Code", key="copy_code_btn"):
        st.toast("Code copied to session!") # Use toast for brief feedback
    
    if st.sidebar.button("🗑 Clear Extracted Code", key="clear_code_btn"):
        st.session_state.extracted_code = ""
        st.session_state.code_language = "python"
        st.rerun() # Rerun to clear sidebar section

# Show current OCR text if available
if st.session_state.current_ocr_text:
    st.sidebar.markdown("---")
    st.sidebar.subheader("Current OCR Text")
    st.sidebar.text_area("Extracted Text", value=st.session_state.current_ocr_text, height=100, disabled=True)
    if st.sidebar.button("🗑 Clear Current OCR", key="clear_ocr_btn"):
        st.session_state.current_ocr_text = ""
        st.session_state.conversation_context = [] # Clear context if OCR is cleared
        st.rerun() # Rerun to clear sidebar section

st.sidebar.markdown("---")
st.sidebar.subheader("OCR History")
if st.session_state.ocr_history:
    for entry in st.session_state.ocr_history[::-1]:
        st.sidebar.markdown(f"**{entry['timestamp']}** ({entry['filename']})")
        st.sidebar.caption(entry['text'][:60] + ("..." if len(entry['text']) > 60 else ""))
else:
    st.sidebar.caption("No OCR history yet.")

if st.sidebar.button("🗑 Clear OCR History", key="clear_ocr_history_btn"):
    st.session_state.ocr_history = []
    st.rerun() # Rerun to update sidebar

# Chatbot Settings
st.sidebar.markdown("---")
st.sidebar.subheader("Chatbot Settings")
# model_choice = "llama3.2:1b" # Currently hardcoded in get_ollama_response
context_mode = st.sidebar.checkbox("Use OCR Context in Chat", value=True, 
                                   help="When enabled, the chatbot will consider the extracted OCR text in all responses")

st.sidebar.markdown("---")
st.sidebar.subheader("Chat History")
if st.session_state.chat_history:
    for chat in st.session_state.chat_history[::-1]:
        role_icon = "🧑" if chat["role"] == "user" else "🤖"
        # Only show relevant parts for brevity in sidebar
        display_message = chat["message"]
        if "\n\n" in display_message: # Truncate code blocks for sidebar
            display_message = display_message.split("\n\n")[0] + "..."
        elif len(display_message) > 60:
            display_message = display_message[:60] + "..."

        st.sidebar.markdown(f"{role_icon} **{chat['role'].capitalize()}** ({chat['timestamp']})")
        st.sidebar.caption(display_message)
else:
    st.sidebar.caption("No chat history yet.")

if st.sidebar.button("🗑 Clear Chat History", key="clear_chat_btn"):
    st.session_state.chat_history = []
    st.rerun() # Rerun to update sidebar

# ------------------ Custom CSS ------------------
st.markdown("""
<style>
h1 {text-align: center; margin-bottom: 20px;}
.chat-container {max-height: 500px; overflow-y: auto; padding: 10px; border: 1px solid #ddd; border-radius: 10px; background-color: #f9f9f9; margin-bottom: 10px;}
.chat-bubble-user {background-color: #DCF8C6; color: black; padding: 10px; border-radius: 12px; margin:5px 0; max-width: 80%; align-self: flex-end; font-family: sans-serif;}
.chat-bubble-assistant {background-color: #ffffff; color: black; padding: 10px; border-radius: 12px; margin:5px 0; max-width: 80%; align-self: flex-start; font-family: sans-serif;}
.chat-bubble-ocr {background-color: #E3F2FD; color: black; padding: 10px; border-radius: 12px; margin:5px 0; max-width: 90%; align-self: flex-start; border-left: 4px solid #2196F3; font-family: sans-serif;}
.chat-bubble-analysis {background-color: #F3E5F5; color: black; padding: 10px; border-radius: 12px; margin:5px 0; max-width: 90%; align-self: flex-start; border-left: 4px solid #9C27B0; font-family: sans-serif;}
.flex-column {display: flex; flex-direction: column;}
.bottom-bar {display: flex; gap: 10px; margin-top: 10px;}

/* File upload styling for the single widget approach */
.stFileUploader label {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 20px;
    border: 2px dashed #ccc;
    border-radius: 10px;
    background-color: #f9f9f9;
    transition: all 0.3s ease;
    cursor: pointer;
}
.stFileUploader label:hover {
    border-color: #007bff;
    background-color: #f0f8ff;
}
.stFileUploader label > div:first-of-type { /* Styles the first div inside the label, usually the upload icon/text */
    font-size: 24px; /* Adjusted icon size */
    color: #666;
    margin-bottom: 10px;
}
.stFileUploader label > div:nth-of-type(2) { /* Styles the second div, usually the text description */
    color: #666;
    font-weight: 500;
}
.stFileUploader label > div:nth-of-type(3) { /* Styles the third div, usually the file type/size help text */
    font-size: 12px; 
    color: #999; 
    margin-top: 5px;
}

.file-info {
    background-color: #e3f2fd;
    border: 1px solid #2196f3;
    border-radius: 8px;
    padding: 10px;
    margin: 10px 0;
    display: flex;
    align-items: center;
    gap: 10px;
}
.code-storage {
    background-color: #f3e5f5;
    border: 1px solid #9c27b0;
    border-radius: 8px;
    padding: 10px;
    margin: 5px 0;
}

.status-indicator {
    position: fixed;
    top: 10px;
    right: 10px;
    padding: 5px 10px;
    border-radius: 15px;
    font-size: 12px;
    font-weight: bold;
    z-index: 1000; /* Ensure it's above other elements */
}
.context-active {background-color: #4CAF50; color: white;}
.context-inactive {background-color: #FF9800; color: white;}

/* Styling for code blocks within chat */
.stCodeBlock {
    border-radius: 8px !important;
    padding: 15px !important;
    font-family: 'Consolas', 'Monaco', 'Andale Mono', 'Ubuntu Mono', monospace !important;
}
</style>
""", unsafe_allow_html=True)

# ------------------ Page Header ------------------
st.markdown("<h1>📄 OCR + 💬 Chatbot</h1>", unsafe_allow_html=True)

# Status indicator
if st.session_state.current_ocr_text and context_mode:
    st.markdown('<div class="status-indicator context-active">📄 OCR Context Active</div>', unsafe_allow_html=True)
elif st.session_state.current_ocr_text:
    st.markdown('<div class="status-indicator context-inactive">📄 OCR Text Available (Context Off)</div>', unsafe_allow_html=True)

# ------------------ Chat display ------------------
chat_container = st.container()
with chat_container:
    st.markdown('<div class="chat-container flex-column">', unsafe_allow_html=True)
    for chat in st.session_state.chat_history:
        if chat["role"] == "user":
            bubble_class = "chat-bubble-user"
        elif chat.get("type") == "ocr":
            bubble_class = "chat-bubble-ocr"
        elif chat.get("type") == "analysis":
            bubble_class = "chat-bubble-analysis"
        else:
            bubble_class = "chat-bubble-assistant"
        
        # Basic markdown rendering for messages
        message_content = chat["message"]
        # Handle code blocks by explicitly using st.markdown with st.code if needed, or just render markdown
        # For simplicity, treating most as markdown here.
        st.markdown(f'<div class="{bubble_class}"><div>{message_content.replace(chr(10), "<br>")}</div></div>', unsafe_allow_html=True) # Replace newlines with <br> for HTML display
    st.markdown('</div>', unsafe_allow_html=True)

# ------------------ Bottom input bar ------------------
st.markdown('<div class="bottom-bar">', unsafe_allow_html=True)
# Define columns *before* trying to use them
col1, col2 = st.columns([1, 4])

with col1:
    uploaded_file = st.file_uploader(
        "📁 **Drag & Drop Image Here**",
        type=["png", "jpg", "jpeg"],
        label_visibility="visible"
    )

    if uploaded_file is not None and uploaded_file != st.session_state.uploaded_file:
        st.session_state.uploaded_file = uploaded_file
        
        # Show file info
        file_size = uploaded_file.size / 1024  # Convert to KB
        st.markdown(f"""
        <div class="file-info">
            <span style="font-size: 20px;">🖼️</span>
            <div>
                <strong>{uploaded_file.name}</strong><br>
                <small>{file_size:.1f} KB</small>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        img = Image.open(uploaded_file)
        
        with st.spinner("🔍 Extracting text from image..."):
            text = pytesseract.image_to_string(img, lang=lang_choice).strip()

        if text:
            # Update current OCR text for context
            st.session_state.current_ocr_text = text
            
            # Detect if extracted text is code
            detected_language = detect_code_language(text)
            is_code = detected_language != 'unknown'
            
            # Save code temporarily if detected
            if is_code:
                code_info = save_code_temporarily(text, detected_language)
                st.markdown(f"""
                <div class="code-storage">
                    <span style="font-size: 16px;">💾</span>
                    <strong>Code Detected & Stored!</strong><br>
                    <small>Language: {detected_language.upper()} • Lines: {code_info['line_count']}</small>
                </div>
                """, unsafe_allow_html=True)
            
            # Save OCR text to history
            st.session_state.ocr_history.append({
                "filename": uploaded_file.name,
                "text": text,
                "timestamp": datetime.now().strftime("%H:%M"),
                "is_code": is_code,
                "language": detected_language if is_code else None
            })

            # Add extracted text to chat history with special styling
            message_prefix = "💻 **Code Extracted" if is_code else "📄 **Text Extracted"
            st.session_state.chat_history.append({
                "role": "system",
                "type": "ocr",
                "message": f"{message_prefix} from {uploaded_file.name}:**\n\n```{detected_language if is_code else ''}\n{text}\n```",
                "timestamp": datetime.now().strftime("%H:%M")
            })

            # Get AI analysis of the extracted text/code
            with st.spinner("🤖 Analyzing extracted content..."):
                if is_code:
                    analysis_prompt = f"""This appears to be {detected_language} code extracted from an image. Please provide:
1. A brief explanation of what this code does
2. Key functions or components
3. Any notable patterns or potential improvements
4. Possible questions someone might ask about this code

CODE:
{text}"""
                else:
                    analysis_prompt = f"""Please analyze this text that was extracted from an image using OCR:

TEXT:
{text}

Please provide:
1. A brief summary of what this text appears to be
2. Key information or points mentioned  
3. Any notable details or observations
4. Potential questions someone might want to ask about this content"""
                
                analysis = get_ollama_response(analysis_prompt, use_context=False)

            # Add analysis to chat history
            analysis_icon = "⚙️" if is_code else "🔍"
            analysis_title = "Code Analysis" if is_code else "Text Analysis"
            st.session_state.chat_history.append({
                "role": "assistant",
                "type": "analysis",
                "message": f"{analysis_icon} **{analysis_title}:**\n\n{analysis}",
                "timestamp": datetime.now().strftime("%H:%M")
            })

            # Add helpful prompt
            help_message = "💡 I've extracted and analyzed the code from your image. You can ask me to explain specific functions, suggest improvements, or help debug any issues!" if is_code else "💡 I've extracted and analyzed the text from your image. Feel free to ask me questions about the content, request clarifications, or discuss any aspect of the extracted information!"
            
            st.session_state.chat_history.append({
                "role": "assistant", 
                "message": help_message,
                "timestamp": datetime.now().strftime("%H:%M")
            })

        else:
            st.session_state.chat_history.append({
                "role": "assistant",
                "message": "⚠️ No text could be extracted from this image. Please try uploading a clearer image with visible text or code.",
                "timestamp": datetime.now().strftime("%H:%M")
            })

        st.rerun()

# ---- Chat input ----
with col2:
    # Use st.session_state for user_input to maintain value across reruns if needed
    user_input = st.text_input("Type your message here...", value=st.session_state.user_input, key="chat_input_box", 
                               placeholder="Ask questions about the extracted text or chat normally...")
    st.session_state.user_input = user_input # Update session state with current input

    if st.button("Send", key="send_btn") and user_input.strip() != "":
        # Add user message to chat history
        st.session_state.chat_history.append({
            "role": "user",
            "message": user_input,
            "timestamp": datetime.now().strftime("%H:%M")
        })
        st.session_state.user_input = "" # Clear input box after sending

        # Get AI response with or without OCR context
        with st.spinner("Thinking..."):
            if context_mode and st.session_state.current_ocr_text:
                reply = get_ollama_response(user_input, use_context=True)
            else:
                reply = get_ollama_response(user_input, use_context=False)

        # Add assistant reply to chat history
        st.session_state.chat_history.append({
            "role": "assistant",
            "message": reply,
            "timestamp": datetime.now().strftime("%H:%M")
        })

        st.rerun() # Rerun the app to display new messages

st.markdown('</div>', unsafe_allow_html=True)

# ------------------ Instructions ------------------
with st.expander("ℹ️ How to use this app"):
    st.markdown("""
    **OCR + Chatbot Features:**
    
    1.  **Image Upload**: Upload an image containing text (PNG, JPG, JPEG) using the drag-and-drop area.
    2.  **OCR Extraction**: Text is automatically extracted from the image using Tesseract OCR.
    3.  **AI Analysis**: The extracted text (or code) is then analyzed by an AI model (Ollama).
    4.  **Contextual Chat**: You can ask questions about the extracted content. The chatbot can use the OCR text as context if "Use OCR Context in Chat" is enabled.
    5.  **Code Detection**: The app automatically detects if the extracted content is code (Python, JavaScript, Java, C++).
    6.  **Code Storage**: Detected code is stored temporarily in the sidebar, with syntax highlighting.
    7.  **History**: View past OCR extractions and chat conversations in the sidebar.
    
    **Tips:**
    * Ensure Tesseract OCR is installed and the path is correctly set in the script if needed.
    * Use clear, high-contrast images for better OCR accuracy.
    * Toggle "Use OCR Context" in the sidebar to control whether the AI bases its answers on the last OCR'd text.
    * Clear history or extracted code from the sidebar when needed.
    """)