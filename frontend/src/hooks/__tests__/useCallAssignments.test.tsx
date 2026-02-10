/**
 * Tests for useCallAssignments hooks.
 *
 * Tests cover:
 * - Query key structure
 * - useCallAssignments: list fetching with filters
 * - useCallAssignment: single call assignment fetch
 * - useCallAssignmentsByPerson: person-filtered queries
 * - useCallAssignmentsByDate: date-filtered queries
 * - useCreateCallAssignment: creation mutation
 * - useUpdateCallAssignment: update mutation
 * - useDeleteCallAssignment: deletion mutation
 * - useBulkUpdateCallAssignments: bulk update mutation
 * - useBulkDeleteCallAssignments: bulk delete mutation
 * - useGeneratePCAT: PCAT generation mutation
 * - useCoverageReport: coverage report query
 * - useEquityReport: equity report query
 * - useEquityPreview: equity preview mutation
 * - useClearPCATStatus: PCAT clear mutation
 * - Error handling
 */

import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';

import {
  useCallAssignments,
  useCallAssignment,
  useCallAssignmentsByPerson,
  useCallAssignmentsByDate,
  useCreateCallAssignment,
  useUpdateCallAssignment,
  useDeleteCallAssignment,
  useBulkUpdateCallAssignments,
  useBulkDeleteCallAssignments,
  useGeneratePCAT,
  useCoverageReport,
  useEquityReport,
  useEquityPreview,
  useClearPCATStatus,
  callAssignmentQueryKeys,
} from '../useCallAssignments';

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

const mockCallAssignment = {
  id: 'ca-1',
  date: '2025-06-15',
  personId: 'person-1',
  callType: 'overnight' as const,
  isWeekend: false,
  isHoliday: false,
  person: {
    id: 'person-1',
    name: 'Dr. Smith',
    facultyRole: 'core',
  },
};

const mockCallAssignment2 = {
  ...mockCallAssignment,
  id: 'ca-2',
  date: '2025-06-16',
};

const mockListResponse = {
  items: [mockCallAssignment, mockCallAssignment2],
  total: 2,
  skip: 0,
  limit: 100,
};

const mockCoverageReport = {
  startDate: '2025-06-01',
  endDate: '2025-06-30',
  totalExpectedNights: 30,
  coveredNights: 28,
  coveragePercentage: 93.3,
  gaps: ['2025-06-10', '2025-06-20'],
};

const mockEquityReport = {
  startDate: '2025-06-01',
  endDate: '2025-06-30',
  facultyCount: 5,
  totalOvernightCalls: 28,
  sundayCallStats: { min: 1, max: 3, mean: 2.0, stdev: 0.5 },
  weekdayCallStats: { min: 3, max: 7, mean: 5.0, stdev: 1.2 },
  distribution: [],
};

const mockPCATResponse = {
  processed: 2,
  pcatCreated: 2,
  doCreated: 2,
  errors: [],
  results: [],
};

// ============================================================================
// Query Keys Tests
// ============================================================================

describe('callAssignmentQueryKeys', () => {
  it('should have correct base key', () => {
    expect(callAssignmentQueryKeys.all).toEqual(['call-assignments']);
  });

  it('should generate correct list key with filters', () => {
    const filters = { startDate: '2025-06-01', callType: 'overnight' as const };
    expect(callAssignmentQueryKeys.list(filters)).toEqual([
      'call-assignments', 'list', filters,
    ]);
  });

  it('should generate correct detail key', () => {
    expect(callAssignmentQueryKeys.detail('ca-1')).toEqual([
      'call-assignments', 'detail', 'ca-1',
    ]);
  });

  it('should generate correct byPerson key', () => {
    expect(
      callAssignmentQueryKeys.byPerson('person-1', '2025-06-01', '2025-06-30')
    ).toEqual([
      'call-assignments', 'by-person', 'person-1', '2025-06-01', '2025-06-30',
    ]);
  });

  it('should generate correct byDate key', () => {
    expect(callAssignmentQueryKeys.byDate('2025-06-15')).toEqual([
      'call-assignments', 'by-date', '2025-06-15',
    ]);
  });

  it('should generate correct coverage key', () => {
    expect(
      callAssignmentQueryKeys.coverage('2025-06-01', '2025-06-30')
    ).toEqual([
      'call-assignments', 'coverage', '2025-06-01', '2025-06-30',
    ]);
  });

  it('should generate correct equity key', () => {
    expect(
      callAssignmentQueryKeys.equity('2025-06-01', '2025-06-30')
    ).toEqual([
      'call-assignments', 'equity', '2025-06-01', '2025-06-30',
    ]);
  });
});

