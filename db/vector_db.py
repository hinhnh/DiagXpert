import pickle
import faiss
import numpy as np
from typing import List, Tuple, Union
from sentence_transformers import SentenceTransformer
import re


class VectorDatabase:
    """
    A simple FAISS-based vector database for semantic search using SentenceTransformers.
    Supports building from raw text or list of documents, with optional chunking.
    Backward-compatible with existing L2 indices saved on disk.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the vector database.

        Args:
            model_name (str): The Hugging Face model name to use for sentence embeddings.
        """
        print(f"📦 Loading model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.documents: List[str] = []
        # Track metric for newly built indices; for loaded ones we infer
        self._metric: str = "l2"  # or "ip"

    def _split_into_chunks(self, text: str, max_chars: int = 800, overlap: int = 120) -> List[str]:
        """
        Naive sentence-aware chunking for long text.
        Splits on sentence boundaries and packs sentences into chunks of ~max_chars with overlap.
        """
        # Split into sentences (very lightweight)
        sentences = re.split(r"(?<=[\.!?。！？])\s+", text.strip())
        sentences = [s.strip() for s in sentences if s.strip()]
        if not sentences:
            return [text.strip()]

        chunks: List[str] = []
        buffer = ""
        for sent in sentences:
            if len(buffer) + len(sent) + 1 <= max_chars:
                buffer = (buffer + " " + sent).strip()
            else:
                if buffer:
                    chunks.append(buffer)
                # start new buffer with overlap from end of previous buffer
                if overlap > 0 and buffer:
                    tail = buffer[-overlap:]
                    buffer = (tail + " " + sent).strip()
                else:
                    buffer = sent
        if buffer:
            chunks.append(buffer)
        return chunks

    def build(
        self,
        raw_input: Union[str, List[str]],
        *,
        use_cosine: bool = False,
        max_chars_per_chunk: int = 800,
        overlap_chars: int = 120,
    ):
        """
        Build the FAISS index from either a multiline string or a list of strings.

        Args:
            raw_input (Union[str, List[str]]): Input text data.
                - If str: it will be split into sentence-aware chunks.
                - If List[str]: each item becomes a document (and long items are chunked).
            use_cosine (bool): If True, normalize embeddings and use Inner Product (cosine) index.
            max_chars_per_chunk (int): Target maximum characters per chunk when splitting.
            overlap_chars (int): Overlap between consecutive chunks.
        """
        if isinstance(raw_input, str):
            base_chunks = self._split_into_chunks(
                raw_input, max_chars=max_chars_per_chunk, overlap=overlap_chars
            )
            self.documents = [c for c in base_chunks if c.strip()]
        elif isinstance(raw_input, list):
            docs: List[str] = []
            for item in raw_input:
                if isinstance(item, str) and item.strip():
                    if len(item) > max_chars_per_chunk:
                        docs.extend(
                            self._split_into_chunks(
                                item, max_chars=max_chars_per_chunk, overlap=overlap_chars
                            )
                        )
                    else:
                        docs.append(item.strip())
            self.documents = docs
        else:
            raise TypeError("❌ Input must be a string or list of strings.")

        print(f"📝 Preparing {len(self.documents)} documents for indexing...")
        vectors = self.model.encode(self.documents, show_progress_bar=True).astype("float32")

        if use_cosine:
            # Normalize and use Inner Product (cosine similarity)
            faiss.normalize_L2(vectors)
            print(f"🔍 Creating FAISS IndexFlatIP (cosine) with dimension {vectors.shape[1]}")
            self.index = faiss.IndexFlatIP(vectors.shape[1])
            self._metric = "ip"
        else:
            print(f"🔍 Creating FAISS IndexFlatL2 with dimension {vectors.shape[1]}")
            self.index = faiss.IndexFlatL2(vectors.shape[1])
            self._metric = "l2"

        self.index.add(vectors)
        print(f"✅ Index built successfully with {len(self.documents)} documents.")

    def save(self, index_path: str = "faiss_index.pkl", docs_path: str = "docs.pkl"):
        """
        Save the FAISS index and documents to disk.

        Args:
            index_path (str): Path to save the FAISS index.
            docs_path (str): Path to save the document list.
        """
        if self.index is None:
            raise ValueError("❌ Index is not built yet. Cannot save.")

        with open(index_path, "wb") as f:
            pickle.dump(self.index, f)
        with open(docs_path, "wb") as f:
            pickle.dump(self.documents, f)

        print(f"💾 Index saved to {index_path}")
        print(f"💾 Documents saved to {docs_path}")

    def load(self, index_path: str = "faiss_index.pkl", docs_path: str = "docs.pkl"):
        """
        Load a previously saved FAISS index and document list from disk.

        Args:
            index_path (str): Path to the FAISS index file.
            docs_path (str): Path to the document list file.
        """
        with open(index_path, "rb") as f:
            self.index = pickle.load(f)
        with open(docs_path, "rb") as f:
            self.documents = pickle.load(f)

        # Infer metric type if possible
        try:
            mt = getattr(self.index, "metric_type", None)
            if mt == faiss.METRIC_INNER_PRODUCT:
                self._metric = "ip"
            else:
                self._metric = "l2"
        except Exception:
            self._metric = "l2"

        print(f"📂 Loaded index from {index_path}")
        print(f"📂 Loaded {len(self.documents)} documents from {docs_path}")

    def query(
        self,
        query_text: str,
        top_k: int = 3,
        *,
        min_score: float = None,
        max_distance: float = None,
    ) -> List[Tuple[str, float]]:
        """
        Query the database for the top-k most relevant documents.

        Args:
            query_text (str): The input text to search for.
            top_k (int): Number of top results to return.
            min_score (float): Minimum cosine similarity if using IP/cosine index.
            max_distance (float): Maximum L2 distance if using L2 index (for legacy indices).

        Returns:
            List[Tuple[str, float]]: List of (document_text, score_or_distance) tuples.
                - If cosine/IP: score in [0,1]; higher is better.
                - If L2: distance; lower is better.
        """
        if self.index is None or not self.documents:
            raise ValueError("❌ Index or documents are not loaded or built.")

        print(f"🔎 Searching for top {top_k} matches to: \"{query_text}\"")
        query_vec = self.model.encode([query_text]).astype("float32")

        if self._metric == "ip":
            faiss.normalize_L2(query_vec)
        distances, indices = self.index.search(query_vec, top_k)

        results: List[Tuple[str, float]] = []
        for i, dist in zip(indices[0], distances[0]):
            if i < 0 or i >= len(self.documents):
                continue
            doc = self.documents[i]
            if self._metric == "ip":
                score = float(dist)  # cosine similarity
                if min_score is not None and score < min_score:
                    continue
                results.append((doc, score))
            else:
                distance = float(dist)
                if max_distance is not None and distance > max_distance:
                    continue
                results.append((doc, distance))

        return results

    def add_documents(self, new_documents: List[str], max_chars_per_chunk: int = 800, overlap_chars: int = 120):
        """
        Add new documents to existing index.
        
        Args:
            new_documents (List[str]): List of new documents to add.
            max_chars_per_chunk (int): Target maximum characters per chunk when splitting.
            overlap_chars (int): Overlap between consecutive chunks.
        """
        if self.index is None:
            raise ValueError("❌ Index is not built yet. Cannot add documents.")
        
        if not new_documents:
            print("⚠️ No new documents to add.")
            return
        
        print(f"📝 Processing {len(new_documents)} new documents...")
        
        # Process new documents (chunk if necessary)
        processed_docs: List[str] = []
        for doc in new_documents:
            if isinstance(doc, str) and doc.strip():
                if len(doc) > max_chars_per_chunk:
                    chunks = self._split_into_chunks(doc, max_chars=max_chars_per_chunk, overlap=overlap_chars)
                    processed_docs.extend(chunks)
                else:
                    processed_docs.append(doc.strip())
        
        if not processed_docs:
            print("⚠️ No valid documents to add after processing.")
            return
        
        print(f"🔍 Creating embeddings for {len(processed_docs)} new document chunks...")
        
        # Create embeddings for new documents
        new_vectors = self.model.encode(processed_docs, show_progress_bar=True).astype("float32")
        
        # Normalize if using cosine similarity
        if self._metric == "ip":
            faiss.normalize_L2(new_vectors)
        
        # Add to existing index
        self.index.add(new_vectors)
        
        # Add to documents list
        self.documents.extend(processed_docs)
        
        print(f"✅ Successfully added {len(processed_docs)} new document chunks to index.")
        print(f"📊 Total documents in index: {len(self.documents)}")
