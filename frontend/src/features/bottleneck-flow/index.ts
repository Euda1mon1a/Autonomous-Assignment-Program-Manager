/**
 * Bottleneck Flow Feature
 *
 * 3D supervision cascade visualization for the optimization labs.
 * Shows faculty-trainee relationships and simulates cascade effects
 * when faculty become unavailable.
 */

// Main component
export { BottleneckFlowVisualizer } from './BottleneckFlowVisualizer';
export { default } from './BottleneckFlowVisualizer';

// Types
export type {
  BottleneckFlowVisualizerProps,
  BottleneckFaculty,
  BottleneckTrainee,
  BottleneckMetrics,
  SimulationState,
  TraineeStatus,
  TraineeStatusType,
  LaneType,
  LaneConfig,
} from './types';

// Constants
export { COLORS, THREE_COLORS, LANES, SIZES } from './constants';

// Hooks
export { useBottleneckSimulation } from './hooks/useBottleneckSimulation';
export {
  useBottleneckData,
  transformToBottleneckData,
  generateMockData,
} from './hooks/useBottleneckData';

// Components (for advanced usage)
export { SimulationScene } from './components/SimulationScene';
export { UIOverlay } from './components/UIOverlay';
export { LaneVisual } from './components/LaneVisual';
export { FacultyNode } from './components/FacultyNode';
export { TraineeNode } from './components/TraineeNode';
export { DynamicConnection } from './components/DynamicConnection';
