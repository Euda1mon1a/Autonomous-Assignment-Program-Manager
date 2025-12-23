"""Search backend implementations.

Provides abstraction layer for different search engines, with
PostgreSQL full-text search as the primary backend.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import String, and_, case, cast, func, or_, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy.sql import select

from app.models.assignment import Assignment
from app.models.person import Person
from app.models.procedure import Procedure
from app.models.rotation_template import RotationTemplate
from app.models.swap import SwapRecord
from app.services.search.analyzers import SearchAnalyzer, StandardAnalyzer


class SearchBackend(ABC):
    """Abstract base class for search backends."""

    @abstractmethod
    async def search(
        self,
        query: str,
        entity_types: list[str],
        filters: dict[str, Any] | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        Execute search query.

        Args:
            query: Search query string
            entity_types: List of entity types to search (person, assignment, etc.)
            filters: Additional filters (facets)
            limit: Maximum results to return
            offset: Pagination offset

        Returns:
            Dictionary containing results, total count, and facets
        """
        pass

    @abstractmethod
    async def suggest(
        self,
        query: str,
        entity_type: str,
        limit: int = 10,
    ) -> list[str]:
        """
        Get search suggestions/autocomplete.

        Args:
            query: Partial search query
            entity_type: Entity type for suggestions
            limit: Maximum suggestions to return

        Returns:
            List of suggestion strings
        """
        pass


