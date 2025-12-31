"""
ACGME Compliance Engine - Orchestration Layer.

Coordinates all ACGME validation validators and provides:
- Batch validation for full schedules
- Real-time validation for individual assignments
- Compliance dashboard data aggregation
- Violation report generation
- Remediation suggestion engine

This engine integrates work hour, supervision, call, leave, and
rotation validators into a unified compliance system.
"""

import logging
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional
from uuid import UUID

from app.scheduling.validators import (
    CallValidator,
    LeaveValidator,
    RotationValidator,
    SupervisionValidator,
    WorkHourValidator,
)

logger = logging.getLogger(__name__)


@dataclass
class ComplianceCheckResult:
    """Result of a full compliance check."""

    person_id: UUID
    check_date: date
    is_compliant: bool
    critical_violations: int = 0
    high_violations: int = 0
    medium_violations: int = 0
    warnings: int = 0
    violations_by_domain: dict = field(default_factory=dict)
    warnings_by_domain: dict = field(default_factory=dict)
    remediation_suggestions: list[str] = field(default_factory=list)
    last_updated: date | None = None


@dataclass
class ScheduleValidationReport:
    """Report for entire schedule validation."""

    period_start: date
    period_end: date
    total_residents: int
    residents_compliant: int
    compliance_percentage: float
    critical_violations_count: int
    high_violations_count: int
    by_resident: dict = field(default_factory=dict)
    by_domain: dict = field(default_factory=dict)
    executive_summary: str = ""


