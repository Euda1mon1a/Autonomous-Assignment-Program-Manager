'use client';

/**
 * RigidityBadge Component
 *
 * Displays time crystal rigidity score for schedule stability analysis.
 * Shows how much a schedule changes between versions (anti-churn metric).
 */
import React from 'react';
import { Loader2, Lock, Shield, AlertTriangle, Flame } from 'lucide-react';
import {
  useRigidityScore,
  getRigidityColorClass,
  getStabilityIcon,
} from '@/hooks/useRigidityScore';

// ============================================================================
// Types
// ============================================================================

export interface RigidityBadgeProps {
  /** Current schedule assignments */
  currentAssignments: Array<Record<string, string>> | null;
  /** Proposed schedule assignments */
  proposedAssignments: Array<Record<string, string>> | null;
  /** Show detailed breakdown */
  detailed?: boolean;
}

// ============================================================================
// Component
// ============================================================================

export function RigidityBadge({
  currentAssignments,
  proposedAssignments,
  detailed = false,
}: RigidityBadgeProps) {
  const { data, isLoading, error } = useRigidityScore(
    currentAssignments,
    proposedAssignments
  );

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-sm text-slate-400">
        <Loader2 className="w-4 h-4 animate-spin" />
        <span>Calculating rigidity...</span>
      </div>
    );
  }

  // Error or no data
  if (error || !data) {
    return (
      <div className="text-sm text-slate-500">
        Rigidity data unavailable
      </div>
    );
  }

  // Get stability icon component
  const getStabilityIconComponent = (grade: string) => {
    switch (grade) {
      case 'excellent':
        return <Lock className="w-4 h-4" />;
      case 'good':
        return <Shield className="w-4 h-4" />;
      case 'fair':
        return <AlertTriangle className="w-4 h-4" />;
      case 'poor':
      case 'unstable':
        return <Flame className="w-4 h-4" />;
      default:
        return null;
    }
  };

  const Icon = getStabilityIconComponent(data.stability_grade);

  // Compact badge
  if (!detailed) {
    return (
      <div
        className={`flex items-center gap-1.5 px-2.5 py-1 bg-slate-800 rounded-lg ${getRigidityColorClass(data.rigidity_score)}`}
      >
        {Icon}
        <span className="text-xs font-medium">Rigidity:</span>
        <span className="text-sm font-semibold">
          {data.rigidity_score.toFixed(2)}
        </span>
        <span className="text-xs text-slate-400">
          ({data.stability_grade})
        </span>
      </div>
    );
  }

  // Detailed view
  return (
    <div className="space-y-2">
      {/* Score header */}
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-slate-300">
          Schedule Rigidity:
        </span>
        <div
          className={`flex items-center gap-2 ${getRigidityColorClass(data.rigidity_score)}`}
        >
          {Icon}
          <span className="text-sm font-semibold">
            {data.rigidity_score.toFixed(2)}
          </span>
          <span
            className={`text-xs px-2 py-0.5 rounded ${
              data.stability_grade === 'excellent'
                ? 'bg-green-500/20 text-green-400'
                : data.stability_grade === 'good'
                ? 'bg-blue-500/20 text-blue-400'
                : data.stability_grade === 'fair'
                ? 'bg-yellow-500/20 text-yellow-400'
                : 'bg-red-500/20 text-red-400'
            }`}
          >
            {data.stability_grade}
          </span>
        </div>
      </div>

      {/* Change statistics */}
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div className="px-2 py-1.5 bg-slate-800 rounded">
          <div className="text-slate-500">Changes</div>
          <div className="text-white font-medium">
            {data.changed_assignments} / {data.total_assignments}
          </div>
        </div>
        <div className="px-2 py-1.5 bg-slate-800 rounded">
          <div className="text-slate-500">Churn Rate</div>
          <div className="text-white font-medium">
            {(data.change_rate * 100).toFixed(1)}%
          </div>
        </div>
      </div>

      {/* Affected faculty */}
      {data.affected_faculty.length > 0 && (
        <div className="text-xs">
          <div className="text-slate-400 mb-1">
            Affected Faculty: {data.affected_faculty.length}
          </div>
          {data.affected_faculty.length <= 3 && (
            <div className="text-slate-500">
              {data.affected_faculty.join(', ')}
            </div>
          )}
        </div>
      )}

      {/* Interpretation */}
      <div
        className={`px-3 py-2 rounded-lg text-xs ${
          data.rigidity_score >= 0.85
            ? 'bg-green-500/10 text-green-400'
            : data.rigidity_score >= 0.70
            ? 'bg-blue-500/10 text-blue-400'
            : data.rigidity_score >= 0.50
            ? 'bg-yellow-500/10 text-yellow-400'
            : 'bg-red-500/10 text-red-400'
        }`}
      >
        {data.rigidity_score >= 0.95 && '🔒 Excellent stability - minimal disruption'}
        {data.rigidity_score >= 0.85 && data.rigidity_score < 0.95 && '✓ Good stability - acceptable churn'}
        {data.rigidity_score >= 0.70 && data.rigidity_score < 0.85 && '⚠ Moderate churn - review changes'}
        {data.rigidity_score >= 0.50 && data.rigidity_score < 0.70 && '⚠⚠ High churn - significant disruption'}
        {data.rigidity_score < 0.50 && '🔥 Unstable - excessive reshuffling'}
      </div>
    </div>
  );
}

export default RigidityBadge;
