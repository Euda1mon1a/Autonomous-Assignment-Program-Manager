/**
 * N-1/N-2 Resilience Feature
 *
 * Interactive absence simulation to test schedule resilience.
 * Fetches real zone data from the blast radius API.
 */

export { N1N2Visualizer } from './N1N2Visualizer';
export { default } from './N1N2Visualizer';

// Types
export type {
  ResilienceMode,
  Faculty,
  CascadeMetrics,
  SimulationState,
  N1N2VisualizerProps,
  FacultyGridProps,
  CascadeMetricsProps,
  ModeSelectorProps,
} from './types';

// Hooks
export { useN1N2Data } from './hooks/useN1N2Data';
export type { UseN1N2DataResult } from './hooks/useN1N2Data';

// Constants (computeCascadeMetrics still used for client-side simulation)
export { computeCascadeMetrics } from './constants';

// Components (for advanced usage)
export { FacultyGrid } from './components/FacultyGrid';
export { CascadeMetrics as CascadeMetricsComponent } from './components/CascadeMetrics';
export { ModeSelector } from './components/ModeSelector';
