"""
Early Warning System MCP Integration.

Exposes burnout early warning tools as MCP tools for AI assistant interaction.
These tools apply cross-disciplinary science to detect and predict resident
burnout before it occurs.

Tools Provided:
1. detect_burnout_precursors - Seismic STA/LTA algorithm for precursor detection
2. run_spc_analysis - Western Electric Rules for workload drift monitoring
3. calculate_fire_danger_index - CFFDRS multi-temporal burnout prediction

Cross-Disciplinary Science:
- Seismology: P-wave detection adapted for behavioral precursors
- Manufacturing: Statistical Process Control (SPC) for workload monitoring
- Forestry: Fire Weather Index (FWI) for multi-temporal danger rating
"""

from __future__ import annotations

import logging
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# =============================================================================
# Seismic Detection (STA/LTA) Models
# =============================================================================


class PrecursorSignalType(str, Enum):
    """Types of burnout precursor signals to monitor."""

    SWAP_REQUESTS = "swap_requests"
    SICK_CALLS = "sick_calls"
    PREFERENCE_DECLINE = "preference_decline"
    RESPONSE_DELAYS = "response_delays"
    VOLUNTARY_COVERAGE_DECLINE = "voluntary_coverage_decline"


class SeismicAlertInfo(BaseModel):
    """
    Information about a detected seismic (precursor) alert.

    Represents a P-wave equivalent signal that precedes burnout events,
    adapted from seismological detection algorithms.
    """

    signal_type: PrecursorSignalType
    sta_lta_ratio: float = Field(
        ge=0.0, description="STA/LTA ratio at detection (>2.5 indicates anomaly)"
    )
    severity: str = Field(description="Alert severity: low, medium, high, critical")
    predicted_magnitude: float = Field(
        ge=0.0, le=10.0, description="Predicted burnout magnitude (1-10 Richter-like scale)"
    )
    time_to_event_days: float | None = Field(
        default=None, description="Estimated days until burnout event"
    )
    trigger_window_start: int = Field(description="Start index of trigger window in time series")
    trigger_window_end: int = Field(description="End index of trigger window in time series")
    growth_rate: float = Field(description="Rate of STA/LTA ratio increase")


class PrecursorDetectionRequest(BaseModel):
    """Request for burnout precursor detection."""

    resident_id: str = Field(description="UUID of resident to analyze")
    signal_type: PrecursorSignalType = Field(description="Type of precursor signal to detect")
    time_series: list[float] = Field(
        min_length=1, description="Time series data (chronological order, e.g., daily counts)"
    )
    short_window: int = Field(
        default=5, ge=2, description="STA window size (short-term average samples)"
    )
    long_window: int = Field(
        default=30, ge=5, description="LTA window size (long-term average samples)"
    )


class PrecursorDetectionResponse(BaseModel):
    """Response from burnout precursor detection."""

    resident_id: str
    signal_type: PrecursorSignalType
    alerts_detected: int
    alerts: list[SeismicAlertInfo]
    max_sta_lta_ratio: float
    analysis_summary: str
    recommended_actions: list[str]
    severity: str  # "healthy", "warning", "elevated", "critical"


class MultiSignalMagnitudeRequest(BaseModel):
    """Request for multi-signal burnout magnitude prediction."""

    resident_id: str = Field(description="UUID of resident to analyze")
    signals: dict[str, list[float]] = Field(
        description="Dict mapping signal_type to time series data"
    )
    short_window: int = Field(default=5, ge=2)
    long_window: int = Field(default=30, ge=5)


class MultiSignalMagnitudeResponse(BaseModel):
    """Response from multi-signal magnitude prediction."""

    resident_id: str
    predicted_magnitude: float = Field(ge=0.0, le=10.0)
    contributing_signals: int
    signal_magnitudes: dict[str, float]
    confidence_level: str  # "low", "medium", "high"
    interpretation: str
    recommended_actions: list[str]


# =============================================================================
# SPC Monitoring (Western Electric) Models
# =============================================================================


class SPCAlertInfo(BaseModel):
    """
    Information about an SPC (Statistical Process Control) alert.

    Represents a Western Electric Rule violation indicating workload
    drift or anomalous behavior patterns.
    """

    rule: str = Field(description="Western Electric rule violated (Rule 1-4)")
    severity: str = Field(description="Alert severity: INFO, WARNING, CRITICAL")
    message: str = Field(description="Human-readable description of violation")
    data_points: list[float] = Field(description="Data points that triggered the alert")
    control_limits: dict[str, float] = Field(
        description="Control chart limits at time of violation"
    )


class SPCAnalysisRequest(BaseModel):
    """Request for SPC workload analysis."""

    resident_id: str = Field(description="UUID of resident to analyze")
    weekly_hours: list[float] = Field(
        min_length=1, description="Weekly work hours in chronological order"
    )
    target_hours: float = Field(default=60.0, ge=0.0, description="Target weekly hours (centerline)")
    sigma: float = Field(default=5.0, gt=0.0, description="Process standard deviation (hours)")


