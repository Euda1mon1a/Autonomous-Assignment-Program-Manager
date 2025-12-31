/**
 * Test Data Generators
 *
 * Generate realistic test data for load testing.
 */

import { randomIntBetween, randomItem, randomString } from 'k6';

/**
 * Generate random person data
 */
export function generatePerson(role = null) {
  const roles = ['ADMIN', 'COORDINATOR', 'FACULTY', 'RESIDENT', 'CLINICAL_STAFF', 'RN', 'LPN', 'MSA'];
  const pgyYears = [1, 2, 3, 4];

  const firstName = randomItem([
    'John', 'Jane', 'Michael', 'Sarah', 'David', 'Emily',
    'Robert', 'Jennifer', 'William', 'Lisa', 'James', 'Mary'
  ]);

  const lastName = randomItem([
    'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia',
    'Miller', 'Davis', 'Rodriguez', 'Martinez', 'Hernandez', 'Lopez'
  ]);

  const selectedRole = role || randomItem(roles);
  const email = `${firstName.toLowerCase()}.${lastName.toLowerCase()}@test.com`;

  const person = {
    first_name: firstName,
    last_name: lastName,
    email: email,
    role: selectedRole,
    is_active: true
  };

  // Add PGY year for residents
  if (selectedRole === 'RESIDENT') {
    person.pgy_year = randomItem(pgyYears);
  }

  return person;
}

/**
 * Generate random rotation data
 */
export function generateRotation() {
  const types = ['CLINIC', 'INPATIENT', 'PROCEDURES', 'CONFERENCE', 'ADMIN', 'CALL'];
  const names = {
    CLINIC: ['Family Medicine Clinic', 'Pediatrics Clinic', 'Internal Medicine Clinic'],
    INPATIENT: ['General Medicine', 'ICU', 'Emergency Department'],
    PROCEDURES: ['Procedures Lab', 'OR Rotation', 'Endoscopy'],
    CONFERENCE: ['Grand Rounds', 'Case Conference', 'Journal Club'],
    ADMIN: ['Administrative Time', 'Research', 'Quality Improvement'],
    CALL: ['Night Call', 'Weekend Call', 'Holiday Call']
  };

  const type = randomItem(types);
  const name = randomItem(names[type]);

  return {
    name: name,
    rotation_type: type,
    is_active: true,
    requires_supervision: type === 'PROCEDURES' || type === 'INPATIENT',
    max_consecutive_days: type === 'CALL' ? 7 : 14,
    color: generateRandomColor()
  };
}

/**
 * Generate random block data
 */
export function generateBlock(startDate = null) {
  const start = startDate || generateRandomDate();
  const sessionTypes = ['AM', 'PM', 'FULL_DAY', 'CALL'];

  return {
    date: start,
    session_type: randomItem(sessionTypes),
    is_holiday: Math.random() < 0.05,  // 5% chance of holiday
    is_weekend: new Date(start).getDay() % 6 === 0  // Saturday or Sunday
  };
}

/**
 * Generate random assignment data
 */
export function generateAssignment(personId, blockId, rotationId) {
  return {
    person_id: personId,
    block_id: blockId,
    rotation_id: rotationId,
    status: randomItem(['SCHEDULED', 'CONFIRMED', 'COMPLETED']),
    notes: Math.random() < 0.2 ? 'Generated for load test' : null
  };
}

/**
 * Generate random swap request
 */
export function generateSwapRequest(requestorId, targetPersonId = null) {
  const types = ['ONE_TO_ONE', 'ABSORB', 'SPLIT'];
  const statuses = ['PENDING', 'APPROVED', 'REJECTED'];

  const swap = {
    requestor_id: requestorId,
    swap_type: randomItem(types),
    status: randomItem(statuses),
    reason: randomItem([
      'Personal emergency',
      'Medical appointment',
      'Family obligation',
      'Conference attendance',
      'Research commitment'
    ])
  };

  if (targetPersonId && swap.swap_type === 'ONE_TO_ONE') {
    swap.target_person_id = targetPersonId;
  }

  return swap;
}

/**
 * Generate random date within range
 */
export function generateRandomDate(startDate = null, daysRange = 365) {
  const start = startDate ? new Date(startDate) : new Date();
  const randomDays = randomIntBetween(0, daysRange);
  const date = new Date(start);
  date.setDate(date.getDate() + randomDays);
  return date.toISOString().split('T')[0];  // YYYY-MM-DD
}

/**
 * Generate date range
 */
export function generateDateRange(startDate = null, days = 7) {
  const start = startDate || new Date().toISOString().split('T')[0];
  const dates = [];

  for (let i = 0; i < days; i++) {
    const date = new Date(start);
    date.setDate(date.getDate() + i);
    dates.push(date.toISOString().split('T')[0]);
  }

  return dates;
}

/**
 * Generate random color
 */
export function generateRandomColor() {
  const colors = [
    '#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8',
    '#F7DC6F', '#BB8FCE', '#85C1E2', '#F8B739', '#52B788'
  ];
  return randomItem(colors);
}

/**
 * Generate random email
 */
export function generateEmail(prefix = null) {
  const prefixStr = prefix || randomString(8);
  const domains = ['test.com', 'example.com', 'loadtest.com'];
  return `${prefixStr}@${randomItem(domains)}`;
}

/**
 * Generate random phone number
 */
export function generatePhoneNumber() {
  const area = randomIntBetween(200, 999);
  const prefix = randomIntBetween(200, 999);
  const line = randomIntBetween(1000, 9999);
  return `${area}-${prefix}-${line}`;
}

