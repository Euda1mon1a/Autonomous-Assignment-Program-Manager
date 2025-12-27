/**
 * React Hooks for Holographic Visualization Hub
 *
 * Provides data fetching, state management, and real-time updates
 * for the multi-spectral correlation visualization system.
 */

'use client';

import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type {
  WavelengthChannel,
  WavelengthPair,
  WAVELENGTH_PAIRS,
  CorrelationResult,
  SelectionState,
  AnimationConfig,
  AnimationKeyframe,
  SpatialAudioConfig,
  ViolationAudioSource,
  HolographicHubState,
  HubViewMode,
  DependencyGraph,
  DependencyNode,
  DependencyEdge,
  ConstraintCouplingData,
  GuidedTour,
  TourWaypoint,
  ExportConfig,
  ExportedVisualizationState,
  HolographicScene,
  LookingGlassConfig,
  QuantumChannelData,
  TemporalChannelData,
  SpectralChannelData,
  EvolutionaryChannelData,
} from './types';
import { CorrelationEngine, correlationEngine } from './correlation-engine';

// ============================================================================
// Query Keys
// ============================================================================

export const holographicQueryKeys = {
  all: ['holographic'] as const,
  wavelength: (channel: WavelengthChannel) => ['holographic', 'wavelength', channel] as const,
  correlation: (pair: WavelengthPair) => ['holographic', 'correlation', pair.primary, pair.secondary] as const,
  dependencies: (ids: string[]) => ['holographic', 'dependencies', ...ids] as const,
  constraintCoupling: () => ['holographic', 'constraint-coupling'] as const,
  tours: () => ['holographic', 'tours'] as const,
  tour: (id: string) => ['holographic', 'tour', id] as const,
  animations: (range: { start: string; end: string }) => ['holographic', 'animations', range.start, range.end] as const,
};

// ============================================================================
// Wavelength Channel Data Hooks
// ============================================================================

/**
 * Hook for fetching quantum channel data
 */
export function useQuantumChannelData(enabled: boolean = true) {
  return useQuery({
    queryKey: holographicQueryKeys.wavelength('quantum'),
    queryFn: async (): Promise<QuantumChannelData> => {
      // In production, this would fetch from the API
      // For now, generate synthetic quantum data
      return generateSyntheticQuantumData();
    },
    enabled,
    staleTime: 30_000,
  });
}

/**
 * Hook for fetching temporal channel data
 */
export function useTemporalChannelData(
  timeRange: { start: string; end: string } | null,
  enabled: boolean = true
) {
  return useQuery({
    queryKey: [...holographicQueryKeys.wavelength('temporal'), timeRange],
    queryFn: async (): Promise<TemporalChannelData> => {
      return generateSyntheticTemporalData(timeRange);
    },
    enabled: enabled && timeRange !== null,
    staleTime: 30_000,
  });
}

/**
 * Hook for fetching spectral channel data
 */
export function useSpectralChannelData(enabled: boolean = true) {
  return useQuery({
    queryKey: holographicQueryKeys.wavelength('spectral'),
    queryFn: async (): Promise<SpectralChannelData> => {
      return generateSyntheticSpectralData();
    },
    enabled,
    staleTime: 30_000,
  });
}

/**
 * Hook for fetching evolutionary channel data
 */
export function useEvolutionaryChannelData(enabled: boolean = true) {
  return useQuery({
    queryKey: holographicQueryKeys.wavelength('evolutionary'),
    queryFn: async (): Promise<EvolutionaryChannelData> => {
      return generateSyntheticEvolutionaryData();
    },
    enabled,
    staleTime: 30_000,
  });
}

// ============================================================================
// Correlation Hooks
// ============================================================================

/**
 * Hook for managing the correlation engine
 */
export function useCorrelationEngine() {
  const engine = useRef(new CorrelationEngine());
  const [correlations, setCorrelations] = useState<CorrelationResult[]>([]);
  const [isComputing, setIsComputing] = useState(false);

  const updateChannel = useCallback((channel: WavelengthChannel, data: unknown) => {
    engine.current.updateChannelData(channel, data);
  }, []);

  const computeCorrelations = useCallback((pairs: WavelengthPair[]) => {
    setIsComputing(true);
    try {
      const results = engine.current.getAllCorrelations(pairs);
      setCorrelations(results);
    } finally {
      setIsComputing(false);
    }
  }, []);

  const getCorrelation = useCallback((pair: WavelengthPair) => {
    return engine.current.getCorrelation(pair);
  }, []);

  const clearCache = useCallback(() => {
    engine.current.clearCache();
    setCorrelations([]);
  }, []);

  const statistics = useMemo(() => {
    return engine.current.getStatistics();
  }, [correlations]);

  return {
    correlations,
    isComputing,
    updateChannel,
    computeCorrelations,
    getCorrelation,
    clearCache,
    statistics,
  };
}

/**
 * Hook for a specific wavelength pair correlation
 */
