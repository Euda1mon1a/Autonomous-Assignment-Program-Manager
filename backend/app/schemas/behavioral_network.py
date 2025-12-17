"""
Behavioral Network Schemas.

Schemas for swap network analysis, burden equity, and shadow org chart features.
"""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


# =============================================================================
# Enums
# =============================================================================


class BehavioralRole(str, Enum):
    """Informal roles revealed by swap behavior."""
    NEUTRAL = "neutral"
    POWER_BROKER = "power_broker"
    MARTYR = "martyr"
    EVADER = "evader"
    ISOLATE = "isolate"
    STABILIZER = "stabilizer"


class BurdenCategory(str, Enum):
    """Categories of shift burden."""
    MINIMAL = "minimal"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    SEVERE = "severe"
    EXTREME = "extreme"


class EquityStatus(str, Enum):
    """Status of burden equity for a person."""
    BALANCED = "balanced"
    LIGHT = "light"
    HEAVY = "heavy"
    VERY_LIGHT = "very_light"
    CRUSHING = "crushing"


class ProtectionLevel(str, Enum):
    """Protection level for martyrs."""
    NONE = "none"
    MONITORING = "monitoring"
    SOFT_LIMIT = "soft_limit"
    HARD_LIMIT = "hard_limit"


# =============================================================================
# Request Schemas
# =============================================================================


class BurdenCalculationRequest(BaseModel):
    """Request to calculate shift burden."""
    shift_id: UUID
    faculty_id: UUID
    date: datetime
    shift_type: str
    hours: float = Field(..., gt=0)
    is_weekend: bool = False
    is_holiday: bool = False
    is_night: bool = False
    custom_factors: list[str] = Field(default_factory=list)


class SwapRecordInput(BaseModel):
    """Input for recording a swap in the network."""
    source_id: UUID
    source_name: str
    target_id: UUID
    target_name: str
    initiated_by: UUID
    source_burden: float = Field(default=10.0, ge=0)
    target_burden: float = Field(default=0.0, ge=0)
    was_successful: bool = True


class MartyrProtectionCheckRequest(BaseModel):
    """Request to check martyr protection level."""
    faculty_id: UUID
    current_allostatic_load: float = Field(default=0.0, ge=0, le=100)


class SwapBlockCheckRequest(BaseModel):
    """Request to check if a swap should be blocked."""
    target_id: UUID
    source_burden: float = Field(..., ge=0)
    target_current_load: float = Field(default=0.0, ge=0, le=100)


# =============================================================================
# Response Schemas
# =============================================================================


class ShiftBurdenResponse(BaseModel):
    """Response with calculated shift burden."""
    shift_id: UUID
    faculty_id: UUID
    date: datetime
    shift_type: str
    raw_hours: float
    burden_weight: float
    weighted_burden: float
    category: BurdenCategory
    factors: list[str]


class FacultyBurdenProfileResponse(BaseModel):
    """Comprehensive burden profile for a faculty member."""
    faculty_id: UUID
    faculty_name: str
    period_start: datetime
    period_end: datetime
    calculated_at: datetime

    # Raw metrics
    total_hours: float
    total_shifts: int
    shift_breakdown: dict[str, int]

    # Burden metrics
    total_burden: float
    burden_per_hour: float
    high_burden_shifts: int

    # Equity assessment
    equity_status: EquityStatus
    std_devs_from_mean: float

    # Behavioral flags
    behavioral_role: BehavioralRole
    protection_level: ProtectionLevel


class SwapNetworkNodeResponse(BaseModel):
    """Network node (faculty member) response."""
    faculty_id: UUID
    faculty_name: str
    degree: int
    in_degree: int
    out_degree: int
    swap_count: int
    net_burden_flow: float
    burden_absorbed: float
    burden_offloaded: float
    approval_rate: float
    acceptance_rate: float
    behavioral_role: BehavioralRole
    role_confidence: float


class SwapNetworkAnalysisResponse(BaseModel):
    """Complete swap network analysis response."""
    analyzed_at: datetime
    period_start: datetime
    period_end: datetime
    total_swaps: int
    total_faculty: int

    # Network statistics
    network_density: float
    average_degree: float

    # Role distributions
    power_brokers_count: int
    martyrs_count: int
    evaders_count: int
    isolates_count: int
    stabilizers_count: int

    # Risk assessment
    martyr_burnout_risk_count: int
    equity_concerns: list[str]


class MartyrProtectionResponse(BaseModel):
    """Response for martyr protection check."""
    faculty_id: UUID
    protection_level: ProtectionLevel
    reason: str
    behavioral_role: BehavioralRole | None = None


class SwapBlockDecisionResponse(BaseModel):
    """Response for swap block decision."""
    should_block: bool
    reason: str


class BurdenEquityAnalysisResponse(BaseModel):
    """Response for burden equity analysis."""
    mean_burden: float
    std_burden: float
    mean_hours: float
    std_hours: float
    gini_coefficient: float
    equity_grade: str

    distribution: dict[str, int]

    crushing_faculty: list[UUID]
    very_light_faculty: list[UUID]

    recommendations: list[str]


class RecommendationItem(BaseModel):
    """A single recommendation item."""
    priority: str = Field(..., pattern="^(CRITICAL|HIGH|MEDIUM|LOW)$")
    action: str
    details: str


class ShadowOrgChartReportResponse(BaseModel):
    """Complete shadow org chart report response."""
    generated_at: datetime
    period_start: datetime
    period_end: datetime

    network_summary: dict
    behavioral_roles: dict
    risk_flags: dict
    detailed_roles: dict

    burden_equity: BurdenEquityAnalysisResponse | None = None
    recommendations: list[RecommendationItem]
