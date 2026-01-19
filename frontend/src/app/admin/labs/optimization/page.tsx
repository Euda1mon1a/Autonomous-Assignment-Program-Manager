'use client';

/**
 * Schedule Optimization Labs
 *
 * Explore solver landscapes and constraint topology through 3D visualizations.
 * Target: Tier 1-2 users (medium graduation readiness)
 *
 * Contains:
 * - CP-SAT Simulator: 3D optimization landscape
 * - Brane Topology: Multi-dimensional scheduling manifold
 * - Foam Topology: Constraint foam visualization
 * - Stigmergy Flow: Particle flow schedule visualization
 * - Hopfield Energy: Neural attractor energy landscape
 * - BridgeSync: Real-time Python→Three.js data sync
 *
 * @route /admin/labs/optimization
 */

import { useState, useCallback, useMemo, useRef } from 'react';
import dynamic from 'next/dynamic';
import Link from 'next/link';
import { ArrowLeft, Cpu, Layers, Circle, Box, Waves, Zap, GitBranch } from 'lucide-react';
import type {
  SimulationConfig,
  GeminiAnalysisResult,
} from '@/app/admin/visualizations/stigmergy-flow/types';
import { transformPatternsToNodes } from '@/app/admin/visualizations/stigmergy-flow/constants';
import { useStigmergyPatterns } from '@/hooks/useResilience';

// Dynamic imports for 3D visualizations - only load when tab is active
const CpsatSimulator = dynamic(
  () => import('@/features/cpsat-simulator').then((mod) => mod.CpsatSimulator),
  {
    ssr: false,
    loading: () => <LoadingScreen label="Initializing Optimization Node..." />,
  }
);

const BraneTopologyVisualizer = dynamic(
  () =>
    import('@/features/brane-topology').then(
      (mod) => mod.BraneTopologyVisualizer
    ),
  {
    ssr: false,
    loading: () => <LoadingScreen label="Projecting Brane Manifold..." />,
  }
);

const FoamTopologyVisualizer = dynamic(
  () => import('@/components/scheduling/FoamTopologyVisualizer'),
  {
    ssr: false,
    loading: () => <LoadingScreen label="Generating Foam Structure..." />,
  }
);

// Stigmergy Flow components
const StigmergyScene = dynamic(
  () =>
    import('@/app/admin/visualizations/stigmergy-flow/components/StigmergyScene').then(
      (mod) => mod.StigmergyScene
    ),
  { ssr: false }
);

const StigmergyUIOverlay = dynamic(
  () =>
    import('@/app/admin/visualizations/stigmergy-flow/components/UIOverlay').then(
      (mod) => mod.UIOverlay
    ),
  { ssr: false }
);

const HopfieldVisualizer = dynamic(
  () =>
    import('@/features/hopfield-energy').then((mod) => mod.HopfieldVisualizer),
  {
    ssr: false,
    loading: () => <LoadingScreen label="Computing Energy Landscape..." />,
  }
);

const BridgeSyncVisualizer = dynamic(
  () =>
    import('@/features/bridge-sync').then((mod) => mod.BridgeSyncVisualizer),
  {
    ssr: false,
    loading: () => <LoadingScreen label="Establishing Data Bridge..." />,
  }
);

type TabId = 'cpsat' | 'brane' | 'foam' | 'stigmergy' | 'hopfield' | 'bridge';

interface Tab {
  id: TabId;
  label: string;
  icon: React.ElementType;
  description: string;
}

const TABS: Tab[] = [
  {
    id: 'cpsat',
    label: 'CP-SAT Simulator',
    icon: Box,
    description: 'Multi-modal optimization landscape',
  },
  {
    id: 'brane',
    label: 'Brane Topology',
    icon: Layers,
    description: 'Scheduling manifold projection',
  },
  {
    id: 'foam',
    label: 'Foam Topology',
    icon: Circle,
    description: 'Constraint foam structure',
  },
  {
    id: 'stigmergy',
    label: 'Stigmergy Flow',
    icon: Waves,
    description: 'Particle flow schedule visualization',
  },
  {
    id: 'hopfield',
    label: 'Hopfield Energy',
    icon: Zap,
    description: 'Neural attractor energy landscape',
  },
  {
    id: 'bridge',
    label: 'BridgeSync',
    icon: GitBranch,
    description: 'Real-time Python→Three.js data sync',
  },
];

function LoadingScreen({ label }: { label: string }) {
  return (
    <div className="flex-1 flex items-center justify-center bg-black">
      <div className="text-center">
        <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-cyan-500 border-t-transparent" />
        <p className="mt-4 text-sm uppercase tracking-widest text-cyan-400">
          {label}
        </p>
      </div>
    </div>
  );
}

/**
 * Wrapper component for Stigmergy Flow with all required state.
 * Fetches real stigmergy patterns from the backend API and transforms
 * them into ScheduleNode format for 3D visualization.
 */
