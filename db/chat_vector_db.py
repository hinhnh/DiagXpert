import pickle
import faiss
import numpy as np
from typing import List, Tuple, Union, Dict
from sentence_transformers import SentenceTransformer
import logging
from datetime import datetime
import uuid

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatVectorDatabase:
    """
    FAISS-based vector database specifically for chat history with semantic search.
    Stores user messages and assistant responses with embeddings for semantic retrieval.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        logger.info(f"💬 Loading SentenceTransformer model for chat: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.chat_messages: List[str] = []
        self.chat_metadatas: List[Dict] = []

    def add_chat_message(self, role: str, content: str, session_id: str, metadata: Dict = None):
        """
        Add a chat message to the vector database with embedding.
        
        Args:
            role: "user" or "assistant"
            content: Message content
            session_id: Session ID for the message
            metadata: Additional metadata
        """
        content = content.strip()
        if not content:
            logger.warning("⚠️ Attempted to insert empty chat message. Skipping.")
            return

        # Create embedding
        vec = self.model.encode([content]).astype("float32")
        
        # Initialize index if needed
        if self.index is None:
            logger.info("📌 Creating new FAISS index for chat messages.")
            self.index = faiss.IndexFlatL2(vec.shape[1])

        # Add to index
        self.index.add(vec)
        self.chat_messages.append(content)
        
        # Prepare metadata
        chat_metadata = {
            "role": role,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "message_id": str(uuid.uuid4()),
            "type": "chat_message"
        }
        if metadata:
            chat_metadata.update(metadata)
        
        self.chat_metadatas.append(chat_metadata)
        logger.info(f"💬 Added {role} message to chat vector DB. Total: {len(self.chat_messages)}")

    def semantic_search_chat(self, query_text: str, top_k: int = 5, session_id: str = None, 
                            role_filter: str = None) -> List[Tuple[str, Dict, float]]:
        """
        Search chat messages semantically.
        
        Args:
            query_text: Query to search for
            top_k: Number of results to return
            session_id: Filter by specific session (None for all sessions)
            role_filter: Filter by role ("user", "assistant", or None for both)
            
        Returns:
            List of (message_content, metadata, distance) tuples
        """
        if self.index is None or not self.chat_messages:
            logger.warning("⚠️ No chat messages in vector database.")
            return []

        logger.info(f"🔍 Semantic search in chat history: \"{query_text}\"")
        query_vec = self.model.encode([query_text]).astype("float32")
        
        # Get more results than needed for filtering
        search_k = min(len(self.chat_messages), top_k * 3)
        distances, indices = self.index.search(query_vec, search_k)

        results = []
        for i, dist in zip(indices[0], distances[0]):
            metadata = self.chat_metadatas[i]
            
            # Apply filters
            if session_id and metadata.get("session_id") != session_id:
                continue
            if role_filter and metadata.get("role") != role_filter:
                continue
            
            results.append((self.chat_messages[i], metadata, float(dist)))
            
            if len(results) >= top_k:
                break
        
        logger.info(f"✅ Found {len(results)} relevant chat messages.")
        return results

    def get_recent_context(self, session_id: str, max_messages: int = 6) -> List[Tuple[str, Dict]]:
        """
        Get recent messages from a specific session chronologically.
        
        Args:
            session_id: Session to get messages from
            max_messages: Maximum number of messages to return
            
        Returns:
            List of (message_content, metadata) tuples in chronological order
        """
        session_messages = []
        for i, metadata in enumerate(self.chat_metadatas):
            if metadata.get("session_id") == session_id:
                session_messages.append((self.chat_messages[i], metadata, metadata.get("timestamp")))
        
        # Sort by timestamp
        session_messages.sort(key=lambda x: x[2])
        
        # Get recent messages
        recent = session_messages[-max_messages:] if len(session_messages) > max_messages else session_messages
        
        # Return without timestamp
        return [(msg, meta) for msg, meta, _ in recent]

    def get_contextual_messages(self, query_text: str, session_id: str, top_k: int = 3) -> List[Tuple[str, Dict, float]]:
        """
        Get contextually relevant messages from current session and semantically similar from all sessions.
        
        Args:
            query_text: Current user query
            session_id: Current session ID
            top_k: Number of semantic results to include
            
        Returns:
            Combined list of relevant messages
        """
        # Get semantic matches from all sessions
        semantic_results = self.semantic_search_chat(query_text, top_k=top_k)
        
        # Filter out current session messages to avoid duplication
        semantic_results = [
            (msg, meta, dist) for msg, meta, dist in semantic_results 
            if meta.get("session_id") != session_id
        ]
        
        logger.info(f"🎯 Found {len(semantic_results)} contextual messages from other sessions.")
        return semantic_results

    def save_chat_vectors(self, index_path: str = "chat_faiss_index.pkl", 
                         messages_path: str = "chat_messages.pkl", 
                         meta_path: str = "chat_metadata.pkl"):
        """
        Save chat vector database to disk.
        """
        if self.index is None:
            logger.warning("⚠️ No chat index to save.")
            return

        with open(index_path, "wb") as f:
            pickle.dump(self.index, f)
        with open(messages_path, "wb") as f:
            pickle.dump(self.chat_messages, f)
        with open(meta_path, "wb") as f:
            pickle.dump(self.chat_metadatas, f)

        logger.info(f"💾 Chat vector database saved to {index_path}")

    def load_chat_vectors(self, index_path: str = "chat_faiss_index.pkl", 
                         messages_path: str = "chat_messages.pkl", 
                         meta_path: str = "chat_metadata.pkl"):
        """
        Load chat vector database from disk.
        """
        try:
            with open(index_path, "rb") as f:
                self.index = pickle.load(f)
            with open(messages_path, "rb") as f:
                self.chat_messages = pickle.load(f)
            with open(meta_path, "rb") as f:
                self.chat_metadatas = pickle.load(f)

            logger.info(f"📂 Loaded chat vector database with {len(self.chat_messages)} messages")
        except FileNotFoundError:
            logger.info("📝 No existing chat vector database found. Starting fresh.")
        except Exception as e:
            logger.error(f"❌ Error loading chat vector database: {e}")

    def clear_session_messages(self, session_id: str):
        """
        Remove all messages from a specific session.
        """
        if not self.chat_messages:
            return

        # Find indices to remove
        indices_to_remove = []
        for i, metadata in enumerate(self.chat_metadatas):
            if metadata.get("session_id") == session_id:
                indices_to_remove.append(i)

        if not indices_to_remove:
            logger.info(f"🔍 No messages found for session {session_id[:8]}...")
            return

        # Remove in reverse order to maintain indices
        for i in reversed(indices_to_remove):
            del self.chat_messages[i]
            del self.chat_metadatas[i]

        # Rebuild index
        if self.chat_messages:
            vectors = self.model.encode(self.chat_messages, show_progress_bar=False).astype("float32")
            self.index = faiss.IndexFlatL2(vectors.shape[1])
            self.index.add(vectors)
        else:
            self.index = None

        logger.info(f"🗑️ Removed {len(indices_to_remove)} messages from session {session_id[:8]}...")

    def get_stats(self) -> Dict:
        """
        Get statistics about the chat vector database.
        """
        if not self.chat_messages:
            return {"total_messages": 0, "sessions": 0, "user_messages": 0, "assistant_messages": 0}

        sessions = set()
        user_count = 0
        assistant_count = 0

        for metadata in self.chat_metadatas:
            sessions.add(metadata.get("session_id"))
            if metadata.get("role") == "user":
                user_count += 1
            elif metadata.get("role") == "assistant":
                assistant_count += 1

        return {
            "total_messages": len(self.chat_messages),
            "sessions": len(sessions),
            "user_messages": user_count,
            "assistant_messages": assistant_count
        }