class SPCAnalysisResponse(BaseModel):
    """Response from SPC workload analysis."""

    resident_id: str
    violations_detected: int
    alerts: list[SPCAlertInfo]
    control_limits: dict[str, float]
    process_capability: dict[str, float] | None
    weeks_analyzed: int
    mean_hours: float
    std_hours: float
    analysis_summary: str
    recommended_actions: list[str]
    severity: str  # "healthy", "warning", "critical"


class ProcessCapabilityRequest(BaseModel):
    """Request for process capability calculation."""

    weekly_hours: list[float] = Field(min_length=2, description="Weekly work hours data")
    lower_spec_limit: float = Field(default=40.0, description="Lower specification limit (min hours)")
    upper_spec_limit: float = Field(default=80.0, description="Upper specification limit (ACGME max)")


class ProcessCapabilityResponse(BaseModel):
    """Response from process capability calculation."""

    cp: float = Field(description="Process Capability (potential)")
    cpk: float = Field(description="Process Capability Index (actual)")
    pp: float = Field(description="Process Performance (long-term)")
    ppk: float = Field(description="Process Performance Index (long-term actual)")
    mean: float
    sigma: float
    lsl: float
    usl: float
    interpretation: str
    recommendation: str


# =============================================================================
# Burnout Fire Index (CFFDRS) Models
# =============================================================================


class DangerClassEnum(str, Enum):
    """Burnout danger classification (matches FWI System classes)."""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"
    EXTREME = "extreme"


class ComponentScores(BaseModel):
    """
    FWI System component scores.

    Each component represents a different temporal scale:
    - FFMC: Fine Fuel Moisture Code (recent 2 weeks)
    - DMC: Duff Moisture Code (3 month accumulation)
    - DC: Drought Code (yearly satisfaction)
    - ISI: Initial Spread Index (rate of deterioration)
    - BUI: Buildup Index (combined burden)
    - FWI: Fire Weather Index (final danger score)
    """

    ffmc: float = Field(ge=0.0, le=100.0, description="Fine Fuel Moisture Code (acute stress)")
    dmc: float = Field(ge=0.0, le=100.0, description="Duff Moisture Code (medium-term burden)")
    dc: float = Field(ge=0.0, le=100.0, description="Drought Code (long-term dissatisfaction)")
    isi: float = Field(ge=0.0, description="Initial Spread Index (deterioration rate)")
    bui: float = Field(ge=0.0, description="Buildup Index (accumulated burden)")
    fwi: float = Field(ge=0.0, description="Fire Weather Index (final danger score)")


class FireDangerRequest(BaseModel):
    """Request for burnout fire danger calculation."""

    resident_id: str = Field(description="UUID of resident to assess")
    recent_hours: float = Field(ge=0.0, description="Hours worked in last 2 weeks")
    monthly_load: float = Field(ge=0.0, description="Average monthly hours over last 3 months")
    yearly_satisfaction: float = Field(
        ge=0.0, le=1.0, description="Job satisfaction over past year (0.0-1.0)"
    )
    workload_velocity: float = Field(
        default=0.0, description="Rate of workload increase (hours/week)"
    )


class FireDangerResponse(BaseModel):
    """Response from burnout fire danger calculation."""

    resident_id: str
    danger_class: DangerClassEnum
    fwi_score: float
    component_scores: ComponentScores
    is_safe: bool
    requires_intervention: bool
    recommended_restrictions: list[str]
    temporal_analysis: dict[str, str]
    severity: str  # "healthy", "warning", "elevated", "critical", "emergency"


class BatchFireDangerRequest(BaseModel):
    """Request for batch fire danger calculation."""

    residents: list[FireDangerRequest] = Field(
        description="List of resident data for batch processing"
    )


class BatchFireDangerResponse(BaseModel):
    """Response from batch fire danger calculation."""

    residents_analyzed: int
    danger_distribution: dict[str, int]
    highest_risk_residents: list[FireDangerResponse]
    program_average_fwi: float
    recommended_program_actions: list[str]
    severity: str


# =============================================================================
# Tool Functions - Seismic Detection
# =============================================================================