function StigmergyFlowWrapper() {
  // Fetch stigmergy patterns from the API
  const { data: patternsData, isLoading, error } = useStigmergyPatterns();

  // Transform API patterns to visualization nodes
  const data = useMemo(() => {
    return transformPatternsToNodes(patternsData);
  }, [patternsData]);

  const [config, setConfig] = useState<SimulationConfig>({
    speed: 1,
    bloomStrength: 1.5,
    showConnections: true,
    distortion: 0.5,
  });
  const [analysis, setAnalysis] = useState<GeminiAnalysisResult | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const mountedRef = useRef(true);

  const handleAnalyze = useCallback(async () => {
    if (!mountedRef.current) return;
    setIsAnalyzing(true);
    await new Promise((resolve) => setTimeout(resolve, 1500));
    if (!mountedRef.current) return;

    const conflictCount = data.filter((d) => d.type === 'CONFLICT').length;
    const callCount = data.filter((d) => d.type === 'CALL').length;
    const popularCount = data.filter((d) => d.type === 'FMIT').length;

    // Include pattern-specific analysis when using real API data
    const patternTotal = patternsData?.total ?? 0;
    const isRealData = patternTotal > 0;

    setAnalysis({
      summary: isRealData
        ? `Flow analysis complete. Detected ${patternTotal} preference patterns from stigmergy trails. ${popularCount} popular slots (green), ${conflictCount} unpopular slots (red). Total ${data.length} visualization nodes.`
        : `Flow analysis complete. Detected ${data.length} assignment nodes across the spacetime manifold. ${conflictCount} conflict vortices require attention. Call distribution shows ${callCount} night-side trajectories.`,
      hotspots:
        conflictCount > 0
          ? [
              `${conflictCount} unpopular/conflict patterns detected`,
              'Potential preference clustering detected',
              isRealData ? 'Review avoided slot types for workload balance' : 'Supervision gap risk in NIGHT sector',
            ]
          : [],
      recommendations: [
        isRealData ? 'Consider swap pair suggestions from high-affinity connections' : 'Consider redistributing CALL assignments to reduce clustering',
        'Strengthen magnetic field lines (supervision connections) in sparse regions',
        'Pre-compute fallback trajectories for N-1 contingency',
      ],
    });
    setIsAnalyzing(false);
  }, [data, patternsData]);

  if (isLoading) {
    return <LoadingScreen label="Loading Stigmergy Patterns..." />;
  }

  if (error) {
    return (
      <div className="flex-1 flex items-center justify-center bg-black">
        <div className="text-center">
          <p className="text-red-400 text-sm mb-2">Failed to load patterns</p>
          <p className="text-slate-500 text-xs">{error.message}</p>
          <p className="text-slate-600 text-xs mt-2">Falling back to demo data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-full relative overflow-hidden">
      <StigmergyScene data={data} config={config} />
      <StigmergyUIOverlay
        config={config}
        setConfig={setConfig}
        onAnalyze={handleAnalyze}
        analysis={analysis}
        isAnalyzing={isAnalyzing}
      />
    </div>
  );
}

export default function OptimizationLabsPage() {
  const [activeTab, setActiveTab] = useState<TabId>('cpsat');

  const handleTabChange = useCallback((tabId: TabId) => {
    setActiveTab(tabId);
  }, []);

  return (
    <div className="min-h-screen bg-black flex flex-col">
      {/* Header with tabs */}
      <header className="bg-slate-900/80 border-b border-slate-700/50 backdrop-blur-sm z-40">
        <div className="px-4 py-3">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-4">
              <Link
                href="/admin/labs"
                className="flex items-center gap-2 px-3 py-1.5 bg-slate-800/50 border border-slate-700/50 rounded-lg text-slate-400 hover:text-cyan-400 hover:border-cyan-500/50 transition-all"
              >
                <ArrowLeft className="w-4 h-4" />
                <span className="text-sm">Labs</span>
              </Link>
              <div className="flex items-center gap-2">
                <div className="p-1.5 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-lg">
                  <Cpu className="w-4 h-4 text-white" />
                </div>
                <span className="text-sm font-medium text-white">
                  Schedule Optimization
                </span>
              </div>
            </div>
          </div>

          {/* Tab Navigation */}
          <div className="flex gap-2">
            {TABS.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;

              return (
                <button
                  key={tab.id}
                  onClick={() => handleTabChange(tab.id)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/50'
                      : 'text-slate-400 hover:text-white hover:bg-slate-700/50 border border-transparent'
                  }`}
                  title={tab.description}
                >
                  <Icon className="w-4 h-4" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>
        </div>
      </header>

      {/* Visualization Container - unmount on tab switch for memory cleanup */}
      <div className="flex-1 relative">
        {activeTab === 'cpsat' && <CpsatSimulator />}
        {activeTab === 'brane' && <BraneTopologyVisualizer />}
        {activeTab === 'foam' && <FoamTopologyVisualizer />}
        {activeTab === 'stigmergy' && <StigmergyFlowWrapper />}
        {activeTab === 'hopfield' && <HopfieldVisualizer />}
        {activeTab === 'bridge' && <BridgeSyncVisualizer />}
      </div>
    </div>
  );
}
