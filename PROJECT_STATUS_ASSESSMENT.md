# Project Status Assessment

**Generated:** 2025-12-17
**Current Branch:** `claude/assess-project-status-Ia9J6`
**Overall Status:** ~85% Complete - Ready for Integration Phase

---

## Executive Summary

The **Autonomous Assignment Program Manager** (Residency Scheduler) is a production-ready medical residency scheduling application with comprehensive FMIT (Faculty Member In Training) integration recently completed. The codebase is mature with 40+ backend test files, robust API coverage, and a well-structured frontend.

**Key Achievements:**
- Core scheduling with 4 algorithms (Greedy, CP-SAT, PuLP, Hybrid)
- ACGME compliance validation (80-hour, 1-in-7, supervision ratios)
- Complete FMIT swap system with conflict detection
- 3-tier resilience framework (code complete)
- 34 database tables across 8 migrations

---

## Current State vs. Recommended Priorities

### Phase 1 Analysis (Week 1 Priorities)

| Priority | Feature | Status | Notes |
|----------|---------|--------|-------|
| P0 | **Audit Query API** | ⚠️ 70% | Frontend hooks exist (`frontend/src/features/audit/hooks.ts`), needs backend `/audit/*` routes |
| P0 | **Cross-System Conflict Detection** | ✅ 90% | Backend services exist, frontend hooks complete |
| P1 | **Coverage Gap Analysis** | ✅ 85% | Implemented in `fmit_health.py:123-146`, `GET /fmit/coverage` |
| P1 | **FMIT Health Dashboard** | ✅ Complete | Comprehensive API: `/fmit/health`, `/fmit/status`, `/fmit/metrics`, `/fmit/coverage`, `/fmit/alerts/summary` |

### Phase 2 Analysis (Week 2 Priorities)

| Priority | Feature | Status | Notes |
|----------|---------|--------|-------|
| P0 | **Unified Heatmap** | ❌ Not Started | No plotly/kaleido integration |
| P1 | **Conflict Dashboard** | ✅ 85% | Frontend components exist (`ConflictDashboard.tsx`, `ConflictList.tsx`) |
| P1 | **Calendar Export ICS** | ❌ Not Started | No ical library |
| P1 | **Swap Marketplace UI** | ⚠️ 60% | Backend swap portal exists, frontend needs UI completion |

### Phase 3 Analysis (Week 3+ Features)

| Feature | Status | Notes |
|---------|--------|-------|
| Swap Auto-Matching | ⚠️ 50% | `faculty_preference_service.py` exists, matching logic partial |
| Conflict Auto-Resolution | ⚠️ 40% | Detection works, auto-resolution needs work |
| Pareto Optimization | ❌ Not Started | pymoo not installed |
| Temporal Constraints | ⚠️ 60% | Basic constraints in `constraints.py` |
| Preference ML | ❌ Not Started | Future enhancement |

---

## Detailed Component Status

### Backend (Python/FastAPI)

| Component | Files | Status | Coverage |
|-----------|-------|--------|----------|
| **API Routes** | 13 modules | ✅ Complete | 40+ endpoints |
| **Services** | 25 modules | ✅ Complete | All core functionality |
| **Models** | 19 core + 22 resilience | ✅ Complete | 41 total |
| **Repositories** | 5 modules | ✅ Complete | Clean data access layer |
| **Scheduling** | 6 modules | ✅ Complete | 4 algorithms |
| **Resilience** | 12 modules | ✅ Complete | 3-tier framework |
| **Tests** | 40 files | ✅ Good | High coverage |

### Frontend (Next.js/React)

| Component | Status | Notes |
|-----------|--------|-------|
| **Core Pages** | ✅ Complete | 13 pages implemented |
| **Components** | ✅ Complete | 33+ reusable components |
| **Audit Feature** | ✅ Complete | Full hooks, UI components |
| **Conflicts Feature** | ✅ Complete | Dashboard, resolution UI |
| **Import/Export** | ✅ Complete | Excel support |
| **Templates Feature** | ✅ Complete | Pattern editor, templates |
| **Tests** | ⚠️ 40% | MSW setup, needs expansion |

