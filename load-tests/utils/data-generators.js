/**
 * Test Data Generators for k6 Load Tests
 *
 * Generates realistic test data for load testing the Residency Scheduler.
 * Includes generators for people, assignments, absences, and other entities.
 *
 * @module utils/data-generators
 */

import { randomIntBetween, randomItem } from 'k6';

/**
 * Common first names for test data
 */
const FIRST_NAMES = [
  'John', 'Jane', 'Michael', 'Sarah', 'David', 'Emily', 'Chris', 'Jessica',
  'Daniel', 'Ashley', 'Matthew', 'Amanda', 'Andrew', 'Melissa', 'Joshua',
  'Stephanie', 'Ryan', 'Nicole', 'Brandon', 'Jennifer', 'Tyler', 'Rachel',
  'Kevin', 'Laura', 'Justin', 'Rebecca', 'Aaron', 'Michelle', 'Steven',
];

/**
 * Common last names for test data
 */
const LAST_NAMES = [
  'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller',
  'Davis', 'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Wilson',
  'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee',
  'Thompson', 'White', 'Harris', 'Sanchez', 'Clark', 'Lewis', 'Robinson',
];

/**
 * Medical specialties for faculty
 */
const SPECIALTIES = [
  'Family Medicine',
  'Internal Medicine',
  'Emergency Medicine',
  'Sports Medicine',
  'Geriatrics',
  'Pediatrics',
  'Women\'s Health',
  'Dermatology',
  'Preventive Medicine',
  'Pain Management',
];

/**
 * Primary duties for faculty
 */
const PRIMARY_DUTIES = [
  'Clinical Care',
  'Teaching',
  'Research',
  'Administration',
  'Clinical Care & Teaching',
  'Teaching & Research',
];

/**
 * Rotation types
 */
const ROTATION_TYPES = [
  'Clinic',
  'Inpatient',
  'Procedures',
  'Conference',
  'Admin',
  'Research',
  'Elective',
];

/**
 * Absence types
 */
const ABSENCE_TYPES = [
  'Medical Leave',
  'Military Deployment',
  'TDY (Temporary Duty)',
  'Conference',
  'Vacation',
  'Family Emergency',
  'Sick Leave',
  'Maternity/Paternity Leave',
];

/**
 * Generate a random full name
 *
 * @returns {string} Full name
 */
export function generateName() {
  const firstName = randomItem(FIRST_NAMES);
  const lastName = randomItem(LAST_NAMES);
  return `${firstName} ${lastName}`;
}

/**
 * Generate a random email from a name
 *
 * @param {string} name - Full name
 * @returns {string} Email address
 */
export function generateEmail(name) {
  const normalized = name.toLowerCase().replace(/\s+/g, '.');
  const domain = randomItem(['test.com', 'example.com', 'loadtest.org']);
  const timestamp = Date.now();
  return `${normalized}.${timestamp}@${domain}`;
}

/**
 * Generate a random date between two dates
 *
 * @param {Date} start - Start date
 * @param {Date} end - End date
 * @returns {string} ISO date string (YYYY-MM-DD)
 */
export function randomDate(start, end) {
  const startTime = start.getTime();
  const endTime = end.getTime();
  const randomTime = startTime + Math.random() * (endTime - startTime);
  const date = new Date(randomTime);
  return date.toISOString().split('T')[0];
}

/**
 * Generate a random date range
 *
 * @param {number} minDays - Minimum duration in days
 * @param {number} maxDays - Maximum duration in days
 * @returns {Object} Object with start_date and end_date
 */
export function generateDateRange(minDays = 1, maxDays = 30) {
  const today = new Date();
  const futureDate = new Date(today.getTime() + 90 * 24 * 60 * 60 * 1000); // 90 days from now

  const startDate = randomDate(today, futureDate);
  const start = new Date(startDate);

  const duration = randomIntBetween(minDays, maxDays);
  const end = new Date(start.getTime() + duration * 24 * 60 * 60 * 1000);

  return {
    start_date: startDate,
    end_date: end.toISOString().split('T')[0],
  };
}

/**
 * Generate random person data (resident or faculty)
 *
 * @param {string} type - Person type ('resident' or 'faculty')
 * @returns {Object} Person data object
 */