export function useWavelengthCorrelation(pair: WavelengthPair) {
  const { getCorrelation, updateChannel } = useCorrelationEngine();
  const [result, setResult] = useState<CorrelationResult | null>(null);

  const primaryQuery = useQuery({
    queryKey: holographicQueryKeys.wavelength(pair.primary),
    queryFn: async () => generateChannelData(pair.primary),
    staleTime: 30_000,
  });

  const secondaryQuery = useQuery({
    queryKey: holographicQueryKeys.wavelength(pair.secondary),
    queryFn: async () => generateChannelData(pair.secondary),
    staleTime: 30_000,
  });

  useEffect(() => {
    if (primaryQuery.data) {
      updateChannel(pair.primary, primaryQuery.data);
    }
    if (secondaryQuery.data) {
      updateChannel(pair.secondary, secondaryQuery.data);
    }
    if (primaryQuery.data && secondaryQuery.data) {
      setResult(getCorrelation(pair));
    }
  }, [primaryQuery.data, secondaryQuery.data, pair, updateChannel, getCorrelation]);

  return {
    result,
    isLoading: primaryQuery.isLoading || secondaryQuery.isLoading,
    error: primaryQuery.error || secondaryQuery.error,
  };
}

// ============================================================================
// Selection & Interaction Hooks
// ============================================================================

/**
 * Hook for managing selection state
 */
export function useSelectionState() {
  const [selection, setSelection] = useState<SelectionState>({
    selectedResidents: [],
    selectedConstraints: [],
    selectedTimeRange: null,
    activeChannels: ['temporal', 'spectral'],
    highlightMode: 'dependencies',
    history: [],
  });

  const selectResident = useCallback((residentId: string, append: boolean = false) => {
    setSelection(prev => {
      const newResidents = append
        ? prev.selectedResidents.includes(residentId)
          ? prev.selectedResidents.filter(id => id !== residentId)
          : [...prev.selectedResidents, residentId]
        : [residentId];

      return {
        ...prev,
        selectedResidents: newResidents,
        history: [
          ...prev.history,
          {
            timestamp: new Date().toISOString(),
            type: append ? (prev.selectedResidents.includes(residentId) ? 'remove' : 'add') : 'set',
            category: 'resident',
            values: [residentId],
          },
        ],
      };
    });
  }, []);

  const selectConstraint = useCallback((constraintId: string, append: boolean = false) => {
    setSelection(prev => {
      const newConstraints = append
        ? prev.selectedConstraints.includes(constraintId)
          ? prev.selectedConstraints.filter(id => id !== constraintId)
          : [...prev.selectedConstraints, constraintId]
        : [constraintId];

      return {
        ...prev,
        selectedConstraints: newConstraints,
        history: [
          ...prev.history,
          {
            timestamp: new Date().toISOString(),
            type: append ? (prev.selectedConstraints.includes(constraintId) ? 'remove' : 'add') : 'set',
            category: 'constraint',
            values: [constraintId],
          },
        ],
      };
    });
  }, []);

  const setTimeRange = useCallback((range: { start: string; end: string } | null) => {
    setSelection(prev => ({
      ...prev,
      selectedTimeRange: range,
      history: [
        ...prev.history,
        {
          timestamp: new Date().toISOString(),
          type: 'set',
          category: 'timeRange',
          values: range ? [range.start, range.end] : [],
        },
      ],
    }));
  }, []);

  const toggleChannel = useCallback((channel: WavelengthChannel) => {
    setSelection(prev => ({
      ...prev,
      activeChannels: prev.activeChannels.includes(channel)
        ? prev.activeChannels.filter(c => c !== channel)
        : [...prev.activeChannels, channel],
      history: [
        ...prev.history,
        {
          timestamp: new Date().toISOString(),
          type: prev.activeChannels.includes(channel) ? 'remove' : 'add',
          category: 'channel',
          values: [channel],
        },
      ],
    }));
  }, []);

  const setHighlightMode = useCallback((mode: SelectionState['highlightMode']) => {
    setSelection(prev => ({ ...prev, highlightMode: mode }));
  }, []);

  const clearSelection = useCallback(() => {
    setSelection(prev => ({
      ...prev,
      selectedResidents: [],
      selectedConstraints: [],
      selectedTimeRange: null,
      history: [
        ...prev.history,
        { timestamp: new Date().toISOString(), type: 'clear', category: 'resident', values: [] },
      ],
    }));
  }, []);

  const undo = useCallback(() => {
    setSelection(prev => {
      if (prev.history.length === 0) return prev;

      const lastAction = prev.history[prev.history.length - 1];
      const newHistory = prev.history.slice(0, -1);

      // Reverse the last action
      switch (lastAction.category) {
        case 'resident':
          if (lastAction.type === 'add') {
            return {
              ...prev,
              selectedResidents: prev.selectedResidents.filter(id => !lastAction.values.includes(id)),
              history: newHistory,
            };
          } else if (lastAction.type === 'remove') {
            return {
              ...prev,
              selectedResidents: [...prev.selectedResidents, ...lastAction.values],
              history: newHistory,
            };
          }
          break;
        case 'constraint':
          if (lastAction.type === 'add') {
            return {
              ...prev,
              selectedConstraints: prev.selectedConstraints.filter(id => !lastAction.values.includes(id)),
              history: newHistory,
            };
          } else if (lastAction.type === 'remove') {
            return {
              ...prev,
              selectedConstraints: [...prev.selectedConstraints, ...lastAction.values],
              history: newHistory,
            };
          }
          break;
      }

      return { ...prev, history: newHistory };
    });
  }, []);

  return {
    selection,
    selectResident,
    selectConstraint,
    setTimeRange,
    toggleChannel,
    setHighlightMode,
    clearSelection,
    undo,
  };
}

