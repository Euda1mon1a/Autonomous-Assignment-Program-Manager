"""
Domain Context Module for Scheduler MCP Tools.

Provides abbreviation expansion, constraint explanations, and scheduling pattern
context to make MCP tool responses more accessible to non-technical users.

Reference: docs/development/MCP_DOMAIN_GLOSSARY.md
Created: 2025-12-24
"""

import re
from typing import Any

# =============================================================================
# ABBREVIATIONS
# =============================================================================

ABBREVIATIONS: dict[str, str] = {
    # Personnel & Training Levels
    "PGY-1": "Post-Graduate Year 1 (first-year resident/intern)",
    "PGY-2": "Post-Graduate Year 2 (second-year resident)",
    "PGY-3": "Post-Graduate Year 3 (third-year resident)",
    "PGY": "Post-Graduate Year",
    "MS": "Medical Student",
    "MS3": "Medical Student Year 3",
    "MS4": "Medical Student Year 4",
    "TY": "Transitional Year Intern",
    "PSYCH": "Psychiatry Intern",

    # Faculty Roles
    "PD": "Program Director",
    "APD": "Associate Program Director",
    "OIC": "Officer in Charge",
    "SM": "Sports Medicine",
    "CORE": "Core Faculty",
    "DEPT_CHIEF": "Department Chief",

    # Regulatory Bodies
    "ACGME": "Accreditation Council for Graduate Medical Education",
    "LCME": "Liaison Committee on Medical Education",

    # Schedule Elements
    "FMIT": "Family Medicine Inpatient Team",
    "PC": "Post-Call (recovery day after overnight call)",
    "ASM": "Academic Sports Medicine",
    "NF": "Night Float",
    "AM": "Morning Session",
    "PM": "Afternoon Session",

    # Military/Administrative
    "TDY": "Temporary Duty",
    "DEP": "Deployment",
    "FEM": "Family Emergency",
    "PER": "Personal (time off)",
    "MTF": "Military Treatment Facility",
    "PERSEC": "Personnel Security",
    "OPSEC": "Operations Security",

    # Other Common Terms
    "PII": "Personally Identifiable Information",
    "PHI": "Protected Health Information",
}


# =============================================================================
# CONSTRAINT EXPLANATIONS
# =============================================================================