export function generatePerson(type = null) {
  const personType = type || randomItem(['resident', 'faculty']);
  const name = generateName();
  const email = generateEmail(name);

  const basePerson = {
    name: name,
    type: personType,
    email: email,
  };

  if (personType === 'resident') {
    return {
      ...basePerson,
      pgy_level: randomIntBetween(1, 3),
      target_clinical_blocks: randomIntBetween(40, 56),
    };
  } else {
    // Faculty
    const numSpecialties = randomIntBetween(1, 3);
    const specialties = [];
    for (let i = 0; i < numSpecialties; i++) {
      const specialty = randomItem(SPECIALTIES);
      if (!specialties.includes(specialty)) {
        specialties.push(specialty);
      }
    }

    return {
      ...basePerson,
      performs_procedures: Math.random() > 0.5,
      specialties: specialties,
      primary_duty: randomItem(PRIMARY_DUTIES),
    };
  }
}

/**
 * Generate random resident data
 *
 * @returns {Object} Resident data object
 */
export function generateResident() {
  return generatePerson('resident');
}

/**
 * Generate random faculty data
 *
 * @returns {Object} Faculty data object
 */
export function generateFaculty() {
  return generatePerson('faculty');
}

/**
 * Generate random assignment data
 * Note: Requires existing person_id and block_id
 *
 * @param {string} personId - Person UUID
 * @param {string} blockId - Block UUID
 * @param {string} rotationType - Rotation type (optional)
 * @returns {Object} Assignment data object
 */
export function generateAssignment(personId, blockId, rotationType = null) {
  return {
    person_id: personId,
    block_id: blockId,
    rotation_type: rotationType || randomItem(ROTATION_TYPES),
    notes: Math.random() > 0.7 ? 'Auto-generated test assignment' : null,
  };
}

/**
 * Generate random absence/deployment data
 *
 * @param {string} personId - Person UUID
 * @param {number} minDays - Minimum duration in days (default: 1)
 * @param {number} maxDays - Maximum duration in days (default: 14)
 * @returns {Object} Absence data object
 */
export function generateAbsence(personId, minDays = 1, maxDays = 14) {
  const dateRange = generateDateRange(minDays, maxDays);
  const absenceType = randomItem(ABSENCE_TYPES);

  return {
    person_id: personId,
    start_date: dateRange.start_date,
    end_date: dateRange.end_date,
    absence_type: absenceType,
    reason: `${absenceType} - Load test data`,
    approved: Math.random() > 0.3, // 70% approved
  };
}

/**
 * Generate random deployment data (military-specific absence)
 *
 * @param {string} personId - Person UUID
 * @returns {Object} Deployment data object
 */
export function generateDeployment(personId) {
  const dateRange = generateDateRange(30, 180); // Deployments are longer

  return {
    person_id: personId,
    start_date: dateRange.start_date,
    end_date: dateRange.end_date,
    absence_type: randomItem(['Military Deployment', 'TDY (Temporary Duty)']),
    reason: 'Military deployment - Load test data',
    approved: true, // Deployments are typically pre-approved
  };
}

/**
 * Generate random swap request data
 *
 * @param {string} requesterId - Requester person UUID
 * @param {string} assignmentId - Assignment UUID to swap
 * @param {string} targetPersonId - Target person UUID (optional for absorb type)
 * @returns {Object} Swap request data object
 */
export function generateSwapRequest(requesterId, assignmentId, targetPersonId = null) {
  const swapType = targetPersonId ? 'one_to_one' : 'absorb';

  const baseSwap = {
    requester_id: requesterId,
    assignment_id: assignmentId,
    swap_type: swapType,
    reason: 'Load test swap request',
  };

  if (targetPersonId) {
    baseSwap.target_person_id = targetPersonId;
  }

  return baseSwap;
}

/**
 * Generate random certification data
 *
 * @param {string} personId - Person UUID
 * @returns {Object} Certification data object
 */
export function generateCertification(personId) {
  const certifications = [
    'ACLS (Advanced Cardiovascular Life Support)',
    'BLS (Basic Life Support)',
    'PALS (Pediatric Advanced Life Support)',
    'ATLS (Advanced Trauma Life Support)',
    'Board Certified - Family Medicine',
    'DEA License',
    'State Medical License',
  ];

  const dateRange = generateDateRange(365, 730); // Valid for 1-2 years

  return {
    person_id: personId,
    certification_name: randomItem(certifications),
    certification_number: `CERT-${randomIntBetween(10000, 99999)}`,
    issued_date: dateRange.start_date,
    expiration_date: dateRange.end_date,
    verified: Math.random() > 0.2, // 80% verified
  };
}

