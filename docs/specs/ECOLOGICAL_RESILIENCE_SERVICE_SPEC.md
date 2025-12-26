# Ecological Resilience Service - Implementation Specification

> **Version**: 1.0
> **Date**: 2025-12-26
> **Status**: Production-Ready Specification
> **Phase**: Implementation Planning
> **Tier**: 3+ (Cross-Disciplinary Analytics - Ecology Module)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Service Architecture](#service-architecture)
3. [Database Schema](#database-schema)
4. [API Endpoints](#api-endpoints)
5. [Analysis Modules](#analysis-modules)
6. [Integration Points](#integration-points)
7. [Implementation Phases](#implementation-phases)
8. [Testing Requirements](#testing-requirements)
9. [Monitoring & Alerts](#monitoring--alerts)
10. [Performance Specifications](#performance-specifications)

---

## Executive Summary

### Purpose

The **Ecological Resilience Service** applies ecological systems theory—specifically Holling's Adaptive Cycle, Panarchy, and biodiversity-stability relationships—to medical residency scheduling. This service provides early warning signals of program degradation, phase-appropriate intervention strategies, and cross-scale cascade detection.

### Key Capabilities

1. **Adaptive Cycle Tracking**: Map program state to Holling's 4-phase cycle (r, K, Ω, α)
2. **Panarchy Multi-Scale Monitoring**: Track dynamics across Individual → Team → Department → Institution
3. **Tipping Point Detection**: Identify early warning signals before regime shifts
4. **Diversity-Stability Analysis**: Quantify how faculty skill diversity buffers disruption
5. **Cross-Scale Cascade Detection**: Prevent "revolt" cascades from individual burnout to program collapse

### Technical Foundation

- **Source Domain**: Ecological resilience theory (50+ years validated)
- **Mathematical Basis**:
  - Adaptive cycle phase space (potential × connectedness × resilience)
  - Shannon & Simpson diversity indices
  - Critical slowing down detection (autocorrelation, variance)
  - Portfolio effect (community variance reduction)
- **Integration**: Extends existing Tier 3 cross-disciplinary modules

### Expected Impact

- **Proactive Intervention**: 2-4 week lead time before crisis events
- **Phase-Appropriate Strategy**: Different interventions for r/K/Ω/α phases
- **Diversity Optimization**: Evidence-based faculty hiring/cross-training
- **System-Level Monitoring**: Complements individual-level burnout metrics

---

## Service Architecture

### Component Hierarchy

```
EcologicalResilienceService
├── AdaptiveCycleTracker
│   ├── Potential Calculator (accumulated capital)
│   ├── Connectedness Analyzer (network coupling)
│   ├── Resilience Estimator (disturbance absorption)
│   └── Phase Classifier (r, K, Ω, α)
│
├── PanarchyMonitor
│   ├── Individual Scale Tracker (days-weeks)
│   ├── Team Scale Tracker (weeks-months)
│   ├── Departmental Scale Tracker (months-years)
│   ├── Institutional Scale Tracker (years-decades)
│   ├── Revolt Connection Detector (bottom-up cascade)
│   └── Remember Connection Analyzer (top-down stability)
│
├── TippingPointDetector
│   ├── Critical Slowing Down Monitor (recovery time)
│   ├── Variance Tracker (flickering detection)
│   ├── Skewness Analyzer (distribution shifts)
│   └── Multi-Signal Aggregator (confidence scoring)
│
├── DiversityAnalyzer
│   ├── Shannon Index Calculator (weighted diversity)
│   ├── Simpson Index Calculator (dominance)
│   ├── Response Diversity Analyzer (substitutability)
│   ├── Portfolio Effect Calculator (variance reduction)
│   └── Functional Diversity Mapper (role categories)
│
└── RecoveryDynamicsPredictor
    ├── Reorganization Path Analyzer (α phase)
    ├── Hysteresis Modeler (threshold asymmetry)
    └── Restoration Cost Estimator
```

### Class Structure

#### 1. Main Service Class

```python
# File: backend/app/resilience/ecological_resilience.py

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.resilience.adaptive_cycle import AdaptiveCycleTracker
from app.resilience.diversity_metrics import DiversityAnalyzer
from app.resilience.panarchy import PanarchyMonitor
from app.resilience.tipping_points import TippingPointDetector

logger = get_logger(__name__)


class AdaptiveCyclePhase(str, Enum):
    """Holling's four adaptive cycle phases."""
    EXPLOITATION = "exploitation"        # r: Growth, innovation, low capital
    CONSERVATION = "conservation"        # K: Mature, high capital, rigid
    RELEASE = "release"                  # Ω: Crisis, rapid destabilization
    REORGANIZATION = "reorganization"    # α: Renewal, experimentation
    TRANSITION = "transition"            # Between phases


class ScaleLevel(str, Enum):
    """Panarchy scale hierarchy."""
    INDIVIDUAL = "individual"      # Days-weeks (residents/faculty)
    TEAM = "team"                  # Weeks-months (rotations, call teams)
    DEPARTMENTAL = "departmental"  # Months-years (program, schedule templates)
    INSTITUTIONAL = "institutional" # Years-decades (medical center, accreditation)


class DangerLevel(str, Enum):
    """Tipping point urgency classification."""
    MONITOR = "monitor"           # Early signals, watch trends
    PREPARE = "prepare"           # Multiple signals, contingency planning
    IMMEDIATE = "immediate"       # Near threshold, intervention required


@dataclass
class AdaptiveCycleMetrics:
    """Three-dimensional position in adaptive cycle."""

    # Core dimensions (0.0-1.0)
    potential: float                    # Accumulated capital (expertise, relationships)
    connectedness: float                # System coupling strength
    resilience: float                   # Disturbance absorption capacity

    # Phase classification
    current_phase: AdaptiveCyclePhase
    phase_duration: timedelta          # How long in current phase
    phase_stability: float             # 0-1: Confidence in classification

    # Transition risk
    omega_risk: float                  # 0-1: Probability of entering Ω
    early_warning_signals: list[str] = field(default_factory=list)

    # Historical tracking
    time_since_last_omega: Optional[timedelta] = None
    previous_phase: Optional[AdaptiveCyclePhase] = None

    # Component metrics
    component_scores: dict = field(default_factory=dict)


@dataclass
class PanarchyState:
    """Multi-scale system state."""

    timestamp: datetime

    # States at each scale
    individual_phase: AdaptiveCyclePhase
    team_phase: AdaptiveCyclePhase
    departmental_phase: AdaptiveCyclePhase
    institutional_phase: AdaptiveCyclePhase

    # Cross-scale connections
    revolt_risk: float                  # 0-1: Bottom-up cascade probability
    memory_strength: float              # 0-1: Top-down stabilization

    # Synchronization detection
    synchronized_scales: list[ScaleLevel] = field(default_factory=list)
    cascade_warning: bool = False

    # Stability assessment
    overall_stability: float            # 0-1: Composite stability
    weakest_scale: ScaleLevel
    strongest_scale: ScaleLevel


@dataclass
class TippingPointAlert:
    """Early warning signal for approaching regime shift."""

    metric_name: str
    current_value: float
    threshold_estimate: float
    distance_to_threshold: float       # 0-1, lower = closer

    # Early warning signals detected
    critical_slowing: bool
    increased_variance: bool
    skewness_shift: bool

    # Confidence and urgency
    confidence: float                   # 0-1
    urgency: DangerLevel

    # Intervention guidance
    intervention: str
    reversibility: str                  # "reversible", "limited_window", "irreversible"
    estimated_time_to_threshold: Optional[timedelta] = None

    # Context
    detected_at: datetime = field(default_factory=datetime.utcnow)
    historical_trend: Optional[dict] = None


@dataclass
class DiversityMetrics:
    """Biodiversity-inspired faculty diversity metrics."""

    # Basic diversity indices
    species_richness: int              # Total unique skills/specialties
    shannon_index: float               # Weighted diversity (1.5-3.5 typical)
    simpson_index: float               # Probability of different skills (0-1)
    evenness: float                    # Distribution uniformity (0-1)

    # Functional diversity
    functional_richness: int           # Number of functional groups
    response_diversity: float          # Avg substitutes per specialty

    # Stability prediction
    portfolio_effect: float            # Variance reduction from diversity (>1 = stabilizing)
    stability_score: float             # 0-1: Composite stability prediction

    # Risk assessment
    low_diversity_alerts: list[str] = field(default_factory=list)
    monoculture_risks: dict = field(default_factory=dict)
    single_point_failures: list[dict] = field(default_factory=list)


@dataclass
class EcologicalResilienceReport:
    """Comprehensive ecological resilience assessment."""

    timestamp: datetime

    # Adaptive cycle state
    adaptive_cycle: AdaptiveCycleMetrics

    # Panarchy (multi-scale)
    panarchy: PanarchyState

    # Tipping points
    tipping_point_alerts: list[TippingPointAlert] = field(default_factory=list)

    # Diversity
    diversity: DiversityMetrics

    # Overall assessment
    overall_risk: str                   # "low", "moderate", "high", "critical"
    priority_interventions: list[str] = field(default_factory=list)

    # Integration with existing framework
    defense_level_recommendation: Optional[str] = None
    spc_integration: Optional[dict] = None
    fire_index_integration: Optional[dict] = None


class EcologicalResilienceService:
    """
    Main service orchestrating ecological resilience analysis.

    Integrates:
    - Adaptive cycle tracking
    - Panarchy multi-scale monitoring
    - Tipping point detection
    - Diversity-stability analysis
    """

    def __init__(
        self,
        db: Session,
        adaptive_cycle_tracker: Optional[AdaptiveCycleTracker] = None,
        panarchy_monitor: Optional[PanarchyMonitor] = None,
        tipping_point_detector: Optional[TippingPointDetector] = None,
        diversity_analyzer: Optional[DiversityAnalyzer] = None
    ):
        """Initialize service with dependency injection."""
        self.db = db
        self.adaptive_cycle = adaptive_cycle_tracker or AdaptiveCycleTracker(db)
        self.panarchy = panarchy_monitor or PanarchyMonitor(db)
        self.tipping_points = tipping_point_detector or TippingPointDetector(db)
        self.diversity = diversity_analyzer or DiversityAnalyzer(db)

        self.logger = get_logger(__name__)

    async def analyze_system_resilience(
        self,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None
    ) -> EcologicalResilienceReport:
        """
        Comprehensive ecological resilience analysis.

        Args:
            period_start: Analysis start date (default: 90 days ago)
            period_end: Analysis end date (default: now)

        Returns:
            Complete ecological resilience assessment
        """
        self.logger.info("Starting ecological resilience analysis")

        # Default to 90-day lookback
        if period_end is None:
            period_end = datetime.utcnow()
        if period_start is None:
            period_start = period_end - timedelta(days=90)

        # Run all analyses in parallel (async)
        adaptive_cycle_task = self.adaptive_cycle.calculate_current_state(
            period_start, period_end
        )
        panarchy_task = self.panarchy.analyze_cross_scale_state(
            period_start, period_end
        )
        tipping_points_task = self.tipping_points.detect_all_signals(
            period_start, period_end
        )
        diversity_task = self.diversity.calculate_comprehensive_metrics()

        # Await results
        adaptive_cycle_metrics = await adaptive_cycle_task
        panarchy_state = await panarchy_task
        tipping_alerts = await tipping_points_task
        diversity_metrics = await diversity_task

        # Aggregate overall risk
        overall_risk = self._calculate_overall_risk(
            adaptive_cycle_metrics,
            panarchy_state,
            tipping_alerts,
            diversity_metrics
        )

        # Generate priority interventions
        interventions = self._generate_interventions(
            adaptive_cycle_metrics,
            panarchy_state,
            tipping_alerts,
            diversity_metrics
        )

        # Integration recommendations
        defense_level = self._map_to_defense_level(overall_risk, adaptive_cycle_metrics)

        report = EcologicalResilienceReport(
            timestamp=datetime.utcnow(),
            adaptive_cycle=adaptive_cycle_metrics,
            panarchy=panarchy_state,
            tipping_point_alerts=tipping_alerts,
            diversity=diversity_metrics,
            overall_risk=overall_risk,
            priority_interventions=interventions,
            defense_level_recommendation=defense_level
        )

        # Persist to database
        await self._persist_report(report)

        self.logger.info(
            f"Ecological resilience analysis complete: "
            f"Phase={adaptive_cycle_metrics.current_phase.value}, "
            f"Risk={overall_risk}, "
            f"Alerts={len(tipping_alerts)}"
        )

        return report

    def _calculate_overall_risk(
        self,
        adaptive_cycle: AdaptiveCycleMetrics,
        panarchy: PanarchyState,
        alerts: list[TippingPointAlert],
        diversity: DiversityMetrics
    ) -> str:
        """Calculate composite risk level."""
        risk_score = 0.0

        # Adaptive cycle contribution
        if adaptive_cycle.current_phase == AdaptiveCyclePhase.RELEASE:
            risk_score += 3.0  # Crisis phase
        elif adaptive_cycle.current_phase == AdaptiveCyclePhase.CONSERVATION:
            risk_score += 2.0 * adaptive_cycle.omega_risk  # K phase with high Ω risk
        elif adaptive_cycle.current_phase == AdaptiveCyclePhase.REORGANIZATION:
            risk_score += 1.5  # Uncertain reorganization

        # Panarchy contribution
        if panarchy.cascade_warning:
            risk_score += 2.0
        risk_score += (1.0 - panarchy.overall_stability) * 2.0

        # Tipping point contribution
        immediate_alerts = [a for a in alerts if a.urgency == DangerLevel.IMMEDIATE]
        prepare_alerts = [a for a in alerts if a.urgency == DangerLevel.PREPARE]
        risk_score += len(immediate_alerts) * 1.5
        risk_score += len(prepare_alerts) * 0.5

        # Diversity contribution
        risk_score += (1.0 - diversity.stability_score) * 1.5

        # Map to categorical risk
        if risk_score < 2.0:
            return "low"
        elif risk_score < 4.0:
            return "moderate"
        elif risk_score < 6.0:
            return "high"
        else:
            return "critical"

    def _generate_interventions(
        self,
        adaptive_cycle: AdaptiveCycleMetrics,
        panarchy: PanarchyState,
        alerts: list[TippingPointAlert],
        diversity: DiversityMetrics
    ) -> list[str]:
        """Generate phase-appropriate intervention recommendations."""
        interventions = []

        # Phase-specific interventions
        if adaptive_cycle.current_phase == AdaptiveCyclePhase.CONSERVATION:
            if adaptive_cycle.omega_risk > 0.7:
                interventions.append(
                    "K→Ω CRITICAL: Proactively trigger reorganization before crisis. "
                    "Reduce connectedness through workload distribution, increase buffer capacity."
                )
            elif adaptive_cycle.omega_risk > 0.5:
                interventions.append(
                    "K phase high Ω risk: Increase resilience buffer. "
                    "Reduce utilization below 80%, cross-train faculty, diversify specialties."
                )

        elif adaptive_cycle.current_phase == AdaptiveCyclePhase.RELEASE:
            interventions.append(
                "Ω ACTIVE: Crisis management protocols. Activate fallback schedules, "
                "essential services only, prepare for α reorganization."
            )

        elif adaptive_cycle.current_phase == AdaptiveCyclePhase.REORGANIZATION:
            interventions.append(
                "α phase: Support experimentation. Pilot new templates, gather feedback, "
                "track convergence to stable r phase. Avoid premature rigidity."
            )

        # Panarchy interventions
        if panarchy.cascade_warning:
            interventions.append(
                f"CASCADE WARNING: {len(panarchy.synchronized_scales)} scales entering Ω. "
                f"Strengthen {panarchy.weakest_scale.value} scale to prevent propagation."
            )

        if panarchy.revolt_risk > 0.6:
            interventions.append(
                "High revolt risk: Individual→Team cascade likely. "
                "Intervene at team scale before individual Ω events propagate upward."
            )

        if panarchy.memory_strength < 0.4:
            interventions.append(
                "Weak institutional memory: Strengthen policies, document decisions, "
                "ensure leadership continuity. Low memory = high volatility."
            )

        # Tipping point interventions
        for alert in alerts:
            if alert.urgency == DangerLevel.IMMEDIATE:
                interventions.append(f"IMMEDIATE: {alert.intervention}")

        # Diversity interventions
        if diversity.stability_score < 0.5:
            interventions.append(
                f"Low diversity (stability={diversity.stability_score:.2f}): "
                f"Recruit diverse specialties, cross-train faculty. "
                f"Current Shannon index={diversity.shannon_index:.2f} (target >2.5)."
            )

        for spof in diversity.single_point_failures:
            interventions.append(
                f"Single point of failure: {spof['specialty']} covered by only "
                f"{spof['faculty_count']} faculty. Cross-train backups immediately."
            )

        return interventions

    def _map_to_defense_level(
        self,
        overall_risk: str,
        adaptive_cycle: AdaptiveCycleMetrics
    ) -> str:
        """Map ecological risk to Defense-in-Depth levels."""
        # Ω phase = RED/BLACK
        if adaptive_cycle.current_phase == AdaptiveCyclePhase.RELEASE:
            return "RED"

        # Risk-based mapping
        risk_to_defense = {
            "low": "GREEN",
            "moderate": "YELLOW",
            "high": "ORANGE",
            "critical": "RED"
        }

        return risk_to_defense.get(overall_risk, "YELLOW")

    async def _persist_report(self, report: EcologicalResilienceReport):
        """Persist report to database."""
        # Import models here to avoid circular imports
        from app.models.resilience import (
            CyclePhaseHistory,
            DiversitySnapshot,
            TippingPointAlertRecord
        )

        # Save adaptive cycle history
        cycle_record = CyclePhaseHistory(
            phase=report.adaptive_cycle.current_phase.value,
            potential=report.adaptive_cycle.potential,
            connectedness=report.adaptive_cycle.connectedness,
            resilience=report.adaptive_cycle.resilience,
            omega_risk=report.adaptive_cycle.omega_risk,
            component_scores=report.adaptive_cycle.component_scores
        )
        self.db.add(cycle_record)

        # Save diversity snapshot
        diversity_record = DiversitySnapshot(
            shannon_index=report.diversity.shannon_index,
            simpson_index=report.diversity.simpson_index,
            response_diversity=report.diversity.response_diversity,
            stability_score=report.diversity.stability_score,
            functional_richness=report.diversity.functional_richness
        )
        self.db.add(diversity_record)

        # Save tipping point alerts
        for alert in report.tipping_point_alerts:
            alert_record = TippingPointAlertRecord(
                metric_name=alert.metric_name,
                current_value=alert.current_value,
                threshold_estimate=alert.threshold_estimate,
                distance_to_threshold=alert.distance_to_threshold,
                critical_slowing=alert.critical_slowing,
                increased_variance=alert.increased_variance,
                skewness_shift=alert.skewness_shift,
                confidence=alert.confidence,
                urgency=alert.urgency.value,
                intervention=alert.intervention,
                reversibility=alert.reversibility
            )
            self.db.add(alert_record)

        await self.db.commit()
```

#### 2. Adaptive Cycle Tracker

```python
# File: backend/app/resilience/adaptive_cycle.py

import statistics
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models import Assignment, Person, Block
from app.resilience.ecological_resilience import (
    AdaptiveCycleMetrics,
    AdaptiveCyclePhase
)

logger = get_logger(__name__)


class AdaptiveCycleTracker:
    """
    Calculate residency program position in Holling's adaptive cycle.

    Tracks three dimensions:
    - Potential: Accumulated capital (expertise, relationships, protocols)
    - Connectedness: System coupling strength (dependencies, rigidity)
    - Resilience: Disturbance absorption capacity (flexibility, diversity)
    """

    def __init__(self, db: Session):
        self.db = db
        self.logger = get_logger(__name__)

    async def calculate_current_state(
        self,
        period_start: datetime,
        period_end: datetime
    ) -> AdaptiveCycleMetrics:
        """Calculate current position in adaptive cycle."""

        # Calculate three core dimensions
        potential = await self._calculate_potential(period_start, period_end)
        connectedness = await self._calculate_connectedness(period_start, period_end)
        resilience = await self._calculate_resilience(period_start, period_end)

        # Classify phase
        current_phase = self._classify_phase(potential, connectedness, resilience)

        # Calculate Ω risk (for K phase)
        omega_risk = self._calculate_omega_risk(
            potential, connectedness, resilience, current_phase
        )

        # Detect early warning signals
        warnings = await self._detect_early_warnings(period_start, period_end)

        # Historical context
        previous_state = await self._get_previous_state()
        phase_duration = await self._calculate_phase_duration(current_phase)
        time_since_omega = await self._time_since_last_omega()

        # Phase stability (confidence)
        stability = self._calculate_phase_stability(
            potential, connectedness, resilience, current_phase
        )

        return AdaptiveCycleMetrics(
            potential=potential,
            connectedness=connectedness,
            resilience=resilience,
            current_phase=current_phase,
            phase_duration=phase_duration,
            phase_stability=stability,
            omega_risk=omega_risk,
            early_warning_signals=warnings,
            time_since_last_omega=time_since_omega,
            previous_phase=previous_state.current_phase if previous_state else None,
            component_scores={
                "potential": potential,
                "connectedness": connectedness,
                "resilience": resilience
            }
        )

    async def _calculate_potential(
        self,
        period_start: datetime,
        period_end: datetime
    ) -> float:
        """
        Calculate accumulated capital (0.0-1.0).

        Components:
        - Resident procedure counts (competency progress)
        - Faculty-resident mentorship stability
        - Schedule template maturity
        - Protocol documentation completeness
        """
        scores = []

        # 1. Competency progress (procedure counts)
        # Query procedure counts per resident
        # High counts = high potential
        # Normalize to 0-1 (e.g., 100+ procedures = 1.0)
        competency_score = 0.0  # TODO: Implement from procedure_credential model
        scores.append(competency_score)

        # 2. Mentorship stability
        # Query assignment stability (same faculty-resident pairings)
        # High stability = high potential
        stability_query = select(Assignment).where(
            Assignment.block_id.in_(
                select(Block.id).where(
                    Block.date >= period_start.date(),
                    Block.date <= period_end.date()
                )
            )
        )
        assignments = (await self.db.execute(stability_query)).scalars().all()

        # Calculate pairing stability (simplified)
        if len(assignments) > 0:
            unique_pairings = len(set(
                (a.person_id, a.rotation_template_id) for a in assignments
            ))
            mentorship_score = min(1.0, unique_pairings / 50.0)  # 50+ = stable
            scores.append(mentorship_score)

        # 3. Schedule template maturity
        # Days since last major schedule change
        # More mature = higher potential
        template_maturity = 0.7  # Placeholder (would query schedule_run model)
        scores.append(template_maturity)

        # 4. Documentation completeness
        # Count of documented protocols, policies
        documentation_score = 0.6  # Placeholder
        scores.append(documentation_score)

        # Average all components
        potential = statistics.mean(scores) if scores else 0.5
        return max(0.0, min(1.0, potential))

    async def _calculate_connectedness(
        self,
        period_start: datetime,
        period_end: datetime
    ) -> float:
        """
        Calculate system coupling strength (0.0-1.0).

        Components:
        - Network density (how interconnected)
        - Faculty substitutability (inverse of Herfindahl index)
        - Cross-coverage dependencies
        - Single points of failure
        """
        scores = []

        # 1. Network density
        # High density = high connectedness = rigid
        # Would use NetworkX to calculate from assignment graph
        network_density = 0.5  # Placeholder
        scores.append(network_density)

        # 2. Faculty substitutability
        # Low substitutability = high connectedness
        # Herfindahl index: Σ(market_share²)
        # High HHI = concentrated = rigid
        faculty_query = select(Person).where(Person.role == "FACULTY")
        faculty = (await self.db.execute(faculty_query)).scalars().all()

        if len(faculty) > 1:
            # Equal distribution = low connectedness
            # Concentrated = high connectedness
            equal_share = 1.0 / len(faculty)
            hhi = len(faculty) * (equal_share ** 2)  # Min HHI (uniform)
            max_hhi = 1.0  # All in one person
            # Normalize: 0 = perfectly distributed, 1 = monopoly
            substitutability_score = hhi / max_hhi
            scores.append(substitutability_score)

        # 3. Cross-coverage dependencies
        # Count of assignments requiring specific faculty
        dependency_score = 0.6  # Placeholder
        scores.append(dependency_score)

        # 4. Single points of failure (inverse)
        # Fewer SPOFs = lower connectedness
        spof_count = 3  # Placeholder (from hub_analysis)
        spof_score = min(1.0, spof_count / 10.0)  # 10+ SPOFs = max
        scores.append(spof_score)

        connectedness = statistics.mean(scores) if scores else 0.5
        return max(0.0, min(1.0, connectedness))

    async def _calculate_resilience(
        self,
        period_start: datetime,
        period_end: datetime
    ) -> float:
        """
        Calculate disturbance absorption capacity (0.0-1.0).

        Components:
        - Utilization buffer (1 - utilization_rate)
        - N-1/N-2 contingency pass rate
        - Diversity indices (Shannon, Simpson)
        - Response diversity (coverage redundancy)
        """
        scores = []

        # 1. Utilization buffer
        # Low utilization = high resilience
        utilization_rate = 0.65  # Placeholder (from utilization monitor)
        buffer_score = 1.0 - utilization_rate
        scores.append(buffer_score)

        # 2. Contingency pass rate
        # Pass N-1 and N-2 = high resilience
        n1_pass = True  # Placeholder (from contingency analyzer)
        n2_pass = False
        contingency_score = (1.0 if n1_pass else 0.0) + (1.0 if n2_pass else 0.0)
        contingency_score /= 2.0  # Normalize
        scores.append(contingency_score)

        # 3. Diversity indices
        # High diversity = high resilience
        shannon_index = 2.3  # Placeholder (from diversity analyzer)
        # Shannon typically 1.5-3.5, normalize
        diversity_score = min(1.0, shannon_index / 3.5)
        scores.append(diversity_score)

        # 4. Response diversity
        # Multiple ways to cover each service = high resilience
        response_diversity = 2.5  # Placeholder (avg substitutes per specialty)
        response_score = min(1.0, response_diversity / 5.0)  # 5+ = excellent
        scores.append(response_score)

        resilience = statistics.mean(scores) if scores else 0.5
        return max(0.0, min(1.0, resilience))

    def _classify_phase(
        self,
        potential: float,
        connectedness: float,
        resilience: float
    ) -> AdaptiveCyclePhase:
        """
        Classify adaptive cycle phase based on three dimensions.

        Phase mapping:
        - r (Exploitation): Low P, Low C, High R → Growth
        - K (Conservation): High P, High C, Low R → Mature/Rigid
        - Ω (Release): Low P, Low C, Low R → Crisis
        - α (Reorganization): Low P, Low C, Mid-High R → Renewal
        """

        # Thresholds
        HIGH = 0.7
        LOW = 0.3

        # K: High potential AND high connectedness
        if potential > HIGH and connectedness > HIGH:
            return AdaptiveCyclePhase.CONSERVATION

        # Ω: Low potential AND low connectedness AND low resilience
        elif potential < LOW and connectedness < LOW and resilience < 0.4:
            return AdaptiveCyclePhase.RELEASE

        # α: Low potential AND low connectedness BUT moderate+ resilience
        elif potential < LOW and connectedness < LOW and resilience >= 0.4:
            return AdaptiveCyclePhase.REORGANIZATION

        # r: Growing potential, moderate connectedness, good resilience
        elif potential < HIGH and resilience > 0.5:
            return AdaptiveCyclePhase.EXPLOITATION

        # Transition state
        else:
            return AdaptiveCyclePhase.TRANSITION

    def _calculate_omega_risk(
        self,
        potential: float,
        connectedness: float,
        resilience: float,
        phase: AdaptiveCyclePhase
    ) -> float:
        """
        Calculate risk of transitioning to Ω (release/crisis).

        Highest risk in K phase with:
        - Very high connectedness (rigidity)
        - Very low resilience (brittle)
        - External stressors present
        """
        if phase != AdaptiveCyclePhase.CONSERVATION:
            # Only K phase has significant Ω risk
            return 0.0

        # Risk components
        rigidity_risk = connectedness  # Higher connectedness = higher risk
        brittleness_risk = 1.0 - resilience  # Lower resilience = higher risk

        # Combine (weighted)
        omega_risk = (rigidity_risk * 0.6) + (brittleness_risk * 0.4)

        return max(0.0, min(1.0, omega_risk))

    async def _detect_early_warnings(
        self,
        period_start: datetime,
        period_end: datetime
    ) -> list[str]:
        """Detect early warning signals of approaching Ω transition."""
        warnings = []

        # Would integrate with tipping_point_detector for:
        # - Critical slowing down
        # - Increased variance
        # - Decreased resilience

        # Placeholder
        return warnings

    async def _get_previous_state(self) -> Optional[AdaptiveCycleMetrics]:
        """Retrieve last adaptive cycle state from database."""
        # Query CyclePhaseHistory model
        # Return most recent record
        return None  # Placeholder

    async def _calculate_phase_duration(
        self,
        current_phase: AdaptiveCyclePhase
    ) -> timedelta:
        """Calculate how long system has been in current phase."""
        # Query CyclePhaseHistory for phase changes
        # Count days since last transition
        return timedelta(days=30)  # Placeholder

    async def _time_since_last_omega(self) -> Optional[timedelta]:
        """Calculate time since last Ω (crisis) event."""
        # Query CyclePhaseHistory for last RELEASE phase
        return timedelta(days=180)  # Placeholder

    def _calculate_phase_stability(
        self,
        potential: float,
        connectedness: float,
        resilience: float,
        phase: AdaptiveCyclePhase
    ) -> float:
        """
        Calculate confidence in phase classification (0.0-1.0).

        Higher stability = clearer phase boundaries.
        Lower stability = near phase transition.
        """
        # Distance from phase boundaries
        # Clear K: P>0.8, C>0.8 → high stability
        # Near boundary: P≈0.7, C≈0.7 → low stability

        if phase == AdaptiveCyclePhase.CONSERVATION:
            # How far from K→Ω boundary?
            k_strength = min(potential, connectedness)
            return k_strength  # 0.9 = very K, 0.7 = borderline

        elif phase == AdaptiveCyclePhase.RELEASE:
            # In crisis, stability is low by definition
            return 0.3

        elif phase == AdaptiveCyclePhase.REORGANIZATION:
            # α phase is inherently uncertain
            return 0.5

        elif phase == AdaptiveCyclePhase.EXPLOITATION:
            # r phase: growing but not yet mature
            return 0.7

        else:  # TRANSITION
            return 0.4  # Low confidence in transitional states
```

---

## Database Schema

### New Models

Add to `/backend/app/models/resilience.py`:

```python
# Ecological Resilience Models

class CyclePhaseHistory(Base):
    """
    Historical tracking of adaptive cycle phases.

    Records program position in Holling's adaptive cycle over time.
    """

    __tablename__ = "cycle_phase_history"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Adaptive cycle position
    phase = Column(
        String(30), nullable=False
    )  # exploitation, conservation, release, reorganization
    potential = Column(Float, nullable=False)  # 0-1: Accumulated capital
    connectedness = Column(Float, nullable=False)  # 0-1: System coupling
    resilience = Column(Float, nullable=False)  # 0-1: Disturbance absorption

    # Risk assessment
    omega_risk = Column(Float, default=0.0)  # 0-1: Probability of crisis
    early_warning_count = Column(Integer, default=0)

    # Phase metadata
    phase_duration_days = Column(Integer)  # Days in current phase
    phase_stability = Column(Float)  # 0-1: Classification confidence

    # Component scores (detailed breakdown)
    component_scores = Column(JSONType())

    def __repr__(self):
        return f"<CyclePhaseHistory(phase='{self.phase}', P={self.potential:.2f}, C={self.connectedness:.2f}, R={self.resilience:.2f})>"


class PanarchyStateRecord(Base):
    """
    Multi-scale system state (panarchy hierarchy).

    Tracks adaptive cycle phases across four nested scales:
    Individual → Team → Department → Institution
    """

    __tablename__ = "panarchy_states"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Phases at each scale
    individual_phase = Column(String(30), nullable=False)
    team_phase = Column(String(30), nullable=False)
    departmental_phase = Column(String(30), nullable=False)
    institutional_phase = Column(String(30), nullable=False)

    # Cross-scale connections
    revolt_risk = Column(Float, default=0.0)  # 0-1: Bottom-up cascade
    memory_strength = Column(Float, default=0.0)  # 0-1: Top-down stability

    # Synchronization
    synchronized_scales = Column(StringArrayType())  # Scales in same phase
    cascade_warning = Column(Boolean, default=False)

    # Stability
    overall_stability = Column(Float)  # 0-1: Composite
    weakest_scale = Column(String(30))  # individual, team, etc.
    strongest_scale = Column(String(30))

    def __repr__(self):
        return (
            f"<PanarchyStateRecord("
            f"I={self.individual_phase}, T={self.team_phase}, "
            f"D={self.departmental_phase}, Inst={self.institutional_phase})>"
        )


class DiversitySnapshot(Base):
    """
    Faculty skill diversity metrics snapshot.

    Biodiversity-inspired indices for faculty composition.
    """

    __tablename__ = "diversity_snapshots"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    calculated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Basic diversity indices
    species_richness = Column(Integer, nullable=False)  # Unique skills count
    shannon_index = Column(Float, nullable=False)  # 1.5-3.5 typical
    simpson_index = Column(Float, nullable=False)  # 0-1
    evenness = Column(Float, nullable=False)  # 0-1: Distribution uniformity

    # Functional diversity
    functional_richness = Column(Integer, nullable=False)  # Functional groups
    response_diversity = Column(Float, nullable=False)  # Avg substitutes

    # Stability metrics
    portfolio_effect = Column(Float, nullable=False)  # >1 = stabilizing
    stability_score = Column(Float, nullable=False)  # 0-1: Composite

    # Risk flags
    low_diversity_alert = Column(Boolean, default=False)
    monoculture_risk = Column(Boolean, default=False)
    single_point_failure_count = Column(Integer, default=0)

    # Detailed breakdown
    skill_distribution = Column(JSONType())  # {skill: count}
    specialty_coverage = Column(JSONType())  # {specialty: [faculty_ids]}

    def __repr__(self):
        return (
            f"<DiversitySnapshot("
            f"Shannon={self.shannon_index:.2f}, "
            f"Simpson={self.simpson_index:.2f}, "
            f"Stability={self.stability_score:.2f})>"
        )


class TippingPointAlertRecord(Base):
    """
    Early warning alerts for approaching regime shifts.

    Records tipping point detection events.
    """

    __tablename__ = "tipping_point_alerts"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    detected_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Metric being monitored
    metric_name = Column(String(100), nullable=False)
    current_value = Column(Float, nullable=False)
    threshold_estimate = Column(Float, nullable=False)
    distance_to_threshold = Column(Float, nullable=False)  # 0-1

    # Early warning signals
    critical_slowing = Column(Boolean, default=False)
    increased_variance = Column(Boolean, default=False)
    skewness_shift = Column(Boolean, default=False)

    # Assessment
    confidence = Column(Float, nullable=False)  # 0-1
    urgency = Column(
        String(20), nullable=False
    )  # monitor, prepare, immediate

    # Guidance
    intervention = Column(String(1000), nullable=False)
    reversibility = Column(
        String(30), nullable=False
    )  # reversible, limited_window, irreversible
    estimated_time_to_threshold_days = Column(Integer)

    # Historical trend
    historical_trend = Column(JSONType())

    # Resolution
    resolved_at = Column(DateTime)
    resolution_action = Column(String(500))
    was_prevented = Column(Boolean)

    def __repr__(self):
        return (
            f"<TippingPointAlert("
            f"metric='{self.metric_name}', "
            f"urgency='{self.urgency}', "
            f"confidence={self.confidence:.2f})>"
        )

    @property
    def is_active(self) -> bool:
        """Check if alert is still active."""
        return self.resolved_at is None


class RecoveryPathRecord(Base):
    """
    Reorganization (α phase) recovery path tracking.

    Records experimental schedule templates and convergence progress.
    """

    __tablename__ = "recovery_paths"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Recovery context
    crisis_event_id = Column(GUID())  # Related ResilienceEvent
    from_phase = Column(String(30), nullable=False)  # Usually "release" (Ω)
    to_phase_target = Column(String(30), nullable=False)  # Usually "exploitation" (r)

    # Experimental templates tried
    templates_tested = Column(Integer, default=0)
    successful_templates = Column(Integer, default=0)
    failed_templates = Column(Integer, default=0)

    # Convergence metrics
    coverage_rate = Column(Float)  # Current coverage
    target_coverage = Column(Float, default=0.85)  # Goal
    resident_acceptance = Column(Float)  # 0-1: Survey results
    faculty_acceptance = Column(Float)  # 0-1: Survey results
    acgme_compliance = Column(Boolean, default=True)

    # Progress
    convergence_score = Column(Float)  # 0-1: How close to stable r
    is_converged = Column(Boolean, default=False)

    # Completion
    completed_at = Column(DateTime)
    final_phase_reached = Column(String(30))
    success = Column(Boolean)  # True = reached r, False = stuck in α

    def __repr__(self):
        return (
            f"<RecoveryPathRecord("
            f"templates={self.templates_tested}, "
            f"convergence={self.convergence_score:.2f}, "
            f"converged={self.is_converged})>"
        )
```

### Alembic Migration

```python
# File: backend/alembic/versions/XXXX_add_ecological_resilience.py

"""Add ecological resilience models

Revision ID: XXXX
Revises: YYYY
Create Date: 2025-12-26
"""

from alembic import op
import sqlalchemy as sa
from app.db.types import GUID, JSONType, StringArrayType


revision = 'XXXX'
down_revision = 'YYYY'  # Latest migration
branch_labels = None
depends_on = None


def upgrade():
    # Create cycle_phase_history table
    op.create_table(
        'cycle_phase_history',
        sa.Column('id', GUID(), primary_key=True),
        sa.Column('timestamp', sa.DateTime, nullable=False),
        sa.Column('phase', sa.String(30), nullable=False),
        sa.Column('potential', sa.Float, nullable=False),
        sa.Column('connectedness', sa.Float, nullable=False),
        sa.Column('resilience', sa.Float, nullable=False),
        sa.Column('omega_risk', sa.Float, default=0.0),
        sa.Column('early_warning_count', sa.Integer, default=0),
        sa.Column('phase_duration_days', sa.Integer),
        sa.Column('phase_stability', sa.Float),
        sa.Column('component_scores', JSONType()),
    )

    # Create index on timestamp for efficient queries
    op.create_index(
        'ix_cycle_phase_history_timestamp',
        'cycle_phase_history',
        ['timestamp'],
        unique=False
    )

    # Create panarchy_states table
    op.create_table(
        'panarchy_states',
        sa.Column('id', GUID(), primary_key=True),
        sa.Column('timestamp', sa.DateTime, nullable=False),
        sa.Column('individual_phase', sa.String(30), nullable=False),
        sa.Column('team_phase', sa.String(30), nullable=False),
        sa.Column('departmental_phase', sa.String(30), nullable=False),
        sa.Column('institutional_phase', sa.String(30), nullable=False),
        sa.Column('revolt_risk', sa.Float, default=0.0),
        sa.Column('memory_strength', sa.Float, default=0.0),
        sa.Column('synchronized_scales', StringArrayType()),
        sa.Column('cascade_warning', sa.Boolean, default=False),
        sa.Column('overall_stability', sa.Float),
        sa.Column('weakest_scale', sa.String(30)),
        sa.Column('strongest_scale', sa.String(30)),
    )

    op.create_index(
        'ix_panarchy_states_timestamp',
        'panarchy_states',
        ['timestamp'],
        unique=False
    )

    # Create diversity_snapshots table
    op.create_table(
        'diversity_snapshots',
        sa.Column('id', GUID(), primary_key=True),
        sa.Column('calculated_at', sa.DateTime, nullable=False),
        sa.Column('species_richness', sa.Integer, nullable=False),
        sa.Column('shannon_index', sa.Float, nullable=False),
        sa.Column('simpson_index', sa.Float, nullable=False),
        sa.Column('evenness', sa.Float, nullable=False),
        sa.Column('functional_richness', sa.Integer, nullable=False),
        sa.Column('response_diversity', sa.Float, nullable=False),
        sa.Column('portfolio_effect', sa.Float, nullable=False),
        sa.Column('stability_score', sa.Float, nullable=False),
        sa.Column('low_diversity_alert', sa.Boolean, default=False),
        sa.Column('monoculture_risk', sa.Boolean, default=False),
        sa.Column('single_point_failure_count', sa.Integer, default=0),
        sa.Column('skill_distribution', JSONType()),
        sa.Column('specialty_coverage', JSONType()),
    )

    op.create_index(
        'ix_diversity_snapshots_calculated_at',
        'diversity_snapshots',
        ['calculated_at'],
        unique=False
    )

    # Create tipping_point_alerts table
    op.create_table(
        'tipping_point_alerts',
        sa.Column('id', GUID(), primary_key=True),
        sa.Column('detected_at', sa.DateTime, nullable=False),
        sa.Column('metric_name', sa.String(100), nullable=False),
        sa.Column('current_value', sa.Float, nullable=False),
        sa.Column('threshold_estimate', sa.Float, nullable=False),
        sa.Column('distance_to_threshold', sa.Float, nullable=False),
        sa.Column('critical_slowing', sa.Boolean, default=False),
        sa.Column('increased_variance', sa.Boolean, default=False),
        sa.Column('skewness_shift', sa.Boolean, default=False),
        sa.Column('confidence', sa.Float, nullable=False),
        sa.Column('urgency', sa.String(20), nullable=False),
        sa.Column('intervention', sa.String(1000), nullable=False),
        sa.Column('reversibility', sa.String(30), nullable=False),
        sa.Column('estimated_time_to_threshold_days', sa.Integer),
        sa.Column('historical_trend', JSONType()),
        sa.Column('resolved_at', sa.DateTime),
        sa.Column('resolution_action', sa.String(500)),
        sa.Column('was_prevented', sa.Boolean),
    )

    op.create_index(
        'ix_tipping_point_alerts_detected_at',
        'tipping_point_alerts',
        ['detected_at'],
        unique=False
    )

    # Create recovery_paths table
    op.create_table(
        'recovery_paths',
        sa.Column('id', GUID(), primary_key=True),
        sa.Column('started_at', sa.DateTime, nullable=False),
        sa.Column('crisis_event_id', GUID()),
        sa.Column('from_phase', sa.String(30), nullable=False),
        sa.Column('to_phase_target', sa.String(30), nullable=False),
        sa.Column('templates_tested', sa.Integer, default=0),
        sa.Column('successful_templates', sa.Integer, default=0),
        sa.Column('failed_templates', sa.Integer, default=0),
        sa.Column('coverage_rate', sa.Float),
        sa.Column('target_coverage', sa.Float, default=0.85),
        sa.Column('resident_acceptance', sa.Float),
        sa.Column('faculty_acceptance', sa.Float),
        sa.Column('acgme_compliance', sa.Boolean, default=True),
        sa.Column('convergence_score', sa.Float),
        sa.Column('is_converged', sa.Boolean, default=False),
        sa.Column('completed_at', sa.DateTime),
        sa.Column('final_phase_reached', sa.String(30)),
        sa.Column('success', sa.Boolean),
    )

    op.create_index(
        'ix_recovery_paths_started_at',
        'recovery_paths',
        ['started_at'],
        unique=False
    )


def downgrade():
    op.drop_index('ix_recovery_paths_started_at')
    op.drop_table('recovery_paths')

    op.drop_index('ix_tipping_point_alerts_detected_at')
    op.drop_table('tipping_point_alerts')

    op.drop_index('ix_diversity_snapshots_calculated_at')
    op.drop_table('diversity_snapshots')

    op.drop_index('ix_panarchy_states_timestamp')
    op.drop_table('panarchy_states')

    op.drop_index('ix_cycle_phase_history_timestamp')
    op.drop_table('cycle_phase_history')
```

---

## API Endpoints

### Route Definition

Add to `/backend/app/api/routes/resilience.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional

from app.api import deps
from app.resilience.ecological_resilience import EcologicalResilienceService
from app.schemas.ecological_resilience import (
    AdaptiveCycleResponse,
    PanarchyStateResponse,
    TippingPointAlertResponse,
    DiversityMetricsResponse,
    EcologicalResilienceReportResponse
)

router = APIRouter(prefix="/api/v1/ecology", tags=["Ecological Resilience"])


@router.get("/adaptive-cycle", response_model=AdaptiveCycleResponse)
async def get_adaptive_cycle_state(
    period_days: int = Query(90, ge=1, le=365, description="Analysis period in days"),
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """
    Get current adaptive cycle phase and metrics.

    Returns program position in Holling's adaptive cycle:
    - **r (Exploitation)**: Growth phase, innovation, low capital
    - **K (Conservation)**: Mature phase, high capital, rigid structure
    - **Ω (Release)**: Crisis phase, rapid destabilization
    - **α (Reorganization)**: Renewal phase, experimentation

    **Metrics:**
    - Potential: Accumulated capital (expertise, relationships)
    - Connectedness: System coupling strength
    - Resilience: Disturbance absorption capacity
    - Omega Risk: Probability of entering crisis (K→Ω)

    **Use Cases:**
    - Phase-appropriate intervention strategies
    - Early warning of approaching crisis (high Ω risk in K phase)
    - Track program maturation over time
    """
    service = EcologicalResilienceService(db)

    period_end = datetime.utcnow()
    period_start = period_end - timedelta(days=period_days)

    report = await service.analyze_system_resilience(period_start, period_end)

    return AdaptiveCycleResponse(
        timestamp=report.timestamp,
        phase=report.adaptive_cycle.current_phase.value,
        potential=report.adaptive_cycle.potential,
        connectedness=report.adaptive_cycle.connectedness,
        resilience=report.adaptive_cycle.resilience,
        omega_risk=report.adaptive_cycle.omega_risk,
        phase_duration_days=report.adaptive_cycle.phase_duration.days,
        phase_stability=report.adaptive_cycle.phase_stability,
        early_warning_signals=report.adaptive_cycle.early_warning_signals,
        component_scores=report.adaptive_cycle.component_scores
    )


@router.get("/panarchy", response_model=PanarchyStateResponse)
async def get_panarchy_state(
    period_days: int = Query(90, ge=1, le=365),
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """
    Get multi-scale panarchy state.

    Tracks adaptive cycle phases across four nested scales:
    1. **Individual** (days-weeks): Resident/faculty daily workload
    2. **Team** (weeks-months): Rotation assignments, call schedules
    3. **Departmental** (months-years): Program structure, annual templates
    4. **Institutional** (years-decades): Medical center policies, accreditation

    **Cross-Scale Connections:**
    - **Revolt Risk**: Probability of bottom-up cascade (individual → team → dept)
    - **Memory Strength**: Top-down stabilization (institution → dept → team)

    **Alerts:**
    - **Cascade Warning**: Multiple scales entering Ω simultaneously
    - **Synchronized Scales**: Scales in same phase (risky if all in Ω)

    **Use Cases:**
    - Detect individual burnout before team collapse
    - Identify weak institutional memory
    - Prevent cascade failures across organizational levels
    """
    service = EcologicalResilienceService(db)

    period_end = datetime.utcnow()
    period_start = period_end - timedelta(days=period_days)

    report = await service.analyze_system_resilience(period_start, period_end)

    return PanarchyStateResponse(
        timestamp=report.timestamp,
        individual_phase=report.panarchy.individual_phase.value,
        team_phase=report.panarchy.team_phase.value,
        departmental_phase=report.panarchy.departmental_phase.value,
        institutional_phase=report.panarchy.institutional_phase.value,
        revolt_risk=report.panarchy.revolt_risk,
        memory_strength=report.panarchy.memory_strength,
        synchronized_scales=[s.value for s in report.panarchy.synchronized_scales],
        cascade_warning=report.panarchy.cascade_warning,
        overall_stability=report.panarchy.overall_stability,
        weakest_scale=report.panarchy.weakest_scale.value,
        strongest_scale=report.panarchy.strongest_scale.value
    )


@router.post("/tipping-points", response_model=list[TippingPointAlertResponse])
async def detect_tipping_points(
    period_days: int = Query(90, ge=1, le=365),
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """
    Detect early warning signals of approaching regime shifts.

    **Monitored Metrics:**
    - Faculty attrition rate (threshold: 15%)
    - Coverage rate (threshold: 85%)
    - Average allostatic load (threshold: 60)
    - ACGME violation rate (threshold: 5%)

    **Early Warning Signals:**
    1. **Critical Slowing Down**: System takes longer to recover from perturbations
       - Measured via autocorrelation increase
       - Recovery time trending upward

    2. **Increased Variance** (Flickering): System oscillates between states
       - Recent variance > 2× historical baseline
       - Indicates proximity to threshold

    3. **Skewness Shift**: Distribution shifts toward extreme values
       - Positive skew: Few overloaded faculty (centralization)
       - Negative skew: Many overloaded faculty (systemic problem)

    **Urgency Levels:**
    - **Monitor**: Early signals detected, track trends
    - **Prepare**: Multiple signals + <20% from threshold → contingency planning
    - **Immediate**: Multiple signals + <10% from threshold → intervention required

    **Use Cases:**
    - 2-4 week lead time before crisis
    - Evidence-based intervention timing
    - Distinguish reversible vs. irreversible tipping points
    """
    service = EcologicalResilienceService(db)

    period_end = datetime.utcnow()
    period_start = period_end - timedelta(days=period_days)

    report = await service.analyze_system_resilience(period_start, period_end)

    return [
        TippingPointAlertResponse(
            metric_name=alert.metric_name,
            current_value=alert.current_value,
            threshold_estimate=alert.threshold_estimate,
            distance_to_threshold=alert.distance_to_threshold,
            critical_slowing=alert.critical_slowing,
            increased_variance=alert.increased_variance,
            skewness_shift=alert.skewness_shift,
            confidence=alert.confidence,
            urgency=alert.urgency.value,
            intervention=alert.intervention,
            reversibility=alert.reversibility,
            estimated_time_to_threshold_days=(
                alert.estimated_time_to_threshold.days
                if alert.estimated_time_to_threshold else None
            ),
            detected_at=alert.detected_at
        )
        for alert in report.tipping_point_alerts
    ]


@router.get("/diversity", response_model=DiversityMetricsResponse)
async def get_diversity_metrics(
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """
    Get faculty skill diversity metrics.

    **Biodiversity-Inspired Indices:**

    1. **Shannon Index** (H'): Weighted diversity
       - Formula: H' = -Σ(p_i × ln(p_i))
       - Range: 1.5 (low) to 3.5 (high diversity)
       - Interpretation: Higher = more diverse skill distribution

    2. **Simpson Index** (D): Dominance measure
       - Formula: D = 1 - Σ(p_i²)
       - Range: 0 (no diversity) to 1 (maximum diversity)
       - Interpretation: Probability two random faculty have different skills

    3. **Response Diversity**: Substitutability
       - Average number of faculty per specialty
       - Higher = more redundancy = higher resilience

    4. **Portfolio Effect**: Variance reduction
       - Formula: PE = (Σ individual variances) / (n² × community variance)
       - PE > 1 indicates stabilizing effect of diversity

    **Stability Score** (0-1 composite):
    - 30% Simpson index
    - 30% Shannon index (normalized)
    - 20% Response diversity
    - 20% Portfolio effect

    **Alerts:**
    - Low diversity (Shannon < 1.5, Simpson < 0.6)
    - Monoculture risk (>60% faculty with same primary specialty)
    - Single point failures (specialty covered by <2 faculty)

    **Use Cases:**
    - Evidence-based faculty recruitment priorities
    - Cross-training recommendations
    - Predict program stability under stress
    """
    service = EcologicalResilienceService(db)

    report = await service.analyze_system_resilience()

    return DiversityMetricsResponse(
        timestamp=report.timestamp,
        species_richness=report.diversity.species_richness,
        shannon_index=report.diversity.shannon_index,
        simpson_index=report.diversity.simpson_index,
        evenness=report.diversity.evenness,
        functional_richness=report.diversity.functional_richness,
        response_diversity=report.diversity.response_diversity,
        portfolio_effect=report.diversity.portfolio_effect,
        stability_score=report.diversity.stability_score,
        low_diversity_alerts=report.diversity.low_diversity_alerts,
        monoculture_risks=report.diversity.monoculture_risks,
        single_point_failures=report.diversity.single_point_failures
    )


@router.get("/report", response_model=EcologicalResilienceReportResponse)
async def get_comprehensive_report(
    period_days: int = Query(90, ge=1, le=365),
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """
    Get comprehensive ecological resilience report.

    Combines all ecological resilience analyses into single report:
    - Adaptive cycle state
    - Panarchy multi-scale assessment
    - Tipping point alerts
    - Diversity metrics
    - Overall risk assessment
    - Priority interventions

    **Overall Risk Levels:**
    - **Low**: System stable, normal operations
    - **Moderate**: Some warning signals, monitor closely
    - **High**: Multiple risk factors, prepare interventions
    - **Critical**: Crisis imminent or active, emergency response

    **Integration with Existing Framework:**
    - Maps to Defense-in-Depth levels (GREEN/YELLOW/ORANGE/RED/BLACK)
    - Feeds SPC monitoring variance detection
    - Complements Fire Weather Index multi-temporal analysis

    **Use Cases:**
    - Weekly resilience dashboard review
    - Monthly leadership briefing
    - Accreditation compliance evidence
    - Post-crisis analysis
    """
    service = EcologicalResilienceService(db)

    period_end = datetime.utcnow()
    period_start = period_end - timedelta(days=period_days)

    report = await service.analyze_system_resilience(period_start, period_end)

    return EcologicalResilienceReportResponse.from_domain(report)


@router.get("/history/adaptive-cycle", response_model=list[AdaptiveCycleResponse])
async def get_adaptive_cycle_history(
    days: int = Query(365, ge=1, le=730, description="Historical period"),
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """
    Get historical adaptive cycle progression.

    Returns time series of adaptive cycle states for trend analysis.

    **Use Cases:**
    - Visualize cycle progression over academic year
    - Identify phase transition patterns
    - Correlate phases with external events (deployments, holidays)
    - Validate cycle theory against program history
    """
    from app.models.resilience import CyclePhaseHistory
    from sqlalchemy import select

    cutoff = datetime.utcnow() - timedelta(days=days)

    query = (
        select(CyclePhaseHistory)
        .where(CyclePhaseHistory.timestamp >= cutoff)
        .order_by(CyclePhaseHistory.timestamp.asc())
    )

    records = (await db.execute(query)).scalars().all()

    return [
        AdaptiveCycleResponse(
            timestamp=r.timestamp,
            phase=r.phase,
            potential=r.potential,
            connectedness=r.connectedness,
            resilience=r.resilience,
            omega_risk=r.omega_risk,
            phase_duration_days=r.phase_duration_days,
            phase_stability=r.phase_stability,
            early_warning_signals=[],  # Not stored in history
            component_scores=r.component_scores or {}
        )
        for r in records
    ]


@router.get("/history/diversity", response_model=list[DiversityMetricsResponse])
async def get_diversity_history(
    days: int = Query(365, ge=1, le=730),
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """
    Get historical diversity metrics.

    Returns time series of faculty diversity indices.

    **Use Cases:**
    - Track diversity improvement over time
    - Evaluate recruitment/cross-training effectiveness
    - Correlate diversity with program stability events
    """
    from app.models.resilience import DiversitySnapshot
    from sqlalchemy import select

    cutoff = datetime.utcnow() - timedelta(days=days)

    query = (
        select(DiversitySnapshot)
        .where(DiversitySnapshot.calculated_at >= cutoff)
        .order_by(DiversitySnapshot.calculated_at.asc())
    )

    records = (await db.execute(query)).scalars().all()

    return [
        DiversityMetricsResponse(
            timestamp=r.calculated_at,
            species_richness=r.species_richness,
            shannon_index=r.shannon_index,
            simpson_index=r.simpson_index,
            evenness=r.evenness,
            functional_richness=r.functional_richness,
            response_diversity=r.response_diversity,
            portfolio_effect=r.portfolio_effect,
            stability_score=r.stability_score,
            low_diversity_alerts=[],  # Reconstruct from flags
            monoculture_risks={},
            single_point_failures=[]
        )
        for r in records
    ]
```

### Pydantic Schemas

Create `/backend/app/schemas/ecological_resilience.py`:

```python
"""Pydantic schemas for ecological resilience API responses."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AdaptiveCycleResponse(BaseModel):
    """Adaptive cycle state response."""

    timestamp: datetime
    phase: str = Field(
        ...,
        description="Current phase: exploitation, conservation, release, reorganization"
    )
    potential: float = Field(..., ge=0.0, le=1.0, description="Accumulated capital")
    connectedness: float = Field(..., ge=0.0, le=1.0, description="System coupling")
    resilience: float = Field(..., ge=0.0, le=1.0, description="Disturbance absorption")
    omega_risk: float = Field(..., ge=0.0, le=1.0, description="Crisis probability")
    phase_duration_days: int = Field(..., description="Days in current phase")
    phase_stability: float = Field(
        ..., ge=0.0, le=1.0, description="Classification confidence"
    )
    early_warning_signals: list[str] = Field(
        default_factory=list, description="Active warning signals"
    )
    component_scores: dict = Field(default_factory=dict, description="Detailed breakdown")


class PanarchyStateResponse(BaseModel):
    """Multi-scale panarchy state response."""

    timestamp: datetime
    individual_phase: str
    team_phase: str
    departmental_phase: str
    institutional_phase: str
    revolt_risk: float = Field(..., ge=0.0, le=1.0, description="Bottom-up cascade risk")
    memory_strength: float = Field(
        ..., ge=0.0, le=1.0, description="Top-down stability"
    )
    synchronized_scales: list[str] = Field(default_factory=list)
    cascade_warning: bool = Field(
        ..., description="Multiple scales in crisis simultaneously"
    )
    overall_stability: float = Field(..., ge=0.0, le=1.0)
    weakest_scale: str
    strongest_scale: str


class TippingPointAlertResponse(BaseModel):
    """Tipping point early warning alert."""

    metric_name: str
    current_value: float
    threshold_estimate: float
    distance_to_threshold: float = Field(
        ..., ge=0.0, le=1.0, description="0=at threshold, 1=far from threshold"
    )
    critical_slowing: bool = Field(..., description="Recovery time increasing")
    increased_variance: bool = Field(..., description="Flickering detected")
    skewness_shift: bool = Field(..., description="Distribution shifted")
    confidence: float = Field(..., ge=0.0, le=1.0)
    urgency: str = Field(..., description="monitor, prepare, or immediate")
    intervention: str = Field(..., description="Recommended action")
    reversibility: str = Field(
        ..., description="reversible, limited_window, or irreversible"
    )
    estimated_time_to_threshold_days: Optional[int] = Field(None)
    detected_at: datetime


class DiversityMetricsResponse(BaseModel):
    """Faculty diversity metrics response."""

    timestamp: datetime
    species_richness: int = Field(..., description="Unique skills count")
    shannon_index: float = Field(..., description="Weighted diversity (1.5-3.5)")
    simpson_index: float = Field(
        ..., ge=0.0, le=1.0, description="Probability of different skills"
    )
    evenness: float = Field(..., ge=0.0, le=1.0, description="Distribution uniformity")
    functional_richness: int = Field(..., description="Functional groups")
    response_diversity: float = Field(..., description="Avg substitutes per specialty")
    portfolio_effect: float = Field(..., description=">1 indicates stabilization")
    stability_score: float = Field(..., ge=0.0, le=1.0, description="Composite score")
    low_diversity_alerts: list[str] = Field(default_factory=list)
    monoculture_risks: dict = Field(default_factory=dict)
    single_point_failures: list[dict] = Field(default_factory=list)


class EcologicalResilienceReportResponse(BaseModel):
    """Comprehensive ecological resilience report."""

    timestamp: datetime
    adaptive_cycle: AdaptiveCycleResponse
    panarchy: PanarchyStateResponse
    tipping_point_alerts: list[TippingPointAlertResponse]
    diversity: DiversityMetricsResponse
    overall_risk: str = Field(..., description="low, moderate, high, critical")
    priority_interventions: list[str]
    defense_level_recommendation: Optional[str] = Field(
        None, description="Suggested Defense-in-Depth level"
    )

    @classmethod
    def from_domain(cls, report):
        """Convert domain model to response schema."""
        from app.resilience.ecological_resilience import EcologicalResilienceReport

        # Implementation would map domain objects to Pydantic models
        # Simplified for specification
        pass
```

---

## Analysis Modules

### Module Implementations (Continued in next section due to length)

The following modules are detailed in the research document and should be implemented according to the patterns shown:

1. **AdaptiveCycleTracker** - See implementation above
2. **PanarchyMonitor** - Cross-scale tracking with revolt/remember connections
3. **TippingPointDetector** - Critical slowing, variance, skewness detection
4. **DiversityAnalyzer** - Shannon, Simpson, portfolio effect calculations
5. **RecoveryDynamicsPredictor** - α phase convergence tracking

---

## Integration Points

### 1. Resilience Service Integration

```python
# Add to backend/app/resilience/service.py

from app.resilience.ecological_resilience import (
    EcologicalResilienceService,
    AdaptiveCyclePhase
)

class ResilienceService:
    """Extended with ecological resilience."""

    def __init__(self, db: Session, config: ResilienceConfig):
        # Existing initialization...
        self.ecology = EcologicalResilienceService(db)

    async def comprehensive_health_check(self) -> SystemHealthReport:
        """Add ecological metrics to health check."""
        # Existing health check...

        # Add ecological assessment
        ecology_report = await self.ecology.analyze_system_resilience()

        # Map ecological phase to defense level
        if ecology_report.adaptive_cycle.current_phase == AdaptiveCyclePhase.RELEASE:
            # Ω crisis → escalate to RED
            self.defense_level = DefenseLevel.CONTAINMENT

        # Add to overall report
        report.ecology_status = ecology_report
        return report
```

### 2. Defense-in-Depth Integration

Map adaptive cycle phases to defense levels:

| Adaptive Cycle | Defense Level | Rationale |
|----------------|---------------|-----------|
| r (Exploitation) | GREEN | Growth, innovation, stable |
| K (Conservation) | YELLOW (Ω risk <0.5)<br>ORANGE (Ω risk ≥0.5) | Mature but increasingly rigid |
| Ω (Release) | RED/BLACK | Crisis, emergency response |
| α (Reorganization) | YELLOW/ORANGE | Reorganizing, uncertain but recovering |

### 3. SPC Integration

```python
# Feed ecological variance signals to SPC monitoring

from app.resilience.spc_monitoring import WorkloadControlChart

# Tipping point "flickering" detection feeds SPC variance tracking
if tipping_alert.increased_variance:
    spc_chart.investigate_special_cause_variation()
```

### 4. Fire Index Integration

```python
# Multi-temporal alignment

from app.resilience.burnout_fire_index import BurnoutDangerRating

# Adaptive cycle potential aligns with FWI buildup index (BUI)
# K phase high potential = high BUI = accumulated fuel
```

---

## Implementation Phases

### Phase 1: Foundation (Months 1-3)

**Goals:**
- Adaptive cycle tracking operational
- Diversity metrics calculated
- Database schema deployed
- Basic API endpoints functional

**Deliverables:**
- [ ] `AdaptiveCycleTracker` class implemented
- [ ] `DiversityAnalyzer` class implemented
- [ ] Database models created
- [ ] Alembic migration written and tested
- [ ] API endpoints: `/adaptive-cycle`, `/diversity`
- [ ] Unit tests (>90% coverage)
- [ ] Integration tests with existing resilience framework

**Success Criteria:**
- Adaptive cycle phase correctly classified for 3 test scenarios (r, K, α)
- Diversity metrics calculated for all faculty
- API returns valid responses with <500ms latency

**Tasks:**
1. Week 1-2: Database schema & models
2. Week 3-4: AdaptiveCycleTracker implementation
3. Week 5-6: DiversityAnalyzer implementation
4. Week 7-8: API endpoints & schemas
5. Week 9-10: Testing & validation
6. Week 11-12: Documentation & code review

---

### Phase 2: Tipping Point Detection (Months 4-6)

**Goals:**
- Early warning signal detection operational
- Panarchy multi-scale tracking functional
- Alert integration with existing notification system

**Deliverables:**
- [ ] `TippingPointDetector` class implemented
  - [ ] Critical slowing down algorithm
  - [ ] Variance tracking (flickering)
  - [ ] Skewness shift detection
- [ ] `PanarchyMonitor` class implemented
  - [ ] Four-scale tracking
  - [ ] Revolt connection detector
  - [ ] Remember connection analyzer
- [ ] API endpoints: `/tipping-points`, `/panarchy`
- [ ] Email/webhook alerts for IMMEDIATE urgency
- [ ] Dashboard widgets (frontend)

**Success Criteria:**
- Detect simulated tipping point 2-4 weeks before threshold crossing
- Identify revolt cascade in test scenario
- Zero false positives on 90-day stable baseline data

**Tasks:**
1. Week 1-3: TippingPointDetector core algorithms
2. Week 4-6: PanarchyMonitor implementation
3. Week 7-8: Alert integration
4. Week 9-10: Frontend dashboard widgets
5. Week 11-12: Validation with historical data

---

### Phase 3: Recovery Dynamics (Months 7-9)

**Goals:**
- Reorganization (α phase) guidance operational
- Hysteresis modeling functional
- Scenario simulation available

**Deliverables:**
- [ ] `RecoveryDynamicsPredictor` class
- [ ] Reorganization path tracking
- [ ] Hysteresis threshold modeling
- [ ] Scenario simulator for testing interventions
- [ ] API endpoint: `/report` (comprehensive)

**Success Criteria:**
- Recommend reorganization strategy with >70% expert acceptance
- Predict α phase duration within ±1 week (tested on historical data)
- Identify irreversible tipping points correctly

---

### Phase 4: Production Integration (Months 10-12)

**Goals:**
- Full production deployment
- Dashboard complete
- Celery scheduled tasks operational
- Documentation published

**Deliverables:**
- [ ] Dashboard widgets complete
  - [ ] Adaptive cycle position visualization (phase space plot)
  - [ ] Diversity radar chart
  - [ ] Tipping point early warning panel
  - [ ] Panarchy hierarchy view
- [ ] Celery tasks
  - [ ] Daily adaptive cycle calculation
  - [ ] Daily tipping point detection
  - [ ] Weekly diversity recalculation
  - [ ] Monthly panarchy analysis
- [ ] User guide documentation
- [ ] Intervention playbook
- [ ] Case studies from historical validation

**Success Criteria:**
- <5 second API response time (95th percentile)
- 95% uptime for Celery tasks
- User acceptance >80% (survey)
- All metrics accessible via dashboard

---

## Testing Requirements

### Unit Tests

**Coverage Target**: >90% for all modules

```python
# Example: tests/resilience/test_adaptive_cycle.py

import pytest
from datetime import datetime, timedelta

from app.resilience.adaptive_cycle import AdaptiveCycleTracker
from app.resilience.ecological_resilience import AdaptiveCyclePhase


class TestAdaptiveCycleTracker:
    """Test suite for adaptive cycle classification."""

    async def test_classify_r_phase(self, db):
        """Test r (exploitation) phase classification."""
        tracker = AdaptiveCycleTracker(db)

        # Mock conditions: Low P, Low C, High R
        # This should classify as r (growth/exploitation)
        phase = tracker._classify_phase(
            potential=0.3,
            connectedness=0.2,
            resilience=0.8
        )

        assert phase == AdaptiveCyclePhase.EXPLOITATION

    async def test_classify_k_phase(self, db):
        """Test K (conservation) phase classification."""
        tracker = AdaptiveCycleTracker(db)

        # Mock conditions: High P, High C (mature/rigid)
        phase = tracker._classify_phase(
            potential=0.85,
            connectedness=0.90,
            resilience=0.4
        )

        assert phase == AdaptiveCyclePhase.CONSERVATION

    async def test_omega_risk_high_in_k_phase(self, db):
        """Test Ω risk calculation in K phase."""
        tracker = AdaptiveCycleTracker(db)

        # K phase with low resilience = high Ω risk
        omega_risk = tracker._calculate_omega_risk(
            potential=0.9,
            connectedness=0.95,
            resilience=0.2,
            phase=AdaptiveCyclePhase.CONSERVATION
        )

        assert omega_risk > 0.7  # High risk

    async def test_omega_risk_zero_in_r_phase(self, db):
        """Test Ω risk is zero outside K phase."""
        tracker = AdaptiveCycleTracker(db)

        omega_risk = tracker._calculate_omega_risk(
            potential=0.3,
            connectedness=0.2,
            resilience=0.8,
            phase=AdaptiveCyclePhase.EXPLOITATION
        )

        assert omega_risk == 0.0
```

### Integration Tests

```python
# tests/resilience/test_ecological_integration.py

class TestEcologicalResilienceIntegration:
    """Test integration with existing resilience framework."""

    async def test_defense_level_escalation(self, db):
        """Test ecological Ω phase triggers RED defense level."""
        service = EcologicalResilienceService(db)

        # Create Ω phase conditions
        # ...

        report = await service.analyze_system_resilience()

        assert report.adaptive_cycle.current_phase == AdaptiveCyclePhase.RELEASE
        assert report.defense_level_recommendation == "RED"

    async def test_diversity_feeds_spc(self, db):
        """Test diversity variance feeds SPC monitoring."""
        # Test that low diversity triggers SPC variance investigation
        pass
```

### Performance Tests

```python
# tests/resilience/test_ecological_performance.py

class TestEcologicalPerformance:
    """Performance benchmarks."""

    async def test_analysis_latency(self, db):
        """Test comprehensive analysis completes <5s."""
        service = EcologicalResilienceService(db)

        start = datetime.now()
        report = await service.analyze_system_resilience()
        duration = (datetime.now() - start).total_seconds()

        assert duration < 5.0  # <5 second SLA
```

---

## Monitoring & Alerts

### Celery Scheduled Tasks

```python
# File: backend/app/resilience/tasks.py (extend existing)

from celery import shared_task
from app.db.session import SessionLocal
from app.resilience.ecological_resilience import EcologicalResilienceService

@shared_task
def ecological_daily_check():
    """
    Daily ecological resilience analysis.

    Runs: Every day at 6:00 AM
    Duration: ~30 seconds
    """
    db = SessionLocal()
    try:
        service = EcologicalResilienceService(db)
        report = await service.analyze_system_resilience()

        # Send alerts for IMMEDIATE urgency tipping points
        immediate_alerts = [
            a for a in report.tipping_point_alerts
            if a.urgency == DangerLevel.IMMEDIATE
        ]

        if immediate_alerts:
            send_urgent_alerts(immediate_alerts)

        # Log summary
        logger.info(
            f"Ecological check: Phase={report.adaptive_cycle.current_phase.value}, "
            f"Risk={report.overall_risk}, Alerts={len(immediate_alerts)}"
        )
    finally:
        db.close()


@shared_task
def diversity_weekly_update():
    """
    Weekly diversity metrics recalculation.

    Runs: Every Monday at 8:00 AM
    Duration: ~10 seconds
    """
    db = SessionLocal()
    try:
        service = EcologicalResilienceService(db)
        diversity_metrics = await service.diversity.calculate_comprehensive_metrics()

        # Check for low diversity alerts
        if diversity_metrics.stability_score < 0.5:
            send_diversity_warning(diversity_metrics)
    finally:
        db.close()


# Add to Celery beat schedule:
app.conf.beat_schedule.update({
    'ecological-daily-check': {
        'task': 'app.resilience.tasks.ecological_daily_check',
        'schedule': crontab(hour=6, minute=0),  # 6 AM daily
    },
    'diversity-weekly-update': {
        'task': 'app.resilience.tasks.diversity_weekly_update',
        'schedule': crontab(day_of_week=1, hour=8, minute=0),  # Monday 8 AM
    },
})
```

### Alert Thresholds

| Condition | Alert Level | Action |
|-----------|-------------|--------|
| Ω risk >0.7 in K phase | WARNING | Email program director |
| Ω phase entered | CRITICAL | Email + webhook + SMS |
| Tipping point IMMEDIATE urgency | CRITICAL | Email + webhook |
| Diversity stability <0.5 | WARNING | Email monthly report |
| Cascade warning (panarchy) | CRITICAL | Email + escalate to institution |
| 2+ scales in Ω simultaneously | EMERGENCY | Email + phone call + MCP alert |

---

## Performance Specifications

### Latency Requirements

| Endpoint | Target Latency (p95) | Max Acceptable |
|----------|---------------------|----------------|
| GET /adaptive-cycle | 200ms | 500ms |
| GET /panarchy | 300ms | 800ms |
| POST /tipping-points | 500ms | 1500ms |
| GET /diversity | 100ms | 300ms |
| GET /report | 1000ms | 3000ms |

### Throughput

- **Concurrent Users**: Support 50 concurrent API requests
- **Celery Tasks**: Daily tasks complete within 5 minutes
- **Database Queries**: <100ms for historical data retrieval

### Data Retention

| Data Type | Retention Period | Rationale |
|-----------|------------------|-----------|
| Cycle phase history | 5 years | Academic cycle analysis |
| Diversity snapshots | 3 years | Recruitment trend tracking |
| Tipping point alerts | 2 years | Post-incident review |
| Panarchy states | 1 year | Cross-scale pattern analysis |

### Scalability

- **Faculty**: Support programs up to 100 faculty
- **Residents**: Support programs up to 200 residents
- **Historical Data**: Efficient queries over 5+ years of data
- **Concurrent Analyses**: Handle 10 simultaneous comprehensive reports

---

## Dependencies

### Python Packages

All required packages already in `requirements.txt`:

```python
numpy==2.3.5           # Array operations
scipy>=1.11.0          # Statistical functions (skewness, etc.)
networkx>=3.0          # Graph analysis for panarchy
```

### External Services

- **PostgreSQL**: Database for persistence
- **Redis**: Celery broker
- **Celery**: Background task scheduling

---

## Documentation Requirements

### User Guide

Topics to cover:

1. **Introduction to Ecological Resilience**
   - Why ecology for healthcare?
   - Key concepts (adaptive cycle, panarchy, tipping points)

2. **Interpreting the Dashboard**
   - Adaptive cycle phase meanings
   - What to do in each phase
   - Understanding tipping point alerts

3. **Intervention Playbook**
   - Phase-specific strategies
   - Cross-scale cascade prevention
   - Diversity improvement tactics

4. **Case Studies**
   - Historical validation examples
   - Success stories from pilot programs

### API Documentation

- OpenAPI/Swagger autogenerated
- Endpoint descriptions (see API section above)
- Example requests/responses
- Error codes and handling

### Developer Guide

- Module architecture
- Adding new diversity indices
- Calibrating thresholds
- Testing procedures

---

## Acceptance Criteria

### Phase 1 Sign-off

- [ ] Adaptive cycle correctly classifies 5 test scenarios
- [ ] Diversity metrics match hand-calculated values
- [ ] All database migrations apply cleanly
- [ ] API endpoints return valid JSON
- [ ] Unit tests achieve >90% coverage
- [ ] Code review approved by 2 senior engineers

### Phase 2 Sign-off

- [ ] Tipping point detector identifies 2/2 simulated events
- [ ] Panarchy monitor detects revolt cascade in test scenario
- [ ] No false positives on 90-day stable baseline
- [ ] Alert emails delivered within 5 minutes
- [ ] Integration tests pass

### Phase 3 Sign-off

- [ ] Reorganization predictor tested on 3 historical crises
- [ ] Accuracy within ±1 week for α phase duration
- [ ] Scenario simulator functional
- [ ] Hysteresis model validated

### Phase 4 Production Release

- [ ] Dashboard fully functional
- [ ] Celery tasks running on schedule
- [ ] Performance SLAs met (see table above)
- [ ] User acceptance survey >80% positive
- [ ] Documentation published
- [ ] Security audit passed
- [ ] ACGME compliance verification

---

## Risk Mitigation

### Implementation Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Insufficient historical data | Medium | High | Use synthetic data for testing; collect 3 months baseline before full deployment |
| Threshold calibration | High | Medium | Start with conservative thresholds; iteratively tune based on false positive/negative rates |
| Performance degradation | Low | Medium | Implement caching; use async queries; load test early |
| User resistance to new metrics | Medium | Medium | Extensive documentation; training sessions; gradual rollout |

### Operational Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| False positive alerts | Medium | Low | Confidence scoring; require multiple signals for IMMEDIATE alerts |
| Missed true positives | Low | High | Conservative thresholds; redundant detection (SPC + ecology) |
| Dashboard performance | Low | Medium | Cache expensive queries; precompute daily |
| Data quality issues | Medium | Medium | Validation checks; data quality monitoring; graceful degradation |

---

## Appendices

### A. Mathematical Formulas

**Shannon Diversity Index:**
```
H' = -Σ(p_i × ln(p_i))

where p_i = proportion of individuals belonging to species i
```

**Simpson Diversity Index:**
```
D = 1 - Σ(p_i²)

where p_i = proportion of individuals belonging to species i
```

**Portfolio Effect:**
```
PE = (Σ σ_i²) / (n² × σ_community²)

where:
  σ_i² = variance of individual i
  n = number of individuals
  σ_community² = variance of community total
```

**Critical Slowing Down (Autocorrelation):**
```
AR(1) = Cor(X_t, X_{t-1})

Increasing AR(1) → approaching tipping point
```

### B. Glossary

- **Adaptive Cycle**: Holling's 4-phase model (r→K→Ω→α) of ecosystem dynamics
- **Panarchy**: Nested hierarchy of adaptive cycles across scales
- **Revolt**: Bottom-up cascade of crisis from small to large scale
- **Remember**: Top-down stabilization from large to small scale
- **Regime Shift**: Abrupt, persistent change in system state
- **Tipping Point**: Critical threshold beyond which feedbacks drive system to alternative state
- **Portfolio Effect**: Stabilization from asynchronous responses of diverse components

### C. References

See `docs/research/ECOLOGY_RESILIENCE_INTEGRATION.md` for full academic citations.

Key sources:
- Holling (1973): Original adaptive cycle formulation
- Gunderson & Holling (2002): *Panarchy* book
- Scheffer et al. (2009): Early warning signals in Nature
- Tilman et al. (2014): Biodiversity-stability mechanisms

---

**Document Status**: Production-ready specification
**Estimated Implementation Effort**: 12 months (4 phases × 3 months)
**Dependencies**: Existing resilience framework (Tier 1-3 modules)
**Risk Level**: Medium (novel application, requires validation)
**Impact Potential**: High (fills gap in proactive system-level monitoring)

---

**Next Steps**:

1. **Stakeholder Review**: Present to program leadership for approval
2. **Resource Allocation**: Assign development team (2 backend engineers, 1 frontend engineer)
3. **Phase 1 Kickoff**: Database schema design workshop
4. **Baseline Data Collection**: Begin 90-day data collection for calibration
5. **Pilot Program**: Select 1-2 programs for initial deployment

---

**Revision History**:

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2025-12-26 | 1.0 | Initial specification | Resilience Engineering Team |

