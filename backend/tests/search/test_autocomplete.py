"""
Tests for autocomplete service.

Comprehensive test suite for autocomplete functionality,
covering suggestions, context filtering, and caching.
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock

from app.search.autocomplete import (
    AutocompleteContext,
    SuggestionSource,
    AutocompleteSuggestion,
    AutocompleteAnalytics,
)


class TestAutocompleteContext:
    """Test suite for AutocompleteContext enum."""

    def test_context_values(self):
        """Test AutocompleteContext has all expected values."""
        # Assert
        assert AutocompleteContext.PERSON == "person"
        assert AutocompleteContext.ROTATION == "rotation"
        assert AutocompleteContext.PROCEDURE == "procedure"
        assert AutocompleteContext.GLOBAL == "global"


class TestSuggestionSource:
    """Test suite for SuggestionSource enum."""

    def test_source_values(self):
        """Test SuggestionSource has all expected values."""
        # Assert
        assert SuggestionSource.DATABASE == "database"
        assert SuggestionSource.POPULAR == "popular"
        assert SuggestionSource.PERSONALIZED == "personalized"
        assert SuggestionSource.CACHED == "cached"
        assert SuggestionSource.TYPO_CORRECTED == "typo_corrected"


class TestAutocompleteSuggestion:
    """Test suite for AutocompleteSuggestion dataclass."""

    def test_suggestion_creation(self):
        """Test creating an autocomplete suggestion."""
        # Act
        suggestion = AutocompleteSuggestion(
            text="Dr. John Smith",
            context=AutocompleteContext.PERSON,
            source=SuggestionSource.DATABASE,
            score=0.95,
            metadata={"id": "123", "type": "faculty"},
            matched_field="name",
        )

        # Assert
        assert suggestion.text == "Dr. John Smith"
        assert suggestion.context == AutocompleteContext.PERSON
        assert suggestion.source == SuggestionSource.DATABASE
        assert suggestion.score == 0.95
        assert suggestion.metadata["id"] == "123"
        assert suggestion.matched_field == "name"

    def test_suggestion_default_values(self):
        """Test suggestion uses default values when not provided."""
        # Act
        suggestion = AutocompleteSuggestion(
            text="Test",
            context=AutocompleteContext.GLOBAL,
            source=SuggestionSource.DATABASE,
        )

        # Assert
        assert suggestion.score == 1.0  # Default
        assert suggestion.metadata == {}  # Default
        assert suggestion.matched_field is None  # Default

    def test_suggestion_to_dict(self):
        """Test converting suggestion to dictionary."""
        # Arrange
        suggestion = AutocompleteSuggestion(
            text="Cardiology Rotation",
            context=AutocompleteContext.ROTATION,
            source=SuggestionSource.POPULAR,
            score=0.87654321,
            metadata={"rotation_id": "rot-456"},
            matched_field="name",
        )

        # Act
        result = suggestion.to_dict()

        # Assert
        assert result["text"] == "Cardiology Rotation"
        assert result["context"] == "rotation"
        assert result["source"] == "popular"
        assert result["score"] == 0.877  # Rounded to 3 decimals
        assert result["metadata"]["rotation_id"] == "rot-456"
        assert result["matched_field"] == "name"


class TestAutocompleteAnalytics:
    """Test suite for AutocompleteAnalytics dataclass."""

    def test_analytics_creation(self):
        """Test creating autocomplete analytics."""
        # Act
        analytics = AutocompleteAnalytics(
            query="john",
            user_id="user-123",
            context=AutocompleteContext.PERSON,
            suggestions_count=5,
            cache_hit=True,
            response_time_ms=12.5,
            sources_used=["database", "popular"],
        )

        # Assert
        assert analytics.query == "john"
        assert analytics.user_id == "user-123"
        assert analytics.context == AutocompleteContext.PERSON
        assert analytics.suggestions_count == 5
        assert analytics.cache_hit is True
        assert analytics.response_time_ms == 12.5
        assert analytics.sources_used == ["database", "popular"]
        assert isinstance(analytics.timestamp, datetime)

    def test_analytics_to_dict(self):
        """Test converting analytics to dictionary."""
        # Arrange
        analytics = AutocompleteAnalytics(
            query="test",
            user_id=None,
            context=AutocompleteContext.GLOBAL,
            suggestions_count=10,
            cache_hit=False,
            response_time_ms=25.123456,
            sources_used=["database"],
        )

        # Act
        result = analytics.to_dict()

        # Assert
        assert result["query"] == "test"
        assert result["user_id"] is None
        assert result["context"] == "global"
        assert result["suggestions_count"] == 10
        assert result["cache_hit"] is False
        assert result["response_time_ms"] == 25.12  # Rounded to 2 decimals
        assert result["sources_used"] == ["database"]
        assert "timestamp" in result


class TestAutocompleteSuggestionComparison:
    """Test suite for suggestion comparison and ranking."""

    def test_suggestions_can_be_sorted_by_score(self):
        """Test suggestions can be sorted by relevance score."""
        # Arrange
        s1 = AutocompleteSuggestion(
            text="A",
            context=AutocompleteContext.PERSON,
            source=SuggestionSource.DATABASE,
            score=0.5,
        )
        s2 = AutocompleteSuggestion(
            text="B",
            context=AutocompleteContext.PERSON,
            source=SuggestionSource.DATABASE,
            score=0.9,
        )
        s3 = AutocompleteSuggestion(
            text="C",
            context=AutocompleteContext.PERSON,
            source=SuggestionSource.DATABASE,
            score=0.7,
        )

        # Act
        sorted_suggestions = sorted([s1, s2, s3], key=lambda s: s.score, reverse=True)

        # Assert
        assert sorted_suggestions[0].text == "B"  # Highest score
        assert sorted_suggestions[1].text == "C"
        assert sorted_suggestions[2].text == "A"  # Lowest score


class TestAutocompleteSuggestionMetadata:
    """Test suite for suggestion metadata handling."""

    def test_metadata_stores_additional_info(self):
        """Test metadata can store additional information."""
        # Arrange
        metadata = {
            "id": "person-123",
            "pgy_level": 2,
            "specialty": "family_medicine",
            "active": True,
            "last_updated": "2025-01-01",
        }

        # Act
        suggestion = AutocompleteSuggestion(
            text="PGY2-01",
            context=AutocompleteContext.PERSON,
            source=SuggestionSource.DATABASE,
            metadata=metadata,
        )

        # Assert
        assert suggestion.metadata["id"] == "person-123"
        assert suggestion.metadata["pgy_level"] == 2
        assert suggestion.metadata["specialty"] == "family_medicine"
        assert suggestion.metadata["active"] is True
        assert suggestion.metadata["last_updated"] == "2025-01-01"
