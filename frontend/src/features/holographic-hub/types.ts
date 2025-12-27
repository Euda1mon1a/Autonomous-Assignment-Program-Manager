/**
 * Holographic Visualization Hub Types
 *
 * Far Realm Session 10: Correlation & Interaction Engine
 *
 * Defines comprehensive type system for multi-spectral correlation analysis,
 * cross-wavelength pattern detection, and interactive 3D visualization.
 */

// ============================================================================
// Core Wavelength Channel Types
// ============================================================================

/**
 * Primary wavelength channels for multi-spectral analysis
 */
export type WavelengthChannel =
  | 'quantum'      // Superposition states, entanglement, coherence
  | 'temporal'     // Time-series patterns, phase relationships
  | 'spectral'     // Frequency domain, power spectral density
  | 'evolutionary' // Population dynamics, fitness landscapes
  | 'topological'  // Network structure, connectivity patterns
  | 'thermal';     // Heat/stress distributions, burnout gradients

/**
 * Cross-wavelength correlation pair
 */
export interface WavelengthPair {
  primary: WavelengthChannel;
  secondary: WavelengthChannel;
  label: string;
  description: string;
}

/**
 * Pre-defined correlation pairs that reveal composite insights
 */
export const WAVELENGTH_PAIRS: WavelengthPair[] = [
  {
    primary: 'temporal',
    secondary: 'spectral',
    label: 'Circadian Resonance',
    description: 'Temporal patterns in frequency space reveal circadian rhythms',
  },
  {
    primary: 'quantum',
    secondary: 'evolutionary',
    label: 'Quantum Fitness',
    description: 'Superposition states influencing evolutionary trajectories',
  },
  {
    primary: 'spectral',
    secondary: 'thermal',
    label: 'Harmonic Stress',
    description: 'Frequency patterns correlated with burnout hotspots',
  },
  {
    primary: 'temporal',
    secondary: 'topological',
    label: 'Temporal Networks',
    description: 'How network structure evolves over time',
  },
  {
    primary: 'quantum',
    secondary: 'spectral',
    label: 'Quantum Harmonics',
    description: 'Quantum coherence patterns in frequency domain',
  },
  {
    primary: 'evolutionary',
    secondary: 'thermal',
    label: 'Evolution Pressure',
    description: 'Fitness landscapes shaped by stress distributions',
  },
];

// ============================================================================
// Quantum Channel Types
// ============================================================================

/**
 * Quantum state representation for schedule superposition
 */
export interface QuantumState {
  /** Unique identifier for this quantum state */
  stateId: string;
  /** Schedule configuration this state represents */
  scheduleVariantId: string;
  /** Complex amplitude (magnitude and phase) */
  amplitude: ComplexNumber;
  /** Probability of collapsing to this state */
  probability: number;
  /** Entanglement links to other states */
  entanglements: EntanglementLink[];
  /** Coherence measure (0-1) */
  coherence: number;
  /** Decoherence rate per time unit */
  decoherenceRate: number;
}

export interface ComplexNumber {
  real: number;
  imaginary: number;
  magnitude: number;
  phase: number;
}

export interface EntanglementLink {
  targetStateId: string;
  correlationStrength: number;
  bellStateType: 'phi+' | 'phi-' | 'psi+' | 'psi-';
}

export interface QuantumChannelData {
  states: QuantumState[];
  totalProbability: number;
  averageCoherence: number;
  entanglementDensity: number;
  blochSpherePoints: BlochSpherePoint[];
}

export interface BlochSpherePoint {
  stateId: string;
  theta: number;  // Polar angle (0 to π)
  phi: number;    // Azimuthal angle (0 to 2π)
  radius: number; // 0-1, represents purity
  color: string;
}

// ============================================================================
// Temporal Channel Types
// ============================================================================

/**
 * Temporal analysis data for schedule evolution
 */
