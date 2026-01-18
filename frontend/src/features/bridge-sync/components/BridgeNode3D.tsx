/**
 * Bridge Node 3D Component
 *
 * 3D representation of a node in the bridge visualization.
 */

'use client';

import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Text } from '@react-three/drei';
import * as THREE from 'three';
import { NODE_COLORS } from '../constants';
import type { BridgeNode } from '../types';

interface BridgeNode3DProps {
  node: BridgeNode;
}

export function BridgeNode3D({ node }: BridgeNode3DProps) {
  const meshRef = useRef<THREE.Mesh>(null);
  const glowRef = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    if (!meshRef.current || !glowRef.current) return;

    // Pulse effect based on status
    const pulse =
      node.status === 'processing'
        ? Math.sin(state.clock.elapsedTime * 4) * 0.1 + 1
        : 1;

    meshRef.current.scale.setScalar(pulse);
    glowRef.current.scale.setScalar(pulse * 1.3);

    // Rotate slightly
    meshRef.current.rotation.y += 0.01;
  });

  const color = NODE_COLORS[node.type];
  const isError = node.status === 'error';
  const isProcessing = node.status === 'processing';

  return (
    <group position={[node.position.x, node.position.y, node.position.z]}>
      {/* Main node */}
      <mesh ref={meshRef}>
        <boxGeometry args={[0.5, 0.5, 0.5]} />
        <meshStandardMaterial
          color={isError ? '#ef4444' : color}
          emissive={isError ? '#ef4444' : color}
          emissiveIntensity={isProcessing ? 0.5 : 0.2}
          metalness={0.8}
          roughness={0.2}
        />
      </mesh>

      {/* Glow effect */}
      <mesh ref={glowRef}>
        <boxGeometry args={[0.6, 0.6, 0.6]} />
        <meshBasicMaterial color={color} transparent opacity={0.15} />
      </mesh>

      {/* Label */}
      <Text
        position={[0, -0.5, 0]}
        fontSize={0.15}
        color="white"
        anchorX="center"
        anchorY="top"
      >
        {node.label}
      </Text>

      {/* Throughput indicator */}
      <Text
        position={[0, 0.45, 0.26]}
        fontSize={0.1}
        color="#94a3b8"
        anchorX="center"
        anchorY="bottom"
      >
        {node.throughput}/s
      </Text>
    </group>
  );
}

export default BridgeNode3D;
