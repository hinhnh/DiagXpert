import json
import os
import logging
from datetime import datetime
from typing import List, Dict, Optional
import uuid
from .chat_vector_db import ChatVectorDatabase

logger = logging.getLogger(__name__)

class ChatHistoryManager:
    """Quản lý lịch sử chat với khả năng lưu trữ và tải context"""
    
    def __init__(self, history_file: str = "chat_history.json"):
        """
        Khởi tạo ChatHistoryManager
        
        Args:
            history_file: Đường dẫn đến file lưu lịch sử chat
        """
        self.history_file = history_file
        self.current_session_id = str(uuid.uuid4())
        self.sessions = self._load_history()
        self.chat_vector_db = ChatVectorDatabase()
        self.chat_vector_db.load_chat_vectors()
        logger.info(f"💬 Initialized ChatHistoryManager with session ID: {self.current_session_id}")
        logger.info(f"🔍 Chat vector database stats: {self.chat_vector_db.get_stats()}")
    
    def _load_history(self) -> Dict:
        """Tải lịch sử chat từ file"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"📂 Loaded chat history with {len(data.get('sessions', {}))} sessions")
                    return data
            except Exception as e:
                logger.error(f"❌ Error loading chat history: {e}")
                return {"sessions": {}, "metadata": {"created_at": datetime.now().isoformat()}}
        else:
            logger.info("📝 Creating new chat history file")
            return {"sessions": {}, "metadata": {"created_at": datetime.now().isoformat()}}
    
    def _save_history(self):
        """Lưu lịch sử chat vào file"""
        try:
            self.sessions["metadata"]["last_updated"] = datetime.now().isoformat()
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.sessions, f, ensure_ascii=False, indent=2)
            logger.info("💾 Saved chat history to file")
        except Exception as e:
            logger.error(f"❌ Error saving chat history: {e}")
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """
        Thêm tin nhắn vào lịch sử chat hiện tại
        
        Args:
            role: "user" hoặc "assistant"
            content: Nội dung tin nhắn
            metadata: Thông tin bổ sung (ví dụ: context_used, response_time)
        """
        if self.current_session_id not in self.sessions["sessions"]:
            self.sessions["sessions"][self.current_session_id] = {
                "created_at": datetime.now().isoformat(),
                "messages": []
            }
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self.sessions["sessions"][self.current_session_id]["messages"].append(message)
        self._save_history()
        
        # Also add to vector database for semantic search
        self.chat_vector_db.add_chat_message(role, content, self.current_session_id, metadata)
        self.chat_vector_db.save_chat_vectors()
        
        logger.info(f"📝 Added {role} message to session {self.current_session_id[:8]}...")
    
    def get_current_session_context(self, max_messages: int = 10) -> List[Dict]:
        """
        Lấy context từ phiên chat hiện tại
        
        Args:
            max_messages: Số lượng tin nhắn tối đa để lấy làm context
            
        Returns:
            Danh sách tin nhắn để làm context
        """
        if self.current_session_id not in self.sessions["sessions"]:
            return []
        
        messages = self.sessions["sessions"][self.current_session_id]["messages"]
        # Lấy các tin nhắn gần nhất, nhưng đảm bảo có cặp user-assistant
        recent_messages = messages[-max_messages:] if len(messages) > max_messages else messages
        
        # Chuyển đổi sang định dạng OpenAI API
        context_messages = []
        for msg in recent_messages:
            context_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        logger.info(f"📋 Retrieved {len(context_messages)} messages for context")
        return context_messages
    
    def semantic_search_history(self, query: str, top_k: int = 3, include_current_session: bool = True) -> List[Dict]:
        """
        Tìm kiếm semantic trong lịch sử chat
        
        Args:
            query: Truy vấn tìm kiếm
            top_k: Số lượng kết quả trả về
            include_current_session: Có bao gồm session hiện tại không
            
        Returns:
            Danh sách tin nhắn liên quan theo ngữ nghĩa
        """
        if include_current_session:
            results = self.chat_vector_db.semantic_search_chat(query, top_k=top_k)
        else:
            results = self.chat_vector_db.get_contextual_messages(query, self.current_session_id, top_k=top_k)
        
        # Convert to OpenAI format
        semantic_messages = []
        for content, metadata, score in results:
            semantic_messages.append({
                "role": metadata.get("role"),
                "content": content,
                "metadata": {
                    **metadata,
                    "semantic_score": score,
                    "is_semantic_result": True
                }
            })
        
        logger.info(f"🔍 Found {len(semantic_messages)} semantically relevant messages")
        return semantic_messages
    
    def get_enhanced_context(self, query: str, max_recent: int = 4, max_semantic: int = 2) -> List[Dict]:
        """
        Lấy context nâng cao kết hợp recent + semantic search
        
        Args:
            query: Query hiện tại để tìm kiếm semantic
            max_recent: Số tin nhắn gần đây tối đa
            max_semantic: Số kết quả semantic tối đa
            
        Returns:
            Danh sách messages đã được kết hợp và sắp xếp
        """
        # Lấy tin nhắn gần đây từ session hiện tại
        recent_messages = self.get_current_session_context(max_messages=max_recent)
        
        # Lấy tin nhắn liên quan semantic từ các session khác
        semantic_messages = self.semantic_search_history(query, top_k=max_semantic, include_current_session=False)
        
        # Kết hợp: semantic trước, recent sau để đảm bảo context flow
        combined_messages = semantic_messages + recent_messages
        
        logger.info(f"🧠 Enhanced context: {len(semantic_messages)} semantic + {len(recent_messages)} recent")
        return combined_messages
    
    def get_session_summary(self, session_id: str = None) -> Optional[Dict]:
        """
        Lấy tóm tắt của một phiên chat
        
        Args:
            session_id: ID của phiên chat, nếu None thì lấy phiên hiện tại
            
        Returns:
            Thông tin tóm tắt phiên chat
        """
        if session_id is None:
            session_id = self.current_session_id
        
        if session_id not in self.sessions["sessions"]:
            return None
        
        session = self.sessions["sessions"][session_id]
        return {
            "session_id": session_id,
            "created_at": session["created_at"],
            "message_count": len(session["messages"]),
            "last_message": session["messages"][-1]["timestamp"] if session["messages"] else None
        }
    
    def get_all_sessions(self) -> List[Dict]:
        """Lấy danh sách tất cả phiên chat"""
        sessions_list = []
        for session_id, session_data in self.sessions["sessions"].items():
            summary = self.get_session_summary(session_id)
            if summary:
                sessions_list.append(summary)
        
        # Sắp xếp theo thời gian tạo (mới nhất trước)
        sessions_list.sort(key=lambda x: x["created_at"], reverse=True)
        return sessions_list
    
    def start_new_session(self) -> str:
        """
        Bắt đầu phiên chat mới
        
        Returns:
            ID của phiên chat mới
        """
        self.current_session_id = str(uuid.uuid4())
        logger.info(f"🆕 Started new chat session: {self.current_session_id[:8]}...")
        return self.current_session_id
    
    def switch_session(self, session_id: str) -> bool:
        """
        Chuyển sang phiên chat khác
        
        Args:
            session_id: ID của phiên chat muốn chuyển đến
            
        Returns:
            True nếu chuyển thành công, False nếu không tìm thấy phiên
        """
        if session_id in self.sessions["sessions"]:
            self.current_session_id = session_id
            logger.info(f"🔄 Switched to session: {session_id[:8]}...")
            return True
        else:
            logger.warning(f"⚠️ Session not found: {session_id[:8]}...")
            return False
    
    def delete_session(self, session_id: str) -> bool:
        """
        Xóa một phiên chat
        
        Args:
            session_id: ID của phiên chat muốn xóa
            
        Returns:
            True nếu xóa thành công, False nếu không tìm thấy phiên
        """
        if session_id in self.sessions["sessions"]:
            del self.sessions["sessions"][session_id]
            self._save_history()
            
            # Also remove from vector database
            self.chat_vector_db.clear_session_messages(session_id)
            self.chat_vector_db.save_chat_vectors()
            
            logger.info(f"🗑️ Deleted session: {session_id[:8]}...")
            
            # Nếu xóa phiên hiện tại, tạo phiên mới
            if session_id == self.current_session_id:
                self.start_new_session()
            
            return True
        else:
            logger.warning(f"⚠️ Cannot delete session (not found): {session_id[:8]}...")
            return False
    
    def clear_all_history(self):
        """Xóa toàn bộ lịch sử chat"""
        self.sessions = {"sessions": {}, "metadata": {"created_at": datetime.now().isoformat()}}
        self._save_history()
        
        # Clear vector database
        self.chat_vector_db = ChatVectorDatabase()
        self.chat_vector_db.save_chat_vectors()
        
        self.start_new_session()
        logger.info("🧹 Cleared all chat history and vector database")
    
    def get_conversation_context_for_ai(self, include_system_prompt: bool = True) -> List[Dict]:
        """
        Lấy context conversation để gửi cho AI model
        Bao gồm system prompt và lịch sử tin nhắn gần đây
        
        Args:
            include_system_prompt: Có bao gồm system prompt không
            
        Returns:
            Danh sách messages theo format OpenAI
        """
        messages = []
        
        # Thêm system prompt nếu cần
        if include_system_prompt:
            messages.append({
                "role": "system",
                "content": (
                    "You are DiagXpert, an AI assistant for automotive diagnostics. "
                    "Use the context provided and conversation history to answer questions accurately. "
                    "Be helpful, professional, and provide detailed technical information when needed."
                )
            })
        
        # Thêm lịch sử conversation
        context_messages = self.get_current_session_context(max_messages=8)  # Giới hạn để tránh token limit
        messages.extend(context_messages)
        
        return messages