/**
 * Hook for fetching dependency graph based on selection
 */
export function useDependencyGraph(selection: SelectionState) {
  const allSelectedIds = [
    ...selection.selectedResidents,
    ...selection.selectedConstraints,
  ];

  return useQuery({
    queryKey: holographicQueryKeys.dependencies(allSelectedIds),
    queryFn: async (): Promise<DependencyGraph> => {
      return generateSyntheticDependencyGraph(allSelectedIds);
    },
    enabled: allSelectedIds.length > 0,
    staleTime: 10_000,
  });
}

// ============================================================================
// Animation Hooks
// ============================================================================

/**
 * Hook for managing animation state
 */
export function useAnimationController(
  timeRange: { start: string; end: string } | null
) {
  const [config, setConfig] = useState<AnimationConfig>({
    isPlaying: false,
    currentFrame: 0,
    totalFrames: 100,
    fps: 30,
    loopMode: 'loop',
    timeRange: timeRange || { start: '', end: '' },
    easing: 'easeInOut',
    interpolation: 'spline',
  });

  const animationRef = useRef<number | null>(null);
  const lastFrameTimeRef = useRef<number>(0);

  // Fetch keyframes
  const keyframesQuery = useQuery({
    queryKey: holographicQueryKeys.animations(config.timeRange),
    queryFn: async (): Promise<AnimationKeyframe[]> => {
      return generateSyntheticKeyframes(config.totalFrames);
    },
    enabled: config.timeRange.start !== '' && config.timeRange.end !== '',
  });

  // Animation loop
  useEffect(() => {
    if (!config.isPlaying) {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
        animationRef.current = null;
      }
      return;
    }

    const frameDuration = 1000 / config.fps;

    const animate = (timestamp: number) => {
      if (timestamp - lastFrameTimeRef.current >= frameDuration) {
        lastFrameTimeRef.current = timestamp;

        setConfig(prev => {
          let nextFrame = prev.currentFrame + 1;

          if (nextFrame >= prev.totalFrames) {
            if (prev.loopMode === 'loop') {
              nextFrame = 0;
            } else if (prev.loopMode === 'pingpong') {
              // This would need more state to track direction
              nextFrame = prev.totalFrames - 2;
            } else {
              return { ...prev, isPlaying: false };
            }
          }

          return { ...prev, currentFrame: nextFrame };
        });
      }

      animationRef.current = requestAnimationFrame(animate);
    };

    animationRef.current = requestAnimationFrame(animate);

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [config.isPlaying, config.fps, config.loopMode, config.totalFrames]);

  const play = useCallback(() => {
    setConfig(prev => ({ ...prev, isPlaying: true }));
  }, []);

  const pause = useCallback(() => {
    setConfig(prev => ({ ...prev, isPlaying: false }));
  }, []);

  const stop = useCallback(() => {
    setConfig(prev => ({ ...prev, isPlaying: false, currentFrame: 0 }));
  }, []);

  const seekTo = useCallback((frame: number) => {
    setConfig(prev => ({
      ...prev,
      currentFrame: Math.max(0, Math.min(frame, prev.totalFrames - 1)),
    }));
  }, []);

  const setSpeed = useCallback((fps: number) => {
    setConfig(prev => ({ ...prev, fps: Math.max(1, Math.min(fps, 120)) }));
  }, []);

  const setLoopMode = useCallback((mode: AnimationConfig['loopMode']) => {
    setConfig(prev => ({ ...prev, loopMode: mode }));
  }, []);

  const currentKeyframe = useMemo(() => {
    return keyframesQuery.data?.[config.currentFrame] || null;
  }, [keyframesQuery.data, config.currentFrame]);

  return {
    config,
    keyframes: keyframesQuery.data || [],
    currentKeyframe,
    isLoading: keyframesQuery.isLoading,
    play,
    pause,
    stop,
    seekTo,
    setSpeed,
    setLoopMode,
  };
}

// ============================================================================
// Spatial Audio Hooks
// ============================================================================

/**
 * Hook for managing spatial audio
 */
