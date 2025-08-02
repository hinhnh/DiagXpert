from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer('all-MiniLM-L6-v2')

sentences = [
    "How do I reset my password?",
    "I forgot my password, what can I do?",
    "Where is the nearest restaurant?"
]

embeddings = model.encode(sentences, convert_to_tensor=True)

# So sánh độ tương đồng giữa 2 câu đầu
similarity = util.pytorch_cos_sim(embeddings[0], embeddings[1])
print(f"Similarity: {similarity.item():.4f}")