async def detect_burnout_precursors(
    request: PrecursorDetectionRequest,
) -> PrecursorDetectionResponse:
    """
    Detect early warning signs of burnout using seismic STA/LTA algorithm.

    This tool applies seismological precursor detection to workload patterns,
    identifying P-wave equivalents that precede burnout events. The STA/LTA
    (Short-Term Average / Long-Term Average) algorithm detects sudden changes
    in baseline behavior.

    Scientific Basis:
    - In seismology, P-waves arrive before destructive S-waves
    - STA/LTA ratio >2.5 indicates significant deviation from baseline
    - Multiple signal types increase detection confidence

    Precursor Signals Monitored:
    - swap_requests: Frequency of shift swap requests increasing
    - sick_calls: Pattern changes in unplanned absences
    - preference_decline: Declining preferred shifts
    - response_delays: Slower response times to requests
    - voluntary_coverage_decline: Refusing extra shifts

    Args:
        request: PrecursorDetectionRequest with resident_id, signal_type, and time_series

    Returns:
        PrecursorDetectionResponse with detected alerts and recommendations

    Example:
        # Detect swap request anomalies over 60 days
        result = await detect_burnout_precursors(PrecursorDetectionRequest(
            resident_id="abc-123",
            signal_type=PrecursorSignalType.SWAP_REQUESTS,
            time_series=[0, 1, 0, 1, 0, 2, 3, 5, 7, 8, ...]  # daily counts
        ))

        if result.alerts_detected > 0:
            print(f"WARNING: {result.alerts[0].severity} precursor detected")
    """
    logger.info(
        f"Detecting burnout precursors for resident {request.resident_id}, "
        f"signal_type={request.signal_type.value}"
    )

    try:
        from app.resilience.seismic_detection import (
            BurnoutEarlyWarning,
            PrecursorSignal,
        )

        # Initialize detector with specified windows
        detector = BurnoutEarlyWarning(
            short_window=request.short_window,
            long_window=request.long_window,
        )

        # Convert string to UUID for the detector
        try:
            resident_uuid = UUID(request.resident_id)
        except ValueError:
            # If not a valid UUID, create a deterministic one from the string
            import hashlib

            hash_bytes = hashlib.md5(request.resident_id.encode()).digest()
            resident_uuid = UUID(bytes=hash_bytes)

        # Map MCP signal type to backend enum
        signal_map = {
            PrecursorSignalType.SWAP_REQUESTS: PrecursorSignal.SWAP_REQUESTS,
            PrecursorSignalType.SICK_CALLS: PrecursorSignal.SICK_CALLS,
            PrecursorSignalType.PREFERENCE_DECLINE: PrecursorSignal.PREFERENCE_DECLINE,
            PrecursorSignalType.RESPONSE_DELAYS: PrecursorSignal.RESPONSE_DELAYS,
            PrecursorSignalType.VOLUNTARY_COVERAGE_DECLINE: PrecursorSignal.VOLUNTARY_COVERAGE_DECLINE,
        }
        backend_signal = signal_map[request.signal_type]

        # Detect precursors
        alerts = detector.detect_precursors(
            resident_id=resident_uuid,
            signal_type=backend_signal,
            time_series=request.time_series,
        )

        # Convert alerts to response format
        alert_infos = []
        max_ratio = 0.0
        for alert in alerts:
            max_ratio = max(max_ratio, alert.sta_lta_ratio)
            time_to_event_days = None
            if alert.time_to_event:
                time_to_event_days = alert.time_to_event.total_seconds() / 86400

            alert_infos.append(
                SeismicAlertInfo(
                    signal_type=request.signal_type,
                    sta_lta_ratio=alert.sta_lta_ratio,
                    severity=alert.severity,
                    predicted_magnitude=alert.predicted_magnitude,
                    time_to_event_days=time_to_event_days,
                    trigger_window_start=alert.context.get("trigger_start_idx", 0),
                    trigger_window_end=alert.context.get("trigger_end_idx", 0),
                    growth_rate=alert.context.get("growth_rate", 0.0),
                )
            )

        # Determine overall severity
        if any(a.severity == "critical" for a in alert_infos):
            severity = "critical"
        elif any(a.severity == "high" for a in alert_infos):
            severity = "elevated"
        elif any(a.severity == "medium" for a in alert_infos):
            severity = "warning"
        elif alert_infos:
            severity = "warning"
        else:
            severity = "healthy"

        # Generate recommendations
        recommendations = []
        if severity == "critical":
            recommendations = [
                "URGENT: Schedule immediate wellness check-in",
                "Review recent workload and reduce if possible",
                "Consider temporary assignment changes",
                "Notify program director of burnout risk",
            ]
        elif severity == "elevated":
            recommendations = [
                "Schedule wellness check-in within 48 hours",
                "Monitor additional precursor signals",
                "Review upcoming schedule for opportunities to reduce load",
            ]
        elif severity == "warning":
            recommendations = [
                "Continue monitoring this signal",
                "Consider proactive wellness outreach",
            ]
        else:
            recommendations = [
                "No intervention needed",
                "Continue routine monitoring",
            ]

        # Generate summary
        if alert_infos:
            summary = (
                f"Detected {len(alert_infos)} precursor alert(s) for {request.signal_type.value}. "
                f"Maximum STA/LTA ratio: {max_ratio:.2f}. "
                f"Highest severity: {severity}."
            )
        else:
            summary = (
                f"No precursor signals detected for {request.signal_type.value}. "
                f"Resident is within normal behavioral baseline."
            )

        return PrecursorDetectionResponse(
            resident_id=request.resident_id,
            signal_type=request.signal_type,
            alerts_detected=len(alert_infos),
            alerts=alert_infos,
            max_sta_lta_ratio=max_ratio,
            analysis_summary=summary,
            recommended_actions=recommendations,
            severity=severity,
        )

    except ImportError as e:
        logger.error(f"Seismic detection module unavailable: {e}")
        # Return fallback response
        return PrecursorDetectionResponse(
            resident_id=request.resident_id,
            signal_type=request.signal_type,
            alerts_detected=0,
            alerts=[],
            max_sta_lta_ratio=0.0,
            analysis_summary="Seismic detection module unavailable - using fallback",
            recommended_actions=["Backend service unavailable - retry later"],
            severity="warning",
        )

    except Exception as e:
        logger.error(f"Precursor detection failed: {e}")
        raise RuntimeError(f"Failed to detect burnout precursors: {e}") from e


