"""Tests for quota management schemas (Pydantic validation and Field coverage)."""

import pytest
from pydantic import ValidationError

from app.schemas.quota import (
    QuotaLimits,
    QuotaUsage,
    QuotaRemaining,
    QuotaPercentage,
    ResourceQuotaStatus,
    QuotaResetTimes,
    QuotaStatus,
    QuotaPolicyConfig,
    SetCustomQuotaRequest,
    SetCustomQuotaResponse,
    ResetQuotaRequest,
    ResetQuotaResponse,
    QuotaAlert,
    QuotaAlertsResponse,
    QuotaPolicyInfo,
    AllPoliciesResponse,
    QuotaUsageReport,
    QuotaExceededDetail,
    RecordUsageRequest,
    RecordUsageResponse,
)


# ===========================================================================
# QuotaLimits / QuotaUsage / QuotaRemaining / QuotaPercentage Tests
# ===========================================================================


class TestQuotaLimits:
    def test_valid(self):
        r = QuotaLimits(daily=100, monthly=3000)
        assert r.daily == 100


class TestQuotaUsage:
    def test_valid(self):
        r = QuotaUsage(daily=50, monthly=1500)
        assert r.monthly == 1500


class TestQuotaRemaining:
    def test_valid(self):
        r = QuotaRemaining(daily=50, monthly=1500)
        assert r.daily == 50


class TestQuotaPercentage:
    def test_valid(self):
        r = QuotaPercentage(daily=50.0, monthly=50.0)
        assert r.daily == 50.0


# ===========================================================================
# ResourceQuotaStatus Tests
# ===========================================================================


class TestResourceQuotaStatus:
    def test_valid(self):
        r = ResourceQuotaStatus(
            limits=QuotaLimits(daily=100, monthly=3000),
            usage=QuotaUsage(daily=50, monthly=1500),
            remaining=QuotaRemaining(daily=50, monthly=1500),
            percentage=QuotaPercentage(daily=50.0, monthly=50.0),
        )
        assert r.limits.daily == 100


# ===========================================================================
# QuotaResetTimes Tests
# ===========================================================================


class TestQuotaResetTimes:
    def test_valid(self):
        r = QuotaResetTimes(
            daily="2026-03-02T00:00:00Z",
            monthly="2026-04-01T00:00:00Z",
        )
        assert "2026-03-02" in r.daily


# ===========================================================================
# QuotaStatus Tests
# ===========================================================================


class TestQuotaStatus:
    def test_valid(self):
        r = QuotaStatus(
            user_id="user-1",
            policy_type="standard",
            reset_times=QuotaResetTimes(
                daily="2026-03-02T00:00:00Z",
                monthly="2026-04-01T00:00:00Z",
            ),
            resources={},
        )
        assert r.policy_type == "standard"


# ===========================================================================
# QuotaPolicyConfig Tests
# ===========================================================================


