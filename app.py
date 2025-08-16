import os
import logging
import tempfile
import re
from flask import Flask, request, render_template, jsonify
from werkzeug.utils import secure_filename
from openai import AzureOpenAI
from dotenv import load_dotenv
from db.vector_db import VectorDatabase
from db.chat_history import ChatHistoryManager
from docx import Document
import PyPDF2

# =========================
# Load environment & logging
# =========================
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =========================
# Flask setup
# =========================
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload

# =========================
# Azure OpenAI setup
# =========================
client_chat = AzureOpenAI(
    api_version="2024-07-01-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT_CHAT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY_CHAT"),
)
client_embed = AzureOpenAI(
    api_version="2024-07-01-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT_EMBED"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY_EMBED"),
)

chat_model = os.getenv("AZURE_OPENAI_CHAT_MODEL", "GPT-4o-mini")
embedding_model = os.getenv("AZURE_OPENAI_MODEL_EMBED", "text-embedding-3-small")

# =========================
# Vector DB & Chat History
# =========================
vector_db = VectorDatabase()
chat_history = ChatHistoryManager()

index_path = "faiss_index.pkl"
docs_path = "docs.pkl"
meta_path = "metadata.pkl"

if not os.path.exists(index_path) or not os.path.exists(docs_path) or not os.path.exists(meta_path):
    logger.warning("⚠️ One or more vector DB files missing, initializing empty DB.")
    vector_db.save(index_path, docs_path, meta_path)
else:
    vector_db.load(index_path, docs_path, meta_path)

logger.info("📂 Loaded vector database")
logger.info("💬 Initialized chat history manager")

# =========================
# Helper functions
# =========================
def read_docx(file_path: str) -> str:
    doc = Document(file_path)
    return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

def read_pdf(file_path: str) -> str:
    text = []
    with open(file_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text.append(page_text)
    return "\n".join(text)

def chunk_text(text, max_chars=1000):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    chunk = ""
    for s in sentences:
        if len(chunk) + len(s) + 1 > max_chars:
            if chunk:
                chunks.append(chunk.strip())
            chunk = s
        else:
            chunk += " " + s
    if chunk:
        chunks.append(chunk.strip())
    return chunks

# =========================
# Routes
# =========================
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/insert_file", methods=["POST"])
def insert_file():
    file = request.files.get("file")
    if not file:
        logger.warning("No file received in request!")
        return jsonify({"error": "⚠️ No file uploaded"}), 400

    filename = secure_filename(file.filename)
    suffix = os.path.splitext(filename)[1]

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            file_path = tmp.name
            file.save(file_path)
        logger.info(f"📄 Saved uploaded file: {file_path}")

        # Read file content
        if filename.lower().endswith(".docx"):
            content = read_docx(file_path)
        elif filename.lower().endswith(".pdf"):
            content = read_pdf(file_path)
        else:
            logger.warning(f"Unsupported file type: {filename}")
            return jsonify({"error": "⚠️ Unsupported file type"}), 400

        # Chunk text
        chunks = chunk_text(content, max_chars=1000)
        logger.info(f"📦 Split into {len(chunks)} chunks for file: {filename}")

        # Insert each chunk
        for i, chunk in enumerate(chunks):
            embedding_resp = client_embed.embeddings.create(
                model=embedding_model,
                input=chunk
            )
            embedding_vector = embedding_resp.data[0].embedding
            vector_db.insert_text(chunk, metadata={"source": filename, "chunk": i})
            logger.info(f"🔹 Inserted chunk {i+1}/{len(chunks)}")

        # Save updated DB
        vector_db.save(index_path, docs_path, meta_path)
        logger.info(f"✅ Finished inserting all chunks from {filename}")

        return jsonify({"message": f"✅ Inserted {len(chunks)} chunks from {filename}"})

    except Exception as e:
        logger.exception("❌ Error inserting file into vector db")
        return jsonify({"error": str(e)}), 500

    finally:
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"🗑 Removed temporary file: {file_path}")

# =========================
# Chat History Routes
# =========================
@app.route("/chat/sessions", methods=["GET"])
def get_chat_sessions():
    """Lấy danh sách tất cả phiên chat"""
    try:
        sessions = chat_history.get_all_sessions()
        return jsonify({
            "sessions": sessions,
            "current_session_id": chat_history.current_session_id
        })
    except Exception as e:
        logger.exception("❌ Error getting chat sessions")
        return jsonify({"error": str(e)}), 500

@app.route("/chat/session/new", methods=["POST"])
def new_chat_session():
    """Tạo phiên chat mới"""
    try:
        new_session_id = chat_history.start_new_session()
        return jsonify({
            "message": "✅ Started new chat session",
            "session_id": new_session_id
        })
    except Exception as e:
        logger.exception("❌ Error creating new chat session")
        return jsonify({"error": str(e)}), 500

