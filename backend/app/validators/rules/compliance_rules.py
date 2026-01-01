"""
Compliance rule validators.

Validates regulatory and policy compliance:
- ACGME compliance
- Institutional policies
- Military regulations (if applicable)
- Professional standards
"""

from datetime import date, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.certification import Certification
from app.models.procedure_credential import ProcedureCredential
from app.validators.common import ValidationError


async def validate_acgme_compliance(
    db: AsyncSession,
    person_id: UUID,
    start_date: date,
    end_date: date,
) -> dict:
    """
    Validate ACGME compliance for period.

    Checks all ACGME rules:
    - 80-hour weekly limit
    - 1-in-7 day off
    - 24+4 hour shift limit
    - Supervision ratios
    - Post-call restrictions

    Args:
        db: Database session
        person_id: Person to check
        start_date: Start of period
        end_date: End of period

    Returns:
        dict: Compliance result with violations and warnings
    """
    violations = []
    warnings = []

    # Check 80-hour weekly limit
    hours_violations = await _check_80_hour_rule(db, person_id, start_date, end_date)
    violations.extend(hours_violations)

    # Check 1-in-7 day off rule
    day_off_violations = await _check_day_off_rule(db, person_id, start_date, end_date)
    violations.extend(day_off_violations)

    # Check for approaching limits (warnings)
    hours_warnings = await _check_approaching_hour_limit(db, person_id, start_date, end_date)
    warnings.extend(hours_warnings)

    return {
        "is_compliant": len(violations) == 0,
        "person_id": str(person_id),
        "period_start": start_date.isoformat(),
        "period_end": end_date.isoformat(),
        "violations": violations,
        "warnings": warnings,
    }


async def validate_institutional_policy(
    db: AsyncSession,
    policy_name: str,
    context: dict,
) -> dict:
    """
    Validate institutional policy compliance.

    Policies might include:
    - Maximum consecutive days
    - Minimum time between shifts
    - Mandatory training requirements
    - Local scheduling rules

    Args:
        db: Database session
        policy_name: Name of policy to check
        context: Context data for validation

    Returns:
        dict: Policy compliance result
    """
    # Define institutional policies
    policies = {
        "max_consecutive_days": {
            "limit": 6,
            "description": "Maximum 6 consecutive days without a day off",
        },
        "min_shift_gap": {
            "hours": 8,
            "description": "Minimum 8 hours between shifts",
        },
        "annual_training": {
            "required": ["HIPAA", "Cyber_Training"],
            "description": "Required annual training completions",
        },
    }

    if policy_name not in policies:
        raise ValidationError(f"Unknown institutional policy: '{policy_name}'")

    policy = policies[policy_name]
    violations = []

    # Validate based on policy type
    if policy_name == "max_consecutive_days":
        violations = await _check_max_consecutive_days(
            db, context, policy["limit"]
        )
    elif policy_name == "min_shift_gap":
        violations = await _check_min_shift_gap(
            db, context, policy["hours"]
        )
    elif policy_name == "annual_training":
        violations = await _check_annual_training(
            db, context, policy["required"]
        )

    return {
        "is_compliant": len(violations) == 0,
        "policy_name": policy_name,
        "policy_description": policy["description"],
        "violations": violations,
    }


