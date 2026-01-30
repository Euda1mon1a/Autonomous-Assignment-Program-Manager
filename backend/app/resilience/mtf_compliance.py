"""
MTF Compliance: "The Iron Dome" - Automated Bureaucratic Defense.

In a Military Treatment Facility, you can't solve problems with money or hiring.
You solve them with Rank, Regulations, and Paper Trails.

This module "weaponizes compliance" to protect schedulers from the inevitable
fallout of staffing crises. It turns the scheduler into an automated JAG
(Judge Advocate General) / Inspector General officer.

Overview
--------
The Iron Dome addresses a fundamental asymmetry in military healthcare: the
scheduling system can detect catastrophic risks (N-1 failures, burnout cascades,
ACGME violations), but lacks institutional authority to force action. This module
provides that authority through automated compliance documentation that creates
legal/regulatory pressure.

When the system detects dangerous conditions, it doesn't just log a warning—it
generates formal military documentation that forces command accountability.

Key Components
--------------

1. **DRRS Translation Layer** (DRRSTranslator)
   - Converts internal scheduling metrics to Defense Readiness Reporting System format
   - Translates LoadSheddingLevel → DRRS C-ratings (C1-C5)
   - Maps EquilibriumState → Mission Capability Status (FMC/PMC/NMC)
   - Calculates Personnel (P) and Equipment/Capability (S) readiness ratings
   - Generates SITREP-style executive summaries for command briefings

   Use case: Transform "residents are stressed" into "Unit rated C4, Not Mission
   Capable due to P4 personnel readiness—requires immediate command intervention"

2. **MFR Generator** (MFRGenerator)
   - Creates immutable Memoranda for Record with cryptographic hashing
   - Documents risk acceptance when schedules published under dangerous conditions
   - Auto-generates 5 MFR types: Risk Acceptance, Safety Concern, Compliance
     Violation, Resource Request, Stand-Down
   - Includes system state snapshots, findings, risk assessments, recommendations
   - Routes to appropriate distribution lists (DIO, Risk Management, Commander, etc.)

   Use case: When Commander orders "make it work" with insufficient staff, system
   generates timestamped MFR documenting that risk assessment predicted 98%
   probability of ACGME violation—shifting liability back to command

3. **Circuit Breaker** (CircuitBreaker)
   - Implements safety stand-down protocol based on system health thresholds
   - Three states: CLOSED (normal), HALF_OPEN (limited ops), OPEN (locked)
   - Automatically trips on: N-1 failure, coverage collapse (<70%), allostatic
     overload (>80), critical volatility, positive feedback cascades
   - Locks operations: new assignments, schedule changes, leave approval
   - Always permits: emergency coverage, patient safety assignments, viewing
   - Supports command override with time limits and mandatory MFR documentation

   Use case: System detects single point of failure and automatically prevents
   any schedule modifications, returning HTTP 451 "Unavailable For Legal Reasons"
   until conditions improve or commander provides documented override

4. **RFF Drafter** (RFFDrafter)
   - Generates Request for Forces documents using military SMEAC format
     (Situation, Mission, Execution, Administration, Command)
   - Uses cascade predictions to mathematically prove resource needs
   - Maps medical specialties to Military Occupational Specialty (MOS) codes
   - Projects mission failure timeline without support
   - Compiles supporting metrics from resilience framework

   Use case: System calculates 14 days until "extinction vortex" and auto-drafts
   RFF requesting 2 Reserve Component physicians (MOS 60H) with full justification
   that speaks bureaucratic language to unlock resources

Integration Points
------------------

This module integrates with other resilience components:

- **resilience.mtf_types**: Imports SystemHealthState, CascadePrediction,
  PositiveFeedbackRisk for system state tracking

- **resilience.sacrifice**: LoadSheddingLevel provides graduated defense-in-depth
  response that DRRS Translator maps to military C-ratings

- **resilience.allostasis**: Allostatic load metrics feed into personnel readiness
  (P-rating) calculations and circuit breaker thresholds

- **resilience.contingency**: N-1/N-2 analysis results determine capability ratings
  (S-rating) and circuit breaker triggers

- **resilience.lechatelier**: Cascade predictions power RFF timeline projections
  and risk assessment severity

The IronDomeService class provides a unified interface combining all four
components into a single "regulatory bodyguard" service.

Usage Example
-------------

Basic readiness assessment::

    from app.resilience.mtf_compliance import IronDomeService
    from app.schemas.resilience import LoadSheddingLevel, EquilibriumState

    iron_dome = IronDomeService()

    # Generate DRRS readiness report
    assessment = iron_dome.assess_readiness(
        load_shedding_level=LoadSheddingLevel.ORANGE,
        equilibrium_state=EquilibriumState.STRESSED,
        n1_pass=False,
        n2_pass=True,
        coverage_rate=0.82,
        available_faculty=15,
        required_faculty=18,
        overloaded_faculty_count=4
    )

    print(assessment.executive_summary)
    # Output: "UNIT STATUS: YELLOW\nOverall: C3 | Personnel: P3 | Capability: S4\n..."

Circuit breaker and MFR generation::

    # Check if circuit breaker trips
    cb_check = iron_dome.check_circuit_breaker(
        n1_pass=False,
        n2_pass=False,
        coverage_rate=0.68,
        average_allostatic_load=85,
        volatility_level="critical",
        compensation_debt=1200,
    )

    if cb_check.tripped:
        # Circuit breaker tripped - generate MFR
        mfr = iron_dome.generate_risk_mfr(
            subject="Critical Staffing Shortage - Week of 2025-12-20",
            system_state=current_system_state,
            scheduler_name="Maj Smith, Program Director",
            scheduler_objection="Recommend activating reserve pool before publishing schedule"
        )

        # MFR is now immutable record with hash, timestamp, findings
        print(f"MFR {mfr.id} generated at {mfr.generated_at}")
        print(f"Risk Level: {mfr.risk_level.value}")
        print(f"Distribution: {', '.join(mfr.distribution_list)}")

Request for Forces drafting::

    # Auto-generate RFF when system predicts failure
    rff = iron_dome.draft_resource_request(
        requesting_unit="Department of Family Medicine",
        mission_affected=[MissionType.PRIMARY_CARE, MissionType.GME],
        mos_required=["60H", "66H"],  # Attending physician, Nurse Practitioner
        personnel_count=3,
        duration_days=90,
        justification="Prevent cascade failure and ACGME citation",
        system_state=current_system_state,
        cascade_prediction=cascade_analysis
    )

    # RFF includes full SMEAC format documentation
    print(rff.situation)  # Military situation analysis
    print(rff.projected_without_support.outcomes)  # Timeline to failure

Military Terminology
--------------------

- **DRRS**: Defense Readiness Reporting System - standardized DoD readiness reporting
- **C-rating**: Overall readiness category (C1=fully capable, C5=critical deficiency)
- **P-rating**: Personnel readiness (P1=100%+ manning, P4=<80%)
- **S-rating**: Equipment/capability readiness (S1=all systems go, S4=major gaps)
- **MFR**: Memorandum for Record - official documentation of events/decisions
- **RFF**: Request for Forces - formal request for additional military personnel
- **SITREP**: Situation Report - summary of current operational status
- **DIO**: Designated Institutional Official - ACGME compliance authority
- **MOS**: Military Occupational Specialty - job code (e.g., 60H = physician)
- **OPCON**: Operational Control - command authority over assigned forces
- **UIC**: Unit Identification Code - unique identifier for military units
- **FMC/PMC/NMC**: Fully/Partially/Not Mission Capable

The insight: The system already calculates risk. This module makes risk
visible in ways that create accountability and force action.
"""

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any, NotRequired, TypedDict
from uuid import UUID, uuid4

from app.resilience.mtf_types import (
    CascadePrediction,
    PositiveFeedbackRisk,
    ProjectionWithoutSupport,
    SupportingMetrics,
    SystemHealthState,
)
from app.schemas.mtf_compliance import (
    CircuitBreakerState,
    CircuitBreakerTrigger,
    DRRSCategory,
    EquipmentReadinessLevel,
    MFRPriority,
    MFRType,
    MissionCapabilityStatus,
    MissionType,
    OverrideAuthority,
    PersonnelReadinessLevel,
    RiskLevel,
)
from app.schemas.resilience import (
    EquilibriumState,
    LoadSheddingLevel,
)

logger = logging.getLogger(__name__)


# =============================================================================
# TypedDict Definitions for Complex State Objects
# =============================================================================


class SystemStateDict(TypedDict, total=False):
    """
    Dictionary representation of system health state.

    Used when system state is passed as a dictionary instead of
    SystemHealthState object. All fields are optional (total=False)
    to allow partial state representations.
    """

    n1_pass: bool
    n2_pass: bool
    coverage_rate: float
    average_allostatic_load: float
    load_shedding_level: str
    equilibrium_state: str
    phase_transition_risk: str
    compensation_debt: float
    volatility_level: str


class ViolationDict(TypedDict, total=False):
    """
    Dictionary representation of a single compliance violation.

    Provides type safety for violation data passed as dictionaries.
    """

    rule_id: str
    severity: str  # 'critical', 'warning', 'info'
    description: str
    affected_items: list[str]
    recommendation: str | None


class MTFComplianceResultDict(TypedDict):
    """
    Dictionary representation of MTF compliance check results.

    Provides type safety for compliance results passed as dictionaries.
    """

    is_compliant: bool
    score: float
    violations: list[ViolationDict]
    recommendations: list[str]
    checked_at: NotRequired[date | None]


class ContingencyAnalysisDict(TypedDict):
    """
    Dictionary representation of N-1/N-2 contingency analysis results.

    Tracks system resilience to faculty losses and identifies
    single/dual points of failure.
    """

    n1_pass: bool
    n2_pass: bool
    single_point_failures: NotRequired[list[str]]
    dual_point_failures: NotRequired[list[tuple[str, str]]]
    vulnerable_rotations: NotRequired[list[str]]
    risk_level: NotRequired[str]


