/**
 * Tests for Holographic Hub Hooks
 */

import { renderHook, act, waitFor } from "@testing-library/react";
import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import {
  useHolographicState,
  useFilteredManifoldPoints,
  usePointInteraction,
} from "../hooks";
import { ManifoldPoint, LayerVisibility, ConstraintVisibility } from "../types";

// Create wrapper for hooks that need QueryClient
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  const Wrapper = ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: queryClient }, children);
  Wrapper.displayName = "TestQueryWrapper";
  return Wrapper;
};

describe("useHolographicState", () => {
  it("initializes with default state", () => {
    const { result } = renderHook(() => useHolographicState());

    expect(result.current.state.layerVisibility.quantum).toBe(true);
    expect(result.current.state.constraintVisibility.acgme).toBe(true);
    expect(result.current.state.isAnimating).toBe(true);
    expect(result.current.state.selectedPointId).toBeNull();
  });

  it("toggles layer visibility", () => {
    const { result } = renderHook(() => useHolographicState());

    expect(result.current.state.layerVisibility.quantum).toBe(true);

    act(() => {
      result.current.toggleLayer("quantum");
    });

    expect(result.current.state.layerVisibility.quantum).toBe(false);

    act(() => {
      result.current.toggleLayer("quantum");
    });

    expect(result.current.state.layerVisibility.quantum).toBe(true);
  });

  it("toggles constraint visibility", () => {
    const { result } = renderHook(() => useHolographicState());

    expect(result.current.state.constraintVisibility.acgme).toBe(true);

    act(() => {
      result.current.toggleConstraint("acgme");
    });

    expect(result.current.state.constraintVisibility.acgme).toBe(false);
  });

  it("selects and deselects points", () => {
    const { result } = renderHook(() => useHolographicState());

    act(() => {
      result.current.selectPoint("point-1");
    });

    expect(result.current.state.selectedPointId).toBe("point-1");

    act(() => {
      result.current.selectPoint(null);
    });

    expect(result.current.state.selectedPointId).toBeNull();
  });

  it("hovers points", () => {
    const { result } = renderHook(() => useHolographicState());

    act(() => {
      result.current.hoverPoint("point-1");
    });

    expect(result.current.state.hoveredPointId).toBe("point-1");
  });

  it("toggles animation", () => {
    const { result } = renderHook(() => useHolographicState());

    expect(result.current.state.isAnimating).toBe(true);

    act(() => {
      result.current.setAnimating(false);
    });

    expect(result.current.state.isAnimating).toBe(false);
  });

  it("sets animation speed with bounds", () => {
    const { result } = renderHook(() => useHolographicState());

    act(() => {
      result.current.setAnimationSpeed(2.5);
    });

    expect(result.current.state.animationSpeed).toBe(2.5);

    // Test upper bound
    act(() => {
      result.current.setAnimationSpeed(10);
    });

    expect(result.current.state.animationSpeed).toBe(3);

    // Test lower bound
    act(() => {
      result.current.setAnimationSpeed(-1);
    });

    expect(result.current.state.animationSpeed).toBe(0);
  });

  it("sets all layers visible/hidden", () => {
    const { result } = renderHook(() => useHolographicState());

    act(() => {
      result.current.setAllLayersVisible(false);
    });

    expect(result.current.state.layerVisibility.quantum).toBe(false);
    expect(result.current.state.layerVisibility.temporal).toBe(false);
    expect(result.current.state.layerVisibility.evolutionary).toBe(false);

    act(() => {
      result.current.setAllLayersVisible(true);
    });

    expect(result.current.state.layerVisibility.quantum).toBe(true);
    expect(result.current.state.layerVisibility.temporal).toBe(true);
    expect(result.current.state.layerVisibility.evolutionary).toBe(true);
  });

  it("sets all constraints visible/hidden", () => {
    const { result } = renderHook(() => useHolographicState());

    act(() => {
      result.current.setAllConstraintsVisible(false);
    });

    expect(result.current.state.constraintVisibility.acgme).toBe(false);
    expect(result.current.state.constraintVisibility.fairness).toBe(false);

    act(() => {
      result.current.setAllConstraintsVisible(true);
    });

    expect(result.current.state.constraintVisibility.acgme).toBe(true);
    expect(result.current.state.constraintVisibility.fairness).toBe(true);
  });

  it("sets quality level", () => {
    const { result } = renderHook(() => useHolographicState());

    act(() => {
      result.current.setQuality("ultra");
    });

    expect(result.current.state.quality).toBe("ultra");
  });

  it("accepts initial state", () => {
    const { result } = renderHook(() =>
      useHolographicState({
        isAnimating: false,
        quality: "high",
      })
    );

    expect(result.current.state.isAnimating).toBe(false);
    expect(result.current.state.quality).toBe("high");
  });
});