async def predict_burnout_magnitude(
    request: MultiSignalMagnitudeRequest,
) -> MultiSignalMagnitudeResponse:
    """
    Predict burnout magnitude from multiple precursor signals.

    Combines evidence from multiple signal types to estimate the severity
    of a potential burnout event on a 1-10 scale (similar to Richter scale
    for earthquakes).

    Scientific Basis:
    - Multiple independent signals increase prediction confidence
    - Weighted averaging emphasizes strongest indicators
    - Multi-signal confirmation bonus reflects seismic network validation

    Args:
        request: MultiSignalMagnitudeRequest with signals dictionary

    Returns:
        MultiSignalMagnitudeResponse with predicted magnitude

    Example:
        result = await predict_burnout_magnitude(MultiSignalMagnitudeRequest(
            resident_id="abc-123",
            signals={
                "swap_requests": [0, 1, 2, 5, 8, ...],
                "sick_calls": [0, 0, 1, 2, 3, ...],
                "response_delays": [1, 2, 3, 8, 12, ...]
            }
        ))

        if result.predicted_magnitude >= 7.0:
            print("CRITICAL: High burnout magnitude predicted")
    """
    logger.info(
        f"Predicting burnout magnitude for resident {request.resident_id} "
        f"with {len(request.signals)} signals"
    )

    try:
        from app.resilience.seismic_detection import (
            BurnoutEarlyWarning,
            PrecursorSignal,
        )

        detector = BurnoutEarlyWarning(
            short_window=request.short_window,
            long_window=request.long_window,
        )

        # Map signal names to PrecursorSignal enum
        signal_map = {
            "swap_requests": PrecursorSignal.SWAP_REQUESTS,
            "sick_calls": PrecursorSignal.SICK_CALLS,
            "preference_decline": PrecursorSignal.PREFERENCE_DECLINE,
            "response_delays": PrecursorSignal.RESPONSE_DELAYS,
            "voluntary_coverage_decline": PrecursorSignal.VOLUNTARY_COVERAGE_DECLINE,
        }

        # Convert to format expected by detector
        precursor_signals = {}
        for signal_name, time_series in request.signals.items():
            if signal_name in signal_map:
                precursor_signals[signal_map[signal_name]] = time_series

        # Get predicted magnitude
        magnitude = detector.predict_burnout_magnitude(precursor_signals)

        # Calculate individual signal magnitudes for transparency
        signal_magnitudes = {}
        for signal_name, time_series in request.signals.items():
            if signal_name in signal_map and len(time_series) >= request.long_window:
                single_signal = {signal_map[signal_name]: time_series}
                signal_magnitudes[signal_name] = detector.predict_burnout_magnitude(single_signal)

        # Determine confidence based on signal count
        contributing = len(signal_magnitudes)
        if contributing >= 4:
            confidence = "high"
        elif contributing >= 2:
            confidence = "medium"
        else:
            confidence = "low"

        # Generate interpretation
        if magnitude >= 8.0:
            interpretation = (
                "EXTREME: Imminent burnout risk. Multiple signals confirm "
                "severe behavioral deviation from baseline."
            )
            recommendations = [
                "EMERGENCY: Immediate intervention required",
                "Schedule mandatory wellness evaluation",
                "Reduce workload to minimum safe level",
                "Consider temporary leave",
            ]
        elif magnitude >= 6.0:
            interpretation = (
                "HIGH: Significant burnout risk detected. Behavioral patterns "
                "indicate sustained stress accumulation."
            )
            recommendations = [
                "Schedule urgent wellness check-in",
                "Review and reduce non-essential workload",
                "Monitor daily for further deterioration",
            ]
        elif magnitude >= 4.0:
            interpretation = (
                "MODERATE: Elevated burnout risk. Some behavioral changes detected "
                "that warrant attention."
            )
            recommendations = [
                "Schedule wellness check-in within 1 week",
                "Review upcoming schedule for high-stress periods",
                "Continue monitoring all signals",
            ]
        elif magnitude >= 2.0:
            interpretation = (
                "LOW: Minor behavioral changes detected. Within normal variation "
                "but worth monitoring."
            )
            recommendations = [
                "Continue routine monitoring",
                "Consider proactive wellness outreach",
            ]
        else:
            interpretation = (
                "MINIMAL: No significant burnout risk detected. Behavioral patterns "
                "are within normal baseline."
            )
            recommendations = ["Continue routine monitoring"]

        return MultiSignalMagnitudeResponse(
            resident_id=request.resident_id,
            predicted_magnitude=magnitude,
            contributing_signals=contributing,
            signal_magnitudes=signal_magnitudes,
            confidence_level=confidence,
            interpretation=interpretation,
            recommended_actions=recommendations,
        )

    except ImportError as e:
        logger.error(f"Seismic detection module unavailable: {e}")
        return MultiSignalMagnitudeResponse(
            resident_id=request.resident_id,
            predicted_magnitude=0.0,
            contributing_signals=0,
            signal_magnitudes={},
            confidence_level="low",
            interpretation="Module unavailable - using fallback",
            recommended_actions=["Backend service unavailable - retry later"],
        )

    except Exception as e:
        logger.error(f"Magnitude prediction failed: {e}")
        raise RuntimeError(f"Failed to predict burnout magnitude: {e}") from e


