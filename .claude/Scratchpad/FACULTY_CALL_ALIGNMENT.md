# Faculty Call & Call Roster Alignment

**Branch:** `session/067-antigravity-faculty-call` | **Date:** 2026-01-07

## Status: WORKING ✅

`/call-roster` now displays faculty call assignments correctly.

## Restore This State

```bash
git checkout session/067-antigravity-faculty-call
docker-compose -f docker-compose.local.yml up -d --build
```

## All Fixes Applied This Session

### Backend Schema Fixes
| File | Fix |
|------|-----|
| `backend/app/schemas/block.py` | `block_number` limit 13 → 14 (DB has block 14 for June) |
| `backend/app/schemas/absence.py` | `deployment_orders: bool` → `bool \| None` |
| `backend/app/schemas/rotation_template.py` | Added `academic`, `clinical`, `leave` to valid types |
| `backend/app/schemas/call_assignment.py` | `call_date` aliased to `date` |

### Backend Controller Fixes (model_validate)
| File | Methods Fixed |
|------|---------------|
| `assignment_controller.py` | `list_assignments` |
| `block_controller.py` | `list_blocks`, `get_blocks_by_date_range` |
| `person_controller.py` | `list_people`, `list_residents`, `list_faculty` |
| `call_assignment_controller.py` | `get_call_assignments_by_person`, `get_call_assignments_by_date` |
| `credential_controller.py` | 3 methods |
| `procedure_controller.py` | `list_procedures` |
| `certification_controller.py` | 2 methods |

### Frontend Fixes
| File | Fix |
|------|-----|
| `frontend/src/features/call-roster/hooks.ts` | **REWROTE** - Now uses `/call-assignments` endpoint instead of `/assignments?activity_type=on_call`. Also fixed `page_size: 1000` → `500` (backend max) |
| `frontend/src/app/admin/faculty-call/page.tsx` | Null safety in transform |

### Other
| File | Fix |
|------|-----|
| `backend/scripts/seed_antigravity.py` | Fixed `.append()` bug on int counter |

## Key Debugging Patterns Learned

### "Objects are not valid as a React child" with `{type, loc, msg, input, ctx}`
**Cause:** Pydantic validation error object being rendered instead of data
**Debug:** Check backend logs for `ValidationError` or test endpoint with curl
**Fixes:**
1. Controller missing `model_validate()` on ORM objects
2. Schema field type too strict (e.g., `bool` when DB has `NULL` → use `bool | None`)
3. Schema constraint too strict (e.g., `le=13` when DB has 14)

### 422 Unprocessable Entity
**Cause:** Request validation failure
**Debug:** Check response body for `detail` with `loc` field showing which param failed
**Example:** `page_size=1000` when backend only allows `le=500`

## Data (call_assignments table)

| Type | Count | Jan 2026 |
|------|-------|----------|
| sunday | 52 | 4 |
| weekday | 206 | 17 |
| holiday | 4 | 1 |
| backup | 103 | 9 |
| **Total** | **365** | **31** |

## URLs

- `/call-roster` - ✅ WORKING - Shows faculty call calendar
- `/admin/faculty-call` - Faculty call management
- `/admin/templates` - PCAT/DO templates

## Test Credentials

- Username: `admin`
- Password: `admin123`

## Next Steps (if continuing)

1. Commit all changes
2. Test other pages that might have similar `model_validate()` issues
3. Consider adding pagination to call-roster if >500 assignments needed
