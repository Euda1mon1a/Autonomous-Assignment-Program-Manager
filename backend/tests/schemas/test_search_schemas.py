"""Tests for search schemas (field_validators, Field bounds, defaults)."""

import pytest
from pydantic import ValidationError

from app.schemas.search import (
    SearchRequest,
    SearchResultItem,
    FacetCount,
    SearchFacets,
    SearchResponse,
    SuggestionRequest,
    SuggestionResponse,
    PeopleSearchRequest,
    RotationSearchRequest,
    ProcedureSearchRequest,
    QuickSearchRequest,
    QuickSearchResponse,
)


class TestSearchRequest:
    def test_defaults(self):
        r = SearchRequest(query="Dr. Smith")
        assert r.entity_types == ["person"]
        assert r.filters == {}
        assert r.page == 1
        assert r.page_size == 20
        assert r.sort_by == "relevance"
        assert r.sort_order == "desc"
        assert r.highlight is True
        assert r.fuzzy is True

    # --- query min_length=1, max_length=500 ---

    def test_query_empty(self):
        with pytest.raises(ValidationError):
            SearchRequest(query="")

    def test_query_too_long(self):
        with pytest.raises(ValidationError):
            SearchRequest(query="x" * 501)

    # --- entity_types field_validator ---

    def test_valid_entity_types(self):
        r = SearchRequest(
            query="test",
            entity_types=["person", "rotation", "procedure", "assignment", "swap"],
        )
        assert len(r.entity_types) == 5

    def test_invalid_entity_type(self):
        with pytest.raises(ValidationError, match="Invalid entity types"):
            SearchRequest(query="test", entity_types=["person", "invalid"])

    # --- sort_order field_validator ---

    def test_valid_sort_orders(self):
        r = SearchRequest(query="test", sort_order="asc")
        assert r.sort_order == "asc"
        r = SearchRequest(query="test", sort_order="desc")
        assert r.sort_order == "desc"

    def test_invalid_sort_order(self):
        with pytest.raises(ValidationError, match="sort_order must be 'asc' or 'desc'"):
            SearchRequest(query="test", sort_order="random")

    # --- page ge=1 ---

    def test_page_below_min(self):
        with pytest.raises(ValidationError):
            SearchRequest(query="test", page=0)

    # --- page_size ge=1, le=100 ---

    def test_page_size_below_min(self):
        with pytest.raises(ValidationError):
            SearchRequest(query="test", page_size=0)

    def test_page_size_above_max(self):
        with pytest.raises(ValidationError):
            SearchRequest(query="test", page_size=101)


class TestSearchResultItem:
    def test_valid_minimal(self):
        r = SearchResultItem(id="p1", type="person", title="Dr. Smith")
        assert r.subtitle == ""
        assert r.score == 0.0
        assert r.highlights == {}
        assert r.entity is None

    def test_full(self):
        r = SearchResultItem(
            id="p1",
            type="person",
            title="Dr. Smith",
            subtitle="PGY-2 Resident",
            score=0.95,
            highlights={"name": ["Dr. <em>Smith</em>"]},
            entity={"id": "p1", "name": "Dr. Smith"},
        )
        assert r.score == 0.95
        assert len(r.highlights["name"]) == 1


class TestFacetCount:
    def test_valid(self):
        r = FacetCount(value="resident", count=15)
        assert r.value == "resident"


class TestSearchFacets:
    def test_defaults(self):
        r = SearchFacets()
        assert r.type == {}
        assert r.pgy_level == {}
        assert r.faculty_role == {}
        assert r.status == {}
        assert r.category == {}

    def test_populated(self):
        r = SearchFacets(
            type={"resident": 10, "faculty": 5},
            pgy_level={"1": 3, "2": 4, "3": 3},
        )
        assert r.type["resident"] == 10


class TestSearchResponse:
    def test_valid(self):
        r = SearchResponse(
            items=[], total=0, page=1, page_size=20, total_pages=0, query="test"
        )
        assert r.facets == {}

    def test_with_facets(self):
        r = SearchResponse(
            items=[],
            total=100,
            page=1,
            page_size=20,
            total_pages=5,
            query="Dr.",
            facets={"type": {"resident": 60, "faculty": 40}},
        )
        assert r.facets["type"]["resident"] == 60


