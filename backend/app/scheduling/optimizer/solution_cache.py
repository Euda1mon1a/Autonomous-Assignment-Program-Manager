"""
Solution caching for schedule generation.

This module implements caching for schedule generation solutions to avoid
redundant computation. It stores both complete solutions and partial solutions
(for incremental building) using a Redis-backed cache.

Key Concepts:
    **Problem Hashing**: Each scheduling problem is converted to a deterministic
    hash based on persons, rotations, blocks, and constraints. Identical problems
    produce identical hashes, enabling cache lookups.

    **Partial Solutions**: For long-running schedule generation, partial solutions
    can be cached at intermediate points. This enables:
        - Resume after interruption
        - Incremental building for dynamic updates
        - Fine-grained invalidation when small changes occur

    **Similarity Search**: (Planned) Find cached solutions for similar problems
    that can be adapted rather than regenerating from scratch.

Cache Architecture:
    - Uses Redis via CacheManager for distributed caching
    - Default TTL of 1 hour (3600 seconds)
    - Key format: "schedule_solution:{hash}" for complete solutions
    - Key format: "partial_solution:{hash}:{start}:{end}" for partials

Classes:
    SolutionCache: Main cache interface for storing and retrieving solutions.

    IncrementalSolutionBuilder: Helper for building solutions incrementally
        while caching intermediate results.

Functions:
    get_solution_cache: Singleton accessor for global cache instance.

Example:
    >>> cache = get_solution_cache()
    >>> problem_hash = cache.generate_problem_hash(
    ...     persons=[{"id": "p1"}, {"id": "p2"}],
    ...     rotations=[{"id": "r1"}],
    ...     blocks=[{"id": "b1"}],
    ...     constraints={"max_hours": 80}
    ... )
    >>> # Check for cached solution
    >>> cached = await cache.get_solution(problem_hash)
    >>> if cached:
    ...     print("Cache hit!")
    ...     return cached
    >>> # Generate and cache new solution
    >>> solution = await generate_schedule(...)
    >>> await cache.set_solution(problem_hash, solution)

See Also:
    - app/cache/cache_manager.py: Underlying Redis cache implementation
    - app/scheduling/optimizer/incremental_update.py: Incremental update strategies
"""

import hashlib
import json
import logging
from datetime import date, timedelta
from typing import Any, Optional

from app.cache.cache_manager import get_cache_manager

logger = logging.getLogger(__name__)