// ============================================================================
// useCallAssignments Tests
// ============================================================================

describe('useCallAssignments', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch call assignments without filters', async () => {
    mockGet.mockResolvedValueOnce(mockListResponse);

    const { result } = renderHook(() => useCallAssignments(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockGet).toHaveBeenCalledWith('/call-assignments');
    expect(result.current.data?.items).toHaveLength(2);
    expect(result.current.data?.total).toBe(2);
  });

  it('should pass filters as query params', async () => {
    mockGet.mockResolvedValueOnce(mockListResponse);

    const { result } = renderHook(
      () =>
        useCallAssignments({
          startDate: '2025-06-01',
          endDate: '2025-06-30',
          personId: 'person-1',
          callType: 'overnight',
          skip: 0,
          limit: 50,
        }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    const url = mockGet.mock.calls[0][0] as string;
    expect(url).toContain('start_date=2025-06-01');
    expect(url).toContain('end_date=2025-06-30');
    expect(url).toContain('person_id=person-1');
    expect(url).toContain('call_type=overnight');
    expect(url).toContain('skip=0');
    expect(url).toContain('limit=50');
  });

  it('should handle error', async () => {
    mockGet.mockRejectedValueOnce({ message: 'Server error', status: 500 });

    const { result } = renderHook(() => useCallAssignments(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });
  });
});

// ============================================================================
// useCallAssignment Tests
// ============================================================================

describe('useCallAssignment', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch a single call assignment', async () => {
    mockGet.mockResolvedValueOnce(mockCallAssignment);

    const { result } = renderHook(() => useCallAssignment('ca-1'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockGet).toHaveBeenCalledWith('/call-assignments/ca-1');
    expect(result.current.data?.id).toBe('ca-1');
    expect(result.current.data?.callType).toBe('overnight');
  });

  it('should not fetch when id is empty', () => {
    const { result } = renderHook(() => useCallAssignment(''), {
      wrapper: createWrapper(),
    });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.isFetching).toBe(false);
    expect(mockGet).not.toHaveBeenCalled();
  });
});

// ============================================================================
// useCallAssignmentsByPerson Tests
// ============================================================================

describe('useCallAssignmentsByPerson', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch call assignments by person', async () => {
    mockGet.mockResolvedValueOnce(mockListResponse);

    const { result } = renderHook(
      () => useCallAssignmentsByPerson('person-1', '2025-06-01', '2025-06-30'),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    const url = mockGet.mock.calls[0][0] as string;
    expect(url).toContain('/call-assignments/by-person/person-1');
    expect(url).toContain('start_date=2025-06-01');
    expect(url).toContain('end_date=2025-06-30');
  });

  it('should not fetch when personId is empty', () => {
    const { result } = renderHook(
      () => useCallAssignmentsByPerson(''),
      { wrapper: createWrapper() }
    );

    expect(result.current.isLoading).toBe(false);
    expect(result.current.isFetching).toBe(false);
    expect(mockGet).not.toHaveBeenCalled();
  });

  it('should fetch without date range params when not provided', async () => {
    mockGet.mockResolvedValueOnce(mockListResponse);

    const { result } = renderHook(
      () => useCallAssignmentsByPerson('person-1'),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockGet).toHaveBeenCalledWith(
      '/call-assignments/by-person/person-1'
    );
  });
});

// ============================================================================
// useCallAssignmentsByDate Tests
// ============================================================================