class PostgreSQLSearchBackend(SearchBackend):
    """
    PostgreSQL-based search backend using full-text search.

    Uses PostgreSQL's tsvector and tsquery for efficient full-text search
    with ranking, highlighting, and fuzzy matching support.
    """

    def __init__(
        self,
        db: Session,
        analyzer: SearchAnalyzer | None = None,
    ):
        """
        Initialize PostgreSQL search backend.

        Args:
            db: Database session
            analyzer: Text analyzer (defaults to StandardAnalyzer)
        """
        self.db = db
        self.analyzer = analyzer or StandardAnalyzer()

    async def search(
        self,
        query: str,
        entity_types: list[str],
        filters: dict[str, Any] | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        Execute search across specified entity types.

        Args:
            query: Search query string
            entity_types: List of entity types to search
            filters: Optional filters (type, pgy_level, etc.)
            limit: Maximum results per entity type
            offset: Pagination offset

        Returns:
            Dictionary with results, total, and facets
        """
        filters = filters or {}
        results = []
        total = 0
        facets = {}

        # Process query with analyzer
        tokens = self.analyzer.analyze(query)
        search_query = " & ".join(tokens) if tokens else query

        # Search each entity type
        for entity_type in entity_types:
            if entity_type == "person":
                entity_results = await self._search_people(
                    search_query, filters, limit, offset
                )
            elif entity_type == "rotation":
                entity_results = await self._search_rotations(
                    search_query, filters, limit, offset
                )
            elif entity_type == "procedure":
                entity_results = await self._search_procedures(
                    search_query, filters, limit, offset
                )
            elif entity_type == "swap":
                entity_results = await self._search_swaps(
                    search_query, filters, limit, offset
                )
            else:
                continue

            results.extend(entity_results["items"])
            total += entity_results["total"]

            # Merge facets
            if "facets" in entity_results:
                for key, value in entity_results["facets"].items():
                    if key not in facets:
                        facets[key] = {}
                    for k, v in value.items():
                        facets[key][k] = facets[key].get(k, 0) + v

        # Sort by relevance score (if available)
        results.sort(key=lambda x: x.get("score", 0), reverse=True)

        return {
            "items": results[:limit],
            "total": total,
            "facets": facets,
            "query": query,
        }

    async def _search_people(
        self,
        query: str,
        filters: dict[str, Any],
        limit: int,
        offset: int,
    ) -> dict[str, Any]:
        """
        Search people (residents and faculty).

        Args:
            query: Processed search query
            filters: Filter criteria
            limit: Result limit
            offset: Result offset

        Returns:
            Search results for people
        """
        # Build base query
        stmt = select(Person)

        # Apply filters
        conditions = []

        if "type" in filters:
            conditions.append(Person.type == filters["type"])

        if "pgy_level" in filters:
            conditions.append(Person.pgy_level == filters["pgy_level"])

        if "faculty_role" in filters:
            conditions.append(Person.faculty_role == filters["faculty_role"])

        # Full-text search on name and email
        if query:
            # Use PostgreSQL ILIKE for simple pattern matching
            # In production, consider using tsvector for better performance
            search_condition = or_(
                Person.name.ilike(f"%{query}%"),
                Person.email.ilike(f"%{query}%"),
            )
            conditions.append(search_condition)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Apply ordering (by relevance)
        # Prioritize exact name matches
        if query:
            stmt = stmt.order_by(
                case(
                    (Person.name.ilike(f"{query}%"), 1),  # Starts with query
                    (Person.name.ilike(f"%{query}%"), 2),  # Contains query
                    else_=3,
                ),
                Person.name,
            )
        else:
            stmt = stmt.order_by(Person.name)

        # Apply pagination
        stmt = stmt.limit(limit).offset(offset)

        # Execute query
        result = await self.db.execute(stmt)
        people = result.scalars().all()

        # Calculate facets
        facets = await self._calculate_people_facets(conditions)

        # Format results
        items = [
            {
                "id": str(person.id),
                "type": "person",
                "entity": person,
                "title": person.name,
                "subtitle": f"{person.type.title()} - {person.email or 'No email'}",
                "score": self._calculate_relevance_score(person.name, query),
                "highlights": self._highlight_text(person.name, query),
            }
            for person in people
        ]

        return {
            "items": items,
            "total": total,
            "facets": facets,
        }

    async def _search_rotations(
        self,
        query: str,
        filters: dict[str, Any],
        limit: int,
        offset: int,
    ) -> dict[str, Any]:
        """Search rotation templates."""
        stmt = select(RotationTemplate)

        conditions = []

        if query:
            search_condition = or_(
                RotationTemplate.name.ilike(f"%{query}%"),
                RotationTemplate.abbreviation.ilike(f"%{query}%"),
            )
            conditions.append(search_condition)

        if "category" in filters:
            conditions.append(RotationTemplate.category == filters["category"])

        if conditions:
            stmt = stmt.where(and_(*conditions))

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Apply ordering
        if query:
            stmt = stmt.order_by(
                case(
                    (RotationTemplate.name.ilike(f"{query}%"), 1),
                    (RotationTemplate.name.ilike(f"%{query}%"), 2),
                    else_=3,
                ),
                RotationTemplate.name,
            )
        else:
            stmt = stmt.order_by(RotationTemplate.name)

        stmt = stmt.limit(limit).offset(offset)

        result = await self.db.execute(stmt)
        rotations = result.scalars().all()

        items = [
            {
                "id": str(rotation.id),
                "type": "rotation",
                "entity": rotation,
                "title": rotation.name,
                "subtitle": f"Category: {rotation.category or 'N/A'}",
                "score": self._calculate_relevance_score(rotation.name, query),
                "highlights": self._highlight_text(rotation.name, query),
            }
            for rotation in rotations
        ]

        return {
            "items": items,
            "total": total,
            "facets": {},
        }

    async def _search_procedures(
        self,
        query: str,
        filters: dict[str, Any],
        limit: int,
        offset: int,
    ) -> dict[str, Any]:
        """Search procedures."""
        stmt = select(Procedure)

        conditions = []

        if query:
            search_condition = or_(
                Procedure.name.ilike(f"%{query}%"),
                cast(Procedure.cpt_codes, String).ilike(f"%{query}%"),
            )
            conditions.append(search_condition)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Apply ordering
        stmt = stmt.order_by(Procedure.name)
        stmt = stmt.limit(limit).offset(offset)

        result = await self.db.execute(stmt)
        procedures = result.scalars().all()

        items = [
            {
                "id": str(procedure.id),
                "type": "procedure",
                "entity": procedure,
                "title": procedure.name,
                "subtitle": f"CPT: {', '.join(procedure.cpt_codes or [])}",
                "score": self._calculate_relevance_score(procedure.name, query),
                "highlights": self._highlight_text(procedure.name, query),
            }
            for procedure in procedures
        ]

        return {
            "items": items,
            "total": total,
            "facets": {},
        }

    async def _search_swaps(
        self,
        query: str,
        filters: dict[str, Any],
        limit: int,
        offset: int,
    ) -> dict[str, Any]:
        """Search swap records."""
        stmt = select(SwapRecord)

        conditions = []

        if "status" in filters:
            conditions.append(SwapRecord.status == filters["status"])

        if "swap_type" in filters:
            conditions.append(SwapRecord.swap_type == filters["swap_type"])

        if conditions:
            stmt = stmt.where(and_(*conditions))

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Apply ordering (most recent first)
        stmt = stmt.order_by(SwapRecord.requested_at.desc())
        stmt = stmt.limit(limit).offset(offset)

        result = await self.db.execute(stmt)
        swaps = result.scalars().all()

        items = [
            {
                "id": str(swap.id),
                "type": "swap",
                "entity": swap,
                "title": f"Swap Request - {swap.swap_type}",
                "subtitle": f"Status: {swap.status}",
                "score": 1.0,
                "highlights": {},
            }
            for swap in swaps
        ]

        return {
            "items": items,
            "total": total,
            "facets": {},
        }

    async def _calculate_people_facets(
        self,
        conditions: list,
    ) -> dict[str, dict[str, int]]:
        """
        Calculate facet counts for people search.

        Args:
            conditions: Existing search conditions

        Returns:
            Dictionary of facet counts
        """
        facets = {}

        # Type facets (resident vs faculty)
        type_stmt = select(Person.type, func.count(Person.id).label("count")).group_by(
            Person.type
        )

        if conditions:
            type_stmt = type_stmt.where(and_(*conditions))

        type_result = await self.db.execute(type_stmt)
        facets["type"] = {row[0]: row[1] for row in type_result.all()}

        # PGY level facets (for residents)
        pgy_stmt = (
            select(Person.pgy_level, func.count(Person.id).label("count"))
            .where(Person.pgy_level.isnot(None))
            .group_by(Person.pgy_level)
        )

        if conditions:
            pgy_stmt = pgy_stmt.where(and_(*conditions))

        pgy_result = await self.db.execute(pgy_stmt)
        facets["pgy_level"] = {
            f"PGY-{row[0]}": row[1] for row in pgy_result.all() if row[0]
        }

        return facets

    async def suggest(
        self,
        query: str,
        entity_type: str,
        limit: int = 10,
    ) -> list[str]:
        """
        Get autocomplete suggestions.

        Args:
            query: Partial search query
            entity_type: Entity type for suggestions
            limit: Maximum suggestions

        Returns:
            List of suggestion strings
        """
        suggestions = []

        if entity_type == "person":
            # Get person name suggestions
            stmt = (
                select(Person.name)
                .where(Person.name.ilike(f"{query}%"))
                .order_by(Person.name)
                .limit(limit)
            )

            result = await self.db.execute(stmt)
            suggestions = [row[0] for row in result.all()]

        elif entity_type == "rotation":
            # Get rotation name suggestions
            stmt = (
                select(RotationTemplate.name)
                .where(RotationTemplate.name.ilike(f"{query}%"))
                .order_by(RotationTemplate.name)
                .limit(limit)
            )

            result = await self.db.execute(stmt)
            suggestions = [row[0] for row in result.all()]

        return suggestions

    def _calculate_relevance_score(self, text: str, query: str) -> float:
        """
        Calculate relevance score for text vs query.

        Args:
            text: Text to score
            query: Search query

        Returns:
            Relevance score (0.0 to 1.0)
        """
        if not query or not text:
            return 0.0

        text_lower = text.lower()
        query_lower = query.lower()

        # Exact match
        if text_lower == query_lower:
            return 1.0

        # Starts with query
        if text_lower.startswith(query_lower):
            return 0.9

        # Contains query
        if query_lower in text_lower:
            return 0.7

        # Fuzzy match (simple word overlap)
        text_words = set(text_lower.split())
        query_words = set(query_lower.split())
        overlap = len(text_words & query_words)
        if overlap > 0:
            return 0.5 * (overlap / len(query_words))

        return 0.1

    def _highlight_text(self, text: str, query: str) -> dict[str, list[str]]:
        """
        Generate highlighted fragments of text matching query.

        Args:
            text: Text to highlight
            query: Search query

        Returns:
            Dictionary with highlighted fragments
        """
        if not query or not text:
            return {}

        # Find query position in text (case-insensitive)
        text_lower = text.lower()
        query_lower = query.lower()

        highlights = []
        start = 0

        while True:
            pos = text_lower.find(query_lower, start)
            if pos == -1:
                break

            # Extract fragment with context (20 chars before/after)
            fragment_start = max(0, pos - 20)
            fragment_end = min(len(text), pos + len(query) + 20)
            fragment = text[fragment_start:fragment_end]

            # Add ellipsis if truncated
            if fragment_start > 0:
                fragment = "..." + fragment
            if fragment_end < len(text):
                fragment = fragment + "..."

            highlights.append(fragment)
            start = pos + len(query)

            # Limit to 3 highlights
            if len(highlights) >= 3:
                break

        return {"highlights": highlights} if highlights else {}
