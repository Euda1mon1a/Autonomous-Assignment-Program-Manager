/**
 * Schedule Animator Component
 *
 * Shows schedule evolution over time with smooth transitions
 * and keyframe-based animation controls.
 */

'use client';

import React, { useMemo, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type {
  AnimationConfig,
  AnimationKeyframe,
  AnimatedAssignment,
} from './types';

interface ScheduleAnimatorProps {
  config: AnimationConfig;
  keyframes: AnimationKeyframe[];
  currentKeyframe: AnimationKeyframe | null;
  onPlay: () => void;
  onPause: () => void;
  onSeek: (frame: number) => void;
  width?: number;
  height?: number;
}

export function ScheduleAnimator({
  config,
  keyframes,
  currentKeyframe,
  onPlay,
  onPause,
  onSeek,
  width = 800,
  height = 600,
}: ScheduleAnimatorProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Interpolate between keyframes for smooth animation
  const interpolatedAssignments = useMemo(() => {
    if (!currentKeyframe) return [];

    // Get next keyframe for interpolation
    const nextFrameIdx = Math.min(config.currentFrame + 1, keyframes.length - 1);
    const nextKeyframe = keyframes[nextFrameIdx];

    if (!nextKeyframe || config.currentFrame === keyframes.length - 1) {
      return currentKeyframe.state.assignments;
    }

    // Calculate interpolation factor
    const t = config.currentFrame - Math.floor(config.currentFrame);

    // Interpolate each assignment
    return currentKeyframe.state.assignments.map((current, i) => {
      const next = nextKeyframe.state.assignments[i];
      if (!next) return current;

      return {
        ...current,
        position: {
          x: lerp(current.position.x, next.position.x, t),
          y: lerp(current.position.y, next.position.y, t),
          z: lerp(current.position.z, next.position.z, t),
        },
        scale: lerp(current.scale, next.scale, t),
      };
    });
  }, [currentKeyframe, config.currentFrame, keyframes]);

  // Draw to canvas for performance
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.fillStyle = '#0f172a';
    ctx.fillRect(0, 0, width, height);

    // Draw grid
    ctx.strokeStyle = 'rgba(139, 92, 246, 0.1)';
    ctx.lineWidth = 1;
    for (let x = 0; x <= width; x += 50) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
    }
    for (let y = 0; y <= height; y += 50) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }

    // Draw assignments as particles
    for (const assignment of interpolatedAssignments) {
      const screenX = width / 2 + assignment.position.x * 40;
      const screenY = height / 2 - assignment.position.y * 40;
      const radius = 10 * assignment.scale;

      // Draw glow
      const gradient = ctx.createRadialGradient(
        screenX, screenY, 0,
        screenX, screenY, radius * 2
      );
      gradient.addColorStop(0, assignment.color);
      gradient.addColorStop(1, 'transparent');

      ctx.fillStyle = gradient;
      ctx.beginPath();
      ctx.arc(screenX, screenY, radius * 2, 0, Math.PI * 2);
      ctx.fill();

      // Draw core
      ctx.fillStyle = assignment.color;
      ctx.beginPath();
      ctx.arc(screenX, screenY, radius, 0, Math.PI * 2);
      ctx.fill();

      // Draw depth indicator (z position)
      const zOffset = assignment.position.z * 5;
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(screenX, screenY);
      ctx.lineTo(screenX + zOffset, screenY - zOffset);
      ctx.stroke();
    }

    // Draw frame info
    ctx.fillStyle = '#94a3b8';
    ctx.font = '12px monospace';
    ctx.fillText(`Frame: ${config.currentFrame + 1} / ${config.totalFrames}`, 10, 20);
    if (currentKeyframe) {
      ctx.fillText(`Time: ${new Date(currentKeyframe.timestamp).toLocaleTimeString()}`, 10, 35);
      ctx.fillText(`Coverage: ${currentKeyframe.state.coverageScore.toFixed(1)}%`, 10, 50);
    }

    // Draw violations indicator
    if (currentKeyframe?.state.violations.length > 0) {
      ctx.fillStyle = '#ef4444';
      ctx.fillText(`⚠ ${currentKeyframe.state.violations.length} violations`, 10, 65);
    }

  }, [interpolatedAssignments, width, height, config, currentKeyframe]);

  return (
    <div className="w-full h-full flex flex-col bg-slate-950">
      {/* Canvas */}
      <div className="flex-1 relative">
        <canvas
          ref={canvasRef}
          width={width}
          height={height}
          className="w-full h-full object-contain"
        />

        {/* Overlay controls */}
        <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 flex items-center gap-3 bg-slate-900/90 backdrop-blur rounded-full px-6 py-3">
          {/* Play/Pause */}
          <button
            onClick={config.isPlaying ? onPause : onPlay}
            className="w-10 h-10 rounded-full bg-violet-600 hover:bg-violet-500 flex items-center justify-center text-white"
          >
            {config.isPlaying ? (
              <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                <rect x="3" y="2" width="4" height="12" rx="1" />
                <rect x="9" y="2" width="4" height="12" rx="1" />
              </svg>
            ) : (
              <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                <path d="M4 2l10 6-10 6V2z" />
              </svg>
            )}
          </button>

          {/* Timeline scrubber */}
          <div className="w-64 relative">
            <input
              type="range"
              min={0}
              max={config.totalFrames - 1}
              value={config.currentFrame}
              onChange={(e) => onSeek(Number(e.target.value))}
              className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer"
            />
            <div className="flex justify-between text-xs text-slate-500 mt-1">
              <span>0</span>
              <span>{config.currentFrame + 1}</span>
              <span>{config.totalFrames}</span>
            </div>
          </div>

          {/* Speed indicator */}
          <div className="text-xs text-slate-400">
            {config.fps} FPS
          </div>
        </div>

        {/* Wavelength indicators */}
        {currentKeyframe?.state.wavelengthSnapshots && (
          <div className="absolute top-4 right-4 space-y-2">
            {Object.entries(currentKeyframe.state.wavelengthSnapshots).map(([channel, value]) => (
              <div key={channel} className="flex items-center gap-2 text-xs">
                <span className="text-slate-400 w-16">{channel}</span>
                <div className="w-16 h-2 bg-slate-800 rounded-full overflow-hidden">
                  <motion.div
                    className="h-full bg-violet-500"
                    animate={{ width: `${(value as number) * 100}%` }}
                    transition={{ duration: 0.3 }}
                  />
                </div>
                <span className="text-slate-500 w-10">
                  {((value as number) * 100).toFixed(0)}%
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Keyframe timeline */}
      <div className="h-20 bg-slate-900 border-t border-slate-800 p-2">
        <div className="relative h-full overflow-x-auto">
          <div className="flex gap-1 h-full items-end">
            {keyframes.slice(0, 100).map((kf, i) => {
              const isActive = i === config.currentFrame;
              const hasViolations = kf.state.violations.length > 0;
              const barHeight = 20 + (kf.state.coverageScore / 100) * 40;

              return (
                <button
                  key={kf.frameIndex}
                  onClick={() => onSeek(i)}
                  className={`w-2 rounded-t transition-all ${
                    isActive
                      ? 'bg-violet-500'
                      : hasViolations
                      ? 'bg-red-500/50 hover:bg-red-500'
                      : 'bg-slate-700 hover:bg-slate-600'
                  }`}
                  style={{ height: barHeight }}
                  title={`Frame ${i + 1}: ${kf.state.coverageScore.toFixed(1)}% coverage`}
                />
              );
            })}
          </div>

          {/* Playhead */}
          <motion.div
            className="absolute top-0 w-0.5 h-full bg-violet-400"
            animate={{
              left: `${(config.currentFrame / config.totalFrames) * 100}%`,
            }}
            transition={{ duration: 0.1 }}
          />
        </div>
      </div>
    </div>
  );
}

// Linear interpolation helper
function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}

export default ScheduleAnimator;
