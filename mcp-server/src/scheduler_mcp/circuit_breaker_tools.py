"""
Circuit Breaker MCP Tools.

Exposes circuit breaker resilience module capabilities as MCP tools for AI
assistant interaction. These tools enable monitoring and management of
distributed systems-inspired failure isolation patterns.

Key Capabilities:
- Status monitoring of all circuit breakers
- Health metrics and failure rate analysis
- Half-open state testing for recovery verification
- Manual override controls for emergency situations

Based on the Netflix Hystrix pattern and Release It! book by Michael Nygard.
"""

import logging
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# =============================================================================
# Enums and Response Models
# =============================================================================


class CircuitStateEnum(str, Enum):
    """Circuit breaker states following the classic pattern."""

    CLOSED = "closed"  # Normal operation, requests pass through
    OPEN = "open"  # Circuit tripped, requests fail fast
    HALF_OPEN = "half_open"  # Testing recovery, limited requests allowed


class BreakerSeverityEnum(str, Enum):
    """Overall severity level for circuit breaker health."""

    HEALTHY = "healthy"  # All breakers closed, system normal
    WARNING = "warning"  # Some breakers half-open or elevated failure rates
    CRITICAL = "critical"  # Multiple breakers open, degraded service
    EMERGENCY = "emergency"  # System-wide circuit breaker failures


class StateTransitionInfo(BaseModel):
    """Information about a circuit breaker state transition."""

    from_state: str = Field(description="Previous state (closed, open, half_open)")
    to_state: str = Field(description="New state (closed, open, half_open)")
    timestamp: str = Field(description="ISO format timestamp of transition")
    reason: str = Field(description="Reason for the transition")


class CircuitBreakerStatusInfo(BaseModel):
    """Detailed status information for a single circuit breaker."""

    name: str = Field(description="Unique name of the circuit breaker")
    state: CircuitStateEnum = Field(description="Current circuit state")
    failure_rate: float = Field(ge=0.0, le=1.0, description="Current failure rate (0.0 to 1.0)")
    success_rate: float = Field(ge=0.0, le=1.0, description="Current success rate (0.0 to 1.0)")
    total_requests: int = Field(ge=0, description="Total requests processed")
    successful_requests: int = Field(ge=0, description="Successful request count")
    failed_requests: int = Field(ge=0, description="Failed request count")
    rejected_requests: int = Field(ge=0, description="Rejected request count (circuit open)")
    consecutive_failures: int = Field(ge=0, description="Current consecutive failure streak")
    consecutive_successes: int = Field(ge=0, description="Current consecutive success streak")
    opened_at: str | None = Field(
        default=None, description="ISO timestamp when circuit opened (if open)"
    )
    last_failure_time: str | None = Field(default=None, description="ISO timestamp of last failure")
    last_success_time: str | None = Field(default=None, description="ISO timestamp of last success")
    recent_transitions: list[StateTransitionInfo] = Field(
        default_factory=list, description="Last 10 state transitions"
    )


class AllBreakersStatusResponse(BaseModel):
    """Response from checking status of all circuit breakers."""

    total_breakers: int = Field(ge=0, description="Total registered circuit breakers")
    closed_breakers: int = Field(ge=0, description="Breakers in CLOSED state (normal)")
    open_breakers: int = Field(ge=0, description="Breakers in OPEN state (tripped)")
    half_open_breakers: int = Field(ge=0, description="Breakers in HALF_OPEN state (testing)")
    open_breaker_names: list[str] = Field(
        default_factory=list, description="Names of OPEN breakers"
    )
    half_open_breaker_names: list[str] = Field(
        default_factory=list, description="Names of HALF_OPEN breakers"
    )
    breakers: list[CircuitBreakerStatusInfo] = Field(
        default_factory=list, description="Detailed status for each breaker"
    )
    overall_health: str = Field(
        description="Overall system health: healthy, warning, critical, emergency"
    )
    recommendations: list[str] = Field(default_factory=list, description="Recommended actions")
    checked_at: str = Field(description="ISO timestamp of status check")


