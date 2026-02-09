"""Tests for procedure credential schemas (field/model validators, CRUD)."""

from datetime import date, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.procedure import ProcedureSummary
from app.schemas.procedure_credential import (
    CredentialBase,
    CredentialCreate,
    CredentialUpdate,
    CredentialResponse,
    CredentialWithProcedureResponse,
    CredentialListResponse,
    CredentialWithProcedureListResponse,
    PersonSummary,
    CredentialWithPersonResponse,
    QualifiedFacultyResponse,
    FacultyCredentialSummary,
)


class TestCredentialBase:
    def test_defaults(self):
        r = CredentialBase()
        assert r.status == "active"
        assert r.competency_level == "qualified"
        assert r.issued_date is None
        assert r.expiration_date is None
        assert r.last_verified_date is None
        assert r.max_concurrent_residents is None
        assert r.max_per_week is None
        assert r.max_per_academic_year is None
        assert r.notes is None

    # --- status field_validator ---

    def test_status_valid(self):
        for s in ("active", "expired", "suspended", "pending"):
            r = CredentialBase(status=s)
            assert r.status == s

    def test_status_invalid(self):
        with pytest.raises(ValidationError, match="status must be one of"):
            CredentialBase(status="revoked")

    # --- competency_level field_validator ---

    def test_competency_valid(self):
        for c in ("trainee", "qualified", "expert", "master"):
            r = CredentialBase(competency_level=c)
            assert r.competency_level == c

    def test_competency_invalid(self):
        with pytest.raises(ValidationError, match="competency_level must be one of"):
            CredentialBase(competency_level="novice")

    # --- model_validator: expiration_date > issued_date ---

    def test_expiration_after_issue(self):
        r = CredentialBase(
            issued_date=date(2026, 1, 1), expiration_date=date(2027, 1, 1)
        )
        assert r.expiration_date > r.issued_date

    def test_expiration_before_issue(self):
        with pytest.raises(ValidationError, match="expiration_date.*must be after"):
            CredentialBase(
                issued_date=date(2027, 1, 1), expiration_date=date(2026, 1, 1)
            )

    def test_expiration_equal_issue(self):
        with pytest.raises(ValidationError, match="expiration_date.*must be after"):
            CredentialBase(
                issued_date=date(2026, 1, 1), expiration_date=date(2026, 1, 1)
            )


class TestCredentialCreate:
    def test_valid(self):
        r = CredentialCreate(person_id=uuid4(), procedure_id=uuid4())
        assert r.status == "active"
        assert r.competency_level == "qualified"


class TestCredentialUpdate:
    def test_all_none(self):
        r = CredentialUpdate()
        assert r.status is None
        assert r.competency_level is None
        assert r.expiration_date is None
        assert r.notes is None

    def test_partial(self):
        r = CredentialUpdate(status="expired", notes="Needs renewal")
        assert r.status == "expired"

    # --- status field_validator (None-aware) ---

    def test_status_invalid(self):
        with pytest.raises(ValidationError, match="status must be one of"):
            CredentialUpdate(status="revoked")

    # --- competency_level field_validator (None-aware) ---

    def test_competency_invalid(self):
        with pytest.raises(ValidationError, match="competency_level must be one of"):
            CredentialUpdate(competency_level="novice")


class TestCredentialResponse:
    def _make_response(self, **overrides):
        defaults = {
            "id": uuid4(),
            "person_id": uuid4(),
            "procedure_id": uuid4(),
            "status": "active",
            "competency_level": "qualified",
            "created_at": datetime(2026, 1, 1),
            "updated_at": datetime(2026, 1, 1),
            "is_valid": True,
        }
        defaults.update(overrides)
        return CredentialResponse(**defaults)

    def test_valid(self):
        r = self._make_response()
        assert r.is_valid is True


class TestCredentialWithProcedureResponse:
    def test_valid(self):
        proc = ProcedureSummary(id=uuid4(), name="Appendectomy")
        r = CredentialWithProcedureResponse(
            id=uuid4(),
            person_id=uuid4(),
            procedure_id=uuid4(),
            status="active",
            competency_level="expert",
            created_at=datetime(2026, 1, 1),
            updated_at=datetime(2026, 1, 1),
            is_valid=True,
            procedure=proc,
        )
        assert r.procedure.name == "Appendectomy"


class TestCredentialListResponse:
    def test_valid(self):
        r = CredentialListResponse(items=[], total=0)
        assert r.items == []


class TestCredentialWithProcedureListResponse:
    def test_valid(self):
        r = CredentialWithProcedureListResponse(items=[], total=0)
        assert r.items == []


class TestPersonSummary:
    def test_valid(self):
        r = PersonSummary(id=uuid4(), name="Dr. Smith", type="faculty")
        assert r.type == "faculty"


class TestCredentialWithPersonResponse:
    def test_valid(self):
        person = PersonSummary(id=uuid4(), name="Dr. Smith", type="faculty")
        r = CredentialWithPersonResponse(
            id=uuid4(),
            person_id=uuid4(),
            procedure_id=uuid4(),
            status="active",
            competency_level="qualified",
            created_at=datetime(2026, 1, 1),
            updated_at=datetime(2026, 1, 1),
            is_valid=True,
            person=person,
        )
        assert r.person.name == "Dr. Smith"


class TestQualifiedFacultyResponse:
    def test_valid(self):
        r = QualifiedFacultyResponse(
            procedure_id=uuid4(),
            procedure_name="C-Section",
            qualified_faculty=[],
            total=0,
        )
        assert r.qualified_faculty == []

    def test_with_faculty(self):
        p = PersonSummary(id=uuid4(), name="Dr. Jones", type="faculty")
        r = QualifiedFacultyResponse(
            procedure_id=uuid4(),
            procedure_name="C-Section",
            qualified_faculty=[p],
            total=1,
        )
        assert len(r.qualified_faculty) == 1


class TestFacultyCredentialSummary:
    def test_valid(self):
        r = FacultyCredentialSummary(
            person_id=uuid4(),
            person_name="Dr. Smith",
            total_credentials=5,
            active_credentials=4,
            expiring_soon=1,
            procedures=[],
        )
        assert r.expiring_soon == 1
