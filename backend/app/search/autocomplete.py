"""
Autocomplete service for search functionality.

Provides intelligent autocomplete suggestions with:
- Prefix-based completion
- Context-aware suggestions
- Personalized suggestions based on user history
- Popular queries tracking
- Redis-backed caching
- Multi-field completion (persons, rotations, procedures)
- Typo-tolerant completion using Levenshtein distance
- Completion analytics and metrics

Example:
    from app.search.autocomplete import AutocompleteService, get_autocomplete_service

    autocomplete = get_autocomplete_service()
    suggestions = await autocomplete.get_suggestions(
        query="john",
        user_id="user-123",
        context="person",
        limit=10
    )
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import redis
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import CacheTTL, get_service_cache
from app.core.config import get_settings
from app.models.person import Person
from app.models.procedure import Procedure
from app.models.rotation_template import RotationTemplate

logger = logging.getLogger(__name__)


class AutocompleteContext(str, Enum):
    """Context types for autocomplete suggestions."""

    PERSON = "person"
    ROTATION = "rotation"
    PROCEDURE = "procedure"
    GLOBAL = "global"


class SuggestionSource(str, Enum):
    """Source of autocomplete suggestion."""

    DATABASE = "database"
    POPULAR = "popular"
    PERSONALIZED = "personalized"
    CACHED = "cached"
    TYPO_CORRECTED = "typo_corrected"


@dataclass
class AutocompleteSuggestion:
    """
    Represents a single autocomplete suggestion.

    Attributes:
        text: The suggestion text
        context: Context type (person, rotation, etc.)
        source: Source of the suggestion
        score: Relevance score (0-1)
        metadata: Additional metadata (id, type, etc.)
        matched_field: Which field matched (name, email, etc.)
    """

    text: str
    context: AutocompleteContext
    source: SuggestionSource
    score: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)
    matched_field: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert suggestion to dictionary."""
        return {
            "text": self.text,
            "context": self.context.value,
            "source": self.source.value,
            "score": round(self.score, 3),
            "metadata": self.metadata,
            "matched_field": self.matched_field,
        }


