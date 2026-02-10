/**
 * Tests for useAbsences hooks.
 *
 * Tests cover:
 * - Query key structure
 * - useAbsence: single absence fetch
 * - useAbsenceList: filtered absence listing
 * - useAbsences: simplified person-filtered fetch
 * - useLeaveCalendar: calendar view query
 * - useMilitaryLeave: military leave with client-side filtering
 * - useLeaveBalance: leave balance query
 * - useAbsenceCreate: absence creation mutation
 * - useAbsenceUpdate: absence update mutation
 * - useAbsenceDelete: absence deletion mutation
 * - useAbsenceApprove: approval/rejection mutation
 * - useAwayComplianceDashboard: compliance dashboard query
 * - useAwayFromProgramSummary: individual compliance summary
 * - useAwayThresholdCheck: threshold preview query
 * - Error handling
 */

import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';

import {
  useAbsence,
  useAbsenceList,
  useAbsences,
  useLeaveCalendar,
  useMilitaryLeave,
  useLeaveBalance,
  useAbsenceCreate,
  useAbsenceUpdate,
  useAbsenceDelete,
  useAbsenceApprove,
  useAwayComplianceDashboard,
  useAwayFromProgramSummary,
  useAwayThresholdCheck,
  absenceQueryKeys,
  awayComplianceQueryKeys,
} from '../useAbsences';

// ============================================================================
// Mocks
// ============================================================================

jest.mock('@/lib/api', () => ({
  get: jest.fn(),
  post: jest.fn(),
  put: jest.fn(),
  del: jest.fn(),
}));

import { get, post, put, del } from '@/lib/api';

const mockGet = get as jest.Mock;
const mockPost = post as jest.Mock;
const mockPut = put as jest.Mock;
const mockDel = del as jest.Mock;

// ============================================================================
// Test Setup
// ============================================================================

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
      mutations: { retry: false },
    },
  });

  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  };
}

// ============================================================================
// Test Data
// ============================================================================

const mockAbsence = {
  id: 'abs-1',
  personId: 'person-1',
  startDate: '2025-07-01',
  endDate: '2025-07-14',
  absenceType: 'vacation',
  isAwayFromProgram: true,
  deploymentOrders: false,
  tdyLocation: null,
  replacementActivity: null,
  notes: 'Annual leave',
  createdAt: '2025-06-01T00:00:00Z',
};

const mockDeploymentAbsence = {
  ...mockAbsence,
  id: 'abs-2',
  absenceType: 'deployment',
  deploymentOrders: true,
  startDate: '2025-08-01',
  endDate: '2025-12-01',
};

const mockTdyAbsence = {
  ...mockAbsence,
  id: 'abs-3',
  absenceType: 'tdy',
  tdyLocation: 'Fort Bragg',
  startDate: '2025-09-01',
  endDate: '2025-09-15',
};

const mockConferenceAbsence = {
  ...mockAbsence,
  id: 'abs-4',
  absenceType: 'conference',
  startDate: '2025-10-01',
  endDate: '2025-10-03',
};

const mockListResponse = {
  items: [mockAbsence, mockDeploymentAbsence, mockTdyAbsence, mockConferenceAbsence],
  total: 4,
};

const mockLeaveCalendarResponse = {
  startDate: '2025-07-01',
  endDate: '2025-07-31',
  entries: [
    {
      facultyId: 'person-1',
      facultyName: 'Dr. Smith',
      leave_type: 'vacation',
      startDate: '2025-07-01',
      endDate: '2025-07-14',
      is_blocking: true,
      has_fmit_conflict: false,
    },
  ],
  conflictCount: 0,
};

const mockLeaveBalance = {
  personId: 'person-1',
  personName: 'Dr. Smith',
  vacation_days: 15,
  sick_days: 10,
  personal_days: 3,
  total_days_taken: 5,
  total_days_allocated: 30,
};

