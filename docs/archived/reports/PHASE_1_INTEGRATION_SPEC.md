# Phase 1 Integration Specification: Exotic Modules

**Status**: Ready for Implementation
**Timeline**: 1 month
**Risk Level**: Low
**Effort**: 2-3 weeks

---

## Overview

Phase 1 integrates three low-risk exotic modules into the production resilience framework:

1. **Keystone Species Analysis** - Identify critical scheduling resources
2. **Catastrophe Theory Detector** - Predict system bifurcation points
3. **Zeno Governor Enforcement** - Limit human interventions that freeze solver

All three modules are already exported in `app/resilience/__init__.py` and `app/scheduling/__init__.py`.

---

## Module 1: Keystone Species Integration

### Purpose
Identify faculty, residents, and rotations whose removal would cause disproportionate schedule collapse. Used by contingency planning and N-1/N-2 analysis.

### Files Involved
- **Source**: `/backend/app/resilience/keystone_analysis.py` (700+ lines, complete)
- **New File**: `/backend/app/resilience/keystone_integration.py` (300 lines, new)
- **Modified**: `/backend/app/resilience/unified_critical_index.py`
- **Modified**: `/backend/app/resilience/service.py` (ResilienceService)
- **Tests**: `/backend/tests/resilience/test_keystone_integration.py` (new)

### Implementation Steps

#### Step 1: Create Integration Adapter
**File**: `backend/app/resilience/keystone_integration.py`

```python
"""Keystone species integration into resilience framework."""

from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.resilience.keystone_analysis import (
    KeystoneAnalyzer,
    KeystoneResource,
    KeystoneRiskLevel,
    SuccessionPlan,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class KeystoneIntegration:
    """Integrate keystone analysis into health checks."""

    def __init__(self, db: Session):
        self.db = db
        self.analyzer = KeystoneAnalyzer()

    async def identify_critical_resources(
        self,
        critical_rotation_names: Optional[list[str]] = None,
    ) -> dict[str, list[KeystoneResource]]:
        """
        Identify keystones in current schedule.

        Args:
            critical_rotation_names: Focus on these rotations (None = all)

        Returns:
            Dictionary of keystones by category:
            - faculty: Critical faculty members
            - residents: Critical residents
            - rotations: Critical rotations
        """
        # Get all people and rotations
        faculty = await self._get_active_faculty()
        residents = await self._get_active_residents()
        rotations = await self._get_rotation_templates(critical_rotation_names)

        # Analyze keystones
        keystones_faculty = await self.analyzer.identify_keystones(
            resources=faculty,
            resource_type="faculty",
            db=self.db,
        )
        keystones_residents = await self.analyzer.identify_keystones(
            resources=residents,
            resource_type="resident",
            db=self.db,
        )
        keystones_rotations = await self.analyzer.identify_keystones(
            resources=rotations,
            resource_type="rotation",
            db=self.db,
        )

        return {
            "faculty": keystones_faculty,
            "residents": keystones_residents,
            "rotations": keystones_rotations,
        }

    async def generate_succession_plans(
        self,
        keystones: dict[str, list[KeystoneResource]],
    ) -> list[SuccessionPlan]:
        """Generate succession plans for keystones."""
        plans = []

        for resource_type, keystones_list in keystones.items():
            for resource in keystones_list:
                plan = await self.analyzer.create_succession_plan(
                    keystones=resource,
                    db=self.db,
                )
                plans.append(plan)

        return plans

    # Helper methods...
```

#### Step 2: Integrate into ResilienceService
**File**: `backend/app/resilience/service.py`

Add to `ResilienceService.health_check()`:

```python
async def health_check(self, db: Session) -> HealthReport:
    """Enhanced health check with keystone analysis."""

    # ... existing checks ...

    # NEW: Keystone analysis
    keystone_integration = KeystoneIntegration(db)
    critical_resources = await keystone_integration.identify_critical_resources()
    succession_plans = await keystone_integration.generate_succession_plans(
        critical_resources
    )

    # Add to report
    report.critical_resources = critical_resources
    report.succession_plans = succession_plans

    return report
```

