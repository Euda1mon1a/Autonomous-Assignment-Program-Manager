# Code Review: crazy-murdock worktree (Notifications + Swap Wiring)

> **Reviewed:** 2026-03-12 | **Branch:** `.claude/worktrees/crazy-murdock` | **Reviewer:** Claude Opus 4.6
> **Scope:** 15 files, +1,086 / -67 lines — notification routes, swap route expansion, approval chain, role filtering, platform wiring roadmap

---

## Critical (3) — merge blockers

### 1. Authorization bypass in `approval_chain.py`

Missing parentheses on dependency factories. The auth check is never executed.

```python
# BUG (line 160, 364):
dependencies=[Depends(require_coordinator_or_above)]   # factory returned, never called
dependencies=[Depends(require_admin)]

# FIX:
dependencies=[Depends(require_coordinator_or_above())]
dependencies=[Depends(require_admin())]
```

Rest of codebase consistently uses `()` form (see `mcp_proxy.py`, `export.py`, `absences.py`). As written, any authenticated user can create approval records and daily seals.

### 2. `User` model has no `person_id` attribute

`notifications.py` (lines 39, 45, 84, 99, 132) and `swap.py` (line 106) access `current_user.person_id`. The `User` model has no such column or property. Every notification route and `request_swap` will raise `AttributeError` at runtime.

**Fix:** Either add `person_id` FK to User model (requires migration), or resolve via relationship/lookup.

### 3. Duplicate notification rows

`InAppChannel.deliver()` (`channels_core.py:175-187`) creates and commits a `Notification` row. Then `NotificationService.send_notification()` (`service.py:268-279`) creates a second row for the same event. Every in-app notification is inserted twice.

**Fix:** Remove the insert from one of the two locations.

---

## Important (9)

### 4. XSS in email HTML — `channels_core.py:291-330`

`EmailChannel._format_html` uses raw f-string interpolation of `payload.subject`, `payload.body`, and `payload.priority` without `html.escape()`. If notification data originates from user input (swap reason text), HTML/JS injection is possible.

### 5. Unused import — `swap.py:54`

`get_current_user` imported but never used. Only `get_current_active_user` is used. Will fail ruff lint.

### 6. `asyncio.run()` in Celery task — `tasks.py:358`

`process_scheduled_notifications` uses `asyncio.run()` inside a Celery task. Fragile if an event loop already exists (test harnesses, certain worker pools). Consider synchronous service method or `loop.run_until_complete()`.

### 7. Webhook returns `success=True` when unconfigured — `channels_core.py:380-391`

When `self.webhook_url` is `None`, delivery is skipped but `DeliveryResult(success=True)` is returned. Should return `success=False` with "No webhook URL configured".

### 8. Fat routes violate layered architecture — `swap.py`

CLAUDE.md specifies "Routes thin, logic in services." Swap route handlers are 50-100+ lines each with:
- Direct DB queries and commits
- Notification dispatch logic
- Approval chain recording
- WebSocket broadcasting
- Lock window checking

The notification + approval + broadcast pattern is copy-pasted across 5 endpoints. Should be extracted to a service.

### 9. No authorization on swap history/detail — `swap.py:583, 679`

Docstring says "faculty can only view swaps involving themselves" but `get_swap_history` and `get_swap` have no role-based filtering. Any authenticated user can view any swap record.

### 10. Mixed SQLAlchemy styles — `notifications.py`

Mixes SA 2.0 (`select(Notification).where(...)` on lines 44, 51) with legacy 1.x (`db.query(Notification).filter(...)` on lines 81, 104). Should be consistent per project conventions.

### 11. Raw DB queries in route layer — `approval_chain.py:250-261`

`list_approval_records` builds raw SA queries (imports `desc` inside function body) instead of delegating to `ApprovalChainService`. Service methods exist for filtered paths but the default path bypasses them.

### 12. No route-level tests

New features without corresponding tests:
- Notification routes (list, get, mark-read, mark-all-read)
- Swap request/approve/execute endpoints
- Notification + approval chain integration in swap flow

Existing `test_channels.py` and `test_approval_chain_service.py` only cover lower layers.

---

## Suggestions (6)

### 13. UUIDs used as display names — `swap.py`

Notification data uses `str(request.source_faculty_id)` for `source_name`. Notifications will render: "Requester: 7b3d4e5f-...". Should look up person's display name.

### 14. camelCase query param aliases — `approval_chain.py:54, 120, 223-226`

Query params use `alias="chainId"`, `alias="targetEntityType"`. CLAUDE.md: "URL query params MUST use snake_case" — axios interceptor doesn't convert URL params.

### 15. Dead comment placement — `channels_core.py:399-400`

`# Channel registry` comment trapped inside except block after a `return`. Should be at module level.

### 16. `render_notification` return type imprecise — `notification_types.py:362`

Returns `dict[str, str | list[str]] | None` but callers treat it as `dict[str, Any]`. Not blocking but could be tighter.

### 17. Indentation oddity — `service.py:219, 232, 238, 267`

Several blocks dedented to wrong nesting level. Syntactically valid but confusing. Likely formatting artifact.

### 18. `PLATFORM_WIRING_ROADMAP.md` — no issues

Well-structured planning doc. Parallelization matrix is useful. `ROADMAP.md` reference is correct.

---

## Summary

| Severity | Count |
|----------|-------|
| Critical | 3 |
| Important | 9 |
| Suggestion | 6 |

**Priority order:** Fix #1 (auth bypass) → #2 (person_id crash) → #3 (duplicate rows) → #4 (XSS) → #8 (fat routes, refactor) → rest.