describe('useCallAssignmentsByDate', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch call assignments by date', async () => {
    mockGet.mockResolvedValueOnce(mockListResponse);

    const { result } = renderHook(
      () => useCallAssignmentsByDate('2025-06-15'),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockGet).toHaveBeenCalledWith(
      '/call-assignments/by-date/2025-06-15'
    );
  });

  it('should not fetch when date is empty', () => {
    const { result } = renderHook(
      () => useCallAssignmentsByDate(''),
      { wrapper: createWrapper() }
    );

    expect(result.current.isLoading).toBe(false);
    expect(result.current.isFetching).toBe(false);
    expect(mockGet).not.toHaveBeenCalled();
  });
});

// ============================================================================
// useCreateCallAssignment Tests
// ============================================================================

describe('useCreateCallAssignment', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should create a call assignment', async () => {
    mockPost.mockResolvedValueOnce(mockCallAssignment);

    const { result } = renderHook(() => useCreateCallAssignment(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        callDate: '2025-06-15',
        personId: 'person-1',
        callType: 'weekday',
      });
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockPost).toHaveBeenCalledWith('/call-assignments', {
      callDate: '2025-06-15',
      personId: 'person-1',
      callType: 'weekday',
    });
    expect(result.current.data?.id).toBe('ca-1');
  });
});

// ============================================================================
// useUpdateCallAssignment Tests
// ============================================================================

describe('useUpdateCallAssignment', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should update a call assignment', async () => {
    const updated = { ...mockCallAssignment, personId: 'person-2' };
    mockPut.mockResolvedValueOnce(updated);

    const { result } = renderHook(() => useUpdateCallAssignment(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        id: 'ca-1',
        data: { personId: 'person-2' },
      });
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockPut).toHaveBeenCalledWith('/call-assignments/ca-1', {
      personId: 'person-2',
    });
    expect(result.current.data?.personId).toBe('person-2');
  });
});

// ============================================================================
// useDeleteCallAssignment Tests
// ============================================================================

describe('useDeleteCallAssignment', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should delete a call assignment', async () => {
    mockDel.mockResolvedValueOnce(undefined);

    const { result } = renderHook(() => useDeleteCallAssignment(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate('ca-1');
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockDel).toHaveBeenCalledWith('/call-assignments/ca-1');
  });
});

// ============================================================================
// useBulkUpdateCallAssignments Tests
// ============================================================================

describe('useBulkUpdateCallAssignments', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should bulk update call assignments', async () => {
    const mockResponse = {
      updated: 2,
      errors: [],
      assignments: [mockCallAssignment, mockCallAssignment2],
    };
    mockPost.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(() => useBulkUpdateCallAssignments(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        assignmentIds: ['ca-1', 'ca-2'],
        updates: { personId: 'person-2' },
      });
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockPost).toHaveBeenCalledWith('/call-assignments/bulk-update', {
      assignmentIds: ['ca-1', 'ca-2'],
      updates: { personId: 'person-2' },
    });
    expect(result.current.data?.updated).toBe(2);
  });
});

// ============================================================================
// useBulkDeleteCallAssignments Tests
// ============================================================================

describe('useBulkDeleteCallAssignments', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should bulk delete call assignments', async () => {
    mockDel.mockResolvedValue(undefined);

    const { result } = renderHook(() => useBulkDeleteCallAssignments(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate(['ca-1', 'ca-2']);
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockDel).toHaveBeenCalledTimes(2);
    expect(mockDel).toHaveBeenCalledWith('/call-assignments/ca-1');
    expect(mockDel).toHaveBeenCalledWith('/call-assignments/ca-2');
    expect(result.current.data?.deleted).toBe(2);
    expect(result.current.data?.errors).toEqual([]);
  });

  it('should handle partial failures in bulk delete', async () => {
    mockDel
      .mockResolvedValueOnce(undefined)
      .mockRejectedValueOnce({ message: 'Not found' });

    const { result } = renderHook(() => useBulkDeleteCallAssignments(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate(['ca-1', 'ca-2']);
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.deleted).toBe(1);
    expect(result.current.data?.errors).toHaveLength(1);
  });
});

