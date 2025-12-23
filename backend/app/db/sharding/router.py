"""
Shard routing utilities.

This module provides routing logic to direct database operations to the
correct shard based on sharding keys.
"""

import logging
from collections.abc import Callable
from typing import Any, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.sharding.strategies import ShardInfo, ShardingStrategy

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ShardKeyExtractor:
    """
    Extract sharding keys from various input types.

    Supports extraction from:
    - Direct values (strings, integers, etc.)
    - Dictionary-like objects (dict, Pydantic models)
    - ORM models
    - Custom extraction functions
    """

    def __init__(
        self,
        key_field: str | None = None,
        extractor_func: Callable[[Any], Any] | None = None,
    ) -> None:
        """
        Initialize shard key extractor.

        Args:
            key_field: Field name to extract from objects
            extractor_func: Custom extraction function
        """
        self.key_field = key_field
        self.extractor_func = extractor_func

        if not key_field and not extractor_func:
            raise ValueError("Either key_field or extractor_func must be provided")

    def extract(self, obj: Any) -> Any:
        """
        Extract sharding key from an object.

        Args:
            obj: Object to extract key from

        Returns:
            Extracted sharding key

        Raises:
            ValueError: If key cannot be extracted
        """
        # Use custom extractor if provided
        if self.extractor_func:
            try:
                return self.extractor_func(obj)
            except Exception as e:
                raise ValueError(f"Custom extractor failed: {e}") from e

        # Direct value (string, int, etc.)
        if isinstance(obj, (str, int, float)):
            return obj

        # Dictionary-like access
        if isinstance(obj, dict):
            if self.key_field not in obj:
                raise ValueError(f"Key field '{self.key_field}' not found in dict")
            return obj[self.key_field]

        # Pydantic model
        if hasattr(obj, "model_dump"):
            data = obj.model_dump()
            if self.key_field not in data:
                raise ValueError(f"Key field '{self.key_field}' not found in model")
            return data[self.key_field]

        # SQLAlchemy model or object with attributes
        if hasattr(obj, self.key_field):
            return getattr(obj, self.key_field)

        raise ValueError(
            f"Cannot extract key field '{self.key_field}' from {type(obj).__name__}"
        )


class ShardRouter:
    """
    Route database operations to appropriate shards.

    The router determines which shard(s) to use for a given operation based on
    the sharding strategy and extracted shard keys.

    Example:
        router = ShardRouter(strategy, key_extractor)
        shard_id = router.route(user_data)
        shard_info = router.get_shard_info(shard_id)
    """

    def __init__(
        self,
        strategy: ShardingStrategy,
        key_extractor: ShardKeyExtractor,
    ) -> None:
        """
        Initialize shard router.

        Args:
            strategy: Sharding strategy to use
            key_extractor: Key extraction logic
        """
        self.strategy = strategy
        self.key_extractor = key_extractor

    def route(self, obj: Any) -> int:
        """
        Route an object to its target shard.

        Args:
            obj: Object to route (or direct sharding key)

        Returns:
            Shard ID

        Raises:
            ValueError: If routing fails
        """
        try:
            key = self.key_extractor.extract(obj)
            shard_id = self.strategy.get_shard_id(key)
            logger.debug(f"Routed key {key} to shard {shard_id}")
            return shard_id
        except Exception as e:
            logger.error(f"Routing failed: {e}", exc_info=True)
            raise ValueError(f"Failed to route object: {e}") from e

    def route_batch(self, objects: list[Any]) -> dict[int, list[Any]]:
        """
        Route multiple objects to their target shards.

        Args:
            objects: List of objects to route

        Returns:
            Dictionary mapping shard_id -> list of objects
        """
        shard_groups: dict[int, list[Any]] = {}

        for obj in objects:
            try:
                shard_id = self.route(obj)
                if shard_id not in shard_groups:
                    shard_groups[shard_id] = []
                shard_groups[shard_id].append(obj)
            except Exception as e:
                logger.warning(f"Failed to route object: {e}")
                continue

        return shard_groups

    def get_shard_info(self, shard_id: int) -> ShardInfo | None:
        """
        Get information about a specific shard.

        Args:
            shard_id: Shard identifier

        Returns:
            ShardInfo if found, None otherwise
        """
        return self.strategy.get_shard_info(shard_id)

    def get_all_shard_ids(self) -> list[int]:
        """
        Get all available shard IDs.

        Returns:
            List of all shard IDs
        """
        return [shard.shard_id for shard in self.strategy.shards]

    def get_active_shard_ids(self) -> list[int]:
        """
        Get all active shard IDs.

        Returns:
            List of active shard IDs
        """
        return [shard.shard_id for shard in self.strategy.get_active_shards()]


