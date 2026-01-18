/**
 * Solver Agent Component
 *
 * Animated glowing sphere that traverses the optimization landscape,
 * simulating how a CP-SAT solver explores the search space.
 * Updates metrics as it moves and finds better solutions.
 */

"use client";

import React, { useRef, useState } from "react";
import * as THREE from "three";
import { useFrame } from "@react-three/fiber";

import { SolverAgentProps, SolverStatus } from "../types";
import { COLORS } from "../constants";

export const SolverAgent: React.FC<SolverAgentProps> = ({ config, onUpdate }) => {
  const agentRef = useRef<THREE.Group>(null);
  const [bestZ, setBestZ] = useState(15);

  const state = useRef({
    targetX: 0,
    targetY: 0,
    currentX: 0,
    currentY: 0,
    branches: 0,
    backtracks: 0,
    status: "exploring" as SolverStatus,
  });

  useFrame(() => {
    // Decision logic - simulate solver behavior
    if (Math.random() < 0.01) {
      // Random jump to new region (backtrack)
      state.current.targetX = (Math.random() - 0.5) * 35;
      state.current.targetY = (Math.random() - 0.5) * 35;
      state.current.branches++;
      state.current.status = "backtracking";
    } else if (Math.random() < 0.05) {
      // Descending into local minimum
      state.current.status = "descending";
    } else if (Math.random() < 0.02) {
      // Pruning inferior branches
      state.current.status = "pruning";
      state.current.backtracks++;
    } else {
      state.current.status = "exploring";
    }

    // Smooth movement toward target
    state.current.currentX +=
      (state.current.targetX - state.current.currentX) * 0.04;
    state.current.currentY +=
      (state.current.targetY - state.current.currentY) * 0.04;

    const x = state.current.currentX;
    const y = state.current.currentY;

    // Height calculation matched to Landscape.tsx
    const z =
      Math.sin(x * 0.4 * config.noiseScale) *
        Math.cos(y * 0.4 * config.noiseScale) *
        config.amplitude +
      Math.sin(x * 0.8 * config.noiseScale) *
        Math.sin(y * 0.8 * config.noiseScale) *
        (config.amplitude / 2) +
      Math.cos(x * 1.5 * config.noiseScale + y * 1.5 * config.noiseScale) *
        (config.amplitude / 6) -
      2;

    if (agentRef.current) {
      agentRef.current.position.set(x, z, y);

      // Update metrics when we find a better solution
      if (z < bestZ) {
        setBestZ(z);
        const gap = ((z + 10) / 20).toFixed(4);
        onUpdate({
          objective: (z + config.amplitude).toFixed(5),
          branches: state.current.branches,
          backtracks: state.current.backtracks,
          status: state.current.status,
          gap: `${gap}%`,
        });
      }
    }
  });

  return (
    <group>
      {/* Solver agent sphere */}
      <group ref={agentRef}>
        <mesh>
          <sphereGeometry args={[0.2, 16, 16]} />
          <meshBasicMaterial color={COLORS.primary} />
        </mesh>
        <pointLight color={COLORS.primary} intensity={1.5} distance={10} />
      </group>

      {/* Pruning plane (upper bound visualization) */}
      <mesh position={[0, bestZ, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <planeGeometry args={[45, 45]} />
        <meshBasicMaterial
          color={COLORS.primary}
          transparent
          opacity={0.03}
          side={THREE.DoubleSide}
        />
      </mesh>
    </group>
  );
};

export default SolverAgent;
