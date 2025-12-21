# Cross-Disciplinary Resilience API Integration

## Overview

This guide demonstrates how to integrate the cross-disciplinary resilience modules into FastAPI endpoints. These modules apply concepts from manufacturing (SPC), telecommunications (Erlang C), seismology (STA/LTA), forest fire science (FWI), materials science (creep/fatigue), and epidemiology to medical residency scheduling.

The modules are located in `/backend/app/resilience/` and provide:
- **Statistical Process Control (SPC)**: Workload monitoring with Western Electric rules
- **Six Sigma Process Capability**: Schedule quality metrics (Cp, Cpk, Pp, Ppk)
- **Epidemiology**: Burnout spread modeling using SIR models
- **Erlang C**: Specialist coverage optimization using queuing theory
- **Seismic Detection**: Early warning for burnout using STA/LTA
- **Fire Weather Index**: Multi-temporal burnout danger rating
- **Creep/Fatigue**: Long-term overwork prediction using materials science

---

## Quick Start

### Basic Import Pattern

```python
from app.resilience import (
    WorkloadControlChart,
    ScheduleCapabilityAnalyzer,
    BurnoutEpidemiology,
    ErlangCCalculator,
    BurnoutEarlyWarning,
    BurnoutDangerRating,
    CreepFatigueModel,
)
```

### Alternative: Import from Specific Modules

```python
from app.resilience.spc_monitoring import WorkloadControlChart, SPCAlert
from app.resilience.process_capability import ScheduleCapabilityAnalyzer, ProcessCapabilityReport
from app.resilience.burnout_epidemiology import BurnoutEpidemiology, BurnoutState
from app.resilience.erlang_coverage import ErlangCCalculator, SpecialistCoverage
from app.resilience.seismic_detection import BurnoutEarlyWarning, PrecursorSignal, SeismicAlert
from app.resilience.burnout_fire_index import BurnoutDangerRating, DangerClass
from app.resilience.creep_fatigue import CreepFatigueModel, CreepAnalysis
```

---

## Endpoint Examples

### 1. SPC Workload Monitoring Endpoint

Monitor resident workload using Statistical Process Control with Western Electric rules.

```python
from datetime import date, timedelta
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.api.deps import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.resilience.spc_monitoring import WorkloadControlChart, SPCAlert

router = APIRouter()


class SPCAlertResponse(BaseModel):
    """Response schema for SPC alert."""
    rule: str
    severity: str
    message: str
    resident_id: UUID | None
    data_points: list[float]
    control_limits: dict


class WorkloadSPCRequest(BaseModel):
    """Request to analyze workload with SPC."""
    resident_id: UUID
    weekly_hours: list[float] = Field(
        ...,
        min_items=8,
        description="Weekly hours in chronological order (min 8 weeks)"
    )
    target_hours: float = Field(60.0, ge=0, le=80)
    sigma: float = Field(5.0, ge=0.1, le=20)


class WorkloadSPCResponse(BaseModel):
    """SPC workload analysis response."""
    resident_id: UUID
    analyzed_at: str
    target_hours: float
    sigma: float
    alerts: list[SPCAlertResponse]
    control_limits: dict
    status: str
    recommendations: list[str]


@router.post("/analytics/spc/workload", response_model=WorkloadSPCResponse)
async def analyze_workload_spc(
    request: WorkloadSPCRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Analyze resident workload using Statistical Process Control.

    Uses Western Electric Rules to detect:
    - Rule 1: 1 point beyond 3σ (CRITICAL)
    - Rule 2: 2 of 3 points beyond 2σ (WARNING)
    - Rule 3: 4 of 5 points beyond 1σ (WARNING)
    - Rule 4: 8 consecutive points on same side of centerline (INFO)

    Example request:
    ```json
    {
        "resident_id": "123e4567-e89b-12d3-a456-426614174000",
        "weekly_hours": [58, 62, 59, 67, 71, 75, 78, 80],
        "target_hours": 60,
        "sigma": 5
    }
    ```
    """
    from datetime import datetime

    # Initialize control chart
    chart = WorkloadControlChart(
        target_hours=request.target_hours,
        sigma=request.sigma,
    )

    # Detect violations
    alerts = chart.detect_western_electric_violations(
        resident_id=request.resident_id,
        weekly_hours=request.weekly_hours,
    )

    # Generate recommendations
    recommendations = []
    if any(alert.severity == "CRITICAL" for alert in alerts):
        recommendations.append(
            "URGENT: Critical workload violation detected - immediate intervention required"
        )
        recommendations.append(
            f"Reduce workload to target {request.target_hours}h/week immediately"
        )
    elif any(alert.severity == "WARNING" for alert in alerts):
        recommendations.append(
            "Warning: Workload trend detected - monitor closely and adjust schedule"
        )
    else:
        recommendations.append("Workload within control limits - continue monitoring")

    # Determine overall status
    if alerts:
        max_severity = max(alert.severity for alert in alerts)
        status = max_severity.lower()
    else:
        status = "normal"

    return WorkloadSPCResponse(
        resident_id=request.resident_id,
        analyzed_at=datetime.utcnow().isoformat(),
        target_hours=request.target_hours,
        sigma=request.sigma,
        alerts=[
            SPCAlertResponse(
                rule=alert.rule,
                severity=alert.severity,
                message=alert.message,
                resident_id=alert.resident_id,
                data_points=alert.data_points,
                control_limits=alert.control_limits,
            )
            for alert in alerts
        ],
        control_limits={
            "ucl_3sigma": chart.ucl_3sigma,
            "lcl_3sigma": chart.lcl_3sigma,
            "ucl_2sigma": chart.ucl_2sigma,
            "lcl_2sigma": chart.lcl_2sigma,
            "centerline": chart.target_hours,
        },
        status=status,
        recommendations=recommendations,
    )
```

