/**
 * useHalfDayAssignments Hook Tests
 *
 * Tests for half-day assignment hooks including list queries,
 * block-based fetching, and utility functions for map building.
 */
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';
import * as api from '@/lib/api';
import {
  useHalfDayAssignments,
  useHalfDayAssignmentsByBlock,
  buildHalfDayAssignmentMap,
  getSlotAssignment,
} from '@/hooks/useHalfDayAssignments';

// Mock the api module
jest.mock('@/lib/api');

const mockedApi = api as jest.Mocked<typeof api>;

// Create a fresh QueryClient for each test
function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
        staleTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  });
}

// Wrapper component with QueryClientProvider
function createWrapper() {
  const queryClient = createTestQueryClient();
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  };
}

// Mock data
const mockHalfDayAssignments = [
  {
    id: 'hda-1',
    personId: 'person-1',
    personName: 'Dr. Smith',
    personType: 'resident',
    pgyLevel: 2,
    date: '2024-01-15',
    timeOfDay: 'AM' as const,
    activityId: 'activity-1',
    activityCode: 'IM',
    activityName: 'Inpatient Medicine',
    displayAbbreviation: 'IM',
    source: 'solver' as const,
    isLocked: false,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
  },
  {
    id: 'hda-2',
    personId: 'person-1',
    personName: 'Dr. Smith',
    personType: 'resident',
    pgyLevel: 2,
    date: '2024-01-15',
    timeOfDay: 'PM' as const,
    activityId: 'activity-2',
    activityCode: 'LEC',
    activityName: 'Lecture',
    displayAbbreviation: 'LEC',
    source: 'preload' as const,
    isLocked: true,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
  },
  {
    id: 'hda-3',
    personId: 'person-2',
    personName: 'Dr. Jones',
    personType: 'resident',
    pgyLevel: 1,
    date: '2024-01-15',
    timeOfDay: 'AM' as const,
    activityId: 'activity-3',
    activityCode: 'C',
    activityName: 'Continuity Clinic',
    displayAbbreviation: 'C',
    source: 'preload' as const,
    isLocked: true,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
  },
];

describe('useHalfDayAssignments', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch half-day assignments by block successfully', async () => {
    const mockResponse = {
      assignments: mockHalfDayAssignments,
      total: 3,
      blockNumber: 1,
      academicYear: 2024,
      startDate: '2024-01-15',
      endDate: '2024-01-28',
    };

    mockedApi.get.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(
      () =>
        useHalfDayAssignments({
          blockNumber: 1,
          academicYear: 2024,
        }),
      {
        wrapper: createWrapper(),
      }
    );

    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.assignments).toHaveLength(3);
    expect(result.current.data?.blockNumber).toBe(1);
    expect(result.current.data?.academicYear).toBe(2024);

    // URL params must use snake_case
    expect(mockedApi.get).toHaveBeenCalledWith(
      expect.stringContaining('block_number=1')
    );
    expect(mockedApi.get).toHaveBeenCalledWith(
      expect.stringContaining('academic_year=2024')
    );
  });

  it('should fetch half-day assignments by date range', async () => {
    const mockResponse = {
      assignments: mockHalfDayAssignments,
      total: 3,
      blockNumber: null,
      academicYear: null,
      startDate: '2024-01-15',
      endDate: '2024-01-28',
    };

    mockedApi.get.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(
      () =>
        useHalfDayAssignments({
          startDate: '2024-01-15',
          endDate: '2024-01-28',
        }),
      {
        wrapper: createWrapper(),
      }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.assignments).toHaveLength(3);
    // URL params must use snake_case
    expect(mockedApi.get).toHaveBeenCalledWith(
      expect.stringContaining('start_date=2024-01-15')
    );
    expect(mockedApi.get).toHaveBeenCalledWith(
      expect.stringContaining('end_date=2024-01-28')
    );
  });

  it('should filter by person type using snake_case param', async () => {
    const mockResponse = {
      assignments: mockHalfDayAssignments,
      total: 3,
      blockNumber: 1,
      academicYear: 2024,
      startDate: '2024-01-15',
      endDate: '2024-01-28',
    };

    mockedApi.get.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(
      () =>
        useHalfDayAssignments({
          blockNumber: 1,
          academicYear: 2024,
          personType: 'resident',
        }),
      {
        wrapper: createWrapper(),
      }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    // URL param must use snake_case
    expect(mockedApi.get).toHaveBeenCalledWith(
      expect.stringContaining('person_type=resident')
    );
  });

  it('should be disabled when insufficient params provided', () => {
    // Missing academic year
    const { result: missingYear } = renderHook(
      () =>
        useHalfDayAssignments({
          blockNumber: 1,
        }),
      {
        wrapper: createWrapper(),
      }
    );

    expect(missingYear.current.isLoading).toBe(false);
    expect(missingYear.current.isFetching).toBe(false);

    // Missing end date
    const { result: missingEnd } = renderHook(
      () =>
        useHalfDayAssignments({
          startDate: '2024-01-15',
        }),
      {
        wrapper: createWrapper(),
      }
    );

    expect(missingEnd.current.isLoading).toBe(false);
    expect(missingEnd.current.isFetching).toBe(false);
  });

  it('should handle empty results', async () => {
    const mockResponse = {
      assignments: [],
      total: 0,
      blockNumber: 1,
      academicYear: 2024,
      startDate: '2024-01-15',
      endDate: '2024-01-28',
    };

    mockedApi.get.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(
      () =>
        useHalfDayAssignments({
          blockNumber: 1,
          academicYear: 2024,
        }),
      {
        wrapper: createWrapper(),
      }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.assignments).toHaveLength(0);
  });

  it('should not retry on auth errors', async () => {
    const authError = { message: 'Unauthorized', status: 401 };
    mockedApi.get.mockRejectedValueOnce(authError);

    const { result } = renderHook(
      () =>
        useHalfDayAssignments({
          blockNumber: 1,
          academicYear: 2024,
        }),
      {
        wrapper: createWrapper(),
      }
    );

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    // Should only be called once (no retries)
    expect(mockedApi.get).toHaveBeenCalledTimes(1);
  });
});

