/**
 * Holographic Visualization Hub
 *
 * Far Realm Session 10: Complete multi-spectral correlation and interaction engine.
 * Combines quantum, temporal, spectral, and evolutionary wavelengths for composite insights.
 */

'use client';

import React, { useState, useCallback, useMemo, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  useHolographicHub,
  useWavelengthCorrelation,
} from './hooks';
import type {
  WavelengthChannel,
  WavelengthPair,
  HubViewMode,
  CorrelationResult,
  GuidedTour,
} from './types';
import {
  WAVELENGTH_COLORS,
  WAVELENGTH_LABELS,
  WAVELENGTH_PAIRS,
  CONSTRAINT_CATEGORY_COLORS,
  COUPLING_TYPE_COLORS,
} from './types';
import { CorrelationVisualization } from './CorrelationVisualization';
import { WavelengthMixer } from './WavelengthMixer';
import { InteractiveSelector } from './InteractiveSelector';
import { ScheduleAnimator } from './ScheduleAnimator';
import { LookingGlassRenderer } from './LookingGlassRenderer';
import { SpatialAudioPanel } from './SpatialAudioPanel';
import { ConstraintCouplingView } from './ConstraintCouplingView';
import { ExportPanel } from './ExportPanel';
import { GuidedTourPlayer } from './GuidedTourPlayer';

// ============================================================================
// Main Hub Component
// ============================================================================

interface HolographicHubProps {
  /** Initial time range for visualization */
  initialTimeRange?: { start: string; end: string };
  /** Enable Looking Glass holographic display */
  enableLookingGlass?: boolean;
  /** Callback when visualization state changes */
  onStateChange?: (state: unknown) => void;
}