const mockAwaySummary = {
  personId: 'person-1',
  academicYear: '2025-2026',
  daysUsed: 10,
  daysRemaining: 18,
  thresholdStatus: 'ok' as const,
  maxDays: 28,
  warningDays: 21,
  absences: [],
};

const mockAwayCheck = {
  currentDays: 10,
  projectedDays: 17,
  thresholdStatus: 'ok' as const,
  daysRemaining: 11,
  maxDays: 28,
  warningDays: 21,
};

const mockAllResidentsAway = {
  academicYear: '2025-2026',
  residents: [mockAwaySummary],
  summary: {
    totalResidents: 1,
    byStatus: { ok: 1, warning: 0, critical: 0, exceeded: 0 },
  },
};

// ============================================================================
// Query Keys Tests
// ============================================================================

describe('absenceQueryKeys', () => {
  it('should have correct base key', () => {
    expect(absenceQueryKeys.all()).toEqual(['absences']);
  });

  it('should generate correct list key', () => {
    expect(absenceQueryKeys.lists()).toEqual(['absences', 'list']);
  });

  it('should generate correct list key with filters', () => {
    const filters = { personId: 'person-1', absenceType: 'vacation' };
    expect(absenceQueryKeys.list(filters)).toEqual([
      'absences', 'list', filters,
    ]);
  });

  it('should generate correct detail key', () => {
    expect(absenceQueryKeys.detail('abs-1')).toEqual([
      'absences', 'detail', 'abs-1',
    ]);
  });

  it('should generate correct balance key', () => {
    expect(absenceQueryKeys.balance('person-1')).toEqual([
      'absences', 'balance', 'person-1',
    ]);
  });

  it('should generate correct calendar key', () => {
    expect(absenceQueryKeys.calendar('2025-07-01', '2025-07-31')).toEqual([
      'absences', 'calendar', '2025-07-01', '2025-07-31',
    ]);
  });

  it('should generate correct military key', () => {
    expect(absenceQueryKeys.military()).toEqual(['absences', 'military']);
  });
});

describe('awayComplianceQueryKeys', () => {
  it('should have correct base key', () => {
    expect(awayComplianceQueryKeys.all()).toEqual(['away-compliance']);
  });

  it('should generate correct dashboard key', () => {
    expect(awayComplianceQueryKeys.dashboard(2025)).toEqual([
      'away-compliance', 'dashboard', 2025,
    ]);
  });

  it('should generate correct summary key', () => {
    expect(awayComplianceQueryKeys.summary('person-1', 2025)).toEqual([
      'away-compliance', 'summary', 'person-1', 2025,
    ]);
  });

  it('should generate correct check key', () => {
    expect(awayComplianceQueryKeys.check('person-1', 7, 2025)).toEqual([
      'away-compliance', 'check', 'person-1', 7, 2025,
    ]);
  });
});

// ============================================================================
// useAbsence Tests
// ============================================================================

describe('useAbsence', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch a single absence', async () => {
    mockGet.mockResolvedValueOnce(mockAbsence);

    const { result } = renderHook(() => useAbsence('abs-1'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockGet).toHaveBeenCalledWith('/absences/abs-1');
    expect(result.current.data?.id).toBe('abs-1');
    expect(result.current.data?.absenceType).toBe('vacation');
  });

  it('should not fetch when id is empty', () => {
    const { result } = renderHook(() => useAbsence(''), {
      wrapper: createWrapper(),
    });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.isFetching).toBe(false);
    expect(mockGet).not.toHaveBeenCalled();
  });

  it('should handle error', async () => {
    mockGet.mockRejectedValueOnce({ message: 'Not found', status: 404 });

    const { result } = renderHook(() => useAbsence('nonexistent'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });
  });
});

// ============================================================================
// useAbsenceList Tests
// ============================================================================

