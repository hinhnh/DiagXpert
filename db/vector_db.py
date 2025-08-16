import pickle
import faiss
import numpy as np
from typing import List, Tuple, Union, Dict
from sentence_transformers import SentenceTransformer
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorDatabase:
    """
    FAISS-based vector database with metadata support.
    Supports building from raw text, inserting new chunks with metadata,
    and querying top-k relevant documents along with metadata.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        logger.info(f"📦 Loading SentenceTransformer model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.documents: List[str] = []
        self.metadatas: List[Dict] = []

    def build(self, raw_input: Union[str, List[str]], metadatas: List[Dict] = None):
        """
        Build FAISS index from text or list of strings with optional metadata.
        """
        if isinstance(raw_input, str):
            self.documents = [chunk.strip() for chunk in raw_input.split("\n") if chunk.strip()]
        elif isinstance(raw_input, list):
            self.documents = [chunk.strip() for chunk in raw_input if isinstance(chunk, str) and chunk.strip()]
        else:
            raise TypeError("❌ Input must be a string or list of strings.")

        if metadatas is None:
            self.metadatas = [{} for _ in self.documents]
        else:
            if len(metadatas) != len(self.documents):
                raise ValueError("Length of metadatas must match number of documents")
            self.metadatas = metadatas

        logger.info(f"📝 Preparing {len(self.documents)} documents for indexing...")
        vectors = self.model.encode(self.documents, show_progress_bar=True).astype("float32")
        logger.info(f"🔍 Creating FAISS index with dimension {vectors.shape[1]}")
        self.index = faiss.IndexFlatL2(vectors.shape[1])
        self.index.add(vectors)
        logger.info(f"✅ Index built successfully with {len(self.documents)} documents.")

    def insert_text(self, text: str, metadata: Dict = None):
        """
        Insert a new chunk with optional metadata into FAISS index.
        """
        text = text.strip()
        if not text:
            logger.warning("⚠️ Attempted to insert empty text chunk. Skipping.")
            return

        vec = self.model.encode([text]).astype("float32")
        if self.index is None:
            logger.info("📌 Index not found. Creating new FAISS index.")
            self.index = faiss.IndexFlatL2(vec.shape[1])

        self.index.add(vec)
        self.documents.append(text)
        self.metadatas.append(metadata if metadata else {})
        logger.info(f"🔹 Inserted new chunk. Total documents: {len(self.documents)}")

    def query(self, query_text: str, top_k: int = 3) -> List[Tuple[str, float]]:
        """
        Query top-k documents without metadata.
        """
        if self.index is None or not self.documents:
            raise ValueError("❌ Index or documents are not loaded or built.")

        logger.info(f"🔎 Searching top {top_k} matches for: \"{query_text}\"")
        query_vec = self.model.encode([query_text]).astype("float32")
        distances, indices = self.index.search(query_vec, top_k)

        results = []
        for i, dist in zip(indices[0], distances[0]):
            results.append((self.documents[i], float(dist)))
        logger.info(f"✅ Found {len(results)} results.")
        return results

    def query_with_metadata(self, query_text: str, top_k: int = 3) -> List[Tuple[str, Dict, float]]:
        """
        Query top-k documents and return (text, metadata, distance).
        """
        if self.index is None or not self.documents:
            raise ValueError("❌ Index or documents are not loaded or built.")

        logger.info(f"🔎 Searching top {top_k} matches (with metadata) for: \"{query_text}\"")
        query_vec = self.model.encode([query_text]).astype("float32")
        distances, indices = self.index.search(query_vec, top_k)

        results = []
        for i, dist in zip(indices[0], distances[0]):
            results.append((self.documents[i], self.metadatas[i], float(dist)))
        logger.info(f"✅ Found {len(results)} results with metadata.")
        return results

    def save(self, index_path: str = "faiss_index.pkl", docs_path: str = "docs.pkl", meta_path: str = "metadata.pkl"):
        """
        Save FAISS index, documents, and metadata to disk.
        """
        if self.index is None:
            raise ValueError("❌ Index is not built yet. Cannot save.")

        with open(index_path, "wb") as f:
            pickle.dump(self.index, f)
        with open(docs_path, "wb") as f:
            pickle.dump(self.documents, f)
        with open(meta_path, "wb") as f:
            pickle.dump(self.metadatas, f)

        logger.info(f"💾 Index saved to {index_path}")
        logger.info(f"💾 Documents saved to {docs_path}")
        logger.info(f"💾 Metadata saved to {meta_path}")

    def load(self, index_path: str = "faiss_index.pkl", docs_path: str = "docs.pkl", meta_path: str = "metadata.pkl"):
        """
        Load FAISS index, documents, and metadata from disk.
        """
        with open(index_path, "rb") as f:
            self.index = pickle.load(f)
        with open(docs_path, "rb") as f:
            self.documents = pickle.load(f)
        with open(meta_path, "rb") as f:
            self.metadatas = pickle.load(f)

        logger.info(f"📂 Loaded index from {index_path}")
        logger.info(f"📂 Loaded {len(self.documents)} documents from {docs_path}")
        logger.info(f"📂 Loaded metadata for {len(self.metadatas)} documents")
