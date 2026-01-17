"use client";

/**
 * Brane Topology Visualization Page
 *
 * Exotic 3D visualization of residency scheduling using brane-theory metaphor.
 * Three dimensional layers represent different system states:
 *
 * - BRANE ALPHA (Ideal): The bureaucratic perfect state
 * - BRANE BETA (Real-time): Current operational reality
 * - BRANE OMEGA (Collapse): Systemic decay state
 *
 * The entropy slider simulates faculty attrition, showing how the system
 * degrades from deterministic state toward probabilistic chaos.
 *
 * @route /admin/visualizations/brane-topology
 */

import React from "react";
import dynamic from "next/dynamic";

// Dynamic import for Three.js component (no SSR - needs WebGL)
const BraneTopologyVisualizer = dynamic(
  () =>
    import("@/features/brane-topology").then(
      (mod) => mod.BraneTopologyVisualizer
    ),
  {
    ssr: false,
    loading: () => <LoadingScreen />,
  }
);

/**
 * Loading screen while WebGL initializes
 */
const LoadingScreen: React.FC = () => (
  <div className="fixed inset-0 z-50 flex items-center justify-center bg-black">
    <div className="text-center">
      <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-cyan-500 border-t-transparent" />
      <p className="mt-4 text-sm uppercase tracking-widest text-cyan-400">
        Initializing Brane Topology...
      </p>
      <p className="mt-2 text-xs text-slate-600">
        Projecting multi-dimensional scheduling manifold
      </p>
    </div>
  </div>
);

export default function BraneTopologyPage() {
  return <BraneTopologyVisualizer />;
}
