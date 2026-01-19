/**
 * Faculty Node Component
 *
 * 3D sphere representing a faculty member in the supervision cascade.
 * Larger sphere with pulsing animation when active, dark when disabled.
 */

'use client';

import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { SIZES, THREE_COLORS } from '../constants';
import type { FacultyNodeProps } from '../types';

export function FacultyNode({
  faculty,
  position,
  isDisabled,
  laneColor,
}: FacultyNodeProps) {
  const meshRef = useRef<THREE.Mesh>(null);

  // Subtle pulse animation when active
  useFrame(({ clock }) => {
    if (meshRef.current && !isDisabled) {
      const scale = 1 + Math.sin(clock.elapsedTime * 2) * 0.05;
      meshRef.current.scale.setScalar(scale);
    }
  });

  // Color based on state and lane
  const color = isDisabled
    ? THREE_COLORS.down
    : faculty.lane === 'RESERVE'
      ? THREE_COLORS.reserve
      : THREE_COLORS.nominal;

  const emissiveIntensity = isDisabled ? 0 : 0.7;

  return (
    <mesh ref={meshRef} position={position}>
      <sphereGeometry args={[SIZES.faculty, 32, 32]} />
      <meshStandardMaterial
        color={color}
        emissive={color}
        emissiveIntensity={emissiveIntensity}
        metalness={0.3}
        roughness={0.7}
      />
    </mesh>
  );
}

export default FacultyNode;