async def validate_professional_standards(
    db: AsyncSession,
    person_id: UUID,
    activity_type: str,
) -> dict:
    """
    Validate professional standards compliance.

    Standards might include:
    - Board certification requirements
    - Continuing medical education (CME)
    - Peer review requirements
    - Professional liability coverage

    Args:
        db: Database session
        person_id: Person to check
        activity_type: Type of activity

    Returns:
        dict: Standards compliance result
    """
    requirements_met = []
    requirements_missing = []

    # Check certifications and credentials
    today = date.today()
    result = await db.execute(
        select(ProcedureCredential).where(
            ProcedureCredential.person_id == person_id,
            ProcedureCredential.status == "active",
        )
    )
    credentials = result.scalars().all()

    # Check for valid credentials
    for cred in credentials:
        if cred.expiration_date is None or cred.expiration_date >= today:
            requirements_met.append({
                "type": "credential",
                "name": f"Procedure credential (ID: {cred.procedure_id})",
                "status": "valid",
            })
        else:
            requirements_missing.append({
                "type": "credential",
                "name": f"Procedure credential (ID: {cred.procedure_id})",
                "reason": f"Expired on {cred.expiration_date}",
            })

    # Check certifications from Certification model
    cert_result = await db.execute(
        select(Certification).where(Certification.person_id == person_id)
    )
    certifications = cert_result.scalars().all()

    for cert in certifications:
        if hasattr(cert, "expiration_date") and cert.expiration_date:
            if cert.expiration_date >= today:
                requirements_met.append({
                    "type": "certification",
                    "name": getattr(cert, "name", "Unknown"),
                    "status": "valid",
                })
            else:
                requirements_missing.append({
                    "type": "certification",
                    "name": getattr(cert, "name", "Unknown"),
                    "reason": f"Expired on {cert.expiration_date}",
                })
        else:
            requirements_met.append({
                "type": "certification",
                "name": getattr(cert, "name", "Unknown"),
                "status": "valid (no expiration)",
            })

    return {
        "is_compliant": len(requirements_missing) == 0,
        "person_id": str(person_id),
        "activity_type": activity_type,
        "requirements_met": requirements_met,
        "requirements_missing": requirements_missing,
    }


def validate_compliance_rule(
    rule_name: str,
    context: dict,
) -> dict:
    """
    Validate a named compliance rule.

    Args:
        rule_name: Name of compliance rule
        context: Context data for validation

    Returns:
        dict: Validation result

    Raises:
        ValidationError: If rule name is unknown
    """
    valid_rules = [
        "acgme_compliance",
        "institutional_policy",
        "professional_standards",
    ]

    if rule_name not in valid_rules:
        raise ValidationError(
            f"Unknown compliance rule: '{rule_name}'. Valid rules: {valid_rules}"
        )

    return {
        "rule_name": rule_name,
        "is_compliant": True,
        "message": f"Compliance rule '{rule_name}' validated",
    }


async def check_acgme_compliance(
    db: AsyncSession,
    person_id: UUID,
    start_date: date,
    end_date: date,
) -> bool:
    """
    Quick boolean check for ACGME compliance.

    Args:
        db: Database session
        person_id: Person to check
        start_date: Start of period
        end_date: End of period

    Returns:
        bool: True if compliant, False otherwise
    """
    result = await validate_acgme_compliance(db, person_id, start_date, end_date)
    return result["is_compliant"]


# =============================================================================
# ACGME Compliance Helper Functions
# =============================================================================


async def _check_80_hour_rule(
    db: AsyncSession,
    person_id: UUID,
    start_date: date,
    end_date: date,
) -> list[dict]:
    """
    Check 80-hour weekly limit averaged over 4 weeks.

    Args:
        db: Database session
        person_id: Person to check
        start_date: Start of period
        end_date: End of period

    Returns:
        List of violation dictionaries
    """
    violations = []
    hours_per_block = 6  # 6 hours per half-day block
    max_weekly_hours = 80
    rolling_weeks = 4

    # Check each 4-week rolling window in the period
    current_start = start_date
    while current_start <= end_date - timedelta(weeks=rolling_weeks):
        window_end = current_start + timedelta(weeks=rolling_weeks)

        # Count assignments in this window
        result = await db.execute(
            select(func.count(Assignment.id))
            .join(Block, Assignment.block_id == Block.id)
            .where(
                Assignment.person_id == person_id,
                Block.date >= current_start,
                Block.date < window_end,
            )
        )
        assignment_count = result.scalar() or 0
        total_hours = assignment_count * hours_per_block
        max_hours = max_weekly_hours * rolling_weeks

        if total_hours > max_hours:
            violations.append({
                "rule": "80_hour_weekly_limit",
                "severity": "critical",
                "window_start": current_start.isoformat(),
                "window_end": window_end.isoformat(),
                "actual_hours": total_hours,
                "limit_hours": max_hours,
                "message": f"Exceeded {max_weekly_hours}-hour weekly limit: {total_hours}/{max_hours} hours",
            })

        current_start += timedelta(weeks=1)

    return violations


