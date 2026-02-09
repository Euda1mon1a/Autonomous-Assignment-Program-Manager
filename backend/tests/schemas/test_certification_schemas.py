"""Tests for certification schemas (Pydantic validation, field_validator, model_validator)."""

from datetime import date, datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.certification import (
    CertificationTypeBase,
    CertificationTypeCreate,
    CertificationTypeUpdate,
    CertificationTypeResponse,
    CertificationTypeListResponse,
    CertificationTypeSummary,
    PersonCertificationBase,
    PersonCertificationCreate,
    PersonCertificationUpdate,
    PersonCertificationListResponse,
    PersonSummary,
    ExpiringCertificationResponse,
    ExpiringCertificationsListResponse,
    ComplianceSummaryResponse,
    PersonComplianceResponse,
    ReminderQueueResponse,
)


# ===========================================================================
# CertificationTypeBase Tests
# ===========================================================================


class TestCertificationTypeBase:
    def _valid_kwargs(self):
        return {"name": "BLS"}

    def test_valid_minimal(self):
        r = CertificationTypeBase(**self._valid_kwargs())
        assert r.full_name is None
        assert r.description is None
        assert r.renewal_period_months == 24
        assert r.required_for_residents is True
        assert r.required_for_faculty is True
        assert r.required_for_specialties is None
        assert r.reminder_days_180 is True
        assert r.reminder_days_90 is True
        assert r.reminder_days_30 is True
        assert r.reminder_days_14 is True
        assert r.reminder_days_7 is True
        assert r.is_active is True

    def test_full(self):
        r = CertificationTypeBase(
            name="ACLS",
            full_name="Advanced Cardiovascular Life Support",
            description="Required for all emergency department staff",
            renewal_period_months=12,
            required_for_residents=True,
            required_for_faculty=False,
            required_for_specialties="Emergency Medicine,Internal Medicine",
        )
        assert r.full_name == "Advanced Cardiovascular Life Support"

    # --- name min_length=1, max_length=100 ---

    def test_name_empty(self):
        with pytest.raises(ValidationError):
            CertificationTypeBase(name="")

    def test_name_too_long(self):
        with pytest.raises(ValidationError):
            CertificationTypeBase(name="x" * 101)

    # --- full_name min_length=1, max_length=200 ---

    def test_full_name_empty(self):
        with pytest.raises(ValidationError):
            CertificationTypeBase(name="BLS", full_name="")

    def test_full_name_too_long(self):
        with pytest.raises(ValidationError):
            CertificationTypeBase(name="BLS", full_name="x" * 201)

    # --- description min_length=1, max_length=1000 ---

    def test_description_empty(self):
        with pytest.raises(ValidationError):
            CertificationTypeBase(name="BLS", description="")

    def test_description_too_long(self):
        with pytest.raises(ValidationError):
            CertificationTypeBase(name="BLS", description="x" * 1001)

    # --- renewal_period_months ge=1, le=120 ---

    def test_renewal_period_boundaries(self):
        r = CertificationTypeBase(name="BLS", renewal_period_months=1)
        assert r.renewal_period_months == 1
        r = CertificationTypeBase(name="BLS", renewal_period_months=120)
        assert r.renewal_period_months == 120

    def test_renewal_period_zero(self):
        with pytest.raises(ValidationError):
            CertificationTypeBase(name="BLS", renewal_period_months=0)

    def test_renewal_period_above_max(self):
        with pytest.raises(ValidationError):
            CertificationTypeBase(name="BLS", renewal_period_months=121)

    # --- required_for_specialties min_length=1, max_length=500 ---

    def test_required_for_specialties_empty(self):
        with pytest.raises(ValidationError):
            CertificationTypeBase(name="BLS", required_for_specialties="")

    def test_required_for_specialties_too_long(self):
        with pytest.raises(ValidationError):
            CertificationTypeBase(name="BLS", required_for_specialties="x" * 501)


# ===========================================================================
# CertificationTypeCreate Tests
# ===========================================================================


class TestCertificationTypeCreate:
    def test_inherits_base(self):
        r = CertificationTypeCreate(name="PALS")
        assert r.name == "PALS"
        assert r.renewal_period_months == 24


