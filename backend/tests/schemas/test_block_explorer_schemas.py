"""Tests for block explorer schemas (aliases, nested models, status values)."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from app.schemas.block_explorer import (
    BlockMeta,
    CompletenessItem,
    CompletenessData,
    ACGMERule,
    ACGMEComplianceData,
    HealthData,
    CalendarWeek,
    CalendarData,
    ResidentHalfDay,
    ResidentExplorerData,
    RotationExplorerData,
    ValidationCheck,
    SourceInfo,
    BlockExplorerResponse,
)


class TestBlockMeta:
    def test_with_aliases(self):
        r = BlockMeta(
            blockNumber=10,
            title="Block 10",
            dateRange="Jan 1 - Jan 31",
            startDate="2026-01-01",
            endDate="2026-01-31",
            daysInBlock=31,
            generatedAt=datetime(2026, 1, 1),
        )
        assert r.block_number == 10
        assert r.days_in_block == 31

    def test_with_field_names(self):
        r = BlockMeta(
            block_number=10,
            title="Block 10",
            date_range="Jan 1 - Jan 31",
            start_date="2026-01-01",
            end_date="2026-01-31",
            days_in_block=31,
            generated_at=datetime(2026, 1, 1),
        )
        assert r.block_number == 10


class TestCompletenessItem:
    def test_minimal(self):
        r = CompletenessItem(status="pass")
        assert r.assigned is None
        assert r.total is None
        assert r.active is None
        assert r.defined is None
        assert r.recorded is None
        assert r.pending is None
        assert r.filled is None
        assert r.gaps is None

    def test_populated(self):
        r = CompletenessItem(assigned=10, total=12, status="warn")
        assert r.assigned == 10
        assert r.status == "warn"


class TestCompletenessData:
    def _make_item(self, status="pass"):
        return CompletenessItem(status=status)

    def test_with_aliases(self):
        r = CompletenessData(
            residents=self._make_item(),
            faculty=self._make_item(),
            rotations=self._make_item(),
            absences=self._make_item(),
            callRoster=self._make_item("warn"),
            coverage=self._make_item(),
        )
        assert r.call_roster.status == "warn"

    def test_with_field_names(self):
        r = CompletenessData(
            residents=self._make_item(),
            faculty=self._make_item(),
            rotations=self._make_item(),
            absences=self._make_item(),
            call_roster=self._make_item(),
            coverage=self._make_item(),
        )
        assert r.call_roster is not None


class TestACGMERule:
    def test_valid(self):
        r = ACGMERule(
            id="80hr",
            name="80-Hour Rule",
            status="pass",
            detail="All residents compliant",
            threshold="<= 80 hours/week",
        )
        assert r.status == "pass"


class TestACGMEComplianceData:
    def test_with_aliases(self):
        rule = ACGMERule(
            id="80hr", name="80-Hour", status="pass", detail="OK", threshold="<= 80"
        )
        r = ACGMEComplianceData(
            overallStatus="pass",
            lastChecked=datetime(2026, 3, 1),
            rules=[rule],
        )
        assert r.overall_status == "pass"


class TestHealthData:
    def test_with_aliases(self):
        r = HealthData(
            coverage=95,
            residentCount=10,
            totalResidents=12,
            acgmeCompliant=True,
            completeness=85,
            status="ready",
        )
        assert r.resident_count == 10
        assert r.acgme_compliant is True
        assert r.conflicts == 0

    def test_with_field_names(self):
        r = HealthData(
            coverage=95,
            resident_count=10,
            total_residents=12,
            acgme_compliant=True,
            completeness=85,
            status="warning",
        )
        assert r.status == "warning"


class TestCalendarWeek:
    def test_with_alias(self):
        r = CalendarWeek(weekNum=1, dates=["2026-01-01", "2026-01-02"])
        assert r.week_num == 1

    def test_with_field_name(self):
        r = CalendarWeek(week_num=2, dates=["2026-01-08"])
        assert r.week_num == 2


class TestCalendarData:
    def test_with_alias(self):
        week = CalendarWeek(weekNum=1, dates=["2026-01-01"])
        r = CalendarData(weeks=[week], dayLabels=["Mon", "Tue"])
        assert r.day_labels == ["Mon", "Tue"]


class TestResidentHalfDay:
    def test_with_aliases(self):
        r = ResidentHalfDay(
            date="2026-01-01",
            am="CL",
            pm="PR",
            amSource="GEN",
            pmSource="MAN",
        )
        assert r.am_source == "GEN"
        assert r.pm_source == "MAN"


class TestResidentExplorerData:
    def test_with_aliases(self):
        half_day = ResidentHalfDay(
            date="2026-01-01", am="CL", pm="PR", amSource="GEN", pmSource="GEN"
        )
        r = ResidentExplorerData(
            id="r1",
            name="Dr. Smith",
            pgyLevel=2,
            rotation="FM Clinic",
            rotationId="rot-1",
            assignmentCount=20,
            completeAssignments=18,
            absenceDays=2,
            source="GEN",
            needsAttention=False,
            halfDays=[half_day],
        )
        assert r.pgy_level == 2
        assert r.assignment_count == 20
        assert r.notes is None
        assert r.attention_reason is None


class TestRotationExplorerData:
    def test_with_aliases(self):
        r = RotationExplorerData(
            id="rot-1",
            name="FM Clinic",
            abbreviation="FMC",
            category="outpatient",
            color="#4CAF50",
            assignedCount=8,
            residents=["r1", "r2"],
            callEligible=True,
            leaveEligible=False,
        )
        assert r.assigned_count == 8
        assert r.capacity is None
        assert r.description is None
        assert r.call_eligible is True
        assert r.leave_eligible is False


class TestValidationCheck:
    def test_valid(self):
        r = ValidationCheck(
            name="Coverage Check",
            status="pass",
            description="All rotations have adequate coverage",
            details="12/12 rotations covered",
        )
        assert r.status == "pass"


class TestSourceInfo:
    def test_valid(self):
        r = SourceInfo(
            label="Generated",
            color="#4CAF50",
            description="Auto-generated by scheduler",
            count=150,
            percentage=75,
        )
        assert r.count == 150


class TestBlockExplorerResponse:
    def _make_meta(self):
        return BlockMeta(
            block_number=10,
            title="Block 10",
            date_range="Jan-Feb",
            start_date="2026-01-01",
            end_date="2026-01-31",
            days_in_block=31,
            generated_at=datetime(2026, 1, 1),
        )

    def _make_completeness(self):
        item = CompletenessItem(status="pass")
        return CompletenessData(
            residents=item,
            faculty=item,
            rotations=item,
            absences=item,
            call_roster=item,
            coverage=item,
        )

    def _make_compliance(self):
        return ACGMEComplianceData(
            overall_status="pass",
            last_checked=datetime(2026, 1, 1),
            rules=[],
        )

    def _make_health(self):
        return HealthData(
            coverage=100,
            resident_count=12,
            total_residents=12,
            acgme_compliant=True,
            completeness=100,
            status="ready",
        )

    def _make_calendar(self):
        return CalendarData(weeks=[], day_labels=[])

    def test_valid(self):
        r = BlockExplorerResponse(
            meta=self._make_meta(),
            completeness=self._make_completeness(),
            acgme_compliance=self._make_compliance(),
            health=self._make_health(),
            calendar=self._make_calendar(),
            residents=[],
            rotations=[],
            validation_checks=[],
            activity_colors={"CL": "#4CAF50"},
            sources={},
        )
        assert r.meta.block_number == 10
        assert r.health.status == "ready"