# =============================================================================
# Tool Functions - SPC Monitoring
# =============================================================================


async def run_spc_analysis(
    request: SPCAnalysisRequest,
) -> SPCAnalysisResponse:
    """
    Run Statistical Process Control analysis using Western Electric Rules.

    This tool applies manufacturing quality control methodology to workload
    monitoring. It detects when workload patterns deviate from expected norms,
    enabling early intervention before ACGME violations or burnout.

    Western Electric Rules Implemented:
    - Rule 1: 1 point beyond 3-sigma (CRITICAL - process out of control)
    - Rule 2: 2 of 3 consecutive points beyond 2-sigma (WARNING - shift detected)
    - Rule 3: 4 of 5 consecutive points beyond 1-sigma (WARNING - trend detected)
    - Rule 4: 8 consecutive points on same side of centerline (INFO - sustained shift)

    Scientific Basis:
    - Control charts assume normal distribution around target
    - 3-sigma limits contain 99.7% of normal variation
    - Violations indicate special cause variation requiring investigation

    Args:
        request: SPCAnalysisRequest with weekly hours data

    Returns:
        SPCAnalysisResponse with violations and control chart data

    Example:
        result = await run_spc_analysis(SPCAnalysisRequest(
            resident_id="abc-123",
            weekly_hours=[58, 62, 59, 67, 71, 75, 78, 80],
            target_hours=60.0,
            sigma=5.0
        ))

        if result.violations_detected > 0:
            for alert in result.alerts:
                print(f"{alert.rule}: {alert.message}")
    """
    logger.info(
        f"Running SPC analysis for resident {request.resident_id} "
        f"({len(request.weekly_hours)} weeks)"
    )

    try:
        from app.resilience.spc_monitoring import (
            WorkloadControlChart,
            calculate_control_limits,
            calculate_process_capability,
        )

        # Initialize control chart
        chart = WorkloadControlChart(
            target_hours=request.target_hours,
            sigma=request.sigma,
        )

        # Convert resident_id to UUID
        try:
            resident_uuid = UUID(request.resident_id)
        except ValueError:
            import hashlib

            hash_bytes = hashlib.md5(request.resident_id.encode()).digest()
            resident_uuid = UUID(bytes=hash_bytes)

        # Detect violations
        alerts = chart.detect_western_electric_violations(
            resident_id=resident_uuid,
            weekly_hours=request.weekly_hours,
        )

        # Convert to response format
        alert_infos = []
        for alert in alerts:
            alert_infos.append(
                SPCAlertInfo(
                    rule=alert.rule,
                    severity=alert.severity,
                    message=alert.message,
                    data_points=alert.data_points,
                    control_limits=alert.control_limits,
                )
            )

        # Calculate statistics
        import statistics

        mean_hours = statistics.mean(request.weekly_hours)
        std_hours = (
            statistics.stdev(request.weekly_hours)
            if len(request.weekly_hours) >= 2
            else 0.0
        )

        # Calculate control limits
        control_limits = {
            "ucl_3sigma": request.target_hours + 3 * request.sigma,
            "lcl_3sigma": request.target_hours - 3 * request.sigma,
            "ucl_2sigma": request.target_hours + 2 * request.sigma,
            "lcl_2sigma": request.target_hours - 2 * request.sigma,
            "ucl_1sigma": request.target_hours + 1 * request.sigma,
            "lcl_1sigma": request.target_hours - 1 * request.sigma,
            "centerline": request.target_hours,
        }

        # Calculate process capability if enough data
        capability = None
        if len(request.weekly_hours) >= 2:
            try:
                cap_result = calculate_process_capability(
                    data=request.weekly_hours,
                    lsl=40.0,  # Minimum reasonable hours
                    usl=80.0,  # ACGME maximum
                )
                capability = {
                    "cp": cap_result["cp"],
                    "cpk": cap_result["cpk"],
                    "interpretation": cap_result["interpretation"],
                }
            except Exception:
                pass

        # Determine severity
        if any(a.severity == "CRITICAL" for a in alert_infos):
            severity = "critical"
        elif any(a.severity == "WARNING" for a in alert_infos):
            severity = "warning"
        else:
            severity = "healthy"

        # Generate recommendations
        recommendations = []
        if severity == "critical":
            recommendations = [
                "URGENT: Process out of control - immediate investigation required",
                "Review recent schedule assignments for errors",
                "Check for data entry issues",
                "Consider immediate workload adjustment",
            ]
        elif severity == "warning":
            recommendations = [
                "Investigate cause of workload shift or trend",
                "Review rotation assignments for next block",
                "Monitor for continued drift",
            ]
        else:
            recommendations = [
                "Process in control - continue normal monitoring",
                "Workload variation within expected limits",
            ]

        # Generate summary
        if alert_infos:
            rules_violated = set(a.rule for a in alert_infos)
            summary = (
                f"Detected {len(alert_infos)} Western Electric Rule violation(s): "
                f"{', '.join(rules_violated)}. Mean workload: {mean_hours:.1f}h "
                f"(target: {request.target_hours:.1f}h)."
            )
        else:
            summary = (
                f"No Western Electric Rule violations detected. "
                f"Mean workload: {mean_hours:.1f}h (target: {request.target_hours:.1f}h). "
                f"Process is in statistical control."
            )

        return SPCAnalysisResponse(
            resident_id=request.resident_id,
            violations_detected=len(alert_infos),
            alerts=alert_infos,
            control_limits=control_limits,
            process_capability=capability,
            weeks_analyzed=len(request.weekly_hours),
            mean_hours=mean_hours,
            std_hours=std_hours,
            analysis_summary=summary,
            recommended_actions=recommendations,
            severity=severity,
        )

    except ImportError as e:
        logger.error(f"SPC monitoring module unavailable: {e}")
        import statistics

        mean_hours = statistics.mean(request.weekly_hours)
        return SPCAnalysisResponse(
            resident_id=request.resident_id,
            violations_detected=0,
            alerts=[],
            control_limits={},
            process_capability=None,
            weeks_analyzed=len(request.weekly_hours),
            mean_hours=mean_hours,
            std_hours=0.0,
            analysis_summary="SPC module unavailable - using fallback",
            recommended_actions=["Backend service unavailable - retry later"],
            severity="warning",
        )

    except Exception as e:
        logger.error(f"SPC analysis failed: {e}")
        raise RuntimeError(f"Failed to run SPC analysis: {e}") from e