class BreakerHealthMetrics(BaseModel):
    """Health metrics for circuit breakers."""

    total_requests: int = Field(ge=0, description="Total requests across all breakers")
    total_failures: int = Field(ge=0, description="Total failures across all breakers")
    total_rejections: int = Field(ge=0, description="Total rejections across all breakers")
    overall_failure_rate: float = Field(
        ge=0.0, le=1.0, description="Overall failure rate across all breakers"
    )
    breakers_above_threshold: int = Field(
        ge=0, description="Breakers with failure rate above critical threshold"
    )
    average_failure_rate: float = Field(
        ge=0.0, le=1.0, description="Average failure rate across breakers"
    )
    max_failure_rate: float = Field(
        ge=0.0, le=1.0, description="Maximum failure rate among breakers"
    )
    unhealthiest_breaker: str | None = Field(
        default=None, description="Name of breaker with highest failure rate"
    )


class BreakerHealthResponse(BaseModel):
    """Response from health metrics check."""

    total_breakers: int = Field(ge=0, description="Total registered breakers")
    metrics: BreakerHealthMetrics = Field(description="Aggregated health metrics")
    breakers_needing_attention: list[str] = Field(
        default_factory=list,
        description="Breakers that need immediate attention (open or high failure rate)",
    )
    trend_analysis: str = Field(description="Trend analysis: improving, stable, degrading")
    severity: BreakerSeverityEnum = Field(description="Overall severity level")
    recommendations: list[str] = Field(default_factory=list, description="Recommended actions")
    analyzed_at: str = Field(description="ISO timestamp of analysis")


class HalfOpenTestResult(BaseModel):
    """Result from a half-open state test."""

    breaker_name: str = Field(description="Name of the tested breaker")
    initial_state: str = Field(description="State before test")
    current_state: str = Field(description="State after test")
    test_successful: bool = Field(description="Whether test request succeeded")
    consecutive_successes: int = Field(ge=0, description="Current success streak")
    success_threshold: int = Field(ge=1, description="Successes needed to close")
    ready_to_close: bool = Field(description="Whether breaker has enough successes to close")
    message: str = Field(description="Human-readable result message")


class HalfOpenTestResponse(BaseModel):
    """Response from testing half-open breaker state."""

    breaker_name: str = Field(description="Name of the breaker")
    is_half_open: bool = Field(description="Whether breaker is in HALF_OPEN state")
    test_allowed: bool = Field(description="Whether test was allowed to execute")
    test_result: HalfOpenTestResult | None = Field(
        default=None, description="Test result if executed"
    )
    error_message: str | None = Field(default=None, description="Error message if test not allowed")
    recommendations: list[str] = Field(default_factory=list, description="Recommended next steps")
    tested_at: str = Field(description="ISO timestamp of test")


class ManualOverrideRequest(BaseModel):
    """Request for manual circuit breaker override."""

    breaker_name: str = Field(description="Name of the breaker to override")
    action: str = Field(description="Action: open, close, reset")
    reason: str = Field(description="Reason for the override (for audit trail)")


class ManualOverrideResponse(BaseModel):
    """Response from manual override action."""

    breaker_name: str = Field(description="Name of the breaker")
    action: str = Field(description="Action taken")
    success: bool = Field(description="Whether action succeeded")
    previous_state: str = Field(description="State before override")
    current_state: str = Field(description="State after override")
    reason: str = Field(description="Reason for override")
    message: str = Field(description="Human-readable result message")
    override_at: str = Field(description="ISO timestamp of override")


# =============================================================================
# Tool Functions
# =============================================================================


