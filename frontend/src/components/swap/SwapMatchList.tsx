/**
 * SwapMatchList Component
 *
 * Displays compatible swap matches with scoring
 */

import React, { useState } from 'react';
import { Badge } from '../ui/Badge';
import { ShiftIndicator } from '../schedule/ShiftIndicator';
import { RotationBadge } from '../schedule/RotationBadge';

export interface SwapMatch {
  personId: string;
  personName: string;
  pgyLevel: string;
  blockId: string;
  date: string;
  shift: 'AM' | 'PM' | 'Night';
  rotationType: string;
  compatibilityScore: number; // 0-100
  reasons: string[];
  warnings?: string[];
}

export interface SwapMatchListProps {
  matches: SwapMatch[];
  onSelectMatch: (match: SwapMatch) => void;
  className?: string;
}

const getScoreColor = (score: number): string => {
  if (score >= 80) return 'text-green-600 bg-green-100';
  if (score >= 60) return 'text-yellow-600 bg-yellow-100';
  return 'text-orange-600 bg-orange-100';
};

const getScoreLabel = (score: number): string => {
  if (score >= 80) return 'Excellent Match';
  if (score >= 60) return 'Good Match';
  return 'Fair Match';
};

export const SwapMatchList: React.FC<SwapMatchListProps> = ({
  matches,
  onSelectMatch,
  className = '',
}) => {
  const [expandedMatchId, setExpandedMatchId] = useState<string | null>(null);

  const sortedMatches = [...matches].sort((a, b) => b.compatibilityScore - a.compatibilityScore);

  if (matches.length === 0) {
    return (
      <div className={`swap-match-list bg-white rounded-lg shadow p-6 text-center ${className}`}>
        <div className="text-4xl mb-3">🔍</div>
        <h3 className="text-lg font-semibold text-gray-700 mb-2">No Compatible Matches Found</h3>
        <p className="text-sm text-gray-600">
          Try selecting a different block or check back later
        </p>
      </div>
    );
  }

  return (
    <div className={`swap-match-list bg-white rounded-lg shadow-lg ${className}`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <h3 className="text-xl font-bold">Compatible Swap Matches</h3>
        <p className="text-sm text-gray-600 mt-1">
          Found {matches.length} potential match{matches.length !== 1 ? 'es' : ''}
        </p>
      </div>

      {/* Match List */}
      <div className="divide-y divide-gray-200">
        {sortedMatches.map((match) => {
          const isExpanded = expandedMatchId === match.blockId;
          const scoreColor = getScoreColor(match.compatibilityScore);
          const scoreLabel = getScoreLabel(match.compatibilityScore);

          return (
            <div
              key={match.blockId}
              className="p-4 hover:bg-gray-50 transition-colors"
            >
              {/* Match Header */}
              <div className="flex items-start justify-between gap-4 mb-2">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <h4 className="font-semibold text-lg">{match.personName}</h4>
                    <Badge variant="default">{match.pgyLevel}</Badge>
                  </div>

                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-sm text-gray-600">
                      {new Date(match.date).toLocaleDateString('en-US', {
                        weekday: 'short',
                        month: 'short',
                        day: 'numeric',
                      })}
                    </span>
                    <ShiftIndicator shift={match.shift} size="sm" variant="badge" />
                    <RotationBadge rotationType={match.rotationType} size="sm" />
                  </div>
                </div>

                {/* Compatibility Score */}
                <div className="text-right">
                  <div className={`inline-flex items-center justify-center w-16 h-16 rounded-full font-bold text-xl ${scoreColor}`}>
                    {match.compatibilityScore}
                  </div>
                  <div className="text-xs text-gray-600 mt-1">{scoreLabel}</div>
                </div>
              </div>

              {/* Reasons Preview */}
              <div className="mb-3">
                <div className="text-sm text-gray-700">
                  {match.reasons.slice(0, 2).map((reason, idx) => (
                    <div key={idx} className="flex items-start gap-2 mb-1">
                      <span className="text-green-600">✓</span>
                      <span>{reason}</span>
                    </div>
                  ))}
                  {match.reasons.length > 2 && !isExpanded && (
                    <button
                      onClick={() => setExpandedMatchId(match.blockId)}
                      className="text-blue-600 hover:text-blue-800 text-sm focus:outline-none focus:underline"
                    >
                      +{match.reasons.length - 2} more reasons
                    </button>
                  )}
                </div>
              </div>

              {/* Expanded Details */}
              {isExpanded && (
                <div className="mb-3 p-3 bg-gray-50 rounded border border-gray-200">
                  <div className="text-sm">
                    <div className="font-medium mb-2">All Match Reasons:</div>
                    {match.reasons.map((reason, idx) => (
                      <div key={idx} className="flex items-start gap-2 mb-1">
                        <span className="text-green-600">✓</span>
                        <span>{reason}</span>
                      </div>
                    ))}

                    {match.warnings && match.warnings.length > 0 && (
                      <>
                        <div className="font-medium mt-3 mb-2 text-orange-700">Warnings:</div>
                        {match.warnings.map((warning, idx) => (
                          <div key={idx} className="flex items-start gap-2 mb-1 text-orange-700">
                            <span>⚠️</span>
                            <span>{warning}</span>
                          </div>
                        ))}
                      </>
                    )}
                  </div>
                  <button
                    onClick={() => setExpandedMatchId(null)}
                    className="text-blue-600 hover:text-blue-800 text-sm mt-2 focus:outline-none focus:underline"
                  >
                    Show less
                  </button>
                </div>
              )}

              {/* Warnings (if any) */}
              {match.warnings && match.warnings.length > 0 && !isExpanded && (
                <div className="mb-3 p-2 bg-yellow-50 border border-yellow-200 rounded">
                  <div className="flex items-start gap-2 text-sm text-yellow-800">
                    <span>⚠️</span>
                    <span>{match.warnings[0]}</span>
                  </div>
                  {match.warnings.length > 1 && (
                    <button
                      onClick={() => setExpandedMatchId(match.blockId)}
                      className="text-yellow-700 hover:text-yellow-900 text-xs mt-1 focus:outline-none focus:underline"
                    >
                      +{match.warnings.length - 1} more warnings
                    </button>
                  )}
                </div>
              )}

              {/* Select Button */}
              <button
                onClick={() => onSelectMatch(match)}
                className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
              >
                Select This Match
              </button>
            </div>
          );
        })}
      </div>

      {/* Footer Info */}
      <div className="p-4 border-t border-gray-200 bg-gray-50 text-xs text-gray-600">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-green-100"></div>
            <span>80-100: Excellent</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-yellow-100"></div>
            <span>60-79: Good</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-orange-100"></div>
            <span>&lt;60: Fair</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SwapMatchList;
