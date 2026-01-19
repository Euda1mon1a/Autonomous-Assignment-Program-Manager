"""
Pydantic schemas for Hopfield Network API endpoints.

Defines request/response models for schedule stability analysis.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# =============================================================================
# Enums
# =============================================================================


class AttractorType(str, Enum):
    """Types of attractors in the energy landscape."""

    GLOBAL_MINIMUM = "global_minimum"
    LOCAL_MINIMUM = "local_minimum"
    SPURIOUS = "spurious"
    METASTABLE = "metastable"
    SADDLE_POINT = "saddle_point"


class StabilityLevel(str, Enum):
    """Stability classification of schedule state."""

    VERY_STABLE = "very_stable"
    STABLE = "stable"
    MARGINALLY_STABLE = "marginally_stable"
    UNSTABLE = "unstable"
    HIGHLY_UNSTABLE = "highly_unstable"


# =============================================================================
# Energy Analysis
# =============================================================================


class HopfieldEnergyRequest(BaseModel):
    """Request for Hopfield energy calculation."""

    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    schedule_id: str | None = Field(None, description="Optional schedule ID")


class EnergyMetricsResponse(BaseModel):
    """Energy metrics for a schedule configuration."""

    total_energy: float = Field(..., description="Total Hopfield energy")
    normalized_energy: float = Field(
        ..., ge=-1.0, le=1.0, description="Normalized energy [-1, 1]"
    )
    energy_density: float = Field(..., description="Energy per assignment")
    interaction_energy: float = Field(..., description="Pairwise interaction energy")
    stability_score: float = Field(
        ..., ge=0.0, le=1.0, description="Stability score [0, 1]"
    )
    gradient_magnitude: float = Field(
        ..., ge=0.0, description="Energy gradient magnitude"
    )
    is_local_minimum: bool = Field(..., description="Whether state is at local minimum")
    distance_to_minimum: int = Field(
        ..., ge=0, description="Hamming distance to nearest minimum"
    )


class HopfieldEnergyResponse(BaseModel):
    """Response from Hopfield energy calculation."""

    analyzed_at: str = Field(..., description="ISO timestamp of analysis")
    schedule_id: str | None = Field(None, description="Schedule ID if provided")
    period_start: str = Field(..., description="Analysis period start")
    period_end: str = Field(..., description="Analysis period end")
    assignments_analyzed: int = Field(..., ge=0, description="Number of assignments")
    metrics: EnergyMetricsResponse = Field(..., description="Energy metrics")
    stability_level: StabilityLevel = Field(..., description="Stability classification")
    interpretation: str = Field(..., description="Human-readable interpretation")
    recommendations: list[str] = Field(default_factory=list)
    source: str = Field("backend", description="Data source")


# =============================================================================
# Nearby Attractors
# =============================================================================


class NearbyAttractorsRequest(BaseModel):
    """Request for nearby attractor search."""

    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    max_distance: int = Field(
        10, ge=1, le=50, description="Maximum Hamming distance to search"
    )


class AttractorInfoResponse(BaseModel):
    """Information about a detected attractor."""

    attractor_id: str = Field(..., description="Unique attractor identifier")
    attractor_type: AttractorType = Field(..., description="Type of attractor")
    energy_level: float = Field(..., description="Energy at attractor state")
    basin_depth: float = Field(..., ge=0.0, description="Energy barrier to escape")
    basin_volume: int = Field(..., ge=0, description="Estimated states in basin")
    hamming_distance: int = Field(..., ge=0, description="Distance from current state")
    pattern_description: str = Field(..., description="Pattern description")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence")


class NearbyAttractorsResponse(BaseModel):
    """Response from nearby attractor search."""

    analyzed_at: str = Field(..., description="ISO timestamp of analysis")
    current_state_energy: float = Field(..., description="Energy of current state")
    attractors_found: int = Field(..., ge=0, description="Number of attractors found")
    attractors: list[AttractorInfoResponse] = Field(default_factory=list)
    global_minimum_identified: bool = Field(
        ..., description="Whether global minimum was found"
    )
    current_basin_id: str | None = Field(
        None, description="ID of basin containing current state"
    )
    interpretation: str = Field(..., description="Human-readable interpretation")
    recommendations: list[str] = Field(default_factory=list)
    source: str = Field("backend", description="Data source")


# =============================================================================
# Basin Depth
# =============================================================================


class BasinDepthRequest(BaseModel):
    """Request for basin depth measurement."""

    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    num_perturbations: int = Field(
        100, ge=10, le=1000, description="Number of perturbations to test"
    )


class BasinMetricsResponse(BaseModel):
    """Metrics quantifying basin of attraction stability."""

    min_escape_energy: float = Field(..., ge=0.0, description="Minimum escape barrier")
    avg_escape_energy: float = Field(..., ge=0.0, description="Average escape barrier")
    max_escape_energy: float = Field(..., ge=0.0, description="Maximum escape barrier")
    basin_stability_index: float = Field(
        ..., ge=0.0, le=1.0, description="Basin stability index [0, 1]"
    )
    num_escape_paths: int = Field(..., ge=0, description="Number of escape paths")
    nearest_saddle_distance: int = Field(
        ..., ge=0, description="Distance to nearest saddle point"
    )
    basin_radius: int = Field(..., ge=0, description="Maximum distance within basin")
    critical_perturbation_size: int = Field(
        ..., ge=0, description="Changes needed to escape basin"
    )


class BasinDepthResponse(BaseModel):
    """Response from basin depth measurement."""

    analyzed_at: str = Field(..., description="ISO timestamp of analysis")
    schedule_id: str | None = Field(None, description="Schedule ID if provided")
    attractor_id: str = Field(..., description="ID of measured attractor")
    metrics: BasinMetricsResponse = Field(..., description="Basin metrics")
    stability_level: StabilityLevel = Field(..., description="Stability classification")
    is_robust: bool = Field(..., description="Whether schedule is robust")
    robustness_threshold: int = Field(
        ..., ge=0, description="Max simultaneous changes tolerated"
    )
    interpretation: str = Field(..., description="Human-readable interpretation")
    recommendations: list[str] = Field(default_factory=list)
    source: str = Field("backend", description="Data source")


# =============================================================================
# Spurious Attractors
# =============================================================================


class SpuriousAttractorsRequest(BaseModel):
    """Request for spurious attractor detection."""

    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    search_radius: int = Field(
        20, ge=5, le=50, description="Hamming distance search radius"
    )


class SpuriousAttractorInfoResponse(BaseModel):
    """Information about a detected spurious attractor."""

    attractor_id: str = Field(..., description="Unique identifier")
    energy_level: float = Field(..., description="Energy at spurious attractor")
    basin_size: int = Field(..., ge=0, description="Size of spurious basin")
    anti_pattern_type: str = Field(..., description="Type of anti-pattern")
    description: str = Field(..., description="Description of the anti-pattern")
    risk_level: str = Field(..., description="Risk level: low, medium, high, critical")
    distance_from_valid: int = Field(
        ..., ge=0, description="Distance from valid schedule"
    )
    probability_of_capture: float = Field(
        ..., ge=0.0, le=1.0, description="Probability of falling into basin"
    )
    mitigation_strategy: str = Field(..., description="Recommended mitigation")


class SpuriousAttractorsResponse(BaseModel):
    """Response from spurious attractor detection."""

    analyzed_at: str = Field(..., description="ISO timestamp of analysis")
    spurious_attractors_found: int = Field(
        ..., ge=0, description="Number of spurious attractors"
    )
    spurious_attractors: list[SpuriousAttractorInfoResponse] = Field(
        default_factory=list
    )
    total_basin_coverage: float = Field(
        ..., ge=0.0, le=1.0, description="Fraction covered by spurious basins"
    )
    highest_risk_attractor: str | None = Field(
        None, description="ID of highest risk attractor"
    )
    is_current_state_spurious: bool = Field(
        ..., description="Whether current state is in spurious basin"
    )
    interpretation: str = Field(..., description="Human-readable interpretation")
    recommendations: list[str] = Field(default_factory=list)
    source: str = Field("backend", description="Data source")
