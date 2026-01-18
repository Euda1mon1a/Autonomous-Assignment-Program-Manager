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
 *
 * @route /admin/labs/optimization
 */

import { useState, useCallback } from 'react';
import dynamic from 'next/dynamic';
import Link from 'next/link';
import { ArrowLeft, Cpu, Layers, Circle, Box } from 'lucide-react';

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

type TabId = 'cpsat' | 'brane' | 'foam';

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
      </div>
    </div>
  );
}
