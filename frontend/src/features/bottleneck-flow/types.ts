/**
 * Bottleneck Flow Visualizer Types
 *
 * TypeScript interfaces for the 3D supervision cascade visualization.
 * All field names use camelCase per CLAUDE.md API naming convention.
 */

import * as THREE from 'three';

// ============================================================================
// Lane Types
// ============================================================================

export type LaneType = 'AT' | 'FMIT' | 'RESERVE';

export interface LaneConfig {
  y: number;
  color: string;
  threeColor: THREE.Color;
  name: string;
}

// ============================================================================
// Entity Types
// ============================================================================

/**
 * Faculty member in the bottleneck visualization.
 * Maps to backend Person model with type='faculty'.
 */
export interface BottleneckFaculty {
  id: string;
  name: string;
  lane: LaneType;
  specialty: string;
  traineeIds: string[];
  isDisabled: boolean;
}

/**
 * Trainee (resident) in the bottleneck visualization.
 * Maps to backend Person model with type='resident'.
 */
export interface BottleneckTrainee {
  id: string;
  name: string;
  pgy: 1 | 2 | 3;
  primaryFacultyId: string;
  backupFacultyId: string;
}

// ============================================================================
// Simulation Types
// ============================================================================

/**
 * Current state of the bottleneck simulation.
 */
export interface SimulationState {
  showSuggestedFix: boolean;
  disabledFacultyIds: Set<string>;
}

/**
 * Metrics calculated from the current simulation state.
 */
export interface BottleneckMetrics {
  coverage: number;
  orphaned: number;
  rerouted: number;
  atRisk: number;
}

/**
 * Status of a trainee in the cascade simulation.
 */
export type TraineeStatusType = 'nominal' | 'orphaned' | 'rerouted' | 'at-risk';

/**
 * Full status information for a trainee including target faculty.
 */
export interface TraineeStatus {
  status: TraineeStatusType;
  targetFacultyId: string | null;
  targetPositionOffset: [number, number, number] | null;
}

/**
 * Extended trainee with computed status and position data.
 */
export interface TraineeNodeData extends BottleneckTrainee {
  statusObj: TraineeStatus;
  primaryPos: THREE.Vector3 | undefined;
  targetPos: THREE.Vector3 | undefined;
}

// ============================================================================
// Component Props
// ============================================================================

export interface BottleneckFlowVisualizerProps {
  className?: string;
}

export interface SimulationSceneProps {
  faculty: BottleneckFaculty[];
  trainees: BottleneckTrainee[];
  simState: SimulationState;
  onMetricsUpdate: (metrics: BottleneckMetrics) => void;
}

export interface UIOverlayProps {
  metrics: BottleneckMetrics;
  simState: SimulationState;
  faculty: BottleneckFaculty[];
  onToggleFaculty: (id: string) => void;
  onToggleFix: () => void;
  onReset: () => void;
}

export interface FacultyNodeProps {
  faculty: BottleneckFaculty;
  position: [number, number, number];
  isDisabled: boolean;
  laneColor: THREE.Color;
}

export interface TraineeNodeProps {
  trainee: BottleneckTrainee;
  status: TraineeStatus;
  primaryFacultyPos: THREE.Vector3;
  targetFacultyPos?: THREE.Vector3;
  orbitIndex: number;
  totalInCohort: number;
}

export interface DynamicConnectionProps {
  traineeRef: React.RefObject<THREE.Mesh>;
  targetPos: THREE.Vector3;
  status: TraineeStatusType;
}

export interface LaneVisualProps {
  config: LaneConfig;
}
