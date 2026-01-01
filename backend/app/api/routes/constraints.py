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
from typing import Any

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


@router.get(
    "/status",
    response_model=ConstraintListResponse,
    summary="Get constraint system status",
    description="""
    Retrieve comprehensive status of the constraint management system.

    Returns a complete overview including:
    - **All Constraints**: Full list of registered constraints
    - **Enabled Count**: Number of currently active constraints
    - **Disabled Count**: Number of inactive constraints
    - **Configuration Details**: Priority, weight, category, and dependencies for each

    This endpoint is useful for system health monitoring and configuration auditing.
    """,
    responses={
        200: {"description": "Constraint status retrieved successfully"},
        500: {"description": "Failed to retrieve constraint status"},
    },
)
async def get_constraint_status():
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
    except Exception as e:
        logger.error(f"Error getting constraint status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get constraint status",
        )


@router.get(
    "",
    response_model=ConstraintListResponse,
    summary="List all constraints",
    description="""
    List all registered scheduling constraints in the system.

    This is an alias for the `/status` endpoint and returns identical data.
    Provides a complete view of all constraints with their current configuration,
    enabled/disabled status, priorities, and dependencies.

    Useful for configuration management and debugging scheduling behavior.
    """,
    responses={
        200: {"description": "Constraints listed successfully"},
        500: {"description": "Failed to list constraints"},
    },
)
async def list_constraints():
    """
    List all constraints.

    Returns:
        ConstraintListResponse: List of all constraints
    """
    return await get_constraint_status()


@router.get(
    "/enabled",
    response_model=list[ConstraintStatusResponse],
    summary="List enabled constraints",
    description="""
    Retrieve only the constraints that are currently enabled and active.

    Enabled constraints are actively enforced during schedule generation and
    validation. This endpoint is useful for:
    - Understanding which rules are currently in effect
    - Troubleshooting why certain schedules are rejected
    - Verifying constraint configuration before schedule generation

    Each constraint includes priority, weight, category, and dependency information.
    """,
    responses={
        200: {"description": "Enabled constraints listed successfully"},
        500: {"description": "Failed to list enabled constraints"},
    },
)
async def list_enabled_constraints():
    """
    List enabled constraints.

    Returns:
        list[ConstraintStatusResponse]: List of enabled constraints
    """
    try:
        config_manager = get_constraint_config()
        enabled = config_manager.get_all_enabled()

        return [_constraint_to_response(c) for c in enabled]
    except Exception as e:
        logger.error(f"Error listing enabled constraints: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list enabled constraints",
        )


@router.get(
    "/disabled",
    response_model=list[ConstraintStatusResponse],
    summary="List disabled constraints",
    description="""
    Retrieve only the constraints that are currently disabled and inactive.

    Disabled constraints are registered in the system but not enforced during
    schedule generation or validation. This endpoint is useful for:
    - Identifying available but unused constraints
    - Planning constraint configuration changes
    - Auditing which rules have been intentionally turned off

    Each constraint includes the reason for being disabled (if provided) along
    with its configuration details.
    """,
    responses={
        200: {"description": "Disabled constraints listed successfully"},
        500: {"description": "Failed to list disabled constraints"},
    },
)
async def list_disabled_constraints():
    """
    List disabled constraints.

    Returns:
        list[ConstraintStatusResponse]: List of disabled constraints
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


@router.get(
    "/category/{category}",
    response_model=list[ConstraintStatusResponse],
    summary="List constraints by category",
    description="""
    Retrieve all constraints belonging to a specific category.

    Valid categories include:
    - **ACGME**: Work hour limits, supervision ratios, rest requirements
    - **CAPACITY**: Staffing levels, concurrent assignments
    - **COVERAGE**: Shift coverage, call requirements, geographic distribution
    - **PREFERENCE**: Individual preferences, soft constraints
    - **RESILIENCE**: Burnout prevention, workload balancing, N-1/N-2 contingency
    - **FAIRNESS**: Equitable distribution of desirable/undesirable shifts

    Returns all constraints in the category regardless of enabled/disabled status.
    This is useful for understanding the full scope of rules in each area.
    """,
    responses={
        200: {"description": "Constraints in category listed successfully"},
        400: {"description": "Invalid category name provided"},
        500: {"description": "Failed to list constraints by category"},
    },
)
async def list_constraints_by_category(category: str):
    """
    List constraints by category.

    Args:
        category: Constraint category (ACGME, CAPACITY, COVERAGE, etc.)

    Returns:
        list[ConstraintStatusResponse]: List of constraints in category
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