export interface TemporalChannelData {
  /** Time series of schedule states */
  timeSeries: TimeSeriesPoint[];
  /** Detected phase relationships */
  phaseRelationships: PhaseRelationship[];
  /** Temporal clusters (recurring patterns) */
  clusters: TemporalCluster[];
  /** Lag correlations */
  lagCorrelations: LagCorrelation[];
}

export interface TimeSeriesPoint {
  timestamp: string;
  value: number;
  metadata: {
    personId?: string;
    constraintId?: string;
    assignmentId?: string;
  };
  derivative?: number;  // Rate of change
  acceleration?: number; // Second derivative
}

export interface PhaseRelationship {
  sourceId: string;
  targetId: string;
  phaseShift: number;  // In radians
  coherence: number;
  frequency: number;
}

export interface TemporalCluster {
  clusterId: string;
  startTime: string;
  endTime: string;
  pattern: 'daily' | 'weekly' | 'monthly' | 'block' | 'custom';
  strength: number;
  members: string[];
}

export interface LagCorrelation {
  lag: number;
  correlation: number;
  significance: number;
}

// ============================================================================
// Spectral Channel Types
// ============================================================================

/**
 * Spectral analysis data (frequency domain)
 */
export interface SpectralChannelData {
  /** Power spectral density */
  powerSpectrum: SpectralPoint[];
  /** Detected harmonics */
  harmonics: HarmonicPeak[];
  /** Cross-spectral density (if comparing signals) */
  crossSpectralDensity?: SpectralPoint[];
  /** Coherence spectrum */
  coherenceSpectrum: SpectralPoint[];
  /** Phase spectrum */
  phaseSpectrum: SpectralPoint[];
}

export interface SpectralPoint {
  frequency: number;
  power: number;
  phase?: number;
}

export interface HarmonicPeak {
  frequency: number;
  amplitude: number;
  phase: number;
  harmonic: number;  // 1 = fundamental, 2 = first harmonic, etc.
  label: string;     // e.g., "Weekly rotation cycle"
}

// ============================================================================
// Evolutionary Channel Types
// ============================================================================

/**
 * Evolutionary dynamics data
 */
export interface EvolutionaryChannelData {
  /** Population state over generations */
  populationHistory: PopulationState[];
  /** Fitness landscape */
  fitnessLandscape: FitnessPoint[];
  /** Selection pressure */
  selectionPressure: SelectionPressurePoint[];
  /** Mutation events */
  mutations: MutationEvent[];
  /** Attractor basins */
  attractors: AttractorBasin[];
}

export interface PopulationState {
  generation: number;
  populations: Record<string, number>;
  totalFitness: number;
  diversity: number;  // Shannon entropy
  dominantStrategy: string;
}

export interface FitnessPoint {
  x: number;
  y: number;
  z: number;
  fitness: number;
  strategyId: string;
}

export interface SelectionPressurePoint {
  generation: number;
  pressure: number;
  direction: 'cooperative' | 'competitive' | 'neutral';
}

export interface MutationEvent {
  generation: number;
  fromStrategy: string;
  toStrategy: string;
  probability: number;
}

export interface AttractorBasin {
  attractorId: string;
  center: { x: number; y: number; z: number };
  radius: number;
  stability: 'stable' | 'unstable' | 'limit_cycle' | 'chaotic';
  trappedPopulation: number;
}

// ============================================================================
// Correlation Engine Types
// ============================================================================

/**
 * Correlation result between two wavelength channels
 */
export interface CorrelationResult {
  /** Pair being correlated */
  pair: WavelengthPair;
  /** Overall correlation coefficient (-1 to 1) */
  correlation: number;
  /** Statistical significance (p-value) */
  significance: number;
  /** Mutual information (bits) */
  mutualInformation: number;
  /** Transfer entropy (directional causality) */
  transferEntropy: {
    primaryToSecondary: number;
    secondaryToPrimary: number;
  };
  /** Detected patterns from correlation */
  patterns: CorrelationPattern[];
  /** Visualization data for the correlation */
  visualizationData: CorrelationVisualizationData;
}

