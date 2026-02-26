# Board Review Curriculum Planner Design Document

> **Target Audience:** Claude Code CLI
> **Last Updated:** 2026-02-26
> **Status:** Frontend Complete (Mock-First) — Backend Deferred

---

## Executive Summary

The Board Review Curriculum Planner integrates Tripler AMC Family Medicine's 18-month board review curriculum into the residency scheduler. It tracks 78 didactic sessions across 20 blocks, maps each to 202 ABFM Family Medicine Certification Areas (FMCAs) across 5 domains, and provides ITE score-based remediation planning.

**Current state:** Full mock-first frontend (4 tabs, localStorage persistence). Backend integration deferred until UI is validated.

---

## 1. Scope Definition

### 1.1 Curriculum Structure

| Element | Count | Description |
|---------|-------|-------------|
| **ABFM Domains** | 5 | ACD (35%), CCM (25%), UEC (20%), PC (15%), FOC (5%) |
| **FMCAs** | 202 | Family Medicine Certification Areas mapped to domains |
| **Blocks** | 20 | Topical groupings (Cardiovascular, Pulmonology, etc.) |
| **Sessions** | 78 | Individual didactic sessions within blocks |
| **Cycle** | 18 months | Full curriculum duration |

### 1.2 ABFM Domain Blueprint

| Code | Domain | Target % | Description |
|------|--------|----------|-------------|
| ACD | Acute Care & Diagnosis | 35 | Ambulatory scenarios requiring diagnosis or initial treatment |
| CCM | Chronic Care Management | 25 | Ongoing management of chronic diseases |
| UEC | Emergent & Urgent Care | 20 | Time-sensitive decisions in ED/hospital/urgent settings |
| PC | Preventive Care | 15 | Preventive services in ambulatory settings |
| FOC | Foundations of Care | 5 | Biostatistics, EBM, health policy, ethics, QI, health equity |

### 1.3 Feature Tabs

| Tab | Purpose | Data Sources |
|-----|---------|--------------|
| **Dashboard** | Completion metrics, domain coverage, timeline | Session statuses, domain mappings |
| **Curriculum** | Block/session browser with filters and status toggles | Blocks, sessions, FMCAs |
| **Analytics** | Domain distribution, heat map, FMCA gap analysis | Domain-session mappings, FMCA list |
| **ITE Mapping** | Score-based remediation prioritization | ITE percentile scores + session mappings |

---

## 2. Frontend Architecture

### 2.1 File Structure

```
frontend/src/
├── types/board-review.ts           # TypeScript interfaces
├── data/board-review-data.ts       # Static seed data (DOMAINS, FMCAS, BLOCKS)
├── hooks/useBoardReview.ts         # TanStack Query hooks + mock logic
├── app/admin/board-review/
│   ├── page.tsx                    # Main page (4 tabs)
│   └── loading.tsx                 # Suspense fallback
└── components/analytics/           # Reusable components (shared with PEC Phase 3)
    ├── DomainTracker.tsx           # Progress bars with target markers
    ├── HeatMapTable.tsx            # Row × column heat map
    ├── GapAnalysis.tsx             # Covered vs uncovered items
    └── TimelineStrip.tsx           # Horizontal block timeline
```

### 2.2 Type Conventions

Per AAPM standards:
- **Keys:** camelCase (`sessionId`, `domainCoverage`)
- **Enum values:** snake_case (`not_started`, `in_progress`, `completed`) — Gorgon's Gaze rule
- **Domain codes:** UPPER_CASE abbreviations (`ACD`, `CCM`, `UEC`, `PC`, `FOC`) — ABFM standard

### 2.3 State Management

| State | Storage | Scope |
|-------|---------|-------|
| Session status/presenter/date/notes | `localStorage` (`aapm-board-review-sessions`) | Persisted across refreshes |
| Tab selection, filters | React `useState` | Session only |
| Computed metrics (dashboard, analytics) | TanStack Query cache | 30-60s stale time |

### 2.4 Feature Flag

```env
NEXT_PUBLIC_BOARD_REVIEW_MOCK_MODE=true   # default: mock data
NEXT_PUBLIC_BOARD_REVIEW_MOCK_MODE=false  # use backend API
```

### 2.5 Reusable Analytics Components

These components in `components/analytics/` are generic and designed for reuse by PEC Phase 3:

