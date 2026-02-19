from datetime import date
from uuid import uuid4

import pytest

from app.models.assignment import Assignment
from app.models.schedule_draft import DraftSourceType, ScheduleDraft
from app.services.schedule_draft_service import ScheduleDraftService


def test_add_solver_assignments_raises_when_block_missing(db):
    draft = ScheduleDraft(
        id=uuid4(),
        target_block=10,
        target_start_date=date(2025, 1, 1),
        target_end_date=date(2025, 1, 28),
        source_type=DraftSourceType.SOLVER,
    )
    db.add(draft)
    db.commit()

    assignment = Assignment(
        id=uuid4(),
        block_id=uuid4(),
        person_id=uuid4(),
        role="primary",
    )

    service = ScheduleDraftService(db)

    with pytest.raises(ValueError, match="block_id"):
        service.add_solver_assignments_to_draft_sync(draft.id, [assignment])
