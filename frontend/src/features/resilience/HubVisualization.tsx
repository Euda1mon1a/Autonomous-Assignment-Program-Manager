/**
 * Hub Visualization Component
 *
 * Displays network graph visualization of resource dependencies
 * and hub centrality analysis. Shows faculty members as nodes with
 * connections to services they cover, sized/colored by risk level.
 *
 * ## Data Source
 * API: POST /api/v1/resilience/tier3/hubs/analyze
 * MCP: mcp__residency-scheduler__analyze_hub_centrality_tool
 *
 * ## Response Structure (HubAnalysisResponse)
 * ```typescript
 * {
 *   analyzed_at: string;
 *   total_faculty: number;
 *   total_hubs: number;
 *   hubs: Array<{
 *     faculty_id: string;
 *     faculty_name: string;
 *     composite_score: number;      // 0-1, weighted centrality
 *     risk_level: 'low' | 'moderate' | 'high' | 'critical' | 'catastrophic';
 *     unique_services: number;      // Services only this person covers
 *     degree_centrality: number;    // Connection breadth
 *     betweenness_centrality: number; // Bottleneck potential
 *     services_covered: number;
 *     replacement_difficulty: number; // 0-1
 *   }>;
 * }
 * ```
 *
 * ## Visualization Requirements
 *
 * 1. **Force-Directed Graph** (recommended: React Three Fiber or Recharts)
 *    - Nodes = Faculty members
 *    - Edges = Shared service coverage
 *    - Node size = composite_score (larger = more critical)
 *    - Node color = risk_level (gradient: green->yellow->orange->red->purple)
 *
 * 2. **Node Interaction**
 *    - Hover: Show tooltip with faculty name, risk level, services covered
 *    - Click: Expand to show detailed hub profile (calls GET /tier3/hubs/{id}/profile)
 *
 * 3. **Risk Level Color Mapping**
 *    - low: #22c55e (green-500)
 *    - moderate: #eab308 (yellow-500)
 *    - high: #f97316 (orange-500)
 *    - critical: #ef4444 (red-500)
 *    - catastrophic: #a855f7 (purple-500)
 *
 * 4. **Supporting Views**
 *    - Summary stats panel (total hubs by risk level)
 *    - Cross-training recommendations list
 *    - Hub distribution report
 *
 * ## Implementation Options
 *
 * Option A: React Three Fiber (Recommended - matches existing 3D visualizations)
 *   - Use @react-three/drei for controls
 *   - Force simulation via custom hook or d3-force
 *   - See: frontend/src/features/voxel-schedule/SolverVisualization.tsx
 *   - See: frontend/src/features/holographic-hub/HolographicManifold.tsx
 *
 * Option B: Recharts (Simpler, 2D)
 *   - Already installed in package.json
 *   - ScatterChart with custom shapes
 *   - Less visual impact but faster to implement
 *
 * Option C: react-force-graph (External library needed)
 *   - npm install react-force-graph-2d
 *   - Purpose-built for network graphs
 *   - Would need to be added to dependencies
 *
 * ## API Hook (to be created)
 * ```typescript
 * // frontend/src/hooks/useHubAnalysis.ts
 * export function useHubAnalysis(options?: { startDate?: string; endDate?: string }) {
 *   return useQuery({
 *     queryKey: ['hub-analysis', options?.startDate, options?.endDate],
 *     queryFn: async () => {
 *       const params = new URLSearchParams();
 *       if (options?.startDate) params.append('start_date', options.startDate);
 *       if (options?.endDate) params.append('end_date', options.endDate);
 *       const response = await fetch(`/api/v1/resilience/tier3/hubs/analyze?${params}`, {
 *         method: 'POST'
 *       });
 *       return response.json();
 *     }
 *   });
 * }
 * ```
 *
 * ## Related Endpoints
 * - GET /tier3/hubs/top - Top N critical hubs
 * - GET /tier3/hubs/{id}/profile - Detailed hub profile
 * - GET /tier3/hubs/cross-training - Training recommendations
 * - GET /tier3/hubs/distribution - System-wide distribution report
 * - GET /tier3/hubs/status - Analysis status summary
 *
 * @module features/resilience/HubVisualization
 */

'use client';

import React from 'react';

// =============================================================================
// Types
// =============================================================================

export type HubRiskLevel = 'low' | 'moderate' | 'high' | 'critical' | 'catastrophic';

export interface HubNode {
  facultyId: string;
  facultyName: string;
  compositeScore: number;
  riskLevel: HubRiskLevel;
  uniqueServices: number;
  degreeCentrality: number;
  betweennessCentrality: number;
  servicesCovered: number;
  replacementDifficulty: number;
}

export interface HubAnalysisData {
  analyzedAt: string;
  totalFaculty: number;
  totalHubs: number;
  hubs: HubNode[];
}