export function useSpatialAudio() {
  const audioContextRef = useRef<AudioContext | null>(null);
  const gainNodeRef = useRef<GainNode | null>(null);
  const oscillatorsRef = useRef<Map<string, OscillatorNode>>(new Map());

  const [config, setConfig] = useState<SpatialAudioConfig>({
    masterVolume: 0.5,
    isEnabled: false,
    listenerPosition: { x: 0, y: 0, z: 5 },
    listenerOrientation: {
      forward: { x: 0, y: 0, z: -1 },
      up: { x: 0, y: 1, z: 0 },
    },
    distanceModel: 'inverse',
    refDistance: 1,
    maxDistance: 100,
    rolloffFactor: 1,
  });

  const [activeSources, setActiveSources] = useState<ViolationAudioSource[]>([]);

  // Initialize audio context
  const initAudio = useCallback(() => {
    if (!audioContextRef.current) {
      audioContextRef.current = new AudioContext();
      gainNodeRef.current = audioContextRef.current.createGain();
      gainNodeRef.current.connect(audioContextRef.current.destination);
      gainNodeRef.current.gain.value = config.masterVolume;
    }
    setConfig(prev => ({ ...prev, isEnabled: true }));
  }, [config.masterVolume]);

  // Clean up audio context
  const disposeAudio = useCallback(() => {
    // Stop all oscillators
    for (const osc of oscillatorsRef.current.values()) {
      try {
        osc.stop();
        osc.disconnect();
      } catch {
        // Ignore errors from already stopped oscillators
      }
    }
    oscillatorsRef.current.clear();

    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    setConfig(prev => ({ ...prev, isEnabled: false }));
  }, []);

  // Update master volume
  const setVolume = useCallback((volume: number) => {
    const clampedVolume = Math.max(0, Math.min(1, volume));
    if (gainNodeRef.current) {
      gainNodeRef.current.gain.value = clampedVolume;
    }
    setConfig(prev => ({ ...prev, masterVolume: clampedVolume }));
  }, []);

  // Add a violation audio source
  const addViolationSource = useCallback((source: ViolationAudioSource) => {
    if (!audioContextRef.current || !gainNodeRef.current) return;

    const ctx = audioContextRef.current;

    // Create oscillator
    const oscillator = ctx.createOscillator();
    const sourceGain = ctx.createGain();
    const panner = ctx.createPanner();

    // Configure oscillator
    oscillator.type = source.audio.waveform === 'noise' ? 'sawtooth' : source.audio.waveform;
    oscillator.frequency.value = source.audio.frequency;

    // Configure panner for 3D positioning
    panner.positionX.value = source.position.x;
    panner.positionY.value = source.position.y;
    panner.positionZ.value = source.position.z;
    panner.distanceModel = config.distanceModel;
    panner.refDistance = config.refDistance;
    panner.maxDistance = config.maxDistance;
    panner.rolloffFactor = config.rolloffFactor;

    // Configure gain envelope
    sourceGain.gain.setValueAtTime(0, ctx.currentTime);
    sourceGain.gain.linearRampToValueAtTime(
      source.audio.volume * source.severity,
      ctx.currentTime + source.audio.attack
    );
    sourceGain.gain.linearRampToValueAtTime(
      source.audio.volume * source.severity * source.audio.sustain,
      ctx.currentTime + source.audio.attack + source.audio.decay
    );

    // Connect nodes
    oscillator.connect(sourceGain);
    sourceGain.connect(panner);
    panner.connect(gainNodeRef.current);

    // Start oscillator
    oscillator.start();
    oscillatorsRef.current.set(source.sourceId, oscillator);

    setActiveSources(prev => [...prev, source]);
  }, [config]);

  // Remove a violation audio source
  const removeViolationSource = useCallback((sourceId: string) => {
    const oscillator = oscillatorsRef.current.get(sourceId);
    if (oscillator) {
      try {
        oscillator.stop();
        oscillator.disconnect();
      } catch {
        // Ignore
      }
      oscillatorsRef.current.delete(sourceId);
    }
    setActiveSources(prev => prev.filter(s => s.sourceId !== sourceId));
  }, []);

  // Update listener position (camera position)
  const updateListenerPosition = useCallback((position: { x: number; y: number; z: number }) => {
    if (audioContextRef.current) {
      const listener = audioContextRef.current.listener;
      if (listener.positionX) {
        listener.positionX.value = position.x;
        listener.positionY.value = position.y;
        listener.positionZ.value = position.z;
      }
    }
    setConfig(prev => ({ ...prev, listenerPosition: position }));
  }, []);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      disposeAudio();
    };
  }, [disposeAudio]);

  return {
    config,
    activeSources,
    initAudio,
    disposeAudio,
    setVolume,
    addViolationSource,
    removeViolationSource,
    updateListenerPosition,
  };
}

// ============================================================================
// Constraint Coupling Hook
// ============================================================================

/**
 * Hook for fetching constraint coupling data
 */
export function useConstraintCoupling() {
  return useQuery({
    queryKey: holographicQueryKeys.constraintCoupling(),
    queryFn: async (): Promise<ConstraintCouplingData> => {
      return generateSyntheticConstraintCoupling();
    },
    staleTime: 60_000,
  });
}

// ============================================================================
// Guided Tour Hooks
// ============================================================================

/**
 * Hook for fetching available tours
 */
export function useGuidedTours() {
  return useQuery({
    queryKey: holographicQueryKeys.tours(),
    queryFn: async (): Promise<GuidedTour[]> => {
      return generateBuiltInTours();
    },
    staleTime: Infinity, // Tours are static
  });
}

/**
 * Hook for tour playback
 */