#### Step 3: Create API Endpoint
**File**: `backend/app/api/routes/resilience.py` (new endpoint)

```python
@router.get("/resilience/keystones")
async def get_keystone_analysis(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get keystone resource analysis for contingency planning."""
    keystone_integration = KeystoneIntegration(db)
    keystones = await keystone_integration.identify_critical_resources()
    succession_plans = await keystone_integration.generate_succession_plans(keystones)

    return {
        "keystones": keystones,
        "succession_plans": succession_plans,
        "timestamp": datetime.now(),
    }
```

#### Step 4: Test Suite
**File**: `backend/tests/resilience/test_keystone_integration.py`

```python
"""Tests for keystone integration."""

import pytest
from app.resilience.keystone_integration import KeystoneIntegration


@pytest.mark.asyncio
class TestKeystoneIntegration:
    """Test keystone identification and integration."""

    async def test_identify_keystones(self, db, faculty_with_assignments):
        """Test identification of keystone faculty."""
        integration = KeystoneIntegration(db)
        keystones = await integration.identify_critical_resources()

        assert "faculty" in keystones
        assert len(keystones["faculty"]) > 0

        # Verify keystoneness is computed
        for keystone in keystones["faculty"]:
            assert keystone.keystoneness > 0
            assert keystone.risk_level in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

    async def test_succession_planning(self, db, critical_faculty):
        """Test succession plan generation."""
        integration = KeystoneIntegration(db)
        keystones = await integration.identify_critical_resources()
        plans = await integration.generate_succession_plans(keystones)

        assert len(plans) > 0
        for plan in plans:
            assert plan.primary_resource is not None
            assert plan.replacements is not None
            assert len(plan.replacements) > 0

    async def test_cascade_prediction(self, db, faculty_network):
        """Test cascade analysis for keystone removal."""
        integration = KeystoneIntegration(db)
        analyzer = integration.analyzer

        # Simulate removing a keystone
        cascade = analyzer.analyze_cascade_impact(
            removed_resource_id=faculty_network.keystones[0].id,
            db=db,
        )

        assert cascade is not None
        assert cascade.affected_resources > 0
```

### Success Criteria
- [ ] Keystones identified in health check output
- [ ] Succession plans generated for all HIGH/CRITICAL keystones
- [ ] API endpoint returns keystones in 1 second
- [ ] Tests pass with 95%+ coverage
- [ ] Documentation updated

### Estimated Effort: 2-3 days

---

## Module 2: Catastrophe Theory Integration

### Purpose
Predict sudden system failures from gradual parameter changes. Used to detect bifurcation points in scheduling feasibility and morale.

### Files Involved
- **Source**: `/backend/app/resilience/exotic/catastrophe.py` (400+ lines, complete)
- **New File**: `/backend/app/resilience/catastrophe_integration.py` (300 lines, new)
- **Modified**: `/backend/app/scheduling/engine.py` (add post-solve check)
- **Tests**: `/backend/tests/resilience/test_catastrophe_integration.py` (new)

### Implementation Steps

#### Step 1: Create Integration Adapter
**File**: `backend/app/resilience/catastrophe_integration.py`

