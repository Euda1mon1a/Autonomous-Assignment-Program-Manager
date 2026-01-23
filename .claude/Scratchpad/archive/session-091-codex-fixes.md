# Session 091: Codex Fixes & Merge Cleanup

**Date:** 2026-01-13
**Branch:** `feat/session-091`

## PRs Merged This Session

### PR #707 - Admin 3D tabs + bug fixes
- Added Solver 3D / Schedule 3D tabs to admin/scheduling
- Fixed tuple unpacking bug in engine.py
- Fixed queue endpoint (get_stats → get_queue_stats)
- Added OpenAPI type generation (drift prevention)
- **Codex fixes:** in_progress→RUNNING status, camelCase config keys

### PR #708 - Terminology fix
- Renamed total_blocks_assigned → total_assignments (Pydantic alias)
- No DB migration needed

## PR Open

### PR #709 - tIdx fix (re-added)
- Lost during squash merge conflict resolution
- Clears stale tIdx when processing moved deltas
- **Must merge for 3D viz to work correctly**

## Admin/Scheduler Status

| Feature | Status |
|---------|--------|
| Schedule generation | ✅ Works (1048 assignments, 0 violations) |
| 3D tabs visible | ✅ Merged |
| Solver visualization | ⚠️ Needs PR #709 for moved voxel fix |
| Queue status mapping | ✅ Fixed |
| Config key handling | ✅ Fixed |

## CI Status

Pre-existing Jest mock failures (`TypeError: The "original" argument...`). Not from our changes.

## Lesson Learned

**Squash merge + conflict resolution via GitHub UI = risky**
- UI strips context, easy to accidentally drop changes
- Better to resolve conflicts locally, then merge
