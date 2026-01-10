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
} from "./types";
import {
  generateMockHolographicData,
  buildHolographicDataset,
} from "./data-pipeline";

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
      } catch (err) {
        // console.error("Failed to parse real-time update:", err);
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