```python
"""Catastrophe theory integration into schedule generation."""

from app.resilience.exotic.catastrophe import (
    CatastropheDetector,
    CatastrophePoint,
    CuspParameters,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class CatastropheIntegration:
    """Detect catastrophic failures in schedule feasibility."""

    def __init__(self):
        self.detector = CatastropheDetector()

    async def assess_schedule_stability(
        self,
        resilience_metrics: dict,
    ) -> dict:
        """
        Assess if schedule is near bifurcation point.

        Args:
            resilience_metrics: Current resilience health metrics

        Returns:
            Assessment with risk level and recommendations
        """
        # Extract control parameters
        parameters = CuspParameters(
            a=resilience_metrics.get("stress_level", 0),     # Asymmetry
            b=resilience_metrics.get("workload_ratio", 0),   # Bias
            x=resilience_metrics.get("morale_index", 0.5),   # Behavior
            potential=0.0,
        )

        # Check for catastrophe regions
        assessment = self.detector.assess_feasibility_surface(
            parameters=parameters
        )

        return {
            "has_bifurcation": assessment.has_bifurcation_point,
            "bifurcation_distance": assessment.distance_to_bifurcation,
            "risk_level": assessment.risk_level,
            "recommended_actions": assessment.recommended_actions,
            "parameter_state": assessment.parameter_state,
        }

    async def generate_warnings(
        self,
        assessment: dict,
    ) -> list[str]:
        """Generate human-readable warnings."""
        warnings = []

        if assessment["has_bifurcation"]:
            distance = assessment["bifurcation_distance"]
            if distance < 0.2:
                warnings.append(
                    f"CRITICAL: Schedule near bifurcation point "
                    f"({distance:.1%} away). Risk of sudden collapse."
                )
            elif distance < 0.5:
                warnings.append(
                    f"WARNING: Schedule stability compromised "
                    f"({distance:.1%} from bifurcation). Prepare fallback."
                )

        risk_level = assessment.get("risk_level")
        if risk_level == "CRITICAL":
            warnings.append("Catastrophe risk is CRITICAL. Switch to fallback schedule.")
        elif risk_level == "HIGH":
            warnings.append("Catastrophe risk is HIGH. Consider parameter adjustments.")

        return warnings
```

#### Step 2: Integrate into Schedule Engine
**File**: `backend/app/scheduling/engine.py`

Add to `generate()` method after solver completes (around line 350):

```python
# NEW: Post-solve catastrophe detection
from app.resilience.catastrophe_integration import CatastropheIntegration

catastrophe_integration = CatastropheIntegration()
catastrophe_assessment = await catastrophe_integration.assess_schedule_stability(
    resilience_metrics=self.resilience.get_current_metrics()
)

catastrophe_warnings = await catastrophe_integration.generate_warnings(
    catastrophe_assessment
)

# Add warnings to response
schedule_result["catastrophe_assessment"] = catastrophe_assessment
schedule_result["warnings"].extend(catastrophe_warnings)

# Log critical risks
if catastrophe_assessment["risk_level"] == "CRITICAL":
    logger.error(
        f"Schedule generated near catastrophe bifurcation point. "
        f"Distance: {catastrophe_assessment['bifurcation_distance']:.1%}"
    )
```

#### Step 3: Add to Health Report
**File**: `backend/app/resilience/service.py`

```python
async def health_check(self, db: Session) -> HealthReport:
    """Health check with catastrophe detection."""

    # ... existing checks ...

    # NEW: Catastrophe assessment
    catastrophe_integration = CatastropheIntegration()
    catastrophe_assessment = await catastrophe_integration.assess_schedule_stability(
        resilience_metrics=self.get_current_metrics()
    )

    report.catastrophe_risk = catastrophe_assessment["risk_level"]
    report.bifurcation_distance = catastrophe_assessment["bifurcation_distance"]

    return report
```

#### Step 4: Test Suite
**File**: `backend/tests/resilience/test_catastrophe_integration.py`

