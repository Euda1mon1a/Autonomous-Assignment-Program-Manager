# Session 077 - Bugs Found & Fixed

**Date:** 2026-01-09
**Context:** First ASTRONAUT mission revealed multiple issues

---

## Fixed This Session

### 1. Cross-Origin Cookie Issue (CRITICAL)
**Symptom:** Login succeeds but immediately redirects back to login
**Root Cause:** `SameSite=lax` cookies not sent cross-origin (port 3000 → 8000)
**Fix:** Added Next.js rewrites to proxy `/api/*` through frontend (same-origin)

**Files Changed:**
- `frontend/next.config.js` - Added rewrites for API proxy
- `docker-compose.local.yml` - Added `BACKEND_INTERNAL_URL=http://backend:8000`

### 2. Empty POST Body Through Proxy
**Symptom:** 422 Unprocessable Entity on login, `content-length: 0`
**Root Cause:** `URLSearchParams` object not serialized correctly through proxy
**Fix:** Call `.toString()` on formData before sending

**File Changed:**
- `frontend/src/lib/auth.ts:181` - `formData.toString()`

### 3. Null Date Crash in UpcomingAbsences
**Symptom:** `Cannot read properties of undefined (reading 'split')` on dashboard
**Root Cause:** Some absence records have null `start_date` or `end_date`
**Fix:** Added null guard before `parseISO()`

**File Changed:**
- `frontend/src/components/dashboard/UpcomingAbsences.tsx:84-85`

---

## Discovered But Not Fixed

### Seaborn Warning (Low Priority)
**Symptom:** `seaborn not available - enhanced visualization disabled` on every Python command
**Location:** Somewhere in backend analytics code
**Fix:** Remove optional import or add seaborn to requirements
**Tracked:** HUMAN_TODO.md

### Heatmap Empty Data (Expected)
**Symptom:** Heatmap page shows "No data available"
**Root Cause:** No schedule data in database
**Fix:** Generate schedule data (Block 10)
**Tracked:** HUMAN_TODO.md

---

## ASTRONAUT Mission Status

**Mission 001:** SCHEDULE_RECON_001
**Status:** COMPLETE (archived)
**Debrief:** `.claude/Missions/archive/DEBRIEF_20260109_063000.md`

**Mission 002:** PGY_INVESTIGATION_002
**Status:** BLOCKED - Login issue persists in browser
**Briefing:** `.claude/Missions/CURRENT.md`

---

## Session 078 - Ongoing Issue

### Login Works in Curl, Fails in Browser

**Symptom:** ASTRONAUT (and manual browser) can't log in despite fixes

**What We Know:**
1. Backend receives and processes login correctly (form data parsed)
2. Cookie is set correctly (`Set-Cookie` header forwarded through proxy)
3. Curl test works end-to-end (login + /auth/me with cookie)
4. Issue occurs on ALL browsers (Comet/Chromium, Safari/Webkit)
5. Container was rebuilt at 06:21 UTC with all fixes

**Current Hypothesis:**
- Cookie IS being set by browser
- But subsequent requests (GET /auth/me) may not be sending cookie
- OR auth.ts getCurrentUser() is failing silently

**Investigation Needed:**
- Browser Network tab showing login POST response
- Browser console errors
- Whether redirect happens after login attempt

---

## Technical Notes

### Why Proxy Instead of Fixing SameSite?
- `SameSite=none` requires `Secure=true` which requires HTTPS
- Local dev uses HTTP, so can't use `SameSite=none; Secure`
- Proxy makes requests same-origin, avoiding the issue entirely
- Production will use same-origin anyway (single domain)

### Chrome vs Comet Behavior
- Chrome stricter on cookie policies
- Comet (Arc?) more permissive
- Proxy fix works for both

---

## Files Modified

```
frontend/next.config.js          # API proxy rewrites
frontend/src/lib/auth.ts         # formData.toString()
frontend/src/components/dashboard/UpcomingAbsences.tsx  # null guard
docker-compose.local.yml         # BACKEND_INTERNAL_URL env
HUMAN_TODO.md                    # Documented seaborn/heatmap
```
