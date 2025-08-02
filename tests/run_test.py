"""
run_test.py

This script loads questions from `test_questions.json`, sends them to the chatbot,
and checks if the response contains the expected phrase.
"""

import json
import os
from chatbot import ask  # Function to send questions to the chatbot

def run_tests():
    # Get the absolute path to the test_questions.json file located in the same directory as this script
    current_dir = os.path.dirname(__file__)
    test_file_path = os.path.join(current_dir, "test_questions.json")

    # Load the list of test cases from the JSON file
    with open(test_file_path, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    total = len(test_cases)
    passed = 0

    print("\n🔍 Running chatbot tests...\n")

    for i, case in enumerate(test_cases, start=1):
        question = case["question"]
        expected = case["expected_phrase"].lower()

        # Send the question to the chatbot and get its response
        response = ask(question)
        response_lower = response.lower()

        # Check if the expected phrase is in the chatbot's response
        result = "✅ PASS" if expected in response_lower else "❌ FAIL"
        if result.startswith("✅"):
            passed