class CapacityMetricsDict(TypedDict):
    """
    Dictionary representation of capacity and utilization metrics.

    Tracks system capacity, current utilization, and any deficits
    for resource planning and load shedding decisions.
    """

    capacity: int
    utilization: float
    deficit: NotRequired[int]
    available_slots: NotRequired[int]
    filled_slots: NotRequired[int]
    coverage_percentage: NotRequired[float]


class CascadePredictionDict(TypedDict, total=False):
    """
    Dictionary representation of cascade failure prediction.

    Used for predicting system collapse timelines.
    """

    days_until_exhaustion: int
    probability: float
    trigger_event: str


class PositiveFeedbackRiskDict(TypedDict):
    """
    Dictionary representation of positive feedback risk.

    Identifies self-reinforcing failure cycles.
    """

    confidence: float
    risk_type: NotRequired[str]
    description: NotRequired[str]

    # =============================================================================
    # Type-Safe Data Classes for MTF Compliance
    # =============================================================================


@dataclass
class MTFViolation:
    """
    A single MTF compliance violation detected by the system.

    Represents a specific failure to meet regulatory, safety, or operational
    requirements. Used to build comprehensive compliance reports.

    Attributes:
        rule_id: Unique identifier for the violated rule (e.g., "ACGME_80HR", "N1_FAIL")
        severity: Severity level - 'critical' (immediate action), 'warning' (needs attention),
                  'info' (informational only)
        description: Human-readable description of what was violated and why it matters
        affected_items: List of specific items affected (person IDs, rotation names, dates, etc.)
        recommendation: Optional suggested remediation action
    """

    rule_id: str
    severity: str  # 'critical', 'warning', 'info'
    description: str
    affected_items: list[str] = field(default_factory=list)
    recommendation: str | None = None


@dataclass
class MTFComplianceResult:
    """
    Result of a comprehensive MTF compliance check.

    Aggregates all detected violations and provides an overall compliance
    score and actionable recommendations.

    Attributes:
        is_compliant: True if no critical violations detected
        score: Compliance score from 0.0 (total failure) to 100.0 (perfect compliance)
        violations: List of all detected violations, ordered by severity
        recommendations: Prioritized list of recommended actions to achieve compliance
        checked_at: Date/time when compliance check was performed (for audit trail)
    """

    is_compliant: bool
    score: float  # 0.0 to 100.0
    violations: list[MTFViolation] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    checked_at: date | None = None


@dataclass
class CoverageAnalysis:
    """
    Analysis of schedule coverage gaps and capacity utilization.

    Identifies where and when the schedule has insufficient coverage,
    supporting load shedding and resource request decisions.

    Attributes:
        total_slots: Total number of schedule slots that need coverage
        filled_slots: Number of slots currently filled with assignments
        coverage_percentage: Percentage filled (0.0 to 100.0)
        gaps: List of specific coverage gaps, each containing date, rotation,
              shift, and required specialty information
    """

    total_slots: int
    filled_slots: int
    coverage_percentage: float
    gaps: list[dict[str, str]] = field(default_factory=list)


@dataclass
class ReadinessAssessment:
    """
    Complete DRRS readiness assessment in military reporting format.

    Translates complex scheduling system metrics into Defense Readiness
    Reporting System (DRRS) language that military commanders understand.
    This is what appears on the Commander's daily briefing slide.

    Attributes:
        overall_rating: DRRS C-rating (C1-C5), where C1 is fully mission capable
                        and C5 is critical deficiency
        overall_capability: Mission capability status - FMC (Fully Mission Capable),
                            PMC (Partially), or NMC (Not Mission Capable)
        personnel_rating: P-rating (P1-P4) indicating personnel manning levels
        personnel_percentage: Actual personnel strength as percentage of required
        capability_rating: S-rating (S1-S4) indicating equipment/capability readiness
        deficiencies: List of specific deficiencies degrading readiness
        load_shedding_level: Current sacrifice hierarchy level (NORMAL through CRITICAL)
        equilibrium_state: System equilibrium state (stable, compensating, stressed, etc.)
        executive_summary: SITREP-style narrative summary for command briefing,
                           includes color-coded status and mission impact assessment
    """

    overall_rating: str
    overall_capability: str
    personnel_rating: str
    personnel_percentage: float
    capability_rating: str
    deficiencies: list[str]
    load_shedding_level: str
    equilibrium_state: str
    executive_summary: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "overall_rating": self.overall_rating,
            "overall_capability": self.overall_capability,
            "personnel_rating": self.personnel_rating,
            "personnel_percentage": self.personnel_percentage,
            "capability_rating": self.capability_rating,
            "deficiencies": self.deficiencies,
            "load_shedding_level": self.load_shedding_level,
            "equilibrium_state": self.equilibrium_state,
            "executive_summary": self.executive_summary,
        }


@dataclass
class CircuitBreakerCheck:
    """
    Result of a circuit breaker safety check.

    Indicates whether the circuit breaker has tripped and what operations
    are currently locked/allowed. Used to enforce safety stand-down protocols.

    Attributes:
        tripped: True if circuit breaker tripped during this check
        state: Current circuit breaker state - CLOSED (normal), HALF_OPEN (limited),
               or OPEN (locked down)
        trigger: What triggered the circuit breaker (N1_VIOLATION, COVERAGE_COLLAPSE,
                 ALLOSTATIC_OVERLOAD, etc.) if tripped
        trigger_details: Human-readable explanation of why circuit breaker tripped
        locked_operations: List of operations currently prohibited (e.g., "new_assignments",
                           "schedule_changes", "leave_approval")
        allowed_operations: List of operations always permitted (emergency_coverage,
                            patient_safety_assignment, view_schedule, etc.)
        override_active: True if a command override is currently in effect,
                         allowing operations despite trip
    """

    tripped: bool
    state: str
    trigger: str | None
    trigger_details: str | None
    locked_operations: list[str]
    allowed_operations: list[str]
    override_active: bool

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "tripped": self.tripped,
            "state": self.state,
            "trigger": self.trigger,
            "trigger_details": self.trigger_details,
            "locked_operations": self.locked_operations,
            "allowed_operations": self.allowed_operations,
            "override_active": self.override_active,
        }


@dataclass
class IronDomeStatus:
    """
    Overall status of the Iron Dome compliance defense system.

    Provides a complete snapshot of the Iron Dome's defensive posture,
    including circuit breaker state and documentation generation activity.

    Attributes:
        circuit_breaker_state: Current state (CLOSED/HALF_OPEN/OPEN)
        scheduling_locked: True if scheduling operations are locked due to safety concerns
        override_active: True if command has provided documented override
        trigger: What caused the current defensive posture, if applicable
        mfrs_generated: Count of Memoranda for Record generated (liability documentation)
        rffs_generated: Count of Request for Forces documents generated (resource requests)
        locked_operations: List of currently prohibited operations
    """

    circuit_breaker_state: str
    scheduling_locked: bool
    override_active: bool
    trigger: str | None
    mfrs_generated: int
    rffs_generated: int
    locked_operations: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "circuit_breaker_state": self.circuit_breaker_state,
            "scheduling_locked": self.scheduling_locked,
            "override_active": self.override_active,
            "trigger": self.trigger,
            "mfrs_generated": self.mfrs_generated,
            "rffs_generated": self.rffs_generated,
            "locked_operations": self.locked_operations,
        }

        # =============================================================================
        # DRRS Translation Layer
        # =============================================================================