# ===========================================================================
# CertificationTypeUpdate Tests
# ===========================================================================


class TestCertificationTypeUpdate:
    def test_all_none(self):
        r = CertificationTypeUpdate()
        assert r.name is None
        assert r.full_name is None
        assert r.description is None
        assert r.renewal_period_months is None
        assert r.required_for_residents is None
        assert r.required_for_faculty is None
        assert r.required_for_specialties is None
        assert r.reminder_days_180 is None
        assert r.reminder_days_90 is None
        assert r.reminder_days_30 is None
        assert r.reminder_days_14 is None
        assert r.reminder_days_7 is None
        assert r.is_active is None


# ===========================================================================
# CertificationTypeResponse Tests
# ===========================================================================


class TestCertificationTypeResponse:
    def test_valid(self):
        r = CertificationTypeResponse(
            id=uuid4(),
            name="BLS",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert r.renewal_period_months == 24


# ===========================================================================
# CertificationTypeListResponse Tests
# ===========================================================================


class TestCertificationTypeListResponse:
    def test_valid(self):
        r = CertificationTypeListResponse(items=[], total=0)
        assert r.items == []


# ===========================================================================
# CertificationTypeSummary Tests
# ===========================================================================


class TestCertificationTypeSummary:
    def test_valid(self):
        r = CertificationTypeSummary(id=uuid4(), name="ACLS")
        assert r.full_name is None


# ===========================================================================
# PersonCertificationBase Tests
# ===========================================================================


class TestPersonCertificationBase:
    def _valid_kwargs(self):
        return {
            "issued_date": date.today() - timedelta(days=365),
            "expiration_date": date.today() + timedelta(days=365),
        }

    def test_valid_minimal(self):
        r = PersonCertificationBase(**self._valid_kwargs())
        assert r.certification_number is None
        assert r.status == "current"
        assert r.verified_by is None
        assert r.verified_date is None
        assert r.document_url is None
        assert r.notes is None

    # --- status pattern ---

    def test_valid_statuses(self):
        for s in ["current", "expiring_soon", "expired", "pending"]:
            kw = self._valid_kwargs()
            kw["status"] = s
            r = PersonCertificationBase(**kw)
            assert r.status == s

    def test_invalid_status(self):
        kw = self._valid_kwargs()
        kw["status"] = "revoked"
        with pytest.raises(ValidationError):
            PersonCertificationBase(**kw)

    # --- model_validator: expiration_date > issued_date ---

    def test_expiration_equals_issued(self):
        today = date.today()
        with pytest.raises(ValidationError):
            PersonCertificationBase(issued_date=today, expiration_date=today)

    def test_expiration_before_issued(self):
        with pytest.raises(ValidationError):
            PersonCertificationBase(
                issued_date=date.today(),
                expiration_date=date.today() - timedelta(days=1),
            )

    # --- certification_number min_length=1, max_length=100 ---

    def test_certification_number_empty(self):
        kw = self._valid_kwargs()
        kw["certification_number"] = ""
        with pytest.raises(ValidationError):
            PersonCertificationBase(**kw)

    def test_certification_number_too_long(self):
        kw = self._valid_kwargs()
        kw["certification_number"] = "x" * 101
        with pytest.raises(ValidationError):
            PersonCertificationBase(**kw)

    # --- verified_by min_length=1, max_length=200 ---

    def test_verified_by_empty(self):
        kw = self._valid_kwargs()
        kw["verified_by"] = ""
        with pytest.raises(ValidationError):
            PersonCertificationBase(**kw)

    def test_verified_by_too_long(self):
        kw = self._valid_kwargs()
        kw["verified_by"] = "x" * 201
        with pytest.raises(ValidationError):
            PersonCertificationBase(**kw)

    # --- document_url min_length=1, max_length=500 ---

    def test_document_url_empty(self):
        kw = self._valid_kwargs()
        kw["document_url"] = ""
        with pytest.raises(ValidationError):
            PersonCertificationBase(**kw)

    def test_document_url_too_long(self):
        kw = self._valid_kwargs()
        kw["document_url"] = "x" * 501
        with pytest.raises(ValidationError):
            PersonCertificationBase(**kw)

    # --- notes min_length=1, max_length=2000 ---

    def test_notes_empty(self):
        kw = self._valid_kwargs()
        kw["notes"] = ""
        with pytest.raises(ValidationError):
            PersonCertificationBase(**kw)

    def test_notes_too_long(self):
        kw = self._valid_kwargs()
        kw["notes"] = "x" * 2001
        with pytest.raises(ValidationError):
            PersonCertificationBase(**kw)

    def test_notes_max_length(self):
        kw = self._valid_kwargs()
        kw["notes"] = "x" * 2000
        r = PersonCertificationBase(**kw)
        assert len(r.notes) == 2000


# ===========================================================================
# PersonCertificationCreate Tests
# ===========================================================================


class TestPersonCertificationCreate:
    def test_valid(self):
        r = PersonCertificationCreate(
            person_id=uuid4(),
            certification_type_id=uuid4(),
            issued_date=date.today() - timedelta(days=30),
            expiration_date=date.today() + timedelta(days=700),
        )
        assert r.status == "current"


# ===========================================================================
# PersonCertificationUpdate Tests
# ===========================================================================


class TestPersonCertificationUpdate:
    def test_all_none(self):
        r = PersonCertificationUpdate()
        assert r.certification_number is None
        assert r.issued_date is None
        assert r.expiration_date is None
        assert r.status is None
        assert r.verified_by is None
        assert r.verified_date is None
        assert r.document_url is None
        assert r.notes is None

    def test_status_valid(self):
        r = PersonCertificationUpdate(status="expired")
        assert r.status == "expired"

    def test_status_none_allowed(self):
        r = PersonCertificationUpdate(status=None)
        assert r.status is None

    def test_status_invalid(self):
        with pytest.raises(ValidationError):
            PersonCertificationUpdate(status="revoked")


# ===========================================================================
# PersonCertificationListResponse Tests
# ===========================================================================


class TestPersonCertificationListResponse:
    def test_valid(self):
        r = PersonCertificationListResponse(items=[], total=0)
        assert r.items == []


# ===========================================================================
# PersonSummary Tests
# ===========================================================================


class TestPersonSummary:
    def test_valid(self):
        r = PersonSummary(id=uuid4(), name="Dr. Smith", type="faculty")
        assert r.email is None


# ===========================================================================
# ExpiringCertificationResponse Tests
# ===========================================================================


class TestExpiringCertificationResponse:
    def test_valid(self):
        r = ExpiringCertificationResponse(
            id=uuid4(),
            person=PersonSummary(id=uuid4(), name="Dr. Smith", type="faculty"),
            certification_type=CertificationTypeSummary(id=uuid4(), name="BLS"),
            expiration_date=date.today() + timedelta(days=30),
            days_until_expiration=30,
            status="expiring_soon",
        )
        assert r.days_until_expiration == 30


# ===========================================================================
# ExpiringCertificationsListResponse Tests
# ===========================================================================


class TestExpiringCertificationsListResponse:
    def test_valid(self):
        r = ExpiringCertificationsListResponse(items=[], total=0, days_threshold=90)
        assert r.days_threshold == 90


# ===========================================================================
# ComplianceSummaryResponse Tests
# ===========================================================================


class TestComplianceSummaryResponse:
    def test_valid(self):
        r = ComplianceSummaryResponse(
            total=100,
            current=90,
            expiring_soon=5,
            expired=5,
            compliance_rate=0.9,
        )
        assert r.compliance_rate == 0.9


# ===========================================================================
# PersonComplianceResponse Tests
# ===========================================================================


class TestPersonComplianceResponse:
    def test_valid(self):
        r = PersonComplianceResponse(
            person=PersonSummary(id=uuid4(), name="Dr. Jones", type="resident"),
            total_required=5,
            total_current=4,
            expired=1,
            expiring_soon=0,
            missing=[],
            is_compliant=False,
        )
        assert r.is_compliant is False


# ===========================================================================
# ReminderQueueResponse Tests
# ===========================================================================


class TestReminderQueueResponse:
    def test_valid(self):
        r = ReminderQueueResponse(days_threshold=30, certifications=[], total=0)
        assert r.total == 0