class ACGMEComplianceEngine:
    """
    Orchestrates all ACGME compliance validators.

    This engine:
    1. Coordinates validation across all compliance domains
    2. Aggregates results for reporting
    3. Generates remediation suggestions
    4. Provides compliance dashboard metrics
    """

    def __init__(self):
        """Initialize compliance engine with all validators."""
        self.work_hour_validator = WorkHourValidator()
        self.supervision_validator = SupervisionValidator()
        self.call_validator = CallValidator()
        self.leave_validator = LeaveValidator()
        self.rotation_validator = RotationValidator()

    def validate_complete_schedule(
        self,
        period_start: date,
        period_end: date,
        schedule_data: dict,
    ) -> ScheduleValidationReport:
        """
        Validate entire schedule across all compliance domains.

        Args:
            period_start: Schedule period start date
            period_end: Schedule period end date
            schedule_data: Dict with keys:
                - 'residents': list of resident dicts
                - 'assignments': list of assignment dicts
                - 'blocks': list of block dicts
                - 'call_assignments': dict of call assignments
                - 'leave_records': dict of leave records

        Returns:
            ScheduleValidationReport with complete validation results
        """
        logger.info(
            f"Starting complete schedule validation: {period_start} to {period_end}"
        )

        residents = schedule_data.get("residents", [])
        assignments = schedule_data.get("assignments", [])
        blocks = schedule_data.get("blocks", [])
        call_assignments = schedule_data.get("call_assignments", {})
        leave_records = schedule_data.get("leave_records", {})

        # Run validation for each resident
        by_resident = {}
        total_critical = 0
        total_high = 0

        for resident in residents:
            resident_id = resident.get("id")
            pgy_level = resident.get("pgy_level")

            result = self.validate_resident_compliance(
                person_id=resident_id,
                pgy_level=pgy_level,
                period_start=period_start,
                period_end=period_end,
                assignments=[
                    a for a in assignments if a.get("person_id") == resident_id
                ],
                blocks=blocks,
                call_assignments=call_assignments.get(resident_id, []),
                leave_records=leave_records.get(resident_id, []),
            )

            by_resident[str(resident_id)] = result
            total_critical += result.critical_violations
            total_high += result.high_violations

        # Aggregate results
        residents_compliant = sum(1 for r in by_resident.values() if r.is_compliant)
        compliance_percentage = (
            residents_compliant / len(residents) * 100
            if residents and len(residents) > 0
            else 100.0
        )

        # Validate supervision across blocks
        supervision_violations, sup_metrics = (
            self.supervision_validator.validate_period_supervision(
                period_blocks=self._build_block_supervision_data(
                    assignments, blocks, residents
                )
            )
        )
        total_high += len(supervision_violations)

        # Generate executive summary
        executive_summary = self._generate_executive_summary(
            residents_compliant,
            len(residents),
            total_critical,
            total_high,
            compliance_percentage,
        )

        report = ScheduleValidationReport(
            period_start=period_start,
            period_end=period_end,
            total_residents=len(residents),
            residents_compliant=residents_compliant,
            compliance_percentage=compliance_percentage,
            critical_violations_count=total_critical,
            high_violations_count=total_high,
            by_resident=by_resident,
            by_domain={
                "supervision": sup_metrics,
            },
            executive_summary=executive_summary,
        )

        logger.info(
            f"Schedule validation complete: {compliance_percentage:.1f}% "
            f"compliant ({residents_compliant}/{len(residents)} residents)"
        )

        return report

    def validate_resident_compliance(
        self,
        person_id: UUID,
        pgy_level: int,
        period_start: date,
        period_end: date,
        assignments: list[dict],
        blocks: list[dict],
        call_assignments: list[dict],
        leave_records: list[dict],
    ) -> ComplianceCheckResult:
        """
        Validate single resident across all domains.

        Args:
            person_id: Resident ID
            pgy_level: PGY level
            period_start: Period start
            period_end: Period end
            assignments: Resident's assignments
            blocks: All blocks
            call_assignments: Resident's call assignments
            leave_records: Resident's leave records

        Returns:
            ComplianceCheckResult for this resident
        """
        violations_by_domain = {}
        warnings_by_domain = {}
        remediation = []

        # 1. Work Hour Validation
        hours_by_date = self._calculate_hours_by_date(assignments, blocks)
        wh_violations, wh_warnings = (
            self.work_hour_validator.validate_80_hour_rolling_average(
                person_id=person_id,
                hours_by_date=hours_by_date,
            )
        )
        violations_by_domain["work_hours"] = wh_violations
        warnings_by_domain["work_hours"] = wh_warnings

        if wh_violations:
            remediation.append(
                "Reduce work hour assignments to maintain 80-hour rolling average"
            )

        # 2. Supervision Validation (as resident)
        # Supervision is checked per-block, not per-resident

        # 3. Call Validation
        call_dates = [c.get("date") for c in call_assignments if c.get("date")]
        call_violations, call_warnings = self.call_validator.validate_call_frequency(
            person_id=person_id,
            call_dates=call_dates,
        )
        violations_by_domain["call"] = call_violations
        warnings_by_domain["call"] = call_warnings

        if call_violations:
            remediation.append(
                "Review call assignment frequency; adjust to meet every-3rd-night rule"
            )

        # 4. Leave Validation
        leave_violations = []
        for leave in leave_records:
            violation = self.leave_validator.validate_no_assignment_during_block(
                person_id=person_id,
                absence_id=leave.get("id"),
                absence_type=leave.get("type"),
                start_date=leave.get("start_date"),
                end_date=leave.get("end_date"),
                assigned_dates=list(hours_by_date.keys()),
                is_blocking=leave.get("is_blocking"),
            )
            if violation:
                leave_violations.append(violation)

        violations_by_domain["leave"] = leave_violations
        if leave_violations:
            remediation.append("Remove assignments that conflict with approved leaves")

        # 5. Rotation Validation
        rotation_violations = []
        clinic_blocks = len(
            [a for a in assignments if "clinic" in a.get("rotation_name", "").lower()]
        )

        if pgy_level == 1 and clinic_blocks < 8:
            rotation_violations.append(
                self.rotation_validator.validate_pgy_level_clinic_requirements(
                    person_id=person_id,
                    pgy_level=pgy_level,
                    clinic_blocks_completed=clinic_blocks,
                    year_to_date=True,
                )
            )

        violations_by_domain["rotation"] = [v for v in rotation_violations if v]
        if violations_by_domain["rotation"]:
            remediation.append(
                "Schedule additional clinic rotations to meet PGY-level requirements"
            )

        # Aggregate violation counts
        total_critical = sum(
            len([v for v in vlist if isinstance(v, list)])
            for vlist in violations_by_domain.values()
        )
        critical_count = sum(
            1
            for domain_violations in violations_by_domain.values()
            for v in (
                domain_violations
                if isinstance(domain_violations, list)
                else [domain_violations]
            )
            if v and hasattr(v, "severity") and v.severity == "CRITICAL"
        )
        high_count = sum(
            1
            for domain_violations in violations_by_domain.values()
            for v in (
                domain_violations
                if isinstance(domain_violations, list)
                else [domain_violations]
            )
            if v and hasattr(v, "severity") and v.severity == "HIGH"
        )

        warning_count = sum(
            len(w) if isinstance(w, list) else (1 if w else 0)
            for w in warnings_by_domain.values()
        )

        is_compliant = critical_count == 0 and high_count == 0

        return ComplianceCheckResult(
            person_id=person_id,
            check_date=date.today(),
            is_compliant=is_compliant,
            critical_violations=critical_count,
            high_violations=high_count,
            warnings=warning_count,
            violations_by_domain=violations_by_domain,
            warnings_by_domain=warnings_by_domain,
            remediation_suggestions=remediation,
            last_updated=date.today(),
        )

    def validate_single_assignment(
        self,
        assignment_data: dict,
        person_id: UUID,
        pgy_level: int,
        existing_assignments: list[dict],
        leave_records: list[dict],
    ) -> tuple[bool, list[str]]:
        """
        Pre-validate single assignment before committing.

        Args:
            assignment_data: New assignment to validate
            person_id: Resident ID
            pgy_level: PGY level
            existing_assignments: Current assignments
            leave_records: Leave records for resident

        Returns:
            (is_valid, reasons_if_invalid) tuple
        """
        reasons = []

        block_date = assignment_data.get("block_date")
        assigned_dates = [a.get("block_date") for a in existing_assignments]
        assigned_dates.append(block_date)

        # Check leave conflicts
        for leave in leave_records:
            if self.leave_validator.should_block_assignment(
                leave.get("type"),
                leave.get("start_date"),
                leave.get("end_date"),
                leave.get("is_blocking"),
            ):
                if leave.get("start_date") <= block_date <= leave.get("end_date"):
                    reasons.append(
                        f"Assignment conflicts with {leave.get('type')} leave "
                        f"({leave.get('start_date')} to {leave.get('end_date')})"
                    )

        is_valid = len(reasons) == 0
        return is_valid, reasons

    def _build_block_supervision_data(
        self,
        assignments: list[dict],
        blocks: list[dict],
        residents: list[dict],
    ) -> list[dict]:
        """Build supervision data by block."""
        block_supervision = {}
        block_dates = {b.get("id"): b.get("date") for b in blocks}

        for assignment in assignments:
            block_id = assignment.get("block_id")
            person_id = assignment.get("person_id")

            if block_id not in block_supervision:
                block_supervision[block_id] = {
                    "block_id": block_id,
                    "block_date": block_dates.get(block_id),
                    "pgy1_residents": [],
                    "other_residents": [],
                    "faculty_assigned": [],
                }

            # Find person
            person = next((r for r in residents if r.get("id") == person_id), None)
            if not person:
                continue

            if person.get("type") == "resident":
                if person.get("pgy_level") == 1:
                    block_supervision[block_id]["pgy1_residents"].append(person_id)
                else:
                    block_supervision[block_id]["other_residents"].append(person_id)
            elif person.get("type") == "faculty":
                block_supervision[block_id]["faculty_assigned"].append(person_id)

        return list(block_supervision.values())

    def _calculate_hours_by_date(
        self,
        assignments: list[dict],
        blocks: list[dict],
    ) -> dict[date, float]:
        """Calculate work hours by date from assignments."""
        block_dates = {b.get("id"): b.get("date") for b in blocks}
        hours_by_date = {}

        for assignment in assignments:
            block_id = assignment.get("block_id")
            block_date = block_dates.get(block_id)

            if not block_date:
                continue

            # Standard 6 hours per block
            hours = 6.0
            if block_date in hours_by_date:
                hours_by_date[block_date] += hours
            else:
                hours_by_date[block_date] = hours

        return hours_by_date

    def _generate_executive_summary(
        self,
        compliant: int,
        total: int,
        critical: int,
        high: int,
        percentage: float,
    ) -> str:
        """Generate executive summary of validation results."""
        summary_lines = [
            "ACGME Compliance Summary",
            f"Residents Compliant: {compliant}/{total} ({percentage:.1f}%)",
        ]

        if critical > 0:
            summary_lines.append(f"CRITICAL VIOLATIONS: {critical}")
        if high > 0:
            summary_lines.append(f"HIGH VIOLATIONS: {high}")

        if critical == 0 and high == 0 and percentage == 100:
            summary_lines.append("Status: FULLY COMPLIANT")
        elif critical > 0:
            summary_lines.append("Status: NON-COMPLIANT (Critical Issues)")
        elif high > 0:
            summary_lines.append("Status: NON-COMPLIANT (High Issues)")
        else:
            summary_lines.append("Status: COMPLIANT WITH WARNINGS")

        return "\n".join(summary_lines)

    def generate_compliance_dashboard_data(
        self,
        report: ScheduleValidationReport,
    ) -> dict:
        """
        Generate data for compliance dashboard.

        Args:
            report: ScheduleValidationReport from validation

        Returns:
            Dashboard data dict for frontend rendering
        """
        return {
            "summary": {
                "total_residents": report.total_residents,
                "compliant": report.residents_compliant,
                "percentage": report.compliance_percentage,
                "critical_violations": report.critical_violations_count,
                "high_violations": report.high_violations_count,
            },
            "period": {
                "start": report.period_start.isoformat(),
                "end": report.period_end.isoformat(),
            },
            "by_domain": report.by_domain,
            "executive_summary": report.executive_summary,
            "recommendations": self._generate_recommendations(report),
        }

    def _generate_recommendations(self, report: ScheduleValidationReport) -> list[str]:
        """Generate recommendations based on validation results."""
        recommendations = []

        if report.compliance_percentage < 95:
            recommendations.append(
                f"Address compliance gaps: {100 - report.compliance_percentage:.1f}% "
                f"of residents have violations"
            )

        if report.critical_violations_count > 0:
            recommendations.append(
                f"URGENT: Resolve {report.critical_violations_count} critical "
                f"violations immediately"
            )

        if report.high_violations_count > 0:
            recommendations.append(
                f"HIGH PRIORITY: Address {report.high_violations_count} high-severity violations"
            )

        if not recommendations:
            recommendations.append("Schedule is compliant. No action needed.")

        return recommendations
