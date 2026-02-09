"""Tests for admin user schemas (enums, Field bounds, aliases, defaults)."""

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.admin_user import (
    UserRole,
    UserStatus,
    BulkAction,
    ActivityAction,
    AdminUserBase,
    AdminUserCreate,
    AdminUserUpdate,
    AdminUserResponse,
    AdminUserListResponse,
    AccountLockRequest,
    AccountLockResponse,
    ResendInviteRequest,
    ResendInviteResponse,
    ActivityLogEntry,
    ActivityLogResponse,
    ActivityLogFilters,
    BulkUserActionRequest,
    BulkUserActionResponse,
    UserListQueryParams,
)


class TestUserRole:
    def test_values(self):
        assert UserRole.ADMIN == "admin"
        assert UserRole.COORDINATOR == "coordinator"
        assert UserRole.FACULTY == "faculty"
        assert UserRole.CLINICAL_STAFF == "clinical_staff"
        assert UserRole.RN == "rn"
        assert UserRole.LPN == "lpn"
        assert UserRole.MSA == "msa"
        assert UserRole.RESIDENT == "resident"

    def test_count(self):
        assert len(UserRole) == 8


class TestUserStatus:
    def test_values(self):
        assert UserStatus.ACTIVE == "active"
        assert UserStatus.INACTIVE == "inactive"
        assert UserStatus.LOCKED == "locked"
        assert UserStatus.PENDING == "pending"

    def test_count(self):
        assert len(UserStatus) == 4


class TestBulkAction:
    def test_values(self):
        assert BulkAction.ACTIVATE == "activate"
        assert BulkAction.DEACTIVATE == "deactivate"
        assert BulkAction.DELETE == "delete"

    def test_count(self):
        assert len(BulkAction) == 3


class TestActivityAction:
    def test_values(self):
        assert ActivityAction.USER_CREATED == "user_created"
        assert ActivityAction.LOGIN_SUCCESS == "login_success"
        assert ActivityAction.INVITE_RESENT == "invite_resent"

    def test_count(self):
        assert len(ActivityAction) == 11


# ── AdminUserBase ────────────────────────────────────────────────────────


class TestAdminUserBase:
    def test_defaults(self):
        r = AdminUserBase(email="test@example.com", first_name="John", last_name="Doe")
        assert r.role == UserRole.COORDINATOR

    # --- first_name/last_name min_length=1, max_length=100 ---

    def test_first_name_empty(self):
        with pytest.raises(ValidationError):
            AdminUserBase(email="test@example.com", first_name="", last_name="Doe")

    def test_last_name_too_long(self):
        with pytest.raises(ValidationError):
            AdminUserBase(
                email="test@example.com",
                first_name="John",
                last_name="x" * 101,
            )

    # --- email must be EmailStr ---

    def test_invalid_email(self):
        with pytest.raises(ValidationError):
            AdminUserBase(email="not-an-email", first_name="John", last_name="Doe")


# ── AdminUserCreate ─────────────────────────────────────────────────────


class TestAdminUserCreate:
    def test_defaults(self):
        r = AdminUserCreate(
            email="test@example.com", first_name="John", last_name="Doe"
        )
        assert r.username is None
        assert r.send_invite is True

    # --- username min_length=3, max_length=100 ---

    def test_username_too_short(self):
        with pytest.raises(ValidationError):
            AdminUserCreate(
                email="test@example.com",
                first_name="John",
                last_name="Doe",
                username="ab",
            )

    def test_username_too_long(self):
        with pytest.raises(ValidationError):
            AdminUserCreate(
                email="test@example.com",
                first_name="John",
                last_name="Doe",
                username="x" * 101,
            )


# ── AdminUserUpdate ─────────────────────────────────────────────────────


class TestAdminUserUpdate:
    def test_all_none(self):
        r = AdminUserUpdate()
        assert r.email is None
        assert r.first_name is None
        assert r.last_name is None
        assert r.role is None
        assert r.is_active is None

    def test_partial(self):
        r = AdminUserUpdate(first_name="Updated", role=UserRole.ADMIN)
        assert r.first_name == "Updated"
        assert r.role == UserRole.ADMIN

    def test_first_name_bounds(self):
        with pytest.raises(ValidationError):
            AdminUserUpdate(first_name="")


# ── AdminUserResponse ───────────────────────────────────────────────────


class TestAdminUserResponse:
    def test_defaults(self):
        r = AdminUserResponse(
            id=uuid4(),
            username="jdoe",
            email="test@example.com",
            role="coordinator",
            is_active=True,
        )
        assert r.is_locked is False
        assert r.lock_reason is None
        assert r.created_at is None
        assert r.last_login is None
        assert r.invite_sent_at is None


# ── AdminUserListResponse (aliases) ─────────────────────────────────────


class TestAdminUserListResponse:
    def test_by_alias(self):
        r = AdminUserListResponse(items=[], total=0, page=1, pageSize=20, totalPages=0)
        assert r.page_size == 20
        assert r.total_pages == 0

    def test_by_field_name(self):
        r = AdminUserListResponse(
            items=[], total=0, page=1, page_size=20, total_pages=0
        )
        assert r.page_size == 20


# ── AccountLock schemas ─────────────────────────────────────────────────


