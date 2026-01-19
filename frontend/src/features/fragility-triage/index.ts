/**
 * Fragility Triage Feature
 *
 * Barrel exports for the fragility triage visualization.
 */

export { FragilityGrid } from './components/FragilityGrid';
export { AnalysisPanel } from './components/AnalysisPanel';
export { SimulationControl } from './components/SimulationControl';
export { SCENARIOS, generateMockDays } from './constants';
export { useFragilityData, useVulnerabilityReport } from './hooks/useFragilityData';
export type { DayData, Scenario, AnalysisResponse } from './types';
export type {
  VulnerabilityReportResponse,
  CentralityScore,
  N1Vulnerability,
  N2FatalPair,
} from './hooks/useFragilityData';
