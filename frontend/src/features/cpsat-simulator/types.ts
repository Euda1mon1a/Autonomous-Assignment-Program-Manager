/**
 * CP-SAT Simulator Types
 *
 * Types for the constraint programming solver visualization.
 * Simulates how OR-Tools CP-SAT explores the optimization space.
 */

/**
 * Solver status states
 */
export type SolverStatus = "exploring" | "descending" | "backtracking" | "pruning";

/**
 * Real-time solver metrics
 */
export interface SolverMetrics {
  /** Current objective function value */
  objective: string;
  /** Number of search tree branches explored */
  branches: number;
  /** Number of backtracks performed */
  backtracks: number;
  /** Current solver status */
  status: SolverStatus;
  /** Optimality gap percentage */
  gap: string;
}

/**
 * Landscape configuration for the cost function surface
 */
export interface LandscapeConfig {
  /** Complexity factor (0.1 - 1.0) */
  complexity: number;
  /** Noise scale for surface features (0.5 - 2.5) */
  noiseScale: number;
  /** Amplitude of surface height variation (1 - 10) */
  amplitude: number;
}

/**
 * Chat message for AI narration
 */
export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

/**
 * Props for the main simulator component
 */
export interface CpsatSimulatorProps {
  /** Initial landscape configuration */
  initialConfig?: LandscapeConfig;
  /** Show/hide the HUD */
  showHud?: boolean;
  /** Show/hide the control panel */
  showControls?: boolean;
  /** Custom class name */
  className?: string;
}

/**
 * Props for the Landscape component
 */
export interface LandscapeProps {
  config: LandscapeConfig;
}

/**
 * Props for the SolverAgent component
 */
export interface SolverAgentProps {
  config: LandscapeConfig;
  onUpdate: (metrics: Partial<SolverMetrics>) => void;
}

/**
 * Props for the HUD component
 */
export interface HudProps {
  metrics: SolverMetrics;
  history: ChatMessage[];
  loading: boolean;
}

/**
 * Props for the ControlPanel component
 */
export interface ControlPanelProps {
  onScenarioPrompt: (prompt: string) => void;
  onRefreshExplain: () => void;
}
