#!/usr/bin/env python3
"""
Script debug vector search để kiểm tra tại sao không tìm thấy documents về pin
"""

import pickle
import sys
import os

# Thêm src vào path
sys.path.insert(0, 'src')

from db.vector_db import VectorDatabase

def debug_vector_search():
    """Debug vector search với câu hỏi về pin"""
    
    print("🔍 Debug Vector Search cho câu hỏi: 'Pin ô tô có mấy loại?'")
    print("=" * 60)
    
    # Tải database
    docs_path = "data/docs.pkl"
    index_path = "data/faiss_index.pkl"
    
    if not os.path.exists(docs_path):
        print("❌ Không tìm thấy database docs.pkl")
        return
    
    if not os.path.exists(index_path):
        print("❌ Không tìm thấy vector index faiss_index.pkl")
        return
    
    print("📚 Đang tải database...")
    
    # Tải documents
    with open(docs_path, 'rb') as f:
        docs = pickle.load(f)
    
    print(f"📚 Tổng documents: {len(docs)}")
    
    # Hiển thị tất cả documents
    print("\n📄 Tất cả documents:")
    for i, doc in enumerate(docs):
        doc_preview = doc[:100] + "..." if len(doc) > 100 else doc
        print(f"  Doc {i+1}: {doc_preview}")
    
    # Khởi tạo VectorDatabase
    print("\n🔧 Đang khởi tạo VectorDatabase...")
    vector_db = VectorDatabase()
    
    # Load index
    print("📂 Đang load vector index...")
    vector_db.load(index_path, docs_path)
    
    print(f"✅ Loaded index với {len(vector_db.documents)} documents")
    
    # Test query
    query = "Pin ô tô có mấy loại?"
    print(f"\n🔍 Test query: '{query}'")
    
    # Search với top_k cao hơn để xem tất cả results
    results = vector_db.query(query, top_k=10)
    
    if results:
        print(f"\n📊 Vector search results (top {len(results)}):")
        for i, (doc, score) in enumerate(results):
            doc_preview = doc[:100] + "..." if len(doc) > 100 else doc
            print(f"  Result {i+1}: Score {score:.4f}")
            print(f"    Content: {doc_preview}")
            print()
    else:
        print("❌ Không có kết quả nào!")
    
    # Kiểm tra documents có từ "battery" hoặc "pin"
    print("\n🔍 Kiểm tra documents có từ 'battery' hoặc 'pin':")
    battery_docs = []
    for i, doc in enumerate(docs):
        if 'battery' in doc.lower() or 'pin' in doc.lower():
            battery_docs.append((i+1, doc))
    
    if battery_docs:
        print(f"✅ Tìm thấy {len(battery_docs)} documents về battery/pin:")
        for doc_num, doc in battery_docs:
            doc_preview = doc[:100] + "..." if len(doc) > 100 else doc
            print(f"  Doc {doc_num}: {doc_preview}")
    else:
        print("❌ Không tìm thấy documents nào về battery/pin!")

if __name__ == "__main__":
    debug_vector_search()
