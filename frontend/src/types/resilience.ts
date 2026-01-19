/**
 * Resilience API Types
 * Mirrors backend/app/schemas/resilience.py
 */

// ============================================================================
// Enums
// ============================================================================

export enum UtilizationLevel {
  GREEN = "GREEN", // < 70% - healthy buffer
  YELLOW = "YELLOW", // 70-80% - approaching threshold
  ORANGE = "ORANGE", // 80-90% - degraded operations
  RED = "RED", // 90-95% - critical, cascade risk
  BLACK = "BLACK", // > 95% - imminent failure
}

export enum DefenseLevel {
  PREVENTION = "PREVENTION",
  CONTROL = "CONTROL",
  SAFETY_SYSTEMS = "SAFETY_SYSTEMS",
  CONTAINMENT = "CONTAINMENT",
  EMERGENCY = "EMERGENCY",
}

export enum LoadSheddingLevel {
  NORMAL = "NORMAL",
  YELLOW = "YELLOW",
  ORANGE = "ORANGE",
  RED = "RED",
  BLACK = "BLACK",
  CRITICAL = "CRITICAL",
}

export enum OverallStatus {
  HEALTHY = "healthy",
  WARNING = "warning",
  DEGRADED = "degraded",
  CRITICAL = "critical",
  EMERGENCY = "emergency",
}

export type EmergencyCoverageStatus = "success" | "partial" | "failed";

// ============================================================================
// Base Interfaces
// ============================================================================

export interface UtilizationMetrics {
  utilizationRate: number;
  level: UtilizationLevel;
  bufferRemaining: number;
  waitTimeMultiplier: number;
  safeCapacity: number;
  currentDemand: number;
  theoreticalCapacity: number;
}

export interface RedundancyStatus {
  service: string;
  status: string;
  available: number;
  minimumRequired: number;
  buffer: number;
}

export interface CentralityScore {
  facultyId: string; // UUID
  facultyName: string;
  centralityScore: number;
  servicesCovered: number;
  uniqueCoverageSlots: number;
  replacementDifficulty: number;
  riskLevel: string;
}

// ============================================================================
// Health Check Types
// ============================================================================

export interface HealthCheckResponse {
  timestamp: string; // ISO date string
  overallStatus: OverallStatus;

  // Component statuses
  utilization: UtilizationMetrics;
  defenseLevel: DefenseLevel;
  redundancyStatus: RedundancyStatus[];
  loadSheddingLevel: LoadSheddingLevel;
  activeFallbacks: string[];
  crisisMode: boolean;

  // Risk indicators
  n1Pass: boolean;
  n2Pass: boolean;
  phaseTransitionRisk: string;

  // Recommendations
  immediateActions: string[];
  watchItems: string[];
}

// ============================================================================
// Vulnerability Report Types
// ============================================================================

export interface VulnerabilityReportResponse {
  analyzedAt: string;
  periodStart: string;
  periodEnd: string;

  n1Pass: boolean;
  n2Pass: boolean;
  phaseTransitionRisk: string;

  // Details are simplified as Record<string, any> or generic object for now
  // unless we need specific typing for the nested vulnerability details
  n1Vulnerabilities: Array<{
    facultyId: string;
    affectedBlocks: number[];
    severity: string;
  }>;
  n2FatalPairs: Array<{
    faculty1Id: string;
    faculty2Id: string;
  }>;
  mostCriticalFaculty: CentralityScore[];

  recommendedActions: string[];
}

// ============================================================================
// Emergency Coverage Types
// ============================================================================

/**
 * Request to find emergency coverage for an absence
 */
export interface EmergencyCoverageRequest {
  personId: string;
  startDate: string;
  endDate: string;
  reason: string;
  isDeployment: boolean;
}

/**
 * Detail about a single replacement or gap
 */
export interface CoverageDetail {
  date: string;
  originalAssignment: string;
  replacement?: string;
  status: "replaced" | "gap";
}

/**
 * Response from emergency coverage request
 */
export interface EmergencyCoverageResponse {
  status: EmergencyCoverageStatus;
  replacementsFound: number;
  coverageGaps: number;
  requiresManualReview: boolean;
  details: CoverageDetail[];
}

// ============================================================================
// Defense Level Types
// ============================================================================

/**
 * Response from defense level endpoint
 */
export interface DefenseLevelResponse {
  level: DefenseLevel;
  levelNumber: number;
  description: string;
  recommendedActions: string[];
  escalationThreshold: number;
}

