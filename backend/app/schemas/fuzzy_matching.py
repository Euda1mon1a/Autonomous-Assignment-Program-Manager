"""Fuzzy matching schemas for request/response validation."""

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class FuzzyMatchAlgorithm(str):
    """Available fuzzy matching algorithms."""

    LEVENSHTEIN = "levenshtein"
    SOUNDEX = "soundex"
    METAPHONE = "metaphone"
    NGRAM = "ngram"
    COMBINED = "combined"


class FuzzyMatchRequest(BaseModel):
    """Request schema for fuzzy matching."""

    query: str = Field(..., min_length=1, max_length=500, description="Text to match")
    candidates: list[str] = Field(
        ..., min_items=1, description="List of candidate strings to match against"
    )
    algorithm: str = Field(
        default=FuzzyMatchAlgorithm.COMBINED,
        description="Algorithm to use: levenshtein, soundex, metaphone, ngram, or combined",
    )
    threshold: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score (0.0-1.0) to include in results",
    )
    max_results: int = Field(
        default=10, ge=1, le=100, description="Maximum number of results to return"
    )
    case_sensitive: bool = Field(
        default=False, description="Whether matching should be case-sensitive"
    )

    @field_validator("algorithm")
    @classmethod
    def validate_algorithm(cls, v: str) -> str:
        """Validate algorithm type."""
        valid_algorithms = {
            FuzzyMatchAlgorithm.LEVENSHTEIN,
            FuzzyMatchAlgorithm.SOUNDEX,
            FuzzyMatchAlgorithm.METAPHONE,
            FuzzyMatchAlgorithm.NGRAM,
            FuzzyMatchAlgorithm.COMBINED,
        }
        if v not in valid_algorithms:
            raise ValueError(
                f"Invalid algorithm: {v}. Must be one of: {', '.join(valid_algorithms)}"
            )
        return v


class FuzzyMatchResult(BaseModel):
    """Individual fuzzy match result."""

    value: str = Field(..., description="Matched candidate string")
    score: float = Field(..., ge=0.0, le=1.0, description="Similarity score (0.0-1.0)")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score (0.0-1.0)"
    )
    algorithm_scores: dict[str, float] = Field(
        default_factory=dict, description="Individual scores from each algorithm used"
    )
    rank: int = Field(..., ge=1, description="Rank in result set (1-based)")

    class Config:
        from_attributes = True


class FuzzyMatchResponse(BaseModel):
    """Response schema for fuzzy matching."""

    query: str = Field(..., description="Original query string")
    matches: list[FuzzyMatchResult] = Field(..., description="Matched results")
    total_candidates: int = Field(
        ..., description="Total number of candidates searched"
    )
    total_matches: int = Field(..., description="Total number of matches found")
    algorithm: str = Field(..., description="Algorithm used for matching")
    threshold: float = Field(..., description="Threshold used for filtering")
    execution_time_ms: float = Field(..., description="Execution time in milliseconds")


class NameMatchRequest(BaseModel):
    """Request schema for name matching (specialized for person names)."""

    query: str = Field(
        ..., min_length=1, max_length=200, description="Name to search for"
    )
    entity_type: str = Field(
        default="person", description="Entity type to search: person, faculty, resident"
    )
    threshold: float = Field(
        default=0.7, ge=0.0, le=1.0, description="Minimum similarity score for matches"
    )
    max_results: int = Field(
        default=10, ge=1, le=50, description="Maximum results to return"
    )
    include_nicknames: bool = Field(
        default=True, description="Include nickname matching"
    )
    include_phonetic: bool = Field(
        default=True, description="Include phonetic matching"
    )

    @field_validator("entity_type")
    @classmethod
    def validate_entity_type(cls, v: str) -> str:
        """Validate entity type."""
        valid_types = {"person", "faculty", "resident"}
        if v not in valid_types:
            raise ValueError(
                f"Invalid entity type: {v}. Must be one of: {', '.join(valid_types)}"
            )
        return v


class NameMatchResult(BaseModel):
    """Individual name match result with entity information."""

    id: UUID = Field(..., description="Entity ID")
    name: str = Field(..., description="Matched name")
    score: float = Field(..., ge=0.0, le=1.0, description="Similarity score")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    entity_type: str = Field(
        ..., description="Type of entity (person, faculty, resident)"
    )
    match_type: str = Field(
        ..., description="Type of match: exact, fuzzy, phonetic, nickname"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional entity metadata (email, role, etc.)",
    )

    class Config:
        from_attributes = True


class NameMatchResponse(BaseModel):
    """Response schema for name matching."""

    query: str = Field(..., description="Original query")
    matches: list[NameMatchResult] = Field(..., description="Matched entities")
    total_matches: int = Field(..., description="Total matches found")
    execution_time_ms: float = Field(..., description="Execution time in milliseconds")


class DeduplicationRequest(BaseModel):
    """Request schema for fuzzy deduplication."""

    items: list[str] = Field(
        ..., min_items=1, description="List of items to deduplicate"
    )
    threshold: float = Field(
        default=0.85,
        ge=0.0,
        le=1.0,
        description="Similarity threshold for considering items as duplicates",
    )
    algorithm: str = Field(
        default=FuzzyMatchAlgorithm.COMBINED,
        description="Algorithm to use for comparison",
    )
    keep_first: bool = Field(
        default=True,
        description="Keep first occurrence of duplicates (vs. highest quality)",
    )

    @field_validator("algorithm")
    @classmethod
    def validate_algorithm(cls, v: str) -> str:
        """Validate algorithm type."""
        valid_algorithms = {
            FuzzyMatchAlgorithm.LEVENSHTEIN,
            FuzzyMatchAlgorithm.SOUNDEX,
            FuzzyMatchAlgorithm.METAPHONE,
            FuzzyMatchAlgorithm.NGRAM,
            FuzzyMatchAlgorithm.COMBINED,
        }
        if v not in valid_algorithms:
            raise ValueError(f"Invalid algorithm: {v}")
        return v


