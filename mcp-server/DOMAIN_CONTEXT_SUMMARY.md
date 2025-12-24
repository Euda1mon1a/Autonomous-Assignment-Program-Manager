# Domain Context Module - Implementation Summary

**Created:** 2025-12-24
**File:** `mcp-server/src/scheduler_mcp/domain_context.py`
**Lines:** 699
**Purpose:** Provide abbreviation expansion, constraint explanations, and scheduling pattern context for MCP tools

---

## File Structure

### 1. ABBREVIATIONS Dictionary (28 entries)

Comprehensive mapping of domain abbreviations to full names:

#### Personnel & Training Levels (8)
- PGY-1, PGY-2, PGY-3, PGY
- MS, MS3, MS4
- TY, PSYCH

#### Faculty Roles (6)
- PD, APD, OIC
- SM, CORE, DEPT_CHIEF

#### Regulatory Bodies (2)
- ACGME, LCME

#### Schedule Elements (6)
- FMIT, PC, ASM
- NF, AM, PM

#### Military/Administrative (8)
- TDY, DEP, FEM, PER
- MTF, PERSEC, OPSEC
- PII, PHI

---

## 2. CONSTRAINT_EXPLANATIONS Dictionary (13 documented)

### Hard Constraints (9)
1. **AvailabilityConstraint** - Person must be available (not on leave/TDY)
2. **OnePersonPerBlockConstraint** - One assignment per person per session
3. **EightyHourRuleConstraint** - ACGME 80-hour weekly limit
4. **OneInSevenRuleConstraint** - ACGME 1-in-7 rest requirement
5. **SupervisionRatioConstraint** - Faculty:Resident ratios per ACGME
6. **InvertedWednesdayConstraint** - 4th Wednesday special schedule
7. **WednesdayAMInternOnlyConstraint** - Wednesday AM clinic staffing
8. **FMITWeekBlockingConstraint** - FMIT week blocks entire week
9. **PostCallAutoAssignmentConstraint** - Post-call recovery assignment

### Soft Constraints (4)
1. **EquityConstraint** - Fair distribution of assignments
2. **ContinuityConstraint** - Same faculty for patient panels
3. **PreferenceConstraint** - Honor faculty preferences
4. **HubProtectionConstraint** - Protect critical nodes from overload
5. **UtilizationBufferConstraint** - Keep utilization under 80%

Each constraint includes:
- Type (hard/soft)
- Short description
- Detailed explanation
- Violation impact
- Fix options (for hard constraints)
- Code reference
- Regulatory reference (where applicable)

---

## 3. SCHEDULING_PATTERNS Dictionary (6 patterns)

### Documented Patterns

1. **inverted_wednesday**
   - Normal vs 4th Wednesday schedule
   - AM/PM faculty must differ
   - Code ref: `constraints/temporal.py:380`

2. **fmit_week**
   - Mon-Fri FMIT pattern
   - Overnight call Thursday
   - Post-call Friday
   - Code ref: `constraints/fmit.py:75`

3. **post_call**
   - Recovery day rules
   - No clinic for 24 hours
   - Code ref: `constraints/post_call.py:41`

4. **block_structure**
   - Academic year hierarchy
   - 13 blocks × 4 weeks
   - 730 total sessions

5. **supervision_ratios**
   - PGY-1: 0 learners
   - PGY-2/3: Max 2 learners
   - Faculty: Max 4 residents

6. **work_hour_rules**
   - 80-hour rule
   - 1-in-7 rule
   - Max shift duration

---

## 4. ROLE_CONTEXT Dictionary

### Faculty Roles (6)
- PD, APD, OIC, DEPT_CHIEF, SPORTS_MED, CORE
- Includes clinic slots/week, constraints, admin status

### Screener Roles (4)
- DEDICATED (100%), RN (90%), EMT (80%), RESIDENT (70%)
- Includes efficiency percentages

---

## 5. PII_SECURITY_CONTEXT Dictionary

### Never Expose (6 fields)
- person.name, person.email
- absence.tdy_location, absence.deployment_*
- schedule_assignment (with names)

### Safe Fields (5 types)
- person_id (anonymized)
- role, constraint_name, violation_type, date

### Risk Levels
- CRITICAL, HIGH, MEDIUM, LOW

---

## 6. Helper Functions (9 functions)

1. **expand_abbreviations(text, first_occurrence_only=False)**
   - Expands known abbreviations
   - Optional first-occurrence-only mode
   - Uses word boundaries to avoid partial matches

2. **explain_constraint(constraint_name)**
   - Returns detailed constraint explanation
   - Includes fix options and references

3. **explain_pattern(pattern_name)**
   - Returns detailed pattern explanation
   - Includes schedule details and code refs

4. **enrich_violation_response(violation)**
   - Adds domain context to violations
   - Expands abbreviations
   - Adds fix suggestions

5. **get_role_context(role)**
   - Returns faculty or screener role details
   - Includes constraints and clinic slots

6. **list_all_abbreviations()**
   - Returns sorted list of all abbreviations

7. **list_all_constraints()**
   - Returns sorted list of all constraints

8. **is_pii_safe(field_name)**
   - Checks if field is safe to expose
   - Used for security validation

9. **__all__** export list
   - Properly exports all public APIs