### Infrastructure

| Component | Status | Notes |
|-----------|--------|-------|
| **Docker** | ✅ Ready | Multi-container setup |
| **PostgreSQL** | ✅ Ready | 8 migrations applied |
| **Monitoring** | ⚠️ Config Only | Prometheus/Grafana configs exist, not deployed |
| **Redis** | ❌ Not Deployed | Required for Celery |
| **CI/CD** | ✅ Ready | GitHub Actions configured |

---

## Critical Gaps for Production

### Immediate (P0 - Must Have)

1. **Audit Query Backend Routes**
   - Frontend expects `/audit/logs`, `/audit/statistics`, `/audit/export`
   - SQLAlchemy-Continuum is configured but routes missing
   - **Effort:** 2-3 hours

2. **Unified Heatmap Visualization**
   - Combine residency + FMIT schedules in single view
   - Requires plotly + kaleido
   - **Effort:** 4-6 hours

### High Priority (P1 - Should Have)

3. **Calendar ICS Export**
   - Allow faculty to export schedules to personal calendars
   - Requires icalendar library
   - **Effort:** 1-2 hours

4. **Swap Marketplace UI**
   - Complete frontend for swap browsing/requesting
   - Backend ready at `/api/portal/*`
   - **Effort:** 2-3 hours

### Infrastructure (Required for Production)

5. **Deploy Redis**
   - Required for Celery background tasks
   - Needed for: health checks, notifications, periodic analysis
   - **Effort:** 30 min

6. **Configure Celery Workers**
   - Start worker and beat scheduler
   - Enable resilience monitoring
   - **Effort:** 30 min

---

## Recommended Next Steps

### Minimum Viable Path (8-12 hours)

For a military hospital deployment with both residency and FMIT scheduling:

```
Order  | Task                        | Est.  | Dependency
-------|-----------------------------|-------|------------
1      | Audit API Backend Routes    | 2-3h  | None
2      | Cross-System Conflict API   | 2-3h  | #1
3      | Coverage Gap Endpoints      | 1-2h  | None
4      | Unified Heatmap             | 4-6h  | plotly, kaleido
```

### Full Phase 1+2 Path (16-20 hours)

```
Order  | Task                        | Est.  | Dependency
-------|-----------------------------|-------|------------
1      | Audit API Backend Routes    | 2-3h  | None
2      | Cross-System Conflict API   | 2-3h  | #1
3      | Coverage Gap Enhancement    | 1-2h  | None
4      | Unified Heatmap             | 4-6h  | plotly, kaleido
5      | Conflict Dashboard Polish   | 2-3h  | #2
6      | Calendar ICS Export         | 1-2h  | icalendar
7      | Swap Marketplace UI         | 2-3h  | None
```

---

## Technical Dependencies

### Already Installed
- SQLAlchemy 2.0.45 (with audit support via Continuum)
- FastAPI 0.124.4
- OR-Tools + PuLP (constraint solving)
- NetworkX (graph analysis)
- openpyxl (Excel export)
- Prometheus client (metrics)

### Needs Installation
- `plotly` - Heatmap visualization
- `kaleido` - Static image export for plotly
- `icalendar` - ICS calendar export
- `pymoo` - Multi-objective optimization (Phase 3)

---

## Files Reference

### Key Backend Files for Next Phase
- `backend/app/api/routes/` - Add audit routes here
- `backend/app/services/conflict_auto_detector.py` - Enhance for cross-system
- `backend/app/api/routes/fmit_health.py` - Coverage gap base (676 lines)
- `backend/app/services/fmit_scheduler_service.py` - Core FMIT logic

