"""
Constraint Management API Routes

Provides API endpoints for viewing and managing constraint configurations.

Endpoints:
    GET /api/v1/constraints/status - Get constraint status
    GET /api/v1/constraints - List all constraints
    GET /api/v1/constraints/enabled - List enabled constraints
    GET /api/v1/constraints/disabled - List disabled constraints
    POST /api/v1/constraints/{name}/enable - Enable a constraint
    POST /api/v1/constraints/{name}/disable - Disable a constraint
    POST /api/v1/constraints/preset/{preset} - Apply a preset
"""

import logging
from typing import Dict, List

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.scheduling.constraints.config import (
    ConstraintCategory,
    ConstraintConfig,
    get_constraint_config,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/constraints", tags=["constraints"])


class ConstraintStatusResponse(BaseModel):
    """Response model for constraint status."""

    name: str
    enabled: bool
    priority: int
    weight: float
    category: str
    description: str
    dependencies: list[str]
    enable_condition: str | None
    disable_reason: str | None


class ConstraintListResponse(BaseModel):
    """Response model for constraint list."""

    constraints: list[ConstraintStatusResponse]
    total: int
    enabled_count: int
    disabled_count: int


class ConstraintEnableResponse(BaseModel):
    """Response model for enable/disable operations."""

    success: bool
    message: str
    constraint: ConstraintStatusResponse


class PresetApplyResponse(BaseModel):
    """Response model for preset application."""

    success: bool
    message: str
    enabled_constraints: list[str]
    disabled_constraints: list[str]


def _constraint_to_response(config: ConstraintConfig) -> ConstraintStatusResponse:
    """Convert ConstraintConfig to response model."""
    return ConstraintStatusResponse(
        name=config.name,
        enabled=config.enabled,
        priority=config.priority.value,
        weight=config.weight,
        category=config.category.value,
        description=config.description,
        dependencies=config.dependencies,
        enable_condition=config.enable_condition,
        disable_reason=config.disable_reason,
    )


@router.get("/status", response_model=ConstraintListResponse)
async def get_constraint_status() -> ConstraintListResponse:
    """
    Get status of all constraints.

    Returns summary of enabled/disabled constraints and their configurations.

    Returns:
        ConstraintListResponse: Status of all constraints
    """
    try:
        config_manager = get_constraint_config()

        all_configs = list(config_manager._configs.values())
        enabled_count = len(config_manager.get_all_enabled())
        disabled_count = len(config_manager.get_all_disabled())

        constraints = [_constraint_to_response(c) for c in all_configs]

        return ConstraintListResponse(
            constraints=constraints,
            total=len(all_configs),
            enabled_count=enabled_count,
            disabled_count=disabled_count,
        )
    except (ValueError, KeyError, AttributeError) as e:
        logger.error(f"Error getting constraint status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get constraint status",
        )


@router.get("", response_model=ConstraintListResponse)
async def list_constraints() -> ConstraintListResponse:
    """
    List all constraints.

    Returns:
        ConstraintListResponse: List of all constraints
    """
    return await get_constraint_status()


@router.get("/enabled", response_model=list[ConstraintStatusResponse])
async def list_enabled_constraints() -> list[ConstraintStatusResponse]:
    """
    List enabled constraints.

    Returns:
        List[ConstraintStatusResponse]: List of enabled constraints
    """
    try:
        config_manager = get_constraint_config()
        enabled = config_manager.get_all_enabled()

        return [_constraint_to_response(c) for c in enabled]
    except (ValueError, KeyError, AttributeError) as e:
        logger.error(f"Error listing enabled constraints: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list enabled constraints",
        )


@router.get("/disabled", response_model=list[ConstraintStatusResponse])
async def list_disabled_constraints() -> list[ConstraintStatusResponse]:
    """
    List disabled constraints.

    Returns:
        List[ConstraintStatusResponse]: List of disabled constraints
    """
    try:
        config_manager = get_constraint_config()
        disabled = config_manager.get_all_disabled()

        return [_constraint_to_response(c) for c in disabled]
    except Exception as e:
        logger.error(f"Error listing disabled constraints: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list disabled constraints",
        )


@router.get("/category/{category}", response_model=list[ConstraintStatusResponse])
async def list_constraints_by_category(category: str) -> list[ConstraintStatusResponse]:
    """
    List constraints by category.

    Args:
        category: Constraint category (ACGME, CAPACITY, COVERAGE, etc.)

    Returns:
        List[ConstraintStatusResponse]: List of constraints in category
    """
    try:
        # Validate category
        try:
            cat_enum = ConstraintCategory(category.upper())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid category: {category}. Valid categories: {[c.value for c in ConstraintCategory]}",
            )

        config_manager = get_constraint_config()

        # Get all constraints in category (enabled and disabled)
        constraints = [
            c for c in config_manager._configs.values() if c.category == cat_enum
        ]

        return [_constraint_to_response(c) for c in constraints]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing constraints by category: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list constraints by category",
        )


