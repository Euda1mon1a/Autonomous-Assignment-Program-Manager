# Session 2026-01-11/12: Frontend Consolidation

## Status: POST-MERGE FIXES APPLIED

---

## PRs Merged
| PR | Description | Status |
|----|-------------|--------|
| #695 | RiskBar design system component | ✅ MERGED |
| #696 | Swaps Hub + P2 fix | ✅ MERGED |
| #697 | Personal Schedule + People + Call + Import + Activities + Compliance + P1 fix | ✅ MERGED |

---

## Post-Merge Fixes (Commit 30e42e2a)

### 1. Route Conflict
- **Issue:** `/(hub)/people/page.tsx` and `/people/page.tsx` both resolved to `/people`
- **Fix:** Deleted `/people/page.tsx`

### 2. Database Schema
- **Issue:** PR #690 MEDCOM day-type migration blocked; API returned "column day_type does not exist"
- **Fix:** Added columns directly to blocks table:
  - `day_type` (enum)
  - `operational_intent` (enum)
  - `actual_date` (date)

### 3. Navigation Update
- **Issue:** Nav still pointed to old routes
- **Fix:** Updated Navigation.tsx:
  - `/call-roster` → `/call-hub`
  - `/import-export` → `/hub/import-export`
  - Simplified admin nav to: Game Theory, Lab, Users, Health, Settings, Legacy

### 4. Legacy Admin Page
- Created `/admin/legacy/page.tsx` with links to all old admin routes
- Backward compatibility during transition

### 5. API Base URL
- **Issue:** Frontend called `localhost:8000` directly (CORS cookie issue)
- **Fix:** Changed to `/api/v1` (uses Next.js proxy)

---

## Known Issue: Schedule Page Sparse Data
- DB has 732 assignments for March 2026
- UI shows ~20
- API ignoring `pageSize=500`, returning only 100 items
- **Not fixed yet** - backend pagination issue

---

## Resume Instructions
1. Fix backend assignments API pagination (ignores pageSize param)
2. Run `/check-codex` on any new PRs
3. Test consolidated routes: /swaps, /people, /call-hub, /hub/import-export

---

## Dev Server
- Running on http://localhost:3001
- Backend: http://localhost:8000 (via Docker)