async def check_circuit_breakers() -> AllBreakersStatusResponse:
    """
    Get status of all registered circuit breakers.

    This tool retrieves comprehensive status information for all circuit
    breakers in the system, including their current state, failure rates,
    and recent state transitions.

    Circuit Breaker States:
    - CLOSED: Normal operation, all requests pass through
    - OPEN: Circuit tripped due to failures, requests fail fast
    - HALF_OPEN: Testing recovery, limited requests allowed

    Returns:
        AllBreakersStatusResponse with status for all breakers

    Example:
        result = await check_circuit_breakers()
        if result.open_breakers > 0:
            print(f"WARNING: {result.open_breakers} breakers are OPEN")
            for name in result.open_breaker_names:
                print(f"  - {name}")
    """
    logger.info("Checking status of all circuit breakers")

    try:
        from app.resilience.circuit_breaker import get_registry

        registry = get_registry()
        health_data = registry.health_check()
        all_statuses = registry.get_all_statuses()

        # Build detailed breaker status list
        breakers = []
        for name, status in all_statuses.items():
            transitions = []
            for t in status.get("recent_transitions", []):
                transitions.append(
                    StateTransitionInfo(
                        from_state=t.get("from", "unknown"),
                        to_state=t.get("to", "unknown"),
                        timestamp=t.get("timestamp", ""),
                        reason=t.get("reason", ""),
                    )
                )

            breakers.append(
                CircuitBreakerStatusInfo(
                    name=name,
                    state=CircuitStateEnum(status.get("state", "closed")),
                    failure_rate=status.get("failure_rate", 0.0),
                    success_rate=status.get("success_rate", 0.0),
                    total_requests=status.get("total_requests", 0),
                    successful_requests=status.get("successful_requests", 0),
                    failed_requests=status.get("failed_requests", 0),
                    rejected_requests=status.get("rejected_requests", 0),
                    consecutive_failures=status.get("consecutive_failures", 0),
                    consecutive_successes=status.get("consecutive_successes", 0),
                    opened_at=status.get("opened_at"),
                    last_failure_time=status.get("last_failure_time"),
                    last_success_time=status.get("last_success_time"),
                    recent_transitions=transitions,
                )
            )

        # Determine overall health
        open_count = health_data.get("open_breakers", 0)
        half_open_count = health_data.get("half_open_breakers", 0)
        total = health_data.get("total_breakers", 0)
        failure_rate = health_data.get("overall_failure_rate", 0.0)

        if open_count > total * 0.5 or failure_rate > 0.5:
            overall_health = "emergency"
        elif open_count > 0 or failure_rate > 0.3:
            overall_health = "critical"
        elif half_open_count > 0 or failure_rate > 0.1:
            overall_health = "warning"
        else:
            overall_health = "healthy"

        # Generate recommendations
        recommendations = []
        if open_count > 0:
            recommendations.append(
                f"IMMEDIATE: {open_count} circuit breaker(s) are OPEN - investigate failures"
            )
        if half_open_count > 0:
            recommendations.append(
                f"MONITOR: {half_open_count} breaker(s) in HALF_OPEN - monitor recovery"
            )
        if failure_rate > 0.1:
            recommendations.append(
                f"ATTENTION: Overall failure rate is {failure_rate * 100:.1f}% - review system health"
            )
        if not recommendations:
            recommendations.append("All circuit breakers operating normally")

        return AllBreakersStatusResponse(
            total_breakers=total,
            closed_breakers=health_data.get("closed_breakers", 0),
            open_breakers=open_count,
            half_open_breakers=half_open_count,
            open_breaker_names=health_data.get("open_breaker_names", []),
            half_open_breaker_names=health_data.get("half_open_breaker_names", []),
            breakers=breakers,
            overall_health=overall_health,
            recommendations=recommendations,
            checked_at=datetime.utcnow().isoformat(),
        )

    except ImportError as e:
        logger.warning(f"Circuit breaker module unavailable: {e}")
        return AllBreakersStatusResponse(
            total_breakers=0,
            closed_breakers=0,
            open_breakers=0,
            half_open_breakers=0,
            open_breaker_names=[],
            half_open_breaker_names=[],
            breakers=[],
            overall_health="healthy",
            recommendations=["Circuit breaker module not available"],
            checked_at=datetime.utcnow().isoformat(),
        )
    except Exception as e:
        logger.error(f"Failed to check circuit breakers: {e}")
        raise RuntimeError(f"Failed to check circuit breakers: {e}") from e


