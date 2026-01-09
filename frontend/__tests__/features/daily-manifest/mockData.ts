/**
 * Mock Data for Daily Manifest Tests
 *
 * Provides factory functions and mock responses for testing the daily manifest feature.
 */

import type {
  PersonAssignment,
  LocationManifest,
  DailyManifestData,
} from '@/features/daily-manifest/types';

// ============================================================================
// Factory Functions
// ============================================================================

export const manifestMockFactories = {
  /**
   * Create a mock person assignment
   */
  personAssignment: (overrides: Partial<PersonAssignment> = {}): PersonAssignment => ({
    person: {
      id: 'person-1',
      name: 'Dr. John Smith',
      pgyLevel: 2,
      roleType: 'resident',
    },
    role: 'Primary Care',
    activity: 'Outpatient Clinic',
    assignmentId: 'assign-1',
    rotationName: 'Family Medicine',
    ...overrides,
  }),

  /**
   * Create a mock location manifest
   */
  locationManifest: (overrides: Partial<LocationManifest> = {}): LocationManifest => ({
    clinicLocation: 'Main Clinic',
    timeSlots: {
      AM: [
        manifestMockFactories.personAssignment({
          person: { id: 'person-1', name: 'Dr. John Smith', pgyLevel: 2, roleType: 'resident' },
        }),
        manifestMockFactories.personAssignment({
          person: { id: 'person-2', name: 'Dr. Jane Doe', pgyLevel: 3, roleType: 'resident' },
        }),
      ],
      PM: [
        manifestMockFactories.personAssignment({
          person: { id: 'person-3', name: 'Dr. Bob Johnson', roleType: 'faculty' },
        }),
      ],
    },
    staffingSummary: {
      total: 3,
      residents: 2,
      faculty: 1,
      fellows: 0,
    },
    capacity: {
      current: 3,
      maximum: 5,
    },
    ...overrides,
  }),

  /**
   * Create a mock daily manifest data response
   */
  dailyManifestData: (overrides: Partial<DailyManifestData> = {}): DailyManifestData => ({
    date: '2025-12-21',
    timeOfDay: 'AM',
    locations: [
      manifestMockFactories.locationManifest(),
      manifestMockFactories.locationManifest({
        clinicLocation: 'South Clinic',
        timeSlots: {
          AM: [
            manifestMockFactories.personAssignment({
              person: { id: 'person-4', name: 'Dr. Sarah Wilson', pgyLevel: 1, roleType: 'resident' },
            }),
          ],
        },
        staffingSummary: {
          total: 1,
          residents: 1,
          faculty: 0,
          fellows: 0,
        },
      }),
    ],
    generatedAt: '2025-12-21T10:30:00Z',
    summary: {
      totalLocations: 2,
      totalStaff: 4,
      totalResidents: 3,
      totalFaculty: 1,
    },
    ...overrides,
  }),
};

// ============================================================================
// Mock Responses
// ============================================================================

export const manifestMockResponses = {
  /**
   * Standard daily manifest response with multiple locations
   */
  dailyManifest: manifestMockFactories.dailyManifestData(),

  /**
   * Empty manifest (no locations)
   */
  emptyManifest: manifestMockFactories.dailyManifestData({
    locations: [],
    summary: {
      totalLocations: 0,
      totalStaff: 0,
      totalResidents: 0,
      totalFaculty: 0,
    },
  }),

  /**
   * Manifest with over-capacity location
   */
  overCapacityManifest: manifestMockFactories.dailyManifestData({
    locations: [
      manifestMockFactories.locationManifest({
        clinicLocation: 'Busy Clinic',
        capacity: {
          current: 6,
          maximum: 5,
        },
        staffingSummary: {
          total: 6,
          residents: 4,
          faculty: 2,
          fellows: 0,
        },
      }),
    ],
  }),

  /**
   * Manifest with near-capacity location
   */
  nearCapacityManifest: manifestMockFactories.dailyManifestData({
    locations: [
      manifestMockFactories.locationManifest({
        clinicLocation: 'Almost Full Clinic',
        capacity: {
          current: 5,
          maximum: 5,
        },
      }),
    ],
  }),

  /**
   * Manifest with fellows
   */
  manifestWithFellows: manifestMockFactories.dailyManifestData({
    locations: [
      manifestMockFactories.locationManifest({
        clinicLocation: 'Academic Center',
        timeSlots: {
          AM: [
            manifestMockFactories.personAssignment({
              person: { id: 'fellow-1', name: 'Dr. Fellow One', roleType: 'fellow' },
            }),
            manifestMockFactories.personAssignment({
              person: { id: 'fellow-2', name: 'Dr. Fellow Two', roleType: 'fellow' },
            }),
          ],
        },
        staffingSummary: {
          total: 2,
          residents: 0,
          faculty: 0,
          fellows: 2,
        },
      }),
    ],
    summary: {
      totalLocations: 1,
      totalStaff: 2,
      totalResidents: 0,
      totalFaculty: 0,
    },
  }),

  /**
   * Manifest with location without capacity info
   */
  manifestWithoutCapacity: manifestMockFactories.dailyManifestData({
    locations: [
      manifestMockFactories.locationManifest({
        clinicLocation: 'No Capacity Tracking',
        capacity: undefined,
      }),
    ],
  }),

  /**
   * Manifest for ALL time period
   */
  allDayManifest: manifestMockFactories.dailyManifestData({
    timeOfDay: 'ALL',
    locations: [
      manifestMockFactories.locationManifest({
        clinicLocation: 'All Day Clinic',
        timeSlots: {
          AM: [
            manifestMockFactories.personAssignment({
              person: { id: 'person-1', name: 'Dr. Morning Person', roleType: 'resident' },
            }),
          ],
          PM: [
            manifestMockFactories.personAssignment({
              person: { id: 'person-2', name: 'Dr. Evening Person', roleType: 'resident' },
            }),
          ],
        },
      }),
    ],
  }),
};