CONSTRAINT_EXPLANATIONS: dict[str, dict[str, Any]] = {
    # Hard Constraints (Must Be Satisfied)
    "AvailabilityConstraint": {
        "type": "hard",
        "short": "Person must be available",
        "description": "Ensures a person is not assigned when they are on leave, TDY, deployment, or otherwise unavailable.",
        "violation_impact": "CRITICAL - Cannot assign unavailable personnel",
        "fix_options": [
            "Remove the assignment",
            "Assign a different available person",
            "Adjust leave/absence dates if incorrect"
        ],
        "code_reference": "backend/app/scheduling/constraints/acgme.py:53"
    },

    "OnePersonPerBlockConstraint": {
        "type": "hard",
        "short": "One assignment per person per session",
        "description": "A person cannot be in two places at once. Each person can have at most one assignment per AM or PM session.",
        "violation_impact": "CRITICAL - Double-booking detected",
        "fix_options": [
            "Remove one of the conflicting assignments",
            "Move one assignment to a different session",
            "Assign a different person to one slot"
        ],
        "code_reference": "backend/app/scheduling/constraints/capacity.py:31"
    },

    "EightyHourRuleConstraint": {
        "type": "hard",
        "short": "ACGME 80-hour weekly limit",
        "description": "Residents cannot work more than 80 hours per week, averaged over a rolling 4-week period. This is an ACGME regulatory requirement.",
        "violation_impact": "REGULATORY - ACGME compliance violation",
        "fix_options": [
            "Reduce assignments in the current week",
            "Redistribute assignments across the 4-week block",
            "Add additional residents to share load"
        ],
        "code_reference": "backend/app/scheduling/constraints/acgme.py:141",
        "regulatory_reference": "ACGME Common Program Requirements Section VI.F.1"
    },

    "OneInSevenRuleConstraint": {
        "type": "hard",
        "short": "ACGME 1-in-7 rest requirement",
        "description": "Residents must have at least one 24-hour period off every 7 days. This is an ACGME regulatory requirement for resident well-being.",
        "violation_impact": "REGULATORY - ACGME compliance violation",
        "fix_options": [
            "Add a day off within the 7-day window",
            "Adjust assignment schedule to ensure rest day",
            "Redistribute assignments to create gaps"
        ],
        "code_reference": "backend/app/scheduling/constraints/acgme.py:361",
        "regulatory_reference": "ACGME Common Program Requirements Section VI.F.2"
    },

    "SupervisionRatioConstraint": {
        "type": "hard",
        "short": "Faculty:Resident supervision ratios",
        "description": "Ensures adequate faculty supervision per ACGME. PGY-1 cannot supervise (0 learners). PGY-2/3 can supervise max 2 learners. Faculty can supervise max 4 residents.",
        "violation_impact": "REGULATORY - Inadequate supervision",
        "fix_options": [
            "Add additional faculty coverage",
            "Reduce number of learners in session",
            "Use higher-level residents for supervision"
        ],
        "code_reference": "backend/app/scheduling/constraints/acgme.py:517",
        "regulatory_reference": "ACGME Common Program Requirements Section VI.B"
    },

    "InvertedWednesdayConstraint": {
        "type": "hard",
        "short": "4th Wednesday special schedule",
        "description": "On the 4th Wednesday of the month (days 22-28), residents have lectures in AM and advising in PM. Faculty coverage differs: one faculty AM, a DIFFERENT faculty PM (for equity).",
        "violation_impact": "OPERATIONAL - Special schedule not followed",
        "fix_options": [
            "Assign different faculty to AM vs PM slots",
            "Swap faculty assignments to ensure variety",
            "Check if date is truly 4th Wednesday (day 22-28)"
        ],
        "code_reference": "backend/app/scheduling/constraints/temporal.py:380",
        "see_also": "SCHEDULING_PATTERNS['inverted_wednesday']"
    },

    "WednesdayAMInternOnlyConstraint": {
        "type": "hard",
        "short": "Wednesday AM clinic staffing",
        "description": "On non-inverted Wednesdays (1st, 2nd, 3rd), residents attend ASM (Academic Sports Medicine) in the AM. Only interns (PGY-1) should be assigned to Wednesday AM clinic.",
        "violation_impact": "OPERATIONAL - Wrong training level for session",
        "fix_options": [
            "Assign a PGY-1 instead of PGY-2/3",
            "Move non-intern to different session",
            "Verify Wednesday type (normal vs inverted)"
        ],
        "code_reference": "backend/app/scheduling/constraints/temporal.py:26"
    },

    "FMITWeekBlockingConstraint": {
        "type": "hard",
        "short": "FMIT week blocks entire week",
        "description": "When a resident is assigned to FMIT (Family Medicine Inpatient Team) week, it blocks the entire week Mon-Fri. This includes overnight call on Thursday and post-call recovery on Friday.",
        "violation_impact": "OPERATIONAL - Week-long commitment not honored",
        "fix_options": [
            "Clear all conflicting assignments for the week",
            "Move FMIT assignment to different week",
            "Ensure post-call day is protected on Friday"
        ],
        "code_reference": "backend/app/scheduling/constraints/fmit.py:75",
        "see_also": "SCHEDULING_PATTERNS['fmit_week']"
    },

    "PostCallAutoAssignmentConstraint": {
        "type": "hard",
        "short": "Post-call recovery assignment",
        "description": "After overnight call, residents must have a post-call (PC) recovery day. No clinic assignments for 24 hours post-call. This is for resident safety and patient care quality.",
        "violation_impact": "SAFETY - Insufficient recovery after overnight",
        "fix_options": [
            "Assign post-call template to next day",
            "Clear any clinic assignments following call",
            "Verify call night is correctly marked"
        ],
        "code_reference": "backend/app/scheduling/constraints/post_call.py:41",
        "see_also": "SCHEDULING_PATTERNS['post_call']"
    },

    # Soft Constraints (Optimization Goals)
    "EquityConstraint": {
        "type": "soft",
        "short": "Fair distribution of assignments",
        "description": "Ensures assignments are fairly distributed among personnel. Prevents overloading some while others are underutilized.",
        "violation_impact": "QUALITY - Unfair workload distribution",
        "weight": "HIGH",
        "code_reference": "backend/app/scheduling/constraints/equity.py"
    },

    "ContinuityConstraint": {
        "type": "soft",
        "short": "Same faculty for patient panels",
        "description": "Maintains continuity of care by preferring the same faculty for ongoing patient relationships.",
        "violation_impact": "QUALITY - Patient continuity disrupted",
        "weight": "MEDIUM",
        "code_reference": "backend/app/scheduling/constraints/continuity.py"
    },

    "PreferenceConstraint": {
        "type": "soft",
        "short": "Honor faculty preferences",
        "description": "Attempts to honor faculty preferences for specific shifts, days off, or assignment types when possible.",
        "violation_impact": "QUALITY - Preferences not met",
        "weight": "LOW",
        "code_reference": "backend/app/scheduling/constraints/preferences.py"
    },

    "HubProtectionConstraint": {
        "type": "soft",
        "short": "Protect critical nodes from overload",
        "description": "Identifies 'hub' personnel (critical to operations) and prevents overloading them to avoid single points of failure.",
        "violation_impact": "RESILIENCE - Hub node at risk",
        "weight": "HIGH",
        "code_reference": "backend/app/scheduling/constraints/resilience.py"
    },

    "UtilizationBufferConstraint": {
        "type": "soft",
        "short": "Keep utilization under 80%",
        "description": "Based on queuing theory, keeps personnel utilization under 80% to prevent cascade failures and maintain system resilience.",
        "violation_impact": "RESILIENCE - Overutilization risk",
        "weight": "HIGH",
        "code_reference": "backend/app/scheduling/constraints/resilience.py",
        "reference": "docs/architecture/cross-disciplinary-resilience.md"
    },
}


