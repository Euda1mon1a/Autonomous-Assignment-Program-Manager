/**
 * Holographic Visualization Hub Types
 *
 * Type definitions for the multi-spectral constraint manifold renderer.
 * This hub receives data from all Far Realm sessions (1-8) and projects
 * them into a unified 3D constraint space for simultaneous observation.
 *
 * The "holographic" metaphor:
 * - Different wavelengths = different constraint types (ACGME, fairness, fatigue)
 * - Spectral layers = different analytical dimensions (quantum, temporal, evolutionary)
 * - Manifold projection = dimensionality reduction of N-dimensional constraint space
 */

// ============================================================================
// Core Constraint Types
// ============================================================================

/**
 * Constraint categories with associated visualization colors
 */
export type ConstraintType =
  | "acgme" // Red - Regulatory compliance (80-hour rule, supervision ratios)
  | "fairness" // Blue - Workload equity and distribution
  | "fatigue" // Yellow - Burnout risk and work intensity
  | "temporal" // Cyan - Time-based conflicts and sequencing
  | "preference" // Green - Individual preferences and requests
  | "coverage" // Orange - Staffing requirements and gaps
  | "skill" // Purple - Credential and qualification constraints
  | "custom"; // White - User-defined constraints

/**
 * Spectral wavelength layers from different analytical sessions
 */
export type SpectralLayer =
  | "quantum" // Session 1: Probabilistic constraint states
  | "temporal" // Session 2: Time-evolving schedule dynamics
  | "topological" // Session 3: Structural constraint relationships
  | "spectral" // Session 4: Frequency-domain patterns
  | "evolutionary" // Session 5: Game-theoretic strategy evolution
  | "gravitational" // Session 6: Constraint attraction/repulsion fields
  | "phase" // Session 7: Schedule state transitions
  | "thermodynamic"; // Session 8: Energy/entropy of schedules

// ============================================================================
// Constraint Data Point
// ============================================================================

/**
 * A single constraint data point in N-dimensional space
 * Before dimensionality reduction
 */
export interface ConstraintDataPoint {
  id: string;
  type: ConstraintType;
  layer: SpectralLayer;

  /** Original N-dimensional coordinates (before projection) */
  dimensions: number[];

  /** Constraint violation severity (0 = satisfied, 1 = critical violation) */
  severity: number;

  /** Constraint weight in the optimization objective */
  weight: number;

  /** Entities involved in this constraint */
  entities: {
    personIds?: string[];
    blockIds?: string[];
    activityIds?: string[];
  };

  /** Human-readable constraint description */
  label: string;

  /** Additional metadata from source session */
  metadata: Record<string, unknown>;

  /** Timestamp when this data was generated */
  timestamp: string;
}

// ============================================================================
// Projected Manifold Point
// ============================================================================

/**
 * A constraint point after dimensionality reduction to 3D
 */
export interface ManifoldPoint {
  id: string;
  constraintId: string;
  type: ConstraintType;
  layer: SpectralLayer;

  /** 3D projected coordinates */
  position: {
    x: number;
    y: number;
    z: number;
  };

  /** Projection confidence (0-1, how well this point represents original data) */
  projectionConfidence: number;

  /** Visual properties */
  visual: {
    color: [number, number, number]; // RGB normalized 0-1
    opacity: number;
    size: number;
    glowIntensity: number;
  };

  /** Constraint status */
  status: {
    isSatisfied: boolean;
    isViolated: boolean;
    isCritical: boolean;
    tension: number; // 0-1, how "stretched" this constraint is
  };

  /** Original severity from source data */
  severity: number;

  /** Label for hover tooltip */
  label: string;
}

// ============================================================================
// Data Pipeline Types
// ============================================================================

/**
 * Standardized format for session data exports
 * All sessions (1-8) must export data in this format
 */
export interface SessionDataExport {
  sessionId: number;
  sessionName: SpectralLayer;
  timestamp: string;
  version: string;

  /** Constraint data points from this session */
  constraints: ConstraintDataPoint[];

  /** Session-specific aggregated metrics */
  metrics: {
    totalConstraints: number;
    satisfiedCount: number;
    violatedCount: number;
    criticalCount: number;
    averageSeverity: number;
    averageTension: number;
  };

  /** Correlation data with other sessions (if available) */
  correlations?: {
    targetSession: SpectralLayer;
    correlationCoefficient: number;
    sharedConstraintIds: string[];
  }[];
}

/**
 * Combined data from all sessions for holographic rendering
 */
export interface HolographicDataset {
  timestamp: string;
  sessions: SessionDataExport[];

  /** All constraints merged and deduplicated */
  allConstraints: ConstraintDataPoint[];

  /** Projected manifold points (after dimensionality reduction) */
  manifoldPoints: ManifoldPoint[];

  /** Global statistics across all sessions */
  globalStats: {
    totalUniqueConstraints: number;
    constraintsByType: Record<ConstraintType, number>;
    constraintsByLayer: Record<SpectralLayer, number>;
    overallHealth: number; // 0-1 schedule health score
    projectionMethod: ProjectionMethod;
    projectionQuality: number; // 0-1 preservation of distances
  };
}

