/**
 * Export Panel Component
 *
 * Provides export functionality for saving visualization states
 * to various formats for presentations and sharing.
 */

'use client';

import React, { useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import type {
  ExportConfig,
  ExportFormat,
  ExportInclusions,
  ExportQuality,
  ExportedVisualizationState,
  WavelengthChannel,
} from './types';
import { WAVELENGTH_LABELS } from './types';

interface ExportPanelProps {
  onExport: (params: {
    config: ExportConfig;
    scene: unknown;
    selection: unknown;
    correlations: unknown[];
  }) => void;
  isExporting: boolean;
  lastExport?: ExportedVisualizationState | null;
}

const FORMAT_OPTIONS: Array<{ value: ExportFormat; label: string; icon: string; description: string }> = [
  { value: 'png', label: 'PNG Image', icon: '🖼️', description: 'High-quality static image' },
  { value: 'svg', label: 'SVG Vector', icon: '📐', description: 'Scalable vector graphics' },
  { value: 'webm', label: 'WebM Video', icon: '🎬', description: 'Animated video capture' },
  { value: 'gif', label: 'Animated GIF', icon: '🎞️', description: 'Looping animation' },
  { value: 'gltf', label: 'glTF 3D', icon: '🎨', description: '3D model for AR/VR' },
  { value: 'usdz', label: 'USDZ AR', icon: '📱', description: 'Apple AR Quick Look' },
  { value: 'json', label: 'JSON Data', icon: '📄', description: 'Raw visualization data' },
  { value: 'csv', label: 'CSV Spreadsheet', icon: '📊', description: 'Tabular data export' },
];

const QUALITY_PRESETS = {
  draft: { resolution: { width: 800, height: 600 }, fps: 15, compression: 0.7, antiAliasing: 1, shadows: false, reflections: false },
  standard: { resolution: { width: 1920, height: 1080 }, fps: 30, compression: 0.5, antiAliasing: 4, shadows: true, reflections: false },
  high: { resolution: { width: 3840, height: 2160 }, fps: 60, compression: 0.2, antiAliasing: 8, shadows: true, reflections: true },
} as const;

export function ExportPanel({
  onExport,
  isExporting,
  lastExport,
}: ExportPanelProps) {
  const [config, setConfig] = useState<ExportConfig>({
    format: 'png',
    include: {
      currentView: true,
      animation: false,
      cameraPath: false,
      selectionState: true,
      wavelengthData: ['temporal', 'spectral'],
      correlations: true,
      audioMarkers: false,
    },
    quality: QUALITY_PRESETS.standard,
    metadata: {
      title: 'Holographic Visualization Export',
      description: '',
      author: '',
      timestamp: new Date().toISOString(),
      version: '1.0',
      tags: [],
      customFields: {},
    },
  });

  const [activeTab, setActiveTab] = useState<'format' | 'include' | 'quality' | 'metadata'>('format');
  const [tagInput, setTagInput] = useState('');

  const updateInclude = useCallback((key: keyof ExportInclusions, value: unknown) => {
    setConfig(prev => ({
      ...prev,
      include: { ...prev.include, [key]: value },
    }));
  }, []);

  const updateMetadata = useCallback((key: string, value: string) => {
    setConfig(prev => ({
      ...prev,
      metadata: { ...prev.metadata, [key]: value },
    }));
  }, []);

  const toggleWavelength = useCallback((channel: WavelengthChannel) => {
    setConfig(prev => ({
      ...prev,
      include: {
        ...prev.include,
        wavelengthData: prev.include.wavelengthData.includes(channel)
          ? prev.include.wavelengthData.filter(c => c !== channel)
          : [...prev.include.wavelengthData, channel],
      },
    }));
  }, []);

  const addTag = useCallback(() => {
    if (tagInput.trim() && !config.metadata.tags.includes(tagInput.trim())) {
      setConfig(prev => ({
        ...prev,
        metadata: {
          ...prev.metadata,
          tags: [...prev.metadata.tags, tagInput.trim()],
        },
      }));
      setTagInput('');
    }
  }, [tagInput, config.metadata.tags]);

  const removeTag = useCallback((tag: string) => {
    setConfig(prev => ({
      ...prev,
      metadata: {
        ...prev.metadata,
        tags: prev.metadata.tags.filter(t => t !== tag),
      },
    }));
  }, []);

  const handleExport = useCallback(() => {
    onExport({
      config,
      scene: null, // Would be populated from current scene
      selection: null, // Would be populated from selection state
      correlations: [], // Would be populated from correlation results
    });
  }, [config, onExport]);

  return (
    <div className="p-4 border-b border-slate-700">
      <h3 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
        <span className="text-xl">💾</span>
        Export Visualization
      </h3>

      {/* Tab Navigation */}
      <div className="flex gap-1 mb-4 bg-slate-800 rounded-lg p-1">
        {(['format', 'include', 'quality', 'metadata'] as const).map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`flex-1 px-2 py-1.5 rounded text-xs transition-colors ${
              activeTab === tab
                ? 'bg-violet-600 text-white'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      {/* Format Tab */}
      {activeTab === 'format' && (
        <div className="space-y-2">
          {FORMAT_OPTIONS.map(option => (
            <button
              key={option.value}
              onClick={() => setConfig(prev => ({ ...prev, format: option.value }))}
              className={`w-full text-left p-2 rounded-lg transition-colors flex items-center gap-3 ${
                config.format === option.value
                  ? 'bg-violet-600/20 border border-violet-500'
                  : 'bg-slate-800/50 hover:bg-slate-800 border border-transparent'
              }`}
            >
              <span className="text-lg">{option.icon}</span>
              <div className="flex-1">
                <div className="text-sm text-white">{option.label}</div>
                <div className="text-xs text-slate-400">{option.description}</div>
              </div>
              {config.format === option.value && (
                <span className="text-violet-400">✓</span>
              )}
            </button>
          ))}
        </div>
      )}

      {/* Include Tab */}
      {activeTab === 'include' && (
        <div className="space-y-3">
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={config.include.currentView}
              onChange={(e) => updateInclude('currentView', e.target.checked)}
              className="w-4 h-4 rounded bg-slate-700 border-slate-600"
            />
            <span className="text-slate-300">Current View Snapshot</span>
          </label>

          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={config.include.animation}
              onChange={(e) => updateInclude('animation', e.target.checked)}
              className="w-4 h-4 rounded bg-slate-700 border-slate-600"
            />
            <span className="text-slate-300">Animation Sequence</span>
          </label>

          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={config.include.cameraPath}
              onChange={(e) => updateInclude('cameraPath', e.target.checked)}
              className="w-4 h-4 rounded bg-slate-700 border-slate-600"
            />
            <span className="text-slate-300">Camera Path</span>
          </label>

          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={config.include.selectionState}
              onChange={(e) => updateInclude('selectionState', e.target.checked)}
              className="w-4 h-4 rounded bg-slate-700 border-slate-600"
            />
            <span className="text-slate-300">Selection State</span>
          </label>

          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={config.include.correlations}
              onChange={(e) => updateInclude('correlations', e.target.checked)}
              className="w-4 h-4 rounded bg-slate-700 border-slate-600"
            />
            <span className="text-slate-300">Correlation Results</span>
          </label>

          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={config.include.audioMarkers}
              onChange={(e) => updateInclude('audioMarkers', e.target.checked)}
              className="w-4 h-4 rounded bg-slate-700 border-slate-600"
            />
            <span className="text-slate-300">Audio Markers</span>
          </label>

          <div className="pt-2 border-t border-slate-700">
            <div className="text-xs text-slate-400 mb-2">Wavelength Channels</div>
            <div className="flex flex-wrap gap-1">
              {(['quantum', 'temporal', 'spectral', 'evolutionary', 'topological', 'thermal'] as WavelengthChannel[]).map(channel => (
                <button
                  key={channel}
                  onClick={() => toggleWavelength(channel)}
                  className={`px-2 py-1 rounded text-xs ${
                    config.include.wavelengthData.includes(channel)
                      ? 'bg-violet-600 text-white'
                      : 'bg-slate-800 text-slate-400'
                  }`}
                >
                  {WAVELENGTH_LABELS[channel]}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Quality Tab */}
      {activeTab === 'quality' && (
        <div className="space-y-4">
          <div>
            <div className="text-xs text-slate-400 mb-2">Preset</div>
            <div className="grid grid-cols-3 gap-1">
              {(['draft', 'standard', 'high'] as const).map(preset => (
                <button
                  key={preset}
                  onClick={() => setConfig(prev => ({
                    ...prev,
                    quality: QUALITY_PRESETS[preset],
                  }))}
                  className={`px-2 py-1.5 rounded text-xs capitalize ${
                    JSON.stringify(config.quality) === JSON.stringify(QUALITY_PRESETS[preset])
                      ? 'bg-violet-600 text-white'
                      : 'bg-slate-800 text-slate-400'
                  }`}
                >
                  {preset}
                </button>
              ))}
            </div>
          </div>

          <div>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-slate-400">Resolution</span>
              <span className="text-white">{config.quality.resolution.width}×{config.quality.resolution.height}</span>
            </div>
          </div>

          <div>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-slate-400">FPS</span>
              <span className="text-white">{config.quality.fps}</span>
            </div>
            <input
              type="range"
              min={1}
              max={60}
              value={config.quality.fps}
              onChange={(e) => setConfig(prev => ({
                ...prev,
                quality: { ...prev.quality, fps: Number(e.target.value) },
              }))}
              className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer"
            />
          </div>

          <div>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-slate-400">Anti-Aliasing</span>
              <span className="text-white">{config.quality.antiAliasing}x</span>
            </div>
            <div className="grid grid-cols-4 gap-1">
              {([1, 2, 4, 8] as const).map(aa => (
                <button
                  key={aa}
                  onClick={() => setConfig(prev => ({
                    ...prev,
                    quality: { ...prev.quality, antiAliasing: aa },
                  }))}
                  className={`px-2 py-1 rounded text-xs ${
                    config.quality.antiAliasing === aa
                      ? 'bg-violet-600 text-white'
                      : 'bg-slate-800 text-slate-400'
                  }`}
                >
                  {aa}x
                </button>
              ))}
            </div>
          </div>

          <div className="flex gap-4">
            <label className="flex items-center gap-2 text-xs">
              <input
                type="checkbox"
                checked={config.quality.shadows}
                onChange={(e) => setConfig(prev => ({
                  ...prev,
                  quality: { ...prev.quality, shadows: e.target.checked },
                }))}
                className="w-3 h-3 rounded bg-slate-700 border-slate-600"
              />
              <span className="text-slate-300">Shadows</span>
            </label>

            <label className="flex items-center gap-2 text-xs">
              <input
                type="checkbox"
                checked={config.quality.reflections}
                onChange={(e) => setConfig(prev => ({
                  ...prev,
                  quality: { ...prev.quality, reflections: e.target.checked },
                }))}
                className="w-3 h-3 rounded bg-slate-700 border-slate-600"
              />
              <span className="text-slate-300">Reflections</span>
            </label>
          </div>
        </div>
      )}

      {/* Metadata Tab */}
      {activeTab === 'metadata' && (
        <div className="space-y-3">
          <div>
            <label className="text-xs text-slate-400 block mb-1">Title</label>
            <input
              type="text"
              value={config.metadata.title}
              onChange={(e) => updateMetadata('title', e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1.5 text-sm text-white"
            />
          </div>

          <div>
            <label className="text-xs text-slate-400 block mb-1">Description</label>
            <textarea
              value={config.metadata.description}
              onChange={(e) => updateMetadata('description', e.target.value)}
              rows={2}
              className="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1.5 text-sm text-white resize-none"
            />
          </div>

          <div>
            <label className="text-xs text-slate-400 block mb-1">Author</label>
            <input
              type="text"
              value={config.metadata.author}
              onChange={(e) => updateMetadata('author', e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1.5 text-sm text-white"
            />
          </div>

          <div>
            <label className="text-xs text-slate-400 block mb-1">Tags</label>
            <div className="flex gap-1 mb-2 flex-wrap">
              {config.metadata.tags.map(tag => (
                <span
                  key={tag}
                  className="px-2 py-0.5 bg-violet-600/30 text-violet-300 rounded text-xs flex items-center gap-1"
                >
                  {tag}
                  <button onClick={() => removeTag(tag)} className="hover:text-white">×</button>
                </span>
              ))}
            </div>
            <div className="flex gap-1">
              <input
                type="text"
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && addTag()}
                placeholder="Add tag..."
                className="flex-1 bg-slate-800 border border-slate-700 rounded px-2 py-1 text-sm text-white"
              />
              <button
                onClick={addTag}
                className="px-2 py-1 bg-slate-700 hover:bg-slate-600 text-white rounded text-sm"
              >
                +
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Export Button */}
      <button
        onClick={handleExport}
        disabled={isExporting}
        className={`w-full mt-4 py-2 rounded-lg text-sm font-medium transition-colors ${
          isExporting
            ? 'bg-slate-700 text-slate-400 cursor-not-allowed'
            : 'bg-violet-600 hover:bg-violet-500 text-white'
        }`}
      >
        {isExporting ? (
          <span className="flex items-center justify-center gap-2">
            <motion.span
              animate={{ rotate: 360 }}
              transition={{ repeat: Infinity, duration: 1 }}
              className="w-4 h-4 border-2 border-slate-400 border-t-transparent rounded-full"
            />
            Exporting...
          </span>
        ) : (
          `Export as ${FORMAT_OPTIONS.find(f => f.value === config.format)?.label || config.format.toUpperCase()}`
        )}
      </button>

      {/* Last Export Info */}
      {lastExport && (
        <div className="mt-3 p-2 bg-slate-800/50 rounded text-xs">
          <div className="text-slate-400 mb-1">Last Export</div>
          <div className="text-white">{lastExport.exportId}</div>
          <div className="text-slate-500">{new Date(lastExport.exportedAt).toLocaleString()}</div>
        </div>
      )}
    </div>
  );
}

export default ExportPanel;
