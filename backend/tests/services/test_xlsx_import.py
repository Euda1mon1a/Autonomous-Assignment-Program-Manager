"""
Comprehensive edge case tests for xlsx_import service.

Tests all dataclasses, enums, and helper methods without requiring openpyxl fixtures.
"""
from datetime import date, timedelta

import pytest

from app.services.xlsx_import import (
    ScheduleConflict,
    ScheduleSlot,
    SlotType,
    ProviderSchedule,
    ImportResult,
    ClinicScheduleImporter,
    has_back_to_back_conflict,
    count_alternating_cycles,
    get_schedule_flexibility,
)


class TestSlotTypeEnum:
    """Test SlotType enum values."""

    def test_all_slot_types_exist(self):
        """Test that all expected slot types are defined."""
        assert SlotType.CLINIC.value == "clinic"
        assert SlotType.FMIT.value == "fmit"
        assert SlotType.OFF.value == "off"
        assert SlotType.VACATION.value == "vacation"
        assert SlotType.CONFERENCE.value == "conference"
        assert SlotType.ADMIN.value == "admin"
        assert SlotType.UNKNOWN.value == "unknown"

    def test_enum_equality(self):
        """Test enum equality comparisons."""
        assert SlotType.CLINIC == SlotType.CLINIC
        assert SlotType.CLINIC != SlotType.FMIT

    def test_enum_in_collection(self):
        """Test enum membership in collections."""
        slot_types = {SlotType.CLINIC, SlotType.FMIT}
        assert SlotType.CLINIC in slot_types
        assert SlotType.VACATION not in slot_types


class TestScheduleSlot:
    """Test ScheduleSlot dataclass."""

    def test_basic_creation(self):
        """Test creating a basic schedule slot."""
        slot = ScheduleSlot(
            provider_name="Dr. Smith",
            date=date(2024, 1, 15),
            time_of_day="AM",
            slot_type=SlotType.CLINIC,
            raw_value="C",
        )

        assert slot.provider_name == "Dr. Smith"
        assert slot.date == date(2024, 1, 15)
        assert slot.time_of_day == "AM"
        assert slot.slot_type == SlotType.CLINIC
        assert slot.raw_value == "C"
        assert slot.location is None
        assert slot.notes is None

    def test_slot_with_optional_fields(self):
        """Test slot creation with location and notes."""
        slot = ScheduleSlot(
            provider_name="Dr. Jones",
            date=date(2024, 2, 20),
            time_of_day="PM",
            slot_type=SlotType.FMIT,
            raw_value="FMIT",
            location="Main Hospital",
            notes="Weekend coverage",
        )

        assert slot.location == "Main Hospital"
        assert slot.notes == "Weekend coverage"

    def test_key_property(self):
        """Test that key property generates unique identifier."""
        slot = ScheduleSlot(
            provider_name="Dr. Smith",
            date=date(2024, 1, 15),
            time_of_day="AM",
            slot_type=SlotType.CLINIC,
            raw_value="C",
        )

        expected_key = ("Dr. Smith", date(2024, 1, 15), "AM")
        assert slot.key == expected_key

    def test_key_uniqueness(self):
        """Test that different slots have different keys."""
        slot1 = ScheduleSlot(
            provider_name="Dr. Smith",
            date=date(2024, 1, 15),
            time_of_day="AM",
            slot_type=SlotType.CLINIC,
            raw_value="C",
        )

        slot2 = ScheduleSlot(
            provider_name="Dr. Smith",
            date=date(2024, 1, 15),
            time_of_day="PM",
            slot_type=SlotType.CLINIC,
            raw_value="C",
        )

        assert slot1.key != slot2.key

    def test_key_consistency(self):
        """Test that key remains consistent across multiple calls."""
        slot = ScheduleSlot(
            provider_name="Dr. Test",
            date=date(2024, 3, 1),
            time_of_day="AM",
            slot_type=SlotType.OFF,
            raw_value="OFF",
        )

        key1 = slot.key
        key2 = slot.key
        assert key1 == key2
        assert key1 is not key2  # Different tuple instances