class DRRSTranslator:
    """
    Translates internal scheduling metrics to Defense Readiness Reporting System.

    The Commander doesn't care about "resident wellness" or "fairness."
    They care about Readiness and Mission Capability.

    This translator turns:
    - LoadSheddingLevel -> DRRS C-ratings
    - EquilibriumState -> Mission capability percentage
    - AllostasisMetrics -> Personnel readiness
    """

    # Map LoadSheddingLevel to DRRS Category
    # DRRS C-ratings indicate overall unit readiness to perform assigned mission:
    # C1 = Fully Mission Capable (all systems go)
    # C2 = Substantially Mission Capable (minor deficiencies, can perform mission)
    # C3 = Marginally Mission Capable (significant deficiencies, mission degraded)
    # C4 = Not Mission Capable (major deficiencies, cannot fully perform mission)
    # C5 = Not Mission Capable - Critical (only emergency operations possible)
    LOAD_SHEDDING_TO_DRRS = {
        LoadSheddingLevel.NORMAL: DRRSCategory.C1,  # All services operational
        LoadSheddingLevel.YELLOW: DRRSCategory.C2,  # Minor load shedding (elective procedures delayed)
        LoadSheddingLevel.ORANGE: DRRSCategory.C3,  # Moderate load shedding (non-essential services suspended)
        LoadSheddingLevel.RED: DRRSCategory.C4,  # Major load shedding (essential services only)
        LoadSheddingLevel.BLACK: DRRSCategory.C4,  # Severe load shedding (emergency and urgent only)
        LoadSheddingLevel.CRITICAL: DRRSCategory.C5,  # Critical - patient safety only, system near collapse
    }

    # Map EquilibriumState to Mission Capability Status
    # Mission Capability indicates whether unit can perform its assigned missions:
    # FMC = Fully Mission Capable (can perform all assigned missions)
    # PMC = Partially Mission Capable (can perform some but not all missions)
    # NMC = Not Mission Capable (cannot perform primary mission without augmentation)
    EQUILIBRIUM_TO_MISSION = {
        EquilibriumState.STABLE: MissionCapabilityStatus.FMC,  # System mathematically sustainable
        EquilibriumState.COMPENSATING: MissionCapabilityStatus.PMC,  # System using compensation mechanisms
        EquilibriumState.STRESSED: MissionCapabilityStatus.PMC,  # System under stress but holding
        EquilibriumState.UNSUSTAINABLE: MissionCapabilityStatus.NMC,  # System math doesn't work long-term
        EquilibriumState.CRITICAL: MissionCapabilityStatus.NMC,  # System approaching collapse
    }

    # Military Occupational Specialty (MOS) codes for medical personnel
    # These codes are used in RFF (Request for Forces) documents to specify
    # what type of medical personnel are needed. Different services use different
    # codes (Army uses 60-series for medical officers, 68-series for enlisted).
    MOS_DESCRIPTIONS = {
        "60H": "Physician, Attending",  # Board-certified attending physician
        "60M": "Physician, Resident",  # Physician in residency training
        "66H": "Nurse Practitioner",  # Advanced practice registered nurse
        "68W": "Combat Medic/Healthcare Specialist",  # Enlisted medic/EMT equivalent
        "68C": "Practical Nursing Specialist",  # Licensed Practical Nurse (LPN)
        "68K": "Medical Laboratory Specialist",  # Lab technician
    }

    def translate_load_shedding(
        self,
        level: LoadSheddingLevel,
    ) -> tuple[DRRSCategory, str]:
        """
        Translate LoadSheddingLevel to DRRS C-rating with explanation.

        Args:
            level: Current load shedding level

        Returns:
            Tuple of (DRRS category, explanation)
        """
        drrs = self.LOAD_SHEDDING_TO_DRRS.get(level, DRRSCategory.C5)

        explanations = {
            DRRSCategory.C1: "Fully Mission Capable. All medical services operational.",
            DRRSCategory.C2: "Substantially Mission Capable. Minor deficiencies in non-essential services.",
            DRRSCategory.C3: "Marginally Mission Capable. Significant deficiencies affecting mission support.",
            DRRSCategory.C4: "Not Mission Capable. Major deficiencies. Unit cannot fully perform core mission.",
            DRRSCategory.C5: "Not Mission Capable. Critical deficiencies. Only emergency patient safety maintained.",
        }

        return drrs, explanations.get(drrs, "Unknown status")

    def translate_personnel_strength(
        self,
        available_faculty: int,
        required_faculty: int,
        overloaded_count: int = 0,
    ) -> tuple[PersonnelReadinessLevel, float]:
        """
        Translate faculty availability to Personnel (P) readiness.

        Personnel readiness considers not just headcount but effective capacity.
        Faculty in allostatic overload count as 0.5 personnel (degraded effectiveness).

        P-ratings (DRRS Personnel Readiness):
        - P1: ≥100% manning (fully staffed or overstaffed)
        - P2: 90-99% manning (minor shortage)
        - P3: 80-89% manning (significant shortage)
        - P4: <80% manning (critical shortage)

        Args:
            available_faculty: Number of faculty available (headcount)
            required_faculty: Number of faculty required (authorized manning)
            overloaded_count: Number of faculty in allostatic overload (burnout risk)

        Returns:
            Tuple of (P-rating, effective percentage)
        """
        if required_faculty == 0:
            return PersonnelReadinessLevel.P4, 0.0

            # Calculate effective availability accounting for degraded capacity of overloaded personnel
            # Overloaded faculty count as 0.5 personnel (50% effective) due to fatigue/burnout
            # This prevents gaming the system by overworking existing staff to appear "fully manned"
        effective_available = max(0, available_faculty - (overloaded_count * 0.5))
        percentage = (effective_available / required_faculty) * 100

        # Map effective percentage to P-rating thresholds
        if percentage >= 100:
            return PersonnelReadinessLevel.P1, percentage  # Fully manned
        elif percentage >= 90:
            return PersonnelReadinessLevel.P2, percentage  # Minor shortage
        elif percentage >= 80:
            return PersonnelReadinessLevel.P3, percentage  # Significant shortage
        else:
            return PersonnelReadinessLevel.P4, percentage  # Critical shortage

    def translate_capability(
        self,
        n1_pass: bool,
        n2_pass: bool,
        coverage_rate: float,
    ) -> tuple[EquipmentReadinessLevel, list[str]]:
        """
        Translate contingency analysis to Capability (S) readiness.

        In DRRS, "S-rating" typically refers to equipment readiness, but we adapt it
        for capability readiness - whether the system can perform its mission even
        when stressed (losing personnel, high demand, etc.).

        N-1/N-2 analysis tests system resilience:
        - N-1: Can system survive losing ANY single person?
        - N-2: Can system survive losing ANY pair of people?

        Failures represent single/dual points of failure in mission capability.

        S-ratings (DRRS Equipment/Capability Readiness):
        - S1: All systems operational, no deficiencies
        - S2: Minor deficiencies (1 issue, no single points of failure)
        - S3: Significant deficiencies (multiple issues, but N-1 passes)
        - S4: Major deficiencies (N-1 failure = any single loss causes mission failure)

        Args:
            n1_pass: Whether system passes N-1 (single loss) test
            n2_pass: Whether system passes N-2 (double loss) test
            coverage_rate: Current coverage rate (0.0 to 1.0)

        Returns:
            Tuple of (S-rating, list of deficiency descriptions)
        """
        deficiencies = []

        # Check for single point of failure (N-1 failure)
        if not n1_pass:
            deficiencies.append(
                "Single Point of Failure: Any faculty loss causes service gaps"
            )

            # Check for dual point vulnerabilities (N-2 failure)
        if not n2_pass:
            deficiencies.append(
                "Dual Point of Failure: Two faculty losses cause critical gaps"
            )

            # Check for coverage degradation
        if coverage_rate < 0.90:
            deficiencies.append(
                f"Coverage degraded: {coverage_rate * 100:.0f}% vs 90% minimum"
            )

            # Determine S-rating based on deficiency count and N-1 status
            # N-1 failure is the critical threshold - if you can't survive ANY single loss,
            # you're S4 regardless of anything else
        if not deficiencies:
            return EquipmentReadinessLevel.S1, deficiencies  # Perfect - no deficiencies
        elif len(deficiencies) == 1 and n1_pass:
            return (
                EquipmentReadinessLevel.S2,
                deficiencies,
            )  # Minor - 1 deficiency, resilient
        elif n1_pass:
            return (
                EquipmentReadinessLevel.S3,
                deficiencies,
            )  # Significant - multiple issues
        else:
            return (
                EquipmentReadinessLevel.S4,
                deficiencies,
            )  # Major - single point of failure exists

    def generate_sitrep_summary(
        self,
        drrs_rating: DRRSCategory,
        p_rating: PersonnelReadinessLevel,
        s_rating: EquipmentReadinessLevel,
        load_shedding_level: LoadSheddingLevel,
        deficiencies: list[str],
    ) -> str:
        """
        Generate a SITREP (Situational Report) style summary.

        This is the slide for the Morning Briefing that forces the Commander
        to stare at a giant "RED" status on their readiness dashboard.

        Args:
            drrs_rating: Overall DRRS category
            p_rating: Personnel readiness
            s_rating: Capability readiness
            load_shedding_level: Current sacrifice hierarchy level
            deficiencies: List of identified deficiencies

        Returns:
            Executive summary in military format
        """
        severity_word = {
            DRRSCategory.C1: "GREEN",
            DRRSCategory.C2: "AMBER",
            DRRSCategory.C3: "YELLOW",
            DRRSCategory.C4: "RED",
            DRRSCategory.C5: "BLACK",
        }

        status = severity_word.get(drrs_rating, "UNKNOWN")

        if drrs_rating in (DRRSCategory.C4, DRRSCategory.C5):
            template = (
                f"UNIT STATUS: {status}\n"
                f"Overall: {drrs_rating.value} | Personnel: {p_rating.value} | Capability: {s_rating.value}\n\n"
                f"MISSION IMPACT: Unit is Non-Mission Capable for standard operations. "
                f"Load shedding at {load_shedding_level.value} level. "
                f"Recommend immediate Cross-Leveling of assets or diversion of non-emergency cases.\n\n"
                f"DEFICIENCIES:\n"
            )
        elif drrs_rating == DRRSCategory.C3:
            template = (
                f"UNIT STATUS: {status}\n"
                f"Overall: {drrs_rating.value} | Personnel: {p_rating.value} | Capability: {s_rating.value}\n\n"
                f"MISSION IMPACT: Unit is Marginally Mission Capable. "
                f"Non-essential services suspended. Commander attention required.\n\n"
                f"DEFICIENCIES:\n"
            )
        else:
            template = (
                f"UNIT STATUS: {status}\n"
                f"Overall: {drrs_rating.value} | Personnel: {p_rating.value} | Capability: {s_rating.value}\n\n"
                f"MISSION IMPACT: Unit is Mission Capable with minor limitations.\n\n"
            )
            if not deficiencies:
                return template.strip()
            template += "WATCH ITEMS:\n"

        for deficiency in deficiencies:
            template += f"  - {deficiency}\n"

        return template.strip()

        # =============================================================================
        # MFR (Memorandum for Record) Generator
        # =============================================================================


@dataclass
class MFRDocument:
    """
    A generated Memorandum for Record (MFR) - formal military documentation.

    MFRs are immutable, cryptographically hashed documents that create an
    official record of system conditions, risks identified, and decisions made.
    They shift liability from schedulers to command when dangerous conditions
    are documented and schedules are published anyway.

    Attributes:
        id: Unique UUID for this MFR
        generated_at: Timestamp when MFR was created (immutable)
        mfr_type: Type of MFR (RISK_ACCEPTANCE, SAFETY_CONCERN, COMPLIANCE_VIOLATION,
                  RESOURCE_REQUEST, STAND_DOWN)
        priority: Urgency level (ROUTINE, PRIORITY, IMMEDIATE, FLASH)
        subject: Subject line for the memorandum
        header: Formatted header with date, MFR ID, priority
        body: Main body text following military format (PURPOSE, BACKGROUND, FINDINGS, etc.)
        findings: List of specific findings from system analysis (N-1 failures, overload, etc.)
        risk_assessment: Narrative risk assessment (CATASTROPHIC, CRITICAL, HIGH, MODERATE, LOW)
        recommendations: Prioritized list of recommended actions
        system_state_snapshot: Complete system state at time of generation (for audit/reconstruction)
        document_hash: SHA-256 hash for immutability verification
        risk_level: Computed risk level enum value
        requires_commander_signature: True if this MFR requires commander acknowledgment
        distribution_list: List of roles/positions who must receive this MFR
                           (DIO, Risk Management, Patient Safety Officer, Commander, etc.)
    """

    id: UUID
    generated_at: datetime
    mfr_type: MFRType
    priority: MFRPriority
    subject: str
    header: str
    body: str
    findings: list[str]
    risk_assessment: str
    recommendations: list[str]
    system_state_snapshot: SystemStateDict
    document_hash: str
    risk_level: RiskLevel
    requires_commander_signature: bool
    distribution_list: list[str]


