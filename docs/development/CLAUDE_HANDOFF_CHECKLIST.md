***REMOVED*** Claude Agent Handoff Checklist

> **Created:** 2025-12-25
> **Purpose:** Prevent integration gaps when handing off between Claude Web and Claude Code
> **Root Cause:** Block 10 constraints were implemented but not registered in ConstraintManager

---

***REMOVED******REMOVED*** Why This Checklist Exists

During Block 10 development, we discovered a pattern: **"Code complete but not wired up."**

1. Claude Web designed constraints with full implementation code
2. Claude Code implemented the constraint classes
3. **Nobody documented or executed the ConstraintManager registration step**
4. Roadmap wasn't updated to reflect completed vs pending work
5. Each agent assumed the other would handle integration

This checklist ensures all handoffs are complete and nothing falls through the cracks.

---

***REMOVED******REMOVED*** Implementation Checklist

When implementing a new constraint, feature, or component, verify ALL of these:

***REMOVED******REMOVED******REMOVED*** Code Layer
- [ ] Code implemented (constraint class, method, etc.)
- [ ] Unit tests written and passing
- [ ] Docstrings and type hints complete

***REMOVED******REMOVED******REMOVED*** Integration Layer
- [ ] Exported from `__init__.py` (if applicable)
- [ ] Registered in manager/registry (if applicable)
- [ ] Imported in parent module (if applicable)

***REMOVED******REMOVED******REMOVED*** Verification Layer
- [ ] Integration tests written (if applicable)
- [ ] Verified constraint appears in `create_default()` or equivalent
- [ ] Docker container synced with new files

***REMOVED******REMOVED******REMOVED*** Documentation Layer
- [ ] Roadmap status updated (mark ✅ with commit hash)
- [ ] CHANGELOG updated (if user-facing)
- [ ] Commit message references the task ID

---

***REMOVED******REMOVED*** Handoff Documentation Template

When handing off between Claude Web and Claude Code, include this in your summary:

```markdown
***REMOVED******REMOVED*** Handoff: [Feature Name]

***REMOVED******REMOVED******REMOVED*** What Was Done
- [x] Designed constraint X in file Y
- [x] Implemented add_to_cpsat() method
- [x] Implemented validate() method

***REMOVED******REMOVED******REMOVED*** What Remains
- [ ] Import in manager.py (line X)
- [ ] Register in create_default() (line Y)
- [ ] Write tests in test_X.py
- [ ] Update roadmap status

***REMOVED******REMOVED******REMOVED*** Verification Command
pytest tests/test_X.py -v

***REMOVED******REMOVED******REMOVED*** Files Modified
- path/to/file1.py (lines X-Y)
- path/to/file2.py (new file)
```

---

***REMOVED******REMOVED*** Integration Checkpoint Questions

Before marking any task as "complete," ask:

***REMOVED******REMOVED******REMOVED*** 1. Is it importable?
Check `__init__.py` exports:
```bash
***REMOVED*** Verify the class can be imported
python -c "from app.scheduling.constraints.fmit import PostFMITSundayBlockingConstraint"
```

***REMOVED******REMOVED******REMOVED*** 2. Is it registered?
Check manager's `create_default()`:
```python
***REMOVED*** Look for the constraint in manager.py
grep -n "PostFMITSundayBlockingConstraint" backend/app/scheduling/constraints/manager.py
```

***REMOVED******REMOVED******REMOVED*** 3. Is it tested?
Check for corresponding test file:
```bash
***REMOVED*** Verify tests exist
ls backend/tests/*post_fmit* backend/tests/*sunday_blocking*
```

***REMOVED******REMOVED******REMOVED*** 4. Is it documented?
Check roadmap status:
```bash
***REMOVED*** Search for task in roadmap
grep "PostFMITSundayBlockingConstraint" docs/planning/BLOCK_10_ROADMAP.md
```

---

***REMOVED******REMOVED*** Common Integration Gaps

| Gap Type | Symptom | Fix |
|----------|---------|-----|
| **Missing import** | `ImportError` or constraint not in list | Add to manager.py imports |
| **Missing registration** | Constraint exists but never runs | Add to `create_default()` |
| **Missing export** | Module doesn't expose class | Add to `__init__.py` |
| **Missing test** | No coverage for new code | Create test file |
| **Stale roadmap** | Task shows "Pending" when done | Update with ✅ and commit hash |

---

***REMOVED******REMOVED*** Session Closing Protocol

Before ending a session, complete this checklist:

***REMOVED******REMOVED******REMOVED*** 1. Update Status Documents
- [ ] Roadmap updated with what was completed
- [ ] Task statuses marked accurately (✅, ⚠️, ❌)
- [ ] Commit hashes added for traceability

***REMOVED******REMOVED******REMOVED*** 2. Document Remaining Work
- [ ] Remaining tasks clearly listed
- [ ] Dependencies identified
- [ ] Next agent knows what to do

***REMOVED******REMOVED******REMOVED*** 3. Verify Integration
- [ ] All new files synced to Docker (if applicable)
- [ ] Tests run and pass
- [ ] No orphaned code (implemented but not registered)

