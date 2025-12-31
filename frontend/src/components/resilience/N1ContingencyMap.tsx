/**
 * N1ContingencyMap Component
 *
 * Displays N-1 contingency analysis (power grid-style vulnerability detection)
 */

import React, { useState } from 'react';
import { Badge } from '../ui/Badge';

export interface N1ContingencyMapProps {
  criticalResources: string[]; // People who are single points of failure
  vulnerableRotations: string[]; // Rotations that fail if one person is removed
  recoveryDistance: number; // Minimum edits to recover from N-1 shock
  onDrillDown?: () => void;
  className?: string;
}

export const N1ContingencyMap: React.FC<N1ContingencyMapProps> = ({
  criticalResources,
  vulnerableRotations,
  recoveryDistance,
  onDrillDown,
  className = '',
}) => {
  const [selectedResource, setSelectedResource] = useState<string | null>(null);

  const hasCriticalVulnerabilities = criticalResources.length > 0 || vulnerableRotations.length > 0;
  const severityLevel = criticalResources.length > 3 ? 'high' : criticalResources.length > 0 ? 'medium' : 'low';

  const severityConfig = {
    high: {
      color: 'bg-red-50 border-red-500',
      icon: '🚨',
      label: 'High Vulnerability',
      description: 'Multiple single points of failure detected. System highly vulnerable to disruption.',
    },
    medium: {
      color: 'bg-yellow-50 border-yellow-500',
      icon: '⚠️',
      label: 'Medium Vulnerability',
      description: 'Some critical resources identified. Contingency planning recommended.',
    },
    low: {
      color: 'bg-green-50 border-green-500',
      icon: '✅',
      label: 'Low Vulnerability',
      description: 'System has good redundancy. Can withstand single resource failures.',
    },
  };

  const config = severityConfig[severityLevel];

  return (
    <div className={`n1-contingency-map ${className}`}>
      {/* Status Summary */}
      <div className={`border-l-4 rounded-lg p-6 mb-6 ${config.color}`}>
        <div className="flex items-start gap-4">
          <span className="text-4xl" role="img" aria-label={config.label}>
            {config.icon}
          </span>
          <div className="flex-1">
            <h3 className="text-xl font-bold mb-2">{config.label}</h3>
            <p className="text-sm mb-4">{config.description}</p>

            <div className="grid grid-cols-3 gap-4">
              <div className="bg-white bg-opacity-50 rounded p-3">
                <div className="text-2xl font-bold text-red-600">
                  {criticalResources.length}
                </div>
                <div className="text-xs text-gray-700">Critical Resources</div>
              </div>
              <div className="bg-white bg-opacity-50 rounded p-3">
                <div className="text-2xl font-bold text-orange-600">
                  {vulnerableRotations.length}
                </div>
                <div className="text-xs text-gray-700">Vulnerable Rotations</div>
              </div>
              <div className="bg-white bg-opacity-50 rounded p-3">
                <div className="text-2xl font-bold text-blue-600">
                  {recoveryDistance}
                </div>
                <div className="text-xs text-gray-700">Recovery Distance</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Critical Resources List */}
      {criticalResources.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-4 mb-4">
          <h4 className="font-semibold mb-3 flex items-center gap-2">
            <span>🎯</span>
            <span>Critical Resources (Single Points of Failure)</span>
          </h4>
          <div className="space-y-2">
            {criticalResources.map((resource, idx) => (
              <button
                key={idx}
                onClick={() => setSelectedResource(selectedResource === resource ? null : resource)}
                className="w-full text-left p-3 bg-red-50 border border-red-200 rounded hover:bg-red-100 transition-colors focus:outline-none focus:ring-2 focus:ring-red-500"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Badge variant="destructive">SPOF</Badge>
                    <span className="font-medium">{resource}</span>
                  </div>
                  <span className="text-red-600">⚠️</span>
                </div>
                {selectedResource === resource && (
                  <div className="mt-2 pt-2 border-t border-red-300 text-sm text-gray-700">
                    <strong>Impact:</strong> Removing this resource would cause schedule failure.
                    No suitable backup available. Recommend cross-training or hiring additional staff.
                  </div>
                )}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Vulnerable Rotations */}
      {vulnerableRotations.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-4 mb-4">
          <h4 className="font-semibold mb-3 flex items-center gap-2">
            <span>📋</span>
            <span>Vulnerable Rotations</span>
          </h4>
          <div className="grid grid-cols-2 gap-2">
            {vulnerableRotations.map((rotation, idx) => (
              <div
                key={idx}
                className="p-2 bg-orange-50 border border-orange-200 rounded text-sm"
              >
                <div className="flex items-center gap-2">
                  <span className="text-orange-600">⚡</span>
                  <span className="font-medium">{rotation}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recovery Distance Explanation */}
      <div className="bg-gray-50 rounded-lg p-4 mb-4">
        <h4 className="font-semibold text-sm mb-3">Recovery Distance Analysis</h4>
        <div className="text-sm text-gray-700 space-y-2">
          <div className="flex items-start gap-2">
            <span className="font-bold">Current Distance:</span>
            <span>
              {recoveryDistance} edit{recoveryDistance !== 1 ? 's' : ''} required to recover from
              single resource failure (N-1 shock)
            </span>
          </div>
          <div className="flex items-start gap-2">
            <span className="font-bold">Interpretation:</span>
            <span>
              {recoveryDistance === 0 && 'System can auto-recover from any single failure'}
              {recoveryDistance > 0 && recoveryDistance <= 3 && 'Minor adjustments needed for recovery'}
              {recoveryDistance > 3 && recoveryDistance <= 10 && 'Moderate rescheduling required'}
              {recoveryDistance > 10 && 'Extensive rescheduling required - high vulnerability'}
            </span>
          </div>
        </div>
      </div>

      {/* Recommendations */}
      {hasCriticalVulnerabilities && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
          <h4 className="font-semibold text-sm mb-3 text-blue-900">💡 Recommended Mitigations</h4>
          <ul className="space-y-2 text-sm text-blue-800">
            <li className="flex items-start gap-2">
              <span>→</span>
              <span>Cross-train personnel to provide backup coverage</span>
            </li>
            <li className="flex items-start gap-2">
              <span>→</span>
              <span>Develop contingency schedules for critical resource absences</span>
            </li>
            <li className="flex items-start gap-2">
              <span>→</span>
              <span>Consider hiring additional staff for vulnerable rotations</span>
            </li>
            <li className="flex items-start gap-2">
              <span>→</span>
              <span>Implement rotation sharing agreements with partner programs</span>
            </li>
          </ul>
        </div>
      )}

      {/* Drill Down Button */}
      {onDrillDown && (
        <button
          onClick={onDrillDown}
          className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
        >
          View Full Contingency Analysis
        </button>
      )}

      {/* Framework Info */}
      <div className="mt-4 text-xs text-gray-600 bg-blue-50 rounded p-3">
        <strong>N-1 Contingency:</strong> Borrowed from power grid reliability engineering. Tests whether
        the system can survive the failure of any single resource (N-1 criterion). Recovery distance
        measures minimum schedule edits needed to recover from single-point failures.
      </div>
    </div>
  );
};

export default N1ContingencyMap;
