"""
Constraint management tools for the Scheduler MCP server.

Provides MCP tools for listing, inspecting, toggling, and configuring
scheduling constraints via the FastAPI backend.
"""

import logging

from pydantic import BaseModel, Field

from .api_client import get_api_client

logger = logging.getLogger(__name__)


# =============================================================================
# Response Models
# =============================================================================


class ConstraintInfo(BaseModel):
    """Information about a single scheduling constraint."""

    name: str = Field(..., description="Constraint name")
    enabled: bool = Field(..., description="Whether constraint is enabled")
    priority: int = Field(..., description="Priority level (lower = higher priority)")
    weight: float = Field(..., description="Constraint weight for soft constraints")
    category: str = Field(..., description="Category (ACGME, CAPACITY, COVERAGE, etc.)")
    description: str = Field("", description="Human-readable description")
    dependencies: list[str] = Field(default_factory=list, description="Dependent constraints")
    enable_condition: str | None = Field(None, description="Condition for auto-enable")
    disable_reason: str | None = Field(None, description="Reason if disabled")


class ListConstraintsResult(BaseModel):
    """Result of listing constraints."""

    constraints: list[ConstraintInfo] = Field(
        default_factory=list, description="Constraint list"
    )
    total_count: int = Field(0, description="Total constraints")
    enabled_count: int = Field(0, description="Number of enabled constraints")
    disabled_count: int = Field(0, description="Number of disabled constraints")
    error: str | None = Field(None, description="Error message if failed")


class GetConstraintResult(BaseModel):
    """Result of getting a specific constraint."""

    success: bool = Field(..., description="Whether constraint was found")
    constraint: ConstraintInfo | None = Field(None, description="Constraint details")
    error: str | None = Field(None, description="Error message if failed")


class ToggleConstraintResult(BaseModel):
    """Result of enabling/disabling a constraint."""

    success: bool = Field(..., description="Whether toggle succeeded")
    message: str = Field("", description="Status message")
    constraint: ConstraintInfo | None = Field(None, description="Updated constraint")
    error: str | None = Field(None, description="Error message if failed")


class ApplyPresetResult(BaseModel):
    """Result of applying a constraint preset."""

    success: bool = Field(..., description="Whether preset was applied")
    message: str = Field("", description="Status message")
    enabled_constraints: list[str] = Field(
        default_factory=list, description="Enabled constraint names"
    )
    disabled_constraints: list[str] = Field(
        default_factory=list, description="Disabled constraint names"
    )
    error: str | None = Field(None, description="Error message if failed")


# =============================================================================
# Helper
# =============================================================================


def _parse_constraint(data: dict) -> ConstraintInfo:
    """Parse API response into ConstraintInfo."""
    return ConstraintInfo(
        name=data.get("name", ""),
        enabled=data.get("enabled", False),
        priority=data.get("priority", 0),
        weight=data.get("weight", 0.0),
        category=data.get("category", ""),
        description=data.get("description", ""),
        dependencies=data.get("dependencies", []),
        enable_condition=data.get("enable_condition"),
        disable_reason=data.get("disable_reason"),
    )


# =============================================================================
# Tool Functions
# =============================================================================


async def list_constraints(filter: str = "all") -> ListConstraintsResult:
    """
    List scheduling constraints with optional filter.

    Args:
        filter: Filter mode - "all", "enabled", or "disabled"

    Returns:
        ListConstraintsResult with constraint list and counts
    """
    if filter not in ("all", "enabled", "disabled"):
        return ListConstraintsResult(
            error=f"Invalid filter: {filter}. Must be 'all', 'enabled', or 'disabled'"
        )

    try:
        client = await get_api_client()
        results = await client.list_constraints(filter=filter)
        constraints = [_parse_constraint(c) for c in results]
        enabled = sum(1 for c in constraints if c.enabled)
        disabled = len(constraints) - enabled
        return ListConstraintsResult(
            constraints=constraints,
            total_count=len(constraints),
            enabled_count=enabled,
            disabled_count=disabled,
        )
    except Exception as e:
        logger.error(f"Failed to list constraints: {e}")
        return ListConstraintsResult(error=str(e))


