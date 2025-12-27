/**
 * Guided Tour Player Component
 *
 * Plays pre-programmed camera paths that highlight key insights
 * in the holographic visualization.
 */

'use client';

import React, { useCallback, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type {
  GuidedTour,
  TourWaypoint,
  WavelengthChannel,
} from './types';
import { WAVELENGTH_COLORS, WAVELENGTH_LABELS } from './types';

interface TourPlayerState {
  currentWaypointIndex: number;
  currentWaypoint: TourWaypoint | null;
  isPlaying: boolean;
  progress: number;
  play: () => void;
  pause: () => void;
  reset: () => void;
  goToWaypoint: (index: number) => void;
  totalWaypoints: number;
}

interface GuidedTourPlayerProps {
  tour: GuidedTour;
  player: TourPlayerState;
  onEnd: () => void;
}

export function GuidedTourPlayer({
  tour,
  player,
  onEnd,
}: GuidedTourPlayerProps) {
  const {
    currentWaypointIndex,
    currentWaypoint,
    isPlaying,
    progress,
    play,
    pause,
    reset,
    goToWaypoint,
    totalWaypoints,
  } = player;

  // Calculate total tour progress
  const totalProgress = useMemo(() => {
    if (!tour.waypoints.length) return 0;
    const waypointProgress = currentWaypointIndex / tour.waypoints.length;
    const withinWaypointProgress = progress / tour.waypoints.length;
    return waypointProgress + withinWaypointProgress;
  }, [currentWaypointIndex, progress, tour.waypoints.length]);

  // Handle keyboard controls
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      switch (e.key) {
        case ' ':
        case 'k':
          e.preventDefault();
          isPlaying ? pause() : play();
          break;
        case 'ArrowLeft':
          e.preventDefault();
          goToWaypoint(Math.max(0, currentWaypointIndex - 1));
          break;
        case 'ArrowRight':
          e.preventDefault();
          goToWaypoint(Math.min(totalWaypoints - 1, currentWaypointIndex + 1));
          break;
        case 'Escape':
          e.preventDefault();
          onEnd();
          break;
        case 'r':
          e.preventDefault();
          reset();
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isPlaying, play, pause, goToWaypoint, currentWaypointIndex, totalWaypoints, onEnd, reset]);

  // Format time
  const formatTime = useCallback((seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }, []);

  // Calculate elapsed and remaining time
  const elapsedTime = useMemo(() => {
    let elapsed = 0;
    for (let i = 0; i < currentWaypointIndex; i++) {
      const wp = tour.waypoints[i];
      elapsed += wp.transition.duration + wp.dwellTime;
    }
    if (currentWaypoint) {
      elapsed += progress * (currentWaypoint.transition.duration + currentWaypoint.dwellTime);
    }
    return elapsed;
  }, [currentWaypointIndex, progress, currentWaypoint, tour.waypoints]);

  const remainingTime = tour.duration - elapsedTime;

  return (
    <div className="absolute inset-0 flex flex-col">
      {/* Tour Header */}
      <div className="absolute top-4 left-4 right-4 z-10 flex items-center justify-between">
        <div className="bg-slate-900/90 backdrop-blur rounded-lg px-4 py-2">
          <h2 className="text-white font-medium">{tour.name}</h2>
          <p className="text-slate-400 text-sm">{tour.description}</p>
        </div>

        <button
          onClick={onEnd}
          className="bg-slate-900/90 backdrop-blur rounded-lg px-4 py-2 text-slate-300 hover:text-white"
        >
          Exit Tour
        </button>
      </div>

      {/* Main visualization area - placeholder for actual 3D scene */}
      <div className="flex-1 relative bg-gradient-to-br from-slate-900 via-violet-950/20 to-slate-900">
        {/* Camera target indicator */}
        {currentWaypoint && (
          <motion.div
            className="absolute left-1/2 top-1/2 transform -translate-x-1/2 -translate-y-1/2"
            animate={{
              scale: [1, 1.2, 1],
            }}
            transition={{ repeat: Infinity, duration: 2 }}
          >
            <div className="w-32 h-32 border-2 border-violet-500/50 rounded-full flex items-center justify-center">
              <div className="w-16 h-16 border border-violet-400/50 rounded-full flex items-center justify-center">
                <div className="w-4 h-4 bg-violet-500 rounded-full" />
              </div>
            </div>
          </motion.div>
        )}

        {/* Active wavelength channels indicator */}
        {currentWaypoint && currentWaypoint.activeChannels.length > 0 && (
          <div className="absolute top-20 right-4 bg-slate-900/80 backdrop-blur rounded-lg p-3">
            <div className="text-xs text-slate-400 mb-2">Active Channels</div>
            <div className="flex flex-col gap-2">
              {currentWaypoint.activeChannels.map(channel => (
                <motion.div
                  key={channel}
                  className="flex items-center gap-2"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                >
                  <motion.span
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: WAVELENGTH_COLORS[channel] }}
                    animate={{ scale: [1, 1.3, 1] }}
                    transition={{ repeat: Infinity, duration: 2 }}
                  />
                  <span className="text-sm text-slate-300">{WAVELENGTH_LABELS[channel]}</span>
                </motion.div>
              ))}
            </div>
          </div>
        )}

        {/* Highlighted entities */}
        {currentWaypoint && currentWaypoint.highlights.length > 0 && (
          <div className="absolute top-20 left-4 bg-slate-900/80 backdrop-blur rounded-lg p-3">
            <div className="text-xs text-slate-400 mb-2">Highlighted</div>
            <div className="flex flex-wrap gap-1">
              {currentWaypoint.highlights.map(id => (
                <span
                  key={id}
                  className="px-2 py-1 bg-violet-600/30 text-violet-300 rounded text-xs"
                >
                  {id}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Annotation Display */}
      <AnimatePresence mode="wait">
        {currentWaypoint && (
          <motion.div
            key={currentWaypoint.index}
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -50 }}
            className="absolute bg-slate-900/95 backdrop-blur-lg rounded-xl p-6 shadow-2xl border border-violet-500/30 max-w-md"
            style={{
              left: `${currentWaypoint.annotation.position.x * 100}%`,
              top: `${currentWaypoint.annotation.position.y * 100}%`,
              transform: 'translate(-50%, -50%)',
            }}
          >
            <h3 className="text-xl font-semibold text-white mb-2">
              {currentWaypoint.annotation.title}
            </h3>
            <p className="text-slate-300">
              {currentWaypoint.annotation.body}
            </p>

            {/* Pointer line to 3D position */}
            {currentWaypoint.annotation.pointer && (
              <div className="absolute w-1 h-12 bg-gradient-to-b from-violet-500 to-transparent -bottom-12 left-1/2 -translate-x-1/2" />
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Bottom Controls */}
      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-slate-950 to-transparent pt-20 pb-6 px-6">
        {/* Progress Bar */}
        <div className="relative h-2 bg-slate-800 rounded-full mb-4 overflow-hidden">
          {/* Waypoint markers */}
          {tour.waypoints.map((wp, i) => {
            const position = (i / tour.waypoints.length) * 100;
            return (
              <button
                key={wp.index}
                onClick={() => goToWaypoint(i)}
                className={`absolute top-1/2 -translate-y-1/2 w-3 h-3 rounded-full transition-colors ${
                  i === currentWaypointIndex
                    ? 'bg-violet-500 ring-2 ring-violet-300'
                    : i < currentWaypointIndex
                    ? 'bg-violet-600'
                    : 'bg-slate-600 hover:bg-slate-500'
                }`}
                style={{ left: `${position}%` }}
                title={wp.annotation.title}
              />
            );
          })}

          {/* Progress fill */}
          <motion.div
            className="absolute top-0 left-0 h-full bg-gradient-to-r from-violet-600 to-violet-400"
            style={{ width: `${totalProgress * 100}%` }}
          />
        </div>

        {/* Controls Row */}
        <div className="flex items-center justify-between">
          {/* Time Display */}
          <div className="text-sm text-slate-400 font-mono min-w-[100px]">
            {formatTime(elapsedTime)} / {formatTime(tour.duration)}
          </div>

          {/* Playback Controls */}
          <div className="flex items-center gap-4">
            {/* Previous */}
            <button
              onClick={() => goToWaypoint(Math.max(0, currentWaypointIndex - 1))}
              disabled={currentWaypointIndex === 0}
              className={`p-2 rounded-full transition-colors ${
                currentWaypointIndex === 0
                  ? 'text-slate-600 cursor-not-allowed'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800'
              }`}
            >
              <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                <path d="M12.79 5.23a.75.75 0 0 1-.02 1.06L8.832 10l3.938 3.71a.75.75 0 1 1-1.04 1.08l-4.5-4.25a.75.75 0 0 1 0-1.08l4.5-4.25a.75.75 0 0 1 1.06.02Z" />
              </svg>
            </button>

            {/* Play/Pause */}
            <button
              onClick={isPlaying ? pause : play}
              className="w-14 h-14 rounded-full bg-violet-600 hover:bg-violet-500 text-white flex items-center justify-center shadow-lg shadow-violet-500/30 transition-colors"
            >
              {isPlaying ? (
                <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M6.75 5.25a.75.75 0 0 1 .75.75v12a.75.75 0 0 1-1.5 0V6a.75.75 0 0 1 .75-.75Zm9.75 0a.75.75 0 0 1 .75.75v12a.75.75 0 0 1-1.5 0V6a.75.75 0 0 1 .75-.75Z" />
                </svg>
              ) : (
                <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.666 6.347a1.125 1.125 0 0 1 0 1.972l-11.666 6.347c-.75.412-1.667-.13-1.667-.986V5.653Z" />
                </svg>
              )}
            </button>

            {/* Next */}
            <button
              onClick={() => goToWaypoint(Math.min(totalWaypoints - 1, currentWaypointIndex + 1))}
              disabled={currentWaypointIndex >= totalWaypoints - 1}
              className={`p-2 rounded-full transition-colors ${
                currentWaypointIndex >= totalWaypoints - 1
                  ? 'text-slate-600 cursor-not-allowed'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800'
              }`}
            >
              <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                <path d="M7.21 14.77a.75.75 0 0 1 .02-1.06L11.168 10 7.23 6.29a.75.75 0 1 1 1.04-1.08l4.5 4.25a.75.75 0 0 1 0 1.08l-4.5 4.25a.75.75 0 0 1-1.06-.02Z" />
              </svg>
            </button>
          </div>

          {/* Waypoint Counter */}
          <div className="text-sm text-slate-400 min-w-[100px] text-right">
            Waypoint {currentWaypointIndex + 1} of {totalWaypoints}
          </div>
        </div>

        {/* Keyboard Shortcuts */}
        <div className="mt-4 flex items-center justify-center gap-6 text-xs text-slate-600">
          <span><kbd className="px-1.5 py-0.5 bg-slate-800 rounded">Space</kbd> Play/Pause</span>
          <span><kbd className="px-1.5 py-0.5 bg-slate-800 rounded">←</kbd> <kbd className="px-1.5 py-0.5 bg-slate-800 rounded">→</kbd> Navigate</span>
          <span><kbd className="px-1.5 py-0.5 bg-slate-800 rounded">R</kbd> Restart</span>
          <span><kbd className="px-1.5 py-0.5 bg-slate-800 rounded">Esc</kbd> Exit</span>
        </div>
      </div>

      {/* Tour level badge */}
      <div className="absolute bottom-6 left-6">
        <span className={`px-3 py-1 rounded-full text-xs font-medium ${
          tour.level === 'beginner' ? 'bg-emerald-500/20 text-emerald-300' :
          tour.level === 'intermediate' ? 'bg-amber-500/20 text-amber-300' :
          'bg-rose-500/20 text-rose-300'
        }`}>
          {tour.level.charAt(0).toUpperCase() + tour.level.slice(1)}
        </span>
      </div>

      {/* Remaining time */}
      <div className="absolute bottom-6 right-6 text-slate-500 text-xs">
        {formatTime(remainingTime)} remaining
      </div>
    </div>
  );
}

export default GuidedTourPlayer;
