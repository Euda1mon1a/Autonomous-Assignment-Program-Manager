"""
Search indexer service for document indexing and full-text search.

Provides comprehensive search indexing with:
- Document indexing with customizable field mappings
- Incremental index updates for real-time search
- Full reindex capability for schema changes
- Index versioning with zero-downtime migrations
- Field analyzers and tokenizers configuration
- Index aliases for seamless version switching
- Index health monitoring and diagnostics
- Bulk indexing for efficient batch operations

The indexer uses Redis as the backend with RediSearch-compatible operations,
but is designed to be backend-agnostic for future Elasticsearch/OpenSearch support.

Example:
    indexer = get_search_indexer()

    # Define document mapping
    mapping = DocumentMapping(
        index_name="person",
        fields={
            "name": FieldType.TEXT,
            "email": FieldType.TEXT,
            "pgy_level": FieldType.INTEGER,
        },
        analyzers={
            "name": FieldAnalyzer.STANDARD,
            "email": FieldAnalyzer.KEYWORD,
        }
    )

    # Create index
    await indexer.create_index(mapping)

    # Index document
    await indexer.index_document(
        "person",
        person_id,
        {"name": "John Doe", "email": "john@example.com", "pgy_level": 2}
    )

    # Search
    results = await indexer.search("person", "john")

    # Full reindex
    await indexer.reindex_all("person", person_iterator)
"""

import hashlib
import json
import logging
import time
from collections import defaultdict
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from threading import RLock
from typing import Any

import redis.asyncio as redis

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class FieldType(str, Enum):
    """
    Field types for document mapping.

    Determines how fields are indexed and searched.
    """

    TEXT = "text"  # Full-text search with tokenization
    KEYWORD = "keyword"  # Exact match, no tokenization
    INTEGER = "integer"  # Numeric field
    FLOAT = "float"  # Floating point numeric
    BOOLEAN = "boolean"  # Boolean field
    DATE = "date"  # Date/datetime field
    GEO = "geo"  # Geographic coordinates
    JSON = "json"  # Nested JSON object


class FieldAnalyzer(str, Enum):
    """
    Field analyzers for text processing.

    Controls how text fields are tokenized and normalized.
    """

    STANDARD = "standard"  # Standard tokenization (words, lowercase)
    KEYWORD = "keyword"  # No tokenization, exact match
    SIMPLE = "simple"  # Lowercase, split on non-letters
    WHITESPACE = "whitespace"  # Split on whitespace only
    ENGLISH = "english"  # English language analyzer with stemming
    LOWERCASE = "lowercase"  # Lowercase normalization only
    NGRAM = "ngram"  # N-gram tokenization for partial matching
    EDGE_NGRAM = "edge_ngram"  # Edge n-gram for autocomplete


class IndexStatus(str, Enum):
    """Index status states."""

    CREATING = "creating"  # Index being created
    ACTIVE = "active"  # Index is active and searchable
    INDEXING = "indexing"  # Bulk indexing in progress
    REINDEXING = "reindexing"  # Full reindex in progress
    MIGRATING = "migrating"  # Schema migration in progress
    READONLY = "readonly"  # Read-only mode
    FAILED = "failed"  # Index creation/operation failed
    DELETED = "deleted"  # Index has been deleted


