/**
 * Stigmergy Flow Visualization Constants
 */

import { ParticleType, ScheduleNode } from './types';

// Scene layout constants
export const TIME_SCALE = 5;        // Z-axis spacing for days
export const ROW_SPACING = 2;       // X-axis spacing for people
export const TIME_OF_DAY_Y = {      // Y-axis positions for time slots
  AM: 2,
  PM: -2,
  NIGHT: -4,
};

// Particle counts
export const MAX_PARTICLES = 2500;
export const DAYS_TO_DISPLAY = 90;

// Animation
export const AUTO_ROTATE_SPEED = 0.5;
export const PULSE_SPEED = 2;

// Mock names for demo (no real PERSEC data)
export const MOCK_NAMES = [
  'Dr. Alpha', 'Dr. Beta', 'Dr. Gamma', 'Dr. Delta',
  'Res. Echo', 'Res. Foxtrot', 'Res. Golf', 'Res. Hotel',
  'Res. India', 'Res. Juliet', 'Res. Kilo', 'Res. Lima',
];

/**
 * Generate mock schedule data for visualization demo
 */
export const generateMockData = (): ScheduleNode[] => {
  const nodes: ScheduleNode[] = [];
  const days = 7;
  const residents = 5;
  const faculty = 3;

  // Generate Faculty assignments
  for (let f = 0; f < faculty; f++) {
    for (let d = 0; d < days; d++) {
      const hasClinic = Math.random() > 0.3;
      if (!hasClinic) continue;

      const id = `fac-${f}-${d}`;
      const timeOfDay: 'AM' | 'PM' = Math.random() > 0.5 ? 'AM' : 'PM';

      nodes.push({
        id,
        personName: MOCK_NAMES[f],
        role: 'FACULTY',
        type: ParticleType.CLINIC,
        date: new Date(Date.now() + d * 86400000).toISOString(),
        timeOfDay,
        position: [
          (f - faculty / 2) * ROW_SPACING,
          TIME_OF_DAY_Y[timeOfDay],
          (d - days / 2) * TIME_SCALE,
        ],
        connections: [],
        intensity: 1,
      });
    }
  }

  // Generate Resident assignments
  for (let r = 0; r < residents; r++) {
    for (let d = 0; d < days; d++) {
      const id = `res-${r}-${d}`;
      const rand = Math.random();

      let type = ParticleType.CLINIC;
      let timeOfDay: 'AM' | 'PM' | 'NIGHT' = 'AM';

      if (rand > 0.85) {
        type = ParticleType.CALL;
        timeOfDay = 'NIGHT';
      } else if (rand > 0.65) {
        type = ParticleType.FMIT;
        timeOfDay = Math.random() > 0.5 ? 'AM' : 'PM';
      } else if (rand < 0.08) {
        type = ParticleType.CONFLICT;
      } else if (rand < 0.12) {
        type = ParticleType.UNASSIGNED;
      }

      // Find a faculty to connect to (supervision relationship)
      const potentialFaculty = nodes.filter(
        (n) =>
          n.role === 'FACULTY' &&
          Math.abs(n.position[2] - (d - days / 2) * TIME_SCALE) < 1
      );
      const connections =
        potentialFaculty.length > 0 ? [potentialFaculty[0].id] : [];

      nodes.push({
        id,
        personName: MOCK_NAMES[faculty + r],
        role: 'RESIDENT',
        type,
        date: new Date(Date.now() + d * 86400000).toISOString(),
        timeOfDay,
        position: [
          (r + faculty - (residents + faculty) / 2) * ROW_SPACING,
          TIME_OF_DAY_Y[timeOfDay],
          (d - days / 2) * TIME_SCALE,
        ],
        connections,
        intensity: type === ParticleType.CONFLICT ? 1.5 : 1,
      });
    }
  }

  return nodes;
};
