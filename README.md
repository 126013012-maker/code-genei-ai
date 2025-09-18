---

# 🗨️ code-genei-ai

AI chatbot powered by **Ollama**, **Streamlit** for interactive text/code analysis.

---

## 🏆 Milestones & Features

### 1️⃣ Basic Ollama Chatbot (` chatbot_ollama.py `)

* Simple chatbot built in VS Code.
* Connected to **Ollama 3.2.1b** for conversational AI.
* Powered by **Streamlit** for an interactive web interface.
* Supports basic chatting functionality.

### 2️⃣ Enhanced UI Chatbot (`chatbot_ollama1.py`)

* Improved user interface for a better chat experience.
* Allows selection of **different Ollama models**.
* Designed with chat history, input/output styling, and responsive UI.
* Multiple models can be used for comparison and experimentation.

### 3️⃣ OCR-Integrated Chatbot (`ocr1.py`)

* Integrates **OCR text extraction** using **Pytesseract**.
* Automatically detects the programming language of code snippets (Python, C++, Java, JS).
* Interactive chatbot can respond **with or without OCR context**.
* Sidebar includes:

  * Chat history
  * OCR results
  * Code storage
* Supports multi-language OCR (English, French, Chinese, etc.) in advanced versions.

---

## 🛠️ Tech Stack

* Python 3.11+
* Streamlit for UI
* Ollama 3.2.1b for AI chat models
* Pytesseract for OCR
* Optional: OpenCV for OCR preprocessing

---

## ⚡ How to Run

1. **Activate your Python virtual environment**

```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

2. **Install required Python packages**

```bash
pip install streamlit
pip install pytesseract
pip install opencv-python   # Optional
```

3. **Download and install Ollama 3.2.1b**

* Follow the [Ollama installation guide](https://ollama.com/docs/installation).
* Ensure the Ollama executable is available in your system PATH.
* Start the Ollama server:

```bash
ollama serve
```

4. **Run your Streamlit app**

```bash
# Basic chatbot
streamlit run app.py

# Enhanced UI
streamlit run app1.py

# OCR-integrated chatbot
streamlit run ocr.py
```

5. **Open the chatbot in your browser**

* Go to: [http://localhost:8501](http://localhost:8501)
* Start chatting with the AI.

✅ **Notes:**

* Keep the virtual environment active while running the app.
* The Ollama server must stay running for chat functionality.
* Ensure **Tesseract OCR** is installed for OCR features.

---

## 📁 Project Files & Demo

### 📝 Python Scripts
| File                 | Description                                        |
| -------------------- | ---------------------------------------------------|
| app.py               | Main Streamlit chatbot app (Ollama connection)     |
| chatbot_ollama.py    | Simple Ollama chatbot (initial version)            |
| chatbot_ollama1.py   | Enhanced UI chatbot with multiple models           |
| ocr1.py              | OCR-integrated chatbot with code detection         |

### 📸 UI Screenshots

### 📄 UI PDFs
[View Chatbot UI](https://github.com/126013012-maker/code-genei-ai/blob/main/UI%20screenshot.pdf)  
[View Chatbot Output](https://github.com/126013012-maker/code-genei-ai/blob/main/UI%20screenshot-2.pdf)  

### 🎥 Demo Video
[Watch Chatbot Demo](https://github.com/126013012-maker/code-genei-ai/blob/main/chatbot%20output.mp4)