```python
"""Tests for catastrophe integration."""

import pytest
from app.resilience.catastrophe_integration import CatastropheIntegration


@pytest.mark.asyncio
class TestCatastropheIntegration:
    """Test catastrophe detection integration."""

    async def test_stable_system(self):
        """Test stable system is not near bifurcation."""
        integration = CatastropheIntegration()
        assessment = await integration.assess_schedule_stability(
            resilience_metrics={
                "stress_level": 0.3,
                "workload_ratio": 0.7,
                "morale_index": 0.8,
            }
        )

        assert assessment["risk_level"] != "CRITICAL"
        assert assessment["bifurcation_distance"] > 0.5

    async def test_near_bifurcation(self):
        """Test detection of near-bifurcation state."""
        integration = CatastropheIntegration()
        assessment = await integration.assess_schedule_stability(
            resilience_metrics={
                "stress_level": 0.9,  # High stress
                "workload_ratio": 0.95,  # Near 100%
                "morale_index": 0.2,  # Low morale
            }
        )

        assert assessment["has_bifurcation"] is True
        assert assessment["bifurcation_distance"] < 0.3

    async def test_warning_generation(self):
        """Test warning message generation."""
        integration = CatastropheIntegration()
        assessment = {
            "has_bifurcation": True,
            "bifurcation_distance": 0.15,
            "risk_level": "CRITICAL",
        }

        warnings = await integration.generate_warnings(assessment)
        assert len(warnings) > 0
        assert any("CRITICAL" in w for w in warnings)
```

### Success Criteria
- [ ] Catastrophe assessment added to schedule generation output
- [ ] Warnings generated when near bifurcation
- [ ] Health report includes catastrophe risk
- [ ] Tests pass with 95%+ coverage
- [ ] Documentation updated

### Estimated Effort: 3-5 days

---

## Module 3: Zeno Governor Enforcement

### Purpose
Prevent human interventions (manual overrides) from freezing the solver in local optima. Limits intervention frequency and enforces "freedom windows" for solver exploration.

### Files Involved
- **Source**: `/backend/app/scheduling/zeno_governor.py` (350+ lines, complete)
- **New File**: `/backend/app/scheduling/zeno_enforcement.py` (300 lines, new)
- **Modified**: `/backend/app/api/routes/schedule.py` (edit endpoints)
- **Modified**: `/backend/app/scheduling/engine.py` (optional: tracking)
- **Tests**: `/backend/tests/scheduling/test_zeno_enforcement.py` (new)

### Implementation Steps

#### Step 1: Create Enforcement Adapter
**File**: `backend/app/scheduling/zeno_enforcement.py`

