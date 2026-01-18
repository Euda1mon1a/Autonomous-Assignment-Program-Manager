/**
 * Fragility Triage Types
 *
 * TypeScript interfaces for the fragility triage visualization.
 */

export interface DayData {
  /** Day number (1-28) */
  day: number;
  /** Fragility score (0.0 to 1.0) */
  fragility: number;
  /** Single Point of Failure name or null */
  spof: string | null;
  /** List of active violations/cascading failures */
  violations: string[];
  /** Staffing level percentage */
  staffingLevel: number;
}

export interface Scenario {
  /** Unique identifier */
  id: string;
  /** Display label */
  label: string;
  /** Impact on redundancy (percentage points) */
  impact: number;
  /** Description of the scenario */
  description: string;
}

export interface AnalysisResponse {
  /** AI-generated tactical analysis */
  analysis: string;
  /** List of suggested mitigations */
  mitigations: string[];
}
