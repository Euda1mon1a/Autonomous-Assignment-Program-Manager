/**
 * CP-SAT Simulator Constants
 *
 * Visual and simulation constants for the optimization landscape.
 */

import { LandscapeConfig } from "./types";

/**
 * Color palette for the visualization
 */
export const COLORS = {
  primary: "#00f2ff",
  secondary: "#ff0055",
  surface: "#050505",
  text: "#cbd5e1",
  muted: "#64748b",
} as const;

/**
 * Landscape dimensions
 */
export const LANDSCAPE_SIZE = 40;
export const GRID_DIVISIONS = 80;

/**
 * Default landscape configuration
 */
export const DEFAULT_CONFIG: LandscapeConfig = {
  complexity: 0.5,
  noiseScale: 1.0,
  amplitude: 4.0,
};

/**
 * Default initial metrics
 */
export const DEFAULT_METRICS = {
  objective: "0.00000",
  branches: 0,
  backtracks: 0,
  status: "exploring" as const,
  gap: "1.000%",
};

/**
 * Solver status descriptions for fallback AI narration
 */
export const STATUS_DESCRIPTIONS: Record<string, string[]> = {
  exploring: [
    "Traversing unexplored regions of the search space. Evaluating potential constraint satisfaction paths.",
    "Expanding the frontier of known solutions. Probing local optima for global characteristics.",
    "Scanning the topology for promising descent vectors. Branch-and-bound heuristics active.",
  ],
  descending: [
    "Gradient descent initiated. Following the steepest path toward local minimum.",
    "Objective function improving. Narrowing in on a feasible region.",
    "Propagating constraints through the decision tree. Solution quality increasing.",
  ],
  backtracking: [
    "Dead end detected. Reversing to last viable branch point.",
    "Constraint violation encountered. Unwinding state to explore alternatives.",
    "Local optimum exhausted. Backtracking to unexplored decision nodes.",
  ],
  pruning: [
    "Inferior branches eliminated. Bounding function confirms suboptimality.",
    "Pruning search tree. Current bound exceeds known solution quality.",
    "Cutting off dominated solutions. Focusing compute on promising subspaces.",
  ],
};

/**
 * Get a random status description for fallback AI narration
 */
export function getStatusDescription(status: string): string {
  const descriptions = STATUS_DESCRIPTIONS[status] ?? STATUS_DESCRIPTIONS.exploring;
  return descriptions[Math.floor(Math.random() * descriptions.length)];
}