```python
"""Zeno governor enforcement for schedule editing."""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.scheduling.zeno_governor import (
    ZenoGovernor,
    ZenoRisk,
    HumanIntervention,
    InterventionPolicy,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class ZenoEnforcement:
    """Enforce Zeno governor limits on schedule modifications."""

    def __init__(self, db: Session):
        self.db = db
        self.governor = ZenoGovernor()

    async def record_intervention(
        self,
        resident_id: UUID,
        assignment_ids: list[UUID],
        reason: str,
        modified_by: UUID,
    ) -> dict:
        """
        Record a human intervention on the schedule.

        Args:
            resident_id: Who was affected
            assignment_ids: Which assignments were modified
            reason: Why the modification was made
            modified_by: Who made the modification

        Returns:
            Intervention record with risk assessment
        """
        intervention = HumanIntervention(
            timestamp=datetime.now(),
            assignment_ids=assignment_ids,
            reason=reason,
            modified_by=modified_by,
        )

        # Record in governor
        self.governor.record_intervention(intervention)

        # Check risk level
        risk = self.governor.get_risk_level()

        logger.info(
            f"Recorded intervention by {modified_by} "
            f"(reason: {reason}). Risk level: {risk}"
        )

        return {
            "intervention_id": str(intervention.id),
            "timestamp": intervention.timestamp,
            "risk_level": risk,
            "frozen_ratio": self.governor.get_frozen_ratio(),
            "intervention_count": self.governor.get_intervention_count(),
        }

    async def check_intervention_allowed(self) -> tuple[bool, Optional[str]]:
        """
        Check if another intervention is allowed.

        Returns:
            (allowed, reason_if_denied)
        """
        risk = self.governor.get_risk_level()

        if risk == ZenoRisk.CRITICAL:
            return False, (
                "Zeno governor: Too many interventions (CRITICAL risk). "
                "The frequent manual reviews are preventing the solver from "
                "exploring new solutions. Allow the solver freedom to optimize."
            )

        if risk == ZenoRisk.HIGH:
            return (
                True,
                "Warning: High intervention frequency. "
                "Consider reducing manual overrides to improve solver exploration."
            )

        return True, None

    async def get_freedom_window(self) -> dict:
        """
        Get current solver freedom window status.

        Returns:
            Window details and when next intervention is safe
        """
        window = self.governor.get_optimization_freedom_window()

        if window.is_open:
            return {
                "status": "OPEN",
                "reason": "Solver has freedom for exploration",
                "ends_at": window.end_time,
                "hours_remaining": (window.end_time - datetime.now()).total_seconds() / 3600,
            }
        else:
            return {
                "status": "CLOSED",
                "reason": "Solver is locked to preserve current schedule",
                "opens_at": window.end_time,
                "hours_until_open": (window.end_time - datetime.now()).total_seconds() / 3600,
            }

    async def get_metrics(self) -> dict:
        """Get current Zeno metrics for dashboard."""
        metrics = self.governor.get_metrics()

        return {
            "intervention_count": metrics.total_interventions,
            "frozen_ratio": metrics.frozen_ratio,
            "measurement_frequency": metrics.measurement_frequency,
            "risk_level": self.governor.get_risk_level(),
            "trend": metrics.trend,  # "INCREASING", "STABLE", "DECREASING"
            "recommendations": metrics.recommendations,
        }

    async def reset_metrics(self, reason: str) -> dict:
        """Reset intervention counter after optimization phase."""
        logger.info(f"Resetting Zeno metrics: {reason}")
        self.governor.reset_metrics()
        return await self.get_metrics()
```

#### Step 2: Integrate into Schedule Edit Routes
**File**: `backend/app/api/routes/schedule.py`

Add to any endpoint that modifies assignments:

```python
@router.post("/schedules/{schedule_id}/assignments/{assignment_id}/lock")
async def lock_assignment(
    schedule_id: UUID,
    assignment_id: UUID,
    request: AssignmentLockRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lock an assignment (human intervention)."""

    # NEW: Check Zeno limits
    zeno_enforcement = ZenoEnforcement(db)
    allowed, warning = await zeno_enforcement.check_intervention_allowed()

    if not allowed:
        raise HTTPException(status_code=429, detail=warning)

    # Record intervention
    intervention_record = await zeno_enforcement.record_intervention(
        resident_id=assignment.resident_id,
        assignment_ids=[assignment_id],
        reason=request.reason or "Manual lock",
        modified_by=current_user.id,
    )

    # Proceed with lock (with warning if needed)
    response = {"locked": True, "assignment_id": assignment_id}

    if warning:
        response["warning"] = warning

    response["zeno_metrics"] = intervention_record

    return response
```

#### Step 3: Create Dashboard Endpoint
**File**: `backend/app/api/routes/scheduling.py` (new endpoint)

```python
@router.get("/schedules/zeno-metrics")
async def get_zeno_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get Zeno governor metrics for dashboard."""
    zeno_enforcement = ZenoEnforcement(db)

    metrics = await zeno_enforcement.get_metrics()
    freedom_window = await zeno_enforcement.get_freedom_window()

    return {
        "metrics": metrics,
        "freedom_window": freedom_window,
        "timestamp": datetime.now(),
    }
```

#### Step 4: Test Suite
**File**: `backend/tests/scheduling/test_zeno_enforcement.py`