class MFRGenerator:
    """
    Generates Memoranda for Record for liability protection.

    When a Commander orders you to "make it work" with zero resources,
    you usually comply and take the blame when a patient gets hurt or
    residents burn out.

    This generator auto-creates formal MFRs stamped with the current
    timestamp and system state, putting the liability back on Command.

    "On [Date], the Scheduling System calculated a 98% probability of
    ACGME violation and a 'High' risk of patient safety errors. The
    Scheduler advised against this. This schedule was published under
    direct order/duress."
    """

    # MFR Templates defining format and routing for each document type
    # Each template specifies:
    # - header_template: Subject line format
    # - requires_signature: Whether commander/authority must sign
    # - distribution: Who must receive this MFR (routing list)
    #
    # Distribution routing follows military/healthcare chain of command:
    # - DIO (Designated Institutional Official): ACGME compliance authority
    # - Commander: Military chain of command
    # - Risk Management: Liability and risk assessment
    # - Patient Safety Officer: Clinical safety oversight
    # - Program Director: Residency program leadership
    MFR_TEMPLATES = {
        MFRType.RISK_ACCEPTANCE: {
            "header_template": "MEMORANDUM FOR RECORD\n\nSUBJECT: Risk Acceptance - {subject}",
            "requires_signature": True,  # Must have commander acknowledgment
            "distribution": [
                "Designated Institutional Official",
                "Risk Management",
                "Quality Assurance",
            ],
        },
        MFRType.SAFETY_CONCERN: {
            "header_template": "MEMORANDUM FOR RECORD\n\nSUBJECT: Patient/Staff Safety Concern - {subject}",
            "requires_signature": True,  # Critical - requires signature
            "distribution": [
                "DIO",
                "Risk Management",
                "Patient Safety Officer",
                "Commander",
            ],
        },
        MFRType.COMPLIANCE_VIOLATION: {
            "header_template": "MEMORANDUM FOR RECORD\n\nSUBJECT: ACGME/DHA Compliance Concern - {subject}",
            "requires_signature": True,  # ACGME violations require acknowledgment
            "distribution": ["Program Director", "DIO", "GME Office"],
        },
        MFRType.RESOURCE_REQUEST: {
            "header_template": "MEMORANDUM FOR RECORD\n\nSUBJECT: Resource Request Documentation - {subject}",
            "requires_signature": False,  # Informational - documents the ask
            "distribution": ["Department Chief", "Resource Manager"],
        },
        MFRType.STAND_DOWN: {
            "header_template": "MEMORANDUM FOR RECORD\n\nSUBJECT: Safety Stand-Down Initiated - {subject}",
            "requires_signature": True,  # Critical event - requires signature
            "distribution": [
                "Commander",
                "DIO",
                "Risk Management",
                "Patient Safety Officer",
            ],
        },
    }

    def generate_mfr(
        self,
        mfr_type: MFRType,
        subject: str,
        system_state: SystemHealthState | SystemStateDict,
        scheduler_name: str,
        scheduler_objection: str | None = None,
        priority: MFRPriority = MFRPriority.ROUTINE,
        additional_findings: list[str] | None = None,
    ) -> MFRDocument:
        """
        Generate a Memorandum for Record.

        Args:
            mfr_type: Type of MFR
            subject: Subject line
            system_state: Current system state snapshot
            scheduler_name: Name of scheduler creating MFR
            scheduler_objection: Scheduler's documented objection
            priority: Urgency level
            additional_findings: Extra findings to include

        Returns:
            Generated MFR document
        """
        template = self.MFR_TEMPLATES[mfr_type]
        mfr_id = uuid4()
        now = datetime.now()

        # Generate header
        header = template["header_template"].format(subject=subject)
        header += f"\n\nDATE: {now.strftime('%d %B %Y')}"
        header += f"\nPRIORITY: {priority.value.upper()}"
        header += f"\nMFR ID: {mfr_id}"

        # Extract key metrics from system state
        findings = self._extract_findings(system_state, additional_findings)
        risk_level = self._assess_risk_level(system_state)
        risk_assessment = self._generate_risk_assessment(system_state, risk_level)

        # Generate body
        body = self._generate_body(
            mfr_type=mfr_type,
            system_state=system_state,
            scheduler_name=scheduler_name,
            scheduler_objection=scheduler_objection,
            findings=findings,
            now=now,
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            mfr_type, system_state, risk_level
        )

        # Generate hash for immutability verification
        hash_content = f"{mfr_id}{now.isoformat()}{header}{body}"
        document_hash = hashlib.sha256(hash_content.encode()).hexdigest()

        # Convert system_state to dict for snapshot
        state_snapshot: SystemStateDict = (
            system_state.to_dict()
            if isinstance(system_state, SystemHealthState)
            else system_state
        )  # type: ignore[assignment]

        return MFRDocument(
            id=mfr_id,
            generated_at=now,
            mfr_type=mfr_type,
            priority=priority,
            subject=subject,
            header=header,
            body=body,
            findings=findings,
            risk_assessment=risk_assessment,
            recommendations=recommendations,
            system_state_snapshot=state_snapshot,
            document_hash=document_hash,
            risk_level=risk_level,
            requires_commander_signature=template["requires_signature"],
            distribution_list=template["distribution"],
        )

    def _extract_findings(
        self,
        system_state: SystemHealthState | SystemStateDict,
        additional: list[str] | None,
    ) -> list[str]:
        """Extract findings from system state."""
        findings = []

        # Handle both SystemHealthState and dict
        if isinstance(system_state, SystemHealthState):
            n1_pass = system_state.n1_pass
            n2_pass = system_state.n2_pass
            load_level = system_state.load_shedding_level
            coverage = system_state.coverage_rate
            avg_load = system_state.average_allostatic_load
            eq_state = system_state.equilibrium_state
            phase_risk = system_state.phase_transition_risk
        else:
            n1_pass = system_state.get("n1_pass", True)
            n2_pass = system_state.get("n2_pass", True)
            load_level = system_state.get("load_shedding_level")
            coverage = system_state.get("coverage_rate", 1.0)
            avg_load = system_state.get("average_allostatic_load", 0)
            eq_state = system_state.get("equilibrium_state")
            phase_risk = system_state.get("phase_transition_risk", "low")

            # N-1/N-2 analysis
        if not n1_pass:
            findings.append(
                "N-1 VULNERABILITY: System will fail to maintain coverage if ANY single "
                "faculty member is unavailable. Single point of failure exists."
            )

        if not n2_pass:
            findings.append(
                "N-2 VULNERABILITY: System will fail catastrophically if two faculty "
                "members are simultaneously unavailable. Fatal pairs identified."
            )

            # Load shedding
        if load_level and load_level not in ("NORMAL", LoadSheddingLevel.NORMAL):
            findings.append(
                f"LOAD SHEDDING ACTIVE: Operating at {load_level} level. "
                f"Non-essential services have been suspended."
            )

            # Coverage
        if coverage < 0.90:
            findings.append(
                f"COVERAGE DEGRADED: Current coverage at {coverage * 100:.0f}%, "
                f"below 90% minimum standard."
            )

            # Allostatic load
        if avg_load > 60:
            findings.append(
                f"STAFF OVERLOAD: Average allostatic load at {avg_load:.0f}/100. "
                f"Personnel are in chronic stress state."
            )

            # Equilibrium
        if eq_state in (
            "unsustainable",
            "critical",
            EquilibriumState.UNSUSTAINABLE,
            EquilibriumState.CRITICAL,
        ):
            findings.append(
                "UNSUSTAINABLE OPERATIONS: Current staffing model mathematically cannot "
                "be maintained. System will degrade further without intervention."
            )

            # Phase transition risk
        if phase_risk in ("high", "critical"):
            findings.append(
                f"PHASE TRANSITION RISK: {phase_risk.upper()}. System is approaching "
                "bifurcation point where small changes may cause catastrophic failure."
            )

        if additional:
            findings.extend(additional)

        return findings

    def _assess_risk_level(
        self, system_state: SystemHealthState | SystemStateDict
    ) -> RiskLevel:
        """
        Assess overall risk level from system state using weighted scoring.

        Risk scoring algorithm:
        - N-1 failure: +3 (any single loss causes gaps - single point of failure)
        - N-2 failure: +2 (two losses cause gaps - dual point vulnerability)
        - Coverage <70%: +4 (critical), <80%: +3 (severe), <90%: +2 (degraded)
        - Allostatic load >80: +3 (burnout imminent), >60: +2 (chronic stress)
        - Equilibrium critical: +4, unsustainable: +3 (system math doesn't work)

        Risk levels:
        - 10+: CATASTROPHIC (multiple critical failures)
        - 7-9: CRITICAL (severe risk requiring immediate action)
        - 4-6: HIGH (significant risk, documented acceptance needed)
        - 2-3: MODERATE (watchlist, increased monitoring)
        - 0-1: LOW (normal operations)

        Args:
            system_state: Current system health state

        Returns:
            Computed risk level enum
        """
        risk_score = 0

        # Handle both SystemHealthState and dict
        if isinstance(system_state, SystemHealthState):
            n1_pass = system_state.n1_pass
            n2_pass = system_state.n2_pass
            coverage = system_state.coverage_rate
            avg_load = system_state.average_allostatic_load
            eq_state = system_state.equilibrium_state
        else:
            n1_pass = system_state.get("n1_pass", True)
            n2_pass = system_state.get("n2_pass", True)
            coverage = system_state.get("coverage_rate", 1.0)
            avg_load = system_state.get("average_allostatic_load", 0)
            eq_state = system_state.get("equilibrium_state", "stable")

            # Contingency analysis failures (system resilience to personnel loss)
        if not n1_pass:
            risk_score += 3  # Single point of failure exists
        if not n2_pass:
            risk_score += 2  # Dual point vulnerability exists

            # Coverage degradation (how many shifts are filled)
        if coverage < 0.70:
            risk_score += 4  # Critical: <70% coverage = major service gaps
        elif coverage < 0.80:
            risk_score += 3  # Severe: 70-80% coverage = significant gaps
        elif coverage < 0.90:
            risk_score += 2  # Degraded: 80-90% coverage = minor gaps

            # Staff burnout indicators (allostatic load)
        if avg_load > 80:
            risk_score += 3  # Burnout imminent, attrition risk high
        elif avg_load > 60:
            risk_score += 2  # Chronic stress, sustainability concerns

            # System equilibrium state (can the system math work?)
        if eq_state in ("critical", EquilibriumState.CRITICAL):
            risk_score += 4  # System mathematically unstable
        elif eq_state in ("unsustainable", EquilibriumState.UNSUSTAINABLE):
            risk_score += 3  # System cannot maintain current state

            # Map total risk score to risk level
        if risk_score >= 10:
            return RiskLevel.CATASTROPHIC
        elif risk_score >= 7:
            return RiskLevel.CRITICAL
        elif risk_score >= 4:
            return RiskLevel.HIGH
        elif risk_score >= 2:
            return RiskLevel.MODERATE
        return RiskLevel.LOW

    def _generate_risk_assessment(
        self,
        system_state: SystemHealthState | SystemStateDict,
        risk_level: RiskLevel,
    ) -> str:
        """Generate risk assessment narrative."""
        templates = {
            RiskLevel.CATASTROPHIC: (
                "RISK ASSESSMENT: CATASTROPHIC\n\n"
                "Multiple critical indicators suggest imminent system failure. "
                "Patient safety cannot be assured under current conditions. "
                "Immediate command intervention required. Any schedule published "
                "under these conditions represents acceptance of liability for "
                "preventable adverse outcomes."
            ),
            RiskLevel.CRITICAL: (
                "RISK ASSESSMENT: CRITICAL\n\n"
                "System is operating beyond safe parameters. High probability of "
                "adverse patient or staff outcomes if conditions persist. "
                "Command awareness is required before continuing operations."
            ),
            RiskLevel.HIGH: (
                "RISK ASSESSMENT: HIGH\n\n"
                "Significant deficiencies exist that increase likelihood of "
                "adverse outcomes. Continued operation requires documented risk "
                "acceptance and mitigation planning."
            ),
            RiskLevel.MODERATE: (
                "RISK ASSESSMENT: MODERATE\n\n"
                "Conditions are strained but manageable with vigilance. "
                "Monitoring recommended to prevent escalation."
            ),
            RiskLevel.LOW: (
                "RISK ASSESSMENT: LOW\n\n"
                "Operations are within normal parameters. Standard monitoring "
                "continues."
            ),
        }
        return templates.get(risk_level, "Risk level undetermined.")

    def _generate_body(
        self,
        mfr_type: MFRType,
        system_state: SystemHealthState | SystemStateDict,
        scheduler_name: str,
        scheduler_objection: str | None,
        findings: list[str],
        now: datetime,
    ) -> str:
        """Generate the body of the MFR."""
        body = f"\n\n1. PURPOSE: To document system conditions at {now.strftime('%H%M hours, %d %B %Y')}.\n\n"

        body += "2. BACKGROUND: The automated scheduling system continuously monitors "
        body += "staffing levels, coverage rates, and system health indicators. This "
        body += "memorandum documents conditions that warrant formal record.\n\n"

        body += "3. FINDINGS:\n"
        for i, finding in enumerate(findings, 1):
            body += f"   {chr(96 + i)}. {finding}\n"

        if scheduler_objection:
            body += "\n4. SCHEDULER OBJECTION:\n"
            body += f"   {scheduler_name} has documented the following objection:\n"
            body += f'   "{scheduler_objection}"\n\n'
            body += "5. "
        else:
            body += "\n4. "

        if mfr_type == MFRType.RISK_ACCEPTANCE:
            body += (
                "RISK ACCEPTANCE NOTICE: By approving or publishing the schedule "
                "under these documented conditions, the approving authority accepts "
                "responsibility for associated risks. The scheduling system has "
                "documented this as a 'Force Majeure' event.\n"
            )
        elif mfr_type == MFRType.STAND_DOWN:
            body += (
                "STAND-DOWN INITIATED: Due to conditions documented above, scheduling "
                "operations have been suspended pending command review. Patient safety "
                "operations continue. All non-emergency assignments are frozen.\n"
            )

        return body

    def _generate_recommendations(
        self,
        mfr_type: MFRType,
        system_state: SystemHealthState | SystemStateDict,
        risk_level: RiskLevel,
    ) -> list[str]:
        """Generate recommendations based on MFR type and risk level."""
        recs = []

        if risk_level in (RiskLevel.CRITICAL, RiskLevel.CATASTROPHIC):
            recs.append("IMMEDIATE: Notify Commander and DIO of conditions")
            recs.append(
                "IMMEDIATE: Initiate Safety Stand-Down protocol if not already active"
            )

            # Handle both SystemHealthState and dict
        if isinstance(system_state, SystemHealthState):
            n1_pass = system_state.n1_pass
            coverage = system_state.coverage_rate
            avg_load = system_state.average_allostatic_load
        else:
            n1_pass = system_state.get("n1_pass", True)
            coverage = system_state.get("coverage_rate", 1.0)
            avg_load = system_state.get("average_allostatic_load", 0)

        if not n1_pass:
            recs.append("Request cross-leveling of personnel from adjacent units")
            recs.append("Activate reserve/backup coverage pools")

        if coverage < 0.85:
            recs.append(
                "Consider diversion of non-emergency cases to partner facilities"
            )
            recs.append("Implement graduated return-to-normal coverage plan")

        if avg_load > 60:
            recs.append("Implement mandatory rest periods for high-load personnel")
            recs.append("Defer all non-essential administrative requirements")

        if mfr_type == MFRType.RESOURCE_REQUEST:
            recs.append("Submit Request for Forces (RFF) to DHA")
            recs.append("Document timeline to mission failure without resources")

        return recs

        # =============================================================================
        # Circuit Breaker (Safety Stand-Down)
        # =============================================================================


