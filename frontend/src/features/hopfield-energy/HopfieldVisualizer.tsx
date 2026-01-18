/**
 * Hopfield Energy Landscape Visualizer
 *
 * 3D visualization of schedule stability using Hopfield network concepts.
 * Shows how schedules "settle" into stable states (attractors).
 *
 * Features:
 * - 3D energy surface with military color coding
 * - Ball representing current schedule state
 * - Gradient descent to find stable configurations
 * - Coverage and balance sliders
 *
 * @route Part of /admin/labs/optimization
 */

'use client';

import { useState, useCallback, useEffect, useRef, Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { PerspectiveCamera, OrbitControls, Stars } from '@react-three/drei';

import { computeEnergy, getReadinessStatus } from './constants';
import { EnergySurface } from './components/EnergySurface';
import { EnergyBall } from './components/EnergyBall';
import { ControlPanel } from './components/ControlPanel';
import type { HopfieldVisualizerProps, ReadinessStatus } from './types';

export function HopfieldVisualizer({
  initialCoverage = 50,
  initialBalance = 50,
  showControls = true,
  className = '',
}: HopfieldVisualizerProps): JSX.Element {
  const [coverage, setCoverage] = useState(initialCoverage);
  const [balance, setBalance] = useState(initialBalance);
  const [isSettling, setIsSettling] = useState(false);

  // Track mounted state to prevent updates after unmount
  const mountedRef = useRef(true);
  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  // Compute derived state
  const normalizedCoverage = coverage / 100;
  const normalizedBalance = balance / 100;
  const energy = computeEnergy(normalizedCoverage, normalizedBalance);

  // Compute min/max for status calculation (approximation)
  const minEnergy = computeEnergy(0.85, 0.85); // Near global min
  const maxEnergy = computeEnergy(0, 0); // Near max
  const normalizedEnergy = (energy - minEnergy) / (maxEnergy - minEnergy);
  const status: ReadinessStatus = getReadinessStatus(
    Math.max(0, Math.min(1, normalizedEnergy))
  );

  const handleCoverageChange = useCallback((value: number) => {
    setCoverage(value);
    setIsSettling(false);
  }, []);

  const handleBalanceChange = useCallback((value: number) => {
    setBalance(value);
    setIsSettling(false);
  }, []);

  const handleToggleSettle = useCallback(() => {
    setIsSettling((prev) => !prev);
  }, []);

  const handlePositionUpdate = useCallback((u: number, v: number) => {
    if (!mountedRef.current) return;
    setCoverage(u * 100);
    setBalance(v * 100);
  }, []);

  return (
    <div className={`relative w-full h-full bg-[#0f0f1a] ${className}`}>
      {/* 3D Canvas */}
      <Canvas shadows gl={{ antialias: true }}>
        <PerspectiveCamera makeDefault position={[4, 4, 4]} fov={60} />
        <color attach="background" args={['#0f0f1a']} />

        {/* Lighting */}
        <ambientLight intensity={0.4} />
        <directionalLight position={[5, 10, 5]} intensity={0.8} />
        <pointLight position={[-3, 3, -3]} intensity={0.5} color="#22c55e" />

        <Suspense fallback={null}>
          <EnergySurface />
          <EnergyBall
            coverage={normalizedCoverage}
            balance={normalizedBalance}
            isSettling={isSettling}
            onPositionUpdate={handlePositionUpdate}
          />
          <Stars
            radius={50}
            depth={50}
            count={2000}
            factor={4}
            saturation={0}
            fade
            speed={1}
          />
        </Suspense>

        <OrbitControls
          enablePan={false}
          maxDistance={12}
          minDistance={3}
          autoRotate={!isSettling}
          autoRotateSpeed={0.3}
        />
      </Canvas>

      {/* Control Panel */}
      {showControls && (
        <ControlPanel
          coverage={coverage}
          balance={balance}
          energy={energy}
          status={status}
          isSettling={isSettling}
          onCoverageChange={handleCoverageChange}
          onBalanceChange={handleBalanceChange}
          onToggleSettle={handleToggleSettle}
        />
      )}

      {/* Info Panel */}
      <div className="absolute bottom-4 right-4 max-w-xs bg-slate-950/90 border border-slate-800 p-4 rounded-xl backdrop-blur-md text-white">
        <h3 className="text-sm font-semibold text-green-300 mb-2">
          What is this?
        </h3>
        <p className="text-xs text-slate-400 leading-relaxed">
          Hopfield networks model how systems &quot;settle&quot; into stable states
          (attractors). The ball represents the current schedule—it rolls toward
          energy minima where coverage is high and workload is balanced. Military
          color coding shows operational readiness at a glance.
        </p>
      </div>
    </div>
  );
}

export default HopfieldVisualizer;
