"""
Shard management utilities.

This module provides the ShardManager class for coordinating sharding operations,
managing shard connections, and orchestrating cross-shard operations.
"""

import logging
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.db.sharding.router import (
    CrossShardQuery,
    ShardDistribution,
    ShardKeyExtractor,
    ShardRouter,
)
from app.db.sharding.strategies import ShardInfo, ShardingStrategy

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ShardConnection:
    """
    Manage connection to a single shard.

    Handles engine creation, session management, and connection health checks.
    """

    def __init__(
        self,
        shard_info: ShardInfo,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_pre_ping: bool = True,
        echo: bool = False,
    ) -> None:
        """
        Initialize shard connection.

        Args:
            shard_info: Shard configuration
            pool_size: Connection pool size
            max_overflow: Max connections beyond pool_size
            pool_pre_ping: Enable connection health checks
            echo: Echo SQL statements (for debugging)
        """
        self.shard_info = shard_info
        self.pool_size = pool_size
        self.max_overflow = max_overflow

        # Create async engine for this shard
        self.engine = create_async_engine(
            shard_info.connection_string,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=pool_pre_ping,
            echo=echo,
        )

        # Create session factory
        self.session_factory = sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def get_session(self) -> AsyncSession:
        """
        Get a new database session for this shard.

        Returns:
            AsyncSession for the shard
        """
        return self.session_factory()

    async def health_check(self) -> bool:
        """
        Check if shard connection is healthy.

        Returns:
            True if healthy, False otherwise
        """
        try:
            async with self.get_session() as session:
                await session.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Health check failed for shard {self.shard_info.shard_id}: {e}")
            return False

    async def close(self) -> None:
        """Close all connections and dispose of the engine."""
        await self.engine.dispose()


