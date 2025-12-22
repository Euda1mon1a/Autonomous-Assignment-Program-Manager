"""
Sharding strategies for database partitioning.

This module provides various sharding strategies:
- Hash-based: Consistent hashing for uniform distribution
- Range-based: Partition by value ranges (e.g., date ranges, ID ranges)
- Directory-based: Explicit mapping of keys to shards
"""

import hashlib
from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Protocol, Tuple, Union

from pydantic import BaseModel, Field


class ShardInfo(BaseModel):
    """Information about a database shard."""

    shard_id: int = Field(..., description="Unique shard identifier")
    name: str = Field(..., description="Shard name")
    connection_string: str = Field(..., description="Database connection string")
    weight: float = Field(default=1.0, ge=0.0, description="Shard weight for load balancing")
    is_active: bool = Field(default=True, description="Whether shard is active")
    min_value: Optional[Any] = Field(default=None, description="Min value for range sharding")
    max_value: Optional[Any] = Field(default=None, description="Max value for range sharding")

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True


class ShardingStrategy(ABC):
    """
    Abstract base class for sharding strategies.

    All sharding strategies must implement the get_shard_id method to determine
    which shard a given key should be routed to.
    """

    def __init__(self, shards: List[ShardInfo]) -> None:
        """
        Initialize sharding strategy.

        Args:
            shards: List of available shards
        """
        self.shards = shards
        self._validate_shards()

    def _validate_shards(self) -> None:
        """
        Validate shard configuration.

        Raises:
            ValueError: If shard configuration is invalid
        """
        if not self.shards:
            raise ValueError("At least one shard must be configured")

        shard_ids = [s.shard_id for s in self.shards]
        if len(shard_ids) != len(set(shard_ids)):
            raise ValueError("Shard IDs must be unique")

    @abstractmethod
    def get_shard_id(self, key: Any) -> int:
        """
        Determine which shard a key should be routed to.

        Args:
            key: Sharding key (e.g., user_id, timestamp)

        Returns:
            int: Shard ID

        Raises:
            ValueError: If key is invalid or cannot be routed
        """
        pass

    def get_shard_info(self, shard_id: int) -> Optional[ShardInfo]:
        """
        Get information about a specific shard.

        Args:
            shard_id: Shard identifier

        Returns:
            ShardInfo if found, None otherwise
        """
        for shard in self.shards:
            if shard.shard_id == shard_id:
                return shard
        return None

    def get_active_shards(self) -> List[ShardInfo]:
        """
        Get all active shards.

        Returns:
            List of active shard information
        """
        return [s for s in self.shards if s.is_active]


class HashShardingStrategy(ShardingStrategy):
    """
    Hash-based sharding strategy using consistent hashing.

    Uses MD5 hashing to distribute keys uniformly across shards.
    Supports virtual nodes for better distribution.

    Example:
        strategy = HashShardingStrategy(shards, num_virtual_nodes=150)
        shard_id = strategy.get_shard_id("user_123")
    """

    def __init__(
        self,
        shards: List[ShardInfo],
        num_virtual_nodes: int = 150,
        hash_function: str = "md5",
    ) -> None:
        """
        Initialize hash-based sharding strategy.

        Args:
            shards: List of available shards
            num_virtual_nodes: Number of virtual nodes per physical shard
            hash_function: Hash function to use ('md5', 'sha1', 'sha256')
        """
        super().__init__(shards)
        self.num_virtual_nodes = num_virtual_nodes
        self.hash_function = hash_function
        self._build_hash_ring()

    def _build_hash_ring(self) -> None:
        """Build consistent hash ring with virtual nodes."""
        self.hash_ring: Dict[int, int] = {}

        for shard in self.get_active_shards():
            # Create virtual nodes for better distribution
            for i in range(self.num_virtual_nodes):
                virtual_key = f"{shard.shard_id}:{i}"
                hash_value = self._hash(virtual_key)
                self.hash_ring[hash_value] = shard.shard_id

        # Sort hash ring keys for binary search
        self.sorted_keys = sorted(self.hash_ring.keys())

    def _hash(self, key: str) -> int:
        """
        Hash a key to an integer value.

        Args:
            key: Key to hash

        Returns:
            Hash value as integer
        """
        if self.hash_function == "md5":
            hash_obj = hashlib.md5(key.encode())
        elif self.hash_function == "sha1":
            hash_obj = hashlib.sha1(key.encode())
        elif self.hash_function == "sha256":
            hash_obj = hashlib.sha256(key.encode())
        else:
            raise ValueError(f"Unsupported hash function: {self.hash_function}")

        return int(hash_obj.hexdigest(), 16)

    def get_shard_id(self, key: Any) -> int:
        """
        Get shard ID using consistent hashing.

        Args:
            key: Sharding key (converted to string for hashing)

        Returns:
            Shard ID

        Raises:
            ValueError: If no active shards available
        """
        if not self.sorted_keys:
            raise ValueError("No active shards available")

        # Convert key to string for hashing
        key_str = str(key)
        hash_value = self._hash(key_str)

        # Find the first hash ring node >= hash_value (clockwise)
        for ring_hash in self.sorted_keys:
            if ring_hash >= hash_value:
                return self.hash_ring[ring_hash]

        # Wrap around to the first node
        return self.hash_ring[self.sorted_keys[0]]

    def add_shard(self, shard: ShardInfo) -> None:
        """
        Add a new shard to the strategy.

        Args:
            shard: Shard to add
        """
        if shard not in self.shards:
            self.shards.append(shard)
            self._build_hash_ring()

    def remove_shard(self, shard_id: int) -> None:
        """
        Remove a shard from the strategy.

        Args:
            shard_id: ID of shard to remove
        """
        self.shards = [s for s in self.shards if s.shard_id != shard_id]
        self._build_hash_ring()