---

### 2. Process Capability Dashboard

Assess schedule quality using Six Sigma Cp/Cpk metrics.

```python
class ProcessCapabilityRequest(BaseModel):
    """Request for process capability analysis."""
    weekly_hours: list[float] = Field(..., min_items=30, description="Min 30 samples recommended")
    min_hours: float = Field(40.0, description="Lower specification limit")
    max_hours: float = Field(80.0, description="Upper specification limit (ACGME)")
    target_hours: float | None = Field(None, description="Target hours (defaults to midpoint)")


class ProcessCapabilityResponse(BaseModel):
    """Process capability analysis response."""
    capability_status: str  # EXCELLENT, CAPABLE, MARGINAL, INCAPABLE
    sigma_level: float
    cp: float
    cpk: float
    pp: float
    ppk: float
    cpm: float
    mean: float
    std_dev: float
    sample_size: int
    estimated_defect_ppm: float
    centering_assessment: str
    recommendations: list[str]


@router.post("/analytics/capability/workload", response_model=ProcessCapabilityResponse)
async def analyze_workload_capability(
    request: ProcessCapabilityRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Analyze workload distribution capability using Six Sigma metrics.

    Returns Cp/Cpk indices showing how consistently the scheduling
    process maintains hours within ACGME limits.

    Capability Interpretation:
    - Cpk >= 2.0: World-class (6σ quality)
    - Cpk >= 1.67: Excellent (5σ quality)
    - Cpk >= 1.33: Capable (4σ quality, industry standard)
    - Cpk >= 1.0: Marginal (3σ quality)
    - Cpk < 1.0: Incapable (defects expected)
    """
    from app.resilience.process_capability import ScheduleCapabilityAnalyzer

    analyzer = ScheduleCapabilityAnalyzer()

    # Analyze capability
    report = analyzer.analyze_workload_capability(
        weekly_hours=request.weekly_hours,
        min_hours=request.min_hours,
        max_hours=request.max_hours,
        target_hours=request.target_hours,
    )

    # Get detailed summary
    summary = analyzer.get_capability_summary(report)

    return ProcessCapabilityResponse(
        capability_status=report.capability_status,
        sigma_level=report.sigma_level,
        cp=report.cp,
        cpk=report.cpk,
        pp=report.pp,
        ppk=report.ppk,
        cpm=report.cpm,
        mean=report.mean,
        std_dev=report.std_dev,
        sample_size=report.sample_size,
        estimated_defect_ppm=float(summary["estimated_defect_rate"]["ppm"]),
        centering_assessment=summary["centering"],
        recommendations=summary["recommendations"],
    )
```

---

### 3. Burnout Contagion Analysis

Use epidemiological SIR models to analyze burnout spread through social networks.