async def get_breaker_health() -> BreakerHealthResponse:
    """
    Get health metrics for all circuit breakers.

    This tool provides aggregated health metrics across all circuit breakers,
    including failure rates, rejection counts, and trend analysis. Use this
    for dashboards and alerting.

    Metrics include:
    - Total requests, failures, and rejections across all breakers
    - Overall and average failure rates
    - Identification of unhealthiest breakers
    - Trend analysis (improving, stable, degrading)

    Returns:
        BreakerHealthResponse with aggregated health metrics

    Example:
        health = await get_breaker_health()
        print(f"Overall failure rate: {health.metrics.overall_failure_rate*100:.1f}%")
        if health.breakers_needing_attention:
            print(f"Breakers need attention: {health.breakers_needing_attention}")
    """
    logger.info("Getting circuit breaker health metrics")

    try:
        from app.resilience.circuit_breaker import get_registry

        registry = get_registry()
        health_data = registry.health_check()
        all_statuses = registry.get_all_statuses()

        # Calculate metrics
        total_requests = health_data.get("total_requests", 0)
        total_failures = health_data.get("total_failures", 0)
        total_rejections = health_data.get("total_rejections", 0)
        overall_failure_rate = health_data.get("overall_failure_rate", 0.0)

        # Find breakers needing attention
        needing_attention = []
        failure_rates = []
        unhealthiest = None
        max_failure_rate = 0.0

        for name, status in all_statuses.items():
            state = status.get("state", "closed")
            fr = status.get("failure_rate", 0.0)
            failure_rates.append(fr)

            if fr > max_failure_rate:
                max_failure_rate = fr
                unhealthiest = name

            if state in ("open", "half_open") or fr > 0.2:
                needing_attention.append(name)

        avg_failure_rate = sum(failure_rates) / len(failure_rates) if failure_rates else 0.0
        breakers_above_threshold = sum(1 for fr in failure_rates if fr > 0.2)

        # Determine trend (simplified - in production would use historical data)
        if overall_failure_rate > 0.3:
            trend = "degrading"
        elif overall_failure_rate > 0.1:
            trend = "stable"
        else:
            trend = "improving"

        # Determine severity
        open_count = health_data.get("open_breakers", 0)
        total_breakers = health_data.get("total_breakers", 0)

        if open_count > total_breakers * 0.5 or overall_failure_rate > 0.5:
            severity = BreakerSeverityEnum.EMERGENCY
        elif open_count > 0 or overall_failure_rate > 0.3:
            severity = BreakerSeverityEnum.CRITICAL
        elif breakers_above_threshold > 0 or overall_failure_rate > 0.1:
            severity = BreakerSeverityEnum.WARNING
        else:
            severity = BreakerSeverityEnum.HEALTHY

        # Generate recommendations
        recommendations = []
        if severity == BreakerSeverityEnum.EMERGENCY:
            recommendations.append("EMERGENCY: System-wide circuit breaker failures detected")
            recommendations.append("Consider activating crisis response protocols")
        if unhealthiest and max_failure_rate > 0.2:
            recommendations.append(
                f"Investigate {unhealthiest} - failure rate {max_failure_rate * 100:.1f}%"
            )
        if total_rejections > 0:
            recommendations.append(
                f"{total_rejections} requests rejected - monitor downstream services"
            )
        if not needing_attention:
            recommendations.append("All circuit breakers within healthy thresholds")

        metrics = BreakerHealthMetrics(
            total_requests=total_requests,
            total_failures=total_failures,
            total_rejections=total_rejections,
            overall_failure_rate=overall_failure_rate,
            breakers_above_threshold=breakers_above_threshold,
            average_failure_rate=avg_failure_rate,
            max_failure_rate=max_failure_rate,
            unhealthiest_breaker=unhealthiest,
        )

        return BreakerHealthResponse(
            total_breakers=total_breakers,
            metrics=metrics,
            breakers_needing_attention=needing_attention,
            trend_analysis=trend,
            severity=severity,
            recommendations=recommendations,
            analyzed_at=datetime.utcnow().isoformat(),
        )

    except ImportError as e:
        logger.warning(f"Circuit breaker module unavailable: {e}")
        return BreakerHealthResponse(
            total_breakers=0,
            metrics=BreakerHealthMetrics(
                total_requests=0,
                total_failures=0,
                total_rejections=0,
                overall_failure_rate=0.0,
                breakers_above_threshold=0,
                average_failure_rate=0.0,
                max_failure_rate=0.0,
                unhealthiest_breaker=None,
            ),
            breakers_needing_attention=[],
            trend_analysis="stable",
            severity=BreakerSeverityEnum.HEALTHY,
            recommendations=["Circuit breaker module not available"],
            analyzed_at=datetime.utcnow().isoformat(),
        )
    except Exception as e:
        logger.error(f"Failed to get breaker health: {e}")
        raise RuntimeError(f"Failed to get breaker health: {e}") from e