### Key Frontend Files for Next Phase
- `frontend/src/features/audit/` - Complete, needs backend
- `frontend/src/features/conflicts/` - Complete
- `frontend/src/lib/hooks.ts` - API hooks
- `frontend/src/app/` - Page routes

---

## Recent Git Activity

Last 10 commits all focused on FMIT integration:
```
80f036a Claude/consolidate m9xx0 branches w fxl4 (#191)
7d57d25 Claude/fmit integ swap workflow m9 xx0 (#187)
2aa50fd Claude/fmit test faculty pref svc m9 xx0 (#185)
aabe38f Claude/fmit cli commands m9 xx0 (#190)
b362bc8 Claude/fmit test conflict repo m9 xx0 (#184)
d4025b2 Claude/fmit health routes m9 xx0 (#186)
e12b343 Claude/fmit test swap repo m9 xx0 (#188)
996e26e Claude/fmit test swap notify svc m9 xx0 (#183)
```

---

## Conclusion

The project is **well-positioned for operational integration**. Core scheduling and FMIT systems are complete. The primary gaps are:

1. **Audit API routes** - Frontend ready, backend needs routes
2. **Unified visualization** - Needs plotly integration
3. **Infrastructure** - Redis + Celery deployment

**Recommended approach:** Focus on P0 items (Audit API, Heatmap) for minimum viable deployment, then iterate on P1 features.

---

## Future: Longitudinal Scheduling Analytics (PI/QI Research)

> **Priority:** Low (post-production)
> **Value:** High - Actual performance improvement data, not checkbox compliance
> **Status:** Design phase - Not started

### Motivation

Current "quality improvement" in medical scheduling is often retrospective chart review and anecdotal feedback. This initiative would provide **quantitative, longitudinal analysis** of scheduling fairness, satisfaction, and stability — the kind of data that could actually inform policy changes and be published.

The existing codebase has strong foundations:
- SQLAlchemy-Continuum already versions all Assignment changes
- 21 constraint classes with weighted penalties (translatable to metrics)
- `explain_json` field captures decision rationale per assignment
- ScheduleRun model tracks generation events

What's missing is the **metrics computation layer** and **temporal analysis framework**.

---

### Proposed Architecture: Schedule Metrics Framework

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SCHEDULE ANALYTICS PIPELINE                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   ┌─────────────┐     ┌──────────────┐     ┌───────────────────┐   │
│   │ Assignment  │────▶│   Metrics    │────▶│  MetricSnapshot   │   │
│   │  Versions   │     │   Computer   │     │    (per version)  │   │
│   │ (Continuum) │     │              │     │                   │   │
│   └─────────────┘     └──────────────┘     └───────────────────┘   │
│         │                    │                       │              │
│         │                    │                       ▼              │
│         │                    │              ┌───────────────────┐   │
│         │                    │              │   Time Series     │   │
│         │                    │              │   Analysis        │   │
│         │                    │              │   (pandas/scipy)  │   │
│         │                    │              └───────────────────┘   │
│         │                    │                       │              │
│         ▼                    ▼                       ▼              │
│   ┌─────────────┐     ┌──────────────┐     ┌───────────────────┐   │
│   │  Schedule   │     │    Pyomo     │     │   Visualization   │   │
│   │    Diff     │     │    Model     │     │   & Export        │   │
│   │  (deltas)   │     │ (optional)   │     │   (publication)   │   │
│   └─────────────┘     └──────────────┘     └───────────────────┘   │
│                              │                                      │
│                              ▼                                      │
│                       ┌──────────────┐                              │
│                       │  Sensitivity │                              │
│                       │  Analysis    │                              │
│                       │  (research)  │                              │
│                       └──────────────┘                              │
└─────────────────────────────────────────────────────────────────────┘
```

---

### Metrics Module Sketch

#### Core Metrics Classes

```python
# backend/app/analytics/scheduling_metrics.py (proposed)

from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Optional
from datetime import datetime
import numpy as np

