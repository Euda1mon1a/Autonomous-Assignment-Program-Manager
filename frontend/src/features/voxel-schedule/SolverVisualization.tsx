'use client';

/**
 * SolverVisualization - Real-Time CP-SAT Solver Visualization
 *
 * This component demonstrates the integration of all pieces for
 * watching the CP-SAT solver work in real-time:
 *
 * 1. WebSocket subscription to solver progress
 * 2. Delta-based solution updates
 * 3. Animated transitions between solutions
 * 4. High-performance instanced rendering
 *
 * Usage:
 *   <SolverVisualization taskId={scheduleRunId} />
 *
 * @module features/voxel-schedule/SolverVisualization
 */

import React, { useState, useCallback, useMemo, useEffect } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Grid, Text, Html, Stats } from '@react-three/drei';

import {
  InstancedVoxelRenderer,
  VoxelInstance,
  ACTIVITY_COLORS,
  ACTIVITY_NAMES,
} from './InstancedVoxelRenderer';
import {
  useSolutionTransitions,
  SolutionDelta,
} from './useSolutionTransitions';
import {
  useSolverWebSocket,
  Assignment,
  SolverMetrics,
} from './useSolverWebSocket';

// ============================================================================
// Types
// ============================================================================

interface SolverVisualizationProps {
  /** Solver task ID to subscribe to */
  taskId: string | null;
  /** Person index mapping (personId -> y position) */
  personIndex?: Map<string, number>;
  /** Block index mapping (blockId -> x position) */
  blockIndex?: Map<string, number>;
  /** Template to activity layer mapping */
  templateToLayer?: Map<string, number>;
  /** Show performance stats */
  showStats?: boolean;
  /** Callback when visualization is ready */
  onReady?: () => void;
}

// ============================================================================
// Sub-Components
// ============================================================================

/**
 * Progress overlay showing solver metrics.
 */
const ProgressOverlay: React.FC<{
  metrics: SolverMetrics | null;
  status: string;
  voxelCount: number;
}> = ({ metrics, status, voxelCount }) => {
  if (!metrics && status === 'idle') return null;

  const statusColors: Record<string, string> = {
    idle: 'bg-gray-500',
    solving: 'bg-blue-500',
    complete: 'bg-green-500',
    error: 'bg-red-500',
  };

  return (
    <div className="absolute top-4 left-4 bg-slate-900/90 backdrop-blur-md rounded-xl p-4 text-white min-w-[280px] border border-slate-700/50 shadow-2xl">
      <div className="flex items-center gap-3 mb-3">
        <div
          className={`w-3 h-3 rounded-full ${statusColors[status] || 'bg-gray-500'} ${
            status === 'solving' ? 'animate-pulse' : ''
          }`}
        />
        <span className="font-bold text-lg capitalize">{status}</span>
      </div>

      {metrics && (
        <>
          {/* Progress bar */}
          <div className="mb-3">
            <div className="flex justify-between text-xs text-slate-400 mb-1">
              <span>Progress</span>
              <span>{metrics.progressPct.toFixed(1)}%</span>
            </div>
            <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-blue-500 to-green-500 transition-all duration-300"
                style={{ width: `${metrics.progressPct}%` }}
              />
            </div>
          </div>

          {/* Metrics grid */}
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <div className="text-slate-400 text-xs">Solutions</div>
              <div className="font-mono text-lg">{metrics.solutionsFound}</div>
            </div>
            <div>
              <div className="text-slate-400 text-xs">Optimality Gap</div>
              <div className="font-mono text-lg">
                {metrics.optimalityGapPct.toFixed(1)}%
              </div>
            </div>
            <div>
              <div className="text-slate-400 text-xs">Assignments</div>
              <div className="font-mono text-lg">{voxelCount}</div>
            </div>
            <div>
              <div className="text-slate-400 text-xs">Elapsed</div>
              <div className="font-mono text-lg">
                {metrics.elapsedSeconds.toFixed(1)}s
              </div>
            </div>
          </div>

          {metrics.isOptimal && (
            <div className="mt-3 text-center text-green-400 font-bold text-sm border-t border-slate-700 pt-3">
              ✓ OPTIMAL SOLUTION FOUND
            </div>
          )}
        </>
      )}
    </div>
  );
};

