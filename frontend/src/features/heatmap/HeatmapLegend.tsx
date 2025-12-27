/**
 * Heatmap Legend Component
 *
 * Displays color scale legend, activity type legend, and coverage indicators
 * for the heatmap visualization.
 */

import React from 'react';
import { Info } from 'lucide-react';
import type { ColorScale, HeatmapViewMode } from './types';
import {
  DEFAULT_COLOR_SCALES,
  ACTIVITY_TYPE_COLORS,
  COVERAGE_INDICATOR_COLORS,
} from './types';

export interface HeatmapLegendProps {
  viewMode?: HeatmapViewMode;
  colorScale?: ColorScale;
  showActivityTypes?: boolean;
  showCoverageIndicators?: boolean;
}

export function HeatmapLegend({
  viewMode = 'coverage',
  colorScale,
  showActivityTypes = true,
  showCoverageIndicators = true,
}: HeatmapLegendProps) {
  // Use provided color scale or default based on view mode
  const scale = colorScale || DEFAULT_COLOR_SCALES[viewMode];

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-4 space-y-4">
      <div className="flex items-center gap-2 text-sm font-semibold text-gray-700">
        <Info className="w-4 h-4" />
        Legend
      </div>

      {/* Color Scale */}
      <div>
        <h3 className="text-xs font-medium text-gray-600 mb-2">Intensity Scale</h3>
        <div className="space-y-2">
          {/* Color gradient bar */}
          <div
            className="h-6 rounded-md"
            style={{
              background: `linear-gradient(to right, ${scale.colors.join(', ')})`,
            }}
          />
          {/* Scale labels */}
          <div className="flex justify-between text-xs text-gray-600">
            <span>{scale.min}</span>
            {scale.labels && scale.labels.length > 0 && (
              <div className="flex-1 flex justify-around">
                {scale.labels.map((label, index) => (
                  <span key={index}>{label}</span>
                ))}
              </div>
            )}
            <span>{scale.max}</span>
          </div>
        </div>
      </div>

      {/* Activity Type Legend */}
      {showActivityTypes && (
        <div>
          <h3 className="text-xs font-medium text-gray-600 mb-2">Activity Types</h3>
          <div className="grid grid-cols-2 gap-2">
            {Object.entries(ACTIVITY_TYPE_COLORS).map(([type, color]) => (
              <div key={type} className="flex items-center gap-2">
                <div
                  className="w-4 h-4 rounded"
                  style={{ backgroundColor: color }}
                />
                <span className="text-xs text-gray-700 capitalize">
                  {type.replace('_', ' ')}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Coverage Indicators */}
      {showCoverageIndicators && (
        <div>
          <h3 className="text-xs font-medium text-gray-600 mb-2">Coverage Status</h3>
          <div className="space-y-2">
            {Object.entries(COVERAGE_INDICATOR_COLORS).map(([status, color]) => (
              <div key={status} className="flex items-center gap-2">
                <div
                  className="w-4 h-4 rounded"
                  style={{ backgroundColor: color }}
                />
                <span className="text-xs text-gray-700 capitalize">
                  {status.replace('_', ' ')}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* View mode description */}
      <div className="pt-2 border-t border-gray-200">
        <p className="text-xs text-gray-500">
          {viewMode === 'coverage' && (
            <>
              Shows rotation coverage percentage. Green = full coverage, yellow = partial,
              red = low coverage, black = critical gap requiring immediate attention.
            </>
          )}
          {viewMode === 'workload' && (
            <>
              Shows workload distribution. Blue = light, yellow = moderate, red = heavy,
              black = critical overload requiring intervention.
            </>
          )}
          {viewMode === 'custom' && (
            <>
              Custom visualization. Intensity scale: cool colors (low) → warm (high) →
              black (critical). Adjust filters to explore the schedule.
            </>
          )}
        </p>
      </div>
    </div>
  );
}

/**
 * Compact legend variant for inline display
 */
export function CompactHeatmapLegend({ viewMode = 'coverage' }: { viewMode?: HeatmapViewMode }) {
  const scale = DEFAULT_COLOR_SCALES[viewMode];

  return (
    <div className="inline-flex items-center gap-4 px-4 py-2 bg-gray-50 rounded-md">
      <span className="text-xs font-medium text-gray-600">Scale:</span>
      <div
        className="w-32 h-4 rounded"
        style={{
          background: `linear-gradient(to right, ${scale.colors.join(', ')})`,
        }}
      />
      <div className="flex items-center gap-2 text-xs text-gray-600">
        <span>{scale.min}</span>
        <span>-</span>
        <span>{scale.max}</span>
      </div>
    </div>
  );
}
