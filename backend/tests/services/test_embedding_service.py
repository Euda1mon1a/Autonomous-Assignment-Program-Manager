"""Tests for embedding service using sentence-transformers."""

import hashlib
from unittest.mock import Mock, patch

import numpy as np
import pytest

from app.services.embedding_service import EmbeddingService, get_cached_embedding


class TestEmbeddingServiceModelLoading:
    """Test model loading and initialization."""

    def test_get_model_lazy_loads(self):
        """Test that model is lazy-loaded on first access."""
        # Reset model to None
        EmbeddingService._model = None

        with patch("app.services.embedding_service.SentenceTransformer") as mock_st:
            mock_model = Mock()
            mock_st.return_value = mock_model

            # First call should load model
            model1 = EmbeddingService.get_model()

            assert model1 is mock_model
            mock_st.assert_called_once_with(EmbeddingService.MODEL_NAME)

    def test_get_model_returns_singleton(self):
        """Test that subsequent calls return the same model instance."""
        # Reset model to None
        EmbeddingService._model = None

        with patch("app.services.embedding_service.SentenceTransformer") as mock_st:
            mock_model = Mock()
            mock_st.return_value = mock_model

            # First call
            model1 = EmbeddingService.get_model()
            # Second call
            model2 = EmbeddingService.get_model()

            assert model1 is model2
            # Should only be called once (singleton)
            mock_st.assert_called_once()

    def test_model_name_constant(self):
        """Test that model name is correctly set."""
        assert EmbeddingService.MODEL_NAME == "all-MiniLM-L6-v2"

    def test_embedding_dimension_constant(self):
        """Test that embedding dimension is correctly set."""
        assert EmbeddingService.EMBEDDING_DIM == 384


class TestEmbeddingServiceEmbedText:
    """Test single text embedding generation."""

    def test_embed_text_success(self):
        """Test successful embedding generation for single text."""
        # Reset model
        EmbeddingService._model = None

        # Mock the model
        mock_model = Mock()
        mock_embedding = np.array([0.1, 0.2, 0.3] * 128)  # 384 dimensions
        mock_model.encode.return_value = mock_embedding

        with patch("app.services.embedding_service.SentenceTransformer") as mock_st:
            mock_st.return_value = mock_model

            result = EmbeddingService.embed_text("Test text")

            # Verify encode was called with correct parameters
            mock_model.encode.assert_called_once_with(
                "Test text", convert_to_numpy=True
            )

            # Verify result is a list of floats
            assert isinstance(result, list)
            assert len(result) == 384
            assert all(isinstance(x, float) for x in result)

    def test_embed_text_empty_string(self):
        """Test embedding generation for empty string."""
        # Reset model
        EmbeddingService._model = None

        mock_model = Mock()
        mock_embedding = np.array([0.0] * 384)
        mock_model.encode.return_value = mock_embedding

        with patch("app.services.embedding_service.SentenceTransformer") as mock_st:
            mock_st.return_value = mock_model

            result = EmbeddingService.embed_text("")

            mock_model.encode.assert_called_once_with("", convert_to_numpy=True)
            assert isinstance(result, list)
            assert len(result) == 384

    def test_embed_text_long_text(self):
        """Test embedding generation for long text."""
        # Reset model
        EmbeddingService._model = None

        mock_model = Mock()
        mock_embedding = np.array([0.5] * 384)
        mock_model.encode.return_value = mock_embedding

        with patch("app.services.embedding_service.SentenceTransformer") as mock_st:
            mock_st.return_value = mock_model

            long_text = "This is a very long text. " * 100
            result = EmbeddingService.embed_text(long_text)

            mock_model.encode.assert_called_once()
            assert isinstance(result, list)
            assert len(result) == 384

    def test_embed_text_special_characters(self):
        """Test embedding generation with special characters."""
        # Reset model
        EmbeddingService._model = None

        mock_model = Mock()
        mock_embedding = np.array([0.3] * 384)
        mock_model.encode.return_value = mock_embedding

        with patch("app.services.embedding_service.SentenceTransformer") as mock_st:
            mock_st.return_value = mock_model

            special_text = "Test with émojis 🚀 and spëcial çhars!"
            result = EmbeddingService.embed_text(special_text)

            mock_model.encode.assert_called_once_with(
                special_text, convert_to_numpy=True
            )
            assert isinstance(result, list)


