# Session 079 Handoff

**Branch:** `session/075-continued-work` | **Date:** 2026-01-08
**Base:** `main @ 1f44e533`

---

## COMPLETE THIS SESSION

### 1. WebSocket Live Updates
- `10e61c28` - Initial schedule page wiring
- `49dafbeb` - Full expansion to all routes + status indicator
- Broadcasts added to: absences.py, swap.py, assignments.py, block_scheduler.py
- WebSocketStatus component shows connection state

### 2. Bug Fixes (this commit)
- **WebSocket stuck reconnecting**: Disabled autoConnect (shows "Offline")
  - Root cause: Backend requires JWT token in query param, frontend doesn't expose it
  - TODO: Implement proper WebSocket auth with token refresh
- **Admin People button**: Wired up AddPersonModal
  - Added import, state, onClick handler, modal render

---

## FILES MODIFIED THIS SESSION

| File | Change |
|------|--------|
| `backend/app/api/routes/absences.py` | +4 WebSocket broadcasts |
| `backend/app/api/routes/swap.py` | +2 WebSocket broadcasts |
| `backend/app/api/routes/assignments.py` | +4 WebSocket broadcasts |
| `backend/app/api/routes/block_scheduler.py` | +4 WebSocket broadcasts |
| `frontend/src/components/ui/WebSocketStatus.tsx` | NEW - connection indicator |
| `frontend/src/app/schedule/page.tsx` | WebSocket hook + status indicator |
| `frontend/src/app/admin/people/page.tsx` | Fixed Add Person button |

---

## KNOWN ISSUES / TECH DEBT

### WebSocket Auth (FUTURE)
- Backend `/api/v1/ws` requires JWT token as query param
- Frontend uses httpOnly cookies, doesn't expose access_token to JS
- Options:
  1. Add non-httpOnly token for WebSocket
  2. Backend: accept cookie-based auth for WS upgrade
  3. Token refresh endpoint that returns token to JS
- For now: autoConnect=false, shows "Offline"

---

## TEST CREDENTIALS
- Username: `admin`
- Password: `admin123`

---

## STACK STATUS
- Containers: 8/8 healthy
- DB Backup: `~/backups/scheduler_db_pre_websocket.sql.gz`

---

## CRITICAL TODO (Human Required)

**PERSEC: Remove PII from git history**
- Files deleted from HEAD but still in main branch history
- Affected: BLOCK_10_SUMMARY.md, AIRTABLE_EXPORT_SUMMARY.md, etc.
- Requires: `git filter-repo` + force push to main
- Tracked in: `docs/TODO_INVENTORY.md` (Critical section)
