/**
 * DefenseLevel Component
 *
 * Visual indicator for 5-tier defense in depth level (GREEN → YELLOW → ORANGE → RED → BLACK)
 *
 * The backend returns defense levels using nuclear safety terminology:
 * - PREVENTION, CONTROL, SAFETY_SYSTEMS, CONTAINMENT, EMERGENCY
 *
 * This component maps those to color-coded levels for visual display.
 */

import React from 'react';

export type DefenseLevelType = 'GREEN' | 'YELLOW' | 'ORANGE' | 'RED' | 'BLACK';

/**
 * Backend defense level values (nuclear safety paradigm).
 * These come from the resilience API's DefenseLevel enum.
 */
export type BackendDefenseLevel =
  | 'PREVENTION'
  | 'CONTROL'
  | 'SAFETY_SYSTEMS'
  | 'CONTAINMENT'
  | 'EMERGENCY';

/**
 * Maps backend defense level to frontend color-coded level.
 *
 * Backend (Nuclear Safety)  →  Frontend (Color)
 * ─────────────────────────────────────────────
 * PREVENTION                →  GREEN   (Normal operations)
 * CONTROL                   →  YELLOW  (Minor degradation)
 * SAFETY_SYSTEMS            →  ORANGE  (Active mitigation)
 * CONTAINMENT               →  RED     (Crisis containment)
 * EMERGENCY                 →  BLACK   (Full emergency)
 */
export const mapBackendDefenseLevel = (
  backendLevel: BackendDefenseLevel | string | undefined
): DefenseLevelType => {
  const mapping: Record<BackendDefenseLevel, DefenseLevelType> = {
    PREVENTION: 'GREEN',
    CONTROL: 'YELLOW',
    SAFETY_SYSTEMS: 'ORANGE',
    CONTAINMENT: 'RED',
    EMERGENCY: 'BLACK',
  };

  if (!backendLevel) return 'GREEN';
  return mapping[backendLevel as BackendDefenseLevel] || 'GREEN';
};

export interface DefenseLevelProps {
  level: DefenseLevelType;
  onDrillDown?: () => void;
  className?: string;
}

const levelConfig: Record<DefenseLevelType, {
  color: string;
  bgColor: string;
  icon: string;
  label: string;
  description: string;
  actions: string[];
}> = {
  GREEN: {
    color: 'text-green-900',
    bgColor: 'bg-green-500',
    icon: '✅',
    label: 'GREEN - Normal Operations',
    description: 'All systems nominal. Standard operating procedures in effect.',
    actions: [
      'Continue routine monitoring',
      'Maintain standard staffing levels',
      'No special actions required',
    ],
  },
  YELLOW: {
    color: 'text-yellow-900',
    bgColor: 'bg-yellow-500',
    icon: '⚡',
    label: 'YELLOW - Elevated Watch',
    description: 'Early warning indicators detected. Increased monitoring recommended.',
    actions: [
      'Increase monitoring frequency',
      'Review upcoming schedules for potential issues',
      'Prepare contingency resources',
    ],
  },
  ORANGE: {
    color: 'text-orange-900',
    bgColor: 'bg-orange-500',
    icon: '⚠️',
    label: 'ORANGE - Caution',
    description: 'Multiple warning indicators active. Proactive intervention required.',
    actions: [
      'Activate contingency plans',
      'Redistribute workload if possible',
      'Consider activating backup personnel',
    ],
  },
  RED: {
    color: 'text-red-900',
    bgColor: 'bg-red-500',
    icon: '🚨',
    label: 'RED - Critical',
    description: 'System stress approaching critical levels. Immediate action required.',
    actions: [
      'Implement emergency staffing protocols',
      'Activate all backup resources',
      'Consider reducing non-essential operations',
    ],
  },
  BLACK: {
    color: 'text-gray-900',
    bgColor: 'bg-gray-900',
    icon: '🆘',
    label: 'BLACK - Emergency',
    description: 'System failure imminent or occurring. Crisis management mode.',
    actions: [
      'Activate emergency response protocols',
      'Deploy all available resources',
      'Escalate to command staff immediately',
    ],
  },
};

const allLevels: DefenseLevelType[] = ['GREEN', 'YELLOW', 'ORANGE', 'RED', 'BLACK'];

export const DefenseLevel: React.FC<DefenseLevelProps> = ({
  level,
  onDrillDown,
  className = '',
}) => {
  // Default to GREEN if level is undefined or invalid
  const safeLevel: DefenseLevelType = level && levelConfig[level] ? level : 'GREEN';
  const config = levelConfig[safeLevel];
  const currentIndex = allLevels.indexOf(safeLevel);

  return (
    <div className={`defense-level ${className}`}>
      {/* Level Indicator Bar */}
      <div
        className="mb-6"
        role="status"
        aria-live="polite"
        aria-label="Defense level indicator"
      >
        <div className="flex gap-2">
          {allLevels.map((levelName, idx) => {
            const isActive = idx <= currentIndex;
            const levelCfg = levelConfig[levelName];

            return (
              <div
                key={levelName}
                className="flex-1"
                title={levelCfg.label}
              >
                <div
                  className={`
                    h-12 rounded-lg transition-all
                    ${isActive ? levelCfg.bgColor : 'bg-gray-200'}
                    ${isActive ? 'ring-2 ring-offset-2 ring-gray-300' : ''}
                  `}
                  role="img"
                  aria-label={`${levelName} defense level${isActive ? ' - active' : ''}`}
                />
                <div className="text-xs text-center mt-1 font-medium text-gray-700">
                  {levelName}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Current Level Details */}
      <div className={`border-l-4 rounded-lg p-6 bg-gray-50 ${config.bgColor.replace('bg-', 'border-')}`}>
        <div className="flex items-start gap-4">
          <span className="text-4xl" aria-hidden="true">
            {config.icon}
          </span>
          <div className="flex-1">
            <h3 className={`text-2xl font-bold mb-2 ${config.color}`}>
              {config.label}
            </h3>
            <p className="text-sm text-gray-700 mb-4">{config.description}</p>

            {/* Recommended Actions */}
            <div className="bg-white rounded-lg p-4 shadow-sm">
              <h4 className="font-semibold text-sm mb-2">Recommended Actions:</h4>
              <ul className="space-y-2">
                {config.actions.map((action, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-sm">
                    <span className="text-blue-600 font-bold" aria-hidden="true">→</span>
                    <span>{action}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* Drill Down Button */}
      {onDrillDown && (
        <div className="mt-4 text-center">
          <button
            onClick={onDrillDown}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
            aria-label="View detailed defense level analysis"
          >
            View Detailed Analysis
          </button>
        </div>
      )}

      {/* Framework Info */}
      <div className="mt-4 text-xs text-gray-600 bg-blue-50 rounded p-3">
        <strong>Defense in Depth:</strong> 5-tier safety system inspired by industrial safety practices.
        Each level represents increasing system stress requiring escalated response protocols.
      </div>
    </div>
  );
};

export default DefenseLevel;