@app.route("/chat/session/<session_id>", methods=["POST"])
def switch_chat_session(session_id):
    """Chuyển sang phiên chat khác"""
    try:
        success = chat_history.switch_session(session_id)
        if success:
            # Lấy lịch sử của phiên này để hiển thị
            context_messages = chat_history.get_current_session_context(max_messages=50)
            return jsonify({
                "message": "✅ Switched to session",
                "session_id": session_id,
                "messages": context_messages
            })
        else:
            return jsonify({"error": "❌ Session not found"}), 404
    except Exception as e:
        logger.exception("❌ Error switching chat session")
        return jsonify({"error": str(e)}), 500

@app.route("/chat/session/<session_id>", methods=["DELETE"])
def delete_chat_session(session_id):
    """Xóa phiên chat"""
    try:
        success = chat_history.delete_session(session_id)
        if success:
            return jsonify({
                "message": "✅ Deleted session",
                "current_session_id": chat_history.current_session_id
            })
        else:
            return jsonify({"error": "❌ Session not found"}), 404
    except Exception as e:
        logger.exception("❌ Error deleting chat session")
        return jsonify({"error": str(e)}), 500

@app.route("/chat/history", methods=["GET"])
def get_chat_history():
    """Lấy lịch sử chat của phiên hiện tại"""
    try:
        messages = chat_history.get_current_session_context(max_messages=100)
        return jsonify({
            "session_id": chat_history.current_session_id,
            "messages": messages
        })
    except Exception as e:
        logger.exception("❌ Error getting chat history")
        return jsonify({"error": str(e)}), 500

@app.route("/chat/clear", methods=["POST"])
def clear_chat_history():
    """Xóa toàn bộ lịch sử chat"""
    try:
        chat_history.clear_all_history()
        return jsonify({"message": "✅ Cleared all chat history"})
    except Exception as e:
        logger.exception("❌ Error clearing chat history")
        return jsonify({"error": str(e)}), 500

@app.route("/ask", methods=["POST"])
def ask():
    user_input = request.json.get("question", "").strip()
    logger.info(f"📥 User input: {user_input}")

    if not user_input:
        return jsonify({"answer": "⚠️ Please provide a valid question."}), 400

    try:
        # Lưu câu hỏi của user vào lịch sử
        chat_history.add_message("user", user_input)
        
        # Query vector DB with metadata
        results = vector_db.query_with_metadata(user_input, top_k=3)

        # Prepare context from vector DB
        context_list = []
        for doc, score, meta in results:
            # Nếu score là dict (FAISS hoặc embedding trả về dict), lấy distance
            if isinstance(score, dict):
                score_val = score.get("distance", score.get("score", 0))
            else:
                score_val = score
            context_list.append(doc)
            logger.info("🔹 Retrieved chunk: %.60s... | score=%s | metadata=%s",
                        doc, repr(score_val), repr(meta))

        context = "\n---\n".join(context_list)

        # Lấy enhanced context (recent + semantic search)
        enhanced_context = chat_history.get_enhanced_context(user_input, max_recent=4, max_semantic=2)

        # Build messages với context từ vector DB và enhanced conversation history
        messages = [
            {"role": "system", "content": (
                "You are DiagXpert, an AI assistant for automotive diagnostics.\n"
                "Use the following technical context and conversation history to answer user questions accurately.\n"
                "The conversation history includes both recent messages and semantically relevant messages from previous conversations.\n"
                f"Technical Context:\n{context}"
            )}
        ]
        
        # Thêm enhanced context (đã bao gồm cả recent và semantic)
        for msg in enhanced_context:
            # Bỏ qua tin nhắn hiện tại (chưa có response)
            if msg.get("content") != user_input:
                messages.append({
                    "role": msg["role"], 
                    "content": msg["content"]
                })
        
        # Thêm tin nhắn hiện tại
        messages.append({"role": "user", "content": user_input})

        # Call Azure OpenAI chat
        response = client_chat.chat.completions.create(
            model=chat_model,
            messages=messages,
            temperature=0,
        )
        answer = response.choices[0].message.content.strip()
        
        # Lưu câu trả lời vào lịch sử
        chat_history.add_message("assistant", answer, metadata={
            "context_chunks_used": len(context_list),
            "vector_search_results": len(results),
            "enhanced_context_used": len(enhanced_context)
        })
        
        return jsonify({"answer": answer})

    except Exception as e:
        logger.exception("❌ Error during answer generation")
        error_msg = f"❌ Error: {str(e)}"
        # Lưu lỗi vào lịch sử
        chat_history.add_message("assistant", error_msg, metadata={"error": True})
        return jsonify({"answer": error_msg}), 500

# =========================
# Run app
# =========================
if __name__ == "__main__":
    app.run(debug=True)