```python
import networkx as nx
from datetime import datetime, timedelta


class BurnoutEpiRequest(BaseModel):
    """Request for burnout epidemiology analysis."""
    burned_out_residents: list[UUID] = Field(..., description="Currently burned out residents")
    time_window_weeks: int = Field(4, ge=1, le=12, description="Time window for secondary cases")


class BurnoutEpiResponse(BaseModel):
    """Burnout epidemiology response."""
    reproduction_number: float
    status: str
    intervention_level: str
    secondary_cases: dict[str, int]
    super_spreaders: list[UUID]
    high_risk_contacts: list[UUID]
    total_cases_analyzed: int
    total_close_contacts: int
    recommended_interventions: list[str]


@router.post("/analytics/burnout/epidemiology", response_model=BurnoutEpiResponse)
async def analyze_burnout_contagion(
    request: BurnoutEpiRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Analyze burnout spread using epidemiological models.

    Calculates effective reproduction number (Rt) for burnout:
    - Rt < 0.5: Declining (burnout contained)
    - Rt < 1.0: Controlled (stable)
    - Rt < 2.0: Spreading (moderate intervention)
    - Rt < 3.0: Rapid spread (aggressive intervention)
    - Rt >= 3.0: Crisis (emergency intervention)

    Identifies super-spreaders and high-risk contacts.
    """
    from app.resilience.burnout_epidemiology import BurnoutEpidemiology
    from app.models.person import Person
    from app.models.assignment import Assignment

    # Build social network from shared shifts
    # In production, this would use actual assignment data
    G = nx.Graph()

    # Get all residents
    residents = db.query(Person).filter(Person.type == "resident").all()

    # Add nodes
    for resident in residents:
        G.add_node(resident.id)

    # Add edges based on shared shifts (simplified)
    # In production, query assignments and connect residents
    # who frequently work together
    assignments = db.query(Assignment).all()
    # ... build edges from shared blocks ...

    # Initialize epidemiology analyzer
    epi = BurnoutEpidemiology(social_network=G)

    # Calculate reproduction number
    report = epi.calculate_reproduction_number(
        burned_out_residents=set(request.burned_out_residents),
        time_window=timedelta(weeks=request.time_window_weeks),
    )

    return BurnoutEpiResponse(
        reproduction_number=report.reproduction_number,
        status=report.status,
        intervention_level=report.intervention_level.value,
        secondary_cases=report.secondary_cases,
        super_spreaders=report.super_spreaders,
        high_risk_contacts=report.high_risk_contacts,
        total_cases_analyzed=report.total_cases_analyzed,
        total_close_contacts=report.total_close_contacts,
        recommended_interventions=report.recommended_interventions,
    )
```

---

### 4. Specialist Coverage Optimization

Use Erlang C queuing theory to optimize specialist staffing.

```python
class ErlangCRequest(BaseModel):
    """Request for Erlang C specialist coverage optimization."""
    specialty: str = Field(..., description="Specialty name (e.g., Orthopedic Surgery)")
    arrival_rate: float = Field(..., ge=0, description="Cases per hour")
    service_time: float = Field(..., ge=0, description="Average time per case (hours)")
    target_wait_prob: float = Field(0.05, ge=0, le=1, description="Max acceptable wait probability")


class ErlangCResponse(BaseModel):
    """Erlang C optimization response."""
    specialty: str
    required_specialists: int
    predicted_wait_probability: float
    offered_load: float
    service_level: float
    wait_probability: float
    avg_wait_time: float
    occupancy: float
    recommendations: list[str]


@router.post("/analytics/erlang/optimize", response_model=ErlangCResponse)
async def optimize_specialist_coverage(
    request: ErlangCRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Optimize specialist coverage using Erlang C queuing theory.

    Determines minimum number of specialists needed to meet
    service level targets (e.g., 95% answered immediately).

    Example use cases:
    - ER orthopedic coverage (must respond within 15 min)
    - Call schedule optimization
    - Procedure coverage planning
    """
    from app.resilience.erlang_coverage import ErlangCCalculator

    calc = ErlangCCalculator()

    # Optimize coverage
    coverage = calc.optimize_specialist_coverage(
        specialty=request.specialty,
        arrival_rate=request.arrival_rate,
        service_time=request.service_time,
        target_wait_prob=request.target_wait_prob,
    )

    # Get detailed metrics
    metrics = calc.calculate_metrics(
        arrival_rate=request.arrival_rate,
        service_time=request.service_time,
        servers=coverage.required_specialists,
    )

    # Generate recommendations
    recommendations = []
    if metrics.occupancy > 0.85:
        recommendations.append(
            f"Warning: High occupancy ({metrics.occupancy:.1%}) - "
            "consider adding one more specialist for buffer"
        )
    if metrics.wait_probability > request.target_wait_prob * 1.5:
        recommendations.append(
            "Wait probability higher than target - increase staffing"
        )
    else:
        recommendations.append(
            f"Optimal staffing: {coverage.required_specialists} specialists meets targets"
        )

    return ErlangCResponse(
        specialty=coverage.specialty,
        required_specialists=coverage.required_specialists,
        predicted_wait_probability=coverage.predicted_wait_probability,
        offered_load=coverage.offered_load,
        service_level=coverage.service_level,
        wait_probability=metrics.wait_probability,
        avg_wait_time=metrics.avg_wait_time,
        occupancy=metrics.occupancy,
        recommendations=recommendations,
    )
```