class SolutionCache:
    """
    Cache for schedule generation solutions.

    Provides caching for both complete schedule solutions and partial solutions
    during incremental generation. Uses Redis for distributed caching with
    configurable TTL.

    The cache is keyed by a hash of the problem definition, ensuring that
    identical problems return cached results while any change to inputs
    triggers fresh computation.

    Attributes:
        cache: The underlying CacheManager instance.
        ttl: Default time-to-live in seconds for cached entries.

    Example:
        >>> cache = SolutionCache()
        >>> hash = cache.generate_problem_hash(persons, rotations, blocks, constraints)
        >>> solution = await cache.get_solution(hash)
        >>> if solution is None:
        ...     solution = await generate_schedule(...)
        ...     await cache.set_solution(hash, solution)
    """

    def __init__(self) -> None:
        """
        Initialize solution cache.

        Sets up cache manager connection and default TTL (time to live)
        of 1 hour for cached solutions. The TTL can be overridden on a
        per-entry basis when setting solutions.
        """
        self.cache = get_cache_manager()
        self.ttl = 3600  # 1 hour

    def generate_problem_hash(
        self,
        persons: list[dict],
        rotations: list[dict],
        blocks: list[dict],
        constraints: dict,
    ) -> str:
        """
        Generate a deterministic hash for a scheduling problem.

        Creates a unique identifier for a scheduling problem based on its
        inputs. The hash is deterministic: identical inputs always produce
        the same hash, enabling reliable cache lookups.

        Args:
            persons: List of person dictionaries. Only IDs are used for hashing
                to avoid false cache misses from irrelevant attribute changes.

            rotations: List of rotation dictionaries. Only IDs are used.

            blocks: List of block dictionaries. Only IDs are used.

            constraints: Constraint parameters dictionary. All keys and values
                are included in the hash since constraint changes affect solutions.

        Returns:
            A 16-character hexadecimal hash string that uniquely identifies
            this problem configuration.

        Note:
            The hash is based on sorted IDs and JSON-serialized constraints,
            ensuring order-independence for lists while capturing all
            constraint details.

        Example:
            >>> hash1 = cache.generate_problem_hash(
            ...     persons=[{"id": "p1"}, {"id": "p2"}],
            ...     rotations=[{"id": "r1"}],
            ...     blocks=[{"id": "b1"}],
            ...     constraints={"max_hours": 80}
            ... )
            >>> hash2 = cache.generate_problem_hash(
            ...     persons=[{"id": "p2"}, {"id": "p1"}],  # Different order
            ...     rotations=[{"id": "r1"}],
            ...     blocks=[{"id": "b1"}],
            ...     constraints={"max_hours": 80}
            ... )
            >>> assert hash1 == hash2  # Order doesn't matter
        """
        # Create deterministic representation
        problem_data = {
            "persons": sorted([p["id"] for p in persons]),
            "rotations": sorted([r["id"] for r in rotations]),
            "blocks": sorted([b["id"] for b in blocks]),
            "constraints": constraints,
        }

        problem_json = json.dumps(problem_data, sort_keys=True)
        return hashlib.sha256(problem_json.encode()).hexdigest()[:16]

    async def get_solution(
        self,
        problem_hash: str,
    ) -> dict | None:
        """
        Retrieve a cached solution for a problem.

        Looks up a complete schedule solution by its problem hash. Returns
        the cached solution if found and not expired, None otherwise.

        Args:
            problem_hash: Hash string from generate_problem_hash() identifying
                the scheduling problem.

        Returns:
            The cached solution dictionary if found, None on cache miss.
            The solution contains 'assignments' and any solver metadata.

        Example:
            >>> cached = await cache.get_solution(problem_hash)
            >>> if cached:
            ...     assignments = cached["assignments"]
            ...     print(f"Found {len(assignments)} cached assignments")
        """
        key = f"schedule_solution:{problem_hash}"
        cached = await self.cache.get(key)

        if cached:
            logger.info(f"Solution cache hit for {problem_hash}")
            return json.loads(cached)

        logger.debug(f"Solution cache miss for {problem_hash}")
        return None

    async def set_solution(
        self,
        problem_hash: str,
        solution: dict,
        ttl: int | None = None,
    ) -> None:
        """
        Store a solution in the cache.

        Caches a complete schedule solution for later retrieval. The solution
        is associated with the problem hash and stored with the specified
        or default TTL.

        Args:
            problem_hash: Hash string identifying the scheduling problem.
                Generate using generate_problem_hash().

            solution: The complete schedule solution dictionary. Should contain
                'assignments' and any relevant solver metadata.

            ttl: Optional time-to-live in seconds. If None, uses the default
                TTL of 3600 seconds (1 hour).

        Note:
            Setting a solution with an existing hash will overwrite the
            previous cached value.

        Example:
            >>> solution = {
            ...     "assignments": [...],
            ...     "objective_value": 150,
            ...     "solver_time": 45.2
            ... }
            >>> await cache.set_solution(problem_hash, solution)
            >>> # Or with custom TTL
            >>> await cache.set_solution(problem_hash, solution, ttl=7200)
        """
        key = f"schedule_solution:{problem_hash}"
        await self.cache.set(key, json.dumps(solution), ttl or self.ttl)
        logger.info(f"Cached solution for {problem_hash}")

    async def get_partial_solution(
        self,
        problem_hash: str,
        date_range: tuple[date, date],
    ) -> dict | None:
        """
        Retrieve a cached partial solution for a date range.

        Partial solutions are cached during incremental schedule building.
        This allows resuming interrupted generation or reusing portions
        of a schedule when only part of the problem changes.

        Args:
            problem_hash: Hash string identifying the scheduling problem.

            date_range: Tuple of (start_date, end_date) for the partial
                solution. Both dates are inclusive.

        Returns:
            The cached partial solution dictionary if found, None otherwise.
            Contains 'assignments' for the specified date range only.

        Example:
            >>> from datetime import date
            >>> start = date(2024, 1, 1)
            >>> end = date(2024, 1, 31)
            >>> partial = await cache.get_partial_solution(hash, (start, end))
            >>> if partial:
            ...     print(f"Found {len(partial['assignments'])} cached assignments")
        """
        start_date, end_date = date_range
        key = f"partial_solution:{problem_hash}:{start_date}:{end_date}"
        cached = await self.cache.get(key)

        if cached:
            logger.info(f"Partial solution cache hit for {problem_hash}")
            return json.loads(cached)

        return None

    async def set_partial_solution(
        self,
        problem_hash: str,
        date_range: tuple[date, date],
        partial_solution: dict,
        ttl: int | None = None,
    ) -> None:
        """
        Store a partial solution in the cache.

        Caches a portion of a schedule solution for a specific date range.
        Useful for incremental building where different date ranges are
        generated separately.

        Args:
            problem_hash: Hash string identifying the scheduling problem.

            date_range: Tuple of (start_date, end_date) for this partial
                solution. Both dates are inclusive.

            partial_solution: Dictionary containing 'assignments' for the
                specified date range only.

            ttl: Optional time-to-live in seconds. Defaults to class TTL.

        Example:
            >>> from datetime import date
            >>> partial = {"assignments": [...]}  # January only
            >>> await cache.set_partial_solution(
            ...     hash,
            ...     (date(2024, 1, 1), date(2024, 1, 31)),
            ...     partial
            ... )
        """
        start_date, end_date = date_range
        key = f"partial_solution:{problem_hash}:{start_date}:{end_date}"
        await self.cache.set(key, json.dumps(partial_solution), ttl or self.ttl)

    async def invalidate_solutions(
        self,
        person_ids: list[str] | None = None,
        rotation_ids: list[str] | None = None,
        date_range: tuple[date, date] | None = None,
    ) -> int:
        """
        Invalidate cached solutions affected by changes.

        When persons, rotations, or constraints change, cached solutions
        may become invalid. This method removes affected cache entries
        to ensure fresh computation occurs.

        Args:
            person_ids: Optional list of person IDs that changed. If provided,
                would selectively invalidate solutions containing these persons.
                (Currently invalidates all - selective invalidation is planned.)

            rotation_ids: Optional list of rotation IDs that changed.
                (Currently invalidates all - selective invalidation is planned.)

            date_range: Optional tuple of (start_date, end_date) affected.
                (Currently invalidates all - selective invalidation is planned.)

        Returns:
            Number of cache entries invalidated.

        Note:
            Current implementation invalidates ALL cached solutions for
            simplicity. Future versions will implement selective invalidation
            based on the provided parameters.

        Example:
            >>> # Person left the program - invalidate affected schedules
            >>> count = await cache.invalidate_solutions(person_ids=["p123"])
            >>> print(f"Invalidated {count} cached solutions")
        """
        # For now, invalidate all solutions
        # In production, would be more selective based on parameters
        count = await self.cache.invalidate_pattern("schedule_solution:*")
        count += await self.cache.invalidate_pattern("partial_solution:*")

        logger.info(f"Invalidated {count} solution cache entries")
        return count

    async def get_similar_solutions(
        self,
        problem_hash: str,
        similarity_threshold: float = 0.8,
    ) -> list[dict]:
        """
        Find similar cached solutions that could be adapted.

        When a cache miss occurs, similar solutions from different but related
        problems might provide good starting points for the solver or reduce
        computation by adapting an existing solution.

        Args:
            problem_hash: Hash of the current problem to find similar solutions for.

            similarity_threshold: Minimum similarity score (0.0 to 1.0) for a
                solution to be considered. Default 0.8 means solutions must be
                at least 80% similar.

        Returns:
            List of similar solution dictionaries, sorted by similarity score
            (highest first). Empty list if no similar solutions found.

        Note:
            This is currently a placeholder. Future implementation will:
            1. Store problem metadata alongside solutions
            2. Compute similarity based on person/rotation/block overlap
            3. Return solutions that share significant overlap with current problem

        Example:
            >>> similar = await cache.get_similar_solutions(new_hash, threshold=0.9)
            >>> if similar:
            ...     print(f"Found {len(similar)} similar solutions to adapt")
        """
        # This is a placeholder for similarity search
        # In production, would implement fuzzy matching on problem parameters
        logger.debug(f"Looking for similar solutions to {problem_hash}")
        return []


