# 🚗 Resource Folder - Automotive Training Documents

## 📁 **Mô tả:**
Folder này chứa các tài liệu mẫu về ô tô để test chức năng upload và training của DiagXpert AI system.

## 📚 **Các tài liệu có sẵn:**

### **1. 🔥 Engine Diagnostics (`engine_diagnostics.docx`)**
- **Nội dung:** Engine overheating symptoms, causes, diagnostic procedures
- **Chủ đề:** Cooling system, thermostat, water pump, head gasket
- **Ứng dụng:** Test RAG với engine problems

### **2. 🔋 Battery System (`battery_system.docx`)**
- **Nội dung:** Battery types, problems, maintenance, testing
- **Chủ đề:** Lead-acid, AGM, charging system, diagnostics
- **Ứng dụng:** Test vector search với battery issues

### **3. 🛑 Brake System (`brake_system.docx`)**
- **Nội dung:** Brake components, problems, maintenance, safety
- **Chủ đề:** Disc brakes, drum brakes, ABS, brake fluid
- **Ứng dụng:** Test batching với brake maintenance

### **4. ⚡ Electrical System (`electrical_system.docx`)**
- **Nội dung:** Electrical circuits, problems, testing, repairs
- **Chủ đề:** Starting system, charging system, lighting, diagnostics
- **Ứng dụng:** Test RAG với electrical issues

## 🎯 **Cách sử dụng để test DiagXpert:**

### **Bước 1: Upload Documents**
1. Mở DiagXpert web interface
2. Vào tab **"Upload Documents"**
3. Chọn các file .docx từ folder này
4. Click **"Upload to Vector DB"**

### **Bước 2: Test AI Chat**
1. Vào tab **"Chat"**
2. Hỏi các câu hỏi như:
   - "Làm sao để sửa lỗi engine nóng?"
   - "Cách kiểm tra battery?"
   - "Vấn đề về brake system?"
   - "Electrical system troubleshooting?"

### **Bước 3: Test Workshop 4 Features**
```bash
python run.py workshop4
```

## 🔍 **Test Scenarios:**

### **Scenario 1: Engine Overheating**
- **Upload:** `engine_diagnostics.docx`
- **Question:** "What are the symptoms of engine overheating?"
- **Expected:** AI trả lời dựa trên symptoms từ document

### **Scenario 2: Battery Problems**
- **Upload:** `battery_system.docx`
- **Question:** "How to test battery voltage?"
- **Expected:** AI trả lời về voltage testing procedures

### **Scenario 3: Brake Maintenance**
- **Upload:** `brake_system.docx`
- **Question:** "When to replace brake pads?"
- **Expected:** AI trả lời về maintenance schedule

### **Scenario 4: Electrical Issues**
- **Upload:** `electrical_system.docx`
- **Question:** "Common electrical problems?"
- **Expected:** AI trả lời về electrical troubleshooting

## 🧠 **AI Learning Process:**

```
1. 📤 Upload Documents → Extract Text
2. 🧠 Create Embeddings → Vector Database
3. 🔍 Semantic Search → Find Relevant Info
4. 🔄 RAG Pipeline → Context + Generation
5. 🤖 AI Response → Based on Knowledge Base
```

## 📊 **Expected Results:**

- **Vector Search:** Tìm documents liên quan đến query
- **RAG Techniques:** Bổ sung context vào AI response
- **Batching:** Xử lý nhiều documents cùng lúc
- **AI Accuracy:** Trả lời chính xác dựa trên documents

## ⚠️ **Lưu ý:**

- Documents này chỉ để test, không phải tài liệu chuyên môn thực tế
- Format .docx để test file processing capabilities
- Nội dung đa dạng để test semantic search
- Có thể thêm documents khác để mở rộng knowledge base

---

**Happy Testing! 🚀**