export interface CorrelationPattern {
  patternId: string;
  type: 'resonance' | 'coupling' | 'cascade' | 'feedback' | 'synchronization';
  strength: number;
  description: string;
  involvedEntities: string[];
  temporalSpan?: { start: string; end: string };
}

export interface CorrelationVisualizationData {
  /** Points for scatter plot */
  scatterPoints: Array<{
    x: number;
    y: number;
    entityId: string;
    metadata: Record<string, unknown>;
  }>;
  /** Regression line */
  regressionLine?: {
    slope: number;
    intercept: number;
    r2: number;
  };
  /** Density contours for 2D KDE */
  densityContours: Array<{
    level: number;
    path: Array<{ x: number; y: number }>;
  }>;
  /** 3D surface for cross-correlation */
  correlationSurface?: {
    xGrid: number[];
    yGrid: number[];
    zValues: number[][];
  };
}

// ============================================================================
// Cross-Wavelength Mixing Types
// ============================================================================

/**
 * Cross-wavelength mixing configuration
 */
export interface WavelengthMixConfig {
  /** Primary channel contribution (0-1) */
  primaryWeight: number;
  /** Secondary channel contribution (0-1) */
  secondaryWeight: number;
  /** Mixing mode */
  mode: 'additive' | 'multiplicative' | 'spectral' | 'phase';
  /** Color mapping */
  colorMap: WavelengthColorMap;
  /** Opacity curve */
  opacityCurve: OpacityCurve;
}

export interface WavelengthColorMap {
  channel: WavelengthChannel;
  colors: string[];
  stops: number[];
}

export interface OpacityCurve {
  type: 'linear' | 'exponential' | 'sigmoid' | 'step';
  min: number;
  max: number;
  threshold?: number;
}

/**
 * Mixed wavelength visualization data
 */
export interface MixedWavelengthData {
  /** Points in 3D space with mixed attributes */
  points: MixedPoint[];
  /** Field lines showing flow */
  fieldLines: FieldLine[];
  /** Isosurfaces at threshold values */
  isoSurfaces: IsoSurface[];
}

export interface MixedPoint {
  position: { x: number; y: number; z: number };
  primaryValue: number;
  secondaryValue: number;
  mixedValue: number;
  color: string;
  opacity: number;
  entityId: string;
}

export interface FieldLine {
  points: Array<{ x: number; y: number; z: number }>;
  strength: number;
  direction: 'forward' | 'backward' | 'bidirectional';
}

export interface IsoSurface {
  level: number;
  vertices: Float32Array;
  normals: Float32Array;
  indices: Uint32Array;
  color: string;
  opacity: number;
}

// ============================================================================
// Interactive Selection Types
// ============================================================================

/**
 * Selection state for interactive exploration
 */
export interface SelectionState {
  /** Currently selected residents */
  selectedResidents: string[];
  /** Currently selected constraints */
  selectedConstraints: string[];
  /** Currently selected time range */
  selectedTimeRange: { start: string; end: string } | null;
  /** Currently selected wavelength channels */
  activeChannels: WavelengthChannel[];
  /** Highlight mode */
  highlightMode: 'dependencies' | 'conflicts' | 'correlations' | 'none';
  /** Selection history for undo */
  history: SelectionHistoryEntry[];
}

export interface SelectionHistoryEntry {
  timestamp: string;
  type: 'add' | 'remove' | 'clear' | 'set';
  category: 'resident' | 'constraint' | 'timeRange' | 'channel';
  values: string[];
}

/**
 * Dependency graph for selected entities
 */
export interface DependencyGraph {
  nodes: DependencyNode[];
  edges: DependencyEdge[];
  clusters: DependencyCluster[];
}

export interface DependencyNode {
  id: string;
  type: 'resident' | 'constraint' | 'assignment' | 'rotation';
  label: string;
  position: { x: number; y: number; z: number };
  importance: number;  // PageRank or centrality score
  isSelected: boolean;
  wavelengthValues: Partial<Record<WavelengthChannel, number>>;
}