class IncrementalSolutionBuilder:
    """
    Build solutions incrementally and cache intermediate results.

    This class helps construct schedule solutions piece by piece, caching
    partial results along the way. Useful for:
        - Long-running schedule generation that may be interrupted
        - Building schedules in date-range chunks
        - Resuming from cached partial solutions after changes

    The builder maintains a current solution state and automatically
    caches partial solutions as they are added.

    Attributes:
        cache: Reference to the SolutionCache for caching operations.
        current_solution: The solution being built, with 'assignments' list.
        problem_hash: Hash of the current problem for cache keying.

    Example:
        >>> builder = IncrementalSolutionBuilder(cache)
        >>> await builder.initialize(persons, rotations, blocks, constraints)
        >>>
        >>> # Build in monthly chunks
        >>> for month in months:
        ...     assignments = await generate_month(month)
        ...     await builder.add_assignments(assignments, month_range)
        >>>
        >>> solution = await builder.finalize()
    """

    def __init__(self, solution_cache: SolutionCache):
        """
        Initialize incremental solution builder.

        Sets up builder with reference to solution cache for loading
        and storing intermediate results during incremental build.

        Args:
            solution_cache: SolutionCache instance for caching operations.
                The same cache should be used across related builds for
                proper cache utilization.
        """
        self.cache = solution_cache
        self.current_solution: dict = {}
        self.problem_hash: str | None = None

    async def initialize(
        self,
        persons: list[dict],
        rotations: list[dict],
        blocks: list[dict],
        constraints: dict,
    ) -> None:
        """
        Initialize builder with problem definition.

        Generates a problem hash and attempts to load a previously cached
        solution. If found, the cached solution is loaded as the starting
        point. Otherwise, initializes an empty solution structure.

        Args:
            persons: List of persons in the scheduling problem.
            rotations: List of available rotations.
            blocks: List of time blocks to schedule.
            constraints: Constraint parameters for the problem.

        Note:
            If a cached solution is found, it is loaded into current_solution.
            This allows resuming from where a previous build left off.

        Example:
            >>> builder = IncrementalSolutionBuilder(cache)
            >>> await builder.initialize(persons, rotations, blocks, constraints)
            >>> if builder.current_solution.get("assignments"):
            ...     print("Resuming from cached solution")
        """
        self.problem_hash = self.cache.generate_problem_hash(
            persons, rotations, blocks, constraints
        )

        # Try to load cached solution
        cached = await self.cache.get_solution(self.problem_hash)
        if cached:
            self.current_solution = cached
            logger.info("Loaded cached solution")
        else:
            self.current_solution = {"assignments": []}

    async def add_assignments(
        self,
        assignments: list[dict],
        date_range: tuple[date, date],
    ) -> None:
        """
        Add assignments for a date range.

        Appends new assignments to the current solution and caches them
        as a partial solution for the specified date range. This enables
        resuming from this point if generation is interrupted.

        Args:
            assignments: List of assignment dictionaries to add. Each should
                contain 'person_id', 'block_id', 'rotation_id', etc.

            date_range: Tuple of (start_date, end_date) covered by these
                assignments. Used as the cache key for partial solution.

        Note:
            Assignments are appended to the existing list, not replaced.
            For overlapping date ranges, ensure no duplicate assignments.

        Example:
            >>> jan_assignments = await generate_january()
            >>> await builder.add_assignments(
            ...     jan_assignments,
            ...     (date(2024, 1, 1), date(2024, 1, 31))
            ... )
        """
        self.current_solution["assignments"].extend(assignments)

        # Cache partial solution
        if self.problem_hash:
            await self.cache.set_partial_solution(
                self.problem_hash,
                date_range,
                {"assignments": assignments},
            )

    async def finalize(self) -> dict:
        """
        Finalize and cache the complete solution.

        Stores the complete assembled solution in the cache and returns it.
        Should be called after all assignments have been added to mark
        the solution as complete.

        Returns:
            The complete solution dictionary containing all assignments
            added via add_assignments().

        Note:
            After finalization, the complete solution is cached with the
            default TTL. The builder can be reused for a new problem by
            calling initialize() again.

        Example:
            >>> # After adding all assignments
            >>> complete_solution = await builder.finalize()
            >>> print(f"Complete solution: {len(complete_solution['assignments'])} assignments")
        """
        if self.problem_hash:
            await self.cache.set_solution(
                self.problem_hash,
                self.current_solution,
            )

        logger.info("Finalized and cached complete solution")
        return self.current_solution


# Global solution cache
_solution_cache: SolutionCache | None = None


def get_solution_cache() -> SolutionCache:
    """
    Get the global solution cache instance.

    Implements singleton pattern for the solution cache. Creates a new
    instance on first call, returns the existing instance on subsequent calls.
    This ensures all code shares the same cache instance for consistency.

    Returns:
        SolutionCache: Global singleton cache instance.

    Note:
        The singleton is module-level, so different modules importing this
        function will share the same cache instance.

    Example:
        >>> cache = get_solution_cache()
        >>> problem_hash = cache.generate_problem_hash(
        ...     persons, rotations, blocks, constraints
        ... )
        >>> cached_solution = await cache.get_solution(problem_hash)
    """
    global _solution_cache
    if _solution_cache is None:
        _solution_cache = SolutionCache()
    return _solution_cache
