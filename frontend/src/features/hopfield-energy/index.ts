/**
 * Hopfield Energy Landscape
 *
 * 3D visualization of schedule stability using neural attractor dynamics.
 * Now with real API data integration.
 */

export { HopfieldVisualizer } from './HopfieldVisualizer';
export { default } from './HopfieldVisualizer';

// Types
export type {
  HopfieldVisualizerProps,
  EnergyState,
  ReadinessStatus,
  EnergySurfaceProps,
  EnergyBallProps,
  ControlPanelProps,
  HopfieldEnergyResponse,
  EnergyMetricsResponse,
  StabilityLevel,
} from './types';

// Re-export hooks from centralized location
export {
  useHopfieldEnergy,
  useNearbyAttractors,
  useBasinDepth,
  useSpuriousAttractors,
} from '@/hooks/useHopfield';

// Constants
export {
  GRID_SIZE,
  SURFACE_SIZE,
  computeEnergy,
  computeGradient,
  getMilitaryColor,
  getReadinessStatus,
  STATUS_CONFIG,
  LEGEND_ITEMS,
} from './constants';

// Components (for advanced usage)
export { EnergySurface } from './components/EnergySurface';
export { EnergyBall } from './components/EnergyBall';
export { ControlPanel } from './components/ControlPanel';