// ============================================================================
// Utilization Threshold Types
// ============================================================================

/**
 * Response from utilization threshold check
 */
export interface UtilizationThresholdResponse {
  utilizationRate: number;
  level: UtilizationLevel;
  aboveThreshold: boolean;
  bufferRemaining: number;
  waitTimeMultiplier: number;
  message: string;
  recommendations: string[];
}

// ============================================================================
// Burnout Epidemiology Types
// ============================================================================

/**
 * Response from burnout Rt calculation
 */
export interface BurnoutRtResponse {
  rt: number;
  status: "declining" | "stable" | "growing" | "crisis";
  secondaryCases: number;
  timeWindowDays: number;
  confidenceInterval?: {
    lower: number;
    upper: number;
  };
  interventions: string[];
}

// ============================================================================
// Circuit Breaker Types (Netflix Hystrix pattern)
// ============================================================================

export enum CircuitState {
  CLOSED = "closed", // Normal operation
  OPEN = "open", // Circuit tripped, fail-fast
  HALF_OPEN = "half_open", // Testing recovery
}

export enum BreakerSeverity {
  HEALTHY = "healthy",
  WARNING = "warning",
  CRITICAL = "critical",
  EMERGENCY = "emergency",
}

export interface StateTransitionInfo {
  fromState: string;
  toState: string;
  timestamp: string;
  reason: string;
}

export interface CircuitBreakerStatusInfo {
  name: string;
  state: CircuitState;
  failureRate: number;
  successRate: number;
  totalRequests: number;
  successfulRequests: number;
  failedRequests: number;
  rejectedRequests: number;
  consecutiveFailures: number;
  consecutiveSuccesses: number;
  openedAt: string | null;
  lastFailureTime: string | null;
  lastSuccessTime: string | null;
  recentTransitions: StateTransitionInfo[];
}

export interface AllBreakersStatusResponse {
  totalBreakers: number;
  closedBreakers: number;
  openBreakers: number;
  halfOpenBreakers: number;
  openBreakerNames: string[];
  halfOpenBreakerNames: string[];
  breakers: CircuitBreakerStatusInfo[];
  overallHealth: string;
  recommendations: string[];
  checkedAt: string;
}

export interface BreakerHealthMetrics {
  totalRequests: number;
  totalFailures: number;
  totalRejections: number;
  overallFailureRate: number;
  breakersAboveThreshold: number;
  averageFailureRate: number;
  maxFailureRate: number;
  unhealthiestBreaker: string | null;
}

export interface BreakerHealthResponse {
  totalBreakers: number;
  metrics: BreakerHealthMetrics;
  breakersNeedingAttention: string[];
  trendAnalysis: string;
  severity: BreakerSeverity;
  recommendations: string[];
  analyzedAt: string;
}

// ============================================================================
// MTF Compliance Types (Military Multi-Tier Functionality)
// ============================================================================

export interface MTFComplianceResponse {
  drrsCategory: string; // DRRS C-rating (C1-C5)
  missionCapability: string;
  personnelRating: string; // P-rating (P1-P4)
  capabilityRating: string; // S-rating (S1-S4)
  circuitBreaker: Record<string, unknown> | null;
  executiveSummary: string;
  deficiencies: string[];
  ironDomeStatus: string; // green/yellow/red
  severity: string; // healthy/warning/critical/emergency
}

// ============================================================================
// Unified Critical Index Types (Multi-factor risk aggregation)
// ============================================================================

export enum RiskPattern {
  UNIVERSAL_CRITICAL = "universal_critical",
  STRUCTURAL_BURNOUT = "structural_burnout",
  INFLUENTIAL_HUB = "influential_hub",
  SOCIAL_CONNECTOR = "social_connector",
  ISOLATED_WORKHORSE = "isolated_workhorse",
  BURNOUT_VECTOR = "burnout_vector",
  NETWORK_ANCHOR = "network_anchor",
  LOW_RISK = "low_risk",
}

export enum InterventionType {
  IMMEDIATE_PROTECTION = "immediate_protection",
  CROSS_TRAINING = "cross_training",
  WORKLOAD_REDUCTION = "workload_reduction",
  NETWORK_DIVERSIFICATION = "network_diversification",
  MONITORING = "monitoring",
  WELLNESS_SUPPORT = "wellness_support",
}