---

### 5. Burnout Early Warning System

Use STA/LTA (seismic detection) for burnout precursor signals.

```python
class BurnoutEarlyWarningRequest(BaseModel):
    """Request for burnout early warning analysis."""
    resident_id: UUID
    signal_type: str = Field(..., description="swap_requests, sick_calls, preference_decline, etc.")
    time_series: list[float] = Field(..., min_items=30, description="Daily counts over time")
    short_window: int = Field(5, ge=2, le=10)
    long_window: int = Field(30, ge=10, le=90)


class SeismicAlertResponse(BaseModel):
    """Seismic alert response."""
    signal_type: str
    sta_lta_ratio: float
    severity: str
    predicted_magnitude: float
    time_to_event_days: int | None
    context: dict


class BurnoutEarlyWarningResponse(BaseModel):
    """Early warning response."""
    resident_id: UUID
    analyzed_at: str
    alerts: list[SeismicAlertResponse]
    status: str
    recommendations: list[str]


@router.post("/analytics/burnout/early-warning", response_model=BurnoutEarlyWarningResponse)
async def detect_burnout_precursors(
    request: BurnoutEarlyWarningRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Detect burnout precursor signals using STA/LTA (seismology).

    Monitors behavioral signals that precede burnout:
    - Swap request frequency
    - Sick call patterns
    - Preference declines
    - Response delays
    - Voluntary coverage declines

    Uses Short-Term Average / Long-Term Average ratio to detect
    sudden changes in baseline behavior (similar to earthquake P-wave detection).
    """
    from app.resilience.seismic_detection import (
        BurnoutEarlyWarning,
        PrecursorSignal,
    )

    # Map signal type string to enum
    signal_map = {
        "swap_requests": PrecursorSignal.SWAP_REQUESTS,
        "sick_calls": PrecursorSignal.SICK_CALLS,
        "preference_decline": PrecursorSignal.PREFERENCE_DECLINE,
        "response_delays": PrecursorSignal.RESPONSE_DELAYS,
        "voluntary_coverage_decline": PrecursorSignal.VOLUNTARY_COVERAGE_DECLINE,
    }

    if request.signal_type not in signal_map:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid signal_type. Must be one of: {list(signal_map.keys())}"
        )

    # Initialize detector
    detector = BurnoutEarlyWarning(
        short_window=request.short_window,
        long_window=request.long_window,
    )

    # Detect precursors
    alerts = detector.detect_precursors(
        resident_id=request.resident_id,
        signal_type=signal_map[request.signal_type],
        time_series=request.time_series,
    )

    # Generate recommendations
    recommendations = []
    if any(alert.severity == "critical" for alert in alerts):
        recommendations.append("URGENT: Critical precursor detected - immediate wellness check required")
    elif any(alert.severity == "high" for alert in alerts):
        recommendations.append("High-risk precursor - schedule wellness intervention within 48 hours")
    elif alerts:
        recommendations.append("Precursor detected - monitor closely and consider preventive support")
    else:
        recommendations.append("No significant precursors detected - continue routine monitoring")

    # Determine status
    status = "critical" if any(a.severity == "critical" for a in alerts) else \
             "warning" if alerts else "normal"

    return BurnoutEarlyWarningResponse(
        resident_id=request.resident_id,
        analyzed_at=datetime.utcnow().isoformat(),
        alerts=[
            SeismicAlertResponse(
                signal_type=alert.signal_type.value,
                sta_lta_ratio=alert.sta_lta_ratio,
                severity=alert.severity,
                predicted_magnitude=alert.predicted_magnitude,
                time_to_event_days=alert.time_to_event.days if alert.time_to_event else None,
                context=alert.context,
            )
            for alert in alerts
        ],
        status=status,
        recommendations=recommendations,
    )
```

---

### 6. Fire Weather Danger Rating

Multi-temporal burnout assessment using Canadian Forest Fire Weather Index.

