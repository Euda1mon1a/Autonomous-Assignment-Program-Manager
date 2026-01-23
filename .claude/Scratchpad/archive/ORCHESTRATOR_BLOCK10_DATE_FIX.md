# ORCHESTRATOR Briefing: Block 10 Date Correction

> **Created:** 2026-01-01T13:39
> **Priority:** P1 (Blocking Block 10 generation)
> **Delegated To:** META_UPDATER or Claude Code

---

## Problem Statement

Block 10 dates are **incorrectly documented** in 36+ locations:
- **Wrong:** March 12 - April 8, 2026
- **Correct:** **March 12 - April 8, 2026** (Thu-Wed, 28 days)

### Root Cause

`generate_blocks.py` comments and examples were written before Block 0 (orientation July 1-2) was accounted for. The algorithm calculates correctly but the hardcoded example dates in docstrings are wrong.

### Source of Truth

[`docs/architecture/ACADEMIC_YEAR_BLOCKS.md`](file:///Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/docs/architecture/ACADEMIC_YEAR_BLOCKS.md) line 46:
```
| **10** | Thu, Mar 12, 2026 | Wed, Apr 8, 2026 | 28 | Standard |
```

---

## Files to Fix

### High Priority (Script defaults/examples)

| File | Line | Fix |
|------|------|-----|
| `scripts/generate_blocks.py` | 9-10 | Change `2026-03-12` → `2026-03-12`, `2026-04-08` → `2026-04-08` |
| `scripts/verify_schedule.py` | 9, 496 | Change defaults and examples |

### Medium Priority (Documentation)

| File | Action |
|------|--------|
| `scripts/README.md` | Fix 2 occurrences |
| `docs/guides/SCHEDULE_GENERATION_RUNBOOK.md` | Fix ~15 occurrences |
| `docs/planning/BLOCK_10_ROADMAP.md` | Fix ~3 occurrences |
| `docs/development/BLOCK10_CONSTRAINTS_TECHNICAL.md` | Fix header date |
| `docs/development/SCHEDULE_VERIFICATION_TEMPLATE.md` | Fix SQL examples |
| `docs/development/AGENT_SKILLS.md` | Fix 1 occurrence |
| `docs/reports/README.md` | Fix 1 occurrence |
| `docs/ADDING_A_SKILL.md` | Fix 1 occurrence |

### Low Priority (Test assertions)

| File | Action |
|------|--------|
| `backend/tests/scripts/test_generate_blocks.py` | Update assertion docstring line 53 |

---

## Execution Pattern

```bash
# Simple sed replacement (run from repo root)
find . -type f \( -name "*.py" -o -name "*.md" \) \
  -exec sed -i '' 's/2026-03-12/2026-03-12/g' {} \;
find . -type f \( -name "*.py" -o -name "*.md" \) \
  -exec sed -i '' 's/2026-04-08/2026-04-08/g' {} \;
find . -type f \( -name "*.py" -o -name "*.md" \) \
  -exec sed -i '' 's/March 12 - April 8/March 12 - April 8/g' {} \;
```

---

## Verification

After fix:
```bash
# Should return 0 results
grep -r "2026-03-12" --include="*.py" --include="*.md" . | grep -v ".git"
grep -r "2026-04-08" --include="*.py" --include="*.md" . | grep -v ".git"
```

---

## After Date Fix: Generate Block 10

Once dates are corrected, run:
```bash
docker compose -f docker-compose.local.yml exec backend \
  python scripts/scheduling/generate_schedule.py --block 10 --dry-run --verbose
```

---

*Briefing prepared by ORCHESTRATOR (Antigravity)*