class RangeShardingStrategy(ShardingStrategy):
    """
    Range-based sharding strategy.

    Partitions data based on value ranges (e.g., date ranges, ID ranges).
    Useful for time-series data or sequential IDs.

    Example:
        # Shard by date range
        shards = [
            ShardInfo(shard_id=0, min_value=date(2020,1,1), max_value=date(2020,12,31)),
            ShardInfo(shard_id=1, min_value=date(2021,1,1), max_value=date(2021,12,31)),
        ]
        strategy = RangeShardingStrategy(shards)
        shard_id = strategy.get_shard_id(date(2021, 6, 15))
    """

    def __init__(self, shards: List[ShardInfo]) -> None:
        """
        Initialize range-based sharding strategy.

        Args:
            shards: List of shards with min_value and max_value set
        """
        super().__init__(shards)
        self._validate_ranges()

    def _validate_ranges(self) -> None:
        """
        Validate that all shards have valid ranges.

        Raises:
            ValueError: If ranges are invalid or overlapping
        """
        for shard in self.shards:
            if shard.min_value is None or shard.max_value is None:
                raise ValueError(
                    f"Shard {shard.shard_id} must have min_value and max_value defined"
                )

            if shard.min_value >= shard.max_value:
                raise ValueError(
                    f"Shard {shard.shard_id}: min_value must be less than max_value"
                )

        # Check for overlapping ranges
        active_shards = self.get_active_shards()
        for i, shard1 in enumerate(active_shards):
            for shard2 in active_shards[i + 1 :]:
                if self._ranges_overlap(shard1, shard2):
                    raise ValueError(
                        f"Shards {shard1.shard_id} and {shard2.shard_id} have overlapping ranges"
                    )

    def _ranges_overlap(self, shard1: ShardInfo, shard2: ShardInfo) -> bool:
        """
        Check if two shard ranges overlap.

        Args:
            shard1: First shard
            shard2: Second shard

        Returns:
            True if ranges overlap
        """
        return not (
            shard1.max_value < shard2.min_value or shard2.max_value < shard1.min_value
        )

    def get_shard_id(self, key: Any) -> int:
        """
        Get shard ID based on range.

        Args:
            key: Value to check (must be comparable with min/max values)

        Returns:
            Shard ID

        Raises:
            ValueError: If key doesn't fall within any shard range
        """
        for shard in self.get_active_shards():
            if shard.min_value <= key <= shard.max_value:
                return shard.shard_id

        raise ValueError(f"Key {key} does not fall within any shard range")

    def get_shard_ids_for_range(
        self, min_key: Any, max_key: Any
    ) -> List[int]:
        """
        Get all shard IDs that overlap with a given range.

        Useful for cross-shard queries on range data.

        Args:
            min_key: Minimum value of range
            max_key: Maximum value of range

        Returns:
            List of shard IDs that overlap with the range
        """
        shard_ids = []
        for shard in self.get_active_shards():
            # Check if ranges overlap
            if not (max_key < shard.min_value or min_key > shard.max_value):
                shard_ids.append(shard.shard_id)

        return shard_ids