class TestEmbeddingServiceEmbedBatch:
    """Test batch text embedding generation."""

    def test_embed_batch_multiple_texts(self):
        """Test successful batch embedding generation."""
        # Reset model
        EmbeddingService._model = None

        mock_model = Mock()
        # Mock batch of 3 embeddings
        mock_embeddings = np.array(
            [
                [0.1] * 384,
                [0.2] * 384,
                [0.3] * 384,
            ]
        )
        mock_model.encode.return_value = mock_embeddings

        with patch("app.services.embedding_service.SentenceTransformer") as mock_st:
            mock_st.return_value = mock_model

            texts = ["Text one", "Text two", "Text three"]
            result = EmbeddingService.embed_batch(texts)

            # Verify encode was called with correct parameters
            mock_model.encode.assert_called_once_with(
                texts, convert_to_numpy=True, show_progress_bar=False
            )

            # Verify result structure
            assert isinstance(result, list)
            assert len(result) == 3
            assert all(isinstance(emb, list) for emb in result)
            assert all(len(emb) == 384 for emb in result)
            assert all(isinstance(x, float) for emb in result for x in emb)

    def test_embed_batch_single_text(self):
        """Test batch embedding with single text."""
        # Reset model
        EmbeddingService._model = None

        mock_model = Mock()
        mock_embeddings = np.array([[0.5] * 384])
        mock_model.encode.return_value = mock_embeddings

        with patch("app.services.embedding_service.SentenceTransformer") as mock_st:
            mock_st.return_value = mock_model

            result = EmbeddingService.embed_batch(["Single text"])

            assert len(result) == 1
            assert len(result[0]) == 384

    def test_embed_batch_empty_list(self):
        """Test batch embedding with empty list."""
        # Reset model
        EmbeddingService._model = None

        mock_model = Mock()
        mock_embeddings = np.array([])
        mock_model.encode.return_value = mock_embeddings

        with patch("app.services.embedding_service.SentenceTransformer") as mock_st:
            mock_st.return_value = mock_model

            result = EmbeddingService.embed_batch([])

            mock_model.encode.assert_called_once_with(
                [], convert_to_numpy=True, show_progress_bar=False
            )
            assert isinstance(result, list)

    def test_embed_batch_large_batch(self):
        """Test batch embedding with large number of texts."""
        # Reset model
        EmbeddingService._model = None

        mock_model = Mock()
        batch_size = 100
        mock_embeddings = np.random.rand(batch_size, 384)
        mock_model.encode.return_value = mock_embeddings

        with patch("app.services.embedding_service.SentenceTransformer") as mock_st:
            mock_st.return_value = mock_model

            texts = [f"Text {i}" for i in range(batch_size)]
            result = EmbeddingService.embed_batch(texts)

            assert len(result) == batch_size
            assert all(len(emb) == 384 for emb in result)

    def test_embed_batch_mixed_lengths(self):
        """Test batch embedding with texts of varying lengths."""
        # Reset model
        EmbeddingService._model = None

        mock_model = Mock()
        mock_embeddings = np.array(
            [
                [0.1] * 384,
                [0.2] * 384,
                [0.3] * 384,
            ]
        )
        mock_model.encode.return_value = mock_embeddings

        with patch("app.services.embedding_service.SentenceTransformer") as mock_st:
            mock_st.return_value = mock_model

            texts = [
                "Short",
                "Medium length text here",
                "This is a much longer text with many more words in it. " * 10,
            ]
            result = EmbeddingService.embed_batch(texts)

            assert len(result) == 3
            # All embeddings should have same dimension regardless of input length
            assert all(len(emb) == 384 for emb in result)


class TestEmbeddingServiceHashText:
    """Test text hashing functionality."""

    def test_hash_text_basic(self):
        """Test basic text hashing."""
        text = "Hello, world!"
        result = EmbeddingService.hash_text(text)

        # Should return a hex string
        assert isinstance(result, str)
        # SHA256 produces 64 hex characters
        assert len(result) == 64
        # Should be valid hex
        assert all(c in "0123456789abcdef" for c in result)

    def test_hash_text_consistency(self):
        """Test that same text produces same hash."""
        text = "Consistent text"
        hash1 = EmbeddingService.hash_text(text)
        hash2 = EmbeddingService.hash_text(text)

        assert hash1 == hash2

    def test_hash_text_different_inputs(self):
        """Test that different texts produce different hashes."""
        text1 = "Text one"
        text2 = "Text two"

        hash1 = EmbeddingService.hash_text(text1)
        hash2 = EmbeddingService.hash_text(text2)

        assert hash1 != hash2

    def test_hash_text_empty_string(self):
        """Test hashing empty string."""
        result = EmbeddingService.hash_text("")

        # Should still produce a valid hash
        assert isinstance(result, str)
        assert len(result) == 64

        # Verify it matches expected SHA256 of empty string
        expected = hashlib.sha256(b"").hexdigest()
        assert result == expected

    def test_hash_text_unicode(self):
        """Test hashing text with unicode characters."""
        text = "Hello 世界 🌍"
        result = EmbeddingService.hash_text(text)

        assert isinstance(result, str)
        assert len(result) == 64

        # Verify consistency
        assert result == EmbeddingService.hash_text(text)

    def test_hash_text_whitespace_sensitive(self):
        """Test that hashing is sensitive to whitespace."""
        text1 = "hello world"
        text2 = "hello  world"  # Extra space
        text3 = "hello world "  # Trailing space

        hash1 = EmbeddingService.hash_text(text1)
        hash2 = EmbeddingService.hash_text(text2)
        hash3 = EmbeddingService.hash_text(text3)

        # All should be different
        assert hash1 != hash2
        assert hash1 != hash3
        assert hash2 != hash3

    def test_hash_text_case_sensitive(self):
        """Test that hashing is case-sensitive."""
        text1 = "Hello World"
        text2 = "hello world"

        hash1 = EmbeddingService.hash_text(text1)
        hash2 = EmbeddingService.hash_text(text2)

        assert hash1 != hash2


