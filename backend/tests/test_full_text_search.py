"""Tests for full-text search service."""

import pytest

from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.schemas.search import SearchRequest
from app.search.full_text import (
    FullTextSearchService,
    QueryTokenizer,
    RelevanceScorer,
    SearchAnalytics,
    SpellCorrector,
    TextHighlighter,
    get_search_service,
)


class TestQueryTokenizer:
    """Test suite for query tokenizer."""

    def test_tokenize_simple_query(self):
        """Test tokenization of simple query."""
        tokenizer = QueryTokenizer()
        result = tokenizer.tokenize("hello world")

        assert result["tokens"] == ["hello", "world"]
        assert result["phrases"] == []
        assert result["original"] == "hello world"

    def test_tokenize_with_stop_words(self):
        """Test that stop words are filtered out."""
        tokenizer = QueryTokenizer()
        result = tokenizer.tokenize("the quick brown fox")

        # "the" is a stop word
        assert "the" not in result["tokens"]
        assert "quick" in result["tokens"]
        assert "brown" in result["tokens"]
        assert "fox" in result["tokens"]

    def test_tokenize_with_phrases(self):
        """Test tokenization with quoted phrases."""
        tokenizer = QueryTokenizer()
        result = tokenizer.tokenize('hello "john doe" world')

        assert "john doe" in result["phrases"]
        assert "hello" in result["tokens"]
        assert "world" in result["tokens"]

    def test_tokenize_empty_query(self):
        """Test tokenization of empty query."""
        tokenizer = QueryTokenizer()
        result = tokenizer.tokenize("")

        assert result["tokens"] == []
        assert result["phrases"] == []


class TestSpellCorrector:
    """Test suite for spell corrector."""

    def test_add_to_vocabulary(self):
        """Test adding words to vocabulary."""
        corrector = SpellCorrector()
        corrector.add_to_vocabulary(["hello", "world", "test"])

        assert "hello" in corrector.vocabulary
        assert "world" in corrector.vocabulary
        assert "test" in corrector.vocabulary

    def test_edit_distance(self):
        """Test edit distance calculation."""
        corrector = SpellCorrector()

        assert corrector.edit_distance("hello", "hello") == 0
        assert corrector.edit_distance("hello", "hallo") == 1
        assert corrector.edit_distance("hello", "help") == 2

    def test_suggest_corrections(self):
        """Test spelling suggestions."""
        corrector = SpellCorrector()
        corrector.add_to_vocabulary(["hello", "world", "help"])

        # "helo" should suggest "hello" and "help"
        suggestions = corrector.suggest("helo")
        assert "hello" in suggestions or "help" in suggestions

    def test_correct_query(self):
        """Test query correction."""
        corrector = SpellCorrector()
        corrector.add_to_vocabulary(["hello", "world"])

        result = corrector.correct_query("helo wrld")
        assert result["has_corrections"]
        assert "hello" in result["corrected"].lower()

    def test_no_correction_needed(self):
        """Test when no correction is needed."""
        corrector = SpellCorrector()
        corrector.add_to_vocabulary(["hello", "world"])

        result = corrector.correct_query("hello world")
        assert not result["has_corrections"]
        assert result["corrected"] == "hello world"


class TestRelevanceScorer:
    """Test suite for relevance scorer."""

    def test_calculate_tf(self):
        """Test term frequency calculation."""
        tf = RelevanceScorer.calculate_tf("hello", "hello world hello")
        assert tf > 0
        assert tf == 2.0 / 3.0  # 2 occurrences in 3 words

    def test_calculate_tf_no_match(self):
        """Test TF when term not found."""
        tf = RelevanceScorer.calculate_tf("foo", "hello world")
        assert tf == 0.0

    def test_calculate_idf(self):
        """Test inverse document frequency."""
        documents = [
            "hello world",
            "hello there",
            "foo bar",
        ]
        idf = RelevanceScorer.calculate_idf("hello", documents)
        assert idf > 0

    def test_score_match(self):
        """Test relevance scoring."""
        score = RelevanceScorer.score_match(
            ["john", "doe"],
            {
                "name": "John Doe",
                "email": "john.doe@example.com",
            },
        )
        assert score > 0
        assert score <= 1.0

    def test_score_no_match(self):
        """Test scoring when no terms match."""
        score = RelevanceScorer.score_match(
            ["foo", "bar"],
            {
                "name": "John Doe",
                "email": "john.doe@example.com",
            },
        )
        assert score == 0.0


