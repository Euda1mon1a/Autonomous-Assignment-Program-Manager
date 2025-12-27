/**
 * Correlation Visualization Component
 *
 * Renders cross-wavelength correlation results with scatter plots,
 * density contours, and correlation surfaces.
 */

'use client';

import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import type {
  CorrelationResult,
  WavelengthChannel,
  CorrelationVisualizationData,
} from './types';
import { WAVELENGTH_COLORS, WAVELENGTH_LABELS } from './types';

interface CorrelationVisualizationProps {
  result: CorrelationResult;
  primaryChannel: WavelengthChannel;
  secondaryChannel: WavelengthChannel;
  width?: number;
  height?: number;
}

export function CorrelationVisualization({
  result,
  primaryChannel,
  secondaryChannel,
  width = 800,
  height = 600,
}: CorrelationVisualizationProps) {
  const { visualizationData } = result;
  const padding = 60;
  const chartWidth = width - padding * 2;
  const chartHeight = height - padding * 2;

  // Scale functions
  const scaleX = useMemo(() => {
    return (value: number) => padding + value * chartWidth;
  }, [chartWidth]);

  const scaleY = useMemo(() => {
    return (value: number) => height - padding - value * chartHeight;
  }, [chartHeight, height]);

  // Render density contours as filled regions
  const contourPaths = useMemo(() => {
    return visualizationData.densityContours.map((contour, i) => {
      if (contour.path.length < 3) return null;

      // Simple convex hull approximation for visualization
      const sortedByAngle = [...contour.path].sort((a, b) => {
        const centerX = contour.path.reduce((sum, p) => sum + p.x, 0) / contour.path.length;
        const centerY = contour.path.reduce((sum, p) => sum + p.y, 0) / contour.path.length;
        return Math.atan2(a.y - centerY, a.x - centerX) -
               Math.atan2(b.y - centerY, b.x - centerX);
      });

      const pathD = sortedByAngle
        .map((p, idx) =>
          `${idx === 0 ? 'M' : 'L'} ${scaleX(p.x)} ${scaleY(p.y)}`
        )
        .join(' ') + ' Z';

      return (
        <motion.path
          key={`contour-${i}`}
          d={pathD}
          fill={WAVELENGTH_COLORS[primaryChannel]}
          fillOpacity={contour.level * 0.2}
          stroke={WAVELENGTH_COLORS[primaryChannel]}
          strokeOpacity={0.3}
          strokeWidth={1}
          initial={{ pathLength: 0, opacity: 0 }}
          animate={{ pathLength: 1, opacity: 1 }}
          transition={{ duration: 0.5, delay: i * 0.1 }}
        />
      );
    });
  }, [visualizationData.densityContours, scaleX, scaleY, primaryChannel]);

  // Render regression line
  const regressionLine = useMemo(() => {
    if (!visualizationData.regressionLine) return null;

    const { slope, intercept, r2 } = visualizationData.regressionLine;
    const x1 = 0;
    const x2 = 1;
    const y1 = Math.max(0, Math.min(1, intercept));
    const y2 = Math.max(0, Math.min(1, slope + intercept));

    return (
      <motion.line
        x1={scaleX(x1)}
        y1={scaleY(y1)}
        x2={scaleX(x2)}
        y2={scaleY(y2)}
        stroke={result.correlation > 0 ? '#22c55e' : '#ef4444'}
        strokeWidth={2}
        strokeDasharray="8 4"
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: 0.8 }}
      />
    );
  }, [visualizationData.regressionLine, scaleX, scaleY, result.correlation]);

  return (
    <div className="w-full h-full flex flex-col bg-slate-950">
      {/* Header */}
      <div className="p-4 border-b border-slate-800">
        <h2 className="text-lg font-semibold text-white flex items-center gap-3">
          <span
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: WAVELENGTH_COLORS[primaryChannel] }}
          />
          <span>{WAVELENGTH_LABELS[primaryChannel]}</span>
          <span className="text-slate-500">×</span>
          <span
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: WAVELENGTH_COLORS[secondaryChannel] }}
          />
          <span>{WAVELENGTH_LABELS[secondaryChannel]}</span>
        </h2>
        <p className="text-sm text-slate-400 mt-1">{result.pair.description}</p>
      </div>

      {/* Visualization */}
      <div className="flex-1 p-4">
        <svg
          width="100%"
          height="100%"
          viewBox={`0 0 ${width} ${height}`}
          className="max-w-full max-h-full mx-auto"
        >
          {/* Background grid */}
          <defs>
            <pattern
              id="grid"
              width={chartWidth / 10}
              height={chartHeight / 10}
              patternUnits="userSpaceOnUse"
              x={padding}
              y={padding}
            >
              <path
                d={`M ${chartWidth / 10} 0 L 0 0 0 ${chartHeight / 10}`}
                fill="none"
                stroke="rgba(139, 92, 246, 0.1)"
                strokeWidth="1"
              />
            </pattern>
          </defs>
          <rect
            x={padding}
            y={padding}
            width={chartWidth}
            height={chartHeight}
            fill="url(#grid)"
            stroke="rgba(139, 92, 246, 0.2)"
          />

          {/* Density contours */}
          <g>{contourPaths}</g>

          {/* Scatter points */}
          <g>
            {visualizationData.scatterPoints.map((point, i) => (
              <motion.circle
                key={point.entityId}
                cx={scaleX(point.x)}
                cy={scaleY(point.y)}
                r={4}
                fill={WAVELENGTH_COLORS[primaryChannel]}
                fillOpacity={0.6}
                stroke={WAVELENGTH_COLORS[secondaryChannel]}
                strokeWidth={1}
                initial={{ scale: 0, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ delay: i * 0.01 }}
                whileHover={{ scale: 1.5 }}
              />
            ))}
          </g>

          {/* Regression line */}
          {regressionLine}

          {/* Axes */}
          <g className="text-slate-400" fontSize="12">
            {/* X axis */}
            <line
              x1={padding}
              y1={height - padding}
              x2={width - padding}
              y2={height - padding}
              stroke="currentColor"
            />
            <text
              x={width / 2}
              y={height - 10}
              textAnchor="middle"
              fill="currentColor"
            >
              {WAVELENGTH_LABELS[primaryChannel]}
            </text>

            {/* Y axis */}
            <line
              x1={padding}
              y1={padding}
              x2={padding}
              y2={height - padding}
              stroke="currentColor"
            />
            <text
              x={15}
              y={height / 2}
              textAnchor="middle"
              fill="currentColor"
              transform={`rotate(-90, 15, ${height / 2})`}
            >
              {WAVELENGTH_LABELS[secondaryChannel]}
            </text>

            {/* Tick marks */}
            {[0, 0.25, 0.5, 0.75, 1].map(tick => (
              <g key={`tick-${tick}`}>
                {/* X ticks */}
                <line
                  x1={scaleX(tick)}
                  y1={height - padding}
                  x2={scaleX(tick)}
                  y2={height - padding + 5}
                  stroke="currentColor"
                />
                <text
                  x={scaleX(tick)}
                  y={height - padding + 18}
                  textAnchor="middle"
                  fontSize="10"
                  fill="currentColor"
                >
                  {tick.toFixed(2)}
                </text>

                {/* Y ticks */}
                <line
                  x1={padding - 5}
                  y1={scaleY(tick)}
                  x2={padding}
                  y2={scaleY(tick)}
                  stroke="currentColor"
                />
                <text
                  x={padding - 10}
                  y={scaleY(tick) + 4}
                  textAnchor="end"
                  fontSize="10"
                  fill="currentColor"
                >
                  {tick.toFixed(2)}
                </text>
              </g>
            ))}
          </g>

          {/* Correlation badge */}
          <g transform={`translate(${width - padding - 100}, ${padding + 20})`}>
            <rect
              x={0}
              y={0}
              width={90}
              height={60}
              rx={8}
              fill="rgba(15, 23, 42, 0.9)"
              stroke="rgba(139, 92, 246, 0.3)"
            />
            <text x={10} y={20} fontSize="10" fill="#94a3b8">
              Correlation
            </text>
            <text
              x={10}
              y={40}
              fontSize="18"
              fontWeight="bold"
              fill={result.correlation > 0 ? '#22c55e' : '#ef4444'}
            >
              {result.correlation.toFixed(3)}
            </text>
            <text x={10} y={54} fontSize="9" fill="#64748b">
              R² = {(result.correlation ** 2).toFixed(3)}
            </text>
          </g>
        </svg>
      </div>

      {/* Pattern Summary */}
      {result.patterns.length > 0 && (
        <div className="p-4 border-t border-slate-800">
          <h3 className="text-sm font-medium text-slate-300 mb-2">
            Detected Patterns
          </h3>
          <div className="flex flex-wrap gap-2">
            {result.patterns.slice(0, 5).map(pattern => (
              <span
                key={pattern.patternId}
                className={`px-2 py-1 rounded text-xs ${
                  pattern.type === 'resonance'
                    ? 'bg-violet-500/20 text-violet-300'
                    : pattern.type === 'coupling'
                    ? 'bg-cyan-500/20 text-cyan-300'
                    : pattern.type === 'synchronization'
                    ? 'bg-emerald-500/20 text-emerald-300'
                    : 'bg-slate-500/20 text-slate-300'
                }`}
              >
                {pattern.type}: {(pattern.strength * 100).toFixed(0)}%
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default CorrelationVisualization;