export interface DependencyEdge {
  source: string;
  target: string;
  weight: number;
  type: 'constraint' | 'assignment' | 'correlation' | 'conflict';
  bidirectional: boolean;
  metadata?: Record<string, unknown>;
}

export interface DependencyCluster {
  clusterId: string;
  nodeIds: string[];
  centroid: { x: number; y: number; z: number };
  cohesion: number;
  label: string;
}

// ============================================================================
// Animation Types
// ============================================================================

/**
 * Animation configuration for schedule evolution
 */
export interface AnimationConfig {
  /** Playback state */
  isPlaying: boolean;
  /** Current frame index */
  currentFrame: number;
  /** Total frames */
  totalFrames: number;
  /** Playback speed (frames per second) */
  fps: number;
  /** Loop mode */
  loopMode: 'none' | 'loop' | 'pingpong';
  /** Time range for animation */
  timeRange: { start: string; end: string };
  /** Easing function */
  easing: 'linear' | 'easeIn' | 'easeOut' | 'easeInOut' | 'spring';
  /** Interpolation mode for values */
  interpolation: 'linear' | 'spline' | 'step';
}

/**
 * Animation keyframe
 */
export interface AnimationKeyframe {
  frameIndex: number;
  timestamp: string;
  state: ScheduleAnimationState;
  transitions: FrameTransition[];
}

export interface ScheduleAnimationState {
  assignments: AnimatedAssignment[];
  violations: string[];
  coverageScore: number;
  wavelengthSnapshots: Partial<Record<WavelengthChannel, number>>;
}

export interface AnimatedAssignment {
  assignmentId: string;
  personId: string;
  rotationId: string;
  position: { x: number; y: number; z: number };
  color: string;
  scale: number;
}

export interface FrameTransition {
  type: 'move' | 'appear' | 'disappear' | 'morph' | 'pulse';
  entityId: string;
  from: Partial<AnimatedAssignment>;
  to: Partial<AnimatedAssignment>;
  duration: number;
}

// ============================================================================
// Looking Glass Display Types
// ============================================================================

/**
 * Looking Glass holographic display configuration
 */
export interface LookingGlassConfig {
  /** Display device type */
  deviceType: 'portrait' | 'landscape' | '8k' | 'go' | 'unknown';
  /** Calibration data */
  calibration: LookingGlassCalibration;
  /** View cone angle in degrees */
  viewCone: number;
  /** Number of views (quilt columns x rows) */
  quiltSettings: QuiltSettings;
  /** 3D rendering parameters */
  rendering: LookingGlassRendering;
}

export interface LookingGlassCalibration {
  pitch: number;
  slope: number;
  center: number;
  viewCone: number;
  invView: number;
  displayAspect: number;
  numViews: number;
}

export interface QuiltSettings {
  columns: number;
  rows: number;
  totalViews: number;
  viewWidth: number;
  viewHeight: number;
  quiltWidth: number;
  quiltHeight: number;
}

export interface LookingGlassRendering {
  /** Camera field of view */
  fov: number;
  /** Camera convergence distance */
  convergenceDistance: number;
  /** Interocular distance for stereo */
  interocularDistance: number;
  /** Focus plane distance */
  focusDistance: number;
  /** Depth compression factor */
  depthCompression: number;
}

/**
 * Holographic scene configuration
 */
export interface HolographicScene {
  /** Scene identifier */
  sceneId: string;
  /** Camera configuration */
  camera: HolographicCamera;
  /** Light sources */
  lights: HolographicLight[];
  /** Scene objects */
  objects: HolographicObject[];
  /** Post-processing effects */
  effects: HolographicEffect[];
  /** Environment map */
  environment?: string;
}

export interface HolographicCamera {
  position: { x: number; y: number; z: number };
  target: { x: number; y: number; z: number };
  up: { x: number; y: number; z: number };
  fov: number;
  near: number;
  far: number;
}