```python
class FireDangerRequest(BaseModel):
    """Request for fire weather danger rating."""
    resident_id: UUID
    recent_hours: float = Field(..., ge=0, description="Hours in last 2 weeks")
    monthly_load: float = Field(..., ge=0, description="Avg monthly hours (3 months)")
    yearly_satisfaction: float = Field(..., ge=0, le=1, description="Job satisfaction (0-1)")
    workload_velocity: float = Field(0.0, description="Rate of workload increase (hours/week)")


class FireDangerResponse(BaseModel):
    """Fire danger rating response."""
    resident_id: UUID
    danger_class: str  # LOW, MODERATE, HIGH, VERY_HIGH, EXTREME
    fwi_score: float
    component_scores: dict
    is_safe: bool
    requires_intervention: bool
    recommended_restrictions: list[str]


@router.post("/analytics/burnout/fire-danger", response_model=FireDangerResponse)
async def calculate_burnout_danger(
    request: FireDangerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Calculate burnout danger using Fire Weather Index (FWI) System.

    Combines three temporal scales:
    - FFMC: Fine Fuel Moisture (recent 2-week hours)
    - DMC: Duff Moisture (3-month sustained load)
    - DC: Drought Code (yearly satisfaction erosion)
    - ISI: Initial Spread Index (workload velocity)
    - BUI: Buildup Index (combined burden)
    - FWI: Fire Weather Index (final danger score)

    Danger Classes:
    - LOW (FWI < 20): Normal operations
    - MODERATE (20-40): Monitor closely
    - HIGH (40-60): Reduce workload
    - VERY_HIGH (60-80): Urgent intervention
    - EXTREME (80+): Emergency measures
    """
    from app.resilience.burnout_fire_index import BurnoutDangerRating

    rating = BurnoutDangerRating()

    # Calculate danger
    report = rating.calculate_burnout_danger(
        resident_id=request.resident_id,
        recent_hours=request.recent_hours,
        monthly_load=request.monthly_load,
        yearly_satisfaction=request.yearly_satisfaction,
        workload_velocity=request.workload_velocity,
    )

    return FireDangerResponse(
        resident_id=report.resident_id,
        danger_class=report.danger_class.value.upper(),
        fwi_score=report.fwi_score,
        component_scores=report.component_scores,
        is_safe=report.is_safe,
        requires_intervention=report.requires_intervention,
        recommended_restrictions=report.recommended_restrictions,
    )
```

---

### 7. Chronic Overwork Prediction

Creep/fatigue analysis from materials science for long-term burnout prediction.

```python
class CreepFatigueRequest(BaseModel):
    """Request for creep/fatigue analysis."""
    resident_id: UUID
    sustained_workload: float = Field(..., ge=0, le=1, description="Workload fraction (0-1)")
    duration_days: int = Field(..., ge=1, description="Duration of sustained workload")
    rotation_stresses: list[float] = Field(
        ...,
        description="Historical rotation stress levels (0-1)"
    )


class CreepFatigueResponse(BaseModel):
    """Creep/fatigue analysis response."""
    resident_id: UUID
    overall_risk: str  # high, moderate, low
    risk_score: float
    risk_description: str
    creep_analysis: dict
    fatigue_analysis: dict
    recommendations: list[str]


@router.post("/analytics/burnout/creep-fatigue", response_model=CreepFatigueResponse)
async def analyze_creep_fatigue(
    request: CreepFatigueRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Predict burnout using creep/fatigue analysis from materials science.

    Combines two failure modes:
    1. Creep: Long-term sustained workload effects (Larson-Miller parameter)
    2. Fatigue: Cumulative damage from rotation cycles (Miner's rule)

    Creep Stages:
    - PRIMARY: Adaptation phase
    - SECONDARY: Steady-state (sustainable)
    - TERTIARY: Accelerating damage (high risk)

    Provides time-to-burnout estimates and stress reduction recommendations.
    """
    from app.resilience.creep_fatigue import CreepFatigueModel

    model = CreepFatigueModel()

    # Assess combined risk
    risk = model.assess_combined_risk(
        resident_id=request.resident_id,
        sustained_workload=request.sustained_workload,
        duration=timedelta(days=request.duration_days),
        rotation_stresses=request.rotation_stresses,
    )

    return CreepFatigueResponse(**risk)
```

---

## Celery Task Integration

Integrate cross-disciplinary modules into background tasks for automated monitoring.

### Example: Periodic SPC Monitoring Task