class TestScheduleConflict:
    """Test ScheduleConflict dataclass and message generation."""

    def test_double_book_message(self):
        """Test message generation for double-booking conflict."""
        conflict = ScheduleConflict(
            provider_name="Dr. Smith",
            date=date(2024, 1, 15),
            time_of_day="AM",
            conflict_type="double_book",
            fmit_assignment="FMIT",
            clinic_assignment="CC",
            severity="error",
        )

        assert "Dr. Smith" in conflict.message
        assert "double-booked" in conflict.message
        assert "FMIT=FMIT" in conflict.message
        assert "Clinic=CC" in conflict.message
        assert "Mon Jan 15" in conflict.message or "Mon Jan 15" in conflict.message

    def test_fmit_clinic_overlap_message(self):
        """Test message generation for FMIT/clinic overlap."""
        conflict = ScheduleConflict(
            provider_name="Dr. Jones",
            date=date(2024, 2, 20),
            time_of_day="PM",
            conflict_type="fmit_clinic_overlap",
            severity="warning",
        )

        assert "Dr. Jones" in conflict.message
        assert "FMIT during clinic" in conflict.message
        assert "Tue Feb 20" in conflict.message or "Tue Feb 20" in conflict.message

    def test_specialty_unavailable_message(self):
        """Test message generation for specialty provider unavailable."""
        conflict = ScheduleConflict(
            provider_name="Dr. FAC-SPORTS",
            date=date(2024, 3, 10),
            time_of_day="AM",
            conflict_type="specialty_unavailable",
            severity="warning",
        )

        assert "Dr. FAC-SPORTS" in conflict.message
        assert "specialty provider" in conflict.message
        assert "unavailable for clinic" in conflict.message

    def test_consecutive_weeks_message(self):
        """Test message generation for consecutive weeks pattern."""
        conflict = ScheduleConflict(
            provider_name="Dr. Lee",
            date=date(2024, 4, 1),
            time_of_day="AM",
            conflict_type="consecutive_weeks",
            severity="warning",
        )

        assert "Dr. Lee" in conflict.message
        assert "alternating week pattern" in conflict.message
        assert "family hardship" in conflict.message

    def test_custom_message(self):
        """Test that custom message is preserved."""
        custom_msg = "Custom conflict description"
        conflict = ScheduleConflict(
            provider_name="Dr. Custom",
            date=date(2024, 5, 1),
            time_of_day="PM",
            conflict_type="unknown",
            message=custom_msg,
        )

        assert conflict.message == custom_msg

    def test_unknown_conflict_type_message(self):
        """Test fallback message for unknown conflict types."""
        conflict = ScheduleConflict(
            provider_name="Dr. Unknown",
            date=date(2024, 6, 1),
            time_of_day="AM",
            conflict_type="weird_conflict",
        )

        assert "Dr. Unknown" in conflict.message
        assert "Conflict for" in conflict.message

    def test_severity_levels(self):
        """Test different severity levels."""
        error = ScheduleConflict(
            provider_name="Dr. Error",
            date=date(2024, 1, 1),
            time_of_day="AM",
            conflict_type="double_book",
            severity="error",
        )
        assert error.severity == "error"

        warning = ScheduleConflict(
            provider_name="Dr. Warning",
            date=date(2024, 1, 1),
            time_of_day="AM",
            conflict_type="specialty_unavailable",
            severity="warning",
        )
        assert warning.severity == "warning"

        info = ScheduleConflict(
            provider_name="Dr. Info",
            date=date(2024, 1, 1),
            time_of_day="AM",
            conflict_type="consecutive_weeks",
            severity="info",
        )
        assert info.severity == "info"


