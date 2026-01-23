# Session 2026-01-11: ACGME 1-in-7 PAUSE Logic Enshrinement

## Summary

Protected the ACGME 1-in-7 rule implementation from incorrect AI "fixes".

## Context

**Codex P2 Feedback:** Claimed absence should reset consecutive_days counter.
**Physician Decision:** WRONG. Current PAUSE behavior is correct.

## ACGME 1-in-7 Rule Interpretation (Approved)

| Event Type | Counter Action |
|------------|----------------|
| **Scheduled day off** (weekend, forced 1-in-7) | RESET to 0 |
| **Absence** (leave, TDY, etc.) | HOLD (no change) |

### Rationale
1. Leave is SEPARATE from ACGME-required rest days
2. Schedule must be compliant INDEPENDENT of leave status
3. Absence ≠ "day off" for 1-in-7 purposes
4. Prevents gaming: can't work 6→leave→work 6→leave→work 6...
5. Ensures 1-in-7 distribution throughout block

## Files Modified

### 1. `backend/app/services/block_assignment_expansion_service.py`

**Docstring added** (lines 173-194):
- ACGME 1-in-7 RULE IMPLEMENTATION header
- PAUSE behavior explanation
- 5 reasons why PAUSE is correct
- Physician approval stamp
- CODEX P2 REJECTED note

**Comment block added** (lines 237-247):
```
╔══════════════════════════════════════════════════════════════════╗
║  ACGME 1-in-7 RULE - PAUSE BEHAVIOR (DO NOT MODIFY)              ║
║  Absence: Counter HOLDS (doesn't reset) - this is INTENTIONAL    ║
║  CODEX P2 REJECTED: "Reset on absence" is WRONG.                 ║
╚══════════════════════════════════════════════════════════════════╝
```

### 2. `backend/tests/services/test_block_assignment_expansion_service.py` (NEW)

Created test class `TestOneInSevenPauseBehavior`:
- `test_absence_does_not_reset_consecutive_days`
- `test_scheduled_day_off_resets_consecutive_days`
- `test_cannot_game_system_with_absences`

All tests documented with physician approval stamp.

## PR #686 Status

- CI: Multiple failures (backend ~19min - likely dependency issue)
- Codex P1: Weekly pattern activity/offs - dismissed (inpatient templates not solved)
- Codex P2: 1-in-7 reset on absence - **REJECTED** (enshrined PAUSE instead)

## State of Scheduler

See `.claude/plans/virtual-snacking-summit.md` for full audit:
- Block 10: PRODUCTION READY (1,008 assignments, 100% ACGME)
- 4 working solvers (greedy, cp_sat, pulp, hybrid)
- Research lab preserved (~13,600 lines bio-inspired/quantum)

## Next Steps

1. Wait for PR #686 CI (check backend dependency issue)
2. `/admin/templates` 404 - real issue, add to backlog
3. Consider running tests locally to verify PAUSE protection
