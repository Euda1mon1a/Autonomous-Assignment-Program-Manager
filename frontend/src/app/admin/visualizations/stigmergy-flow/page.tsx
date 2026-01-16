'use client';

/**
 * Stigmergy Flow Visualization Page
 *
 * Experimental 3D visualization of schedule assignments as particles
 * flowing through spacetime. Named after ant pheromone trail patterns.
 *
 * Purpose: Explore whether humans can learn to interpret schedule
 * patterns intuitively through spatial visualization rather than
 * traditional tables/charts.
 *
 * @route /admin/visualizations/stigmergy-flow
 */

import React, { useState, useEffect, useCallback } from 'react';
import dynamic from 'next/dynamic';
import { ScheduleNode, SimulationConfig, GeminiAnalysisResult } from './types';
import { generateMockData } from './constants';

// Dynamic imports for Three.js components (no SSR - needs WebGL)
const StigmergyScene = dynamic(
  () => import('./components/StigmergyScene').then((mod) => mod.StigmergyScene),
  { ssr: false }
);

const UIOverlay = dynamic(
  () => import('./components/UIOverlay').then((mod) => mod.UIOverlay),
  { ssr: false }
);

/**
 * Loading screen while WebGL initializes
 */
const LoadingScreen: React.FC = () => (
  <div className="fixed inset-0 bg-black flex items-center justify-center z-50">
    <div className="text-center">
      <div className="inline-block w-8 h-8 border-4 border-cyan-500 border-t-transparent rounded-full animate-spin" />
      <p className="mt-4 text-cyan-400 tracking-widest text-sm uppercase">
        Initializing Spacetime Flow...
      </p>
    </div>
  </div>
);

export default function StigmergyFlowPage() {
  const [isLoading, setIsLoading] = useState(true);
  const [data, setData] = useState<ScheduleNode[]>([]);
  const [config, setConfig] = useState<SimulationConfig>({
    speed: 1,
    bloomStrength: 1.5,
    showConnections: true,
    distortion: 0.5,
  });
  const [analysis, setAnalysis] = useState<GeminiAnalysisResult | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Initialize mock data on mount
  useEffect(() => {
    const mockData = generateMockData();
    setData(mockData);

    // Fade out loading screen
    const timer = setTimeout(() => setIsLoading(false), 1000);
    return () => clearTimeout(timer);
  }, []);

  // Mock AI analysis (would connect to actual API in production)
  const handleAnalyze = useCallback(async () => {
    setIsAnalyzing(true);

    // Simulate API delay
    await new Promise((resolve) => setTimeout(resolve, 1500));

    // Mock analysis result
    const conflictCount = data.filter((d) => d.type === 'CONFLICT').length;
    const callCount = data.filter((d) => d.type === 'CALL').length;

    setAnalysis({
      summary: `Flow analysis complete. Detected ${data.length} assignment nodes across the spacetime manifold. ${conflictCount} conflict vortices require attention. Call distribution shows ${callCount} night-side trajectories.`,
      hotspots:
        conflictCount > 0
          ? [
              `${conflictCount} conflict vortices detected in the flow`,
              'Potential duty hour clustering on day 3-4',
              'Supervision gap risk in NIGHT sector',
            ]
          : [],
      recommendations: [
        'Consider redistributing CALL assignments to reduce clustering',
        'Strengthen magnetic field lines (supervision connections) in sparse regions',
        'Pre-compute fallback trajectories for N-1 contingency',
      ],
    });

    setIsAnalyzing(false);
  }, [data]);

  return (
    <div className="w-full h-screen text-white relative overflow-hidden font-sans">
      {isLoading && <LoadingScreen />}

      <StigmergyScene data={data} config={config} />

      <UIOverlay
        config={config}
        setConfig={setConfig}
        onAnalyze={handleAnalyze}
        analysis={analysis}
        isAnalyzing={isAnalyzing}
      />
    </div>
  );
}