```python
from celery import shared_task
from datetime import date, timedelta

@shared_task(
    bind=True,
    name="app.resilience.tasks.spc_workload_monitoring",
    max_retries=3,
)
def spc_workload_monitoring(self):
    """
    Monitor all residents' workload using SPC (runs daily).

    Detects Western Electric rule violations and sends alerts.
    """
    from app.db.session import SessionLocal
    from app.models.person import Person
    from app.models.assignment import Assignment
    from app.resilience.spc_monitoring import WorkloadControlChart
    from app.resilience.tasks import send_resilience_alert

    db = SessionLocal()
    try:
        # Get all residents
        residents = db.query(Person).filter(Person.type == "resident").all()

        chart = WorkloadControlChart(target_hours=60.0, sigma=5.0)
        critical_alerts = []

        for resident in residents:
            # Get last 8 weeks of hours
            # (In production, query from assignments)
            weekly_hours = get_weekly_hours(db, resident.id, weeks=8)

            if len(weekly_hours) >= 8:
                alerts = chart.detect_western_electric_violations(
                    resident_id=resident.id,
                    weekly_hours=weekly_hours,
                )

                # Collect critical alerts
                critical = [a for a in alerts if a.severity == "CRITICAL"]
                if critical:
                    critical_alerts.extend(critical)

        # Send alert if critical violations found
        if critical_alerts:
            send_resilience_alert.delay(
                level="critical",
                message=f"SPC: {len(critical_alerts)} critical workload violations detected",
                details={
                    "violations": [
                        {
                            "resident_id": str(a.resident_id),
                            "rule": a.rule,
                            "message": a.message,
                        }
                        for a in critical_alerts[:5]  # Top 5
                    ]
                },
            )

        return {
            "residents_analyzed": len(residents),
            "critical_violations": len(critical_alerts),
        }

    finally:
        db.close()


def get_weekly_hours(db, resident_id, weeks=8):
    """Helper to get weekly hours from assignments."""
    # Implementation depends on your assignment model
    # This is a simplified example
    from datetime import date, timedelta

    weekly_hours = []
    for i in range(weeks):
        week_start = date.today() - timedelta(weeks=weeks-i)
        week_end = week_start + timedelta(days=7)

        # Query assignments for this week
        # Calculate total hours
        # weekly_hours.append(total)

    return weekly_hours
```

### Example: Burnout Epidemiology Monitoring

```python
@shared_task(
    bind=True,
    name="app.resilience.tasks.burnout_epidemiology_check",
)
def burnout_epidemiology_check(self):
    """
    Monitor burnout spread using epidemiology (runs weekly).
    """
    from app.db.session import SessionLocal
    from app.resilience.burnout_epidemiology import BurnoutEpidemiology
    import networkx as nx

    db = SessionLocal()
    try:
        # Build social network from assignments
        G = build_social_network(db)

        # Get burned out residents (would use real burnout assessment)
        burned_out = get_burned_out_residents(db)

        if burned_out:
            epi = BurnoutEpidemiology(social_network=G)
            report = epi.calculate_reproduction_number(
                burned_out_residents=set(burned_out),
                time_window=timedelta(weeks=4),
            )

            # Alert if Rt > 1 (spreading)
            if report.reproduction_number >= 1.0:
                send_resilience_alert.delay(
                    level="warning",
                    message=f"Burnout spreading: Rt={report.reproduction_number:.2f}",
                    details=report.to_dict(),
                )

            return {
                "reproduction_number": report.reproduction_number,
                "status": report.status,
                "intervention_level": report.intervention_level.value,
            }

        return {"status": "no_cases"}

    finally:
        db.close()
```

---

## Prometheus Metrics

Expose metrics from cross-disciplinary modules for monitoring.

### Metrics Definition

```python
# In app/resilience/metrics.py

from prometheus_client import Counter, Gauge, Histogram

class CrossDisciplinaryMetrics:
    """Prometheus metrics for cross-disciplinary modules."""

    def __init__(self):
        # SPC Metrics
        self.spc_violations = Counter(
            'resilience_spc_violations_total',
            'Total SPC rule violations detected',
            ['rule', 'severity']
        )

        self.process_capability = Gauge(
            'resilience_process_cpk',
            'Process capability index (Cpk)',
            ['metric_type']
        )

        # Epidemiology Metrics
        self.burnout_reproduction_number = Gauge(
            'resilience_burnout_rt',
            'Burnout reproduction number (Rt)'
        )

        self.burnout_cases = Gauge(
            'resilience_burnout_cases',
            'Current burnout cases',
            ['state']  # susceptible, at_risk, burned_out, recovered
        )

        # Erlang C Metrics
        self.specialist_coverage = Gauge(
            'resilience_specialist_coverage',
            'Required specialists by specialty',
            ['specialty']
        )

        self.wait_probability = Gauge(
            'resilience_wait_probability',
            'Probability of wait for specialist',
            ['specialty']
        )

        # Fire Index Metrics
        self.burnout_danger_fwi = Gauge(
            'resilience_burnout_fwi',
            'Fire Weather Index for burnout',
            ['resident_id']
        )

        self.danger_class_count = Gauge(
            'resilience_danger_class_count',
            'Count of residents by danger class',
            ['danger_class']
        )

    def record_spc_violation(self, rule: str, severity: str):
        """Record SPC violation."""
        self.spc_violations.labels(rule=rule, severity=severity).inc()

    def update_process_capability(self, cpk: float, cp: float):
        """Update process capability metrics."""
        self.process_capability.labels(metric_type='cpk').set(cpk)
        self.process_capability.labels(metric_type='cp').set(cp)

    def update_burnout_rt(self, rt: float):
        """Update burnout reproduction number."""
        self.burnout_reproduction_number.set(rt)

    def update_specialist_coverage(self, specialty: str, required: int):
        """Update specialist coverage."""
        self.specialist_coverage.labels(specialty=specialty).set(required)
```