class TestGetCachedEmbedding:
    """Test cached embedding function."""

    def test_get_cached_embedding_returns_tuple(self):
        """Test that cached embedding returns a tuple."""
        # Reset model and clear cache
        EmbeddingService._model = None
        get_cached_embedding.cache_clear()

        mock_model = Mock()
        mock_embedding = np.array([0.1, 0.2, 0.3] * 128)
        mock_model.encode.return_value = mock_embedding

        with patch("app.services.embedding_service.SentenceTransformer") as mock_st:
            mock_st.return_value = mock_model

            result = get_cached_embedding("Test text")

            # Should return tuple (for hashability)
            assert isinstance(result, tuple)
            assert len(result) == 384

    def test_get_cached_embedding_caches_results(self):
        """Test that results are cached and reused."""
        # Reset model and clear cache
        EmbeddingService._model = None
        get_cached_embedding.cache_clear()

        mock_model = Mock()
        mock_embedding = np.array([0.5] * 384)
        mock_model.encode.return_value = mock_embedding

        with patch("app.services.embedding_service.SentenceTransformer") as mock_st:
            mock_st.return_value = mock_model

            # First call
            result1 = get_cached_embedding("Test text")
            # Second call with same text
            result2 = get_cached_embedding("Test text")

            # Should return same result
            assert result1 == result2

            # Model encode should only be called once (due to caching)
            assert mock_model.encode.call_count == 1

    def test_get_cached_embedding_different_texts(self):
        """Test that different texts get different cache entries."""
        # Reset model and clear cache
        EmbeddingService._model = None
        get_cached_embedding.cache_clear()

        mock_model = Mock()
        mock_model.encode.side_effect = [
            np.array([0.1] * 384),
            np.array([0.2] * 384),
        ]

        with patch("app.services.embedding_service.SentenceTransformer") as mock_st:
            mock_st.return_value = mock_model

            result1 = get_cached_embedding("Text one")
            result2 = get_cached_embedding("Text two")

            # Should be different
            assert result1 != result2

            # Both should have been computed
            assert mock_model.encode.call_count == 2

    def test_get_cached_embedding_respects_cache_size(self):
        """Test that cache respects maxsize limit."""
        # Clear cache
        get_cached_embedding.cache_clear()

        # Reset model
        EmbeddingService._model = None

        mock_model = Mock()
        # Generate different embeddings for each call
        mock_model.encode.side_effect = [np.array([float(i)] * 384) for i in range(150)]

        with patch("app.services.embedding_service.SentenceTransformer") as mock_st:
            mock_st.return_value = mock_model

            # Generate embeddings for more than cache size (maxsize=100)
            for i in range(150):
                get_cached_embedding(f"Text {i}")

            # Cache info should show some evictions
            cache_info = get_cached_embedding.cache_info()
            assert cache_info.maxsize == 100
            assert cache_info.currsize <= 100

    def test_get_cached_embedding_cache_info(self):
        """Test cache info provides statistics."""
        # Clear cache
        get_cached_embedding.cache_clear()

        info = get_cached_embedding.cache_info()

        assert hasattr(info, "hits")
        assert hasattr(info, "misses")
        assert hasattr(info, "maxsize")
        assert hasattr(info, "currsize")
        assert info.maxsize == 100

    def test_get_cached_embedding_cache_clear(self):
        """Test cache can be cleared."""
        # Reset model
        EmbeddingService._model = None

        mock_model = Mock()
        mock_embedding = np.array([0.7] * 384)
        mock_model.encode.return_value = mock_embedding

        with patch("app.services.embedding_service.SentenceTransformer") as mock_st:
            mock_st.return_value = mock_model

            # Generate some cached entries
            get_cached_embedding("Text A")
            get_cached_embedding("Text B")

            # Clear cache
            get_cached_embedding.cache_clear()

            # Cache should be empty
            info = get_cached_embedding.cache_info()
            assert info.currsize == 0

            # Next call should miss cache
            get_cached_embedding("Text A")
            info = get_cached_embedding.cache_info()
            assert info.misses >= 1


