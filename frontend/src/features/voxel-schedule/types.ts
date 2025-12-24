/**
 * Types for 3D Voxel Schedule Visualization
 */

export interface VoxelPosition {
  x: number;
  y: number;
  z: number;
}

export interface VoxelIdentity {
  assignment_id: string | null;
  person_id: string | null;
  person_name: string | null;
  block_id: string | null;
  block_date: string | null;
  block_time_of_day: string | null;
  activity_name: string | null;
  activity_type: string | null;
}

export interface VoxelVisual {
  color: string;
  rgba: [number, number, number, number];
  opacity: number;
  height: number;
}

export interface VoxelState {
  is_occupied: boolean;
  is_conflict: boolean;
  is_violation: boolean;
  violation_details: string[];
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
  x_size: number;
  y_size: number;
  z_size: number;
  x_labels: string[];
  y_labels: string[];
  z_labels: string[];
}

export interface VoxelGridStatistics {
  total_assignments: number;
  total_conflicts: number;
  total_violations: number;
  coverage_percentage: number;
}

export interface VoxelGridData {
  dimensions: VoxelGridDimensions;
  voxels: Voxel[];
  statistics: VoxelGridStatistics;
  date_range: {
    start_date: string | null;
    end_date: string | null;
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
  type: "double_booking" | "supervision_gap" | "acgme_violation";
}

/**
 * Coverage gap from spatial analysis
 */
export interface CoverageGap {
  x: number;
  time_label: string;
  coverage_count: number;
  severity: "critical" | "warning";
}
