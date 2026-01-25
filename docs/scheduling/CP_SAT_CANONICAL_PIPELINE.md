# CP-SAT Canonical Pipeline (JSON → XLSX)

**Purpose:** Define the current authoritative pipeline for schedule generation and export. This doc avoids names/PII and is intended for PRs and external review.

## Canonical Flow (Two-Phase with Optional Pause)

**Phase A — Generation (CP-SAT)**
1. **Preload** locked assignments (e.g., absences, protected activities, lecture/advising, manual entries).
2. **CP-SAT block/call generation** produces core assignments and call records.
3. **Sync PCAT/DO from call** into half-day assignments.
4. **CP-SAT activity solver** fills **only unlocked** half-day slots.

**Phase B — Export (JSON → XLSX)**
5. **HalfDayJSONExporter** reads `half_day_assignments` (descriptive truth).
6. **JSONToXlsxConverter** fills the official Block Template2 workbook.
7. **Excel output** is produced from the template (formatting preserved).

**Pauses are allowed** between Phase A and Phase B. Generation and export can be separate steps.

---

## Sources of Truth

- **Descriptive Truth:** `half_day_assignments`
- **Locked slots:** `source = preload | manual` (never overwritten by solver)
- **Solver slots:** `source = solver`

The activity solver **only fills unlocked slots**. It never overwrites preloads or manual edits.

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
- **Faculty activities in CP-SAT activity solver** (AT coverage + admin activities).
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

- **Generation:** `backend/app/scheduling/engine.py` (CP‑SAT enforced)
- **Activity solver:** `backend/app/scheduling/activity_solver.py`
- **JSON export:** `backend/app/services/half_day_json_exporter.py`
- **JSON → XLSX:** `backend/app/services/json_to_xlsx_converter.py`
- **Canonical export service:** `backend/app/services/canonical_schedule_export_service.py`

---

## Non‑Canonical / Legacy

- **XML export** remains for validation/legacy tooling only.
- **Expansion service** is archived and no longer part of the pipeline.
