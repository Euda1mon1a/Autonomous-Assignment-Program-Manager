# ML Integration Status

> **Created:** 2026-02-20
> **Last Updated:** 2026-02-20
> **Authority:** Comprehensive status of ML pipeline integration, branch triage, and Block 12 readiness
> **Linked from:** [MASTER_PRIORITY_LIST.md](MASTER_PRIORITY_LIST.md) (LOW #17)

---

## 1. Branch Triage Results

### Fully Superseded (deleted)

| Branch | Commits Ahead | Verdict | Reason |
|--------|---------------|---------|--------|
| `feat/ml-scorer-graph-node-and-import-fixes` | 12 | **DELETED** | All content merged to main via PR #1181. Branch forked before #1181 merge base; all block12 import scripts, ml_score node, test scaffold, graph_state fields are identical on main. Branch was behind main on PRs #1182-1185. |
| `docs/ml-scorer-pipeline-docs` | 5 | **DELETED** | Doc-only updates superseded by main. MLP entries older than current main (missing PR #1182-1185 session log entries, #22 resolution). ENGINE_ASSIGNMENT_FLOW, SCHEDULE_GENERATION_RUNBOOK, ADR langchain — all had older content than main. |

### Kept (active work)

| Branch | Commits Ahead | Verdict | Reason |
|--------|---------------|---------|--------|
| `feat/schedule-vision-research` | 1 | **KEEP** | Active ML research scripts (CatBoost, TabPFN, distillation). Not related to Block 12. Stale on graph files — needs rebase before merge. |
| `feature/empty-table-features` | 4 | **MERGED** | Merged as PR #1182. Seeds Game Theory, Resilience, Swaps, Wellness, Notification tables. |

### Verification

Content verified identical between branch and main for all critical files:
- `scripts/data/block12_import/` (10 files) — identical
- `scripts/templates/block_import_template.py` — identical
- `backend/tests/test_scheduling_graph.py` — identical
- `docs/scheduling/BLOCK12_SCHEDULE_LOAD.md` — identical
- `backend/app/scheduling/graph_state.py` — identical

---

## 2. Database Reality (Laptop PG17)

### Schema State

| Table Category | Count | Notes |
|----------------|-------|-------|
| Tables total | 116 | Mature schema |
| Faculty | 10 | |
| PGY-1 residents | 6 | |
| PGY-2 residents | 6 | |
| PGY-3 residents | 5 | |
| Rotation templates (active) | 79 | Types: absence, education, inpatient, off, outpatient, recovery |

### Block 12 Data State

| Resource | Count | Status |
|----------|-------|--------|
| Blocks | 112 | May 8, 2025 – Jun 3, 2026 |
| Assignments | 1,186 | Populated |
| Block assignments | **0** | EMPTY — critical gap |
| HDAs (Block 12 date range) | 884 | 648 solver, 0 manual, 0 predicted, **277 null activity** |

### Schedule Run History

| Metric | Value |
|--------|-------|
| Total runs | 368 |
| Successful | 32 (8.7%) |
| Partial | 34 (9.2%) |
| Failed | 301 (81.8%) |
| Last success | Jan 30, 2026 (Block 10, 444 assigned, 59s) |
| Feb 12 batch | ALL FAILED (0 assigned, ~1.3s, empty config_json) |

**Key finding:** The solver CAN succeed (32 successes, best was 1,048 assigned in 53s for a full-year hybrid run). The Feb 12 batch all failed instantly with empty `config_json`, suggesting invocation without proper parameters — not a solver bug.

### Critical Gaps

1. **block_assignments = 0 for Block 12** — `dry_run.py` rebuilds this
2. **277 HDAs with null activity_id** — Need `load_predictions.py` or manual fill
3. **No successful Block 12 run** — Last success was Block 10
4. **81.8% failure rate** — Root cause: parameter/data issues, not solver defects

---

## 3. ML Pipeline Status

### LangGraph Pipeline (13 nodes) — COMPLETE

PR #1181 merged the full pipeline. Node 12 (`ml_score`) runs post-validation when `ML_ENABLED=true`.

```
init → load_data → check_residents ─?→ build_context → pre_validate
  ─?→ solve ─?→ persist_and_call ─?→ activity_solver → backfill
  → persist_draft_or_live → validate → ml_score → finalize → END
```

**Files:**
- `backend/app/scheduling/graph.py` — Graph definition + `generate_via_graph()`
- `backend/app/scheduling/graph_nodes.py` — 13 node functions
- `backend/app/scheduling/graph_state.py` — `ScheduleGraphState` + `ScheduleGraphConfig`

### ML Scorer (ScheduleScorer) — INTEGRATED, UNFITTED

- **Ensemble:** PreferencePredictor, ConflictPredictor, WorkloadOptimizer
- **Graceful degradation:** Returns empty scores when models unfitted (NotFittedError caught)
- **Temporal fields:** Conflict payload includes temporal context
- **Status:** Models need training data to become useful

### Schedule-ML-Bridge — NOT IN REPO

No `schedule-ml-bridge` directory exists in the AAPM repository. The plan referenced it as standalone — needs to be created or imported when training data is available.

### Experimental ML Approaches

| Approach | Location | Status |
|----------|----------|--------|
| `schedule-vision` | `feat/schedule-vision-research` branch | 1 commit, 8 files (CatBoost + TabPFN + distillation) |
| `schedule-vision-neural` | Not yet created | Planned |
| Additional experimental | TBD | Planned |

---

## 4. Block 12 Generation Readiness

### Can Block 12 be generated without handjamming?

**PARTIALLY.** The CP-SAT solver pipeline is complete (13/13 nodes), and all import scripts are on main. But data gaps must be filled first.

### Prerequisites (in order)

1. **Run `checkpoint.sh`** — DB backup before changes
2. **Run `dry_run.py`** — Rebuild block_assignments + template-derived HDAs for Block 12
3. **Run `fix_memorial_day.py`** — Flag May 26 as holiday
4. **Attempt solver generation** — `POST /api/schedule/generate` with Block 12 params
5. **If gaps remain:** Run `load_predictions.py` to backfill ML predictions
6. **Export to Excel** → Coordinator reviews/handjams remaining slots → `import_block12.py` imports
7. **Capture training data** (see below)

### Import Scripts Available (all on main)

| Script | Purpose | Lines |
|--------|---------|-------|
| `import_block12.py` | Excel handjam importer with NAME_MAP + CODE_MAP | ~508 |
| `dry_run.py` | Pre-flight validator + baseline generator | ~362 |
| `load_predictions.py` | ML prediction backfill | ~205 |
| `expand_block12_hdas.py` | HDA expansion | ~159 |
| `fix_block12_assignments.py` | Assignment rebuild | ~151 |
| `fix_memorial_day.py` | Holiday flagging | ~87 |
| `check_block13_staleness.py` | Next-block validation | ~160 |
| `audit_deployed_faculty.py` | Remove deployed faculty | ~124 |
| `checkpoint.sh` | DB backup/restore helper | ~24 |

---

## 5. Training Data Capture Plan

When manual handjam is needed (likely for the 277 null-activity slots):

1. **Solver assignments** are tagged `source='solver'` in the database
2. **Manual overrides** imported via `import_block12.py` are tagged `source='manual'`
3. The `source` column IS the training signal: manual overrides of solver suggestions = learning signal
4. **Export:** Full Block 12 HDAs (solver + manual) as JSON for ML model training
5. **Target:** Train PreferencePredictor and ConflictPredictor on real coordinator decisions

### Data Flow

```
Solver generates → Export to Excel → Coordinator handjams → import_block12.py
                                                              ↓
                                                    source='manual' tag
                                                              ↓
                                              Training data for ML models
```

---

## 6. MCP Tools for Block 12

### Available Tools (49 registered)

| Tool | Purpose |
|------|---------|
| `generate_schedule_tool` | CP-SAT/greedy/PuLP schedule generation |
| `validate_schedule_tool` | ACGME compliance check |
| `create_backup_tool` | DB safety (MANDATORY before writes) |
| `restore_backup_tool` | DB rollback |
| `generate_block_quality_report_tool` | Quality metrics |
| `export_schedule_tool` | Excel/CSV export |

### Skills (47 total)

| Skill | Purpose |
|-------|---------|
| `safe-schedule-generation` | Backup-first workflow (MANDATORY) |
| `schedule-validator` | Post-gen ACGME check |
| `tamc-excel-scheduling` | Excel patterns (NAME_MAP, CODE_MAP) |
| `schedule-verification` | Integrity audit |

---

## 7. Next Actions

| Priority | Action | Effort |
|----------|--------|--------|
| **NOW** | Delete superseded branches | 5 min |
| **NEXT** | Rebase `feat/schedule-vision-research` onto main | 30 min |
| **NEXT** | Run `dry_run.py` in read-only mode to validate data | 15 min |
| **BLOCKED** | Full Block 12 generation | Needs dry_run + data validation first |
| **FUTURE** | Train ML models on Block 12 coordinator decisions | After Block 12 handjam cycle |
| **FUTURE** | Create schedule-ml-bridge repo/module | After training data available |