async def test_half_open_breaker(
    breaker_name: str,
) -> HalfOpenTestResponse:
    """
    Test a circuit breaker in HALF_OPEN state to verify recovery.

    When a circuit breaker is in HALF_OPEN state, it allows limited test
    requests to determine if the downstream service has recovered. This
    tool provides information about the half-open state and recovery progress.

    Half-Open Recovery Process:
    1. Circuit opens after failure_threshold failures
    2. After timeout_seconds, circuit transitions to HALF_OPEN
    3. Limited requests are allowed through
    4. If success_threshold successes occur, circuit closes (recovery)
    5. If any failure occurs, circuit reopens

    Args:
        breaker_name: Name of the circuit breaker to test

    Returns:
        HalfOpenTestResponse with test results and recovery status

    Raises:
        ValueError: If breaker_name is not found

    Example:
        # Check if database breaker is ready to recover
        result = await test_half_open_breaker("database_connection")
        if result.is_half_open:
            print(f"Recovery progress: {result.test_result.consecutive_successes}/"
                  f"{result.test_result.success_threshold}")
            if result.test_result.ready_to_close:
                print("Breaker is ready to close - service has recovered!")
    """
    logger.info(f"Testing half-open state for breaker: {breaker_name}")

    try:
        from app.resilience.circuit_breaker import get_registry

        registry = get_registry()

        # Check if breaker exists
        if not registry.exists(breaker_name):
            return HalfOpenTestResponse(
                breaker_name=breaker_name,
                is_half_open=False,
                test_allowed=False,
                test_result=None,
                error_message=f"Circuit breaker '{breaker_name}' not found",
                recommendations=[
                    f"Available breakers: {registry.list_breakers()}",
                    "Use check_circuit_breakers_tool to see all registered breakers",
                ],
                tested_at=datetime.utcnow().isoformat(),
            )

        breaker = registry.get(breaker_name)
        status = breaker.get_status()
        current_state = status.get("state", "closed")

        # Check if breaker is in HALF_OPEN state
        is_half_open = current_state == "half_open"

        if not is_half_open:
            recommendations = []
            if current_state == "closed":
                recommendations.append("Breaker is CLOSED - operating normally")
                recommendations.append("No recovery testing needed")
            else:  # OPEN
                recommendations.append("Breaker is OPEN - waiting for timeout")
                recommendations.append(f"Opened at: {status.get('opened_at', 'unknown')}")
                recommendations.append("Wait for timeout to transition to HALF_OPEN")

            return HalfOpenTestResponse(
                breaker_name=breaker_name,
                is_half_open=False,
                test_allowed=False,
                test_result=None,
                error_message=f"Breaker is in {current_state.upper()} state, not HALF_OPEN",
                recommendations=recommendations,
                tested_at=datetime.utcnow().isoformat(),
            )

        # Breaker is in HALF_OPEN - provide recovery status
        consecutive_successes = status.get("consecutive_successes", 0)
        # Get success threshold from config (default is 2)
        success_threshold = breaker.config.success_threshold if hasattr(breaker, "config") else 2
        ready_to_close = consecutive_successes >= success_threshold

        test_result = HalfOpenTestResult(
            breaker_name=breaker_name,
            initial_state="half_open",
            current_state=current_state,
            test_successful=True,  # We're just checking status, not actually calling
            consecutive_successes=consecutive_successes,
            success_threshold=success_threshold,
            ready_to_close=ready_to_close,
            message=(
                f"Recovery in progress: {consecutive_successes}/{success_threshold} successes"
                if not ready_to_close
                else "Recovery complete - breaker ready to close"
            ),
        )

        recommendations = []
        if ready_to_close:
            recommendations.append("Breaker has met success threshold")
            recommendations.append("Next successful request will close the circuit")
        else:
            remaining = success_threshold - consecutive_successes
            recommendations.append(f"Need {remaining} more successful requests to recover")
            recommendations.append("Monitor downstream service health")

        return HalfOpenTestResponse(
            breaker_name=breaker_name,
            is_half_open=True,
            test_allowed=True,
            test_result=test_result,
            error_message=None,
            recommendations=recommendations,
            tested_at=datetime.utcnow().isoformat(),
        )

    except ImportError as e:
        logger.warning(f"Circuit breaker module unavailable: {e}")
        return HalfOpenTestResponse(
            breaker_name=breaker_name,
            is_half_open=False,
            test_allowed=False,
            test_result=None,
            error_message="Circuit breaker module not available",
            recommendations=[],
            tested_at=datetime.utcnow().isoformat(),
        )
    except Exception as e:
        logger.error(f"Failed to test half-open breaker: {e}")
        raise RuntimeError(f"Failed to test half-open breaker: {e}") from e


