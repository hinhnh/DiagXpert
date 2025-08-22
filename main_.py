import os
import logging
import tempfile
import re
import sqlite3
import uuid
from datetime import datetime
from flask import Flask, request, render_template, jsonify, session
from werkzeug.utils import secure_filename
from openai import AzureOpenAI
from dotenv import load_dotenv
from db.vector_db import VectorDatabase
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
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")

# Lịch sử đưa lên model: số lượt gần nhất (user+assistant = 1 lượt)
MAX_TURNS = int(os.getenv("CHAT_HISTORY_MAX_TURNS", "10"))

# Auto-summary cấu hình
SUMMARY_TRIGGER_MSGS = int(os.getenv("SUMMARY_TRIGGER_MSGS", "30"))       # bắt đầu tạo summary sau 30 message
SUMMARY_EVERY_N_MSGS = int(os.getenv("SUMMARY_EVERY_N_MSGS", "10"))       # sau đó cứ mỗi 10 message sẽ làm mới
SUMMARY_MAX_INPUT_CHARS = int(os.getenv("SUMMARY_MAX_INPUT_CHARS", "16000"))  # giới hạn input đưa vào tóm tắt

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
# Vector DB
# =========================
vector_db = VectorDatabase()
index_path = "faiss_index.pkl"
docs_path = "docs.pkl"
meta_path = "metadata.pkl"

if not os.path.exists(index_path) or not os.path.exists(docs_path) or not os.path.exists(meta_path):
    logger.warning("⚠️ One or more vector DB files missing, initializing empty DB.")
    vector_db.save(index_path, docs_path, meta_path)
else:
    vector_db.load(index_path, docs_path, meta_path)

logger.info("📂 Loaded vector database")

# =========================
# SQLite helpers
# =========================
DB_PATH = os.getenv("CHAT_HISTORY_DB_PATH", "chat_history.db")

def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def _init_db():
    with _get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user','assistant')),
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS session_summaries (
                session_id TEXT PRIMARY KEY,
                summary_text TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )
        conn.commit()

_init_db()
logger.info("🗄️ SQLite initialized at %s", DB_PATH)

def _get_or_create_session_id() -> str:
    sid = session.get("sid")
    if not sid:
        sid = uuid.uuid4().hex
        session["sid"] = sid
    return sid

def save_message(session_id: str, role: str, content: str) -> None:
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO messages (session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (session_id, role, content, datetime.utcnow().isoformat()),
        )
        conn.commit()

def count_messages(session_id: str) -> int:
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS c FROM messages WHERE session_id=?",
            (session_id,)
        ).fetchone()
    return int(row["c"] or 0)

def fetch_history(session_id: str, max_turns: int) -> list[dict]:
    """Trả về 2*max_turns messages gần nhất (theo thứ tự cũ → mới)."""
    limit = max_turns * 2
    with _get_conn() as conn:
        rows = conn.execute(
            """
            SELECT role, content, created_at
            FROM messages
            WHERE session_id=?
            ORDER BY id DESC
            LIMIT ?
            """,
            (session_id, limit),
        ).fetchall()
    rows = list(reversed(rows))
    return [{"role": r["role"], "content": r["content"], "created_at": r["created_at"]} for r in rows]

def fetch_full_history(session_id: str) -> list[sqlite3.Row]:
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT role, content, created_at FROM messages WHERE session_id=? ORDER BY id ASC",
            (session_id,)
        ).fetchall()
    return rows

def clear_history_db(session_id: str) -> int:
    with _get_conn() as conn:
        cur = conn.execute("DELETE FROM messages WHERE session_id=?", (session_id,))
        conn.commit()
        return cur.rowcount

def get_summary(session_id: str) -> str | None:
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT summary_text FROM session_summaries WHERE session_id=?",
            (session_id,)
        ).fetchone()
    return row["summary_text"] if row else None

def upsert_summary(session_id: str, summary_text: str) -> None:
    with _get_conn() as conn:
        now = datetime.utcnow().isoformat()
        conn.execute(
            """
            INSERT INTO session_summaries (session_id, summary_text, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                summary_text=excluded.summary_text,
                updated_at=excluded.updated_at
            """,
            (session_id, summary_text, now)
        )
        conn.commit()

def need_summary(session_id: str) -> bool:
    total = count_messages(session_id)
    if total < SUMMARY_TRIGGER_MSGS:
        return False
    # Làm mới mỗi N message
    return total % SUMMARY_EVERY_N_MSGS == 0

def build_summary_text_from_history(rows: list[sqlite3.Row]) -> str:
    """
    Gộp lịch sử thành plain text ngắn gọn để đưa vào prompt tóm tắt.
    Cắt bớt đầu nếu vượt quá SUMMARY_MAX_INPUT_CHARS.
    """
    lines = [f"{r['role'].upper()}: {r['content']}" for r in rows]
    joined = "\n".join(lines)
    if len(joined) > SUMMARY_MAX_INPUT_CHARS:
        joined = joined[-SUMMARY_MAX_INPUT_CHARS:]  # lấy đoạn cuối (gần đây) để tóm tắt
    return joined

