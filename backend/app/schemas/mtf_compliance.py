"""
MTF (Military Treatment Facility) Compliance Schemas.

The "Iron Dome" module - Automated Bureaucratic Defense for military medicine.

This module translates clinical scheduling metrics into military readiness
language and generates compliance documentation that protects schedulers
from blame when forced into unsafe staffing situations.

Key insight: In a military hospital, you don't solve problems with money
or hiring - you solve them with Rank, Regulations, and Paper Trails.
"""

from datetime import datetime
from enum import IntEnum, Enum
from uuid import UUID

from pydantic import BaseModel, Field


***REMOVED*** =============================================================================
***REMOVED*** DRRS (Defense Readiness Reporting System) Translation Layer
***REMOVED*** =============================================================================


class DRRSCategory(str, Enum):
    """
    Defense Readiness Reporting System (DRRS) C-ratings.

    Standard military readiness categories that commanders understand.
    Maps to LoadSheddingLevel for universal military comprehension.
    """
    C1 = "C-1"  ***REMOVED*** Fully mission capable - all resources available
    C2 = "C-2"  ***REMOVED*** Substantially mission capable - minor deficiencies
    C3 = "C-3"  ***REMOVED*** Marginally mission capable - significant deficiencies
    C4 = "C-4"  ***REMOVED*** Not mission capable - major deficiencies
    C5 = "C-5"  ***REMOVED*** Not mission capable - critical deficiencies


class PersonnelReadinessLevel(str, Enum):
    """Personnel (P) readiness sub-rating."""
    P1 = "P-1"  ***REMOVED*** 100% of required personnel
    P2 = "P-2"  ***REMOVED*** 90-99% of required personnel
    P3 = "P-3"  ***REMOVED*** 80-89% of required personnel (partially mission capable)
    P4 = "P-4"  ***REMOVED*** Below 80% (non-mission capable)


class EquipmentReadinessLevel(str, Enum):
    """Equipment/capability (S) readiness sub-rating."""
    S1 = "S-1"  ***REMOVED*** All equipment/capabilities operational
    S2 = "S-2"  ***REMOVED*** Minor capability gaps
    S3 = "S-3"  ***REMOVED*** Significant capability gaps
    S4 = "S-4"  ***REMOVED*** Major capability gaps


class MissionType(str, Enum):
    """Types of medical missions for readiness assessment."""
    LEVEL_1_TRAUMA = "level_1_trauma"
    LEVEL_2_TRAUMA = "level_2_trauma"
    INPATIENT_MEDICINE = "inpatient_medicine"
    SURGICAL_SERVICES = "surgical_services"
    EMERGENCY_DEPARTMENT = "emergency_department"
    OUTPATIENT_PRIMARY = "outpatient_primary"
    SPECIALTY_CARE = "specialty_care"
    GRADUATE_MEDICAL_EDUCATION = "graduate_medical_education"


class MissionCapabilityStatus(str, Enum):
    """Mission capability assessment."""
    FMC = "FMC"    ***REMOVED*** Fully Mission Capable
    PMC = "PMC"    ***REMOVED*** Partially Mission Capable
    NMC = "NMC"    ***REMOVED*** Non-Mission Capable


***REMOVED*** =============================================================================
***REMOVED*** MFR (Memorandum for Record) Generation
***REMOVED*** =============================================================================


class MFRType(str, Enum):
    """Types of Memoranda for Record."""
    RISK_ACCEPTANCE = "risk_acceptance"      ***REMOVED*** Commander accepted known risk
    SAFETY_CONCERN = "safety_concern"        ***REMOVED*** Patient/staff safety at risk
    COMPLIANCE_VIOLATION = "compliance_violation"  ***REMOVED*** ACGME/DHA violation
    RESOURCE_REQUEST = "resource_request"    ***REMOVED*** Request for forces/resources
    STAND_DOWN = "stand_down"                ***REMOVED*** Safety stand-down initiated


class MFRPriority(str, Enum):
    """Priority/urgency of the MFR."""
    ROUTINE = "routine"
    PRIORITY = "priority"
    IMMEDIATE = "immediate"
    FLASH = "flash"  ***REMOVED*** Highest urgency


class RiskLevel(str, Enum):
    """Risk levels for documentation."""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"
    CATASTROPHIC = "catastrophic"


***REMOVED*** =============================================================================
***REMOVED*** Circuit Breaker (Safety Stand-Down)
***REMOVED*** =============================================================================


class CircuitBreakerState(str, Enum):
    """State of the scheduling circuit breaker."""
    CLOSED = "closed"       ***REMOVED*** Normal operations
    HALF_OPEN = "half_open"  ***REMOVED*** Limited operations, testing recovery
    OPEN = "open"           ***REMOVED*** Scheduling locked, requires override


