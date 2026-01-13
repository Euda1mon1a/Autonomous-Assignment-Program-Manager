# Session 2026-01-12: Hub Consolidation Roadmap

## TL;DR
Fixed GUI post-consolidation (Couatl Killer), created comprehensive hub roadmap, addressed Codex feedback. Ready for Phase 1 hub work.

## PR #698 (Merged)
```
ff2186fe feat: Couatl Killer + Hub Consolidation Roadmap (#698)
```

### Key Deliverables
1. **Couatl Killer** - Pre-commit hook catching camelCase query params
2. **Hub Roadmap** - `docs/planning/FRONTEND_HUB_CONSOLIDATION_ROADMAP.md`
3. **Codex Fixes** - Tier mapping + blocks pagination

## Tier Model (Final)
| Tier | Role | Who |
|------|------|-----|
| 0 | Self-service | Residents, Faculty |
| 0.5 | Learner managers | Select faculty (future) |
| 1 | Program ops | Coordinators, Chiefs |
| 2 | System admin | Admin only |

**Transparency:** Tier 0 can VIEW everything (except audit). Tier controls EDIT, not VIEW.

## Hub Inventory (13 total)
| Status | Hubs |
|--------|------|
| ✅ Done | Swap Hub |
| Partial | Schedule, People, Call, Import/Export |
| To Build | Activity, Absences, Procedures, Ops, Compliance, Analytics, Config |
| Roadmap | Learner Hub (Tier 0.5) |

## Priority Order
1. Activity Hub
2. Absences Hub
3. People Hub Enhancement
4. Procedures Hub
5. Ops Hub
6. Compliance Hub
7. Analytics Hub
8. Import/Export Hub
9. Config Hub
10. Schedule Hub
11. Call Hub

## Current State
- **Branch:** `feat/hub-consolidation-phase1`
- **Base:** `ff2186fe` (main, synced)
- **Dev Server:** Running on :3002

## Key Files
- `docs/planning/FRONTEND_HUB_CONSOLIDATION_ROADMAP.md` - Master roadmap
- `scripts/couatl-killer.sh` - Query param validator
- `frontend/src/components/ui/RiskBar.tsx` - Tier utility (fixed)
- `frontend/src/hooks/useAssignmentsForRange.ts` - Blocks hook (simplified)

## Gold Standard Pattern
Swap Hub (`/swaps`) - replicate for all hubs:
- Declarative tab config
- Tier-based filtering
- RiskBar integration
- Feature module pattern

## Warnings
1. **Couatl Killer** - Axios interceptor doesn't convert query strings
2. **Permission Double-Check** - Filter tabs AND guard content render
3. **Parallel Run** - Don't delete legacy until hub verified