export interface HolographicLight {
  type: 'ambient' | 'directional' | 'point' | 'spot';
  color: string;
  intensity: number;
  position?: { x: number; y: number; z: number };
  target?: { x: number; y: number; z: number };
  castShadow: boolean;
}

export interface HolographicObject {
  objectId: string;
  geometry: 'sphere' | 'box' | 'cylinder' | 'torus' | 'custom';
  position: { x: number; y: number; z: number };
  rotation: { x: number; y: number; z: number };
  scale: { x: number; y: number; z: number };
  material: HolographicMaterial;
  customGeometry?: Float32Array;
}

export interface HolographicMaterial {
  type: 'standard' | 'physical' | 'holographic' | 'wireframe';
  color: string;
  opacity: number;
  metalness?: number;
  roughness?: number;
  emissive?: string;
  emissiveIntensity?: number;
  hologramColor?: string;
  scanlineIntensity?: number;
  fresnelPower?: number;
}

export interface HolographicEffect {
  type: 'bloom' | 'dof' | 'chromatic' | 'scanlines' | 'glitch';
  enabled: boolean;
  intensity: number;
  parameters: Record<string, number>;
}

// ============================================================================
// Spatial Audio Types
// ============================================================================

/**
 * Spatial audio configuration for constraint violation sonification
 */
export interface SpatialAudioConfig {
  /** Master volume (0-1) */
  masterVolume: number;
  /** Audio context state */
  isEnabled: boolean;
  /** Listener position (usually camera position) */
  listenerPosition: { x: number; y: number; z: number };
  /** Listener orientation */
  listenerOrientation: {
    forward: { x: number; y: number; z: number };
    up: { x: number; y: number; z: number };
  };
  /** Distance model */
  distanceModel: 'linear' | 'inverse' | 'exponential';
  /** Reference distance */
  refDistance: number;
  /** Maximum distance */
  maxDistance: number;
  /** Rolloff factor */
  rolloffFactor: number;
}

/**
 * Audio source for a constraint violation
 */
export interface ViolationAudioSource {
  /** Unique source identifier */
  sourceId: string;
  /** Violation type */
  violationType: ViolationType;
  /** 3D position */
  position: { x: number; y: number; z: number };
  /** Violation severity (0-1) */
  severity: number;
  /** Panning (stereo position) */
  panning: number;
  /** Audio parameters */
  audio: AudioParameters;
  /** Is currently active */
  isActive: boolean;
}

export type ViolationType =
  | 'acgme_hours'
  | 'acgme_rest'
  | 'supervision'
  | 'coverage_gap'
  | 'conflict'
  | 'credential_missing'
  | 'workload_imbalance';

export interface AudioParameters {
  /** Base frequency in Hz */
  frequency: number;
  /** Waveform type */
  waveform: 'sine' | 'square' | 'triangle' | 'sawtooth' | 'noise';
  /** Volume (0-1) */
  volume: number;
  /** Attack time in seconds */
  attack: number;
  /** Decay time in seconds */
  decay: number;
  /** Sustain level (0-1) */
  sustain: number;
  /** Release time in seconds */
  release: number;
  /** Modulation frequency (for tremolo/vibrato) */
  modFrequency?: number;
  /** Modulation depth */
  modDepth?: number;
}

/**
 * Audio theme mapping violation types to sounds
 */
