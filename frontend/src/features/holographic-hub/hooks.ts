/**
 * Holographic Visualization Hub Hooks
 *
 * React hooks for managing holographic visualization state,
 * data fetching, and real-time updates.
 */

// WebXR type declarations for browser environments with WebXR support
declare global {
  interface XRSession extends EventTarget {
    end(): Promise<void>;
  }
  interface XRSystem {
    isSessionSupported(mode: string): Promise<boolean>;
    requestSession(mode: string, options?: XRSessionInit): Promise<XRSession>;
  }
  interface XRSessionInit {
    requiredFeatures?: string[];
    optionalFeatures?: string[];
  }
}

import { useState, useCallback, useEffect, useRef, useMemo } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import {
  HolographicDataset,
  HolographicState,
  LayerVisibility,
  ConstraintVisibility,
  CameraState,
  ProjectionConfig,
  SpectralLayer,
  ConstraintType,
  ManifoldPoint,
  HolographicDataRequest,
  HolographicDataResponse,
  ConstraintDataPoint,
  SessionDataExport,
} from "./types";
import {
  generateMockHolographicData,
  buildHolographicDataset,
} from "./data-pipeline";
import {
  fetchAllExoticData,
  type ExoticResilienceData,
  type EntropyMetricsResponse,
  type ImmuneAssessmentResponse,
  type HopfieldEnergyResponse,
  type MetastabilityResponse,
} from "@/api/exotic-resilience";

// ============================================================================
// Default States
// ============================================================================

const DEFAULT_LAYER_VISIBILITY: LayerVisibility = {
  quantum: true,
  temporal: true,
  topological: true,
  spectral: true,
  evolutionary: true,
  gravitational: true,
  phase: true,
  thermodynamic: true,
};

const DEFAULT_CONSTRAINT_VISIBILITY: ConstraintVisibility = {
  acgme: true,
  fairness: true,
  fatigue: true,
  temporal: true,
  preference: true,
  coverage: true,
  skill: true,
  custom: true,
};

const DEFAULT_CAMERA_STATE: CameraState = {
  position: [10, 8, 10],
  target: [0, 0, 0],
  fov: 60,
  near: 0.1,
  far: 1000,
};

const DEFAULT_PROJECTION_CONFIG: ProjectionConfig = {
  method: "pca",
  pca: {
    nComponents: 3,
    whiten: false,
  },
};

// ============================================================================
// useHolographicData - Main data fetching hook
// ============================================================================

interface UseHolographicDataOptions {
  startDate?: string;
  endDate?: string;
  layers?: SpectralLayer[];
  constraintTypes?: ConstraintType[];
  projectionMethod?: ProjectionConfig["method"];
  useMockData?: boolean;
  refetchInterval?: number;
}

