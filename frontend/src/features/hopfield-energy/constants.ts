/**
 * Hopfield Energy Landscape Constants
 *
 * Energy function and color mapping for schedule stability visualization.
 */

import type { ReadinessStatus, MilitaryColor } from './types';

/** Grid resolution for the energy surface */
export const GRID_SIZE = 60;

/** Surface dimensions */
export const SURFACE_SIZE = 4;

/** Gradient descent step size */
export const DESCENT_STEP = 0.005;

/** Gradient epsilon for numerical differentiation */
export const GRADIENT_EPS = 0.01;

/** Convergence threshold */
export const CONVERGENCE_THRESHOLD = 0.01;

/**
 * Compute Hopfield energy at a given (coverage, balance) point.
 * Creates a landscape with:
 * - Global minimum near (0.85, 0.85) - full coverage, perfect balance
 * - Local minima to demonstrate attractor dynamics
 * - Sinusoidal noise for visual interest
 *
 * @param u - Normalized coverage (0-1)
 * @param v - Normalized balance (0-1)
 * @returns Energy value (lower = more stable)
 */
export function computeEnergy(u: number, v: number): number {
  // Sinusoidal noise for visual texture
  const noise = 0.4 * Math.sin(u * 12) * Math.cos(v * 12);

  // Base quadratic bowl centered at (0.5, 0.5)
  const base = -1.5 * ((u - 0.5) ** 2 + (v - 0.5) ** 2);

  // Global minimum near (0.85, 0.85) - optimal state
  const globalMin = -2.5 * Math.exp(-((u - 0.85) ** 2 + (v - 0.85) ** 2) * 8);

  // Local minima - represent sub-optimal stable states
  const localMin1 = -1.2 * Math.exp(-((u - 0.3) ** 2 + (v - 0.7) ** 2) * 12);
  const localMin2 = -1.0 * Math.exp(-((u - 0.6) ** 2 + (v - 0.25) ** 2) * 10);

  return (base + noise + globalMin + localMin1 + localMin2) * 0.8;
}

/**
 * Compute energy gradient at a point for gradient descent.
 *
 * @param u - Normalized coverage (0-1)
 * @param v - Normalized balance (0-1)
 * @returns [dE/du, dE/dv] gradient vector
 */
export function computeGradient(u: number, v: number): [number, number] {
  const dEdU =
    (computeEnergy(u + GRADIENT_EPS, v) - computeEnergy(u - GRADIENT_EPS, v)) /
    (2 * GRADIENT_EPS);
  const dEdV =
    (computeEnergy(u, v + GRADIENT_EPS) - computeEnergy(u, v - GRADIENT_EPS)) /
    (2 * GRADIENT_EPS);
  return [dEdU, dEdV];
}

/**
 * Get military color for a normalized energy value.
 * Color coding follows military readiness levels:
 * - White: Optimal (exceeds expectations)
 * - Green: Stable (good operational state)
 * - Amber: Caution (marginal)
 * - Red: Danger (unstable)
 * - Black: Death Zone (critical failure)
 *
 * @param t - Normalized energy (0 = best, 1 = worst)
 * @returns RGB color values (0-1)
 */
export function getMilitaryColor(t: number): MilitaryColor {
  if (t < 0.15) {
    // White (optimal)
    const blend = t / 0.15;
    return { r: 1.0 - blend * 0.1, g: 1.0 - blend * 0.13, b: 1.0 - blend * 0.6 };
  } else if (t < 0.35) {
    // Green (stable)
    const blend = (t - 0.15) / 0.2;
    return { r: 0.13 + blend * 0.87, g: 0.87 - blend * 0.22, b: 0.4 - blend * 0.2 };
  } else if (t < 0.55) {
    // Amber (caution)
    const blend = (t - 0.35) / 0.2;
    return { r: 1.0 - blend * 0.07, g: 0.65 - blend * 0.43, b: 0.2 - blend * 0.05 };
  } else if (t < 0.8) {
    // Red (danger)
    const blend = (t - 0.55) / 0.25;
    return { r: 0.93 - blend * 0.83, g: 0.22 - blend * 0.17, b: 0.15 - blend * 0.1 };
  } else {
    // Black (death zone)
    const blend = (t - 0.8) / 0.2;
    return { r: 0.1 - blend * 0.08, g: 0.05 - blend * 0.03, b: 0.05 - blend * 0.03 };
  }
}

/**
 * Get readiness status from normalized energy.
 *
 * @param t - Normalized energy (0 = best, 1 = worst)
 * @returns Readiness status
 */
export function getReadinessStatus(t: number): ReadinessStatus {
  if (t < 0.15) return 'white';
  if (t < 0.35) return 'green';
  if (t < 0.55) return 'amber';
  if (t < 0.8) return 'red';
  return 'black';
}

/**
 * Status display configuration
 */
export const STATUS_CONFIG: Record<
  ReadinessStatus,
  { text: string; className: string }
> = {
  white: {
    text: 'WHITE - Optimal',
    className: 'bg-white/20 text-white border border-white/30',
  },
  green: {
    text: 'GREEN - Stable',
    className: 'bg-green-500/20 text-green-400 border border-green-500/30',
  },
  amber: {
    text: 'AMBER - Caution',
    className: 'bg-amber-500/20 text-amber-400 border border-amber-500/30',
  },
  red: {
    text: 'RED - Danger',
    className: 'bg-red-500/20 text-red-400 border border-red-500/30',
  },
  black: {
    text: 'BLACK - Death Zone',
    className: 'bg-gray-900 text-red-500 border border-red-900',
  },
};

/**
 * Legend items for the visualization
 */
export const LEGEND_ITEMS = [
  { color: 'bg-white', label: 'White = Optimal (exceeds expectations)' },
  { color: 'bg-green-500', label: 'Green = Stable (good)' },
  { color: 'bg-amber-500', label: 'Amber = Caution (marginal)' },
  { color: 'bg-red-500', label: 'Red = Danger (unstable)' },
  { color: 'bg-gray-900 border border-gray-700', label: 'Black = Death Zone' },
];
