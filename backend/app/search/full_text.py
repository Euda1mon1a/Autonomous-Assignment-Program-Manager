"""
Full-text search service for the Residency Scheduler.

Provides comprehensive search capabilities with:
- Multi-field search across entities
- Query parsing and tokenization
- Relevance scoring (TF-IDF based)
- Term highlighting
- Search filters and facets
- Spell correction suggestions
- Pagination support
- Search analytics tracking

Example:
    from app.search.full_text import FullTextSearchService, SearchQuery

    service = FullTextSearchService(db)
    results = await service.search(
        SearchQuery(
            query="John Doe",
            entity_types=["person"],
            page=1,
            page_size=20
        )
    )
"""

import logging
import re
from collections import defaultdict
from datetime import datetime
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models.assignment import Assignment
from app.models.person import Person
from app.models.procedure import Procedure
from app.models.rotation_template import RotationTemplate
from app.models.swap import SwapRecord
from app.schemas.search import (
    SearchRequest,
    SearchResponse,
    SearchResultItem,
)

logger = logging.getLogger(__name__)


class SearchAnalytics:
    """
    Track search analytics for improving search quality.

    Stores metrics like:
    - Query frequency
    - Result counts
    - Click-through rates
    - Zero-result queries
    """

    def __init__(self) -> None:
        """Initialize analytics tracker."""
        self.query_log: list[dict[str, Any]] = []
        self.zero_result_queries: list[str] = []
        self.popular_queries: dict[str, int] = defaultdict(int)

    def log_search(
        self,
        query: str,
        entity_types: list[str],
        result_count: int,
        execution_time_ms: float,
    ) -> None:
        """
        Log a search query.

        Args:
            query: Search query string
            entity_types: List of searched entity types
            result_count: Number of results returned
            execution_time_ms: Query execution time in milliseconds
        """
        self.query_log.append(
            {
                "query": query,
                "entity_types": entity_types,
                "result_count": result_count,
                "execution_time_ms": execution_time_ms,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

        self.popular_queries[query.lower()] += 1

        if result_count == 0:
            self.zero_result_queries.append(query)

    def get_stats(self) -> dict[str, Any]:
        """
        Get analytics statistics.

        Returns:
            Dictionary with analytics metrics
        """
        if not self.query_log:
            return {
                "total_searches": 0,
                "avg_execution_time_ms": 0,
                "avg_results_per_query": 0,
                "zero_result_rate": 0,
                "top_queries": [],
            }

        total_searches = len(self.query_log)
        total_execution_time = sum(log["execution_time_ms"] for log in self.query_log)
        total_results = sum(log["result_count"] for log in self.query_log)

        top_queries = sorted(
            self.popular_queries.items(), key=lambda x: x[1], reverse=True
        )[:10]

        return {
            "total_searches": total_searches,
            "avg_execution_time_ms": total_execution_time / total_searches,
            "avg_results_per_query": total_results / total_searches,
            "zero_result_rate": len(self.zero_result_queries) / total_searches,
            "top_queries": [{"query": q, "count": c} for q, c in top_queries],
        }


class QueryTokenizer:
    """
    Tokenize and parse search queries.

    Handles:
    - Word tokenization
    - Stop word removal
    - Phrase detection
    - Special character handling
    """

    # Common stop words to filter out
    STOP_WORDS = {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "for",
        "from",
        "has",
        "he",
        "in",
        "is",
        "it",
        "its",
        "of",
        "on",
        "that",
        "the",
        "to",
        "was",
        "will",
        "with",
    }

    def __init__(self) -> None:
        """Initialize tokenizer."""
        self.phrase_pattern = re.compile(r'"([^"]+)"')
        self.word_pattern = re.compile(r"\b\w+\b")

    def tokenize(self, query: str) -> dict[str, Any]:
        """
        Tokenize a search query.

        Args:
            query: Raw search query string

        Returns:
            Dictionary with:
            - tokens: List of search tokens
            - phrases: List of quoted phrases
            - original: Original query string
        """
        # Extract quoted phrases
        phrases = self.phrase_pattern.findall(query)

        # Remove quotes and extract words
        query_no_quotes = self.phrase_pattern.sub("", query)
        words = self.word_pattern.findall(query_no_quotes.lower())

        # Filter stop words
        tokens = [w for w in words if w not in self.STOP_WORDS]

        return {
            "tokens": tokens,
            "phrases": phrases,
            "original": query,
        }


class SpellCorrector:
    """
    Provide spell correction suggestions for search queries.

    Uses a simple edit distance algorithm to suggest corrections
    from a known vocabulary.
    """

    def __init__(self, vocabulary: set[str] | None = None) -> None:
        """
        Initialize spell corrector.

        Args:
            vocabulary: Set of known correct words
        """
        self.vocabulary = vocabulary or set()

    def add_to_vocabulary(self, words: list[str]) -> None:
        """
        Add words to the vocabulary.

        Args:
            words: List of words to add
        """
        self.vocabulary.update(word.lower() for word in words)

    def edit_distance(self, word1: str, word2: str) -> int:
        """
        Calculate Levenshtein edit distance between two words.

        Args:
            word1: First word
            word2: Second word

        Returns:
            Edit distance (number of edits needed)
        """
        m, n = len(word1), len(word2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]

        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if word1[i - 1] == word2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1]
                else:
                    dp[i][j] = 1 + min(
                        dp[i - 1][j],  # deletion
                        dp[i][j - 1],  # insertion
                        dp[i - 1][j - 1],  # substitution
                    )

        return dp[m][n]

    def suggest(self, word: str, max_distance: int = 2) -> list[str]:
        """
        Suggest corrections for a misspelled word.

        Args:
            word: Potentially misspelled word
            max_distance: Maximum edit distance for suggestions

        Returns:
            List of suggested corrections
        """
        word_lower = word.lower()

        # If word is in vocabulary, no correction needed
        if word_lower in self.vocabulary:
            return []

        suggestions = []
        for vocab_word in self.vocabulary:
            distance = self.edit_distance(word_lower, vocab_word)
            if distance <= max_distance:
                suggestions.append((vocab_word, distance))

                # Sort by edit distance and return top 5
        suggestions.sort(key=lambda x: x[1])
        return [word for word, _ in suggestions[:5]]

    def correct_query(self, query: str) -> dict[str, Any]:
        """
        Suggest corrections for a query string.

        Args:
            query: Search query string

        Returns:
            Dictionary with:
            - original: Original query
            - corrected: Suggested correction
            - has_corrections: Whether corrections were found
        """
        tokenizer = QueryTokenizer()
        parsed = tokenizer.tokenize(query)

        corrections = {}
        for token in parsed["tokens"]:
            suggestions = self.suggest(token)
            if suggestions:
                corrections[token] = suggestions[0]

        if not corrections:
            return {
                "original": query,
                "corrected": query,
                "has_corrections": False,
            }

        corrected_query = query
        for original, correction in corrections.items():
            corrected_query = re.sub(
                r"\b" + re.escape(original) + r"\b",
                correction,
                corrected_query,
                flags=re.IGNORECASE,
            )

        return {
            "original": query,
            "corrected": corrected_query,
            "has_corrections": True,
            "corrections": corrections,
        }


class RelevanceScorer:
    """
    Calculate relevance scores for search results.

    Uses a simplified TF-IDF (Term Frequency-Inverse Document Frequency)
    approach to score matches.
    """

    @staticmethod
    def calculate_tf(term: str, text: str) -> float:
        """
        Calculate term frequency.

        Args:
            term: Search term
            text: Text to search in

        Returns:
            Term frequency (0-1)
        """
        if not text:
            return 0.0

        text_lower = text.lower()
        term_lower = term.lower()

        count = text_lower.count(term_lower)
        words = len(text.split())

        if words == 0:
            return 0.0

        return count / words

    @staticmethod
    def calculate_idf(term: str, documents: list[str]) -> float:
        """
        Calculate inverse document frequency.

        Args:
            term: Search term
            documents: List of all documents

        Returns:
            IDF score
        """
        if not documents:
            return 0.0

        term_lower = term.lower()
        doc_count = sum(1 for doc in documents if term_lower in doc.lower())

        if doc_count == 0:
            return 0.0

        import math

        return math.log(len(documents) / doc_count)

    @staticmethod
    def score_match(
        query_tokens: list[str],
        fields: dict[str, str],
        field_weights: dict[str, float] | None = None,
    ) -> float:
        """
        Calculate relevance score for a match.

        Args:
            query_tokens: Tokenized search query
            fields: Dictionary of field_name -> field_value
            field_weights: Optional weights for each field

        Returns:
            Relevance score (0-1)
        """
        if not query_tokens:
            return 0.0

        default_weights = {
            "name": 3.0,
            "email": 2.0,
            "type": 1.5,
            "description": 1.0,
        }

        weights = field_weights or default_weights
        total_score = 0.0
        max_possible = 0.0

        for field_name, field_value in fields.items():
            if not field_value:
                continue

            weight = weights.get(field_name, 1.0)
            max_possible += weight

            field_score = 0.0
            for token in query_tokens:
                tf = RelevanceScorer.calculate_tf(token, field_value)
                field_score += tf

            total_score += field_score * weight

        if max_possible == 0:
            return 0.0

        return min(total_score / max_possible, 1.0)


class TextHighlighter:
    """
    Highlight matching terms in search results.

    Wraps matched terms with markers for UI highlighting.
    """

    @staticmethod
    def highlight(
        text: str,
        terms: list[str],
        before: str = "<mark>",
        after: str = "</mark>",
        max_length: int = 200,
    ) -> str:
        """
        Highlight matching terms in text.

        Args:
            text: Text to highlight
            terms: Terms to highlight
            before: Opening marker
            after: Closing marker
            max_length: Maximum length of highlighted snippet

        Returns:
            Highlighted text snippet
        """
        if not text or not terms:
            return text[:max_length] if text else ""

        text_lower = text.lower()

        # Find first match position
        first_match = -1
        for term in terms:
            pos = text_lower.find(term.lower())
            if pos != -1 and (first_match == -1 or pos < first_match):
                first_match = pos

                # Extract snippet around match
        if first_match == -1:
            snippet = text[:max_length]
        else:
            start = max(0, first_match - 50)
            end = min(len(text), first_match + max_length - 50)
            snippet = text[start:end]
            if start > 0:
                snippet = "..." + snippet
            if end < len(text):
                snippet = snippet + "..."

                # Highlight terms
        highlighted = snippet
        for term in terms:
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            highlighted = pattern.sub(f"{before}{term}{after}", highlighted)

        return highlighted

    @staticmethod
    def extract_fragments(
        text: str,
        terms: list[str],
        fragment_size: int = 100,
        max_fragments: int = 3,
    ) -> list[str]:
        """
        Extract text fragments containing matching terms.

        Args:
            text: Text to extract from
            terms: Terms to match
            fragment_size: Size of each fragment
            max_fragments: Maximum number of fragments

        Returns:
            List of text fragments
        """
        if not text or not terms:
            return []

        text_lower = text.lower()
        matches = []

        for term in terms:
            pos = 0
            while True:
                pos = text_lower.find(term.lower(), pos)
                if pos == -1:
                    break
                matches.append(pos)
                pos += 1

        if not matches:
            return []

        matches.sort()
        fragments = []

        for i, match_pos in enumerate(matches[:max_fragments]):
            start = max(0, match_pos - fragment_size // 2)
            end = min(len(text), match_pos + fragment_size // 2)
            fragment = text[start:end]

            if start > 0:
                fragment = "..." + fragment
            if end < len(text):
                fragment = fragment + "..."

            fragments.append(fragment)

        return fragments


class FullTextSearchService:
    """
    Full-text search service for the Residency Scheduler.

    Provides comprehensive search across all entities with:
    - Multi-field search
    - Relevance ranking
    - Highlighting
    - Faceted search
    - Spell correction
    - Analytics
    """

    def __init__(self, db: Session) -> None:
        """
        Initialize search service.

        Args:
            db: Database session
        """
        self.db = db
        self.tokenizer = QueryTokenizer()
        self.spell_corrector = SpellCorrector()
        self.analytics = SearchAnalytics()

        # Build vocabulary from database
        self._build_vocabulary()

    def _build_vocabulary(self) -> None:
        """Build spell-check vocabulary from database."""
        try:
            # Get person names
            persons = self.db.query(Person.name).all()
            names = [name for (name,) in persons if name]

            # Get rotation names
            rotations = self.db.query(RotationTemplate.name).all()
            rotation_names = [name for (name,) in rotations if name]

            # Get procedure names
            procedures = self.db.query(Procedure.name).all()
            procedure_names = [name for (name,) in procedures if name]

            # Combine and add to vocabulary
            all_names = names + rotation_names + procedure_names
            words = []
            for name in all_names:
                words.extend(name.lower().split())

            self.spell_corrector.add_to_vocabulary(words)

        except Exception as e:
            logger.warning(f"Error building vocabulary: {e}")

    async def search(self, search_request: SearchRequest) -> SearchResponse:
        """
        Execute a full-text search.

        Args:
            search_request: Search request parameters

        Returns:
            Search response with results
        """
        start_time = datetime.utcnow()

        # Tokenize query
        parsed = self.tokenizer.tokenize(search_request.query)

        # Search each entity type
        all_results = []

        if "person" in search_request.entity_types:
            person_results = await self._search_persons(parsed, search_request.filters)
            all_results.extend(person_results)

        if "rotation" in search_request.entity_types:
            rotation_results = await self._search_rotations(
                parsed, search_request.filters
            )
            all_results.extend(rotation_results)

        if "procedure" in search_request.entity_types:
            procedure_results = await self._search_procedures(
                parsed, search_request.filters
            )
            all_results.extend(procedure_results)

        if "assignment" in search_request.entity_types:
            assignment_results = await self._search_assignments(
                parsed, search_request.filters
            )
            all_results.extend(assignment_results)

        if "swap" in search_request.entity_types:
            swap_results = await self._search_swaps(parsed, search_request.filters)
            all_results.extend(swap_results)

            # Sort by relevance score
        all_results.sort(key=lambda x: x.score, reverse=True)

        # Apply pagination
        total = len(all_results)
        start_idx = (search_request.page - 1) * search_request.page_size
        end_idx = start_idx + search_request.page_size
        paginated_results = all_results[start_idx:end_idx]

        # Calculate facets
        facets = self._calculate_facets(all_results)

        # Calculate execution time
        execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        # Log analytics
        self.analytics.log_search(
            query=search_request.query,
            entity_types=search_request.entity_types,
            result_count=total,
            execution_time_ms=execution_time,
        )

        return SearchResponse(
            items=paginated_results,
            total=total,
            page=search_request.page,
            page_size=search_request.page_size,
            total_pages=(total + search_request.page_size - 1)
            // search_request.page_size,
            facets=facets,
            query=search_request.query,
        )

    async def _search_persons(
        self,
        parsed_query: dict[str, Any],
        filters: dict[str, Any],
    ) -> list[SearchResultItem]:
        """
        Search persons.

        Args:
            parsed_query: Parsed query tokens
            filters: Additional filters

        Returns:
            List of search result items
        """
        tokens = parsed_query["tokens"]
        phrases = parsed_query["phrases"]

        query = self.db.query(Person)

        # Build search conditions
        conditions = []
        for token in tokens + phrases:
            conditions.append(
                or_(
                    Person.name.ilike(f"%{token}%"),
                    Person.email.ilike(f"%{token}%"),
                    Person.type.ilike(f"%{token}%"),
                )
            )

        if conditions:
            query = query.filter(or_(*conditions))

            # Apply filters
        if filters.get("type"):
            query = query.filter(Person.type == filters["type"])
        if filters.get("pgy_level"):
            query = query.filter(Person.pgy_level == filters["pgy_level"])
        if filters.get("faculty_role"):
            query = query.filter(Person.faculty_role == filters["faculty_role"])

        persons = query.all()

        results = []
        for person in persons:
            # Calculate relevance score
            score = RelevanceScorer.score_match(
                tokens,
                {
                    "name": person.name,
                    "email": person.email or "",
                    "type": person.type,
                },
            )

            # Generate highlights
            highlights = {}
            if tokens:
                highlights["name"] = [TextHighlighter.highlight(person.name, tokens)]
                if person.email:
                    highlights["email"] = [
                        TextHighlighter.highlight(person.email, tokens)
                    ]

                    # Build subtitle
            subtitle_parts = [person.type.title()]
            if person.pgy_level:
                subtitle_parts.append(f"PGY-{person.pgy_level}")
            if person.faculty_role:
                subtitle_parts.append(person.faculty_role.upper())

            results.append(
                SearchResultItem(
                    id=str(person.id),
                    type="person",
                    title=person.name,
                    subtitle=" | ".join(subtitle_parts),
                    score=score,
                    highlights=highlights,
                    entity={
                        "id": str(person.id),
                        "name": person.name,
                        "email": person.email,
                        "type": person.type,
                        "pgy_level": person.pgy_level,
                        "faculty_role": person.faculty_role,
                    },
                )
            )

        return results

    async def _search_rotations(
        self,
        parsed_query: dict[str, Any],
        filters: dict[str, Any],
    ) -> list[SearchResultItem]:
        """
        Search rotation templates.

        Args:
            parsed_query: Parsed query tokens
            filters: Additional filters

        Returns:
            List of search result items
        """
        tokens = parsed_query["tokens"]
        phrases = parsed_query["phrases"]

        query = self.db.query(RotationTemplate)

        # Build search conditions
        conditions = []
        for token in tokens + phrases:
            conditions.append(
                or_(
                    RotationTemplate.name.ilike(f"%{token}%"),
                    RotationTemplate.rotation_type.ilike(f"%{token}%"),
                    RotationTemplate.abbreviation.ilike(f"%{token}%"),
                )
            )

        if conditions:
            query = query.filter(or_(*conditions))

            # Apply filters
        if filters.get("rotation_type"):
            query = query.filter(
                RotationTemplate.rotation_type == filters["rotation_type"]
            )

        rotations = query.all()

        results = []
        for rotation in rotations:
            # Calculate relevance score
            score = RelevanceScorer.score_match(
                tokens,
                {
                    "name": rotation.name,
                    "type": rotation.rotation_type,
                    "abbreviation": rotation.abbreviation or "",
                },
            )

            # Generate highlights
            highlights = {}
            if tokens:
                highlights["name"] = [TextHighlighter.highlight(rotation.name, tokens)]

            results.append(
                SearchResultItem(
                    id=str(rotation.id),
                    type="rotation",
                    title=rotation.name,
                    subtitle=rotation.rotation_type.title(),
                    score=score,
                    highlights=highlights,
                    entity={
                        "id": str(rotation.id),
                        "name": rotation.name,
                        "rotation_type": rotation.rotation_type,
                        "abbreviation": rotation.abbreviation,
                    },
                )
            )

        return results

    async def _search_procedures(
        self,
        parsed_query: dict[str, Any],
        filters: dict[str, Any],
    ) -> list[SearchResultItem]:
        """
        Search procedures.

        Args:
            parsed_query: Parsed query tokens
            filters: Additional filters

        Returns:
            List of search result items
        """
        tokens = parsed_query["tokens"]
        phrases = parsed_query["phrases"]

        query = self.db.query(Procedure)

        # Build search conditions
        conditions = []
        for token in tokens + phrases:
            conditions.append(
                or_(
                    Procedure.name.ilike(f"%{token}%"),
                    Procedure.category.ilike(f"%{token}%"),
                )
            )

        if conditions:
            query = query.filter(or_(*conditions))

            # Apply filters
        if filters.get("category"):
            query = query.filter(Procedure.category == filters["category"])

        procedures = query.all()

        results = []
        for procedure in procedures:
            # Calculate relevance score
            score = RelevanceScorer.score_match(
                tokens,
                {
                    "name": procedure.name,
                    "category": procedure.category or "",
                },
            )

            # Generate highlights
            highlights = {}
            if tokens:
                highlights["name"] = [TextHighlighter.highlight(procedure.name, tokens)]

            results.append(
                SearchResultItem(
                    id=str(procedure.id),
                    type="procedure",
                    title=procedure.name,
                    subtitle=procedure.category or "Procedure",
                    score=score,
                    highlights=highlights,
                    entity={
                        "id": str(procedure.id),
                        "name": procedure.name,
                        "category": procedure.category,
                    },
                )
            )

        return results

    async def _search_assignments(
        self,
        parsed_query: dict[str, Any],
        filters: dict[str, Any],
    ) -> list[SearchResultItem]:
        """
        Search assignments.

        Args:
            parsed_query: Parsed query tokens
            filters: Additional filters

        Returns:
            List of search result items
        """
        tokens = parsed_query["tokens"]

        query = self.db.query(Assignment).options(
            joinedload(Assignment.person),
            joinedload(Assignment.rotation_template),
        )

        # Search by person name or rotation
        conditions = []
        for token in tokens:
            conditions.append(
                or_(
                    Assignment.role.ilike(f"%{token}%"),
                    Assignment.activity_override.ilike(f"%{token}%"),
                )
            )

        if conditions:
            query = query.filter(or_(*conditions))

            # Apply filters
        if filters.get("role"):
            query = query.filter(Assignment.role == filters["role"])

        assignments = query.limit(100).all()

        results = []
        for assignment in assignments:
            person_name = assignment.person.name if assignment.person else "Unknown"
            activity_name = assignment.activity_name

            # Calculate relevance score
            score = RelevanceScorer.score_match(
                tokens,
                {
                    "person": person_name,
                    "activity": activity_name,
                    "role": assignment.role,
                },
            )

            results.append(
                SearchResultItem(
                    id=str(assignment.id),
                    type="assignment",
                    title=f"{person_name} - {activity_name}",
                    subtitle=assignment.role.title(),
                    score=score,
                    highlights={},
                    entity={
                        "id": str(assignment.id),
                        "person_id": str(assignment.person_id),
                        "person_name": person_name,
                        "activity": activity_name,
                        "role": assignment.role,
                    },
                )
            )

        return results

    async def _search_swaps(
        self,
        parsed_query: dict[str, Any],
        filters: dict[str, Any],
    ) -> list[SearchResultItem]:
        """
        Search swap records.

        Args:
            parsed_query: Parsed query tokens
            filters: Additional filters

        Returns:
            List of search result items
        """
        tokens = parsed_query["tokens"]

        query = self.db.query(SwapRecord)

        # Build search conditions
        conditions = []
        for token in tokens:
            conditions.append(
                or_(
                    SwapRecord.status.ilike(f"%{token}%"),
                    SwapRecord.swap_type.ilike(f"%{token}%"),
                )
            )

        if conditions:
            query = query.filter(or_(*conditions))

            # Apply filters
        if filters.get("status"):
            query = query.filter(SwapRecord.status == filters["status"])

        swaps = query.limit(100).all()

        results = []
        for swap in swaps:
            # Calculate relevance score
            score = RelevanceScorer.score_match(
                tokens,
                {
                    "status": swap.status,
                    "type": swap.swap_type or "",
                },
            )

            results.append(
                SearchResultItem(
                    id=str(swap.id),
                    type="swap",
                    title=f"Swap Request - {swap.status.title()}",
                    subtitle=swap.swap_type or "Swap",
                    score=score,
                    highlights={},
                    entity={
                        "id": str(swap.id),
                        "status": swap.status,
                        "swap_type": swap.swap_type,
                    },
                )
            )

        return results

    def _calculate_facets(
        self,
        results: list[SearchResultItem],
    ) -> dict[str, dict[str, int]]:
        """
        Calculate facet counts for filtering.

        Args:
            results: Search results

        Returns:
            Dictionary of facet_name -> {value -> count}
        """
        facets = {
            "type": defaultdict(int),
            "person_type": defaultdict(int),
            "pgy_level": defaultdict(int),
            "faculty_role": defaultdict(int),
            "status": defaultdict(int),
        }

        for result in results:
            # Entity type facet
            facets["type"][result.type] += 1

            # Entity-specific facets
            if result.entity:
                entity = result.entity

                if entity.get("type"):
                    facets["person_type"][entity["type"]] += 1

                if entity.get("pgy_level"):
                    facets["pgy_level"][f"PGY-{entity['pgy_level']}"] += 1

                if entity.get("faculty_role"):
                    facets["faculty_role"][entity["faculty_role"]] += 1

                if entity.get("status"):
                    facets["status"][entity["status"]] += 1

                    # Convert defaultdict to regular dict
        return {
            key: dict(value_dict) for key, value_dict in facets.items() if value_dict
        }

    def suggest_spelling(self, query: str) -> dict[str, Any]:
        """
        Suggest spelling corrections for a query.

        Args:
            query: Search query string

        Returns:
            Dictionary with correction suggestions
        """
        return self.spell_corrector.correct_query(query)

    def get_analytics(self) -> dict[str, Any]:
        """
        Get search analytics.

        Returns:
            Analytics statistics
        """
        return self.analytics.get_stats()


def get_search_service(db: Session) -> FullTextSearchService:
    """
    Get full-text search service instance.

    Args:
        db: Database session

    Returns:
        Configured search service
    """
    return FullTextSearchService(db)