@dataclass
class AutocompleteAnalytics:
    """Analytics data for autocomplete performance."""

    query: str
    user_id: str | None
    context: AutocompleteContext
    suggestions_count: int
    cache_hit: bool
    response_time_ms: float
    sources_used: list[str]
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert analytics to dictionary."""
        return {
            "query": self.query,
            "user_id": self.user_id,
            "context": self.context.value,
            "suggestions_count": self.suggestions_count,
            "cache_hit": self.cache_hit,
            "response_time_ms": round(self.response_time_ms, 2),
            "sources_used": self.sources_used,
            "timestamp": self.timestamp.isoformat(),
        }


class AutocompleteService:
    """
    Service for intelligent autocomplete suggestions.

    Provides fast, context-aware autocomplete with personalization,
    popular queries tracking, and typo tolerance.

    Features:
    - Prefix-based matching with multiple fields
    - Context-aware filtering (person, rotation, procedure)
    - Personalized suggestions based on user history
    - Popular queries tracking with decay
    - Redis caching for performance
    - Typo-tolerant matching using edit distance
    - Analytics tracking

    Example:
        service = AutocompleteService(db)
        suggestions = await service.get_suggestions(
            query="john",
            user_id="user-123",
            context=AutocompleteContext.PERSON,
            limit=10
        )
    """

    # Redis key prefixes
    POPULAR_QUERIES_KEY = "autocomplete:popular"
    USER_HISTORY_KEY_PREFIX = "autocomplete:user_history"
    SUGGESTION_CACHE_PREFIX = "autocomplete:cache"
    ANALYTICS_KEY_PREFIX = "autocomplete:analytics"

    # Scoring weights
    SCORE_EXACT_MATCH = 1.0
    SCORE_PREFIX_MATCH = 0.9
    SCORE_WORD_START = 0.8
    SCORE_SUBSTRING = 0.6
    SCORE_TYPO_CORRECTED = 0.5
    SCORE_POPULAR_BOOST = 0.2
    SCORE_PERSONALIZED_BOOST = 0.3

    # Cache TTLs
    CACHE_TTL_SHORT = CacheTTL.SHORT  # 1 minute
    CACHE_TTL_MEDIUM = CacheTTL.MEDIUM  # 5 minutes
    POPULAR_QUERIES_TTL = 86400  # 24 hours
    USER_HISTORY_TTL = 604800  # 7 days

    # Query tracking
    MAX_USER_HISTORY = 100
    MAX_POPULAR_QUERIES = 1000
    MIN_QUERY_LENGTH = 2
    MAX_QUERY_LENGTH = 100

    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize autocomplete service.

        Args:
            db: Async database session
        """
        self.db = db
        self.cache = get_service_cache()
        self.settings = get_settings()
        self._redis: redis.Redis | None = None

    def _get_redis(self) -> redis.Redis:
        """
        Get or create Redis connection.

        Returns:
            Redis client instance
        """
        if self._redis is None:
            redis_url = self.settings.redis_url_with_password
            self._redis = redis.from_url(redis_url, decode_responses=True)
        return self._redis

    async def get_suggestions(
        self,
        query: str,
        user_id: str | None = None,
        context: AutocompleteContext = AutocompleteContext.GLOBAL,
        limit: int = 10,
        include_typo_tolerance: bool = True,
    ) -> list[AutocompleteSuggestion]:
        """
        Get autocomplete suggestions for a query.

        Args:
            query: Search query prefix
            user_id: Optional user ID for personalization
            context: Context for suggestions (person, rotation, etc.)
            limit: Maximum number of suggestions
            include_typo_tolerance: Whether to include typo-tolerant matches

        Returns:
            List of autocomplete suggestions, sorted by relevance

        Example:
            suggestions = await service.get_suggestions(
                query="joh",
                user_id="user-123",
                context=AutocompleteContext.PERSON,
                limit=10
            )
        """
        start_time = datetime.utcnow()
        sources_used: list[str] = []

        # Validate and normalize query
        query = self._normalize_query(query)
        if not query or len(query) < self.MIN_QUERY_LENGTH:
            return []

            # Check cache first
        cache_key = self._build_cache_key(query, context, user_id)
        cached = self.cache.get(cache_key)
        if cached:
            logger.debug(f"Cache hit for autocomplete query: {query}")
            suggestions = [AutocompleteSuggestion(**s) for s in cached]
            sources_used.append("cache")
            cache_hit = True
        else:
            cache_hit = False
            suggestions = []

            # Get suggestions from different sources
            db_suggestions = await self._get_database_suggestions(query, context, limit)
            suggestions.extend(db_suggestions)
            if db_suggestions:
                sources_used.append("database")

                # Add popular queries
            popular_suggestions = await self._get_popular_suggestions(
                query, context, limit
            )
            suggestions.extend(popular_suggestions)
            if popular_suggestions:
                sources_used.append("popular")

                # Add personalized suggestions
            if user_id:
                personalized = await self._get_personalized_suggestions(
                    query, user_id, context, limit
                )
                suggestions.extend(personalized)
                if personalized:
                    sources_used.append("personalized")

                    # Add typo-tolerant suggestions if enabled
            if include_typo_tolerance and len(suggestions) < limit:
                typo_suggestions = await self._get_typo_tolerant_suggestions(
                    query, context, limit - len(suggestions)
                )
                suggestions.extend(typo_suggestions)
                if typo_suggestions:
                    sources_used.append("typo_corrected")

                    # Sort by score and deduplicate
            suggestions = self._rank_and_deduplicate(suggestions, limit)

            # Cache the results
            self.cache.set(
                cache_key,
                [s.to_dict() for s in suggestions],
                ttl=self.CACHE_TTL_MEDIUM,
            )

            # Track query if it has results
        if suggestions and user_id:
            await self._track_query(query, user_id, context)

            # Record analytics
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        await self._record_analytics(
            query=query,
            user_id=user_id,
            context=context,
            suggestions_count=len(suggestions),
            cache_hit=cache_hit,
            response_time_ms=response_time,
            sources_used=sources_used,
        )

        return suggestions

    async def _get_database_suggestions(
        self,
        query: str,
        context: AutocompleteContext,
        limit: int,
    ) -> list[AutocompleteSuggestion]:
        """
        Get suggestions from database based on context.

        Args:
            query: Search query
            context: Context type
            limit: Maximum suggestions

        Returns:
            List of database-backed suggestions
        """
        suggestions = []

        if context in (AutocompleteContext.PERSON, AutocompleteContext.GLOBAL):
            person_suggestions = await self._search_persons(query, limit)
            suggestions.extend(person_suggestions)

        if context in (AutocompleteContext.ROTATION, AutocompleteContext.GLOBAL):
            rotation_suggestions = await self._search_rotations(query, limit)
            suggestions.extend(rotation_suggestions)

        if context in (AutocompleteContext.PROCEDURE, AutocompleteContext.GLOBAL):
            procedure_suggestions = await self._search_procedures(query, limit)
            suggestions.extend(procedure_suggestions)

        return suggestions

    async def _search_persons(
        self, query: str, limit: int
    ) -> list[AutocompleteSuggestion]:
        """
        Search for persons matching query.

        Searches across name and email fields with different scoring.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of person suggestions
        """
        query_lower = query.lower()
        query_pattern = f"%{query_lower}%"

        stmt = (
            select(Person)
            .where(
                or_(
                    func.lower(Person.name).like(query_pattern),
                    func.lower(Person.email).like(query_pattern),
                )
            )
            .limit(limit * 2)  # Get more to allow for scoring
        )

        result = await self.db.execute(stmt)
        persons = result.scalars().all()

        suggestions = []
        for person in persons:
            # Calculate score based on match type
            score = self._calculate_match_score(query_lower, person.name.lower())
            matched_field = "name"

            # Check email match
            if person.email:
                email_score = self._calculate_match_score(
                    query_lower, person.email.lower()
                )
                if email_score > score:
                    score = email_score
                    matched_field = "email"

            suggestion = AutocompleteSuggestion(
                text=person.name,
                context=AutocompleteContext.PERSON,
                source=SuggestionSource.DATABASE,
                score=score,
                metadata={
                    "id": str(person.id),
                    "type": person.type,
                    "email": person.email,
                    "pgy_level": (
                        person.pgy_level if person.type == "resident" else None
                    ),
                },
                matched_field=matched_field,
            )
            suggestions.append(suggestion)

        return suggestions

    async def _search_rotations(
        self, query: str, limit: int
    ) -> list[AutocompleteSuggestion]:
        """
        Search for rotations matching query.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of rotation suggestions
        """
        query_lower = query.lower()
        query_pattern = f"%{query_lower}%"

        stmt = (
            select(RotationTemplate)
            .where(
                or_(
                    func.lower(RotationTemplate.name).like(query_pattern),
                    func.lower(RotationTemplate.description).like(query_pattern),
                )
            )
            .limit(limit * 2)
        )

        result = await self.db.execute(stmt)
        rotations = result.scalars().all()

        suggestions = []
        for rotation in rotations:
            score = self._calculate_match_score(query_lower, rotation.name.lower())
            matched_field = "name"

            # Check description match
            if rotation.description:
                desc_score = self._calculate_match_score(
                    query_lower, rotation.description.lower()
                )
                if desc_score > score:
                    score = desc_score
                    matched_field = "description"

            suggestion = AutocompleteSuggestion(
                text=rotation.name,
                context=AutocompleteContext.ROTATION,
                source=SuggestionSource.DATABASE,
                score=score,
                metadata={
                    "id": str(rotation.id),
                    "category": rotation.category,
                    "description": rotation.description,
                },
                matched_field=matched_field,
            )
            suggestions.append(suggestion)

        return suggestions

    async def _search_procedures(
        self, query: str, limit: int
    ) -> list[AutocompleteSuggestion]:
        """
        Search for procedures matching query.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of procedure suggestions
        """
        query_lower = query.lower()
        query_pattern = f"%{query_lower}%"

        stmt = (
            select(Procedure)
            .where(
                or_(
                    func.lower(Procedure.name).like(query_pattern),
                    func.lower(Procedure.code).like(query_pattern),
                )
            )
            .limit(limit * 2)
        )

        result = await self.db.execute(stmt)
        procedures = result.scalars().all()

        suggestions = []
        for procedure in procedures:
            score = self._calculate_match_score(query_lower, procedure.name.lower())
            matched_field = "name"

            # Check code match
            if procedure.code:
                code_score = self._calculate_match_score(
                    query_lower, procedure.code.lower()
                )
                if code_score > score:
                    score = code_score
                    matched_field = "code"

            suggestion = AutocompleteSuggestion(
                text=procedure.name,
                context=AutocompleteContext.PROCEDURE,
                source=SuggestionSource.DATABASE,
                score=score,
                metadata={
                    "id": str(procedure.id),
                    "code": procedure.code,
                    "category": procedure.category,
                },
                matched_field=matched_field,
            )
            suggestions.append(suggestion)

        return suggestions

    def _calculate_match_score(self, query: str, text: str) -> float:
        """
        Calculate relevance score for a match.

        Scoring criteria:
        - Exact match: 1.0
        - Prefix match: 0.9
        - Word start match: 0.8
        - Substring match: 0.6

        Args:
            query: Search query (lowercase)
            text: Text to match against (lowercase)

        Returns:
            Score between 0 and 1
        """
        if not text:
            return 0.0

            # Exact match
        if query == text:
            return self.SCORE_EXACT_MATCH

            # Prefix match
        if text.startswith(query):
            return self.SCORE_PREFIX_MATCH

            # Word start match
        words = text.split()
        for word in words:
            if word.startswith(query):
                return self.SCORE_WORD_START

                # Substring match
        if query in text:
            # Boost score if match is closer to start
            position = text.index(query)
            position_penalty = position / len(text)
            return self.SCORE_SUBSTRING * (1 - position_penalty * 0.5)

        return 0.0

    async def _get_popular_suggestions(
        self,
        query: str,
        context: AutocompleteContext,
        limit: int,
    ) -> list[AutocompleteSuggestion]:
        """
        Get popular query suggestions.

        Uses Redis sorted set to track query popularity with time decay.

        Args:
            query: Search query prefix
            context: Context type
            limit: Maximum suggestions

        Returns:
            List of popular query suggestions
        """
        try:
            redis_client = self._get_redis()
            key = f"{self.POPULAR_QUERIES_KEY}:{context.value}"

            # Get top queries matching prefix
            all_queries = redis_client.zrevrange(key, 0, -1, withscores=True)

            matching_queries = []
            for q, score in all_queries:
                if q.lower().startswith(query.lower()):
                    matching_queries.append((q, score))

                    # Sort by score and take top N
            matching_queries.sort(key=lambda x: x[1], reverse=True)
            matching_queries = matching_queries[:limit]

            suggestions = []
            for q, popularity_score in matching_queries:
                # Normalize popularity score to 0-1 range
                normalized_score = min(1.0, popularity_score / 100)
                boost = normalized_score * self.SCORE_POPULAR_BOOST

                suggestion = AutocompleteSuggestion(
                    text=q,
                    context=context,
                    source=SuggestionSource.POPULAR,
                    score=self.SCORE_PREFIX_MATCH + boost,
                    metadata={"popularity": popularity_score},
                )
                suggestions.append(suggestion)

            return suggestions

        except redis.ConnectionError as e:
            logger.warning(
                f"Redis error getting popular suggestions: {e}", exc_info=True
            )
            return []
        except (ValueError, TypeError) as e:
            logger.error(
                f"Data validation error getting popular suggestions: {e}", exc_info=True
            )
            return []
        except redis.RedisError as e:
            logger.error(f"Redis error getting popular suggestions: {e}", exc_info=True)
            return []

    async def _get_personalized_suggestions(
        self,
        query: str,
        user_id: str,
        context: AutocompleteContext,
        limit: int,
    ) -> list[AutocompleteSuggestion]:
        """
        Get personalized suggestions based on user history.

        Args:
            query: Search query prefix
            user_id: User ID
            context: Context type
            limit: Maximum suggestions

        Returns:
            List of personalized suggestions
        """
        try:
            redis_client = self._get_redis()
            key = f"{self.USER_HISTORY_KEY_PREFIX}:{user_id}:{context.value}"

            # Get user's recent queries
            history = redis_client.lrange(key, 0, self.MAX_USER_HISTORY)

            # Find matching queries
            matching = []
            for q in history:
                if q.lower().startswith(query.lower()):
                    matching.append(q)

                    # Deduplicate while preserving order (most recent first)
            seen = set()
            unique_matching = []
            for q in matching:
                if q not in seen:
                    seen.add(q)
                    unique_matching.append(q)

            suggestions = []
            for q in unique_matching[:limit]:
                suggestion = AutocompleteSuggestion(
                    text=q,
                    context=context,
                    source=SuggestionSource.PERSONALIZED,
                    score=self.SCORE_PREFIX_MATCH + self.SCORE_PERSONALIZED_BOOST,
                    metadata={"personalized": True},
                )
                suggestions.append(suggestion)

            return suggestions

        except redis.ConnectionError as e:
            logger.warning(
                f"Redis error getting personalized suggestions: {e}", exc_info=True
            )
            return []
        except (ValueError, TypeError) as e:
            logger.error(
                f"Data validation error getting personalized suggestions: {e}",
                exc_info=True,
            )
            return []
        except redis.RedisError as e:
            logger.error(
                f"Redis error getting personalized suggestions: {e}", exc_info=True
            )
            return []

    async def _get_typo_tolerant_suggestions(
        self,
        query: str,
        context: AutocompleteContext,
        limit: int,
    ) -> list[AutocompleteSuggestion]:
        """
        Get suggestions with typo tolerance using Levenshtein distance.

        Finds similar queries that may have typos (1-2 character difference).

        Args:
            query: Search query
            context: Context type
            limit: Maximum suggestions

        Returns:
            List of typo-corrected suggestions
        """
        if len(query) < 3:
            # Too short for reliable typo correction
            return []

        try:
            redis_client = self._get_redis()
            popular_key = f"{self.POPULAR_QUERIES_KEY}:{context.value}"

            # Get popular queries to check against
            popular_queries = redis_client.zrevrange(popular_key, 0, 200)

            suggestions = []
            for candidate in popular_queries:
                # Calculate edit distance
                distance = self._levenshtein_distance(query.lower(), candidate.lower())

                # Allow 1 edit for queries < 6 chars, 2 edits for longer
                max_distance = 1 if len(query) < 6 else 2

                if 0 < distance <= max_distance:
                    # Calculate score based on edit distance
                    score = self.SCORE_TYPO_CORRECTED * (
                        1 - distance / max_distance / 2
                    )

                    suggestion = AutocompleteSuggestion(
                        text=candidate,
                        context=context,
                        source=SuggestionSource.TYPO_CORRECTED,
                        score=score,
                        metadata={
                            "original_query": query,
                            "edit_distance": distance,
                        },
                    )
                    suggestions.append(suggestion)

                    # Sort by score and limit
            suggestions.sort(key=lambda s: s.score, reverse=True)
            return suggestions[:limit]

        except redis.ConnectionError as e:
            logger.warning(f"Redis error getting typo suggestions: {e}", exc_info=True)
            return []
        except (ValueError, TypeError) as e:
            logger.error(
                f"Data validation error getting typo suggestions: {e}", exc_info=True
            )
            return []
        except redis.RedisError as e:
            logger.error(f"Redis error getting typo suggestions: {e}", exc_info=True)
            return []

    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """
        Calculate Levenshtein (edit) distance between two strings.

        Args:
            s1: First string
            s2: Second string

        Returns:
            Minimum number of single-character edits needed
        """
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                # Cost of insertions, deletions, or substitutions
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    def _rank_and_deduplicate(
        self,
        suggestions: list[AutocompleteSuggestion],
        limit: int,
    ) -> list[AutocompleteSuggestion]:
        """
        Rank suggestions by score and remove duplicates.

        Args:
            suggestions: List of suggestions
            limit: Maximum results

        Returns:
            Ranked and deduplicated suggestions
        """
        # Deduplicate by text while keeping highest score
        seen: dict[str, AutocompleteSuggestion] = {}
        for suggestion in suggestions:
            key = suggestion.text.lower()
            if key not in seen or suggestion.score > seen[key].score:
                seen[key] = suggestion

                # Sort by score
        unique_suggestions = list(seen.values())
        unique_suggestions.sort(key=lambda s: s.score, reverse=True)

        return unique_suggestions[:limit]

    async def _track_query(
        self,
        query: str,
        user_id: str,
        context: AutocompleteContext,
    ) -> None:
        """
        Track query for popularity and personalization.

        Args:
            query: Search query
            user_id: User ID
            context: Context type
        """
        try:
            redis_client = self._get_redis()

            # Track popular queries (global)
            popular_key = f"{self.POPULAR_QUERIES_KEY}:{context.value}"
            redis_client.zincrby(popular_key, 1, query)
            redis_client.expire(popular_key, self.POPULAR_QUERIES_TTL)

            # Trim to max size
            redis_client.zremrangebyrank(
                popular_key, 0, -(self.MAX_POPULAR_QUERIES + 1)
            )

            # Track user history (personalized)
            history_key = f"{self.USER_HISTORY_KEY_PREFIX}:{user_id}:{context.value}"
            redis_client.lpush(history_key, query)
            redis_client.ltrim(history_key, 0, self.MAX_USER_HISTORY - 1)
            redis_client.expire(history_key, self.USER_HISTORY_TTL)

        except redis.ConnectionError as e:
            logger.warning(f"Redis error tracking query: {e}", exc_info=True)
        except (ValueError, TypeError) as e:
            logger.error(f"Data validation error tracking query: {e}", exc_info=True)
        except redis.RedisError as e:
            logger.error(f"Redis error tracking query: {e}", exc_info=True)

    async def _record_analytics(
        self,
        query: str,
        user_id: str | None,
        context: AutocompleteContext,
        suggestions_count: int,
        cache_hit: bool,
        response_time_ms: float,
        sources_used: list[str],
    ) -> None:
        """
        Record analytics for autocomplete request.

        Args:
            query: Search query
            user_id: Optional user ID
            context: Context type
            suggestions_count: Number of suggestions returned
            cache_hit: Whether cache was hit
            response_time_ms: Response time in milliseconds
            sources_used: List of sources used
        """
        try:
            analytics = AutocompleteAnalytics(
                query=query,
                user_id=user_id,
                context=context,
                suggestions_count=suggestions_count,
                cache_hit=cache_hit,
                response_time_ms=response_time_ms,
                sources_used=sources_used,
            )

            # Store in Redis with daily key for aggregation
            redis_client = self._get_redis()
            date_key = datetime.utcnow().strftime("%Y-%m-%d")
            analytics_key = f"{self.ANALYTICS_KEY_PREFIX}:{date_key}"

            # Add to list (limited to prevent unbounded growth)
            redis_client.lpush(analytics_key, str(analytics.to_dict()))
            redis_client.ltrim(analytics_key, 0, 9999)  # Keep last 10k entries
            redis_client.expire(analytics_key, 604800)  # 7 days

            logger.debug(
                f"Autocomplete: query='{query}' "
                f"suggestions={suggestions_count} "
                f"cache_hit={cache_hit} "
                f"time={response_time_ms:.2f}ms"
            )

        except (redis.ConnectionError, redis.RedisError) as e:
            logger.error(f"Redis error recording analytics: {e}", exc_info=True)
        except (ValueError, TypeError) as e:
            logger.error(
                f"Data validation error recording analytics: {e}", exc_info=True
            )

    async def get_analytics(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Get autocomplete analytics for date range.

        Args:
            start_date: Start date (default: 7 days ago)
            end_date: End date (default: today)

        Returns:
            Analytics summary with metrics
        """
        if end_date is None:
            end_date = datetime.utcnow()
        if start_date is None:
            start_date = end_date - timedelta(days=7)

        try:
            redis_client = self._get_redis()

            # Collect analytics from all days in range
            all_analytics = []
            current_date = start_date
            while current_date <= end_date:
                date_key = current_date.strftime("%Y-%m-%d")
                analytics_key = f"{self.ANALYTICS_KEY_PREFIX}:{date_key}"

                entries = redis_client.lrange(analytics_key, 0, -1)
                for entry in entries:
                    try:
                        # Parse stored dict string back to dict
                        all_analytics.append(eval(entry))
                    except Exception:
                        pass

                current_date += timedelta(days=1)

                # Compute summary statistics
            total_queries = len(all_analytics)
            cache_hits = sum(1 for a in all_analytics if a.get("cache_hit"))
            avg_response_time = (
                sum(a.get("response_time_ms", 0) for a in all_analytics) / total_queries
                if total_queries > 0
                else 0
            )
            avg_suggestions = (
                sum(a.get("suggestions_count", 0) for a in all_analytics)
                / total_queries
                if total_queries > 0
                else 0
            )

            # Count by context
            context_counts = defaultdict(int)
            for a in all_analytics:
                context_counts[a.get("context", "unknown")] += 1

                # Count by source
            source_counts = defaultdict(int)
            for a in all_analytics:
                for source in a.get("sources_used", []):
                    source_counts[source] += 1

            return {
                "total_queries": total_queries,
                "cache_hit_rate": (
                    cache_hits / total_queries if total_queries > 0 else 0
                ),
                "avg_response_time_ms": round(avg_response_time, 2),
                "avg_suggestions": round(avg_suggestions, 2),
                "by_context": dict(context_counts),
                "by_source": dict(source_counts),
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            }

        except (redis.ConnectionError, redis.RedisError) as e:
            logger.error(f"Redis error getting analytics: {e}", exc_info=True)
            return {
                "error": str(e),
                "total_queries": 0,
            }
        except (ValueError, TypeError, KeyError) as e:
            logger.error(f"Data processing error getting analytics: {e}", exc_info=True)
            return {
                "error": str(e),
                "total_queries": 0,
            }

    async def clear_cache(self, context: AutocompleteContext | None = None) -> int:
        """
        Clear autocomplete cache.

        Args:
            context: Optional context to clear (if None, clear all)

        Returns:
            Number of entries cleared
        """
        if context:
            pattern = f"{self.SUGGESTION_CACHE_PREFIX}:*:{context.value}:*"
        else:
            pattern = f"{self.SUGGESTION_CACHE_PREFIX}:*"

        return self.cache.invalidate_pattern(pattern)

    def _normalize_query(self, query: str) -> str:
        """
        Normalize query string.

        Args:
            query: Raw query string

        Returns:
            Normalized query
        """
        if not query:
            return ""

            # Trim whitespace
        query = query.strip()

        # Truncate if too long
        if len(query) > self.MAX_QUERY_LENGTH:
            query = query[: self.MAX_QUERY_LENGTH]

        return query

    def _build_cache_key(
        self,
        query: str,
        context: AutocompleteContext,
        user_id: str | None = None,
    ) -> str:
        """
        Build cache key for autocomplete request.

        Args:
            query: Search query
            context: Context type
            user_id: Optional user ID

        Returns:
            Cache key string
        """
        user_part = user_id if user_id else "anon"
        return f"{self.SUGGESTION_CACHE_PREFIX}:{query.lower()}:{context.value}:{user_part}"

        # Global service instance


_autocomplete_service: AutocompleteService | None = None


def get_autocomplete_service(db: AsyncSession) -> AutocompleteService:
    """
    Get autocomplete service instance.

    Args:
        db: Async database session

    Returns:
        AutocompleteService instance

    Example:
        from app.search.autocomplete import get_autocomplete_service

        async def my_handler(db: AsyncSession):
            autocomplete = get_autocomplete_service(db)
            suggestions = await autocomplete.get_suggestions("john")
    """
    return AutocompleteService(db)