class MetricCategory(Enum):
    FAIRNESS = "fairness"
    SATISFACTION = "satisfaction"
    STABILITY = "stability"
    COMPLIANCE = "compliance"
    RESILIENCE = "resilience"


@dataclass
class FairnessMetrics:
    """Workload distribution equity measures"""

    # Gini coefficient: 0 = perfect equality, 1 = perfect inequality
    gini_coefficient: float

    # Standard deviation of blocks per person
    workload_variance: float

    # Ratio of PGY-1 workload to PGY-3 workload (should be ~1.0)
    pgy_equity_ratio: float

    # Weekend assignment distribution fairness
    weekend_burden_gini: float

    # Holiday assignment distribution fairness
    holiday_burden_gini: float

    # Call assignment distribution fairness
    call_burden_gini: float

    # Hub faculty protection score (are critical faculty overloaded?)
    hub_protection_score: float  # 0-1, higher = better protected


@dataclass
class SatisfactionMetrics:
    """Preference fulfillment and accommodation measures"""

    # Percentage of faculty preferred weeks honored
    preference_fulfillment_rate: float

    # Percentage of faculty blocked weeks respected
    blocked_week_compliance: float

    # Continuity score: preference for consecutive assignments
    continuity_score: float

    # Absence accommodation rate
    absence_accommodation_rate: float

    # FMIT swap request success rate
    swap_success_rate: float

    # Average assignment confidence (from explain_json)
    mean_assignment_confidence: float


@dataclass
class StabilityMetrics:
    """Schedule churn and cascade measures"""

    # Number of assignments changed from previous version
    assignments_changed: int

    # Percentage of schedule that changed
    churn_rate: float

    # How far changes cascade (avg hops in dependency graph)
    ripple_factor: float

    # Single-point-of-failure risk score
    n1_vulnerability_score: float

    # Number of constraint violations introduced
    new_violations: int

    # Time since last major refactoring (days)
    days_since_major_change: int


@dataclass
class ComplianceMetrics:
    """ACGME and policy compliance measures"""

    # 80-hour rule compliance percentage
    eighty_hour_compliance: float

    # 1-in-7 day off compliance percentage
    one_in_seven_compliance: float

    # Supervision ratio compliance
    supervision_compliance: float

    # Number of hard constraint violations
    hard_violations: int

    # Weighted sum of soft constraint penalties
    soft_penalty_total: float


@dataclass
class ScheduleVersionMetrics:
    """Complete metrics snapshot for a schedule version"""

    version_id: str
    computed_at: datetime
    schedule_run_id: Optional[str]

    fairness: FairnessMetrics
    satisfaction: SatisfactionMetrics
    stability: StabilityMetrics
    compliance: ComplianceMetrics

    # Metadata
    total_assignments: int
    total_persons: int
    total_blocks: int
    date_range_start: datetime
    date_range_end: datetime
```

#### Metrics Computer Service

```python
# backend/app/services/metrics_computer.py (proposed)

class ScheduleMetricsComputer:
    """
    Computes comprehensive metrics for a schedule state.

    Can operate on:
    - Current live schedule
    - Historical version (via Continuum)
    - Hypothetical schedule (for what-if analysis)
    """

    def __init__(self, db: Session):
        self.db = db

    async def compute_fairness(
        self,
        assignments: List[Assignment],
        persons: List[Person]
    ) -> FairnessMetrics:
        """Compute all fairness metrics for given assignments"""

        # Workload per person
        workloads = self._count_workloads(assignments, persons)

        return FairnessMetrics(
            gini_coefficient=self._gini(list(workloads.values())),
            workload_variance=np.std(list(workloads.values())),
            pgy_equity_ratio=self._pgy_equity(assignments, persons),
            weekend_burden_gini=self._weekend_gini(assignments, persons),
            holiday_burden_gini=self._holiday_gini(assignments, persons),
            call_burden_gini=self._call_gini(assignments, persons),
            hub_protection_score=self._hub_protection(assignments, persons),
        )

    def _gini(self, values: List[float]) -> float:
        """Calculate Gini coefficient for distribution equality"""
        if not values or all(v == 0 for v in values):
            return 0.0
        sorted_values = sorted(values)
        n = len(sorted_values)
        cumsum = np.cumsum(sorted_values)
        return (2 * sum((i + 1) * v for i, v in enumerate(sorted_values)) -
                (n + 1) * sum(sorted_values)) / (n * sum(sorted_values))

    async def compute_for_version(
        self,
        version_id: str
    ) -> ScheduleVersionMetrics:
        """Compute metrics for a historical schedule version"""
        # Load assignments at that version via Continuum
        # ...

    async def compute_current(self) -> ScheduleVersionMetrics:
        """Compute metrics for current live schedule"""
        # ...

    async def compare_versions(
        self,
        version_a: str,
        version_b: str
    ) -> Dict[str, float]:
        """Compute deltas between two schedule versions"""
        # ...