export function useTourPlayer(tour: GuidedTour | null) {
  const [currentWaypointIndex, setCurrentWaypointIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const currentWaypoint = useMemo(() => {
    return tour?.waypoints[currentWaypointIndex] || null;
  }, [tour, currentWaypointIndex]);

  // Auto-advance through waypoints
  useEffect(() => {
    if (!isPlaying || !currentWaypoint) {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
      return;
    }

    const totalDuration = currentWaypoint.transition.duration + currentWaypoint.dwellTime;
    const intervalMs = 100;
    let elapsed = 0;

    const tick = () => {
      elapsed += intervalMs / 1000;
      setProgress(elapsed / totalDuration);

      if (elapsed >= totalDuration) {
        // Move to next waypoint
        if (tour && currentWaypointIndex < tour.waypoints.length - 1) {
          setCurrentWaypointIndex(prev => prev + 1);
          setProgress(0);
        } else {
          setIsPlaying(false);
          setProgress(1);
        }
      } else {
        timerRef.current = setTimeout(tick, intervalMs);
      }
    };

    timerRef.current = setTimeout(tick, intervalMs);

    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, [isPlaying, currentWaypoint, currentWaypointIndex, tour]);

  const play = useCallback(() => setIsPlaying(true), []);
  const pause = useCallback(() => setIsPlaying(false), []);
  const reset = useCallback(() => {
    setCurrentWaypointIndex(0);
    setProgress(0);
    setIsPlaying(false);
  }, []);
  const goToWaypoint = useCallback((index: number) => {
    setCurrentWaypointIndex(Math.max(0, Math.min(index, (tour?.waypoints.length || 1) - 1)));
    setProgress(0);
  }, [tour]);

  return {
    currentWaypointIndex,
    currentWaypoint,
    isPlaying,
    progress,
    play,
    pause,
    reset,
    goToWaypoint,
    totalWaypoints: tour?.waypoints.length || 0,
  };
}

// ============================================================================
// Export Hook
// ============================================================================

/**
 * Hook for exporting visualization states
 */
export function useVisualizationExport() {
  const queryClient = useQueryClient();

  const exportMutation = useMutation({
    mutationFn: async ({
      config,
      scene,
      selection,
      correlations,
    }: {
      config: ExportConfig;
      scene: HolographicScene;
      selection: SelectionState;
      correlations: CorrelationResult[];
    }): Promise<ExportedVisualizationState> => {
      // In production, this would call the backend to generate exports
      const exportId = `export-${Date.now()}`;

      return {
        exportId,
        exportedAt: new Date().toISOString(),
        config,
        scene,
        selection,
        correlations,
        wavelengthSnapshots: {},
        files: [
          {
            type: config.format,
            path: `/exports/${exportId}.${config.format}`,
            size: 0,
          },
        ],
      };
    },
  });

  return {
    exportVisualization: exportMutation.mutate,
    isExporting: exportMutation.isPending,
    exportResult: exportMutation.data,
    exportError: exportMutation.error,
  };
}

// ============================================================================
// Main Hub State Hook
// ============================================================================

/**
 * Main hook that combines all holographic hub state
 */
export function useHolographicHub() {
  const [viewMode, setViewMode] = useState<HubViewMode>('explore');
  const [activeTour, setActiveTour] = useState<GuidedTour | null>(null);

  const selectionState = useSelectionState();
  const correlationEngine = useCorrelationEngine();
  const spatialAudio = useSpatialAudio();

  const animationController = useAnimationController(
    selectionState.selection.selectedTimeRange
  );

  const dependencyGraph = useDependencyGraph(selectionState.selection);
  const constraintCoupling = useConstraintCoupling();
  const guidedTours = useGuidedTours();
  const tourPlayer = useTourPlayer(activeTour);
  const visualizationExport = useVisualizationExport();

  // Load channel data based on active channels
  const quantumData = useQuantumChannelData(
    selectionState.selection.activeChannels.includes('quantum')
  );
  const temporalData = useTemporalChannelData(
    selectionState.selection.selectedTimeRange,
    selectionState.selection.activeChannels.includes('temporal')
  );
  const spectralData = useSpectralChannelData(
    selectionState.selection.activeChannels.includes('spectral')
  );
  const evolutionaryData = useEvolutionaryChannelData(
    selectionState.selection.activeChannels.includes('evolutionary')
  );

  // Update correlation engine when channel data changes
  useEffect(() => {
    if (quantumData.data) {
      correlationEngine.updateChannel('quantum', quantumData.data);
    }
    if (temporalData.data) {
      correlationEngine.updateChannel('temporal', temporalData.data);
    }
    if (spectralData.data) {
      correlationEngine.updateChannel('spectral', spectralData.data);
    }
    if (evolutionaryData.data) {
      correlationEngine.updateChannel('evolutionary', evolutionaryData.data);
    }
  }, [quantumData.data, temporalData.data, spectralData.data, evolutionaryData.data]);

  const startTour = useCallback((tour: GuidedTour) => {
    setActiveTour(tour);
    setViewMode('tour');
  }, []);

  const endTour = useCallback(() => {
    setActiveTour(null);
    tourPlayer.reset();
    setViewMode('explore');
  }, [tourPlayer]);

  return {
    // View state
    viewMode,
    setViewMode,

    // Selection
    ...selectionState,

    // Correlations
    correlations: correlationEngine.correlations,
    correlationStatistics: correlationEngine.statistics,
    computeCorrelations: correlationEngine.computeCorrelations,

    // Animation
    animation: animationController,

    // Audio
    audio: spatialAudio,

    // Dependencies
    dependencyGraph: dependencyGraph.data || null,
    isDependencyLoading: dependencyGraph.isLoading,

    // Constraint coupling
    constraintCoupling: constraintCoupling.data || null,
    isConstraintCouplingLoading: constraintCoupling.isLoading,

    // Tours
    availableTours: guidedTours.data || [],
    activeTour,
    tourPlayer,
    startTour,
    endTour,

    // Export
    ...visualizationExport,

    // Channel data
    channelData: {
      quantum: quantumData.data || null,
      temporal: temporalData.data || null,
      spectral: spectralData.data || null,
      evolutionary: evolutionaryData.data || null,
    },
    isChannelLoading: {
      quantum: quantumData.isLoading,
      temporal: temporalData.isLoading,
      spectral: spectralData.isLoading,
      evolutionary: evolutionaryData.isLoading,
    },
  };
}

// ============================================================================
// Synthetic Data Generators (for development/demo)
// ============================================================================

function generateChannelData(channel: WavelengthChannel): unknown {
  switch (channel) {
    case 'quantum':
      return generateSyntheticQuantumData();
    case 'temporal':
      return generateSyntheticTemporalData(null);
    case 'spectral':
      return generateSyntheticSpectralData();
    case 'evolutionary':
      return generateSyntheticEvolutionaryData();
    default:
      return null;
  }
}

function generateSyntheticQuantumData(): QuantumChannelData {
  const numStates = 20;
  const states = Array.from({ length: numStates }, (_, i) => {
    const theta = (i / numStates) * Math.PI;
    const phi = (i / numStates) * 2 * Math.PI;

    return {
      stateId: `state-${i}`,
      scheduleVariantId: `variant-${i}`,
      amplitude: {
        real: Math.cos(theta) * Math.cos(phi),
        imaginary: Math.cos(theta) * Math.sin(phi),
        magnitude: Math.abs(Math.cos(theta)),
        phase: phi,
      },
      probability: 1 / numStates,
      entanglements: i > 0 ? [{
        targetStateId: `state-${i - 1}`,
        correlationStrength: Math.random() * 0.5 + 0.5,
        bellStateType: 'phi+' as const,
      }] : [],
      coherence: 0.5 + Math.random() * 0.5,
      decoherenceRate: 0.01 + Math.random() * 0.05,
    };
  });

  return {
    states,
    totalProbability: 1,
    averageCoherence: states.reduce((sum, s) => sum + s.coherence, 0) / numStates,
    entanglementDensity: 0.7,
    blochSpherePoints: states.map(s => ({
      stateId: s.stateId,
      theta: Math.acos(s.amplitude.real),
      phi: s.amplitude.phase,
      radius: s.amplitude.magnitude,
      color: `hsl(${(s.coherence * 360) % 360}, 70%, 50%)`,
    })),
  };
}

function generateSyntheticTemporalData(
  timeRange: { start: string; end: string } | null
): TemporalChannelData {
  const numPoints = 100;
  const now = new Date();

  return {
    timeSeries: Array.from({ length: numPoints }, (_, i) => ({
      timestamp: new Date(now.getTime() - (numPoints - i) * 3600000).toISOString(),
      value: Math.sin(i * 0.1) * 0.5 + 0.5 + Math.random() * 0.2,
      metadata: { personId: `person-${i % 10}` },
      derivative: Math.cos(i * 0.1) * 0.05,
    })),
    phaseRelationships: [
      { sourceId: 'person-0', targetId: 'person-1', phaseShift: Math.PI / 4, coherence: 0.8, frequency: 0.1 },
      { sourceId: 'person-2', targetId: 'person-3', phaseShift: Math.PI / 2, coherence: 0.6, frequency: 0.15 },
    ],
    clusters: [
      { clusterId: 'daily-1', startTime: '', endTime: '', pattern: 'daily', strength: 0.85, members: ['person-0', 'person-1'] },
      { clusterId: 'weekly-1', startTime: '', endTime: '', pattern: 'weekly', strength: 0.72, members: ['person-2', 'person-3', 'person-4'] },
    ],
    lagCorrelations: Array.from({ length: 20 }, (_, i) => ({
      lag: i - 10,
      correlation: Math.exp(-Math.abs(i - 10) * 0.1) * (i === 10 ? 1 : 0.5 + Math.random() * 0.3),
      significance: 0.01 + Math.random() * 0.04,
    })),
  };
}

function generateSyntheticSpectralData(): SpectralChannelData {
  const numPoints = 64;

  return {
    powerSpectrum: Array.from({ length: numPoints }, (_, i) => ({
      frequency: i / numPoints,
      power: Math.exp(-i * 0.1) + (i === 7 ? 0.5 : 0) + (i === 14 ? 0.3 : 0), // Peaks at specific frequencies
    })),
    harmonics: [
      { frequency: 7 / numPoints, amplitude: 0.5, phase: 0, harmonic: 1, label: 'Weekly cycle' },
      { frequency: 14 / numPoints, amplitude: 0.3, phase: Math.PI / 4, harmonic: 2, label: 'Bi-weekly' },
      { frequency: 1 / numPoints, amplitude: 0.8, phase: 0, harmonic: 1, label: 'Daily cycle' },
    ],
    coherenceSpectrum: Array.from({ length: numPoints }, (_, i) => ({
      frequency: i / numPoints,
      coherence: Math.exp(-i * 0.05) * 0.8,
    })),
    phaseSpectrum: Array.from({ length: numPoints }, (_, i) => ({
      frequency: i / numPoints,
      power: (i * Math.PI / numPoints) % (2 * Math.PI),
    })),
  };
}

function generateSyntheticEvolutionaryData(): EvolutionaryChannelData {
  const numGenerations = 50;
  const strategies = ['cooperative', 'aggressive', 'tit_for_tat', 'random'];

  return {
    populationHistory: Array.from({ length: numGenerations }, (_, gen) => {
      const coopPop = 25 + gen * 0.3 + Math.random() * 5;
      const aggPop = 25 - gen * 0.2 + Math.random() * 5;
      const tftPop = 25 + gen * 0.1 + Math.random() * 5;
      const randPop = 25 - gen * 0.2 + Math.random() * 5;
      const total = coopPop + aggPop + tftPop + randPop;

      return {
        generation: gen,
        populations: {
          cooperative: coopPop / total * 100,
          aggressive: aggPop / total * 100,
          tit_for_tat: tftPop / total * 100,
          random: randPop / total * 100,
        },
        totalFitness: 1000 + gen * 10 + Math.random() * 50,
        diversity: 2 - gen * 0.02 + Math.random() * 0.1,
        dominantStrategy: gen > 30 ? 'cooperative' : 'tit_for_tat',
      };
    }),
    fitnessLandscape: Array.from({ length: 100 }, (_, i) => ({
      x: (i % 10) / 10,
      y: Math.floor(i / 10) / 10,
      z: Math.sin(i * 0.3) * 0.3 + 0.5,
      fitness: Math.sin(i * 0.3) * 0.3 + 0.5 + Math.random() * 0.1,
      strategyId: strategies[i % strategies.length],
    })),
    selectionPressure: Array.from({ length: numGenerations }, (_, gen) => ({
      generation: gen,
      pressure: 0.5 + Math.sin(gen * 0.1) * 0.3,
      direction: gen < 20 ? 'competitive' : gen < 40 ? 'neutral' : 'cooperative',
    })),
    mutations: [
      { generation: 10, fromStrategy: 'random', toStrategy: 'cooperative', probability: 0.02 },
      { generation: 25, fromStrategy: 'aggressive', toStrategy: 'tit_for_tat', probability: 0.03 },
    ],
    attractors: [
      { attractorId: 'coop-basin', center: { x: 0.7, y: 0.7, z: 0.8 }, radius: 0.3, stability: 'stable', trappedPopulation: 45 },
      { attractorId: 'tft-basin', center: { x: 0.5, y: 0.5, z: 0.6 }, radius: 0.2, stability: 'stable', trappedPopulation: 30 },
    ],
  };
}

function generateSyntheticDependencyGraph(selectedIds: string[]): DependencyGraph {
  const numNodes = 15;
  const nodes: DependencyNode[] = [];
  const edges: DependencyEdge[] = [];

  // Generate nodes
  for (let i = 0; i < numNodes; i++) {
    const type = i < 5 ? 'resident' : i < 10 ? 'constraint' : 'rotation';
    const id = `${type}-${i}`;
    nodes.push({
      id,
      type: type as 'resident' | 'constraint' | 'rotation',
      label: `${type.charAt(0).toUpperCase() + type.slice(1)} ${i}`,
      position: {
        x: Math.cos((i / numNodes) * 2 * Math.PI) * 3,
        y: Math.sin((i / numNodes) * 2 * Math.PI) * 3,
        z: (i / numNodes) * 2 - 1,
      },
      importance: Math.random(),
      isSelected: selectedIds.includes(id),
      wavelengthValues: {
        quantum: Math.random(),
        temporal: Math.random(),
        spectral: Math.random(),
      },
    });
  }

  // Generate edges
  for (let i = 0; i < numNodes; i++) {
    const numEdges = Math.floor(Math.random() * 3) + 1;
    for (let j = 0; j < numEdges; j++) {
      const target = Math.floor(Math.random() * numNodes);
      if (target !== i) {
        edges.push({
          source: nodes[i].id,
          target: nodes[target].id,
          weight: Math.random(),
          type: Math.random() > 0.5 ? 'constraint' : 'correlation',
          bidirectional: Math.random() > 0.7,
        });
      }
    }
  }

  return {
    nodes,
    edges,
    clusters: [
      {
        clusterId: 'cluster-1',
        nodeIds: nodes.slice(0, 5).map(n => n.id),
        centroid: { x: -2, y: 0, z: 0 },
        cohesion: 0.8,
        label: 'Resident Group 1',
      },
      {
        clusterId: 'cluster-2',
        nodeIds: nodes.slice(5, 10).map(n => n.id),
        centroid: { x: 2, y: 0, z: 0 },
        cohesion: 0.6,
        label: 'Constraint Group',
      },
    ],
  };
}

function generateSyntheticConstraintCoupling(): ConstraintCouplingData {
  const constraintTypes = ['acgme', 'coverage', 'preference', 'institutional', 'personal'];
  const numConstraints = 20;

  const constraints = Array.from({ length: numConstraints }, (_, i) => ({
    constraintId: `constraint-${i}`,
    name: `Constraint ${i}`,
    type: (i % 2 === 0 ? 'hard' : 'soft') as 'hard' | 'soft',
    category: constraintTypes[i % constraintTypes.length] as 'acgme' | 'coverage' | 'preference' | 'institutional' | 'personal',
    weight: Math.random(),
    position: {
      x: Math.cos((i / numConstraints) * 2 * Math.PI) * 5,
      y: Math.sin((i / numConstraints) * 2 * Math.PI) * 5,
      z: Math.sin(i * 0.5) * 2,
    },
    violations: Math.floor(Math.random() * 10),
    satisfactionRate: 0.7 + Math.random() * 0.3,
  }));

  const couplings: ConstraintCouplingData['couplings'] = [];
  for (let i = 0; i < numConstraints; i++) {
    for (let j = i + 1; j < numConstraints; j++) {
      if (Math.random() > 0.7) {
        const strength = (Math.random() - 0.5) * 2; // -1 to 1
        couplings.push({
          source: constraints[i].constraintId,
          target: constraints[j].constraintId,
          strength,
          type: strength > 0.3 ? 'reinforcing' : strength < -0.3 ? 'competing' : 'neutral',
          frequency: Math.random(),
          impact: Math.abs(strength) * Math.random(),
        });
      }
    }
  }

  return {
    constraints,
    couplings,
    clusters: [
      {
        clusterId: 'acgme-cluster',
        constraintIds: constraints.filter(c => c.category === 'acgme').map(c => c.constraintId),
        centroid: { x: 0, y: 3, z: 0 },
        internalCohesion: 0.85,
        externalCoupling: 0.4,
        dominantType: 'reinforcing',
      },
    ],
    forceField: {
      resolution: { x: 10, y: 10, z: 10 },
      vectors: new Float32Array(1000 * 3),
      potential: new Float32Array(1000),
      streamlines: [],
    },
  };
}

function generateBuiltInTours(): GuidedTour[] {
  const baseTour: GuidedTour = {
    tourId: 'intro-holographic',
    name: 'Introduction to Holographic Visualization',
    description: 'Learn the basics of navigating and interacting with the 3D schedule visualization',
    duration: 120,
    level: 'beginner',
    waypoints: [
      {
        index: 0,
        camera: {
          position: { x: 0, y: 0, z: 10 },
          target: { x: 0, y: 0, z: 0 },
          up: { x: 0, y: 1, z: 0 },
          fov: 60,
          near: 0.1,
          far: 1000,
        },
        dwellTime: 5,
        transition: { duration: 2, easing: 'easeInOut', pathType: 'arc' },
        highlights: [],
        activeChannels: ['temporal'],
        annotation: {
          title: 'Welcome to the Holographic Hub',
          body: 'This 3D visualization shows your schedule data from multiple perspectives.',
          position: { x: 0.5, y: 0.9 },
          duration: 5,
        },
        actions: [],
      },
      {
        index: 1,
        camera: {
          position: { x: 5, y: 5, z: 5 },
          target: { x: 0, y: 0, z: 0 },
          up: { x: 0, y: 1, z: 0 },
          fov: 60,
          near: 0.1,
          far: 1000,
        },
        dwellTime: 8,
        transition: { duration: 3, easing: 'easeInOut', pathType: 'spline' },
        highlights: [],
        activeChannels: ['temporal', 'spectral'],
        annotation: {
          title: 'Multi-Spectral Viewing',
          body: 'Combine different wavelength channels to reveal hidden patterns.',
          position: { x: 0.5, y: 0.9 },
          duration: 8,
        },
        actions: [
          { type: 'highlight', parameters: { entities: ['person-0', 'person-1'] }, timing: 'during' },
        ],
      },
    ],
    tags: ['introduction', 'navigation', 'basics'],
  };

  return [baseTour];
}

function generateSyntheticKeyframes(numFrames: number): AnimationKeyframe[] {
  return Array.from({ length: numFrames }, (_, i) => ({
    frameIndex: i,
    timestamp: new Date(Date.now() + i * 3600000).toISOString(),
    state: {
      assignments: Array.from({ length: 10 }, (_, j) => ({
        assignmentId: `assignment-${j}`,
        personId: `person-${j}`,
        rotationId: `rotation-${j % 3}`,
        position: {
          x: Math.cos((j + i * 0.1) * 0.5) * 3,
          y: Math.sin((j + i * 0.1) * 0.5) * 3,
          z: j * 0.5 - 2.5,
        },
        color: `hsl(${(j * 36 + i) % 360}, 70%, 50%)`,
        scale: 1 + Math.sin(i * 0.1) * 0.1,
      })),
      violations: i % 10 === 0 ? ['violation-1'] : [],
      coverageScore: 85 + Math.sin(i * 0.05) * 10,
      wavelengthSnapshots: {
        quantum: Math.sin(i * 0.02) * 0.5 + 0.5,
        temporal: Math.cos(i * 0.03) * 0.5 + 0.5,
      },
    },
    transitions: [],
  }));
}
