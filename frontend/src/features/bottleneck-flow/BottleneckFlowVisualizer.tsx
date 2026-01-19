/**
 * Bottleneck Flow Visualizer
 *
 * Main wrapper component for the 3D supervision cascade visualization.
 * Combines data fetching, simulation state, 3D scene, and UI overlay.
 *
 * @route Part of /admin/labs/optimization
 */

'use client';

import { useRef, useEffect, Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Stars } from '@react-three/drei';
import { useFaculty, useResidents } from '@/hooks/usePeople';
import { useBottleneckData } from './hooks/useBottleneckData';
import { useBottleneckSimulation } from './hooks/useBottleneckSimulation';
import { SimulationScene } from './components/SimulationScene';
import { UIOverlay } from './components/UIOverlay';
import type { BottleneckFlowVisualizerProps } from './types';

/**
 * Loading screen shown while data is being fetched.
 */
function LoadingScreen({ label }: { label: string }) {
  return (
    <div className="flex-1 flex items-center justify-center bg-[#0a0a0a] min-h-[400px]">
      <div className="text-center">
        <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-green-500 border-t-transparent" />
        <p className="mt-4 text-sm uppercase tracking-widest text-green-400">
          {label}
        </p>
      </div>
    </div>
  );
}

/**
 * Bottleneck Flow Visualizer
 *
 * Interactive 3D visualization of faculty-trainee supervision relationships.
 * Toggle faculty availability to see cascade effects:
 * - Trainees become orphaned, rerouted to backups, or at-risk
 * - Metrics show coverage percentage and affected counts
 *
 * @example
 * ```tsx
 * <BottleneckFlowVisualizer className="h-[600px]" />
 * ```
 */
export function BottleneckFlowVisualizer({
  className = '',
}: BottleneckFlowVisualizerProps) {
  const mountedRef = useRef(true);

  // Track mounted state to prevent updates after unmount
  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  // Fetch real data from existing hooks
  const { data: facultyData, isLoading: facultyLoading } = useFaculty();
  const { data: residentsData, isLoading: residentsLoading } = useResidents();

  // Transform API data to visualization format
  const { faculty, trainees } = useBottleneckData(facultyData, residentsData);

  // Simulation state management
  const {
    simState,
    metrics,
    handleToggleFaculty,
    handleToggleFix,
    handleReset,
    setMetrics,
  } = useBottleneckSimulation();

  // Show loading screen while fetching data
  if (facultyLoading || residentsLoading) {
    return <LoadingScreen label="Loading supervision network..." />;
  }

  return (
    <div className={`relative w-full h-screen bg-[#0a0a0a] ${className}`}>
      {/* 3D Canvas */}
      <Canvas
        camera={{ position: [30, 25, 50], fov: 60 }}
        dpr={[1, 2]}
        className="absolute inset-0"
      >
        <color attach="background" args={['#0a0a0a']} />

        <Suspense fallback={null}>
          <SimulationScene
            faculty={faculty}
            trainees={trainees}
            simState={simState}
            onMetricsUpdate={setMetrics}
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
          enableDamping
          dampingFactor={0.05}
          target={[0, 0, -30]}
          maxDistance={150}
          minDistance={10}
        />
      </Canvas>

      {/* 2D UI Overlay */}
      <UIOverlay
        metrics={metrics}
        simState={simState}
        faculty={faculty}
        onToggleFaculty={handleToggleFaculty}
        onToggleFix={handleToggleFix}
        onReset={handleReset}
      />
    </div>
  );
}

export default BottleneckFlowVisualizer;