async def get_constraint(name: str) -> GetConstraintResult:
    """
    Get details of a specific scheduling constraint.

    Args:
        name: Constraint name (e.g. "OvernightCallGeneration")

    Returns:
        GetConstraintResult with constraint details
    """
    try:
        client = await get_api_client()
        result = await client.get_constraint(name)
        return GetConstraintResult(
            success=True,
            constraint=_parse_constraint(result),
        )
    except Exception as e:
        logger.error(f"Failed to get constraint {name}: {e}")
        return GetConstraintResult(success=False, error=str(e))


async def list_constraints_by_category(category: str) -> ListConstraintsResult:
    """
    List constraints in a specific category.

    Args:
        category: Category name (ACGME, CAPACITY, COVERAGE, CALL, EQUITY,
                  PREFERENCE, SCHEDULING, FACULTY, CUSTOM)

    Returns:
        ListConstraintsResult with constraints in the category
    """
    try:
        client = await get_api_client()
        results = await client.list_constraints_by_category(category)
        constraints = [_parse_constraint(c) for c in results]
        enabled = sum(1 for c in constraints if c.enabled)
        return ListConstraintsResult(
            constraints=constraints,
            total_count=len(constraints),
            enabled_count=enabled,
            disabled_count=len(constraints) - enabled,
        )
    except Exception as e:
        logger.error(f"Failed to list constraints by category {category}: {e}")
        return ListConstraintsResult(error=str(e))


async def toggle_constraint(name: str, enabled: bool) -> ToggleConstraintResult:
    """
    Enable or disable a scheduling constraint.

    Args:
        name: Constraint name
        enabled: True to enable, False to disable

    Returns:
        ToggleConstraintResult with updated constraint state
    """
    try:
        client = await get_api_client()
        result = await client.toggle_constraint(name, enabled=enabled)
        action = "enabled" if enabled else "disabled"
        logger.info(f"Constraint {action}: {name}")
        constraint_data = result.get("constraint", {})
        return ToggleConstraintResult(
            success=result.get("success", True),
            message=result.get("message", f"Constraint '{name}' {action}"),
            constraint=_parse_constraint(constraint_data) if constraint_data else None,
        )
    except Exception as e:
        logger.error(f"Failed to toggle constraint {name}: {e}")
        return ToggleConstraintResult(success=False, error=str(e))


async def apply_constraint_preset(preset: str) -> ApplyPresetResult:
    """
    Apply a constraint preset configuration.

    Available presets:
        - minimal: Only essential constraints
        - strict: All constraints enabled with doubled weights
        - resilience_tier1: Core resilience constraints
        - resilience_tier2: All resilience constraints
        - call_scheduling: Call scheduling constraints
        - sports_medicine: Sports medicine constraints

    Args:
        preset: Preset name

    Returns:
        ApplyPresetResult with enabled/disabled constraint lists
    """
    valid_presets = [
        "minimal", "strict", "resilience_tier1", "resilience_tier2",
        "call_scheduling", "sports_medicine",
    ]
    if preset not in valid_presets:
        return ApplyPresetResult(
            success=False,
            error=f"Invalid preset: {preset}. Valid: {valid_presets}",
        )

    try:
        client = await get_api_client()
        result = await client.apply_constraint_preset(preset)
        logger.info(f"Applied constraint preset: {preset}")
        return ApplyPresetResult(
            success=result.get("success", True),
            message=result.get("message", f"Applied preset '{preset}'"),
            enabled_constraints=result.get("enabled_constraints", []),
            disabled_constraints=result.get("disabled_constraints", []),
        )
    except Exception as e:
        logger.error(f"Failed to apply preset {preset}: {e}")
        return ApplyPresetResult(success=False, error=str(e))
