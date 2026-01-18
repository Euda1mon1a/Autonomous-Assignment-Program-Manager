/**
 * Data Packet 3D Component
 *
 * Animated packet traveling along edges.
 */

'use client';

import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { PACKET_COLORS } from '../constants';
import type { DataPacket } from '../types';

interface DataPacket3DProps {
  packet: DataPacket;
  startPos: THREE.Vector3;
  endPos: THREE.Vector3;
  onComplete: (id: string) => void;
}

export function DataPacket3D({
  packet,
  startPos,
  endPos,
  onComplete,
}: DataPacket3DProps) {
  const meshRef = useRef<THREE.Mesh>(null);
  const progressRef = useRef(0);

  useFrame((state, delta) => {
    if (!meshRef.current) return;

    // Animate progress
    progressRef.current += delta * 0.5;

    if (progressRef.current >= 1) {
      onComplete(packet.id);
      return;
    }

    // Interpolate position with easing
    const t = progressRef.current;
    const eased = t * t * (3 - 2 * t); // smoothstep

    meshRef.current.position.lerpVectors(startPos, endPos, eased);

    // Add slight vertical wave
    meshRef.current.position.y += Math.sin(t * Math.PI * 2) * 0.1;

    // Scale based on packet size
    const scale = 0.08 + (packet.size / 5000) * 0.05;
    meshRef.current.scale.setScalar(scale);

    // Rotate
    meshRef.current.rotation.x += delta * 3;
    meshRef.current.rotation.y += delta * 2;
  });

  const color = PACKET_COLORS[packet.type];

  return (
    <mesh ref={meshRef} position={startPos}>
      <octahedronGeometry args={[1, 0]} />
      <meshStandardMaterial
        color={color}
        emissive={color}
        emissiveIntensity={0.5}
        metalness={0.9}
        roughness={0.1}
      />
    </mesh>
  );
}

export default DataPacket3D;
