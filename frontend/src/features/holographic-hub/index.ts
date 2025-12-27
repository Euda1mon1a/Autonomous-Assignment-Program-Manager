/**
 * Holographic Visualization Hub
 *
 * Far Realm Session 10: Correlation & Interaction Engine
 *
 * A complete multi-spectral visualization system for schedule analysis,
 * combining quantum, temporal, spectral, and evolutionary data channels.
 */

// Main component
export { HolographicHub } from './HolographicHub';
export { default } from './HolographicHub';

// Sub-components
export { CorrelationVisualization } from './CorrelationVisualization';
export { WavelengthMixer } from './WavelengthMixer';
export { InteractiveSelector } from './InteractiveSelector';
export { ScheduleAnimator } from './ScheduleAnimator';
export { LookingGlassRenderer } from './LookingGlassRenderer';
export { SpatialAudioPanel } from './SpatialAudioPanel';
export { ConstraintCouplingView } from './ConstraintCouplingView';
export { ExportPanel } from './ExportPanel';
export { GuidedTourPlayer } from './GuidedTourPlayer';

// Hooks
export {
  useHolographicHub,
  useCorrelationEngine,
  useWavelengthCorrelation,
  useSelectionState,
  useDependencyGraph,
  useAnimationController,
  useSpatialAudio,
  useConstraintCoupling,
  useGuidedTours,
  useTourPlayer,
  useVisualizationExport,
  useQuantumChannelData,
  useTemporalChannelData,
  useSpectralChannelData,
  useEvolutionaryChannelData,
  holographicQueryKeys,
} from './hooks';

// Correlation engine
export {
  CorrelationEngine,
  correlationEngine,
  pearsonCorrelation,
  spearmanCorrelation,
  mutualInformation,
  transferEntropy,
  crossCorrelation,
  coherenceSpectrum,
  detectResonance,
  detectCoupling,
  detectCascade,
  detectFeedback,
  detectSynchronization,
  detectCircadianResonance,
  detectQuantumFitness,
  detectHarmonicStress,
  computeWavelengthCorrelation,
} from './correlation-engine';

// Types
export type {
  // Wavelength types
  WavelengthChannel,
  WavelengthPair,
  WavelengthMixConfig,
  WavelengthColorMap,
  OpacityCurve,
  MixedWavelengthData,
  MixedPoint,
  FieldLine,
  IsoSurface,

  // Quantum channel
  QuantumState,
  ComplexNumber,
  EntanglementLink,
  QuantumChannelData,
  BlochSpherePoint,

  // Temporal channel
  TemporalChannelData,
  TimeSeriesPoint,
  PhaseRelationship,
  TemporalCluster,
  LagCorrelation,

  // Spectral channel
  SpectralChannelData,
  SpectralPoint,
  HarmonicPeak,

  // Evolutionary channel
  EvolutionaryChannelData,
  PopulationState,
  FitnessPoint,
  SelectionPressurePoint,
  MutationEvent,
  AttractorBasin,

  // Correlation types
  CorrelationResult,
  CorrelationPattern,
  CorrelationVisualizationData,

  // Selection types
  SelectionState,
  SelectionHistoryEntry,
  DependencyGraph,
  DependencyNode,
  DependencyEdge,
  DependencyCluster,

  // Animation types
  AnimationConfig,
  AnimationKeyframe,
  ScheduleAnimationState,
  AnimatedAssignment,
  FrameTransition,

  // Looking Glass types
  LookingGlassConfig,
  LookingGlassCalibration,
  QuiltSettings,
  LookingGlassRendering,
  HolographicScene,
  HolographicCamera,
  HolographicLight,
  HolographicObject,
  HolographicMaterial,
  HolographicEffect,

  // Spatial audio types
  SpatialAudioConfig,
  ViolationAudioSource,
  ViolationType,
  AudioParameters,

  // Constraint coupling types
  ConstraintCouplingData,
  ConstraintNode,
  ConstraintCoupling,
  CouplingCluster,
  ForceFieldData,

  // Export types
  ExportConfig,
  ExportFormat,
  ExportInclusions,
  ExportQuality,
  ExportMetadata,
  ExportedVisualizationState,

  // Tour types
  GuidedTour,
  TourWaypoint,
  WaypointTransition,
  TourAnnotation,
  TourAction,
  TourNarration,

  // Hub state types
  HolographicHubState,
  HubViewMode,
  RenderingQuality,
  PanelStates,
} from './types';

// Constants
export {
  WAVELENGTH_PAIRS,
  WAVELENGTH_COLORS,
  WAVELENGTH_LABELS,
  CONSTRAINT_CATEGORY_COLORS,
  COUPLING_TYPE_COLORS,
  VIOLATION_AUDIO_THEMES,
  BUILT_IN_TOURS,
} from './types';