export interface DomainScoreInfo {
  rawScore: number;
  normalizedScore: number;
  percentile: number;
  isCritical: boolean;
  details: Record<string, unknown>;
}

export interface FacultyUnifiedIndex {
  facultyId: string;
  facultyName: string;
  compositeIndex: number;
  riskPattern: RiskPattern;
  confidence: number;
  domainScores: Record<string, DomainScoreInfo>;
  domainAgreement: number;
  leadingDomain: string | null;
  conflictDetails: string[];
  recommendedInterventions: InterventionType[];
  priorityRank: number;
}

export interface UnifiedCriticalIndexResponse {
  analyzedAt: string;
  totalFaculty: number;
  overallIndex: number;
  riskLevel: string;
  riskConcentration: number;
  criticalCount: number;
  universalCriticalCount: number;
  patternDistribution: Record<string, number>;
  topPriority: string[];
  topCriticalFaculty: FacultyUnifiedIndex[];
  contributingFactors: Record<string, number>;
  trend: string;
  topConcerns: string[];
  recommendations: string[];
  severity: string;
}

// ============================================================================
// Blast Radius Zone Types (Tier 2 Strategic)
// ============================================================================

export enum ZoneType {
  INPATIENT = "inpatient",
  OUTPATIENT = "outpatient",
  EDUCATION = "education",
  RESEARCH = "research",
  ADMINISTRATIVE = "admin",
  ON_CALL = "on_call",
}

export enum ZoneStatus {
  GREEN = "green",
  YELLOW = "yellow",
  ORANGE = "orange",
  RED = "red",
  BLACK = "black",
}

export enum ContainmentLevel {
  NONE = "none",
  SOFT = "soft",
  MODERATE = "moderate",
  STRICT = "strict",
  LOCKDOWN = "lockdown",
}

/**
 * Health report for a scheduling zone
 */
export interface ZoneHealthReport {
  zoneId: string;
  zoneName: string;
  zoneType: ZoneType;
  checkedAt: string;
  status: ZoneStatus;
  containmentLevel: ContainmentLevel;
  isSelfSufficient: boolean;
  hasSurplus: boolean;
  availableFaculty: number;
  minimumRequired: number;
  optimalRequired: number;
  capacityRatio: number;
  facultyBorrowed: number;
  facultyLent: number;
  netBorrowing: number;
  activeIncidents: number;
  servicesAffected: string[];
  recommendations: string[];
}

/**
 * Overall blast radius containment report
 */
export interface BlastRadiusReportResponse {
  generatedAt: string;
  totalZones: number;
  zonesHealthy: number;
  zonesDegraded: number;
  zonesCritical: number;
  containmentActive: boolean;
  containmentLevel: ContainmentLevel;
  zonesIsolated: number;
  activeBorrowingRequests: number;
  pendingBorrowingRequests: number;
  zoneReports: ZoneHealthReport[];
  recommendations: string[];
}

// ============================================================================
// Stigmergy Types (Tier 3: Preference Trails)
// ============================================================================

/**
 * A single slot preference pattern from stigmergy analysis
 */
export interface SlotPreferencePattern {
  slotType: string;
  netPreference: number;
}

/**
 * A swap pair affinity from stigmergy analysis
 */
export interface SwapPairPattern {
  facultyId1: string;
  facultyId2: string;
  affinity: number;
}

/**
 * Response from stigmergy patterns endpoint
 */
export interface StigmergyPatternsResponse {
  patterns: StigmergyPatternData[];
  total: number;
}

/**
 * Individual pattern data from the stigmergy API.
 * The backend returns a single pattern object with arrays of slot preferences and swap pairs.
 *
 * Structure (after axios camelCase conversion):
 * {
 *   popularSlots: [[slotType, netPreference], ...],
 *   unpopularSlots: [[slotType, netPreference], ...],
 *   neutralSlots: [[slotType, netPreference], ...],
 *   strongSwapPairs: [[facultyId1, facultyId2, strength], ...],
 *   totalPatterns: number
 * }
 */
export interface StigmergyPatternData {
  // Slot preference patterns: [slotType, netPreference][]
  popularSlots: Array<[string, number]>;
  unpopularSlots: Array<[string, number]>;
  neutralSlots?: Array<[string, number]>;

  // Swap pair patterns: [facultyId1, facultyId2, strength][]
  strongSwapPairs: Array<[string, string, number]>;

  // Metadata
  totalPatterns: number;
}