@dataclass
class CircuitBreakerOverride:
    """
    An active override of the circuit breaker by command authority.

    When the circuit breaker trips, only specific authorities can override it
    to continue operations. The override is time-limited and must be documented
    with an associated MFR that accepts liability.

    Attributes:
        id: Unique UUID for this override
        authority: Who authorized the override (COMMANDER, DIO, PATIENT_SAFETY_OFFICER,
                   RISK_MANAGEMENT, PROGRAM_DIRECTOR)
        reason: Documented justification for the override
        activated_at: When the override was activated
        expires_at: When the override automatically expires (time-limited)
        mfr_id: Associated MFR documenting the risk acceptance, if generated
    """

    id: UUID
    authority: OverrideAuthority
    reason: str
    activated_at: datetime
    expires_at: datetime
    mfr_id: UUID | None = None


@dataclass
class CircuitBreakerStatus:
    """
    Current status of the circuit breaker safety system.

    Provides complete information about the circuit breaker's state,
    what triggered it, any active overrides, and what operations are permitted.

    Attributes:
        state: Current state (CLOSED/HALF_OPEN/OPEN)
        triggered_at: When the circuit breaker last tripped, if applicable
        trigger: What caused the trip (N1_VIOLATION, COVERAGE_COLLAPSE, etc.)
        trigger_details: Human-readable explanation of the trigger
        override: Active override object if command has overridden the breaker
        locked_operations: Operations currently prohibited
        allowed_operations: Operations always permitted (emergency/patient safety)
    """

    state: CircuitBreakerState
    triggered_at: datetime | None
    trigger: CircuitBreakerTrigger | None
    trigger_details: str | None
    override: CircuitBreakerOverride | None
    locked_operations: list[str]
    allowed_operations: list[str]


