"""Pydantic schemas for scheduling catalyst API endpoints."""

from datetime import date
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class BarrierTypeEnum(str, Enum):
    """Classification of energy barriers."""

    KINETIC = "kinetic"
    THERMODYNAMIC = "thermodynamic"
    STERIC = "steric"
    ELECTRONIC = "electronic"
    REGULATORY = "regulatory"


class CatalystTypeEnum(str, Enum):
    """Classification of catalysts."""

    HOMOGENEOUS = "homogeneous"
    HETEROGENEOUS = "heterogeneous"
    ENZYMATIC = "enzymatic"
    AUTOCATALYTIC = "autocatalytic"


class ReactionTypeEnum(str, Enum):
    """Types of schedule changes."""

    SWAP = "swap"
    REASSIGNMENT = "reassignment"
    CANCELLATION = "cancellation"
    CREATION = "creation"
    MODIFICATION = "modification"


# =============================================================================
# Request Schemas
# =============================================================================


class BarrierDetectionRequest(BaseModel):
    """Request to detect barriers for a proposed schedule change."""

    assignment_id: UUID = Field(..., description="ID of the assignment to analyze")
    proposed_change: dict[str, Any] = Field(
        ..., description="Description of the proposed change"
    )
    reference_date: date | None = Field(
        default=None, description="Reference date for calculations (defaults to today)"
    )


class CatalystAnalysisRequest(BaseModel):
    """Request to find catalysts for detected barriers."""

    barriers: list["EnergyBarrierResponse"] = Field(
        ..., description="Barriers to find catalysts for"
    )
    max_catalysts: int = Field(
        default=3, ge=1, le=10, description="Maximum catalysts per barrier"
    )


class PathwayOptimizationRequest(BaseModel):
    """Request to find optimal pathway for a schedule change."""

    assignment_id: UUID = Field(..., description="ID of the assignment to change")
    proposed_change: dict[str, Any] = Field(
        ..., description="Description of the proposed change"
    )
    energy_threshold: float = Field(
        default=0.8, ge=0.0, le=1.0, description="Maximum acceptable activation energy"
    )
    prefer_mechanisms: bool = Field(
        default=True, description="Prefer automated mechanisms over personnel"
    )
    allow_multi_step: bool = Field(
        default=True, description="Allow multi-step pathways"
    )


class SwapBarrierAnalysisRequest(BaseModel):
    """Request to analyze barriers for a swap operation."""

    source_faculty_id: UUID = Field(..., description="ID of source faculty")
    source_week: date = Field(..., description="Source week date")
    target_faculty_id: UUID = Field(..., description="ID of target faculty")
    target_week: date | None = Field(
        default=None, description="Target week date (for 1:1 swaps)"
    )
    swap_type: str = Field(default="one_to_one", description="Type of swap")


class BatchOptimizationRequest(BaseModel):
    """Request to optimize multiple schedule changes."""

    changes: list[PathwayOptimizationRequest] = Field(
        ..., min_length=1, description="List of changes to optimize"
    )
    find_optimal_order: bool = Field(
        default=True, description="Find optimal execution order"
    )


# =============================================================================
# Response Schemas
# =============================================================================


class EnergyBarrierResponse(BaseModel):
    """Response schema for an energy barrier."""

    barrier_type: BarrierTypeEnum
    name: str
    description: str
    energy_contribution: float = Field(ge=0.0, le=1.0)
    is_absolute: bool
    source: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True


class ActivationEnergyResponse(BaseModel):
    """Response schema for activation energy calculation."""

    value: float = Field(ge=0.0, le=1.0, description="Normalized activation energy")
    components: dict[BarrierTypeEnum, float] = Field(
        default_factory=dict, description="Breakdown by barrier type"
    )
    catalyzed_value: float | None = Field(
        default=None, description="Energy after catalyst application"
    )
    catalyst_effect: float = Field(
        default=0.0, description="Reduction achieved by catalysts"
    )
    is_feasible: bool = Field(description="Whether the change is feasible")
    effective_energy: float = Field(description="Effective energy after catalysis")
    reduction_percentage: float = Field(
        description="Percentage reduction from catalysis"
    )


