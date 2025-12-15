import type {
  Person,
  Block,
  Assignment,
  RotationTemplate,
  Absence,
  ValidationResult,
  Violation,
} from '../../frontend/src/types/api';

// ============================================================================
// Mock People Data
// ============================================================================

export const mockResidents: Person[] = [
  {
    id: 'resident-1',
    name: 'Dr. Sarah Johnson',
    email: 'sarah.johnson@example.com',
    type: 'resident',
    pgy_level: 1,
    performs_procedures: true,
    specialties: ['Emergency Medicine'],
    primary_duty: 'Clinical',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'resident-2',
    name: 'Dr. Michael Chen',
    email: 'michael.chen@example.com',
    type: 'resident',
    pgy_level: 1,
    performs_procedures: true,
    specialties: ['Emergency Medicine'],
    primary_duty: 'Clinical',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'resident-3',
    name: 'Dr. Emily Rodriguez',
    email: 'emily.rodriguez@example.com',
    type: 'resident',
    pgy_level: 2,
    performs_procedures: true,
    specialties: ['Emergency Medicine', 'Trauma'],
    primary_duty: 'Clinical',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'resident-4',
    name: 'Dr. James Williams',
    email: 'james.williams@example.com',
    type: 'resident',
    pgy_level: 2,
    performs_procedures: true,
    specialties: ['Emergency Medicine'],
    primary_duty: 'Clinical',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'resident-5',
    name: 'Dr. Ashley Martinez',
    email: 'ashley.martinez@example.com',
    type: 'resident',
    pgy_level: 3,
    performs_procedures: true,
    specialties: ['Emergency Medicine', 'Trauma', 'Critical Care'],
    primary_duty: 'Clinical',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'resident-6',
    name: 'Dr. David Kim',
    email: 'david.kim@example.com',
    type: 'resident',
    pgy_level: 3,
    performs_procedures: true,
    specialties: ['Emergency Medicine', 'Ultrasound'],
    primary_duty: 'Clinical',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
];

export const mockFaculty: Person[] = [
  {
    id: 'faculty-1',
    name: 'Dr. Robert Thompson',
    email: 'robert.thompson@example.com',
    type: 'faculty',
    pgy_level: null,
    performs_procedures: true,
    specialties: ['Emergency Medicine', 'Medical Education'],
    primary_duty: 'Attending',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'faculty-2',
    name: 'Dr. Jennifer Davis',
    email: 'jennifer.davis@example.com',
    type: 'faculty',
    pgy_level: null,
    performs_procedures: true,
    specialties: ['Emergency Medicine', 'Ultrasound'],
    primary_duty: 'Attending',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'faculty-3',
    name: 'Dr. Patricia Garcia',
    email: 'patricia.garcia@example.com',
    type: 'faculty',
    pgy_level: null,
    performs_procedures: false,
    specialties: ['Emergency Medicine', 'Research'],
    primary_duty: 'Administrative',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
];

export const mockAllPeople: Person[] = [...mockResidents, ...mockFaculty];

// ============================================================================
// Mock Rotation Templates
// ============================================================================

export const mockRotationTemplates: RotationTemplate[] = [
  {
    id: 'rotation-1',
    name: 'Emergency Department',
    activity_type: 'inpatient',
    abbreviation: 'ED',
    clinic_location: 'Main Hospital',
    max_residents: 4,
    requires_specialty: null,
    requires_procedure_credential: false,
    supervision_required: true,
    max_supervision_ratio: 4,
    created_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'rotation-2',
    name: 'Trauma Center',
    activity_type: 'procedure',
    abbreviation: 'TRMA',
    clinic_location: 'Level 1 Trauma Center',
    max_residents: 2,
    requires_specialty: 'Trauma',
    requires_procedure_credential: true,
    supervision_required: true,
    max_supervision_ratio: 2,
    created_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'rotation-3',
    name: 'Outpatient Clinic',
    activity_type: 'clinic',
    abbreviation: 'OPC',
    clinic_location: 'Outpatient Building',
    max_residents: 3,
    requires_specialty: null,
    requires_procedure_credential: false,
    supervision_required: true,
    max_supervision_ratio: 3,
    created_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'rotation-4',
    name: 'Night Call',
    activity_type: 'call',
    abbreviation: 'CALL',
    clinic_location: 'Main Hospital',
    max_residents: 2,
    requires_specialty: null,
    requires_procedure_credential: false,
    supervision_required: true,
    max_supervision_ratio: 2,
    created_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'rotation-5',
    name: 'Conference',
    activity_type: 'conference',
    abbreviation: 'CONF',
    clinic_location: 'Conference Center',
    max_residents: null,
    requires_specialty: null,
    requires_procedure_credential: false,
    supervision_required: false,
    max_supervision_ratio: 10,
    created_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'rotation-6',
    name: 'Elective Rotation',
    activity_type: 'elective',
    abbreviation: 'ELEC',
    clinic_location: 'Various',
    max_residents: 1,
    requires_specialty: null,
    requires_procedure_credential: false,
    supervision_required: false,
    max_supervision_ratio: 1,
    created_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'rotation-7',
    name: 'Ultrasound Clinic',
    activity_type: 'procedure',
    abbreviation: 'US',
    clinic_location: 'Imaging Center',
    max_residents: 2,
    requires_specialty: 'Ultrasound',
    requires_procedure_credential: true,
    supervision_required: true,
    max_supervision_ratio: 2,
    created_at: '2024-01-01T00:00:00Z',
  },
];

// ============================================================================
// Mock Blocks
// ============================================================================

/**
 * Generate mock blocks for a date range
 * Creates blocks for each day with AM and PM sessions
 */
export function generateMockBlocks(
  startDate: Date,
  endDate: Date,
  blockNumberStart: number = 1
): Block[] {
  const blocks: Block[] = [];
  let blockNumber = blockNumberStart;
  const currentDate = new Date(startDate);

  while (currentDate <= endDate) {
    const dateStr = currentDate.toISOString().split('T')[0];
    const dayOfWeek = currentDate.getDay();
    const isWeekend = dayOfWeek === 0 || dayOfWeek === 6;

    // AM block
    blocks.push({
      id: `block-${blockNumber}-am`,
      date: dateStr,
      time_of_day: 'AM',
      block_number: blockNumber,
      is_weekend: isWeekend,
      is_holiday: false,
      holiday_name: null,
    });

    // PM block
    blocks.push({
      id: `block-${blockNumber}-pm`,
      date: dateStr,
      time_of_day: 'PM',
      block_number: blockNumber,
      is_weekend: isWeekend,
      is_holiday: false,
      holiday_name: null,
    });

    blockNumber++;
    currentDate.setDate(currentDate.getDate() + 1);
  }

  return blocks;
}

// ============================================================================
// Mock Assignments
// ============================================================================

/**
 * Generate mock assignments for testing
 */
export function generateMockAssignments(
  blocks: Block[],
  people: Person[],
  rotationTemplates: RotationTemplate[]
): Assignment[] {
  const assignments: Assignment[] = [];
  let assignmentId = 1;

  // Assign residents to rotations in a round-robin pattern
  blocks.forEach((block, index) => {
    const personIndex = index % people.length;
    const person = people[personIndex];
    const rotationIndex = index % rotationTemplates.length;
    const rotation = rotationTemplates[rotationIndex];

    assignments.push({
      id: `assignment-${assignmentId}`,
      block_id: block.id,
      person_id: person.id,
      rotation_template_id: rotation.id,
      role: 'primary',
      activity_override: null,
      notes: null,
      created_by: 'test-user',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    });

    assignmentId++;
  });

  return assignments;
}

// ============================================================================
// Mock Absences
// ============================================================================

export const mockAbsences: Absence[] = [
  {
    id: 'absence-1',
    person_id: 'resident-1',
    start_date: '2024-02-01',
    end_date: '2024-02-05',
    absence_type: 'vacation',
    deployment_orders: false,
    tdy_location: null,
    replacement_activity: null,
    notes: 'Planned vacation',
    created_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'absence-2',
    person_id: 'resident-3',
    start_date: '2024-02-10',
    end_date: '2024-02-12',
    absence_type: 'conference',
    deployment_orders: false,
    tdy_location: 'Las Vegas, NV',
    replacement_activity: null,
    notes: 'ACEP Conference',
    created_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'absence-3',
    person_id: 'resident-5',
    start_date: '2024-02-15',
    end_date: '2024-02-20',
    absence_type: 'deployment',
    deployment_orders: true,
    tdy_location: 'Fort Bragg, NC',
    replacement_activity: 'Military Training',
    notes: 'Annual deployment',
    created_at: '2024-01-01T00:00:00Z',
  },
];

// ============================================================================
// Mock ACGME Violations
// ============================================================================

export const mockViolations: Violation[] = [
  {
    type: 'HOURS_WEEKLY_LIMIT',
    severity: 'CRITICAL',
    person_id: 'resident-1',
    person_name: 'Dr. Sarah Johnson',
    block_id: 'block-10-pm',
    message: 'Weekly duty hours exceed 80-hour limit',
    details: {
      weekly_hours: 85,
      limit: 80,
      week_start: '2024-01-08',
      week_end: '2024-01-14',
    },
  },
  {
    type: 'SUPERVISION_REQUIRED',
    severity: 'CRITICAL',
    person_id: 'resident-2',
    person_name: 'Dr. Michael Chen',
    block_id: 'block-15-am',
    message: 'PGY-1 resident assigned to rotation requiring supervision without faculty',
    details: {
      rotation_name: 'Trauma Center',
      requires_supervision: true,
      supervisor_assigned: false,
    },
  },
  {
    type: 'REST_PERIOD',
    severity: 'HIGH',
    person_id: 'resident-3',
    person_name: 'Dr. Emily Rodriguez',
    block_id: 'block-20-am',
    message: 'Insufficient rest period between shifts',
    details: {
      rest_hours: 6,
      required_hours: 8,
      previous_shift_end: '2024-01-15T23:00:00Z',
      next_shift_start: '2024-01-16T05:00:00Z',
    },
  },
  {
    type: 'CONSECUTIVE_DAYS',
    severity: 'MEDIUM',
    person_id: 'resident-4',
    person_name: 'Dr. James Williams',
    block_id: 'block-25-pm',
    message: 'Working more than 6 consecutive days',
    details: {
      consecutive_days: 7,
      limit: 6,
      start_date: '2024-01-15',
      end_date: '2024-01-21',
    },
  },
  {
    type: 'SPECIALTY_MISMATCH',
    severity: 'LOW',
    person_id: 'resident-2',
    person_name: 'Dr. Michael Chen',
    block_id: 'block-30-am',
    message: 'Resident assigned to specialty rotation without required specialty credential',
    details: {
      rotation_name: 'Ultrasound Clinic',
      required_specialty: 'Ultrasound',
      person_specialties: ['Emergency Medicine'],
    },
  },
];

export const mockValidationResult: ValidationResult = {
  valid: false,
  total_violations: mockViolations.length,
  violations: mockViolations,
  coverage_rate: 0.92,
  statistics: {
    total_blocks: 280,
    assigned_blocks: 258,
    unassigned_blocks: 22,
    total_residents: 6,
    total_faculty: 3,
  },
};

// ============================================================================
// Mock API Responses
// ============================================================================

export const mockApiResponses = {
  people: {
    items: mockAllPeople,
    total: mockAllPeople.length,
  },
  rotationTemplates: {
    items: mockRotationTemplates,
    total: mockRotationTemplates.length,
  },
  absences: {
    items: mockAbsences,
    total: mockAbsences.length,
  },
};

// ============================================================================
// Test Helper Functions
// ============================================================================

/**
 * Create a mock schedule for a specific date range
 */
export function createMockSchedule(startDate: Date, endDate: Date) {
  const blocks = generateMockBlocks(startDate, endDate);
  const assignments = generateMockAssignments(blocks, mockResidents, mockRotationTemplates);

  return {
    blocks,
    assignments,
    people: mockAllPeople,
    rotationTemplates: mockRotationTemplates,
    absences: mockAbsences,
  };
}

/**
 * Get a specific person by ID
 */
export function getPersonById(id: string): Person | undefined {
  return mockAllPeople.find((p) => p.id === id);
}

/**
 * Get a specific rotation template by ID
 */
export function getRotationTemplateById(id: string): RotationTemplate | undefined {
  return mockRotationTemplates.find((r) => r.id === id);
}

/**
 * Filter assignments by person ID
 */
export function getAssignmentsByPerson(
  assignments: Assignment[],
  personId: string
): Assignment[] {
  return assignments.filter((a) => a.person_id === personId);
}

/**
 * Filter assignments by date range
 */
export function getAssignmentsByDateRange(
  assignments: Assignment[],
  blocks: Block[],
  startDate: string,
  endDate: string
): Assignment[] {
  const blocksInRange = blocks.filter((b) => b.date >= startDate && b.date <= endDate);
  const blockIds = new Set(blocksInRange.map((b) => b.id));
  return assignments.filter((a) => blockIds.has(a.block_id));
}
