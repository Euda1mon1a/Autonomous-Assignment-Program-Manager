/**
 * Spatial Audio Panel Component
 *
 * Controls for 3D spatial audio that represents constraint
 * violation intensity as audio density.
 */

'use client';

import React, { useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import type {
  SpatialAudioConfig,
  ViolationAudioSource,
  ViolationType,
} from './types';
import { VIOLATION_AUDIO_THEMES } from './types';

interface SpatialAudioPanelProps {
  config: SpatialAudioConfig;
  sources: ViolationAudioSource[];
  onInitAudio: () => void;
  onDisposeAudio: () => void;
  onSetVolume: (volume: number) => void;
  onAddSource?: (source: ViolationAudioSource) => void;
  onRemoveSource?: (sourceId: string) => void;
}

const VIOLATION_TYPE_LABELS: Record<ViolationType, string> = {
  acgme_hours: 'ACGME Hours',
  acgme_rest: 'ACGME Rest',
  supervision: 'Supervision',
  coverage_gap: 'Coverage Gap',
  conflict: 'Conflict',
  credential_missing: 'Credential Missing',
  workload_imbalance: 'Workload Imbalance',
};

const VIOLATION_TYPE_COLORS: Record<ViolationType, string> = {
  acgme_hours: '#ef4444',
  acgme_rest: '#f97316',
  supervision: '#eab308',
  coverage_gap: '#22c55e',
  conflict: '#3b82f6',
  credential_missing: '#8b5cf6',
  workload_imbalance: '#ec4899',
};

export function SpatialAudioPanel({
  config,
  sources,
  onInitAudio,
  onDisposeAudio,
  onSetVolume,
  onAddSource,
  onRemoveSource,
}: SpatialAudioPanelProps) {
  const [selectedType, setSelectedType] = useState<ViolationType>('acgme_hours');
  const [showWaveform, setShowWaveform] = useState(true);

  // Generate demo source
  const handleAddDemoSource = useCallback(() => {
    if (!onAddSource) return;

    const theme = VIOLATION_AUDIO_THEMES[selectedType];
    const source: ViolationAudioSource = {
      sourceId: `source-${Date.now()}`,
      violationType: selectedType,
      position: {
        x: (Math.random() - 0.5) * 10,
        y: (Math.random() - 0.5) * 10,
        z: (Math.random() - 0.5) * 5,
      },
      severity: 0.5 + Math.random() * 0.5,
      panning: (Math.random() - 0.5) * 2,
      audio: {
        frequency: theme.frequency || 440,
        waveform: theme.waveform || 'sine',
        volume: 0.3,
        attack: theme.attack || 0.1,
        decay: theme.decay || 0.2,
        sustain: theme.sustain || 0.5,
        release: theme.release || 0.3,
        modFrequency: theme.modFrequency,
        modDepth: theme.modDepth,
      },
      isActive: true,
    };

    onAddSource(source);
  }, [selectedType, onAddSource]);

  return (
    <div className="p-4 border-b border-slate-700">
      <h3 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
        <span className="text-xl">🔊</span>
        Spatial Audio
      </h3>

      {/* Enable/Disable Toggle */}
      <div className="mb-4">
        <button
          onClick={config.isEnabled ? onDisposeAudio : onInitAudio}
          className={`w-full py-2 rounded-lg text-sm font-medium transition-colors ${
            config.isEnabled
              ? 'bg-red-500/20 text-red-300 hover:bg-red-500/30 border border-red-500/30'
              : 'bg-emerald-500/20 text-emerald-300 hover:bg-emerald-500/30 border border-emerald-500/30'
          }`}
        >
          {config.isEnabled ? 'Disable Audio' : 'Enable Audio'}
        </button>
      </div>

      {config.isEnabled && (
        <>
          {/* Master Volume */}
          <div className="mb-4">
            <div className="flex justify-between text-xs text-slate-400 mb-2">
              <span>Master Volume</span>
              <span>{Math.round(config.masterVolume * 100)}%</span>
            </div>
            <input
              type="range"
              min={0}
              max={1}
              step={0.01}
              value={config.masterVolume}
              onChange={(e) => onSetVolume(Number(e.target.value))}
              className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer"
            />
          </div>

          {/* Distance Model */}
          <div className="mb-4">
            <label className="text-xs text-slate-400 block mb-2">Distance Model</label>
            <div className="grid grid-cols-3 gap-1">
              {(['linear', 'inverse', 'exponential'] as const).map(model => (
                <button
                  key={model}
                  className={`px-2 py-1 text-xs rounded ${
                    config.distanceModel === model
                      ? 'bg-violet-600 text-white'
                      : 'bg-slate-800 text-slate-400'
                  }`}
                >
                  {model.charAt(0).toUpperCase() + model.slice(1)}
                </button>
              ))}
            </div>
          </div>

          {/* Waveform Preview Toggle */}
          <div className="mb-4">
            <button
              onClick={() => setShowWaveform(!showWaveform)}
              className="text-xs text-slate-400 hover:text-white flex items-center gap-1"
            >
              <span>{showWaveform ? '▼' : '▶'}</span>
              Waveform Preview
            </button>
          </div>

          {/* Violation Type Waveforms */}
          {showWaveform && (
            <div className="mb-4 space-y-2">
              {(Object.keys(VIOLATION_AUDIO_THEMES) as ViolationType[]).map(type => {
                const theme = VIOLATION_AUDIO_THEMES[type];
                const isSelected = selectedType === type;

                return (
                  <button
                    key={type}
                    onClick={() => setSelectedType(type)}
                    className={`w-full text-left p-2 rounded-lg transition-colors ${
                      isSelected
                        ? 'bg-slate-700 border border-violet-500'
                        : 'bg-slate-800/50 hover:bg-slate-800 border border-transparent'
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <span
                        className="w-2 h-2 rounded-full"
                        style={{ backgroundColor: VIOLATION_TYPE_COLORS[type] }}
                      />
                      <span className="text-xs text-slate-300">
                        {VIOLATION_TYPE_LABELS[type]}
                      </span>
                      <span className="ml-auto text-xs text-slate-500">
                        {theme.frequency}Hz
                      </span>
                    </div>

                    {/* Waveform visualization */}
                    <svg
                      viewBox="0 0 100 30"
                      className="w-full h-6"
                    >
                      <WaveformPath
                        type={theme.waveform || 'sine'}
                        color={VIOLATION_TYPE_COLORS[type]}
                      />
                    </svg>
                  </button>
                );
              })}
            </div>
          )}

          {/* Active Sources */}
          <div className="mb-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-slate-400">
                Active Sources ({sources.length})
              </span>
              {onAddSource && (
                <button
                  onClick={handleAddDemoSource}
                  className="text-xs px-2 py-1 bg-violet-600 hover:bg-violet-500 text-white rounded"
                >
                  + Add Demo
                </button>
              )}
            </div>

            <div className="space-y-1 max-h-32 overflow-y-auto">
              {sources.length === 0 ? (
                <div className="text-xs text-slate-500 text-center py-2">
                  No active audio sources
                </div>
              ) : (
                sources.map(source => (
                  <div
                    key={source.sourceId}
                    className="flex items-center gap-2 p-2 bg-slate-800/50 rounded text-xs"
                  >
                    <motion.span
                      className="w-2 h-2 rounded-full"
                      style={{ backgroundColor: VIOLATION_TYPE_COLORS[source.violationType] }}
                      animate={{ scale: [1, 1.2, 1] }}
                      transition={{ repeat: Infinity, duration: 1 / (source.audio.frequency / 100) }}
                    />
                    <span className="flex-1 text-slate-300">
                      {VIOLATION_TYPE_LABELS[source.violationType]}
                    </span>
                    <span className="text-slate-500">
                      {(source.severity * 100).toFixed(0)}%
                    </span>
                    {onRemoveSource && (
                      <button
                        onClick={() => onRemoveSource(source.sourceId)}
                        className="text-slate-500 hover:text-red-400"
                      >
                        ×
                      </button>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>

          {/* 3D Position Map */}
          <div className="bg-slate-800/50 rounded-lg p-2">
            <div className="text-xs text-slate-500 mb-2">Spatial Distribution</div>
            <svg viewBox="-6 -6 12 12" className="w-full h-24">
              {/* Grid */}
              <circle cx="0" cy="0" r="5" fill="none" stroke="#334155" strokeWidth="0.05" />
              <circle cx="0" cy="0" r="2.5" fill="none" stroke="#334155" strokeWidth="0.05" strokeDasharray="0.2" />
              <line x1="-5" y1="0" x2="5" y2="0" stroke="#334155" strokeWidth="0.05" />
              <line x1="0" y1="-5" x2="0" y2="5" stroke="#334155" strokeWidth="0.05" />

              {/* Listener position */}
              <circle cx="0" cy="0" r="0.3" fill="#8b5cf6" />
              <path
                d="M 0 -0.5 L 0.3 0.2 L 0 0 L -0.3 0.2 Z"
                fill="#8b5cf6"
                transform="translate(0, -0.7)"
              />

              {/* Source positions */}
              {sources.map(source => (
                <motion.g key={source.sourceId}>
                  <motion.circle
                    cx={source.position.x / 2}
                    cy={-source.position.y / 2}
                    r={0.3 + source.severity * 0.3}
                    fill={VIOLATION_TYPE_COLORS[source.violationType]}
                    fillOpacity={0.6}
                    animate={{
                      r: [0.3 + source.severity * 0.3, 0.5 + source.severity * 0.3, 0.3 + source.severity * 0.3],
                    }}
                    transition={{
                      repeat: Infinity,
                      duration: 60 / source.audio.frequency,
                    }}
                  />
                  <motion.circle
                    cx={source.position.x / 2}
                    cy={-source.position.y / 2}
                    r={1}
                    fill="none"
                    stroke={VIOLATION_TYPE_COLORS[source.violationType]}
                    strokeOpacity={0.3}
                    animate={{
                      r: [0.5, 2, 0.5],
                      opacity: [0.3, 0, 0.3],
                    }}
                    transition={{
                      repeat: Infinity,
                      duration: 2,
                    }}
                  />
                </motion.g>
              ))}
            </svg>
          </div>
        </>
      )}
    </div>
  );
}

// Waveform visualization component
function WaveformPath({
  type,
  color,
}: {
  type: 'sine' | 'square' | 'triangle' | 'sawtooth' | 'noise';
  color: string;
}) {
  const points = 50;
  let d = 'M 0 15';

  for (let i = 0; i <= points; i++) {
    const x = (i / points) * 100;
    const t = (i / points) * 4 * Math.PI;
    let y: number;

    switch (type) {
      case 'square':
        y = Math.sign(Math.sin(t)) * 10 + 15;
        break;
      case 'triangle':
        y = (Math.asin(Math.sin(t)) * 2 / Math.PI) * 10 + 15;
        break;
      case 'sawtooth':
        y = ((t % (2 * Math.PI)) / Math.PI - 1) * 10 + 15;
        break;
      case 'noise':
        y = (Math.random() - 0.5) * 20 + 15;
        break;
      case 'sine':
      default:
        y = Math.sin(t) * 10 + 15;
    }

    d += ` L ${x} ${y}`;
  }

  return (
    <path
      d={d}
      fill="none"
      stroke={color}
      strokeWidth="1"
      strokeOpacity="0.8"
    />
  );
}

export default SpatialAudioPanel;