// ============================================================================
// useGeneratePCAT Tests
// ============================================================================

describe('useGeneratePCAT', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should generate PCAT assignments', async () => {
    mockPost.mockResolvedValueOnce(mockPCATResponse);

    const { result } = renderHook(() => useGeneratePCAT(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({ assignmentIds: ['ca-1', 'ca-2'] });
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockPost).toHaveBeenCalledWith(
      '/call-assignments/generate-pcat',
      { assignmentIds: ['ca-1', 'ca-2'] }
    );
    expect(result.current.data?.processed).toBe(2);
    expect(result.current.data?.pcatCreated).toBe(2);
    expect(result.current.data?.doCreated).toBe(2);
  });
});

// ============================================================================
// useCoverageReport Tests
// ============================================================================

describe('useCoverageReport', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch coverage report', async () => {
    mockGet.mockResolvedValueOnce(mockCoverageReport);

    const { result } = renderHook(
      () => useCoverageReport('2025-06-01', '2025-06-30'),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    const url = mockGet.mock.calls[0][0] as string;
    expect(url).toContain('/call-assignments/reports/coverage');
    expect(result.current.data?.coveredNights).toBe(28);
    expect(result.current.data?.gaps).toHaveLength(2);
  });

  it('should not fetch when dates are empty', () => {
    const { result } = renderHook(
      () => useCoverageReport('', ''),
      { wrapper: createWrapper() }
    );

    expect(result.current.isLoading).toBe(false);
    expect(result.current.isFetching).toBe(false);
    expect(mockGet).not.toHaveBeenCalled();
  });
});

// ============================================================================
// useEquityReport Tests
// ============================================================================

describe('useEquityReport', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch equity report', async () => {
    mockGet.mockResolvedValueOnce(mockEquityReport);

    const { result } = renderHook(
      () => useEquityReport('2025-06-01', '2025-06-30'),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    const url = mockGet.mock.calls[0][0] as string;
    expect(url).toContain('/call-assignments/reports/equity');
    expect(result.current.data?.facultyCount).toBe(5);
    expect(result.current.data?.totalOvernightCalls).toBe(28);
  });

  it('should not fetch when dates are empty', () => {
    const { result } = renderHook(
      () => useEquityReport('', ''),
      { wrapper: createWrapper() }
    );

    expect(result.current.isLoading).toBe(false);
    expect(result.current.isFetching).toBe(false);
    expect(mockGet).not.toHaveBeenCalled();
  });
});

// ============================================================================
// useEquityPreview Tests
// ============================================================================

describe('useEquityPreview', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should preview equity changes', async () => {
    const mockPreviewResponse = {
      startDate: '2025-06-01',
      endDate: '2025-06-30',
      currentEquity: mockEquityReport,
      projectedEquity: mockEquityReport,
      facultyDetails: [],
      improvementScore: 0.15,
    };
    mockPost.mockResolvedValueOnce(mockPreviewResponse);

    const { result } = renderHook(() => useEquityPreview(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        startDate: '2025-06-01',
        endDate: '2025-06-30',
        simulatedChanges: [{ newPersonId: 'person-2' }],
      });
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockPost).toHaveBeenCalledWith(
      '/call-assignments/equity-preview',
      {
        startDate: '2025-06-01',
        endDate: '2025-06-30',
        simulatedChanges: [{ newPersonId: 'person-2' }],
      }
    );
    expect(result.current.data?.improvementScore).toBe(0.15);
  });
});

// ============================================================================
// useClearPCATStatus Tests
// ============================================================================

describe('useClearPCATStatus', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should clear PCAT status via bulk update', async () => {
    const mockResponse = { updated: 2, errors: [], assignments: [] };
    mockPost.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(() => useClearPCATStatus(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate(['ca-1', 'ca-2']);
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockPost).toHaveBeenCalledWith('/call-assignments/bulk-update', {
      assignmentIds: ['ca-1', 'ca-2'],
      updates: {},
    });
  });
});
