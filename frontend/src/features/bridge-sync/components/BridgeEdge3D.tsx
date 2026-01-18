/**
 * Bridge Edge 3D Component
 *
 * Line connecting two nodes with flow animation.
 */

'use client';

import { useMemo, useRef, useEffect } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import type { BridgeEdge, BridgeNode } from '../types';

interface BridgeEdge3DProps {
  edge: BridgeEdge;
  nodes: BridgeNode[];
}

export function BridgeEdge3D({ edge, nodes }: BridgeEdge3DProps) {
  const lineRef = useRef<THREE.Line>(null);
  const dashOffsetRef = useRef(0);

  const sourceNode = nodes.find((n) => n.id === edge.source);
  const targetNode = nodes.find((n) => n.id === edge.target);

  const points = useMemo(() => {
    if (!sourceNode || !targetNode) return [];

    return [
      new THREE.Vector3(
        sourceNode.position.x,
        sourceNode.position.y,
        sourceNode.position.z
      ),
      new THREE.Vector3(
        targetNode.position.x,
        targetNode.position.y,
        targetNode.position.z
      ),
    ];
  }, [sourceNode, targetNode]);

  const geometry = useMemo(() => {
    if (points.length < 2) return null;
    return new THREE.BufferGeometry().setFromPoints(points);
  }, [points]);

  // Compute line distances for dashed material to work
  useEffect(() => {
    if (lineRef.current && geometry) {
      lineRef.current.computeLineDistances();
    }
  }, [geometry]);

  useFrame((state, delta) => {
    if (!lineRef.current?.material) return;

    // Animate dash offset for flow effect
    if (edge.active) {
      dashOffsetRef.current -= delta * 2;
      (lineRef.current.material as THREE.LineDashedMaterial).dashOffset =
        dashOffsetRef.current;
    }
  });

  if (!geometry || points.length < 2) return null;

  return (
    <line ref={lineRef} geometry={geometry}>
      <lineDashedMaterial
        color={edge.active ? '#06b6d4' : '#475569'}
        dashSize={0.2}
        gapSize={0.1}
        opacity={edge.active ? 0.8 : 0.3}
        transparent
      />
    </line>
  );
}

export default BridgeEdge3D;