class TestQuotaPolicyConfig:
    def _valid_kwargs(self):
        return {
            "daily_limit": 1000,
            "monthly_limit": 30000,
            "schedule_generation_daily": 10,
            "schedule_generation_monthly": 100,
            "export_daily": 50,
            "export_monthly": 500,
            "report_daily": 20,
            "report_monthly": 200,
        }

    def test_valid(self):
        r = QuotaPolicyConfig(**self._valid_kwargs())
        assert r.allow_overage is False
        assert r.overage_percentage == 0.0

    # --- gt=0 on all limit fields ---

    def test_daily_limit_zero(self):
        kw = self._valid_kwargs()
        kw["daily_limit"] = 0
        with pytest.raises(ValidationError):
            QuotaPolicyConfig(**kw)

    def test_monthly_limit_zero(self):
        kw = self._valid_kwargs()
        kw["monthly_limit"] = 0
        with pytest.raises(ValidationError):
            QuotaPolicyConfig(**kw)

    def test_schedule_generation_daily_zero(self):
        kw = self._valid_kwargs()
        kw["schedule_generation_daily"] = 0
        with pytest.raises(ValidationError):
            QuotaPolicyConfig(**kw)

    def test_schedule_generation_monthly_zero(self):
        kw = self._valid_kwargs()
        kw["schedule_generation_monthly"] = 0
        with pytest.raises(ValidationError):
            QuotaPolicyConfig(**kw)

    def test_export_daily_zero(self):
        kw = self._valid_kwargs()
        kw["export_daily"] = 0
        with pytest.raises(ValidationError):
            QuotaPolicyConfig(**kw)

    def test_export_monthly_zero(self):
        kw = self._valid_kwargs()
        kw["export_monthly"] = 0
        with pytest.raises(ValidationError):
            QuotaPolicyConfig(**kw)

    def test_report_daily_zero(self):
        kw = self._valid_kwargs()
        kw["report_daily"] = 0
        with pytest.raises(ValidationError):
            QuotaPolicyConfig(**kw)

    def test_report_monthly_zero(self):
        kw = self._valid_kwargs()
        kw["report_monthly"] = 0
        with pytest.raises(ValidationError):
            QuotaPolicyConfig(**kw)

    def test_all_limits_minimum(self):
        kw = dict.fromkeys(self._valid_kwargs(), 1)
        r = QuotaPolicyConfig(**kw)
        assert r.daily_limit == 1

    # --- overage_percentage ge=0.0, le=1.0 ---

    def test_overage_percentage_boundaries(self):
        kw = self._valid_kwargs()
        kw["overage_percentage"] = 0.0
        r = QuotaPolicyConfig(**kw)
        assert r.overage_percentage == 0.0

        kw["overage_percentage"] = 1.0
        r = QuotaPolicyConfig(**kw)
        assert r.overage_percentage == 1.0

    def test_overage_percentage_negative(self):
        kw = self._valid_kwargs()
        kw["overage_percentage"] = -0.1
        with pytest.raises(ValidationError):
            QuotaPolicyConfig(**kw)

    def test_overage_percentage_above_one(self):
        kw = self._valid_kwargs()
        kw["overage_percentage"] = 1.1
        with pytest.raises(ValidationError):
            QuotaPolicyConfig(**kw)


# ===========================================================================
# SetCustomQuotaRequest Tests
# ===========================================================================


class TestSetCustomQuotaRequest:
    def _make_policy(self):
        return QuotaPolicyConfig(
            daily_limit=1000,
            monthly_limit=30000,
            schedule_generation_daily=10,
            schedule_generation_monthly=100,
            export_daily=50,
            export_monthly=500,
            report_daily=20,
            report_monthly=200,
        )

    def test_valid(self):
        r = SetCustomQuotaRequest(user_id="user-1", policy=self._make_policy())
        assert r.ttl_seconds is None

    # --- ttl_seconds gt=0 ---

    def test_ttl_seconds_positive(self):
        r = SetCustomQuotaRequest(
            user_id="user-1", policy=self._make_policy(), ttl_seconds=3600
        )
        assert r.ttl_seconds == 3600

    def test_ttl_seconds_zero(self):
        with pytest.raises(ValidationError):
            SetCustomQuotaRequest(
                user_id="user-1", policy=self._make_policy(), ttl_seconds=0
            )

    def test_ttl_seconds_negative(self):
        with pytest.raises(ValidationError):
            SetCustomQuotaRequest(
                user_id="user-1", policy=self._make_policy(), ttl_seconds=-1
            )


# ===========================================================================
# SetCustomQuotaResponse Tests
# ===========================================================================


class TestSetCustomQuotaResponse:
    def _make_policy(self):
        return QuotaPolicyConfig(
            daily_limit=1000,
            monthly_limit=30000,
            schedule_generation_daily=10,
            schedule_generation_monthly=100,
            export_daily=50,
            export_monthly=500,
            report_daily=20,
            report_monthly=200,
        )

    def test_valid(self):
        r = SetCustomQuotaResponse(
            success=True,
            message="Custom quota set",
            user_id="user-1",
            policy=self._make_policy(),
        )
        assert r.expires_at is None


