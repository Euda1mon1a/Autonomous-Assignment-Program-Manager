/**
 * Lane Visual Component
 *
 * 3D lane visualization with floor plane, edge lines, and streaming particles.
 * Represents one of three operational lanes: AT, FMIT, or RESERVE.
 */

'use client';

import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { Line } from '@react-three/drei';
import * as THREE from 'three';
import { STREAM_LENGTH, FLOW_SPEED, PARTICLE_COUNT } from '../constants';
import type { LaneVisualProps } from '../types';

export function LaneVisual({ config }: LaneVisualProps) {
  const particlesRef = useRef<THREE.Points>(null);

  // Static floor geometry
  const floorGeometry = useMemo(
    () => new THREE.PlaneGeometry(20, STREAM_LENGTH),
    []
  );

  // Lane edge line points
  const leftEdgePoints = useMemo(
    (): [number, number, number][] => [
      [-10, -0.5, 0],
      [-10, -0.5, -STREAM_LENGTH],
    ],
    []
  );

  const rightEdgePoints = useMemo(
    (): [number, number, number][] => [
      [10, -0.5, 0],
      [10, -0.5, -STREAM_LENGTH],
    ],
    []
  );

  // Particle system for streaming effect
  const particles = useMemo(() => {
    const positions = new Float32Array(PARTICLE_COUNT * 3);

    for (let i = 0; i < PARTICLE_COUNT; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 18; // x spread
      positions[i * 3 + 1] = (Math.random() - 0.5) * 2; // y relative to lane
      positions[i * 3 + 2] = -Math.random() * STREAM_LENGTH; // z depth
    }

    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    return geometry;
  }, []);

  // Animate particle flow
  useFrame(() => {
    if (particlesRef.current) {
      const positions = particlesRef.current.geometry.attributes.position
        .array as Float32Array;

      for (let i = 0; i < PARTICLE_COUNT; i++) {
        // Move particles forward
        positions[i * 3 + 2] += FLOW_SPEED;

        // Reset particles that pass the origin
        if (positions[i * 3 + 2] > 0) {
          positions[i * 3 + 2] = -STREAM_LENGTH;
        }
      }

      particlesRef.current.geometry.attributes.position.needsUpdate = true;
    }
  });

  return (
    <group position={[0, config.y, 0]}>
      {/* Floor Plane */}
      <mesh
        rotation={[-Math.PI / 2, 0, 0]}
        position={[0, -0.5, -STREAM_LENGTH / 2]}
      >
        <primitive object={floorGeometry} />
        <meshBasicMaterial
          color={config.threeColor}
          transparent
          opacity={0.08}
          side={THREE.DoubleSide}
        />
      </mesh>

      {/* Left Edge Line */}
      <Line
        points={leftEdgePoints}
        color={config.color}
        transparent
        opacity={0.4}
        lineWidth={2}
      />

      {/* Right Edge Line */}
      <Line
        points={rightEdgePoints}
        color={config.color}
        transparent
        opacity={0.4}
        lineWidth={2}
      />

      {/* Streaming Particles */}
      <points ref={particlesRef}>
        <primitive object={particles} />
        <pointsMaterial
          color={config.threeColor}
          size={0.25}
          transparent
          opacity={0.6}
          blending={THREE.AdditiveBlending}
        />
      </points>
    </group>
  );
}

export default LaneVisual;
