/**
 * Brane Topology Visualizer
 *
 * A 3D visualization of residency scheduling through a brane-theory metaphor.
 * Three dimensional layers represent different system states:
 *
 * - BRANE ALPHA (Ideal): The bureaucratic perfect state (green)
 * - BRANE BETA (Real-time): Current operational reality (cyan)
 * - BRANE OMEGA (Collapse): Systemic decay state (red)
 *
 * The visualization shows:
 * - Faculty, residents, and interns as spheres on dimensional branes
 * - FMIT anchor as a central octahedron
 * - Supervision matrix lines connecting faculty to trainees
 * - Entropy slider to simulate faculty attrition
 * - ACGME supervision math panel
 *
 * As entropy increases:
 * - Positions gain "wave function jitter"
 * - Faculty availability drops
 * - System approaches critical supervision threshold
 */

"use client";

import React, { useState } from "react";
import { Canvas } from "@react-three/fiber";
import { PerspectiveCamera, OrbitControls, Stars } from "@react-three/drei";

import { BraneTopologyProps } from "./types";
import { DEFAULT_DATA, BRANE_LAYERS } from "./constants";
import { InpatientAnchor } from "./components/InpatientAnchor";
import { BraneLayer } from "./components/BraneLayer";
import { SupervisionMatrix } from "./components/SupervisionMatrix";
import { MathPanel } from "./components/MathPanel";
import { EntropyControls } from "./components/EntropyControls";

export function BraneTopologyVisualizer({
  initialEntropy = 0.12,
  data = DEFAULT_DATA,
  showMathPanel = true,
  showControls = true,
  className = "",
}: BraneTopologyProps): JSX.Element {
  const [entropy, setEntropy] = useState(initialEntropy);

  // Faculty availability drops as entropy increases (simulating attrition)
  const availableFaculty = Math.max(0, data.faculty - Math.floor(entropy * 11));

  // Supervision requirement calculation
  // Interns count 0.5 AT, Residents count 0.25 AT
  const totalAT = data.interns * 0.5 + data.residents * 0.25;
  // Ceiling of load, plus 1 for mandatory FMIT anchor
  const reqFaculty = Math.ceil(totalAT) + 1;

  return (
    <div
      className={`relative h-screen w-full select-none overflow-hidden bg-[#020202] ${className}`}
    >
      {/* 3D Canvas */}
      <Canvas shadows dpr={[1, 2]} className="absolute left-0 top-0 z-0 h-full w-full">
        <PerspectiveCamera makeDefault position={[12, 6, 18]} fov={35} />

        {/* Starfield background */}
        <Stars
          radius={100}
          depth={50}
          count={4000}
          factor={4}
          saturation={0}
          fade
          speed={1.5}
        />

        {/* Lighting */}
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} intensity={1.5} color="#00e5ff" />
        <pointLight position={[-10, -10, -10]} intensity={0.5} color="#ff3131" />

        {/* FMIT Anchor at center */}
        <InpatientAnchor entropy={entropy} />

        {/* Brane Alpha: The Bureaucratic Ideal (Green) */}
        <BraneLayer
          entropy={0}
          offset={BRANE_LAYERS.alpha.offset}
          label={BRANE_LAYERS.alpha.label}
          colorOverride={BRANE_LAYERS.alpha.color}
          active={entropy < 0.2}
        />

        {/* Brane Beta: Operational Reality (Real-time) */}
        <BraneLayer
          entropy={entropy}
          offset={BRANE_LAYERS.beta.offset}
          label={BRANE_LAYERS.beta.label}
        />

        {/* Brane Omega: Systemic Decay (Red) */}
        <BraneLayer
          entropy={entropy * 2.5}
          offset={BRANE_LAYERS.omega.offset}
          label={BRANE_LAYERS.omega.label}
          colorOverride={BRANE_LAYERS.omega.color}
        />

        {/* Supervision lines on real-time brane */}
        <SupervisionMatrix entropy={entropy} availableFaculty={availableFaculty} />

        {/* Camera controls */}
        <OrbitControls enablePan={false} maxDistance={30} minDistance={10} />
      </Canvas>

      {/* HUD Overlays */}
      {showMathPanel && (
        <MathPanel
          availableFaculty={availableFaculty}
          reqFaculty={reqFaculty}
          totalAT={totalAT}
          data={data}
        />
      )}

      {showControls && (
        <EntropyControls
          entropy={entropy}
          setEntropy={setEntropy}
          availableFaculty={availableFaculty}
          reqFaculty={reqFaculty}
        />
      )}

      {/* Location/Time HUD */}
      <div className="pointer-events-none absolute bottom-8 right-8 z-10 text-right opacity-40">
        <div className="mb-1 font-mono text-[10px] uppercase tracking-tighter text-slate-400">
          Tripler Army Medical Center
        </div>
        <div className="font-mono text-[12px] tracking-[0.3em] text-cyan-500">
          RESIDENCY_MAP.v4.0
        </div>
      </div>
    </div>
  );
}

export default BraneTopologyVisualizer;