# ===========================================================================
# ResetQuotaRequest Tests
# ===========================================================================


class TestResetQuotaRequest:
    def test_defaults(self):
        r = ResetQuotaRequest(user_id="user-1")
        assert r.resource_type is None
        assert r.reset_daily is True
        assert r.reset_monthly is False


# ===========================================================================
# ResetQuotaResponse Tests
# ===========================================================================


class TestResetQuotaResponse:
    def test_valid(self):
        r = ResetQuotaResponse(
            success=True,
            message="Quota reset",
            user_id="user-1",
        )
        assert r.success is True


# ===========================================================================
# QuotaAlert Tests
# ===========================================================================


class TestQuotaAlert:
    def test_valid(self):
        r = QuotaAlert(
            resource_type="api",
            timestamp="2026-03-01T10:00:00Z",
            alert_level="warning",
            daily_percentage=80.0,
            monthly_percentage=50.0,
        )
        assert r.alert_level == "warning"


# ===========================================================================
# QuotaAlertsResponse Tests
# ===========================================================================


class TestQuotaAlertsResponse:
    def test_valid(self):
        r = QuotaAlertsResponse(user_id="user-1", alerts=[])
        assert r.alerts == []


# ===========================================================================
# QuotaPolicyInfo Tests
# ===========================================================================


class TestQuotaPolicyInfo:
    def _make_policy(self):
        return QuotaPolicyConfig(
            daily_limit=1000,
            monthly_limit=30000,
            schedule_generation_daily=10,
            schedule_generation_monthly=100,
            export_daily=50,
            export_monthly=500,
            report_daily=20,
            report_monthly=200,
        )

    def test_valid(self):
        r = QuotaPolicyInfo(
            policy_type="standard",
            roles=["admin", "coordinator"],
            config=self._make_policy(),
        )
        assert len(r.roles) == 2


# ===========================================================================
# AllPoliciesResponse Tests
# ===========================================================================


class TestAllPoliciesResponse:
    def test_valid(self):
        r = AllPoliciesResponse(policies=[])
        assert r.policies == []


# ===========================================================================
# QuotaUsageReport Tests
# ===========================================================================


class TestQuotaUsageReport:
    def test_valid(self):
        r = QuotaUsageReport(
            user_id="user-1",
            policy_type="standard",
            period="daily",
            resources={},
            total_usage=50,
            total_limit=100,
            usage_percentage=50.0,
            generated_at="2026-03-01T10:00:00Z",
        )
        assert r.usage_percentage == 50.0


# ===========================================================================
# QuotaExceededDetail Tests
# ===========================================================================


class TestQuotaExceededDetail:
    def test_valid(self):
        r = QuotaExceededDetail(
            message="Daily API quota exceeded",
            resource_type="api",
            daily_limit=100,
            monthly_limit=3000,
            reset_times=QuotaResetTimes(
                daily="2026-03-02T00:00:00Z",
                monthly="2026-04-01T00:00:00Z",
            ),
        )
        assert r.error == "Quota exceeded"


# ===========================================================================
# RecordUsageRequest Tests
# ===========================================================================


class TestRecordUsageRequest:
    def test_defaults(self):
        r = RecordUsageRequest(user_id="user-1")
        assert r.resource_type == "api"
        assert r.amount == 1

    # --- amount gt=0 ---

    def test_amount_positive(self):
        r = RecordUsageRequest(user_id="user-1", amount=5)
        assert r.amount == 5

    def test_amount_zero(self):
        with pytest.raises(ValidationError):
            RecordUsageRequest(user_id="user-1", amount=0)

    def test_amount_negative(self):
        with pytest.raises(ValidationError):
            RecordUsageRequest(user_id="user-1", amount=-1)


# ===========================================================================
# RecordUsageResponse Tests
# ===========================================================================


class TestRecordUsageResponse:
    def test_valid(self):
        r = RecordUsageResponse(
            success=True,
            user_id="user-1",
            resource_type="api",
            daily_usage=51,
            monthly_usage=1501,
        )
        assert r.daily_usage == 51