class CircuitBreakerTrigger(str, Enum):
    """What triggered the circuit breaker."""
    N1_VIOLATION = "n1_violation"
    N2_VIOLATION = "n2_violation"
    ALLOSTATIC_OVERLOAD = "allostatic_overload"
    VOLATILITY_CRITICAL = "volatility_critical"
    COMPENSATION_DEBT_EXCEEDED = "compensation_debt_exceeded"
    POSITIVE_FEEDBACK_CASCADE = "positive_feedback_cascade"
    COVERAGE_COLLAPSE = "coverage_collapse"
    MANUAL_ACTIVATION = "manual_activation"


class OverrideAuthority(str, Enum):
    """Who can override the circuit breaker."""
    SCHEDULER = "scheduler"            ***REMOVED*** Limited override
    CHIEF_RESIDENT = "chief_resident"  ***REMOVED*** Extended override
    PROGRAM_DIRECTOR = "program_director"  ***REMOVED*** Full override
    DIO = "dio"                        ***REMOVED*** Designated Institutional Official
    COMMANDER = "commander"            ***REMOVED*** MTF Commander
    RISK_MANAGEMENT = "risk_management"


***REMOVED*** =============================================================================
***REMOVED*** Request/Response Schemas
***REMOVED*** =============================================================================


class DRRSReadinessRequest(BaseModel):
    """Request for DRRS readiness assessment."""
    include_all_missions: bool = Field(
        default=True,
        description="Include all mission types in assessment"
    )
    specific_missions: list[MissionType] | None = Field(
        default=None,
        description="Specific missions to assess"
    )


class MissionReadiness(BaseModel):
    """Readiness assessment for a specific mission type."""
    mission_type: MissionType
    mission_name: str
    capability_status: MissionCapabilityStatus
    personnel_rating: PersonnelReadinessLevel
    capability_rating: EquipmentReadinessLevel
    combined_rating: DRRSCategory
    deficiencies: list[str]
    degradation_percentage: float = Field(
        ge=0.0, le=100.0,
        description="Percentage capability degraded from baseline"
    )
    recovery_actions: list[str]


class DRRSReadinessResponse(BaseModel):
    """Full DRRS readiness report - the "SITREP"."""
    assessed_at: datetime
    overall_rating: DRRSCategory
    overall_capability: MissionCapabilityStatus
    personnel_rating: PersonnelReadinessLevel
    capability_rating: EquipmentReadinessLevel

    ***REMOVED*** Mission-specific breakdowns
    missions: list[MissionReadiness]
    missions_fmc: int  ***REMOVED*** Fully Mission Capable count
    missions_pmc: int  ***REMOVED*** Partially Mission Capable count
    missions_nmc: int  ***REMOVED*** Non-Mission Capable count

    ***REMOVED*** Translated from internal metrics
    load_shedding_level: str
    sacrifice_hierarchy_state: str
    equilibrium_state: str

    ***REMOVED*** Commander-focused summary
    executive_summary: str
    recommended_actions: list[str]

    ***REMOVED*** Risk indicators in military language
    risk_to_force: RiskLevel
    risk_to_mission: RiskLevel


class MFRRequest(BaseModel):
    """Request to generate a Memorandum for Record."""
    mfr_type: MFRType
    priority: MFRPriority = MFRPriority.ROUTINE
    subject: str = Field(..., min_length=10, max_length=200)
    include_system_state: bool = True
    include_vulnerability_analysis: bool = True
    include_recommendations: bool = True
    scheduler_name: str = Field(..., min_length=2, max_length=100)
    scheduler_objection: str | None = Field(
        default=None,
        description="Scheduler's documented objection to the situation"
    )


class MFRResponse(BaseModel):
    """Generated Memorandum for Record."""
    id: UUID
    generated_at: datetime
    mfr_type: MFRType
    priority: MFRPriority
    subject: str

    ***REMOVED*** Document content
    header: str
    body: str
    findings: list[str]
    risk_assessment: str
    recommendations: list[str]

    ***REMOVED*** Audit trail
    system_state_snapshot: dict
    document_hash: str  ***REMOVED*** SHA-256 for immutability verification

    ***REMOVED*** Classification
    risk_level: RiskLevel
    requires_commander_signature: bool
    distribution_list: list[str]


class RFFRequest(BaseModel):
    """Request for Forces (RFF) generation request."""
    requesting_unit: str = Field(..., min_length=2, max_length=100)
    uic: str | None = Field(
        default=None,
        description="Unit Identification Code"
    )
    mission_affected: list[MissionType]
    mos_required: list[str] = Field(
        description="Military Occupational Specialty codes needed (e.g., 60H, 66H)"
    )
    personnel_count: int = Field(..., ge=1)
    duration_days: int = Field(..., ge=1, le=365)
    justification: str = Field(..., min_length=50, max_length=2000)


