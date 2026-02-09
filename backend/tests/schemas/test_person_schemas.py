"""Tests for person schemas (enums, Field bounds, field_validators, defaults, batch ops)."""

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.person import (
    FacultyRoleSchema,
    PersonType,
    PersonBase,
    PersonCreate,
    PersonUpdate,
    PersonResponse,
    PersonListResponse,
    BatchPersonCreateRequest,
    BatchPersonUpdateItem,
    BatchPersonUpdateRequest,
    BatchPersonDeleteRequest,
    BatchOperationResult,
    BatchPersonResponse,
)


class TestFacultyRoleSchema:
    def test_values(self):
        assert FacultyRoleSchema.PD == "pd"
        assert FacultyRoleSchema.APD == "apd"
        assert FacultyRoleSchema.OIC == "oic"
        assert FacultyRoleSchema.DEPT_CHIEF == "dept_chief"
        assert FacultyRoleSchema.SPORTS_MED == "sports_med"
        assert FacultyRoleSchema.CORE == "core"
        assert FacultyRoleSchema.ADJUNCT == "adjunct"

    def test_count(self):
        assert len(FacultyRoleSchema) == 7


class TestPersonType:
    def test_values(self):
        assert PersonType.RESIDENT == "resident"
        assert PersonType.FACULTY == "faculty"

    def test_count(self):
        assert len(PersonType) == 2


class TestPersonBase:
    def test_valid_resident(self):
        r = PersonBase(name="Dr. Smith", type=PersonType.RESIDENT, pgy_level=2)
        assert r.email is None
        assert r.performs_procedures is False
        assert r.specialties is None
        assert r.primary_duty is None
        assert r.faculty_role is None

    def test_valid_faculty(self):
        r = PersonBase(
            name="Dr. Jones",
            type=PersonType.FACULTY,
            faculty_role=FacultyRoleSchema.CORE,
        )
        assert r.faculty_role == FacultyRoleSchema.CORE

    # --- name min_length=1, max_length=100, validator strips ---

    def test_name_empty(self):
        with pytest.raises(ValidationError):
            PersonBase(name="", type=PersonType.RESIDENT)

    def test_name_whitespace_only(self):
        with pytest.raises(ValidationError, match="name cannot be empty"):
            PersonBase(name="   ", type=PersonType.RESIDENT)

    def test_name_stripped(self):
        r = PersonBase(name="  Dr. Smith  ", type=PersonType.RESIDENT)
        assert r.name == "Dr. Smith"

    def test_name_too_long(self):
        with pytest.raises(ValidationError):
            PersonBase(name="x" * 101, type=PersonType.RESIDENT)

    # --- pgy_level ge=1, le=3 ---

    def test_pgy_level_below_min(self):
        with pytest.raises(ValidationError):
            PersonBase(name="Dr. Smith", type=PersonType.RESIDENT, pgy_level=0)

    def test_pgy_level_above_max(self):
        with pytest.raises(ValidationError):
            PersonBase(name="Dr. Smith", type=PersonType.RESIDENT, pgy_level=4)

    # --- performs_procedures coerce None to False ---

    def test_performs_procedures_none_coerced(self):
        r = PersonBase(
            name="Dr. Smith", type=PersonType.RESIDENT, performs_procedures=None
        )
        assert r.performs_procedures is False

    # --- specialties validator ---

    def test_valid_specialties(self):
        r = PersonBase(
            name="Dr. Smith",
            type=PersonType.FACULTY,
            specialties=["Cardiology", "Pulmonology"],
        )
        assert len(r.specialties) == 2

    def test_specialty_empty_string(self):
        with pytest.raises(
            ValidationError, match="Each specialty must be between 1 and 50"
        ):
            PersonBase(name="Dr. Smith", type=PersonType.FACULTY, specialties=[""])

    def test_specialty_too_long(self):
        with pytest.raises(
            ValidationError, match="Each specialty must be between 1 and 50"
        ):
            PersonBase(
                name="Dr. Smith",
                type=PersonType.FACULTY,
                specialties=["x" * 51],
            )


class TestPersonCreate:
    def test_valid(self):
        r = PersonCreate(name="Dr. Smith", type=PersonType.RESIDENT, pgy_level=1)
        assert r.pgy_level == 1


class TestPersonUpdate:
    def test_all_none(self):
        r = PersonUpdate()
        assert r.name is None
        assert r.email is None
        assert r.pgy_level is None
        assert r.performs_procedures is None
        assert r.specialties is None
        assert r.primary_duty is None
        assert r.faculty_role is None

    def test_partial(self):
        r = PersonUpdate(name="Dr. Updated", pgy_level=3)
        assert r.name == "Dr. Updated"
        assert r.pgy_level == 3

    # --- name validator on update ---

    def test_name_whitespace_update(self):
        with pytest.raises(ValidationError, match="name cannot be empty"):
            PersonUpdate(name="   ")

    # --- pgy_level bounds on update ---

    def test_pgy_level_below_min_update(self):
        with pytest.raises(ValidationError):
            PersonUpdate(pgy_level=0)

    def test_pgy_level_above_max_update(self):
        with pytest.raises(ValidationError):
            PersonUpdate(pgy_level=4)


class TestPersonResponse:
    def test_defaults(self):
        r = PersonResponse(
            id=uuid4(),
            name="Dr. Smith",
            type=PersonType.RESIDENT,
            pgy_level=2,
            created_at=datetime(2026, 1, 1),
            updated_at=datetime(2026, 1, 1),
        )
        assert r.sunday_call_count == 0
        assert r.weekday_call_count == 0
        assert r.fmit_weeks_count == 0


class TestPersonListResponse:
    def test_valid(self):
        r = PersonListResponse(items=[], total=0)
        assert r.items == []


class TestBatchPersonCreateRequest:
    def test_valid(self):
        person = PersonCreate(name="Dr. Smith", type=PersonType.RESIDENT)
        r = BatchPersonCreateRequest(people=[person])
        assert r.dry_run is False

    # --- people min_length=1 ---

    def test_people_empty(self):
        with pytest.raises(ValidationError):
            BatchPersonCreateRequest(people=[])


class TestBatchPersonUpdateRequest:
    def test_valid(self):
        item = BatchPersonUpdateItem(
            person_id=uuid4(), updates=PersonUpdate(name="Updated")
        )
        r = BatchPersonUpdateRequest(people=[item])
        assert r.dry_run is False

    # --- people min_length=1 ---

    def test_people_empty(self):
        with pytest.raises(ValidationError):
            BatchPersonUpdateRequest(people=[])


class TestBatchPersonDeleteRequest:
    def test_valid(self):
        r = BatchPersonDeleteRequest(person_ids=[uuid4()])
        assert r.dry_run is False

    # --- person_ids min_length=1 ---

    def test_person_ids_empty(self):
        with pytest.raises(ValidationError):
            BatchPersonDeleteRequest(person_ids=[])


class TestBatchOperationResult:
    def test_success(self):
        r = BatchOperationResult(index=0, success=True, person_id=uuid4())
        assert r.error is None

    def test_failure(self):
        r = BatchOperationResult(index=1, success=False, error="Not found")
        assert r.person_id is None


class TestBatchPersonResponse:
    def test_defaults(self):
        r = BatchPersonResponse(operation_type="create", total=5, succeeded=5, failed=0)
        assert r.results == []
        assert r.dry_run is False
        assert r.created_ids is None