// ============================================================================
// Projection Configuration
// ============================================================================

export type ProjectionMethod = "pca" | "umap" | "tsne" | "custom";

export interface ProjectionConfig {
  method: ProjectionMethod;

  /** PCA-specific config */
  pca?: {
    nComponents: 3;
    whiten: boolean;
  };

  /** UMAP-specific config */
  umap?: {
    nNeighbors: number;
    minDist: number;
    metric: "euclidean" | "manhattan" | "cosine";
  };

  /** t-SNE-specific config */
  tsne?: {
    perplexity: number;
    learningRate: number;
    nIterations: number;
  };
}

// ============================================================================
// Visualization State
// ============================================================================

/**
 * Layer visibility state for multi-spectral viewing
 */
export interface LayerVisibility {
  quantum: boolean;
  temporal: boolean;
  topological: boolean;
  spectral: boolean;
  evolutionary: boolean;
  gravitational: boolean;
  phase: boolean;
  thermodynamic: boolean;
}

/**
 * Constraint type visibility
 */
export interface ConstraintVisibility {
  acgme: boolean;
  fairness: boolean;
  fatigue: boolean;
  temporal: boolean;
  preference: boolean;
  coverage: boolean;
  skill: boolean;
  custom: boolean;
}

/**
 * Camera state for 3D navigation
 */
export interface CameraState {
  position: [number, number, number];
  target: [number, number, number];
  fov: number;
  near: number;
  far: number;
}

/**
 * Complete visualization state
 */
export interface HolographicState {
  layerVisibility: LayerVisibility;
  constraintVisibility: ConstraintVisibility;
  camera: CameraState;

  /** Currently selected/hovered point */
  selectedPointId: string | null;
  hoveredPointId: string | null;

  /** Animation state */
  isAnimating: boolean;
  animationSpeed: number;

  /** Projection configuration */
  projection: ProjectionConfig;

  /** Rendering quality (affects performance) */
  quality: "low" | "medium" | "high" | "ultra";

  /** WebXR state */
  xrEnabled: boolean;
  xrSession: XRSession | null;
}

// ============================================================================
// Color Palette
// ============================================================================

/**
 * Constraint type color mapping
 * Based on visibility/accessibility guidelines
 */
export const CONSTRAINT_COLORS: Record<ConstraintType, [number, number, number]> = {
  acgme: [0.9, 0.2, 0.2], // Red - Critical regulatory
  fairness: [0.2, 0.5, 0.9], // Blue - Equity
  fatigue: [0.95, 0.8, 0.2], // Yellow - Warning/fatigue
  temporal: [0.2, 0.8, 0.9], // Cyan - Time
  preference: [0.3, 0.8, 0.4], // Green - Preferences
  coverage: [0.95, 0.5, 0.2], // Orange - Coverage
  skill: [0.6, 0.3, 0.8], // Purple - Skills/credentials
  custom: [0.8, 0.8, 0.8], // White/gray - Custom
};

/**
 * Spectral layer color modifiers (applied as glow/tint)
 */
export const LAYER_COLORS: Record<SpectralLayer, [number, number, number]> = {
  quantum: [0.5, 0.0, 1.0], // Deep purple - quantum uncertainty
  temporal: [0.0, 0.5, 1.0], // Blue - time flow
  topological: [0.0, 1.0, 0.5], // Teal - structure
  spectral: [1.0, 1.0, 0.0], // Yellow - frequency
  evolutionary: [1.0, 0.5, 0.0], // Orange - evolution
  gravitational: [0.5, 0.5, 0.5], // Gray - gravity wells
  phase: [1.0, 0.0, 0.5], // Magenta - phase transitions
  thermodynamic: [1.0, 0.2, 0.2], // Red-orange - energy/heat
};

// ============================================================================
// Event Types
// ============================================================================

export interface HolographicEvent {
  type:
    | "point_selected"
    | "point_hovered"
    | "layer_toggled"
    | "projection_changed"
    | "data_updated"
    | "xr_session_started"
    | "xr_session_ended";
  payload: unknown;
  timestamp: number;
}

export type HolographicEventHandler = (event: HolographicEvent) => void;

// ============================================================================
// API Types
// ============================================================================

export interface HolographicDataRequest {
  /** Date range for constraint data */
  startDate: string;
  endDate: string;

  /** Which sessions to include */
  layers?: SpectralLayer[];

  /** Which constraint types to include */
  constraintTypes?: ConstraintType[];

  /** Projection method to use */
  projectionMethod?: ProjectionMethod;

  /** Filter by severity threshold */
  minSeverity?: number;

  /** Include satisfied constraints */
  includeSatisfied?: boolean;
}

export interface HolographicDataResponse {
  success: boolean;
  data?: HolographicDataset;
  error?: string;
  timestamp: string;
}
