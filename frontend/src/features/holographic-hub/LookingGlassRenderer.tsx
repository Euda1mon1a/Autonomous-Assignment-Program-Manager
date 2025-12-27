/**
 * Looking Glass Renderer Component
 *
 * Integrates with Looking Glass holographic displays for
 * true 3D visualization without glasses.
 */

'use client';

import React, { useRef, useEffect, useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import type {
  LookingGlassConfig,
  QuiltSettings,
  HolographicScene,
  HolographicCamera,
} from './types';

interface LookingGlassRendererProps {
  scene: HolographicScene | null;
  enabled: boolean;
  onDeviceDetected?: (config: LookingGlassConfig) => void;
}

// Default Looking Glass device configurations
const DEVICE_PRESETS: Record<string, Partial<LookingGlassConfig>> = {
  portrait: {
    deviceType: 'portrait',
    viewCone: 40,
    quiltSettings: {
      columns: 8,
      rows: 6,
      totalViews: 48,
      viewWidth: 420,
      viewHeight: 560,
      quiltWidth: 3360,
      quiltHeight: 3360,
    },
  },
  landscape: {
    deviceType: 'landscape',
    viewCone: 50,
    quiltSettings: {
      columns: 5,
      rows: 9,
      totalViews: 45,
      viewWidth: 819,
      viewHeight: 455,
      quiltWidth: 4096,
      quiltHeight: 4096,
    },
  },
  go: {
    deviceType: 'go',
    viewCone: 54,
    quiltSettings: {
      columns: 11,
      rows: 6,
      totalViews: 66,
      viewWidth: 512,
      viewHeight: 512,
      quiltWidth: 5632,
      quiltHeight: 3072,
    },
  },
};

export function LookingGlassRenderer({
  scene,
  enabled,
  onDeviceDetected,
}: LookingGlassRendererProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const quiltCanvasRef = useRef<HTMLCanvasElement>(null);
  const [deviceConfig, setDeviceConfig] = useState<LookingGlassConfig | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [previewMode, setPreviewMode] = useState<'quilt' | 'single' | 'hologram'>('single');
  const [selectedPreset, setSelectedPreset] = useState<string>('portrait');

  // Detect Looking Glass device
  useEffect(() => {
    if (!enabled) return;

    const detectDevice = async () => {
      // In production, this would use the Looking Glass WebXR API or Bridge SDK
      // For now, use preset configuration
      const preset = DEVICE_PRESETS[selectedPreset];

      const config: LookingGlassConfig = {
        deviceType: preset.deviceType || 'portrait',
        calibration: {
          pitch: 354.42108154296875,
          slope: -5.2,
          center: 0.5,
          viewCone: preset.viewCone || 40,
          invView: 0,
          displayAspect: 0.75,
          numViews: preset.quiltSettings?.totalViews || 48,
        },
        viewCone: preset.viewCone || 40,
        quiltSettings: preset.quiltSettings || DEVICE_PRESETS.portrait.quiltSettings!,
        rendering: {
          fov: 14,
          convergenceDistance: 5,
          interocularDistance: 0.5,
          focusDistance: 5,
          depthCompression: 0.5,
        },
      };

      setDeviceConfig(config);
      setIsConnected(true);
      onDeviceDetected?.(config);
    };

    detectDevice();
  }, [enabled, selectedPreset, onDeviceDetected]);

  // Render quilt for Looking Glass
  const renderQuilt = useCallback(() => {
    if (!quiltCanvasRef.current || !deviceConfig || !scene) return;

    const ctx = quiltCanvasRef.current.getContext('2d');
    if (!ctx) return;

    const { quiltSettings } = deviceConfig;

    // Set canvas size to quilt dimensions
    quiltCanvasRef.current.width = quiltSettings.quiltWidth;
    quiltCanvasRef.current.height = quiltSettings.quiltHeight;

    // Render each view
    for (let row = 0; row < quiltSettings.rows; row++) {
      for (let col = 0; col < quiltSettings.columns; col++) {
        const viewIndex = row * quiltSettings.columns + col;
        if (viewIndex >= quiltSettings.totalViews) continue;

        // Calculate camera offset for this view
        const viewAngle = ((viewIndex / quiltSettings.totalViews) - 0.5) * deviceConfig.viewCone * (Math.PI / 180);
        const cameraOffset = Math.tan(viewAngle) * deviceConfig.rendering.convergenceDistance;

        // Render single view
        const viewX = col * quiltSettings.viewWidth;
        const viewY = row * quiltSettings.viewHeight;

        // Create temporary canvas for this view
        const viewCanvas = document.createElement('canvas');
        viewCanvas.width = quiltSettings.viewWidth;
        viewCanvas.height = quiltSettings.viewHeight;
        const viewCtx = viewCanvas.getContext('2d');

        if (viewCtx) {
          renderSingleView(viewCtx, scene, cameraOffset, quiltSettings.viewWidth, quiltSettings.viewHeight);
          ctx.drawImage(viewCanvas, viewX, viewY);
        }
      }
    }
  }, [deviceConfig, scene]);

  // Render single view
  const renderSingleView = (
    ctx: CanvasRenderingContext2D,
    scene: HolographicScene,
    cameraOffset: number,
    width: number,
    height: number
  ) => {
    // Clear with scene background
    ctx.fillStyle = '#0a0a1a';
    ctx.fillRect(0, 0, width, height);

    // Apply camera offset for parallax
    ctx.save();
    ctx.translate(width / 2 + cameraOffset * 50, height / 2);

    // Draw scene objects with depth-based parallax
    for (const obj of scene.objects) {
      const parallax = (obj.position.z * cameraOffset) * 10;

      ctx.save();
      ctx.translate(
        obj.position.x * 30 + parallax,
        -obj.position.y * 30
      );
      ctx.scale(obj.scale.x, obj.scale.y);
      ctx.rotate(obj.rotation.z);

      // Draw based on geometry type
      ctx.fillStyle = obj.material.color;
      ctx.globalAlpha = obj.material.opacity;

      switch (obj.geometry) {
        case 'sphere':
          ctx.beginPath();
          ctx.arc(0, 0, 20, 0, Math.PI * 2);
          ctx.fill();

          // Add holographic effect
          if (obj.material.type === 'holographic') {
            const gradient = ctx.createRadialGradient(0, 0, 0, 0, 0, 25);
            gradient.addColorStop(0, obj.material.hologramColor || '#00ffff');
            gradient.addColorStop(0.5, 'transparent');
            gradient.addColorStop(1, obj.material.hologramColor || '#00ffff');
            ctx.fillStyle = gradient;
            ctx.globalAlpha = 0.3;
            ctx.fill();
          }
          break;

        case 'box':
          ctx.fillRect(-15, -15, 30, 30);
          break;

        case 'cylinder':
          ctx.beginPath();
          ctx.ellipse(0, 0, 15, 25, 0, 0, Math.PI * 2);
          ctx.fill();
          break;

        default:
          ctx.fillRect(-10, -10, 20, 20);
      }

      ctx.restore();
    }

    ctx.restore();

    // Add scanline effect if enabled
    const hasScanlinesEffect = scene.effects.find(e => e.type === 'scanlines' && e.enabled);
    if (hasScanlinesEffect) {
      ctx.fillStyle = 'rgba(0, 0, 0, 0.03)';
      for (let y = 0; y < height; y += 2) {
        ctx.fillRect(0, y, width, 1);
      }
    }
  };

  // Preview canvas rendering
  useEffect(() => {
    if (!canvasRef.current || !scene) return;

    const ctx = canvasRef.current.getContext('2d');
    if (!ctx) return;

    const width = canvasRef.current.width;
    const height = canvasRef.current.height;

    if (previewMode === 'single') {
      renderSingleView(ctx, scene, 0, width, height);
    } else if (previewMode === 'quilt' && quiltCanvasRef.current) {
      renderQuilt();
      // Scale quilt to preview canvas
      ctx.drawImage(quiltCanvasRef.current, 0, 0, width, height);
    }
  }, [scene, previewMode, renderQuilt]);

  if (!enabled) return null;

  return (
    <div className="absolute inset-0 bg-black/80 flex flex-col items-center justify-center">
      {/* Header */}
      <div className="absolute top-4 left-4 right-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-emerald-400' : 'bg-red-400'}`} />
          <span className="text-white font-medium">
            Looking Glass {isConnected ? 'Connected' : 'Disconnected'}
          </span>
          {deviceConfig && (
            <span className="text-slate-400 text-sm">
              ({deviceConfig.deviceType} - {deviceConfig.quiltSettings.totalViews} views)
            </span>
          )}
        </div>

        {/* Device preset selector */}
        <div className="flex items-center gap-2">
          <span className="text-slate-400 text-sm">Device:</span>
          <select
            value={selectedPreset}
            onChange={(e) => setSelectedPreset(e.target.value)}
            className="bg-slate-800 text-white text-sm rounded px-2 py-1 border border-slate-700"
          >
            <option value="portrait">Portrait</option>
            <option value="landscape">Landscape</option>
            <option value="go">Go</option>
          </select>
        </div>
      </div>

      {/* Preview canvas */}
      <div className="relative">
        <canvas
          ref={canvasRef}
          width={600}
          height={450}
          className="rounded-lg border border-slate-700 shadow-2xl"
        />

        {/* View mode indicator */}
        <div className="absolute bottom-2 left-2 bg-black/60 backdrop-blur rounded px-2 py-1 text-xs text-slate-300">
          {previewMode === 'single' ? 'Single View Preview' :
           previewMode === 'quilt' ? `Quilt (${deviceConfig?.quiltSettings.totalViews} views)` :
           'Hologram Output'}
        </div>
      </div>

      {/* Hidden quilt canvas for rendering */}
      <canvas ref={quiltCanvasRef} style={{ display: 'none' }} />

      {/* Controls */}
      <div className="mt-4 flex items-center gap-4">
        <div className="flex items-center gap-2 bg-slate-800 rounded-lg p-1">
          {(['single', 'quilt', 'hologram'] as const).map(mode => (
            <button
              key={mode}
              onClick={() => setPreviewMode(mode)}
              className={`px-3 py-1.5 rounded text-sm transition-colors ${
                previewMode === mode
                  ? 'bg-violet-600 text-white'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {mode.charAt(0).toUpperCase() + mode.slice(1)}
            </button>
          ))}
        </div>

        <button
          onClick={renderQuilt}
          className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-sm"
        >
          Render Quilt
        </button>

        <button
          className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm"
          onClick={() => {
            // Export quilt image
            if (quiltCanvasRef.current) {
              const link = document.createElement('a');
              link.download = 'holographic-quilt.png';
              link.href = quiltCanvasRef.current.toDataURL('image/png');
              link.click();
            }
          }}
        >
          Export Quilt
        </button>
      </div>

      {/* Device info */}
      {deviceConfig && (
        <div className="mt-4 grid grid-cols-4 gap-4 text-center text-xs">
          <div className="bg-slate-800/50 rounded p-2">
            <div className="text-slate-500">View Cone</div>
            <div className="text-white font-mono">{deviceConfig.viewCone}°</div>
          </div>
          <div className="bg-slate-800/50 rounded p-2">
            <div className="text-slate-500">Views</div>
            <div className="text-white font-mono">{deviceConfig.quiltSettings.totalViews}</div>
          </div>
          <div className="bg-slate-800/50 rounded p-2">
            <div className="text-slate-500">Quilt Size</div>
            <div className="text-white font-mono">
              {deviceConfig.quiltSettings.quiltWidth}×{deviceConfig.quiltSettings.quiltHeight}
            </div>
          </div>
          <div className="bg-slate-800/50 rounded p-2">
            <div className="text-slate-500">FOV</div>
            <div className="text-white font-mono">{deviceConfig.rendering.fov}°</div>
          </div>
        </div>
      )}
    </div>
  );
}

export default LookingGlassRenderer;