class TestProviderSchedule:
    """Test ProviderSchedule dataclass."""

    def test_empty_schedule(self):
        """Test creating an empty provider schedule."""
        schedule = ProviderSchedule(name="Dr. Empty")

        assert schedule.name == "Dr. Empty"
        assert len(schedule.specialties) == 0
        assert len(schedule.slots) == 0

    def test_add_slot(self):
        """Test adding slots to a schedule."""
        schedule = ProviderSchedule(name="Dr. Test")

        slot1 = ScheduleSlot(
            provider_name="Dr. Test",
            date=date(2024, 1, 15),
            time_of_day="AM",
            slot_type=SlotType.CLINIC,
            raw_value="C",
        )

        schedule.add_slot(slot1)
        assert len(schedule.slots) == 1

    def test_get_slot_exists(self):
        """Test retrieving an existing slot."""
        schedule = ProviderSchedule(name="Dr. Test")

        slot = ScheduleSlot(
            provider_name="Dr. Test",
            date=date(2024, 1, 15),
            time_of_day="AM",
            slot_type=SlotType.CLINIC,
            raw_value="C",
        )

        schedule.add_slot(slot)
        retrieved = schedule.get_slot(date(2024, 1, 15), "AM")

        assert retrieved is not None
        assert retrieved.slot_type == SlotType.CLINIC

    def test_get_slot_not_exists(self):
        """Test retrieving a non-existent slot returns None."""
        schedule = ProviderSchedule(name="Dr. Test")

        retrieved = schedule.get_slot(date(2024, 1, 15), "AM")
        assert retrieved is None

    def test_get_slot_wrong_time(self):
        """Test that different times of day are treated separately."""
        schedule = ProviderSchedule(name="Dr. Test")

        am_slot = ScheduleSlot(
            provider_name="Dr. Test",
            date=date(2024, 1, 15),
            time_of_day="AM",
            slot_type=SlotType.CLINIC,
            raw_value="C",
        )

        schedule.add_slot(am_slot)

        # Same date, different time
        retrieved = schedule.get_slot(date(2024, 1, 15), "PM")
        assert retrieved is None

    def test_slot_overwrite(self):
        """Test that adding a slot with same key overwrites previous."""
        schedule = ProviderSchedule(name="Dr. Test")

        slot1 = ScheduleSlot(
            provider_name="Dr. Test",
            date=date(2024, 1, 15),
            time_of_day="AM",
            slot_type=SlotType.CLINIC,
            raw_value="C",
        )

        slot2 = ScheduleSlot(
            provider_name="Dr. Test",
            date=date(2024, 1, 15),
            time_of_day="AM",
            slot_type=SlotType.FMIT,
            raw_value="FMIT",
        )

        schedule.add_slot(slot1)
        schedule.add_slot(slot2)

        assert len(schedule.slots) == 1
        retrieved = schedule.get_slot(date(2024, 1, 15), "AM")
        assert retrieved.slot_type == SlotType.FMIT

    def test_get_fmit_weeks_empty(self):
        """Test get_fmit_weeks with no FMIT slots."""
        schedule = ProviderSchedule(name="Dr. Test")

        weeks = schedule.get_fmit_weeks()
        assert len(weeks) == 0

    def test_get_fmit_weeks_single_week(self):
        """Test get_fmit_weeks with slots in a single week."""
        schedule = ProviderSchedule(name="Dr. Test")

        # Monday through Friday of same week
        for day_offset in range(5):
            slot = ScheduleSlot(
                provider_name="Dr. Test",
                date=date(2024, 1, 15) + timedelta(days=day_offset),  # Mon-Fri
                time_of_day="AM",
                slot_type=SlotType.FMIT,
                raw_value="FMIT",
            )
            schedule.add_slot(slot)

        weeks = schedule.get_fmit_weeks()
        assert len(weeks) == 1
        # Should be Monday-Sunday of that week
        assert weeks[0][0] == date(2024, 1, 15)  # Monday
        assert weeks[0][1] == date(2024, 1, 21)  # Sunday

    def test_get_fmit_weeks_multiple_weeks(self):
        """Test get_fmit_weeks with slots in different weeks."""
        schedule = ProviderSchedule(name="Dr. Test")

        # Week 1: Jan 15-21 (Monday-Sunday)
        slot1 = ScheduleSlot(
            provider_name="Dr. Test",
            date=date(2024, 1, 15),  # Monday
            time_of_day="AM",
            slot_type=SlotType.FMIT,
            raw_value="FMIT",
        )
        schedule.add_slot(slot1)

        # Week 2: Jan 29 - Feb 4 (skip one week)
        slot2 = ScheduleSlot(
            provider_name="Dr. Test",
            date=date(2024, 1, 29),  # Monday
            time_of_day="AM",
            slot_type=SlotType.FMIT,
            raw_value="FMIT",
        )
        schedule.add_slot(slot2)

        weeks = schedule.get_fmit_weeks()
        assert len(weeks) == 2
        assert weeks[0][0] == date(2024, 1, 15)
        assert weeks[1][0] == date(2024, 1, 29)

    def test_get_fmit_weeks_ignores_non_fmit(self):
        """Test that get_fmit_weeks ignores non-FMIT slots."""
        schedule = ProviderSchedule(name="Dr. Test")

        fmit_slot = ScheduleSlot(
            provider_name="Dr. Test",
            date=date(2024, 1, 15),
            time_of_day="AM",
            slot_type=SlotType.FMIT,
            raw_value="FMIT",
        )
        schedule.add_slot(fmit_slot)

        clinic_slot = ScheduleSlot(
            provider_name="Dr. Test",
            date=date(2024, 1, 22),
            time_of_day="AM",
            slot_type=SlotType.CLINIC,
            raw_value="C",
        )
        schedule.add_slot(clinic_slot)

        weeks = schedule.get_fmit_weeks()
        assert len(weeks) == 1  # Only counts FMIT week

    def test_get_fmit_weeks_mid_week_start(self):
        """Test get_fmit_weeks when FMIT starts mid-week."""
        schedule = ProviderSchedule(name="Dr. Test")

        # Wednesday of a week
        slot = ScheduleSlot(
            provider_name="Dr. Test",
            date=date(2024, 1, 17),  # Wednesday
            time_of_day="AM",
            slot_type=SlotType.FMIT,
            raw_value="FMIT",
        )
        schedule.add_slot(slot)

        weeks = schedule.get_fmit_weeks()
        assert len(weeks) == 1
        # Should still be Monday-Sunday of that week
        assert weeks[0][0] == date(2024, 1, 15)  # Monday
        assert weeks[0][1] == date(2024, 1, 21)  # Sunday

    def test_has_alternating_pattern_empty(self):
        """Test has_alternating_pattern with no FMIT weeks."""
        schedule = ProviderSchedule(name="Dr. Test")
        assert schedule.has_alternating_pattern() is False

    def test_has_alternating_pattern_too_few_weeks(self):
        """Test has_alternating_pattern with fewer than 3 weeks."""
        schedule = ProviderSchedule(name="Dr. Test")

        # Two weeks
        for week_offset in [0, 14]:
            slot = ScheduleSlot(
                provider_name="Dr. Test",
                date=date(2024, 1, 15) + timedelta(days=week_offset),
                time_of_day="AM",
                slot_type=SlotType.FMIT,
                raw_value="FMIT",
            )
            schedule.add_slot(slot)

        assert schedule.has_alternating_pattern() is False

    def test_has_alternating_pattern_true(self):
        """Test has_alternating_pattern detects week-on/week-off."""
        schedule = ProviderSchedule(name="Dr. Test")

        # Week 1, skip week 2, week 3, skip week 4, week 5
        # This creates alternating pattern
        week_dates = [
            date(2024, 1, 15),   # Week 1 (Mon)
            date(2024, 1, 29),   # Week 3 (skip week 2)
            date(2024, 2, 12),   # Week 5 (skip week 4)
        ]

        for d in week_dates:
            slot = ScheduleSlot(
                provider_name="Dr. Test",
                date=d,
                time_of_day="AM",
                slot_type=SlotType.FMIT,
                raw_value="FMIT",
            )
            schedule.add_slot(slot)

        assert schedule.has_alternating_pattern() is True

    def test_has_alternating_pattern_consecutive_false(self):
        """Test has_alternating_pattern returns false for consecutive weeks."""
        schedule = ProviderSchedule(name="Dr. Test")

        # Three consecutive weeks
        for week_offset in [0, 7, 14]:
            slot = ScheduleSlot(
                provider_name="Dr. Test",
                date=date(2024, 1, 15) + timedelta(days=week_offset),
                time_of_day="AM",
                slot_type=SlotType.FMIT,
                raw_value="FMIT",
            )
            schedule.add_slot(slot)

        # Consecutive is not alternating
        assert schedule.has_alternating_pattern() is False

    def test_has_alternating_pattern_wide_gaps_false(self):
        """Test has_alternating_pattern returns false for wide gaps."""
        schedule = ProviderSchedule(name="Dr. Test")

        # Weeks with large gaps (more than 2 weeks)
        week_dates = [
            date(2024, 1, 15),   # Week 1
            date(2024, 2, 5),    # Week 4 (3 week gap)
            date(2024, 2, 26),   # Week 7 (3 week gap)
        ]

        for d in week_dates:
            slot = ScheduleSlot(
                provider_name="Dr. Test",
                date=d,
                time_of_day="AM",
                slot_type=SlotType.FMIT,
                raw_value="FMIT",
            )
            schedule.add_slot(slot)

        # Gaps too large for alternating pattern
        assert schedule.has_alternating_pattern() is False

    def test_has_alternating_pattern_boundary(self):
        """Test has_alternating_pattern at boundaries (6-8 day gaps)."""
        schedule = ProviderSchedule(name="Dr. Test")

        # Exactly 7 day gap (boundary case)
        week_dates = [
            date(2024, 1, 15),   # Week 1 (Mon)
            date(2024, 1, 29),   # Week 3 (14 days later = 7 day gap after week 1 ends)
            date(2024, 2, 12),   # Week 5
        ]

        for d in week_dates:
            slot = ScheduleSlot(
                provider_name="Dr. Test",
                date=d,
                time_of_day="AM",
                slot_type=SlotType.FMIT,
                raw_value="FMIT",
            )
            schedule.add_slot(slot)

        assert schedule.has_alternating_pattern() is True

    def test_specialties_list(self):
        """Test provider with specialties."""
        schedule = ProviderSchedule(
            name="Dr. Specialist",
            specialties=["Sports Medicine", "Orthopedics"]
        )

        assert len(schedule.specialties) == 2
        assert "Sports Medicine" in schedule.specialties


