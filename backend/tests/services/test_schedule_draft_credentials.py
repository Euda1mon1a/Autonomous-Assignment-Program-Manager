from datetime import date, datetime
from uuid import uuid4

import pytest

from app.models.activity import Activity
from app.models.person import Person
from app.models.procedure import Procedure
from app.models.procedure_credential import ProcedureCredential
from app.models.schedule_draft import (
    DraftFlagType,
    DraftSourceType,
    ScheduleDraft,
    ScheduleDraftFlag,
    ScheduleDraftStatus,
)
from app.models.user import User
from app.services.schedule_draft_service import ScheduleDraftService


@pytest.mark.asyncio
async def test_missing_credential_flag_blocks_publish(db, sample_faculty: Person):
    user = User(
        id=uuid4(),
        username="admin_user",
        email="admin@example.com",
        hashed_password="hashed",
        role="admin",
    )
    procedure = Procedure(name="Vasectomy", specialty="Urology")
    activity = Activity(
        name="Vasectomy Clinic",
        code="vas",
        display_abbreviation="VAS",
        activity_category="clinical",
        procedure_id=procedure.id,
    )
    db.add_all([user, procedure, activity])
    db.commit()

    draft = ScheduleDraft(
        id=uuid4(),
        created_at=datetime.utcnow(),
        created_by_id=user.id,
        target_start_date=date.today(),
        target_end_date=date.today(),
        status=ScheduleDraftStatus.DRAFT,
        source_type=DraftSourceType.SOLVER,
        change_summary={"added": 0, "modified": 0, "deleted": 0},
        flags_total=0,
        flags_acknowledged=0,
    )
    db.add(draft)
    db.commit()

    service = ScheduleDraftService(db)
    await service.add_assignment_to_draft(
        draft_id=draft.id,
        person_id=sample_faculty.id,
        assignment_date=date.today(),
        time_of_day="AM",
        activity_code="vas",
    )

    flags = (
        db.query(ScheduleDraftFlag)
        .filter(
            ScheduleDraftFlag.draft_id == draft.id,
            ScheduleDraftFlag.flag_type == DraftFlagType.CREDENTIAL_MISSING,
        )
        .all()
    )
    assert len(flags) == 1

    result = await service.publish_draft(
        draft_id=draft.id,
        published_by_id=user.id,
        override_comment=None,
        validate_acgme=False,
    )
    assert result.success is False
    assert result.error_code == "FLAGS_UNACKNOWLEDGED"


@pytest.mark.asyncio
async def test_valid_credential_no_flag(db, sample_faculty: Person):
    user = User(
        id=uuid4(),
        username="admin_user",
        email="admin2@example.com",
        hashed_password="hashed",
        role="admin",
    )
    procedure = Procedure(name="Sports Med", specialty="Sports")
    activity = Activity(
        name="Sports Med Clinic",
        code="smc",
        display_abbreviation="SMC",
        activity_category="clinical",
        procedure_id=procedure.id,
    )
    credential = ProcedureCredential(
        person_id=sample_faculty.id,
        procedure_id=procedure.id,
        status="active",
    )
    db.add_all([user, procedure, activity, credential])
    db.commit()

    draft = ScheduleDraft(
        id=uuid4(),
        created_at=datetime.utcnow(),
        created_by_id=user.id,
        target_start_date=date.today(),
        target_end_date=date.today(),
        status=ScheduleDraftStatus.DRAFT,
        source_type=DraftSourceType.SOLVER,
        change_summary={"added": 0, "modified": 0, "deleted": 0},
        flags_total=0,
        flags_acknowledged=0,
    )
    db.add(draft)
    db.commit()

    service = ScheduleDraftService(db)
    await service.add_assignment_to_draft(
        draft_id=draft.id,
        person_id=sample_faculty.id,
        assignment_date=date.today(),
        time_of_day="PM",
        activity_code="smc",
    )

    flags = (
        db.query(ScheduleDraftFlag)
        .filter(
            ScheduleDraftFlag.draft_id == draft.id,
            ScheduleDraftFlag.flag_type == DraftFlagType.CREDENTIAL_MISSING,
        )
        .all()
    )
    assert len(flags) == 0
