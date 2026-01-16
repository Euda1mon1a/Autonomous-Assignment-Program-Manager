# Gamified Research Data Collection Platform

> **Status:** Phase 1 In Development (Backend + Frontend Scaffolding Complete)
> **Timeline:** Q2 2027 - Q1 2028
> **Priority:** P0 for Documentation, P1 for Implementation

## Overview

The Gamified Research Data Collection Platform enables voluntary wellness check-ins for residents and faculty, correlating self-reported data with algorithmic predictions from our exotic/resilience modules. This creates a research-ready dataset for validating multi-factor burnout/stress models.

## Research Motivation

Based on Tan et al. 2026 (JAMA Network Open):
- Work hours (β=0.05, P=.34) are NOT significantly associated with burnout
- Stress IS associated with hours (β=0.27, P<.001)
- Burnout depends on: what happens during hours, life outside work, relationship to work, organizational culture

**Our Opportunity:** Validate our multi-factor models (Burnout Rt, FRMS, Fire Danger Index) against self-reported data.

## Feature Components

### 1. Quick Check-In Widget
Embedded in dashboard for low-friction daily pulse checks.

### 2. Wellness Hub Page
Dedicated `/wellness` route with:
- Survey completion tracking
- Points & streaks display
- Achievement gallery
- Anonymous leaderboard
- Survey history

### 3. Hopfield "Roll the Ball" Visualization
Interactive 3D visualization where users position a ball on the energy landscape to indicate perceived program stability.

### 4. Anonymous Leaderboard
Opt-in participation with custom display names.

## Survey Instruments

| Survey | Items | Time | Measures | Frequency |
|--------|-------|------|----------|-----------|
| MBI-2 | 2 | 30s | Burnout (EE + DP) | Weekly |
| PSS-4 | 4 | 1m | Perceived stress | Weekly |
| PSQI-1 | 1 | 10s | Sleep quality | Weekly |
| GSE-4 | 4 | 1m | Self-efficacy | Bi-weekly |
| Pulse | 1 | 5s | Quick mood/energy | Daily |

**Total weekly commitment:** ~3 minutes

## Exotic Module Correlation Matrix

| Our Module | MCP Tool | Survey Measure |
|------------|----------|----------------|
| Burnout Rt | `calculate_burnout_rt_tool` | MBI-2 |
| Fire Danger Index | `calculate_fire_danger_tool` | PSS-4 + MBI-2 |
| FRMS Fatigue | `run_frms_assessment_tool` | PSQI-1 |
| Creep Fatigue | `assess_creep_fatigue_tool` | PSS-4 trend |
| Defense Levels | `get_defense_level_tool` | Program Pulse |
| Hopfield Energy | `calculate_hopfield_energy_tool` | User position |
| SPC Analysis | `run_spc_analysis_tool` | Stress variance |
| Shapley Workload | `calculate_shapley_workload_tool` | GSE-4 |

## Gamification System

### Points Economy

| Action | Points | Limit |
|--------|--------|-------|
| MBI-2 | 50 | 1x/week |
| PSS-4 | 50 | 1x/week |
| Sleep | 25 | 1x/week |
| GSE-4 | 50 | 1x/2 weeks |
| Quick pulse | 10 | 1x/day |
| Hopfield positioning | 25 | 1x/week |
| Weekly streak bonus | 50 | After 2+ weeks |
| Block completion bonus | 200 | All surveys done |

### Achievements

| Badge | Criteria |
|-------|----------|
| First Check-In | Complete first survey |
| Century Club | 100 pts lifetime |
| Rising Star | 500 pts lifetime |
| Iron Resident | 1000 pts lifetime |
| Weekly Warrior | 4-week streak |
| Consistency King | 8-week streak |
| Data Hero | All surveys in a block |
| Research Champion | 52-week participation |

## Technical Implementation

### Backend (Completed)

- **Models:** `backend/app/models/wellness.py`
  - `Survey` - Survey definitions
  - `SurveyResponse` - Responses with privacy-preserving linkage
  - `WellnessAccount` - Gamification account
  - `WellnessPointTransaction` - Points ledger
  - `HopfieldPosition` - Energy landscape positions
  - `WellnessLeaderboardSnapshot` - Periodic rankings
  - `SurveyAvailability` - Cooldown tracking

