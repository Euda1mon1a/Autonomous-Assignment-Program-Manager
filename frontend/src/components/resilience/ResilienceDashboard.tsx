/**
 * ResilienceDashboard Component
 *
 * Main dashboard for resilience metrics inspired by cross-disciplinary best practices
 */

import React from 'react';
import { DefenseLevel } from './DefenseLevel';
import { UtilizationGauge } from './UtilizationGauge';
import { BurnoutRtDisplay } from './BurnoutRtDisplay';
import { N1ContingencyMap } from './N1ContingencyMap';
import { EarlyWarningPanel } from './EarlyWarningPanel';
import { Badge } from '../ui/Badge';

export interface ResilienceMetrics {
  defenseLevel: 'GREEN' | 'YELLOW' | 'ORANGE' | 'RED' | 'BLACK';
  utilization: {
    current: number; // 0-100
    threshold: number; // Usually 80
    trend: 'increasing' | 'stable' | 'decreasing';
  };
  burnoutRt: {
    value: number; // Reproduction number
    threshold: number; // Usually 1.0
    trend: 'increasing' | 'stable' | 'decreasing';
  };
  n1Contingency: {
    criticalResources: string[];
    vulnerableRotations: string[];
    recoveryDistance: number; // Minimum edits to recover
  };
  earlyWarnings: Array<{
    id: string;
    type: 'utilization' | 'burnout' | 'coverage' | 'compliance';
    severity: 'critical' | 'warning' | 'info';
    message: string;
    detectedAt: string;
  }>;
  lastUpdated: string;
}

export interface ResilienceDashboardProps {
  metrics: ResilienceMetrics;
  onRefresh?: () => void;
  onDrillDown?: (metric: string) => void;
  className?: string;
}

export const ResilienceDashboard: React.FC<ResilienceDashboardProps> = ({
  metrics,
  onRefresh,
  onDrillDown,
  className = '',
}) => {
  const criticalWarnings = metrics.earlyWarnings.filter(w => w.severity === 'critical');
  const hasActiveWarnings = metrics.earlyWarnings.length > 0;

  return (
    <div className={`resilience-dashboard space-y-6 ${className}`}>
      {/* Header */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold">Resilience Dashboard</h1>
            <p className="text-sm text-gray-600 mt-1">
              Cross-disciplinary resilience monitoring and early warning system
            </p>
          </div>
          {onRefresh && (
            <button
              onClick={onRefresh}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
              aria-label="Refresh metrics"
            >
              🔄 Refresh
            </button>
          )}
        </div>

        {/* Status Banner */}
        {hasActiveWarnings && (
          <div className="p-4 bg-yellow-50 border-l-4 border-yellow-500 rounded">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-2xl">⚠️</span>
                <div>
                  <div className="font-semibold text-yellow-900">
                    Active Warnings Detected
                  </div>
                  <div className="text-sm text-yellow-800">
                    {criticalWarnings.length > 0 && (
                      <span className="font-medium">
                        {criticalWarnings.length} critical,{' '}
                      </span>
                    )}
                    {metrics.earlyWarnings.length} total warnings
                  </div>
                </div>
              </div>
              <Badge variant={criticalWarnings.length > 0 ? 'destructive' : 'warning'}>
                {metrics.earlyWarnings.length} Active
              </Badge>
            </div>
          </div>
        )}

        {/* Last Updated */}
        <div className="text-xs text-gray-500 mt-4">
          Last updated: {new Date(metrics.lastUpdated).toLocaleString()}
        </div>
      </div>

      {/* Defense Level */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-xl font-bold mb-4">Defense Level</h2>
        <DefenseLevel
          level={metrics.defenseLevel}
          onDrillDown={() => onDrillDown?.('defense-level')}
        />
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Utilization */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-bold mb-4">Utilization (80% Threshold)</h2>
          <UtilizationGauge
            current={metrics.utilization.current}
            threshold={metrics.utilization.threshold}
            trend={metrics.utilization.trend}
            onDrillDown={() => onDrillDown?.('utilization')}
          />
        </div>

        {/* Burnout Rt */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-bold mb-4">Burnout Reproduction (Rt)</h2>
          <BurnoutRtDisplay
            value={metrics.burnoutRt.value}
            threshold={metrics.burnoutRt.threshold}
            trend={metrics.burnoutRt.trend}
            onDrillDown={() => onDrillDown?.('burnout-rt')}
          />
        </div>
      </div>

      {/* N-1 Contingency */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-xl font-bold mb-4">N-1 Contingency Analysis</h2>
        <N1ContingencyMap
          criticalResources={metrics.n1Contingency.criticalResources}
          vulnerableRotations={metrics.n1Contingency.vulnerableRotations}
          recoveryDistance={metrics.n1Contingency.recoveryDistance}
          onDrillDown={() => onDrillDown?.('n1-contingency')}
        />
      </div>

      {/* Early Warnings */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-xl font-bold mb-4">Early Warning System</h2>
        <EarlyWarningPanel
          warnings={metrics.earlyWarnings}
          onDismiss={(id) => console.log('Dismiss warning:', id)}
          onDrillDown={() => onDrillDown?.('early-warnings')}
        />
      </div>

      {/* Info Footer */}
      <div className="bg-gray-50 rounded-lg p-4 text-xs text-gray-600">
        <div className="font-medium mb-2">Resilience Framework Concepts:</div>
        <ul className="list-disc list-inside space-y-1">
          <li><strong>80% Utilization Threshold:</strong> Queuing theory prevents cascade failures</li>
          <li><strong>N-1 Contingency:</strong> Power grid-style vulnerability detection</li>
          <li><strong>Defense in Depth:</strong> 5-tier safety levels (GREEN → BLACK)</li>
          <li><strong>Burnout Rt:</strong> Epidemiological reproduction number for burnout spread</li>
          <li><strong>Early Warnings:</strong> SPC monitoring with Western Electric rules</li>
        </ul>
      </div>
    </div>
  );
};

export default ResilienceDashboard;
