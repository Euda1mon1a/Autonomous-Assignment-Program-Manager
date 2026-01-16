'use client';

/**
 * UIOverlay - HUD and controls for Stigmergy Flow visualization
 *
 * Features:
 * - Title/branding
 * - Simulation parameter controls (bloom, distortion, connections)
 * - Gemini AI analysis panel
 * - Legend
 */

import React from 'react';
import { Settings, BrainCircuit, AlertTriangle, CheckCircle } from 'lucide-react';
import { SimulationConfig, GeminiAnalysisResult, ParticleType } from '../types';

interface UIOverlayProps {
  config: SimulationConfig;
  setConfig: React.Dispatch<React.SetStateAction<SimulationConfig>>;
  onAnalyze: () => void;
  analysis: GeminiAnalysisResult | null;
  isAnalyzing: boolean;
}

const LEGEND_ITEMS = [
  { type: ParticleType.CLINIC, label: 'Clinic Assignments', color: '#3b82f6' },
  { type: ParticleType.FMIT, label: 'FMIT Rotations', color: '#22c55e' },
  { type: ParticleType.CALL, label: 'Call Shifts', color: '#eab308' },
  { type: ParticleType.CONFLICT, label: 'Conflict Vortices', color: '#ef4444' },
  { type: ParticleType.UNASSIGNED, label: 'Unassigned Slots', color: '#ffffff' },
];

export const UIOverlay: React.FC<UIOverlayProps> = ({
  config,
  setConfig,
  onAnalyze,
  analysis,
  isAnalyzing,
}) => {
  return (
    <div className="absolute inset-0 pointer-events-none flex flex-col justify-between p-6">
      {/* Header Row */}
      <div className="flex justify-between items-start pointer-events-auto">
        {/* Title Panel */}
        <div className="p-4 rounded-xl border border-white/10 backdrop-blur-md bg-black/40 text-white max-w-md">
          <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-500">
            STIGMERGY FLOW
          </h1>
          <p className="text-xs text-gray-400 mt-1 uppercase tracking-widest">
            Resilience Framework Visualization
          </p>
        </div>

        {/* Controls Panel */}
        <div className="p-4 rounded-xl border border-white/10 backdrop-blur-md bg-black/40 text-white w-64">
          <div className="flex items-center gap-2 mb-4 border-b border-white/10 pb-2">
            <Settings size={16} className="text-blue-400" />
            <h3 className="font-semibold text-sm">Simulation Parameters</h3>
          </div>

          <div className="space-y-4">
            {/* Bloom Control */}
            <div>
              <label className="text-xs text-gray-400 block mb-1">
                Bioluminescence (Bloom)
              </label>
              <input
                type="range"
                min="0"
                max="3"
                step="0.1"
                value={config.bloomStrength}
                onChange={(e) =>
                  setConfig({ ...config, bloomStrength: parseFloat(e.target.value) })
                }
                className="w-full h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
              />
            </div>

            {/* Distortion Control */}
            <div>
              <label className="text-xs text-gray-400 block mb-1">
                Gravitational Lensing
              </label>
              <input
                type="range"
                min="0"
                max="2"
                step="0.1"
                value={config.distortion}
                onChange={(e) =>
                  setConfig({ ...config, distortion: parseFloat(e.target.value) })
                }
                className="w-full h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-purple-500"
              />
            </div>

            {/* Connections Toggle */}
            <div className="flex items-center justify-between">
              <label className="text-xs text-gray-400">Magnetic Fields</label>
              <button
                onClick={() =>
                  setConfig({ ...config, showConnections: !config.showConnections })
                }
                className={`w-10 h-5 rounded-full relative transition-colors ${
                  config.showConnections ? 'bg-green-500' : 'bg-gray-700'
                }`}
              >
                <div
                  className={`absolute top-1 left-1 w-3 h-3 bg-white rounded-full transition-transform ${
                    config.showConnections ? 'translate-x-5' : ''
                  }`}
                />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Footer Row */}
      <div className="flex justify-between items-end pointer-events-auto">
        {/* Legend */}
        <div className="p-4 rounded-xl border border-white/10 backdrop-blur-md bg-black/40 text-white">
          <h3 className="text-xs font-bold text-gray-400 uppercase mb-3 tracking-widest">
            Pheromone Trail Map
          </h3>
          <div className="space-y-2">
            {LEGEND_ITEMS.map((item) => (
              <div key={item.type} className="flex items-center gap-2">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{
                    backgroundColor: item.color,
                    boxShadow: `0 0 8px ${item.color}`,
                  }}
                />
                <span className="text-xs text-gray-300">{item.label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* AI Analysis Panel */}
        <div className="p-5 rounded-xl border border-white/10 backdrop-blur-md bg-black/60 text-white w-80 max-h-[50vh] overflow-y-auto">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <BrainCircuit size={18} className="text-purple-400" />
              <h3 className="font-semibold text-sm">AI Insight</h3>
            </div>
            <button
              onClick={onAnalyze}
              disabled={isAnalyzing}
              className="text-xs px-3 py-1 bg-white/10 hover:bg-white/20 rounded-md transition-colors disabled:opacity-50"
            >
              {isAnalyzing ? 'Analyzing...' : 'Analyze Flow'}
            </button>
          </div>

          {!analysis && !isAnalyzing && (
            <p className="text-xs text-gray-500 italic text-center py-4">
              Initiate analysis to detect scheduling anomalies and flow hotspots.
            </p>
          )}

          {analysis && (
            <div className="space-y-4 animate-in fade-in">
              <div className="bg-white/5 p-3 rounded-lg">
                <p className="text-xs text-gray-300 leading-relaxed">
                  {analysis.summary}
                </p>
              </div>

              {analysis.hotspots.length > 0 && (
                <div>
                  <h4 className="text-xs font-bold text-red-400 mb-2 flex items-center gap-1">
                    <AlertTriangle size={12} /> Flow Hotspots
                  </h4>
                  <ul className="space-y-1">
                    {analysis.hotspots.map((h, i) => (
                      <li
                        key={i}
                        className="text-xs text-gray-400 pl-2 border-l border-red-500/30"
                      >
                        {h}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {analysis.recommendations.length > 0 && (
                <div>
                  <h4 className="text-xs font-bold text-green-400 mb-2 flex items-center gap-1">
                    <CheckCircle size={12} /> Optimization
                  </h4>
                  <ul className="space-y-1">
                    {analysis.recommendations.map((r, i) => (
                      <li
                        key={i}
                        className="text-xs text-gray-400 pl-2 border-l border-green-500/30"
                      >
                        {r}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Controls Hint */}
      <div className="absolute bottom-6 left-1/2 -translate-x-1/2 text-gray-500 text-xs pointer-events-none">
        DRAG TO ROTATE | SCROLL TO ZOOM | SHIFT + DRAG TO PAN
      </div>
    </div>
  );
};
