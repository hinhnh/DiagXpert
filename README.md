# DiagXpert – AI Chatbot for Automotive Diagnostics

DiagXpert is a web application built with **Flask**, integrated with **Azure OpenAI** and **FAISS vector database**, to assist engineers and technicians in retrieving technical information and diagnosing vehicle issues. The system can process DOCX and PDF files, extract content, store it in a vector database, and answer questions based on the stored content.

---

## 🔹 Features

- Upload and process DOCX and PDF files.
- Split text into smaller chunks for embedding.
- Store and query information using **FAISS vector database**.
- AI chatbot answers technical questions based on stored content.
- Uses Azure OpenAI for **embeddings** and **chat completion**.

---

## 🛠️ System Requirements

- Python >= 3.10
- Install required libraries:
  ```bash
  pip install flask python-dotenv openai PyPDF2 python-docx werkzeug
  ```
- Azure OpenAI account with endpoints and keys for Chat completions and Embeddings.

---

## ⚙️ Environment Configuration

Create a `.env` file with:

```env
AZURE_OPENAI_ENDPOINT_CHAT=<your_chat_endpoint>
AZURE_OPENAI_API_KEY_CHAT=<your_chat_api_key>
AZURE_OPENAI_ENDPOINT_EMBED=<your_embedding_endpoint>
AZURE_OPENAI_API_KEY_EMBED=<your_embedding_api_key>
AZURE_OPENAI_CHAT_MODEL=GPT-4o-mini
AZURE_OPENAI_MODEL_EMBED=text-embedding-3-small
```

---

## 📝 Project Structure

```
project/
│
├─ app.py                # Main Flask app
├─ db/
│  └─ vector_db.py       # FAISS vector DB management class
├─ templates/
│  └─ index.html         # Front-end web page
├─ faiss_index.pkl        # FAISS index
├─ docs.pkl               # Stored document content
├─ metadata.pkl           # Chunk metadata
└─ .env                  # Environment variables
```

---

## 🚀 Running the Application

```bash
python app.py
```

- Access the application at [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 📂 Uploading Files

- Endpoint: `POST /insert_file`
- Supported formats: `.docx`, `.pdf`
- Process:
  1. Save temporary file.
  2. Extract content.
  3. Split content into chunks (\~1000 characters per chunk).
  4. Generate embeddings and insert into FAISS DB.
  5. Delete temporary file.

**Response example:**

```json
{
  "message": "✅ Inserted 5 chunks from example.pdf"
}
```

---

## 💬 Asking Questions

- Endpoint: `POST /ask`
- Request body example:

```json
{
  "question": "How to reset the ECU?"
}
```

- Process:
  1. Query the vector DB with top 3 relevant chunks.
  2. Send context and user question to Azure OpenAI Chat model.
  3. Return answer based on context.

**Response example:**

```json
{
  "answer": "To reset the ECU, you need to..."
}
```

---

## 🔹 Logging & Debug

- Tracks:
  - File upload
  - Chunking
  - Embedding creation
  - Database queries
  - OpenAI Chat calls

---

## ⚠️ Notes

- Maximum file size: 16 MB.
- If vector DB files (`faiss_index.pkl`, `docs.pkl`, `metadata.pkl`) are missing, an empty database is initialized.
- Only `.docx` and `.pdf` files are supported.

---

## 🔧 Extensibility

- Add support for other file types: TXT, CSV, etc.
- Increase `top_k` chunks when querying.
- Enhance front-end interface for better user experience.