def generate_summary(session_id: str) -> str:
    """Gọi model để tạo/tái tạo summary cho cả phiên."""
    rows = fetch_full_history(session_id)
    if not rows:
        return ""
    source = build_summary_text_from_history(rows)

    sys = (
        "You are a helpful assistant that writes compact, precise session summaries.\n"
        "Summarize the conversation for future context: keep key facts, decisions, user preferences, constraints,"
        " numeric values, and unresolved actions. Avoid fluff. Vietnamese output if user speaks Vietnamese."
    )
    prompt = (
        "Tóm tắt ngắn gọn cuộc hội thoại sau (gạch đầu dòng). "
        "Giữ kỹ thuật và số liệu chính xác. Nếu có bước hành động, liệt kê rõ.\n\n"
        f"---\n{source}\n---"
    )

    resp = client_chat.chat.completions.create(
        model=chat_model,
        messages=[
            {"role": "system", "content": sys},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
    )
    summary = resp.choices[0].message.content.strip()
    return summary

def maybe_update_summary(session_id: str) -> None:
    """Nếu đạt ngưỡng thì tạo/refresh summary và lưu DB."""
    if not need_summary(session_id):
        return
    try:
        summary = generate_summary(session_id)
        upsert_summary(session_id, summary)
        logger.info("📝 Session %s summary updated (%d chars)", session_id, len(summary))
    except Exception:
        logger.exception("Failed to generate/update summary")

# =========================
# File reading & chunking
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
# Message builder
# =========================
def _build_messages_with_history(context: str, user_input: str, hist: list[dict], summary_text: str | None) -> list[dict]:
    # system 1: role dự án + context RAG
    base_system = {
        "role": "system",
        "content": (
            "You are DiagXpert, an AI assistant for automotive diagnostics.\n"
            "Use the following technical context to answer user questions accurately.\n"
            f"Context:\n{context}"
        ),
    }

    messages = [base_system]

    # system 2 (nếu có): session summary giúp model giữ ngữ cảnh dài hạn
    if summary_text:
        messages.append({
            "role": "system",
            "content": (
                "Session summary (for continuity):\n"
                f"{summary_text}"
            )
        })

    # thêm history rút gọn theo MAX_TURNS
    hist_msgs = [{"role": h["role"], "content": h["content"]} for h in hist]
    messages += hist_msgs

    # user hiện tại
    messages.append({"role": "user", "content": user_input})
    return messages

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

        if filename.lower().endswith(".docx"):
            content = read_docx(file_path)
        elif filename.lower().endswith(".pdf"):
            content = read_pdf(file_path)
        else:
            logger.warning(f"Unsupported file type: {filename}")
            return jsonify({"error": "⚠️ Unsupported file type"}), 400

        chunks = chunk_text(content, max_chars=1000)
        logger.info(f"📦 Split into {len(chunks)} chunks for file: {filename}")

        for i, chunk in enumerate(chunks):
            embedding_resp = client_embed.embeddings.create(
                model=embedding_model,
                input=chunk
            )
            _ = embedding_resp.data[0].embedding  # nếu VectorDatabase cần thì dùng
            vector_db.insert_text(chunk, metadata={"source": filename, "chunk": i})
            logger.info(f"🔹 Inserted chunk {i+1}/{len(chunks)}")

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

@app.route("/ask", methods=["POST"])
def ask():
    user_input = request.json.get("question", "").strip()
    logger.info(f"📥 User input: {user_input}")

    if not user_input:
        return jsonify({"answer": "⚠️ Please provide a valid question."}), 400

    try:
        session_id = _get_or_create_session_id()

        # RAG context
        results = vector_db.query_with_metadata(user_input, top_k=3)
        context_list = []
        for doc, score, meta in results:
            score_val = score.get("distance", score.get("score", 0)) if isinstance(score, dict) else score
            context_list.append(doc)
            logger.info("🔹 Retrieved chunk: %.60s... | score=%s | metadata=%s",
                        doc, repr(score_val), repr(meta))
        context = "\n---\n".join(context_list)

        # Lịch sử + summary
        hist = fetch_history(session_id, MAX_TURNS)
        summary_text = get_summary(session_id)

        # Build messages
        messages = _build_messages_with_history(context, user_input, hist, summary_text)

        # Gọi model
        response = client_chat.chat.completions.create(
            model=chat_model,
            messages=messages,
            temperature=0,
        )
        answer = response.choices[0].message.content.strip()

        # Lưu message & auto-summary nếu cần
        save_message(session_id, "user", user_input)
        save_message(session_id, "assistant", answer)
        maybe_update_summary(session_id)

        return jsonify({"answer": answer})

    except Exception as e:
        logger.exception("❌ Error during answer generation")
        return jsonify({"answer": f"❌ Error: {str(e)}"}), 500

@app.route("/history", methods=["GET"])
def get_history():
    session_id = _get_or_create_session_id()
    # cho xem nhiều hơn khi xem lịch sử
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT role, content, created_at FROM messages WHERE session_id=? ORDER BY id ASC",
            (session_id,)
        ).fetchall()
    hist = [{"role": r["role"], "content": r["content"], "created_at": r["created_at"]} for r in rows]
    return jsonify({"history": hist, "count": len(hist)})

@app.route("/clear_history", methods=["POST"])
def clear_history():
    session_id = _get_or_create_session_id()
    deleted = clear_history_db(session_id)
    # clear luôn summary
    upsert_summary(session_id, "")
    return jsonify({"message": f"🧹 Cleared {deleted} messages for this session and reset summary."})

@app.route("/summary", methods=["GET"])
def get_summary_api():
    session_id = _get_or_create_session_id()
    return jsonify({
        "session_id": session_id,
        "summary": get_summary(session_id) or "",
    })

@app.route("/rebuild_summary", methods=["POST"])
def rebuild_summary_api():
    session_id = _get_or_create_session_id()
    try:
        summary = generate_summary(session_id)
        upsert_summary(session_id, summary)
        return jsonify({"message": "✅ Summary rebuilt.", "summary": summary})
    except Exception as e:
        logger.exception("❌ Error rebuilding summary")
        return jsonify({"error": str(e)}), 500

# =========================
# Run app
# =========================
if __name__ == "__main__":
    app.run(debug=True)
