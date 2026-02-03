"""Tests for swap validation helper utilities."""

from datetime import date, timedelta
from typing import cast
from uuid import uuid4

import pytest

from app.models.assignment import Assignment
from app.models.swap import SwapRecord, SwapType
from app.services.swap.validation.compliance_checker import ACGMEComplianceChecker
from app.services.swap.validation.pre_swap_validator import PreSwapValidator


def test_calculate_weekly_hours_splits_evenly() -> None:
    checker = ACGMEComplianceChecker(db=None)  # type: ignore[arg-type]

    assignments = cast(list[Assignment], [object()] * 8)
    weekly_hours = checker._calculate_weekly_hours(assignments)

    assert weekly_hours == [20.0, 20.0, 20.0, 20.0]


@pytest.mark.asyncio
async def test_pre_swap_quick_validate_rejects_past_week(monkeypatch) -> None:
    validator = PreSwapValidator(db=None)  # type: ignore[arg-type]

    async def always_true(_faculty_id):
        return True

    monkeypatch.setattr(validator, "_faculty_exists", always_true)

    swap = SwapRecord(
        id=uuid4(),
        source_faculty_id=uuid4(),
        target_faculty_id=uuid4(),
        source_week=date.today() - timedelta(days=1),
        target_week=None,
        swap_type=SwapType.ONE_TO_ONE,
    )

    assert await validator.quick_validate(swap) is False


@pytest.mark.asyncio
async def test_pre_swap_quick_validate_accepts_future_week(monkeypatch) -> None:
    validator = PreSwapValidator(db=None)  # type: ignore[arg-type]

    async def always_true(_faculty_id):
        return True

    monkeypatch.setattr(validator, "_faculty_exists", always_true)

    swap = SwapRecord(
        id=uuid4(),
        source_faculty_id=uuid4(),
        target_faculty_id=uuid4(),
        source_week=date.today() + timedelta(days=14),
        target_week=None,
        swap_type=SwapType.ONE_TO_ONE,
    )

    assert await validator.quick_validate(swap) is True
