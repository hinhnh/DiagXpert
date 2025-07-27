import os
from flask import Flask, request, render_template, jsonify
from openai import AzureOpenAI
from dotenv import load_dotenv

# Load environment variables from .env file (e.g., API keys, endpoints)
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Initialize Azure OpenAI client using credentials from environment variables
client = AzureOpenAI(
    api_version="2024-07-01-preview",  # API version of Azure OpenAI being used
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),  # Your Azure OpenAI endpoint
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),          # Your Azure OpenAI API key
)

# Name of the deployed model (e.g., "GPT-4o-mini")
deployment_name = "GPT-4o-mini"

# Define route for the homepage
@app.route("/")
def home():
    # Render the chatbot interface (HTML template)
    return render_template("index.html")

# Define route to handle user question (POST request)
@app.route("/ask", methods=["POST"])
def ask():
    # Get the user input (question) from the JSON request payload
    user_input = request.json.get("question", "")
    
    # Define the conversation context:
    # - System message defines the assistant's behavior and domain
    # - User message contains the actual question
    messages = [
        {"role": "system", "content": (
            "You are DiagXpert, an AI automotive manufacturing assistant. "
            "Answer technical questions clearly and concisely, using step-by-step instructions if needed.")},
        {"role": "user", "content": user_input}
    ]

    try:
        # Send the conversation to the Azure OpenAI API and get the response
        response = client.chat.completions.create(
            model=deployment_name,
            messages=messages,
            temperature=0,  # Use deterministic output (good for consistency)
        )
        # Extract the assistant's reply from the response object
        answer = response.choices[0].message.content.strip()

        # Return the answer to the frontend as a JSON response
        return jsonify({"answer": answer})
    
    except Exception as e:
        # If there's an error (e.g., API call failed), return the error message
        return jsonify({"answer": f"❌ Error: {str(e)}"}), 500

# Entry point for running the app locally
if __name__ == "__main__":
    app.run(debug=True)  # Enable debug mode for development (auto reloads on changes)
