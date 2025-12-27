/**
 * Holographic Visualization Hub
 *
 * A multi-spectral constraint manifold renderer that integrates data
 * from all Far Realm analysis sessions (1-8) into a unified 3D view.
 *
 * ## Features
 *
 * - **N-dimensional projection**: PCA, UMAP, t-SNE for dimensionality reduction
 * - **Multi-spectral layers**: Toggle visibility of different analytical dimensions
 * - **Constraint type filtering**: Show/hide by ACGME, fairness, fatigue, etc.
 * - **Real-time updates**: WebSocket/SSE support for live data streaming
 * - **Interactive 3D navigation**: Orbit, zoom, pan with mouse controls
 * - **WebXR foundation**: Basic VR/AR support for immersive viewing
 *
 * ## Spectral Layers (from Far Realm Sessions)
 *
 * 1. **Quantum**: Probabilistic constraint states (Session 1)
 * 2. **Temporal**: Time-evolving schedule dynamics (Session 2)
 * 3. **Topological**: Structural constraint relationships (Session 3)
 * 4. **Spectral**: Frequency-domain patterns (Session 4)
 * 5. **Evolutionary**: Game-theoretic strategy evolution (Session 5)
 * 6. **Gravitational**: Constraint attraction/repulsion fields (Session 6)
 * 7. **Phase**: Schedule state transitions (Session 7)
 * 8. **Thermodynamic**: Energy/entropy of schedules (Session 8)
 *
 * ## Usage
 *
 * ```tsx
 * import { HolographicManifold } from '@/features/holographic-hub';
 *
 * function ConstraintVisualization() {
 *   return (
 *     <HolographicManifold
 *       startDate={new Date()}
 *       endDate={new Date(Date.now() + 14 * 24 * 60 * 60 * 1000)}
 *       useMockData={true}
 *       showControls={true}
 *       showLegend={true}
 *       onPointClick={(point) => console.log('Selected:', point)}
 *     />
 *   );
 * }
 * ```
 *
 * ## Architecture
 *
 * ```
 * Data Pipeline:
 * ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
 * │ Session 1-8 │ -> │  Normalize  │ -> │   Project   │
 * │   Exports   │    │   & Merge   │    │  (PCA/UMAP) │
 * └─────────────┘    └─────────────┘    └─────────────┘
 *                                              │
 *                                              v
 *                    ┌─────────────┐    ┌─────────────┐
 *                    │   Render    │ <- │  Colorize   │
 *                    │   Canvas    │    │  & Style    │
 *                    └─────────────┘    └─────────────┘
 * ```
 *
 * @module holographic-hub
 */

// Types
export * from "./types";

// Data Pipeline
export {
  projectPCA,
  projectUMAP,
  projectTSNE,
  normalizeSessionData,
  mergeSessionData,
  projectToManifold,
  buildHolographicDataset,
  generateMockSessionData,
  generateMockHolographicData,
} from "./data-pipeline";

// Shaders
export {
  constraintPointVertexShader,
  constraintPointFragmentShader,
  tensionLineVertexShader,
  tensionLineFragmentShader,
  manifoldGridVertexShader,
  manifoldGridFragmentShader,
  layerAuraVertexShader,
  layerAuraFragmentShader,
  createConstraintPointUniforms,
  createTensionLineUniforms,
  createManifoldGridUniforms,
  createLayerAuraUniforms,
} from "./shaders";

// Hooks
export {
  useHolographicData,
  useHolographicState,
  useFilteredManifoldPoints,
  useAnimationFrame,
  useWebXR,
  useRealTimeUpdates,
  usePointInteraction,
} from "./hooks";

// Components
export { HolographicManifold } from "./HolographicManifold";
export { LayerControlPanel } from "./LayerControlPanel";

// Default export
export { default } from "./HolographicManifold";