/**
 * Legend showing activity layer colors.
 */
const Legend: React.FC = () => (
  <div className="absolute bottom-4 right-4 bg-slate-900/90 backdrop-blur-md rounded-xl p-4 border border-slate-700/50 shadow-2xl">
    <h4 className="font-bold text-white mb-3 text-sm uppercase tracking-wider">
      Activity Layers
    </h4>
    <div className="space-y-2">
      {Object.entries(ACTIVITY_NAMES).map(([index, name]) => (
        <div key={index} className="flex items-center gap-2">
          <div
            className="w-3 h-3 rounded shadow-sm"
            style={{ backgroundColor: ACTIVITY_COLORS[Number(index)] }}
          />
          <span className="text-slate-300 text-xs">{name}</span>
        </div>
      ))}
    </div>
  </div>
);

/**
 * 3D grid system with axis labels.
 */
const GridSystem: React.FC<{
  xLabels: string[];
  yLabels: string[];
  zLabels: string[];
  spacing: number;
}> = ({ xLabels, yLabels, zLabels, spacing }) => {
  return (
    <group>
      {/* Floor grid */}
      <Grid
        position={[
          (xLabels.length * spacing) / 2 - spacing / 2,
          -0.5,
          (zLabels.length * spacing) / 2 - spacing / 2,
        ]}
        args={[xLabels.length * spacing + 2, zLabels.length * spacing + 2]}
        cellSize={spacing}
        cellThickness={0.5}
        cellColor="#334155"
        sectionSize={spacing * 5}
        sectionThickness={1}
        sectionColor="#475569"
        fadeDistance={50}
      />

      {/* X-axis labels (Time/Blocks) */}
      {xLabels.slice(0, 20).map((label, i) => (
        <Text
          key={`x-${i}`}
          position={[i * spacing, -0.5, -1.5]}
          rotation={[-Math.PI / 4, 0, 0]}
          fontSize={0.25}
          color="#94a3b8"
          anchorX="center"
        >
          {label}
        </Text>
      ))}

      {/* Y-axis labels (People) */}
      {yLabels.slice(0, 30).map((label, i) => (
        <Text
          key={`y-${i}`}
          position={[-1.5, i * spacing, 0]}
          fontSize={0.25}
          color="#94a3b8"
          anchorX="right"
        >
          {label.slice(0, 12)}
        </Text>
      ))}

      {/* Z-axis labels (Activities) */}
      {zLabels.map((label, i) => (
        <Text
          key={`z-${i}`}
          position={[-1, -0.5, i * spacing]}
          rotation={[0, Math.PI / 4, 0]}
          fontSize={0.2}
          color="#64748b"
          anchorX="right"
        >
          {label}
        </Text>
      ))}
    </group>
  );
};

// ============================================================================
// Main Component
// ============================================================================

/**
 * Real-time solver visualization component.
 *
 * Connects all pieces:
 * - WebSocket for solver updates
 * - Transition animations for solution changes
 * - Instanced rendering for performance
 *
 * @example
 * ```tsx
 * <SolverVisualization
 *   taskId={scheduleRunId}
 *   personIndex={personIndexMap}
 *   blockIndex={blockIndexMap}
 *   templateToLayer={templateLayerMap}
 * />
 * ```
 */
