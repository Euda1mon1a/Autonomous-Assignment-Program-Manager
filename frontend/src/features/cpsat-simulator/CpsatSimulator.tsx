/**
 * CP-SAT Simulator
 *
 * 3D visualization of constraint programming solver behavior.
 * Shows how OR-Tools CP-SAT explores a multi-modal optimization landscape.
 *
 * Features:
 * - 3D cost function surface with multiple local minima
 * - Animated solver agent traversing the search space
 * - Real-time metrics (objective, gap, branches, status)
 * - Optional AI narration of solver behavior
 * - Interactive landscape configuration
 */

"use client";

import React, { useState, useCallback, useEffect, useRef, Suspense } from "react";
import { Canvas } from "@react-three/fiber";
import {
  PerspectiveCamera,
  OrbitControls,
  Stars,
  Environment,
} from "@react-three/drei";

import {
  CpsatSimulatorProps,
  SolverMetrics,
  LandscapeConfig,
  ChatMessage,
} from "./types";
import { DEFAULT_CONFIG, DEFAULT_METRICS, getStatusDescription } from "./constants";
import { Landscape } from "./components/Landscape";
import { SolverAgent } from "./components/SolverAgent";
import { HUD } from "./components/HUD";
import { ControlPanel } from "./components/ControlPanel";

export function CpsatSimulator({
  initialConfig = DEFAULT_CONFIG,
  showHud = true,
  showControls = true,
  className = "",
}: CpsatSimulatorProps): JSX.Element {
  const [metrics, setMetrics] = useState<SolverMetrics>(DEFAULT_METRICS);
  const [config, setConfig] = useState<LandscapeConfig>(initialConfig);
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [loadingAI, setLoadingAI] = useState(false);

  // Track mounted state to prevent state updates after unmount
  const mountedRef = useRef(true);
  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  // Initial AI greeting (using fallback descriptions)
  useEffect(() => {
    const initAI = async () => {
      if (!mountedRef.current) return;
      setLoadingAI(true);
      // Simulate AI delay
      await new Promise((resolve) => setTimeout(resolve, 500));
      if (!mountedRef.current) return;
      const explanation =
        "Optimization node online. Traversing the constraint satisfaction manifold. " +
        "Seeking global minimum across multi-modal terrain.";
      setChatHistory([{ role: "assistant", content: explanation }]);
      setLoadingAI(false);
    };
    initAI();
  }, []);

  const handleUpdateMetrics = useCallback((newMetrics: Partial<SolverMetrics>) => {
    setMetrics((prev) => ({ ...prev, ...newMetrics }));
  }, []);

  const handleScenarioPrompt = async (prompt: string) => {
    if (!mountedRef.current) return;
    setLoadingAI(true);
    setChatHistory((prev) => [...prev, { role: "user", content: prompt }]);

    // Simulate AI processing
    await new Promise((resolve) => setTimeout(resolve, 800));
    if (!mountedRef.current) return;

    // Generate new config based on prompt keywords
    const newConfig: LandscapeConfig = {
      complexity: prompt.includes("complex") ? 0.9 : 0.5,
      noiseScale: prompt.includes("rough") ? 2.0 : 1.0,
      amplitude: prompt.includes("deep") ? 8.0 : 4.0,
    };
    setConfig(newConfig);

    // Generate response
    const explanation = `Topology reconfigured. ${getStatusDescription(metrics.status)} New landscape parameters applied.`;
    setChatHistory((prev) => [...prev, { role: "assistant", content: explanation }]);
    setLoadingAI(false);
  };

  const handleRefreshExplain = async () => {
    if (!mountedRef.current) return;
    setLoadingAI(true);
    await new Promise((resolve) => setTimeout(resolve, 500));
    if (!mountedRef.current) return;
    const explanation = getStatusDescription(metrics.status);
    setChatHistory((prev) => [...prev, { role: "assistant", content: explanation }]);
    setLoadingAI(false);
  };

  return (
    <div
      className={`relative h-screen w-full select-none bg-black ${className}`}
    >
      {/* 3D Canvas */}
      <Canvas shadows gl={{ antialias: true }}>
        <PerspectiveCamera makeDefault position={[30, 20, 30]} fov={40} />
        <color attach="background" args={["#000"]} />

        {/* Starfield */}
        <Stars
          radius={100}
          depth={50}
          count={6000}
          factor={6}
          saturation={0}
          fade
          speed={1.5}
        />
        <fog attach="fog" args={["#000", 30, 90]} />

        {/* Lighting */}
        <ambientLight intensity={0.3} />
        <pointLight position={[20, 40, 20]} intensity={1.5} color="#00f2ff" />
        <spotLight
          position={[0, 50, 0]}
          intensity={0.5}
          angle={0.5}
          penumbra={1}
          castShadow
        />

        <Suspense fallback={null}>
          <Landscape config={config} />
          <SolverAgent config={config} onUpdate={handleUpdateMetrics} />
          <Environment preset="night" />
        </Suspense>

        <OrbitControls
          enablePan={false}
          maxDistance={60}
          minDistance={15}
          maxPolarAngle={Math.PI / 2.1}
        />
      </Canvas>

      {/* UI Layers */}
      {showHud && (
        <HUD metrics={metrics} history={chatHistory} loading={loadingAI} />
      )}

      {showControls && (
        <ControlPanel
          onScenarioPrompt={handleScenarioPrompt}
          onRefreshExplain={handleRefreshExplain}
        />
      )}

      {/* System status decals */}
      <div className="pointer-events-none absolute bottom-8 right-8 select-none text-right opacity-40">
        <div className="mb-1 text-[10px] uppercase tracking-[0.4em] text-slate-500">
          Distributed Compute Mesh
        </div>
        <div className="font-mono text-[14px] font-bold tracking-[0.2em] text-cyan-500">
          NODE_7742_OPTIMIZER_v4.2.1
        </div>
      </div>

      {/* Grid overlay */}
      <div className="pointer-events-none absolute inset-0 border-[40px] border-white/[0.02] mix-blend-overlay" />

      {/* Scanline effect */}
      <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.25)_50%),linear-gradient(90deg,rgba(255,0,0,0.06),rgba(0,255,0,0.02),rgba(0,0,255,0.06))] bg-[length:100%_2px,3px_100%] opacity-10" />
    </div>
  );
}

export default CpsatSimulator;