/**
 * Generate random procedure credential data
 *
 * @param {string} personId - Person UUID
 * @returns {Object} Procedure credential data object
 */
export function generateProcedureCredential(personId) {
  const procedures = [
    'Joint Injection',
    'Laceration Repair',
    'IUD Insertion',
    'Colposcopy',
    'Endometrial Biopsy',
    'Skin Biopsy',
    'Abscess I&D',
    'Vasectomy',
    'Trigger Point Injection',
  ];

  return {
    person_id: personId,
    procedure_name: randomItem(procedures),
    competency_level: randomItem(['Beginner', 'Intermediate', 'Advanced', 'Expert']),
    completed_count: randomIntBetween(0, 50),
    required_count: randomIntBetween(10, 30),
    last_performed_date: randomDate(new Date(Date.now() - 90 * 24 * 60 * 60 * 1000), new Date()),
  };
}

/**
 * Generate batch of people
 *
 * @param {number} count - Number of people to generate
 * @param {string} type - Person type ('resident', 'faculty', or null for mixed)
 * @returns {Array} Array of person data objects
 */
export function generatePeopleBatch(count, type = null) {
  const people = [];
  for (let i = 0; i < count; i++) {
    people.push(generatePerson(type));
  }
  return people;
}

/**
 * Generate unique test identifier
 * Useful for creating unique names/emails during parallel test execution
 *
 * @param {string} prefix - Prefix for the identifier
 * @returns {string} Unique identifier
 */
export function generateTestId(prefix = 'test') {
  const timestamp = Date.now();
  const random = randomIntBetween(1000, 9999);
  const vuId = __VU; // k6 virtual user ID
  const iterId = __ITER; // k6 iteration number
  return `${prefix}_${vuId}_${iterId}_${timestamp}_${random}`;
}

/**
 * Generate realistic schedule preferences
 *
 * @returns {Object} Schedule preference data
 */
export function generateSchedulePreferences() {
  return {
    preferred_rotations: randomItem([
      ['Clinic', 'Procedures'],
      ['Inpatient', 'Emergency Medicine'],
      ['Research', 'Conference'],
      ['Clinic', 'Admin'],
    ]),
    max_consecutive_days: randomIntBetween(5, 10),
    preferred_weekends_off: randomIntBetween(1, 2),
    avoid_back_to_back: Math.random() > 0.5,
  };
}

/**
 * Generate random query parameters for list endpoints
 *
 * @param {Object} options - Options for query generation
 * @returns {string} URL query string
 */
export function generateListQueryParams(options = {}) {
  const params = new URLSearchParams();

  // Pagination
  if (options.includePagination !== false) {
    params.append('skip', randomIntBetween(0, 100));
    params.append('limit', randomItem([10, 20, 50, 100]));
  }

  // Sorting
  if (options.includeSorting && Math.random() > 0.5) {
    params.append('sort_by', randomItem(['name', 'created_at', 'updated_at']));
    params.append('sort_order', randomItem(['asc', 'desc']));
  }

  // Filtering
  if (options.includeFilters && Math.random() > 0.5) {
    if (options.entityType === 'person') {
      params.append('type', randomItem(['resident', 'faculty']));
    }
  }

  return params.toString();
}

/**
 * Pick random items from an array
 *
 * @param {Array} array - Source array
 * @param {number} count - Number of items to pick
 * @returns {Array} Array of random items
 */
export function pickRandomItems(array, count) {
  const shuffled = [...array].sort(() => 0.5 - Math.random());
  return shuffled.slice(0, Math.min(count, array.length));
}

/**
 * Generate realistic ACGME compliance test data
 *
 * @param {string} personId - Person UUID
 * @returns {Object} ACGME compliance data
 */
export function generateACGMETestData(personId) {
  return {
    person_id: personId,
    week_start: randomDate(new Date(), new Date(Date.now() + 28 * 24 * 60 * 60 * 1000)),
    total_hours: randomIntBetween(40, 80),
    max_consecutive_hours: randomIntBetween(8, 24),
    days_off_in_week: randomIntBetween(0, 2),
  };
}