export const VIOLATION_AUDIO_THEMES: Record<ViolationType, Partial<AudioParameters>> = {
  acgme_hours: {
    frequency: 220,  // A3 - low warning tone
    waveform: 'sine',
    attack: 0.1,
    decay: 0.3,
    sustain: 0.6,
    release: 0.5,
  },
  acgme_rest: {
    frequency: 330,  // E4 - mid warning
    waveform: 'triangle',
    attack: 0.05,
    decay: 0.2,
    sustain: 0.4,
    release: 0.3,
  },
  supervision: {
    frequency: 440,  // A4 - attention
    waveform: 'square',
    attack: 0.02,
    decay: 0.1,
    sustain: 0.3,
    release: 0.2,
  },
  coverage_gap: {
    frequency: 523,  // C5 - high alert
    waveform: 'sawtooth',
    attack: 0.01,
    decay: 0.15,
    sustain: 0.5,
    release: 0.4,
  },
  conflict: {
    frequency: 587,  // D5 - clash
    waveform: 'square',
    attack: 0.01,
    decay: 0.05,
    sustain: 0.2,
    release: 0.1,
    modFrequency: 8,
    modDepth: 0.3,
  },
  credential_missing: {
    frequency: 392,  // G4 - moderate concern
    waveform: 'triangle',
    attack: 0.2,
    decay: 0.4,
    sustain: 0.7,
    release: 0.6,
  },
  workload_imbalance: {
    frequency: 349,  // F4 - fatigue tone
    waveform: 'sine',
    attack: 0.3,
    decay: 0.5,
    sustain: 0.8,
    release: 0.8,
    modFrequency: 2,
    modDepth: 0.1,
  },
};

// ============================================================================
// Constraint Coupling Types
// ============================================================================

/**
 * Constraint coupling visualization data
 */
export interface ConstraintCouplingData {
  /** All constraints in the system */
  constraints: ConstraintNode[];
  /** Coupling edges between constraints */
  couplings: ConstraintCoupling[];
  /** Coupling clusters */
  clusters: CouplingCluster[];
  /** Force field data for visualization */
  forceField: ForceFieldData;
}

export interface ConstraintNode {
  constraintId: string;
  name: string;
  type: 'hard' | 'soft';
  category: 'acgme' | 'coverage' | 'preference' | 'institutional' | 'personal';
  weight: number;
  position: { x: number; y: number; z: number };
  violations: number;
  satisfactionRate: number;
}

export interface ConstraintCoupling {
  source: string;
  target: string;
  strength: number;  // -1 (competing) to 1 (reinforcing)
  type: 'reinforcing' | 'competing' | 'neutral';
  frequency: number;  // How often they interact
  impact: number;     // Magnitude of interaction effect
}

export interface CouplingCluster {
  clusterId: string;
  constraintIds: string[];
  centroid: { x: number; y: number; z: number };
  internalCohesion: number;
  externalCoupling: number;
  dominantType: 'reinforcing' | 'competing' | 'mixed';
}

export interface ForceFieldData {
  /** Grid resolution */
  resolution: { x: number; y: number; z: number };
  /** Force vectors at each grid point */
  vectors: Float32Array;
  /** Potential energy at each grid point */
  potential: Float32Array;
  /** Streamlines through the field */
  streamlines: Array<Array<{ x: number; y: number; z: number }>>;
}

// ============================================================================
// Export Types
// ============================================================================

/**
 * Export configuration for visualization states
 */
export interface ExportConfig {
  /** Export format */
  format: ExportFormat;
  /** What to include */
  include: ExportInclusions;
  /** Quality settings */
  quality: ExportQuality;
  /** Metadata to embed */
  metadata: ExportMetadata;
}

export type ExportFormat =
  | 'png'
  | 'svg'
  | 'webm'
  | 'gif'
  | 'gltf'
  | 'usdz'
  | 'json'
  | 'csv';

export interface ExportInclusions {
  /** Include current view snapshot */
  currentView: boolean;
  /** Include animation sequence */
  animation: boolean;
  /** Include camera path */
  cameraPath: boolean;
  /** Include selection state */
  selectionState: boolean;
  /** Include wavelength data */
  wavelengthData: WavelengthChannel[];
  /** Include correlation results */
  correlations: boolean;
  /** Include audio markers */
  audioMarkers: boolean;
}

export interface ExportQuality {
  /** Image resolution */
  resolution: { width: number; height: number };
  /** Animation FPS */
  fps: number;
  /** Compression level (0-1, 0=no compression) */
  compression: number;
  /** Anti-aliasing samples */
  antiAliasing: 1 | 2 | 4 | 8;
  /** Include shadows */
  shadows: boolean;
  /** Include reflections */
  reflections: boolean;
}

