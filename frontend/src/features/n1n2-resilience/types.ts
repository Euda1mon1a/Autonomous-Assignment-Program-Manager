/**
 * N-1/N-2 Resilience Visualizer Types
 *
 * Types for simulating faculty absences and measuring cascade effects.
 */

/**
 * Resilience mode - how many simultaneous absences the system can handle
 */
export type ResilienceMode = 'N-1' | 'N-2';

/**
 * Faculty member with absence simulation status
 */
export interface Faculty {
  id: string;
  name: string;
  role: 'attending' | 'senior' | 'junior';
  specialty: string;
  coverage: number; // Percentage of schedule covered (0-100)
  isAbsent: boolean;
  criticality: 'low' | 'medium' | 'high' | 'critical';
}

/**
 * Cascade metrics after absence simulation
 */
export interface CascadeMetrics {
  coverageGap: number; // Percentage of uncovered slots
  affectedSlots: number; // Number of slots affected
  cascadeDepth: number; // How many layers of redistribution needed
  redistributionLoad: number; // Average additional load on remaining faculty
  systemStatus: 'stable' | 'strained' | 'critical' | 'failed';
  recoveryTime: string; // Estimated time to recover
}

/**
 * Simulation state
 */
export interface SimulationState {
  mode: ResilienceMode;
  absentFaculty: string[]; // IDs of absent faculty
  metrics: CascadeMetrics;
  isRunning: boolean;
}

/**
 * Props for the main visualizer
 */
export interface N1N2VisualizerProps {
  className?: string;
}

/**
 * Props for the faculty grid
 */
export interface FacultyGridProps {
  faculty: Faculty[];
  absentFaculty: string[];
  mode: ResilienceMode;
  onToggleAbsence: (id: string) => void;
}

/**
 * Props for cascade metrics display
 */
export interface CascadeMetricsProps {
  metrics: CascadeMetrics;
  mode: ResilienceMode;
}

/**
 * Props for mode selector
 */
export interface ModeSelectorProps {
  mode: ResilienceMode;
  onModeChange: (mode: ResilienceMode) => void;
  absentCount: number;
}
