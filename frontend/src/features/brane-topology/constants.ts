/**
 * Brane Topology Constants
 *
 * Architectural constants for the residency visualization.
 * Quantizes the units of the Tripler Residency program.
 */

import * as THREE from "three";

import { ResidencyData, UnitSpec } from "./types";

/**
 * Default residency data
 * - Interns: 0.5 AT (Supervision Load)
 * - Residents: 0.25 AT (Supervision Load)
 * - Faculty: Total available "Anchors"
 */
export const DEFAULT_DATA: ResidencyData = {
  interns: 6,
  residents: 11,
  faculty: 10,
};

/**
 * Generate unit specifications based on residency data
 */
export function generateUnitSpecs(data: ResidencyData): UnitSpec[] {
  const specs: UnitSpec[] = [];

  // Faculty units (red, larger)
  for (let i = 0; i < data.faculty; i++) {
    specs.push({
      id: `F-${i}`,
      type: "FACULTY",
      color: "#ff3131",
      size: 0.24,
      label: i === 0 ? "FMIT" : "FAC",
    });
  }

  // Resident units (cyan, medium)
  for (let i = 0; i < data.residents; i++) {
    specs.push({
      id: `R-${i}`,
      type: "RESIDENT",
      color: "#00e5ff",
      size: 0.16,
    });
  }

  // Intern units (white, smaller)
  for (let i = 0; i < data.interns; i++) {
    specs.push({
      id: `I-${i}`,
      type: "INTERN",
      color: "#ffffff",
      size: 0.12,
    });
  }

  return specs;
}

/**
 * Calculate position on the "Branes" (Rings)
 * Positions units in a circular pattern with entropy-based jitter
 */
export function getUnitPosition(
  unit: UnitSpec,
  index: number,
  totalUnits: number,
  entropy: number,
  offset: number
): THREE.Vector3 {
  // Distribute units evenly around a circle
  const angle = (index / totalUnits) * Math.PI * 2;

  // Faculty closer to center, trainees on outer ring
  const radius = unit.type === "FACULTY" ? 3.5 : 5.8;

  // Entropy causes "Wave Function Jitter"
  // Use deterministic pseudo-random based on unit id for consistency
  const seed = hashCode(unit.id);
  const jitterX = seededRandom(seed) * entropy * 2.5;
  const jitterY = seededRandom(seed + 1) * entropy * 2.5;
  const jitterZ = seededRandom(seed + 2) * entropy * 1.5;

  return new THREE.Vector3(
    Math.cos(angle) * radius + jitterX,
    Math.sin(angle) * radius + jitterY,
    offset + jitterZ
  );
}

/**
 * Simple string hash function for deterministic randomness
 */
function hashCode(str: string): number {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = (hash << 5) - hash + char;
    hash = hash & hash; // Convert to 32bit integer
  }
  return Math.abs(hash);
}

/**
 * Seeded pseudo-random number generator
 * Returns value between -0.5 and 0.5
 */
function seededRandom(seed: number): number {
  const x = Math.sin(seed * 9999) * 10000;
  return (x - Math.floor(x)) - 0.5;
}

/**
 * Color palette for the visualization
 */
export const BRANE_COLORS = {
  ideal: "#00ff8a", // Green - bureaucratic ideal
  realtime: "#00e5ff", // Cyan - operational reality
  collapse: "#ff3131", // Red - systemic decay
  faculty: "#ff3131",
  resident: "#00e5ff",
  intern: "#ffffff",
  background: "#020202",
} as const;

/**
 * Brane layer configurations
 */
export const BRANE_LAYERS = {
  alpha: {
    label: "BRANE ALPHA // IDEAL",
    offset: 4,
    color: BRANE_COLORS.ideal,
  },
  beta: {
    label: "BRANE BETA // REAL-TIME",
    offset: 0,
    color: undefined, // Uses unit colors
  },
  omega: {
    label: "BRANE OMEGA // COLLAPSE",
    offset: -4,
    color: BRANE_COLORS.collapse,
  },
} as const;
