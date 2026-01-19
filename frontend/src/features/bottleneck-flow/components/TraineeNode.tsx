/**
 * Trainee Node Component
 *
 * 3D sphere representing a trainee (resident) in the supervision cascade.
 * Orbits around faculty, changes behavior based on status:
 * - nominal: Orbits primary faculty
 * - at-risk: Hovers uneasily near disabled primary
 * - rerouted: Orbits backup faculty
 * - orphaned: Drifts into the void
 */

'use client';

import { useRef, forwardRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { SIZES, THREE_COLORS, ORBIT_RADIUS, LERP_FACTOR } from '../constants';
import type { TraineeNodeProps } from '../types';

export const TraineeNode = forwardRef<THREE.Mesh, TraineeNodeProps>(
  function TraineeNode(
    {
      trainee,
      status,
      primaryFacultyPos,
      targetFacultyPos,
      orbitIndex,
      totalInCohort,
    },
    ref
  ) {
    const meshRef = useRef<THREE.Mesh>(null);
    const positionRef = useRef(new THREE.Vector3());

    // Calculate orbit parameters
    const orbitAngle = (orbitIndex / totalInCohort) * Math.PI * 2;

    // Determine appearance based on status
    let color = THREE_COLORS.nominal;
    if (status.status === 'orphaned') color = THREE_COLORS.critical;
    if (status.status === 'rerouted') color = THREE_COLORS.degraded;
    if (status.status === 'at-risk') color = THREE_COLORS.critical;

    // Size based on PGY level
    const size =
      trainee.pgy === 1
        ? SIZES.pgy1
        : trainee.pgy === 2
          ? SIZES.pgy2
          : SIZES.pgy3;

    useFrame(({ clock }) => {
      const mesh = meshRef.current || (ref as React.RefObject<THREE.Mesh>)?.current;
      if (!mesh) return;

      const time = clock.elapsedTime;
      const targetVec = new THREE.Vector3();

      if (status.status === 'orphaned') {
        // Drift away into the void
        const driftX = primaryFacultyPos.x + 25;
        const driftY = primaryFacultyPos.y - 8;
        const driftZ = primaryFacultyPos.z;
        targetVec.set(driftX, driftY, driftZ);

        // Add chaotic wobble
        targetVec.x += Math.sin(time * 2 + orbitAngle) * 0.5;
        targetVec.y += Math.cos(time * 3) * 0.5;
      } else if (status.status === 'at-risk') {
        // Hover uneasily near disabled primary
        const driftX = primaryFacultyPos.x + 5;
        const driftY = primaryFacultyPos.y - 2;
        targetVec.set(driftX, driftY, primaryFacultyPos.z);

        // Subtle uneasy motion
        targetVec.x += Math.sin(time * 3 + orbitAngle) * 0.3;
        targetVec.y += Math.cos(time * 2) * 0.2;
      } else if (targetFacultyPos) {
        // Orbiting a faculty (either primary or backup)
        const angle = orbitAngle + time * 0.3;
        const x = targetFacultyPos.x + Math.cos(angle) * ORBIT_RADIUS;
        const z = targetFacultyPos.z + Math.sin(angle) * ORBIT_RADIUS;
        const y = targetFacultyPos.y + Math.sin(time * 2 + orbitAngle) * 0.2;
        targetVec.set(x, y, z);
      }

      // Lerp current position to target for smooth transition
      positionRef.current.lerp(targetVec, LERP_FACTOR);
      mesh.position.copy(positionRef.current);
    });

    return (
      <mesh ref={ref || meshRef}>
        <sphereGeometry args={[size, 24, 24]} />
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={status.status === 'nominal' ? 0.2 : 0.5}
          metalness={0.2}
          roughness={0.8}
        />
      </mesh>
    );
  }
);

export default TraineeNode;