| Component | Props | Reuse Pattern |
|-----------|-------|---------------|
| `DomainTracker` | `domains: DomainConfig[]` | Any domain/category progress tracking |
| `HeatMapTable` | `cells, columns, rows` | Any 2D categorical heat map |
| `GapAnalysis` | `items: GapItem[]` | Any coverage/gap audit |
| `TimelineStrip` | `blocks: TimelineBlock[]` | Any sequential phase visualization |

---

## 3. Domain Model (Backend — Deferred)

### 3.1 Database Tables

When backend is implemented, follow existing patterns from `backend/app/models/`:

```python
# backend/app/models/board_review.py

class BoardReviewSession(Base):
    """Individual board review didactic session."""
    __tablename__ = "board_review_sessions"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    block_id = Column(Integer, nullable=False)
    session_number = Column(Integer, nullable=False)  # 1-78
    title = Column(String(500), nullable=False)
    presenter = Column(String(200), nullable=True)
    status = Column(
        Enum("not_started", "in_progress", "completed", name="session_status"),
        default="not_started",
        nullable=False,
    )
    scheduled_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    domain_fmca_mappings = Column(JSONB, nullable=False)  # {domain_code: [fmca_names]}
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class BoardReviewBlock(Base):
    """Topical block grouping sessions."""
    __tablename__ = "board_review_blocks"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    block_number = Column(Integer, unique=True, nullable=False)  # 1-20
    name = Column(String(200), nullable=False)
    weeks = Column(Integer, nullable=False)
    icon = Column(String(10), nullable=True)

class IteScore(Base):
    """ITE domain percentile scores per resident per year."""
    __tablename__ = "ite_scores"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    person_id = Column(GUID, ForeignKey("people.id"), nullable=False)
    academic_year = Column(String(10), nullable=False)  # e.g., "AY25-26"
    acd_score = Column(Integer, nullable=True)
    ccm_score = Column(Integer, nullable=True)
    uec_score = Column(Integer, nullable=True)
    pc_score = Column(Integer, nullable=True)
    foc_score = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
```

### 3.2 API Endpoints

```
GET    /api/board-review/dashboard           → BoardReviewDashboard
GET    /api/board-review/blocks              → BoardReviewBlock[] (with sessions)
GET    /api/board-review/blocks?domain=ACD&status=completed  → filtered
PATCH  /api/board-review/sessions/{id}       → SessionUpdate
GET    /api/board-review/analytics           → { blockDomainCounts, heatMap, fmcaGaps }
POST   /api/board-review/ite/analyze         → IteRemediationItem[]
GET    /api/board-review/ite/scores/{person_id}  → IteScores
POST   /api/board-review/ite/scores          → create/update IteScores
```

### 3.3 Seed Data

The static data in `frontend/src/data/board-review-data.ts` serves as the seed script source. When backend is built:

1. Create Alembic migration for tables
2. Port `BLOCKS` array to a seed script (`backend/scripts/seed_board_review.py`)
3. `DOMAINS` and `FMCAS` remain as reference constants (backend + frontend)

---

## 4. Integration Points

### 4.1 Schedule Integration (Future)

Board review sessions can link to the scheduling system:

- **Activity model:** Create a `board_review` activity type for scheduling
- **InstitutionalEvent model:** Map sessions to calendar events
- **WeeklyPattern model:** Recurring board review time slots

### 4.2 PEC Evidence Source (Future)

Board review completion data feeds into PEC:

- Curriculum delivery metrics → PEC annual program evaluation
- Domain coverage gaps → PEC action items
- ITE score trends → PEC remediation decisions

---

## 5. Verification Checklist

- [x] `cd frontend && npx tsc --noEmit` — zero board review type errors
- [x] `cd frontend && npx eslint src/**/board-review* src/hooks/useBoardReview.ts src/components/analytics/*` — clean
- [x] Navigate to `/admin/board-review` — page loads with all 4 tabs
- [x] Dashboard tab shows domain coverage bars and timeline
- [x] Curriculum tab shows all 20 blocks with 78 sessions
- [x] Status toggle cycles not_started → in_progress → completed
- [x] Filters (domain, status, search) narrow visible sessions
- [x] Analytics tab shows heat map and gap analysis
- [x] ITE tab accepts scores and generates remediation plan
- [x] Navigation shows "Board Review" link in admin bar
- [x] localStorage persists session state across refreshes
- [ ] Backend API endpoints (deferred)
- [ ] Database migration (deferred)
- [ ] Seed data script (deferred)
- [ ] Schedule integration (deferred)
- [ ] PEC evidence source integration (deferred)
