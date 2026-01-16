# Session 2026-01-16: Research Data Collection & Gamification

## Status: PHASE 1 COMPLETE ✅

**Branch:** `main` (PRs #725 merged, #724 deferred features documented)
**P0 Documentation:** `docs/features/GAMIFIED_RESEARCH_PLATFORM.md`

---

## Context from Previous Session

### Completed Earlier Today
- PR #725 squash-merged (PAI agent spawning)
- `.claude/mcp/DEFERRED_GOVERNANCE_FEATURES.md` created (400+ lines)
- `.claude/mcp/PAI_AGENT_MCP_BRIDGE.md` cherry-picked from #724
- `docs/development/AGENT_SPAWNING.md` created (651 lines)

### Research Analysis
Analyzed Tan et al. (2026) JAMA Network Open study:
- **Key Finding:** Work hours (β=0.05, P=.34) NOT significantly associated with burnout
- **Stress IS associated** with hours (β=0.27, P<.001)
- **Competency IS associated** with hours (β=0.14, P<.001)
- **Implication:** Our multi-factor approach (Burnout Rt, FRMS, Fire Danger Index) is validated

---

## Current Focus: Gamified Research Data Collection

### User Idea
> "I wonder if we put a page where surveys were available and not forced, gamified (points?) custom icons? etc., we could collect data"

### Concept Exploration

**Why This Matters:**
1. Tan et al. study was cross-sectional (limitation they noted)
2. Longitudinal data would be more valuable
3. Self-reported burnout/stress/competency validates our algorithmic predictions
4. Military residency is under-studied population

### Gamification Elements to Consider

| Element | Purpose | Implementation |
|---------|---------|----------------|
| Points | Reward participation | Accumulate per survey completed |
| Badges/Icons | Achievement recognition | Custom military-themed icons |
| Streaks | Encourage consistency | Daily/weekly check-in rewards |
| Leaderboards | Social motivation | Anonymous ranking (opt-in) |
| Progress Bars | Visual feedback | "X% to next badge" |
| Unlockables | Long-term engagement | New avatars, themes |

### Data to Collect (Aligned with Tan et al.)

| Survey Type | Frequency | Items |
|-------------|-----------|-------|
| Mini Burnout | Weekly | MBI-2 (2-item) |
| Stress Check | Weekly | PSS-4 (4-item) |
| Sleep Quality | Weekly | PSQI single-item |
| Self-Efficacy | Bi-weekly | GSE-4 (4-item) |
| Weekly Reflection | Weekly | Open-ended (optional) |

### MCP Tools That Could Feed Surveys

The surveys could correlate self-report with algorithmic predictions:

| Our Tool | User Survey | Correlation Study |
|----------|-------------|-------------------|
| `calculate_burnout_rt_tool` | Self-reported burnout | Validate contagion model |
| `assess_creep_fatigue_tool` | Perceived workload | Validate cumulative strain |
| `calculate_fire_danger_tool` | Weekly stress | Validate multi-factor index |
| `analyze_sleep_debt_tool` | Sleep quality | Validate fatigue model |

### Privacy Considerations

- All surveys anonymous or pseudonymous
- Aggregate reporting only
- IRB approval if publishing research
- HIPAA N/A (wellness, not treatment)
- Opt-in only, no pressure
- Data not linked to scheduling decisions

### Technical Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend                             │
│  ┌─────────────────────────────────────────────────┐   │
│  │           /wellness/surveys                      │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐           │   │
│  │  │ MBI-2   │ │ PSS-4   │ │ Sleep   │           │   │
│  │  │ Survey  │ │ Survey  │ │ Check   │           │   │
│  │  └────┬────┘ └────┬────┘ └────┬────┘           │   │
│  │       │           │           │                 │   │
│  │       └───────────┼───────────┘                 │   │
│  │                   ▼                             │   │
│  │  ┌─────────────────────────────────────────┐   │   │
│  │  │      Gamification Engine                │   │   │
│  │  │  - Points tracker                       │   │   │
│  │  │  - Badge/achievement system             │   │   │
│  │  │  - Streak counter                       │   │   │
│  │  │  - Progress visualization               │   │   │
│  │  └─────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                    Backend                              │
│  ┌─────────────────────────────────────────────────┐   │
│  │  /api/wellness/                                 │   │
│  │    POST /surveys/{type}  - Submit response      │   │
│  │    GET  /points          - Get user points      │   │
│  │    GET  /achievements    - Get badges           │   │
│  │    GET  /leaderboard     - Anonymous ranking    │   │
│  └─────────────────────────────────────────────────┘   │
│                          │                              │
│                          ▼                              │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Research Analytics                             │   │
│  │    - Aggregate trends                           │   │
│  │    - Correlation with MCP predictions          │   │
│  │    - De-identified export for research         │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## Phase 1 Implementation Complete ✅

### Files Created

**Backend Models:** `backend/app/models/wellness.py`
- `Survey` - Survey definitions with questions JSON
- `SurveyResponse` - Responses with privacy-preserving linkage (SET NULL)
- `WellnessAccount` - Gamification account (points, streaks, achievements)
- `WellnessPointTransaction` - Points ledger for audit
- `HopfieldPosition` - Energy landscape positions
- `WellnessLeaderboardSnapshot` - Periodic rankings
- `SurveyAvailability` - Cooldown tracking

**Backend Schemas:** `backend/app/schemas/wellness.py`
- Full Pydantic v2 schemas for all operations
- Predefined survey instruments: MBI_2_QUESTIONS, PSS_4_QUESTIONS, PSQI_1_QUESTIONS, GSE_4_QUESTIONS, PULSE_QUESTIONS

**Backend Service:** `backend/app/services/wellness_service.py`
- Survey submission with scoring
- Points economy (earn, track, ledger)
- Streak management (weekly)
- Achievement unlocking logic
- Leaderboard management

**Backend Routes:** `backend/app/api/routes/wellness.py`
- `/wellness/surveys` - List and submit surveys
- `/wellness/account` - Manage gamification account
- `/wellness/leaderboard` - Anonymous rankings
- `/wellness/hopfield` - Position submission
- `/wellness/pulse` - Quick check-ins
- `/wellness/admin/analytics` - Aggregate stats

**Frontend Types:** `frontend/src/features/wellness/types.ts`
- TypeScript interfaces (camelCase)
- Achievement definitions
- Survey type display mappings

**Frontend Hooks:** `frontend/src/features/wellness/hooks/useWellness.ts`
- React Query hooks for all endpoints
- Query keys for cache management

**Frontend Components:**
- `frontend/src/features/wellness/components/QuickPulseWidget.tsx` - Dashboard widget
- `frontend/src/features/wellness/index.ts` - Feature exports

**Frontend Pages:**
- `frontend/src/app/wellness/page.tsx` - Main hub with tabs (Surveys, Achievements, Leaderboard, History)
- `frontend/src/app/wellness/surveys/[surveyId]/page.tsx` - Survey completion flow

**Documentation:**
- `docs/features/GAMIFIED_RESEARCH_PLATFORM.md` - **P0 Complete** (comprehensive roadmap)

### Files Modified

- `backend/app/models/__init__.py` - Added wellness model exports
- `backend/app/api/routes/__init__.py` - Registered wellness router

### Deferred (Per User Request)

- **Alembic Migration:** Tables not yet created - defer to implementation phase
- **Seed Data:** Predefined surveys not seeded to database

---

## Next Phases (Future Work)

### Phase 2: Gamification Enhancement (Q3 2027)
- [ ] Points redemption system
- [ ] Streak recovery mechanics
- [ ] Email notifications for streaks

### Phase 3: Hopfield Integration (Q4 2027)
- [ ] 3D energy landscape (React Three Fiber)
- [ ] Draggable ball interaction
- [ ] Position → algorithm correlation

### Phase 4: Research Analytics (Q1 2028)
- [ ] Admin analytics dashboard
- [ ] Algorithm correlation reports
- [ ] De-identified CSV export
- [ ] IRB protocol documentation

---

## Related Files

- `tan_2026_oi_251437_1767812642.93194.pdf` - JAMA study
- `.claude/mcp/DEFERRED_GOVERNANCE_FEATURES.md` - Tiered access (residents = read-only)
- `frontend/src/app/(admin)/admin/visualizations/` - Existing viz pages
- `docs/features/GAMIFIED_RESEARCH_PLATFORM.md` - **P0 Documentation** (new)

---

*Scratchpad created 2026-01-16 | Phase 1 complete 2026-01-16*
