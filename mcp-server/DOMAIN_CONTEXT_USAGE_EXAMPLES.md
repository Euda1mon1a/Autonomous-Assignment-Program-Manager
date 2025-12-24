# Domain Context Module - Usage Examples for MCP Tools

**Purpose:** Show how to integrate domain_context.py into MCP tools for better user experience

---

## Example 1: Enriching Constraint Violation Responses

### Before (Raw violation)
```python
@mcp.tool()
async def check_constraints(schedule_id: str) -> dict:
    violations = await get_violations(schedule_id)
    return {
        "violations": [
            {
                "constraint": "EightyHourRuleConstraint",
                "message": "PGY-1 worked 85 hours in week 3"
            }
        ]
    }
```

**User sees:** Technical constraint name with no context

### After (With domain context)
```python
from scheduler_mcp.domain_context import enrich_violation_response

@mcp.tool()
async def check_constraints(schedule_id: str) -> dict:
    violations = await get_violations(schedule_id)

    enriched_violations = [
        enrich_violation_response(v) for v in violations
    ]

    return {"violations": enriched_violations}
```

**User now sees:**
```json
{
  "constraint": "EightyHourRuleConstraint",
  "message": "PGY-1 (Post-Graduate Year 1) worked 85 hours in week 3",
  "explanation": {
    "type": "hard",
    "short": "ACGME 80-hour weekly limit",
    "description": "Residents cannot work more than 80 hours per week...",
    "violation_impact": "REGULATORY - ACGME compliance violation"
  },
  "fix_options": [
    "Reduce assignments in the current week",
    "Redistribute assignments across the 4-week block",
    "Add additional residents to share load"
  ],
  "code_reference": "backend/app/scheduling/constraints/acgme.py:141"
}
```

---

## Example 2: Creating a Glossary Tool

```python
from scheduler_mcp.domain_context import (
    list_all_abbreviations,
    list_all_constraints,
    SCHEDULING_PATTERNS
)

@mcp.tool()
async def explain_term(term: str) -> dict:
    """
    Explain a scheduling term, abbreviation, or constraint.

    Args:
        term: The term to explain (e.g., "PGY-1", "FMIT", "EightyHourRule")

    Returns:
        Explanation with context
    """
    from scheduler_mcp.domain_context import (
        ABBREVIATIONS,
        explain_constraint,
        explain_pattern
    )

    # Check if it's an abbreviation
    if term in ABBREVIATIONS:
        return {
            "type": "abbreviation",
            "term": term,
            "full_name": ABBREVIATIONS[term]
        }

    # Check if it's a constraint
    explanation = explain_constraint(term)
    if explanation:
        return {
            "type": "constraint",
            "term": term,
            **explanation
        }

    # Check if it's a pattern
    pattern = explain_pattern(term)
    if pattern:
        return {
            "type": "pattern",
            "term": term,
            **pattern
        }

    return {
        "type": "unknown",
        "message": f"Term '{term}' not found in glossary"
    }

@mcp.tool()
async def list_glossary() -> dict:
    """List all available terms in the glossary."""
    abbrevs = list_all_abbreviations()
    constraints = list_all_constraints()
    patterns = list(SCHEDULING_PATTERNS.keys())

    return {
        "abbreviations": abbrevs,
        "constraints": constraints,
        "patterns": patterns,
        "total_terms": len(abbrevs) + len(constraints) + len(patterns)
    }
```

---

## Example 3: PII-Safe Field Filtering

```python
from scheduler_mcp.domain_context import is_pii_safe

@mcp.tool()
async def get_schedule_details(schedule_id: str) -> dict:
    """Get schedule details with PII filtering."""
    raw_schedule = await fetch_schedule(schedule_id)

    # Filter out PII-sensitive fields
    safe_schedule = {}
    for field, value in raw_schedule.items():
        if is_pii_safe(field):
            safe_schedule[field] = value
        else:
            safe_schedule[field] = "[REDACTED - PII]"

    return safe_schedule

# Example output:
# {
#   "schedule_id": "SCH-001",
#   "person_id": "RES-123",
#   "role": "PGY-2",
#   "person.name": "[REDACTED - PII]",
#   "person.email": "[REDACTED - PII]",
#   "date": "2025-01-15"
# }
```