export function HolographicHub({
  initialTimeRange,
  enableLookingGlass = false,
  onStateChange,
}: HolographicHubProps) {
  const hub = useHolographicHub();
  const [selectedPair, setSelectedPair] = useState<WavelengthPair>(WAVELENGTH_PAIRS[0]);
  const [showPanels, setShowPanels] = useState({
    wavelength: true,
    correlation: true,
    animation: false,
    audio: false,
    export: false,
  });

  // Get correlation for selected pair
  const correlation = useMemo(() => {
    return hub.correlations.find(
      c => c.pair.primary === selectedPair.primary && c.pair.secondary === selectedPair.secondary
    );
  }, [hub.correlations, selectedPair]);

  // Compute correlations when channels are loaded
  useEffect(() => {
    const activeChannelPairs = WAVELENGTH_PAIRS.filter(
      pair =>
        hub.selection.activeChannels.includes(pair.primary) &&
        hub.selection.activeChannels.includes(pair.secondary)
    );
    if (activeChannelPairs.length > 0) {
      hub.computeCorrelations(activeChannelPairs);
    }
  }, [hub.selection.activeChannels, hub.channelData]);

  const togglePanel = useCallback((panel: keyof typeof showPanels) => {
    setShowPanels(prev => ({ ...prev, [panel]: !prev[panel] }));
  }, []);

  return (
    <div className="relative w-full h-screen bg-slate-950 text-white overflow-hidden">
      {/* Header */}
      <HubHeader
        viewMode={hub.viewMode}
        onViewModeChange={hub.setViewMode}
        correlationStats={hub.correlationStatistics}
      />

      {/* Main Visualization Area */}
      <div className="flex h-[calc(100vh-4rem)]">
        {/* Left Sidebar - Wavelength Controls */}
        <AnimatePresence>
          {showPanels.wavelength && (
            <motion.aside
              initial={{ x: -300, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: -300, opacity: 0 }}
              className="w-72 bg-slate-900/80 backdrop-blur border-r border-slate-700 p-4 overflow-y-auto"
            >
              <WavelengthControlPanel
                activeChannels={hub.selection.activeChannels}
                onToggleChannel={hub.toggleChannel}
                channelLoading={hub.isChannelLoading}
              />

              <div className="mt-6">
                <h3 className="text-sm font-semibold text-slate-300 mb-3">Correlation Pairs</h3>
                <div className="space-y-2">
                  {WAVELENGTH_PAIRS.map(pair => (
                    <button
                      key={`${pair.primary}-${pair.secondary}`}
                      onClick={() => setSelectedPair(pair)}
                      className={`w-full text-left p-2 rounded-lg text-sm transition-colors ${
                        selectedPair.primary === pair.primary && selectedPair.secondary === pair.secondary
                          ? 'bg-violet-600/30 border border-violet-500'
                          : 'bg-slate-800/50 hover:bg-slate-800 border border-transparent'
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        <span
                          className="w-2 h-2 rounded-full"
                          style={{ backgroundColor: WAVELENGTH_COLORS[pair.primary] }}
                        />
                        <span className="text-slate-300">{pair.label}</span>
                      </div>
                      <p className="text-xs text-slate-500 mt-1">{pair.description}</p>
                    </button>
                  ))}
                </div>
              </div>
            </motion.aside>
          )}
        </AnimatePresence>

        {/* Center - Main Visualization */}
        <main className="flex-1 relative">
          {/* View Mode Content */}
          {hub.viewMode === 'explore' && (
            <ExploreView
              selection={hub.selection}
              dependencyGraph={hub.dependencyGraph}
              onSelectResident={hub.selectResident}
              onSelectConstraint={hub.selectConstraint}
              constraintCoupling={hub.constraintCoupling}
            />
          )}

          {hub.viewMode === 'correlate' && correlation && (
            <CorrelationVisualization
              result={correlation}
              primaryChannel={selectedPair.primary}
              secondaryChannel={selectedPair.secondary}
            />
          )}

          {hub.viewMode === 'animate' && (
            <ScheduleAnimator
              config={hub.animation.config}
              keyframes={hub.animation.keyframes}
              currentKeyframe={hub.animation.currentKeyframe}
              onPlay={hub.animation.play}
              onPause={hub.animation.pause}
              onSeek={hub.animation.seekTo}
            />
          )}

          {hub.viewMode === 'tour' && hub.activeTour && (
            <GuidedTourPlayer
              tour={hub.activeTour}
              player={hub.tourPlayer}
              onEnd={hub.endTour}
            />
          )}

          {/* Looking Glass Overlay */}
          {enableLookingGlass && (
            <LookingGlassRenderer
              scene={null} // Would be populated from current view
              enabled={enableLookingGlass}
            />
          )}

          {/* Floating Controls */}
          <FloatingControls
            showPanels={showPanels}
            onTogglePanel={togglePanel}
            viewMode={hub.viewMode}
          />
        </main>

        {/* Right Sidebar - Context Panels */}
        <AnimatePresence>
          {(showPanels.correlation || showPanels.animation || showPanels.audio || showPanels.export) && (
            <motion.aside
              initial={{ x: 300, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: 300, opacity: 0 }}
              className="w-80 bg-slate-900/80 backdrop-blur border-l border-slate-700 overflow-y-auto"
            >
              {showPanels.correlation && correlation && (
                <CorrelationDetailsPanel result={correlation} />
              )}

              {showPanels.animation && (
                <AnimationControlPanel
                  config={hub.animation.config}
                  onPlay={hub.animation.play}
                  onPause={hub.animation.pause}
                  onStop={hub.animation.stop}
                  onSeek={hub.animation.seekTo}
                  onSetSpeed={hub.animation.setSpeed}
                />
              )}

              {showPanels.audio && (
                <SpatialAudioPanel
                  config={hub.audio.config}
                  sources={hub.audio.activeSources}
                  onInitAudio={hub.audio.initAudio}
                  onDisposeAudio={hub.audio.disposeAudio}
                  onSetVolume={hub.audio.setVolume}
                />
              )}

              {showPanels.export && (
                <ExportPanel
                  onExport={hub.exportVisualization}
                  isExporting={hub.isExporting}
                  lastExport={hub.exportResult}
                />
              )}
            </motion.aside>
          )}
        </AnimatePresence>
      </div>

      {/* Tour Selection Modal */}
      {hub.viewMode === 'tour' && !hub.activeTour && (
        <TourSelectionModal
          tours={hub.availableTours}
          onSelectTour={hub.startTour}
          onClose={() => hub.setViewMode('explore')}
        />
      )}
    </div>
  );
}

// ============================================================================
// Sub-Components
// ============================================================================

interface HubHeaderProps {
  viewMode: HubViewMode;
  onViewModeChange: (mode: HubViewMode) => void;
  correlationStats: {
    channelsLoaded: WavelengthChannel[];
    correlationsComputed: number;
    strongestCorrelation: { pair: WavelengthPair; value: number } | null;
    totalPatterns: number;
  };
}

function HubHeader({ viewMode, onViewModeChange, correlationStats }: HubHeaderProps) {
  const viewModes: { mode: HubViewMode; label: string; icon: string }[] = [
    { mode: 'explore', label: 'Explore', icon: '🔍' },
    { mode: 'correlate', label: 'Correlate', icon: '🔗' },
    { mode: 'animate', label: 'Animate', icon: '▶️' },
    { mode: 'tour', label: 'Tour', icon: '🎬' },
    { mode: 'export', label: 'Export', icon: '📤' },
  ];

  return (
    <header className="h-16 bg-slate-900/90 backdrop-blur border-b border-slate-700 flex items-center justify-between px-6">
      <div className="flex items-center gap-4">
        <h1 className="text-xl font-bold bg-gradient-to-r from-violet-400 to-cyan-400 bg-clip-text text-transparent">
          Holographic Hub
        </h1>

        <div className="flex items-center gap-1 bg-slate-800 rounded-lg p-1">
          {viewModes.map(({ mode, label, icon }) => (
            <button
              key={mode}
              onClick={() => onViewModeChange(mode)}
              className={`px-3 py-1.5 rounded-md text-sm flex items-center gap-1.5 transition-colors ${
                viewMode === mode
                  ? 'bg-violet-600 text-white'
                  : 'text-slate-400 hover:text-white hover:bg-slate-700'
              }`}
            >
              <span>{icon}</span>
              <span>{label}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="flex items-center gap-6 text-sm">
        <div className="flex items-center gap-2">
          <span className="text-slate-500">Channels:</span>
          <div className="flex gap-1">
            {correlationStats.channelsLoaded.map(channel => (
              <span
                key={channel}
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: WAVELENGTH_COLORS[channel] }}
                title={WAVELENGTH_LABELS[channel]}
              />
            ))}
          </div>
        </div>

        <div className="text-slate-400">
          <span className="text-violet-400">{correlationStats.correlationsComputed}</span> correlations
        </div>

        <div className="text-slate-400">
          <span className="text-cyan-400">{correlationStats.totalPatterns}</span> patterns
        </div>

        {correlationStats.strongestCorrelation && (
          <div className="text-slate-400">
            Strongest: <span className="text-emerald-400">
              {correlationStats.strongestCorrelation.value.toFixed(3)}
            </span>
          </div>
        )}
      </div>
    </header>
  );
}

interface WavelengthControlPanelProps {
  activeChannels: WavelengthChannel[];
  onToggleChannel: (channel: WavelengthChannel) => void;
  channelLoading: Record<WavelengthChannel, boolean>;
}

function WavelengthControlPanel({
  activeChannels,
  onToggleChannel,
  channelLoading,
}: WavelengthControlPanelProps) {
  const channels: WavelengthChannel[] = ['quantum', 'temporal', 'spectral', 'evolutionary', 'topological', 'thermal'];

  return (
    <div>
      <h3 className="text-sm font-semibold text-slate-300 mb-3">Wavelength Channels</h3>
      <div className="space-y-2">
        {channels.map(channel => {
          const isActive = activeChannels.includes(channel);
          const isLoading = channelLoading[channel];

          return (
            <button
              key={channel}
              onClick={() => onToggleChannel(channel)}
              className={`w-full flex items-center gap-3 p-2 rounded-lg text-sm transition-all ${
                isActive
                  ? 'bg-slate-800 border border-slate-600'
                  : 'bg-slate-800/30 border border-transparent hover:bg-slate-800/60'
              }`}
            >
              <div
                className={`w-4 h-4 rounded-full transition-all ${isActive ? 'scale-110' : 'scale-75 opacity-50'}`}
                style={{ backgroundColor: WAVELENGTH_COLORS[channel] }}
              />
              <span className={isActive ? 'text-white' : 'text-slate-500'}>
                {WAVELENGTH_LABELS[channel]}
              </span>
              {isLoading && (
                <span className="ml-auto">
                  <LoadingSpinner size="sm" />
                </span>
              )}
              {isActive && !isLoading && (
                <span className="ml-auto text-xs text-emerald-400">●</span>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}

interface CorrelationDetailsPanelProps {
  result: CorrelationResult;
}

function CorrelationDetailsPanel({ result }: CorrelationDetailsPanelProps) {
  return (
    <div className="p-4 border-b border-slate-700">
      <h3 className="text-sm font-semibold text-slate-300 mb-3">
        Correlation Analysis
      </h3>

      <div className="space-y-4">
        {/* Correlation Coefficient */}
        <div>
          <div className="flex justify-between text-xs text-slate-500 mb-1">
            <span>Pearson Correlation</span>
            <span className={result.correlation > 0 ? 'text-emerald-400' : 'text-rose-400'}>
              {result.correlation.toFixed(4)}
            </span>
          </div>
          <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
            <div
              className={`h-full transition-all ${result.correlation > 0 ? 'bg-emerald-500' : 'bg-rose-500'}`}
              style={{ width: `${Math.abs(result.correlation) * 100}%` }}
            />
          </div>
        </div>

        {/* Significance */}
        <div>
          <div className="flex justify-between text-xs text-slate-500 mb-1">
            <span>Significance (p-value)</span>
            <span className={result.significance < 0.05 ? 'text-emerald-400' : 'text-amber-400'}>
              {result.significance.toFixed(4)}
            </span>
          </div>
          <div className="text-xs text-slate-400">
            {result.significance < 0.01 ? 'Highly significant' :
             result.significance < 0.05 ? 'Significant' :
             result.significance < 0.1 ? 'Marginally significant' : 'Not significant'}
          </div>
        </div>

        {/* Mutual Information */}
        <div>
          <div className="flex justify-between text-xs text-slate-500 mb-1">
            <span>Mutual Information</span>
            <span className="text-violet-400">{result.mutualInformation.toFixed(3)} bits</span>
          </div>
        </div>

        {/* Transfer Entropy */}
        <div>
          <div className="text-xs text-slate-500 mb-2">Transfer Entropy (Causality)</div>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="bg-slate-800/50 p-2 rounded">
              <div className="text-slate-400">{result.pair.primary} → {result.pair.secondary}</div>
              <div className="text-cyan-400 font-mono">{result.transferEntropy.primaryToSecondary.toFixed(4)}</div>
            </div>
            <div className="bg-slate-800/50 p-2 rounded">
              <div className="text-slate-400">{result.pair.secondary} → {result.pair.primary}</div>
              <div className="text-amber-400 font-mono">{result.transferEntropy.secondaryToPrimary.toFixed(4)}</div>
            </div>
          </div>
        </div>

        {/* Detected Patterns */}
        {result.patterns.length > 0 && (
          <div>
            <div className="text-xs text-slate-500 mb-2">Detected Patterns ({result.patterns.length})</div>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {result.patterns.map(pattern => (
                <div
                  key={pattern.patternId}
                  className="bg-slate-800/50 p-2 rounded text-xs"
                >
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`px-1.5 py-0.5 rounded text-xs ${
                      pattern.type === 'resonance' ? 'bg-violet-500/20 text-violet-300' :
                      pattern.type === 'coupling' ? 'bg-cyan-500/20 text-cyan-300' :
                      pattern.type === 'cascade' ? 'bg-amber-500/20 text-amber-300' :
                      pattern.type === 'feedback' ? 'bg-emerald-500/20 text-emerald-300' :
                      'bg-slate-500/20 text-slate-300'
                    }`}>
                      {pattern.type}
                    </span>
                    <span className="text-slate-400">
                      strength: {(pattern.strength * 100).toFixed(0)}%
                    </span>
                  </div>
                  <p className="text-slate-400">{pattern.description}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

interface AnimationControlPanelProps {
  config: {
    isPlaying: boolean;
    currentFrame: number;
    totalFrames: number;
    fps: number;
  };
  onPlay: () => void;
  onPause: () => void;
  onStop: () => void;
  onSeek: (frame: number) => void;
  onSetSpeed: (fps: number) => void;
}

function AnimationControlPanel({
  config,
  onPlay,
  onPause,
  onStop,
  onSeek,
  onSetSpeed,
}: AnimationControlPanelProps) {
  return (
    <div className="p-4 border-b border-slate-700">
      <h3 className="text-sm font-semibold text-slate-300 mb-3">
        Animation Controls
      </h3>

      <div className="space-y-4">
        {/* Playback Controls */}
        <div className="flex items-center justify-center gap-4">
          <button
            onClick={onStop}
            className="p-2 rounded-full bg-slate-800 hover:bg-slate-700"
          >
            ⏹️
          </button>
          <button
            onClick={config.isPlaying ? onPause : onPlay}
            className="p-3 rounded-full bg-violet-600 hover:bg-violet-500"
          >
            {config.isPlaying ? '⏸️' : '▶️'}
          </button>
        </div>

        {/* Timeline */}
        <div>
          <div className="flex justify-between text-xs text-slate-500 mb-1">
            <span>Frame {config.currentFrame + 1}</span>
            <span>of {config.totalFrames}</span>
          </div>
          <input
            type="range"
            min={0}
            max={config.totalFrames - 1}
            value={config.currentFrame}
            onChange={(e) => onSeek(Number(e.target.value))}
            className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer"
          />
        </div>

        {/* Speed Control */}
        <div>
          <div className="text-xs text-slate-500 mb-1">Speed: {config.fps} FPS</div>
          <input
            type="range"
            min={1}
            max={60}
            value={config.fps}
            onChange={(e) => onSetSpeed(Number(e.target.value))}
            className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer"
          />
        </div>

        {/* Progress */}
        <div className="h-1 bg-slate-800 rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-gradient-to-r from-violet-500 to-cyan-500"
            style={{ width: `${(config.currentFrame / config.totalFrames) * 100}%` }}
          />
        </div>
      </div>
    </div>
  );
}

interface FloatingControlsProps {
  showPanels: Record<string, boolean>;
  onTogglePanel: (panel: string) => void;
  viewMode: HubViewMode;
}

function FloatingControls({ showPanels, onTogglePanel, viewMode }: FloatingControlsProps) {
  const panels = [
    { key: 'wavelength', icon: '🌈', label: 'Wavelengths' },
    { key: 'correlation', icon: '🔗', label: 'Correlation' },
    { key: 'animation', icon: '⏱️', label: 'Animation' },
    { key: 'audio', icon: '🔊', label: 'Audio' },
    { key: 'export', icon: '💾', label: 'Export' },
  ];

  return (
    <div className="absolute bottom-6 left-1/2 transform -translate-x-1/2 flex items-center gap-2 bg-slate-900/90 backdrop-blur rounded-full px-4 py-2 border border-slate-700">
      {panels.map(({ key, icon, label }) => (
        <button
          key={key}
          onClick={() => onTogglePanel(key)}
          className={`p-2 rounded-full transition-colors ${
            showPanels[key]
              ? 'bg-violet-600 text-white'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
          title={label}
        >
          {icon}
        </button>
      ))}
    </div>
  );
}

interface ExploreViewProps {
  selection: {
    selectedResidents: string[];
    selectedConstraints: string[];
    highlightMode: string;
  };
  dependencyGraph: {
    nodes: Array<{ id: string; label: string; position: { x: number; y: number; z: number }; isSelected: boolean }>;
    edges: Array<{ source: string; target: string; weight: number; type: string }>;
  } | null;
  onSelectResident: (id: string, append?: boolean) => void;
  onSelectConstraint: (id: string, append?: boolean) => void;
  constraintCoupling: {
    constraints: Array<{ constraintId: string; name: string; position: { x: number; y: number; z: number } }>;
    couplings: Array<{ source: string; target: string; strength: number; type: string }>;
  } | null;
}

function ExploreView({
  selection,
  dependencyGraph,
  onSelectResident,
  onSelectConstraint,
  constraintCoupling,
}: ExploreViewProps) {
  return (
    <div className="w-full h-full flex items-center justify-center">
      {/* 3D Canvas Placeholder - Would use Three.js in production */}
      <div className="relative w-full h-full bg-gradient-to-br from-slate-900 via-violet-950/20 to-slate-900">
        {/* Grid overlay */}
        <div className="absolute inset-0 bg-[linear-gradient(rgba(139,92,246,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(139,92,246,0.03)_1px,transparent_1px)] bg-[size:50px_50px]" />

        {/* Visualization placeholder with animated nodes */}
        <svg className="w-full h-full" viewBox="-10 -10 20 20">
          {/* Draw edges */}
          {dependencyGraph?.edges.map((edge, i) => {
            const source = dependencyGraph.nodes.find(n => n.id === edge.source);
            const target = dependencyGraph.nodes.find(n => n.id === edge.target);
            if (!source || !target) return null;

            return (
              <motion.line
                key={`edge-${i}`}
                x1={source.position.x}
                y1={source.position.y}
                x2={target.position.x}
                y2={target.position.y}
                stroke={COUPLING_TYPE_COLORS[edge.type] || '#6b7280'}
                strokeWidth={edge.weight * 0.1}
                strokeOpacity={0.5}
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={{ duration: 0.5, delay: i * 0.02 }}
              />
            );
          })}

          {/* Draw nodes */}
          {dependencyGraph?.nodes.map((node, i) => (
            <motion.g
              key={node.id}
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: i * 0.03, type: 'spring' }}
            >
              <motion.circle
                cx={node.position.x}
                cy={node.position.y}
                r={node.isSelected ? 0.5 : 0.3}
                fill={node.isSelected ? '#8b5cf6' : '#3b82f6'}
                stroke={node.isSelected ? '#c4b5fd' : 'transparent'}
                strokeWidth={0.1}
                whileHover={{ scale: 1.3 }}
                onClick={() => {
                  if (node.id.startsWith('resident')) {
                    onSelectResident(node.id, true);
                  } else if (node.id.startsWith('constraint')) {
                    onSelectConstraint(node.id, true);
                  }
                }}
                className="cursor-pointer"
              />
              <text
                x={node.position.x}
                y={node.position.y + 0.8}
                textAnchor="middle"
                fontSize="0.25"
                fill="#94a3b8"
              >
                {node.label}
              </text>
            </motion.g>
          ))}
        </svg>

        {/* Info overlay */}
        <div className="absolute top-4 left-4 bg-slate-900/80 backdrop-blur rounded-lg p-3 text-xs">
          <div className="text-slate-400 mb-2">Selected:</div>
          <div className="text-violet-400">
            {selection.selectedResidents.length} residents
          </div>
          <div className="text-cyan-400">
            {selection.selectedConstraints.length} constraints
          </div>
        </div>

        {/* Legend */}
        <div className="absolute bottom-4 right-4 bg-slate-900/80 backdrop-blur rounded-lg p-3 text-xs">
          <div className="text-slate-400 mb-2">Edge Types:</div>
          {Object.entries(COUPLING_TYPE_COLORS).map(([type, color]) => (
            <div key={type} className="flex items-center gap-2">
              <span className="w-3 h-0.5 rounded" style={{ backgroundColor: color }} />
              <span className="text-slate-300 capitalize">{type}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

interface TourSelectionModalProps {
  tours: GuidedTour[];
  onSelectTour: (tour: GuidedTour) => void;
  onClose: () => void;
}

function TourSelectionModal({ tours, onSelectTour, onClose }: TourSelectionModalProps) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        className="bg-slate-900 rounded-xl border border-slate-700 p-6 max-w-lg w-full mx-4"
        onClick={e => e.stopPropagation()}
      >
        <h2 className="text-xl font-bold text-white mb-4">Select a Guided Tour</h2>
        <p className="text-slate-400 text-sm mb-6">
          Explore pre-programmed camera paths highlighting key insights in the holographic visualization.
        </p>

        <div className="space-y-3 max-h-80 overflow-y-auto">
          {tours.map(tour => (
            <button
              key={tour.tourId}
              onClick={() => onSelectTour(tour)}
              className="w-full text-left p-4 rounded-lg bg-slate-800/50 hover:bg-slate-800 border border-slate-700 hover:border-violet-500 transition-all"
            >
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-medium text-white">{tour.name}</h3>
                <span className={`px-2 py-0.5 rounded text-xs ${
                  tour.level === 'beginner' ? 'bg-emerald-500/20 text-emerald-300' :
                  tour.level === 'intermediate' ? 'bg-amber-500/20 text-amber-300' :
                  'bg-rose-500/20 text-rose-300'
                }`}>
                  {tour.level}
                </span>
              </div>
              <p className="text-sm text-slate-400 mb-2">{tour.description}</p>
              <div className="flex items-center gap-4 text-xs text-slate-500">
                <span>⏱️ {Math.floor(tour.duration / 60)}:{(tour.duration % 60).toString().padStart(2, '0')}</span>
                <span>📍 {tour.waypoints.length} waypoints</span>
              </div>
            </button>
          ))}
        </div>

        <button
          onClick={onClose}
          className="mt-6 w-full py-2 px-4 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700"
        >
          Cancel
        </button>
      </motion.div>
    </motion.div>
  );
}

function LoadingSpinner({ size = 'md' }: { size?: 'sm' | 'md' | 'lg' }) {
  const sizeClasses = {
    sm: 'w-3 h-3',
    md: 'w-5 h-5',
    lg: 'w-8 h-8',
  };

  return (
    <div className={`${sizeClasses[size]} animate-spin rounded-full border-2 border-slate-600 border-t-violet-500`} />
  );
}

export default HolographicHub;