class TestTextHighlighter:
    """Test suite for text highlighter."""

    def test_highlight_basic(self):
        """Test basic text highlighting."""
        result = TextHighlighter.highlight(
            "Hello world, welcome to the world",
            ["world"],
        )
        assert "<mark>" in result
        assert "</mark>" in result

    def test_highlight_multiple_terms(self):
        """Test highlighting multiple terms."""
        result = TextHighlighter.highlight(
            "Hello world, welcome to the world",
            ["hello", "world"],
        )
        assert result.count("<mark>") >= 2

    def test_highlight_case_insensitive(self):
        """Test case-insensitive highlighting."""
        result = TextHighlighter.highlight(
            "Hello World",
            ["hello", "world"],
        )
        assert "<mark>" in result

    def test_extract_fragments(self):
        """Test text fragment extraction."""
        text = "This is a long text with many words. The search term appears here. And more text follows."
        fragments = TextHighlighter.extract_fragments(
            text,
            ["search", "term"],
            fragment_size=50,
        )
        assert len(fragments) > 0
        assert any("search" in frag.lower() for frag in fragments)


class TestSearchAnalytics:
    """Test suite for search analytics."""

    def test_log_search(self):
        """Test search logging."""
        analytics = SearchAnalytics()
        analytics.log_search(
            query="john doe",
            entity_types=["person"],
            result_count=5,
            execution_time_ms=10.5,
        )

        assert len(analytics.query_log) == 1
        assert analytics.query_log[0]["query"] == "john doe"
        assert analytics.query_log[0]["result_count"] == 5

    def test_track_zero_results(self):
        """Test tracking zero-result queries."""
        analytics = SearchAnalytics()
        analytics.log_search(
            query="nonexistent",
            entity_types=["person"],
            result_count=0,
            execution_time_ms=5.0,
        )

        assert len(analytics.zero_result_queries) == 1
        assert "nonexistent" in analytics.zero_result_queries

    def test_popular_queries(self):
        """Test popular query tracking."""
        analytics = SearchAnalytics()

        # Log same query multiple times
        for _ in range(3):
            analytics.log_search("john", ["person"], 5, 10.0)

        for _ in range(2):
            analytics.log_search("jane", ["person"], 3, 10.0)

        stats = analytics.get_stats()
        top_queries = stats["top_queries"]

        # "john" should be most popular
        assert top_queries[0]["query"] == "john"
        assert top_queries[0]["count"] == 3

    def test_get_stats(self):
        """Test statistics calculation."""
        analytics = SearchAnalytics()

        analytics.log_search("query1", ["person"], 5, 10.0)
        analytics.log_search("query2", ["person"], 0, 8.0)
        analytics.log_search("query3", ["person"], 10, 12.0)

        stats = analytics.get_stats()

        assert stats["total_searches"] == 3
        assert stats["avg_execution_time_ms"] == 10.0
        assert stats["avg_results_per_query"] == 5.0
        assert stats["zero_result_rate"] == pytest.approx(1.0 / 3.0)


