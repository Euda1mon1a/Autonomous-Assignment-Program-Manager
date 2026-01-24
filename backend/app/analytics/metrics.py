"""Metric definitions and calculations for schedule analytics."""

import statistics
from collections import Counter, defaultdict
from typing import Any

from app.analytics.types import ConsecutiveDutyStats, MetricResult


def calculate_fairness_index(assignments: list[dict[str, Any]]) -> MetricResult:
    """
    Calculate fairness index (Gini coefficient) for workload distribution.

    Args:
        assignments: List of assignment dicts with person_id keys

    Returns:
        Dict with value, trend, benchmark, and status
    """
    if not assignments:
        return {
            "value": 1.0,
            "trend": "stable",
            "benchmark": 0.9,
            "status": "good",
            "description": "Perfect fairness (no assignments)",
            "details": {},
        }

    # Count assignments per person
    person_counts = Counter([a["person_id"] for a in assignments])
    counts = sorted(person_counts.values())
    n = len(counts)

    if n == 0:
        return {
            "value": 1.0,
            "trend": "stable",
            "benchmark": 0.9,
            "status": "good",
            "description": "Perfect fairness (no people)",
            "details": {},
        }

    # Calculate Gini coefficient
    cumsum = 0
    for i, count in enumerate(counts):
        cumsum += (2 * (i + 1) - n - 1) * count

    total = sum(counts)
    gini = cumsum / (n * total) if total > 0 else 0

    # Convert to fairness index (1 - Gini, so higher is better)
    fairness = 1 - abs(gini)

    # Determine status
    if fairness >= 0.9:
        status = "good"
    elif fairness >= 0.75:
        status = "warning"
    else:
        status = "critical"

    return {
        "value": round(fairness, 3),
        "trend": "stable",
        "benchmark": 0.9,
        "status": status,
        "description": f"Workload fairness across {n} people",
        "details": {
            "min_assignments": min(counts),
            "max_assignments": max(counts),
            "mean_assignments": round(statistics.mean(counts), 2),
            "std_dev": round(statistics.stdev(counts), 2) if n > 1 else 0,
        },
    }


def calculate_coverage_rate(
    blocks: list[dict[str, Any]], assignments: list[dict[str, Any]]
) -> MetricResult:
    """
    Calculate percentage of blocks that are covered by assignments.

    Args:
        blocks: List of block dicts with id keys
        assignments: List of assignment dicts with block_id keys

    Returns:
        Dict with value, trend, benchmark, and status
    """
    if not blocks:
        return {
            "value": 100.0,
            "trend": "stable",
            "benchmark": 95.0,
            "status": "good",
            "description": "No blocks to cover",
            "details": {},
        }

    total_blocks = len(blocks)
    covered_blocks = len({a["block_id"] for a in assignments})
    coverage_rate = (covered_blocks / total_blocks) * 100

    # Determine status
    if coverage_rate >= 95.0:
        status = "good"
    elif coverage_rate >= 85.0:
        status = "warning"
    else:
        status = "critical"

    return {
        "value": round(coverage_rate, 2),
        "trend": "stable",
        "benchmark": 95.0,
        "status": status,
        "description": f"{covered_blocks}/{total_blocks} blocks covered",
        "details": {
            "total_blocks": total_blocks,
            "covered_blocks": covered_blocks,
            "uncovered_blocks": total_blocks - covered_blocks,
        },
    }


def calculate_acgme_compliance_rate(violations: int, total_checks: int) -> MetricResult:
    """
    Calculate ACGME compliance rate.

    Args:
        violations: Number of violations found
        total_checks: Total number of compliance checks performed

    Returns:
        Dict with value, trend, benchmark, and status
    """
    if total_checks == 0:
        return {
            "value": 100.0,
            "trend": "stable",
            "benchmark": 100.0,
            "status": "good",
            "description": "No compliance checks performed",
            "details": {},
        }

    compliance_rate = ((total_checks - violations) / total_checks) * 100

    # Determine status
    if violations == 0:
        status = "good"
    elif compliance_rate >= 90.0:
        status = "warning"
    else:
        status = "critical"

    return {
        "value": round(compliance_rate, 2),
        "trend": "stable",
        "benchmark": 100.0,
        "status": status,
        "description": f"{violations} violations in {total_checks} checks",
        "details": {
            "total_checks": total_checks,
            "violations": violations,
            "compliance_checks_passed": total_checks - violations,
        },
    }


