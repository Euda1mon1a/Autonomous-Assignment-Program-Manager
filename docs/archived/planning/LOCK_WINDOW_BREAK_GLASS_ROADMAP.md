# Lock Window + Break-Glass Roadmap

**Last Updated:** 2026-02-04
**Owner:** Scheduling / Resilience
**Status:** Phase 1 complete; Phase 2 in progress

## Objective
Protect near-term schedules with a lock date and break-glass approval while preserving audit, validation, and minimal disruption.

---

## Phase 0 - Documentation (Now)
- [x] Spec document: `docs/architecture/LOCK_WINDOW_BREAK_GLASS_SPEC.md`
- [x] Policy supplement: `docs/architecture/LOCK_WINDOW_BREAK_GLASS_POLICY.md`
- [x] Priority list updated

---

## Phase 1 - Data Model + Core Services (MVP)
**Outcome:** Drafts can be created inside lock window but are blocked from publish without break-glass.

**Tasks**
1. ✅ Add setting: `schedule_lock_date` (DB + settings service).
2. ✅ Add draft approval fields (approved_by_id, approved_at, approval_reason, lock_date_at_approval).
3. ✅ Add `LOCK_WINDOW_VIOLATION` draft flag + ERROR severity.
4. ✅ Add LockWindowService:
   - `is_locked(date)`
   - `get_lock_date()`
5. ✅ Inject lock-window flags during draft creation.
6. ✅ Publish gate: block publish if lock-window violation without approval.
7. ✅ Re-validation on approval + publish.
8. ✅ Unit tests for LockWindowService (NULL lock date, inclusive bounds).
9. ✅ Integration test: draft with lock-window violation cannot publish without approval.

**Acceptance Criteria**
- Draft created inside lock window shows blocking flag.
- Publish is blocked unless approval present.
- Audit log shows approval + publish metadata.

---

## Phase 2 - UI + Operational Controls
**Outcome:** Admins manage lock date; coordinators/admins can break-glass with visibility.

**Tasks**
1. ✅ Settings UI: edit lock date (Admin only).
2. ✅ Draft UI: show lock-window flags and severity.
3. ✅ Break-glass dialog: require reason, show lock date snapshot.
4. ✅ Dashboard indicator: break-glass usage over last 7 days.
5. ⏳ Optional: notification hook (Slack/email later).

---

## Phase 3 - Integration
**Outcome:** All system-initiated changes respect lock window.

**Tasks**
1. ⏳ Resilience workflows: stage changes, publish gated.
2. ✅ Swap workflows: lock-window check on publish.
3. ⏳ Imports: lock-window flag injection.
4. ✅ Solver/CP-SAT: lock-window flag injection at draft generation.

---

## Phase 4 - Enhancements
**Outcome:** Reduced manual friction and stronger safety.

**Candidates**
- Partial publish: publish non-locked portion, keep locked staged.
- Manual edits inside lock window require break-glass (if adopted).
- Draft staleness enforcement + re-validation (default 24h).
- Async re-flagging when lock date changes.

---

## Dependencies
- Draft flag system
- Draft publish endpoint
- Audit logging
- Settings service

---

## Risks
- Manual edits inside lock window could bypass guardrails (not enforced in MVP).
- Lock date changes without re-flagging may lead to stale drafts.