---

## Example 4: Context-Aware Error Messages

```python
from scheduler_mcp.domain_context import (
    expand_abbreviations,
    explain_constraint
)

@mcp.tool()
async def assign_shift(
    person_id: str,
    date: str,
    rotation: str
) -> dict:
    """Assign a shift with context-aware error handling."""

    try:
        assignment = await create_assignment(person_id, date, rotation)
        return {
            "success": True,
            "assignment": assignment
        }

    except ConstraintViolation as e:
        # Get constraint explanation
        explanation = explain_constraint(e.constraint_name)

        # Expand abbreviations in error message
        expanded_message = expand_abbreviations(e.message)

        return {
            "success": False,
            "error": {
                "constraint": e.constraint_name,
                "message": expanded_message,
                "explanation": explanation["short"] if explanation else None,
                "fix_suggestions": explanation.get("fix_options", []) if explanation else [],
                "severity": explanation.get("violation_impact", "UNKNOWN") if explanation else "UNKNOWN"
            }
        }
```

---

## Example 5: Pattern Detection and Explanation

```python
from scheduler_mcp.domain_context import explain_pattern
from datetime import datetime

@mcp.tool()
async def explain_date_pattern(date: str) -> dict:
    """
    Explain what scheduling pattern applies to a specific date.

    Args:
        date: ISO date string (YYYY-MM-DD)

    Returns:
        Pattern explanation for that date
    """
    dt = datetime.fromisoformat(date)

    # Check if it's a Wednesday
    if dt.weekday() == 2:  # Wednesday
        day_of_month = dt.day

        # 4th Wednesday check (days 22-28)
        if 22 <= day_of_month <= 28:
            pattern = explain_pattern("inverted_wednesday")
            return {
                "date": date,
                "day_of_week": "Wednesday",
                "pattern": "Inverted Wednesday (4th Wednesday)",
                "details": pattern,
                "special_rules": [
                    "Residents: Lecture AM, Advising PM",
                    "Faculty: Different faculty AM vs PM required"
                ]
            }
        else:
            return {
                "date": date,
                "day_of_week": "Wednesday",
                "pattern": "Normal Wednesday",
                "special_rules": [
                    "Residents: ASM (Academic Sports Medicine) AM",
                    "Residents: Didactics PM"
                ]
            }

    return {
        "date": date,
        "day_of_week": dt.strftime("%A"),
        "pattern": "Standard day",
        "special_rules": []
    }
```

---

## Example 6: Interactive Constraint Help

```python
from scheduler_mcp.domain_context import (
    explain_constraint,
    list_all_constraints
)

@mcp.tool()
async def constraint_help(constraint_name: str = None) -> dict:
    """
    Get help about scheduling constraints.

    Args:
        constraint_name: Optional specific constraint to explain.
                        If None, lists all constraints.

    Returns:
        Constraint information
    """
    if constraint_name:
        # Explain specific constraint
        explanation = explain_constraint(constraint_name)
        if not explanation:
            return {
                "error": f"Constraint '{constraint_name}' not found",
                "available_constraints": [c["name"] for c in list_all_constraints()]
            }

        return {
            "constraint": constraint_name,
            **explanation,
            "usage_tip": "Use this in violation responses to explain to users"
        }
    else:
        # List all constraints
        constraints = list_all_constraints()

        return {
            "total_constraints": len(constraints),
            "hard_constraints": [c for c in constraints if c["type"] == "hard"],
            "soft_constraints": [c for c in constraints if c["type"] == "soft"],
            "tip": "Call with constraint_name parameter for detailed explanation"
        }
```

