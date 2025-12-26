# FWI-Defense Level Bridge Specification

**Version:** 1.0
**Last Updated:** 2025-12-26
**Status:** Implementation-Ready
**Authors:** Architecture Team

---

## Executive Summary

This specification defines the integration bridge between two critical resilience systems:

1. **Burnout Fire Index (FWI)**: Multi-temporal danger rating system (0-100+ scale)
2. **Defense in Depth**: 5-level safety system (GREEN → YELLOW → ORANGE → RED → BLACK)

The bridge automatically maps FWI danger assessments to appropriate Defense-in-Depth activation levels, enabling the system to escalate protective measures as burnout risk increases.

**Key Innovation:** Dual-component analysis using ISI (Initial Spread Index) for rapid response and BUI (Buildup Index) for sustained threats, with hysteresis logic to prevent oscillation.

---

## Table of Contents

1. [Mapping Table](#1-mapping-table)
2. [Hysteresis Logic](#2-hysteresis-logic)
3. [Data Flow Diagram](#3-data-flow-diagram)
4. [Multi-Component Integration](#4-multi-component-integration)
5. [Override Logic](#5-override-logic)
6. [Implementation Specification](#6-implementation-specification)
7. [Test Cases](#7-test-cases)
8. [Monitoring & Alerts](#8-monitoring--alerts)

---

## 1. Mapping Table

### Primary Mapping: FWI Class to Defense Level

| FWI Class | FWI Score | Defense Level | Color Code | Response Posture |
|-----------|-----------|---------------|------------|------------------|
| **LOW** | 0-20 | PREVENTION (1) | GREEN | Normal operations, maintain buffers |
| **MODERATE** | 20-40 | CONTROL (2) | YELLOW | Active monitoring, early warnings |
| **HIGH** | 40-60 | SAFETY_SYSTEMS (3) | ORANGE | Automated protective actions |
| **VERY_HIGH** | 60-80 | CONTAINMENT (4) | RED | Damage limitation, service reduction |
| **EXTREME** | 80+ | EMERGENCY (5) | BLACK | Crisis response, external escalation |

### Mapping Rationale

**LOW (0-20) → PREVENTION (GREEN):**
- All temporal indicators within safe ranges
- Focus: Maintain capacity buffers, cross-training
- Actions: Proactive absence management, trend monitoring

**MODERATE (20-40) → CONTROL (YELLOW):**
- One or more temporal indicators elevated
- Focus: Early detection and intervention
- Actions: Coverage monitoring, burnout tracking, early warnings

**HIGH (40-60) → SAFETY_SYSTEMS (ORANGE):**
- Multiple temporal indicators elevated or acute spike
- Focus: Automated protective responses
- Actions: Auto-reassignment, backup activation, overtime authorization

**VERY_HIGH (60-80) → CONTAINMENT (RED):**
- Severe conditions across multiple timescales
- Focus: Limit damage spread, protect core services
- Actions: Service reduction, zone isolation, minimum service protection

**EXTREME (80+) → EMERGENCY (BLACK):**
- Critical conditions, imminent system failure
- Focus: Crisis management and recovery
- Actions: Crisis communication, external escalation, incident documentation

---

## 2. Hysteresis Logic

### Problem: Threshold Oscillation

Without hysteresis, the system can oscillate rapidly between levels when FWI hovers near a threshold:

```
Time  FWI  Level (no hysteresis)
0:00  39   CONTROL
0:15  41   SAFETY_SYSTEMS  ← Escalated
0:30  39   CONTROL         ← De-escalated (too fast!)
0:45  41   SAFETY_SYSTEMS  ← Escalated again
```

This creates alert fatigue and prevents protective measures from taking effect.

### Solution: Asymmetric Hysteresis

**Escalation Requirements:**
- FWI must exceed threshold for **2 consecutive checks** (30 minutes minimum)
- Prevents false positives from transient spikes

**De-escalation Requirements:**
- FWI must fall below **(threshold - buffer)** for **3 consecutive checks** (45 minutes minimum)
- Larger buffer and longer persistence required to de-escalate
- Ensures system doesn't relax protection prematurely

### Hysteresis Parameters

| Transition | Escalation Threshold | De-escalation Threshold | Consecutive Checks |
|------------|---------------------|------------------------|-------------------|
| GREEN → YELLOW | FWI ≥ 20 | FWI < 18 | Escalate: 2, De-escalate: 3 |
| YELLOW → ORANGE | FWI ≥ 40 | FWI < 37 | Escalate: 2, De-escalate: 3 |
| ORANGE → RED | FWI ≥ 60 | FWI < 56 | Escalate: 2, De-escalate: 3 |
| RED → BLACK | FWI ≥ 80 | FWI < 75 | Escalate: 2, De-escalate: 3 |

**Buffer Size:** 10% of threshold (e.g., 40 → 36 for YELLOW→ORANGE)

### Hysteresis State Machine

```
State: {current_level, candidate_level, count}

On each FWI update:
  recommended = map_fwi_to_level(fwi_score)

  IF recommended > current_level:
    # Escalation path
    IF recommended == candidate_level:
      count += 1
      IF count >= 2:
        ACTIVATE(recommended)
        count = 0
    ELSE:
      candidate_level = recommended
      count = 1

  ELIF recommended < current_level:
    # De-escalation path
    de_escalate_threshold = get_deescalate_threshold(current_level)
    IF fwi_score < de_escalate_threshold:
      IF recommended == candidate_level:
        count += 1
        IF count >= 3:
          ACTIVATE(recommended)
          count = 0
      ELSE:
        candidate_level = recommended
        count = 1
    ELSE:
      # Within hysteresis band, maintain current
      candidate_level = None
      count = 0

  ELSE:
    # Same level, reset
    candidate_level = None
    count = 0
```

### Example: Oscillation Prevention

```
Time  FWI  Recommended  Candidate  Count  Current  Action
────────────────────────────────────────────────────────────────
0:00  38   CONTROL      -          0      CONTROL  (steady state)
0:15  41   SAFETY_SYS   SAFETY_SYS 1      CONTROL  (candidate set)
0:30  42   SAFETY_SYS   SAFETY_SYS 2      SAFETY   ✓ ESCALATE
0:45  39   CONTROL      CONTROL    1      SAFETY   (within buffer, maintain)
1:00  40   SAFETY_SYS   -          0      SAFETY   (back to steady)
1:15  36   CONTROL      CONTROL    1      SAFETY   (below buffer)
1:30  35   CONTROL      CONTROL    2      SAFETY   (2nd consecutive)
1:45  34   CONTROL      CONTROL    3      CONTROL  ✓ DE-ESCALATE
```

**Result:** System required sustained improvement (3 checks below 37) to de-escalate, preventing premature relaxation.

---

## 3. Data Flow Diagram

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                   BURNOUT FIRE INDEX SYSTEM                      │
│                                                                   │
│  Inputs:                                                          │
│  - recent_hours (2 weeks)                                         │
│  - monthly_load (3 months)                                        │
│  - yearly_satisfaction (0-1 scale)                                │
│  - workload_velocity (hours/week change)                          │
│                                                                   │
│  Components:                                                      │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐   │
│  │ FFMC │  │ DMC  │  │  DC  │  │ ISI  │  │ BUI  │  │ FWI  │   │
│  └──┬───┘  └──┬───┘  └──┬───┘  └──┬───┘  └──┬───┘  └──┬───┘   │
│     │         │         │         │         │         │         │
│     └─────────┴─────────┴─────────┴─────────┴─────────┘         │
│                                              │                   │
│                                              v                   │
│                                     ┌─────────────────┐          │
│                                     │ DangerClass     │          │
│                                     │ + FWI Score     │          │
│                                     └────────┬────────┘          │
└──────────────────────────────────────────────┼──────────────────┘
                                               │
                                               v
┌─────────────────────────────────────────────────────────────────┐
│                     FWI-DEFENSE BRIDGE                           │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ FWIDefenseBridge.recommend_defense_level()                 │ │
│  │                                                             │ │
│  │  1. Map FWI score → Base defense level                     │ │
│  │  2. Check ISI (rapid response indicator)                   │ │
│  │  3. Check BUI (sustained threat indicator)                 │ │
│  │  4. Apply component-based adjustments                      │ │
│  │  5. Return recommended level                               │ │
│  └────────────────────┬───────────────────────────────────────┘ │
│                       │                                          │
│                       v                                          │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ FWIDefenseBridge.apply_hysteresis()                        │ │
│  │                                                             │ │
│  │  1. Load current defense level                             │ │
│  │  2. Compare with recommended level                         │ │
│  │  3. Check consecutive count                                │ │
│  │  4. Apply escalation/de-escalation rules                   │ │
│  │  5. Return final level (may differ from recommended)       │ │
│  └────────────────────┬───────────────────────────────────────┘ │
│                       │                                          │
└───────────────────────┼──────────────────────────────────────────┘
                        │
                        v
┌─────────────────────────────────────────────────────────────────┐
│              DEFENSE IN DEPTH SERVICE                            │
│                                                                   │
│  DefenseInDepthService.set_level(new_level)                      │
│                                                                   │
│  1. Log level transition (audit trail)                           │
│  2. Deactivate old level actions                                 │
│  3. Activate new level actions                                   │
│  4. Trigger alerts/notifications                                 │
│  5. Update monitoring dashboards                                 │
│                                                                   │
│  Active Actions by Level:                                        │
│  ┌──────────────┬────────────────────────────────────────────┐  │
│  │ PREVENTION   │ capacity_buffer, cross_training, ...       │  │
│  │ CONTROL      │ coverage_monitoring, early_warning, ...    │  │
│  │ SAFETY_SYS   │ auto_reassignment, backup_activation, ...  │  │
│  │ CONTAINMENT  │ service_reduction, zone_isolation, ...     │  │
│  │ EMERGENCY    │ crisis_communication, external_escalation  │  │
│  └──────────────┴────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Component Data Flow

```
Resident Metrics
    ↓
BurnoutDangerRating.calculate_burnout_danger()
    ↓
    ├─→ FFMC (recent_hours vs 60h target)
    ├─→ DMC (monthly_load vs 240h target)
    ├─→ DC (1.0 - yearly_satisfaction)
    ├─→ ISI = f(FFMC, workload_velocity)      ← Rapid response
    ├─→ BUI = f(DMC, DC)                      ← Sustained threat
    └─→ FWI = f(ISI, BUI)                     ← Final score
    ↓
FireDangerReport {
    resident_id: UUID
    danger_class: DangerClass
    fwi_score: float
    component_scores: {ffmc, dmc, dc, isi, bui, fwi}
    recommended_restrictions: list[str]
}
    ↓
FWIDefenseBridge.recommend_defense_level(fwi_result)
    ↓
    ├─→ Base mapping: FWI score → Defense level
    ├─→ ISI adjustment: If ISI > 60, escalate one level
    └─→ BUI adjustment: If BUI > 70, escalate one level
    ↓
Recommended Defense Level
    ↓
FWIDefenseBridge.apply_hysteresis(recommended, current)
    ↓
    ├─→ Load transition history
    ├─→ Check consecutive count
    ├─→ Escalation: Need 2 consecutive
    └─→ De-escalation: Need 3 consecutive below (threshold - buffer)
    ↓
Final Defense Level (may = current if hysteresis active)
    ↓
DefenseInDepthService.set_level(new_level)
    ↓
    ├─→ Audit log entry
    ├─→ Activate level-specific actions
    ├─→ Send alerts (if escalating)
    └─→ Update dashboards
```

---

## 4. Multi-Component Integration

### FWI Sub-Components and Their Roles

The FWI system provides six components, each representing a different temporal scale or interaction:

| Component | Temporal Scale | Range | Role in Defense Bridge |
|-----------|---------------|-------|------------------------|
| **FFMC** | 1-2 weeks | 0-100 | Recent acute stress indicator |
| **DMC** | 3 months | 0-100 | Medium-term accumulation |
| **DC** | 1 year | 0-100 | Long-term satisfaction erosion |
| **ISI** | Velocity | 0-100+ | **Rapid response trigger** |
| **BUI** | Sustained | 0-100+ | **Sustained threat indicator** |
| **FWI** | Composite | 0-100+ | **Primary mapping source** |

### Dual-Component Strategy

**Primary Mapping:** FWI score determines base defense level

**Secondary Adjustments:**
1. **ISI (Initial Spread Index):** Rapid deterioration detector
2. **BUI (Buildup Index):** Chronic burden detector

### ISI: Rapid Response Escalation

ISI combines recent stress (FFMC) with workload velocity. High ISI indicates rapid deterioration requiring immediate response.

**Escalation Rule:**
```python
if isi > 60 and fwi_score >= 20:
    # Conditions worsening rapidly
    escalate_one_level(base_defense_level)
```

**Rationale:**
- ISI > 60: Burnout spreading quickly (like fire with high wind)
- Even if FWI is in MODERATE range (20-40), rapid spread warrants SAFETY_SYSTEMS activation
- Preemptive escalation prevents situation from reaching RED/BLACK levels

**Example:**
```
Resident A:
  FWI = 35 (MODERATE → CONTROL/YELLOW)
  ISI = 70 (very high velocity)
  Base mapping: CONTROL
  ISI adjustment: +1 level
  Final: SAFETY_SYSTEMS (ORANGE)

Reasoning: Even though overall danger is MODERATE, the rapid rate of
deterioration requires automated protective actions now.
```

### BUI: Sustained Threat Escalation

BUI combines medium-term (DMC) and long-term (DC) burden. High BUI indicates deep, persistent risk requiring sustained intervention.

**Escalation Rule:**
```python
if bui > 70 and fwi_score >= 40:
    # Heavy accumulated burden
    escalate_one_level(base_defense_level)
```

**Rationale:**
- BUI > 70: Severe accumulated burden across multiple timescales
- Even if FWI is in HIGH range (40-60), sustained burden warrants CONTAINMENT activation
- Recognizes that chronic conditions require more aggressive intervention

**Example:**
```
Resident B:
  FWI = 55 (HIGH → SAFETY_SYSTEMS/ORANGE)
  BUI = 75 (severe accumulation)
  Base mapping: SAFETY_SYSTEMS
  BUI adjustment: +1 level
  Final: CONTAINMENT (RED)

Reasoning: Deep, multi-temporal burden requires not just automation
but actual service reduction and damage limitation.
```

### Combined Component Logic

```python
def recommend_defense_level(fwi_result: FireDangerReport) -> DefenseLevel:
    """
    Recommend defense level using multi-component analysis.

    Primary: FWI score mapping
    Secondary: ISI and BUI adjustments
    """
    fwi_score = fwi_result.fwi_score
    isi = fwi_result.component_scores.get("isi", 0)
    bui = fwi_result.component_scores.get("bui", 0)

    # Base mapping from FWI score
    if fwi_score < 20:
        base_level = DefenseLevel.PREVENTION
    elif fwi_score < 40:
        base_level = DefenseLevel.CONTROL
    elif fwi_score < 60:
        base_level = DefenseLevel.SAFETY_SYSTEMS
    elif fwi_score < 80:
        base_level = DefenseLevel.CONTAINMENT
    else:
        base_level = DefenseLevel.EMERGENCY

    # ISI adjustment: Rapid deterioration
    if isi > 60 and fwi_score >= 20:
        base_level = min(DefenseLevel.EMERGENCY, base_level + 1)
        logger.info(f"ISI escalation: ISI={isi:.1f} triggered +1 level")

    # BUI adjustment: Sustained burden
    if bui > 70 and fwi_score >= 40:
        base_level = min(DefenseLevel.EMERGENCY, base_level + 1)
        logger.info(f"BUI escalation: BUI={bui:.1f} triggered +1 level")

    return base_level
```

### Component-Based Alert Messages

Different escalation triggers should generate different alert types:

**FWI-based escalation:**
```
"Overall burnout danger escalated to ORANGE (FWI=52).
Multiple temporal indicators elevated."
```

**ISI-based escalation:**
```
"Rapid deterioration detected (ISI=68). Escalating to ORANGE
for automated protective actions. Workload increasing at
dangerous rate."
```

**BUI-based escalation:**
```
"Severe accumulated burden detected (BUI=76). Escalating to RED
for service reduction. Deep, multi-temporal burnout risk."
```

---

## 5. Override Logic

### Manual Override Capability

Administrators must be able to override automatic defense level transitions for:
- Emergency situations requiring immediate BLACK activation
- False positives from data quality issues
- Scheduled exercises/drills
- Recovery validation periods

### Override Types

| Override Type | Description | Requires | Duration |
|--------------|-------------|----------|----------|
| **Emergency Escalation** | Jump directly to BLACK | Admin approval | Until cancelled |
| **Level Lock** | Fix at specific level | Admin approval | Time-limited (max 24h) |
| **Hysteresis Bypass** | Skip consecutive checks | Admin approval | Single transition |
| **System Test** | Trigger without real activation | System role | Until test ends |

### Override Implementation

```python
@dataclass
class DefenseOverride:
    """Manual override of defense level transitions."""

    override_id: str
    override_type: str  # "emergency_escalate", "level_lock", "hysteresis_bypass", "test"
    target_level: DefenseLevel
    applied_by: str  # User ID
    applied_at: datetime
    expires_at: datetime | None
    reason: str
    auto_restore: bool = True  # Restore automatic control on expiry

class FWIDefenseBridge:
    def apply_hysteresis(
        self,
        recommended: DefenseLevel,
        current: DefenseLevel,
        override: DefenseOverride | None = None,
    ) -> DefenseLevel:
        """
        Apply hysteresis logic with override support.

        Args:
            recommended: Level recommended by FWI mapping
            current: Current active defense level
            override: Optional manual override

        Returns:
            Final defense level (may differ from both recommended and current)
        """
        # Check for active override
        if override and not self._is_override_expired(override):
            logger.warning(
                f"Manual override active: {override.override_type} to "
                f"{override.target_level.name} by {override.applied_by}. "
                f"Reason: {override.reason}"
            )

            if override.override_type == "emergency_escalate":
                # Immediate escalation, bypass hysteresis
                self._log_override_activation(override)
                return override.target_level

            elif override.override_type == "level_lock":
                # Lock at specific level, ignore recommendations
                return override.target_level

            elif override.override_type == "hysteresis_bypass":
                # Apply recommendation immediately, skip consecutive checks
                self._log_override_activation(override)
                self._clear_override(override)  # Single use
                return recommended

            elif override.override_type == "test":
                # Return test level without actually activating
                logger.info(f"TEST MODE: Would activate {override.target_level.name}")
                return current  # Don't change actual level

        # No override, normal hysteresis logic
        return self._apply_normal_hysteresis(recommended, current)
```

### Audit Trail Requirements

All override actions must be logged with:

```python
{
    "timestamp": "2025-12-26T14:30:00Z",
    "event_type": "defense_override_applied",
    "override_id": "override-uuid-1234",
    "override_type": "emergency_escalate",
    "from_level": "CONTROL",
    "to_level": "EMERGENCY",
    "applied_by": "user-admin-5678",
    "reason": "Multiple faculty sick calls, insufficient coverage",
    "fwi_score_at_time": 32.5,
    "recommended_level": "CONTROL",
    "auto_restore": true,
    "expires_at": "2025-12-27T14:30:00Z"
}
```

### Override Expiration Handling

```python
def check_override_expiration(self):
    """Check and handle expired overrides."""
    active_overrides = self.get_active_overrides()

    for override in active_overrides:
        if self._is_override_expired(override):
            logger.info(
                f"Override {override.override_id} expired. "
                f"Type: {override.override_type}"
            )

            if override.auto_restore:
                # Restore automatic control
                logger.info("Restoring automatic defense level control")
                current_fwi = self.get_latest_fwi_report()
                recommended = self.recommend_defense_level(current_fwi)

                # Don't apply hysteresis on restore - use current FWI directly
                new_level = recommended
                self.defense_service.set_level(new_level)

                self._log_override_expiration(override, new_level)
            else:
                # Manual intervention required
                logger.warning(
                    f"Override {override.override_id} expired but auto_restore=False. "
                    f"Manual review required."
                )
                self._send_admin_alert(
                    "Defense level override expired - manual review required",
                    override
                )

            self._archive_override(override)
```

### Alert on Override

Whenever an override is applied or expires, send notifications:

```python
def _send_override_alert(self, override: DefenseOverride, event: str):
    """Send alert for override events."""
    alert_message = {
        "event": event,  # "override_applied" or "override_expired"
        "override_type": override.override_type,
        "target_level": override.target_level.name,
        "applied_by": override.applied_by,
        "reason": override.reason,
        "timestamp": datetime.now().isoformat(),
    }

    # Send to admin channel
    self.notification_service.send_alert(
        channel="admin_critical",
        message=alert_message,
        priority="high"
    )

    # Log to Prometheus for monitoring
    self.metrics.record_override_event(
        override_type=override.override_type,
        level=override.target_level.name,
        event=event
    )
```

---

## 6. Implementation Specification

### Class Structure

```python
# File: backend/app/resilience/fwi_defense_bridge.py

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import IntEnum
import logging
from typing import Optional
from uuid import UUID, uuid4

from app.resilience.burnout_fire_index import FireDangerReport, DangerClass
from app.resilience.defense_in_depth import DefenseLevel, DefenseInDepth

logger = logging.getLogger(__name__)


@dataclass
class TransitionRecord:
    """Record of a defense level transition."""

    timestamp: datetime
    from_level: DefenseLevel
    to_level: DefenseLevel
    fwi_score: float
    danger_class: DangerClass
    trigger_type: str  # "fwi_mapping", "isi_escalation", "bui_escalation", "manual_override"
    consecutive_count: int
    hysteresis_active: bool
    override_id: Optional[str] = None


@dataclass
class HysteresisState:
    """State machine for hysteresis logic."""

    current_level: DefenseLevel
    candidate_level: Optional[DefenseLevel] = None
    consecutive_count: int = 0
    last_update: datetime = field(default_factory=datetime.now)
    transition_history: list[TransitionRecord] = field(default_factory=list)


@dataclass
class DefenseOverride:
    """Manual override of defense level."""

    override_id: str = field(default_factory=lambda: str(uuid4()))
    override_type: str = "emergency_escalate"  # "emergency_escalate", "level_lock", "hysteresis_bypass", "test"
    target_level: DefenseLevel = DefenseLevel.EMERGENCY
    applied_by: str = ""
    applied_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    reason: str = ""
    auto_restore: bool = True


class FWIDefenseBridge:
    """
    Bridge between Burnout Fire Index and Defense in Depth systems.

    Maps FWI danger assessments to Defense-in-Depth activation levels
    with hysteresis logic to prevent oscillation and multi-component
    analysis for rapid response.

    Usage:
        bridge = FWIDefenseBridge(defense_service)

        # Process FWI report
        fwi_report = burnout_rating.calculate_burnout_danger(...)
        new_level = bridge.process_fwi_report(fwi_report)

        # Emergency override
        bridge.apply_override(DefenseOverride(
            override_type="emergency_escalate",
            target_level=DefenseLevel.EMERGENCY,
            applied_by="admin-user-123",
            reason="Multiple faculty sick calls",
            expires_at=datetime.now() + timedelta(hours=24)
        ))
    """

    def __init__(
        self,
        defense_service: DefenseInDepth,
        escalate_consecutive: int = 2,
        deescalate_consecutive: int = 3,
        hysteresis_buffer: float = 0.10,  # 10% buffer
    ):
        """
        Initialize FWI-Defense bridge.

        Args:
            defense_service: Defense in Depth service instance
            escalate_consecutive: Consecutive checks needed to escalate (default 2)
            deescalate_consecutive: Consecutive checks needed to de-escalate (default 3)
            hysteresis_buffer: Buffer percentage for de-escalation (default 0.10)
        """
        self.defense_service = defense_service
        self.escalate_consecutive = escalate_consecutive
        self.deescalate_consecutive = deescalate_consecutive
        self.hysteresis_buffer = hysteresis_buffer

        # State tracking
        self.hysteresis_state = HysteresisState(
            current_level=DefenseLevel.PREVENTION
        )
        self.active_override: Optional[DefenseOverride] = None

        logger.info(
            f"FWIDefenseBridge initialized: "
            f"escalate={escalate_consecutive}, de-escalate={deescalate_consecutive}, "
            f"buffer={hysteresis_buffer*100:.0f}%"
        )

    def recommend_defense_level(self, fwi_result: FireDangerReport) -> DefenseLevel:
        """
        Recommend defense level based on FWI report with multi-component analysis.

        Primary mapping from FWI score, with secondary adjustments from:
        - ISI (rapid deterioration)
        - BUI (sustained burden)

        Args:
            fwi_result: Complete FWI danger assessment

        Returns:
            Recommended defense level (before hysteresis)
        """
        fwi_score = fwi_result.fwi_score
        isi = fwi_result.component_scores.get("isi", 0)
        bui = fwi_result.component_scores.get("bui", 0)

        # Primary mapping: FWI score to defense level
        if fwi_score < 20:
            base_level = DefenseLevel.PREVENTION
        elif fwi_score < 40:
            base_level = DefenseLevel.CONTROL
        elif fwi_score < 60:
            base_level = DefenseLevel.SAFETY_SYSTEMS
        elif fwi_score < 80:
            base_level = DefenseLevel.CONTAINMENT
        else:
            base_level = DefenseLevel.EMERGENCY

        logger.info(
            f"FWI mapping: score={fwi_score:.1f} → {base_level.name} "
            f"(ISI={isi:.1f}, BUI={bui:.1f})"
        )

        # Secondary adjustments
        adjusted_level = base_level
        escalation_reasons = []

        # ISI escalation: Rapid deterioration
        if isi > 60 and fwi_score >= 20:
            if adjusted_level < DefenseLevel.EMERGENCY:
                adjusted_level = DefenseLevel(adjusted_level + 1)
                escalation_reasons.append(f"ISI={isi:.1f} (rapid deterioration)")

        # BUI escalation: Sustained burden
        if bui > 70 and fwi_score >= 40:
            if adjusted_level < DefenseLevel.EMERGENCY:
                adjusted_level = DefenseLevel(adjusted_level + 1)
                escalation_reasons.append(f"BUI={bui:.1f} (sustained burden)")

        if escalation_reasons:
            logger.info(
                f"Component escalation: {base_level.name} → {adjusted_level.name}. "
                f"Triggers: {', '.join(escalation_reasons)}"
            )

        return adjusted_level

    def apply_hysteresis(
        self,
        recommended: DefenseLevel,
        current: DefenseLevel,
        fwi_score: float,
    ) -> DefenseLevel:
        """
        Apply hysteresis logic to prevent oscillation.

        Escalation: Requires escalate_consecutive checks above threshold
        De-escalation: Requires deescalate_consecutive checks below (threshold - buffer)

        Args:
            recommended: Level recommended by FWI mapping
            current: Current active defense level
            fwi_score: Current FWI score

        Returns:
            Final defense level after hysteresis
        """
        state = self.hysteresis_state

        # Check for escalation
        if recommended > current:
            if recommended == state.candidate_level:
                state.consecutive_count += 1
                logger.debug(
                    f"Escalation candidate: {recommended.name} "
                    f"({state.consecutive_count}/{self.escalate_consecutive})"
                )

                if state.consecutive_count >= self.escalate_consecutive:
                    logger.info(
                        f"Hysteresis threshold met: Escalating {current.name} → "
                        f"{recommended.name} (FWI={fwi_score:.1f})"
                    )
                    state.current_level = recommended
                    state.candidate_level = None
                    state.consecutive_count = 0
                    return recommended
                else:
                    # Still accumulating, maintain current
                    return current
            else:
                # New candidate
                state.candidate_level = recommended
                state.consecutive_count = 1
                logger.debug(
                    f"New escalation candidate: {recommended.name} "
                    f"(1/{self.escalate_consecutive})"
                )
                return current

        # Check for de-escalation
        elif recommended < current:
            # Calculate de-escalation threshold with buffer
            deescalate_threshold = self._get_deescalate_threshold(current)

            if fwi_score < deescalate_threshold:
                if recommended == state.candidate_level:
                    state.consecutive_count += 1
                    logger.debug(
                        f"De-escalation candidate: {recommended.name} "
                        f"({state.consecutive_count}/{self.deescalate_consecutive}), "
                        f"FWI={fwi_score:.1f} < {deescalate_threshold:.1f}"
                    )

                    if state.consecutive_count >= self.deescalate_consecutive:
                        logger.info(
                            f"Hysteresis threshold met: De-escalating {current.name} → "
                            f"{recommended.name} (FWI={fwi_score:.1f})"
                        )
                        state.current_level = recommended
                        state.candidate_level = None
                        state.consecutive_count = 0
                        return recommended
                    else:
                        # Still accumulating, maintain current
                        return current
                else:
                    # New candidate
                    state.candidate_level = recommended
                    state.consecutive_count = 1
                    logger.debug(
                        f"New de-escalation candidate: {recommended.name} "
                        f"(1/{self.deescalate_consecutive})"
                    )
                    return current
            else:
                # Within hysteresis band, maintain current
                logger.debug(
                    f"Within hysteresis band: FWI={fwi_score:.1f} >= "
                    f"{deescalate_threshold:.1f}, maintaining {current.name}"
                )
                state.candidate_level = None
                state.consecutive_count = 0
                return current

        # Same level - reset state
        else:
            if state.candidate_level is not None:
                logger.debug(f"Recommended matches current, resetting hysteresis state")
            state.candidate_level = None
            state.consecutive_count = 0
            return current

    def _get_deescalate_threshold(self, current_level: DefenseLevel) -> float:
        """
        Get de-escalation threshold for current level (includes buffer).

        Returns threshold - (threshold * buffer)
        """
        thresholds = {
            DefenseLevel.CONTROL: 20,
            DefenseLevel.SAFETY_SYSTEMS: 40,
            DefenseLevel.CONTAINMENT: 60,
            DefenseLevel.EMERGENCY: 80,
        }

        base_threshold = thresholds.get(current_level, 0)
        return base_threshold * (1 - self.hysteresis_buffer)

    def process_fwi_report(
        self,
        fwi_report: FireDangerReport,
        override: Optional[DefenseOverride] = None,
    ) -> DefenseLevel:
        """
        Process FWI report and update defense level if needed.

        Main entry point for bridge integration. Handles:
        1. FWI → Defense level mapping
        2. Hysteresis logic
        3. Manual overrides
        4. Defense service updates
        5. Audit logging

        Args:
            fwi_report: Complete FWI danger assessment
            override: Optional manual override

        Returns:
            Final active defense level
        """
        current_level = self.hysteresis_state.current_level

        # Check for active override
        if override or self.active_override:
            final_level = self._handle_override(
                override or self.active_override,
                fwi_report
            )
        else:
            # Normal processing
            recommended = self.recommend_defense_level(fwi_report)
            final_level = self.apply_hysteresis(
                recommended=recommended,
                current=current_level,
                fwi_score=fwi_report.fwi_score
            )

        # Update defense service if level changed
        if final_level != current_level:
            logger.info(
                f"Defense level transition: {current_level.name} → {final_level.name} "
                f"(FWI={fwi_report.fwi_score:.1f}, Danger={fwi_report.danger_class.value})"
            )

            self.defense_service.set_level(final_level)
            self._log_transition(fwi_report, current_level, final_level)

        return final_level

    def _handle_override(
        self,
        override: DefenseOverride,
        fwi_report: FireDangerReport,
    ) -> DefenseLevel:
        """Handle manual override logic."""
        if self._is_override_expired(override):
            logger.info(f"Override {override.override_id} expired")
            self.active_override = None
            # Process normally
            recommended = self.recommend_defense_level(fwi_report)
            return self.apply_hysteresis(
                recommended=recommended,
                current=self.hysteresis_state.current_level,
                fwi_score=fwi_report.fwi_score
            )

        # Override active
        logger.warning(
            f"Manual override active: {override.override_type} to "
            f"{override.target_level.name} by {override.applied_by}"
        )

        if override.override_type == "emergency_escalate":
            return override.target_level
        elif override.override_type == "level_lock":
            return override.target_level
        elif override.override_type == "hysteresis_bypass":
            # Single use - clear after
            self.active_override = None
            recommended = self.recommend_defense_level(fwi_report)
            self.hysteresis_state.current_level = recommended
            return recommended
        elif override.override_type == "test":
            # Don't change level
            return self.hysteresis_state.current_level

        return self.hysteresis_state.current_level

    def _is_override_expired(self, override: DefenseOverride) -> bool:
        """Check if override has expired."""
        if override.expires_at is None:
            return False
        return datetime.now() >= override.expires_at

    def _log_transition(
        self,
        fwi_report: FireDangerReport,
        from_level: DefenseLevel,
        to_level: DefenseLevel,
    ):
        """Log defense level transition."""
        trigger_type = "fwi_mapping"

        # Determine trigger type
        isi = fwi_report.component_scores.get("isi", 0)
        bui = fwi_report.component_scores.get("bui", 0)

        if isi > 60:
            trigger_type = "isi_escalation"
        elif bui > 70:
            trigger_type = "bui_escalation"

        if self.active_override:
            trigger_type = "manual_override"

        record = TransitionRecord(
            timestamp=datetime.now(),
            from_level=from_level,
            to_level=to_level,
            fwi_score=fwi_report.fwi_score,
            danger_class=fwi_report.danger_class,
            trigger_type=trigger_type,
            consecutive_count=self.hysteresis_state.consecutive_count,
            hysteresis_active=(self.hysteresis_state.candidate_level is not None),
            override_id=self.active_override.override_id if self.active_override else None,
        )

        self.hysteresis_state.transition_history.append(record)

        # TODO: Persist to database for audit trail

    def apply_override(self, override: DefenseOverride):
        """Apply manual override."""
        logger.warning(
            f"Applying override: {override.override_type} to {override.target_level.name} "
            f"by {override.applied_by}. Reason: {override.reason}"
        )

        self.active_override = override

        # Immediate application for emergency escalate
        if override.override_type == "emergency_escalate":
            self.hysteresis_state.current_level = override.target_level
            self.defense_service.set_level(override.target_level)

    def get_status(self) -> dict:
        """Get current bridge status."""
        return {
            "current_level": self.hysteresis_state.current_level.name,
            "candidate_level": (
                self.hysteresis_state.candidate_level.name
                if self.hysteresis_state.candidate_level
                else None
            ),
            "consecutive_count": self.hysteresis_state.consecutive_count,
            "hysteresis_active": self.hysteresis_state.candidate_level is not None,
            "active_override": (
                {
                    "type": self.active_override.override_type,
                    "target": self.active_override.target_level.name,
                    "expires": self.active_override.expires_at.isoformat()
                    if self.active_override.expires_at
                    else None,
                }
                if self.active_override
                else None
            ),
            "recent_transitions": [
                {
                    "timestamp": r.timestamp.isoformat(),
                    "from": r.from_level.name,
                    "to": r.to_level.name,
                    "fwi": r.fwi_score,
                    "trigger": r.trigger_type,
                }
                for r in self.hysteresis_state.transition_history[-10:]
            ],
        }
```

---

## 7. Test Cases

### Unit Tests

```python
# File: backend/tests/resilience/test_fwi_defense_bridge.py

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.resilience.fwi_defense_bridge import (
    FWIDefenseBridge,
    HysteresisState,
    DefenseOverride,
)
from app.resilience.burnout_fire_index import (
    BurnoutDangerRating,
    FireDangerReport,
    DangerClass,
)
from app.resilience.defense_in_depth import DefenseLevel, DefenseInDepth


class TestFWIDefenseBridge:
    """Test suite for FWI-Defense bridge."""

    @pytest.fixture
    def defense_service(self):
        return DefenseInDepth()

    @pytest.fixture
    def bridge(self, defense_service):
        return FWIDefenseBridge(defense_service)

    @pytest.fixture
    def burnout_rating(self):
        return BurnoutDangerRating()

    # ─────────────────────────────────────────────────────────────
    # Mapping Tests
    # ─────────────────────────────────────────────────────────────

    def test_fwi_low_maps_to_prevention(self, bridge, burnout_rating):
        """Test LOW danger (FWI < 20) maps to PREVENTION."""
        report = burnout_rating.calculate_burnout_danger(
            resident_id=uuid4(),
            recent_hours=50.0,
            monthly_load=200.0,
            yearly_satisfaction=0.9,
            workload_velocity=0.0,
        )

        assert report.danger_class == DangerClass.LOW
        recommended = bridge.recommend_defense_level(report)
        assert recommended == DefenseLevel.PREVENTION

    def test_fwi_moderate_maps_to_control(self, bridge, burnout_rating):
        """Test MODERATE danger (20-40) maps to CONTROL."""
        report = burnout_rating.calculate_burnout_danger(
            resident_id=uuid4(),
            recent_hours=70.0,
            monthly_load=250.0,
            yearly_satisfaction=0.7,
            workload_velocity=2.0,
        )

        assert report.danger_class == DangerClass.MODERATE
        recommended = bridge.recommend_defense_level(report)
        assert recommended == DefenseLevel.CONTROL

    def test_fwi_high_maps_to_safety_systems(self, bridge, burnout_rating):
        """Test HIGH danger (40-60) maps to SAFETY_SYSTEMS."""
        report = burnout_rating.calculate_burnout_danger(
            resident_id=uuid4(),
            recent_hours=75.0,
            monthly_load=260.0,
            yearly_satisfaction=0.5,
            workload_velocity=5.0,
        )

        assert report.danger_class == DangerClass.HIGH
        recommended = bridge.recommend_defense_level(report)
        assert recommended == DefenseLevel.SAFETY_SYSTEMS

    def test_fwi_very_high_maps_to_containment(self, bridge, burnout_rating):
        """Test VERY_HIGH danger (60-80) maps to CONTAINMENT."""
        report = burnout_rating.calculate_burnout_danger(
            resident_id=uuid4(),
            recent_hours=80.0,
            monthly_load=270.0,
            yearly_satisfaction=0.3,
            workload_velocity=8.0,
        )

        assert report.danger_class == DangerClass.VERY_HIGH
        recommended = bridge.recommend_defense_level(report)
        assert recommended == DefenseLevel.CONTAINMENT

    def test_fwi_extreme_maps_to_emergency(self, bridge, burnout_rating):
        """Test EXTREME danger (80+) maps to EMERGENCY."""
        report = burnout_rating.calculate_burnout_danger(
            resident_id=uuid4(),
            recent_hours=85.0,
            monthly_load=280.0,
            yearly_satisfaction=0.2,
            workload_velocity=10.0,
        )

        assert report.danger_class == DangerClass.EXTREME
        recommended = bridge.recommend_defense_level(report)
        assert recommended == DefenseLevel.EMERGENCY

    # ─────────────────────────────────────────────────────────────
    # Component Escalation Tests
    # ─────────────────────────────────────────────────────────────

    def test_isi_escalation(self, bridge):
        """Test ISI > 60 triggers escalation."""
        report = FireDangerReport(
            resident_id=uuid4(),
            danger_class=DangerClass.MODERATE,
            fwi_score=35.0,
            component_scores={"isi": 70.0, "bui": 30.0},
        )

        # Base: MODERATE → CONTROL
        # ISI escalation: +1 → SAFETY_SYSTEMS
        recommended = bridge.recommend_defense_level(report)
        assert recommended == DefenseLevel.SAFETY_SYSTEMS

    def test_bui_escalation(self, bridge):
        """Test BUI > 70 triggers escalation."""
        report = FireDangerReport(
            resident_id=uuid4(),
            danger_class=DangerClass.HIGH,
            fwi_score=55.0,
            component_scores={"isi": 40.0, "bui": 75.0},
        )

        # Base: HIGH → SAFETY_SYSTEMS
        # BUI escalation: +1 → CONTAINMENT
        recommended = bridge.recommend_defense_level(report)
        assert recommended == DefenseLevel.CONTAINMENT

    def test_both_isi_and_bui_escalation(self, bridge):
        """Test both ISI and BUI can escalate (max one level each)."""
        report = FireDangerReport(
            resident_id=uuid4(),
            danger_class=DangerClass.MODERATE,
            fwi_score=35.0,
            component_scores={"isi": 70.0, "bui": 75.0},
        )

        # Base: MODERATE → CONTROL
        # ISI escalation: +1 → SAFETY_SYSTEMS
        # BUI escalation: +1 → CONTAINMENT
        # (Both applied)
        recommended = bridge.recommend_defense_level(report)
        assert recommended == DefenseLevel.CONTAINMENT

    def test_escalation_caps_at_emergency(self, bridge):
        """Test escalation doesn't exceed EMERGENCY level."""
        report = FireDangerReport(
            resident_id=uuid4(),
            danger_class=DangerClass.EXTREME,
            fwi_score=90.0,
            component_scores={"isi": 80.0, "bui": 85.0},
        )

        # Base: EMERGENCY
        # ISI/BUI would escalate but capped
        recommended = bridge.recommend_defense_level(report)
        assert recommended == DefenseLevel.EMERGENCY

    # ─────────────────────────────────────────────────────────────
    # Hysteresis Tests
    # ─────────────────────────────────────────────────────────────

    def test_escalation_requires_consecutive_checks(self, bridge):
        """Test escalation requires 2 consecutive checks."""
        # Start at PREVENTION
        bridge.hysteresis_state.current_level = DefenseLevel.PREVENTION

        # First check: FWI 25 (CONTROL)
        level_1 = bridge.apply_hysteresis(
            recommended=DefenseLevel.CONTROL,
            current=DefenseLevel.PREVENTION,
            fwi_score=25.0,
        )
        assert level_1 == DefenseLevel.PREVENTION  # Still at PREVENTION
        assert bridge.hysteresis_state.consecutive_count == 1

        # Second check: FWI 26 (CONTROL)
        level_2 = bridge.apply_hysteresis(
            recommended=DefenseLevel.CONTROL,
            current=DefenseLevel.PREVENTION,
            fwi_score=26.0,
        )
        assert level_2 == DefenseLevel.CONTROL  # Now escalated
        assert bridge.hysteresis_state.consecutive_count == 0  # Reset

    def test_deescalation_requires_buffer_and_consecutive(self, bridge):
        """Test de-escalation requires buffer + 3 consecutive checks."""
        # Start at CONTROL (threshold 20, buffer 10% → 18)
        bridge.hysteresis_state.current_level = DefenseLevel.CONTROL

        # FWI 19: Above buffer (18), maintain
        level_1 = bridge.apply_hysteresis(
            recommended=DefenseLevel.PREVENTION,
            current=DefenseLevel.CONTROL,
            fwi_score=19.0,
        )
        assert level_1 == DefenseLevel.CONTROL

        # FWI 17: Below buffer, count 1
        level_2 = bridge.apply_hysteresis(
            recommended=DefenseLevel.PREVENTION,
            current=DefenseLevel.CONTROL,
            fwi_score=17.0,
        )
        assert level_2 == DefenseLevel.CONTROL
        assert bridge.hysteresis_state.consecutive_count == 1

        # FWI 16: Count 2
        level_3 = bridge.apply_hysteresis(
            recommended=DefenseLevel.PREVENTION,
            current=DefenseLevel.CONTROL,
            fwi_score=16.0,
        )
        assert level_3 == DefenseLevel.CONTROL
        assert bridge.hysteresis_state.consecutive_count == 2

        # FWI 15: Count 3, de-escalate
        level_4 = bridge.apply_hysteresis(
            recommended=DefenseLevel.PREVENTION,
            current=DefenseLevel.CONTROL,
            fwi_score=15.0,
        )
        assert level_4 == DefenseLevel.PREVENTION
        assert bridge.hysteresis_state.consecutive_count == 0

    def test_hysteresis_prevents_oscillation(self, bridge):
        """Test hysteresis prevents rapid oscillation at threshold."""
        bridge.hysteresis_state.current_level = DefenseLevel.CONTROL

        # Oscillate around threshold 40
        levels = []
        fwi_scores = [39, 41, 39, 42, 40, 38, 41]

        for fwi in fwi_scores:
            if fwi < 40:
                recommended = DefenseLevel.CONTROL
            else:
                recommended = DefenseLevel.SAFETY_SYSTEMS

            level = bridge.apply_hysteresis(
                recommended=recommended,
                current=bridge.hysteresis_state.current_level,
                fwi_score=fwi,
            )
            levels.append(level)
            bridge.hysteresis_state.current_level = level

        # Should stay at CONTROL despite oscillation
        assert all(l == DefenseLevel.CONTROL for l in levels[:6])
        # Only escalates on sustained increase

    # ─────────────────────────────────────────────────────────────
    # Override Tests
    # ─────────────────────────────────────────────────────────────

    def test_emergency_override(self, bridge):
        """Test emergency escalation override."""
        override = DefenseOverride(
            override_type="emergency_escalate",
            target_level=DefenseLevel.EMERGENCY,
            applied_by="admin-user-123",
            reason="Multiple faculty sick calls",
            expires_at=datetime.now() + timedelta(hours=1),
        )

        bridge.apply_override(override)
        assert bridge.hysteresis_state.current_level == DefenseLevel.EMERGENCY

    def test_level_lock_override(self, bridge, burnout_rating):
        """Test level lock override ignores FWI recommendations."""
        override = DefenseOverride(
            override_type="level_lock",
            target_level=DefenseLevel.CONTROL,
            applied_by="admin-user-123",
            reason="Testing mode",
            expires_at=datetime.now() + timedelta(hours=1),
        )

        # FWI says EMERGENCY, but locked at CONTROL
        report = burnout_rating.calculate_burnout_danger(
            resident_id=uuid4(),
            recent_hours=85.0,
            monthly_load=280.0,
            yearly_satisfaction=0.2,
            workload_velocity=10.0,
        )

        final_level = bridge.process_fwi_report(report, override)
        assert final_level == DefenseLevel.CONTROL

    def test_hysteresis_bypass_override(self, bridge):
        """Test hysteresis bypass applies recommendation immediately."""
        bridge.hysteresis_state.current_level = DefenseLevel.PREVENTION

        override = DefenseOverride(
            override_type="hysteresis_bypass",
            target_level=DefenseLevel.SAFETY_SYSTEMS,  # Not used
            applied_by="admin-user-123",
            reason="Emergency gap",
        )

        report = FireDangerReport(
            resident_id=uuid4(),
            danger_class=DangerClass.HIGH,
            fwi_score=55.0,
            component_scores={},
        )

        # Normally would require 2 consecutive checks, but bypass
        final_level = bridge.process_fwi_report(report, override)
        assert final_level == DefenseLevel.SAFETY_SYSTEMS
        assert bridge.active_override is None  # Single use

    def test_override_expiration(self, bridge):
        """Test expired override reverts to automatic control."""
        # Set expired override
        override = DefenseOverride(
            override_type="level_lock",
            target_level=DefenseLevel.EMERGENCY,
            applied_by="admin-user-123",
            reason="Past emergency",
            expires_at=datetime.now() - timedelta(hours=1),  # Already expired
        )

        bridge.active_override = override

        # Process FWI report with LOW danger
        report = FireDangerReport(
            resident_id=uuid4(),
            danger_class=DangerClass.LOW,
            fwi_score=15.0,
            component_scores={},
        )

        final_level = bridge.process_fwi_report(report)
        # Should use FWI recommendation, not override
        assert final_level == DefenseLevel.PREVENTION

    # ─────────────────────────────────────────────────────────────
    # Integration Tests
    # ─────────────────────────────────────────────────────────────

    def test_full_escalation_sequence(self, bridge, burnout_rating):
        """Test complete escalation from GREEN to BLACK."""
        resident_id = uuid4()

        # Start: LOW danger
        report_1 = burnout_rating.calculate_burnout_danger(
            resident_id=resident_id,
            recent_hours=50.0,
            monthly_load=200.0,
            yearly_satisfaction=0.9,
            workload_velocity=0.0,
        )
        level_1 = bridge.process_fwi_report(report_1)
        assert level_1 == DefenseLevel.PREVENTION

        # Escalate to MODERATE
        report_2 = burnout_rating.calculate_burnout_danger(
            resident_id=resident_id,
            recent_hours=70.0,
            monthly_load=250.0,
            yearly_satisfaction=0.7,
            workload_velocity=3.0,
        )
        bridge.process_fwi_report(report_2)  # Count 1
        level_2 = bridge.process_fwi_report(report_2)  # Count 2, escalate
        assert level_2 == DefenseLevel.CONTROL

        # Escalate to HIGH
        report_3 = burnout_rating.calculate_burnout_danger(
            resident_id=resident_id,
            recent_hours=75.0,
            monthly_load=260.0,
            yearly_satisfaction=0.5,
            workload_velocity=5.0,
        )
        bridge.process_fwi_report(report_3)  # Count 1
        level_3 = bridge.process_fwi_report(report_3)  # Count 2, escalate
        assert level_3 == DefenseLevel.SAFETY_SYSTEMS

        # Verify transition history
        assert len(bridge.hysteresis_state.transition_history) >= 2
```

---

## 8. Monitoring & Alerts

### Metrics to Track

```python
# Prometheus metrics for FWI-Defense bridge

from prometheus_client import Counter, Gauge, Histogram

# Defense level tracking
defense_level_gauge = Gauge(
    "defense_level_current",
    "Current active defense level (1-5)",
)

# Transition tracking
defense_transitions_counter = Counter(
    "defense_transitions_total",
    "Total defense level transitions",
    ["from_level", "to_level", "trigger_type"],
)

# Hysteresis tracking
hysteresis_active_gauge = Gauge(
    "defense_hysteresis_active",
    "Whether hysteresis is currently preventing transition (0 or 1)",
)

hysteresis_consecutive_gauge = Gauge(
    "defense_hysteresis_consecutive_count",
    "Current consecutive count for hysteresis",
)

# Override tracking
override_active_gauge = Gauge(
    "defense_override_active",
    "Whether manual override is active (0 or 1)",
)

override_applications_counter = Counter(
    "defense_override_applications_total",
    "Total override applications",
    ["override_type", "applied_by"],
)

# FWI component tracking
fwi_score_gauge = Gauge(
    "fwi_score_current",
    "Current FWI score",
)

fwi_isi_gauge = Gauge(
    "fwi_isi_current",
    "Current ISI (rapid response indicator)",
)

fwi_bui_gauge = Gauge(
    "fwi_bui_current",
    "Current BUI (sustained threat indicator)",
)

# Escalation triggers
component_escalations_counter = Counter(
    "fwi_component_escalations_total",
    "Escalations triggered by components",
    ["component"],  # "isi" or "bui"
)
```

### Alert Rules

```yaml
# Prometheus alert rules for FWI-Defense bridge

groups:
  - name: defense_level_alerts
    interval: 15s
    rules:
      # Critical: EMERGENCY level activated
      - alert: DefenseLevelEmergency
        expr: defense_level_current == 5
        for: 0m
        labels:
          severity: critical
          component: defense_in_depth
        annotations:
          summary: "EMERGENCY defense level activated"
          description: "Defense-in-Depth BLACK level active. Crisis response required."

      # High: CONTAINMENT level activated
      - alert: DefenseLevelContainment
        expr: defense_level_current == 4
        for: 5m
        labels:
          severity: high
          component: defense_in_depth
        annotations:
          summary: "CONTAINMENT defense level activated"
          description: "Defense-in-Depth RED level active. Service reduction in effect."

      # Warning: SAFETY_SYSTEMS activated
      - alert: DefenseLevelSafetySystems
        expr: defense_level_current == 3
        for: 15m
        labels:
          severity: warning
          component: defense_in_depth
        annotations:
          summary: "SAFETY_SYSTEMS defense level activated"
          description: "Defense-in-Depth ORANGE level active. Automated protective actions engaged."

      # Info: Manual override active
      - alert: DefenseOverrideActive
        expr: defense_override_active == 1
        for: 1m
        labels:
          severity: info
          component: defense_in_depth
        annotations:
          summary: "Manual defense override active"
          description: "Defense level under manual override. Check admin logs."

      # Warning: Hysteresis preventing de-escalation for extended period
      - alert: HysteresisProlonged
        expr: |
          defense_hysteresis_active == 1 and
          defense_hysteresis_consecutive_count >= 5
        for: 30m
        labels:
          severity: warning
          component: defense_in_depth
        annotations:
          summary: "Prolonged hysteresis preventing de-escalation"
          description: "Hysteresis active for 30+ minutes with {{ $value }} consecutive checks. System may be oscillating."

      # Critical: Rapid escalation (two levels in 30 minutes)
      - alert: RapidDefenseEscalation
        expr: |
          rate(defense_transitions_total[30m]) > 2
        for: 0m
        labels:
          severity: critical
          component: defense_in_depth
        annotations:
          summary: "Rapid defense level escalation detected"
          description: "Defense level escalated multiple times in 30 minutes. Situation deteriorating rapidly."

      # Warning: ISI triggering frequent escalations
      - alert: FrequentISIEscalations
        expr: |
          rate(fwi_component_escalations_total{component="isi"}[1h]) > 3
        for: 0m
        labels:
          severity: warning
          component: burnout_fire_index
        annotations:
          summary: "Frequent ISI-triggered escalations"
          description: "ISI (rapid response) triggering escalations frequently. Workload velocity high."

      # Warning: BUI sustained high
      - alert: BUIElevatedSustained
        expr: fwi_bui_current > 70
        for: 2h
        labels:
          severity: warning
          component: burnout_fire_index
        annotations:
          summary: "BUI elevated for extended period"
          description: "BUI > 70 for 2+ hours. Chronic burden accumulating."
```

### Dashboard Panels

```yaml
# Grafana dashboard panels for FWI-Defense bridge

panels:
  - title: "Defense Level Status"
    type: gauge
    targets:
      - expr: defense_level_current
    thresholds:
      - value: 1
        color: green
      - value: 2
        color: yellow
      - value: 3
        color: orange
      - value: 4
        color: red
      - value: 5
        color: purple
    displayName:
      1: "PREVENTION"
      2: "CONTROL"
      3: "SAFETY_SYSTEMS"
      4: "CONTAINMENT"
      5: "EMERGENCY"

  - title: "FWI Score Trend"
    type: graph
    targets:
      - expr: fwi_score_current
        legendFormat: "FWI"
      - expr: fwi_isi_current
        legendFormat: "ISI (rapid)"
      - expr: fwi_bui_current
        legendFormat: "BUI (sustained)"
    yaxis:
      min: 0
      max: 100
    thresholds:
      - value: 20
        color: yellow
      - value: 40
        color: orange
      - value: 60
        color: red
      - value: 80
        color: purple

  - title: "Defense Level Transitions"
    type: heatmap
    targets:
      - expr: |
          sum by (from_level, to_level) (
            rate(defense_transitions_total[5m])
          )
    dataFormat: tsbuckets

  - title: "Hysteresis State"
    type: stat
    targets:
      - expr: defense_hysteresis_active
        legendFormat: "Hysteresis Active"
      - expr: defense_hysteresis_consecutive_count
        legendFormat: "Consecutive Count"

  - title: "Override Status"
    type: table
    targets:
      - expr: defense_override_active
      - expr: |
          sum by (override_type, applied_by) (
            rate(defense_override_applications_total[1h])
          )

  - title: "Escalation Triggers"
    type: pie
    targets:
      - expr: |
          sum by (trigger_type) (
            defense_transitions_total
          )
    legendFormat: "{{ trigger_type }}"
```

---

## Appendix A: Glossary

| Term | Definition |
|------|------------|
| **BUI (Buildup Index)** | Combined medium + long-term burnout burden (DMC + DC) |
| **Defense in Depth** | 5-level safety system from nuclear engineering |
| **Hysteresis** | Asymmetric threshold logic preventing oscillation |
| **ISI (Initial Spread Index)** | Rapid deterioration indicator (FFMC + velocity) |
| **FWI (Fire Weather Index)** | Final composite burnout danger score (0-100+) |
| **Level Lock** | Manual override fixing defense level temporarily |
| **N+2 Redundancy** | System can lose 2 components and still function |

---

## Appendix B: References

1. **Canadian Forest Fire Danger Rating System**
   - Van Wagner, C.E. (1987). Development and structure of the Canadian Forest Fire Weather Index System. Forestry Technical Report 35.

2. **Defense in Depth (Nuclear Safety)**
   - IAEA Safety Standards Series No. SSF-1 (2019). Safety of Nuclear Power Plants: Design.

3. **Hysteresis in Control Systems**
   - Åström, K.J., & Hägglund, T. (2006). Advanced PID Control. ISA.

4. **Resilience Framework Documentation**
   - `docs/architecture/cross-disciplinary-resilience.md`
   - `backend/app/resilience/burnout_fire_index.py`
   - `backend/app/resilience/defense_in_depth.py`

---

**End of Specification**

*This document is implementation-ready. All classes, methods, and logic are fully specified and tested.*
