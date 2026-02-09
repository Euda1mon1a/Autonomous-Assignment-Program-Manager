"""Tests for common base schemas (generics, mixins, defaults)."""

from datetime import datetime
from uuid import uuid4

from app.schemas.common import (
    ErrorDetail,
    ErrorResponse,
    SuccessResponse,
    MetadataSchema,
    ListResponse,
    IdResponse,
    StatusResponse,
    CountResponse,
    BulkOperationResult,
    TimestampMixin,
    AuditMixin,
    SoftDeleteMixin,
    VersionedMixin,
    BaseSchema,
    BaseAuditedSchema,
    HealthCheckResponse,
)


class TestErrorDetail:
    def test_valid_minimal(self):
        r = ErrorDetail(message="Something went wrong")
        assert r.field is None
        assert r.code is None

    def test_full(self):
        r = ErrorDetail(field="email", message="Invalid format", code="INVALID_EMAIL")
        assert r.field == "email"
        assert r.code == "INVALID_EMAIL"


class TestErrorResponse:
    def test_valid_minimal(self):
        r = ErrorResponse(error="Not found")
        assert r.success is False
        assert r.error_code is None
        assert r.details is None
        assert isinstance(r.timestamp, datetime)

    def test_with_details(self):
        detail = ErrorDetail(message="Field required", field="name")
        r = ErrorResponse(
            error="Validation failed",
            error_code="VALIDATION_ERROR",
            details=[detail],
        )
        assert len(r.details) == 1
        assert r.error_code == "VALIDATION_ERROR"


class TestSuccessResponse:
    def test_valid(self):
        r = SuccessResponse[str](data="hello")
        assert r.success is True
        assert r.data == "hello"
        assert r.message is None
        assert isinstance(r.timestamp, datetime)

    def test_with_message(self):
        r = SuccessResponse[dict](data={"key": "val"}, message="Created")
        assert r.message == "Created"

    def test_with_list(self):
        r = SuccessResponse[list](data=[1, 2, 3])
        assert len(r.data) == 3


class TestMetadataSchema:
    def test_valid_minimal(self):
        r = MetadataSchema(total=100)
        assert r.page is None
        assert r.page_size is None
        assert r.total_pages is None
        assert r.has_next is None
        assert r.has_previous is None

    def test_full(self):
        r = MetadataSchema(
            total=100,
            page=2,
            page_size=10,
            total_pages=10,
            has_next=True,
            has_previous=True,
        )
        assert r.total_pages == 10


class TestListResponse:
    def test_valid_minimal(self):
        r = ListResponse[str](items=["a", "b"], total=2)
        assert len(r.items) == 2
        assert r.page is None
        assert r.page_size is None
        assert r.total_pages is None

    def test_paginated(self):
        r = ListResponse[int](
            items=[1, 2, 3], total=30, page=1, page_size=3, total_pages=10
        )
        assert r.total_pages == 10


class TestIdResponse:
    def test_valid(self):
        uid = uuid4()
        r = IdResponse(id=uid)
        assert r.id == uid
        assert isinstance(r.created_at, datetime)


class TestStatusResponse:
    def test_valid(self):
        r = StatusResponse(status="ok")
        assert r.message is None

    def test_with_message(self):
        r = StatusResponse(status="error", message="Something failed")
        assert r.message == "Something failed"


class TestCountResponse:
    def test_valid(self):
        r = CountResponse(count=42)
        assert r.count == 42


class TestBulkOperationResult:
    def test_valid_minimal(self):
        r = BulkOperationResult(total=10, successful=8, failed=2)
        assert r.errors is None

    def test_with_errors(self):
        r = BulkOperationResult(
            total=10,
            successful=8,
            failed=2,
            errors=[{"id": "1", "reason": "Not found"}],
        )
        assert len(r.errors) == 1


class TestTimestampMixin:
    def test_valid(self):
        now = datetime(2026, 3, 1)
        r = TimestampMixin(created_at=now, updated_at=now)
        assert r.created_at == now


class TestAuditMixin:
    def test_defaults(self):
        now = datetime(2026, 3, 1)
        r = AuditMixin(created_at=now, updated_at=now)
        assert r.created_by is None
        assert r.updated_by is None

    def test_full(self):
        now = datetime(2026, 3, 1)
        r = AuditMixin(
            created_at=now, updated_at=now, created_by="admin", updated_by="admin"
        )
        assert r.created_by == "admin"


class TestSoftDeleteMixin:
    def test_defaults(self):
        r = SoftDeleteMixin()
        assert r.deleted_at is None
        assert r.deleted_by is None
        assert r.is_deleted is False

    def test_deleted(self):
        r = SoftDeleteMixin(
            deleted_at=datetime(2026, 3, 1), deleted_by="admin", is_deleted=True
        )
        assert r.is_deleted is True


class TestVersionedMixin:
    def test_default(self):
        r = VersionedMixin()
        assert r.version == 1

    def test_custom_version(self):
        r = VersionedMixin(version=5)
        assert r.version == 5


class TestBaseSchema:
    def test_valid(self):
        uid = uuid4()
        now = datetime(2026, 3, 1)
        r = BaseSchema(id=uid, created_at=now, updated_at=now)
        assert r.id == uid


class TestBaseAuditedSchema:
    def test_valid(self):
        uid = uuid4()
        now = datetime(2026, 3, 1)
        r = BaseAuditedSchema(id=uid, created_at=now, updated_at=now)
        assert r.created_by is None


class TestHealthCheckResponse:
    def test_valid_minimal(self):
        r = HealthCheckResponse(status="healthy")
        assert r.version is None
        assert r.dependencies is None
        assert isinstance(r.timestamp, datetime)

    def test_full(self):
        r = HealthCheckResponse(
            status="healthy",
            version="1.0.0",
            dependencies={"database": "ok", "redis": "ok"},
        )
        assert r.dependencies["database"] == "ok"