export interface HubVisualizationProps {
  /** Optional data override (for testing or parent-controlled data) */
  data?: HubAnalysisData;
  /** CSS class name */
  className?: string;
  /** Callback when a hub node is selected */
  onHubSelect?: (facultyId: string) => void;
  /** Show loading skeleton */
  isLoading?: boolean;
  /** Error message to display */
  error?: string | null;
}

// =============================================================================
// Constants
// =============================================================================

const RISK_COLORS: Record<HubRiskLevel, string> = {
  low: '#22c55e',       // green-500
  moderate: '#eab308',  // yellow-500
  high: '#f97316',      // orange-500
  critical: '#ef4444',  // red-500
  catastrophic: '#a855f7', // purple-500
};

const RISK_BG_COLORS: Record<HubRiskLevel, string> = {
  low: 'bg-green-500/20',
  moderate: 'bg-yellow-500/20',
  high: 'bg-orange-500/20',
  critical: 'bg-red-500/20',
  catastrophic: 'bg-purple-500/20',
};

const RISK_TEXT_COLORS: Record<HubRiskLevel, string> = {
  low: 'text-green-400',
  moderate: 'text-yellow-400',
  high: 'text-orange-400',
  critical: 'text-red-400',
  catastrophic: 'text-purple-400',
};

// =============================================================================
// Sub-Components
// =============================================================================

/**
 * Summary statistics panel showing hub counts by risk level.
 */
const SummaryPanel: React.FC<{ hubs: HubNode[]; totalFaculty: number }> = ({
  hubs,
  totalFaculty,
}) => {
  const counts = hubs.reduce(
    (acc, hub) => {
      acc[hub.riskLevel] = (acc[hub.riskLevel] || 0) + 1;
      return acc;
    },
    {} as Record<HubRiskLevel, number>
  );

  return (
    <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
      <h3 className="text-sm font-semibold text-slate-300 mb-3">Hub Summary</h3>
      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-slate-400">Total Faculty</span>
          <span className="text-white font-mono">{totalFaculty}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-slate-400">Identified Hubs</span>
          <span className="text-white font-mono">{hubs.length}</span>
        </div>
        <div className="border-t border-slate-700 pt-2 mt-2">
          {(['catastrophic', 'critical', 'high', 'moderate', 'low'] as HubRiskLevel[]).map(
            (level) =>
              counts[level] ? (
                <div key={level} className="flex justify-between items-center py-1">
                  <span className={`capitalize ${RISK_TEXT_COLORS[level]}`}>{level}</span>
                  <span
                    className={`px-2 py-0.5 rounded text-xs font-mono ${RISK_BG_COLORS[level]} ${RISK_TEXT_COLORS[level]}`}
                  >
                    {counts[level]}
                  </span>
                </div>
              ) : null
          )}
        </div>
      </div>
    </div>
  );
};

/**
 * Individual hub card showing key metrics.
 */
const HubCard: React.FC<{
  hub: HubNode;
  onClick?: () => void;
}> = ({ hub, onClick }) => {
  return (
    <button
      onClick={onClick}
      className={`w-full text-left p-3 rounded-lg border transition-all hover:scale-[1.02] ${RISK_BG_COLORS[hub.riskLevel]} border-slate-700 hover:border-slate-500`}
    >
      <div className="flex items-start justify-between">
        <div>
          <h4 className="font-medium text-white">{hub.facultyName}</h4>
          <p className={`text-xs capitalize ${RISK_TEXT_COLORS[hub.riskLevel]}`}>
            {hub.riskLevel} risk
          </p>
        </div>
        <div
          className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold"
          style={{ backgroundColor: RISK_COLORS[hub.riskLevel] }}
        >
          {Math.round(hub.compositeScore * 100)}
        </div>
      </div>
      <div className="mt-2 grid grid-cols-2 gap-2 text-xs text-slate-400">
        <div>
          <span className="block text-slate-500">Unique Services</span>
          <span className="text-white font-mono">{hub.uniqueServices}</span>
        </div>
        <div>
          <span className="block text-slate-500">Replace Difficulty</span>
          <span className="text-white font-mono">
            {Math.round(hub.replacementDifficulty * 100)}%
          </span>
        </div>
      </div>
    </button>
  );
};

/**
 * Placeholder for the force-directed network graph.
 * TODO: Implement with React Three Fiber or Recharts
 */