async def calculate_process_capability_tool(
    request: ProcessCapabilityRequest,
) -> ProcessCapabilityResponse:
    """
    Calculate process capability indices (Cp/Cpk) for workload distribution.

    Process capability measures how well workload distribution fits within
    acceptable bounds (ACGME limits). This is a Six Sigma quality metric
    adapted for medical scheduling.

    Indices Explained:
    - Cp: Process Capability (potential if perfectly centered)
    - Cpk: Process Capability Index (actual, accounts for centering)
    - Pp/Ppk: Long-term performance equivalents

    Interpretation:
    - Cpk < 1.0: Process not capable (expect violations)
    - Cpk = 1.0: Barely capable (2700 ppm defects)
    - Cpk = 1.33: Capable (63 ppm, 4-sigma quality)
    - Cpk = 1.67: Highly capable (0.6 ppm, 5-sigma)
    - Cpk = 2.0: World-class (6-sigma quality)

    Args:
        request: ProcessCapabilityRequest with hours data and spec limits

    Returns:
        ProcessCapabilityResponse with Cp/Cpk indices

    Example:
        result = await calculate_process_capability_tool(ProcessCapabilityRequest(
            weekly_hours=[58, 62, 59, 61, 63, 60, 58, 62],
            lower_spec_limit=40.0,
            upper_spec_limit=80.0
        ))

        print(f"Cpk: {result.cpk:.2f} - {result.interpretation}")
    """
    logger.info(
        f"Calculating process capability for {len(request.weekly_hours)} weeks "
        f"(LSL={request.lower_spec_limit}, USL={request.upper_spec_limit})"
    )

    try:
        from app.resilience.spc_monitoring import calculate_process_capability

        result = calculate_process_capability(
            data=request.weekly_hours,
            lsl=request.lower_spec_limit,
            usl=request.upper_spec_limit,
        )

        # Generate recommendation based on Cpk
        cpk = result["cpk"]
        if cpk < 0:
            recommendation = "CRITICAL: Mean outside specification limits. Immediate workload rebalancing required."
        elif cpk < 1.0:
            recommendation = "Process not capable. High probability of ACGME violations. Reduce workload variability."
        elif cpk < 1.33:
            recommendation = "Marginally capable. Improvement recommended to reduce violation risk."
        elif cpk < 1.67:
            recommendation = "Process capable. Meets 4-sigma quality. Continue current practices."
        else:
            recommendation = "Highly capable. Excellent workload distribution. Maintain current practices."

        return ProcessCapabilityResponse(
            cp=result["cp"],
            cpk=result["cpk"],
            pp=result["pp"],
            ppk=result["ppk"],
            mean=result["mean"],
            sigma=result["sigma"],
            lsl=result["lsl"],
            usl=result["usl"],
            interpretation=result["interpretation"],
            recommendation=recommendation,
        )

    except ImportError as e:
        logger.error(f"SPC module unavailable: {e}")
        import statistics

        mean = statistics.mean(request.weekly_hours)
        sigma = statistics.stdev(request.weekly_hours) if len(request.weekly_hours) >= 2 else 0.0
        return ProcessCapabilityResponse(
            cp=0.0,
            cpk=0.0,
            pp=0.0,
            ppk=0.0,
            mean=mean,
            sigma=sigma,
            lsl=request.lower_spec_limit,
            usl=request.upper_spec_limit,
            interpretation="Module unavailable - using fallback",
            recommendation="Backend service unavailable - retry later",
        )

    except Exception as e:
        logger.error(f"Process capability calculation failed: {e}")
        raise RuntimeError(f"Failed to calculate process capability: {e}") from e


# =============================================================================
# Tool Functions - Burnout Fire Index
# =============================================================================


