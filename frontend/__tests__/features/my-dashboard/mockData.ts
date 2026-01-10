/**
 * Mock data for my-dashboard feature tests
 *
 * Provides realistic test data for dashboard components and hooks
 */

import type {
  DashboardData,
  UpcomingAssignment,
  PendingSwapSummary,
  AbsenceEntry,
  DashboardSummary,
} from '@/features/my-dashboard/types';
import { TimeOfDay, Location } from '@/features/my-dashboard/types';

// ============================================================================
// Mock User Data
// ============================================================================

export const mockUser = {
  id: 'user-123',
  name: 'Dr. John Smith',
  role: 'Resident (PGY-2)',
};

// ============================================================================
// Mock Upcoming Assignments
// ============================================================================

/**
 * Helper to get a local date string in YYYY-MM-DD format
 * This avoids timezone issues when comparing dates
 */
function getLocalDateString(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

/**
 * Helper to get a date offset from today in local timezone
 */
function getLocalDateOffset(daysOffset: number): string {
  const date = new Date();
  date.setDate(date.getDate() + daysOffset);
  return getLocalDateString(date);
}

export const mockAssignmentToday: UpcomingAssignment = {
  id: 'assignment-1',
  date: getLocalDateOffset(0), // Today in local timezone
  timeOfDay: TimeOfDay.AM,
  activity: 'Inpatient Medicine',
  location: Location.WARD,
  canTrade: true,
  isConflict: false,
};

export const mockAssignmentTomorrow: UpcomingAssignment = {
  id: 'assignment-2',
  date: getLocalDateOffset(1), // Tomorrow in local timezone
  timeOfDay: TimeOfDay.PM,
  activity: 'Emergency Department',
  location: Location.ER,
  canTrade: true,
  isConflict: false,
};

export const mockAssignmentNextWeek: UpcomingAssignment = {
  id: 'assignment-3',
  date: getLocalDateOffset(7), // Next week in local timezone
  timeOfDay: TimeOfDay.NIGHT,
  activity: 'ICU Coverage',
  location: Location.ICU,
  canTrade: false,
  isConflict: false,
};

export const mockAssignmentWithConflict: UpcomingAssignment = {
  id: 'assignment-4',
  date: '2025-02-15',
  timeOfDay: TimeOfDay.FULL_DAY,
  activity: 'Operating Room',
  location: Location.OR,
  canTrade: true,
  isConflict: true,
  conflictReason: 'Overlaps with approved vacation request',
};

export const mockAssignmentNotTradeable: UpcomingAssignment = {
  id: 'assignment-5',
  date: '2025-02-20',
  timeOfDay: TimeOfDay.AM,
  activity: 'Clinic',
  location: Location.CLINIC,
  canTrade: false,
  isConflict: false,
};

export const mockUpcomingAssignments: UpcomingAssignment[] = [
  mockAssignmentToday,
  mockAssignmentTomorrow,
  mockAssignmentNextWeek,
  mockAssignmentWithConflict,
  mockAssignmentNotTradeable,
];

// ============================================================================
// Mock Pending Swaps
// ============================================================================

export const mockIncomingSwapPending: PendingSwapSummary = {
  id: 'swap-1',
  type: 'incoming',
  otherFacultyName: 'Dr. Sarah Williams',
  weekDate: '2025-02-01',
  status: 'pending',
  requestedAt: '2025-01-15T10:30:00Z',
  reason: 'Family emergency - need to swap this week',
  canRespond: true,
};

export const mockOutgoingSwapPending: PendingSwapSummary = {
  id: 'swap-2',
  type: 'outgoing',
  otherFacultyName: 'Dr. Michael Chen',
  weekDate: '2025-02-08',
  status: 'pending',
  requestedAt: '2025-01-18T14:00:00Z',
  reason: 'Medical conference',
  canRespond: false,
};

export const mockIncomingSwapApproved: PendingSwapSummary = {
  id: 'swap-3',
  type: 'incoming',
  otherFacultyName: 'Dr. Emily Rodriguez',
  weekDate: '2025-01-25',
  status: 'approved',
  requestedAt: '2025-01-10T09:00:00Z',
  reason: 'Continuing education course',
  canRespond: false,
};

export const mockOutgoingSwapRejected: PendingSwapSummary = {
  id: 'swap-4',
  type: 'outgoing',
  otherFacultyName: 'Dr. David Lee',
  weekDate: '2025-03-01',
  status: 'rejected',
  requestedAt: '2025-01-20T11:15:00Z',
  reason: 'Schedule conflict',
  canRespond: false,
};

export const mockPendingSwaps: PendingSwapSummary[] = [
  mockIncomingSwapPending,
  mockOutgoingSwapPending,
  mockIncomingSwapApproved,
];

// ============================================================================
// Mock Absences
// ============================================================================

export const mockAbsence1: AbsenceEntry = {
  id: 'absence-1',
  startDate: '2025-03-10',
  endDate: '2025-03-14',
  reason: 'Vacation',
  status: 'approved',
  requestedAt: '2025-01-05T08:00:00Z',
};

export const mockAbsence2: AbsenceEntry = {
  id: 'absence-2',
  startDate: '2025-04-01',
  endDate: '2025-04-03',
  reason: 'Conference',
  status: 'pending',
  requestedAt: '2025-01-22T13:00:00Z',
};

export const mockAbsences: AbsenceEntry[] = [mockAbsence1, mockAbsence2];

// ============================================================================
// Mock Dashboard Summary
// ============================================================================

export const mockSummary: DashboardSummary = {
  nextAssignment: 'Today at 8 AM',
  workloadNext4Weeks: 12,
  pendingSwapCount: 2,
  upcomingAbsences: 2,
};

export const mockSummaryNoAssignments: DashboardSummary = {
  nextAssignment: null,
  workloadNext4Weeks: 0,
  pendingSwapCount: 0,
  upcomingAbsences: 0,
};

// ============================================================================
// Mock Complete Dashboard Data
// ============================================================================

export const mockDashboardData: DashboardData = {
  user: mockUser,
  upcomingSchedule: mockUpcomingAssignments,
  pendingSwaps: mockPendingSwaps,
  absences: mockAbsences,
  calendarSyncUrl: 'https://example.com/calendar/sync/token123',
  summary: mockSummary,
};

export const mockDashboardDataEmpty: DashboardData = {
  user: mockUser,
  upcomingSchedule: [],
  pendingSwaps: [],
  absences: [],
  calendarSyncUrl: '',
  summary: mockSummaryNoAssignments,
};

export const mockDashboardDataMinimal: DashboardData = {
  user: mockUser,
  upcomingSchedule: [mockAssignmentToday],
  pendingSwaps: [],
  absences: [],
  calendarSyncUrl: 'https://example.com/calendar/sync/token123',
  summary: {
    nextAssignment: 'Today at 8 AM',
    workloadNext4Weeks: 5,
    pendingSwapCount: 0,
    upcomingAbsences: 0,
  },
};

// ============================================================================
// Mock API Responses (backend format)
// ============================================================================

export const mockDashboardApiResponse = {
  user: {
    id: 'user-123',
    name: 'Dr. John Smith',
    role: 'Resident (PGY-2)',
  },
  upcomingSchedule: [
    {
      id: 'assignment-1',
      date: getLocalDateOffset(0), // Today in local timezone
      timeOfDay: 'AM',
      activity: 'Inpatient Medicine',
      location: 'Ward',
      canTrade: true,
      isConflict: false,
    },
    {
      id: 'assignment-2',
      date: getLocalDateOffset(1), // Tomorrow in local timezone
      timeOfDay: 'PM',
      activity: 'Emergency Department',
      location: 'ER',
      canTrade: true,
      isConflict: false,
    },
  ],
  pendingSwaps: [
    {
      id: 'swap-1',
      sourceFacultyId: 'faculty-1',
      sourceFacultyName: 'Dr. Sarah Williams',
      targetFacultyId: 'user-123',
      targetFacultyName: 'Dr. John Smith',
      sourceWeek: '2025-02-01',
      targetWeek: '2025-02-08',
      status: 'pending',
      requestedAt: '2025-01-15T10:30:00Z',
      reason: 'Family emergency - need to swap this week',
    },
  ],
  absences: [
    {
      id: 'absence-1',
      startDate: '2025-03-10',
      endDate: '2025-03-14',
      reason: 'Vacation',
      status: 'approved',
      requestedAt: '2025-01-05T08:00:00Z',
    },
  ],
  calendarSyncUrl: 'https://example.com/calendar/sync/token123',
  summary: {
    nextAssignment: 'Today at 8 AM',
    workloadNext4Weeks: 12,
    pendingSwapCount: 2,
    upcomingAbsences: 2,
  },
};

export const mockCalendarSyncResponse = {
  success: true,
  url: 'https://example.com/calendar/download/token123.ics',
  message: 'Calendar sync successful',
};

export const mockSwapRequestResponse = {
  success: true,
  message: 'Swap request created successfully',
};

// ============================================================================
// Mock Data Factories
// ============================================================================

export const mockFactories = {
  assignment: (overrides: Partial<UpcomingAssignment> = {}): UpcomingAssignment => ({
    id: `assignment-${Math.random().toString(36).substr(2, 9)}`,
    date: '2025-02-15',
    timeOfDay: TimeOfDay.AM,
    activity: 'General Ward',
    location: Location.WARD,
    canTrade: true,
    isConflict: false,
    ...overrides,
  }),

  pendingSwap: (overrides: Partial<PendingSwapSummary> = {}): PendingSwapSummary => ({
    id: `swap-${Math.random().toString(36).substr(2, 9)}`,
    type: 'incoming',
    otherFacultyName: 'Dr. Test',
    weekDate: '2025-02-01',
    status: 'pending',
    requestedAt: new Date().toISOString(),
    canRespond: true,
    ...overrides,
  }),

  absence: (overrides: Partial<AbsenceEntry> = {}): AbsenceEntry => ({
    id: `absence-${Math.random().toString(36).substr(2, 9)}`,
    startDate: '2025-03-01',
    endDate: '2025-03-03',
    reason: 'Vacation',
    status: 'pending',
    requestedAt: new Date().toISOString(),
    ...overrides,
  }),

  dashboardData: (overrides: Partial<DashboardData> = {}): DashboardData => ({
    user: mockUser,
    upcomingSchedule: [],
    pendingSwaps: [],
    absences: [],
    calendarSyncUrl: '',
    summary: mockSummaryNoAssignments,
    ...overrides,
  }),
};
