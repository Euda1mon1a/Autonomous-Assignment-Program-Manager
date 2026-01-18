/**
 * Sovereign Portal Types
 *
 * Types for the unified command dashboard with 4-panel view.
 */

/**
 * Panel identifiers
 */
export type PanelId = 'spatial' | 'fairness' | 'solver' | 'fragility';

/**
 * Panel configuration
 */
export interface PanelConfig {
  id: PanelId;
  label: string;
  description: string;
  status: 'nominal' | 'warning' | 'critical';
  value: number;
  unit: string;
}

/**
 * System-wide status
 */
export type SystemStatus = 'OPERATIONAL' | 'DEGRADED' | 'CRITICAL' | 'OFFLINE';

/**
 * Alert from any subsystem
 */
export interface SystemAlert {
  id: string;
  panel: PanelId;
  severity: 'info' | 'warning' | 'critical';
  message: string;
  timestamp: Date;
}

/**
 * Spatial panel metrics
 */
export interface SpatialMetrics {
  coveragePercent: number;
  gapCount: number;
  distributionScore: number;
}

/**
 * Fairness panel metrics
 */
export interface FairnessMetrics {
  giniCoefficient: number;
  jainsIndex: number;
  maxDeviation: number;
}

/**
 * Solver panel metrics
 */
export interface SolverMetrics {
  objectiveValue: number;
  constraintsSatisfied: number;
  constraintsTotal: number;
  solutionQuality: 'optimal' | 'feasible' | 'infeasible';
}

/**
 * Fragility panel metrics
 */
export interface FragilityMetrics {
  systemFragility: number;
  criticalPaths: number;
  redundancyLevel: number;
}

/**
 * Aggregate dashboard state
 */
export interface DashboardState {
  status: SystemStatus;
  spatial: SpatialMetrics;
  fairness: FairnessMetrics;
  solver: SolverMetrics;
  fragility: FragilityMetrics;
  alerts: SystemAlert[];
  lastUpdate: Date;
}

/**
 * Props for the main portal
 */
export interface SovereignPortalProps {
  className?: string;
}

/**
 * Props for individual panel
 */
export interface PanelProps {
  config: PanelConfig;
  children: React.ReactNode;
  isExpanded?: boolean;
  onToggleExpand?: () => void;
}