export const SolverVisualization: React.FC<SolverVisualizationProps> = ({
  taskId,
  personIndex: propPersonIndex,
  blockIndex: propBlockIndex,
  templateToLayer: propTemplateToLayer,
  showStats = false,
  onReady,
}) => {
  // Demo data for when indices aren't provided
  const personIndex = useMemo(
    () =>
      propPersonIndex ||
      new Map([
        ['person-1', 0],
        ['person-2', 1],
        ['person-3', 2],
        ['person-4', 3],
        ['person-5', 4],
      ]),
    [propPersonIndex]
  );

  const blockIndex = useMemo(
    () =>
      propBlockIndex ||
      new Map(
        Array.from({ length: 14 }, (_, i) => [`block-${i}`, i])
      ),
    [propBlockIndex]
  );

  const templateToLayer = useMemo(
    () =>
      propTemplateToLayer ||
      new Map([
        ['template-clinic', 0],
        ['template-inpatient', 1],
        ['template-procedures', 2],
        ['template-conference', 3],
        ['template-call', 4],
        ['template-leave', 5],
        ['template-admin', 6],
        ['template-supervision', 7],
      ]),
    [propTemplateToLayer]
  );

  // Transition animations
  const { transitions, isAnimating, applyDelta } = useSolutionTransitions({
    animationDuration: 400,
    staggerDelay: 15,
    spacing: 1.1,
  });

  // WebSocket connection to solver
  const {
    isConnected,
    status,
    metrics,
    currentAssignments,
    latestDelta,
    latestSolutionNum,
  } = useSolverWebSocket({
    taskId,
    onDelta: (delta, solutionNum) => {
      // Trigger animation when delta arrives
      applyDelta(delta, personIndex, blockIndex, templateToLayer);
    },
    onComplete: (event) => {
      console.log('Solver complete:', event.status);
    },
  });

  // Convert assignments to voxels
  const voxels = useMemo((): VoxelInstance[] => {
    return currentAssignments.map((assignment) => ({
      id: `${assignment.personId}-${assignment.blockId}`,
      x: assignment.bIdx ?? blockIndex.get(assignment.blockId) ?? 0,
      y: assignment.rIdx ?? personIndex.get(assignment.personId) ?? 0,
      z: assignment.tIdx ?? templateToLayer.get(assignment.templateId) ?? 0,
      personId: assignment.personId,
      blockId: assignment.blockId,
      templateId: assignment.templateId,
    }));
  }, [currentAssignments, personIndex, blockIndex, templateToLayer]);

  // Generate axis labels
  const xLabels = useMemo(
    () => Array.from(blockIndex.keys()).slice(0, 20),
    [blockIndex]
  );
  const yLabels = useMemo(
    () => Array.from(personIndex.keys()),
    [personIndex]
  );
  const zLabels = useMemo(
    () => Object.values(ACTIVITY_NAMES),
    []
  );

  // Notify when ready
  useEffect(() => {
    if (isConnected && onReady) {
      onReady();
    }
  }, [isConnected, onReady]);

  return (
    <div className="w-full h-full relative">
      {/* Progress overlay */}
      <ProgressOverlay
        metrics={metrics}
        status={status}
        voxelCount={voxels.length}
      />

      {/* Legend */}
      <Legend />

      {/* Connection status indicator */}
      {!isConnected && taskId && (
        <div className="absolute top-4 right-4 bg-yellow-500/90 text-black px-3 py-1 rounded text-sm">
          Connecting to solver...
        </div>
      )}

      {/* Animation indicator */}
      {isAnimating && (
        <div className="absolute top-20 left-4 bg-purple-500/90 text-white px-3 py-1 rounded text-sm">
          Animating solution {latestSolutionNum}...
        </div>
      )}

      {/* Three.js canvas */}
      <Canvas
        camera={{ position: [15, 15, 15], fov: 45 }}
        shadows
      >
        <color attach="background" args={['#0f172a']} />

        {/* Lighting */}
        <ambientLight intensity={0.4} />
        <pointLight position={[20, 20, 20]} intensity={1} />
        <directionalLight position={[-10, 10, 10]} intensity={0.5} />

        {/* Grid and labels */}
        <GridSystem
          xLabels={xLabels}
          yLabels={yLabels}
          zLabels={zLabels}
          spacing={1.1}
        />

        {/* Voxels */}
        <InstancedVoxelRenderer
          voxels={voxels}
          transitions={transitions}
          spacing={1.1}
          voxelSize={0.85}
        />

        {/* Camera controls */}
        <OrbitControls
          enableDamping
          dampingFactor={0.05}
          minDistance={5}
          maxDistance={100}
        />

        {/* Performance stats (optional) */}
        {showStats && <Stats />}
      </Canvas>
    </div>
  );
};

