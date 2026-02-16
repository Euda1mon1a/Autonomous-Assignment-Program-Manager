# Block 10 Schedule Generation: 99.9% Success Plan

**Date:** 2026-01-23  
**Purpose:** Provide a concrete, gated plan to raise Block 10 generation success to 99.9%  
**Scope:** Block 10 (2026-03-12 to 2026-04-08)

---

## Success Contract (All Must Hold)

1. **Preflight gate passes** (`scripts/preflight-block10.sh`) with no warnings.
2. **Generation completes** without exceptions or retries.
3. **No NULL activities** in `weekly_patterns` or `half_day_assignments`.
4. **56 slots per person** for all residents and non-adjunct faculty.
5. **ACGME validation passes** with zero violations.
6. **Activity solver succeeds** (no silent failure) or explicit, documented override.
7. **Export parity**: XML/Excel reflects `half_day_assignments` exactly.

---

## Hard Gates and Acceptance Criteria

### Preflight (Hard Fail)
- Containers running: `residency-scheduler-db`, `residency-scheduler-backend`
- API health returns `status=healthy` and `database=connected`
- Required activities exist (LEC-PM, LEC, ADV, C, C-I, CALL, PCAT, DO, FMIT, NF, IM, PedW, aSM, W, LV, OFF, HOL)
- Required placeholder templates exist (W-AM/W-PM/LV-AM/LV-PM/OFF-AM/OFF-PM/HOL-AM/HOL-PM/LEC-PM/LEC/ADV/C)
- Block 10 assignments count equals resident count
- `weekly_patterns.activity_id` NULL count = 0
- Backup created before generation

### Runtime (Hard Fail)
- Any `"Activity not found"` warning becomes an exception
- Any `IntegrityError` during preload is surfaced and aborts the run
- Activity solver returns `success=true` (no silent warnings)
- Full run wrapped in a single transaction or run-id cleanup on failure

### Post-Generation (Hard Fail)
- `half_day_assignments` count equals `(resident_count + faculty_non_adjunct_count) * 56`
- `half_day_assignments.activity_id` NULL count = 0
- PCAT/DO integrity check passes
- ACGME validation passes with zero violations
- Export parity check passes (XML derived from half_day_assignments)

---

## Implementation Roadmap (Practical Path to 99.9%)

### Phase 0: Gate Everything (Immediate)
- Adopt `scripts/preflight-block10.sh` as required entry gate
- Add runbook step to fail fast on any missing activity/template

### Phase 1: Data Integrity (Must Do)
- Enforce `weekly_patterns.activity_id` NOT NULL via migration
- Enforce `block_assignments.rotation_template_id` NOT NULL or fail fast
- Seed required activities and templates via migrations or deterministic seed

### Phase 2: Runtime Safety (Must Do)
- Convert activity lookup failures to hard errors
- Replace silent `IntegrityError` handling with explicit failure + rollback
- Wrap full generation in a single transaction, or enforce run-id cleanup on failure

### Phase 3: Solver Reliability (Should Do)
- Treat activity solver failure as blocking
- Increase solver timeout where needed; log all fallbacks as errors
- Add retry-once policy for solver timeouts

### Phase 4: Export Parity (Must Do)
- Remove duplicated pattern logic from export
- Export from `half_day_assignments` only
- Add parity check: compare XML/Excel output to DB assignments

### Phase 5: Test Coverage (Should Do)
- Add tests for EC-1, EC-3, EC-4, EC-12, EC-14
- Add a Block 10 integration test that runs full pipeline in a scratch DB

---

## Operational Runbook (Block 10)

1. **Preflight gate**  
   ```bash
   ./scripts/preflight-block10.sh
   ```

2. **Backup**  
   ```bash
   ./scripts/backup-db.sh --docker
   ```

3. **Generate**  
   Use the standard schedule generation endpoint with:
   - `block_number=10`, `academic_year=2025`
   - `expand_block_assignments=true`
   - `timeout_seconds >= 120`

4. **Validate**  
   - NULL activity check
   - ACGME validation
   - PCAT/DO integrity check

5. **Export + parity**  
   - Export XML from `half_day_assignments`
   - Compare to DB counts and spot-check output

---

## Residual Risks (After Completion)

- Unexpected data mutations outside schedule generation (manual edits)
- Unmodeled absence types (DEP/TDY) without activities
- Container drift (out-of-date schema vs seed data)

---

## References

- [BLOCK10_GENERATION_GAPS.md](BLOCK10_GENERATION_GAPS.md)
- [BLOCK10_EDGE_CASES.md](BLOCK10_EDGE_CASES.md)
- [SCHEDULE_GENERATION_RUNBOOK.md](../guides/SCHEDULE_GENERATION_RUNBOOK.md)