- **Schemas:** `backend/app/schemas/wellness.py`
  - Full Pydantic v2 schemas for all operations
  - Predefined survey instruments (MBI-2, PSS-4, etc.)

- **Service:** `backend/app/services/wellness_service.py`
  - Survey submission with scoring
  - Points economy (earn, track, ledger)
  - Streak management
  - Achievement unlocking
  - Leaderboard management

- **Routes:** `backend/app/api/routes/wellness.py`
  - `/wellness/surveys` - List and submit surveys
  - `/wellness/account` - Manage gamification account
  - `/wellness/leaderboard` - Anonymous rankings
  - `/wellness/hopfield` - Position submission
  - `/wellness/pulse` - Quick check-ins
  - `/wellness/admin/analytics` - Aggregate stats

### Frontend (Completed)

- **Types:** `frontend/src/features/wellness/types.ts`
- **Hooks:** `frontend/src/features/wellness/hooks/useWellness.ts`
- **Components:**
  - `QuickPulseWidget` - Dashboard widget
  - Wellness Hub page at `/wellness`
  - Survey completion flow at `/wellness/surveys/[id]`
  - Tabs: Surveys, Achievements, Leaderboard, History

### Deferred

- **Alembic Migration:** Tables not yet created (defer to implementation phase)
- **Hopfield 3D Visualization:** React Three Fiber component (Phase 3)
- **Algorithm Snapshot Capture:** MCP tool integration for correlation

## Privacy & Compliance

| Aspect | Implementation |
|--------|----------------|
| Person linking | Optional; `person_id` can be SET NULL |
| Leaderboard | Opt-in with anonymous display names |
| Export | De-identified aggregate data only |
| Admin access | Aggregate trends, not individual responses |
| Audit trail | SQLAlchemy-Continuum versioning |

### IRB Considerations

If publishing research:
1. IRB approval required (likely expedited review)
2. Informed consent at first survey
3. Right to withdraw (delete responses)
4. De-identification protocol for publications

## Implementation Phases

### Phase 1: Foundation (Q2 2027) ✅ Backend Complete
- [x] Database models
- [x] Pydantic schemas
- [x] Service layer with gamification
- [x] API routes
- [x] Frontend wellness hub
- [x] Survey completion flow
- [ ] Alembic migration (DEFERRED)
- [ ] Seed predefined surveys

### Phase 2: Gamification Enhancement (Q3 2027)
- [ ] Points redemption system
- [ ] Streak recovery mechanics
- [ ] Additional achievements
- [ ] Email notifications for streaks

### Phase 3: Hopfield Integration (Q4 2027)
- [ ] 3D energy landscape (React Three Fiber)
- [ ] Draggable ball interaction
- [ ] Position → algorithm correlation
- [ ] Aggregate visualization

### Phase 4: Research Analytics (Q1 2028)
- [ ] Admin analytics dashboard
- [ ] Algorithm correlation reports
- [ ] De-identified CSV export
- [ ] IRB protocol documentation

## Files Reference

### Backend
```
backend/app/models/wellness.py          # Database models
backend/app/schemas/wellness.py         # Pydantic schemas
backend/app/services/wellness_service.py # Gamification logic
backend/app/api/routes/wellness.py      # API endpoints
```

### Frontend
```
frontend/src/features/wellness/types.ts           # TypeScript types
frontend/src/features/wellness/hooks/useWellness.ts # React Query hooks
frontend/src/features/wellness/components/        # UI components
frontend/src/app/wellness/page.tsx               # Main hub page
frontend/src/app/wellness/surveys/[surveyId]/page.tsx # Survey flow
```

## Publication Targets

- JAMA Network Open (follow-up to Tan et al.)
- Academic Medicine
- Journal of Graduate Medical Education
- Military Medicine (DoD angle)

---

*This platform positions us for research collaboration while keeping implementation scope manageable. The gamification drives engagement; the exotic module correlation drives scientific value.*