```

#### Data Models for Persistence

```python
# backend/app/models/schedule_metrics.py (proposed)

class ScheduleVersion(Base):
    """
    Represents a complete schedule state at a point in time.
    Links to ScheduleRun for generation context.
    """
    __tablename__ = "schedule_versions"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    schedule_run_id = Column(UUID, ForeignKey("schedule_runs.id"), nullable=True)
    version_number = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # What triggered this version
    trigger_type = Column(
        Enum("generation", "swap", "absence", "manual_edit", "auto_rebalance"),
        nullable=False
    )

    # For version tree/history
    parent_version_id = Column(UUID, ForeignKey("schedule_versions.id"), nullable=True)

    # Model fingerprint for reproducibility (optional Pyomo integration)
    model_hash = Column(String(64), nullable=True)  # SHA-256

    # Relationships
    metrics = relationship("MetricSnapshot", back_populates="schedule_version")
    parent = relationship("ScheduleVersion", remote_side=[id])


class MetricSnapshot(Base):
    """
    Point-in-time metric value for a schedule version.
    Normalized structure for flexible metric types.
    """
    __tablename__ = "metric_snapshots"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    schedule_version_id = Column(UUID, ForeignKey("schedule_versions.id"))

    category = Column(
        Enum("fairness", "satisfaction", "stability", "compliance", "resilience"),
        nullable=False
    )
    metric_name = Column(String(50), nullable=False)  # e.g., "gini_coefficient"
    value = Column(Float, nullable=False)

    computed_at = Column(DateTime, default=datetime.utcnow)
    methodology_version = Column(String(20), default="1.0")  # For reproducibility

    # Index for time-series queries
    __table_args__ = (
        Index("ix_metrics_version_category", "schedule_version_id", "category"),
        Index("ix_metrics_name_time", "metric_name", "computed_at"),
    )


class ScheduleDiff(Base):
    """
    Records what changed between schedule versions.
    Enables understanding of schedule evolution.
    """
    __tablename__ = "schedule_diffs"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    from_version_id = Column(UUID, ForeignKey("schedule_versions.id"))
    to_version_id = Column(UUID, ForeignKey("schedule_versions.id"))

    computed_at = Column(DateTime, default=datetime.utcnow)

    # Change summary
    assignments_added = Column(JSON)    # [{person_id, block_id, rotation_id}, ...]
    assignments_removed = Column(JSON)  # [{person_id, block_id, rotation_id}, ...]
    assignments_modified = Column(JSON) # [{person_id, block_id, changes: {...}}, ...]

    # Aggregate stats
    total_changes = Column(Integer)
    persons_affected = Column(Integer)
    blocks_affected = Column(Integer)
```

---

### Pyomo Integration (Optional Research Extension)

For deeper analysis (sensitivity, Pareto frontiers, model introspection):

```python
# backend/app/scheduling/solvers/pyomo_solver.py (proposed)

from pyomo.environ import (
    ConcreteModel, Var, Objective, Constraint,
    Binary, minimize, SolverFactory
)

