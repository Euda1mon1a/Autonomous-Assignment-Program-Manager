/**
 * Bottleneck Data Transform Hook
 *
 * Transforms real faculty/resident roster data from API into
 * visualization-ready format for the 3D bottleneck cascade.
 *
 * PERSEC: All real names are masked with phonetic alphabet identifiers.
 */

import { useMemo } from 'react';
import type { Person } from '@/types/api';
import type { BottleneckFaculty, BottleneckTrainee, LaneType } from '../types';

// ============================================================================
// PERSEC: Name Masking
// ============================================================================

const PHONETIC_ALPHABET = [
  'Alpha',
  'Bravo',
  'Charlie',
  'Delta',
  'Echo',
  'Foxtrot',
  'Golf',
  'Hotel',
  'India',
  'Juliet',
  'Kilo',
  'Lima',
  'Mike',
  'November',
  'Oscar',
  'Papa',
  'Quebec',
  'Romeo',
  'Sierra',
  'Tango',
  'Uniform',
  'Victor',
  'Whiskey',
  'X-Ray',
  'Yankee',
  'Zulu',
];

/**
 * Mask a person's name for PERSEC compliance.
 * Never display real names in visualization.
 */
function maskPersonName(index: number, isFaculty: boolean): string {
  const prefix = isFaculty ? 'Dr.' : 'Res.';
  const suffix = PHONETIC_ALPHABET[index % PHONETIC_ALPHABET.length];
  const number = Math.floor(index / PHONETIC_ALPHABET.length);
  return number > 0 ? `${prefix} ${suffix}-${number}` : `${prefix} ${suffix}`;
}

// ============================================================================
// Lane Assignment Logic
// ============================================================================

/**
 * Determine lane assignment based on faculty specialty/role.
 *
 * Heuristics:
 * - AT: Clinic, Ambulatory, Attending keywords
 * - RESERVE: Float, Backup, Reserve keywords
 * - FMIT: Default for rotations
 */
function determineLane(specialty: string | null, index: number): LaneType {
  const spec = (specialty || '').toLowerCase();

  if (spec.includes('clinic') || spec.includes('ambulatory') || spec.includes('attending')) {
    return 'AT';
  }

  if (spec.includes('float') || spec.includes('backup') || spec.includes('reserve')) {
    return 'RESERVE';
  }

  // Distribute remaining faculty across lanes based on index
  const lanes: LaneType[] = ['AT', 'FMIT', 'FMIT'];
  return lanes[index % lanes.length];
}

// ============================================================================
// Mock Data Generator (Fallback)
// ============================================================================

/**
 * Generate mock data when API data is unavailable.
 * Used for demonstration and development.
 */
export function generateMockData(): {
  faculty: BottleneckFaculty[];
  trainees: BottleneckTrainee[];
} {
  // 10 Faculty: 4 AT, 4 FMIT, 2 Reserve
  const faculty: BottleneckFaculty[] = [
    // AT Faculty (4)
    { id: 'F001', name: 'Dr. Alpha', lane: 'AT', specialty: 'FM Clinic', traineeIds: ['R001', 'R002'], isDisabled: false },
    { id: 'F002', name: 'Dr. Bravo', lane: 'AT', specialty: 'FM Clinic', traineeIds: ['R003', 'R004'], isDisabled: false },
    { id: 'F003', name: 'Dr. Charlie', lane: 'AT', specialty: 'Inpatient', traineeIds: ['R05', 'R06'], isDisabled: false },
    { id: 'F004', name: 'Dr. Delta', lane: 'AT', specialty: 'Geriatrics', traineeIds: ['R07', 'R08'], isDisabled: false },
    // FMIT Faculty (4)
    { id: 'F005', name: 'Dr. Echo', lane: 'FMIT', specialty: 'FMIT Lead', traineeIds: ['R09', 'R10'], isDisabled: false },
    { id: 'F006', name: 'Dr. Foxtrot', lane: 'FMIT', specialty: 'OB/Peds', traineeIds: ['R11', 'R12'], isDisabled: false },
    { id: 'F007', name: 'Dr. Golf', lane: 'FMIT', specialty: 'Sports Med', traineeIds: ['R13', 'R14'], isDisabled: false },
    { id: 'F008', name: 'Dr. Hotel', lane: 'FMIT', specialty: 'Behavioral', traineeIds: ['R15', 'R16', 'R17'], isDisabled: false },
    // Reserve Faculty (2)
    { id: 'F009', name: 'Dr. India', lane: 'RESERVE', specialty: 'Float', traineeIds: [], isDisabled: false },
    { id: 'F010', name: 'Dr. Juliet', lane: 'RESERVE', specialty: 'Backup', traineeIds: [], isDisabled: false },
  ];

  // 17 Trainees: 6 PGY-1 (interns), 6 PGY-2, 5 PGY-3 (11 residents total)
  const trainees: BottleneckTrainee[] = [
    // PGY-1 Interns (6)
    { id: 'R001', name: 'Int. Kilo', pgy: 1, primaryFacultyId: 'F001', backupFacultyId: 'F009' },
    { id: 'R003', name: 'Int. Lima', pgy: 1, primaryFacultyId: 'F002', backupFacultyId: 'F009' },
    { id: 'R05', name: 'Int. Mike', pgy: 1, primaryFacultyId: 'F003', backupFacultyId: 'F010' },
    { id: 'R07', name: 'Int. November', pgy: 1, primaryFacultyId: 'F004', backupFacultyId: 'F010' },
    { id: 'R09', name: 'Int. Oscar', pgy: 1, primaryFacultyId: 'F005', backupFacultyId: 'F009' },
    { id: 'R11', name: 'Int. Papa', pgy: 1, primaryFacultyId: 'F006', backupFacultyId: 'F010' },
    // PGY-2 Residents (6)
    { id: 'R002', name: 'Res. Quebec', pgy: 2, primaryFacultyId: 'F001', backupFacultyId: 'F002' },
    { id: 'R004', name: 'Res. Romeo', pgy: 2, primaryFacultyId: 'F002', backupFacultyId: 'F001' },
    { id: 'R06', name: 'Res. Sierra', pgy: 2, primaryFacultyId: 'F003', backupFacultyId: 'F004' },
    { id: 'R08', name: 'Res. Tango', pgy: 2, primaryFacultyId: 'F004', backupFacultyId: 'F003' },
    { id: 'R10', name: 'Res. Uniform', pgy: 2, primaryFacultyId: 'F005', backupFacultyId: 'F006' },
    { id: 'R12', name: 'Res. Victor', pgy: 2, primaryFacultyId: 'F006', backupFacultyId: 'F005' },
    // PGY-3 Residents (5)
    { id: 'R13', name: 'Res. Whiskey', pgy: 3, primaryFacultyId: 'F007', backupFacultyId: 'F008' },
    { id: 'R14', name: 'Res. X-Ray', pgy: 3, primaryFacultyId: 'F007', backupFacultyId: 'F006' },
    { id: 'R15', name: 'Res. Yankee', pgy: 3, primaryFacultyId: 'F008', backupFacultyId: 'F007' },
    { id: 'R16', name: 'Res. Zulu', pgy: 3, primaryFacultyId: 'F008', backupFacultyId: 'F005' },
    { id: 'R17', name: 'Res. Alpha-2', pgy: 3, primaryFacultyId: 'F008', backupFacultyId: 'F009' },
  ];

  return { faculty, trainees };
}

