import requests
import json

# =========================
# Cấu hình backend
# =========================
BACKEND_URL = "http://127.0.0.1:5000/ask"  # URL backend Flask của bạn

# =========================
# Danh sách câu hỏi test
# =========================
questions = [
    "Khi nào cần thay dầu động cơ?",
    "Kiểm tra mức dầu động cơ bao lâu một lần?",
    "Bao lâu nên kiểm tra áp suất và tình trạng lốp?",
    "Khi nào cần xoay lốp xe để mòn đều?",
    "Khi nào cần thay má phanh?",
    "Kiểm tra má phanh và dầu phanh bao lâu một lần?",
    "Bao lâu cần vệ sinh cực ắc quy và kiểm tra điện áp?",
    "Tuổi thọ trung bình của ắc quy là bao nhiêu năm?",
    "Khi nào cần kiểm tra mức nước làm mát?",
    "Bao lâu cần xả và thay nước làm mát?",
]

# =========================
# Hàm gửi câu hỏi đến backend
# =========================
def ask_question(question: str):
    payload = {"question": question}
    try:
        response = requests.post(BACKEND_URL, json=payload)
        try:
            data = response.json()
            if "answer" in data:
                print(f"\n❓ Question: {question}")
                print(f"💬 Answer: {data['answer']}")
            else:
                print(f"\n❌ No answer returned for: {question}")
                print(data)
        except json.JSONDecodeError:
            print(f"\n❌ Response is not JSON for question: {question}")
            print(response.text)
    except Exception as e:
        print(f"\n❌ Error for question: {question}\n{e}")

# =========================
# Gửi tất cả câu hỏi
# =========================
for q in questions:
    ask_question(q)
