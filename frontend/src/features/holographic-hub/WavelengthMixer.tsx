/**
 * Wavelength Mixer Component
 *
 * Enables cross-wavelength mixing with configurable blend modes
 * for composite visualization insights.
 */

'use client';

import React, { useState, useMemo, useCallback } from 'react';
import { motion } from 'framer-motion';
import type {
  WavelengthChannel,
  WavelengthMixConfig,
  MixedWavelengthData,
  MixedPoint,
} from './types';
import { WAVELENGTH_COLORS, WAVELENGTH_LABELS } from './types';

interface WavelengthMixerProps {
  primaryChannel: WavelengthChannel;
  secondaryChannel: WavelengthChannel;
  primaryData: number[];
  secondaryData: number[];
  onMixConfigChange?: (config: WavelengthMixConfig) => void;
}

export function WavelengthMixer({
  primaryChannel,
  secondaryChannel,
  primaryData,
  secondaryData,
  onMixConfigChange,
}: WavelengthMixerProps) {
  const [config, setConfig] = useState<WavelengthMixConfig>({
    primaryWeight: 0.5,
    secondaryWeight: 0.5,
    mode: 'additive',
    colorMap: {
      channel: primaryChannel,
      colors: [WAVELENGTH_COLORS[primaryChannel], WAVELENGTH_COLORS[secondaryChannel]],
      stops: [0, 1],
    },
    opacityCurve: {
      type: 'linear',
      min: 0.2,
      max: 1,
    },
  });

  // Mix the data based on current config
  const mixedData = useMemo((): MixedPoint[] => {
    const minLen = Math.min(primaryData.length, secondaryData.length);
    const points: MixedPoint[] = [];

    for (let i = 0; i < minLen; i++) {
      const primary = primaryData[i];
      const secondary = secondaryData[i];

      let mixedValue: number;
      switch (config.mode) {
        case 'multiplicative':
          mixedValue = primary * secondary;
          break;
        case 'spectral':
          // Phase-based mixing
          mixedValue = Math.sin(primary * Math.PI) * Math.cos(secondary * Math.PI);
          break;
        case 'phase':
          // Angular mixing
          mixedValue = (Math.atan2(secondary, primary) + Math.PI) / (2 * Math.PI);
          break;
        case 'additive':
        default:
          mixedValue = config.primaryWeight * primary + config.secondaryWeight * secondary;
          break;
      }

      // Normalize to 0-1
      mixedValue = Math.max(0, Math.min(1, mixedValue));

      // Interpolate color
      const color = interpolateColor(
        WAVELENGTH_COLORS[primaryChannel],
        WAVELENGTH_COLORS[secondaryChannel],
        mixedValue
      );

      // Calculate opacity from curve
      const opacity = calculateOpacity(mixedValue, config.opacityCurve);

      points.push({
        position: {
          x: (i / minLen) * 10 - 5,
          y: mixedValue * 5 - 2.5,
          z: (primary - secondary) * 2,
        },
        primaryValue: primary,
        secondaryValue: secondary,
        mixedValue,
        color,
        opacity,
        entityId: `point-${i}`,
      });
    }

    return points;
  }, [primaryData, secondaryData, config, primaryChannel, secondaryChannel]);

  const updateWeight = useCallback((channel: 'primary' | 'secondary', value: number) => {
    setConfig(prev => {
      const newConfig = {
        ...prev,
        [channel === 'primary' ? 'primaryWeight' : 'secondaryWeight']: value,
      };
      onMixConfigChange?.(newConfig);
      return newConfig;
    });
  }, [onMixConfigChange]);

  const updateMode = useCallback((mode: WavelengthMixConfig['mode']) => {
    setConfig(prev => {
      const newConfig = { ...prev, mode };
      onMixConfigChange?.(newConfig);
      return newConfig;
    });
  }, [onMixConfigChange]);

  return (
    <div className="bg-slate-900 rounded-lg p-4">
      <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
        <span className="w-3 h-3 rounded-full" style={{ backgroundColor: WAVELENGTH_COLORS[primaryChannel] }} />
        <span>+</span>
        <span className="w-3 h-3 rounded-full" style={{ backgroundColor: WAVELENGTH_COLORS[secondaryChannel] }} />
        <span className="ml-2">Wavelength Mixer</span>
      </h3>

      {/* Blend Mode Selection */}
      <div className="mb-4">
        <label className="text-xs text-slate-400 block mb-2">Blend Mode</label>
        <div className="grid grid-cols-4 gap-1">
          {(['additive', 'multiplicative', 'spectral', 'phase'] as const).map(mode => (
            <button
              key={mode}
              onClick={() => updateMode(mode)}
              className={`px-2 py-1 text-xs rounded transition-colors ${
                config.mode === mode
                  ? 'bg-violet-600 text-white'
                  : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
              }`}
            >
              {mode.charAt(0).toUpperCase() + mode.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Weight Sliders */}
      <div className="space-y-3 mb-4">
        <div>
          <div className="flex justify-between text-xs mb-1">
            <span style={{ color: WAVELENGTH_COLORS[primaryChannel] }}>
              {WAVELENGTH_LABELS[primaryChannel]}
            </span>
            <span className="text-slate-400">{(config.primaryWeight * 100).toFixed(0)}%</span>
          </div>
          <input
            type="range"
            min={0}
            max={1}
            step={0.01}
            value={config.primaryWeight}
            onChange={(e) => updateWeight('primary', Number(e.target.value))}
            className="w-full h-2 rounded-lg appearance-none cursor-pointer"
            style={{
              background: `linear-gradient(to right, ${WAVELENGTH_COLORS[primaryChannel]} ${config.primaryWeight * 100}%, #334155 ${config.primaryWeight * 100}%)`,
            }}
          />
        </div>

        <div>
          <div className="flex justify-between text-xs mb-1">
            <span style={{ color: WAVELENGTH_COLORS[secondaryChannel] }}>
              {WAVELENGTH_LABELS[secondaryChannel]}
            </span>
            <span className="text-slate-400">{(config.secondaryWeight * 100).toFixed(0)}%</span>
          </div>
          <input
            type="range"
            min={0}
            max={1}
            step={0.01}
            value={config.secondaryWeight}
            onChange={(e) => updateWeight('secondary', Number(e.target.value))}
            className="w-full h-2 rounded-lg appearance-none cursor-pointer"
            style={{
              background: `linear-gradient(to right, ${WAVELENGTH_COLORS[secondaryChannel]} ${config.secondaryWeight * 100}%, #334155 ${config.secondaryWeight * 100}%)`,
            }}
          />
        </div>
      </div>

      {/* Mixed Preview */}
      <div className="bg-slate-950 rounded-lg p-3">
        <div className="text-xs text-slate-400 mb-2">Mixed Output Preview</div>
        <svg viewBox="-6 -3 12 6" className="w-full h-32">
          {/* Grid */}
          <line x1="-5" y1="0" x2="5" y2="0" stroke="#334155" strokeWidth="0.02" />
          <line x1="0" y1="-2.5" x2="0" y2="2.5" stroke="#334155" strokeWidth="0.02" />

          {/* Mixed points */}
          {mixedData.map((point, i) => (
            <motion.circle
              key={point.entityId}
              cx={point.position.x}
              cy={-point.position.y}
              r={0.08}
              fill={point.color}
              fillOpacity={point.opacity}
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: i * 0.002 }}
            />
          ))}

          {/* Field lines (connecting consecutive points) */}
          {mixedData.length > 1 && (
            <motion.path
              d={`M ${mixedData.map(p => `${p.position.x} ${-p.position.y}`).join(' L ')}`}
              fill="none"
              stroke="url(#mixGradient)"
              strokeWidth="0.03"
              strokeOpacity={0.5}
              initial={{ pathLength: 0 }}
              animate={{ pathLength: 1 }}
              transition={{ duration: 1 }}
            />
          )}

          <defs>
            <linearGradient id="mixGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor={WAVELENGTH_COLORS[primaryChannel]} />
              <stop offset="100%" stopColor={WAVELENGTH_COLORS[secondaryChannel]} />
            </linearGradient>
          </defs>
        </svg>

        {/* Statistics */}
        <div className="grid grid-cols-3 gap-2 mt-3 text-xs">
          <div className="text-center">
            <div className="text-slate-500">Mean</div>
            <div className="text-white font-mono">
              {(mixedData.reduce((sum, p) => sum + p.mixedValue, 0) / mixedData.length).toFixed(3)}
            </div>
          </div>
          <div className="text-center">
            <div className="text-slate-500">Std Dev</div>
            <div className="text-white font-mono">
              {calculateStdDev(mixedData.map(p => p.mixedValue)).toFixed(3)}
            </div>
          </div>
          <div className="text-center">
            <div className="text-slate-500">Range</div>
            <div className="text-white font-mono">
              {(Math.max(...mixedData.map(p => p.mixedValue)) -
                Math.min(...mixedData.map(p => p.mixedValue))).toFixed(3)}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Helper functions
function interpolateColor(color1: string, color2: string, t: number): string {
  // Parse hex colors
  const r1 = parseInt(color1.slice(1, 3), 16);
  const g1 = parseInt(color1.slice(3, 5), 16);
  const b1 = parseInt(color1.slice(5, 7), 16);

  const r2 = parseInt(color2.slice(1, 3), 16);
  const g2 = parseInt(color2.slice(3, 5), 16);
  const b2 = parseInt(color2.slice(5, 7), 16);

  // Interpolate
  const r = Math.round(r1 + (r2 - r1) * t);
  const g = Math.round(g1 + (g2 - g1) * t);
  const b = Math.round(b1 + (b2 - b1) * t);

  return `rgb(${r}, ${g}, ${b})`;
}

function calculateOpacity(
  value: number,
  curve: { type: string; min: number; max: number; threshold?: number }
): number {
  const range = curve.max - curve.min;

  switch (curve.type) {
    case 'exponential':
      return curve.min + range * (value * value);
    case 'sigmoid':
      return curve.min + range / (1 + Math.exp(-10 * (value - 0.5)));
    case 'step':
      return value > (curve.threshold || 0.5) ? curve.max : curve.min;
    case 'linear':
    default:
      return curve.min + range * value;
  }
}

function calculateStdDev(values: number[]): number {
  const mean = values.reduce((sum, v) => sum + v, 0) / values.length;
  const squaredDiffs = values.map(v => (v - mean) ** 2);
  return Math.sqrt(squaredDiffs.reduce((sum, v) => sum + v, 0) / values.length);
}

export default WavelengthMixer;
