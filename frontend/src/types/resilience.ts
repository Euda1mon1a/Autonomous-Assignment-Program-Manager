/**
 * Resilience API Types
 * Mirrors backend/app/schemas/resilience.py
 */

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

export interface UtilizationMetrics {
  utilization_rate: number;
  level: UtilizationLevel;
  buffer_remaining: number;
  wait_time_multiplier: number;
  safe_capacity: number;
  current_demand: number;
  theoretical_capacity: number;
}

export interface RedundancyStatus {
  service: string;
  status: string;
  available: number;
  minimum_required: number;
  buffer: number;
}

export interface HealthCheckResponse {
  timestamp: string; // ISO date string
  overall_status: OverallStatus;

  // Component statuses
  utilization: UtilizationMetrics;
  defense_level: DefenseLevel;
  redundancy_status: RedundancyStatus[];
  load_shedding_level: LoadSheddingLevel;
  active_fallbacks: string[];
  crisis_mode: boolean;

  // Risk indicators
  n1_pass: boolean;
  n2_pass: boolean;
  phase_transition_risk: string;

  // Recommendations
  immediate_actions: string[];
  watch_items: string[];
}

export interface CentralityScore {
  faculty_id: string; // UUID
  faculty_name: string;
  centrality_score: number;
  services_covered: number;
  unique_coverage_slots: number;
  replacement_difficulty: number;
  risk_level: string;
}

export interface VulnerabilityReportResponse {
  analyzed_at: string;
  period_start: string;
  period_end: string;

  n1_pass: boolean;
  n2_pass: boolean;
  phase_transition_risk: string;

  // Details are simplified as Record<string, any> or generic object for now
  // unless we need specific typing for the nested vulnerability details
  n1_vulnerabilities: Array<{
    faculty_id: string;
    affected_blocks: number[];
    severity: string;
  }>;
  n2_fatal_pairs: Array<{
    faculty1_id: string;
    faculty2_id: string;
  }>;
  most_critical_faculty: CentralityScore[];

  recommended_actions: string[];
}
