/**
 * Energy Surface Component
 *
 * 3D surface representing the Hopfield energy landscape.
 * Color-coded using military readiness levels.
 */

'use client';

import { useMemo } from 'react';
import * as THREE from 'three';
import { GRID_SIZE, SURFACE_SIZE, computeEnergy, getMilitaryColor } from '../constants';

export function EnergySurface() {
  const { geometry } = useMemo(() => {
    const geo = new THREE.PlaneGeometry(
      SURFACE_SIZE,
      SURFACE_SIZE,
      GRID_SIZE - 1,
      GRID_SIZE - 1
    );
    const vertices = geo.attributes.position.array as Float32Array;
    const colors = new Float32Array(vertices.length);

    let minE = Infinity;
    let maxE = -Infinity;

    // First pass: compute energy and find range
    for (let i = 0; i < vertices.length; i += 3) {
      const x = vertices[i];
      const y = vertices[i + 1];
      const u = (x + SURFACE_SIZE / 2) / SURFACE_SIZE;
      const v = (y + SURFACE_SIZE / 2) / SURFACE_SIZE;
      const energy = computeEnergy(u, v);
      vertices[i + 2] = energy;
      minE = Math.min(minE, energy);
      maxE = Math.max(maxE, energy);
    }

    // Second pass: assign colors
    for (let i = 0; i < vertices.length; i += 3) {
      const energy = vertices[i + 2];
      const t = (energy - minE) / (maxE - minE);
      const color = getMilitaryColor(t);
      colors[i] = color.r;
      colors[i + 1] = color.g;
      colors[i + 2] = color.b;
    }

    geo.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    geo.computeVertexNormals();

    return { geometry: geo, minEnergy: minE, maxEnergy: maxE };
  }, []);

  return (
    <group>
      {/* Main surface */}
      <mesh rotation-x={-Math.PI / 2} geometry={geometry}>
        <meshStandardMaterial
          vertexColors
          side={THREE.DoubleSide}
          metalness={0.3}
          roughness={0.6}
        />
      </mesh>

      {/* Wireframe overlay */}
      <mesh rotation-x={-Math.PI / 2} geometry={geometry.clone()}>
        <meshBasicMaterial
          color="#ffffff"
          wireframe
          transparent
          opacity={0.05}
        />
      </mesh>
    </group>
  );
}

export { EnergySurface as default };