describe("useFilteredManifoldPoints", () => {
  const mockPoints: ManifoldPoint[] = [
    {
      id: "p1",
      constraintId: "c1",
      type: "acgme",
      layer: "quantum",
      position: { x: 0, y: 0, z: 0 },
      projectionConfidence: 0.9,
      visual: { color: [1, 0, 0], opacity: 1, size: 1, glowIntensity: 0.5 },
      status: {
        isSatisfied: false,
        isViolated: true,
        isCritical: false,
        tension: 0.5,
      },
      severity: 0.5,
      label: "Point 1",
    },
    {
      id: "p2",
      constraintId: "c2",
      type: "fairness",
      layer: "temporal",
      position: { x: 1, y: 1, z: 1 },
      projectionConfidence: 0.8,
      visual: { color: [0, 0, 1], opacity: 1, size: 1, glowIntensity: 0.3 },
      status: {
        isSatisfied: true,
        isViolated: false,
        isCritical: false,
        tension: 0.1,
      },
      severity: 0.1,
      label: "Point 2",
    },
    {
      id: "p3",
      constraintId: "c3",
      type: "acgme",
      layer: "temporal",
      position: { x: 2, y: 2, z: 2 },
      projectionConfidence: 0.7,
      visual: { color: [1, 0, 0], opacity: 1, size: 1, glowIntensity: 0.8 },
      status: {
        isSatisfied: false,
        isViolated: true,
        isCritical: true,
        tension: 0.9,
      },
      severity: 0.9,
      label: "Point 3",
    },
  ];

  const allLayersVisible: LayerVisibility = {
    quantum: true,
    temporal: true,
    topological: true,
    spectral: true,
    evolutionary: true,
    gravitational: true,
    phase: true,
    thermodynamic: true,
  };

  const allConstraintsVisible: ConstraintVisibility = {
    acgme: true,
    fairness: true,
    fatigue: true,
    temporal: true,
    preference: true,
    coverage: true,
    skill: true,
    custom: true,
  };

  it("returns all points when all filters are visible", () => {
    const { result } = renderHook(() =>
      useFilteredManifoldPoints(
        mockPoints,
        allLayersVisible,
        allConstraintsVisible
      )
    );

    expect(result.current.length).toBe(3);
  });

  it("filters by layer visibility", () => {
    const layerVisibility = {
      ...allLayersVisible,
      quantum: false,
    };

    const { result } = renderHook(() =>
      useFilteredManifoldPoints(
        mockPoints,
        layerVisibility,
        allConstraintsVisible
      )
    );

    // Should exclude point 1 (quantum layer)
    expect(result.current.length).toBe(2);
    expect(result.current.find((p) => p.id === "p1")).toBeUndefined();
  });

  it("filters by constraint visibility", () => {
    const constraintVisibility = {
      ...allConstraintsVisible,
      acgme: false,
    };

    const { result } = renderHook(() =>
      useFilteredManifoldPoints(
        mockPoints,
        allLayersVisible,
        constraintVisibility
      )
    );

    // Should exclude points 1 and 3 (acgme type)
    expect(result.current.length).toBe(1);
    expect(result.current[0].id).toBe("p2");
  });

  it("applies both filters simultaneously", () => {
    const layerVisibility = {
      ...allLayersVisible,
      quantum: false,
    };
    const constraintVisibility = {
      ...allConstraintsVisible,
      fairness: false,
    };

    const { result } = renderHook(() =>
      useFilteredManifoldPoints(
        mockPoints,
        layerVisibility,
        constraintVisibility
      )
    );

    // Should only include point 3 (temporal layer, acgme type)
    expect(result.current.length).toBe(1);
    expect(result.current[0].id).toBe("p3");
  });

  it("returns empty array when all filters are off", () => {
    const layerVisibility = Object.fromEntries(
      Object.keys(allLayersVisible).map((k) => [k, false])
    ) as LayerVisibility;

    const { result } = renderHook(() =>
      useFilteredManifoldPoints(
        mockPoints,
        layerVisibility,
        allConstraintsVisible
      )
    );

    expect(result.current.length).toBe(0);
  });

  it("returns empty array for undefined points", () => {
    const { result } = renderHook(() =>
      useFilteredManifoldPoints(undefined, allLayersVisible, allConstraintsVisible)
    );

    expect(result.current).toEqual([]);
  });
});