class CircuitBreaker:
    """
    Scheduling Circuit Breaker - The Nuclear Option.

    In aviation, if safety metrics drop, the fleet is grounded.
    In medicine, we keep grinding.

    This circuit breaker implements a safety stop based on system health.
    When conditions are mathematically unsafe, it:
    - LOCKS the schedule
    - REFUSES to assign new shifts
    - TRIGGERS a Safety Stand-Down protocol
    - NOTIFIES the DIO and Risk Management

    The algorithm says no, citing "Patient Safety Priority 1.0",
    and refuses to let you break the law.
    """

    # Thresholds that trigger the circuit breaker
    THRESHOLDS = {
        "coverage_rate_critical": 0.70,
        "coverage_rate_warning": 0.85,
        "allostatic_load_critical": 80,
        "allostatic_load_warning": 60,
        "compensation_debt_critical": 1000,
        "positive_feedback_confidence": 0.8,
    }

    # Operations locked at each state
    LOCKED_OPERATIONS = {
        CircuitBreakerState.CLOSED: [],
        CircuitBreakerState.HALF_OPEN: [
            "new_assignments",
            "schedule_changes",
            "leave_approval",
        ],
        CircuitBreakerState.OPEN: [
            "new_assignments",
            "schedule_changes",
            "leave_approval",
            "fallback_deactivation",
            "load_shedding_reduction",
        ],
    }

    # Operations always allowed (patient safety)
    ALWAYS_ALLOWED = [
        "emergency_coverage",
        "patient_safety_assignment",
        "crisis_response",
        "view_schedule",
        "read_reports",
    ]

    def __init__(self) -> None:
        self.state: CircuitBreakerState = CircuitBreakerState.CLOSED
        self.triggered_at: datetime | None = None
        self.trigger: CircuitBreakerTrigger | None = None
        self.trigger_details: str | None = None
        self.override: CircuitBreakerOverride | None = None
        self.trip_count: int = 0
        self.last_trip: datetime | None = None

    def check_and_trip(
        self,
        n1_pass: bool,
        n2_pass: bool,
        coverage_rate: float,
        average_allostatic_load: float,
        volatility_level: str,
        compensation_debt: float,
        positive_feedback_risks: (
            list[PositiveFeedbackRisk | PositiveFeedbackRiskDict] | None
        ) = None,
    ) -> tuple[bool, CircuitBreakerTrigger | None, str | None]:
        """
        Check conditions and trip circuit breaker if thresholds breached.

        The circuit breaker implements a priority-based cascade of safety checks.
        Checks are ordered from most critical (N-1 failure) to least critical
        (positive feedback risk). First failed check wins and trips the breaker.

        Threshold priority order:
        1. N-1 failure (single point of failure - immediate lockout)
        2. N-2 failure + degraded coverage (dual failure with existing problems)
        3. Coverage collapse (<70% - service gaps)
        4. Allostatic overload (>80 - burnout imminent)
        5. Critical volatility (phase transition risk)
        6. Compensation debt exceeded (>1000 - unsustainable borrowing)
        7. Positive feedback cascade (>0.8 confidence - death spiral detected)

        Args:
            n1_pass: N-1 analysis result (can system survive any single loss?)
            n2_pass: N-2 analysis result (can system survive any two losses?)
            coverage_rate: Current coverage rate (0.0 to 1.0)
            average_allostatic_load: Average faculty allostatic load (0-100)
            volatility_level: Current volatility level string
            compensation_debt: Accumulated compensation debt
            positive_feedback_risks: Detected positive feedback risks (self-reinforcing failures)

        Returns:
            Tuple of (tripped, trigger, details)
            - tripped: True if breaker tripped on this check
            - trigger: What caused the trip (None if no trip)
            - details: Human-readable explanation
        """
        # Early return if already tripped and no override active
        if self.state == CircuitBreakerState.OPEN and not self._override_active():
            # Already tripped and no override - can't trip again
            return False, self.trigger, self.trigger_details

        trigger = None
        details = None

        # Priority 1: N-1 failure (highest priority - single point of failure exists)
        # This means ANY faculty loss will cause service gaps - unacceptable risk
        if not n1_pass:
            trigger = CircuitBreakerTrigger.N1_VIOLATION
            details = "N-1 analysis failed: Any single faculty loss causes service gaps"

            # Priority 2: N-2 failure combined with already degraded coverage
            # Two vulnerabilities means system is brittle and degrading
        elif not n2_pass and coverage_rate < self.THRESHOLDS["coverage_rate_warning"]:
            trigger = CircuitBreakerTrigger.N2_VIOLATION
            details = "N-2 analysis failed with degraded coverage"

            # Priority 3: Coverage collapse - critical threshold breached
            # Below 70% means significant service gaps already exist
        elif coverage_rate < self.THRESHOLDS["coverage_rate_critical"]:
            trigger = CircuitBreakerTrigger.COVERAGE_COLLAPSE
            details = f"Coverage rate ({coverage_rate * 100:.0f}%) below critical threshold (70%)"

            # Priority 4: Allostatic overload - faculty burnout imminent
            # Above 80 means personnel are in chronic stress, attrition risk high
        elif average_allostatic_load > self.THRESHOLDS["allostatic_load_critical"]:
            trigger = CircuitBreakerTrigger.ALLOSTATIC_OVERLOAD
            details = f"Average allostatic load ({average_allostatic_load:.0f}) exceeds critical threshold (80)"

            # Priority 5: Critical volatility - phase transition risk
            # System approaching bifurcation point where small changes cause catastrophic shifts
        elif volatility_level in ("critical", "CRITICAL"):
            trigger = CircuitBreakerTrigger.VOLATILITY_CRITICAL
            details = "System volatility at critical level - phase transition risk"

            # Priority 6: Compensation debt exceeded - unsustainable borrowing
            # System has borrowed too much future capacity, will fail when debt comes due
        elif compensation_debt > self.THRESHOLDS["compensation_debt_critical"]:
            trigger = CircuitBreakerTrigger.COMPENSATION_DEBT_EXCEEDED
            details = f"Compensation debt ({compensation_debt:.0f}) exceeds sustainable threshold"

            # Priority 7: Positive feedback cascade - death spiral detected
            # Self-reinforcing failure cycle identified with high confidence
        elif positive_feedback_risks:
            # Handle both PositiveFeedbackRisk and dict
            high_confidence_risks = [
                r
                for r in positive_feedback_risks
                if (
                    r.confidence
                    if isinstance(r, PositiveFeedbackRisk)
                    else r.get("confidence", 0)
                )
                > self.THRESHOLDS["positive_feedback_confidence"]
            ]
            if high_confidence_risks:
                trigger = CircuitBreakerTrigger.POSITIVE_FEEDBACK_CASCADE
                details = f"High-confidence positive feedback risks detected: {len(high_confidence_risks)}"

                # If any threshold was breached, trip the circuit breaker
        if trigger:
            self._trip(trigger, details)
            return True, trigger, details

            # If in HALF_OPEN state, check if conditions have improved enough to fully close
            # This allows gradual recovery after a trip
        if self.state == CircuitBreakerState.HALF_OPEN:
            if self._conditions_safe(coverage_rate, average_allostatic_load, n1_pass):
                self.close()

                # No trip occurred
        return False, None, None

    def _trip(self, trigger: CircuitBreakerTrigger, details: str) -> None:
        """Trip the circuit breaker."""
        self.state = CircuitBreakerState.OPEN
        self.triggered_at = datetime.now()
        self.trigger = trigger
        self.trigger_details = details
        self.trip_count += 1
        self.last_trip = datetime.now()

        logger.critical(f"CIRCUIT BREAKER TRIPPED: {trigger.value} - {details}")

    def _conditions_safe(
        self,
        coverage_rate: float,
        allostatic_load: float,
        n1_pass: bool,
    ) -> bool:
        """Check if conditions are safe to close breaker."""
        return (
            coverage_rate >= self.THRESHOLDS["coverage_rate_warning"]
            and allostatic_load < self.THRESHOLDS["allostatic_load_warning"]
            and n1_pass
        )

    def _override_active(self) -> bool:
        """Check if a valid override is active."""
        if not self.override:
            return False
        return datetime.now() < self.override.expires_at

    def close(self) -> None:
        """Close the circuit breaker (resume normal operations)."""
        self.state = CircuitBreakerState.CLOSED
        self.triggered_at = None
        self.trigger = None
        self.trigger_details = None
        self.override = None
        logger.info("Circuit breaker CLOSED - normal operations resumed")

    def half_open(self) -> None:
        """Set circuit breaker to half-open (limited operations)."""
        self.state = CircuitBreakerState.HALF_OPEN
        logger.info("Circuit breaker HALF-OPEN - limited operations")

    def override_breaker(
        self,
        authority: OverrideAuthority,
        reason: str,
        duration_hours: int = 8,
        mfr_id: UUID | None = None,
    ) -> CircuitBreakerOverride:
        """
        Override the circuit breaker.

        This creates a documented override that allows operations despite
        the trip. The override expires and generates an MFR.

        Args:
            authority: Who is authorizing the override
            reason: Why the override is needed
            duration_hours: How long the override lasts
            mfr_id: Associated MFR documenting the override

        Returns:
            The override record
        """
        now = datetime.now()
        self.override = CircuitBreakerOverride(
            id=uuid4(),
            authority=authority,
            reason=reason,
            activated_at=now,
            expires_at=now + timedelta(hours=duration_hours),
            mfr_id=mfr_id,
        )

        logger.warning(
            f"Circuit breaker OVERRIDE by {authority.value}: {reason} "
            f"(expires in {duration_hours} hours)"
        )

        return self.override

    def is_operation_allowed(self, operation: str) -> tuple[bool, str | None]:
        """
        Check if an operation is allowed given current state.

        Args:
            operation: Name of the operation to check

        Returns:
            Tuple of (allowed, reason_if_blocked)
        """
        # Always-allowed operations
        if operation in self.ALWAYS_ALLOWED:
            return True, None

            # If override is active, allow everything except patient-safety critical
        if self._override_active():
            return True, None

            # Check locked operations for current state
        locked = self.LOCKED_OPERATIONS.get(self.state, [])
        if operation in locked:
            return False, (
                f"HTTP 451 Unavailable For Legal Reasons: Operation '{operation}' "
                f"suspended per Patient Safety Protocol 1.0. Circuit breaker state: "
                f"{self.state.value}. Trigger: {self.trigger.value if self.trigger else 'None'}. "
                f"Contact Risk Management to override."
            )

        return True, None

    def get_status(self) -> CircuitBreakerStatus:
        """Get current circuit breaker status."""
        locked = self.LOCKED_OPERATIONS.get(self.state, [])

        return CircuitBreakerStatus(
            state=self.state,
            triggered_at=self.triggered_at,
            trigger=self.trigger,
            trigger_details=self.trigger_details,
            override=self.override,
            locked_operations=locked,
            allowed_operations=self.ALWAYS_ALLOWED.copy(),
        )

        # =============================================================================
        # RFF (Request for Forces) Drafter
        # =============================================================================


