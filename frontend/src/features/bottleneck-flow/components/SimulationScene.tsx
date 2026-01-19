/**
 * Simulation Scene Component
 *
 * Main Three.js scene content for the bottleneck cascade visualization.
 * Renders lanes, faculty nodes, trainee nodes, and connection lines.
 * Calculates derived state (trainee status, metrics) from simulation state.
 */

'use client';

import React, { useMemo, createRef, useEffect } from 'react';
import * as THREE from 'three';
import {
  LANES,
  FACULTY_X_SPREAD,
  FACULTY_Z_START,
  FACULTY_Z_SPACING,
  FACULTY_COLUMNS,
} from '../constants';
import { LaneVisual } from './LaneVisual';
import { FacultyNode } from './FacultyNode';
import { TraineeNode } from './TraineeNode';
import { DynamicConnection } from './DynamicConnection';
import type {
  SimulationSceneProps,
  TraineeStatus,
  BottleneckMetrics,
  TraineeNodeData,
} from '../types';

/**
 * Scene content rendered inside the Canvas.
 * Separated to allow useFrame and other R3F hooks.
 */
export function SimulationScene({
  faculty,
  trainees,
  simState,
  onMetricsUpdate,
}: SimulationSceneProps) {
  // Calculate faculty 3D positions based on lane and index
  const facultyPositions = useMemo(() => {
    const map = new Map<string, THREE.Vector3>();

    faculty.forEach((f, index) => {
      const lane = LANES[f.lane];
      const xSpread = ((index % FACULTY_COLUMNS) - 1) * FACULTY_X_SPREAD;
      const zPos =
        FACULTY_Z_START - Math.floor(index / FACULTY_COLUMNS) * FACULTY_Z_SPACING;
      map.set(f.id, new THREE.Vector3(xSpread, lane.y, zPos));
    });

    return map;
  }, [faculty]);

  // Calculate trainee status and derived metrics
  const { traineeNodes, metrics } = useMemo(() => {
    let orphaned = 0;
    let rerouted = 0;
    let atRisk = 0;

    const nodes: TraineeNodeData[] = trainees.map((t) => {
      const primaryPos = facultyPositions.get(t.primaryFacultyId);
      const backupPos = facultyPositions.get(t.backupFacultyId);
      const primaryDisabled = simState.disabledFacultyIds.has(t.primaryFacultyId);
      const backupDisabled = simState.disabledFacultyIds.has(t.backupFacultyId);

      let status: TraineeStatus['status'] = 'nominal';
      let targetFacultyId: string | null = t.primaryFacultyId;
      let targetPos = primaryPos;

      if (primaryDisabled) {
        if (simState.showSuggestedFix && !backupDisabled && backupPos) {
          // Reroute to backup when fix is enabled
          status = 'rerouted';
          targetFacultyId = t.backupFacultyId;
          targetPos = backupPos;
          rerouted++;
        } else if (!backupDisabled && backupPos) {
          // At-risk: backup available but not used
          status = 'at-risk';
          targetFacultyId = null;
          atRisk++;
        } else {
          // Orphaned: both primary and backup unavailable
          status = 'orphaned';
          targetFacultyId = null;
          orphaned++;
        }
      }

      return {
        ...t,
        statusObj: { status, targetFacultyId, targetPositionOffset: null },
        primaryPos,
        targetPos,
      };
    });

    const total = trainees.length;
    const coverage = total > 0 ? Math.round(((total - orphaned) / total) * 100) : 100;

    const newMetrics: BottleneckMetrics = { coverage, orphaned, rerouted, atRisk };

    return { traineeNodes: nodes, metrics: newMetrics };
  }, [trainees, facultyPositions, simState]);

  // Notify parent of metrics changes
  useEffect(() => {
    onMetricsUpdate(metrics);
  }, [metrics, onMetricsUpdate]);

  // Create stable refs for trainee meshes (needed for connection lines)
  const traineeRefs = useMemo(() => {
    const refs: Record<string, React.RefObject<THREE.Mesh>> = {};
    trainees.forEach((t) => {
      refs[t.id] = createRef();
    });
    return refs;
  }, [trainees]);

  return (
    <>
      {/* Lighting - increased for visibility */}
      <ambientLight intensity={0.8} />
      <directionalLight position={[20, 30, 20]} intensity={1.2} />
      <pointLight position={[0, 10, -30]} intensity={0.6} color="#22c55e" />

      {/* Lanes */}
      {Object.entries(LANES).map(([key, config]) => (
        <LaneVisual key={key} config={config} />
      ))}

      {/* Faculty Nodes */}
      {faculty.map((f) => (
        <FacultyNode
          key={f.id}
          faculty={f}
          position={
            (facultyPositions.get(f.id)?.toArray() as [number, number, number]) || [
              0, 0, 0,
            ]
          }
          isDisabled={simState.disabledFacultyIds.has(f.id)}
          laneColor={LANES[f.lane].threeColor}
        />
      ))}

      {/* Trainee Nodes with Connections */}
      {traineeNodes.map((t) => {
        if (!t.primaryPos) return null;

        // Get faculty info to determine orbit index
        const fac = faculty.find((f) => f.id === t.primaryFacultyId);
        const idx = fac ? fac.traineeIds.indexOf(t.id) : 0;
        const count = fac ? fac.traineeIds.length : 1;

        return (
          <React.Fragment key={t.id}>
            <TraineeNode
              ref={traineeRefs[t.id]}
              trainee={t}
              status={t.statusObj}
              primaryFacultyPos={t.primaryPos}
              targetFacultyPos={t.targetPos}
              orbitIndex={idx >= 0 ? idx : 0}
              totalInCohort={count || 1}
            />
            {/* Connection line if trainee has a target position */}
            {t.targetPos && (
              <DynamicConnection
                traineeRef={traineeRefs[t.id]}
                targetPos={t.targetPos}
                status={t.statusObj.status}
              />
            )}
          </React.Fragment>
        );
      })}

      {/* Fog - reduced for better visibility */}
      <fog attach="fog" args={['#0a0a0a', 80, 200]} />
    </>
  );
}

export default SimulationScene;