@router.post(
    "/{name}/enable",
    response_model=ConstraintEnableResponse,
    summary="Enable a constraint",
    description="""
    Enable a specific constraint by name, making it active for schedule generation.

    When a constraint is enabled:
    - It will be enforced during all schedule generation and validation operations
    - Its weight and priority will affect scheduling decisions
    - Dependencies will be checked and must also be enabled
    - The change takes effect immediately for new scheduling operations

    **Note**: If the constraint is already enabled, this operation is idempotent
    and will return success without making changes.

    **Example constraint names**: `acgme_80_hour_rule`, `n_minus_1_resilience`,
    `fair_weekend_distribution`
    """,
    responses={
        200: {"description": "Constraint enabled successfully"},
        404: {"description": "Constraint with the specified name not found"},
        500: {"description": "Failed to enable constraint"},
    },
)
async def enable_constraint(name: str):
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


@router.post(
    "/{name}/disable",
    response_model=ConstraintEnableResponse,
    summary="Disable a constraint",
    description="""
    Disable a specific constraint by name, removing it from active enforcement.

    When a constraint is disabled:
    - It will NOT be enforced during schedule generation or validation
    - Its weight and priority will not affect scheduling decisions
    - Other constraints that depend on it may be automatically disabled
    - The change takes effect immediately for new scheduling operations

    **Note**: If the constraint is already disabled, this operation is idempotent
    and will return success without making changes.

    **Warning**: Disabling critical constraints (e.g., ACGME work hour limits)
    may result in non-compliant schedules. Use with caution.

    **Example constraint names**: `acgme_80_hour_rule`, `n_minus_1_resilience`,
    `fair_weekend_distribution`
    """,
    responses={
        200: {"description": "Constraint disabled successfully"},
        404: {"description": "Constraint with the specified name not found"},
        500: {"description": "Failed to disable constraint"},
    },
)
async def disable_constraint(name: str):
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


@router.post(
    "/preset/{preset}",
    response_model=PresetApplyResponse,
    summary="Apply a constraint preset",
    description="""
    Apply a predefined constraint configuration preset.

    Presets provide quick, battle-tested configurations for common scenarios:

    - **minimal**: Only essential ACGME compliance constraints. Use for maximum
      scheduling flexibility when compliance is the only hard requirement.

    - **strict**: All constraints enabled with doubled weights. Use when you need
      maximum adherence to all rules and preferences, even if it limits schedule
      options.

    - **resilience_tier1**: Core resilience constraints (80% utilization, N-1
      contingency, defense in depth). Use for baseline burnout prevention.

    - **resilience_tier2**: All resilience constraints including advanced
      metrics (SPC monitoring, Erlang coverage, fatigue creep). Use for
      comprehensive wellbeing protection.

    - **call_scheduling**: Optimized for inpatient call and night float
      scheduling. Balances coverage with rest requirements.

    - **sports_medicine**: Specialized for sports medicine programs with
      unique coverage patterns and event-based scheduling.

    Applying a preset will enable/disable multiple constraints simultaneously.
    The response includes lists of what was enabled and disabled.
    """,
    responses={
        200: {"description": "Preset applied successfully"},
        400: {"description": "Invalid preset name"},
        500: {"description": "Failed to apply preset"},
    },
)
async def apply_constraint_preset(preset: str):
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


@router.get(
    "/{name}",
    response_model=ConstraintStatusResponse,
    summary="Get constraint details",
    description="""
    Retrieve detailed information about a specific constraint by name.

    Returns comprehensive configuration including:
    - **Enabled Status**: Whether the constraint is currently active
    - **Priority**: Execution priority (higher priority constraints run first)
    - **Weight**: Relative importance in the objective function
    - **Category**: Classification (ACGME, CAPACITY, COVERAGE, etc.)
    - **Description**: Human-readable explanation of the constraint's purpose
    - **Dependencies**: Other constraints that must be enabled for this one to work
    - **Enable Condition**: Conditions under which this constraint should be enabled
    - **Disable Reason**: Explanation if the constraint is currently disabled

    Useful for debugging scheduling behavior, understanding why certain assignments
    are rejected, and auditing constraint configuration.

    **Example constraint names**: `acgme_80_hour_rule`, `n_minus_1_resilience`,
    `fair_weekend_distribution`
    """,
    responses={
        200: {"description": "Constraint details retrieved successfully"},
        404: {"description": "Constraint with the specified name not found"},
        500: {"description": "Failed to get constraint details"},
    },
)
async def get_constraint(name: str):
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
