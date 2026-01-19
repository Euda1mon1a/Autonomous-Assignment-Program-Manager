/**
 * Bottleneck Flow Visualizer Constants
 *
 * Color palette, lane configurations, and size constants
 * for the 3D supervision cascade visualization.
 */

import * as THREE from 'three';
import type { LaneConfig, LaneType } from './types';

// ============================================================================
// Color Palette
// ============================================================================

export const COLORS = {
  nominal: '#22c55e', // Green - healthy state
  degraded: '#fbbf24', // Amber - warning state
  critical: '#ef4444', // Red - critical/orphaned
  down: '#1a1a1a', // Black - disabled
  reserve: '#a855f7', // Purple - reserve pool
  atLane: '#3b82f6', // Blue - AT coverage lane
} as const;

export const THREE_COLORS = {
  nominal: new THREE.Color(COLORS.nominal),
  degraded: new THREE.Color(COLORS.degraded),
  critical: new THREE.Color(COLORS.critical),
  down: new THREE.Color(COLORS.down),
  reserve: new THREE.Color(0xffffff),
} as const;

// ============================================================================
// Lane Configuration
// ============================================================================

export const LANES: Record<LaneType, LaneConfig> = {
  AT: {
    y: 8,
    color: COLORS.atLane,
    threeColor: new THREE.Color(COLORS.atLane),
    name: 'AT Coverage',
  },
  FMIT: {
    y: 0,
    color: COLORS.nominal,
    threeColor: new THREE.Color(COLORS.nominal),
    name: 'FMIT Rotations',
  },
  RESERVE: {
    y: -8,
    color: COLORS.reserve,
    threeColor: new THREE.Color(COLORS.reserve),
    name: 'Reserve Pool',
  },
} as const;

// ============================================================================
// Node Sizes
// ============================================================================

export const SIZES = {
  faculty: 1.2,
  pgy1: 0.7,
  pgy2: 0.5,
  pgy3: 0.45,
} as const;

// ============================================================================
// Animation Constants
// ============================================================================

export const STREAM_LENGTH = 150;
export const FLOW_SPEED = 0.15;
export const ORBIT_RADIUS = 2.5;
export const LERP_FACTOR = 0.05;

// ============================================================================
// Layout Constants
// ============================================================================

export const FACULTY_X_SPREAD = 5;
export const FACULTY_Z_START = -20;
export const FACULTY_Z_SPACING = 25;
export const FACULTY_COLUMNS = 3;

// ============================================================================
// Particle System
// ============================================================================

export const PARTICLE_COUNT = 200;
