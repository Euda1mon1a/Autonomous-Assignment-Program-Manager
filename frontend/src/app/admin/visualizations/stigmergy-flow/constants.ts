/**
 * Stigmergy Flow Visualization Constants
 */

import type { StigmergyPatternsResponse } from '@/types/resilience';
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

/**
 * Transform stigmergy patterns API response to ScheduleNode format for visualization.
 *
 * The API returns a wrapped response: { patterns: [patternData], total: N }
 * The single pattern in the array contains:
 * - Popular slots as green particles (positive preference)
 * - Unpopular slots as red conflict particles (negative preference)
 * - Neutral slots as standard clinic particles
 * - Swap pair relationships as connection lines
 *
 * @param data - Stigmergy patterns response from the API
 * @returns ScheduleNode[] ready for 3D visualization
 */
export function transformPatternsToNodes(
  data: StigmergyPatternsResponse | undefined
): ScheduleNode[] {
  // Return mock data if API returns empty or undefined
  if (!data || data.total === 0 || data.patterns.length === 0) {
    return generateMockData();
  }

  const nodes: ScheduleNode[] = [];

  // Extract the first (and typically only) pattern from the wrapped response
  const patternData = data.patterns[0];

  // Group patterns by type for organized visualization
  const popularSlots: Array<{ slotType: string; net: number }> = [];
  const unpopularSlots: Array<{ slotType: string; net: number }> = [];
  const swapPairs: Array<{ f1: string; f2: string; strength: number }> = [];

  // Handle popularSlots: [[slotType, netPreference], ...]
  if (Array.isArray(patternData.popularSlots)) {
    for (const [slotType, netPreference] of patternData.popularSlots) {
      popularSlots.push({ slotType, net: netPreference });
    }
  }

  // Handle unpopularSlots: [[slotType, netPreference], ...]
  if (Array.isArray(patternData.unpopularSlots)) {
    for (const [slotType, netPreference] of patternData.unpopularSlots) {
      unpopularSlots.push({ slotType, net: netPreference });
    }
  }

  // Handle strongSwapPairs: [[facultyId1, facultyId2, strength], ...]
  if (Array.isArray(patternData.strongSwapPairs)) {
    for (const [facultyId1, facultyId2, strength] of patternData.strongSwapPairs) {
      swapPairs.push({
        f1: facultyId1,
        f2: facultyId2,
        strength,
      });
    }
  }

  // Create nodes for popular slots (green/FMIT type - positive patterns)
  popularSlots.forEach((slot, index) => {
    const dayOffset = index % 7;
    const rowIndex = Math.floor(index / 7);
    const timeOfDay: 'AM' | 'PM' = index % 2 === 0 ? 'AM' : 'PM';

    nodes.push({
      id: `popular-${index}`,
      personName: `Popular: ${slot.slotType}`,
      role: 'FACULTY',
      type: ParticleType.FMIT, // Green for popular
      date: new Date(Date.now() + dayOffset * 86400000).toISOString(),
      timeOfDay,
      position: [
        (rowIndex - popularSlots.length / 14) * ROW_SPACING,
        TIME_OF_DAY_Y[timeOfDay],
        (dayOffset - 3.5) * TIME_SCALE,
      ],
      connections: [],
      intensity: Math.min(1.5, 0.5 + slot.net), // Brighter for stronger preference
    });
  });

  // Create nodes for unpopular slots (red/CONFLICT type - negative patterns)
  unpopularSlots.forEach((slot, index) => {
    const dayOffset = index % 7;
    const rowIndex = Math.floor(index / 7);
    const timeOfDay: 'AM' | 'PM' = index % 2 === 0 ? 'AM' : 'PM';

    nodes.push({
      id: `unpopular-${index}`,
      personName: `Avoid: ${slot.slotType}`,
      role: 'RESIDENT',
      type: ParticleType.CONFLICT, // Red for unpopular
      date: new Date(Date.now() + dayOffset * 86400000).toISOString(),
      timeOfDay,
      position: [
        (rowIndex - unpopularSlots.length / 14 + 3) * ROW_SPACING,
        TIME_OF_DAY_Y[timeOfDay],
        (dayOffset - 3.5) * TIME_SCALE,
      ],
      connections: [],
      intensity: Math.min(1.5, 0.5 + Math.abs(slot.net)),
    });
  });

  // Create nodes for swap pairs (connected particles showing affinity)
  swapPairs.forEach((pair, index) => {
    const dayOffset = index % 7;
    const timeOfDay: 'AM' | 'PM' | 'NIGHT' = 'PM';

    // Create two connected nodes for each swap pair
    const node1Id = `swap-${index}-a`;
    const node2Id = `swap-${index}-b`;

    nodes.push({
      id: node1Id,
      personName: `Swap: ${pair.f1.slice(0, 8)}`,
      role: 'RESIDENT',
      type: ParticleType.CLINIC,
      date: new Date(Date.now() + dayOffset * 86400000).toISOString(),
      timeOfDay,
      position: [
        -2 * ROW_SPACING,
        TIME_OF_DAY_Y[timeOfDay] + index * 0.5,
        (dayOffset - 3.5) * TIME_SCALE,
      ],
      connections: [node2Id], // Connect to pair partner
      intensity: pair.strength,
    });

    nodes.push({
      id: node2Id,
      personName: `Swap: ${pair.f2.slice(0, 8)}`,
      role: 'RESIDENT',
      type: ParticleType.CLINIC,
      date: new Date(Date.now() + dayOffset * 86400000).toISOString(),
      timeOfDay,
      position: [
        2 * ROW_SPACING,
        TIME_OF_DAY_Y[timeOfDay] + index * 0.5,
        (dayOffset - 3.5) * TIME_SCALE,
      ],
      connections: [node1Id], // Connect back
      intensity: pair.strength,
    });
  });

  // If we have too few nodes from the API data, supplement with mock data
  if (nodes.length < 10) {
    const mockNodes = generateMockData();
    return [...nodes, ...mockNodes.slice(0, 20)];
  }

  return nodes;
}
