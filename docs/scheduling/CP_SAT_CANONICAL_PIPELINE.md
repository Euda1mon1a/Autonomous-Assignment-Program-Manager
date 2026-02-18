# CP-SAT Canonical Pipeline (JSON → XLSX)

**Purpose:** Define the current authoritative pipeline for schedule generation and export. This doc avoids names/PII and is intended for PRs and external review.

## Canonical Flow (Two-Phase with Optional Pause)

**Phase A — Generation (CP-SAT)**
1. **Preload** locked assignments (e.g., absences, protected activities, lecture/advising, manual entries).
2. **Global CP-SAT solve** produces resident rotations, **faculty half‑day activities**
   (C, AT, PCAT, DO, OFF), and overnight call records.
3. **Sync PCAT/DO from call** into half-day assignments (resident post‑call + any gaps).
4. **CP-SAT activity solver** fills **only unlocked** half‑day slots (primarily resident).

**Phase B — Export (JSON → XLSX)**
5. **HalfDayJSONExporter** reads `half_day_assignments` (descriptive truth).
6. **JSONToXlsxConverter** fills the official Block Template2 workbook.
7. **Excel output** is produced from the template (formatting preserved).

**Pauses are allowed** between Phase A and Phase B. Generation and export can be separate steps.

---

## How This Differs from Manual Scheduling (Resident‑First → Faculty Backfill)

**Manual approach (typical human workflow):**
1. Place residents into rotations.
2. Backfill faculty supervision and clinic coverage to meet demand.
3. Iterate when coverage or capacity breaks.

**Canonical CP‑SAT approach (system workflow):**
1. **Solve residents and faculty together** in a single CP‑SAT optimization.
   - Faculty availability, supervision ratios, and physical capacity are **hard constraints**.
   - Resident placement is **jointly optimized** with faculty coverage, not staged.
2. **Persist faculty half‑day assignments first** (they are already final outputs).
3. Use the activity solver **only for resident outpatient activities** (resident expansion).

**Why faculty isn’t “filled later” like residents:**
- CP‑SAT already outputs **faculty half‑day activities** directly (final‑form).
- Resident output is **block/rotation‑level** and requires a second step to map to
  outpatient half‑days (clinic/admin/AT), so only residents need the activity solver.

**Net effect:**
- The solver avoids the common human failure mode of “resident‑first placement that
  later can’t be staffed.”
- Faculty schedules are **authoritative** from CP‑SAT and are not overwritten unless
  explicitly overridden.

---

## Sources of Truth

- **Descriptive Truth:** `half_day_assignments`
- **Locked slots:** `source = preload | manual` (never overwritten by solver)
- **Solver slots:** `source = solver`

The activity solver **only fills unlocked slots**. It never overwrites preloads or manual edits.

**Production rule:** Only CP‑SAT is selectable in production API paths. Other solvers remain
available for development and research but are not exposed in prod dropdowns.

---

## JSON Schedule Shape (Canonical)

```json
{
  "block_start": "YYYY-MM-DD",
  "block_end": "YYYY-MM-DD",
  "source": "half_day_assignments",
  "residents": [
    {
      "name": "First Last",
      "pgy": 1,
      "rotation1": "ROT1",
      "rotation2": "ROT2",
      "days": [
        {"date": "YYYY-MM-DD", "weekday": "Mon", "am": "C", "pm": "C"}
      ]
    }
  ],
  "faculty": [
    {
      "name": "First Last",
      "pgy": null,
      "rotation1": "",
      "rotation2": "",
      "days": [
        {"date": "YYYY-MM-DD", "weekday": "Mon", "am": "AT", "pm": "ADMIN"}
      ]
    }
  ],
  "call": {
    "nights": [
      {"date": "YYYY-MM-DD", "staff": "Last"}
    ]
  }
}
```

---

## What’s Done (as of 2026-01-25)

- **Canonical JSON pipeline**: `half_day_assignments → JSON → XLSX`.
- **Merged-cell safe writing** in the XLSX converter (headers + schedule cells).
- **Faculty activities in global CP‑SAT solver** (C/AT/PCAT/DO/OFF).
- **Row mapping improvements**: supports `Last, First` and `First Last` mapping.
- **Export template binding**: Block Template2 template and structure XML are required for canonical export.

---

## What Remains

- **Preload rules completeness** (NF→Neuro split, TDY blocking, Hilo/Oki pre/post clinic, LEC/ADV on outpatient, etc.).
- **Outpatient rotation requirements**: activity requirement records for all specialty rotations (GUI-editable).
- **End-to-end runbook**: single “generate → pause → export” checklist/script.
- **Strict row mapping enforcement**: fail fast when a person is not mapped.
- **Frontend export flow**: ensure export route uses auth and canonical JSON path.

---

## What’s Uncertain / Needs Confirmation

- **Sports Medicine alignment rule**: confirm SM faculty/activity alignment behavior is correct.
- **AT coverage math**: confirm resident clinic demand → AT coverage mapping for local policy.
- **Template assumptions**: confirm template remains stable for long‑term airgapped deployments.

---

## Reference Entry Points

- **Generation (monolithic):** `backend/app/scheduling/engine.py` → `generate()` (CP‑SAT enforced)
- **Generation (graph):** `backend/app/scheduling/graph.py` → `generate_via_graph()` (LangGraph StateGraph, same output)
- **Graph nodes:** `backend/app/scheduling/graph_nodes.py` (12 nodes wrapping engine phases)
- **Graph state:** `backend/app/scheduling/graph_state.py` (TypedDicts for state + config)
- **Activity solver:** `backend/app/scheduling/activity_solver.py`
- **JSON export:** `backend/app/services/half_day_json_exporter.py`
- **JSON → XLSX:** `backend/app/services/json_to_xlsx_converter.py`
- **Canonical export service:** `backend/app/services/canonical_schedule_export_service.py`

---

## Non‑Canonical / Legacy

- **XML export** remains for validation/legacy tooling only.
- **Expansion service** is archived and no longer part of the pipeline.
