/**
 * Stigmergy Flow Visualization Types
 *
 * Named after the ant pheromone trails in the resilience framework.
 * Represents schedule assignments as particles flowing through spacetime.
 */

import * as THREE from 'three';

export enum ParticleType {
  CLINIC = 'CLINIC',
  FMIT = 'FMIT',
  CALL = 'CALL',
  CONFLICT = 'CONFLICT',
  UNASSIGNED = 'UNASSIGNED'
}

export interface ScheduleNode {
  id: string;
  personName: string;
  role: 'RESIDENT' | 'FACULTY';
  type: ParticleType;
  date: string; // ISO String
  timeOfDay: 'AM' | 'PM' | 'NIGHT';
  position: [number, number, number]; // x, y, z in 3D space
  connections: string[]; // IDs of connected nodes (e.g., supervision relationships)
  intensity: number; // 0-1 for glow brightness
}

export interface SimulationConfig {
  speed: number;
  bloomStrength: number;
  showConnections: boolean;
  distortion: number;
}

export interface GeminiAnalysisResult {
  summary: string;
  hotspots: string[];
  recommendations: string[];
}

// Color mapping for particle types
export const PARTICLE_COLORS: Record<ParticleType, THREE.Color> = {
  [ParticleType.CLINIC]: new THREE.Color('#3b82f6'),     // Blue-500 - Clinic assignments
  [ParticleType.FMIT]: new THREE.Color('#22c55e'),       // Green-500 - FMIT rotations
  [ParticleType.CALL]: new THREE.Color('#eab308'),       // Yellow-500 - Call shifts
  [ParticleType.CONFLICT]: new THREE.Color('#ef4444'),   // Red-500 - Conflicts
  [ParticleType.UNASSIGNED]: new THREE.Color('#ffffff'), // White - Unassigned slots
};
