/**
 * Brane Layer Component
 *
 * Represents a single dimensional "brane" in the visualization.
 * Each brane shows the system state at a different level:
 * - Alpha (Ideal): The bureaucratic perfect state
 * - Beta (Real-time): Current operational reality
 * - Omega (Collapse): Systemic decay if entropy increases
 */

"use client";

import React, { useRef, useMemo } from "react";
import { useFrame } from "@react-three/fiber";
import { Text } from "@react-three/drei";
import * as THREE from "three";

import { BraneLayerProps, UnitSpec } from "../types";
import { generateUnitSpecs, getUnitPosition, DEFAULT_DATA } from "../constants";

export const BraneLayer: React.FC<BraneLayerProps> = ({
  entropy,
  offset,
  label,
  colorOverride,
  active = true,
}) => {
  const groupRef = useRef<THREE.Group>(null);

  // Generate unit specifications
  const unitSpecs = useMemo(() => generateUnitSpecs(DEFAULT_DATA), []);

  // Calculate positions for all units on this brane
  const units = useMemo(() => {
    return unitSpecs.map((unit, i) => ({
      ...unit,
      pos: getUnitPosition(unit, i, unitSpecs.length, entropy, offset),
    }));
  }, [unitSpecs, entropy, offset]);

  // Subtle breathing rotation based on entropy
  useFrame((state) => {
    if (groupRef.current && active) {
      groupRef.current.rotation.z =
        Math.sin(state.clock.elapsedTime * 0.1) * 0.05 * (1 + entropy * 5);
    }
  });

  return (
    <group ref={groupRef}>
      {/* Brane label */}
      <Text
        position={[9, offset, 0]}
        fontSize={0.4}
        color={colorOverride ?? "#ffffff"}
        anchorX="left"
        anchorY="middle"
        fillOpacity={active ? 0.3 : 0.1}
      >
        {label}
      </Text>

      {/* Render each quantized unit as a sphere */}
      {units.map((unit) => (
        <UnitSphere
          key={`${label}-${unit.id}`}
          unit={unit}
          colorOverride={colorOverride}
          active={active}
          entropy={entropy}
        />
      ))}
    </group>
  );
};

interface UnitSphereProps {
  unit: UnitSpec & { pos: THREE.Vector3 };
  colorOverride?: string;
  active: boolean;
  entropy: number;
}

const UnitSphere: React.FC<UnitSphereProps> = ({
  unit,
  colorOverride,
  active,
  entropy,
}) => {
  return (
    <mesh position={unit.pos}>
      <sphereGeometry args={[unit.size, 16, 16]} />
      <meshBasicMaterial
        color={colorOverride ?? unit.color}
        transparent
        opacity={active ? 0.9 - entropy * 0.4 : 0.1}
      />
    </mesh>
  );
};

export default BraneLayer;