@dataclass
class DocumentMapping:
    """
    Document field mapping configuration.

    Defines the schema for an index including field types,
    analyzers, and indexing options.

    Attributes:
        index_name: Name of the index
        fields: Dictionary mapping field names to FieldType
        analyzers: Dictionary mapping field names to FieldAnalyzer
        sortable_fields: List of fields that can be sorted on
        stored_fields: List of fields to store (retrieve in results)
        required_fields: List of required fields for validation
        boost_fields: Dictionary of field -> boost factor for relevance
        metadata: Additional index metadata
    """

    index_name: str
    fields: dict[str, FieldType]
    analyzers: dict[str, FieldAnalyzer] = field(default_factory=dict)
    sortable_fields: list[str] = field(default_factory=list)
    stored_fields: list[str] = field(default_factory=list)
    required_fields: list[str] = field(default_factory=list)
    boost_fields: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert mapping to dictionary."""
        return {
            "index_name": self.index_name,
            "fields": {k: v.value for k, v in self.fields.items()},
            "analyzers": {k: v.value for k, v in self.analyzers.items()},
            "sortable_fields": self.sortable_fields,
            "stored_fields": self.stored_fields,
            "required_fields": self.required_fields,
            "boost_fields": self.boost_fields,
            "metadata": self.metadata,
        }

    def get_schema_hash(self) -> str:
        """
        Generate hash of mapping schema for versioning.

        Returns:
            SHA256 hash of the mapping configuration
        """
        schema_str = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(schema_str.encode()).hexdigest()[:16]


@dataclass
class IndexVersion:
    """
    Index version information for schema evolution.

    Supports zero-downtime reindexing by maintaining multiple
    index versions with aliases.

    Attributes:
        index_name: Base index name
        version: Version number (incremented on schema changes)
        schema_hash: Hash of the index schema
        created_at: When this version was created
        status: Current status of this index version
        doc_count: Number of documents indexed
        mapping: The document mapping for this version
        alias_active: Whether this version is the active alias target
    """

    index_name: str
    version: int
    schema_hash: str
    created_at: datetime
    status: IndexStatus = IndexStatus.CREATING
    doc_count: int = 0
    mapping: DocumentMapping | None = None
    alias_active: bool = False

    @property
    def versioned_name(self) -> str:
        """Get versioned index name (e.g., 'person_v1')."""
        return f"{self.index_name}_v{self.version}"

    def to_dict(self) -> dict[str, Any]:
        """Convert version to dictionary."""
        return {
            "index_name": self.index_name,
            "version": self.version,
            "versioned_name": self.versioned_name,
            "schema_hash": self.schema_hash,
            "created_at": self.created_at.isoformat(),
            "status": self.status.value,
            "doc_count": self.doc_count,
            "alias_active": self.alias_active,
            "mapping": self.mapping.to_dict() if self.mapping else None,
        }


@dataclass
class IndexAlias:
    """
    Index alias for transparent versioning.

    Allows switching between index versions without updating client code.

    Attributes:
        alias_name: Alias name (typically the base index name)
        target_index: Current target versioned index
        previous_target: Previous target for rollback
        updated_at: When alias was last updated
    """

    alias_name: str
    target_index: str
    previous_target: str | None = None
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert alias to dictionary."""
        return {
            "alias_name": self.alias_name,
            "target_index": self.target_index,
            "previous_target": self.previous_target,
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class IndexHealth:
    """
    Index health status and diagnostics.

    Provides monitoring information for index health and performance.

    Attributes:
        index_name: Name of the index
        status: Current index status
        doc_count: Total number of documents
        index_size_bytes: Approximate index size in bytes
        last_index_time: When last document was indexed
        last_reindex_time: When index was last fully reindexed
        error_count: Number of indexing errors
        avg_index_time_ms: Average time to index a document
        search_count: Number of searches performed
        avg_search_time_ms: Average search time in milliseconds
        health_score: Overall health score 0-100
    """

    index_name: str
    status: IndexStatus
    doc_count: int = 0
    index_size_bytes: int = 0
    last_index_time: datetime | None = None
    last_reindex_time: datetime | None = None
    error_count: int = 0
    avg_index_time_ms: float = 0.0
    search_count: int = 0
    avg_search_time_ms: float = 0.0
    health_score: float = 100.0

    def to_dict(self) -> dict[str, Any]:
        """Convert health to dictionary."""
        return {
            "index_name": self.index_name,
            "status": self.status.value,
            "doc_count": self.doc_count,
            "index_size_bytes": self.index_size_bytes,
            "last_index_time": (
                self.last_index_time.isoformat() if self.last_index_time else None
            ),
            "last_reindex_time": (
                self.last_reindex_time.isoformat() if self.last_reindex_time else None
            ),
            "error_count": self.error_count,
            "avg_index_time_ms": round(self.avg_index_time_ms, 2),
            "search_count": self.search_count,
            "avg_search_time_ms": round(self.avg_search_time_ms, 2),
            "health_score": round(self.health_score, 2),
        }


@dataclass
class IndexingMetrics:
    """
    Metrics for indexing operations.

    Tracks performance and volume of indexing operations.
    """

    total_indexed: int = 0
    total_updated: int = 0
    total_deleted: int = 0
    total_errors: int = 0
    total_index_time_ms: float = 0.0
    total_search_time_ms: float = 0.0
    total_searches: int = 0
    bulk_operations: int = 0

    @property
    def avg_index_time_ms(self) -> float:
        """Average time per index operation."""
        total_ops = self.total_indexed + self.total_updated
        if total_ops == 0:
            return 0.0
        return self.total_index_time_ms / total_ops

    @property
    def avg_search_time_ms(self) -> float:
        """Average time per search operation."""
        if self.total_searches == 0:
            return 0.0
        return self.total_search_time_ms / self.total_searches

    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "total_indexed": self.total_indexed,
            "total_updated": self.total_updated,
            "total_deleted": self.total_deleted,
            "total_errors": self.total_errors,
            "total_index_time_ms": round(self.total_index_time_ms, 2),
            "avg_index_time_ms": round(self.avg_index_time_ms, 2),
            "total_searches": self.total_searches,
            "total_search_time_ms": round(self.total_search_time_ms, 2),
            "avg_search_time_ms": round(self.avg_search_time_ms, 2),
            "bulk_operations": self.bulk_operations,
        }