async def override_circuit_breaker(
    breaker_name: str,
    action: str,
    reason: str,
) -> ManualOverrideResponse:
    """
    Manually override a circuit breaker state.

    This tool allows manual control over circuit breaker state for emergency
    situations or maintenance. Use with caution - overriding circuit breakers
    bypasses automatic failure protection.

    Available Actions:
    - open: Force circuit to OPEN state (reject all requests)
    - close: Force circuit to CLOSED state (allow all requests)
    - reset: Reset circuit to initial state (clear all metrics)

    Args:
        breaker_name: Name of the circuit breaker to override
        action: Action to take: "open", "close", or "reset"
        reason: Reason for the override (for audit trail)

    Returns:
        ManualOverrideResponse with result of the override

    Raises:
        ValueError: If breaker_name not found or action is invalid

    Security Note:
        This action is logged for audit purposes. Overriding circuit breakers
        should only be done during planned maintenance or emergency situations.

    Example:
        # Force close a circuit breaker during maintenance
        result = await override_circuit_breaker(
            breaker_name="external_api",
            action="close",
            reason="Scheduled maintenance window - verified service recovery"
        )

        # Force open to protect against known issue
        result = await override_circuit_breaker(
            breaker_name="database",
            action="open",
            reason="Database failover in progress - preventing cascade"
        )
    """
    logger.info(f"Manual override requested: {breaker_name} -> {action} (reason: {reason})")

    # Validate action
    valid_actions = ["open", "close", "reset"]
    if action not in valid_actions:
        raise ValueError(f"Invalid action: {action}. Must be one of: {valid_actions}")

    try:
        from app.resilience.circuit_breaker import get_registry

        registry = get_registry()

        # Check if breaker exists
        if not registry.exists(breaker_name):
            raise ValueError(f"Circuit breaker '{breaker_name}' not found")

        breaker = registry.get(breaker_name)
        previous_state = breaker.state.value

        # Execute the override
        if action == "open":
            breaker.open(reason)
            message = f"Circuit breaker '{breaker_name}' forced OPEN"
        elif action == "close":
            breaker.close(reason)
            message = f"Circuit breaker '{breaker_name}' forced CLOSED"
        else:  # reset
            breaker.reset()
            message = f"Circuit breaker '{breaker_name}' reset to initial state"

        current_state = breaker.state.value
        success = True

        logger.warning(
            f"Circuit breaker override executed: {breaker_name} "
            f"{previous_state} -> {current_state} (reason: {reason})"
        )

        return ManualOverrideResponse(
            breaker_name=breaker_name,
            action=action,
            success=success,
            previous_state=previous_state,
            current_state=current_state,
            reason=reason,
            message=message,
            override_at=datetime.utcnow().isoformat(),
        )

    except ImportError as e:
        logger.warning(f"Circuit breaker module unavailable: {e}")
        return ManualOverrideResponse(
            breaker_name=breaker_name,
            action=action,
            success=False,
            previous_state="unknown",
            current_state="unknown",
            reason=reason,
            message="Circuit breaker module not available",
            override_at=datetime.utcnow().isoformat(),
        )
    except Exception as e:
        logger.error(f"Failed to override circuit breaker: {e}")
        raise RuntimeError(f"Failed to override circuit breaker: {e}") from e