---

## Additional Constraints Discovered (Not Yet Documented)

During codebase analysis, **19 additional constraints** were found that are not yet documented in domain_context.py:

### Hard Constraints (13)
1. **ClinicCapacityConstraint** - `constraints/capacity.py:120`
2. **MaxPhysiciansInClinicConstraint** - `constraints/capacity.py:234`
3. **FacultyRoleClinicConstraint** - `constraints/faculty_role.py:38`
4. **SMFacultyClinicConstraint** - `constraints/faculty_role.py:263`
5. **WednesdayPMSingleFacultyConstraint** - `constraints/temporal.py:208`
6. **NightFloatPostCallConstraint** - `constraints/night_float_post_call.py:40`
7. **FMITMandatoryCallConstraint** - `constraints/fmit.py:312`
8. **PostFMITRecoveryConstraint** - `constraints/fmit.py:468`
9. **FMITContinuityTurfConstraint** - `constraints/fmit.py:671`
10. **FMITStaffingFloorConstraint** - `constraints/fmit.py:782`
11. **SMResidentFacultyAlignmentConstraint** - `constraints/sports_medicine.py:35`

### Soft Constraints (8)
1. **CoverageConstraint** - `constraints/capacity.py:402`
2. **ZoneBoundaryConstraint** - `constraints/resilience.py:473`
3. **PreferenceTrailConstraint** - `constraints/resilience.py:659`
4. **N1VulnerabilityConstraint** - `constraints/resilience.py:869`
5. **SundayCallEquityConstraint** - `constraints/call_equity.py:39`
6. **WeekdayCallEquityConstraint** - `constraints/call_equity.py:231`
7. **TuesdayCallPreferenceConstraint** - `constraints/call_equity.py:400`
8. **DeptChiefWednesdayPreferenceConstraint** - `constraints/call_equity.py:556`

### Recommendation
These constraints should be added to `CONSTRAINT_EXPLANATIONS` in a future update after reviewing the code to understand their behavior and impact.

---

## Usage Examples

### Example 1: Expand Abbreviations
```python
from scheduler_mcp.domain_context import expand_abbreviations

text = "PGY-1 on FMIT with PC on Friday"
expanded = expand_abbreviations(text)
# Result: "PGY-1 (Post-Graduate Year 1) on FMIT (Family Medicine Inpatient Team)
#          with PC (Post-Call) on Friday"
```

### Example 2: Explain Constraint
```python
from scheduler_mcp.domain_context import explain_constraint

explanation = explain_constraint("EightyHourRuleConstraint")
print(explanation["description"])
print(f"Fix options: {explanation['fix_options']}")
```

### Example 3: Enrich Violation
```python
from scheduler_mcp.domain_context import enrich_violation_response

violation = {
    "constraint": "SupervisionRatioConstraint",
    "message": "PGY-1 cannot supervise learners"
}
enriched = enrich_violation_response(violation)
# Adds explanation, fix_options, code_reference, expands abbreviations
```

### Example 4: Check PII Safety
```python
from scheduler_mcp.domain_context import is_pii_safe

is_pii_safe("person_id")  # True
is_pii_safe("person.email")  # False
is_pii_safe("absence.tdy_location")  # False
```

---

## Integration Points

### For MCP Tools
1. Import and use `enrich_violation_response()` for all constraint violation returns
2. Use `expand_abbreviations()` for all user-facing text
3. Use `is_pii_safe()` to validate fields before exposing
4. Use `explain_constraint()` and `explain_pattern()` for help/documentation tools

### For Error Handlers
1. Catch constraint violations
2. Pass through `enrich_violation_response()`
3. Return enriched response to user

### For Documentation Tools
1. Use `list_all_abbreviations()` for glossary generation
2. Use `list_all_constraints()` for constraint reference
3. Use `SCHEDULING_PATTERNS` for pattern documentation

---

## Files Created

1. **mcp-server/src/scheduler_mcp/domain_context.py** (699 lines)
   - Complete domain context module with all data structures and helper functions

2. **mcp-server/DOMAIN_CONTEXT_SUMMARY.md** (this file)
   - Implementation summary and usage guide

---

## Next Steps

### Immediate
- [ ] Add unit tests for domain_context.py helper functions
- [ ] Update MCP tools to use domain_context for violation responses
- [ ] Add domain_context import to __init__.py

### Future Enhancements
- [ ] Document the 19 additional constraints discovered
- [ ] Add constraint relationship mapping (which constraints conflict/complement)
- [ ] Add pattern detection (auto-identify which pattern applies to a given date/context)
- [ ] Create interactive glossary tool using MCP

### Documentation
- [ ] Update MCP_DOMAIN_GLOSSARY.md with newly discovered constraints
- [ ] Create examples in MCP tool documentation showing domain_context usage
- [ ] Add domain_context to agent skills reference

---

## References

- **Source Glossary:** `docs/development/MCP_DOMAIN_GLOSSARY.md`
- **Constraint Code:** `backend/app/scheduling/constraints/*.py`
- **MCP Server:** `mcp-server/src/scheduler_mcp/`
- **CLAUDE.md Guidelines:** Project-level documentation

---

*Generated: 2025-12-24*
*Author: Claude Code Agent*
*Status: Ready for integration*
