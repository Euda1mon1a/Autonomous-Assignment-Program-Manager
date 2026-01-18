/**
 * Sovereign Portal Constants
 *
 * Mock data and utilities for the command dashboard.
 */

import type {
  PanelConfig,
  DashboardState,
  SystemAlert,
  SystemStatus,
} from './types';

/**
 * Panel configurations
 */
export const PANEL_CONFIGS: PanelConfig[] = [
  {
    id: 'spatial',
    label: 'Spatial Coverage',
    description: 'Schedule distribution across time and resources',
    status: 'nominal',
    value: 94.2,
    unit: '%',
  },
  {
    id: 'fairness',
    label: 'Fairness Index',
    description: 'Workload equity across faculty',
    status: 'warning',
    value: 0.87,
    unit: 'Jains',
  },
  {
    id: 'solver',
    label: 'Solver Status',
    description: 'CP-SAT optimization engine',
    status: 'nominal',
    value: 98.5,
    unit: '%',
  },
  {
    id: 'fragility',
    label: 'System Fragility',
    description: 'Resilience and failure risk',
    status: 'nominal',
    value: 0.23,
    unit: 'idx',
  },
];

/**
 * Status colors
 */
export const STATUS_COLORS: Record<PanelConfig['status'], string> = {
  nominal: 'text-green-400',
  warning: 'text-amber-400',
  critical: 'text-red-400',
};

/**
 * Status background colors
 */
export const STATUS_BG_COLORS: Record<PanelConfig['status'], string> = {
  nominal: 'bg-green-500/20 border-green-500/50',
  warning: 'bg-amber-500/20 border-amber-500/50',
  critical: 'bg-red-500/20 border-red-500/50',
};

/**
 * System status colors
 */
export const SYSTEM_STATUS_COLORS: Record<SystemStatus, string> = {
  OPERATIONAL: 'text-green-400',
  DEGRADED: 'text-amber-400',
  CRITICAL: 'text-red-400',
  OFFLINE: 'text-slate-400',
};

/**
 * Generate mock dashboard state
 */
export function generateMockDashboardState(): DashboardState {
  const alerts: SystemAlert[] = [
    {
      id: 'a1',
      panel: 'fairness',
      severity: 'warning',
      message: 'Faculty Dr. Alpha at 115% load capacity',
      timestamp: new Date(Date.now() - 300000),
    },
    {
      id: 'a2',
      panel: 'spatial',
      severity: 'info',
      message: 'Block 10 coverage optimization complete',
      timestamp: new Date(Date.now() - 600000),
    },
    {
      id: 'a3',
      panel: 'fragility',
      severity: 'info',
      message: 'N-1 resilience verified for all critical paths',
      timestamp: new Date(Date.now() - 900000),
    },
  ];

  return {
    status: 'OPERATIONAL',
    spatial: {
      coveragePercent: 94.2,
      gapCount: 3,
      distributionScore: 0.91,
    },
    fairness: {
      giniCoefficient: 0.12,
      jainsIndex: 0.87,
      maxDeviation: 15,
    },
    solver: {
      objectiveValue: 1247.5,
      constraintsSatisfied: 142,
      constraintsTotal: 145,
      solutionQuality: 'feasible',
    },
    fragility: {
      systemFragility: 0.23,
      criticalPaths: 2,
      redundancyLevel: 72,
    },
    alerts,
    lastUpdate: new Date(),
  };
}

/**
 * Compute overall system status from panel statuses
 */
export function computeSystemStatus(
  panels: PanelConfig[]
): SystemStatus {
  const hasCritical = panels.some((p) => p.status === 'critical');
  const hasWarning = panels.some((p) => p.status === 'warning');

  if (hasCritical) return 'CRITICAL';
  if (hasWarning) return 'DEGRADED';
  return 'OPERATIONAL';
}

/**
 * Format timestamp for display
 */
export function formatTimestamp(date: Date): string {
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const minutes = Math.floor(diff / 60000);

  if (minutes < 1) return 'Just now';
  if (minutes < 60) return `${minutes}m ago`;

  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;

  return date.toLocaleDateString();
}
