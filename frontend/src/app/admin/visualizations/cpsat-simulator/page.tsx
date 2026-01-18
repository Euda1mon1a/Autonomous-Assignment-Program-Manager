"use client";

/**
 * CP-SAT Simulator Page
 *
 * 3D visualization of constraint programming solver behavior.
 * Shows how OR-Tools CP-SAT explores a multi-modal optimization landscape.
 *
 * Features:
 * - 3D cost function surface with multiple local minima
 * - Animated solver agent traversing the search space
 * - Real-time metrics (objective, gap, branches, status)
 *
 * @route /admin/visualizations/cpsat-simulator
 */

import React from "react";
import dynamic from "next/dynamic";

// Dynamic import for Three.js component (no SSR - needs WebGL)
const CpsatSimulator = dynamic(
  () => import("@/features/cpsat-simulator").then((mod) => mod.CpsatSimulator),
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
        Initializing Optimization Node...
      </p>
      <p className="mt-2 text-xs text-slate-600">
        Generating multi-modal cost function landscape
      </p>
    </div>
  </div>
);

export default function CpsatSimulatorPage() {
  return <CpsatSimulator />;
}
