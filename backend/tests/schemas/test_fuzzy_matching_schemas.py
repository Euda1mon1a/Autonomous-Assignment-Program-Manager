"""Tests for fuzzy matching schemas (Pydantic validation and field_validator coverage)."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.fuzzy_matching import (
    FuzzyMatchAlgorithm,
    FuzzyMatchRequest,
    FuzzyMatchResult,
    FuzzyMatchResponse,
    NameMatchRequest,
    NameMatchResult,
    NameMatchResponse,
    DeduplicationRequest,
    DuplicateGroup,
    DeduplicationResponse,
    BatchFuzzyMatchRequest,
    BatchFuzzyMatchResult,
    BatchFuzzyMatchResponse,
    MatchConfidenceBreakdown,
    FuzzyMatchConfig,
)


# ===========================================================================
# FuzzyMatchAlgorithm Tests
# ===========================================================================


class TestFuzzyMatchAlgorithm:
    def test_values(self):
        assert FuzzyMatchAlgorithm.LEVENSHTEIN == "levenshtein"
        assert FuzzyMatchAlgorithm.SOUNDEX == "soundex"
        assert FuzzyMatchAlgorithm.METAPHONE == "metaphone"
        assert FuzzyMatchAlgorithm.NGRAM == "ngram"
        assert FuzzyMatchAlgorithm.COMBINED == "combined"


# ===========================================================================
# FuzzyMatchRequest Tests
# ===========================================================================


class TestFuzzyMatchRequest:
    def test_valid(self):
        r = FuzzyMatchRequest(
            query="John Smith",
            candidates=["Jon Smith", "Jane Doe", "John Smyth"],
        )
        assert r.algorithm == FuzzyMatchAlgorithm.COMBINED
        assert r.threshold == 0.6
        assert r.max_results == 10
        assert r.case_sensitive is False

    def test_query_empty(self):
        with pytest.raises(ValidationError):
            FuzzyMatchRequest(query="", candidates=["test"])

    def test_query_too_long(self):
        with pytest.raises(ValidationError):
            FuzzyMatchRequest(query="x" * 501, candidates=["test"])

    def test_candidates_empty(self):
        with pytest.raises(ValidationError):
            FuzzyMatchRequest(query="test", candidates=[])

    def test_threshold_boundaries(self):
        r = FuzzyMatchRequest(query="test", candidates=["test"], threshold=0.0)
        assert r.threshold == 0.0
        r = FuzzyMatchRequest(query="test", candidates=["test"], threshold=1.0)
        assert r.threshold == 1.0

    def test_threshold_above_one(self):
        with pytest.raises(ValidationError):
            FuzzyMatchRequest(query="test", candidates=["test"], threshold=1.1)

    def test_threshold_negative(self):
        with pytest.raises(ValidationError):
            FuzzyMatchRequest(query="test", candidates=["test"], threshold=-0.1)

    def test_max_results_boundaries(self):
        r = FuzzyMatchRequest(query="test", candidates=["test"], max_results=1)
        assert r.max_results == 1
        r = FuzzyMatchRequest(query="test", candidates=["test"], max_results=100)
        assert r.max_results == 100

    def test_max_results_zero(self):
        with pytest.raises(ValidationError):
            FuzzyMatchRequest(query="test", candidates=["test"], max_results=0)

    def test_max_results_above_max(self):
        with pytest.raises(ValidationError):
            FuzzyMatchRequest(query="test", candidates=["test"], max_results=101)

    def test_valid_algorithms(self):
        for algo in [
            "levenshtein",
            "soundex",
            "metaphone",
            "ngram",
            "combined",
        ]:
            r = FuzzyMatchRequest(query="test", candidates=["test"], algorithm=algo)
            assert r.algorithm == algo

    def test_invalid_algorithm(self):
        with pytest.raises(ValidationError):
            FuzzyMatchRequest(query="test", candidates=["test"], algorithm="invalid")


# ===========================================================================
# FuzzyMatchResult Tests
# ===========================================================================


class TestFuzzyMatchResult:
    def test_valid(self):
        r = FuzzyMatchResult(
            value="John Smith",
            score=0.95,
            confidence=0.9,
            rank=1,
        )
        assert r.algorithm_scores == {}

    def test_score_boundaries(self):
        r = FuzzyMatchResult(value="test", score=0.0, confidence=0.0, rank=1)
        assert r.score == 0.0
        r = FuzzyMatchResult(value="test", score=1.0, confidence=1.0, rank=1)
        assert r.score == 1.0

    def test_score_above_one(self):
        with pytest.raises(ValidationError):
            FuzzyMatchResult(value="test", score=1.1, confidence=0.5, rank=1)

    def test_confidence_above_one(self):
        with pytest.raises(ValidationError):
            FuzzyMatchResult(value="test", score=0.5, confidence=1.1, rank=1)

    def test_rank_zero(self):
        with pytest.raises(ValidationError):
            FuzzyMatchResult(value="test", score=0.5, confidence=0.5, rank=0)

    def test_rank_positive(self):
        r = FuzzyMatchResult(value="test", score=0.5, confidence=0.5, rank=1)
        assert r.rank == 1


# ===========================================================================
# FuzzyMatchResponse Tests
# ===========================================================================


class TestFuzzyMatchResponse:
    def test_valid(self):
        r = FuzzyMatchResponse(
            query="test",
            matches=[],
            total_candidates=100,
            total_matches=0,
            algorithm="combined",
            threshold=0.6,
            execution_time_ms=12.5,
        )
        assert r.total_matches == 0


# ===========================================================================
# NameMatchRequest Tests
# ===========================================================================


class TestNameMatchRequest:
    def test_defaults(self):
        r = NameMatchRequest(query="John Smith")
        assert r.entity_type == "person"
        assert r.threshold == 0.7
        assert r.max_results == 10
        assert r.include_nicknames is True
        assert r.include_phonetic is True

    def test_query_empty(self):
        with pytest.raises(ValidationError):
            NameMatchRequest(query="")

    def test_query_too_long(self):
        with pytest.raises(ValidationError):
            NameMatchRequest(query="x" * 201)

    def test_valid_entity_types(self):
        for etype in ["person", "faculty", "resident"]:
            r = NameMatchRequest(query="test", entity_type=etype)
            assert r.entity_type == etype

    def test_invalid_entity_type(self):
        with pytest.raises(ValidationError):
            NameMatchRequest(query="test", entity_type="patient")

    def test_threshold_boundaries(self):
        r = NameMatchRequest(query="test", threshold=0.0)
        assert r.threshold == 0.0
        r = NameMatchRequest(query="test", threshold=1.0)
        assert r.threshold == 1.0

    def test_threshold_above_one(self):
        with pytest.raises(ValidationError):
            NameMatchRequest(query="test", threshold=1.1)

    def test_max_results_boundaries(self):
        r = NameMatchRequest(query="test", max_results=1)
        assert r.max_results == 1
        r = NameMatchRequest(query="test", max_results=50)
        assert r.max_results == 50

    def test_max_results_zero(self):
        with pytest.raises(ValidationError):
            NameMatchRequest(query="test", max_results=0)

    def test_max_results_above_max(self):
        with pytest.raises(ValidationError):
            NameMatchRequest(query="test", max_results=51)


# ===========================================================================
# NameMatchResult Tests
# ===========================================================================


class TestNameMatchResult:
    def test_valid(self):
        r = NameMatchResult(
            id=uuid4(),
            name="John Smith",
            score=0.95,
            confidence=0.9,
            entity_type="faculty",
            match_type="fuzzy",
        )
        assert r.metadata == {}

    def test_score_above_one(self):
        with pytest.raises(ValidationError):
            NameMatchResult(
                id=uuid4(),
                name="test",
                score=1.1,
                confidence=0.5,
                entity_type="person",
                match_type="exact",
            )


# ===========================================================================
# DeduplicationRequest Tests
# ===========================================================================


class TestDeduplicationRequest:
    def test_valid(self):
        r = DeduplicationRequest(items=["John", "Jon", "Jane"])
        assert r.threshold == 0.85
        assert r.algorithm == FuzzyMatchAlgorithm.COMBINED
        assert r.keep_first is True

    def test_items_empty(self):
        with pytest.raises(ValidationError):
            DeduplicationRequest(items=[])

    def test_threshold_boundaries(self):
        r = DeduplicationRequest(items=["a"], threshold=0.0)
        assert r.threshold == 0.0
        r = DeduplicationRequest(items=["a"], threshold=1.0)
        assert r.threshold == 1.0

    def test_threshold_above_one(self):
        with pytest.raises(ValidationError):
            DeduplicationRequest(items=["a"], threshold=1.1)

    def test_invalid_algorithm(self):
        with pytest.raises(ValidationError):
            DeduplicationRequest(items=["a"], algorithm="invalid")

    def test_valid_algorithms(self):
        for algo in ["levenshtein", "soundex", "metaphone", "ngram", "combined"]:
            r = DeduplicationRequest(items=["a", "b"], algorithm=algo)
            assert r.algorithm == algo


# ===========================================================================
# DuplicateGroup Tests
# ===========================================================================


class TestDuplicateGroup:
    def test_valid(self):
        g = DuplicateGroup(
            canonical="John Smith",
            duplicates=["Jon Smith", "John Smyth"],
            similarity_scores={"Jon Smith": 0.9, "John Smyth": 0.85},
        )
        assert len(g.duplicates) == 2

    def test_defaults(self):
        g = DuplicateGroup(canonical="test", duplicates=["tst"])
        assert g.similarity_scores == {}


# ===========================================================================
# DeduplicationResponse Tests
# ===========================================================================


class TestDeduplicationResponse:
    def test_valid(self):
        r = DeduplicationResponse(
            original_count=10,
            deduplicated_count=7,
            duplicates_removed=3,
            unique_items=["a", "b", "c", "d", "e", "f", "g"],
            duplicate_groups=[],
            execution_time_ms=5.0,
        )
        assert r.duplicates_removed == 3


# ===========================================================================
# BatchFuzzyMatchRequest Tests
# ===========================================================================


class TestBatchFuzzyMatchRequest:
    def test_valid(self):
        r = BatchFuzzyMatchRequest(
            queries=["John", "Jane"],
            candidates=["Jon", "Jan", "Jim"],
        )
        assert r.algorithm == FuzzyMatchAlgorithm.COMBINED
        assert r.threshold == 0.6
        assert r.max_results_per_query == 5

    def test_queries_empty(self):
        with pytest.raises(ValidationError):
            BatchFuzzyMatchRequest(queries=[], candidates=["test"])

    def test_queries_too_many(self):
        with pytest.raises(ValidationError):
            BatchFuzzyMatchRequest(queries=["q"] * 1001, candidates=["test"])

    def test_candidates_empty(self):
        with pytest.raises(ValidationError):
            BatchFuzzyMatchRequest(queries=["test"], candidates=[])

    def test_max_results_per_query_boundaries(self):
        r = BatchFuzzyMatchRequest(
            queries=["test"], candidates=["test"], max_results_per_query=1
        )
        assert r.max_results_per_query == 1
        r = BatchFuzzyMatchRequest(
            queries=["test"], candidates=["test"], max_results_per_query=50
        )
        assert r.max_results_per_query == 50

    def test_max_results_per_query_zero(self):
        with pytest.raises(ValidationError):
            BatchFuzzyMatchRequest(
                queries=["test"],
                candidates=["test"],
                max_results_per_query=0,
            )

    def test_invalid_algorithm(self):
        with pytest.raises(ValidationError):
            BatchFuzzyMatchRequest(
                queries=["test"],
                candidates=["test"],
                algorithm="bad",
            )


# ===========================================================================
# BatchFuzzyMatchResult Tests
# ===========================================================================


class TestBatchFuzzyMatchResult:
    def test_valid(self):
        r = BatchFuzzyMatchResult(query="test", matches=[])
        assert r.best_match is None

    def test_with_best_match(self):
        match = FuzzyMatchResult(value="test", score=0.95, confidence=0.9, rank=1)
        r = BatchFuzzyMatchResult(query="test", matches=[match], best_match=match)
        assert r.best_match is not None


# ===========================================================================
# BatchFuzzyMatchResponse Tests
# ===========================================================================


class TestBatchFuzzyMatchResponse:
    def test_valid(self):
        r = BatchFuzzyMatchResponse(
            results=[],
            total_queries=10,
            total_matches=25,
            successful_queries=8,
            failed_queries=2,
            execution_time_ms=150.0,
            avg_time_per_query_ms=15.0,
        )
        assert r.total_queries == 10


# ===========================================================================
# MatchConfidenceBreakdown Tests
# ===========================================================================


class TestMatchConfidenceBreakdown:
    def test_valid(self):
        m = MatchConfidenceBreakdown(
            base_score=0.8,
            length_penalty=0.05,
            phonetic_bonus=0.1,
            prefix_bonus=0.05,
            exact_token_bonus=0.0,
            final_confidence=0.9,
        )
        assert m.final_confidence == 0.9


# ===========================================================================
# FuzzyMatchConfig Tests
# ===========================================================================


class TestFuzzyMatchConfig:
    def test_defaults(self):
        c = FuzzyMatchConfig()
        assert c.levenshtein_weight == 0.3
        assert c.soundex_weight == 0.2
        assert c.metaphone_weight == 0.2
        assert c.ngram_weight == 0.3
        assert c.ngram_size == 2
        assert c.case_sensitive is False
        assert c.normalize_whitespace is True
        assert c.remove_punctuation is True
        assert c.min_length_for_phonetic == 3

    def test_weights_boundary_zero(self):
        c = FuzzyMatchConfig(
            levenshtein_weight=0.0,
            soundex_weight=0.0,
            metaphone_weight=0.0,
            ngram_weight=0.0,
        )
        assert c.levenshtein_weight == 0.0

    def test_weights_boundary_one(self):
        c = FuzzyMatchConfig(levenshtein_weight=1.0)
        assert c.levenshtein_weight == 1.0

    def test_weight_above_one(self):
        with pytest.raises(ValidationError):
            FuzzyMatchConfig(levenshtein_weight=1.1)

    def test_weight_negative(self):
        with pytest.raises(ValidationError):
            FuzzyMatchConfig(soundex_weight=-0.1)

    def test_ngram_size_boundaries(self):
        c = FuzzyMatchConfig(ngram_size=1)
        assert c.ngram_size == 1
        c = FuzzyMatchConfig(ngram_size=5)
        assert c.ngram_size == 5

    def test_ngram_size_zero(self):
        with pytest.raises(ValidationError):
            FuzzyMatchConfig(ngram_size=0)

    def test_ngram_size_above_max(self):
        with pytest.raises(ValidationError):
            FuzzyMatchConfig(ngram_size=6)
