"""Tests for rosetta_parser utility functions (grouping/filtering, no xlsx needed)."""

import pytest
from datetime import date

from app.utils.rosetta_parser import (
    RosettaAssignment,
    get_rosetta_by_resident,
    get_rosetta_by_date,
    get_wednesday_am_assignments,
    get_last_wednesday_assignments,
)


@pytest.fixture
def sample_assignments():
    """Create sample RosettaAssignment data for testing."""
    return [
        RosettaAssignment(
            resident="Smith",
            pgy=1,
            rotation1="FMC",
            rotation2=None,
            date=date(2026, 3, 12),  # Thursday
            time_of_day="AM",
            expected_code="C",
        ),
        RosettaAssignment(
            resident="Smith",
            pgy=1,
            rotation1="FMC",
            rotation2=None,
            date=date(2026, 3, 12),
            time_of_day="PM",
            expected_code="KAP",
        ),
        RosettaAssignment(
            resident="Jones",
            pgy=2,
            rotation1="IM",
            rotation2=None,
            date=date(2026, 3, 12),
            time_of_day="AM",
            expected_code="I",
        ),
        RosettaAssignment(
            resident="Smith",
            pgy=1,
            rotation1="FMC",
            rotation2=None,
            date=date(2026, 3, 18),  # Wednesday
            time_of_day="AM",
            expected_code="C",
        ),
        RosettaAssignment(
            resident="Jones",
            pgy=2,
            rotation1="IM",
            rotation2=None,
            date=date(2026, 3, 18),  # Wednesday
            time_of_day="AM",
            expected_code="LEC",
        ),
        RosettaAssignment(
            resident="Jones",
            pgy=2,
            rotation1="IM",
            rotation2=None,
            date=date(2026, 3, 18),  # Wednesday
            time_of_day="PM",
            expected_code="I",
        ),
        # Last Wednesday assignment
        RosettaAssignment(
            resident="Smith",
            pgy=1,
            rotation1="FMC",
            rotation2=None,
            date=date(2026, 4, 8),  # Last Wednesday
            time_of_day="AM",
            expected_code="LEC",
        ),
    ]


class TestGetRosettaByResident:
    def test_groups_by_resident(self, sample_assignments):
        result = get_rosetta_by_resident(sample_assignments)
        assert "Smith" in result
        assert "Jones" in result
        assert len(result["Smith"]) == 4
        assert len(result["Jones"]) == 3

    def test_empty_list(self):
        result = get_rosetta_by_resident([])
        assert result == {}

    def test_single_resident(self, sample_assignments):
        single = [a for a in sample_assignments if a.resident == "Smith"]
        result = get_rosetta_by_resident(single)
        assert len(result) == 1
        assert "Smith" in result


class TestGetRosettaByDate:
    def test_groups_by_date(self, sample_assignments):
        result = get_rosetta_by_date(sample_assignments)
        assert date(2026, 3, 12) in result
        assert date(2026, 3, 18) in result
        assert len(result[date(2026, 3, 12)]) == 3
        assert len(result[date(2026, 3, 18)]) == 3

    def test_empty_list(self):
        result = get_rosetta_by_date([])
        assert result == {}


class TestGetWednesdayAmAssignments:
    def test_filters_wednesday_am(self, sample_assignments):
        result = get_wednesday_am_assignments(sample_assignments)
        assert len(result) == 3  # 2 on Mar 18 Wed AM + 1 on Apr 8 Wed AM
        for a in result:
            assert a.date.weekday() == 2
            assert a.time_of_day == "AM"

    def test_filters_by_pgy(self, sample_assignments):
        result = get_wednesday_am_assignments(sample_assignments, pgy_filter=1)
        assert len(result) == 2  # Smith has 2 Wednesday AM
        for a in result:
            assert a.pgy == 1

    def test_filters_pgy2(self, sample_assignments):
        result = get_wednesday_am_assignments(sample_assignments, pgy_filter=2)
        assert len(result) == 1
        assert result[0].resident == "Jones"

    def test_empty_list(self):
        result = get_wednesday_am_assignments([])
        assert result == []


class TestGetLastWednesdayAssignments:
    def test_gets_apr8_assignments(self, sample_assignments):
        result = get_last_wednesday_assignments(sample_assignments)
        assert len(result) == 1
        assert result[0].date == date(2026, 4, 8)
        assert result[0].expected_code == "LEC"

    def test_empty_when_no_match(self):
        assignments = [
            RosettaAssignment(
                resident="Test",
                pgy=1,
                rotation1="FMC",
                rotation2=None,
                date=date(2026, 3, 12),
                time_of_day="AM",
                expected_code="C",
            ),
        ]
        result = get_last_wednesday_assignments(assignments)
        assert result == []

    def test_empty_list(self):
        result = get_last_wednesday_assignments([])
        assert result == []


class TestRosettaAssignment:
    def test_namedtuple_fields(self):
        a = RosettaAssignment(
            resident="Test",
            pgy=1,
            rotation1="FMC",
            rotation2=None,
            date=date(2026, 3, 12),
            time_of_day="AM",
            expected_code="C",
        )
        assert a.resident == "Test"
        assert a.pgy == 1
        assert a.rotation1 == "FMC"
        assert a.rotation2 is None
        assert a.date == date(2026, 3, 12)
        assert a.time_of_day == "AM"
        assert a.expected_code == "C"

    def test_equality(self):
        a1 = RosettaAssignment("A", 1, "FMC", None, date(2026, 3, 12), "AM", "C")
        a2 = RosettaAssignment("A", 1, "FMC", None, date(2026, 3, 12), "AM", "C")
        assert a1 == a2