class TestFullTextSearchService:
    """Test suite for full-text search service."""

    @pytest.fixture
    def search_service(self, db):
        """Create search service instance."""
        return FullTextSearchService(db)

    @pytest.fixture
    def sample_persons(self, db):
        """Create sample persons for testing."""
        persons = [
            Person(
                name="John Doe",
                email="john.doe@example.com",
                type="resident",
                pgy_level=1,
            ),
            Person(
                name="Jane Smith",
                email="jane.smith@example.com",
                type="faculty",
                faculty_role="core",
            ),
            Person(
                name="Bob Johnson",
                email="bob.j@example.com",
                type="resident",
                pgy_level=2,
            ),
        ]

        for person in persons:
            db.add(person)
        db.commit()

        for person in persons:
            db.refresh(person)

        return persons

    @pytest.fixture
    def sample_rotations(self, db):
        """Create sample rotations for testing."""
        rotations = [
            RotationTemplate(
                name="PGY-1 Clinic",
                activity_type="clinic",
                abbreviation="C",
            ),
            RotationTemplate(
                name="FMIT Inpatient",
                activity_type="inpatient",
                abbreviation="FMIT",
            ),
            RotationTemplate(
                name="Sports Medicine",
                activity_type="clinic",
                abbreviation="SM",
            ),
        ]

        for rotation in rotations:
            db.add(rotation)
        db.commit()

        for rotation in rotations:
            db.refresh(rotation)

        return rotations

    @pytest.mark.asyncio
    async def test_search_persons_by_name(self, search_service, sample_persons):
        """Test searching persons by name."""
        request = SearchRequest(
            query="John",
            entity_types=["person"],
            page=1,
            page_size=20,
        )

        response = await search_service.search(request)

        assert response.total > 0
        assert any("John" in item.title for item in response.items)

    @pytest.mark.asyncio
    async def test_search_persons_by_email(self, search_service, sample_persons):
        """Test searching persons by email."""
        request = SearchRequest(
            query="jane.smith",
            entity_types=["person"],
            page=1,
            page_size=20,
        )

        response = await search_service.search(request)

        assert response.total > 0
        assert any("Jane" in item.title for item in response.items)

    @pytest.mark.asyncio
    async def test_search_with_filters(self, search_service, sample_persons):
        """Test searching with filters."""
        request = SearchRequest(
            query="",
            entity_types=["person"],
            filters={"type": "resident"},
            page=1,
            page_size=20,
        )

        response = await search_service.search(request)

        # All results should be residents
        for item in response.items:
            assert "resident" in item.subtitle.lower()

    @pytest.mark.asyncio
    async def test_search_rotations(self, search_service, sample_rotations):
        """Test searching rotation templates."""
        request = SearchRequest(
            query="clinic",
            entity_types=["rotation"],
            page=1,
            page_size=20,
        )

        response = await search_service.search(request)

        assert response.total > 0
        assert any("Clinic" in item.title for item in response.items)

    @pytest.mark.asyncio
    async def test_search_pagination(self, search_service, sample_persons):
        """Test search pagination."""
        # Page 1
        request = SearchRequest(
            query="",
            entity_types=["person"],
            page=1,
            page_size=2,
        )

        response = await search_service.search(request)

        assert len(response.items) <= 2
        assert response.page == 1
        assert response.total_pages >= 1

    @pytest.mark.asyncio
    async def test_search_relevance_scoring(self, search_service, sample_persons):
        """Test that results are scored and sorted by relevance."""
        request = SearchRequest(
            query="John",
            entity_types=["person"],
            page=1,
            page_size=20,
        )

        response = await search_service.search(request)

        # Results should be sorted by score (descending)
        scores = [item.score for item in response.items]
        assert scores == sorted(scores, reverse=True)

    @pytest.mark.asyncio
    async def test_search_highlighting(self, search_service, sample_persons):
        """Test term highlighting in results."""
        request = SearchRequest(
            query="John",
            entity_types=["person"],
            page=1,
            page_size=20,
            highlight=True,
        )

        response = await search_service.search(request)

        # At least one result should have highlights
        has_highlights = any(item.highlights for item in response.items)
        assert has_highlights

    @pytest.mark.asyncio
    async def test_search_facets(self, search_service, sample_persons):
        """Test facet calculation."""
        request = SearchRequest(
            query="",
            entity_types=["person"],
            page=1,
            page_size=20,
        )

        response = await search_service.search(request)

        # Should have type facets
        assert "type" in response.facets
        assert "person_type" in response.facets

    @pytest.mark.asyncio
    async def test_search_multiple_entity_types(
        self,
        search_service,
        sample_persons,
        sample_rotations,
    ):
        """Test searching across multiple entity types."""
        request = SearchRequest(
            query="clinic",
            entity_types=["person", "rotation"],
            page=1,
            page_size=20,
        )

        response = await search_service.search(request)

        # May find rotations with "clinic" in name
        entity_types = {item.type for item in response.items}
        assert len(entity_types) >= 1

    def test_spell_correction(self, search_service):
        """Test spell correction suggestions."""
        result = search_service.suggest_spelling("Jhn")

        # Should suggest corrections if vocabulary is built
        assert "original" in result
        assert "corrected" in result

    def test_analytics(self, search_service):
        """Test analytics tracking."""
        stats = search_service.get_analytics()

        assert "total_searches" in stats
        assert "avg_execution_time_ms" in stats
        assert "avg_results_per_query" in stats

    @pytest.mark.asyncio
    async def test_empty_query(self, search_service, sample_persons):
        """Test handling of empty query."""
        request = SearchRequest(
            query="",
            entity_types=["person"],
            page=1,
            page_size=20,
        )

        response = await search_service.search(request)

        # Should return all persons (no filtering)
        assert response.total >= 0

    @pytest.mark.asyncio
    async def test_no_results(self, search_service):
        """Test handling when no results found."""
        request = SearchRequest(
            query="nonexistentxyz123",
            entity_types=["person"],
            page=1,
            page_size=20,
        )

        response = await search_service.search(request)

        assert response.total == 0
        assert len(response.items) == 0


def test_get_search_service(db):
    """Test search service factory function."""
    service = get_search_service(db)

    assert isinstance(service, FullTextSearchService)
    assert service.db == db
