"""Embedding service with tiered Metal acceleration.

Tier 1: MLX server /v1/embeddings (fastest — native Apple Silicon)
Tier 2: sentence-transformers on MPS device (Metal via PyTorch)
Tier 3: sentence-transformers on CPU (fallback, works everywhere)
"""

import hashlib
import logging
import os
from functools import lru_cache
from typing import Any

import httpx

# Optional dependency
try:
    from sentence_transformers import SentenceTransformer

    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None

logger = logging.getLogger(__name__)


def _detect_device() -> str:
    """Detect best available PyTorch device for sentence-transformers."""
    try:
        import torch

        if torch.backends.mps.is_available():
            return "mps"  # Apple Silicon Metal
    except Exception:
        pass
    return "cpu"


class EmbeddingService:
    """Tiered embedding service: MLX server -> MPS -> CPU.

    Uses all-MiniLM-L6-v2 model (384 dimensions) for fast, local embeddings.
    Prefers MLX server when available, falls back to sentence-transformers.
    """

    _model: object | None = None  # SentenceTransformer | None
    _device: str | None = None
    _mlx_available: bool | None = None
    MODEL_NAME = "all-MiniLM-L6-v2"
    EMBEDDING_DIM = 384

    @classmethod
    def _get_mlx_url(cls) -> str:
        return os.getenv("MLX_URL", "http://localhost:8082")

    @classmethod
    def _check_mlx_available(cls) -> bool:
        """Check if MLX server is reachable (cached per session)."""
        if cls._mlx_available is not None:
            return cls._mlx_available
        try:
            resp = httpx.get(f"{cls._get_mlx_url()}/v1/models", timeout=2.0)
            cls._mlx_available = resp.status_code == 200
        except Exception:
            cls._mlx_available = False
        if cls._mlx_available:
            logger.info("MLX server available for embeddings at %s", cls._get_mlx_url())
        return cls._mlx_available

    @classmethod
    def _embed_via_mlx(cls, texts: list[str]) -> list[list[float]]:
        """Generate embeddings via MLX server's OpenAI-compatible endpoint."""
        resp = httpx.post(
            f"{cls._get_mlx_url()}/v1/embeddings",
            json={"input": texts, "model": cls.MODEL_NAME},
            timeout=30.0,
        )
        resp.raise_for_status()
        data = resp.json()
        # OpenAI embeddings response: {"data": [{"embedding": [...], "index": 0}, ...]}
        sorted_data = sorted(data["data"], key=lambda x: x["index"])
        return [item["embedding"] for item in sorted_data]

    @classmethod
    def get_model(cls) -> Any:
        """Lazy load the sentence-transformer model with best available device."""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "sentence-transformers not available. "
                "Install with: pip install sentence-transformers"
            )
        if cls._model is None:
            cls._device = _detect_device()
            cls._model = SentenceTransformer(cls.MODEL_NAME, device=cls._device)
            logger.info(
                "Loaded %s on %s device",
                cls.MODEL_NAME,
                cls._device,
            )
        return cls._model

    @classmethod
    def embed_text(cls, text: str) -> list[float]:
        """Generate embedding for a single text.

        Tries MLX server first, falls back to sentence-transformers.

        Args:
            text: Text to embed

        Returns:
            List of floats (384 dimensions)
        """
        if cls._check_mlx_available():
            try:
                return cls._embed_via_mlx([text])[0]
            except Exception as e:
                logger.warning("MLX embedding failed, falling back: %s", e)
                cls._mlx_available = False  # Don't retry this session

        model = cls.get_model()
        embedding = model.encode(text, convert_to_numpy=True)
        return embedding.tolist()  # type: ignore[no-any-return]

    @classmethod
    def embed_batch(cls, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts efficiently.

        Tries MLX server first, falls back to sentence-transformers.

        Args:
            texts: List of texts to embed

        Returns:
            List of embeddings (each 384 dimensions)
        """
        if not texts:
            return []

        if cls._check_mlx_available():
            try:
                return cls._embed_via_mlx(texts)
            except Exception as e:
                logger.warning("MLX batch embedding failed, falling back: %s", e)
                cls._mlx_available = False

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

    @classmethod
    def reset(cls) -> None:
        """Reset cached state (for testing)."""
        cls._model = None
        cls._device = None
        cls._mlx_available = None


@lru_cache(maxsize=100)
def get_cached_embedding(text: str) -> tuple:
    """Get embedding with LRU caching (for repeated queries).

    Returns tuple for hashability.
    """
    return tuple(EmbeddingService.embed_text(text))