async def calculate_fire_danger_index(
    request: FireDangerRequest,
) -> FireDangerResponse:
    """
    Calculate multi-temporal burnout danger using Fire Weather Index system.

    This tool adapts the Canadian Forest Fire Danger Rating System (CFFDRS)
    Fire Weather Index (FWI) for burnout prediction. Like wildfires, burnout
    develops across multiple time scales that must align for catastrophe.

    FWI System Components:
    - FFMC (Fine Fuel): Recent 2-week workload (immediate risk)
    - DMC (Duff Moisture): 3-month accumulation (medium-term burden)
    - DC (Drought): Yearly satisfaction erosion (long-term risk)
    - ISI (Spread Index): Rate of deterioration (acceleration)
    - BUI (Buildup): Combined medium + long-term burden
    - FWI (Final Index): Composite danger score

    Danger Classes:
    - LOW (<20): Normal operations
    - MODERATE (20-40): Monitor closely
    - HIGH (40-60): Reduce workload
    - VERY_HIGH (60-80): Significant restrictions
    - EXTREME (80+): Emergency measures

    Scientific Basis:
    - FWI System validated over 50+ years across Canada
    - Multi-temporal analysis captures different burnout mechanisms
    - Non-linear interactions model compound effects

    Args:
        request: FireDangerRequest with temporal workload metrics

    Returns:
        FireDangerResponse with FWI score and restrictions

    Example:
        result = await calculate_fire_danger_index(FireDangerRequest(
            resident_id="abc-123",
            recent_hours=75.0,       # High recent workload
            monthly_load=260.0,      # Sustained overwork
            yearly_satisfaction=0.4, # Low satisfaction
            workload_velocity=8.0    # Increasing workload
        ))

        if result.danger_class == DangerClassEnum.EXTREME:
            print("EMERGENCY: Immediate intervention required")
            for restriction in result.recommended_restrictions:
                print(f"  - {restriction}")
    """
    logger.info(
        f"Calculating fire danger index for resident {request.resident_id} "
        f"(recent={request.recent_hours}h, monthly={request.monthly_load}h, "
        f"satisfaction={request.yearly_satisfaction})"
    )

    try:
        from app.resilience.burnout_fire_index import BurnoutDangerRating, DangerClass

        # Initialize rating system
        rating = BurnoutDangerRating()

        # Convert resident_id to UUID
        try:
            resident_uuid = UUID(request.resident_id)
        except ValueError:
            import hashlib

            hash_bytes = hashlib.md5(request.resident_id.encode()).digest()
            resident_uuid = UUID(bytes=hash_bytes)

        # Calculate danger
        report = rating.calculate_burnout_danger(
            resident_id=resident_uuid,
            recent_hours=request.recent_hours,
            monthly_load=request.monthly_load,
            yearly_satisfaction=request.yearly_satisfaction,
            workload_velocity=request.workload_velocity,
        )

        # Map danger class
        danger_class_map = {
            DangerClass.LOW: DangerClassEnum.LOW,
            DangerClass.MODERATE: DangerClassEnum.MODERATE,
            DangerClass.HIGH: DangerClassEnum.HIGH,
            DangerClass.VERY_HIGH: DangerClassEnum.VERY_HIGH,
            DangerClass.EXTREME: DangerClassEnum.EXTREME,
        }

        # Build component scores
        scores = report.component_scores
        component_scores = ComponentScores(
            ffmc=scores.get("ffmc", 0.0),
            dmc=scores.get("dmc", 0.0),
            dc=scores.get("dc", 0.0),
            isi=scores.get("isi", 0.0),
            bui=scores.get("bui", 0.0),
            fwi=scores.get("fwi", 0.0),
        )

        # Generate temporal analysis
        temporal_analysis = {
            "immediate_risk": _interpret_ffmc(scores.get("ffmc", 0.0)),
            "medium_term_burden": _interpret_dmc(scores.get("dmc", 0.0)),
            "long_term_erosion": _interpret_dc(scores.get("dc", 0.0)),
            "deterioration_rate": _interpret_isi(scores.get("isi", 0.0)),
            "accumulated_burden": _interpret_bui(scores.get("bui", 0.0)),
        }

        # Determine severity
        severity_map = {
            DangerClassEnum.LOW: "healthy",
            DangerClassEnum.MODERATE: "warning",
            DangerClassEnum.HIGH: "elevated",
            DangerClassEnum.VERY_HIGH: "critical",
            DangerClassEnum.EXTREME: "emergency",
        }

        mapped_class = danger_class_map[report.danger_class]

        return FireDangerResponse(
            resident_id=request.resident_id,
            danger_class=mapped_class,
            fwi_score=report.fwi_score,
            component_scores=component_scores,
            is_safe=report.is_safe,
            requires_intervention=report.requires_intervention,
            recommended_restrictions=report.recommended_restrictions,
            temporal_analysis=temporal_analysis,
            severity=severity_map.get(mapped_class, "warning"),
        )

    except ImportError as e:
        logger.error(f"Burnout fire index module unavailable: {e}")
        return FireDangerResponse(
            resident_id=request.resident_id,
            danger_class=DangerClassEnum.MODERATE,
            fwi_score=0.0,
            component_scores=ComponentScores(
                ffmc=0.0, dmc=0.0, dc=0.0, isi=0.0, bui=0.0, fwi=0.0
            ),
            is_safe=True,
            requires_intervention=False,
            recommended_restrictions=["Module unavailable - using fallback"],
            temporal_analysis={},
            severity="warning",
        )

    except Exception as e:
        logger.error(f"Fire danger calculation failed: {e}")
        raise RuntimeError(f"Failed to calculate fire danger index: {e}") from e