### Using Metrics in Endpoints

```python
from app.resilience.metrics import get_metrics

@router.post("/analytics/spc/workload")
async def analyze_workload_spc(...):
    metrics = get_metrics()

    # ... analysis code ...

    # Record violations
    for alert in alerts:
        metrics.record_spc_violation(
            rule=alert.rule,
            severity=alert.severity,
        )

    return response
```

---

## Response Schemas

Complete Pydantic schemas for all module types.

```python
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime

# SPC Schemas
class SPCAlertSchema(BaseModel):
    rule: str
    severity: str
    message: str
    resident_id: UUID | None
    timestamp: datetime
    data_points: list[float]
    control_limits: dict

# Process Capability Schemas
class ProcessCapabilitySchema(BaseModel):
    cp: float = Field(..., description="Process capability (potential)")
    cpk: float = Field(..., description="Process capability index (actual)")
    pp: float = Field(..., description="Process performance")
    ppk: float = Field(..., description="Process performance index")
    cpm: float = Field(..., description="Taguchi capability index")
    capability_status: str
    sigma_level: float
    sample_size: int
    mean: float
    std_dev: float

# Epidemiology Schemas
class EpiReportSchema(BaseModel):
    reproduction_number: float
    status: str
    secondary_cases: dict[str, int]
    recommended_interventions: list[str]
    total_cases_analyzed: int
    total_close_contacts: int
    intervention_level: str
    super_spreaders: list[UUID]
    high_risk_contacts: list[UUID]

# Erlang C Schemas
class ErlangMetricsSchema(BaseModel):
    wait_probability: float
    avg_wait_time: float
    service_level: float
    occupancy: float

# Fire Index Schemas
class FireDangerSchema(BaseModel):
    resident_id: UUID
    danger_class: str
    fwi_score: float
    component_scores: dict
    is_safe: bool
    requires_intervention: bool
    recommended_restrictions: list[str]

# Creep/Fatigue Schemas
class CreepAnalysisSchema(BaseModel):
    resident_id: UUID
    creep_stage: str
    larson_miller_parameter: float
    estimated_time_to_failure_days: int
    strain_rate: float
    recommended_stress_reduction: float

class FatigueCurveSchema(BaseModel):
    cycles_to_failure: int
    stress_amplitude: float
    current_cycles: int
    remaining_life_fraction: float
```

---

## Best Practices

### 1. Error Handling

```python
from fastapi import HTTPException

try:
    chart = WorkloadControlChart(target_hours=60, sigma=5)
    alerts = chart.detect_western_electric_violations(...)
except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
except Exception as e:
    logger.error(f"SPC analysis failed: {e}")
    raise HTTPException(status_code=500, detail="Analysis failed")
```

### 2. Input Validation

```python
class WorkloadSPCRequest(BaseModel):
    weekly_hours: list[float] = Field(
        ...,
        min_items=8,
        description="Min 8 weeks for Rule 4"
    )
    target_hours: float = Field(60.0, ge=0, le=80)

    @validator('weekly_hours')
    def validate_hours(cls, v):
        if any(h < 0 or h > 168 for h in v):
            raise ValueError("Hours must be 0-168 (hours in week)")
        return v
```

### 3. Pagination for Large Results

```python
from fastapi import Query

@router.get("/analytics/spc/history")
async def get_spc_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
):
    # ... pagination logic ...
```

### 4. Async Database Operations

```python
from sqlalchemy.ext.asyncio import AsyncSession

@router.post("/analytics/...")
async def endpoint(
    db: AsyncSession = Depends(get_async_db),
):
    # Use async queries
    result = await db.execute(select(Person).where(...))
    residents = result.scalars().all()
```

---

## Complete Example: Combined Endpoint

Here's a complete example combining multiple modules:

