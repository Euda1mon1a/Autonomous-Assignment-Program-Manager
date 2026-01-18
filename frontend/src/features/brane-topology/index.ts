/**
 * Brane Topology Visualizer
 *
 * Exotic 3D visualization of residency scheduling using brane-theory metaphor.
 */

export { BraneTopologyVisualizer } from "./BraneTopologyVisualizer";
export { default } from "./BraneTopologyVisualizer";

// Types
export type {
  BraneTopologyProps,
  ResidencyData,
  UnitType,
  UnitSpec,
} from "./types";

// Constants
export { DEFAULT_DATA, BRANE_COLORS, BRANE_LAYERS } from "./constants";

// Components (for advanced usage)
export { InpatientAnchor } from "./components/InpatientAnchor";
export { BraneLayer } from "./components/BraneLayer";
export { SupervisionMatrix } from "./components/SupervisionMatrix";
export { MathPanel } from "./components/MathPanel";
export { EntropyControls } from "./components/EntropyControls";