class DirectoryShardingStrategy(ShardingStrategy):
    """
    Directory-based sharding strategy with explicit key-to-shard mapping.

    Maintains an explicit lookup table for routing keys to shards.
    Useful when sharding logic is complex or data distribution is uneven.

    Example:
        strategy = DirectoryShardingStrategy(shards)
        strategy.add_mapping("user_123", shard_id=0)
        strategy.add_mapping("user_456", shard_id=1)
        shard_id = strategy.get_shard_id("user_123")
    """

    def __init__(
        self,
        shards: List[ShardInfo],
        default_shard_id: Optional[int] = None,
        directory: Optional[Dict[str, int]] = None,
    ) -> None:
        """
        Initialize directory-based sharding strategy.

        Args:
            shards: List of available shards
            default_shard_id: Default shard for unmapped keys (None = raise error)
            directory: Initial key-to-shard mapping
        """
        super().__init__(shards)
        self.default_shard_id = default_shard_id
        self.directory: Dict[str, int] = directory or {}

        if default_shard_id is not None:
            if not self.get_shard_info(default_shard_id):
                raise ValueError(f"Default shard {default_shard_id} does not exist")

    def get_shard_id(self, key: Any) -> int:
        """
        Get shard ID from directory lookup.

        Args:
            key: Sharding key (converted to string for lookup)

        Returns:
            Shard ID

        Raises:
            ValueError: If key not found and no default shard configured
        """
        key_str = str(key)

        if key_str in self.directory:
            shard_id = self.directory[key_str]
            # Verify shard is still active
            shard = self.get_shard_info(shard_id)
            if shard and shard.is_active:
                return shard_id

        if self.default_shard_id is not None:
            return self.default_shard_id

        raise ValueError(f"Key {key} not found in directory and no default shard configured")

    def add_mapping(self, key: Any, shard_id: int) -> None:
        """
        Add a key-to-shard mapping.

        Args:
            key: Sharding key
            shard_id: Target shard ID

        Raises:
            ValueError: If shard does not exist
        """
        if not self.get_shard_info(shard_id):
            raise ValueError(f"Shard {shard_id} does not exist")

        key_str = str(key)
        self.directory[key_str] = shard_id

    def remove_mapping(self, key: Any) -> None:
        """
        Remove a key-to-shard mapping.

        Args:
            key: Sharding key
        """
        key_str = str(key)
        self.directory.pop(key_str, None)

    def bulk_add_mappings(self, mappings: Dict[Any, int]) -> None:
        """
        Add multiple key-to-shard mappings.

        Args:
            mappings: Dictionary of key -> shard_id

        Raises:
            ValueError: If any shard does not exist
        """
        # Validate all shards exist first
        for shard_id in set(mappings.values()):
            if not self.get_shard_info(shard_id):
                raise ValueError(f"Shard {shard_id} does not exist")

        # Add all mappings
        for key, shard_id in mappings.items():
            self.directory[str(key)] = shard_id

    def get_mappings_for_shard(self, shard_id: int) -> List[str]:
        """
        Get all keys mapped to a specific shard.

        Args:
            shard_id: Shard identifier

        Returns:
            List of keys mapped to the shard
        """
        return [key for key, sid in self.directory.items() if sid == shard_id]

    def migrate_keys(self, from_shard_id: int, to_shard_id: int) -> int:
        """
        Migrate all keys from one shard to another.

        Args:
            from_shard_id: Source shard ID
            to_shard_id: Target shard ID

        Returns:
            Number of keys migrated

        Raises:
            ValueError: If either shard does not exist
        """
        if not self.get_shard_info(from_shard_id):
            raise ValueError(f"Source shard {from_shard_id} does not exist")
        if not self.get_shard_info(to_shard_id):
            raise ValueError(f"Target shard {to_shard_id} does not exist")

        migrated_count = 0
        for key, shard_id in list(self.directory.items()):
            if shard_id == from_shard_id:
                self.directory[key] = to_shard_id
                migrated_count += 1

        return migrated_count