async function fetchHolographicData(
  request: HolographicDataRequest
): Promise<HolographicDataResponse> {
  const params = new URLSearchParams();
  params.append("startDate", request.startDate);
  params.append("endDate", request.endDate);

  if (request.layers) {
    request.layers.forEach((layer) => params.append("layers", layer));
  }
  if (request.constraintTypes) {
    request.constraintTypes.forEach((type) =>
      params.append("constraint_types", type)
    );
  }
  if (request.projectionMethod) {
    params.append("projection_method", request.projectionMethod);
  }
  if (request.minSeverity !== undefined) {
    params.append("min_severity", String(request.minSeverity));
  }
  if (request.includeSatisfied !== undefined) {
    params.append("include_satisfied", String(request.includeSatisfied));
  }

  const response = await fetch(
    `/api/visualization/holographic?${params.toString()}`
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch holographic data: ${response.statusText}`);
  }

  return response.json();
}

export function useHolographicData(options: UseHolographicDataOptions = {}) {
  const {
    startDate = new Date().toISOString().split("T")[0],
    endDate = new Date(Date.now() + 14 * 24 * 60 * 60 * 1000)
      .toISOString()
      .split("T")[0],
    layers,
    constraintTypes,
    projectionMethod = "pca",
    useMockData = true,
    refetchInterval,
  } = options;

  return useQuery<HolographicDataset>({
    queryKey: [
      "holographic-data",
      startDate,
      endDate,
      layers,
      constraintTypes,
      projectionMethod,
    ],
    queryFn: async () => {
      if (useMockData) {
        // Use mock data for development
        return generateMockHolographicData(
          layers || ["quantum", "temporal", "evolutionary", "spectral"]
        );
      }

      const response = await fetchHolographicData({
        startDate,
        endDate,
        layers,
        constraintTypes,
        projectionMethod,
        includeSatisfied: true,
      });

      if (!response.success || !response.data) {
        throw new Error(response.error || "No data returned");
      }

      return response.data;
    },
    staleTime: 60000, // 1 minute
    gcTime: 300000, // 5 minutes
    refetchInterval,
  });
}

// ============================================================================
// useHolographicRealData - Real data from exotic resilience endpoints
// ============================================================================

/**
 * Convert exotic resilience data to SessionDataExport for a specific layer.
 * Each exotic endpoint maps to a spectral layer in the holographic visualization.
 */
function createSessionFromExoticData(
  layer: SpectralLayer,
  sessionId: number,
  data: EntropyMetricsResponse | ImmuneAssessmentResponse | HopfieldEnergyResponse | MetastabilityResponse | null,
  timestamp: string
): SessionDataExport | null {
  if (!data) return null;

  const constraints: ConstraintDataPoint[] = [];

  // Map each exotic endpoint's data to constraint data points
  switch (layer) {
    case "thermodynamic": {
      const entropy = data as EntropyMetricsResponse;
      // Create constraints from entropy metrics
      const dimensions = [
        entropy.personEntropy,
        entropy.rotationEntropy,
        entropy.timeEntropy,
        entropy.jointEntropy,
        entropy.mutualInformation,
        entropy.normalizedEntropy,
        entropy.entropyProductionRate,
        0, // padding
      ];

      // Main entropy constraint
      constraints.push({
        id: `thermodynamic-entropy-main`,
        type: "coverage",
        layer: "thermodynamic",
        dimensions,
        severity: 1 - entropy.normalizedEntropy, // High entropy = good distribution
        weight: 0.8,
        entities: {},
        label: `Entropy: ${entropy.interpretation}`,
        metadata: { apiSource: "thermodynamics/entropy", entropyData: entropy },
        timestamp,
      });

      // Add recommendations as additional constraint points
      entropy.recommendations?.forEach((rec, i) => {
        constraints.push({
          id: `thermodynamic-rec-${i}`,
          type: "preference",
          layer: "thermodynamic",
          dimensions: dimensions.map((d) => d + (Math.random() - 0.5) * 0.2),
          severity: 0.3 + Math.random() * 0.3,
          weight: 0.4,
          entities: {},
          label: rec,
          metadata: { source: "recommendation", index: i },
          timestamp,
        });
      });
      break;
    }

    case "evolutionary": {
      const immune = data as ImmuneAssessmentResponse;
      // Create constraints from immune system assessment
      const dimensions = [
        immune.anomalyScore,
        immune.matchingDetectors / Math.max(1, immune.totalDetectors),
        immune.closestDetectorDistance,
        immune.isAnomaly ? 1 : 0,
        0, 0, 0, 0, // padding
      ];

      constraints.push({
        id: `evolutionary-immune-main`,
        type: immune.isAnomaly ? "acgme" : "fairness",
        layer: "evolutionary",
        dimensions,
        severity: immune.anomalyScore,
        weight: 0.9,
        entities: {},
        label: `Immune Status: ${immune.immuneHealth}`,
        metadata: { apiSource: "immune/assess", immuneData: immune },
        timestamp,
      });

      // Add suggested repairs as constraint points
      immune.suggestedRepairs?.forEach((repair, i) => {
        constraints.push({
          id: `evolutionary-repair-${i}`,
          type: "skill",
          layer: "evolutionary",
          dimensions: dimensions.map((d) => d + (Math.random() - 0.5) * 0.3),
          severity: 0.2 + Math.random() * 0.2,
          weight: 0.5,
          entities: {},
          label: `${repair.repairType}: ${repair.description}`,
          metadata: { source: "repair", ...repair },
          timestamp,
        });
      });
      break;
    }

    case "gravitational": {
      const hopfield = data as HopfieldEnergyResponse;
      const metrics = hopfield.metrics;
      // Create constraints from Hopfield energy landscape
      const dimensions = [
        metrics.totalEnergy,
        metrics.normalizedEnergy,
        metrics.energyDensity,
        metrics.interactionEnergy,
        metrics.stabilityScore,
        metrics.gradientMagnitude,
        metrics.isLocalMinimum ? 1 : 0,
        metrics.distanceToMinimum / 10, // Normalize
      ];

      constraints.push({
        id: `gravitational-hopfield-main`,
        type: "fatigue",
        layer: "gravitational",
        dimensions,
        severity: 1 - metrics.stabilityScore,
        weight: 0.85,
        entities: {},
        label: `Energy Landscape: ${hopfield.interpretation}`,
        metadata: { apiSource: "hopfield/energy", hopfieldData: hopfield },
        timestamp,
      });

      // Stability level as a constraint
      // These keys match backend StabilityLevel enum values (snake_case)
      const stabilityMap: Record<string, number> = {
        // eslint-disable-next-line @typescript-eslint/naming-convention
        "very_stable": 0.1,
        "stable": 0.3,
        // eslint-disable-next-line @typescript-eslint/naming-convention
        "marginally_stable": 0.5,
        "unstable": 0.7,
        // eslint-disable-next-line @typescript-eslint/naming-convention
        "highly_unstable": 0.9,
      };
      constraints.push({
        id: `gravitational-stability`,
        type: "temporal",
        layer: "gravitational",
        dimensions: dimensions.map((d) => d * 0.9),
        severity: stabilityMap[hopfield.stabilityLevel] ?? 0.5,
        weight: 0.7,
        entities: {},
        label: `Stability: ${hopfield.stabilityLevel.replace(/_/g, " ")}`,
        metadata: { stabilityLevel: hopfield.stabilityLevel },
        timestamp,
      });

      // Recommendations
      hopfield.recommendations?.forEach((rec, i) => {
        constraints.push({
          id: `gravitational-rec-${i}`,
          type: "preference",
          layer: "gravitational",
          dimensions: dimensions.map((d) => d + (Math.random() - 0.5) * 0.15),
          severity: 0.25 + Math.random() * 0.25,
          weight: 0.4,
          entities: {},
          label: rec,
          metadata: { source: "recommendation", index: i },
          timestamp,
        });
      });
      break;
    }

    case "phase": {
      const meta = data as MetastabilityResponse;
      // Create constraints from metastability analysis
      const dimensions = [
        meta.energy,
        meta.barrierHeight,
        meta.escapeRate,
        meta.lifetime / 100, // Normalize
        meta.isMetastable ? 1 : 0,
        meta.stabilityScore,
        meta.nearestStableState ?? 0,
        0, // padding
      ];

      const riskMap: Record<string, number> = {
        low: 0.2,
        moderate: 0.4,
        high: 0.7,
        critical: 0.95,
      };

      constraints.push({
        id: `phase-metastability-main`,
        type: meta.isMetastable ? "acgme" : "coverage",
        layer: "phase",
        dimensions,
        severity: riskMap[meta.riskLevel] ?? 0.5,
        weight: 0.9,
        entities: {},
        label: `Metastability: ${meta.riskLevel} risk`,
        metadata: { apiSource: "exotic/metastability", metastabilityData: meta },
        timestamp,
      });

      // Energy barrier constraint
      constraints.push({
        id: `phase-barrier`,
        type: "fatigue",
        layer: "phase",
        dimensions: dimensions.map((d, i) => i === 1 ? d * 1.2 : d * 0.8),
        severity: Math.min(1, meta.barrierHeight),
        weight: 0.6,
        entities: {},
        label: `Energy Barrier: ${meta.barrierHeight.toFixed(2)}`,
        metadata: { barrierHeight: meta.barrierHeight },
        timestamp,
      });

      // Recommendations
      meta.recommendations?.forEach((rec, i) => {
        constraints.push({
          id: `phase-rec-${i}`,
          type: "preference",
          layer: "phase",
          dimensions: dimensions.map((d) => d + (Math.random() - 0.5) * 0.2),
          severity: 0.3 + Math.random() * 0.2,
          weight: 0.35,
          entities: {},
          label: rec,
          metadata: { source: "recommendation", index: i },
          timestamp,
        });
      });
      break;
    }

    default:
      return null;
  }

  if (constraints.length === 0) return null;

  const satisfiedCount = constraints.filter((c) => c.severity === 0).length;
  const violatedCount = constraints.filter((c) => c.severity > 0 && c.severity <= 0.8).length;
  const criticalCount = constraints.filter((c) => c.severity > 0.8).length;

  return {
    sessionId,
    sessionName: layer,
    timestamp,
    version: "1.0.0",
    constraints,
    metrics: {
      totalConstraints: constraints.length,
      satisfiedCount,
      violatedCount,
      criticalCount,
      averageSeverity: constraints.reduce((s, c) => s + c.severity, 0) / constraints.length,
      averageTension: constraints.reduce((s, c) => s + c.weight * c.severity, 0) / constraints.length,
    },
  };
}

/**
 * Aggregate exotic resilience data into HolographicDataset format.
 */
function aggregateToHolographic(
  exoticData: ExoticResilienceData,
  projectionMethod: "pca" | "umap" | "tsne" = "pca"
): HolographicDataset {
  const timestamp = exoticData.fetchedAt;
  const sessions: SessionDataExport[] = [];

  // Map exotic endpoints to spectral layers
  const entropySession = createSessionFromExoticData(
    "thermodynamic",
    8,
    exoticData.entropy,
    timestamp
  );
  if (entropySession) sessions.push(entropySession);

  const immuneSession = createSessionFromExoticData(
    "evolutionary",
    5,
    exoticData.immune,
    timestamp
  );
  if (immuneSession) sessions.push(immuneSession);

  const hopfieldSession = createSessionFromExoticData(
    "gravitational",
    6,
    exoticData.hopfield,
    timestamp
  );
  if (hopfieldSession) sessions.push(hopfieldSession);

  const metastabilitySession = createSessionFromExoticData(
    "phase",
    7,
    exoticData.metastability,
    timestamp
  );
  if (metastabilitySession) sessions.push(metastabilitySession);

  // Use the existing buildHolographicDataset to handle projection
  return buildHolographicDataset(sessions, { method: projectionMethod });
}

interface UseHolographicRealDataOptions {
  startDate?: string;
  endDate?: string;
  projectionMethod?: "pca" | "umap" | "tsne";
  refetchInterval?: number;
  fallbackToMock?: boolean;
}

/**
 * Hook to fetch real holographic data from exotic resilience endpoints.
 *
 * Aggregates data from:
 * - /api/v1/resilience/exotic/thermodynamics/entropy -> thermodynamic layer
 * - /api/v1/resilience/exotic/immune/assess -> evolutionary layer
 * - /api/v1/resilience/exotic/hopfield/energy -> gravitational layer
 * - /api/v1/resilience/exotic/exotic/metastability -> phase layer
 *
 * Falls back to mock data if APIs fail and fallbackToMock is enabled.
 */
export function useHolographicRealData(options: UseHolographicRealDataOptions = {}) {
  const {
    startDate = new Date().toISOString().split("T")[0],
    endDate = new Date(Date.now() + 14 * 24 * 60 * 60 * 1000)
      .toISOString()
      .split("T")[0],
    projectionMethod = "pca",
    refetchInterval,
    fallbackToMock = true,
  } = options;

  // Fetch all exotic endpoints in parallel
  const exoticQuery = useQuery<ExoticResilienceData>({
    queryKey: ["exotic-resilience-data", startDate, endDate],
    queryFn: () => fetchAllExoticData(startDate, endDate),
    staleTime: 60000, // 1 minute
    gcTime: 300000, // 5 minutes
    refetchInterval,
    retry: 2,
  });

  // Aggregate exotic data into holographic format
  const dataset = useMemo<HolographicDataset | undefined>(() => {
    if (exoticQuery.data) {
      // Check if we have at least some valid data
      const hasData = exoticQuery.data.entropy ||
        exoticQuery.data.immune ||
        exoticQuery.data.hopfield ||
        exoticQuery.data.metastability;

      if (hasData) {
        return aggregateToHolographic(exoticQuery.data, projectionMethod);
      }

      // All endpoints failed - use mock if enabled
      if (fallbackToMock && exoticQuery.data.errors.length > 0) {
        console.warn(
          "[HolographicHub] Exotic endpoints failed, falling back to mock:",
          exoticQuery.data.errors
        );
        return generateMockHolographicData([
          "thermodynamic",
          "evolutionary",
          "gravitational",
          "phase",
        ]);
      }
    }

    // If loading or no data yet, return undefined
    if (exoticQuery.isLoading) return undefined;

    // Fallback to mock on error
    if (exoticQuery.isError && fallbackToMock) {
      console.warn(
        "[HolographicHub] Query failed, falling back to mock:",
        exoticQuery.error
      );
      return generateMockHolographicData([
        "thermodynamic",
        "evolutionary",
        "gravitational",
        "phase",
      ]);
    }

    return undefined;
  }, [exoticQuery.data, exoticQuery.isLoading, exoticQuery.isError, exoticQuery.error, projectionMethod, fallbackToMock]);

  return {
    data: dataset,
    isLoading: exoticQuery.isLoading,
    isError: exoticQuery.isError,
    error: exoticQuery.error,
    refetch: exoticQuery.refetch,
    // Expose exotic data errors for debugging
    exoticErrors: exoticQuery.data?.errors ?? [],
    // Expose which endpoints succeeded
    endpoints: {
      entropy: !!exoticQuery.data?.entropy,
      immune: !!exoticQuery.data?.immune,
      hopfield: !!exoticQuery.data?.hopfield,
      metastability: !!exoticQuery.data?.metastability,
    },
  };
}

// ============================================================================
// useHolographicState - Visualization state management
// ============================================================================

export function useHolographicState(initialState?: Partial<HolographicState>) {
  const [state, setState] = useState<HolographicState>({
    layerVisibility: initialState?.layerVisibility || DEFAULT_LAYER_VISIBILITY,
    constraintVisibility:
      initialState?.constraintVisibility || DEFAULT_CONSTRAINT_VISIBILITY,
    camera: initialState?.camera || DEFAULT_CAMERA_STATE,
    selectedPointId: initialState?.selectedPointId || null,
    hoveredPointId: initialState?.hoveredPointId || null,
    isAnimating: initialState?.isAnimating ?? true,
    animationSpeed: initialState?.animationSpeed ?? 1.0,
    projection: initialState?.projection || DEFAULT_PROJECTION_CONFIG,
    quality: initialState?.quality || "medium",
    xrEnabled: initialState?.xrEnabled ?? false,
    xrSession: initialState?.xrSession || null,
  });

  const toggleLayer = useCallback((layer: SpectralLayer) => {
    setState((prev) => ({
      ...prev,
      layerVisibility: {
        ...prev.layerVisibility,
        [layer]: !prev.layerVisibility[layer],
      },
    }));
  }, []);

  const toggleConstraint = useCallback((type: ConstraintType) => {
    setState((prev) => ({
      ...prev,
      constraintVisibility: {
        ...prev.constraintVisibility,
        [type]: !prev.constraintVisibility[type],
      },
    }));
  }, []);

  const setCamera = useCallback((camera: Partial<CameraState>) => {
    setState((prev) => ({
      ...prev,
      camera: { ...prev.camera, ...camera },
    }));
  }, []);

  const selectPoint = useCallback((pointId: string | null) => {
    setState((prev) => ({ ...prev, selectedPointId: pointId }));
  }, []);

  const hoverPoint = useCallback((pointId: string | null) => {
    setState((prev) => ({ ...prev, hoveredPointId: pointId }));
  }, []);

  const setAnimating = useCallback((isAnimating: boolean) => {
    setState((prev) => ({ ...prev, isAnimating }));
  }, []);

  const setAnimationSpeed = useCallback((speed: number) => {
    setState((prev) => ({
      ...prev,
      animationSpeed: Math.max(0, Math.min(3, speed)),
    }));
  }, []);

  const setProjection = useCallback((projection: ProjectionConfig) => {
    setState((prev) => ({ ...prev, projection }));
  }, []);

  const setQuality = useCallback(
    (quality: "low" | "medium" | "high" | "ultra") => {
      setState((prev) => ({ ...prev, quality }));
    },
    []
  );

  const setAllLayersVisible = useCallback((visible: boolean) => {
    setState((prev) => ({
      ...prev,
      layerVisibility: Object.fromEntries(
        Object.keys(prev.layerVisibility).map((k) => [k, visible])
      ) as unknown as LayerVisibility,
    }));
  }, []);

  const setAllConstraintsVisible = useCallback((visible: boolean) => {
    setState((prev) => ({
      ...prev,
      constraintVisibility: Object.fromEntries(
        Object.keys(prev.constraintVisibility).map((k) => [k, visible])
      ) as unknown as ConstraintVisibility,
    }));
  }, []);

  return {
    state,
    toggleLayer,
    toggleConstraint,
    setCamera,
    selectPoint,
    hoverPoint,
    setAnimating,
    setAnimationSpeed,
    setProjection,
    setQuality,
    setAllLayersVisible,
    setAllConstraintsVisible,
  };
}

// ============================================================================
// useFilteredManifoldPoints - Filter points by visibility settings
// ============================================================================

export function useFilteredManifoldPoints(
  points: ManifoldPoint[] | undefined,
  layerVisibility: LayerVisibility,
  constraintVisibility: ConstraintVisibility
): ManifoldPoint[] {
  return useMemo(() => {
    if (!points) return [];

    return points.filter((point) => {
      const layerVisible = layerVisibility[point.layer];
      const constraintVisible = constraintVisibility[point.type];
      return layerVisible && constraintVisible;
    });
  }, [points, layerVisibility, constraintVisibility]);
}

// ============================================================================
// useAnimationFrame - Smooth animation loop
// ============================================================================

export function useAnimationFrame(
  callback: (deltaTime: number) => void,
  isActive: boolean = true
) {
  const requestRef = useRef<number>();
  const previousTimeRef = useRef<number>();
  const callbackRef = useRef(callback);

  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  useEffect(() => {
    if (!isActive) {
      if (requestRef.current) {
        cancelAnimationFrame(requestRef.current);
      }
      return;
    }

    const animate = (time: number) => {
      if (previousTimeRef.current !== undefined) {
        const deltaTime = (time - previousTimeRef.current) / 1000; // Convert to seconds
        callbackRef.current(deltaTime);
      }
      previousTimeRef.current = time;
      requestRef.current = requestAnimationFrame(animate);
    };

    requestRef.current = requestAnimationFrame(animate);

    return () => {
      if (requestRef.current) {
        cancelAnimationFrame(requestRef.current);
      }
    };
  }, [isActive]);
}

// ============================================================================
// useWebXR - WebXR integration for immersive viewing
// ============================================================================

interface WebXRState {
  isSupported: boolean;
  isSessionActive: boolean;
  session: XRSession | null;
  error: string | null;
}

export function useWebXR() {
  const [state, setState] = useState<WebXRState>({
    isSupported: false,
    isSessionActive: false,
    session: null,
    error: null,
  });

  useEffect(() => {
    // Check WebXR support
    if ("xr" in navigator) {
      (navigator as Navigator & { xr: XRSystem }).xr
        ?.isSessionSupported("immersive-vr")
        .then((supported) => {
          setState((prev) => ({ ...prev, isSupported: supported }));
        })
        .catch(() => {
          setState((prev) => ({ ...prev, isSupported: false }));
        });
    }
  }, []);

  const startSession = useCallback(async () => {
    if (!state.isSupported) {
      setState((prev) => ({ ...prev, error: "WebXR not supported" }));
      return;
    }

    try {
      const session = await (
        navigator as Navigator & { xr: XRSystem }
      ).xr?.requestSession("immersive-vr", {
        requiredFeatures: ["local-floor"],
        optionalFeatures: ["bounded-floor", "hand-tracking"],
      });

      if (session) {
        session.addEventListener("end", () => {
          setState((prev) => ({
            ...prev,
            isSessionActive: false,
            session: null,
          }));
        });

        setState((prev) => ({
          ...prev,
          isSessionActive: true,
          session,
          error: null,
        }));
      }
    } catch (err) {
      setState((prev) => ({
        ...prev,
        error: err instanceof Error ? err.message : "Failed to start XR session",
      }));
    }
  }, [state.isSupported]);

  const endSession = useCallback(async () => {
    if (state.session) {
      await state.session.end();
      setState((prev) => ({
        ...prev,
        isSessionActive: false,
        session: null,
      }));
    }
  }, [state.session]);

  return {
    ...state,
    startSession,
    endSession,
  };
}

// ============================================================================
// useRealTimeUpdates - WebSocket/SSE for live constraint updates
// ============================================================================

interface RealTimeUpdateOptions {
  endpoint?: string;
  enabled?: boolean;
  onUpdate?: (data: Partial<HolographicDataset>) => void;
}

export function useRealTimeUpdates(options: RealTimeUpdateOptions = {}) {
  const {
    endpoint = "/api/visualization/holographic/stream",
    enabled = false,
    onUpdate,
  } = options;

  const queryClient = useQueryClient();
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!enabled) {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
        setIsConnected(false);
      }
      return;
    }

    const eventSource = new EventSource(endpoint);
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      setIsConnected(true);
    };

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setLastUpdate(new Date());

        // Update query cache
        queryClient.setQueryData<HolographicDataset>(
          ["holographic-data"],
          (old) => {
            if (!old) return old;
            return { ...old, ...data };
          }
        );

        onUpdate?.(data);
      } catch (_err) {
        // console.error("Failed to parse real-time update:", _err);
      }
    };

    eventSource.onerror = () => {
      setIsConnected(false);
      // Attempt reconnect after delay
      setTimeout(() => {
        if (eventSourceRef.current === eventSource) {
          eventSource.close();
          eventSourceRef.current = null;
        }
      }, 5000);
    };

    return () => {
      eventSource.close();
      eventSourceRef.current = null;
      setIsConnected(false);
    };
  }, [enabled, endpoint, onUpdate, queryClient]);

  return {
    isConnected,
    lastUpdate,
  };
}

// ============================================================================
// usePointInteraction - Point selection and hover handling
// ============================================================================

interface PointInteractionState {
  selectedPoint: ManifoldPoint | null;
  hoveredPoint: ManifoldPoint | null;
}

export function usePointInteraction(points: ManifoldPoint[] | undefined) {
  const [state, setState] = useState<PointInteractionState>({
    selectedPoint: null,
    hoveredPoint: null,
  });

  const pointMap = useMemo(() => {
    const map = new Map<string, ManifoldPoint>();
    if (points) {
      for (const point of points) {
        map.set(point.id, point);
      }
    }
    return map;
  }, [points]);

  const selectPoint = useCallback(
    (pointId: string | null) => {
      const point = pointId ? pointMap.get(pointId) || null : null;
      setState((prev) => ({ ...prev, selectedPoint: point }));
    },
    [pointMap]
  );

  const hoverPoint = useCallback(
    (pointId: string | null) => {
      const point = pointId ? pointMap.get(pointId) || null : null;
      setState((prev) => ({ ...prev, hoveredPoint: point }));
    },
    [pointMap]
  );

  const clearSelection = useCallback(() => {
    setState({ selectedPoint: null, hoveredPoint: null });
  }, []);

  return {
    ...state,
    selectPoint,
    hoverPoint,
    clearSelection,
  };
}