# =============================================================================
# SCHEDULING PATTERNS
# =============================================================================

SCHEDULING_PATTERNS: dict[str, dict[str, Any]] = {
    "inverted_wednesday": {
        "name": "Inverted Wednesday Pattern",
        "description": "4th Wednesday of month has inverted schedule",
        "occurs": "Days 22-28 of month",
        "normal_wednesday": {
            "AM": "Residents: Clinic | Faculty: Clinic",
            "PM": "Residents: Lecture/Simulation | Faculty: 1 covers clinic"
        },
        "inverted_wednesday": {
            "AM": "Residents: Lecture | Faculty: 1 covers clinic",
            "PM": "Residents: Advising | Faculty: 1 DIFFERENT covers clinic"
        },
        "key_constraint": "AM and PM faculty MUST be different people (equity)",
        "code_reference": "backend/app/scheduling/constraints/temporal.py:380"
    },

    "fmit_week": {
        "name": "FMIT Week Pattern",
        "description": "Family Medicine Inpatient Team week-long rotation",
        "occurs": "Any 1 week per 4-week block",
        "schedule": {
            "Monday": "FMIT AM + PM",
            "Tuesday": "FMIT AM + PM",
            "Wednesday": "ASM AM (still required) + FMIT PM",
            "Thursday": "FMIT AM + PM + OVERNIGHT CALL",
            "Friday": "POST-CALL (PC) - recovery day",
            "Weekend": "Weekend call if on FMIT"
        },
        "key_constraint": "Blocks entire week, includes overnight Thursday, PC Friday",
        "code_reference": "backend/app/scheduling/constraints/fmit.py:75"
    },

    "post_call": {
        "name": "Post-Call Recovery",
        "description": "Recovery period after overnight call",
        "timing": "Day immediately following overnight call",
        "rules": {
            "next_AM": "Light duties or off",
            "next_PM": "Off",
            "constraint": "No clinic for 24 hours post-call"
        },
        "rationale": "Resident safety and patient care quality",
        "code_reference": "backend/app/scheduling/constraints/post_call.py:41"
    },

    "block_structure": {
        "name": "Block Structure",
        "description": "How the academic year is divided",
        "hierarchy": {
            "Academic Year": "365 days",
            "Blocks": "13 blocks × 4 weeks each (52 weeks)",
            "Days": "Each day has AM session + PM session",
            "Total Sessions": "730 half-day sessions per year"
        },
        "assignment_hierarchy": [
            "Schedule (Academic Year)",
            "Block (4-week period)",
            "Day",
            "Session (AM/PM)",
            "Assignment (Person + Template + Location)"
        ]
    },

    "supervision_ratios": {
        "name": "ACGME Supervision Ratios",
        "description": "Required faculty-to-learner ratios",
        "ratios": {
            "PGY-1 (Intern)": {"max_learners": 0, "note": "Cannot supervise"},
            "PGY-2/3": {"max_learners": 2, "note": "Can supervise up to 2 learners"},
            "Attending (Faculty)": {"max_learners": 4, "note": "Can supervise up to 4 residents"}
        },
        "regulatory_reference": "ACGME Common Program Requirements Section VI.B",
        "code_reference": "backend/app/scheduling/constraints/acgme.py:517"
    },

    "work_hour_rules": {
        "name": "ACGME Work Hour Rules",
        "description": "Regulatory limits on resident work hours",
        "rules": {
            "80_hour_rule": {
                "limit": "80 hours/week",
                "measurement": "Rolling 4-week average",
                "code_reference": "backend/app/scheduling/constraints/acgme.py:141"
            },
            "one_in_seven": {
                "limit": "1 day off per 7 days",
                "measurement": "24-hour period",
                "code_reference": "backend/app/scheduling/constraints/acgme.py:361"
            },
            "max_shift": {
                "limit": "24 hours + 4 hours",
                "measurement": "Continuous duty period"
            }
        },
        "regulatory_reference": "ACGME Common Program Requirements Section VI.F"
    }
}


