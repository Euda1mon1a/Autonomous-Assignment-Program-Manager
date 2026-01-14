/**
 * 3D Voxel Schedule Visualization Feature
 *
 * A novel approach to schedule visualization using 3D voxel space.
 * Includes both 2D canvas-based view and Three.js 3D view.
 *
 * New in this version:
 * - Real-time solver visualization with animated transitions
 * - Instanced rendering for 50,000+ voxels at 60 FPS
 * - WebSocket streaming of solver solutions
 * - Delta-encoded updates for efficient transmission
 */

// Components
export { VoxelScheduleView } from "./VoxelScheduleView";
export { default as VoxelScheduleView3D } from "./VoxelScheduleView3D";

// High-performance instanced renderer
export {
  InstancedVoxelRenderer,
  ACTIVITY_COLORS,
  ACTIVITY_NAMES,
  assignmentToVoxel,
  calculateVoxelStats,
} from "./InstancedVoxelRenderer";
export type {
  VoxelInstance,
  VoxelTransition,
  InstancedVoxelRendererProps,
} from "./InstancedVoxelRenderer";

// Real-time solver visualization
export { SolverVisualization, SolverVisualizationDemo } from "./SolverVisualization";

// Hooks
export { useSolutionTransitions, easeOutCubic, easeInOutCubic, easeOutBack } from "./useSolutionTransitions";
export type {
  Assignment as TransitionAssignment,
  SolutionDelta,
  TransitionState,
  UseSolutionTransitionsOptions,
  UseSolutionTransitionsReturn,
} from "./useSolutionTransitions";

export { useSolverWebSocket, useSolverProgressPolling } from "./useSolverWebSocket";
export type {
  SolverMetrics,
  Assignment,
  SolverSolutionEvent,
  SolverCompleteEvent,
  SolverStatus,
  UseSolverWebSocketOptions,
  UseSolverWebSocketReturn,
} from "./useSolverWebSocket";

// Note: VoxelScheduleView3D should be lazy-loaded due to Three.js bundle size
// Use: dynamic(() => import('@/features/voxel-schedule/VoxelScheduleView3D'), { ssr: false })

// Types
export type {
  Voxel,
  VoxelGridData,
  VoxelGridDimensions,
  VoxelGridStatistics,
  VoxelPosition,
  VoxelIdentity,
  VoxelVisual,
  VoxelState,
  VoxelMetadata,
  VoxelScheduleViewProps,
  VoxelConflict,
  CoverageGap,
} from "./types";