const NetworkGraphPlaceholder: React.FC<{ hubs: HubNode[] }> = ({ hubs }) => {
  return (
    <div className="relative h-full min-h-[400px] bg-slate-900 rounded-lg border border-slate-700 flex items-center justify-center">
      {/* Decorative background */}
      <div className="absolute inset-0 overflow-hidden opacity-20">
        <svg className="w-full h-full" viewBox="0 0 400 400">
          {/* Draw simple node positions for visual hint */}
          {hubs.slice(0, 20).map((hub, i) => {
            const angle = (i / Math.min(hubs.length, 20)) * Math.PI * 2;
            const radius = 120 + hub.compositeScore * 50;
            const cx = 200 + Math.cos(angle) * radius;
            const cy = 200 + Math.sin(angle) * radius;
            const r = 8 + hub.compositeScore * 12;
            return (
              <g key={hub.facultyId}>
                <line
                  x1="200"
                  y1="200"
                  x2={cx}
                  y2={cy}
                  stroke={RISK_COLORS[hub.riskLevel]}
                  strokeWidth="1"
                  opacity="0.3"
                />
                <circle
                  cx={cx}
                  cy={cy}
                  r={r}
                  fill={RISK_COLORS[hub.riskLevel]}
                  opacity="0.5"
                />
              </g>
            );
          })}
          <circle cx="200" cy="200" r="5" fill="#64748b" />
        </svg>
      </div>

      {/* Placeholder message */}
      <div className="relative z-10 text-center p-8">
        <div className="text-4xl mb-4">🕸️</div>
        <h3 className="text-lg font-semibold text-white mb-2">Network Graph</h3>
        <p className="text-sm text-slate-400 max-w-xs">
          Interactive force-directed visualization showing faculty hub relationships and
          service dependencies.
        </p>
        <div className="mt-4 text-xs text-slate-500">
          {hubs.length} hub nodes to render
        </div>
      </div>
    </div>
  );
};

/**
 * Loading skeleton for the visualization.
 */
const LoadingSkeleton: React.FC = () => (
  <div className="animate-pulse space-y-4">
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
      <div className="lg:col-span-2 h-[400px] bg-slate-800 rounded-lg" />
      <div className="space-y-4">
        <div className="h-40 bg-slate-800 rounded-lg" />
        <div className="h-24 bg-slate-800 rounded-lg" />
        <div className="h-24 bg-slate-800 rounded-lg" />
      </div>
    </div>
  </div>
);

/**
 * Error display component.
 */
const ErrorDisplay: React.FC<{ message: string }> = ({ message }) => (
  <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-6 text-center">
    <div className="text-2xl mb-2">⚠️</div>
    <h3 className="text-red-400 font-medium mb-1">Failed to Load Hub Analysis</h3>
    <p className="text-sm text-slate-400">{message}</p>
  </div>
);

// =============================================================================
// Main Component
// =============================================================================

/**
 * Hub Visualization Component
 *
 * Displays network graph visualization of resource dependencies
 * and hub centrality analysis. Currently renders a scaffold with
 * summary statistics and hub cards. The network graph itself is
 * a placeholder pending D3/Three.js implementation.
 *
 * @example
 * ```tsx
 * // With data from parent
 * <HubVisualization
 *   data={hubAnalysisData}
 *   onHubSelect={(id) => console.log('Selected:', id)}
 * />
 *
 * // With loading state
 * <HubVisualization isLoading />
 *
 * // With error
 * <HubVisualization error="Network error" />
 * ```
 */
export const HubVisualization: React.FC<HubVisualizationProps> = ({
  data,
  className,
  onHubSelect,
  isLoading = false,
  error = null,
}) => {
  if (isLoading) {
    return (
      <div className={className}>
        <LoadingSkeleton />
      </div>
    );
  }

  if (error) {
    return (
      <div className={className}>
        <ErrorDisplay message={error} />
      </div>
    );
  }

  // Default empty state
  const hubs = data?.hubs ?? [];
  const totalFaculty = data?.totalFaculty ?? 0;

  if (hubs.length === 0) {
    return (
      <div className={className}>
        <div className="bg-slate-800/50 rounded-lg p-8 text-center border border-slate-700">
          <div className="text-3xl mb-3">📊</div>
          <h3 className="text-white font-medium mb-1">No Hub Data Available</h3>
          <p className="text-sm text-slate-400">
            Run hub analysis to identify critical faculty members.
          </p>
        </div>
      </div>
    );
  }

  // Sort hubs by composite score (most critical first)
  const sortedHubs = [...hubs].sort((a, b) => b.compositeScore - a.compositeScore);

  return (
    <div className={className}>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Network Graph - takes 2/3 width on large screens */}
        <div className="lg:col-span-2">
          <NetworkGraphPlaceholder hubs={sortedHubs} />
        </div>

        {/* Sidebar with summary and hub list */}
        <div className="space-y-4">
          <SummaryPanel hubs={hubs} totalFaculty={totalFaculty} />

          <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
            <h3 className="text-sm font-semibold text-slate-300 mb-3">Critical Hubs</h3>
            <div className="space-y-2 max-h-[300px] overflow-y-auto">
              {sortedHubs.slice(0, 10).map((hub) => (
                <HubCard
                  key={hub.facultyId}
                  hub={hub}
                  onClick={() => onHubSelect?.(hub.facultyId)}
                />
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Analysis timestamp */}
      {data?.analyzedAt && (
        <div className="mt-4 text-xs text-slate-500 text-right">
          Analyzed: {new Date(data.analyzedAt).toLocaleString()}
        </div>
      )}
    </div>
  );
};

export default HubVisualization;
