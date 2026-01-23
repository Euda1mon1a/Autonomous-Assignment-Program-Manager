# Session 102 EOD Handoff

**Date:** 2026-01-14
**Branch:** `feat/session-091`
**PR:** #709

---

## What Happened Today

1. **DB nuked this morning** - seed data corrupted
2. **XML validation pipeline built** - but validated against bad data
3. **Docker hot reload fixed** - `entrypoint: []` in docker-compose.local.yml
4. **Discovered data mismatches** - DB codes don't match ROSETTA (e.g., `KAP-LD` vs `KAP`)

---

## Current Git State

### 3 Conflicting Files (in both local AND PR #709)
```
.gitignore
backend/app/scheduling/engine.py
backend/app/utils/rosetta_parser.py
```

### 10 Local-Only Files (safe to add)
```
docker-compose.local.yml          # entrypoint fix - KEEP
backend/app/services/schedule_xml_exporter.py      # ROT_HANDLERS aliases - REVIEW
backend/app/services/xml_to_xlsx_converter.py      # changes - REVIEW
backend/app/services/faculty_assignment_expansion_service.py  # big changes - REVIEW
scripts/verify_schedule.py        # new script
docs/planning/BLOCK_10_ROADMAP.md # updates
.claude/* files                   # local
.antigravity/README.md            # local
```

### New Files (untracked, not in PR)
```
backend/app/utils/rosetta_xml_validator.py   # NEW - XML comparison tool
docs/scheduling/Block10_ROSETTA_CORRECT.xml  # NEW - ground truth XML
```

---

## Technical Debt

### P0 - Must Fix Before Merge
1. **Resolve 3 git conflicts** with PR #709
2. **Validate against pristine xlsx** (user to provide)
3. **Review ROT_HANDLERS aliases** - added for bad DB data, may be wrong

### P1 - Should Fix Soon
1. **DB seed data quality** - rotation codes should match ROSETTA patterns
2. **Secondary rotations missing** - Wilhelm has no `rotation2` in Block 10 assignment
3. **Name format inconsistency** - DB has "Katie" vs ROSETTA "Katherine"

### P2 - Nice to Have
1. **Backup hooks** - verify they trigger before destructive ops
2. **XML validation in export pipeline** - currently logs warnings, could block

---

## Morning Workflow

```bash
# 1. Stash everything local
git stash push -m "session-102-local-changes"

# 2. Pull latest from PR
git fetch origin
git checkout feat/session-091
git pull origin feat/session-091

# 3. Pop stash and resolve conflicts
git stash pop
# Resolve: .gitignore, engine.py, rosetta_parser.py

# 4. Wait for pristine xlsx from user

# 5. Validate exports against pristine data

# 6. Commit clean changes, push to PR
```

---

## Files to Keep vs Discard

| File | Action | Reason |
|------|--------|--------|
| `docker-compose.local.yml` | KEEP | Hot reload fix works |
| `rosetta_xml_validator.py` | KEEP | Tooling, no DB dependency |
| `Block10_ROSETTA_CORRECT.xml` | KEEP | Ground truth |
| `rosetta_parser.py` changes | MERGE | Extends PR version |
| `schedule_xml_exporter.py` | REVIEW | ROT_HANDLERS may be wrong |
| `xml_to_xlsx_converter.py` | REVIEW | Needs validation |
| `faculty_assignment_expansion_service.py` | REVIEW | Big changes |

---

## Key Learnings

1. **Don't validate against nuked DB** - wait for pristine source
2. **Central Dogma pattern is sound** - xlsx → XML → validate → xlsx
3. **Code format mismatches** - DB uses `KAP-LD`, ROSETTA uses `KAP`
4. **Docker entrypoint issue** - production ENTRYPOINT breaks local CMD override
