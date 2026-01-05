"""
MCP Proxy API Routes.

Exposes MCP tools to the frontend via REST endpoints. These endpoints serve as
proxies to the MCP server tools, allowing the React frontend to use MCP
functionality without direct MCP client integration.

Security:
- All endpoints require authentication
- Admin-only endpoints are explicitly marked
- Input validation via Pydantic schemas

Created: 2026-01-04 (Session 049)
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.dependencies.role_filter import require_admin
from app.core.security import get_current_active_user
from app.models.user import User
from app.resilience.equity_metrics import equity_report, gini_coefficient, lorenz_curve

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Request/Response Models
# =============================================================================


class EquityMetricsRequest(BaseModel):
    """Request for equity metrics calculation."""

    provider_hours: dict[str, float] = Field(
        ...,
        description="Mapping of provider ID to total hours worked",
        min_length=1,
    )
    intensity_weights: dict[str, float] | None = Field(
        None,
        description="Optional intensity weights per provider (e.g., night shift = 1.5x)",
    )


class EquityMetricsResponse(BaseModel):
    """Response with equity metrics."""

    gini_coefficient: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Gini coefficient (0 = perfect equality, 1 = perfect inequality)",
    )
    is_equitable: bool = Field(
        ...,
        description="Whether workload distribution is equitable (Gini < 0.15)",
    )
    mean_workload: float = Field(
        ...,
        description="Mean workload across all providers",
    )
    std_workload: float = Field(
        ...,
        description="Standard deviation of workload",
    )
    most_overloaded_provider: str | None = Field(
        None,
        description="Provider ID with highest workload",
    )
    most_underloaded_provider: str | None = Field(
        None,
        description="Provider ID with lowest workload",
    )
    max_workload: float = Field(
        ...,
        description="Maximum workload value",
    )
    min_workload: float = Field(
        ...,
        description="Minimum workload value",
    )
    recommendations: list[str] = Field(
        default_factory=list,
        description="Recommended rebalancing actions",
    )
    interpretation: str = Field(
        ...,
        description="Human-readable interpretation",
    )


class LorenzCurveRequest(BaseModel):
    """Request for Lorenz curve generation."""

    values: list[float] = Field(
        ...,
        description="List of workload values to analyze",
        min_length=1,
    )


class LorenzCurveResponse(BaseModel):
    """Response with Lorenz curve data."""

    population_shares: list[float] = Field(
        ...,
        description="Cumulative population share (x-axis)",
    )
    value_shares: list[float] = Field(
        ...,
        description="Cumulative value share (y-axis)",
    )
    equality_line: list[float] = Field(
        ...,
        description="45-degree equality line for comparison",
    )
    gini_coefficient: float = Field(
        ...,
        description="Gini coefficient calculated from curve",
    )


# =============================================================================
# Endpoints
# =============================================================================


@router.post("/calculate-equity-metrics", response_model=EquityMetricsResponse)
async def calculate_equity_metrics(
    request: EquityMetricsRequest,
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_admin()),
) -> EquityMetricsResponse:
    """
    Calculate workload equity metrics using Gini coefficient.

    Proxies to the MCP calculate_equity_metrics_tool. Calculates Gini coefficient
    and provides recommendations for workload rebalancing.

    Gini coefficient interpretation:
    - 0.0: Perfect equality (everyone has same workload)
    - < 0.15: Equitable distribution (target for medical scheduling)
    - 0.15 - 0.25: Moderate inequality
    - > 0.25: High inequality (requires intervention)

    **Requires admin role.**

    Args:
        request: Provider hours mapping and optional intensity weights

    Returns:
        Equity metrics including Gini coefficient and recommendations
    """
    logger.info(
        f"Calculating equity metrics for {len(request.provider_hours)} providers"
    )

    try:
        # Validate intensity weights if provided
        if request.intensity_weights is not None:
            # Ensure all providers have weights
            missing_weights = set(request.provider_hours.keys()) - set(
                request.intensity_weights.keys()
            )
            if missing_weights:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing intensity weights for providers: {missing_weights}",
                )

        # Call the equity_report function from resilience module
        report = equity_report(
            provider_hours=request.provider_hours,
            intensity_weights=request.intensity_weights,
        )

        # Generate interpretation based on Gini coefficient
        gini = report["gini"]
        if gini < 0.15:
            interpretation = (
                f"Workload distribution is equitable (Gini={gini:.3f}). "
                "All providers have balanced assignments."
            )
        elif gini < 0.25:
            interpretation = (
                f"Moderate workload inequality detected (Gini={gini:.3f}). "
                "Some providers may be overloaded. Review recommendations below."
            )
        else:
            interpretation = (
                f"High workload inequality detected (Gini={gini:.3f}). "
                "Significant rebalancing needed to prevent burnout."
            )

        return EquityMetricsResponse(
            gini_coefficient=gini,
            is_equitable=report["is_equitable"],
            mean_workload=report["mean_hours"],
            std_workload=report["std_hours"],
            most_overloaded_provider=report["most_overloaded"],
            most_underloaded_provider=report["most_underloaded"],
            max_workload=report["max_hours"],
            min_workload=report["min_hours"],
            recommendations=report["recommendations"],
            interpretation=interpretation,
        )

    except ValueError as e:
        logger.warning(f"Invalid equity metrics request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.exception(f"Error calculating equity metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate equity metrics",
        ) from e


@router.post("/generate-lorenz-curve", response_model=LorenzCurveResponse)
async def generate_lorenz_curve_endpoint(
    request: LorenzCurveRequest,
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_admin()),
) -> LorenzCurveResponse:
    """
    Generate Lorenz curve data for inequality visualization.

    Proxies to the MCP generate_lorenz_curve_tool. The Lorenz curve plots
    cumulative share of population against cumulative share of value.
    Perfect equality is the 45-degree diagonal line.

    **Requires admin role.**

    Args:
        request: List of workload values

    Returns:
        Lorenz curve coordinates for plotting
    """
    logger.info(f"Generating Lorenz curve for {len(request.values)} values")

    try:
        # Calculate Lorenz curve
        population_shares, value_shares = lorenz_curve(request.values)

        # Calculate Gini coefficient
        gini = gini_coefficient(request.values)

        # Generate equality line (45-degree diagonal)
        equality_line = population_shares.tolist()

        return LorenzCurveResponse(
            population_shares=population_shares.tolist(),
            value_shares=value_shares.tolist(),
            equality_line=equality_line,
            gini_coefficient=gini,
        )

    except ValueError as e:
        logger.warning(f"Invalid Lorenz curve request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.exception(f"Error generating Lorenz curve: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate Lorenz curve",
        ) from e
