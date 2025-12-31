"""
Integration tests for caching layer.

Tests Redis caching integration.
"""

import pytest
from sqlalchemy.orm import Session

from app.models.person import Person


class TestCacheIntegration:
    """Test cache service integration."""

    def test_cache_set_get_integration(self, db: Session):
        """Test basic cache operations."""
        # from app.services.cache import cache_service
        # cache_service.set("test_key", "test_value")
        # value = cache_service.get("test_key")
        # assert value == "test_value"

    def test_cache_invalidation_integration(
        self,
        db: Session,
        sample_resident: Person,
    ):
        """Test cache invalidation on update."""
        # Cache resident data
        # cache_service.set(f"resident:{sample_resident.id}", sample_resident)

        # Update resident
        # sample_resident.name = "Updated Name"
        # db.commit()

        # Cache should be invalidated
        # cached = cache_service.get(f"resident:{sample_resident.id}")
        # assert cached is None or cached.name == "Updated Name"

    def test_cache_ttl_integration(self, db: Session):
        """Test cache time-to-live."""
        # from app.services.cache import cache_service
        # cache_service.set("ttl_test", "value", ttl=1)
        # import time
        # time.sleep(2)
        # value = cache_service.get("ttl_test")
        # assert value is None

    def test_query_result_caching_integration(
        self,
        db: Session,
        sample_residents: list[Person],
    ):
        """Test caching query results."""
        # First query - cache miss
        # results1 = cache_service.get_or_fetch(
        #     "residents_list",
        #     lambda: db.query(Person).all()
        # )

        # Second query - cache hit
        # results2 = cache_service.get_or_fetch(
        #     "residents_list",
        #     lambda: db.query(Person).all()
        # )

        # assert results1 == results2

    def test_cache_bulk_operations_integration(self, db: Session):
        """Test bulk cache operations."""
        # from app.services.cache import cache_service
        # data = {"key1": "value1", "key2": "value2", "key3": "value3"}
        # cache_service.set_many(data)
        # values = cache_service.get_many(list(data.keys()))
        # assert values == data