class PyomoScheduleSolver(BaseSolver):
    """
    Pyomo-based solver for research and analysis.

    NOT intended to replace OR-Tools/PuLP for production.
    Use cases:
    - Model introspection and sensitivity analysis
    - Multi-objective optimization (Pareto frontier)
    - Stochastic scheduling under uncertainty
    - Academic publication and reproducibility
    """

    def build_model(self, context: SchedulingContext) -> ConcreteModel:
        """Construct Pyomo model from scheduling context"""
        model = ConcreteModel()

        # Sets
        model.RESIDENTS = Set(initialize=[r.id for r in context.residents])
        model.BLOCKS = Set(initialize=[b.id for b in context.blocks])
        model.TEMPLATES = Set(initialize=[t.id for t in context.templates])

        # Decision variables: x[r,b,t] = 1 if resident r assigned to block b with template t
        model.x = Var(
            model.RESIDENTS, model.BLOCKS, model.TEMPLATES,
            domain=Binary
        )

        # Translate constraints from existing constraint classes
        self._add_hard_constraints(model, context)
        self._add_soft_constraints(model, context)

        return model

    def get_dual_values(self, model: ConcreteModel) -> Dict[str, float]:
        """Extract shadow prices for constraint analysis"""
        # Useful for understanding which constraints are binding
        # and how much relaxing them would improve the objective
        pass

    def compute_model_hash(self, model: ConcreteModel) -> str:
        """Generate reproducibility hash for model state"""
        # Enables tracking of model evolution over time
        pass

    def export_for_publication(self, model: ConcreteModel, path: str):
        """Export model in standard formats (MPS, LP) for reproducibility"""
        pass
```

---

### API Endpoints (Proposed)

```python
# backend/app/api/routes/analytics.py (proposed)

@router.get("/analytics/metrics/current")
async def get_current_metrics() -> ScheduleVersionMetrics:
    """Get metrics for current live schedule"""

@router.get("/analytics/metrics/history")
async def get_metrics_history(
    metric_name: str,
    start_date: datetime,
    end_date: datetime,
) -> List[MetricTimeSeries]:
    """Get time series of a metric over date range"""

@router.get("/analytics/fairness/trend")
async def get_fairness_trend(
    months: int = 6,
) -> FairnessTrendReport:
    """Get fairness metrics trend over time"""

@router.get("/analytics/compare/{version_a}/{version_b}")
async def compare_versions(
    version_a: str,
    version_b: str,
) -> VersionComparison:
    """Compare metrics between two schedule versions"""

@router.post("/analytics/what-if")
async def what_if_analysis(
    proposed_changes: List[AssignmentChange],
) -> WhatIfResult:
    """Predict metric impact of proposed changes"""

@router.get("/analytics/export/research")
async def export_for_research(
    start_date: datetime,
    end_date: datetime,
    anonymize: bool = True,
) -> ResearchDataExport:
    """Export anonymized data for research/publication"""
