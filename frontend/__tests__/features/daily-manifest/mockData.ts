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
      pgy_level: 2,
      role_type: 'resident',
    },
    role: 'Primary Care',
    activity: 'Outpatient Clinic',
    assignment_id: 'assign-1',
    rotation_name: 'Family Medicine',
    ...overrides,
  }),

  /**
   * Create a mock location manifest
   */
  locationManifest: (overrides: Partial<LocationManifest> = {}): LocationManifest => ({
    clinic_location: 'Main Clinic',
    time_slots: {
      AM: [
        manifestMockFactories.personAssignment({
          person: { id: 'person-1', name: 'Dr. John Smith', pgy_level: 2, role_type: 'resident' },
        }),
        manifestMockFactories.personAssignment({
          person: { id: 'person-2', name: 'Dr. Jane Doe', pgy_level: 3, role_type: 'resident' },
        }),
      ],
      PM: [
        manifestMockFactories.personAssignment({
          person: { id: 'person-3', name: 'Dr. Bob Johnson', role_type: 'faculty' },
        }),
      ],
    },
    staffing_summary: {
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
    time_of_day: 'AM',
    locations: [
      manifestMockFactories.locationManifest(),
      manifestMockFactories.locationManifest({
        clinic_location: 'South Clinic',
        time_slots: {
          AM: [
            manifestMockFactories.personAssignment({
              person: { id: 'person-4', name: 'Dr. Sarah Wilson', pgy_level: 1, role_type: 'resident' },
            }),
          ],
        },
        staffing_summary: {
          total: 1,
          residents: 1,
          faculty: 0,
          fellows: 0,
        },
      }),
    ],
    generated_at: '2025-12-21T10:30:00Z',
    summary: {
      total_locations: 2,
      total_staff: 4,
      total_residents: 3,
      total_faculty: 1,
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
      total_locations: 0,
      total_staff: 0,
      total_residents: 0,
      total_faculty: 0,
    },
  }),

  /**
   * Manifest with over-capacity location
   */
  overCapacityManifest: manifestMockFactories.dailyManifestData({
    locations: [
      manifestMockFactories.locationManifest({
        clinic_location: 'Busy Clinic',
        capacity: {
          current: 6,
          maximum: 5,
        },
        staffing_summary: {
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
        clinic_location: 'Almost Full Clinic',
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
        clinic_location: 'Academic Center',
        time_slots: {
          AM: [
            manifestMockFactories.personAssignment({
              person: { id: 'fellow-1', name: 'Dr. Fellow One', role_type: 'fellow' },
            }),
            manifestMockFactories.personAssignment({
              person: { id: 'fellow-2', name: 'Dr. Fellow Two', role_type: 'fellow' },
            }),
          ],
        },
        staffing_summary: {
          total: 2,
          residents: 0,
          faculty: 0,
          fellows: 2,
        },
      }),
    ],
    summary: {
      total_locations: 1,
      total_staff: 2,
      total_residents: 0,
      total_faculty: 0,
    },
  }),

  /**
   * Manifest with location without capacity info
   */
  manifestWithoutCapacity: manifestMockFactories.dailyManifestData({
    locations: [
      manifestMockFactories.locationManifest({
        clinic_location: 'No Capacity Tracking',
        capacity: undefined,
      }),
    ],
  }),

  /**
   * Manifest for ALL time period
   */
  allDayManifest: manifestMockFactories.dailyManifestData({
    time_of_day: 'ALL',
    locations: [
      manifestMockFactories.locationManifest({
        clinic_location: 'All Day Clinic',
        time_slots: {
          AM: [
            manifestMockFactories.personAssignment({
              person: { id: 'person-1', name: 'Dr. Morning Person', role_type: 'resident' },
            }),
          ],
          PM: [
            manifestMockFactories.personAssignment({
              person: { id: 'person-2', name: 'Dr. Evening Person', role_type: 'resident' },
            }),
          ],
        },
      }),
    ],
  }),
};