def calculate_preference_satisfaction(
    assignments: list[dict[str, Any]], preferences: list[dict[str, Any]]
) -> MetricResult:
    """
    Calculate how well assignments match stated preferences.

    Args:
        assignments: List of assignment dicts
        preferences: List of preference dicts with person_id and rotation_template_id

    Returns:
        Dict with value, trend, benchmark, and status
    """
    if not preferences:
        return {
            "value": 100.0,
            "trend": "stable",
            "benchmark": 80.0,
            "status": "good",
            "description": "No preferences specified",
            "details": {},
        }

    # Build preference map: person_id -> set of preferred rotation_template_ids
    pref_map = defaultdict(set)
    for pref in preferences:
        pref_map[pref["person_id"]].add(pref["rotation_template_id"])

    # Check how many assignments match preferences
    matched = 0
    total_with_prefs = 0

    for assignment in assignments:
        person_id = assignment["person_id"]
        rotation_id = assignment.get("rotation_template_id")

        if person_id in pref_map:
            total_with_prefs += 1
            if rotation_id in pref_map[person_id]:
                matched += 1

    if total_with_prefs == 0:
        satisfaction_rate = 100.0
    else:
        satisfaction_rate = (matched / total_with_prefs) * 100

    # Determine status
    if satisfaction_rate >= 80.0:
        status = "good"
    elif satisfaction_rate >= 60.0:
        status = "warning"
    else:
        status = "critical"

    return {
        "value": round(satisfaction_rate, 2),
        "trend": "stable",
        "benchmark": 80.0,
        "status": status,
        "description": f"{matched}/{total_with_prefs} preferences satisfied",
        "details": {
            "total_preferences": len(preferences),
            "assignments_with_preferences": total_with_prefs,
            "preferences_matched": matched,
        },
    }


def calculate_consecutive_duty_stats(
    person_id: str, assignments: list[dict[str, Any]]
) -> ConsecutiveDutyStats:
    """
    Calculate consecutive duty pattern statistics for a person.

    Args:
        person_id: ID of person to analyze
        assignments: List of all assignments with block info

    Returns:
        Dict with consecutive duty statistics
    """
    # Filter assignments for this person and sort by date
    person_assignments = [
        a
        for a in assignments
        if a.get("person_id") == person_id and a.get("block_date")
    ]

    if not person_assignments:
        return {
            "person_id": person_id,
            "max_consecutive_days": 0,
            "total_duty_days": 0,
            "average_rest_days": 0,
            "status": "good",
            "description": "No assignments found",
            "details": {},
        }

    # Sort by date
    person_assignments.sort(key=lambda x: x["block_date"])

    # Track consecutive days
    duty_dates = set()
    for assignment in person_assignments:
        duty_dates.add(assignment["block_date"])

    duty_dates_sorted = sorted(duty_dates)

    # Calculate consecutive streaks
    max_consecutive = 1
    current_consecutive = 1
    rest_periods = []

    for i in range(1, len(duty_dates_sorted)):
        prev_date = duty_dates_sorted[i - 1]
        curr_date = duty_dates_sorted[i]

        # Check if dates are consecutive
        if (curr_date - prev_date).days == 1:
            current_consecutive += 1
            max_consecutive = max(max_consecutive, current_consecutive)
        else:
            rest_periods.append((curr_date - prev_date).days - 1)
            current_consecutive = 1

    # Determine status based on ACGME guidelines (max 6 consecutive days)
    if max_consecutive <= 6:
        status = "good"
    elif max_consecutive <= 13:
        status = "warning"
    else:
        status = "critical"

    return {
        "person_id": person_id,
        "max_consecutive_days": max_consecutive,
        "total_duty_days": len(duty_dates),
        "average_rest_days": (
            round(statistics.mean(rest_periods), 2) if rest_periods else 0
        ),
        "status": status,
        "description": f"Max {max_consecutive} consecutive days",
        "details": {
            "total_assignments": len(person_assignments),
            "unique_duty_dates": len(duty_dates),
            "rest_periods": len(rest_periods),
        },
    }
