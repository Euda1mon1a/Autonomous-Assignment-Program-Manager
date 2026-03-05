"""Tests for learner schedule generator."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.scheduling.learner_generator import (
    FMIT_WEEK_TEMPLATE,
    WEEKLY_TEMPLATE,
    get_block_week_number,
)


class TestWeeklyTemplate:
    def test_template_has_10_slots(self):
        assert len(WEEKLY_TEMPLATE) == 10

    def test_asm_on_wednesday_am(self):
        asm_slots = [(d, t, a) for d, t, a in WEEKLY_TEMPLATE if a == "ASM"]
        assert len(asm_slots) == 1
        assert asm_slots[0] == (2, "AM", "ASM")

    def test_didactics_on_friday_pm(self):
        didactic_slots = [(d, t, a) for d, t, a in WEEKLY_TEMPLATE if a == "didactics"]
        assert len(didactic_slots) == 1
        assert didactic_slots[0] == (4, "PM", "didactics")

    def test_fmit_template_covers_all_slots(self):
        assert len(FMIT_WEEK_TEMPLATE) == 10  # 5 days * 2 half-days
        assert all(a == "FMIT" for _, _, a in FMIT_WEEK_TEMPLATE)


class TestGetBlockWeekNumber:
    def test_no_start_date(self):
        block = MagicMock()
        block.start_date = None
        assert get_block_week_number(block) == 1

    def test_block_number_mod4(self):
        block = MagicMock()
        block.start_date = "2026-01-01"
        block.block_number = 1
        assert get_block_week_number(block) == 1

        block.block_number = 4
        assert get_block_week_number(block) == 4

        block.block_number = 5
        assert get_block_week_number(block) == 1

        block.block_number = 8
        assert get_block_week_number(block) == 4

    def test_no_block_number(self):
        block = MagicMock()
        block.start_date = "2026-01-01"
        block.block_number = None
        assert get_block_week_number(block) == 1
