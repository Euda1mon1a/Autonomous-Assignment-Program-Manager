/**
 * CP-SAT Simulator
 *
 * 3D visualization of constraint programming solver behavior.
 */

export { CpsatSimulator } from "./CpsatSimulator";
export { default } from "./CpsatSimulator";

// Types
export type {
  CpsatSimulatorProps,
  SolverMetrics,
  SolverStatus,
  LandscapeConfig,
  ChatMessage,
} from "./types";

// Constants
export { COLORS, DEFAULT_CONFIG, DEFAULT_METRICS, LANDSCAPE_SIZE } from "./constants";

// Components (for advanced usage)
export { Landscape } from "./components/Landscape";
export { SolverAgent } from "./components/SolverAgent";
export { HUD } from "./components/HUD";
export { ControlPanel } from "./components/ControlPanel";