@router.post("/{name}/enable", response_model=ConstraintEnableResponse)
async def enable_constraint(name: str) -> ConstraintEnableResponse:
    """
    Enable a constraint.

    Args:
        name: Constraint name

    Returns:
        ConstraintEnableResponse: Result of enable operation
    """
    try:
        config_manager = get_constraint_config()

        # Check if constraint exists
        constraint = config_manager.get(name)
        if not constraint:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Constraint '{name}' not found",
            )

        # Check if already enabled
        if constraint.enabled:
            return ConstraintEnableResponse(
                success=True,
                message=f"Constraint '{name}' is already enabled",
                constraint=_constraint_to_response(constraint),
            )

        # Enable constraint
        success = config_manager.enable(name)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to enable constraint '{name}'",
            )

        # Get updated constraint
        constraint = config_manager.get(name)

        logger.info(f"Enabled constraint via API: {name}")

        return ConstraintEnableResponse(
            success=True,
            message=f"Successfully enabled constraint '{name}'",
            constraint=_constraint_to_response(constraint),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enabling constraint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to enable constraint",
        )


@router.post("/{name}/disable", response_model=ConstraintEnableResponse)
async def disable_constraint(name: str) -> ConstraintEnableResponse:
    """
    Disable a constraint.

    Args:
        name: Constraint name

    Returns:
        ConstraintEnableResponse: Result of disable operation
    """
    try:
        config_manager = get_constraint_config()

        # Check if constraint exists
        constraint = config_manager.get(name)
        if not constraint:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Constraint '{name}' not found",
            )

        # Check if already disabled
        if not constraint.enabled:
            return ConstraintEnableResponse(
                success=True,
                message=f"Constraint '{name}' is already disabled",
                constraint=_constraint_to_response(constraint),
            )

        # Disable constraint
        success = config_manager.disable(name)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to disable constraint '{name}'",
            )

        # Get updated constraint
        constraint = config_manager.get(name)

        logger.info(f"Disabled constraint via API: {name}")

        return ConstraintEnableResponse(
            success=True,
            message=f"Successfully disabled constraint '{name}'",
            constraint=_constraint_to_response(constraint),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disabling constraint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disable constraint",
        )


@router.post("/preset/{preset}", response_model=PresetApplyResponse)
async def apply_constraint_preset(preset: str) -> PresetApplyResponse:
    """
    Apply a constraint preset.

    Valid presets:
    - minimal: Only essential constraints
    - strict: All constraints enabled with doubled weights
    - resilience_tier1: Core resilience constraints
    - resilience_tier2: All resilience constraints
    - call_scheduling: Call scheduling constraints
    - sports_medicine: Sports medicine constraints

    Args:
        preset: Preset name

    Returns:
        PresetApplyResponse: Result of preset application
    """
    try:
        valid_presets = [
            "minimal",
            "strict",
            "resilience_tier1",
            "resilience_tier2",
            "call_scheduling",
            "sports_medicine",
        ]

        if preset not in valid_presets:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid preset: {preset}. Valid presets: {valid_presets}",
            )

        config_manager = get_constraint_config()

        # Get before state
        before_enabled = [c.name for c in config_manager.get_all_enabled()]

        # Apply preset
        config_manager.apply_preset(preset)

        # Get after state
        after_enabled = [c.name for c in config_manager.get_all_enabled()]
        after_disabled = [c.name for c in config_manager.get_all_disabled()]

        # Calculate what changed
        newly_enabled = [c for c in after_enabled if c not in before_enabled]
        newly_disabled = [c for c in before_enabled if c not in after_enabled]

        logger.info(f"Applied constraint preset via API: {preset}")

        return PresetApplyResponse(
            success=True,
            message=f"Successfully applied preset '{preset}'",
            enabled_constraints=after_enabled,
            disabled_constraints=after_disabled,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error applying preset: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to apply preset",
        )


@router.get("/{name}", response_model=ConstraintStatusResponse)
async def get_constraint(name: str) -> ConstraintStatusResponse:
    """
    Get details of a specific constraint.

    Args:
        name: Constraint name

    Returns:
        ConstraintStatusResponse: Constraint details
    """
    try:
        config_manager = get_constraint_config()

        constraint = config_manager.get(name)
        if not constraint:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Constraint '{name}' not found",
            )

        return _constraint_to_response(constraint)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting constraint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get constraint",
        )