class CatalystPersonResponse(BaseModel):
    """Response schema for a person catalyst."""

    person_id: UUID
    name: str
    catalyst_type: CatalystTypeEnum
    effectiveness: dict[BarrierTypeEnum, float] = Field(
        default_factory=dict, description="Effectiveness per barrier type"
    )
    availability: float = Field(ge=0.0, le=1.0, description="Current availability")
    capacity: float = Field(ge=0.0, le=1.0, description="Remaining capacity")


class CatalystMechanismResponse(BaseModel):
    """Response schema for a mechanism catalyst."""

    mechanism_id: str
    name: str
    catalyst_type: CatalystTypeEnum
    target_barriers: list[BarrierTypeEnum]
    reduction_factor: float = Field(ge=0.0, le=1.0)
    auto_applicable: bool = Field(description="Whether can be applied automatically")
    requires_authorization: bool


class CatalystRecommendationResponse(BaseModel):
    """Response schema for catalyst recommendations."""

    barrier: EnergyBarrierResponse
    person_catalysts: list[CatalystPersonResponse]
    mechanism_catalysts: list[CatalystMechanismResponse]
    recommended_catalyst: str = Field(description="Most recommended catalyst")
    confidence: float = Field(
        ge=0.0, le=1.0, description="Confidence in recommendation"
    )


class TransitionStateResponse(BaseModel):
    """Response schema for a transition state."""

    state_id: str
    description: str
    energy: float = Field(ge=0.0, le=1.0)
    is_stable: bool
    duration_estimate_hours: float | None = None


class ReactionPathwayResponse(BaseModel):
    """Response schema for a reaction pathway."""

    pathway_id: str
    total_energy: float
    catalyzed_energy: float
    transition_states: list[TransitionStateResponse]
    catalysts_used: list[str]
    estimated_duration_hours: float | None = None
    success_probability: float = Field(ge=0.0, le=1.0)


class PathwayResultResponse(BaseModel):
    """Response schema for pathway optimization result."""

    success: bool
    pathway: ReactionPathwayResponse | None = None
    alternative_pathways: list[ReactionPathwayResponse] = Field(default_factory=list)
    blocking_barriers: list[EnergyBarrierResponse] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class BarrierAnalysisResponse(BaseModel):
    """Response schema for barrier analysis."""

    total_barriers: int
    barriers: list[EnergyBarrierResponse]
    activation_energy: ActivationEnergyResponse
    has_absolute_barriers: bool
    summary: str


class SwapBarrierAnalysisResponse(BaseModel):
    """Response schema for swap barrier analysis."""

    swap_feasible: bool
    barriers: list[EnergyBarrierResponse]
    activation_energy: ActivationEnergyResponse
    catalyst_recommendations: list[CatalystRecommendationResponse] = Field(
        default_factory=list
    )
    blocking_barriers: list[EnergyBarrierResponse] = Field(default_factory=list)
    pathway: PathwayResultResponse | None = None
    recommendations: list[str] = Field(default_factory=list)


class BatchOptimizationResponse(BaseModel):
    """Response schema for batch optimization."""

    total_changes: int
    successful_pathways: int
    optimal_order: list[int] = Field(
        default_factory=list, description="Optimal execution order (0-indexed)"
    )
    results: list[PathwayResultResponse]
    aggregate_energy: float
    catalyst_conflicts: list[str] = Field(
        default_factory=list, description="Conflicts between catalyst usage"
    )


class CatalystCapacityResponse(BaseModel):
    """Response schema for system catalyst capacity."""

    person_catalysts_available: int
    mechanism_catalysts_available: int
    total_capacity: float = Field(ge=0.0, description="Total remaining capacity")
    bottleneck_catalysts: list[str] = Field(
        default_factory=list, description="Catalysts near capacity"
    )
    recommendations: list[str] = Field(default_factory=list)