***REMOVED******REMOVED******REMOVED*** 4. Commit Summary
Include in final commit or session notes:
```markdown
***REMOVED******REMOVED*** Session Summary

***REMOVED******REMOVED******REMOVED*** Completed
- [x] Implemented PostFMITSundayBlockingConstraint (fmit.py:671-852)
- [x] Added tests (test_fmit_constraints.py)

***REMOVED******REMOVED******REMOVED*** Remaining
- [ ] Register in manager.py
- [ ] Update roadmap

***REMOVED******REMOVED******REMOVED*** Next Steps
1. Add import to manager.py
2. Register in create_default()
3. Re-run schedule generation
```

---

***REMOVED******REMOVED*** Example: Block 10 Constraint Registration

***REMOVED******REMOVED******REMOVED*** What Was Missing

```python
***REMOVED*** backend/app/scheduling/constraints/manager.py

***REMOVED*** MISSING - These imports were needed:
from .fmit import PostFMITSundayBlockingConstraint
from .call_equity import CallSpacingConstraint
from .inpatient import ResidentInpatientHeadcountConstraint

***REMOVED*** MISSING - These registrations in create_default():
manager.add(PostFMITSundayBlockingConstraint())  ***REMOVED*** Hard constraint
manager.add(ResidentInpatientHeadcountConstraint())  ***REMOVED*** Hard constraint
manager.add(CallSpacingConstraint())  ***REMOVED*** Soft constraint
```

***REMOVED******REMOVED******REMOVED*** What Should Have Been Documented

```markdown
***REMOVED******REMOVED*** Handoff: Block 10 Constraints

***REMOVED******REMOVED******REMOVED*** What Was Done
- [x] Designed PostFMITSundayBlockingConstraint
- [x] Designed CallSpacingConstraint
- [x] Designed ResidentInpatientHeadcountConstraint
- [x] Implemented in fmit.py, call_equity.py, inpatient.py

***REMOVED******REMOVED******REMOVED*** What Remains
- [ ] Import PostFMITSundayBlockingConstraint in manager.py (add to imports)
- [ ] Import CallSpacingConstraint in manager.py (add to imports)
- [ ] Import ResidentInpatientHeadcountConstraint in manager.py (add to imports)
- [ ] Register all three in create_default() method
- [ ] Write tests for inpatient constraints
- [ ] Update BLOCK_10_ROADMAP.md

***REMOVED******REMOVED******REMOVED*** Verification Command
pytest backend/tests/test_fmit_constraints.py backend/tests/test_call_equity_constraints.py -v
```

---

***REMOVED******REMOVED*** Verification Script

Save this as `scripts/verify_constraints.py`:

```python
***REMOVED***!/usr/bin/env python3
"""Verify all constraints are properly registered."""

from app.scheduling.constraints.manager import ConstraintManager

def verify_constraint_registration():
    """Check that all constraint files have their classes registered."""
    manager = ConstraintManager.create_default()
    constraint_names = [c.name for c in manager.constraints]

    ***REMOVED*** Expected constraints (update this list as needed)
    expected = [
        "Availability",
        "OnePersonPerBlock",
        "80HourRule",
        "1In7Rule",
        "SupervisionRatio",
        "ClinicCapacity",
        "MaxPhysiciansInClinic",
        "WednesdayAMInternOnly",
        "WednesdayPMSingleFaculty",
        "InvertedWednesday",
        "NightFloatPostCall",
        "Coverage",
        "Equity",
        "Continuity",
        "HubProtection",
        "UtilizationBuffer",
        "ZoneBoundary",
        "PreferenceTrail",
        "N1Vulnerability",
        ***REMOVED*** Block 10 additions
        "PostFMITSundayBlocking",
        "CallSpacing",
        "ResidentInpatientHeadcount",
    ]

    missing = set(expected) - set(constraint_names)
    if missing:
        print(f"❌ Missing constraints: {missing}")
        return False

    print(f"✅ All {len(expected)} constraints registered")
    return True

if __name__ == "__main__":
    verify_constraint_registration()
```

---

***REMOVED******REMOVED*** Quick Reference

| Agent | Primary Role | Handoff Responsibility |
|-------|-------------|------------------------|
| **Claude Web** | Design, architecture, documentation | Document what was designed, what remains |
| **Claude Code** | Implementation, testing, integration | Complete integration, verify registration |
| **Human** | Approval, strategic decisions | Review handoffs, approve PRs |

---

***REMOVED******REMOVED*** Related Documentation

- [Block 10 Roadmap](../planning/BLOCK_10_ROADMAP.md) - Current implementation status
- [Parallel Claude Best Practices](PARALLEL_CLAUDE_BEST_PRACTICES.md) - Multi-agent coordination
- [AI Rules of Engagement](AI_RULES_OF_ENGAGEMENT.md) - Git and PR workflow

---

*This checklist should be referenced by both Claude Web and Claude Code when:*
- *Designing new features (Claude Web)*
- *Implementing designs (Claude Code)*
- *Handing off between sessions*
- *Reviewing completed work*