class TestImportResult:
    """Test ImportResult dataclass."""

    def test_empty_result(self):
        """Test creating an empty result."""
        result = ImportResult(success=True)

        assert result.success is True
        assert len(result.providers) == 0
        assert len(result.conflicts) == 0
        assert len(result.warnings) == 0
        assert len(result.errors) == 0
        assert result.total_slots == 0
        assert result.clinic_slots == 0
        assert result.fmit_slots == 0
        assert result.date_range == (None, None)

    def test_failed_result(self):
        """Test creating a failed result."""
        result = ImportResult(success=False, errors=["File not found"])

        assert result.success is False
        assert len(result.errors) == 1
        assert result.errors[0] == "File not found"

    def test_add_conflict(self):
        """Test adding conflicts to result."""
        result = ImportResult(success=True)

        conflict = ScheduleConflict(
            provider_name="Dr. Test",
            date=date(2024, 1, 15),
            time_of_day="AM",
            conflict_type="double_book",
        )

        result.add_conflict(conflict)
        assert len(result.conflicts) == 1

    def test_get_conflicts_by_provider(self):
        """Test filtering conflicts by provider name."""
        result = ImportResult(success=True)

        conflict1 = ScheduleConflict(
            provider_name="Dr. Smith",
            date=date(2024, 1, 15),
            time_of_day="AM",
            conflict_type="double_book",
        )

        conflict2 = ScheduleConflict(
            provider_name="Dr. Jones",
            date=date(2024, 1, 16),
            time_of_day="PM",
            conflict_type="specialty_unavailable",
        )

        conflict3 = ScheduleConflict(
            provider_name="Dr. Smith",
            date=date(2024, 1, 17),
            time_of_day="AM",
            conflict_type="consecutive_weeks",
        )

        result.add_conflict(conflict1)
        result.add_conflict(conflict2)
        result.add_conflict(conflict3)

        smith_conflicts = result.get_conflicts_by_provider("Dr. Smith")
        assert len(smith_conflicts) == 2
        assert all(c.provider_name == "Dr. Smith" for c in smith_conflicts)

        jones_conflicts = result.get_conflicts_by_provider("Dr. Jones")
        assert len(jones_conflicts) == 1

    def test_get_conflicts_by_provider_none(self):
        """Test getting conflicts for provider with no conflicts."""
        result = ImportResult(success=True)

        conflicts = result.get_conflicts_by_provider("Dr. NotFound")
        assert len(conflicts) == 0

    def test_get_conflicts_by_type(self):
        """Test filtering conflicts by type."""
        result = ImportResult(success=True)

        conflict1 = ScheduleConflict(
            provider_name="Dr. Smith",
            date=date(2024, 1, 15),
            time_of_day="AM",
            conflict_type="double_book",
        )

        conflict2 = ScheduleConflict(
            provider_name="Dr. Jones",
            date=date(2024, 1, 16),
            time_of_day="PM",
            conflict_type="double_book",
        )

        conflict3 = ScheduleConflict(
            provider_name="Dr. Lee",
            date=date(2024, 1, 17),
            time_of_day="AM",
            conflict_type="specialty_unavailable",
        )

        result.add_conflict(conflict1)
        result.add_conflict(conflict2)
        result.add_conflict(conflict3)

        double_books = result.get_conflicts_by_type("double_book")
        assert len(double_books) == 2
        assert all(c.conflict_type == "double_book" for c in double_books)

        specialty = result.get_conflicts_by_type("specialty_unavailable")
        assert len(specialty) == 1

    def test_get_conflicts_by_type_none(self):
        """Test getting conflicts for non-existent type."""
        result = ImportResult(success=True)

        conflicts = result.get_conflicts_by_type("nonexistent")
        assert len(conflicts) == 0

    def test_statistics_fields(self):
        """Test that statistics fields can be set."""
        result = ImportResult(
            success=True,
            total_slots=100,
            clinic_slots=60,
            fmit_slots=30,
            date_range=(date(2024, 1, 1), date(2024, 12, 31))
        )

        assert result.total_slots == 100
        assert result.clinic_slots == 60
        assert result.fmit_slots == 30
        assert result.date_range[0] == date(2024, 1, 1)
        assert result.date_range[1] == date(2024, 12, 31)

    def test_warnings_list(self):
        """Test adding warnings to result."""
        result = ImportResult(
            success=True,
            warnings=["Duplicate provider names found", "Missing dates"]
        )

        assert len(result.warnings) == 2
        assert "Duplicate provider names" in result.warnings[0]