class TestSuggestionRequest:
    def test_defaults(self):
        r = SuggestionRequest(query="Dr")
        assert r.entity_type == "person"
        assert r.limit == 10

    # --- query min_length=1, max_length=200 ---

    def test_query_empty(self):
        with pytest.raises(ValidationError):
            SuggestionRequest(query="")

    def test_query_too_long(self):
        with pytest.raises(ValidationError):
            SuggestionRequest(query="x" * 201)

    # --- entity_type field_validator ---

    def test_valid_entity_types(self):
        for et in ("person", "rotation", "procedure", "assignment", "swap"):
            r = SuggestionRequest(query="test", entity_type=et)
            assert r.entity_type == et

    def test_invalid_entity_type(self):
        with pytest.raises(ValidationError, match="Invalid entity type"):
            SuggestionRequest(query="test", entity_type="unknown")

    # --- limit ge=1, le=50 ---

    def test_limit_below_min(self):
        with pytest.raises(ValidationError):
            SuggestionRequest(query="test", limit=0)

    def test_limit_above_max(self):
        with pytest.raises(ValidationError):
            SuggestionRequest(query="test", limit=51)


class TestSuggestionResponse:
    def test_valid(self):
        r = SuggestionResponse(
            suggestions=["Dr. Smith", "Dr. Smithson"],
            query="Dr. Smi",
            entity_type="person",
        )
        assert len(r.suggestions) == 2


class TestPeopleSearchRequest:
    def test_defaults(self):
        r = PeopleSearchRequest(query="Smith")
        assert r.type is None
        assert r.pgy_level is None
        assert r.faculty_role is None
        assert r.page == 1
        assert r.page_size == 20

    def test_valid_type(self):
        r = PeopleSearchRequest(query="test", type="resident")
        assert r.type == "resident"
        r = PeopleSearchRequest(query="test", type="faculty")
        assert r.type == "faculty"

    def test_invalid_type(self):
        with pytest.raises(
            ValidationError, match="type must be 'resident' or 'faculty'"
        ):
            PeopleSearchRequest(query="test", type="nurse")

    # --- pgy_level ge=1, le=3 ---

    def test_pgy_level_below_min(self):
        with pytest.raises(ValidationError):
            PeopleSearchRequest(query="test", pgy_level=0)

    def test_pgy_level_above_max(self):
        with pytest.raises(ValidationError):
            PeopleSearchRequest(query="test", pgy_level=4)

    # --- faculty_role field_validator ---

    def test_valid_faculty_roles(self):
        for role in ("pd", "apd", "oic", "dept_chief", "sports_med", "core"):
            r = PeopleSearchRequest(query="test", faculty_role=role)
            assert r.faculty_role == role

    def test_invalid_faculty_role(self):
        with pytest.raises(ValidationError, match="Invalid faculty role"):
            PeopleSearchRequest(query="test", faculty_role="unknown")


class TestRotationSearchRequest:
    def test_defaults(self):
        r = RotationSearchRequest(query="ICU")
        assert r.category is None
        assert r.page == 1
        assert r.page_size == 20

    def test_query_empty(self):
        with pytest.raises(ValidationError):
            RotationSearchRequest(query="")


class TestProcedureSearchRequest:
    def test_defaults(self):
        r = ProcedureSearchRequest(query="appendectomy")
        assert r.page == 1
        assert r.page_size == 20


class TestQuickSearchRequest:
    def test_defaults(self):
        r = QuickSearchRequest(query="Smith")
        assert r.entity_type == "person"
        assert r.limit == 10

    def test_invalid_entity_type(self):
        with pytest.raises(ValidationError, match="Invalid entity type"):
            QuickSearchRequest(query="test", entity_type="unknown")

    # --- limit ge=1, le=50 ---

    def test_limit_below_min(self):
        with pytest.raises(ValidationError):
            QuickSearchRequest(query="test", limit=0)

    def test_limit_above_max(self):
        with pytest.raises(ValidationError):
            QuickSearchRequest(query="test", limit=51)


class TestQuickSearchResponse:
    def test_valid(self):
        r = QuickSearchResponse(items=[], query="test", entity_type="person")
        assert r.items == []