class DuplicateGroup(BaseModel):
    """Group of duplicate items."""

    canonical: str = Field(..., description="Canonical (kept) item")
    duplicates: list[str] = Field(..., description="Duplicate items")
    similarity_scores: dict[str, float] = Field(
        default_factory=dict,
        description="Similarity score of each duplicate to canonical",
    )


class DeduplicationResponse(BaseModel):
    """Response schema for fuzzy deduplication."""

    original_count: int = Field(..., description="Original number of items")
    deduplicated_count: int = Field(
        ..., description="Number of unique items after deduplication"
    )
    duplicates_removed: int = Field(..., description="Number of duplicates removed")
    unique_items: list[str] = Field(
        ..., description="Deduplicated list of unique items"
    )
    duplicate_groups: list[DuplicateGroup] = Field(
        ..., description="Groups of duplicates found"
    )
    execution_time_ms: float = Field(..., description="Execution time in milliseconds")


class BatchFuzzyMatchRequest(BaseModel):
    """Request schema for batch fuzzy matching."""

    queries: list[str] = Field(
        ..., min_items=1, max_items=1000, description="List of queries to match"
    )
    candidates: list[str] = Field(
        ..., min_items=1, description="List of candidates to match against"
    )
    algorithm: str = Field(
        default=FuzzyMatchAlgorithm.COMBINED, description="Algorithm to use"
    )
    threshold: float = Field(
        default=0.6, ge=0.0, le=1.0, description="Similarity threshold"
    )
    max_results_per_query: int = Field(
        default=5, ge=1, le=50, description="Maximum results per query"
    )

    @field_validator("algorithm")
    @classmethod
    def validate_algorithm(cls, v: str) -> str:
        """Validate algorithm type."""
        valid_algorithms = {
            FuzzyMatchAlgorithm.LEVENSHTEIN,
            FuzzyMatchAlgorithm.SOUNDEX,
            FuzzyMatchAlgorithm.METAPHONE,
            FuzzyMatchAlgorithm.NGRAM,
            FuzzyMatchAlgorithm.COMBINED,
        }
        if v not in valid_algorithms:
            raise ValueError(f"Invalid algorithm: {v}")
        return v


class BatchFuzzyMatchResult(BaseModel):
    """Result for a single query in batch matching."""

    query: str = Field(..., description="Query string")
    matches: list[FuzzyMatchResult] = Field(..., description="Matches for this query")
    best_match: FuzzyMatchResult | None = Field(
        None, description="Best match (highest score)"
    )


class BatchFuzzyMatchResponse(BaseModel):
    """Response schema for batch fuzzy matching."""

    results: list[BatchFuzzyMatchResult] = Field(
        ..., description="Results for each query"
    )
    total_queries: int = Field(..., description="Total number of queries processed")
    total_matches: int = Field(
        ..., description="Total matches found across all queries"
    )
    successful_queries: int = Field(
        ..., description="Number of queries with at least one match"
    )
    failed_queries: int = Field(..., description="Number of queries with no matches")
    execution_time_ms: float = Field(
        ..., description="Total execution time in milliseconds"
    )
    avg_time_per_query_ms: float = Field(
        ..., description="Average time per query in milliseconds"
    )


class MatchConfidenceBreakdown(BaseModel):
    """Detailed breakdown of match confidence scoring."""

    base_score: float = Field(..., description="Base similarity score from algorithm")
    length_penalty: float = Field(..., description="Penalty for length difference")
    phonetic_bonus: float = Field(..., description="Bonus for phonetic similarity")
    prefix_bonus: float = Field(..., description="Bonus for matching prefix")
    exact_token_bonus: float = Field(..., description="Bonus for exact token matches")
    final_confidence: float = Field(..., description="Final confidence score (0.0-1.0)")


class FuzzyMatchConfig(BaseModel):
    """Configuration for fuzzy matching behavior."""

    levenshtein_weight: float = Field(default=0.3, ge=0.0, le=1.0)
    soundex_weight: float = Field(default=0.2, ge=0.0, le=1.0)
    metaphone_weight: float = Field(default=0.2, ge=0.0, le=1.0)
    ngram_weight: float = Field(default=0.3, ge=0.0, le=1.0)
    ngram_size: int = Field(
        default=2, ge=1, le=5, description="N-gram size (bigrams=2, trigrams=3)"
    )
    case_sensitive: bool = Field(default=False)
    normalize_whitespace: bool = Field(default=True)
    remove_punctuation: bool = Field(default=True)
    min_length_for_phonetic: int = Field(
        default=3, description="Minimum string length to use phonetic matching"
    )

    @field_validator(
        "levenshtein_weight", "soundex_weight", "metaphone_weight", "ngram_weight"
    )
    @classmethod
    def validate_weights_sum(cls, v: float, info) -> float:
        """Validate that weights are valid."""
        # Individual validation - full validation done in service
        return v