class TestAccountLockRequest:
    def test_valid(self):
        r = AccountLockRequest(locked=True, reason="Security concern")
        assert r.locked is True

    def test_reason_too_long(self):
        with pytest.raises(ValidationError):
            AccountLockRequest(locked=True, reason="x" * 501)

    def test_reason_optional(self):
        r = AccountLockRequest(locked=False)
        assert r.reason is None


class TestAccountLockResponse:
    def test_by_alias(self):
        uid = uuid4()
        r = AccountLockResponse(
            userId=uid,
            isLocked=True,
            message="Locked",
        )
        assert r.user_id == uid
        assert r.is_locked is True
        assert r.lock_reason is None

    def test_by_field_name(self):
        uid = uuid4()
        r = AccountLockResponse(
            user_id=uid,
            is_locked=False,
            message="Unlocked",
        )
        assert r.user_id == uid


# ── Invitation schemas ──────────────────────────────────────────────────


class TestResendInviteRequest:
    def test_defaults(self):
        r = ResendInviteRequest()
        assert r.custom_message is None

    def test_by_alias(self):
        r = ResendInviteRequest(customMessage="Welcome!")
        assert r.custom_message == "Welcome!"

    def test_by_field_name(self):
        r = ResendInviteRequest(custom_message="Hello")
        assert r.custom_message == "Hello"

    def test_custom_message_too_long(self):
        with pytest.raises(ValidationError):
            ResendInviteRequest(custom_message="x" * 1001)


class TestResendInviteResponse:
    def test_by_alias(self):
        uid = uuid4()
        r = ResendInviteResponse(
            userId=uid,
            email="test@example.com",
            sentAt=datetime(2026, 1, 1),
            message="Sent",
        )
        assert r.user_id == uid
        assert r.sent_at == datetime(2026, 1, 1)


# ── ActivityLog schemas ─────────────────────────────────────────────────


class TestActivityLogEntry:
    def test_by_alias(self):
        uid = uuid4()
        r = ActivityLogEntry(
            id=uuid4(),
            timestamp=datetime(2026, 1, 1),
            userId=uid,
            action="user_created",
        )
        assert r.user_id == uid
        assert r.user_email is None
        assert r.details is None
        assert r.changes is None

    def test_by_field_name(self):
        uid = uuid4()
        r = ActivityLogEntry(
            id=uuid4(),
            timestamp=datetime(2026, 1, 1),
            user_id=uid,
            action="login_success",
            ip_address="127.0.0.1",
        )
        assert r.ip_address == "127.0.0.1"


class TestActivityLogResponse:
    def test_by_alias(self):
        r = ActivityLogResponse(items=[], total=0, page=1, pageSize=20, totalPages=0)
        assert r.page_size == 20
        assert r.total_pages == 0


class TestActivityLogFilters:
    def test_defaults(self):
        r = ActivityLogFilters()
        assert r.user_id is None
        assert r.action is None
        assert r.date_from is None
        assert r.date_to is None

    def test_by_alias(self):
        uid = uuid4()
        r = ActivityLogFilters(
            userId=uid,
            dateFrom=datetime(2026, 1, 1),
            dateTo=datetime(2026, 3, 31),
        )
        assert r.user_id == uid
        assert r.date_from == datetime(2026, 1, 1)


# ── Bulk operation schemas ──────────────────────────────────────────────


class TestBulkUserActionRequest:
    def test_by_alias(self):
        uid = uuid4()
        r = BulkUserActionRequest(userIds=[uid], action=BulkAction.ACTIVATE)
        assert r.user_ids == [uid]

    def test_by_field_name(self):
        uid = uuid4()
        r = BulkUserActionRequest(user_ids=[uid], action=BulkAction.DEACTIVATE)
        assert r.user_ids == [uid]

    # --- user_ids min_length=1 ---

    def test_user_ids_empty(self):
        with pytest.raises(ValidationError):
            BulkUserActionRequest(userIds=[], action=BulkAction.DELETE)


class TestBulkUserActionResponse:
    def test_defaults(self):
        uid = uuid4()
        r = BulkUserActionResponse(
            action="activate",
            affectedCount=1,
            successIds=[uid],
            message="Done",
        )
        assert r.failed_ids == []
        assert r.errors == []


# ── UserListQueryParams ─────────────────────────────────────────────────


class TestUserListQueryParams:
    def test_defaults(self):
        r = UserListQueryParams()
        assert r.page == 1
        assert r.page_size == 20
        assert r.role is None
        assert r.status is None
        assert r.search is None

    # --- page ge=1 ---

    def test_page_below_min(self):
        with pytest.raises(ValidationError):
            UserListQueryParams(page=0)

    # --- page_size ge=1, le=100 ---

    def test_page_size_below_min(self):
        with pytest.raises(ValidationError):
            UserListQueryParams(page_size=0)

    def test_page_size_above_max(self):
        with pytest.raises(ValidationError):
            UserListQueryParams(page_size=101)

    def test_search_too_long(self):
        with pytest.raises(ValidationError):
            UserListQueryParams(search="x" * 101)

    def test_by_alias(self):
        r = UserListQueryParams(pageSize=50)
        assert r.page_size == 50
