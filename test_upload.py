#!/usr/bin/env python3
"""
Script test upload các file mới vào vector database
"""

import requests
import json
import os
from pathlib import Path

def test_upload_file(file_path):
    """Test upload một file"""
    url = "http://192.168.1.3:5050/upload"
    
    print(f"📤 Đang upload: {file_path.name}")
    
    try:
        with open(file_path, 'rb') as f:
            files = {'files': (file_path.name, f, 'application/octet-stream')}
            response = requests.post(url, files=files)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Upload thành công: {result.get('message', 'OK')}")
            return True
        else:
            print(f"❌ Upload thất bại: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Lỗi upload: {e}")
        return False

def test_ask_question(question):
    """Test hỏi câu hỏi sau khi upload"""
    url = "http://192.168.1.3:5050/ask"
    
    print(f"\n🤔 Hỏi: {question}")
    
    try:
        data = {'question': question}
        response = requests.post(url, json=data)
        
        if response.status_code == 200:
            result = response.json()
            answer = result.get('answer', '')
            print(f"🤖 Trả lời: {answer[:200]}...")
            return True
        else:
            print(f"❌ Lỗi API: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Lỗi hỏi câu hỏi: {e}")
        return False

def main():
    """Test upload và hỏi câu hỏi"""
    resource_dir = Path("resource")
    
    if not resource_dir.exists():
        print("❌ Không tìm thấy thư mục resource")
        return
    
    print("🧪 TEST UPLOAD FILES VÀ HỎI CÂU HỎI")
    print("=" * 50)
    
    # Danh sách file để test upload
    test_files = [
        "air_conditioning_system.txt",
        "fuel_injection_system.docx", 
        "transmission_system.doc",
        "suspension_system.docx"
    ]
    
    # Upload từng file
    uploaded_count = 0
    for file_name in test_files:
        file_path = resource_dir / file_name
        if file_path.exists():
            if test_upload_file(file_path):
                uploaded_count += 1
            print()
        else:
            print(f"⚠️ Không tìm thấy file: {file_name}")
    
    print(f"📊 Upload thành công: {uploaded_count}/{len(test_files)} files")
    
    if uploaded_count > 0:
        print("\n🔍 TEST HỎI CÂU HỎI VỀ CÁC CHỦ ĐỀ MỚI:")
        
        # Test các câu hỏi về chủ đề mới
        test_questions = [
            "Hệ thống điều hòa có những thành phần gì?",
            "Vòi phun nhiên liệu hoạt động như thế nào?",
            "Hộp số tự động có ưu điểm gì?",
            "Giảm chấn trong hệ thống treo có tác dụng gì?"
        ]
        
        for question in test_questions:
            test_ask_question(question)
            print("-" * 40)
    
    print("\n✅ Hoàn thành test!")

if __name__ == "__main__":
    main()
