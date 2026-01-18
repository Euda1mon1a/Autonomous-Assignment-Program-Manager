/**
 * N-1/N-2 Resilience Feature
 *
 * Interactive absence simulation to test schedule resilience.
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

// Constants
export { MOCK_FACULTY, computeCascadeMetrics } from './constants';

// Components (for advanced usage)
export { FacultyGrid } from './components/FacultyGrid';
export { CascadeMetrics as CascadeMetricsComponent } from './components/CascadeMetrics';
export { ModeSelector } from './components/ModeSelector';