describe('useAbsenceList', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch absences without filters', async () => {
    mockGet.mockResolvedValueOnce(mockListResponse);

    const { result } = renderHook(() => useAbsenceList(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockGet).toHaveBeenCalledWith('/absences');
    expect(result.current.data?.items).toHaveLength(4);
    expect(result.current.data?.total).toBe(4);
  });

  it('should pass filters as query params', async () => {
    mockGet.mockResolvedValueOnce(mockListResponse);

    const { result } = renderHook(
      () =>
        useAbsenceList({
          personId: 'person-1',
          startDate: '2025-07-01',
          endDate: '2025-12-31',
          absenceType: 'vacation',
        }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    const url = mockGet.mock.calls[0][0] as string;
    expect(url).toContain('person_id=person-1');
    expect(url).toContain('start_date=2025-07-01');
    expect(url).toContain('end_date=2025-12-31');
    expect(url).toContain('absence_type=vacation');
  });
});

// ============================================================================
// useAbsences Tests (simplified hook)
// ============================================================================

describe('useAbsences', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch absences without person filter', async () => {
    mockGet.mockResolvedValueOnce(mockListResponse);

    const { result } = renderHook(() => useAbsences(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockGet).toHaveBeenCalledWith('/absences');
  });

  it('should fetch absences with person filter', async () => {
    mockGet.mockResolvedValueOnce(mockListResponse);

    const { result } = renderHook(() => useAbsences(42), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockGet).toHaveBeenCalledWith('/absences?person_id=42');
  });
});

// ============================================================================
// useLeaveCalendar Tests
// ============================================================================

describe('useLeaveCalendar', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch leave calendar', async () => {
    mockGet.mockResolvedValueOnce(mockLeaveCalendarResponse);

    const { result } = renderHook(
      () => useLeaveCalendar('2025-07-01', '2025-07-31'),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockGet).toHaveBeenCalledWith(
      '/leave/calendar?start_date=2025-07-01&end_date=2025-07-31'
    );
    expect(result.current.data?.entries).toHaveLength(1);
    expect(result.current.data?.conflictCount).toBe(0);
  });

  it('should not fetch when start date is empty', () => {
    const { result } = renderHook(
      () => useLeaveCalendar('', '2025-07-31'),
      { wrapper: createWrapper() }
    );

    expect(result.current.isLoading).toBe(false);
    expect(result.current.isFetching).toBe(false);
    expect(mockGet).not.toHaveBeenCalled();
  });

  it('should not fetch when end date is empty', () => {
    const { result } = renderHook(
      () => useLeaveCalendar('2025-07-01', ''),
      { wrapper: createWrapper() }
    );

    expect(result.current.isLoading).toBe(false);
    expect(result.current.isFetching).toBe(false);
    expect(mockGet).not.toHaveBeenCalled();
  });
});

// ============================================================================
// useMilitaryLeave Tests
// ============================================================================

describe('useMilitaryLeave', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch and filter to only military leave types', async () => {
    mockGet.mockResolvedValueOnce(mockListResponse);

    const { result } = renderHook(() => useMilitaryLeave(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockGet).toHaveBeenCalledWith('/absences');

    // Should filter out vacation and conference, keep deployment and tdy
    expect(result.current.data?.items).toHaveLength(2);
    expect(result.current.data?.items[0].absenceType).toBe('deployment');
    expect(result.current.data?.items[1].absenceType).toBe('tdy');
    expect(result.current.data?.total).toBe(2);
  });

  it('should pass personId as query param', async () => {
    mockGet.mockResolvedValueOnce({
      items: [mockDeploymentAbsence],
      total: 1,
    });

    const { result } = renderHook(() => useMilitaryLeave('person-1'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockGet).toHaveBeenCalledWith('/absences?person_id=person-1');
  });
});

// ============================================================================
// useLeaveBalance Tests
// ============================================================================

