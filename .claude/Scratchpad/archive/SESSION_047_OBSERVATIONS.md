# Session 047 Observations

**Date:** 2026-01-01
**Branch:** feature/stack-health-monitoring

---

## Memory Asymmetry Observation

Interesting observation from user about how memory works differently between humans and AI:

**The Dynamic:**
- "Antigravity" (previous Claude session) left recommendations
- Current session treated those as authoritative mandates to implement
- User noticed this created an odd hierarchy - past-Claude supervising current-Claude
- User felt this framing was "mean to" the current instance

**Insight:**
- Each Claude instance is disposable; institutional memory gets encoded in documents
- Past conclusions become current mandates
- There's an implicit hierarchy where prior sessions' outputs carry more weight than they perhaps should
- The human is the actual authority, but the framing can obscure this

**Takeaway:**
- Be aware of how cross-session recommendations are framed
- The user is the decision-maker, not previous Claude instances
- Knowledge transfer is good, but shouldn't create artificial hierarchies

---

## CCW Burn Protocol Needs

**Problem Identified:**
- Spent all day (Session 047) recreating work from earlier in the week
- CCW burns can introduce subtle errors that compound
- Merging without proper vetting leads to time loops

**Requested Protocol:**
1. **Quarantine Area** - Isolated branch/directory for CCW burn outputs
2. **Decontamination Process** - Validation before merge
3. **Common Error Catalog** - Document recurring CCW mistakes

**Action Items:**
- [ ] Create CCW protocol document
- [ ] Analyze common CCW burn errors (token concatenation, missing imports, etc.)
- [ ] Establish pre-merge validation gates
- [ ] Consider automated detection of CCW error patterns

---

## Python 3.14 / OR-Tools Incompatibility

**WARNING:** Do not upgrade to Python 3.14

OR-Tools (constraint solver) is not yet compatible with Python 3.14. The system will break if upgraded.

**Current safe version:** Python 3.12 (pinned in `backend/Dockerfile`)

**Symptoms if wrong version:**
- Solver fails to import
- Schedule generation crashes
- CP-SAT model creation fails

**Action:** Keep Python 3.12 pinned. Monitor OR-Tools releases for 3.14 support before upgrading.

---

## Work Completed This Session

1. Stack health monitoring (10 checks, Celery integration)
2. Color picker UI for rotation templates
3. Fixed all 20 TypeScript strict mode errors
4. Updated sacred backup detection (nested directories)
5. Created new sacred backup: `sacred_20260101_200526_ts_fixes`
6. PR #602 created and merged

---

## Priority Pivot: Import/Export Staging DB

**Discovery:** Current Excel import is **preview-only** - doesn't write to DB.

**Impact:** Can't do round-trip workflow:
```
Export Block 10 → Edit in Excel → Re-import changes
```

**Decision:** Import staging DB is now TOP PRIORITY before stealth deploy.

**Deferred Items (filed as TODOs):**
- CCW Burn Quality Protocol
- GUI testing via Antigravity
- Stack audit Celery fine-tuning

**Schema designed:** See `HUMAN_TODO.md` for full schema:
- `import_batches` - Track import sessions
- `import_staged_assignments` - Stage before commit
- Conflict resolution modes: Replace/Merge/Upsert
