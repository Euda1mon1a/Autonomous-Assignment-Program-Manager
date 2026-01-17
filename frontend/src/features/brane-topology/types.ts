/**
 * Brane Topology Visualizer Types
 *
 * Types for the exotic 3D visualization that represents residency
 * scheduling through a brane-theory metaphor with multiple dimensional
 * layers showing Ideal, Real-time, and Collapse states.
 */

import * as THREE from "three";

export type UnitType = "FACULTY" | "RESIDENT" | "INTERN";

export interface UnitSpec {
  id: string;
  type: UnitType;
  color: string;
  size: number;
  label?: string;
  basePos?: THREE.Vector3;
}

export interface RenderedUnit extends UnitSpec {
  pos: THREE.Vector3;
}

export interface ResidencyData {
  interns: number;
  residents: number;
  faculty: number;
}

export interface BraneLayerProps {
  entropy: number;
  offset: number;
  label: string;
  colorOverride?: string;
  active?: boolean;
}

export interface InpatientAnchorProps {
  entropy: number;
}

export interface SupervisionMatrixProps {
  entropy: number;
  availableFaculty: number;
}

export interface MathPanelProps {
  availableFaculty: number;
  reqFaculty: number;
  totalAT: number;
  data: ResidencyData;
}

export interface EntropyControlsProps {
  entropy: number;
  setEntropy: (val: number) => void;
  availableFaculty: number;
  reqFaculty: number;
}

export interface BraneTopologyProps {
  /** Optional initial entropy value (0-0.95) */
  initialEntropy?: number;
  /** Override default residency data */
  data?: ResidencyData;
  /** Show/hide the math panel */
  showMathPanel?: boolean;
  /** Show/hide the entropy controls */
  showControls?: boolean;
  /** Custom class name */
  className?: string;
}
