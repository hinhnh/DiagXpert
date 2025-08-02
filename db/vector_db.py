import pickle
import faiss
import numpy as np
from typing import List, Tuple, Union
from sentence_transformers import SentenceTransformer


class VectorDatabase:
    """
    A simple FAISS-based vector database for semantic search using SentenceTransformers.
    Supports building from raw text or list of documents.
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

    def build(self, raw_input: Union[str, List[str]]):
        """
        Build the FAISS index from either a multiline string or a list of strings.

        Args:
            raw_input (Union[str, List[str]]): Input text data.
                - If str: each non-empty line becomes a document.
                - If List[str]: each item becomes a document.
        """
        if isinstance(raw_input, str):
            self.documents = [chunk.strip() for chunk in raw_input.split("\n") if chunk.strip()]
        elif isinstance(raw_input, list):
            self.documents = [chunk.strip() for chunk in raw_input if isinstance(chunk, str) and chunk.strip()]
        else:
            raise TypeError("❌ Input must be a string or list of strings.")

        print(f"📝 Preparing {len(self.documents)} documents for indexing...")
        vectors = self.model.encode(self.documents, show_progress_bar=True).astype("float32")

        print(f"🔍 Creating FAISS index with dimension {vectors.shape[1]}")
        self.index = faiss.IndexFlatL2(vectors.shape[1])
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

        print(f"📂 Loaded index from {index_path}")
        print(f"📂 Loaded {len(self.documents)} documents from {docs_path}")

    def query(self, query_text: str, top_k: int = 3) -> List[Tuple[str, float]]:
        """
        Query the database for the top-k most relevant documents.

        Args:
            query_text (str): The input text to search for.
            top_k (int): Number of top results to return.

        Returns:
            List[Tuple[str, float]]: List of (document_text, distance) tuples.
        """
        if self.index is None or not self.documents:
            raise ValueError("❌ Index or documents are not loaded or built.")

        print(f"🔎 Searching for top {top_k} matches to: \"{query_text}\"")
        query_vec = self.model.encode([query_text]).astype("float32")
        distances, indices = self.index.search(query_vec, top_k)

        results = []
        for i, dist in zip(indices[0], distances[0]):
            doc = self.documents[i]
            results.append((doc, float(dist)))

        return results
