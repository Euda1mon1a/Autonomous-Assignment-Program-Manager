/**
 * UtilizationGauge Component
 *
 * 80% utilization threshold gauge based on queuing theory
 */

import React from 'react';

export interface UtilizationGaugeProps {
  current: number; // 0-100
  threshold?: number; // Default 80
  trend?: 'increasing' | 'stable' | 'decreasing';
  onDrillDown?: () => void;
  className?: string;
}

export const UtilizationGauge: React.FC<UtilizationGaugeProps> = ({
  current,
  threshold = 80,
  trend = 'stable',
  onDrillDown,
  className = '',
}) => {
  const isAboveThreshold = current >= threshold;
  const isWarning = current >= threshold * 0.9;

  // Color function for potential future use
  const _getColor = () => {
    if (isAboveThreshold) return 'bg-red-500';
    if (isWarning) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const getTextColor = () => {
    if (isAboveThreshold) return 'text-red-700';
    if (isWarning) return 'text-yellow-700';
    return 'text-green-700';
  };

  const trendIcons = {
    increasing: '📈',
    stable: '➡️',
    decreasing: '📉',
  };

  const trendLabels = {
    increasing: 'Increasing',
    stable: 'Stable',
    decreasing: 'Decreasing',
  };

  // Calculate risk of cascade failure based on queuing theory
  const calculateCascadeRisk = (util: number): string => {
    if (util < 60) return 'Very Low';
    if (util < 70) return 'Low';
    if (util < 80) return 'Moderate';
    if (util < 90) return 'High';
    return 'Critical';
  };

  const cascadeRisk = calculateCascadeRisk(current);

  return (
    <div className={`utilization-gauge ${className}`}>
      {/* Main Gauge */}
      <div className="relative mb-6">
        {/* Circular Gauge */}
        <div className="relative w-48 h-48 mx-auto">
          <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
            {/* Background Circle */}
            <circle
              cx="50"
              cy="50"
              r="40"
              fill="none"
              stroke="#e5e7eb"
              strokeWidth="10"
            />

            {/* Progress Circle */}
            <circle
              cx="50"
              cy="50"
              r="40"
              fill="none"
              stroke={isAboveThreshold ? '#ef4444' : isWarning ? '#eab308' : '#22c55e'}
              strokeWidth="10"
              strokeDasharray={`${(current / 100) * 251.2} 251.2`}
              strokeLinecap="round"
            />

            {/* Threshold Marker */}
            <line
              x1="50"
              y1="10"
              x2="50"
              y2="5"
              stroke="#6b7280"
              strokeWidth="2"
              transform={`rotate(${(threshold / 100) * 360} 50 50)`}
            />
          </svg>

          {/* Center Text */}
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <div className={`text-4xl font-bold ${getTextColor()}`}>
              {current.toFixed(1)}%
            </div>
            <div className="text-xs text-gray-600 mt-1">
              of {threshold}% threshold
            </div>
          </div>
        </div>
      </div>

      {/* Status Info */}
      <div className={`border-l-4 rounded-lg p-4 mb-4 ${isAboveThreshold ? 'bg-red-50 border-red-500' : isWarning ? 'bg-yellow-50 border-yellow-500' : 'bg-green-50 border-green-500'}`}>
        <div className="flex items-center justify-between mb-2">
          <div className="font-semibold">
            {isAboveThreshold ? '🚨 Above Threshold' : isWarning ? '⚠️ Approaching Threshold' : '✅ Within Safe Limits'}
          </div>
          <div className="flex items-center gap-2 text-sm">
            <span>{trendIcons[trend]}</span>
            <span className="font-medium">{trendLabels[trend]}</span>
          </div>
        </div>

        <div className="text-sm text-gray-700">
          {isAboveThreshold
            ? 'System utilization exceeds safe operating threshold. Cascade failure risk is elevated.'
            : isWarning
            ? 'System approaching utilization threshold. Monitor closely for degradation.'
            : 'System operating within safe utilization limits. Normal operations.'}
        </div>
      </div>

      {/* Cascade Risk Assessment */}
      <div className="bg-gray-50 rounded-lg p-4 mb-4">
        <h4 className="font-semibold text-sm mb-3">Cascade Failure Risk Analysis</h4>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <div className="text-gray-600">Current Risk:</div>
            <div className={`font-bold text-lg ${
              cascadeRisk === 'Critical' || cascadeRisk === 'High' ? 'text-red-600' :
              cascadeRisk === 'Moderate' ? 'text-yellow-600' : 'text-green-600'
            }`}>
              {cascadeRisk}
            </div>
          </div>
          <div>
            <div className="text-gray-600">Safety Margin:</div>
            <div className="font-bold text-lg">
              {Math.max(0, threshold - current).toFixed(1)}%
            </div>
          </div>
        </div>
      </div>

      {/* Drill Down Button */}
      {onDrillDown && (
        <button
          onClick={onDrillDown}
          className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
        >
          View Detailed Utilization Breakdown
        </button>
      )}

      {/* Framework Info */}
      <div className="mt-4 text-xs text-gray-600 bg-blue-50 rounded p-3">
        <strong>80% Utilization Threshold:</strong> Based on queuing theory (M/M/c model), systems
        operating above 80% utilization experience exponential increases in wait times and risk of
        cascade failures. Derived from telecommunications and power grid best practices.
      </div>
    </div>
  );
};

export default UtilizationGauge;