class RFFResponse(BaseModel):
    """Generated Request for Forces document."""
    id: UUID
    generated_at: datetime

    ***REMOVED*** Request details
    requesting_unit: str
    uic: str | None
    mission_affected: list[MissionType]
    mos_required: list[str]
    personnel_count: int
    duration_days: int

    ***REMOVED*** Generated content
    header: str
    situation: str  ***REMOVED*** Situation paragraph
    mission_impact: str  ***REMOVED*** Mission impact analysis
    execution: str  ***REMOVED*** Requested execution
    sustainment: str  ***REMOVED*** Logistics/admin
    command_and_signal: str  ***REMOVED*** Command relationships

    ***REMOVED*** Supporting data
    supporting_metrics: dict
    projected_without_support: dict  ***REMOVED*** What happens without RFF approval
    document_hash: str


class CircuitBreakerStatusResponse(BaseModel):
    """Current circuit breaker status."""
    state: CircuitBreakerState
    triggered_at: datetime | None
    trigger: CircuitBreakerTrigger | None
    trigger_details: str | None

    ***REMOVED*** Current thresholds
    n1_status: bool  ***REMOVED*** True = passing
    n2_status: bool  ***REMOVED*** True = passing
    average_allostatic_load: float
    volatility_level: str
    compensation_debt: float
    coverage_rate: float

    ***REMOVED*** Override information
    override_active: bool
    override_authority: OverrideAuthority | None
    override_expires: datetime | None
    override_reason: str | None
    override_mfr_id: UUID | None  ***REMOVED*** Links to MFR documenting the override

    ***REMOVED*** What's locked
    locked_operations: list[str]
    allowed_operations: list[str]


class CircuitBreakerOverrideRequest(BaseModel):
    """Request to override circuit breaker."""
    authority: OverrideAuthority
    reason: str = Field(..., min_length=20, max_length=500)
    duration_hours: int = Field(default=8, ge=1, le=72)
    acknowledge_risks: bool = Field(
        ...,
        description="Explicitly acknowledge the documented risks"
    )
    generate_mfr: bool = Field(
        default=True,
        description="Generate MFR documenting the override"
    )


class CircuitBreakerOverrideResponse(BaseModel):
    """Response from circuit breaker override."""
    success: bool
    override_id: UUID | None
    expires_at: datetime | None
    mfr_generated: bool
    mfr_id: UUID | None
    warning_message: str
    risks_acknowledged: list[str]


class SafetyStandDownRequest(BaseModel):
    """Request to initiate a safety stand-down."""
    reason: str = Field(..., min_length=20, max_length=500)
    initiator: str
    notify_dio: bool = True
    notify_risk_management: bool = True
    notify_commander: bool = False


class SafetyStandDownResponse(BaseModel):
    """Response from safety stand-down initiation."""
    stand_down_active: bool
    initiated_at: datetime
    initiated_by: str
    reason: str

    ***REMOVED*** Notifications sent
    dio_notified: bool
    risk_management_notified: bool
    commander_notified: bool

    ***REMOVED*** Generated documentation
    mfr_id: UUID

    ***REMOVED*** Impact
    operations_suspended: list[str]
    operations_continuing: list[str]  ***REMOVED*** Patient safety only
    recovery_requirements: list[str]


***REMOVED*** =============================================================================
***REMOVED*** Audit/History Schemas
***REMOVED*** =============================================================================


class MFRHistoryItem(BaseModel):
    """Historical MFR record."""
    id: UUID
    generated_at: datetime
    mfr_type: MFRType
    priority: MFRPriority
    subject: str
    risk_level: RiskLevel
    document_hash: str


class MFRHistoryResponse(BaseModel):
    """List of historical MFRs."""
    items: list[MFRHistoryItem]
    total: int
    page: int
    page_size: int


class CircuitBreakerEventHistoryItem(BaseModel):
    """Historical circuit breaker event."""
    id: UUID
    timestamp: datetime
    event_type: str  ***REMOVED*** triggered, reset, overridden
    state_before: CircuitBreakerState
    state_after: CircuitBreakerState
    trigger: CircuitBreakerTrigger | None
    override_authority: OverrideAuthority | None
    mfr_id: UUID | None


class CircuitBreakerHistoryResponse(BaseModel):
    """Circuit breaker event history."""
    items: list[CircuitBreakerEventHistoryItem]
    total: int
    page: int
    page_size: int


***REMOVED*** =============================================================================
***REMOVED*** Iron Dome Status (Combined)
***REMOVED*** =============================================================================


class IronDomeStatusResponse(BaseModel):
    """Overall Iron Dome (MTF Compliance) status."""
    timestamp: datetime

    ***REMOVED*** DRRS Readiness
    overall_readiness: DRRSCategory
    missions_nmc_count: int
    risk_to_mission: RiskLevel

    ***REMOVED*** Circuit Breaker
    circuit_breaker_state: CircuitBreakerState
    scheduling_locked: bool
    override_active: bool

    ***REMOVED*** Documentation
    mfrs_generated_today: int
    mfrs_requiring_signature: int
    rffs_pending: int

    ***REMOVED*** Alerts
    active_alerts: list[str]
    recommended_actions: list[str]