describe('useLeaveBalance', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch leave balance', async () => {
    mockGet.mockResolvedValueOnce(mockLeaveBalance);

    const { result } = renderHook(() => useLeaveBalance('person-1'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockGet).toHaveBeenCalledWith('/absences/balance/person-1');
    expect(result.current.data?.vacation_days).toBe(15);
    expect(result.current.data?.sick_days).toBe(10);
  });

  it('should not fetch when personId is empty', () => {
    const { result } = renderHook(() => useLeaveBalance(''), {
      wrapper: createWrapper(),
    });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.isFetching).toBe(false);
    expect(mockGet).not.toHaveBeenCalled();
  });
});

// ============================================================================
// useAbsenceCreate Tests
// ============================================================================

describe('useAbsenceCreate', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should create an absence', async () => {
    mockPost.mockResolvedValueOnce(mockAbsence);

    const { result } = renderHook(() => useAbsenceCreate(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        personId: 'person-1',
        startDate: '2025-07-01',
        endDate: '2025-07-14',
        absenceType: 'vacation',
      });
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockPost).toHaveBeenCalledWith('/absences', {
      personId: 'person-1',
      startDate: '2025-07-01',
      endDate: '2025-07-14',
      absenceType: 'vacation',
    });
    expect(result.current.data?.id).toBe('abs-1');
  });

  it('should handle overlap conflict error', async () => {
    mockPost.mockRejectedValueOnce({
      message: 'Overlapping absence',
      status: 409,
    });

    const { result } = renderHook(() => useAbsenceCreate(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        personId: 'person-1',
        startDate: '2025-07-01',
        endDate: '2025-07-14',
        absenceType: 'vacation',
      });
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });
  });

  it('should create a deployment absence with military fields', async () => {
    mockPost.mockResolvedValueOnce(mockDeploymentAbsence);

    const { result } = renderHook(() => useAbsenceCreate(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        personId: 'person-1',
        startDate: '2025-08-01',
        endDate: '2025-12-01',
        absenceType: 'deployment',
        deploymentOrders: true,
        notes: 'Overseas deployment',
      });
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockPost).toHaveBeenCalledWith('/absences', expect.objectContaining({
      absenceType: 'deployment',
      deploymentOrders: true,
    }));
  });
});

// ============================================================================
// useAbsenceUpdate Tests
// ============================================================================

describe('useAbsenceUpdate', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should update an absence', async () => {
    const updated = { ...mockAbsence, endDate: '2025-07-21' };
    mockPut.mockResolvedValueOnce(updated);

    const { result } = renderHook(() => useAbsenceUpdate(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        id: 'abs-1',
        data: { endDate: '2025-07-21' },
      });
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockPut).toHaveBeenCalledWith('/absences/abs-1', {
      endDate: '2025-07-21',
    });
    expect(result.current.data?.endDate).toBe('2025-07-21');
  });
});

// ============================================================================
// useAbsenceDelete Tests
// ============================================================================

describe('useAbsenceDelete', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should delete an absence', async () => {
    mockDel.mockResolvedValueOnce(undefined);

    const { result } = renderHook(() => useAbsenceDelete(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate('abs-1');
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockDel).toHaveBeenCalledWith('/absences/abs-1');
  });

  it('should handle deletion error', async () => {
    mockDel.mockRejectedValueOnce({ message: 'Not found', status: 404 });

    const { result } = renderHook(() => useAbsenceDelete(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate('nonexistent');
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });
  });
});

// ============================================================================
// useAbsenceApprove Tests
// ============================================================================

describe('useAbsenceApprove', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should approve an absence', async () => {
    mockPost.mockResolvedValueOnce(mockAbsence);

    const { result } = renderHook(() => useAbsenceApprove(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        absence_id: 'abs-1',
        approved: true,
        comments: 'Adequate coverage available',
      });
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockPost).toHaveBeenCalledWith('/absences/abs-1/approve', {
      absence_id: 'abs-1',
      approved: true,
      comments: 'Adequate coverage available',
    });
  });

  it('should reject an absence', async () => {
    mockPost.mockResolvedValueOnce(mockAbsence);

    const { result } = renderHook(() => useAbsenceApprove(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        absence_id: 'abs-1',
        approved: false,
        comments: 'Insufficient coverage',
      });
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockPost).toHaveBeenCalledWith('/absences/abs-1/approve', {
      absence_id: 'abs-1',
      approved: false,
      comments: 'Insufficient coverage',
    });
  });
});

