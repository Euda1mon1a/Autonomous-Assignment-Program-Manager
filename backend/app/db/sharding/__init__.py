"""
Database sharding utilities.

This module provides comprehensive sharding capabilities including:
- Hash-based, range-based, and directory-based sharding strategies
- Shard routing and key extraction
- Cross-shard query execution
- Shard rebalancing and migration

Example:
    from app.db.sharding import ShardManager, HashShardingStrategy

    manager = ShardManager()
    strategy = HashShardingStrategy(num_shards=4)
    manager.register_strategy("users", strategy)

    shard_id = manager.route("users", user_id="123")
"""

from app.db.sharding.manager import ShardManager
from app.db.sharding.router import ShardRouter
from app.db.sharding.strategies import (
    DirectoryShardingStrategy,
    HashShardingStrategy,
    RangeShardingStrategy,
    ShardingStrategy,
)
from app.db.sharding.migration import ShardMigration, ShardRebalancer

__all__ = [
    "ShardManager",
    "ShardRouter",
    "ShardingStrategy",
    "HashShardingStrategy",
    "RangeShardingStrategy",
    "DirectoryShardingStrategy",
    "ShardMigration",
    "ShardRebalancer",
]