class CrossShardQuery:
    """
    Execute queries across multiple shards.

    Provides utilities for fan-out queries and result aggregation when data
    spans multiple shards.

    Example:
        query = CrossShardQuery(sessions)
        results = await query.execute_on_all_shards(
            lambda session: session.execute(select(User))
        )
    """

    def __init__(self, shard_sessions: dict[int, AsyncSession]) -> None:
        """
        Initialize cross-shard query executor.

        Args:
            shard_sessions: Mapping of shard_id -> database session
        """
        self.shard_sessions = shard_sessions

    async def execute_on_shard(
        self,
        shard_id: int,
        query_func: Callable[[AsyncSession], Any],
    ) -> Any:
        """
        Execute a query on a specific shard.

        Args:
            shard_id: Target shard ID
            query_func: Async function that takes a session and returns results

        Returns:
            Query results

        Raises:
            ValueError: If shard session not available
        """
        if shard_id not in self.shard_sessions:
            raise ValueError(f"No session available for shard {shard_id}")

        session = self.shard_sessions[shard_id]
        return await query_func(session)

    async def execute_on_all_shards(
        self,
        query_func: Callable[[AsyncSession], Any],
        shard_ids: list[int] | None = None,
    ) -> dict[int, Any]:
        """
        Execute a query on multiple shards in parallel.

        Args:
            query_func: Async function that takes a session and returns results
            shard_ids: Specific shard IDs to query (None = all shards)

        Returns:
            Dictionary mapping shard_id -> results
        """
        import asyncio

        target_shards = shard_ids or list(self.shard_sessions.keys())
        results = {}

        async def execute_one(shard_id: int) -> tuple[int, Any]:
            try:
                result = await self.execute_on_shard(shard_id, query_func)
                return (shard_id, result)
            except Exception as e:
                logger.error(f"Query failed on shard {shard_id}: {e}", exc_info=True)
                return (shard_id, None)

        # Execute queries in parallel
        tasks = [execute_one(shard_id) for shard_id in target_shards]
        shard_results = await asyncio.gather(*tasks)

        for shard_id, result in shard_results:
            results[shard_id] = result

        return results

    async def aggregate_results(
        self,
        query_func: Callable[[AsyncSession], Any],
        aggregator: Callable[[list[Any]], Any],
        shard_ids: list[int] | None = None,
    ) -> Any:
        """
        Execute queries on multiple shards and aggregate results.

        Args:
            query_func: Async function that takes a session and returns results
            aggregator: Function to aggregate results from all shards
            shard_ids: Specific shard IDs to query (None = all shards)

        Returns:
            Aggregated results

        Example:
            # Count total users across all shards
            total = await query.aggregate_results(
                lambda s: s.execute(select(func.count(User.id))).scalar(),
                sum
            )
        """
        shard_results = await self.execute_on_all_shards(query_func, shard_ids)

        # Filter out None results (failed queries)
        valid_results = [r for r in shard_results.values() if r is not None]

        if not valid_results:
            return None

        return aggregator(valid_results)

    async def merge_sorted_results(
        self,
        query_func: Callable[[AsyncSession], list[T]],
        key_func: Callable[[T], Any],
        limit: int | None = None,
        reverse: bool = False,
        shard_ids: list[int] | None = None,
    ) -> list[T]:
        """
        Execute queries on multiple shards and merge sorted results.

        Useful for paginated queries across shards where each shard returns
        pre-sorted results.

        Args:
            query_func: Async function returning sorted list of items
            key_func: Function to extract sort key from items
            limit: Maximum number of results to return
            reverse: Sort in descending order
            shard_ids: Specific shard IDs to query

        Returns:
            Merged and sorted list of results
        """

        shard_results = await self.execute_on_all_shards(query_func, shard_ids)

        # Flatten all results
        all_results: list[T] = []
        for results in shard_results.values():
            if results:
                all_results.extend(results)

        # Sort merged results
        sorted_results = sorted(all_results, key=key_func, reverse=reverse)

        # Apply limit if specified
        if limit is not None:
            return sorted_results[:limit]

        return sorted_results


class ShardDistribution:
    """
    Analyze and report on data distribution across shards.

    Provides utilities to understand how data is distributed and identify
    potential imbalances.
    """

    def __init__(self, router: ShardRouter) -> None:
        """
        Initialize shard distribution analyzer.

        Args:
            router: Shard router to analyze
        """
        self.router = router

    def analyze_distribution(self, keys: list[Any]) -> dict[int, int]:
        """
        Analyze how a set of keys would be distributed across shards.

        Args:
            keys: List of sharding keys

        Returns:
            Dictionary mapping shard_id -> count of keys
        """
        distribution: dict[int, int] = {}

        for key in keys:
            try:
                shard_id = self.router.strategy.get_shard_id(key)
                distribution[shard_id] = distribution.get(shard_id, 0) + 1
            except Exception as e:
                logger.warning(f"Failed to route key {key}: {e}")

        return distribution

    def calculate_balance_score(self, distribution: dict[int, int]) -> float:
        """
        Calculate distribution balance score (0.0 = perfectly balanced, 1.0 = worst).

        Uses coefficient of variation to measure distribution uniformity.

        Args:
            distribution: Shard distribution counts

        Returns:
            Balance score (lower is better)
        """
        if not distribution:
            return 0.0

        counts = list(distribution.values())
        if len(counts) == 1:
            return 0.0

        mean = sum(counts) / len(counts)
        if mean == 0:
            return 0.0

        variance = sum((x - mean) ** 2 for x in counts) / len(counts)
        std_dev = variance**0.5

        # Coefficient of variation
        cv = std_dev / mean

        # Normalize to 0-1 scale (CV of 1.0 = perfectly imbalanced)
        return min(cv, 1.0)

    def get_distribution_report(self, keys: list[Any]) -> dict[str, Any]:
        """
        Generate comprehensive distribution report.

        Args:
            keys: List of sharding keys

        Returns:
            Distribution report with statistics
        """
        distribution = self.analyze_distribution(keys)
        total_keys = sum(distribution.values())

        report = {
            "total_keys": total_keys,
            "num_shards": len(distribution),
            "distribution": distribution,
            "balance_score": self.calculate_balance_score(distribution),
        }

        if total_keys > 0:
            report["percentages"] = {
                shard_id: (count / total_keys) * 100
                for shard_id, count in distribution.items()
            }

            counts = list(distribution.values())
            report["statistics"] = {
                "min_keys": min(counts),
                "max_keys": max(counts),
                "mean_keys": sum(counts) / len(counts),
                "median_keys": sorted(counts)[len(counts) // 2],
            }

        return report
