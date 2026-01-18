/**
 * Landscape Component
 *
 * 3D multi-modal cost function surface representing the optimization space.
 * The surface is generated using trigonometric functions to create
 * multiple local minima and a complex search topology.
 */

"use client";

import React, { useMemo } from "react";
import * as THREE from "three";

import { LandscapeProps } from "../types";
import { COLORS, LANDSCAPE_SIZE, GRID_DIVISIONS } from "../constants";

export const Landscape: React.FC<LandscapeProps> = ({ config }) => {
  const geometry = useMemo(() => {
    const geo = new THREE.PlaneGeometry(
      LANDSCAPE_SIZE,
      LANDSCAPE_SIZE,
      GRID_DIVISIONS,
      GRID_DIVISIONS
    );
    const pos = geo.attributes.position;

    for (let i = 0; i < pos.count; i++) {
      const x = pos.getX(i);
      const y = pos.getY(i);

      // Complex multi-modal cost function
      // Creates multiple local minima for the solver to explore
      const z =
        Math.sin(x * 0.4 * config.noiseScale) *
          Math.cos(y * 0.4 * config.noiseScale) *
          config.amplitude +
        Math.sin(x * 0.8 * config.noiseScale) *
          Math.sin(y * 0.8 * config.noiseScale) *
          (config.amplitude / 2) +
        Math.cos(x * 1.5 * config.noiseScale + y * 1.5 * config.noiseScale) *
          (config.amplitude / 6);

      pos.setZ(i, z);
    }

    geo.computeVertexNormals();
    return geo;
  }, [config]);

  return (
    <group rotation={[-Math.PI / 2, 0, 0]} position={[0, -2, 0]}>
      {/* Solid dark surface */}
      <mesh geometry={geometry}>
        <meshStandardMaterial color="#0a0a0a" roughness={0.05} metalness={0.9} />
      </mesh>

      {/* Wireframe overlay */}
      <mesh geometry={geometry}>
        <meshBasicMaterial
          color={COLORS.primary}
          wireframe
          transparent
          opacity={0.08}
        />
      </mesh>
    </group>
  );
};

export default Landscape;
