'use client';

/**
 * Energy Landscape Visualizer Component
 *
 * Displays schedule optimization landscape analysis with:
 * - Local minimum indicator (stable vs optimizable)
 * - Landscape metrics grid (energy, basin size, barriers, ruggedness)
 * - Gradient indicator (optimization potential)
 * - Interpretations and recommendations
 */

import { CheckCircle, AlertTriangle, TrendingUp, TrendingDown } from 'lucide-react';

// ============================================================================
// Types
// ============================================================================

export interface EnergyLandscapeResponse {
  currentEnergy: number;
  isLocalMinimum: boolean;
  estimatedBasinSize: number;
  meanBarrierHeight: number;
  meanGradient: number;
  landscapeRuggedness: number;
  numLocalMinima: number;
  interpretation: string;
  recommendations: string[];
  computedAt: string;
  source: string;
}

export interface EnergyLandscapeVisualizerProps {
  data: EnergyLandscapeResponse;
  className?: string;
  onOptimize?: () => void;
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Format energy value with appropriate precision
 */
function formatEnergy(value: number): string {
  return value.toFixed(2);
}

/**
 * Format basin size (typically in units)
 */
function formatBasinSize(value: number): string {
  if (value > 1000) {
    return `${(value / 1000).toFixed(1)}K`;
  }
  return value.toFixed(0);
}

/**
 * Get color classes for local minimum indicator
 */
function getLocalMinimumColor(isLocalMinimum: boolean): {
  bgColor: string;
  textColor: string;
  badgeColor: string;
} {
  if (isLocalMinimum) {
    return {
      bgColor: 'bg-green-50 border-green-200',
      textColor: 'text-green-900',
      badgeColor: 'text-green-600',
    };
  }
  return {
    bgColor: 'bg-yellow-50 border-yellow-200',
    textColor: 'text-yellow-900',
    badgeColor: 'text-yellow-600',
  };
}

/**
 * Interpret ruggedness level (0 = smooth, > 1 = highly rugged)
 */
function getRuggednessInterpretation(value: number): {
  label: string;
  description: string;
  color: string;
} {
  if (value < 0.3) {
    return {
      label: 'Smooth',
      description: 'Clear optimization direction',
      color: 'bg-green-100 text-green-800',
    };
  }
  if (value < 0.7) {
    return {
      label: 'Moderate',
      description: 'Some optimization complexity',
      color: 'bg-blue-100 text-blue-800',
    };
  }
  if (value < 1.2) {
    return {
      label: 'Rugged',
      description: 'Many local minima, complex landscape',
      color: 'bg-yellow-100 text-yellow-800',
    };
  }
  return {
    label: 'Highly Rugged',
    description: 'Multiple competing solutions',
    color: 'bg-red-100 text-red-800',
  };
}

/**
 * Get gradient interpretation
 */
function getGradientInterpretation(value: number): {
  direction: string;
  strength: string;
  color: string;
  icon: React.ReactNode;
} {
  if (value < 0.1) {
    return {
      direction: 'Very Flat',
      strength: 'No clear optimization direction',
      color: 'text-gray-600',
      icon: <div className="w-6 h-6 text-gray-600">→</div>,
    };
  }
  if (value < 0.5) {
    return {
      direction: 'Gentle Slope',
      strength: 'Weak optimization potential',
      color: 'text-yellow-600',
      icon: <TrendingDown className="w-6 h-6 text-yellow-600" />,
    };
  }
  if (value < 1.0) {
    return {
      direction: 'Steep Descent',
      strength: 'Strong optimization potential',
      color: 'text-green-600',
      icon: <TrendingDown className="w-6 h-6 text-green-600" />,
    };
  }
  return {
    direction: 'Very Steep',
    strength: 'Excellent optimization opportunity',
    color: 'text-green-700 font-bold',
    icon: <TrendingDown className="w-6 h-6 text-green-700" />,
  };
}

// ============================================================================
// Metric Card Component
// ============================================================================

interface MetricCardProps {
  label: string;
  value: string;
  unit?: string;
  description?: string;
  color?: 'green' | 'blue' | 'yellow' | 'gray';
}

function MetricCard({
  label,
  value,
  unit = '',
  description = '',
  color = 'gray',
}: MetricCardProps) {
  const colorMap = {
    green: 'bg-green-50 border-green-200',
    blue: 'bg-blue-50 border-blue-200',
    yellow: 'bg-yellow-50 border-yellow-200',
    gray: 'bg-gray-50 border-gray-200',
  };

  return (
    <div className={`p-4 rounded-lg border-2 ${colorMap[color]}`}>
      <p className="text-sm text-gray-600 mb-2">{label}</p>
      <div className="flex items-baseline gap-2">
        <span className="text-3xl font-bold text-gray-900">{value}</span>
        {unit && <span className="text-sm text-gray-600">{unit}</span>}
      </div>
      {description && <p className="text-xs text-gray-600 mt-2">{description}</p>}
    </div>
  );
}

// ============================================================================
// Local Minimum Indicator Component
// ============================================================================

function LocalMinimumIndicator({ isLocalMinimum }: { isLocalMinimum: boolean }) {
  const { bgColor, textColor, badgeColor } = getLocalMinimumColor(isLocalMinimum);

  return (
    <div className={`p-6 rounded-xl border-2 ${bgColor} text-center`}>
      <p className="text-sm text-gray-600 mb-3">Schedule Position</p>
      <div className="flex items-center justify-center gap-3 mb-4">
        {isLocalMinimum ? (
          <CheckCircle className={`w-12 h-12 ${badgeColor}`} />
        ) : (
          <AlertTriangle className={`w-12 h-12 ${badgeColor}`} />
        )}
      </div>
      <h3 className={`text-2xl font-bold ${textColor} mb-2`}>
        {isLocalMinimum ? 'Local Minimum' : 'Not at Minimum'}
      </h3>
      <p className={`text-sm ${textColor}`}>
        {isLocalMinimum
          ? 'Schedule is in a stable position with no nearby improvements.'
          : 'Further optimizations are available.'}
      </p>
    </div>
  );
}

// ============================================================================
// Gradient Indicator Component
// ============================================================================

function GradientIndicator({ gradient }: { gradient: number }) {
  const interpretation = getGradientInterpretation(gradient);

  return (
    <div className="p-6 rounded-xl bg-gray-50 border-2 border-gray-200">
      <p className="text-sm text-gray-600 mb-4">Optimization Potential</p>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          {interpretation.icon}
          <div>
            <p className={`font-bold ${interpretation.color}`}>{interpretation.direction}</p>
            <p className="text-xs text-gray-600">{interpretation.strength}</p>
          </div>
        </div>
      </div>

      {/* Gradient magnitude bar */}
      <div className="mt-4">
        <p className="text-xs text-gray-600 mb-2">Gradient Magnitude</p>
        <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
          <div
            className={`h-full transition-all ${
              gradient < 0.5
                ? 'bg-yellow-500'
                : gradient < 1.0
                  ? 'bg-green-500'
                  : 'bg-green-700'
            }`}
            style={{
              width: `${Math.min(100, (gradient / 1.5) * 100)}%`,
            }}
          />
        </div>
        <p className="text-xs text-gray-600 mt-1">{gradient.toFixed(3)}</p>
      </div>
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export const EnergyLandscapeVisualizer: React.FC<EnergyLandscapeVisualizerProps> = ({
  data,
  className = '',
  onOptimize,
}) => {
  const ruggednessInfo = getRuggednessInterpretation(data.landscapeRuggedness);

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Energy Landscape Analysis</h2>
        <p className="text-sm text-gray-600">
          Schedule optimization landscape computed at {new Date(data.computedAt).toLocaleString()}
        </p>
      </div>

      {/* Local Minimum Indicator - Full Width */}
      <LocalMinimumIndicator isLocalMinimum={data.isLocalMinimum} />

      {/* Metrics Grid - 2x2 Layout */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <MetricCard
          label="Current Energy"
          value={formatEnergy(data.currentEnergy)}
          unit="J"
          description="Lower values indicate better schedule stability"
          color="blue"
        />
        <MetricCard
          label="Basin Size"
          value={formatBasinSize(data.estimatedBasinSize)}
          unit="units"
          description="Area of similar-quality schedules around current solution"
          color="blue"
        />
        <MetricCard
          label="Barrier Height"
          value={formatEnergy(data.meanBarrierHeight)}
          unit="J"
          description="Average energy barrier to adjacent local minima"
          color="yellow"
        />
        <MetricCard
          label="Ruggedness"
          value={data.landscapeRuggedness.toFixed(2)}
          unit=""
          description={ruggednessInfo.description}
          color="yellow"
        />
      </div>

      {/* Gradient Indicator */}
      <GradientIndicator gradient={data.meanGradient} />

      {/* Landscape Characteristics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="p-4 rounded-lg bg-gray-50 border-2 border-gray-200">
          <p className="text-sm text-gray-600 mb-2">Landscape Ruggedness</p>
          <div className={`px-3 py-2 rounded-lg w-fit ${ruggednessInfo.color}`}>
            <p className="font-semibold">{ruggednessInfo.label}</p>
          </div>
        </div>
        <div className="p-4 rounded-lg bg-gray-50 border-2 border-gray-200">
          <p className="text-sm text-gray-600 mb-2">Local Minima Count</p>
          <p className="text-3xl font-bold text-gray-900">{data.numLocalMinima}</p>
          <p className="text-xs text-gray-600 mt-1">distinct optimal solutions detected</p>
        </div>
      </div>

      {/* Interpretation Section */}
      <div className="p-6 rounded-xl bg-blue-50 border-2 border-blue-200">
        <h3 className="text-lg font-semibold text-blue-900 mb-3">Landscape Interpretation</h3>
        <p className="text-sm text-blue-800 leading-relaxed">{data.interpretation}</p>
      </div>

      {/* Recommendations Section */}
      {data.recommendations && data.recommendations.length > 0 && (
        <div className="p-6 rounded-xl bg-green-50 border-2 border-green-200">
          <h3 className="text-lg font-semibold text-green-900 mb-4">Recommendations</h3>
          <ul className="space-y-3">
            {data.recommendations.map((recommendation, index) => (
              <li key={index} className="flex gap-3">
                <div className="flex-shrink-0 mt-1">
                  <div className="flex items-center justify-center h-5 w-5 rounded-full bg-green-600">
                    <span className="text-white text-xs font-bold">{index + 1}</span>
                  </div>
                </div>
                <p className="text-sm text-green-800">{recommendation}</p>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Optimize Button */}
      {onOptimize && !data.isLocalMinimum && (
        <button
          onClick={onOptimize}
          className="w-full px-6 py-3 bg-green-600 hover:bg-green-700 text-white font-semibold rounded-lg transition-colors"
        >
          Optimize Schedule
        </button>
      )}

      {/* Source Attribution */}
      <p className="text-xs text-gray-500 text-right">
        Analysis source: {data.source}
      </p>
    </div>
  );
};

export default EnergyLandscapeVisualizer;