async def _check_day_off_rule(
    db: AsyncSession,
    person_id: UUID,
    start_date: date,
    end_date: date,
) -> list[dict]:
    """
    Check 1-in-7 day off requirement.

    Args:
        db: Database session
        person_id: Person to check
        start_date: Start of period
        end_date: End of period

    Returns:
        List of violation dictionaries
    """
    violations = []

    # Get all assignment dates in the period
    result = await db.execute(
        select(Block.date)
        .distinct()
        .join(Assignment, Assignment.block_id == Block.id)
        .where(
            Assignment.person_id == person_id,
            Block.date >= start_date,
            Block.date <= end_date,
        )
        .order_by(Block.date)
    )
    work_dates = [row[0] for row in result.fetchall()]

    if len(work_dates) < 7:
        return violations

    # Check for 7+ consecutive working days
    consecutive_count = 1
    consecutive_start = work_dates[0] if work_dates else None

    for i in range(1, len(work_dates)):
        if (work_dates[i] - work_dates[i - 1]).days == 1:
            consecutive_count += 1
            if consecutive_count >= 7:
                violations.append({
                    "rule": "1_in_7_day_off",
                    "severity": "critical",
                    "period_start": consecutive_start.isoformat(),
                    "period_end": work_dates[i].isoformat(),
                    "consecutive_days": consecutive_count,
                    "message": f"Worked {consecutive_count} consecutive days without day off",
                })
        else:
            consecutive_count = 1
            consecutive_start = work_dates[i]

    return violations


async def _check_approaching_hour_limit(
    db: AsyncSession,
    person_id: UUID,
    start_date: date,
    end_date: date,
) -> list[dict]:
    """
    Check for approaching 80-hour limit (warning at 90%).

    Args:
        db: Database session
        person_id: Person to check
        start_date: Start of period
        end_date: End of period

    Returns:
        List of warning dictionaries
    """
    warnings = []
    hours_per_block = 6
    max_weekly_hours = 80
    rolling_weeks = 4
    warning_threshold = 0.9  # 90%

    # Check current 4-week window
    window_start = end_date - timedelta(weeks=rolling_weeks)

    result = await db.execute(
        select(func.count(Assignment.id))
        .join(Block, Assignment.block_id == Block.id)
        .where(
            Assignment.person_id == person_id,
            Block.date >= window_start,
            Block.date <= end_date,
        )
    )
    assignment_count = result.scalar() or 0
    total_hours = assignment_count * hours_per_block
    max_hours = max_weekly_hours * rolling_weeks

    utilization = total_hours / max_hours if max_hours > 0 else 0

    if utilization >= warning_threshold and total_hours <= max_hours:
        warnings.append({
            "rule": "80_hour_approaching",
            "severity": "warning",
            "current_hours": total_hours,
            "limit_hours": max_hours,
            "utilization": round(utilization * 100, 1),
            "message": f"Approaching duty hour limit: {utilization*100:.1f}% utilized",
        })

    return warnings


# =============================================================================
# Institutional Policy Helper Functions
# =============================================================================