---

## Example 7: Role Context for Assignments

```python
from scheduler_mcp.domain_context import get_role_context

@mcp.tool()
async def validate_assignment(
    person_role: str,
    assignment_type: str,
    clinic_slots: int
) -> dict:
    """
    Validate if an assignment is appropriate for a role.

    Args:
        person_role: Faculty role (e.g., "PD", "APD", "CORE")
        assignment_type: Type of assignment (e.g., "clinic")
        clinic_slots: Number of clinic slots requested

    Returns:
        Validation result with context
    """
    role_info = get_role_context(person_role)

    if not role_info:
        return {
            "valid": False,
            "error": f"Unknown role: {person_role}"
        }

    # Check clinic slot limits
    max_slots = role_info.get("clinic_slots_per_week", 0)

    if assignment_type == "clinic" and clinic_slots > max_slots:
        return {
            "valid": False,
            "error": f"{role_info['full_name']} can only do {max_slots} clinic slots/week",
            "requested": clinic_slots,
            "allowed": max_slots,
            "role_constraints": role_info.get("constraints", [])
        }

    return {
        "valid": True,
        "role": role_info["full_name"],
        "constraints": role_info.get("constraints", [])
    }
```

---

## Example 8: Batch Abbreviation Expansion for Reports

```python
from scheduler_mcp.domain_context import expand_abbreviations

@mcp.tool()
async def generate_schedule_report(
    schedule_id: str,
    expand_terms: bool = True
) -> dict:
    """
    Generate a human-readable schedule report.

    Args:
        schedule_id: Schedule to report on
        expand_terms: Whether to expand abbreviations (default True)

    Returns:
        Report with expanded terminology
    """
    raw_report = await fetch_schedule_report(schedule_id)

    if expand_terms:
        # Expand all abbreviations in the report text
        report_text = raw_report["summary"]
        expanded_text = expand_abbreviations(
            report_text,
            first_occurrence_only=True  # Only expand first occurrence for readability
        )

        raw_report["summary"] = expanded_text
        raw_report["terminology_expanded"] = True

    return raw_report
```

---

## Integration Checklist

When integrating domain_context into MCP tools:

- [ ] Import relevant functions at the top of your tool module
- [ ] Apply `enrich_violation_response()` to all constraint violations
- [ ] Use `expand_abbreviations()` for user-facing text
- [ ] Use `is_pii_safe()` before exposing any database fields
- [ ] Provide `explain_term()` or similar help tools
- [ ] Add code references from explanations to error messages
- [ ] Test with non-technical users to ensure clarity

---

## Best Practices

1. **Always expand on first use:** Use `first_occurrence_only=True` for long documents
2. **Include fix options:** Violations should always include actionable fixes
3. **Provide code references:** Help developers debug constraint issues
4. **Filter PII:** Always check `is_pii_safe()` before exposing fields
5. **Context-aware errors:** Use constraint explanations in error responses
6. **Help tools:** Provide glossary and help tools for users
7. **Consistent formatting:** Use the same enrichment across all tools

---

## Testing Your Integration

```python
# Test script
import sys
sys.path.insert(0, 'src')

from scheduler_mcp.domain_context import *

# Test 1: Abbreviation expansion
assert "Post-Graduate Year 1" in expand_abbreviations("PGY-1")

# Test 2: Constraint explanation
explanation = explain_constraint("EightyHourRuleConstraint")
assert explanation["type"] == "hard"
assert len(explanation["fix_options"]) > 0

# Test 3: Violation enrichment
violation = {"constraint": "EightyHourRuleConstraint", "message": "Test"}
enriched = enrich_violation_response(violation)
assert "explanation" in enriched
assert "fix_options" in enriched

# Test 4: PII safety
assert is_pii_safe("person_id") == True
assert is_pii_safe("person.email") == False

print("✓ All integration tests passed")
```

---

*Reference: domain_context.py*
*Created: 2025-12-24*