# =============================================================================
# ROLE & PERSONNEL CONTEXT
# =============================================================================

ROLE_CONTEXT: dict[str, dict[str, Any]] = {
    "faculty_roles": {
        "PD": {
            "full_name": "Program Director",
            "clinic_slots_per_week": 0,
            "constraints": ["Avoid Tuesday call"],
            "administrative": True
        },
        "APD": {
            "full_name": "Associate Program Director",
            "clinic_slots_per_week": 2,
            "constraints": ["Avoid Tuesday call"],
            "administrative": True
        },
        "OIC": {
            "full_name": "Officer in Charge",
            "clinic_slots_per_week": 2,
            "constraints": ["Standard constraints"],
            "administrative": False
        },
        "DEPT_CHIEF": {
            "full_name": "Department Chief",
            "clinic_slots_per_week": 1,
            "constraints": ["Prefers Wednesday call"],
            "administrative": True
        },
        "SPORTS_MED": {
            "full_name": "Sports Medicine",
            "clinic_slots_per_week": 0,
            "sports_med_clinic": 4,
            "constraints": ["Sports Medicine clinic only"],
            "administrative": False
        },
        "CORE": {
            "full_name": "Core Faculty",
            "clinic_slots_per_week": "Max 4",
            "constraints": ["Standard constraints"],
            "administrative": False
        }
    },

    "screener_roles": {
        "DEDICATED": {"efficiency": "100%", "description": "Full-time dedicated screener"},
        "RN": {"efficiency": "90%", "description": "Registered Nurse"},
        "EMT": {"efficiency": "80%", "description": "Emergency Medical Technician"},
        "RESIDENT": {"efficiency": "70%", "description": "Resident covering screening"}
    }
}


# =============================================================================
# PII/SECURITY CONTEXT
# =============================================================================

