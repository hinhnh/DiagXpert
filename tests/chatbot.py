"""
chatbot.py

This module provides a simple `ask()` function to send questions to the locally running chatbot API.
"""

import requests

API_URL = "http://127.0.0.1:5000/ask"

def ask(question: str) -> str:
    """
    Sends a question to the chatbot server and returns the response.

    Args:
        question (str): The user’s question.

    Returns:
        str: The chatbot's answer as a plain text string.
    """
    try:
        response = requests.post(API_URL, json={"question": question})
        response.raise_for_status()
        data = response.json()
        return data.get("answer", "[No answer returned]")
    except requests.exceptions.RequestException as e:
        return f"[Error contacting chatbot API: {e}]"
