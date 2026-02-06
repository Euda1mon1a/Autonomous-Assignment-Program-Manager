# Antigravity Memory File
> **Purpose**: Persistent context for Antigravity (Gemini) across sessions
> **Last Updated**: 2026-01-01

## Key Domain Knowledge

### Acronyms & Terminology
| Term | Meaning | Notes |
|------|---------|-------|
| **FMIT** | Family Medicine Inpatient Team | Rotation (NOT faculty-mandated instructional time) |
| **PHI** | Protected Health Information | Never commit to repository |
| **PGY** | Post-Graduate Year | PGY1, PGY2, PGY3 = residency years |
| **AY** | Academic Year | July 1 - June 30 |

### Schedule Generation Order
1. **People** - Already in DB (18 residents, 10 faculty)
2. **Absences** - Load leave, vacation, TDY, conferences FIRST
3. **FMIT** - Pre-assign Family Medicine Inpatient Team rotation
4. **Solver** - Run constraint solver for remaining slots

### Block Structure
- **Block 0**: Orientation (July 1-2)
- **Blocks 1-13**: 28 days each (Thursday-Wednesday)
- Academic year: July 1 through June 30

### Data Sensitivity
- **Sanitized names for GitHub**: "PGY1 Resident 01", "Faculty 01", etc.
- **Real names LOCAL ONLY**: Never commit to repository (OPSEC/PERSEC)
- Real names are in the local database, not in git-tracked files

## Known Issues & Fixes

### 28-Day Bug (Session 046)
- **Root cause**: Frontend uses Monday start instead of Thursday
- **Fix**: Update `weekStartsOn: 1` to `weekStartsOn: 4` in:
  - `frontend/src/app/schedule/page.tsx`
  - `frontend/src/components/schedule/BlockNavigation.tsx`
- **Also needed**: Display block number (e.g., "Block 7 (Dec 18 - Jan 14)")

## Environment Notes
- Use `docker-compose.local.yml` (NOT default docker-compose.yml)
- Container prefix: `scheduler-local-*`
- Admin login: admin/admin123

## Session History
- **Session 046** (2026-01-01): Block 10 dates corrected, Blocks 10-13 generated, 28-day bug diagnosed