class TestSlotTypeMapping:
    """Test SLOT_TYPE_MAPPING for all slot types."""

    def test_clinic_mappings(self):
        """Test all clinic slot type mappings."""
        importer = ClinicScheduleImporter()

        clinic_codes = ["c", "cc", "clc", "clinic", "cv", "pts", "patient", "appt",
                        "sm", "asm", "sports", "pr", "vas", "pedc", "pedsp",
                        "hv", "hc", "c-i", "rcc"]

        for code in clinic_codes:
            result = importer.classify_slot(code)
            assert result == SlotType.CLINIC, f"Failed for code: {code}"

    def test_fmit_mappings(self):
        """Test all FMIT slot type mappings."""
        importer = ClinicScheduleImporter()

        fmit_codes = ["fmit", "nf", "nicu", "pedw", "imw", "inpt", "inpatient",
                      "ward", "wards", "er", "kap", "straub", "oic"]

        for code in fmit_codes:
            result = importer.classify_slot(code)
            assert result == SlotType.FMIT, f"Failed for code: {code}"

    def test_off_mappings(self):
        """Test all OFF slot type mappings."""
        importer = ClinicScheduleImporter()

        off_codes = ["off", "pc", "do", "w", "x", "-", "", "fed", "hol"]

        for code in off_codes:
            result = importer.classify_slot(code)
            assert result == SlotType.OFF, f"Failed for code: {code}"

    def test_vacation_mappings(self):
        """Test all vacation slot type mappings."""
        importer = ClinicScheduleImporter()

        vacation_codes = ["vac", "vacation", "lv", "leave", "al", "dep", "tdy"]

        for code in vacation_codes:
            result = importer.classify_slot(code)
            assert result == SlotType.VACATION, f"Failed for code: {code}"

    def test_conference_mappings(self):
        """Test all conference slot type mappings."""
        importer = ClinicScheduleImporter()

        conf_codes = ["conf", "conference", "cme", "mtg", "lec", "sim",
                      "usafp", "hafp", "facdev"]

        for code in conf_codes:
            result = importer.classify_slot(code)
            assert result == SlotType.CONFERENCE, f"Failed for code: {code}"

    def test_admin_mappings(self):
        """Test all admin slot type mappings."""
        importer = ClinicScheduleImporter()

        admin_codes = ["admin", "adm", "office", "gme", "rsh", "pi", "at",
                       "pcat", "fac", "dm", "dfm"]

        for code in admin_codes:
            result = importer.classify_slot(code)
            assert result == SlotType.ADMIN, f"Failed for code: {code}"

    def test_case_insensitive(self):
        """Test that classification is case-insensitive."""
        importer = ClinicScheduleImporter()

        assert importer.classify_slot("CLINIC") == SlotType.CLINIC
        assert importer.classify_slot("Clinic") == SlotType.CLINIC
        assert importer.classify_slot("cLiNiC") == SlotType.CLINIC

    def test_whitespace_handling(self):
        """Test that whitespace is stripped."""
        importer = ClinicScheduleImporter()

        assert importer.classify_slot("  clinic  ") == SlotType.CLINIC
        assert importer.classify_slot("\tfmit\n") == SlotType.FMIT

    def test_none_handling(self):
        """Test that None is treated as OFF."""
        importer = ClinicScheduleImporter()

        assert importer.classify_slot(None) == SlotType.OFF

    def test_number_stripping(self):
        """Test that trailing numbers are stripped."""
        importer = ClinicScheduleImporter()

        assert importer.classify_slot("C30") == SlotType.CLINIC
        assert importer.classify_slot("FMIT2") == SlotType.FMIT
        assert importer.classify_slot("conf123") == SlotType.CONFERENCE

    def test_compound_codes(self):
        """Test compound codes like PC/OFF."""
        importer = ClinicScheduleImporter()

        # Should prioritize restrictive types
        assert importer.classify_slot("PC/OFF") == SlotType.OFF
        assert importer.classify_slot("C/CV") == SlotType.CLINIC
        assert importer.classify_slot("FMIT/VAC") == SlotType.FMIT  # FMIT is restrictive

    def test_prefix_matching(self):
        """Test prefix matching for longer codes."""
        importer = ClinicScheduleImporter()

        # Should match prefixes (2+ chars)
        assert importer.classify_slot("clinic_special") == SlotType.CLINIC
        assert importer.classify_slot("fmit_rotation") == SlotType.FMIT

    def test_fallback_heuristics(self):
        """Test fallback heuristic matching."""
        importer = ClinicScheduleImporter()

        assert importer.classify_slot("on-call") == SlotType.FMIT
        assert importer.classify_slot("specialty clinic") == SlotType.CLINIC
        assert importer.classify_slot("annual leave") == SlotType.VACATION
        assert importer.classify_slot("medical conference") == SlotType.CONFERENCE

    def test_unknown_codes(self):
        """Test that unrecognized codes return UNKNOWN."""
        importer = ClinicScheduleImporter()

        assert importer.classify_slot("xyz123") == SlotType.UNKNOWN
        assert importer.classify_slot("random text") == SlotType.UNKNOWN


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_provider_name(self):
        """Test handling empty provider names."""
        slot = ScheduleSlot(
            provider_name="",
            date=date(2024, 1, 15),
            time_of_day="AM",
            slot_type=SlotType.CLINIC,
            raw_value="C",
        )

        assert slot.provider_name == ""
        assert slot.key == ("", date(2024, 1, 15), "AM")

    def test_date_boundaries(self):
        """Test schedule slots at date boundaries."""
        # Year boundary
        slot = ScheduleSlot(
            provider_name="Dr. Test",
            date=date(2024, 12, 31),
            time_of_day="PM",
            slot_type=SlotType.CLINIC,
            raw_value="C",
        )

        assert slot.date.year == 2024
        assert slot.date.month == 12
        assert slot.date.day == 31

    def test_leap_year_date(self):
        """Test handling leap year dates."""
        slot = ScheduleSlot(
            provider_name="Dr. Test",
            date=date(2024, 2, 29),  # 2024 is leap year
            time_of_day="AM",
            slot_type=SlotType.FMIT,
            raw_value="FMIT",
        )

        assert slot.date == date(2024, 2, 29)

    def test_schedule_with_single_slot(self):
        """Test schedule with exactly one slot."""
        schedule = ProviderSchedule(name="Dr. Single")

        slot = ScheduleSlot(
            provider_name="Dr. Single",
            date=date(2024, 1, 15),
            time_of_day="AM",
            slot_type=SlotType.CLINIC,
            raw_value="C",
        )
        schedule.add_slot(slot)

        assert len(schedule.slots) == 1
        weeks = schedule.get_fmit_weeks()
        assert len(weeks) == 0  # Not FMIT

    def test_schedule_all_same_type(self):
        """Test schedule where all slots are same type."""
        schedule = ProviderSchedule(name="Dr. AllClinic")

        for i in range(10):
            slot = ScheduleSlot(
                provider_name="Dr. AllClinic",
                date=date(2024, 1, 15) + timedelta(days=i),
                time_of_day="AM",
                slot_type=SlotType.CLINIC,
                raw_value="C",
            )
            schedule.add_slot(slot)

        weeks = schedule.get_fmit_weeks()
        assert len(weeks) == 0  # No FMIT weeks

    def test_very_long_raw_value(self):
        """Test handling very long raw values."""
        long_value = "C" * 1000
        slot = ScheduleSlot(
            provider_name="Dr. Test",
            date=date(2024, 1, 15),
            time_of_day="AM",
            slot_type=SlotType.CLINIC,
            raw_value=long_value,
        )

        assert len(slot.raw_value) == 1000

    def test_special_characters_in_provider_name(self):
        """Test provider names with special characters."""
        names = [
            "Dr. O'Brien",
            "Dr. Smith-Jones",
            "Dr. José García",
            "Dr. Müller",
        ]

        for name in names:
            slot = ScheduleSlot(
                provider_name=name,
                date=date(2024, 1, 15),
                time_of_day="AM",
                slot_type=SlotType.CLINIC,
                raw_value="C",
            )
            assert slot.provider_name == name

    def test_multiple_providers_same_schedule(self):
        """Test result with multiple providers."""
        result = ImportResult(success=True)

        result.providers["Dr. A"] = ProviderSchedule(name="Dr. A")
        result.providers["Dr. B"] = ProviderSchedule(name="Dr. B")
        result.providers["Dr. C"] = ProviderSchedule(name="Dr. C")

        assert len(result.providers) == 3


