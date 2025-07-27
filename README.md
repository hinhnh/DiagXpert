
# DiagXpert - AI Assistant for Automotive Manufacturing

DiagXpert is a web-based chatbot powered by Azure OpenAI that helps answer technical questions in the automotive manufacturing domain.

---

## 🚀 Features

- Built with **Flask** (Python)
- Uses **Azure OpenAI API** for GPT responses
- Designed for **clear, step-by-step answers** in technical settings

---

## 📁 Project Structure

```
.
├── app.py              # Main Flask application
├── .env                # Environment variables (not committed)
├── templates/
│   └── index.html      # Frontend UI
├── static/             # (Optional) CSS, JS, images
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

---

## ⚙️ Prerequisites

- Python 3.7+
- A deployed Azure OpenAI model (e.g., GPT-4o-mini)
- Your Azure OpenAI:
  - Endpoint
  - API Key

---

## 🧪 Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/<your-username>/DiagXpert.git
cd DiagXpert
```

### 2. Create Virtual Environment (optional but recommended)

```bash
python -m venv venv
source venv/bin/activate      # On Mac/Linux
venv\Scripts\activate         # On Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the root directory:

```ini
AZURE_OPENAI_ENDPOINT=https://<your-resource-name>.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
```

> 🔒 **Never commit your `.env` file.** It should be in `.gitignore`.

---

## ▶️ Run the App

```bash
python app.py
```

Open browser:  
📍 `http://127.0.0.1:5000/`

---

## 🧠 How It Works

- Sends user question to Azure OpenAI (e.g., GPT-4o-mini)
- Uses a system prompt to define assistant behavior
- Returns assistant's response as JSON to frontend

---

