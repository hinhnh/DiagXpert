# 🚗 DiagXpert - AI Automotive Diagnostic Assistant

**Professional AI-powered automotive diagnostics with Workshop 4 core features**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)](https://flask.palletsprojects.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📚 **Tổng quan**

DiagXpert là một hệ thống AI chẩn đoán ô tô thông minh, tích hợp hoàn hảo với **Workshop 4: Core Features**. Hệ thống tập trung vào 4 mục tiêu chính:

- **🎯 FAISS/PineCone**: Fast Vector Search
- **🔗 Langchain**: Prompt & Chain Management  
- **🔧 Function Calling**: Dynamic Capabilities
- **📄 Prompt Handling**: Effective processing

## 🏗️ **Kiến trúc chuyên nghiệp**

```
DiagXpert/
├── 📁 src/                          # Source code chính
│   ├── 📁 config/                   # Configuration management
│   │   ├── __init__.py
│   │   └── settings.py              # Professional config system
│   ├── 📁 services/                 # Business logic services
│   │   ├── __init__.py
│   │   └── tts_service.py           # TTS with multiple engines
│   ├── 📁 utils/                    # Utility functions
│   │   ├── __init__.py
│   │   └── logger.py                # Professional logging
│   ├── 📁 models/                   # Data models (future)
│   ├── 📁 api/                      # API endpoints (future)
│   ├── 📁 core/                     # Core business logic (future)
│   ├── __init__.py                  # Package initialization
│   └── main.py                      # Main application
├── 📁 db/                           # Database & vector storage
│   ├── __init__.py
│   ├── vector_db.py                 # FAISS vector database
│   └── build_sample_database.py     # Sample data builder
├── 📁 templates/                    # HTML templates
│   └── index.html                   # Main UI
├── 📁 static/                       # Static assets
│   └── style.css                    # Styling
├── 📁 tests/                        # Test suite (future)
├── 📁 docs/                         # Documentation (future)
├── 📁 data/                         # Data storage (auto-created)
├── requirements.txt                  # Professional dependencies
├── README.md                        # This file
└── .gitignore                       # Git ignore rules
```

## ✨ **Tính năng chính**

### 🔧 **Core Features**
- **AI Diagnostics**: Chẩn đoán ô tô thông minh với GPT
- **Vector Search**: Tìm kiếm semantic với FAISS
- **TTS Service**: Text-to-Speech với multiple engines
- **Web Interface**: Modern UI với real-time chat

### 🎓 **Workshop 4 Core Features**
- **FAISS/PineCone**: Fast vector similarity search
- **Langchain**: Prompt & chain management
- **Function Calling**: Dynamic capabilities
- **Prompt Handling**: Effective processing

### 🏆 **Professional Features**
- **Configuration Management**: Environment-based config
- **Professional Logging**: Colored console + file logging
- **Error Handling**: Robust fallbacks & recovery
- **Performance Monitoring**: Built-in performance tracking
- **Mock Mode**: Offline demonstration capability

## 🚀 **Cài đặt nhanh**

### 1. **Clone repository**
```bash
git clone <repository-url>
cd DiagXpert
```

### 2. **Cài đặt dependencies**
```bash
# Core dependencies
pip install -r requirements.txt

# Workshop 4 dependencies (optional)
pip install langchain langchain-openai langchain-community langchain-tavily langgraph pinecone-client pydantic
```

### 3. **Thiết lập environment**
```bash
# Copy example environment file
cp .env.example .env

# Edit with your API keys
nano .env
```

### 4. **Chạy ứng dụng**
```bash
# Chạy DiagXpert
python run.py

# Chạy Workshop 4 demo
python run.py workshop4
```

## ⚙️ **Configuration**

### **Environment Variables**
```bash
# OpenAI Configuration
OPENAI_BASE_URL=https://your-endpoint.com
OPENAI_API_KEY=your-api-key
OPENAI_MODEL=GPT-4o-mini

# Server Configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=5050
SERVER_DEBUG=false

# TTS Configuration
TTS_ENGINE=pyttsx3
TTS_RATE=150
TTS_VOLUME=0.9

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE_PATH=logs/diagxpert.log
```

### **Configuration Classes**
```python
from src.config.settings import get_config

config = get_config()

# Access configuration
print(f"Server: {config.server.host}:{config.server.port}")
print(f"TTS Engine: {config.tts.engine}")
print(f"OpenAI: {config.openai.is_configured}")
```

## 🎯 **Cách sử dụng**

### **1. Web Interface**
```bash
python run.py
# Truy cập: http://127.0.0.1:5050
```

### **2. Workshop 4 Demo**
```bash
python run.py workshop4
```

### **3. API Endpoints**
```bash
# DiagXpert diagnostics
curl -X POST http://127.0.0.1:5050/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What causes engine overheating?"}'

# TTS service
curl -X POST http://127.0.0.1:5050/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Engine temperature is normal"}'

# Workshop 4 demo
curl http://127.0.0.1:5050/workshop4/demo
```

## 🔧 **TTS Service Architecture**

### **Engine Support**
- **pyttsx3**: Primary engine (macOS, Linux, Windows)
- **Mock Engine**: For testing & development
- **Extensible**: Easy to add new engines

### **Features**
- **Multiple Voices**: Auto-detection & selection
- **Voice Management**: Detailed voice information
- **Error Handling**: Graceful fallbacks
- **Performance**: Optimized audio generation

### **Usage**
```python
from src.services.tts_service import TextToSpeechService

# Create TTS service
tts = TextToSpeechService()

# Synthesize text
audio_bytes = tts.synthesize_to_wav_bytes("Hello, world!")

# Speak directly
tts.speak("Engine diagnostics complete")

# Get voice info
voices = tts.get_available_voices()
voice_info = tts.get_voice_info()
```

## 📊 **Professional Logging**

### **Features**
- **Colored Console**: Different colors for log levels
- **File Logging**: Rotating log files with rotation
- **Performance Tracking**: Built-in performance monitoring
- **Error Decorators**: Automatic error logging

### **Usage**
```python
from src.utils.logger import get_logger, log_performance_decorator, log_errors

logger = get_logger('my_module')

@log_performance_decorator
@log_errors
def my_function():
    logger.info("Function started")
    # ... function logic
    logger.info("Function completed")
```

## 🧪 **Testing**

### **Run Tests**
```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests
pytest tests/

# With coverage
pytest --cov=src tests/
```

### **Test Structure**
```
tests/
├── test_config.py           # Configuration tests
├── test_tts_service.py      # TTS service tests
├── test_vector_db.py        # Vector database tests
└── test_main.py             # Main application tests
```

## 🚀 **Deployment**

### **Production Setup**
```bash
# Install production dependencies only
pip install Flask openai faiss-cpu sentence-transformers pyttsx3 python-dotenv

# Set production environment
export FLASK_ENV=production
export LOG_LEVEL=WARNING

# Run with production server
gunicorn -w 4 -b 0.0.0.0:5050 src.main:app
```

### **Docker Support**
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5050

CMD ["python", "src/main.py"]
```

## 🤝 **Đóng góp**

### **Development Setup**
```bash
# Install development dependencies
pip install -r requirements.txt
pip install black flake8 mypy pytest

# Code formatting
black src/

# Linting
flake8 src/

# Type checking
mypy src/
```

### **Contribution Guidelines**
1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Run linting & tests
5. Submit pull request

## 📚 **Documentation**

- **[API Reference](docs/api.md)**: REST API documentation
- **[Configuration](docs/config.md)**: Configuration guide
- **[Deployment](docs/deployment.md)**: Deployment instructions

## 🎓 **WORKSHOP 4 - CHI TIẾT IMPLEMENTATION**

### **🎯 4 Core Objectives:**

#### **1. FAISS/PineCone Fast Vector Search**
- **Mục đích:** Tìm kiếm nhanh chóng trong vector database
- **Implementation:** Sử dụng FAISS với cosine similarity
- **Code Location:** `src/main.py` - `/workshop4/vector_search`

#### **2. Langchain Prompt & Chain Management**
- **Mục đích:** Quản lý prompts và chains một cách có hệ thống
- **Implementation:** Prompt templates và chain execution
- **Code Location:** `src/main.py` - `/workshop4/langchain`

#### **3. Function Calling Dynamic Capabilities**
- **Mục đích:** Gọi functions động dựa trên context
- **Implementation:** Dynamic function selection và execution
- **Code Location:** `src/main.py` - `/workshop4/function_calling`

#### **4. Handle Prompts Effectively**
- **Mục đích:** Xử lý prompts một cách hiệu quả và linh hoạt
- **Implementation:** Prompt optimization và context management
- **Code Location:** `src/main.py` - `/workshop4/prompt_management`

### **🔧 Tính năng mở rộng:**

#### **RAG Techniques (Retrieval-Augmented Generation)**
- Semantic search với vector database
- Context augmentation cho AI responses
- Dynamic document retrieval

#### **Batching Techniques**
- Batch processing cho documents
- Efficient vector operations
- Memory optimization

#### **Document Upload & Processing**
- Hỗ trợ: TXT, PDF, DOCX, DOC
- Automatic text extraction
- Vector database integration

### **🚨 Giải quyết lỗi TTS:**

#### **Vấn đề đã giải quyết:**
- Audio format compatibility (WAV/MP3)
- FFmpeg conversion issues
- Browser autoplay policies

#### **Giải pháp implemented:**
- Enhanced audio conversion với pydub
- Format detection & fallback
- Better error handling

### **📁 Cấu trúc Workshop 4:**

```
src/
├── main.py                      # Workshop 4 endpoints
├── services/
│   ├── langchain_service.py     # Langchain integration
│   ├── tts_service.py           # Enhanced TTS
│   └── document_processor.py    # File processing
└── config/
    └── settings.py              # Configuration
```

### **🚀 Test Workshop 4:**

```bash
# Test Vector Search
curl -X POST http://127.0.0.1:5050/workshop4/vector_search \
  -H "Content-Type: application/json" \
  -d '{"query":"hệ thống điều hòa"}'

# Test Langchain
curl -X POST http://127.0.0.1:5050/workshop4/langchain \
  -H "Content-Type: application/json" \
  -d '{"query":"Hướng dẫn bảo dưỡng xe"}'

# Test Function Calling
curl -X POST http://127.0.0.1:5050/workshop4/function_calling \
  -H "Content-Type: application/json" \
  -d '{"query":"Kiểm tra pin xe"}'

# Test Prompt Management
curl -X POST http://127.0.0.1:5050/workshop4/prompt_management \
  -H "Content-Type: application/json" \
  -d '{"query":"Tạo prompt cho chẩn đoán động cơ"}'
```

### **🔍 Debugging Tips:**

#### **TTS Issues:**
1. Check browser console cho audio errors
2. Verify FFmpeg installation: `brew install ffmpeg`
3. Check audio format: MP3 vs WAV compatibility
4. Browser autoplay policies: User interaction required

#### **Vector DB Issues:**
1. Check documents loaded: `/upload/status`
2. Verify FAISS index: `vector_db.documents`
3. Test search: `vector_db.search("test", k=1)`

#### **General Issues:**
1. Check logs: Console output và error messages
2. Verify dependencies: `pip list | grep -E "(faiss|flask|openai)"`
3. Environment variables: `.env` file configuration

### **📝 Kết luận Workshop 4:**

Workshop 4 đã được implement đầy đủ với:
- ✅ **4 Core Objectives** (FAISS, Langchain, Function Calling, Prompt Handling)
- ✅ **RAG & Batching Techniques**
- ✅ **Document Upload & Processing**
- ✅ **Modern Gemini-style UI**
- ✅ **Enhanced TTS with MP3 conversion**
- ✅ **Professional code structure**

Ứng dụng sẵn sàng cho production use với automotive diagnostic support!



## 🙏 **Acknowledgments**

- **OpenAI**: For GPT models and API
- **FAISS**: For vector similarity search
- **Flask**: For web framework
- **Workshop 4**: For core RAG system concepts

---

**Built with ❤️ by DiagXpert Team**

*Professional AI Automotive Diagnostics with Workshop 4 Core Features*

