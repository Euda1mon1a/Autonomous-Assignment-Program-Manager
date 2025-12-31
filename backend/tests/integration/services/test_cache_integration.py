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
        ***REMOVED*** from app.services.cache import cache_service
        ***REMOVED*** cache_service.set("test_key", "test_value")
        ***REMOVED*** value = cache_service.get("test_key")
        ***REMOVED*** assert value == "test_value"

    def test_cache_invalidation_integration(
        self,
        db: Session,
        sample_resident: Person,
    ):
        """Test cache invalidation on update."""
        ***REMOVED*** Cache resident data
        ***REMOVED*** cache_service.set(f"resident:{sample_resident.id}", sample_resident)

        ***REMOVED*** Update resident
        ***REMOVED*** sample_resident.name = "Updated Name"
        ***REMOVED*** db.commit()

        ***REMOVED*** Cache should be invalidated
        ***REMOVED*** cached = cache_service.get(f"resident:{sample_resident.id}")
        ***REMOVED*** assert cached is None or cached.name == "Updated Name"

    def test_cache_ttl_integration(self, db: Session):
        """Test cache time-to-live."""
        ***REMOVED*** from app.services.cache import cache_service
        ***REMOVED*** cache_service.set("ttl_test", "value", ttl=1)
        ***REMOVED*** import time
        ***REMOVED*** time.sleep(2)
        ***REMOVED*** value = cache_service.get("ttl_test")
        ***REMOVED*** assert value is None

    def test_query_result_caching_integration(
        self,
        db: Session,
        sample_residents: list[Person],
    ):
        """Test caching query results."""
        ***REMOVED*** First query - cache miss
        ***REMOVED*** results1 = cache_service.get_or_fetch(
        ***REMOVED***     "residents_list",
        ***REMOVED***     lambda: db.query(Person).all()
        ***REMOVED*** )

        ***REMOVED*** Second query - cache hit
        ***REMOVED*** results2 = cache_service.get_or_fetch(
        ***REMOVED***     "residents_list",
        ***REMOVED***     lambda: db.query(Person).all()
        ***REMOVED*** )

        ***REMOVED*** assert results1 == results2

    def test_cache_bulk_operations_integration(self, db: Session):
        """Test bulk cache operations."""
        ***REMOVED*** from app.services.cache import cache_service
        ***REMOVED*** data = {"key1": "value1", "key2": "value2", "key3": "value3"}
        ***REMOVED*** cache_service.set_many(data)
        ***REMOVED*** values = cache_service.get_many(list(data.keys()))
        ***REMOVED*** assert values == data