export interface ExportMetadata {
  title: string;
  description: string;
  author: string;
  timestamp: string;
  version: string;
  tags: string[];
  customFields: Record<string, string>;
}

/**
 * Exported visualization state
 */
export interface ExportedVisualizationState {
  /** Unique export ID */
  exportId: string;
  /** Export timestamp */
  exportedAt: string;
  /** Configuration used */
  config: ExportConfig;
  /** Scene state */
  scene: HolographicScene;
  /** Animation state */
  animation?: AnimationConfig;
  /** Selection state */
  selection: SelectionState;
  /** Active correlations */
  correlations: CorrelationResult[];
  /** Wavelength data snapshots */
  wavelengthSnapshots: Partial<Record<WavelengthChannel, unknown>>;
  /** File references */
  files: Array<{
    type: ExportFormat;
    path: string;
    size: number;
  }>;
}

// ============================================================================
// Guided Tour Types
// ============================================================================

/**
 * Guided tour configuration
 */
export interface GuidedTour {
  /** Unique tour identifier */
  tourId: string;
  /** Display name */
  name: string;
  /** Description */
  description: string;
  /** Estimated duration in seconds */
  duration: number;
  /** Difficulty/complexity level */
  level: 'beginner' | 'intermediate' | 'advanced';
  /** Tour waypoints */
  waypoints: TourWaypoint[];
  /** Audio narration configuration */
  narration?: TourNarration;
  /** Tags for categorization */
  tags: string[];
}

export interface TourWaypoint {
  /** Waypoint index */
  index: number;
  /** Camera position */
  camera: HolographicCamera;
  /** Duration at this waypoint in seconds */
  dwellTime: number;
  /** Transition to this waypoint */
  transition: WaypointTransition;
  /** Highlight these entities */
  highlights: string[];
  /** Activate these wavelength channels */
  activeChannels: WavelengthChannel[];
  /** Annotation to display */
  annotation: TourAnnotation;
  /** Actions to perform */
  actions: TourAction[];
}

export interface WaypointTransition {
  /** Duration of camera movement in seconds */
  duration: number;
  /** Easing function */
  easing: 'linear' | 'easeIn' | 'easeOut' | 'easeInOut' | 'spring';
  /** Path type */
  pathType: 'direct' | 'arc' | 'spline';
  /** Control points for spline */
  controlPoints?: Array<{ x: number; y: number; z: number }>;
}

export interface TourAnnotation {
  /** Title text */
  title: string;
  /** Body text */
  body: string;
  /** Position on screen (0-1 normalized) */
  position: { x: number; y: number };
  /** Pointer to 3D position (optional) */
  pointer?: { x: number; y: number; z: number };
  /** Show duration in seconds */
  duration: number;
}

export interface TourAction {
  type: 'select' | 'highlight' | 'filter' | 'animate' | 'audio' | 'correlate';
  parameters: Record<string, unknown>;
  timing: 'enter' | 'during' | 'exit';
}

export interface TourNarration {
  /** Audio file URL */
  audioUrl?: string;
  /** Text-to-speech content */
  ttsContent?: string;
  /** Timing markers */
  markers: Array<{
    time: number;
    waypointIndex: number;
  }>;
}

/**
 * Pre-defined guided tours highlighting key insights
 */
