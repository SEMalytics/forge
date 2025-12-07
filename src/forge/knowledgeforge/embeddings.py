"""
Vector embeddings for semantic search
"""

from sentence_transformers import SentenceTransformer
from typing import List
import numpy as np
from forge.utils.logger import logger


class EmbeddingManager:
    """Manage vector embeddings for semantic search"""

    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize embedding manager

        Args:
            model_name: Name of the sentence transformer model
        """
        self.model_name = model_name
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        logger.info("Embedding model loaded")

    def encode(self, text: str) -> np.ndarray:
        """
        Encode text to embedding vector

        Args:
            text: Text to encode

        Returns:
            Embedding vector
        """
        return self.model.encode(text)

    def encode_batch(self, texts: List[str]) -> np.ndarray:
        """
        Encode multiple texts to embedding vectors

        Args:
            texts: List of texts to encode

        Returns:
            Array of embedding vectors
        """
        return self.model.encode(texts)

    def cosine_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Similarity score (0-1)
        """
        return np.dot(embedding1, embedding2) / (
            np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
        )

    def find_most_similar(
        self,
        query_embedding: np.ndarray,
        candidate_embeddings: np.ndarray,
        top_k: int = 10
    ) -> List[int]:
        """
        Find most similar embeddings

        Args:
            query_embedding: Query embedding vector
            candidate_embeddings: Array of candidate embeddings
            top_k: Number of top results to return

        Returns:
            List of indices of most similar embeddings
        """
        similarities = np.dot(candidate_embeddings, query_embedding) / (
            np.linalg.norm(candidate_embeddings, axis=1) * np.linalg.norm(query_embedding)
        )

        top_indices = np.argsort(similarities)[-top_k:][::-1]
        return top_indices.tolist()
