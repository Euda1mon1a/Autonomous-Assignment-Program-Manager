# Lock Window + Break-Glass Policy (Resilience)

**Last Updated:** 2026-02-04
**Purpose:** Operational policy for lock-window enforcement and break-glass usage.

---

## Policy Summary
- Lock window applies to **system-initiated** changes.
- Locked window: `date <= schedule_lock_date`.
- System-initiated changes can be staged but **cannot be published** without break-glass.
- Manual changes are allowed for Coordinator/Admin with audit.
- If `schedule_lock_date` is NULL, no lock window is applied.

---

## Source vs Lock Window Matrix

| Source | Inside Lock Window | Outside Lock Window | Notes |
|--------|--------------------|---------------------|-------|
| CP-SAT / Solver | Stage allowed, publish blocked | Publish allowed | Break-glass required for publish inside lock window. |
| Resilience Engine | Stage allowed, publish blocked | Publish allowed | Resilience must stage/advise before approval. |
| Import (Excel/ETL) | Stage allowed, publish blocked | Publish allowed | Same lock policy applies. |
| Swap (user-initiated) | Publish blocked | Publish allowed | Swaps touching locked dates require break-glass. |
| Manual edit (GUI) | Allowed (audit required) | Allowed | Current decision; see Open Risks. |

---

## Break-Glass Requirements
- Coordinator or Admin approval.
- Required reason (text).
- Re-validation (ACGME, coverage, conflicts).
- Audit log entry with lock date snapshot.

---

## Operational Guidelines
1. Prefer staging drafts to visualize impact before approval.
2. Use break-glass only for urgent coverage or patient-safety reasons.
3. Review break-glass usage weekly in dashboard metrics.

---

## Open Risks (Known)
- Manual edits inside lock window are currently allowed and can bypass break-glass.
- Lock date changes can create stale drafts without re-flagging.

---

## Reference
- Spec: `docs/architecture/LOCK_WINDOW_BREAK_GLASS_SPEC.md`
- Roadmap: `docs/archived/planning/LOCK_WINDOW_BREAK_GLASS_ROADMAP.md`