// ============================================================================
// Demo Component
// ============================================================================

/**
 * Demo component with simulated solver updates.
 *
 * This is useful for testing the visualization without a real solver.
 */
export const SolverVisualizationDemo: React.FC = () => {
  const [demoVoxels, setDemoVoxels] = useState<VoxelInstance[]>([]);
  const [solutionNum, setSolutionNum] = useState(0);
  const [isSimulating, setIsSimulating] = useState(false);

  const { transitions, applyDelta } = useSolutionTransitions();

  // Generate random voxels
  const generateRandomVoxels = useCallback((count: number): VoxelInstance[] => {
    const voxels: VoxelInstance[] = [];
    for (let i = 0; i < count; i++) {
      voxels.push({
        id: `voxel-${i}`,
        x: Math.floor(Math.random() * 14),
        y: Math.floor(Math.random() * 10),
        z: Math.floor(Math.random() * 8),
      });
    }
    return voxels;
  }, []);

  // Simulate solver finding new solutions
  const simulateSolution = useCallback(() => {
    const newVoxels = generateRandomVoxels(50 + solutionNum * 20);
    const oldVoxels = demoVoxels;

    // Calculate delta
    const oldSet = new Set(oldVoxels.map((v) => v.id));
    const newSet = new Set(newVoxels.map((v) => v.id));

    const added = newVoxels
      .filter((v) => !oldSet.has(v.id))
      .map((v) => ({
        personId: `person-${v.y}`,
        blockId: `block-${v.x}`,
        templateId: `template-${v.z}`,
      }));

    const removed = oldVoxels
      .filter((v) => !newSet.has(v.id))
      .map((v) => ({
        personId: `person-${v.y}`,
        blockId: `block-${v.x}`,
        templateId: `template-${v.z}`,
      }));

    const delta: SolutionDelta = { added, removed, moved: [] };

    // Apply animation
    applyDelta(
      delta,
      new Map(Array.from({ length: 10 }, (_, i) => [`person-${i}`, i])),
      new Map(Array.from({ length: 14 }, (_, i) => [`block-${i}`, i])),
      new Map(Array.from({ length: 8 }, (_, i) => [`template-${i}`, i]))
    );

    setDemoVoxels(newVoxels);
    setSolutionNum((n) => n + 1);
  }, [demoVoxels, solutionNum, generateRandomVoxels, applyDelta]);

  // Auto-simulate
  useEffect(() => {
    if (!isSimulating) return;

    const interval = setInterval(simulateSolution, 2000);
    return () => clearInterval(interval);
  }, [isSimulating, simulateSolution]);

  return (
    <div className="w-full h-full relative">
      {/* Controls */}
      <div className="absolute top-4 left-4 z-10 flex gap-2">
        <button
          onClick={() => setIsSimulating(!isSimulating)}
          className={`px-4 py-2 rounded font-bold ${
            isSimulating
              ? 'bg-red-500 hover:bg-red-600'
              : 'bg-green-500 hover:bg-green-600'
          } text-white`}
        >
          {isSimulating ? 'Stop' : 'Start'} Simulation
        </button>
        <button
          onClick={simulateSolution}
          className="px-4 py-2 rounded font-bold bg-blue-500 hover:bg-blue-600 text-white"
        >
          Next Solution
        </button>
      </div>

      {/* Stats */}
      <div className="absolute top-4 right-4 bg-slate-900/90 text-white p-4 rounded">
        <div>Solution #{solutionNum}</div>
        <div>Voxels: {demoVoxels.length}</div>
      </div>

      {/* Canvas */}
      <Canvas camera={{ position: [15, 15, 15], fov: 45 }}>
        <color attach="background" args={['#0f172a']} />
        <ambientLight intensity={0.4} />
        <pointLight position={[20, 20, 20]} intensity={1} />

        <InstancedVoxelRenderer
          voxels={demoVoxels}
          transitions={transitions}
        />

        <OrbitControls enableDamping />
      </Canvas>
    </div>
  );
};

export default SolverVisualization;
