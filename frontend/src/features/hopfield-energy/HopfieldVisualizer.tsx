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
 * - Real API data integration for actual schedule metrics
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
import type { StabilityLevel } from '@/api/exotic-resilience';

/**
 * Get color scheme for stability level from API
 */
function getStabilityColor(level: StabilityLevel): {
  bg: string;
  text: string;
  border: string;
  label: string;
} {
  switch (level) {
    case 'very_stable':
      return {
        bg: 'bg-emerald-900/40',
        text: 'text-emerald-400',
        border: 'border-emerald-700/50',
        label: 'Very Stable',
      };
    case 'stable':
      return {
        bg: 'bg-green-900/40',
        text: 'text-green-400',
        border: 'border-green-700/50',
        label: 'Stable',
      };
    case 'marginally_stable':
      return {
        bg: 'bg-amber-900/40',
        text: 'text-amber-400',
        border: 'border-amber-700/50',
        label: 'Marginally Stable',
      };
    case 'unstable':
      return {
        bg: 'bg-orange-900/40',
        text: 'text-orange-400',
        border: 'border-orange-700/50',
        label: 'Unstable',
      };
    case 'highly_unstable':
      return {
        bg: 'bg-red-900/40',
        text: 'text-red-400',
        border: 'border-red-700/50',
        label: 'Highly Unstable',
      };
    default:
      return {
        bg: 'bg-slate-900/40',
        text: 'text-slate-400',
        border: 'border-slate-700/50',
        label: 'Unknown',
      };
  }
}

/**
 * Format timestamp for display
 */
function formatTimestamp(isoString: string): string {
  try {
    return new Date(isoString).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return 'Unknown';
  }
}

export function HopfieldVisualizer({
  initialCoverage = 50,
  initialBalance = 50,
  showControls = true,
  className = '',
  apiData,
  isLoading = false,
  error = null,
  onAnalyze,
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
    <div className={`relative w-full h-screen bg-[#0f0f1a] ${className}`}>
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

      {/* API Metrics Panel */}
      <div className="absolute top-4 right-4 max-w-sm">
        {/* Loading State */}
        {isLoading && (
          <div className="bg-slate-950/90 border border-slate-800 p-4 rounded-xl backdrop-blur-md text-white">
            <div className="flex items-center gap-3">
              <div className="w-5 h-5 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />
              <span className="text-sm text-slate-300">Analyzing schedule...</span>
            </div>
          </div>
        )}

        {/* Error State */}
        {error && !isLoading && (
          <div className="bg-red-950/90 border border-red-800 p-4 rounded-xl backdrop-blur-md text-white">
            <h3 className="text-sm font-semibold text-red-300 mb-2">Analysis Error</h3>
            <p className="text-xs text-red-400">{error}</p>
            {onAnalyze && (
              <button
                onClick={onAnalyze}
                className="mt-3 px-3 py-1.5 text-xs bg-red-800/50 hover:bg-red-800/70 rounded transition-colors"
              >
                Retry
              </button>
            )}
          </div>
        )}

        {/* API Data Display */}
        {apiData && !isLoading && !error && (
          <div className={`border p-4 rounded-xl backdrop-blur-md text-white ${getStabilityColor(apiData.stabilityLevel as StabilityLevel).bg} ${getStabilityColor(apiData.stabilityLevel as StabilityLevel).border}`}>
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-slate-200">Schedule Analysis</h3>
              <span className={`px-2 py-1 text-xs rounded-full border ${getStabilityColor(apiData.stabilityLevel as StabilityLevel).text} ${getStabilityColor(apiData.stabilityLevel as StabilityLevel).border}`}>
                {getStabilityColor(apiData.stabilityLevel as StabilityLevel).label}
              </span>
            </div>

            {/* Key Metrics */}
            <div className="grid grid-cols-2 gap-3 mb-4">
              <div className="bg-black/20 rounded p-2">
                <div className="text-xs text-slate-400">Total Energy</div>
                <div className={`text-lg font-bold ${getStabilityColor(apiData.stabilityLevel as StabilityLevel).text}`}>
                  {apiData.metrics.totalEnergy.toFixed(3)}
                </div>
              </div>
              <div className="bg-black/20 rounded p-2">
                <div className="text-xs text-slate-400">Stability Score</div>
                <div className={`text-lg font-bold ${getStabilityColor(apiData.stabilityLevel as StabilityLevel).text}`}>
                  {(apiData.metrics.stabilityScore * 100).toFixed(0)}%
                </div>
              </div>
              <div className="bg-black/20 rounded p-2">
                <div className="text-xs text-slate-400">Assignments</div>
                <div className="text-lg font-bold text-slate-200">{apiData.assignmentsAnalyzed}</div>
              </div>
              <div className="bg-black/20 rounded p-2">
                <div className="text-xs text-slate-400">Local Minimum</div>
                <div className={`text-lg font-bold ${apiData.metrics.isLocalMinimum ? 'text-emerald-400' : 'text-amber-400'}`}>
                  {apiData.metrics.isLocalMinimum ? 'Yes' : 'No'}
                </div>
              </div>
            </div>

            {/* Interpretation */}
            <div className="mb-4 p-3 bg-black/20 rounded">
              <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-1">Analysis</h4>
              <p className="text-xs text-slate-300 leading-relaxed">{apiData.interpretation}</p>
            </div>

            {/* Recommendations */}
            {apiData.recommendations && apiData.recommendations.length > 0 && (
              <div className="mb-3">
                <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-2">Recommendations</h4>
                <ul className="space-y-1">
                  {apiData.recommendations.slice(0, 3).map((rec, idx) => (
                    <li key={idx} className="flex gap-2 text-xs">
                      <span className="text-cyan-400 flex-shrink-0">•</span>
                      <span className="text-slate-300">{rec}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Metadata */}
            <div className="pt-2 border-t border-slate-700/30 flex justify-between text-xs text-slate-500">
              <span>{formatTimestamp(apiData.analyzedAt)}</span>
              <span>{apiData.periodStart} - {apiData.periodEnd}</span>
            </div>
          </div>
        )}

        {/* Analyze Button (when no data and not loading) */}
        {!apiData && !isLoading && !error && onAnalyze && (
          <button
            onClick={onAnalyze}
            className="bg-cyan-900/40 hover:bg-cyan-900/60 border border-cyan-700/50 px-4 py-3 rounded-xl backdrop-blur-md text-white transition-colors"
          >
            <div className="flex items-center gap-2">
              <span className="text-lg">🔬</span>
              <span className="text-sm font-medium">Analyze Schedule</span>
            </div>
          </button>
        )}
      </div>

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