```python
@router.post("/analytics/burnout/comprehensive")
async def comprehensive_burnout_analysis(
    resident_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Comprehensive burnout analysis using all cross-disciplinary modules.
    """
    from app.resilience import (
        WorkloadControlChart,
        ScheduleCapabilityAnalyzer,
        BurnoutEarlyWarning,
        BurnoutDangerRating,
        CreepFatigueModel,
    )

    # Get resident data
    resident = db.query(Person).filter(Person.id == resident_id).first()
    if not resident:
        raise HTTPException(status_code=404, detail="Resident not found")

    # Get workload history
    weekly_hours = get_weekly_hours(db, resident_id, weeks=12)

    # 1. SPC Analysis
    spc_chart = WorkloadControlChart(target_hours=60, sigma=5)
    spc_alerts = spc_chart.detect_western_electric_violations(
        resident_id=resident_id,
        weekly_hours=weekly_hours,
    )

    # 2. Process Capability
    capability_analyzer = ScheduleCapabilityAnalyzer()
    capability = capability_analyzer.analyze_workload_capability(
        weekly_hours=weekly_hours,
        min_hours=40,
        max_hours=80,
    )

    # 3. Fire Danger Rating
    fire_rating = BurnoutDangerRating()
    danger = fire_rating.calculate_burnout_danger(
        resident_id=resident_id,
        recent_hours=sum(weekly_hours[-2:]) if len(weekly_hours) >= 2 else 0,
        monthly_load=sum(weekly_hours[-12:]) / 3 if len(weekly_hours) >= 12 else 0,
        yearly_satisfaction=0.7,  # Would get from survey
        workload_velocity=5.0,  # Would calculate from trend
    )

    # 4. Creep/Fatigue
    creep_model = CreepFatigueModel()
    creep_risk = creep_model.assess_combined_risk(
        resident_id=resident_id,
        sustained_workload=0.85,  # Would calculate
        duration=timedelta(days=60),
        rotation_stresses=[0.8, 0.9, 0.75, 0.85],
    )

    # Combine results
    return {
        "resident_id": str(resident_id),
        "analyzed_at": datetime.utcnow().isoformat(),
        "spc": {
            "violations": len(spc_alerts),
            "critical": len([a for a in spc_alerts if a.severity == "CRITICAL"]),
            "status": "critical" if any(a.severity == "CRITICAL" for a in spc_alerts) else "normal",
        },
        "capability": {
            "cpk": capability.cpk,
            "status": capability.capability_status,
            "sigma_level": capability.sigma_level,
        },
        "fire_danger": {
            "class": danger.danger_class.value,
            "fwi": danger.fwi_score,
            "safe": danger.is_safe,
        },
        "creep_fatigue": {
            "risk": creep_risk["overall_risk"],
            "score": creep_risk["risk_score"],
        },
        "overall_risk": _calculate_overall_risk(spc_alerts, capability, danger, creep_risk),
        "recommendations": _generate_recommendations(spc_alerts, capability, danger, creep_risk),
    }
```

---

## Testing

Example tests for endpoints:

```python
import pytest
from fastapi.testclient import TestClient

def test_spc_workload_endpoint(client: TestClient):
    """Test SPC workload analysis endpoint."""
    response = client.post(
        "/analytics/spc/workload",
        json={
            "resident_id": "123e4567-e89b-12d3-a456-426614174000",
            "weekly_hours": [58, 62, 59, 67, 71, 75, 78, 80],
            "target_hours": 60,
            "sigma": 5,
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "alerts" in data
    assert "status" in data
    assert data["target_hours"] == 60


def test_process_capability_endpoint(client: TestClient):
    """Test process capability endpoint."""
    response = client.post(
        "/analytics/capability/workload",
        json={
            "weekly_hours": [60 + i for i in range(30)],  # 30 samples
            "min_hours": 40,
            "max_hours": 80,
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "cpk" in data
    assert "capability_status" in data
```

---

## Additional Resources

- **SPC Theory**: Western Electric Statistical Quality Control Handbook (1956)
- **Six Sigma**: Montgomery, D.C. "Introduction to Statistical Quality Control"
- **Erlang C**: Cooper, R.B. "Introduction to Queuing Theory"
- **Epidemiology**: Christakis & Fowler "Connected" (2009)
- **Fire Weather**: Van Wagner "Canadian Forest Fire Weather Index" (1987)
- **Creep/Fatigue**: Larson-Miller Parameter, Miner's Rule

---

*This guide demonstrates practical FastAPI integration patterns for cross-disciplinary resilience modules. Adapt examples to your specific use cases and data models.*
