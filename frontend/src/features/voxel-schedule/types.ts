/**
 * Types for 3D Voxel Schedule Visualization
 */

export interface VoxelPosition {
  x: number;
  y: number;
  z: number;
}

export interface VoxelIdentity {
  assignmentId: string | null;
  personId: string | null;
  personName: string | null;
  blockId: string | null;
  blockDate: string | null;
  blockTimeOfDay: string | null;
  activityName: string | null;
  activityType: string | null;
}

export interface VoxelVisual {
  color: string;
  rgba: [number, number, number, number];
  opacity: number;
  height: number;
}

export interface VoxelState {
  isOccupied: boolean;
  isConflict: boolean;
  isViolation: boolean;
  violationDetails: string[];
}

export interface VoxelMetadata {
  role: string | null;
  confidence: number;
  hours: number;
}

export interface Voxel {
  position: VoxelPosition;
  identity: VoxelIdentity;
  visual: VoxelVisual;
  state: VoxelState;
  metadata: VoxelMetadata;
}

export interface VoxelGridDimensions {
  xSize: number;
  ySize: number;
  zSize: number;
  xLabels: string[];
  yLabels: string[];
  zLabels: string[];
}

export interface VoxelGridStatistics {
  totalAssignments: number;
  totalConflicts: number;
  totalViolations: number;
  coveragePercentage: number;
}

export interface VoxelGridData {
  dimensions: VoxelGridDimensions;
  voxels: Voxel[];
  statistics: VoxelGridStatistics;
  dateRange: {
    startDate: string | null;
    endDate: string | null;
  };
  error?: string;
}

/**
 * Props for VoxelScheduleView component
 */
export interface VoxelScheduleViewProps {
  /** Start date for the visualization window */
  startDate?: Date;
  /** End date for the visualization window */
  endDate?: Date;
  /** Optional filter for specific people */
  personIds?: string[];
  /** Optional filter for specific activity types */
  activityTypes?: string[];
  /** Callback when a voxel is clicked */
  onVoxelClick?: (voxel: Voxel) => void;
  /** Callback when hovering over a voxel */
  onVoxelHover?: (voxel: Voxel | null) => void;
  /** Show only conflicts/violations */
  showConflictsOnly?: boolean;
  /** Color mode for voxels */
  colorMode?: "activity" | "compliance" | "workload";
}

/**
 * Conflict detection result from spatial analysis
 */
export interface VoxelConflict {
  position: VoxelPosition;
  voxels: Voxel[];
  type: "double_booking" | "supervision_gap" | "acgmeViolation";
}

/**
 * Coverage gap from spatial analysis
 */
export interface CoverageGap {
  x: number;
  timeLabel: string;
  coverageCount: number;
  severity: "critical" | "warning";
}