@dataclass
class RFFDocument:
    """
    A generated Request for Forces (RFF) document in military SMEAC format.

    RFFs are formal requests for additional military personnel, following
    the standard five-paragraph SMEAC (Situation, Mission, Execution,
    Administration, Command) format. They use cascade predictions to
    mathematically justify resource needs.

    Attributes:
        id: Unique UUID for this RFF
        generated_at: Timestamp when RFF was created
        requesting_unit: Name of the unit/department requesting forces
        uic: Unit Identification Code, if applicable
        mission_affected: List of mission types impacted (PRIMARY_CARE, GME,
                          SPECIALTY_CARE, EMERGENCY_SERVICES, etc.)
        mos_required: List of Military Occupational Specialty codes needed
                      (e.g., "60H" = physician, "66H" = nurse practitioner)
        personnel_count: Number of personnel requested
        duration_days: Duration of request in days
        header: Formatted RFF header with date, ID, requesting unit, priority
        situation: Paragraph 1 - Situation analysis with current status and criticality
        mission_impact: Paragraph 2 - Mission impact assessment with load shedding info
        execution: Paragraph 3 - Execution details (who, how many, what specialties)
        sustainment: Paragraph 4 - Admin/logistics (billeting, meals, travel, duration)
        command_and_signal: Paragraph 5 - Command relationships and reporting
        supporting_metrics: Detailed system metrics supporting the request
        projected_without_support: Timeline projection of what happens without support
        document_hash: SHA-256 hash for immutability verification
    """

    id: UUID
    generated_at: datetime
    requesting_unit: str
    uic: str | None
    mission_affected: list[MissionType]
    mos_required: list[str]
    personnel_count: int
    duration_days: int
    header: str
    situation: str
    mission_impact: str
    execution: str
    sustainment: str
    command_and_signal: str
    supporting_metrics: SupportingMetrics
    projected_without_support: ProjectionWithoutSupport
    document_hash: str


class RFFDrafter:
    """
    Drafts Request for Forces (RFF) documents.

    Since you can't hire in a military hospital, you have to "request assets."
    This is usually a painful manual process of filling out forms that get rejected.

    This drafter uses LeChatelier stress analysis to mathematically prove
    the need for Reservists or cross-leveled personnel. It speaks the language
    of the bureaucracy to unlock resources that "don't exist" for normal requests.

    "Based on cascade scenario projections, Department X will hit 'Extinction
    Vortex' in 14 days. Request activation of 2 Reservists or 3 GS-Civilians
    immediately to prevent mission failure."
    """

    def draft_rff(
        self,
        requesting_unit: str,
        mission_affected: list[MissionType],
        mos_required: list[str],
        personnel_count: int,
        duration_days: int,
        justification: str,
        system_state: SystemHealthState | SystemStateDict,
        cascade_prediction: CascadePrediction | CascadePredictionDict | None = None,
        uic: str | None = None,
    ) -> RFFDocument:
        """
        Draft a Request for Forces document.

        Args:
            requesting_unit: Name of requesting unit/department
            mission_affected: Which missions are impacted
            mos_required: MOSs needed (e.g., "60H", "66H")
            personnel_count: Number of personnel requested
            duration_days: Duration of request
            justification: Text justification
            system_state: Current system metrics
            cascade_prediction: Optional cascade failure prediction
            uic: Unit Identification Code

        Returns:
            Generated RFF document
        """
        rff_id = uuid4()
        now = datetime.now()

        # Generate header
        header = self._generate_header(requesting_unit, now, rff_id, uic)

        # Generate SMEAC paragraphs (Situation, Mission, Execution, Admin, Command)
        situation = self._generate_situation(system_state, cascade_prediction)
        mission_impact = self._generate_mission_impact(mission_affected, system_state)
        execution = self._generate_execution(
            mos_required, personnel_count, duration_days
        )
        sustainment = self._generate_sustainment(duration_days)
        command_and_signal = self._generate_command()

        # Compile supporting metrics
        supporting_metrics = self._compile_metrics(system_state)

        # Generate projection without support
        projected_without = self._project_without_support(
            system_state, cascade_prediction, duration_days
        )

        # Generate hash
        hash_content = f"{rff_id}{now.isoformat()}{header}{situation}"
        document_hash = hashlib.sha256(hash_content.encode()).hexdigest()

        return RFFDocument(
            id=rff_id,
            generated_at=now,
            requesting_unit=requesting_unit,
            uic=uic,
            mission_affected=mission_affected,
            mos_required=mos_required,
            personnel_count=personnel_count,
            duration_days=duration_days,
            header=header,
            situation=situation,
            mission_impact=mission_impact,
            execution=execution,
            sustainment=sustainment,
            command_and_signal=command_and_signal,
            supporting_metrics=supporting_metrics,
            projected_without_support=projected_without,
            document_hash=document_hash,
        )

    def _generate_header(
        self,
        unit: str,
        now: datetime,
        rff_id: UUID,
        uic: str | None,
    ) -> str:
        """Generate RFF header."""
        header = "REQUEST FOR FORCES (RFF)\n"
        header += "=" * 40 + "\n\n"
        header += f"DATE: {now.strftime('%d %B %Y')}\n"
        header += f"RFF ID: {rff_id}\n"
        header += f"REQUESTING UNIT: {unit}\n"
        if uic:
            header += f"UIC: {uic}\n"
        header += "PRIORITY: IMMEDIATE\n"
        return header

    def _generate_situation(
        self,
        system_state: SystemHealthState | SystemStateDict,
        cascade_prediction: CascadePrediction | CascadePredictionDict | None,
    ) -> str:
        """Generate Situation paragraph."""
        situation = "\n1. SITUATION:\n\n"

        situation += "   a. General: Unit experiencing critical personnel shortage "
        situation += "affecting mission capability.\n\n"

        # Handle both SystemHealthState and dict
        if isinstance(system_state, SystemHealthState):
            coverage = system_state.coverage_rate
            n1_pass = system_state.n1_pass
            load = system_state.average_allostatic_load
        else:
            coverage = system_state.get("coverage_rate", 1.0)
            n1_pass = system_state.get("n1_pass", True)
            load = system_state.get("average_allostatic_load", 0)

        situation += "   b. Current Status:\n"
        situation += f"      - Coverage Rate: {coverage * 100:.0f}%\n"

        if not n1_pass:
            situation += (
                "      - N-1 Analysis: FAILED (single point of failure exists)\n"
            )

        if load > 50:
            situation += f"      - Personnel Stress Level: {load:.0f}/100 (elevated)\n"

        if cascade_prediction:
            # Handle both CascadePrediction and dict
            if isinstance(cascade_prediction, CascadePrediction):
                days_to_failure = cascade_prediction.days_until_exhaustion
            else:
                days_to_failure = cascade_prediction.get("days_until_exhaustion", 999)

            if days_to_failure < 30:
                situation += (
                    "\n   c. CRITICAL: Based on cascade analysis, unit will reach\n"
                )
                situation += f"      mission failure state in {days_to_failure} days without intervention.\n"

        return situation

    def _generate_mission_impact(
        self,
        missions: list[MissionType],
        system_state: SystemHealthState | SystemStateDict,
    ) -> str:
        """Generate Mission Impact paragraph."""
        impact = "\n2. MISSION IMPACT:\n\n"

        impact += "   a. Affected Missions:\n"
        for mission in missions:
            impact += f"      - {mission.value.replace('_', ' ').title()}\n"

            # Handle both SystemHealthState and dict
        if isinstance(system_state, SystemHealthState):
            load_level = system_state.load_shedding_level
            eq_state = system_state.equilibrium_state
        else:
            load_level = system_state.get("load_shedding_level", "NORMAL")
            eq_state = system_state.get("equilibrium_state", "stable")

        if load_level not in ("NORMAL", LoadSheddingLevel.NORMAL):
            impact += f"\n   b. Current Load Shedding: {load_level}\n"
            impact += "      Non-essential services have been suspended.\n"

        if eq_state in (
            "unsustainable",
            "critical",
            EquilibriumState.UNSUSTAINABLE,
            EquilibriumState.CRITICAL,
        ):
            eq_str = eq_state.value if hasattr(eq_state, "value") else str(eq_state)
            impact += (
                f"\n   c. CRITICAL: Current operational tempo is {eq_str.upper()}.\n"
            )
            impact += (
                "      Unit cannot maintain mission without additional resources.\n"
            )

        return impact

    def _generate_execution(
        self,
        mos_required: list[str],
        count: int,
        duration: int,
    ) -> str:
        """Generate Execution paragraph."""
        execution = "\n3. EXECUTION:\n\n"

        execution += "   a. Request:\n"
        execution += f"      - Personnel Count: {count}\n"
        execution += f"      - Duration: {duration} days\n"
        execution += "      - MOS Required:\n"

        mos_desc = DRRSTranslator.MOS_DESCRIPTIONS
        for mos in mos_required:
            desc = mos_desc.get(mos, "Medical Personnel")
            execution += f"         * {mos} - {desc}\n"

        execution += "\n   b. Preferred Support:\n"
        execution += "      - Reserve Component activation\n"
        execution += "      - Cross-leveling from adjacent MTFs\n"
        execution += "      - GS-Civilian temporary hires (if authorized)\n"

        return execution

    def _generate_sustainment(self, duration: int) -> str:
        """Generate Sustainment (Admin/Logistics) paragraph."""
        sustainment = "\n4. SUSTAINMENT:\n\n"

        sustainment += "   a. Billeting: Requesting unit will provide\n"
        sustainment += "   b. Meals: Available at MTF dining facility\n"
        sustainment += f"   c. Duration: {duration} days with option to extend\n"
        sustainment += "   d. Travel: Requesting unit funds authorized\n"

        return sustainment

    def _generate_command(self) -> str:
        """Generate Command and Signal paragraph."""
        command = "\n5. COMMAND AND SIGNAL:\n\n"

        command += "   a. Command: OPCON to receiving MTF Commander\n"
        command += "   b. Reporting: Daily SITREP to originating unit\n"
        command += "   c. Signal: Standard MTF communications\n"

        return command

    def _compile_metrics(
        self, system_state: SystemHealthState | SystemStateDict
    ) -> SupportingMetrics:
        """Compile supporting metrics for the RFF."""
        # Handle both SystemHealthState and dict
        if isinstance(system_state, SystemHealthState):
            return SupportingMetrics(
                coverage_rate=system_state.coverage_rate,
                n1_pass=system_state.n1_pass,
                n2_pass=system_state.n2_pass,
                load_shedding_level=str(system_state.load_shedding_level),
                average_allostatic_load=system_state.average_allostatic_load,
                equilibrium_state=str(system_state.equilibrium_state),
                compensation_debt=system_state.compensation_debt,
                snapshot_timestamp=datetime.now().isoformat(),
            )
        else:
            return SupportingMetrics(
                coverage_rate=system_state.get("coverage_rate"),
                n1_pass=system_state.get("n1_pass"),
                n2_pass=system_state.get("n2_pass"),
                load_shedding_level=str(system_state.get("load_shedding_level")),
                average_allostatic_load=system_state.get("average_allostatic_load"),
                equilibrium_state=str(system_state.get("equilibrium_state")),
                compensation_debt=system_state.get("compensation_debt"),
                snapshot_timestamp=datetime.now().isoformat(),
            )

    def _project_without_support(
        self,
        system_state: SystemHealthState | SystemStateDict,
        cascade_prediction: CascadePrediction | CascadePredictionDict | None,
        duration: int,
    ) -> ProjectionWithoutSupport:
        """Project what happens without the requested support."""
        outcomes: list[str] = []

        days_to_fail = 999
        if cascade_prediction:
            if isinstance(cascade_prediction, CascadePrediction):
                days_to_fail = cascade_prediction.days_until_exhaustion
            else:
                days_to_fail = cascade_prediction.get("days_until_exhaustion", 999)

        mission_failure_likely = False
        if days_to_fail < duration:
            outcomes.append(
                f"Day {days_to_fail}: System exhaustion - compensation mechanisms fail"
            )
            outcomes.append(f"Day {days_to_fail + 7}: Estimated ACGME citation risk")
            mission_failure_likely = True

            # Handle both SystemHealthState and dict
        if isinstance(system_state, SystemHealthState):
            load = system_state.average_allostatic_load
            n1_pass = system_state.n1_pass
        else:
            load = system_state.get("average_allostatic_load", 0)
            n1_pass = system_state.get("n1_pass", True)

        if load > 60:
            outcomes.append(
                "Ongoing: Faculty burnout accelerating - attrition risk elevated"
            )

        if not n1_pass:
            outcomes.append(
                "Continuous: Single faculty absence = immediate coverage gaps"
            )

        return ProjectionWithoutSupport(
            timeline_days=duration,
            outcomes=outcomes,
            mission_failure_likely=mission_failure_likely,
        )

        # =============================================================================
        # Iron Dome Service (Unified Interface)
        # =============================================================================