// ============================================================================
// useAwayComplianceDashboard Tests
// ============================================================================

describe('useAwayComplianceDashboard', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch compliance dashboard', async () => {
    mockGet.mockResolvedValueOnce(mockAllResidentsAway);

    const { result } = renderHook(
      () => useAwayComplianceDashboard(),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockGet).toHaveBeenCalledWith(
      '/absences/compliance/away-from-program'
    );
    expect(result.current.data?.residents).toHaveLength(1);
    expect(result.current.data?.summary.totalResidents).toBe(1);
  });

  it('should pass academic year as query param', async () => {
    mockGet.mockResolvedValueOnce(mockAllResidentsAway);

    const { result } = renderHook(
      () => useAwayComplianceDashboard(2025),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockGet).toHaveBeenCalledWith(
      '/absences/compliance/away-from-program?academic_year=2025'
    );
  });
});

// ============================================================================
// useAwayFromProgramSummary Tests
// ============================================================================

describe('useAwayFromProgramSummary', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch away-from-program summary', async () => {
    mockGet.mockResolvedValueOnce(mockAwaySummary);

    const { result } = renderHook(
      () => useAwayFromProgramSummary('person-1'),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockGet).toHaveBeenCalledWith(
      '/absences/residents/person-1/away-from-program'
    );
    expect(result.current.data?.daysUsed).toBe(10);
    expect(result.current.data?.thresholdStatus).toBe('ok');
  });

  it('should pass academic year param', async () => {
    mockGet.mockResolvedValueOnce(mockAwaySummary);

    const { result } = renderHook(
      () => useAwayFromProgramSummary('person-1', 2025),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockGet).toHaveBeenCalledWith(
      '/absences/residents/person-1/away-from-program?academic_year=2025'
    );
  });

  it('should not fetch when personId is empty', () => {
    const { result } = renderHook(
      () => useAwayFromProgramSummary(''),
      { wrapper: createWrapper() }
    );

    expect(result.current.isLoading).toBe(false);
    expect(result.current.isFetching).toBe(false);
    expect(mockGet).not.toHaveBeenCalled();
  });
});

// ============================================================================
// useAwayThresholdCheck Tests
// ============================================================================

describe('useAwayThresholdCheck', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should check threshold with additional days', async () => {
    mockGet.mockResolvedValueOnce(mockAwayCheck);

    const { result } = renderHook(
      () => useAwayThresholdCheck('person-1', 7),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    const url = mockGet.mock.calls[0][0] as string;
    expect(url).toContain('/absences/residents/person-1/away-from-program/check');
    expect(url).toContain('additional_days=7');

    expect(result.current.data?.currentDays).toBe(10);
    expect(result.current.data?.projectedDays).toBe(17);
    expect(result.current.data?.thresholdStatus).toBe('ok');
  });

  it('should pass academic year param', async () => {
    mockGet.mockResolvedValueOnce(mockAwayCheck);

    const { result } = renderHook(
      () => useAwayThresholdCheck('person-1', 7, 2025),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    const url = mockGet.mock.calls[0][0] as string;
    expect(url).toContain('additional_days=7');
    expect(url).toContain('academic_year=2025');
  });

  it('should not fetch when personId is empty', () => {
    const { result } = renderHook(
      () => useAwayThresholdCheck('', 7),
      { wrapper: createWrapper() }
    );

    expect(result.current.isLoading).toBe(false);
    expect(result.current.isFetching).toBe(false);
    expect(mockGet).not.toHaveBeenCalled();
  });
});
