#!/usr/bin/env python3
"""
Script rebuild vector index sau khi dọn dẹp database
"""

import pickle
import os
from db.vector_db import VectorDatabase

def rebuild_index():
    """Rebuild vector index từ documents đã dọn dẹp"""
    
    docs_path = "data/docs.pkl"
    
    if not os.path.exists(docs_path):
        print("❌ Không tìm thấy database docs.pkl")
        return
    
    print("🔍 Đang tải documents đã dọn dẹp...")
    
    # Tải documents
    with open(docs_path, 'rb') as f:
        docs = pickle.load(f)
    
    print(f"📚 Documents: {len(docs)}")
    
    # Khởi tạo VectorDatabase
    print("🔧 Đang khởi tạo VectorDatabase...")
    vector_db = VectorDatabase()
    
    # Build index mới
    print("🏗️ Đang build vector index...")
    vector_db.build(docs)
    
    # Lưu index mới
    print("💾 Đang lưu vector index...")
    vector_db.save("data/faiss_index.pkl", "data/docs.pkl")
    
    print("✅ Đã rebuild vector index thành công!")
    print(f"📊 Index mới: {len(vector_db.documents)} documents")

if __name__ == "__main__":
    rebuild_index()
