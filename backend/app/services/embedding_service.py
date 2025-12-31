"""Embedding service using sentence-transformers for local vector generation."""

import hashlib
from functools import lru_cache
from typing import List, Optional

# Optional dependency
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None  # type: ignore


class EmbeddingService:
    """Service for generating text embeddings using sentence-transformers.

    Uses all-MiniLM-L6-v2 model (384 dimensions) for fast, local embeddings.
    No API calls required - runs entirely on CPU.
    """

    _model: Optional[object] = None  # SentenceTransformer | None
    MODEL_NAME = "all-MiniLM-L6-v2"
    EMBEDDING_DIM = 384

    @classmethod
    def get_model(cls):  # type: ignore
        """Lazy load the sentence-transformer model."""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "sentence-transformers not available. "
                "Install with: pip install sentence-transformers"
            )
        if cls._model is None:
            cls._model = SentenceTransformer(cls.MODEL_NAME)  # type: ignore
        return cls._model

    @classmethod
    def embed_text(cls, text: str) -> list[float]:
        """Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            List of floats (384 dimensions)
        """
        model = cls.get_model()
        embedding = model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    @classmethod
    def embed_batch(cls, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts efficiently.

        Args:
            texts: List of texts to embed

        Returns:
            List of embeddings (each 384 dimensions)
        """
        model = cls.get_model()
        embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        return [emb.tolist() for emb in embeddings]

    @staticmethod
    def hash_text(text: str) -> str:
        """Generate SHA256 hash of text for change detection.

        Args:
            text: Text to hash

        Returns:
            Hex string of SHA256 hash
        """
        return hashlib.sha256(text.encode()).hexdigest()


@lru_cache(maxsize=100)
def get_cached_embedding(text: str) -> tuple:
    """Get embedding with LRU caching (for repeated queries).

    Returns tuple for hashability.
    """
    return tuple(EmbeddingService.embed_text(text))
