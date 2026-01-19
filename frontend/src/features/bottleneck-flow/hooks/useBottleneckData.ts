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
  const faculty: BottleneckFaculty[] = [
    // AT Faculty
    {
      id: 'F001',
      name: 'Dr. Alpha',
      lane: 'AT',
      specialty: 'FM Clinic',
      traineeIds: ['R001', 'R002', 'R003'],
      isDisabled: false,
    },
    {
      id: 'F002',
      name: 'Dr. Bravo',
      lane: 'AT',
      specialty: 'FM Clinic',
      traineeIds: ['R004', 'R005'],
      isDisabled: false,
    },
    {
      id: 'F003',
      name: 'Dr. Charlie',
      lane: 'AT',
      specialty: 'Inpatient',
      traineeIds: ['R006', 'R007', 'R008'],
      isDisabled: false,
    },
    // FMIT Faculty
    {
      id: 'F004',
      name: 'Dr. Delta',
      lane: 'FMIT',
      specialty: 'FMIT Lead',
      traineeIds: ['R009', 'R010', 'R011', 'R012'],
      isDisabled: false,
    },
    {
      id: 'F005',
      name: 'Dr. Echo',
      lane: 'FMIT',
      specialty: 'FMIT',
      traineeIds: ['R013', 'R014'],
      isDisabled: false,
    },
    {
      id: 'F006',
      name: 'Dr. Foxtrot',
      lane: 'FMIT',
      specialty: 'OB/Peds',
      traineeIds: ['R015', 'R016', 'R017'],
      isDisabled: false,
    },
    // Reserve Faculty
    {
      id: 'F007',
      name: 'Dr. Golf',
      lane: 'RESERVE',
      specialty: 'Float',
      traineeIds: [],
      isDisabled: false,
    },
    {
      id: 'F008',
      name: 'Dr. Hotel',
      lane: 'RESERVE',
      specialty: 'Backup',
      traineeIds: [],
      isDisabled: false,
    },
  ];

  const trainees: BottleneckTrainee[] = [
    // AT Trainees
    { id: 'R001', name: 'Res. India', pgy: 1, primaryFacultyId: 'F001', backupFacultyId: 'F007' },
    { id: 'R002', name: 'Res. Juliet', pgy: 2, primaryFacultyId: 'F001', backupFacultyId: 'F002' },
    { id: 'R003', name: 'Res. Kilo', pgy: 3, primaryFacultyId: 'F001', backupFacultyId: 'F002' },
    { id: 'R004', name: 'Res. Lima', pgy: 1, primaryFacultyId: 'F002', backupFacultyId: 'F007' },
    { id: 'R005', name: 'Res. Mike', pgy: 2, primaryFacultyId: 'F002', backupFacultyId: 'F001' },
    { id: 'R006', name: 'Res. November', pgy: 1, primaryFacultyId: 'F003', backupFacultyId: 'F008' },
    { id: 'R007', name: 'Res. Oscar', pgy: 2, primaryFacultyId: 'F003', backupFacultyId: 'F001' },
    { id: 'R008', name: 'Res. Papa', pgy: 3, primaryFacultyId: 'F003', backupFacultyId: 'F002' },
    // FMIT Trainees
    { id: 'R009', name: 'Res. Quebec', pgy: 1, primaryFacultyId: 'F004', backupFacultyId: 'F005' },
    { id: 'R010', name: 'Res. Romeo', pgy: 2, primaryFacultyId: 'F004', backupFacultyId: 'F005' },
    { id: 'R011', name: 'Res. Sierra', pgy: 3, primaryFacultyId: 'F004', backupFacultyId: 'F006' },
    { id: 'R012', name: 'Res. Tango', pgy: 1, primaryFacultyId: 'F004', backupFacultyId: 'F008' },
    { id: 'R013', name: 'Res. Uniform', pgy: 2, primaryFacultyId: 'F005', backupFacultyId: 'F004' },
    { id: 'R014', name: 'Res. Victor', pgy: 3, primaryFacultyId: 'F005', backupFacultyId: 'F006' },
    { id: 'R015', name: 'Res. Whiskey', pgy: 1, primaryFacultyId: 'F006', backupFacultyId: 'F008' },
    { id: 'R016', name: 'Res. X-Ray', pgy: 2, primaryFacultyId: 'F006', backupFacultyId: 'F004' },
    { id: 'R017', name: 'Res. Yankee', pgy: 3, primaryFacultyId: 'F006', backupFacultyId: 'F005' },
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
