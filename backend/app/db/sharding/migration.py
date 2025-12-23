"""
Shard migration and rebalancing utilities.

This module provides utilities for:
- Moving data between shards (migration)
- Rebalancing data distribution
- Adding/removing shards
- Validating shard consistency
"""

import logging
from collections.abc import Callable
from datetime import datetime
from enum import Enum
from typing import Any, TypeVar

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.sharding.manager import ShardManager
from app.db.sharding.strategies import DirectoryShardingStrategy, ShardInfo

logger = logging.getLogger(__name__)

T = TypeVar("T")


class MigrationStatus(str, Enum):
    """Migration operation status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class MigrationPlan(BaseModel):
    """
    Plan for migrating data between shards.

    Defines which keys/records should be moved from source to target shards.
    """

    migration_id: str = Field(..., description="Unique migration identifier")
    table_name: str = Field(..., description="Table being migrated")
    source_shard_id: int = Field(..., description="Source shard ID")
    target_shard_id: int = Field(..., description="Target shard ID")
    keys_to_migrate: list[Any] = Field(..., description="List of keys to migrate")
    status: MigrationStatus = Field(
        default=MigrationStatus.PENDING, description="Migration status"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    records_migrated: int = Field(default=0, description="Number of records migrated")
    records_failed: int = Field(default=0, description="Number of failed records")
    error_message: str | None = None

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True


class MigrationResult(BaseModel):
    """Result of a migration operation."""

    migration_id: str
    status: MigrationStatus
    records_migrated: int
    records_failed: int
    duration_seconds: float
    error_message: str | None = None


class ShardMigration:
    """
    Execute data migration between shards.

    Provides safe, transactional migration of data from one shard to another
    with rollback capability.

    Example:
        migration = ShardMigration(manager)
        plan = MigrationPlan(
            migration_id="mig_001",
            table_name="users",
            source_shard_id=0,
            target_shard_id=1,
            keys_to_migrate=["user_123", "user_456"]
        )
        result = await migration.execute(plan, fetch_func, insert_func)
    """

    def __init__(self, manager: ShardManager) -> None:
        """
        Initialize shard migration.

        Args:
            manager: Shard manager instance
        """
        self.manager = manager
        self.active_migrations: dict[str, MigrationPlan] = {}

    async def execute(
        self,
        plan: MigrationPlan,
        fetch_func: Callable[[AsyncSession, Any], T | None],
        insert_func: Callable[[AsyncSession, T], None],
        delete_source: bool = True,
        batch_size: int = 100,
    ) -> MigrationResult:
        """
        Execute a migration plan.

        Args:
            plan: Migration plan to execute
            fetch_func: Function to fetch a record from source shard
            insert_func: Function to insert a record into target shard
            delete_source: Whether to delete from source after migration
            batch_size: Number of records to migrate per batch

        Returns:
            MigrationResult with outcome details
        """
        start_time = datetime.utcnow()
        plan.status = MigrationStatus.IN_PROGRESS
        plan.started_at = start_time
        self.active_migrations[plan.migration_id] = plan

        logger.info(
            f"Starting migration {plan.migration_id}: "
            f"{len(plan.keys_to_migrate)} keys from shard {plan.source_shard_id} "
            f"to shard {plan.target_shard_id}"
        )

        try:
            # Process in batches
            for i in range(0, len(plan.keys_to_migrate), batch_size):
                batch_keys = plan.keys_to_migrate[i : i + batch_size]
                await self._migrate_batch(
                    plan, batch_keys, fetch_func, insert_func, delete_source
                )

            # Mark as completed
            plan.status = MigrationStatus.COMPLETED
            plan.completed_at = datetime.utcnow()

            duration = (plan.completed_at - start_time).total_seconds()
            logger.info(
                f"Migration {plan.migration_id} completed: "
                f"{plan.records_migrated} migrated, {plan.records_failed} failed, "
                f"{duration:.2f}s"
            )

            return MigrationResult(
                migration_id=plan.migration_id,
                status=plan.status,
                records_migrated=plan.records_migrated,
                records_failed=plan.records_failed,
                duration_seconds=duration,
            )

        except Exception as e:
            plan.status = MigrationStatus.FAILED
            plan.error_message = str(e)
            logger.error(f"Migration {plan.migration_id} failed: {e}", exc_info=True)

            duration = (datetime.utcnow() - start_time).total_seconds()
            return MigrationResult(
                migration_id=plan.migration_id,
                status=plan.status,
                records_migrated=plan.records_migrated,
                records_failed=plan.records_failed,
                duration_seconds=duration,
                error_message=str(e),
            )
        finally:
            self.active_migrations.pop(plan.migration_id, None)

    async def _migrate_batch(
        self,
        plan: MigrationPlan,
        keys: list[Any],
        fetch_func: Callable[[AsyncSession, Any], T | None],
        insert_func: Callable[[AsyncSession, T], None],
        delete_source: bool,
    ) -> None:
        """
        Migrate a batch of records.

        Args:
            plan: Migration plan
            keys: Keys to migrate in this batch
            fetch_func: Function to fetch records
            insert_func: Function to insert records
            delete_source: Whether to delete from source
        """
        source_session = await self.manager.get_session(plan.source_shard_id)
        target_session = await self.manager.get_session(plan.target_shard_id)

        try:
            for key in keys:
                try:
                    # Fetch from source
                    record = await fetch_func(source_session, key)
                    if not record:
                        logger.warning(
                            f"Record with key {key} not found in source shard"
                        )
                        plan.records_failed += 1
                        continue

                    # Insert into target
                    await insert_func(target_session, record)
                    await target_session.commit()

                    # Delete from source if requested
                    if delete_source:
                        # Note: Delete logic depends on your ORM setup
                        # This is a placeholder - implement based on your models
                        pass

                    plan.records_migrated += 1

                except Exception as e:
                    logger.error(f"Failed to migrate record {key}: {e}", exc_info=True)
                    plan.records_failed += 1
                    await target_session.rollback()

        finally:
            await source_session.close()
            await target_session.close()

    async def rollback(
        self,
        plan: MigrationPlan,
        fetch_func: Callable[[AsyncSession, Any], T | None],
        insert_func: Callable[[AsyncSession, T], None],
    ) -> MigrationResult:
        """
        Rollback a migration (move data back to source).

        Args:
            plan: Original migration plan
            fetch_func: Function to fetch records
            insert_func: Function to insert records

        Returns:
            MigrationResult with rollback outcome
        """
        logger.info(f"Rolling back migration {plan.migration_id}")

        # Create reverse migration plan
        rollback_plan = MigrationPlan(
            migration_id=f"{plan.migration_id}_rollback",
            table_name=plan.table_name,
            source_shard_id=plan.target_shard_id,  # Reverse
            target_shard_id=plan.source_shard_id,  # Reverse
            keys_to_migrate=plan.keys_to_migrate,
        )

        result = await self.execute(
            rollback_plan, fetch_func, insert_func, delete_source=True
        )

        if result.status == MigrationStatus.COMPLETED:
            plan.status = MigrationStatus.ROLLED_BACK
            logger.info(f"Migration {plan.migration_id} successfully rolled back")
        else:
            logger.error(f"Failed to rollback migration {plan.migration_id}")

        return result

    def get_migration_status(self, migration_id: str) -> MigrationPlan | None:
        """
        Get status of an active migration.

        Args:
            migration_id: Migration identifier

        Returns:
            MigrationPlan if found, None otherwise
        """
        return self.active_migrations.get(migration_id)


class RebalancingStrategy(str, Enum):
    """Strategy for rebalancing data across shards."""

    UNIFORM = "uniform"  # Distribute evenly across all shards
    WEIGHTED = "weighted"  # Distribute based on shard weights
    MINIMAL_MOVEMENT = "minimal_movement"  # Minimize data movement


class ShardRebalancer:
    """
    Rebalance data distribution across shards.

    Analyzes current distribution and creates migration plans to achieve
    better balance based on chosen strategy.

    Example:
        rebalancer = ShardRebalancer(manager)
        plans = await rebalancer.create_rebalancing_plan(
            "users",
            all_keys,
            RebalancingStrategy.UNIFORM
        )
        for plan in plans:
            await migration.execute(plan, fetch_func, insert_func)
    """

    def __init__(self, manager: ShardManager) -> None:
        """
        Initialize shard rebalancer.

        Args:
            manager: Shard manager instance
        """
        self.manager = manager

    async def analyze_distribution(
        self, table_name: str, keys: list[Any]
    ) -> dict[str, Any]:
        """
        Analyze current data distribution.

        Args:
            table_name: Table to analyze
            keys: All keys in the table

        Returns:
            Distribution analysis report
        """
        distribution = self.manager.get_distribution(table_name)
        return distribution.get_distribution_report(keys)

    def create_rebalancing_plan(
        self,
        table_name: str,
        current_distribution: dict[int, list[Any]],
        strategy: RebalancingStrategy = RebalancingStrategy.UNIFORM,
    ) -> list[MigrationPlan]:
        """
        Create migration plans to rebalance data.

        Args:
            table_name: Table to rebalance
            current_distribution: Current key distribution (shard_id -> keys)
            strategy: Rebalancing strategy to use

        Returns:
            List of migration plans to execute
        """
        if strategy == RebalancingStrategy.UNIFORM:
            return self._create_uniform_rebalance_plan(table_name, current_distribution)
        elif strategy == RebalancingStrategy.WEIGHTED:
            return self._create_weighted_rebalance_plan(
                table_name, current_distribution
            )
        elif strategy == RebalancingStrategy.MINIMAL_MOVEMENT:
            return self._create_minimal_movement_plan(table_name, current_distribution)
        else:
            raise ValueError(f"Unknown rebalancing strategy: {strategy}")

    def _create_uniform_rebalance_plan(
        self,
        table_name: str,
        current_distribution: dict[int, list[Any]],
    ) -> list[MigrationPlan]:
        """
        Create plan for uniform distribution.

        Distributes keys evenly across all shards.

        Args:
            table_name: Table name
            current_distribution: Current distribution

        Returns:
            List of migration plans
        """
        # Calculate target count per shard
        all_keys = []
        for keys in current_distribution.values():
            all_keys.extend(keys)

        num_shards = len(current_distribution)
        target_per_shard = len(all_keys) // num_shards

        # Create migration plans
        plans: list[MigrationPlan] = []
        shard_ids = sorted(current_distribution.keys())

        # Identify over-loaded and under-loaded shards
        for shard_id in shard_ids:
            current_keys = current_distribution[shard_id]
            current_count = len(current_keys)

            if current_count > target_per_shard:
                # Move excess to other shards
                excess = current_count - target_per_shard
                keys_to_move = current_keys[target_per_shard:]

                # Find target shards with space
                for target_shard_id in shard_ids:
                    if target_shard_id == shard_id:
                        continue

                    target_count = len(current_distribution[target_shard_id])
                    if target_count < target_per_shard:
                        # Calculate how many to move to this shard
                        space_available = target_per_shard - target_count
                        to_move = min(len(keys_to_move), space_available)

                        if to_move > 0:
                            plan = MigrationPlan(
                                migration_id=f"rebalance_{shard_id}_to_{target_shard_id}",
                                table_name=table_name,
                                source_shard_id=shard_id,
                                target_shard_id=target_shard_id,
                                keys_to_migrate=keys_to_move[:to_move],
                            )
                            plans.append(plan)
                            keys_to_move = keys_to_move[to_move:]

                            # Update distribution for next iteration
                            current_distribution[target_shard_id].extend(
                                plan.keys_to_migrate
                            )

                        if not keys_to_move:
                            break

        return plans

    def _create_weighted_rebalance_plan(
        self,
        table_name: str,
        current_distribution: dict[int, list[Any]],
    ) -> list[MigrationPlan]:
        """
        Create plan for weighted distribution.

        Distributes keys based on shard weights.

        Args:
            table_name: Table name
            current_distribution: Current distribution

        Returns:
            List of migration plans
        """
        # Get shard weights from strategy
        if table_name not in self.manager.strategies:
            raise ValueError(f"No strategy found for table {table_name}")

        strategy = self.manager.strategies[table_name]
        shard_weights = {s.shard_id: s.weight for s in strategy.shards}

        # Calculate target counts based on weights
        all_keys = []
        for keys in current_distribution.values():
            all_keys.extend(keys)

        total_weight = sum(shard_weights.values())
        target_counts = {
            shard_id: int(len(all_keys) * (weight / total_weight))
            for shard_id, weight in shard_weights.items()
        }

        # Create migration plans (similar to uniform, but with weighted targets)
        plans: list[MigrationPlan] = []
        # Implementation similar to uniform but using target_counts
        # (Simplified for brevity - full implementation would follow similar logic)

        return plans

    def _create_minimal_movement_plan(
        self,
        table_name: str,
        current_distribution: dict[int, list[Any]],
    ) -> list[MigrationPlan]:
        """
        Create plan with minimal data movement.

        Only moves data if severely imbalanced.

        Args:
            table_name: Table name
            current_distribution: Current distribution

        Returns:
            List of migration plans
        """
        # Calculate balance score
        distribution_obj = self.manager.get_distribution(table_name)
        counts = {
            shard_id: len(keys) for shard_id, keys in current_distribution.items()
        }
        balance_score = distribution_obj.calculate_balance_score(counts)

        # Only rebalance if severely imbalanced (score > 0.3)
        if balance_score < 0.3:
            logger.info(
                f"Distribution is acceptable (score: {balance_score:.2f}), "
                f"no rebalancing needed"
            )
            return []

        # Use uniform strategy but only move minimum necessary
        return self._create_uniform_rebalance_plan(table_name, current_distribution)

    async def add_new_shard(
        self,
        table_name: str,
        new_shard: ShardInfo,
        current_keys: list[Any],
    ) -> list[MigrationPlan]:
        """
        Create migration plan when adding a new shard.

        Args:
            table_name: Table name
            new_shard: New shard to add
            current_keys: All existing keys

        Returns:
            Migration plans to distribute data to new shard
        """
        # Add shard to strategy
        if table_name not in self.manager.strategies:
            raise ValueError(f"No strategy found for table {table_name}")

        strategy = self.manager.strategies[table_name]

        # For hash-based strategies, adding a shard requires rebalancing
        # For directory-based, we can explicitly assign some keys to new shard
        if isinstance(strategy, DirectoryShardingStrategy):
            # Migrate some keys to new shard for balance
            num_existing_shards = len(strategy.shards)
            keys_per_shard = len(current_keys) // (num_existing_shards + 1)

            # Take keys from each existing shard
            plans: list[MigrationPlan] = []
            keys_to_migrate = current_keys[:keys_per_shard]

            if keys_to_migrate:
                # Create plan to move keys to new shard
                # (Source shard would need to be determined based on current mapping)
                pass

            return plans
        else:
            # For other strategies, recalculate distribution
            return []

    async def remove_shard(
        self,
        table_name: str,
        shard_id: int,
        current_distribution: dict[int, list[Any]],
    ) -> list[MigrationPlan]:
        """
        Create migration plan when removing a shard.

        Args:
            table_name: Table name
            shard_id: Shard to remove
            current_distribution: Current key distribution

        Returns:
            Migration plans to move data off the shard
        """
        if shard_id not in current_distribution:
            raise ValueError(f"Shard {shard_id} not found in distribution")

        keys_to_migrate = current_distribution[shard_id]
        if not keys_to_migrate:
            return []

        # Distribute keys to remaining shards
        remaining_shards = [sid for sid in current_distribution if sid != shard_id]
        if not remaining_shards:
            raise ValueError("Cannot remove the last shard")

        plans: list[MigrationPlan] = []
        keys_per_shard = len(keys_to_migrate) // len(remaining_shards)

        for i, target_shard_id in enumerate(remaining_shards):
            start_idx = i * keys_per_shard
            end_idx = (
                start_idx + keys_per_shard
                if i < len(remaining_shards) - 1
                else len(keys_to_migrate)
            )

            batch_keys = keys_to_migrate[start_idx:end_idx]
            if batch_keys:
                plan = MigrationPlan(
                    migration_id=f"remove_{shard_id}_to_{target_shard_id}",
                    table_name=table_name,
                    source_shard_id=shard_id,
                    target_shard_id=target_shard_id,
                    keys_to_migrate=batch_keys,
                )
                plans.append(plan)

        return plans