class SearchIndexer:
    """
    Comprehensive search indexing service.

    Provides full-text search indexing with versioning, bulk operations,
    and health monitoring. Uses Redis as the backend with a design that
    supports future migration to Elasticsearch/OpenSearch.

    Features:
    - Document indexing with custom field mappings
    - Incremental updates for real-time search
    - Full reindexing with zero downtime
    - Index versioning and schema evolution
    - Index aliases for transparent version switching
    - Field analyzers and tokenizers
    - Bulk indexing for efficient batch operations
    - Health monitoring and diagnostics
    - Metrics tracking

    Example:
        indexer = SearchIndexer(namespace="schedule")

        # Create index with mapping
        mapping = DocumentMapping(
            index_name="person",
            fields={"name": FieldType.TEXT, "email": FieldType.TEXT},
            analyzers={"name": FieldAnalyzer.STANDARD},
        )
        await indexer.create_index(mapping)

        # Index document
        await indexer.index_document("person", "123", {"name": "John Doe"})

        # Search
        results = await indexer.search("person", "john")
    """

    def __init__(
        self,
        namespace: str = "search",
        key_prefix: str = "search",
        enable_metrics: bool = True,
    ) -> None:
        """
        Initialize search indexer service.

        Args:
            namespace: Namespace for index organization
            key_prefix: Global prefix for all index keys
            enable_metrics: Enable metrics tracking
        """
        self.namespace = namespace
        self.key_prefix = key_prefix
        self.enable_metrics = enable_metrics

        # Redis connection
        self._redis: redis.Redis | None = None
        self._settings = get_settings()

        # Index metadata storage
        self._indices: dict[str, IndexVersion] = {}
        self._aliases: dict[str, IndexAlias] = {}
        self._health: dict[str, IndexHealth] = {}
        self._indices_lock = RLock()

        # Metrics
        self.metrics = IndexingMetrics()
        self._metrics_lock = RLock()

        # Document count tracking per index
        self._doc_counts: dict[str, int] = defaultdict(int)

    async def _get_redis(self) -> redis.Redis:
        """
        Get or create async Redis connection.

        Returns:
            Redis client instance

        Raises:
            ConnectionError: If Redis is unavailable
        """
        if self._redis is None:
            redis_url = self._settings.redis_url_with_password
            self._redis = redis.from_url(redis_url, decode_responses=True)

        return self._redis

    def _get_index_key(self, index_name: str, doc_id: str) -> str:
        """
        Generate Redis key for a document.

        Args:
            index_name: Index name
            doc_id: Document ID

        Returns:
            Redis key for the document
        """
        return f"{self.key_prefix}:{self.namespace}:{index_name}:doc:{doc_id}"

    def _get_index_metadata_key(self, index_name: str) -> str:
        """
        Generate Redis key for index metadata.

        Args:
            index_name: Index name

        Returns:
            Redis key for index metadata
        """
        return f"{self.key_prefix}:{self.namespace}:{index_name}:metadata"

    def _get_index_mapping_key(self, index_name: str) -> str:
        """
        Generate Redis key for index mapping.

        Args:
            index_name: Index name

        Returns:
            Redis key for index mapping
        """
        return f"{self.key_prefix}:{self.namespace}:{index_name}:mapping"

    def _get_index_docs_set_key(self, index_name: str) -> str:
        """
        Generate Redis key for set of document IDs in an index.

        Args:
            index_name: Index name

        Returns:
            Redis key for document IDs set
        """
        return f"{self.key_prefix}:{self.namespace}:{index_name}:docs"

    def _get_field_index_key(self, index_name: str, field: str, value: str) -> str:
        """
        Generate Redis key for field inverted index.

        Args:
            index_name: Index name
            field: Field name
            value: Field value (token)

        Returns:
            Redis key for field index
        """
        return f"{self.key_prefix}:{self.namespace}:{index_name}:field:{field}:{value}"

    async def create_index(
        self,
        mapping: DocumentMapping,
        version: int | None = None,
    ) -> IndexVersion:
        """
        Create a new index with the specified mapping.

        If version is not specified, creates version 1 or increments
        the latest version if schema has changed.

        Args:
            mapping: Document mapping configuration
            version: Optional specific version number

        Returns:
            IndexVersion object for the created index

        Raises:
            ValueError: If index with same schema already exists

        Example:
            mapping = DocumentMapping(
                index_name="person",
                fields={"name": FieldType.TEXT},
            )
            version = await indexer.create_index(mapping)
        """
        start_time = time.time()

        try:
            redis_client = await self._get_redis()
            index_name = mapping.index_name
            schema_hash = mapping.get_schema_hash()

            # Determine version number
            if version is None:
                # Get latest version
                existing_versions = await self._get_index_versions(index_name)
                if existing_versions:
                    latest = max(existing_versions, key=lambda v: v.version)
                    # Check if schema changed
                    if latest.schema_hash == schema_hash:
                        logger.info(
                            f"Index '{index_name}' already exists with same schema"
                        )
                        return latest
                    version = latest.version + 1
                else:
                    version = 1

                    # Create index version
            index_version = IndexVersion(
                index_name=index_name,
                version=version,
                schema_hash=schema_hash,
                created_at=datetime.utcnow(),
                status=IndexStatus.CREATING,
                mapping=mapping,
            )

            # Store mapping
            mapping_key = self._get_index_mapping_key(index_version.versioned_name)
            await redis_client.set(
                mapping_key,
                json.dumps(mapping.to_dict()),
            )

            # Store version metadata
            metadata_key = self._get_index_metadata_key(index_version.versioned_name)
            await redis_client.hset(
                metadata_key,
                mapping={
                    "version": version,
                    "schema_hash": schema_hash,
                    "created_at": index_version.created_at.isoformat(),
                    "status": IndexStatus.ACTIVE.value,
                    "doc_count": 0,
                },
            )

            # Update in-memory tracking
            with self._indices_lock:
                self._indices[index_version.versioned_name] = index_version
                index_version.status = IndexStatus.ACTIVE

                # Create/update alias to point to new version
            await self._update_alias(index_name, index_version.versioned_name)

            # Initialize health monitoring
            self._health[index_version.versioned_name] = IndexHealth(
                index_name=index_version.versioned_name,
                status=IndexStatus.ACTIVE,
            )

            duration_ms = (time.time() - start_time) * 1000
            logger.info(
                f"Created index '{index_version.versioned_name}' "
                f"with schema hash {schema_hash} in {duration_ms:.2f}ms"
            )

            return index_version

        except redis.ConnectionError as e:
            logger.error(f"Redis connection error creating index: {e}", exc_info=True)
            raise
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.error(
                f"Data serialization error creating index '{mapping.index_name}': {e}",
                exc_info=True,
            )
            raise
        except OSError as e:
            logger.error(
                f"File I/O error creating index '{mapping.index_name}': {e}",
                exc_info=True,
            )
            raise

    async def index_document(
        self,
        index_name: str,
        doc_id: str,
        document: dict[str, Any],
        use_alias: bool = True,
    ) -> bool:
        """
        Index a single document.

        Args:
            index_name: Index name (or alias)
            doc_id: Unique document identifier
            document: Document data as dictionary
            use_alias: If True, resolve index name via alias

        Returns:
            True if indexed successfully

        Raises:
            ValueError: If document validation fails

        Example:
            success = await indexer.index_document(
                "person",
                "123",
                {"name": "John Doe", "email": "john@example.com"}
            )
        """
        start_time = time.time()

        try:
            redis_client = await self._get_redis()

            # Resolve alias to actual index
            if use_alias:
                actual_index = await self._resolve_alias(index_name)
            else:
                actual_index = index_name

                # Get mapping for validation
            mapping = await self._get_mapping(actual_index)
            if mapping:
                self._validate_document(document, mapping)

                # Store document
            doc_key = self._get_index_key(actual_index, doc_id)
            await redis_client.set(doc_key, json.dumps(document))

            # Add to document set
            docs_set_key = self._get_index_docs_set_key(actual_index)
            is_new = await redis_client.sadd(docs_set_key, doc_id)

            # Index fields for search
            if mapping:
                await self._index_fields(actual_index, doc_id, document, mapping)

                # Update document count
            if is_new:
                await self._increment_doc_count(actual_index)

                # Update metrics
            duration_ms = (time.time() - start_time) * 1000
            if self.enable_metrics:
                with self._metrics_lock:
                    if is_new:
                        self.metrics.total_indexed += 1
                    else:
                        self.metrics.total_updated += 1
                    self.metrics.total_index_time_ms += duration_ms

                    # Update health
            if actual_index in self._health:
                health = self._health[actual_index]
                health.last_index_time = datetime.utcnow()
                health.doc_count = self._doc_counts[actual_index]
                # Update rolling average
                total_ops = self.metrics.total_indexed + self.metrics.total_updated
                if total_ops > 0:
                    health.avg_index_time_ms = self.metrics.avg_index_time_ms

            logger.debug(
                f"Indexed document '{doc_id}' in index '{actual_index}' "
                f"in {duration_ms:.2f}ms"
            )

            return True

        except redis.ConnectionError as e:
            logger.warning(f"Redis connection error indexing document: {e}")
            if self.enable_metrics:
                with self._metrics_lock:
                    self.metrics.total_errors += 1
            return False
        except Exception as e:
            logger.error(
                f"Error indexing document '{doc_id}' in index '{index_name}': {e}",
                exc_info=True,
            )
            if self.enable_metrics:
                with self._metrics_lock:
                    self.metrics.total_errors += 1
            return False

    async def bulk_index(
        self,
        index_name: str,
        documents: list[tuple[str, dict[str, Any]]],
        batch_size: int = 100,
        use_alias: bool = True,
    ) -> dict[str, Any]:
        """
        Bulk index multiple documents efficiently.

        Args:
            index_name: Index name (or alias)
            documents: List of (doc_id, document) tuples
            batch_size: Number of documents per batch
            use_alias: If True, resolve index name via alias

        Returns:
            Dictionary with indexing results:
                - total: Total documents processed
                - indexed: Number of new documents
                - updated: Number of updated documents
                - errors: Number of errors
                - duration_ms: Total duration in milliseconds

        Example:
            docs = [
                ("1", {"name": "John"}),
                ("2", {"name": "Jane"}),
            ]
            result = await indexer.bulk_index("person", docs)
        """
        start_time = time.time()

        if not documents:
            return {
                "total": 0,
                "indexed": 0,
                "updated": 0,
                "errors": 0,
                "duration_ms": 0.0,
            }

        try:
            redis_client = await self._get_redis()

            # Resolve alias
            if use_alias:
                actual_index = await self._resolve_alias(index_name)
            else:
                actual_index = index_name

                # Get mapping
            mapping = await self._get_mapping(actual_index)

            indexed_count = 0
            updated_count = 0
            error_count = 0

            # Process in batches
            for i in range(0, len(documents), batch_size):
                batch = documents[i : i + batch_size]

                try:
                    # Use pipeline for efficiency
                    pipe = redis_client.pipeline()

                    for doc_id, document in batch:
                        # Validate document
                        if mapping:
                            try:
                                self._validate_document(document, mapping)
                            except ValueError as e:
                                logger.warning(
                                    f"Validation failed for doc '{doc_id}': {e}"
                                )
                                error_count += 1
                                continue

                                # Store document
                        doc_key = self._get_index_key(actual_index, doc_id)
                        pipe.set(doc_key, json.dumps(document))

                        # Add to document set
                        docs_set_key = self._get_index_docs_set_key(actual_index)
                        pipe.sadd(docs_set_key, doc_id)

                        # Execute batch
                    await pipe.execute()

                    # Index fields (separate pass for simplicity)
                    for doc_id, document in batch:
                        if mapping:
                            try:
                                await self._index_fields(
                                    actual_index, doc_id, document, mapping
                                )
                                indexed_count += 1
                            except (redis.ConnectionError, redis.RedisError) as e:
                                logger.warning(
                                    f"Redis error indexing fields for doc '{doc_id}': {e}",
                                    exc_info=True,
                                )
                                error_count += 1
                            except (ValueError, TypeError) as e:
                                logger.warning(
                                    f"Data validation error indexing fields for doc '{doc_id}': {e}",
                                    exc_info=True,
                                )
                                error_count += 1

                except (redis.ConnectionError, redis.RedisError) as e:
                    logger.error(f"Redis error processing batch: {e}", exc_info=True)
                    error_count += len(batch)
                except (json.JSONDecodeError, ValueError, TypeError) as e:
                    logger.error(
                        f"Data validation error processing batch: {e}", exc_info=True
                    )
                    error_count += len(batch)

                    # Update document count
            total_docs = await redis_client.scard(
                self._get_index_docs_set_key(actual_index)
            )
            self._doc_counts[actual_index] = total_docs

            # Update metadata
            metadata_key = self._get_index_metadata_key(actual_index)
            await redis_client.hset(
                metadata_key,
                "doc_count",
                total_docs,
            )

            duration_ms = (time.time() - start_time) * 1000

            # Update metrics
            if self.enable_metrics:
                with self._metrics_lock:
                    self.metrics.total_indexed += indexed_count
                    self.metrics.total_errors += error_count
                    self.metrics.bulk_operations += 1
                    self.metrics.total_index_time_ms += duration_ms

                    # Update health
            if actual_index in self._health:
                health = self._health[actual_index]
                health.last_index_time = datetime.utcnow()
                health.doc_count = total_docs
                health.error_count += error_count

            result = {
                "total": len(documents),
                "indexed": indexed_count,
                "updated": updated_count,
                "errors": error_count,
                "duration_ms": round(duration_ms, 2),
            }

            logger.info(
                f"Bulk indexed {indexed_count} documents in index '{actual_index}' "
                f"in {duration_ms:.2f}ms ({error_count} errors)"
            )

            return result

        except redis.ConnectionError as e:
            logger.error(
                f"Redis connection error during bulk index: {e}", exc_info=True
            )
            raise
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.error(f"Data validation error during bulk index: {e}", exc_info=True)
            raise

    async def reindex_all(
        self,
        index_name: str,
        document_iterator: AsyncIterator[tuple[str, dict[str, Any]]],
        batch_size: int = 100,
        new_mapping: DocumentMapping | None = None,
    ) -> dict[str, Any]:
        """
        Full reindex of all documents.

        Creates a new index version if mapping is provided, performs bulk
        indexing, then switches the alias. Enables zero-downtime reindexing.

        Args:
            index_name: Index name
            document_iterator: Async iterator yielding (doc_id, document) tuples
            batch_size: Batch size for bulk operations
            new_mapping: Optional new mapping (creates new version)

        Returns:
            Dictionary with reindexing results:
                - new_version: New index version (if created)
                - total_indexed: Total documents indexed
                - duration_ms: Total duration
                - errors: Number of errors

        Example:
            async def get_all_people():
                for person in db.query(Person).all():
                    yield (str(person.id), person_to_dict(person))

            result = await indexer.reindex_all("person", get_all_people())
        """
        start_time = time.time()

        try:
            # Create new version if mapping provided
            if new_mapping:
                new_version = await self.create_index(new_mapping)
                target_index = new_version.versioned_name
                logger.info(f"Created new index version: {target_index}")
            else:
                # Reindex into current version
                target_index = await self._resolve_alias(index_name)
                # Clear existing data
                await self._clear_index(target_index)

                # Update status to reindexing
            if target_index in self._health:
                self._health[target_index].status = IndexStatus.REINDEXING

                # Bulk index all documents
            batch = []
            total_indexed = 0
            total_errors = 0

            async for doc_id, document in document_iterator:
                batch.append((doc_id, document))

                if len(batch) >= batch_size:
                    result = await self.bulk_index(
                        target_index,
                        batch,
                        batch_size=batch_size,
                        use_alias=False,
                    )
                    total_indexed += result["indexed"]
                    total_errors += result["errors"]
                    batch = []

                    # Index remaining documents
            if batch:
                result = await self.bulk_index(
                    target_index,
                    batch,
                    batch_size=batch_size,
                    use_alias=False,
                )
                total_indexed += result["indexed"]
                total_errors += result["errors"]

                # Switch alias if new version was created
            if new_mapping:
                await self._update_alias(index_name, target_index)

                # Update status
            if target_index in self._health:
                health = self._health[target_index]
                health.status = IndexStatus.ACTIVE
                health.last_reindex_time = datetime.utcnow()
                health.doc_count = total_indexed

            duration_ms = (time.time() - start_time) * 1000

            result = {
                "new_version": target_index if new_mapping else None,
                "total_indexed": total_indexed,
                "errors": total_errors,
                "duration_ms": round(duration_ms, 2),
            }

            logger.info(
                f"Reindexed {total_indexed} documents into '{target_index}' "
                f"in {duration_ms:.2f}ms ({total_errors} errors)"
            )

            return result

        except (redis.ConnectionError, redis.RedisError) as e:
            logger.error(f"Redis error during reindex: {e}", exc_info=True)
            raise
        except (ValueError, TypeError) as e:
            logger.error(f"Data validation error during reindex: {e}", exc_info=True)
            raise

    async def search(
        self,
        index_name: str,
        query: str,
        fields: list[str] | None = None,
        limit: int = 10,
        offset: int = 0,
        use_alias: bool = True,
    ) -> dict[str, Any]:
        """
        Search documents in an index.

        Performs full-text search with basic relevance ranking.

        Args:
            index_name: Index name (or alias)
            query: Search query string
            fields: Fields to search (default: all text fields)
            limit: Maximum results to return
            offset: Offset for pagination
            use_alias: If True, resolve index name via alias

        Returns:
            Dictionary with search results:
                - total: Total matching documents
                - hits: List of matching documents
                - query: Original query
                - duration_ms: Search duration

        Example:
            results = await indexer.search("person", "john doe", limit=20)
            for hit in results["hits"]:
                print(hit["_id"], hit["_source"]["name"])
        """
        start_time = time.time()

        try:
            redis_client = await self._get_redis()

            # Resolve alias
            if use_alias:
                actual_index = await self._resolve_alias(index_name)
            else:
                actual_index = index_name

                # Tokenize query
            tokens = self._tokenize(query)

            # Get mapping to determine searchable fields
            mapping = await self._get_mapping(actual_index)
            if not mapping:
                return {
                    "total": 0,
                    "hits": [],
                    "query": query,
                    "duration_ms": 0.0,
                }

                # Determine which fields to search
            if fields is None:
                # Search all text fields
                search_fields = [
                    field
                    for field, field_type in mapping.fields.items()
                    if field_type == FieldType.TEXT
                ]
            else:
                search_fields = fields

                # Find matching documents
            doc_scores: dict[str, float] = defaultdict(float)

            for token in tokens:
                for field in search_fields:
                    # Get documents containing this token in this field
                    field_key = self._get_field_index_key(actual_index, field, token)
                    doc_ids = await redis_client.smembers(field_key)

                    # Score documents (simple TF-based scoring)
                    boost = mapping.boost_fields.get(field, 1.0)
                    for doc_id in doc_ids:
                        doc_scores[doc_id] += 1.0 * boost

                        # Sort by score
            sorted_docs = sorted(
                doc_scores.items(),
                key=lambda x: x[1],
                reverse=True,
            )

            # Apply pagination
            paginated = sorted_docs[offset : offset + limit]

            # Retrieve documents
            hits = []
            for doc_id, score in paginated:
                doc_key = self._get_index_key(actual_index, doc_id)
                doc_data = await redis_client.get(doc_key)
                if doc_data:
                    hits.append(
                        {
                            "_id": doc_id,
                            "_score": score,
                            "_source": json.loads(doc_data),
                        }
                    )

            duration_ms = (time.time() - start_time) * 1000

            # Update metrics
            if self.enable_metrics:
                with self._metrics_lock:
                    self.metrics.total_searches += 1
                    self.metrics.total_search_time_ms += duration_ms

                    # Update health
            if actual_index in self._health:
                health = self._health[actual_index]
                health.search_count += 1
                health.avg_search_time_ms = self.metrics.avg_search_time_ms

            result = {
                "total": len(sorted_docs),
                "hits": hits,
                "query": query,
                "duration_ms": round(duration_ms, 2),
            }

            logger.debug(
                f"Search '{query}' in index '{actual_index}' found {len(sorted_docs)} "
                f"results in {duration_ms:.2f}ms"
            )

            return result

        except redis.ConnectionError as e:
            logger.warning(f"Redis connection error during search: {e}", exc_info=True)
            return {
                "total": 0,
                "hits": [],
                "query": query,
                "duration_ms": 0.0,
                "error": str(e),
            }
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.error(f"Data parsing error during search: {e}", exc_info=True)
            return {
                "total": 0,
                "hits": [],
                "query": query,
                "duration_ms": 0.0,
                "error": str(e),
            }

    async def delete_document(
        self,
        index_name: str,
        doc_id: str,
        use_alias: bool = True,
    ) -> bool:
        """
        Delete a document from the index.

        Args:
            index_name: Index name (or alias)
            doc_id: Document ID to delete
            use_alias: If True, resolve index name via alias

        Returns:
            True if deleted successfully

        Example:
            success = await indexer.delete_document("person", "123")
        """
        try:
            redis_client = await self._get_redis()

            # Resolve alias
            if use_alias:
                actual_index = await self._resolve_alias(index_name)
            else:
                actual_index = index_name

                # Delete document
            doc_key = self._get_index_key(actual_index, doc_id)
            deleted = await redis_client.delete(doc_key)

            # Remove from document set
            docs_set_key = self._get_index_docs_set_key(actual_index)
            await redis_client.srem(docs_set_key, doc_id)

            # Update metrics
            if deleted > 0:
                if self.enable_metrics:
                    with self._metrics_lock:
                        self.metrics.total_deleted += 1

                        # Update document count
                await self._decrement_doc_count(actual_index)

                logger.debug(f"Deleted document '{doc_id}' from index '{actual_index}'")
                return True

            return False

        except redis.ConnectionError as e:
            logger.warning(
                f"Redis connection error deleting document: {e}", exc_info=True
            )
            return False
        except redis.RedisError as e:
            logger.error(f"Redis error deleting document: {e}", exc_info=True)
            return False

    async def get_index_health(self, index_name: str) -> IndexHealth | None:
        """
        Get health status for an index.

        Args:
            index_name: Index name

        Returns:
            IndexHealth object or None if index doesn't exist

        Example:
            health = await indexer.get_index_health("person")
            print(f"Documents: {health.doc_count}")
            print(f"Health score: {health.health_score}")
        """
        try:
            # Resolve alias
            actual_index = await self._resolve_alias(index_name)

            if actual_index not in self._health:
                # Try to load from Redis
                redis_client = await self._get_redis()
                metadata_key = self._get_index_metadata_key(actual_index)
                metadata = await redis_client.hgetall(metadata_key)

                if not metadata:
                    return None

                    # Create health object
                health = IndexHealth(
                    index_name=actual_index,
                    status=IndexStatus(metadata.get("status", "active")),
                    doc_count=int(metadata.get("doc_count", 0)),
                )
                self._health[actual_index] = health

            health = self._health[actual_index]

            # Calculate health score
            health.health_score = self._calculate_health_score(health)

            return health

        except (redis.ConnectionError, redis.RedisError) as e:
            logger.error(f"Redis error getting index health: {e}", exc_info=True)
            return None
        except (ValueError, KeyError) as e:
            logger.error(f"Data parsing error getting index health: {e}", exc_info=True)
            return None

    async def get_all_indices(self) -> list[dict[str, Any]]:
        """
        Get information about all indices.

        Returns:
            List of index information dictionaries

        Example:
            indices = await indexer.get_all_indices()
            for index in indices:
                print(f"{index['name']}: {index['doc_count']} docs")
        """
        try:
            redis_client = await self._get_redis()

            # Find all index metadata keys
            pattern = f"{self.key_prefix}:{self.namespace}:*:metadata"
            cursor = 0
            indices = []

            while True:
                cursor, keys = await redis_client.scan(
                    cursor,
                    match=pattern,
                    count=100,
                )

                for key in keys:
                    metadata = await redis_client.hgetall(key)
                    if metadata:
                        # Extract index name from key
                        index_name = key.split(":")[-2]
                        indices.append(
                            {
                                "name": index_name,
                                "version": int(metadata.get("version", 0)),
                                "doc_count": int(metadata.get("doc_count", 0)),
                                "status": metadata.get("status", "unknown"),
                                "created_at": metadata.get("created_at"),
                            }
                        )

                if cursor == 0:
                    break

            return indices

        except (redis.ConnectionError, redis.RedisError) as e:
            logger.error(f"Redis error getting all indices: {e}", exc_info=True)
            return []
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Data parsing error getting all indices: {e}", exc_info=True)
            return []

    def get_metrics(self) -> dict[str, Any]:
        """
        Get indexing metrics.

        Returns:
            Dictionary with all metrics

        Example:
            metrics = indexer.get_metrics()
            print(f"Total indexed: {metrics['total_indexed']}")
        """
        with self._metrics_lock:
            return self.metrics.to_dict()

    def reset_metrics(self) -> None:
        """Reset all metrics to zero."""
        with self._metrics_lock:
            self.metrics = IndexingMetrics()
        logger.debug("Reset indexing metrics")

        # Internal helper methods

    async def _get_index_versions(self, index_name: str) -> list[IndexVersion]:
        """Get all versions of an index."""
        try:
            redis_client = await self._get_redis()

            # Find all versioned indices
            pattern = f"{self.key_prefix}:{self.namespace}:{index_name}_v*:metadata"
            cursor = 0
            versions = []

            while True:
                cursor, keys = await redis_client.scan(
                    cursor,
                    match=pattern,
                    count=100,
                )

                for key in keys:
                    metadata = await redis_client.hgetall(key)
                    if metadata:
                        version = IndexVersion(
                            index_name=index_name,
                            version=int(metadata.get("version", 0)),
                            schema_hash=metadata.get("schema_hash", ""),
                            created_at=datetime.fromisoformat(
                                metadata.get(
                                    "created_at", datetime.utcnow().isoformat()
                                )
                            ),
                            status=IndexStatus(metadata.get("status", "active")),
                            doc_count=int(metadata.get("doc_count", 0)),
                        )
                        versions.append(version)

                if cursor == 0:
                    break

            return versions

        except (redis.ConnectionError, redis.RedisError) as e:
            logger.error(f"Redis error getting index versions: {e}", exc_info=True)
            return []
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(
                f"Data parsing error getting index versions: {e}", exc_info=True
            )
            return []

    async def _update_alias(self, alias_name: str, target_index: str) -> None:
        """Update index alias to point to a new target."""
        try:
            redis_client = await self._get_redis()

            # Get current alias if it exists
            alias_key = f"{self.key_prefix}:{self.namespace}:alias:{alias_name}"
            current_target = await redis_client.get(alias_key)

            # Create alias object
            alias = IndexAlias(
                alias_name=alias_name,
                target_index=target_index,
                previous_target=current_target,
                updated_at=datetime.utcnow(),
            )

            # Update alias
            await redis_client.set(alias_key, target_index)

            # Store in memory
            with self._indices_lock:
                self._aliases[alias_name] = alias

            logger.info(f"Updated alias '{alias_name}' to point to '{target_index}'")

        except (redis.ConnectionError, redis.RedisError) as e:
            logger.error(f"Redis error updating alias: {e}", exc_info=True)
            raise

    async def _resolve_alias(self, index_name: str) -> str:
        """Resolve index alias to actual index name."""
        try:
            redis_client = await self._get_redis()

            alias_key = f"{self.key_prefix}:{self.namespace}:alias:{index_name}"
            target = await redis_client.get(alias_key)

            if target:
                return target

                # No alias, assume it's a direct index name
            return index_name

        except (redis.ConnectionError, redis.RedisError) as e:
            logger.error(f"Redis error resolving alias: {e}", exc_info=True)
            return index_name

    async def _get_mapping(self, index_name: str) -> DocumentMapping | None:
        """Get mapping for an index."""
        try:
            redis_client = await self._get_redis()

            mapping_key = self._get_index_mapping_key(index_name)
            mapping_data = await redis_client.get(mapping_key)

            if not mapping_data:
                return None

            mapping_dict = json.loads(mapping_data)

            # Reconstruct DocumentMapping
            mapping = DocumentMapping(
                index_name=mapping_dict["index_name"],
                fields={
                    k: FieldType(v) for k, v in mapping_dict.get("fields", {}).items()
                },
                analyzers={
                    k: FieldAnalyzer(v)
                    for k, v in mapping_dict.get("analyzers", {}).items()
                },
                sortable_fields=mapping_dict.get("sortable_fields", []),
                stored_fields=mapping_dict.get("stored_fields", []),
                required_fields=mapping_dict.get("required_fields", []),
                boost_fields=mapping_dict.get("boost_fields", {}),
                metadata=mapping_dict.get("metadata", {}),
            )

            return mapping

        except (redis.ConnectionError, redis.RedisError) as e:
            logger.error(f"Redis error getting mapping: {e}", exc_info=True)
            return None
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.error(f"Data parsing error getting mapping: {e}", exc_info=True)
            return None

    def _validate_document(
        self, document: dict[str, Any], mapping: DocumentMapping
    ) -> None:
        """
        Validate document against mapping.

        Raises:
            ValueError: If validation fails
        """
        # Check required fields
        for field in mapping.required_fields:
            if field not in document:
                raise ValueError(f"Required field '{field}' missing from document")

                # Check field types (basic validation)
        for field, value in document.items():
            if field in mapping.fields:
                field_type = mapping.fields[field]
                # Basic type checking
                if field_type == FieldType.INTEGER and not isinstance(value, int):
                    if not (isinstance(value, str) and value.isdigit()):
                        raise ValueError(
                            f"Field '{field}' expects integer, got {type(value).__name__}"
                        )
                elif field_type == FieldType.BOOLEAN and not isinstance(value, bool):
                    raise ValueError(
                        f"Field '{field}' expects boolean, got {type(value).__name__}"
                    )

    async def _index_fields(
        self,
        index_name: str,
        doc_id: str,
        document: dict[str, Any],
        mapping: DocumentMapping,
    ) -> None:
        """Index individual fields for search."""
        try:
            redis_client = await self._get_redis()

            pipe = redis_client.pipeline()

            for field, value in document.items():
                if field not in mapping.fields:
                    continue

                field_type = mapping.fields[field]

                # Only index searchable fields
                if field_type in (FieldType.TEXT, FieldType.KEYWORD):
                    # Get analyzer
                    analyzer = mapping.analyzers.get(field, FieldAnalyzer.STANDARD)

                    # Tokenize value
                    if field_type == FieldType.TEXT:
                        tokens = self._tokenize(str(value), analyzer)
                    else:
                        tokens = [str(value).lower()]

                        # Add to inverted index
                    for token in tokens:
                        field_key = self._get_field_index_key(index_name, field, token)
                        pipe.sadd(field_key, doc_id)

            await pipe.execute()

        except (redis.ConnectionError, redis.RedisError) as e:
            logger.error(f"Redis error indexing fields: {e}", exc_info=True)
            raise
        except (ValueError, TypeError) as e:
            logger.error(f"Data validation error indexing fields: {e}", exc_info=True)
            raise

    def _tokenize(
        self,
        text: str,
        analyzer: FieldAnalyzer = FieldAnalyzer.STANDARD,
    ) -> list[str]:
        """
        Tokenize text based on analyzer.

        Args:
            text: Text to tokenize
            analyzer: Analyzer to use

        Returns:
            List of tokens
        """
        if analyzer == FieldAnalyzer.KEYWORD:
            return [text.lower()]

            # Standard tokenization: lowercase, split on non-alphanumeric
        text = text.lower()

        if analyzer == FieldAnalyzer.WHITESPACE:
            return text.split()

            # Standard: split on non-alphanumeric
        import re

        tokens = re.findall(r"\w+", text)

        # Filter out very short tokens
        tokens = [t for t in tokens if len(t) > 1]

        return tokens

    async def _clear_index(self, index_name: str) -> None:
        """Clear all documents from an index."""
        try:
            redis_client = await self._get_redis()

            # Get all document IDs
            docs_set_key = self._get_index_docs_set_key(index_name)
            doc_ids = await redis_client.smembers(docs_set_key)

            if doc_ids:
                # Delete all documents
                doc_keys = [
                    self._get_index_key(index_name, doc_id) for doc_id in doc_ids
                ]
                await redis_client.delete(*doc_keys)

                # Clear document set
                await redis_client.delete(docs_set_key)

                # Clear field indices
                pattern = f"{self.key_prefix}:{self.namespace}:{index_name}:field:*"
                cursor = 0
                while True:
                    cursor, keys = await redis_client.scan(
                        cursor, match=pattern, count=100
                    )
                    if keys:
                        await redis_client.delete(*keys)
                    if cursor == 0:
                        break

            self._doc_counts[index_name] = 0

            logger.info(f"Cleared index '{index_name}'")

        except (redis.ConnectionError, redis.RedisError) as e:
            logger.error(f"Redis error clearing index: {e}", exc_info=True)
            raise

    async def _increment_doc_count(self, index_name: str) -> None:
        """Increment document count for an index."""
        self._doc_counts[index_name] += 1

        try:
            redis_client = await self._get_redis()
            metadata_key = self._get_index_metadata_key(index_name)
            await redis_client.hincrby(metadata_key, "doc_count", 1)
        except (redis.ConnectionError, redis.RedisError) as e:
            logger.error(f"Redis error incrementing doc count: {e}", exc_info=True)

    async def _decrement_doc_count(self, index_name: str) -> None:
        """Decrement document count for an index."""
        if self._doc_counts[index_name] > 0:
            self._doc_counts[index_name] -= 1

        try:
            redis_client = await self._get_redis()
            metadata_key = self._get_index_metadata_key(index_name)
            await redis_client.hincrby(metadata_key, "doc_count", -1)
        except (redis.ConnectionError, redis.RedisError) as e:
            logger.error(f"Redis error decrementing doc count: {e}", exc_info=True)

    def _calculate_health_score(self, health: IndexHealth) -> float:
        """
        Calculate health score based on various metrics.

        Returns:
            Health score from 0-100
        """
        score = 100.0

        # Penalize for errors
        if health.error_count > 0:
            error_penalty = min(health.error_count * 5, 30)
            score -= error_penalty

            # Penalize for slow indexing
        if health.avg_index_time_ms > 100:
            speed_penalty = min((health.avg_index_time_ms - 100) / 10, 20)
            score -= speed_penalty

            # Penalize for slow search
        if health.avg_search_time_ms > 50:
            search_penalty = min((health.avg_search_time_ms - 50) / 5, 20)
            score -= search_penalty

            # Penalize for failed status
        if health.status == IndexStatus.FAILED:
            score = 0.0

        return max(0.0, min(100.0, score))

        # Global service instance


_search_indexer: SearchIndexer | None = None
_indexer_lock = RLock()


def get_search_indexer(
    namespace: str = "search",
    **kwargs,
) -> SearchIndexer:
    """
    Get or create the global search indexer instance.

    Args:
        namespace: Namespace for index organization
        **kwargs: Additional arguments for SearchIndexer

    Returns:
        SearchIndexer instance

    Example:
        indexer = get_search_indexer("schedule")
        await indexer.index_document("person", "123", {"name": "John"})
    """
    global _search_indexer

    with _indexer_lock:
        if _search_indexer is None:
            _search_indexer = SearchIndexer(namespace=namespace, **kwargs)

        return _search_indexer