```

---

### Existing Foundation

**Good news:** `backend/app/analytics/metrics.py` already implements several core metrics:

| Function | Coverage | Notes |
|----------|----------|-------|
| `calculate_fairness_index()` | ✅ Complete | Gini coefficient with status thresholds |
| `calculate_coverage_rate()` | ✅ Complete | Block coverage percentage |
| `calculate_acgme_compliance_rate()` | ✅ Complete | Violation tracking |
| `calculate_preference_satisfaction()` | ✅ Complete | Preference matching rate |
| `calculate_consecutive_duty_stats()` | ✅ Complete | Duty pattern analysis |

**What's missing:** Persistence layer (ScheduleVersion, MetricSnapshot tables) and temporal/longitudinal tracking. The computation logic exists; the versioning infrastructure doesn't.

---

### Implementation TODOs

#### Phase 1: Metrics Foundation (Low Priority) — ~40% Complete
- [x] Create `backend/app/analytics/` module structure ✅ exists
- [x] Implement `FairnessMetrics` computation (Gini coefficient) ✅ `calculate_fairness_index()`
- [x] Implement `SatisfactionMetrics` computation (preference fulfillment) ✅ `calculate_preference_satisfaction()`
- [ ] Implement `StabilityMetrics` computation (churn rate, ripple factor) — **new work**
- [ ] Create database migration for `schedule_versions`, `metric_snapshots`, `schedule_diffs`
- [ ] Add Celery task to compute metrics on schedule changes
- [ ] Wire existing metrics functions into `ScheduleMetricsComputer` service

#### Phase 2: Historical Analysis (Low Priority)
- [ ] Leverage SQLAlchemy-Continuum to reconstruct historical schedules
- [ ] Implement `compare_versions` functionality
- [ ] Build time-series query patterns for metrics
- [ ] Add pandas integration for statistical analysis

#### Phase 3: Pyomo Research Layer (Future)
- [ ] Add `pyomo` to requirements.txt
- [ ] Implement `PyomoScheduleSolver` with constraint translation
- [ ] Add model serialization/hashing for reproducibility
- [ ] Implement sensitivity analysis (dual values, reduced costs)
- [ ] Add multi-objective optimization capability

#### Phase 4: Publication Support (Future)
- [ ] Create anonymization pipeline for research export
- [ ] Implement benchmark dataset generation
- [ ] Add statistical significance testing utilities
- [ ] Create visualization exports (matplotlib/plotly for papers)

---

### Research Questions This Enables

With this framework, you could study and publish on:

1. **Fairness Dynamics**
   - How does schedule fairness evolve over an academic year?
   - Do certain interventions (swaps, leaves) systematically disadvantage certain groups?
   - Is there equity drift as accommodations accumulate?

2. **Satisfaction vs Constraint Tension**
   - What's the Pareto frontier between preference satisfaction and coverage?
   - Which preferences are most costly to honor?
   - How much does satisfaction drop when coverage is prioritized?

3. **Stability Analysis**
   - How much schedule churn is "normal" vs problematic?
   - What types of changes cascade most?
   - Can we predict destabilizing changes before they propagate?

4. **Policy Impact**
   - How did new ACGME rules affect fairness metrics?
   - What's the quantitative impact of supervision ratio changes?
   - How do different algorithms compare on fairness vs efficiency?

---

### Dependencies to Add (When Implementing)

```txt
# requirements.txt additions (future)
pyomo>=6.7.0          # Optimization modeling (research only)
highspy>=1.5.0        # HiGHS solver (free, performant)
pandas>=2.0.0         # Time series analysis
scipy>=1.11.0         # Statistical tests
matplotlib>=3.8.0     # Publication-quality figures
```

---

### Why This Matters

Most medical scheduling "quality improvement" is:
- Retrospective chart review
- Anecdotal feedback surveys
- Checkbox compliance audits
- One-time analyses that never repeat

This framework enables **continuous, quantitative, longitudinal analysis** of scheduling outcomes — the kind of evidence-based improvement that could actually change policy and be published in medical education literature.

The fact that we already have versioned assignment history (Continuum) and explainability data (`explain_json`) means we're 60% of the way there. The metrics computation layer is the missing piece.

---

## Conclusion

The project is **well-positioned for operational integration**. Core scheduling and FMIT systems are complete. The primary gaps are:

1. **Audit API routes** - Frontend ready, backend needs routes
2. **Unified visualization** - Needs plotly integration
3. **Infrastructure** - Redis + Celery deployment

**Recommended approach:** Focus on P0 items (Audit API, Heatmap) for minimum viable deployment, then iterate on P1 features.

**Future opportunity:** The longitudinal analytics framework outlined above represents genuine PI/QI potential — not checkbox compliance, but publishable research on scheduling fairness and satisfaction. This should wait until production is stable, but the architectural foundations (versioning, explainability) are already in place.

---

*Assessment generated by Claude Opus 4.5*