class TestHelperFunctions:
    """Test standalone helper functions."""

    def test_has_back_to_back_conflict_empty(self):
        """Test back-to-back detection with empty list."""
        assert has_back_to_back_conflict([]) is False

    def test_has_back_to_back_conflict_single(self):
        """Test back-to-back detection with single week."""
        weeks = [date(2024, 1, 15)]
        assert has_back_to_back_conflict(weeks) is False

    def test_has_back_to_back_conflict_true(self):
        """Test back-to-back detection with consecutive weeks."""
        weeks = [
            date(2024, 1, 15),  # Week 1
            date(2024, 1, 22),  # Week 2 (7 days later)
        ]
        assert has_back_to_back_conflict(weeks) is True

    def test_has_back_to_back_conflict_false(self):
        """Test back-to-back detection with gap."""
        weeks = [
            date(2024, 1, 15),  # Week 1
            date(2024, 1, 29),  # Week 3 (skip week 2)
        ]
        assert has_back_to_back_conflict(weeks) is False

    def test_has_back_to_back_conflict_unsorted(self):
        """Test that function handles unsorted input."""
        weeks = [
            date(2024, 1, 29),
            date(2024, 1, 15),
            date(2024, 1, 22),
        ]
        assert has_back_to_back_conflict(weeks) is True

    def test_count_alternating_cycles_empty(self):
        """Test alternating cycle count with empty list."""
        assert count_alternating_cycles([]) == 0

    def test_count_alternating_cycles_single(self):
        """Test alternating cycle count with single week."""
        weeks = [date(2024, 1, 15)]
        assert count_alternating_cycles(weeks) == 0

    def test_count_alternating_cycles_no_alternating(self):
        """Test alternating cycle count with consecutive weeks."""
        weeks = [
            date(2024, 1, 15),
            date(2024, 1, 22),
            date(2024, 1, 29),
        ]
        # All consecutive (7 day gaps), not alternating
        assert count_alternating_cycles(weeks) == 0

    def test_count_alternating_cycles_alternating(self):
        """Test alternating cycle count with alternating pattern."""
        weeks = [
            date(2024, 1, 15),   # Week 1
            date(2024, 1, 29),   # Week 3 (14 days = alternating)
            date(2024, 2, 12),   # Week 5 (14 days = alternating)
        ]
        assert count_alternating_cycles(weeks) == 2

    def test_get_schedule_flexibility_past(self):
        """Test flexibility for past dates."""
        past_date = date.today() - timedelta(days=10)
        assert get_schedule_flexibility(past_date) == "impossible"

    def test_get_schedule_flexibility_imminent(self):
        """Test flexibility for imminent dates."""
        imminent = date.today() + timedelta(days=7)
        assert get_schedule_flexibility(imminent) == "very_hard"

    def test_get_schedule_flexibility_hard(self):
        """Test flexibility for dates within release horizon."""
        within_horizon = date.today() + timedelta(days=45)
        flexibility = get_schedule_flexibility(within_horizon, release_horizon_days=90)
        assert flexibility == "hard"

    def test_get_schedule_flexibility_easy(self):
        """Test flexibility for dates beyond release horizon."""
        beyond_horizon = date.today() + timedelta(days=120)
        flexibility = get_schedule_flexibility(beyond_horizon, release_horizon_days=90)
        assert flexibility == "easy"

    def test_get_schedule_flexibility_boundary(self):
        """Test flexibility at exact boundary."""
        boundary = date.today() + timedelta(days=90)
        flexibility = get_schedule_flexibility(boundary, release_horizon_days=90)
        # At exactly release date (90 days), condition is days_until < 90, which is False
        # So it returns "easy" (the else clause)
        assert flexibility == "easy"

    def test_get_schedule_flexibility_today(self):
        """Test flexibility for today."""
        today = date.today()
        assert get_schedule_flexibility(today) == "very_hard"


