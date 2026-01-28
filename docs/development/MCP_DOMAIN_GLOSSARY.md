# MCP Domain Glossary & Context Guide

> **Purpose:** Enable MCP tools and AI agents to understand domain-specific terminology
> **Created:** 2025-12-24
> **Status:** Living document - update as patterns are discovered

---

## Table of Contents

1. [Abbreviations](#abbreviations)
2. [Scheduling Concepts](#scheduling-concepts)
3. [Constraint Patterns](#constraint-patterns)
4. [Role Types](#role-types)
5. [Rotation & Activity Types](#rotation-types-templates)
6. [Temporal Patterns](#temporal-patterns)
7. [Open Questions](#open-questions)

---

## Abbreviations

### Personnel & Training Levels

| Abbreviation | Full Name | Description |
|--------------|-----------|-------------|
| **PGY-1** | Post-Graduate Year 1 | First-year resident (intern); cannot supervise learners |
| **PGY-2** | Post-Graduate Year 2 | Second-year resident; can supervise up to 2 learners |
| **PGY-3** | Post-Graduate Year 3 | Third-year resident; can supervise up to 2 learners |
| **MS** | Medical Student | MS3/MS4 on clerkship rotation |
| **TY** | Transitional Year Intern | Non-FM intern rotating through; no FMIT required |
| **PSYCH** | Psychiatry Intern | Psychiatry intern rotating through; no FMIT required |

### Faculty Roles

| Abbreviation | Full Name | Clinic Slots/Week | Special Constraints |
|--------------|-----------|-------------------|---------------------|
| **PD** | Program Director | 0 | Avoid Tuesday call |
| **APD** | Associate Program Director | 2 | Avoid Tuesday call |
| **OIC** | Officer in Charge | 2 | Standard constraints |
| **SM** | Sports Medicine | 0 regular, 4 SM | Sports Medicine clinic only |
| **CORE** | Core Faculty | Max 4 | Standard constraints |
| **DEPT_CHIEF** | Department Chief | 1 | Prefers Wednesday call |

### Regulatory Bodies

| Abbreviation | Full Name | Description |
|--------------|-----------|-------------|
| **ACGME** | Accreditation Council for Graduate Medical Education | Regulates residency programs; enforces work hour limits |
| **LCME** | Liaison Committee on Medical Education | Accredits med schools; does NOT track hours like ACGME |

### Schedule Elements

| Abbreviation | Full Name | Description |
|--------------|-----------|-------------|
| **FMIT** | Family Medicine Inpatient Team | Inpatient rotation; includes overnight call Thursday |
| **PC** | Post Call | Day after overnight call; lighter duties or recovery |
| **ASM** | Academic Sports Medicine | Wednesday AM session for med students |
| **NF** | Night Float | Overnight coverage rotation |
| **AM** | Morning Session | First half of day (typically 7am-12pm) |
| **PM** | Afternoon Session | Second half of day (typically 1pm-5pm) |

### Military/Administrative

| Abbreviation | Full Name | Description | PII Risk |
|--------------|-----------|-------------|----------|
| **TDY** | Temporary Duty | Travel for military assignment | HIGH - reveals movements |
| **DEP** | Deployment | Extended military assignment | HIGH - OPSEC sensitive |
| **FEM** | Family Emergency | Personal emergency leave | MEDIUM - reveals personal info |
| **PER** | Personal | Personal time off | LOW |
| **MTF** | Military Treatment Facility | Medical facility on military base | N/A |
| **PERSEC** | Personnel Security | Protection of personal information | N/A |
| **OPSEC** | Operations Security | Protection of operational information | N/A |

---

## Scheduling Concepts

### Block Structure

```
Academic Year: 365 days
├── 13 Blocks × 4 weeks each (52 weeks)
├── Each day: AM session + PM session
└── Total: 730 half-day sessions per year
```

### Assignment Hierarchy

```
Schedule (Academic Year)
└── Block (4-week period)
    └── Day
        └── Session (AM/PM)
            └── Assignment
                ├── Person (resident/faculty)
                ├── Template (rotation type)
                └── Location (clinic/hospital)
```

### Supervision Ratios (ACGME)

| Supervisor Level | Max Learners |
|------------------|--------------|
| PGY-1 (Intern) | 0 - cannot supervise |
| PGY-2/3 | 2 learners max |
| Attending (Faculty) | 4 residents max |

### Work Hour Rules (ACGME)

| Rule | Limit | Measurement |
|------|-------|-------------|
| 80-Hour Rule | 80 hours/week | Rolling 4-week average |
| 1-in-7 Rule | 1 day off per 7 | 24-hour period |
| Max Shift | 24 hours + 4 | Continuous duty |

---

## Constraint Patterns

### Hard Constraints (Must Be Satisfied)

| Constraint | Description | Code Reference |
|------------|-------------|----------------|
| `AvailabilityConstraint` | Person must be available (not on leave/TDY) | `constraints/acgme.py:53` |
| `OnePersonPerBlockConstraint` | One assignment per person per session | `constraints/capacity.py:31` |
| `EightyHourRuleConstraint` | Max 80 hours/week averaged over 4 weeks | `constraints/acgme.py:141` |
| `OneInSevenRuleConstraint` | One 24-hour off every 7 days | `constraints/acgme.py:361` |
| `SupervisionRatioConstraint` | Faculty:Resident ratios per ACGME | `constraints/acgme.py:517` |
| `InvertedWednesdayConstraint` | 4th Wednesday special schedule | `constraints/temporal.py:380` |
| `WednesdayAMInternOnlyConstraint` | Wednesday AM clinic staffing | `constraints/temporal.py:26` |
| `FMITWeekBlockingConstraint` | FMIT week blocks entire week | `constraints/fmit.py:75` |
| `PostCallAutoAssignmentConstraint` | Post-call recovery assignment | `constraints/post_call.py:41` |

### Soft Constraints (Optimization Goals)

| Constraint | Description | Weight |
|------------|-------------|--------|
| `EquityConstraint` | Fair distribution of assignments | HIGH |
| `ContinuityConstraint` | Same faculty for patient panels | MEDIUM |
| `PreferenceConstraint` | Honor faculty preferences | LOW |
| `HubProtectionConstraint` | Protect critical nodes from overload | HIGH |
| `UtilizationBufferConstraint` | Keep utilization under 80% | HIGH |

---

## Role Types

### Person Types

```python
class PersonType(str, Enum):
    RESIDENT = "resident"    # PGY-1, PGY-2, PGY-3
    FACULTY = "faculty"      # Attending physicians
    LEARNER = "learner"      # Medical students, rotating interns
    SCREENER = "screener"    # Clinical support staff
```

### Faculty Roles (from `backend/app/models/person.py:14`)

```python
class FacultyRole(str, Enum):
    PD = "pd"              # Program Director: 0 clinic, avoid Tue call
    APD = "apd"            # Associate PD: 2/week, avoid Tue call
    OIC = "oic"            # Officer in Charge: 2/week
    DEPT_CHIEF = "dept_chief"  # Dept Chief: 1/week, prefers Wed call
    SPORTS_MED = "sports_med"  # Sports Medicine: 0 regular, 4 SM clinic
    CORE = "core"          # Core Faculty: max 4/week
```

### Screener Roles

```python
class ScreenerRole(str, Enum):
    DEDICATED = "dedicated"  # 100% efficiency
    RN = "rn"               # 90% efficiency
    EMT = "emt"             # 80% efficiency
    RESIDENT = "resident"   # 70% efficiency (when covering)
```

---

## Rotation Types (Templates)

### Rotation Categories

| Rotation Type | Description | Typical Duration |
|---------------|-------------|------------------|
| `clinic` | Continuity clinic rotations | Half-day slots |
| `outpatient` | Elective/selective ambulatory rotations | Half-day slots |
| `inpatient` | Inpatient services (FMIT, wards) | Full week |
| `procedures` | Procedural rotations | Half-day slots |
| `conference` | Didactics/education blocks | Usually PM |
| `call` | On-call coverage rotations | Overnight |
| `recovery` | Post-call recovery | Full day |
| `admin` | Administrative rotations | Varies |
| `leave` | Leave/absence rotations | Varies |

## Activity Types (Slot-level)

These map to **weekly pattern** slots and are not rotation categories.

| Activity Type | Description | Typical Duration |
|---------------|-------------|------------------|
| `fm_clinic` | Family Medicine clinic | AM or PM |
| `specialty` | Specialty clinic | AM or PM |
| `elective` | Elective session | AM or PM |
| `conference` | Lecture/didactics | Usually PM |
| `inpatient` | Inpatient coverage | Full day |
| `call` | Call coverage | Overnight |
| `procedure` | Procedure session | AM or PM |
| `off` | Off / protected time | AM or PM |

### Wednesday Special Sessions

| Wednesday # | AM Activity | PM Activity | Notes |
|-------------|-------------|-------------|-------|
| 1st, 2nd, 3rd | ASM (med students) | Didactics | Normal pattern |
| 4th (Inverted) | Lecture (all) | Advising | Faculty rotation differs |
| 5th (rare) | Normal | Normal | Follows 1st pattern |

---

## Temporal Patterns

### "Inverted Wednesday" Pattern

**Location:** `backend/app/scheduling/constraints/temporal.py:380`

```
Normal Wednesday (1st, 2nd, 3rd of month):
┌────────────────┬────────────────┐
│      AM        │      PM        │
├────────────────┼────────────────┤
│ Residents:     │ Residents:     │
│   Clinic       │   Lecture/Sim  │
│                │                │
│ Faculty:       │ Faculty:       │
│   Clinic       │   1 covers     │
│                │   clinic       │
└────────────────┴────────────────┘

4th Wednesday "Inverted" (day 22-28 of month):
┌────────────────┬────────────────┐
│      AM        │      PM        │
├────────────────┼────────────────┤
│ Residents:     │ Residents:     │
│   Lecture      │   Advising     │
│                │                │
│ Faculty:       │ Faculty:       │
│   1 covers     │   1 DIFFERENT  │
│   clinic       │   covers clinic│
└────────────────┴────────────────┘

Key: AM and PM faculty MUST be different people (equity)
```

### FMIT Week Pattern

```
FMIT Week (any 1 week per 4-week block):
┌─────────┬──────────────────────────────────────┐
│ Day     │ Schedule                              │
├─────────┼──────────────────────────────────────┤
│ Mon     │ FMIT AM + PM                         │
│ Tue     │ FMIT AM + PM                         │
│ Wed     │ ASM AM (still required) + FMIT PM    │
│ Thu     │ FMIT AM + PM + OVERNIGHT CALL        │
│ Fri     │ POST-CALL (PC) - recovery day        │
│ Sat/Sun │ Weekend call if on FMIT              │
└─────────┴──────────────────────────────────────┘
```

### Post-Call Recovery

```
After overnight call:
├── Next AM: Light duties or off
├── Next PM: Off
└── Constraint: No clinic for 24 hours post-call
```

---

## Open Questions

> **Instructions for AI Agents:** When encountering unclear terminology or patterns,
> add questions here rather than guessing. Humans will clarify.

### Terminology Questions

| Question | Context Found | Status |
|----------|---------------|--------|
| What is "turf" in FMIT context? | `FMITContinuityTurfConstraint` | NEEDS CLARIFICATION |
| What is "catalyst" in scheduling? | `scheduling_catalyst/models.py` | NEEDS CLARIFICATION |
| What does "hub" mean in resilience? | `HubProtectionConstraint` | NEEDS CLARIFICATION |
| What is "blast radius" in scheduling? | Mentioned in CLAUDE.md | NEEDS CLARIFICATION |

### Pattern Questions

| Question | Context Found | Status |
|----------|---------------|--------|
| How are "zones" defined for ZoneBoundaryConstraint? | `constraints/resilience.py:473` | NEEDS CLARIFICATION |
| What triggers "N-1 vulnerability"? | `N1VulnerabilityConstraint` | NEEDS CLARIFICATION |
| How is "preference trail" calculated? | `PreferenceTrailConstraint` | NEEDS CLARIFICATION |

### Business Rule Questions

| Question | Context Found | Status |
|----------|---------------|--------|
| Can PGY-1 ever supervise in emergency? | Constraint says 0 learners | NEEDS CLARIFICATION |
| Are TDY absences always classified as OPSEC? | sanitize_pii.py removes them | NEEDS CLARIFICATION |
| What happens if 5th Wednesday exists? | Only 4th Wednesday has special rules | NEEDS CLARIFICATION |

---

## Usage in MCP Tools

### Returning Context-Aware Responses

```python
# Example: Tool response with domain context
@mcp.tool()
async def explain_violation(violation_id: str) -> dict:
    """Explain a constraint violation with domain context."""

    violation = get_violation(violation_id)

    # Add domain context based on constraint type
    if "InvertedWednesday" in violation.constraint:
        return {
            "constraint": "InvertedWednesday",
            "explanation": "4th Wednesday requires different faculty AM vs PM",
            "rule": "Residents: Lecture AM, Advising PM. Faculty: 1 AM, 1 different PM",
            "fix_options": [
                "Assign different faculty to PM slot",
                "Swap with another faculty member"
            ],
            "reference": "constraints/temporal.py:380"
        }
```

### Abbreviation Expansion

```python
# MCP tools should expand abbreviations in responses
ABBREVIATION_MAP = {
    "PGY": "Post-Graduate Year",
    "FMIT": "Family Medicine Inpatient Team",
    "PC": "Post-Call",
    "ASM": "Academic Sports Medicine",
    "TDY": "Temporary Duty",
    "ACGME": "Accreditation Council for Graduate Medical Education",
    # ... etc
}

def expand_abbreviations(text: str) -> str:
    """Expand abbreviations for clarity in responses."""
    for abbrev, full in ABBREVIATION_MAP.items():
        text = text.replace(abbrev, f"{abbrev} ({full})")
    return text
```

---

## PII Sanitization Reference

### Fields That Must Never Leave Local

| Field | Risk Level | Handling |
|-------|------------|----------|
| `person.name` | HIGH (PERSEC) | Use `person_id` only |
| `person.email` | HIGH | Never in MCP responses |
| `absence.tdy_location` | CRITICAL (OPSEC) | Never in MCP responses |
| `absence.deployment_*` | CRITICAL (OPSEC) | Never in MCP responses |
| `schedule_assignment` | MEDIUM | Use anonymized IDs |

### Safe Fields for MCP Responses

| Field | Example | Notes |
|-------|---------|-------|
| `person_id` | `"RES-001"` | Anonymized identifier |
| `role` | `"PGY-2"` | Training level, not identity |
| `constraint_name` | `"EightyHourRule"` | Technical reference |
| `violation_type` | `"HOURS_EXCEEDED"` | Category, not details |
| `date` | `"2025-01-15"` | Date only, no personal context |

---

## Document Maintenance

### Adding New Terms

When encountering new terminology:

1. Search codebase for usage context
2. Add to appropriate section above
3. If unclear, add to **Open Questions**
4. Update MCP tools if needed

### Review Cadence

- Weekly: Review Open Questions with domain experts
- Monthly: Verify abbreviations against codebase
- Per-release: Validate constraint patterns match code

---

*Last Updated: 2025-12-24*
*Next Review: TBD*