```python
"""Tests for Zeno governor enforcement."""

import pytest
from datetime import datetime, timedelta
from app.scheduling.zeno_enforcement import ZenoEnforcement


@pytest.mark.asyncio
class TestZenoEnforcement:
    """Test Zeno governor intervention limits."""

    async def test_allow_single_intervention(self, db):
        """Test single intervention is allowed."""
        enforcement = ZenoEnforcement(db)

        allowed, warning = await enforcement.check_intervention_allowed()
        assert allowed is True
        assert warning is None

    async def test_reject_excessive_interventions(self, db):
        """Test excessive interventions are rejected."""
        enforcement = ZenoEnforcement(db)

        # Record many interventions quickly
        for i in range(20):
            await enforcement.record_intervention(
                resident_id=None,
                assignment_ids=[],
                reason=f"Test intervention {i}",
                modified_by=None,
            )

        # Should now be rejected
        allowed, warning = await enforcement.check_intervention_allowed()
        assert allowed is False
        assert "CRITICAL" in warning

    async def test_freedom_window_status(self, db):
        """Test freedom window reporting."""
        enforcement = ZenoEnforcement(db)

        window = await enforcement.get_freedom_window()
        assert "status" in window
        assert "ends_at" in window or "opens_at" in window

    async def test_metrics_tracking(self, db):
        """Test metric collection."""
        enforcement = ZenoEnforcement(db)

        # Record intervention
        await enforcement.record_intervention(
            resident_id=None,
            assignment_ids=[],
            reason="Test",
            modified_by=None,
        )

        # Get metrics
        metrics = await enforcement.get_metrics()
        assert metrics["intervention_count"] >= 1
        assert "risk_level" in metrics
```

### Success Criteria
- [ ] Interventions tracked in enforcement system
- [ ] Rate limiting enforced (CRITICAL risk blocks edits)
- [ ] Dashboard shows metrics and freedom window
- [ ] Warnings shown when approaching limits
- [ ] Tests pass with 95%+ coverage
- [ ] Documentation updated

### Estimated Effort: 5-7 days

---

## Testing Strategy

### Unit Tests
- Test each module independently
- Mock database and dependencies
- Coverage target: 95%+

### Integration Tests
- Test interaction with resilience framework
- Test interaction with schedule engine
- End-to-end workflows

### Stress Tests
- Keystone: 1000+ faculty members
- Catastrophe: Extreme parameter ranges
- Zeno: Rapid intervention bursts

### Load Tests
- Each module must complete in <1 second
- Health check with all three modules in <2 seconds

---

## Documentation Updates

1. **README.md**: Add Phase 1 features to feature list
2. **docs/architecture/**: Create `phase-1-exotic-integration.md`
3. **docs/api/**: Document new endpoints
4. **CHANGELOG.md**: Document changes
5. **Code comments**: Update module docstrings

---

## Rollout Plan

### Week 1-2: Development
- Implement all three modules
- Write comprehensive tests
- Internal code review

### Week 3: Testing
- Run integration tests
- Stress testing
- Load testing
- Documentation review

### Week 4: Deployment
- Deploy to staging
- 1-week monitoring
- Deploy to production
- Monitor metrics

---

## Success Metrics

| Metric | Target | Success Criteria |
|--------|--------|-----------------|
| Code Coverage | 95%+ | All paths tested |
| Response Time | <1s | No slowdown |
| Bug Rate | 0 P0s | Zero critical bugs |
| Adoption | 100% | Used in all schedules |
| Faculty Feedback | Positive | >4/5 satisfaction |

---

## Contingency Plans

If issues arise:

1. **Keystone analysis too slow**: Cache results, run async
2. **Catastrophe false positives**: Tune parameters
3. **Zeno blocking users**: Reduce intervention limit
4. **Integration breaks existing code**: Feature flags to disable

---

## Sign-Off

- [ ] Product Manager approval
- [ ] Technical Lead approval
- [ ] Security review
- [ ] Documentation review

---

**Document Status**: Ready for Implementation
**Last Updated**: 2025-12-31
**Next Review**: 2026-01-31