class TestWeekCalculationBoundaries:
    """Test boundary conditions for week calculations."""

    def test_week_starting_sunday(self):
        """Test week calculation when FMIT slot is on Sunday."""
        schedule = ProviderSchedule(name="Dr. Test")

        # Sunday (weekday=6)
        sunday = date(2024, 1, 21)
        slot = ScheduleSlot(
            provider_name="Dr. Test",
            date=sunday,
            time_of_day="AM",
            slot_type=SlotType.FMIT,
            raw_value="FMIT",
        )
        schedule.add_slot(slot)

        weeks = schedule.get_fmit_weeks()
        assert len(weeks) == 1
        # Should group into Monday-Sunday of that week
        assert weeks[0][0] == date(2024, 1, 15)  # Monday
        assert weeks[0][1] == date(2024, 1, 21)  # Sunday

    def test_week_starting_monday(self):
        """Test week calculation when FMIT slot is on Monday."""
        schedule = ProviderSchedule(name="Dr. Test")

        # Monday (weekday=0)
        monday = date(2024, 1, 15)
        slot = ScheduleSlot(
            provider_name="Dr. Test",
            date=monday,
            time_of_day="AM",
            slot_type=SlotType.FMIT,
            raw_value="FMIT",
        )
        schedule.add_slot(slot)

        weeks = schedule.get_fmit_weeks()
        assert len(weeks) == 1
        assert weeks[0][0] == monday
        assert weeks[0][1] == monday + timedelta(days=6)

    def test_multiple_slots_same_week(self):
        """Test that multiple slots in same week are grouped together."""
        schedule = ProviderSchedule(name="Dr. Test")

        # Add multiple slots throughout the week
        base_date = date(2024, 1, 15)  # Monday
        for i in range(7):  # Mon-Sun
            slot = ScheduleSlot(
                provider_name="Dr. Test",
                date=base_date + timedelta(days=i),
                time_of_day="AM",
                slot_type=SlotType.FMIT,
                raw_value="FMIT",
            )
            schedule.add_slot(slot)

        weeks = schedule.get_fmit_weeks()
        # Should still be one week
        assert len(weeks) == 1

    def test_sparse_fmit_slots(self):
        """Test FMIT slots with large gaps between them."""
        schedule = ProviderSchedule(name="Dr. Test")

        # Far apart FMIT slots
        dates = [
            date(2024, 1, 15),   # January
            date(2024, 6, 10),   # June (5 months later)
            date(2024, 12, 2),   # December (6 months later)
        ]

        for d in dates:
            slot = ScheduleSlot(
                provider_name="Dr. Test",
                date=d,
                time_of_day="AM",
                slot_type=SlotType.FMIT,
                raw_value="FMIT",
            )
            schedule.add_slot(slot)

        weeks = schedule.get_fmit_weeks()
        assert len(weeks) == 3

    def test_year_boundary_weeks(self):
        """Test weeks that span year boundary."""
        schedule = ProviderSchedule(name="Dr. Test")

        # Week that spans 2024-2025 boundary
        # Dec 30, 2024 is a Monday
        slot = ScheduleSlot(
            provider_name="Dr. Test",
            date=date(2024, 12, 30),  # Monday
            time_of_day="AM",
            slot_type=SlotType.FMIT,
            raw_value="FMIT",
        )
        schedule.add_slot(slot)

        weeks = schedule.get_fmit_weeks()
        assert len(weeks) == 1
        assert weeks[0][0] == date(2024, 12, 30)
        assert weeks[0][1] == date(2025, 1, 5)  # Sunday in new year