// ============================================================================
// Data Transform
// ============================================================================

/**
 * Transform API roster data to bottleneck visualization format.
 *
 * @param facultyList - Faculty members from useFaculty() hook
 * @param residentList - Residents from useResidents() hook
 * @returns Transformed data ready for visualization
 *
 * @example
 * ```tsx
 * const { data: facultyData } = useFaculty();
 * const { data: residentsData } = useResidents();
 *
 * const { faculty, trainees } = useMemo(() => {
 *   return transformToBottleneckData(facultyData?.items, residentsData?.items);
 * }, [facultyData, residentsData]);
 * ```
 */
export function transformToBottleneckData(
  facultyList?: Person[],
  residentList?: Person[]
): { faculty: BottleneckFaculty[]; trainees: BottleneckTrainee[] } {
  // Fallback to mock data if API data unavailable
  if (!facultyList?.length || !residentList?.length) {
    return generateMockData();
  }

  // Transform faculty with lane assignment
  const faculty: BottleneckFaculty[] = facultyList.map((f, idx) => {
    const specialty = Array.isArray(f.specialties) ? f.specialties[0] : null;

    return {
      id: f.id,
      name: maskPersonName(idx, true),
      lane: determineLane(specialty, idx),
      specialty: specialty || 'Family Medicine',
      traineeIds: [], // Populated below
      isDisabled: false,
    };
  });

  // Separate by lane for assignment logic
  const nonReserveFaculty = faculty.filter((f) => f.lane !== 'RESERVE');
  const reserveFaculty = faculty.filter((f) => f.lane === 'RESERVE');

  // Transform residents with supervision assignments
  const trainees: BottleneckTrainee[] = residentList.map((r, idx) => {
    // Constrain PGY to 1-3 for visualization sizing
    const pgy = Math.min(3, Math.max(1, r.pgyLevel || 1)) as 1 | 2 | 3;

    // Assign primary supervisor (round-robin among non-reserve faculty)
    const primaryIdx = idx % (nonReserveFaculty.length || 1);
    const primaryFaculty = nonReserveFaculty[primaryIdx] || faculty[0];

    // Assign backup supervisor (prefer reserve, fallback to different non-reserve)
    let backupFaculty: BottleneckFaculty;
    if (reserveFaculty.length > 0) {
      backupFaculty = reserveFaculty[idx % reserveFaculty.length];
    } else {
      const backupIdx = (primaryIdx + 1) % (nonReserveFaculty.length || 1);
      backupFaculty = nonReserveFaculty[backupIdx] || faculty[0];
    }

    // Update faculty trainee lists
    if (primaryFaculty) {
      primaryFaculty.traineeIds.push(r.id);
    }

    return {
      id: r.id,
      name: maskPersonName(idx, false),
      pgy,
      primaryFacultyId: primaryFaculty?.id || '',
      backupFacultyId: backupFaculty?.id || '',
    };
  });

  return { faculty, trainees };
}

// ============================================================================
// Hook
// ============================================================================

/**
 * Hook for transforming and memoizing bottleneck data.
 *
 * @param facultyData - Response from useFaculty() hook
 * @param residentsData - Response from useResidents() hook
 * @returns Memoized visualization data
 */
export function useBottleneckData(
  facultyData: { items: Person[] } | undefined,
  residentsData: { items: Person[] } | undefined
): { faculty: BottleneckFaculty[]; trainees: BottleneckTrainee[] } {
  return useMemo(() => {
    return transformToBottleneckData(facultyData?.items, residentsData?.items);
  }, [facultyData, residentsData]);
}