describe("usePointInteraction", () => {
  const mockPoints: ManifoldPoint[] = [
    {
      id: "p1",
      constraintId: "c1",
      type: "acgme",
      layer: "quantum",
      position: { x: 0, y: 0, z: 0 },
      projectionConfidence: 0.9,
      visual: { color: [1, 0, 0], opacity: 1, size: 1, glowIntensity: 0.5 },
      status: {
        isSatisfied: false,
        isViolated: true,
        isCritical: false,
        tension: 0.5,
      },
      severity: 0.5,
      label: "Point 1",
    },
    {
      id: "p2",
      constraintId: "c2",
      type: "fairness",
      layer: "temporal",
      position: { x: 1, y: 1, z: 1 },
      projectionConfidence: 0.8,
      visual: { color: [0, 0, 1], opacity: 1, size: 1, glowIntensity: 0.3 },
      status: {
        isSatisfied: true,
        isViolated: false,
        isCritical: false,
        tension: 0.1,
      },
      severity: 0.1,
      label: "Point 2",
    },
  ];

  it("initializes with null selected and hovered points", () => {
    const { result } = renderHook(() => usePointInteraction(mockPoints));

    expect(result.current.selectedPoint).toBeNull();
    expect(result.current.hoveredPoint).toBeNull();
  });

  it("selects a point by ID", () => {
    const { result } = renderHook(() => usePointInteraction(mockPoints));

    act(() => {
      result.current.selectPoint("p1");
    });

    expect(result.current.selectedPoint?.id).toBe("p1");
    expect(result.current.selectedPoint?.label).toBe("Point 1");
  });

  it("hovers a point by ID", () => {
    const { result } = renderHook(() => usePointInteraction(mockPoints));

    act(() => {
      result.current.hoverPoint("p2");
    });

    expect(result.current.hoveredPoint?.id).toBe("p2");
    expect(result.current.hoveredPoint?.label).toBe("Point 2");
  });

  it("clears selection and hover", () => {
    const { result } = renderHook(() => usePointInteraction(mockPoints));

    act(() => {
      result.current.selectPoint("p1");
      result.current.hoverPoint("p2");
    });

    expect(result.current.selectedPoint).not.toBeNull();
    expect(result.current.hoveredPoint).not.toBeNull();

    act(() => {
      result.current.clearSelection();
    });

    expect(result.current.selectedPoint).toBeNull();
    expect(result.current.hoveredPoint).toBeNull();
  });

  it("handles selecting non-existent point", () => {
    const { result } = renderHook(() => usePointInteraction(mockPoints));

    act(() => {
      result.current.selectPoint("non-existent");
    });

    expect(result.current.selectedPoint).toBeNull();
  });

  it("handles undefined points array", () => {
    const { result } = renderHook(() => usePointInteraction(undefined));

    act(() => {
      result.current.selectPoint("p1");
    });

    expect(result.current.selectedPoint).toBeNull();
  });
});
