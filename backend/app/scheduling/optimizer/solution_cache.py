"""Solution caching for schedule generation.

Caches partial and complete solutions to avoid redundant computation.
"""

import hashlib
import json
import logging
from datetime import date, timedelta
from typing import Any, Optional

from app.cache.cache_manager import get_cache_manager

logger = logging.getLogger(__name__)


class SolutionCache:
    """Cache for schedule generation solutions."""

    def __init__(self):
        """Initialize solution cache."""
        self.cache = get_cache_manager()
        self.ttl = 3600  # 1 hour

    def generate_problem_hash(
        self,
        persons: list[dict],
        rotations: list[dict],
        blocks: list[dict],
        constraints: dict,
    ) -> str:
        """Generate hash for scheduling problem.

        Args:
            persons: List of persons
            rotations: List of rotations
            blocks: List of blocks
            constraints: Constraint parameters

        Returns:
            Hash string identifying the problem
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
        """Get cached solution for problem.

        Args:
            problem_hash: Problem hash

        Returns:
            Cached solution or None
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
        """Cache solution for problem.

        Args:
            problem_hash: Problem hash
            solution: Solution data
            ttl: Time to live in seconds
        """
        key = f"schedule_solution:{problem_hash}"
        await self.cache.set(key, json.dumps(solution), ttl or self.ttl)
        logger.info(f"Cached solution for {problem_hash}")

    async def get_partial_solution(
        self,
        problem_hash: str,
        date_range: tuple[date, date],
    ) -> dict | None:
        """Get cached partial solution for date range.

        Args:
            problem_hash: Problem hash
            date_range: (start_date, end_date)

        Returns:
            Cached partial solution or None
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
        """Cache partial solution.

        Args:
            problem_hash: Problem hash
            date_range: (start_date, end_date)
            partial_solution: Partial solution data
            ttl: Time to live in seconds
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
        """Invalidate solutions affected by changes.

        Args:
            person_ids: Optional person IDs that changed
            rotation_ids: Optional rotation IDs that changed
            date_range: Optional date range affected

        Returns:
            Number of cache entries invalidated
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
        """Find similar cached solutions that could be adapted.

        Args:
            problem_hash: Current problem hash
            similarity_threshold: Minimum similarity score (0-1)

        Returns:
            List of similar solutions
        """
        # This is a placeholder for similarity search
        # In production, would implement fuzzy matching on problem parameters
        logger.debug(f"Looking for similar solutions to {problem_hash}")
        return []


class IncrementalSolutionBuilder:
    """Build solutions incrementally and cache intermediate results."""

    def __init__(self, solution_cache: SolutionCache):
        """Initialize incremental solution builder.

        Args:
            solution_cache: SolutionCache instance
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
        """Initialize with problem definition.

        Args:
            persons: List of persons
            rotations: List of rotations
            blocks: List of blocks
            constraints: Constraint parameters
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
        """Add assignments for date range.

        Args:
            assignments: List of assignments
            date_range: Date range for these assignments
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
        """Finalize and cache complete solution.

        Returns:
            Complete solution
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
    """Get global solution cache instance.

    Returns:
        SolutionCache singleton
    """
    global _solution_cache
    if _solution_cache is None:
        _solution_cache = SolutionCache()
    return _solution_cache
