"""
Type definitions for MTF Compliance system state and data structures.

This module provides strongly-typed dataclasses for internal data structures
used by the MTF compliance system, replacing dict[str, Any] patterns with
proper type safety.
"""

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional

from app.schemas.resilience import EquilibriumState, LoadSheddingLevel


class ViolationSeverity(str, Enum):
    """Severity levels for MTF compliance violations."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class MTFViolation:
    """Represents a single MTF compliance violation."""
    rule_id: str
    severity: ViolationSeverity
    description: str
    affected_items: list[str] = field(default_factory=list)
    recommendation: Optional[str] = None


@dataclass
class MTFComplianceResult:
    """Result of an MTF compliance check."""
    is_compliant: bool
    violations: list[MTFViolation] = field(default_factory=list)
    score: float = 100.0
    checked_at: Optional[date] = None
    recommendations: list[str] = field(default_factory=list)


@dataclass
class StaffingLevel:
    """Staffing level information."""
    role: str
    required: int
    available: int
    deficit: int = 0

    def __post_init__(self):
        """Calculate deficit from required and available."""
        self.deficit = max(0, self.required - self.available)


@dataclass
class CoverageGap:
    """Represents a coverage gap in the schedule."""
    date: date
    time_of_day: str
    rotation: str
    required_staff: int
    assigned_staff: int
    gap_size: int = 0

    def __post_init__(self):
        """Calculate gap size from required and assigned."""
        self.gap_size = max(0, self.required_staff - self.assigned_staff)


@dataclass
class SystemHealthState:
    """
    Represents the overall health state of the scheduling system.

    This replaces the generic dict[str, Any] system_state parameter used
    throughout MTF compliance functions.
    """
    # Contingency analysis results
    n1_pass: bool
    n2_pass: bool

    # Coverage metrics
    coverage_rate: float

    # Staff stress metrics
    average_allostatic_load: float
    overloaded_faculty_count: int = 0

    # System state
    load_shedding_level: LoadSheddingLevel | str
    equilibrium_state: EquilibriumState | str

    # Financial/compensatory metrics
    compensation_debt: float = 0.0

    # Volatility and risk
    volatility_level: str = "normal"
    phase_transition_risk: str = "low"

    def to_dict(self) -> dict[str, any]:
        """Convert to dictionary for backward compatibility."""
        return {
            "n1_pass": self.n1_pass,
            "n2_pass": self.n2_pass,
            "coverage_rate": self.coverage_rate,
            "average_allostatic_load": self.average_allostatic_load,
            "overloaded_faculty_count": self.overloaded_faculty_count,
            "load_shedding_level": self.load_shedding_level,
            "equilibrium_state": self.equilibrium_state,
            "compensation_debt": self.compensation_debt,
            "volatility_level": self.volatility_level,
            "phase_transition_risk": self.phase_transition_risk,
        }


@dataclass
class CascadePrediction:
    """
    Cascade failure prediction results.

    Replaces dict[str, Any] cascade_prediction parameter.
    """
    days_until_exhaustion: int
    cascade_probability: float = 0.0
    critical_faculty: list[int] = field(default_factory=list)
    projected_load_increase: float = 0.0

    def to_dict(self) -> dict[str, any]:
        """Convert to dictionary for backward compatibility."""
        return {
            "days_until_exhaustion": self.days_until_exhaustion,
            "cascade_probability": self.cascade_probability,
            "critical_faculty": self.critical_faculty,
            "projected_load_increase": self.projected_load_increase,
        }


@dataclass
class PositiveFeedbackRisk:
    """
    Represents a detected positive feedback risk.

    Replaces dict items in positive_feedback_risks list.
    """
    risk_type: str
    confidence: float
    description: str
    affected_entities: list[str] = field(default_factory=list)
    mitigation_required: bool = False

    def to_dict(self) -> dict[str, any]:
        """Convert to dictionary for backward compatibility."""
        return {
            "risk_type": self.risk_type,
            "confidence": self.confidence,
            "description": self.description,
            "affected_entities": self.affected_entities,
            "mitigation_required": self.mitigation_required,
        }


@dataclass(frozen=True)
class SupportingMetrics:
    """
    Supporting metrics for RFF documents.

    Replaces dict[str, Any] supporting_metrics in RFFDocument.
    """
    coverage_rate: Optional[float]
    n1_pass: Optional[bool]
    n2_pass: Optional[bool]
    load_shedding_level: str
    average_allostatic_load: Optional[float]
    equilibrium_state: str
    compensation_debt: Optional[float]
    snapshot_timestamp: str

    def to_dict(self) -> dict[str, any]:
        """Convert to dictionary for serialization."""
        return {
            "coverage_rate": self.coverage_rate,
            "n1_pass": self.n1_pass,
            "n2_pass": self.n2_pass,
            "load_shedding_level": self.load_shedding_level,
            "average_allostatic_load": self.average_allostatic_load,
            "equilibrium_state": self.equilibrium_state,
            "compensation_debt": self.compensation_debt,
            "snapshot_timestamp": self.snapshot_timestamp,
        }


@dataclass
class ProjectionWithoutSupport:
    """
    Projection of outcomes without requested support.

    Replaces dict[str, Any] projected_without_support in RFFDocument.
    """
    timeline_days: int
    outcomes: list[str] = field(default_factory=list)
    mission_failure_likely: bool = False

    def to_dict(self) -> dict[str, any]:
        """Convert to dictionary for serialization."""
        return {
            "timeline_days": self.timeline_days,
            "outcomes": self.outcomes,
            "mission_failure_likely": self.mission_failure_likely,
        }
