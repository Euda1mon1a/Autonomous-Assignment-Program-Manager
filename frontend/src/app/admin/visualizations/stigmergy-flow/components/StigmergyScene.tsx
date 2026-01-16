'use client';

/**
 * StigmergyScene - Main Three.js canvas
 *
 * Note: Post-processing effects (Bloom, Vignette, etc.) temporarily disabled
 * due to version mismatch between @react-three/fiber@8 and @react-three/postprocessing@3.
 * TODO: Re-enable when upgrading to fiber v9 or downgrading postprocessing.
 */

import React, { Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Stars, PerspectiveCamera } from '@react-three/drei';
import { FlowSimulation } from './FlowSimulation';
import { ScheduleNode, SimulationConfig } from '../types';
import { AUTO_ROTATE_SPEED } from '../constants';

interface StigmergySceneProps {
  data: ScheduleNode[];
  config: SimulationConfig;
}

export const StigmergyScene: React.FC<StigmergySceneProps> = ({
  data,
  config,
}) => {
  // Note: bloomStrength and distortion from config are unused until postprocessing is fixed
  void config.bloomStrength;
  void config.distortion;

  return (
    <div className="fixed inset-0">
      <Canvas dpr={[1, 2]}>
        <PerspectiveCamera makeDefault position={[10, 5, 15]} fov={60} />

        {/* Deep space background */}
        <color attach="background" args={['#020205']} />

        {/* Lighting setup */}
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} intensity={1} />
        <pointLight position={[-10, -10, -10]} intensity={0.5} color="#4400ff" />

        <Suspense fallback={null}>
          {/* Main particle simulation */}
          <FlowSimulation data={data} showConnections={config.showConnections} />

          {/* Background star field */}
          <Stars
            radius={100}
            depth={50}
            count={5000}
            factor={4}
            saturation={0}
            fade
            speed={1}
          />
        </Suspense>

        {/* Camera controls */}
        <OrbitControls
          enablePan={true}
          enableZoom={true}
          autoRotate={true}
          autoRotateSpeed={AUTO_ROTATE_SPEED}
          minPolarAngle={Math.PI / 4}
          maxPolarAngle={Math.PI / 1.5}
        />
      </Canvas>
    </div>
  );
};
