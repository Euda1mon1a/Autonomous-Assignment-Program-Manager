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
