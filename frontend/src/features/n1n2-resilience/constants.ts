/**
 * N-1/N-2 Resilience Visualizer Constants
 *
 * Mock data and computation functions for absence simulation.
 */

import type { Faculty, CascadeMetrics, ResilienceMode } from './types';

/**
 * Mock faculty data
 */
export const MOCK_FACULTY: Faculty[] = [
  {
    id: 'f1',
    name: 'Dr. Alpha',
    role: 'attending',
    specialty: 'General',
    coverage: 18,
    isAbsent: false,
    criticality: 'critical',
  },
  {
    id: 'f2',
    name: 'Dr. Bravo',
    role: 'attending',
    specialty: 'Cardiology',
    coverage: 15,
    isAbsent: false,
    criticality: 'high',
  },
  {
    id: 'f3',
    name: 'Dr. Charlie',
    role: 'attending',
    specialty: 'Pediatrics',
    coverage: 12,
    isAbsent: false,
    criticality: 'high',
  },
  {
    id: 'f4',
    name: 'Dr. Delta',
    role: 'senior',
    specialty: 'Emergency',
    coverage: 14,
    isAbsent: false,
    criticality: 'critical',
  },
  {
    id: 'f5',
    name: 'Dr. Echo',
    role: 'senior',
    specialty: 'General',
    coverage: 10,
    isAbsent: false,
    criticality: 'medium',
  },
  {
    id: 'f6',
    name: 'Dr. Foxtrot',
    role: 'junior',
    specialty: 'General',
    coverage: 8,
    isAbsent: false,
    criticality: 'low',
  },
  {
    id: 'f7',
    name: 'Dr. Golf',
    role: 'junior',
    specialty: 'Pediatrics',
    coverage: 7,
    isAbsent: false,
    criticality: 'low',
  },
  {
    id: 'f8',
    name: 'Dr. Hotel',
    role: 'attending',
    specialty: 'Surgery',
    coverage: 16,
    isAbsent: false,
    criticality: 'high',
  },
];

/**
 * Color mapping for criticality levels
 */
export const CRITICALITY_COLORS: Record<Faculty['criticality'], string> = {
  low: 'from-green-500 to-green-600',
  medium: 'from-amber-500 to-amber-600',
  high: 'from-orange-500 to-orange-600',
  critical: 'from-red-500 to-red-600',
};

/**
 * Border colors for criticality
 */
export const CRITICALITY_BORDER_COLORS: Record<Faculty['criticality'], string> =
  {
    low: 'border-green-500/50 hover:border-green-400',
    medium: 'border-amber-500/50 hover:border-amber-400',
    high: 'border-orange-500/50 hover:border-orange-400',
    critical: 'border-red-500/50 hover:border-red-400',
  };

/**
 * Status colors
 */
export const STATUS_COLORS: Record<CascadeMetrics['systemStatus'], string> = {
  stable: 'text-green-400',
  strained: 'text-amber-400',
  critical: 'text-orange-400',
  failed: 'text-red-400',
};

/**
 * Status background colors
 */
export const STATUS_BG_COLORS: Record<CascadeMetrics['systemStatus'], string> =
  {
    stable: 'bg-green-500/20 border-green-500/50',
    strained: 'bg-amber-500/20 border-amber-500/50',
    critical: 'bg-orange-500/20 border-orange-500/50',
    failed: 'bg-red-500/20 border-red-500/50',
  };

/**
 * Compute cascade metrics based on absent faculty
 */
export function computeCascadeMetrics(
  faculty: Faculty[],
  absentIds: string[],
  mode: ResilienceMode
): CascadeMetrics {
  const absentFaculty = faculty.filter((f) => absentIds.includes(f.id));
  const presentFaculty = faculty.filter((f) => !absentIds.includes(f.id));

  // Total coverage lost
  const totalCoverage = faculty.reduce((sum, f) => sum + f.coverage, 0);
  const lostCoverage = absentFaculty.reduce((sum, f) => sum + f.coverage, 0);
  const coverageGap = totalCoverage > 0 ? (lostCoverage / totalCoverage) * 100 : 0;

  // Affected slots (each coverage point = ~2 slots)
  const affectedSlots = Math.round(lostCoverage * 2);

  // Cascade depth based on criticality
  const criticalAbsent = absentFaculty.filter(
    (f) => f.criticality === 'critical'
  ).length;
  const highAbsent = absentFaculty.filter(
    (f) => f.criticality === 'high'
  ).length;
  const cascadeDepth = criticalAbsent * 3 + highAbsent * 2 + absentFaculty.length;

  // Redistribution load
  const redistributionLoad =
    presentFaculty.length > 0
      ? (lostCoverage / presentFaculty.length) * 10
      : 100;

  // System status
  let systemStatus: CascadeMetrics['systemStatus'];
  const maxAbsences = mode === 'N-1' ? 1 : 2;

  if (absentIds.length === 0) {
    systemStatus = 'stable';
  } else if (absentIds.length <= maxAbsences && coverageGap < 20) {
    systemStatus = 'strained';
  } else if (absentIds.length <= maxAbsences && coverageGap < 35) {
    systemStatus = 'critical';
  } else {
    systemStatus = 'failed';
  }

  // Recovery time
  let recoveryTime: string;
  if (cascadeDepth === 0) {
    recoveryTime = 'N/A';
  } else if (cascadeDepth < 3) {
    recoveryTime = '< 4 hours';
  } else if (cascadeDepth < 6) {
    recoveryTime = '4-12 hours';
  } else if (cascadeDepth < 10) {
    recoveryTime = '12-24 hours';
  } else {
    recoveryTime = '> 24 hours';
  }

  return {
    coverageGap: Math.round(coverageGap * 10) / 10,
    affectedSlots,
    cascadeDepth,
    redistributionLoad: Math.round(redistributionLoad * 10) / 10,
    systemStatus,
    recoveryTime,
  };
}
