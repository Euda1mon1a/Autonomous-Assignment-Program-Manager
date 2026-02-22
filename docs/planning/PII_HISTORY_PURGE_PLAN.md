# PII History Purge — Operational Plan

**Date:** 2026-02-21
**Status:** PLANNING — requires terminal execution with operator
**MPL Reference:** CRITICAL #1 — Purge PII from Git History
**Risk Level:** HIGH — destructive, irreversible, requires coordinated force-push

---

## 1. Problem Statement

Real resident/faculty names with PGY levels, rotation assignments, deployment dates, and leave schedules are embedded in git history. Removing files from HEAD (PR #1189) stops future exposure but does not eliminate historical blobs. Anyone with repo access can recover PII via `git log -S "Name"`.

### Contamination Scope

| Metric | Value |
|--------|-------|
| Files on HEAD with PII | ~29 |
| Historical file paths with PII | ~48 |
| Earliest PII commit | `30ffe8f7` (2025-12-21) |
| Commits after first PII | 1,998 of 2,415 (83%) |
| Repo size (.git/) | 493 MB |

### PII Categories Found

| Category | Example | Files |
|----------|---------|-------|
| Resident full names | First Last with PGY level | import scripts, dry runs, test fixtures |
| Faculty full names | First Last with role | constraints, expansion services, scratchpads |
| Rotation assignments | Name → specific rotation | block12 import, scheduling docs |
| Deployment dates | Name + date range | audit_deployed_faculty.py |
| Leave/absence records | Name + vacation dates | dry_run_report.md, Airtable exports |
| Name mapping dicts | Excel name → DB name | check_block13_staleness.py, import scripts |

### Files on HEAD Containing PII (29)

**Session/Archive (9):**
- `.claude/Scratchpad/archive/SESSION_075_CONTEXT.md`
- `.claude/Scratchpad/archive/session-095-seed-data.md`
- `.claude/Scratchpad/archive/session-096-block-export-test.md`
- `.claude/Scratchpad/archive/session-098-block10-v2.md`
- `.claude/Scratchpad/archive/session-099-faculty-expansion.md`
- `.claude/Scratchpad/archive/session-101-backup-analysis.md`
- `.claude/Scratchpad/archive/session-102-eod-handoff.md`
- `.claude/Scratchpad/archive/session-108-stealth-launch.md`
- `.claude/Scratchpad/archive/session-111-db-xlsx-analysis.md`

**Skills/Config (2):**
- `.claude/archive/Missions/archive/DEBRIEF_20260109_063000.md`
- `.claude/skills/tamc-excel-scheduling/BLOCK_SCHEDULE_RULES.md`

**Backend (5):**
- `backend/alembic/versions/20260114_faculty_constraints.py`
- `backend/alembic/versions/20260114_half_day_tables.py`
- `backend/app/services/preload_service.py`
- `backend/generate_test_data.py`
- `backend/scripts/validate_xlsx_vs_rosetta.py`

**Tests (1):**
- `backend/tests/scheduling/conftest.py`

**Docs (6):**
- `docs/TAMC_SCHEDULING_CONTEXT.md`
- `docs/architecture/BLOCK10_CONSOLIDATED_REFERENCE.md`
- `docs/archived/reports/LOCAL_FILE_CLEANUP_REPORT.md`
- `docs/scheduling/CSV_BRIDGE_SPEC.md`
- `docs/scheduling/README.md`
- `docs/scheduling/ROSETTA_PATTERNS.md`
- `docs/scratchpad/block10-pre-regeneration-snapshot.md`
- `docs/scratchpad/session-143-faculty-clinic-cv-backfill.md`

**Scripts (4):**
- `scripts/csv_to_vba_format.py`
- `scripts/dev/generate_test_data.py`
- `scripts/ops/learned_rules.py`
- `scripts/seed_people.py`

---

## 2. Tool Selection

### `git-filter-repo` (RECOMMENDED)

```bash
brew install git-filter-repo
```

**Why not BFG?**
- BFG only does file deletion or string replacement in blobs, not path-based content rewriting
- BFG is unmaintained (last release 2015)
- `git-filter-repo` is the git project's official recommendation
- Supports `--replace-text` for name→pseudonym substitution
- Supports `--paths-from-file` for targeted blob removal
- Handles all edge cases (merge commits, tags, reflog)

---

## 3. Strategy: Two-Phase Purge

### Phase 1: HEAD Cleanup (pre-rewrite)

Before rewriting history, clean up HEAD so the final state is PII-free. This avoids the rewriter having to handle current-HEAD blobs differently.

**Actions:**
1. Create a replacements mapping file (`/tmp/pii-replacements.txt`)
2. Apply replacements to all 29 HEAD files
3. Commit as `fix(security): anonymize all PII in tracked files`
4. Verify: `git grep -l "Colgan\|Sawyer\|..."` returns nothing

**Replacement format** (one per line):
```
literal:Tessa Sawyer==>Resident R01
literal:Clara Wilhelm==>Resident R02
literal:Colin Travis==>Resident R03
...
literal:Bridget Colgan==>Faculty F01
```

**Decision needed:** Use generic pseudonyms (Resident R01) or realistic fake names? Generic is safer but less readable in docs. Realistic fakes risk confusion with real people.

### Phase 2: History Rewrite

```bash
# MUST be run from a fresh clone (git-filter-repo requires it)
cd /tmp
git clone /path/to/repo aapm-rewrite
cd aapm-rewrite

# Apply text replacements across ALL history
git filter-repo --replace-text /tmp/pii-replacements.txt
```

This rewrites every blob in every commit that contains any of the literal strings. Commit hashes change from the first affected commit forward (~1,998 commits).

**What `--replace-text` does:**
- Scans every blob (file content) in every commit
- Replaces matching strings with their substitution
- Creates new blob → new tree → new commit
- Preserves commit metadata (author, date, message)
- Rewrites all refs (branches, tags)

---

## 4. Coordination Requirements

### Remotes to Update

| Remote | URL | Action |
|--------|-----|--------|
| `origin` | GitHub (Euda1mon1a/AAPM) | Force-push all branches + tags |
| `mini` | Mac Mini (ssh://100.69.127.98/...) | Force-push OR re-clone |

### Pre-Operation Checklist

- [ ] Close/merge all open PRs (force-push invalidates PR diffs)
- [ ] Create full backup: `git bundle create /tmp/aapm-pre-purge.bundle --all`
- [ ] Notify any collaborators (GitHub access list)
- [ ] Verify Mac Mini is reachable: `git ls-remote mini --heads`
- [ ] Ensure no active Codex automations running
- [ ] Pause nightly automations (01:00-02:00 HST)
- [ ] Note current HEAD: `git rev-parse HEAD` (for post-verification)

### Post-Operation Checklist

- [ ] Force-push to origin: `git push origin --force --all && git push origin --force --tags`
- [ ] Force-push to mini: `git push mini --force --all`
- [ ] Verify: `git -S "Colgan" log --all` returns nothing
- [ ] GitHub: Settings → Actions → Clear caches (if any)
- [ ] GitHub: Contact support to clear server-side caches of old commits (optional but recommended)
- [ ] Re-clone on all machines that have the repo
- [ ] Run full test suite on fresh clone
- [ ] Verify Codex automations work with new history
- [ ] Update any saved commit SHAs in docs/config

---

## 5. Execution Script

**This is a TERMINAL operation. Run interactively, not via Claude Code.**

```bash
#!/bin/bash
set -euo pipefail

# ═══════════════════════════════════════════════════════════════
# PII HISTORY PURGE — Run from terminal, NOT Claude Code
# ═══════════════════════════════════════════════════════════════

REPO_DIR="$HOME/Autonomous-Assignment-Program-Manager"
WORK_DIR="/tmp/aapm-pii-purge"
REPLACEMENTS="/tmp/pii-replacements.txt"
BUNDLE="/tmp/aapm-pre-purge-$(date +%Y%m%dT%H%M%S).bundle"

echo "══════════════════════════════════════════"
echo "  PII HISTORY PURGE"
echo "══════════════════════════════════════════"

# ── Step 0: Verify git-filter-repo is installed ──
if ! command -v git-filter-repo &>/dev/null; then
    echo "ERROR: git-filter-repo not installed"
    echo "  brew install git-filter-repo"
    exit 1
fi

# ── Step 1: Create full backup bundle ──
echo ""
echo "[1/7] Creating backup bundle..."
cd "$REPO_DIR"
git bundle create "$BUNDLE" --all
echo "  Backup: $BUNDLE ($(du -h "$BUNDLE" | cut -f1))"

# ── Step 2: Verify replacements file exists ──
echo ""
echo "[2/7] Checking replacements file..."
if [ ! -f "$REPLACEMENTS" ]; then
    echo "ERROR: $REPLACEMENTS not found"
    echo "  Create it first with name==>pseudonym mappings"
    exit 1
fi
echo "  $(wc -l < "$REPLACEMENTS") replacement rules"

# ── Step 3: Fresh clone for rewriting ──
echo ""
echo "[3/7] Creating fresh clone for rewriting..."
rm -rf "$WORK_DIR"
git clone --mirror "$REPO_DIR" "$WORK_DIR"
cd "$WORK_DIR"

# ── Step 4: Run git-filter-repo ──
echo ""
echo "[4/7] Running git-filter-repo --replace-text..."
echo "  This rewrites ~2000 commits. May take 2-5 minutes."
git filter-repo --replace-text "$REPLACEMENTS" --force

# ── Step 5: Verify no PII remains ──
echo ""
echo "[5/7] Verifying PII removal..."
# Check a sample of known PII names
LEAKED=0
for name in "Colgan" "Sawyer" "Monsivais" "Cataquiz" "Gigon" "Headid"; do
    COUNT=$(git log --all -S "$name" --oneline 2>/dev/null | wc -l)
    if [ "$COUNT" -gt 0 ]; then
        echo "  STILL FOUND: $name ($COUNT commits)"
        LEAKED=1
    fi
done
if [ "$LEAKED" -eq 0 ]; then
    echo "  ✓ All checked names removed from history"
else
    echo "  ✗ PII still present — DO NOT PUSH. Investigate."
    exit 1
fi

# ── Step 6: Push to origin ──
echo ""
echo "[6/7] Ready to force-push to origin."
echo "  WARNING: This rewrites ALL commit hashes."
echo "  WARNING: All open PRs will be invalidated."
read -p "  Force-push to origin? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git push origin --force --all
    git push origin --force --tags
    echo "  ✓ Origin updated"
else
    echo "  Skipped origin push"
fi

# ── Step 7: Push to mini ──
echo ""
echo "[7/7] Ready to force-push to mini."
read -p "  Force-push to mini? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git remote add mini ssh://100.69.127.98/Users/aaronmontgomerymini/repos/personal/aapm.git 2>/dev/null || true
    git push mini --force --all
    echo "  ✓ Mini updated"
else
    echo "  Skipped mini push"
fi

echo ""
echo "══════════════════════════════════════════"
echo "  PURGE COMPLETE"
echo "══════════════════════════════════════════"
echo ""
echo "Post-operation steps:"
echo "  1. cd $REPO_DIR && git fetch origin"
echo "  2. git reset --hard origin/main"
echo "  3. Verify: git log --all -S 'Colgan' (should be empty)"
echo "  4. Re-clone on any other machines"
echo "  5. Resume Codex automations"
echo ""
echo "Backup bundle: $BUNDLE"
echo "Rewrite dir: $WORK_DIR (safe to delete after verification)"
```

---

## 6. Replacements File Template

Create `/tmp/pii-replacements.txt` before running the script. Format: `literal:REAL==>FAKE`

```
# ── Residents ──
literal:Tessa Sawyer==>Resident-R01
literal:Clara Wilhelm==>Resident-R02
literal:Colin Travis==>Resident-R03
literal:Katie Byrnes==>Resident-R04
literal:Meleigh Sloss==>Resident-R05
literal:Josh Monsivais==>Resident-R06
literal:Felipe Cataquiz==>Resident-R07
literal:Scott Cook==>Resident-R08
literal:Alaine Gigon==>Resident-R09
literal:James Headid==>Resident-R10
literal:Nick Maher==>Resident-R11
literal:Devin Thomas==>Resident-R12
literal:Christian Hernandez==>Resident-R13
literal:Cam Mayell==>Resident-R14
literal:Clay Petrie==>Resident-R15
literal:Jae You==>Resident-R16
literal:Laura Connolly==>Resident-R17
literal:Brian Dahl==>Resident-R18
literal:Chelsea Tagawa==>Resident-R19

# ── Faculty ──
literal:Bridget Colgan==>Faculty-F01

# ── Last-name-only references (catch partial matches) ──
# ORDER MATTERS: longer strings first to avoid partial replacement
literal:Monsivais==>R06-Last
literal:Cataquiz==>R07-Last
literal:Hernandez==>R13-Last
literal:Connolly==>R17-Last
literal:Wilhelm==>R02-Last
literal:Sawyer==>R01-Last
literal:Mayell==>R14-Last
literal:Petrie==>R15-Last
literal:Headid==>R10-Last
literal:Colgan==>F01-Last
literal:Byrnes==>R04-Last
literal:Gigon==>R09-Last
literal:Sloss==>R05-Last
literal:Maher==>R11-Last
literal:Tagawa==>R19-Last
literal:Dahl==>R18-Last

# ── "Last, First" format (Excel imports) ──
literal:Sawyer, Tessa==>R01-Last, R01-First
literal:Wilhelm, Clara==>R02-Last, R02-First
literal:Travis, Colin==>R03-Last, R03-First
literal:Byrnes, Katie==>R04-Last, R04-First
literal:Sloss, Meleigh==>R05-Last, R05-First
literal:Monsivais, Josh==>R06-Last, R06-First
literal:Cataquiz, Felipe==>R07-Last, R07-First
literal:Cook, Scott==>R08-Last, R08-First
literal:Gigon, Alaine==>R09-Last, R09-First
literal:Headid, James==>R10-Last, R10-First
literal:Maher, Nick==>R11-Last, R11-First
literal:Thomas, Devin==>R12-Last, R12-First
literal:Hernandez, Christian==>R13-Last, R13-First
literal:Mayell, Cam==>R14-Last, R14-First
literal:Petrie, Clay==>R15-Last, R15-First
literal:You, Jae==>R16-Last, R16-First
literal:Colgan, Bridget==>F01-Last, F01-First
```

**IMPORTANT:** This template is incomplete. Before execution:
1. Run `git log --all -S "NAME" --oneline` for each name to verify coverage
2. Check `git grep -i "NAME"` on HEAD for variant spellings
3. Add any names found in the DB seed data or test fixtures
4. The "Last, First" entries MUST come before "First Last" entries (longer match first)

---

## 7. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Backup bundle corrupted | Low | Critical | Verify with `git bundle verify` before proceeding |
| Incomplete name list | Medium | High | Run comprehensive grep after rewrite to verify |
| Mini remote not reachable | Medium | Low | Push to mini later when online |
| Codex automations break | Medium | Medium | Pause automations, re-clone worktrees |
| Open PRs invalidated | Certain | Low | Merge/close all PRs first |
| Commit SHAs in docs stale | Certain | Low | Accept — docs reference content, not hashes |
| `git-filter-repo` fails mid-run | Low | None | Working on mirror clone, original untouched |

---

## 8. Timeline Estimate

| Step | Duration |
|------|----------|
| Create replacements file | 30 min (manual review) |
| HEAD cleanup commit | 15 min |
| Backup bundle | 2 min |
| git-filter-repo run | 2-5 min |
| Verification | 10 min |
| Force-push origin | 2 min |
| Force-push mini | 2 min (if reachable) |
| Re-clone local | 5 min |
| Post-verification | 10 min |
| **Total** | **~75 min** |

---

## 9. Decision Points for Operator

1. **Pseudonym style:** Generic (Resident-R01) vs realistic fake names?
2. **Migration files:** `20260114_faculty_constraints.py` has names in comments. Rewriting migration files changes their hashes — acceptable?
3. **Test fixtures:** `conftest.py` may use real names as test data. Replace with synthetic?
4. **Timing:** Best done during a quiet period (no active PRs, no Codex runs)
5. **GitHub cache purge:** Contact GitHub support to clear dangling commits? (Optional but thorough)

---

*This operation is irreversible after force-push. The bundle backup is your only rollback path.*
