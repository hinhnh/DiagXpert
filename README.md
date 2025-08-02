# DiagXpert: Automotive Diagnostic Chatbot

**DiagXpert** is an AI-powered chatbot application designed for diagnosing automotive errors. It is built with Flask, Azure OpenAI, and FAISS to perform semantic search and generate context-aware responses.

---

## 🧠 Features

- Semantic search using FAISS vector database.
- Retrieval-Augmented Generation (RAG) with Azure GPT.
- Simple web interface for user interaction.
- Contextual answers in both English and Vietnamese.
- Easily extendable to support more technical documents.

---

## 🗂 Project Structure

```
DiagXpert/
├── db/
│   ├── __init__.py
│   └── vector_db.py              # FAISS vector store logic
├── static/
│   └── style.css                 # Frontend styles
├── templates/
│   └── index.html                # Main HTML interface
├── docs.pkl                      # Preprocessed document data
├── faiss_index.pkl               # FAISS vector index
├── main.py                       # Flask app entry point
├── .env                          # Environment variables (API keys)
├── requirements.txt              # Python dependencies
```

---

## ⚙️ Installation & Running the App

### 1. Clone and install dependencies

```bash
git clone https://github.com/your-org/DiagXpert.git
cd DiagXpert
python -m venv venv
source venv/bin/activate         # Or venv\\Scripts\\activate on Windows
pip install -r requirements.txt
```

### 2. Configure `.env`

Create a `.env` file with your Azure OpenAI credentials:

```
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment-name
```

### 3. Run the App

```bash
python main.py
```

Then visit [http://localhost:5000](http://localhost:5000) in your browser to use the chatbot.

---

## 📘 Updating Data

To add more technical data:

1. Convert new documents into plain text or JSON.
2. Run a script to generate embeddings and update `faiss_index.pkl` and `docs.pkl`.
3. Restart the app to load the new data.

---

## 💬 Sample Q&A

```text
Q: The car won't start. What should I check?
A: You should inspect the spark plugs and ignition system.

Q: Xe không nổ máy, tôi nên kiểm tra gì?
A: Bạn nên kiểm tra bugi và hệ thống đánh lửa.
```

---

## ✅ System Requirements

- Python >= 3.8
- Azure OpenAI account
- Required libraries:
  - Flask
  - openai
  - faiss-cpu
  - python-dotenv

---

