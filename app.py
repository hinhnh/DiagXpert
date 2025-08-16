import os
import logging
import numpy as np
from flask import Flask, request, render_template, jsonify
from flask_cors import CORS
from openai import AzureOpenAI
from dotenv import load_dotenv
from db.vector_db import VectorDatabase
from scipy.io.wavfile import write as wav_write
from langdetect import detect

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask
app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)  # Enable CORS for all routes

# Initialize OpenAI client
client = AzureOpenAI(
    api_version="2024-07-01-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
)
deployment_name = "GPT-4o-mini"

# Load vector database
vector_db = VectorDatabase()
vector_db.load("faiss_index.pkl", "docs.pkl")

# Ensure audio folder exists
AUDIO_DIR = os.path.join("static", "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

# -------------------
# Audio save function
# -------------------
def save_audio_wav(audio_data, out_path, sr=24000):
    """Convert and save audio as 16-bit PCM WAV safely."""
    audio_array = np.array(audio_data)

    # Ensure mono/stereo is correct
    if audio_array.ndim > 1:
        channels = audio_array.shape[1]
    else:
        channels = 1

    # Normalize to 16-bit PCM
    if audio_array.dtype != np.int16:
        audio_array = np.int16(audio_array / np.max(np.abs(audio_array)) * 32767)

    logger.info(f"💾 Saving audio: {out_path}, SR={sr}, Channels={channels}")
    wav_write(str(out_path), sr, audio_array)


# -------------------
# Routes
# -------------------
@app.route("/")
def home():
    """Serve the main HTML interface."""
    return render_template("index.html")


@app.route("/ask", methods=["POST"])
def ask():
    user_input = request.json.get("question", "").strip()
    logger.info(f"📥 User input: {user_input}")

    if not user_input:
        return jsonify({"answer": "⚠️ Please provide a valid question."}), 400

    try:
        # Retrieve context from vector DB
        results = vector_db.query(user_input, top_k=3)
        context = "\n---\n".join([doc for doc, _ in results])
        logger.info(f"📚 Retrieved context:\n{context}")

        # Prepare prompt
        messages = [
            {"role": "system", "content": (
                "You are DiagXpert, an AI assistant for automotive diagnostics.\n"
                "Use the following technical context to answer user questions accurately.\n"
                f"Context:\n{context}"
            )},
            {"role": "user", "content": user_input}
        ]

        # Get AI response
        response = client.chat.completions.create(
            model=deployment_name,
            messages=messages,
            temperature=0,
        )
        answer = response.choices[0].message.content.strip()

        # Detect language
        lang = detect(answer)
        logger.info(f"🌐 Detected language: {lang}")

        # Select TTS model
        if lang.startswith("vi"):
            tts_model = os.getenv("AZURE_OPENAI_TTS_VI", "gpt-4o-mini-tts-vietnamese")
        else:
            tts_model = os.getenv("AZURE_OPENAI_TTS_EN", "gpt-4o-mini-tts")

        logger.info(f"🗣 Using TTS model: {tts_model}")

        # Generate TTS audio
        speech_response = client.audio.speech.create(
            model=tts_model,
            voice="alloy",
            input=answer
        )

        # Save audio to file
        audio_filename = f"{os.urandom(8).hex()}.wav"
        audio_path = os.path.join(AUDIO_DIR, audio_filename)

        audio_bytes = speech_response.read()
        audio_np = np.frombuffer(audio_bytes, dtype=np.int16)
        save_audio_wav(audio_np, audio_path, sr=24000)

        return jsonify({
            "answer": answer,
            "audio_url": f"/static/audio/{audio_filename}"
        })

    except Exception as e:
        logger.exception("❌ Error during answer generation")
        return jsonify({"answer": f"❌ Error: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True)
