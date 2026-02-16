# Faculty Constraints Implementation Proposal

**Date:** 2026-01-14
**Status:** DRAFT
**Objective:** Align the codebase with the reality of faculty constraints (Min/Max for Clinic, Supervision/AT, and Admin) and remove hardcoded Python dictionaries.

## 1. Problem Analysis

The current `HUMAN_TODO.md` roadmap assumed that `Person` model constraints were sufficient. A deep dive into `faculty_assignment_expansion_service.py` reveals this is **incorrect**.

### The Gap
The `Person` model currently has:
*   `faculty_role` (Enum)
*   `weekly_clinic_limit` (Computed Property -> Returns a single integer MAX)

The **Real Internal Logic** (`FACULTY_CONSTRAINTS` dict) enforces a complex multi-dimensional constraint set:
*   **Clinic (C)**: `min` and `max` (e.g., Core Faculty is 2-4, not just 4)
*   **Attending/Supervision (AT)**: `min` and `max` (e.g., must supervise 1-3 times/week)
*   **GME Admin**: `min` and `max`
*   **Admin Type**: "GME" vs "DFM" vs "SM"

**Critical Issue:** If we blindly switched to the current `Person` model as planned, we would lose the minimum requirements (the "floor") and the specific supervision (AT) quotas, leading to under-scheduled faculty and ACGME violations.

## 2. Proposed Solution: Flexible Constraint Store

To avoid adding 8+ new columns (`c_min`, `c_max`, `at_min`, `at_max`, `gme_min`, `gme_max`, etc.) to the `Person` table—and to allow for future constraints without schema migrations—we propose a **JSON/JSONB** column.

### Schema Change

```python
# backend/app/models/person.py

class Person(Base):
    # ... existing fields ...

    # Stores flexible constraints for the solver/expansion service
    # Schema: {
    #   "c": {"min": int, "max": int},
    #   "at": {"min": int, "max": int},
    #   "gme": {"min": int, "max": int},
    #   "admin_type": str
    # }
    faculty_constraints = Column(JSONB, nullable=True)
```

*Note: For SQLite testing, we can use a generic `JSON` type or a text field with serialization getters/setters.*

### Why JSON?
1.  **Flexibility:** We can add `research_min` or `procedures_max` later without running Alembic.
2.  **Compactness:** Keeps the `Person` table clean.
3.  **Mapping:** Directly maps to the dictionary structure currently hardcoded in the service.

## 3. Migration Strategy (The "Lift & Shift")

We cannot manually enter data for all faculty. We must **script the migration** using the existing hardcoded source of truth.

**Step 1: Alembic Migration**
*   Add `faculty_constraints` column to `persons` table.

**Step 2: Seed/Migration Script**
*   Read the `FACULTY_CONSTRAINTS` dictionary from `faculty_assignment_expansion_service.py`.
*   Iterate through the dictionary.
*   Look up each `Person` by name (fuzzy match or exact match).
*   Dump the dictionary values into the new `faculty_constraints` column.
*   **Safety Check:** Log any names in the dict that don't exist in the DB.

## 4. Service Refactoring

Once the data is in the DB, we rewrite `faculty_assignment_expansion_service.py`:

```python
def _get_faculty_constraints(self, person: Person) -> dict:
    # 1. Try DB Constraints first
    if person.faculty_constraints:
        return {
            "c_min": person.faculty_constraints.get("c", {}).get("min", 0),
            "c_max": person.faculty_constraints.get("c", {}).get("max", 0),
            "at_min": person.faculty_constraints.get("at", {}).get("min", 0),
            # ... and so on
        }

    # 2. Fallback to Role Defaults (if needed)
    return self._get_defaults_for_role(person.faculty_role)
```

## 5. Alternative Considered: Explicit Columns

If strict SQL schema is required, we would add:
*   `clinic_min` (Int)
*   `clinic_max` (Int)
*   `at_min` (Int)
*   `at_max` (Int)
*   `gme_min` (Int)
*   `gme_max` (Int)
*   `admin_department` (Enum/String)

**Pros:** Stronger type safety, easier to query directly (e.g. "Show me all faculty with clinic > 2").
**Cons:** Schema bloat, requires migration for every new constraint type.

**Recommendation:** Proceed with JSONB (Option 2) for agility, unless "Querying by constraint" is a UI requirement.

## 6. Next Steps

1.  Approve this plan.
2.  Generate Alembic migration.
3.  Create the "Lift & Shift" seed script.
4.  Run migration.
5.  Refactor Service.