/**
 * Generate schedule generation request payload
 * @returns {object} Schedule generation request
 */
export function generateScheduleRequest() {
  const startDate = new Date();
  startDate.setDate(startDate.getDate() + randomIntBetween(1, 30));

  const endDate = new Date(startDate);
  endDate.setDate(endDate.getDate() + randomIntBetween(30, 365));

  return {
    start_date: startDate.toISOString().split('T')[0],
    end_date: endDate.toISOString().split('T')[0],
    optimize: randomItem([true, false]),
    enforce_acgme: true,  // Always enforce compliance
    algorithm: randomItem(['greedy', 'constraint_satisfaction', 'genetic']),
    max_iterations: randomIntBetween(100, 1000),
  };
}

/**
 * Generate assignment filter parameters
 * @returns {object} Query parameters for assignment filtering
 */
export function generateAssignmentFilters() {
  const filters = {};

  if (Math.random() > 0.5) {
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - randomIntBetween(0, 30));
    filters.start_date = startDate.toISOString().split('T')[0];
  }

  if (Math.random() > 0.5) {
    const endDate = new Date();
    endDate.setDate(endDate.getDate() + randomIntBetween(1, 60));
    filters.end_date = endDate.toISOString().split('T')[0];
  }

  if (Math.random() > 0.7) {
    filters.rotation_id = randomIntBetween(1, 20);
  }

  return filters;
}

/**
 * Generate person filter parameters
 * @returns {object} Query parameters for person filtering
 */
export function generatePersonFilters() {
  const roles = ['ADMIN', 'COORDINATOR', 'FACULTY', 'RESIDENT', 'CLINICAL_STAFF', 'RN', 'LPN', 'MSA'];
  const filters = {};

  if (Math.random() > 0.6) {
    filters.role = randomItem(roles);
  }

  if (Math.random() > 0.8) {
    filters.active = randomItem([true, false]);
  }

  return filters;
}

/**
 * Generate block filter parameters
 * @returns {object} Query parameters for block filtering
 */
export function generateBlockFilters() {
  const filters = {};

  const date = new Date();
  date.setDate(date.getDate() + randomIntBetween(-30, 60));
  filters.date = date.toISOString().split('T')[0];

  if (Math.random() > 0.7) {
    filters.session = randomItem(['AM', 'PM']);
  }

  return filters;
}

/**
 * Generate pagination parameters
 * @returns {object} Pagination params (skip, limit)
 */
export function generatePagination() {
  const limit = randomItem([10, 20, 50, 100]);
  const skip = randomIntBetween(0, 5) * limit;  // Random page

  return { skip, limit };
}

/**
 * Convert object to URL query string
 * @param {object} params - Query parameters
 * @returns {string} URL query string
 */
export function toQueryString(params) {
  const parts = [];
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null) {
      parts.push(`${encodeURIComponent(key)}=${encodeURIComponent(value)}`);
    }
  }
  return parts.length > 0 ? `?${parts.join('&')}` : '';
}

/**
 * Generate realistic think time (pause between user actions)
 * @param {number} min - Minimum seconds
 * @param {number} max - Maximum seconds
 * @returns {number} Sleep duration in seconds
 */
export function thinkTime(min = 1, max = 3) {
  return min + Math.random() * (max - min);
}

/**
 * Alias for randomItem from k6 for backward compatibility
 * @param {Array} arr - Array to pick from
 * @returns {*} Random element
 */
export function randomElement(arr) {
  return randomItem(arr);
}

/**
 * Export all generators
 */
export default {
  generateName,
  generateEmail,
  randomDate,
  generateDateRange,
  generatePerson,
  generateResident,
  generateFaculty,
  generateAssignment,
  generateAbsence,
  generateDeployment,
  generateSwapRequest,
  generateCertification,
  generateProcedureCredential,
  generatePeopleBatch,
  generateTestId,
  generateSchedulePreferences,
  generateListQueryParams,
  pickRandomItems,
  generateACGMETestData,
  generateScheduleRequest,
  generateAssignmentFilters,
  generatePersonFilters,
  generateBlockFilters,
  generatePagination,
  toQueryString,
  thinkTime,
  randomElement,
};