class ShardManager:
    """
    Central manager for database sharding operations.

    Coordinates shard routing, connection management, and cross-shard queries.

    Example:
        manager = ShardManager()

        # Register sharding strategy
        manager.register_table("users", strategy, key_extractor)

        # Route a single operation
        shard_id = manager.route("users", user_id="123")
        session = await manager.get_session(shard_id)

        # Execute cross-shard query
        results = await manager.query_all_shards(
            "users",
            lambda s: s.execute(select(User))
        )
    """

    def __init__(self) -> None:
        """Initialize shard manager."""
        self.connections: Dict[int, ShardConnection] = {}
        self.routers: Dict[str, ShardRouter] = {}
        self.strategies: Dict[str, ShardingStrategy] = {}
        self._session_cache: Dict[int, AsyncSession] = {}

    def register_shards(
        self,
        shards: List[ShardInfo],
        pool_size: int = 5,
        max_overflow: int = 10,
    ) -> None:
        """
        Register shard connections.

        Args:
            shards: List of shard configurations
            pool_size: Connection pool size per shard
            max_overflow: Max overflow connections per shard
        """
        for shard in shards:
            if shard.shard_id in self.connections:
                logger.warning(f"Shard {shard.shard_id} already registered, skipping")
                continue

            connection = ShardConnection(
                shard_info=shard,
                pool_size=pool_size,
                max_overflow=max_overflow,
            )
            self.connections[shard.shard_id] = connection
            logger.info(f"Registered shard {shard.shard_id}: {shard.name}")

    def register_table(
        self,
        table_name: str,
        strategy: ShardingStrategy,
        key_extractor: ShardKeyExtractor,
    ) -> None:
        """
        Register a sharding strategy for a table.

        Args:
            table_name: Name of the table/entity
            strategy: Sharding strategy to use
            key_extractor: Key extraction logic
        """
        router = ShardRouter(strategy, key_extractor)
        self.routers[table_name] = router
        self.strategies[table_name] = strategy
        logger.info(f"Registered sharding strategy for table '{table_name}'")

    def route(self, table_name: str, obj: Any) -> int:
        """
        Route an object to its target shard.

        Args:
            table_name: Table/entity name
            obj: Object to route (or direct sharding key)

        Returns:
            Shard ID

        Raises:
            ValueError: If table not registered or routing fails
        """
        if table_name not in self.routers:
            raise ValueError(f"No routing strategy registered for table '{table_name}'")

        return self.routers[table_name].route(obj)

    def route_batch(
        self, table_name: str, objects: List[Any]
    ) -> Dict[int, List[Any]]:
        """
        Route multiple objects to their target shards.

        Args:
            table_name: Table/entity name
            objects: List of objects to route

        Returns:
            Dictionary mapping shard_id -> list of objects

        Raises:
            ValueError: If table not registered
        """
        if table_name not in self.routers:
            raise ValueError(f"No routing strategy registered for table '{table_name}'")

        return self.routers[table_name].route_batch(objects)

    async def get_session(self, shard_id: int) -> AsyncSession:
        """
        Get a database session for a specific shard.

        Args:
            shard_id: Shard identifier

        Returns:
            AsyncSession for the shard

        Raises:
            ValueError: If shard not registered
        """
        if shard_id not in self.connections:
            raise ValueError(f"Shard {shard_id} not registered")

        return await self.connections[shard_id].get_session()

    async def get_session_for_key(
        self, table_name: str, obj: Any
    ) -> tuple[int, AsyncSession]:
        """
        Get database session for an object based on its sharding key.

        Args:
            table_name: Table/entity name
            obj: Object to route (or direct sharding key)

        Returns:
            Tuple of (shard_id, session)
        """
        shard_id = self.route(table_name, obj)
        session = await self.get_session(shard_id)
        return shard_id, session

    async def get_all_sessions(
        self, shard_ids: Optional[List[int]] = None
    ) -> Dict[int, AsyncSession]:
        """
        Get sessions for multiple shards.

        Args:
            shard_ids: Specific shard IDs (None = all registered shards)

        Returns:
            Dictionary mapping shard_id -> session
        """
        target_shards = shard_ids or list(self.connections.keys())
        sessions = {}

        for shard_id in target_shards:
            sessions[shard_id] = await self.get_session(shard_id)

        return sessions

    async def execute_on_shard(
        self,
        shard_id: int,
        func: Callable[[AsyncSession], T],
    ) -> T:
        """
        Execute a function on a specific shard.

        Args:
            shard_id: Target shard ID
            func: Async function that takes a session and returns a result

        Returns:
            Function result
        """
        session = await self.get_session(shard_id)
        try:
            return await func(session)
        finally:
            await session.close()

    async def query_all_shards(
        self,
        table_name: str,
        query_func: Callable[[AsyncSession], Any],
        shard_ids: Optional[List[int]] = None,
    ) -> Dict[int, Any]:
        """
        Execute a query on all shards for a table.

        Args:
            table_name: Table/entity name
            query_func: Async function that takes a session and returns results
            shard_ids: Specific shard IDs to query (None = all shards)

        Returns:
            Dictionary mapping shard_id -> results
        """
        sessions = await self.get_all_sessions(shard_ids)
        cross_shard_query = CrossShardQuery(sessions)

        try:
            return await cross_shard_query.execute_on_all_shards(query_func)
        finally:
            # Close all sessions
            for session in sessions.values():
                await session.close()

    async def aggregate_query(
        self,
        table_name: str,
        query_func: Callable[[AsyncSession], Any],
        aggregator: Callable[[List[Any]], Any],
        shard_ids: Optional[List[int]] = None,
    ) -> Any:
        """
        Execute queries on multiple shards and aggregate results.

        Args:
            table_name: Table/entity name
            query_func: Async function that takes a session and returns results
            aggregator: Function to aggregate results from all shards
            shard_ids: Specific shard IDs to query

        Returns:
            Aggregated results
        """
        sessions = await self.get_all_sessions(shard_ids)
        cross_shard_query = CrossShardQuery(sessions)

        try:
            return await cross_shard_query.aggregate_results(
                query_func, aggregator, shard_ids
            )
        finally:
            for session in sessions.values():
                await session.close()

    def get_distribution(self, table_name: str) -> ShardDistribution:
        """
        Get distribution analyzer for a table.

        Args:
            table_name: Table/entity name

        Returns:
            ShardDistribution instance

        Raises:
            ValueError: If table not registered
        """
        if table_name not in self.routers:
            raise ValueError(f"No routing strategy registered for table '{table_name}'")

        return ShardDistribution(self.routers[table_name])

    async def health_check_all(self) -> Dict[int, bool]:
        """
        Check health of all registered shards.

        Returns:
            Dictionary mapping shard_id -> health status
        """
        import asyncio

        async def check_one(shard_id: int, conn: ShardConnection) -> tuple[int, bool]:
            healthy = await conn.health_check()
            return shard_id, healthy

        tasks = [
            check_one(shard_id, conn)
            for shard_id, conn in self.connections.items()
        ]
        results = await asyncio.gather(*tasks)

        return {shard_id: healthy for shard_id, healthy in results}

    async def get_shard_stats(self, shard_id: int) -> Dict[str, Any]:
        """
        Get statistics for a specific shard.

        Args:
            shard_id: Shard identifier

        Returns:
            Dictionary with shard statistics
        """
        if shard_id not in self.connections:
            raise ValueError(f"Shard {shard_id} not registered")

        conn = self.connections[shard_id]
        healthy = await conn.health_check()

        return {
            "shard_id": shard_id,
            "name": conn.shard_info.name,
            "is_active": conn.shard_info.is_active,
            "is_healthy": healthy,
            "weight": conn.shard_info.weight,
            "pool_size": conn.pool_size,
            "max_overflow": conn.max_overflow,
        }

    async def get_all_shard_stats(self) -> List[Dict[str, Any]]:
        """
        Get statistics for all shards.

        Returns:
            List of shard statistics
        """
        import asyncio

        tasks = [
            self.get_shard_stats(shard_id)
            for shard_id in self.connections.keys()
        ]
        return await asyncio.gather(*tasks)

    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """
        Get information about a sharded table.

        Args:
            table_name: Table/entity name

        Returns:
            Dictionary with table sharding information

        Raises:
            ValueError: If table not registered
        """
        if table_name not in self.routers:
            raise ValueError(f"No routing strategy registered for table '{table_name}'")

        router = self.routers[table_name]
        strategy = self.strategies[table_name]

        return {
            "table_name": table_name,
            "strategy_type": type(strategy).__name__,
            "num_shards": len(strategy.shards),
            "active_shards": len(strategy.get_active_shards()),
            "shard_ids": router.get_all_shard_ids(),
            "active_shard_ids": router.get_active_shard_ids(),
        }

    def list_tables(self) -> List[str]:
        """
        List all registered sharded tables.

        Returns:
            List of table names
        """
        return list(self.routers.keys())

    async def close_all(self) -> None:
        """
        Close all shard connections.

        Should be called on application shutdown.
        """
        import asyncio

        logger.info("Closing all shard connections")

        tasks = [conn.close() for conn in self.connections.values()]
        await asyncio.gather(*tasks)

        self.connections.clear()
        logger.info("All shard connections closed")

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"ShardManager(shards={len(self.connections)}, "
            f"tables={len(self.routers)})"
        )


class ShardContext:
    """
    Context manager for shard operations.

    Provides automatic session management and cleanup for shard operations.

    Example:
        async with ShardContext(manager, shard_id) as session:
            result = await session.execute(select(User))
    """

    def __init__(self, manager: ShardManager, shard_id: int) -> None:
        """
        Initialize shard context.

        Args:
            manager: Shard manager instance
            shard_id: Target shard ID
        """
        self.manager = manager
        self.shard_id = shard_id
        self.session: Optional[AsyncSession] = None

    async def __aenter__(self) -> AsyncSession:
        """Enter context and get session."""
        self.session = await self.manager.get_session(self.shard_id)
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context and close session."""
        if self.session:
            await self.session.close()
