/**
 * Inpatient Anchor Component
 *
 * The FMIT (Family Medicine Inpatient Team) core visualization.
 * Rendered as a floating octahedron at the center of the brane space.
 * The mandatory anchor point that all scheduling revolves around.
 */

"use client";

import React from "react";
import { Float, Text } from "@react-three/drei";

import { InpatientAnchorProps } from "../types";

export const InpatientAnchor: React.FC<InpatientAnchorProps> = ({ entropy }) => {
  // Octahedron grows slightly with entropy (representing stress)
  const octahedronRadius = 0.7 + entropy * 0.5;

  return (
    <Float speed={3} rotationIntensity={1.5} floatIntensity={2}>
      <group position={[0, 0, 0]}>
        {/* Outer wireframe octahedron */}
        <mesh>
          <octahedronGeometry args={[octahedronRadius, 0]} />
          <meshBasicMaterial
            color="#ff3131"
            wireframe
            transparent
            opacity={0.8}
          />
        </mesh>

        {/* Inner glowing sphere */}
        <mesh>
          <sphereGeometry args={[0.35, 32, 32]} />
          <meshBasicMaterial color="#ff3131" transparent opacity={0.4} />
        </mesh>

        {/* Label */}
        <Text
          position={[0, 1.2, 0]}
          fontSize={0.25}
          color="white"
          anchorX="center"
          anchorY="middle"
        >
          FMIT ANCHOR
        </Text>
      </group>
    </Float>
  );
};

export default InpatientAnchor;
