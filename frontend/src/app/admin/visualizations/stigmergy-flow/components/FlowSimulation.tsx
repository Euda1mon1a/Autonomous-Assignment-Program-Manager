'use client';

/**
 * FlowSimulation - Particle system for schedule visualization
 *
 * Each particle represents a schedule assignment:
 * - Blue: Clinic assignments (steady flow)
 * - Green: FMIT rotations (clustered bursts)
 * - Yellow: Call shifts (night-side flow)
 * - Red: Conflicts (collision sparks)
 * - White: Unassigned slots (ghost particles)
 */

import React, { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Trail, Float, Sparkles, QuadraticBezierLine } from '@react-three/drei';
import * as THREE from 'three';
import { ScheduleNode, PARTICLE_COLORS } from '../types';

interface FlowSimulationProps {
  data: ScheduleNode[];
  showConnections: boolean;
}

/**
 * Individual particle with bioluminescent trail
 */
const ParticleInstance: React.FC<{ node: ScheduleNode }> = ({ node }) => {
  const meshRef = useRef<THREE.Mesh>(null);
  const color = PARTICLE_COLORS[node.type];

  // Random offset for floating effect (deterministic per particle)
  const randomOffset = useMemo(() => Math.random() * 100, []);

  useFrame((state) => {
    if (!meshRef.current) return;

    const t = state.clock.getElapsedTime();

    // Pulse effect - particles "breathe"
    const scale = 1 + Math.sin(t * 2 + randomOffset) * 0.2;
    meshRef.current.scale.setScalar(scale);

    // Slight vertical oscillation to simulate flow
    meshRef.current.position.y = node.position[1] + Math.sin(t + randomOffset) * 0.1;
  });

  return (
    <group position={node.position}>
      <Float speed={2} rotationIntensity={0.5} floatIntensity={0.5}>
        {/* The Particle Core */}
        <mesh ref={meshRef}>
          <sphereGeometry args={[0.15, 16, 16]} />
          <meshStandardMaterial
            color={color}
            emissive={color}
            emissiveIntensity={node.intensity * 2}
            toneMapped={false}
          />
        </mesh>

        {/* Bioluminescent Trail */}
        <Trail
          width={0.4}
          length={6}
          color={color}
          attenuation={(t) => t * t}
        >
          <mesh visible={false}>
            <sphereGeometry args={[0.1, 8, 8]} />
            <meshBasicMaterial />
          </mesh>
        </Trail>
      </Float>
    </group>
  );
};

/**
 * Magnetic field lines connecting supervised relationships
 */
const Connections: React.FC<{ data: ScheduleNode[] }> = ({ data }) => {
  const lines = useMemo(() => {
    const connections: {
      start: THREE.Vector3;
      end: THREE.Vector3;
      color: THREE.Color;
    }[] = [];

    // Create lookup map
    const nodeMap = new Map(data.map((n) => [n.id, n]));

    data.forEach((node) => {
      node.connections.forEach((targetId) => {
        const target = nodeMap.get(targetId);
        if (target) {
          connections.push({
            start: new THREE.Vector3(...node.position),
            end: new THREE.Vector3(...target.position),
            color: PARTICLE_COLORS[node.type],
          });
        }
      });
    });

    return connections;
  }, [data]);

  return (
    <group>
      {lines.map((line, i) => (
        <QuadraticBezierLine
          key={i}
          start={line.start}
          end={line.end}
          mid={line.start
            .clone()
            .lerp(line.end, 0.5)
            .add(new THREE.Vector3(0, 2, 0))}
          color={line.color}
          lineWidth={1}
          transparent
          opacity={0.3}
        />
      ))}
    </group>
  );
};

/**
 * Main flow simulation component
 */
export const FlowSimulation: React.FC<FlowSimulationProps> = ({
  data,
  showConnections,
}) => {
  return (
    <group>
      {/* Schedule particles */}
      {data.map((node) => (
        <ParticleInstance key={node.id} node={node} />
      ))}

      {/* Supervision connections (magnetic field lines) */}
      {showConnections && <Connections data={data} />}

      {/* Ambient sparkles for "space/fluid" feel */}
      <Sparkles
        count={200}
        scale={25}
        size={2}
        speed={0.4}
        opacity={0.2}
        color="#88ccff"
      />
    </group>
  );
};