/**
 * Generate schedule generation request
 */
export function generateScheduleRequest(academicYear = null) {
  const year = academicYear || new Date().getFullYear();
  const startDate = `${year}-07-01`;  // Academic year starts July 1
  const endDate = `${year + 1}-06-30`;  // Ends June 30 next year

  return {
    start_date: startDate,
    end_date: endDate,
    algorithm: randomItem(['GREEDY', 'CONSTRAINT_PROGRAMMING', 'HYBRID']),
    optimization_goals: randomItem([
      ['MINIMIZE_VIOLATIONS', 'BALANCE_WORKLOAD'],
      ['MAXIMIZE_PREFERENCES', 'MINIMIZE_CONFLICTS'],
      ['BALANCE_WORKLOAD', 'MINIMIZE_CHANGES']
    ]),
    max_runtime_seconds: randomIntBetween(30, 300),
    include_weekends: true,
    include_holidays: true
  };
}

/**
 * Generate compliance validation request
 */
export function generateComplianceRequest(personId, startDate, endDate) {
  return {
    person_id: personId,
    start_date: startDate,
    end_date: endDate,
    rules: randomItem([
      ['EIGHTY_HOUR_RULE', 'ONE_IN_SEVEN_RULE'],
      ['EIGHTY_HOUR_RULE', 'ONE_IN_SEVEN_RULE', 'SUPERVISION_RATIO'],
      ['EIGHTY_HOUR_RULE']
    ])
  };
}

/**
 * Generate bulk assignment data
 */
export function generateBulkAssignments(count = 10) {
  const assignments = [];

  for (let i = 0; i < count; i++) {
    assignments.push({
      person_id: `person-${randomIntBetween(1, 100)}`,
      block_id: `block-${randomIntBetween(1, 730)}`,
      rotation_id: `rotation-${randomIntBetween(1, 20)}`,
      status: 'SCHEDULED'
    });
  }

  return assignments;
}

/**
 * Generate search query
 */
export function generateSearchQuery() {
  const queries = [
    'John',
    'Clinic',
    'Call',
    'Emergency',
    'ICU',
    'Resident',
    'Faculty',
    '2024',
    'Inpatient'
  ];

  return randomItem(queries);
}

/**
 * Generate pagination params
 */
export function generatePaginationParams() {
  const skip = randomIntBetween(0, 100);
  const limit = randomItem([10, 20, 50, 100]);

  return { skip, limit };
}

/**
 * Generate filter params
 */
export function generateFilterParams() {
  const filters = {};

  // Random filters
  if (Math.random() < 0.3) {
    filters.role = randomItem(['RESIDENT', 'FACULTY', 'ADMIN']);
  }

  if (Math.random() < 0.3) {
    filters.is_active = randomItem([true, false]);
  }

  if (Math.random() < 0.3) {
    filters.start_date = generateRandomDate();
  }

  return filters;
}

/**
 * Generate sort params
 */
export function generateSortParams() {
  const sortFields = ['created_at', 'updated_at', 'name', 'date', 'role'];
  const sortOrders = ['asc', 'desc'];

  return {
    sort_by: randomItem(sortFields),
    sort_order: randomItem(sortOrders)
  };
}

/**
 * Generate realistic work schedule
 */
export function generateWorkSchedule(personId, startDate, days = 7) {
  const schedule = [];
  const rotationIds = ['rotation-1', 'rotation-2', 'rotation-3'];

  for (let i = 0; i < days; i++) {
    const date = new Date(startDate);
    date.setDate(date.getDate() + i);
    const dateStr = date.toISOString().split('T')[0];

    // Skip some days (days off)
    if (Math.random() < 0.15) continue;

    schedule.push({
      person_id: personId,
      date: dateStr,
      rotation_id: randomItem(rotationIds),
      session_type: randomItem(['AM', 'PM', 'FULL_DAY'])
    });
  }

  return schedule;
}

/**
 * Generate resilience metrics request
 */
export function generateResilienceRequest() {
  return {
    analysis_type: randomItem(['N_MINUS_ONE', 'UTILIZATION', 'BURNOUT_RISK']),
    time_window_days: randomItem([7, 14, 30, 90]),
    include_projections: Math.random() < 0.5,
    threshold_utilization: 0.80
  };
}

/**
 * Generate batch of random IDs
 */
export function generateIds(prefix, count) {
  const ids = [];
  for (let i = 0; i < count; i++) {
    ids.push(`${prefix}-${randomIntBetween(1, 10000)}`);
  }
  return ids;
}

/**
 * Generate realistic test scenario
 */
export function generateTestScenario() {
  return {
    persons: Array.from({ length: 50 }, () => generatePerson()),
    rotations: Array.from({ length: 10 }, () => generateRotation()),
    blocks: Array.from({ length: 100 }, () => generateBlock()),
    assignments: Array.from({ length: 200 }, () =>
      generateAssignment(
        `person-${randomIntBetween(1, 50)}`,
        `block-${randomIntBetween(1, 100)}`,
        `rotation-${randomIntBetween(1, 10)}`
      )
    )
  };
}

export default {
  generatePerson,
  generateRotation,
  generateBlock,
  generateAssignment,
  generateSwapRequest,
  generateRandomDate,
  generateDateRange,
  generateRandomColor,
  generateEmail,
  generatePhoneNumber,
  generateScheduleRequest,
  generateComplianceRequest,
  generateBulkAssignments,
  generateSearchQuery,
  generatePaginationParams,
  generateFilterParams,
  generateSortParams,
  generateWorkSchedule,
  generateResilienceRequest,
  generateIds,
  generateTestScenario
};
