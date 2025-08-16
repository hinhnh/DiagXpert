import os
from flask import Flask, request, render_template, jsonify
from openai import AzureOpenAI
from dotenv import load_dotenv
from db.vector_db import VectorDatabase  
import logging

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask
app = Flask(__name__)

# Read config from .env
azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
deployment_name = os.getenv("AZURE_DEPLOYMENT_NAME")

if not all([azure_endpoint, azure_api_key, deployment_name]):
    raise ValueError("⚠️ Missing Azure OpenAI configuration in .env (check ENDPOINT, API_KEY, DEPLOYMENT).")

# Initialize OpenAI client
client = AzureOpenAI(
    api_version="2024-07-01-preview",
    azure_endpoint=azure_endpoint,
    api_key=azure_api_key,
)

# Load vector database
vector_db = VectorDatabase()
vector_db.load("faiss_index.pkl", "docs.pkl")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    user_input = request.json.get("question", "").strip()
    logger.info(f"📥 User input: {user_input}")

    if not user_input:
        return jsonify({"answer": "⚠️ Please provide a valid question."}), 400

    try:
        # Retrieve top-k documents
        results = vector_db.query(user_input, top_k=3)
        context = "\n---\n".join([doc for doc, _ in results])
        logger.info(f"📚 Retrieved context:\n{context}")

        # Build messages for GPT (STRICT RAG)
        messages = [
            {"role": "system", "content": (
                "You are DiagXpert, an AI assistant for automotive diagnostics.\n"
                "You MUST strictly answer based ONLY on the provided context below.\n"
                "If the context does not contain the answer, reply exactly with: "
                "'I don't know based on the provided context.'\n\n"
                f"Context:\n{context}"
            )},
            {"role": "user", "content": user_input}
        ]

        # Call OpenAI
        response = client.chat.completions.create(
            model=deployment_name,
            messages=messages,
            temperature=0,
        )
        answer = response.choices[0].message.content.strip()
        return jsonify({
            "answer": answer,
            "context_used": context  # 👈 trả về context để debug nếu cần
        })

    except Exception as e:
        logger.exception("❌ Error during answer generation")
        return jsonify({"answer": f"❌ Error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