class IronDomeService:
    """
    The Iron Dome - Unified MTF Compliance Service.

    Combines DRRS translation, MFR generation, circuit breaker, and RFF
    drafting into a single service that acts as your Regulatory Bodyguard.

    This service shields schedulers from the friction of a collapsing
    chain of command by weaponizing compliance documentation.
    """

    def __init__(self) -> None:
        self.translator: DRRSTranslator = DRRSTranslator()
        self.mfr_generator: MFRGenerator = MFRGenerator()
        self.circuit_breaker: CircuitBreaker = CircuitBreaker()
        self.rff_drafter: RFFDrafter = RFFDrafter()

        # Document storage (in production, this would be database-backed)
        self.mfr_history: list[MFRDocument] = []
        self.rff_history: list[RFFDocument] = []

    def assess_readiness(
        self,
        load_shedding_level: LoadSheddingLevel,
        equilibrium_state: EquilibriumState,
        n1_pass: bool,
        n2_pass: bool,
        coverage_rate: float,
        available_faculty: int,
        required_faculty: int,
        overloaded_faculty_count: int = 0,
    ) -> ReadinessAssessment:
        """
        Perform full DRRS readiness assessment.

        Returns:
            ReadinessAssessment with military-formatted readiness report (the SITREP).
        """
        # Translate each component
        drrs_rating, drrs_explanation = self.translator.translate_load_shedding(
            load_shedding_level
        )

        p_rating, personnel_pct = self.translator.translate_personnel_strength(
            available_faculty, required_faculty, overloaded_faculty_count
        )

        s_rating, deficiencies = self.translator.translate_capability(
            n1_pass, n2_pass, coverage_rate
        )

        # Generate summary
        summary = self.translator.generate_sitrep_summary(
            drrs_rating, p_rating, s_rating, load_shedding_level, deficiencies
        )

        # Determine overall capability
        if drrs_rating in (DRRSCategory.C4, DRRSCategory.C5):
            capability = MissionCapabilityStatus.NMC
        elif drrs_rating == DRRSCategory.C3:
            capability = MissionCapabilityStatus.PMC
        else:
            capability = MissionCapabilityStatus.FMC

        return ReadinessAssessment(
            overall_rating=drrs_rating.value,
            overall_capability=capability.value,
            personnel_rating=p_rating.value,
            personnel_percentage=personnel_pct,
            capability_rating=s_rating.value,
            deficiencies=deficiencies,
            load_shedding_level=(
                load_shedding_level.value
                if hasattr(load_shedding_level, "value")
                else str(load_shedding_level)
            ),
            equilibrium_state=(
                equilibrium_state.value
                if hasattr(equilibrium_state, "value")
                else str(equilibrium_state)
            ),
            executive_summary=summary,
        )

    def check_circuit_breaker(
        self,
        n1_pass: bool,
        n2_pass: bool,
        coverage_rate: float,
        average_allostatic_load: float,
        volatility_level: str,
        compensation_debt: float,
        positive_feedback_risks: (
            list[PositiveFeedbackRisk | PositiveFeedbackRiskDict] | None
        ) = None,
    ) -> CircuitBreakerCheck:
        """
        Check circuit breaker and trip if thresholds breached.

        Returns:
            CircuitBreakerCheck with current status and any trip information.
        """
        tripped, trigger, details = self.circuit_breaker.check_and_trip(
            n1_pass=n1_pass,
            n2_pass=n2_pass,
            coverage_rate=coverage_rate,
            average_allostatic_load=average_allostatic_load,
            volatility_level=volatility_level,
            compensation_debt=compensation_debt,
            positive_feedback_risks=positive_feedback_risks,
        )

        status = self.circuit_breaker.get_status()

        return CircuitBreakerCheck(
            tripped=tripped,
            state=status.state.value,
            trigger=trigger.value if trigger else None,
            trigger_details=details,
            locked_operations=status.locked_operations,
            allowed_operations=status.allowed_operations,
            override_active=self.circuit_breaker._override_active(),
        )

    def generate_risk_mfr(
        self,
        subject: str,
        system_state: SystemHealthState | SystemStateDict,
        scheduler_name: str,
        scheduler_objection: str | None = None,
    ) -> MFRDocument:
        """
        Generate a risk acceptance MFR.

        Called when publishing a schedule under dangerous conditions.
        """
        mfr = self.mfr_generator.generate_mfr(
            mfr_type=MFRType.RISK_ACCEPTANCE,
            subject=subject,
            system_state=system_state,
            scheduler_name=scheduler_name,
            scheduler_objection=scheduler_objection,
            priority=MFRPriority.PRIORITY,
        )

        self.mfr_history.append(mfr)
        return mfr

    def initiate_safety_stand_down(
        self,
        reason: str,
        initiator: str,
        system_state: SystemHealthState | SystemStateDict,
    ) -> tuple[MFRDocument, IronDomeStatus]:
        """
        Initiate a safety stand-down.

        This trips the circuit breaker and generates documentation.

        Returns:
            Tuple of (MFR document, IronDomeStatus)
        """
        # Trip circuit breaker manually
        self.circuit_breaker._trip(
            CircuitBreakerTrigger.MANUAL_ACTIVATION,
            f"Safety stand-down initiated by {initiator}: {reason}",
        )

        # Generate MFR
        mfr = self.mfr_generator.generate_mfr(
            mfr_type=MFRType.STAND_DOWN,
            subject=f"Safety Stand-Down: {reason}",
            system_state=system_state,
            scheduler_name=initiator,
            priority=MFRPriority.IMMEDIATE,
        )

        self.mfr_history.append(mfr)

        status = self.circuit_breaker.get_status()

        return mfr, IronDomeStatus(
            circuit_breaker_state=status.state.value,
            scheduling_locked=True,
            override_active=self.circuit_breaker._override_active(),
            trigger=status.trigger.value if status.trigger else None,
            mfrs_generated=len(self.mfr_history),
            rffs_generated=len(self.rff_history),
            locked_operations=status.locked_operations,
        )

    def draft_resource_request(
        self,
        requesting_unit: str,
        mission_affected: list[MissionType],
        mos_required: list[str],
        personnel_count: int,
        duration_days: int,
        justification: str,
        system_state: SystemHealthState | SystemStateDict,
        cascade_prediction: CascadePrediction | CascadePredictionDict | None = None,
    ) -> RFFDocument:
        """
        Draft a Request for Forces document.
        """
        rff = self.rff_drafter.draft_rff(
            requesting_unit=requesting_unit,
            mission_affected=mission_affected,
            mos_required=mos_required,
            personnel_count=personnel_count,
            duration_days=duration_days,
            justification=justification,
            system_state=system_state,
            cascade_prediction=cascade_prediction,
        )

        self.rff_history.append(rff)
        return rff

    def get_status(self) -> IronDomeStatus:
        """
        Get overall Iron Dome status.

        Returns:
            IronDomeStatus with complete system status information.
        """
        cb_status = self.circuit_breaker.get_status()

        return IronDomeStatus(
            circuit_breaker_state=cb_status.state.value,
            scheduling_locked=cb_status.state == CircuitBreakerState.OPEN,
            override_active=self.circuit_breaker._override_active(),
            trigger=cb_status.trigger.value if cb_status.trigger else None,
            mfrs_generated=len(self.mfr_history),
            rffs_generated=len(self.rff_history),
            locked_operations=cb_status.locked_operations,
        )
