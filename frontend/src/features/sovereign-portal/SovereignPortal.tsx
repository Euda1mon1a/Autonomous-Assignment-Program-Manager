/**
 * Sovereign Portal - Command Dashboard
 *
 * Unified 4-panel view for schedule system monitoring.
 * Displays Spatial, Fairness, Solver, and Fragility metrics.
 *
 * @route /admin/labs/command
 */

'use client';

import { useState, useEffect, useRef } from 'react';
import { RefreshCw, Maximize2 } from 'lucide-react';
import { Panel } from './components/Panel';
import { StatusBadge } from './components/StatusBadge';
import { AlertFeed } from './components/AlertFeed';
import { SpatialMini } from './components/SpatialMini';
import { FairnessMini } from './components/FairnessMini';
import { SolverMini } from './components/SolverMini';
import { FragilityMini } from './components/FragilityMini';
import { PANEL_CONFIGS, generateMockDashboardState } from './constants';
import type { SovereignPortalProps, DashboardState, PanelId } from './types';

export function SovereignPortal({
  className = '',
}: SovereignPortalProps): JSX.Element {
  const [state, setState] = useState<DashboardState | null>(null);
  const [expandedPanel, setExpandedPanel] = useState<PanelId | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    setState(generateMockDashboardState());
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await new Promise((r) => setTimeout(r, 500));
    if (mountedRef.current) {
      setState(generateMockDashboardState());
      setIsRefreshing(false);
    }
  };

  const handleToggleExpand = (panelId: PanelId) => {
    setExpandedPanel((prev) => (prev === panelId ? null : panelId));
  };

  if (!state) {
    return (
      <div className="flex items-center justify-center h-full bg-slate-900">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-purple-500 border-t-transparent" />
          <p className="mt-4 text-sm uppercase tracking-widest text-purple-400">
            Initializing Command Portal...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className={`min-h-full bg-slate-900 p-6 ${className}`}>
      {/* Header */}
      <div className="flex justify-between items-start mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white mb-1">
            Sovereign Portal
          </h1>
          <p className="text-sm text-slate-400">
            Unified command dashboard for scheduling operations
          </p>
        </div>
        <div className="flex items-center gap-4">
          <StatusBadge status={state.status} lastUpdate={state.lastUpdate} />
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="p-2 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors"
          >
            <RefreshCw
              className={`w-5 h-5 text-slate-400 ${isRefreshing ? 'animate-spin' : ''}`}
            />
          </button>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 4-Panel Grid */}
        <div
          className={`lg:col-span-2 grid gap-4 ${
            expandedPanel ? 'grid-cols-2 grid-rows-2' : 'grid-cols-2'
          }`}
        >
          {/* Spatial Panel */}
          <Panel
            config={PANEL_CONFIGS[0]}
            isExpanded={expandedPanel === 'spatial'}
            onToggleExpand={() => handleToggleExpand('spatial')}
          >
            <SpatialMini metrics={state.spatial} />
          </Panel>

          {/* Fairness Panel */}
          {expandedPanel !== 'spatial' && (
            <Panel
              config={PANEL_CONFIGS[1]}
              isExpanded={expandedPanel === 'fairness'}
              onToggleExpand={() => handleToggleExpand('fairness')}
            >
              <FairnessMini metrics={state.fairness} />
            </Panel>
          )}

          {/* Solver Panel */}
          {expandedPanel !== 'fairness' && expandedPanel !== 'spatial' && (
            <Panel
              config={PANEL_CONFIGS[2]}
              isExpanded={expandedPanel === 'solver'}
              onToggleExpand={() => handleToggleExpand('solver')}
            >
              <SolverMini metrics={state.solver} />
            </Panel>
          )}

          {/* Fragility Panel */}
          {expandedPanel !== 'solver' &&
            expandedPanel !== 'fairness' &&
            expandedPanel !== 'spatial' && (
              <Panel
                config={PANEL_CONFIGS[3]}
                isExpanded={expandedPanel === 'fragility'}
                onToggleExpand={() => handleToggleExpand('fragility')}
              >
                <FragilityMini metrics={state.fragility} />
              </Panel>
            )}
        </div>

        {/* Alert Feed */}
        <div className="space-y-6">
          <AlertFeed alerts={state.alerts} />

          {/* Quick Actions */}
          <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4">
            <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wide mb-3">
              Quick Actions
            </h3>
            <div className="space-y-2">
              <button className="w-full flex items-center gap-2 px-3 py-2 bg-slate-700/50 hover:bg-slate-700 rounded-lg text-sm text-white transition-colors">
                <Maximize2 className="w-4 h-4 text-cyan-400" />
                Open Full Spatial View
              </button>
              <button className="w-full flex items-center gap-2 px-3 py-2 bg-slate-700/50 hover:bg-slate-700 rounded-lg text-sm text-white transition-colors">
                <Maximize2 className="w-4 h-4 text-purple-400" />
                Open Fairness Dashboard
              </button>
              <button className="w-full flex items-center gap-2 px-3 py-2 bg-slate-700/50 hover:bg-slate-700 rounded-lg text-sm text-white transition-colors">
                <Maximize2 className="w-4 h-4 text-amber-400" />
                Open Solver Console
              </button>
            </div>
          </div>

          {/* Info */}
          <div className="bg-slate-800/30 border border-slate-700/50 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-purple-400 mb-2">
              About Sovereign Portal
            </h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              The Sovereign Portal provides a unified command view of all
              scheduling subsystems. Monitor spatial coverage, workload
              fairness, solver optimization, and system fragility from a single
              dashboard. Click any panel to expand for detailed analysis.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default SovereignPortal;