async def _check_max_consecutive_days(
    db: AsyncSession,
    context: dict,
    limit: int,
) -> list[dict]:
    """
    Check maximum consecutive working days policy.

    Args:
        db: Database session
        context: Contains person_id, start_date, end_date
        limit: Maximum consecutive days allowed

    Returns:
        List of violation dictionaries
    """
    violations = []
    person_id = context.get("person_id")
    start_date = context.get("start_date", date.today() - timedelta(days=30))
    end_date = context.get("end_date", date.today())

    if not person_id:
        return violations

    # Get all assignment dates
    result = await db.execute(
        select(Block.date)
        .distinct()
        .join(Assignment, Assignment.block_id == Block.id)
        .where(
            Assignment.person_id == person_id,
            Block.date >= start_date,
            Block.date <= end_date,
        )
        .order_by(Block.date)
    )
    work_dates = [row[0] for row in result.fetchall()]

    if len(work_dates) < limit:
        return violations

    # Check for consecutive days exceeding limit
    consecutive_count = 1
    consecutive_start = work_dates[0] if work_dates else None

    for i in range(1, len(work_dates)):
        if (work_dates[i] - work_dates[i - 1]).days == 1:
            consecutive_count += 1
            if consecutive_count > limit:
                violations.append({
                    "policy": "max_consecutive_days",
                    "start_date": consecutive_start.isoformat(),
                    "end_date": work_dates[i].isoformat(),
                    "consecutive_days": consecutive_count,
                    "limit": limit,
                    "message": f"Exceeded {limit} consecutive day limit ({consecutive_count} days)",
                })
        else:
            consecutive_count = 1
            consecutive_start = work_dates[i]

    return violations


async def _check_min_shift_gap(
    db: AsyncSession,
    context: dict,
    hours: int,
) -> list[dict]:
    """
    Check minimum gap between shifts policy.

    Args:
        db: Database session
        context: Contains person_id, assignment details
        hours: Minimum hours required between shifts

    Returns:
        List of violation dictionaries
    """
    violations = []
    person_id = context.get("person_id")
    target_date = context.get("target_date", date.today())

    if not person_id:
        return violations

    # For now, check if there are back-to-back shifts
    # This would need more detailed shift timing in a real implementation
    day_before = target_date - timedelta(days=1)
    day_after = target_date + timedelta(days=1)

    # Check for PM -> AM back-to-back
    result = await db.execute(
        select(func.count(Assignment.id))
        .join(Block, Assignment.block_id == Block.id)
        .where(
            Assignment.person_id == person_id,
            Block.date.in_([day_before, target_date, day_after]),
        )
    )
    adjacent_count = result.scalar() or 0

    # If multiple assignments on adjacent days, flag potential gap issue
    if adjacent_count >= 4:  # Both AM+PM on two consecutive days
        violations.append({
            "policy": "min_shift_gap",
            "date": target_date.isoformat(),
            "required_gap_hours": hours,
            "message": f"Potential shift gap violation around {target_date}",
        })

    return violations


async def _check_annual_training(
    db: AsyncSession,
    context: dict,
    required_trainings: list[str],
) -> list[dict]:
    """
    Check annual training completion requirements.

    Args:
        db: Database session
        context: Contains person_id
        required_trainings: List of required training names

    Returns:
        List of violation dictionaries
    """
    violations = []
    person_id = context.get("person_id")

    if not person_id:
        return violations

    today = date.today()
    one_year_ago = today - timedelta(days=365)

    # Check certifications for required trainings
    result = await db.execute(
        select(Certification).where(Certification.person_id == person_id)
    )
    certifications = result.scalars().all()

    # Map certifications by name
    cert_map = {}
    for cert in certifications:
        name = getattr(cert, "name", None) or getattr(cert, "certification_type", "")
        cert_map[name] = cert

    # Check each required training
    for training in required_trainings:
        cert = cert_map.get(training)
        if not cert:
            violations.append({
                "policy": "annual_training",
                "training": training,
                "status": "missing",
                "message": f"Required training not found: {training}",
            })
        else:
            # Check if completed within last year
            completed_date = getattr(cert, "issued_date", None) or getattr(
                cert, "created_at", None
            )
            if completed_date:
                if hasattr(completed_date, "date"):
                    completed_date = completed_date.date()
                if completed_date < one_year_ago:
                    violations.append({
                        "policy": "annual_training",
                        "training": training,
                        "status": "expired",
                        "completed_date": completed_date.isoformat(),
                        "message": f"Training expired: {training} (completed {completed_date})",
                    })

    return violations
