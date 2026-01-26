# CP-SAT Pipeline Roadmap (Generation → Export)

**Date:** 2026-01-26  
**Scope:** End-to-end CP-SAT canonical pipeline from data preload through JSON → XLSX export.

This roadmap starts at the beginning (inputs + preloads) and walks forward to export, with concrete checkpoints, remaining work, and verification steps. It is aligned with `docs/scheduling/CP_SAT_CANONICAL_PIPELINE.md` and reflects the current state after PRs #766, #768, #769.

---

## 0) Preconditions (Environment + Data)

**Goal:** Ensure the pipeline has consistent, validated inputs before solving.

**Done**
- CP-SAT canonical pipeline merged (#766).
- Call extraction includes weekend blocks (fix merged).
- Block Template2 header block number now computed by date (fix merged).

**Remaining**
- Data integrity pass for all preloads and rotations (especially outpatient rotations).
- Confirm the academic year start date used by `get_block_number_for_date` aligns with real program dates.

**Verification**
- `SchedulingContext` builds valid indices (residents, faculty, blocks, templates).
- `Block` date range matches the target block and academic year.

**References**
- `backend/app/scheduling/engine.py`
- `backend/app/scheduling/constraints.py`
- `backend/app/utils/academic_blocks.py`

---

## 1) Phase A — Preloads (Locked Assignments)

**Goal:** Load immutable/predefined slots before any solver runs.

**Done**
- Preload framework integrated into scheduling engine.
- Rotation-protected preloads now cover LEC/ADV, Wednesday LEC, intern continuity, night-float/off-site patterns.
- Hilo/Okinawa TDY pre/post clinic pattern implemented (OKI matches Hilo).
- Tests added for protected preload patterns (Wednesday, Hilo/OKI, NF split).

**Remaining (completeness)**
- Any remaining program-specific preloads not yet encoded.

**Acceptance criteria**
- All locked slots are in `half_day_assignments` with `source = preload|manual`.
- Activity solver never overwrites locked slots.

**References**
- `backend/app/services/preload_service.py`
- `backend/app/scheduling/activity_solver.py`
- `docs/scheduling/CP_SAT_CANONICAL_PIPELINE.md`

---

## 2) Phase A — CP-SAT Block + Call Generation

**Goal:** Use CP-SAT to create core assignments and overnight call coverage.

**Done**
- CP-SAT canonical solver path enforced.
- Weekend call extraction preserved in result map.
- Call coverage constraints for Sun–Thu nights active.
- Block 10 regen now produces solver assignments + call (617 assignments, 20 calls).

**Remaining**
- Confirm Sports Medicine alignment rule is correct for local policy.
- Confirm AT coverage math (resident clinic demand → AT coverage).
- Ensure supervision constraint activates (AT/PCAT availability currently logs as missing).
- Verify NF/PC templates exist where Night Float post-call rules are expected.

**Acceptance criteria**
- Call assignments exist for all Sun–Thu nights (no gaps).
- Call assignments appear in `call_assignments` and propagate to post-call rules.
- Block 10 regen produces solver assignments (no preload-only output).
- All solver outputs are consistent with `ConstraintManager` hard constraints.

**References**
- `backend/app/scheduling/solvers.py`
- `backend/app/scheduling/constraints/overnight_call.py`
- `backend/app/scheduling/constraints/call_coverage.py`
- `backend/app/scheduling/constraints/call_equity.py`
- `docs/reports/block10-cpsat-run-20260126.md`

---

## 3) Phase A — Post-call + PCAT/DO Sync

**Goal:** Translate call results into half-day activity slots and post-call rules.

**Done**
- PCAT/DO sync from call implemented in canonical pipeline.

**Remaining**
- Validate post-call coverage logic against program policy for all rotations.

**Acceptance criteria**
- Half-day schedule reflects post-call time off and PCAT/DO per call.
- No conflicts with preloaded protected slots.

**References**
- `backend/app/scheduling/constraints/post_call.py`
- `backend/app/services/half_day_schedule_service.py`

---

## 4) Phase A — Activity Solver (Fill Unlocked Half-Days)

**Goal:** Fill only the unlocked half-day slots based on requirements.

**Done**
- Activity solver honors locks and focuses on open slots.
- Faculty AT/admin activities supported.
- Activity solver completes for Block 10 with capacity overflow safeguards.

**Remaining**
- Complete activity requirement records for all outpatient rotations (GUI-editable).
- Verify rotation-specific activity caps and specialty matching.
- Resolve physical-capacity overflow (capacity constraints are currently skipped
  when minimum demand exceeds max).

**Acceptance criteria**
- No locked slots overwritten.
- Required activities satisfied within block.
- Physical capacity constraints either enforced or explicitly waived with policy.

**References**
- `backend/app/scheduling/activity_solver.py`
- `backend/app/services/rotation_template_service.py`

---

## 5) Phase B — Canonical JSON Export

**Goal:** Export canonical JSON from `half_day_assignments`.

**Done**
- `HalfDayJSONExporter` reads `half_day_assignments` as descriptive truth.
- Faculty included in JSON export.
- Strict row mapping enforced (missing person mapping fails fast).

**Remaining**
- Consolidate any remaining legacy XML-only behaviors.

**Acceptance criteria**
- JSON export schema matches canonical format.
- Missing person mapping causes explicit error (not silent skip).

**References**
- `backend/app/services/half_day_json_exporter.py`
- `backend/app/services/canonical_schedule_export_service.py`

---

## 6) Phase B — JSON → XLSX (Template2)

**Goal:** Render Block Template2 from canonical JSON.

**Done**
- JSON→XLSX conversion implemented.
- Merged-cell safe writing.
- Block number computed from date (no hardcode).
- Strict row mapping enforcement for XLSX.

**Remaining**
- Add user feedback on export failure (backend and frontend).

**Acceptance criteria**
- XLSX output includes all mapped people and call row.
- Missing person mapping fails loudly.

**References**
- `backend/app/services/json_to_xlsx_converter.py`
- `backend/app/services/xml_to_xlsx_converter.py` (legacy)

---

## 7) Frontend Export Flow

**Goal:** Ensure UI export uses canonical JSON path with auth.

**Done**
- Backend canonical export endpoint available.

**Remaining**
- Replace raw `fetch` with axios in `frontend/src/lib/export.ts` (ensure JWT sent).
- Add error toast/feedback for export failure.

**Acceptance criteria**
- Export works under auth without manual tokens.
- UI shows error on export failure.

**References**
- `frontend/src/lib/export.ts`
- `docs/MASTER_PRIORITY_LIST.md`

---

## 8) QA + Validation

**Goal:** Confirm pipeline correctness end-to-end.

**Done**
- CP-SAT regression tests added.
- Weekend call extraction test added.

**Remaining**
- End-to-end “generate → pause → export” runbook.
- Add export verification tests (row mapping, call row, faculty rows).
- Re-run Block 10 after template fixes to validate JSON/XLSX counts.

**Acceptance criteria**
- One command or runbook produces validated XLSX from CP-SAT output.

**References**
- `docs/operations/BLOCK_REGEN_RUNBOOK.md`
- `docs/scheduling/CP_SAT_CANONICAL_PIPELINE.md`
- `backend/tests/services/test_canonical_schedule_export.py`

---

## 9) Final Export Readiness Checklist

**Must be true before “lock-in”**
- Preload rules complete and verified.
- Activity requirements complete for outpatient rotations.
- Frontend export uses authenticated canonical endpoint.
- Strict row mapping enabled (no silent skips). ✅
- End-to-end runbook tested with real-ish block data.

---

## Suggested Execution Order (Next Tasks)

1) **Finish preloads** (NF split, TDY, Hilo/Oki, LEC/ADV outpatient).
2) **Fill activity requirements** for outpatient rotations (GUI-editable).
3) **Lock down exports**: strict row mapping + frontend auth + user-facing errors.
4) **Runbook + E2E validation**: single “generate → export” checklist.

---

## Related Docs

- `docs/scheduling/CP_SAT_CANONICAL_PIPELINE.md`
- `docs/MASTER_PRIORITY_LIST.md`
- `docs/operations/BLOCK_REGEN_RUNBOOK.md`
- `docs/architecture/import-export-system.md`