async def calculate_batch_fire_danger(
    request: BatchFireDangerRequest,
) -> BatchFireDangerResponse:
    """
    Calculate fire danger index for multiple residents.

    Useful for program-wide burnout screening and identifying highest-risk
    residents for intervention.

    Args:
        request: BatchFireDangerRequest with list of resident data

    Returns:
        BatchFireDangerResponse with program-wide statistics

    Example:
        result = await calculate_batch_fire_danger(BatchFireDangerRequest(
            residents=[
                FireDangerRequest(resident_id="res-1", recent_hours=70, ...),
                FireDangerRequest(resident_id="res-2", recent_hours=65, ...),
                ...
            ]
        ))

        print(f"Program average FWI: {result.program_average_fwi:.1f}")
        print(f"High risk: {result.danger_distribution.get('extreme', 0)} residents")
    """
    logger.info(f"Calculating batch fire danger for {len(request.residents)} residents")

    results = []
    for resident_request in request.residents:
        try:
            result = await calculate_fire_danger_index(resident_request)
            results.append(result)
        except Exception as e:
            logger.warning(f"Failed to calculate for {resident_request.resident_id}: {e}")

    # Calculate distribution
    distribution = {
        "low": 0,
        "moderate": 0,
        "high": 0,
        "very_high": 0,
        "extreme": 0,
    }
    for r in results:
        distribution[r.danger_class.value] += 1

    # Get highest risk (top 5 by FWI)
    sorted_results = sorted(results, key=lambda x: x.fwi_score, reverse=True)
    highest_risk = sorted_results[:5]

    # Calculate program average
    avg_fwi = sum(r.fwi_score for r in results) / len(results) if results else 0.0

    # Generate program recommendations
    program_actions = []
    extreme_count = distribution.get("extreme", 0)
    very_high_count = distribution.get("very_high", 0)
    high_count = distribution.get("high", 0)

    if extreme_count > 0:
        program_actions.append(
            f"EMERGENCY: {extreme_count} resident(s) at EXTREME danger - immediate intervention required"
        )
    if very_high_count > 0:
        program_actions.append(
            f"URGENT: {very_high_count} resident(s) at VERY_HIGH danger - schedule wellness evaluations"
        )
    if high_count > 0:
        program_actions.append(
            f"ATTENTION: {high_count} resident(s) at HIGH danger - review workloads"
        )
    if avg_fwi >= 40:
        program_actions.append("Program-wide workload review recommended")
    if len(results) > 0 and (extreme_count + very_high_count) / len(results) > 0.2:
        program_actions.append("Consider program-level wellness initiative")

    if not program_actions:
        program_actions = ["Program burnout risk within acceptable limits"]

    # Determine severity
    if extreme_count > 0:
        severity = "emergency"
    elif very_high_count > 0:
        severity = "critical"
    elif high_count > 0:
        severity = "elevated"
    elif distribution.get("moderate", 0) > 0:
        severity = "warning"
    else:
        severity = "healthy"

    return BatchFireDangerResponse(
        residents_analyzed=len(results),
        danger_distribution=distribution,
        highest_risk_residents=highest_risk,
        program_average_fwi=avg_fwi,
        recommended_program_actions=program_actions,
        severity=severity,
    )


# =============================================================================
# Helper Functions
# =============================================================================


def _interpret_ffmc(ffmc: float) -> str:
    """Interpret FFMC score for temporal analysis."""
    if ffmc >= 85:
        return "Critical - extreme recent overwork"
    elif ffmc >= 60:
        return "High - elevated recent workload"
    elif ffmc >= 30:
        return "Moderate - some recent stress"
    else:
        return "Low - recent workload sustainable"


def _interpret_dmc(dmc: float) -> str:
    """Interpret DMC score for temporal analysis."""
    if dmc >= 70:
        return "Severe - sustained overwork accumulation"
    elif dmc >= 40:
        return "High - medium-term burden building"
    elif dmc >= 20:
        return "Moderate - some accumulated burden"
    else:
        return "Low - sustainable long-term workload"


def _interpret_dc(dc: float) -> str:
    """Interpret DC score for temporal analysis."""
    if dc >= 60:
        return "Severe - chronic dissatisfaction"
    elif dc >= 30:
        return "Moderate - declining satisfaction"
    elif dc >= 10:
        return "Low - minor satisfaction concerns"
    else:
        return "Minimal - high job satisfaction"


def _interpret_isi(isi: float) -> str:
    """Interpret ISI score for temporal analysis."""
    if isi >= 60:
        return "Extreme - rapid deterioration"
    elif isi >= 30:
        return "High - accelerating burnout risk"
    elif isi >= 10:
        return "Moderate - some acceleration"
    else:
        return "Low - stable trajectory"


def _interpret_bui(bui: float) -> str:
    """Interpret BUI score for temporal analysis."""
    if bui >= 70:
        return "Extreme - heavy accumulated burden"
    elif bui >= 40:
        return "High - significant burden"
    elif bui >= 20:
        return "Moderate - some burden"
    else:
        return "Low - manageable burden"