export const BUILT_IN_TOURS: Omit<GuidedTour, 'waypoints'>[] = [
  {
    tourId: 'intro-holographic',
    name: 'Introduction to Holographic Visualization',
    description: 'Learn the basics of navigating and interacting with the 3D schedule visualization',
    duration: 120,
    level: 'beginner',
    tags: ['introduction', 'navigation', 'basics'],
  },
  {
    tourId: 'quantum-superposition',
    name: 'Quantum Schedule Superposition',
    description: 'Explore how schedule alternatives exist in quantum superposition until observed',
    duration: 180,
    level: 'advanced',
    tags: ['quantum', 'superposition', 'alternatives'],
  },
  {
    tourId: 'circadian-resonance',
    name: 'Circadian Resonance Patterns',
    description: 'Discover how temporal and spectral channels reveal circadian work patterns',
    duration: 150,
    level: 'intermediate',
    tags: ['temporal', 'spectral', 'circadian', 'correlation'],
  },
  {
    tourId: 'constraint-coupling',
    name: 'Constraint Coupling Forces',
    description: 'Visualize how constraints interact and influence each other in 3D force fields',
    duration: 200,
    level: 'advanced',
    tags: ['constraints', '3D', 'forces', 'coupling'],
  },
  {
    tourId: 'evolution-dynamics',
    name: 'Evolutionary Strategy Dynamics',
    description: 'Watch scheduling strategies evolve over generations in the fitness landscape',
    duration: 180,
    level: 'intermediate',
    tags: ['evolution', 'game-theory', 'fitness'],
  },
  {
    tourId: 'burnout-detection',
    name: 'Early Burnout Detection',
    description: 'Learn how thermal wavelength patterns reveal burnout risk before symptoms appear',
    duration: 160,
    level: 'intermediate',
    tags: ['thermal', 'burnout', 'wellness', 'prediction'],
  },
];

// ============================================================================
// Hub State Types
// ============================================================================

/**
 * Complete state of the holographic hub
 */
export interface HolographicHubState {
  /** Active wavelength channels */
  activeChannels: WavelengthChannel[];
  /** Current selection */
  selection: SelectionState;
  /** Animation state */
  animation: AnimationConfig;
  /** Looking Glass configuration */
  lookingGlass: LookingGlassConfig | null;
  /** Spatial audio configuration */
  spatialAudio: SpatialAudioConfig;
  /** Active correlations */
  activeCorrelations: CorrelationResult[];
  /** Current tour (if any) */
  activeTour: GuidedTour | null;
  /** Tour playback position */
  tourPosition: number;
  /** View mode */
  viewMode: HubViewMode;
  /** Rendering quality */
  quality: RenderingQuality;
  /** UI panel states */
  panels: PanelStates;
}

export type HubViewMode = 'explore' | 'correlate' | 'animate' | 'tour' | 'export';

export type RenderingQuality = 'low' | 'medium' | 'high' | 'ultra';

export interface PanelStates {
  wavelengthPanel: boolean;
  selectionPanel: boolean;
  correlationPanel: boolean;
  animationPanel: boolean;
  tourPanel: boolean;
  audioPanel: boolean;
  exportPanel: boolean;
}

// ============================================================================
// Color Constants
// ============================================================================

/**
 * Wavelength channel colors
 */
export const WAVELENGTH_COLORS: Record<WavelengthChannel, string> = {
  quantum: '#8b5cf6',     // Purple - quantum realm
  temporal: '#3b82f6',    // Blue - time
  spectral: '#f59e0b',    // Amber - frequency
  evolutionary: '#22c55e', // Green - life/growth
  topological: '#06b6d4', // Cyan - structure
  thermal: '#ef4444',     // Red - heat
};

/**
 * Wavelength channel labels
 */
export const WAVELENGTH_LABELS: Record<WavelengthChannel, string> = {
  quantum: 'Quantum',
  temporal: 'Temporal',
  spectral: 'Spectral',
  evolutionary: 'Evolutionary',
  topological: 'Topological',
  thermal: 'Thermal',
};

/**
 * Constraint category colors
 */
export const CONSTRAINT_CATEGORY_COLORS: Record<string, string> = {
  acgme: '#ef4444',        // Red - regulatory
  coverage: '#3b82f6',     // Blue - operational
  preference: '#22c55e',   // Green - personal
  institutional: '#f59e0b', // Amber - organizational
  personal: '#8b5cf6',     // Purple - individual
};

/**
 * Coupling type colors
 */
export const COUPLING_TYPE_COLORS: Record<string, string> = {
  reinforcing: '#22c55e',  // Green - synergy
  competing: '#ef4444',    // Red - conflict
  neutral: '#6b7280',      // Gray - independent
};