PII_SECURITY_CONTEXT: dict[str, list[str]] = {
    "never_expose": [
        "person.name",
        "person.email",
        "absence.tdy_location",
        "absence.deployment_location",
        "absence.deployment_dates",
        "schedule_assignment (with names)"
    ],

    "safe_fields": [
        "person_id (anonymized)",
        "role (PGY-1, PGY-2, etc.)",
        "constraint_name",
        "violation_type",
        "date (without personal context)"
    ],

    "risk_levels": {
        "CRITICAL": ["TDY locations", "Deployment info"],
        "HIGH": ["Names", "Email addresses"],
        "MEDIUM": ["Schedule assignments with IDs"],
        "LOW": ["Dates", "Constraint types"]
    }
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def expand_abbreviations(text: str, first_occurrence_only: bool = False) -> str:
    """
    Expand known abbreviations in text for clarity.

    Args:
        text: Input text potentially containing abbreviations
        first_occurrence_only: If True, only expand first occurrence of each abbreviation

    Returns:
        Text with abbreviations expanded as "ABBREV (Full Name)"

    Example:
        >>> expand_abbreviations("PGY-1 on FMIT")
        "PGY-1 (Post-Graduate Year 1) on FMIT (Family Medicine Inpatient Team)"
    """
    expanded_text = text
    expanded_set = set()

    # Sort by length (longest first) to avoid partial matches
    sorted_abbrevs = sorted(ABBREVIATIONS.keys(), key=len, reverse=True)

    for abbrev in sorted_abbrevs:
        if abbrev in expanded_text:
            if first_occurrence_only and abbrev in expanded_set:
                continue

            full_name = ABBREVIATIONS[abbrev]
            # Use word boundary to avoid partial matches
            pattern = r'\b' + re.escape(abbrev) + r'\b'
            replacement = f"{abbrev} ({full_name})"

            if first_occurrence_only:
                expanded_text = re.sub(pattern, replacement, expanded_text, count=1)
                expanded_set.add(abbrev)
            else:
                expanded_text = re.sub(pattern, replacement, expanded_text)

    return expanded_text


def explain_constraint(constraint_name: str) -> dict[str, Any] | None:
    """
    Get detailed explanation of a constraint.

    Args:
        constraint_name: Name of the constraint (e.g., "EightyHourRuleConstraint")

    Returns:
        Dictionary with constraint details or None if not found

    Example:
        >>> explain_constraint("EightyHourRuleConstraint")
        {
            "type": "hard",
            "short": "ACGME 80-hour weekly limit",
            "description": "...",
            "violation_impact": "REGULATORY - ACGME compliance violation",
            ...
        }
    """
    return CONSTRAINT_EXPLANATIONS.get(constraint_name)


def explain_pattern(pattern_name: str) -> dict[str, Any] | None:
    """
    Get detailed explanation of a scheduling pattern.

    Args:
        pattern_name: Name of the pattern (e.g., "inverted_wednesday")

    Returns:
        Dictionary with pattern details or None if not found

    Example:
        >>> explain_pattern("fmit_week")
        {
            "name": "FMIT Week Pattern",
            "description": "Family Medicine Inpatient Team week-long rotation",
            ...
        }
    """
    return SCHEDULING_PATTERNS.get(pattern_name)


def enrich_violation_response(violation: dict[str, Any]) -> dict[str, Any]:
    """
    Add domain context to a constraint violation response.

    Takes a raw violation dict and enriches it with:
    - Constraint explanation
    - Abbreviation expansion
    - Fix suggestions
    - Code references

    Args:
        violation: Dictionary containing violation details

    Returns:
        Enriched violation dictionary with added context

    Example:
        >>> violation = {
        ...     "constraint": "EightyHourRuleConstraint",
        ...     "message": "PGY-1 exceeded 80 hours"
        ... }
        >>> enrich_violation_response(violation)
        {
            "constraint": "EightyHourRuleConstraint",
            "message": "PGY-1 (Post-Graduate Year 1) exceeded 80 hours",
            "explanation": {...},
            "fix_options": [...],
            ...
        }
    """
    enriched = violation.copy()

    # Get constraint explanation
    constraint_name = violation.get("constraint", "")
    if constraint_name:
        explanation = explain_constraint(constraint_name)
        if explanation:
            enriched["explanation"] = explanation
            enriched["fix_options"] = explanation.get("fix_options", [])
            enriched["violation_impact"] = explanation.get("violation_impact", "")
            enriched["code_reference"] = explanation.get("code_reference", "")

    # Expand abbreviations in message
    if "message" in enriched:
        enriched["message"] = expand_abbreviations(enriched["message"], first_occurrence_only=True)

    # Expand abbreviations in details
    if "details" in enriched:
        enriched["details"] = expand_abbreviations(enriched["details"], first_occurrence_only=True)

    return enriched


def get_role_context(role: str) -> dict[str, Any] | None:
    """
    Get context information for a faculty or screener role.

    Args:
        role: Role identifier (e.g., "PD", "APD", "RN")

    Returns:
        Dictionary with role context or None if not found

    Example:
        >>> get_role_context("APD")
        {
            "full_name": "Associate Program Director",
            "clinic_slots_per_week": 2,
            "constraints": ["Avoid Tuesday call"],
            ...
        }
    """
    # Check faculty roles
    if role in ROLE_CONTEXT["faculty_roles"]:
        return ROLE_CONTEXT["faculty_roles"][role]

    # Check screener roles
    if role in ROLE_CONTEXT["screener_roles"]:
        return ROLE_CONTEXT["screener_roles"][role]

    return None


def list_all_abbreviations() -> list[dict[str, str]]:
    """
    Get a list of all known abbreviations.

    Returns:
        List of dictionaries with "abbrev" and "full_name" keys

    Example:
        >>> abbrevs = list_all_abbreviations()
        >>> abbrevs[0]
        {"abbrev": "PGY-1", "full_name": "Post-Graduate Year 1 (first-year resident/intern)"}
    """
    return [
        {"abbrev": abbrev, "full_name": full_name}
        for abbrev, full_name in sorted(ABBREVIATIONS.items())
    ]


def list_all_constraints() -> list[dict[str, str]]:
    """
    Get a list of all documented constraints.

    Returns:
        List of dictionaries with constraint name, type, and short description

    Example:
        >>> constraints = list_all_constraints()
        >>> constraints[0]
        {
            "name": "EightyHourRuleConstraint",
            "type": "hard",
            "short": "ACGME 80-hour weekly limit"
        }
    """
    return [
        {
            "name": name,
            "type": details.get("type", ""),
            "short": details.get("short", "")
        }
        for name, details in sorted(CONSTRAINT_EXPLANATIONS.items())
    ]


def is_pii_safe(field_name: str) -> bool:
    """
    Check if a field is safe to expose in MCP responses.

    Args:
        field_name: Name of the field to check

    Returns:
        True if safe to expose, False if contains PII/sensitive data

    Example:
        >>> is_pii_safe("person_id")
        True
        >>> is_pii_safe("person.email")
        False
    """
    # Check against never_expose list
    for unsafe_field in PII_SECURITY_CONTEXT["never_expose"]:
        if unsafe_field in field_name.lower():
            return False

    # Check if it's in safe_fields list
    for safe_field in PII_SECURITY_CONTEXT["safe_fields"]:
        if safe_field.split()[0] in field_name.lower():
            return True

    # Default to unsafe if uncertain
    return False


# =============================================================================
# MODULE METADATA
# =============================================================================

__all__ = [
    # Data structures
    "ABBREVIATIONS",
    "CONSTRAINT_EXPLANATIONS",
    "SCHEDULING_PATTERNS",
    "ROLE_CONTEXT",
    "PII_SECURITY_CONTEXT",

    # Helper functions
    "expand_abbreviations",
    "explain_constraint",
    "explain_pattern",
    "enrich_violation_response",
    "get_role_context",
    "list_all_abbreviations",
    "list_all_constraints",
    "is_pii_safe",
]
