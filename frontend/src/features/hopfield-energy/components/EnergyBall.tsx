/**
 * Energy Ball Component
 *
 * Animated ball representing the current schedule state.
 * Rolls toward energy minima during gradient descent.
 */

'use client';

import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import {
  SURFACE_SIZE,
  DESCENT_STEP,
  CONVERGENCE_THRESHOLD,
  computeEnergy,
  computeGradient,
} from '../constants';
import type { EnergyBallProps } from '../types';

export function EnergyBall({
  coverage,
  balance,
  isSettling,
  onPositionUpdate,
}: EnergyBallProps) {
  const ballRef = useRef<THREE.Mesh>(null);
  const glowRef = useRef<THREE.Mesh>(null);
  const positionRef = useRef({ u: coverage, v: balance });

  // Update position ref when props change (from sliders)
  useMemo(() => {
    if (!isSettling) {
      positionRef.current = { u: coverage, v: balance };
    }
  }, [coverage, balance, isSettling]);

  useFrame((state) => {
    if (!ballRef.current || !glowRef.current) return;

    // Gradient descent when settling
    if (isSettling) {
      const { u, v } = positionRef.current;
      const [dEdU, dEdV] = computeGradient(u, v);
      const gradMag = Math.sqrt(dEdU * dEdU + dEdV * dEdV);

      if (gradMag > CONVERGENCE_THRESHOLD) {
        const newU = Math.max(0, Math.min(1, u - DESCENT_STEP * dEdU));
        const newV = Math.max(0, Math.min(1, v - DESCENT_STEP * dEdV));
        positionRef.current = { u: newU, v: newV };
        onPositionUpdate(newU, newV);
      }
    }

    // Compute 3D position from (u, v)
    const { u, v } = positionRef.current;
    const x = (u - 0.5) * SURFACE_SIZE;
    const z = (0.5 - v) * SURFACE_SIZE;
    const energy = computeEnergy(u, v);

    // Position ball on surface with small offset
    const y = energy + 0.12;

    // Hover animation
    const hoverOffset = Math.sin(state.clock.elapsedTime * 3) * 0.02;

    ballRef.current.position.set(x, y + hoverOffset, z);
    glowRef.current.position.copy(ballRef.current.position);

    // Glow pulse
    const glowScale = 1 + Math.sin(state.clock.elapsedTime * 5) * 0.1;
    glowRef.current.scale.setScalar(glowScale);
  });

  return (
    <group>
      {/* Ball */}
      <mesh ref={ballRef}>
        <sphereGeometry args={[0.12, 32, 32]} />
        <meshStandardMaterial
          color="#ffd700"
          emissive="#ff8c00"
          emissiveIntensity={0.3}
          metalness={0.8}
          roughness={0.2}
        />
      </mesh>

      {/* Glow effect */}
      <mesh ref={glowRef}>
        <sphereGeometry args={[0.18, 32, 32]} />
        <meshBasicMaterial color="#ffd700" transparent opacity={0.2} />
      </mesh>
    </group>
  );
}

export { EnergyBall as default };
