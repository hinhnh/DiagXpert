#!/usr/bin/env python3
"""
Script dọn dẹp database, loại bỏ documents trùng lặp
"""

import pickle
import os
from typing import List, Tuple

def clean_database():
    """Dọn dẹp database, loại bỏ documents trùng lặp"""
    
    # Đường dẫn database
    docs_path = "data/docs.pkl"
    index_path = "data/faiss_index.pkl"
    
    if not os.path.exists(docs_path):
        print("❌ Không tìm thấy database docs.pkl")
        return
    
    print("🔍 Đang tải database...")
    
    # Tải documents
    with open(docs_path, 'rb') as f:
        docs = pickle.load(f)
    
    print(f"📚 Tổng documents: {len(docs)}")
    
    # Tìm documents trùng lặp
    unique_docs = []
    duplicate_count = 0
    
    for i, doc in enumerate(docs):
        doc_content = doc.strip()
        
        # Kiểm tra trùng lặp
        is_duplicate = False
        for unique_doc in unique_docs:
            if doc_content == unique_doc.strip():
                is_duplicate = True
                duplicate_count += 1
                print(f"⚠️ Document {i+1} trùng lặp với document trước đó")
                break
        
        if not is_duplicate:
            unique_docs.append(doc_content)
            print(f"✅ Document {i+1}: {doc_content[:50]}...")
    
    print(f"\n📊 Kết quả dọn dẹp:")
    print(f"   • Documents ban đầu: {len(docs)}")
    print(f"   • Documents trùng lặp: {duplicate_count}")
    print(f"   • Documents sau dọn dẹp: {len(unique_docs)}")
    
    if duplicate_count > 0:
        # Backup database cũ
        backup_path = "data/docs_backup.pkl"
        with open(backup_path, 'wb') as f:
            pickle.dump(docs, f)
        print(f"💾 Backup database cũ: {backup_path}")
        
        # Lưu database mới
        with open(docs_path, 'wb') as f:
            pickle.dump(unique_docs, f)
        print(f"💾 Lưu database mới: {docs_path}")
        
        print("⚠️ Lưu ý: Database cũ đã được backup. Bạn cần rebuild vector index!")
        print("💡 Chạy: python -c \"from db.vector_db import VectorDatabase; VectorDatabase().rebuild_index()\"")
    else:
        print("✅ Database đã sạch, không có documents trùng lặp!")

if __name__ == "__main__":
    clean_database()