class TestEmbeddingServiceIntegration:
    """Integration tests for embedding service."""

    def test_embed_and_hash_workflow(self):
        """Test typical workflow of embedding and hashing."""
        # Reset model
        EmbeddingService._model = None

        mock_model = Mock()
        mock_embedding = np.array([0.4] * 384)
        mock_model.encode.return_value = mock_embedding

        with patch("app.services.embedding_service.SentenceTransformer") as mock_st:
            mock_st.return_value = mock_model

            text = "Document content for ACGME rules"

            # Generate hash for change detection
            content_hash = EmbeddingService.hash_text(text)
            assert len(content_hash) == 64

            # Generate embedding
            embedding = EmbeddingService.embed_text(text)
            assert len(embedding) == 384

            # Re-hash should produce same result
            content_hash2 = EmbeddingService.hash_text(text)
            assert content_hash == content_hash2

    def test_batch_vs_single_embedding_consistency(self):
        """Test that batch and single embeddings produce same results."""
        # Reset model
        EmbeddingService._model = None

        mock_model = Mock()

        # Setup consistent mock responses
        single_embedding = np.array([0.6] * 384)
        batch_embeddings = np.array([[0.6] * 384])

        # Mock encode to return different values based on input type
        def mock_encode(text, convert_to_numpy=True, show_progress_bar=True):
            if isinstance(text, list):
                return batch_embeddings
            else:
                return single_embedding

        mock_model.encode.side_effect = mock_encode

        with patch("app.services.embedding_service.SentenceTransformer") as mock_st:
            mock_st.return_value = mock_model

            text = "Test text"

            # Get embedding as single
            single_result = EmbeddingService.embed_text(text)

            # Reset model for batch call
            mock_model.encode.side_effect = mock_encode

            # Get embedding as batch
            batch_result = EmbeddingService.embed_batch([text])

            # Should produce equivalent results
            assert len(single_result) == len(batch_result[0])
            # Values should match (approximately)
            for s, b in zip(single_result, batch_result[0]):
                assert abs(s - b) < 1e-6


class TestEmbeddingServiceEdgeCases:
    """Test edge cases and error conditions."""

    def test_embed_text_with_newlines(self):
        """Test embedding text with newlines."""
        # Reset model
        EmbeddingService._model = None

        mock_model = Mock()
        mock_embedding = np.array([0.8] * 384)
        mock_model.encode.return_value = mock_embedding

        with patch("app.services.embedding_service.SentenceTransformer") as mock_st:
            mock_st.return_value = mock_model

            text_with_newlines = "Line 1\nLine 2\nLine 3"
            result = EmbeddingService.embed_text(text_with_newlines)

            assert len(result) == 384
            mock_model.encode.assert_called_once()

    def test_embed_text_with_tabs(self):
        """Test embedding text with tabs."""
        # Reset model
        EmbeddingService._model = None

        mock_model = Mock()
        mock_embedding = np.array([0.9] * 384)
        mock_model.encode.return_value = mock_embedding

        with patch("app.services.embedding_service.SentenceTransformer") as mock_st:
            mock_st.return_value = mock_model

            text_with_tabs = "Column1\tColumn2\tColumn3"
            result = EmbeddingService.embed_text(text_with_tabs)

            assert len(result) == 384

    def test_hash_text_very_long_text(self):
        """Test hashing very long text."""
        long_text = "A" * 1000000  # 1 million characters
        hash_result = EmbeddingService.hash_text(long_text)

        # Should still produce valid hash
        assert len(hash_result) == 64
        assert isinstance(hash_result, str)

    def test_embed_batch_preserves_order(self):
        """Test that batch embedding preserves input order."""
        # Reset model
        EmbeddingService._model = None

        mock_model = Mock()
        # Different embeddings for each input
        mock_embeddings = np.array(
            [
                [0.1] * 384,
                [0.2] * 384,
                [0.3] * 384,
                [0.4] * 384,
                [0.5] * 384,
            ]
        )
        mock_model.encode.return_value = mock_embeddings

        with patch("app.services.embedding_service.SentenceTransformer") as mock_st:
            mock_st.return_value = mock_model

            texts = ["First", "Second", "Third", "Fourth", "Fifth"]
            result = EmbeddingService.embed_batch(texts)

            # Order should be preserved
            assert len(result) == 5
            # First embedding should be all 0.1, second all 0.2, etc.
            assert all(abs(x - 0.1) < 1e-6 for x in result[0])
            assert all(abs(x - 0.2) < 1e-6 for x in result[1])
            assert all(abs(x - 0.5) < 1e-6 for x in result[4])