describe('useHalfDayAssignmentsByBlock', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should be a convenience wrapper for useHalfDayAssignments', async () => {
    const mockResponse = {
      assignments: mockHalfDayAssignments,
      total: 3,
      blockNumber: 1,
      academicYear: 2024,
      startDate: '2024-01-15',
      endDate: '2024-01-28',
    };

    mockedApi.get.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(
      () => useHalfDayAssignmentsByBlock(1, 2024),
      {
        wrapper: createWrapper(),
      }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.blockNumber).toBe(1);
    expect(result.current.data?.academicYear).toBe(2024);
  });

  it('should pass personType filter', async () => {
    const mockResponse = {
      assignments: mockHalfDayAssignments.filter(
        (a) => a.personType === 'resident'
      ),
      total: 3,
      blockNumber: 1,
      academicYear: 2024,
      startDate: '2024-01-15',
      endDate: '2024-01-28',
    };

    mockedApi.get.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(
      () => useHalfDayAssignmentsByBlock(1, 2024, 'resident'),
      {
        wrapper: createWrapper(),
      }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockedApi.get).toHaveBeenCalledWith(
      expect.stringContaining('person_type=resident')
    );
  });
});

// ============================================================================
// Utility Function Tests
// ============================================================================

describe('buildHalfDayAssignmentMap', () => {
  it('should build map keyed by personId_date_timeOfDay', () => {
    const map = buildHalfDayAssignmentMap(mockHalfDayAssignments);

    expect(map.size).toBe(3);
    expect(map.has('person-1_2024-01-15_AM')).toBe(true);
    expect(map.has('person-1_2024-01-15_PM')).toBe(true);
    expect(map.has('person-2_2024-01-15_AM')).toBe(true);

    const assignment = map.get('person-1_2024-01-15_AM');
    expect(assignment?.activityCode).toBe('IM');
  });

  it('should handle empty array', () => {
    const map = buildHalfDayAssignmentMap([]);
    expect(map.size).toBe(0);
  });

  it('should handle duplicate keys by keeping last', () => {
    const duplicates = [
      mockHalfDayAssignments[0],
      {
        ...mockHalfDayAssignments[0],
        id: 'hda-duplicate',
        activityCode: 'UPDATED',
      },
    ];

    const map = buildHalfDayAssignmentMap(duplicates);
    expect(map.size).toBe(1);

    const assignment = map.get('person-1_2024-01-15_AM');
    expect(assignment?.activityCode).toBe('UPDATED');
  });
});

describe('getSlotAssignment', () => {
  it('should retrieve assignment from map', () => {
    const map = buildHalfDayAssignmentMap(mockHalfDayAssignments);

    const assignment = getSlotAssignment(map, 'person-1', '2024-01-15', 'AM');
    expect(assignment).toBeDefined();
    expect(assignment?.activityCode).toBe('IM');
  });

  it('should return undefined for non-existent slot', () => {
    const map = buildHalfDayAssignmentMap(mockHalfDayAssignments);

    const assignment = getSlotAssignment(map, 'person-999', '2024-01-15', 'AM');
    expect(assignment).toBeUndefined();
  });

  it('should distinguish between AM and PM slots', () => {
    const map = buildHalfDayAssignmentMap(mockHalfDayAssignments);

    const amAssignment = getSlotAssignment(map, 'person-1', '2024-01-15', 'AM');
    const pmAssignment = getSlotAssignment(map, 'person-1', '2024-01-15', 'PM');

    expect(amAssignment?.activityCode).toBe('IM');
    expect(pmAssignment?.activityCode).toBe('LEC');
    expect(amAssignment?.id).not.toBe(pmAssignment?.id);
  });

  it('should handle empty map', () => {
    const map = new Map();

    const assignment = getSlotAssignment(map, 'person-1', '2024-01-15', 'AM');
    expect(assignment).toBeUndefined();
  });
});
