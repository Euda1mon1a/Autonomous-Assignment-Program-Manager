/**
 * useHalfDayAssignments Hook Tests
 *
 * Tests for half-day assignment hooks including block/date params
 * and map builder utilities.
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
  type HalfDayAssignment,
  type HalfDayAssignmentListResponse,
} from '@/hooks/useHalfDayAssignments';

// Mock the api module
jest.mock('@/lib/api');

const mockedApi = api as jest.Mocked<typeof api>;

// Mock data
const mockAssignments: HalfDayAssignment[] = [
  {
    id: 'hda-1',
    personId: 'person-1',
    personName: 'Dr. Jane Smith',
    personType: 'resident',
    pgyLevel: 2,
    date: '2024-03-01',
    timeOfDay: 'AM',
    activityId: 'activity-1',
    activityCode: 'IM',
    activityName: 'Inpatient Medicine',
    displayAbbreviation: 'IM',
    source: 'solver',
    isLocked: false,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
  },
  {
    id: 'hda-2',
    personId: 'person-1',
    personName: 'Dr. Jane Smith',
    personType: 'resident',
    pgyLevel: 2,
    date: '2024-03-01',
    timeOfDay: 'PM',
    activityId: 'activity-2',
    activityCode: 'LEC',
    activityName: 'Lecture',
    displayAbbreviation: 'LEC',
    source: 'preload',
    isLocked: true,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
  },
  {
    id: 'hda-3',
    personId: 'person-2',
    personName: 'Dr. John Doe',
    personType: 'resident',
    pgyLevel: 1,
    date: '2024-03-01',
    timeOfDay: 'AM',
    activityId: 'activity-3',
    activityCode: 'CLINIC',
    activityName: 'Clinic',
    displayAbbreviation: 'C',
    source: 'preload',
    isLocked: true,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
  },
];

const mockResponse: HalfDayAssignmentListResponse = {
  assignments: mockAssignments,
  total: 3,
  blockNumber: 10,
  academicYear: 2025,
  startDate: '2024-03-01',
  endDate: '2024-03-31',
};

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

describe('useHalfDayAssignments', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch half-day assignments by block', async () => {
    mockedApi.get.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(
      () =>
        useHalfDayAssignments({
          blockNumber: 10,
          academicYear: 2025,
        }),
      { wrapper: createWrapper() }
    );

    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.assignments).toHaveLength(3);
    expect(result.current.data?.blockNumber).toBe(10);
    expect(mockedApi.get).toHaveBeenCalledWith(
      '/half-day-assignments?block_number=10&academic_year=2025'
    );
  });

  it('should fetch by date range', async () => {
    mockedApi.get.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(
      () =>
        useHalfDayAssignments({
          startDate: '2024-03-01',
          endDate: '2024-03-31',
        }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockedApi.get).toHaveBeenCalledWith(
      '/half-day-assignments?start_date=2024-03-01&end_date=2024-03-31'
    );
  });

  it('should filter by person type', async () => {
    const residentAssignments = mockAssignments.filter(
      (a) => a.personType === 'resident'
    );
    mockedApi.get.mockResolvedValueOnce({
      ...mockResponse,
      assignments: residentAssignments,
      total: 3,
    });

    const { result } = renderHook(
      () =>
        useHalfDayAssignments({
          blockNumber: 10,
          academicYear: 2025,
          personType: 'resident',
        }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockedApi.get).toHaveBeenCalledWith(
      '/half-day-assignments?block_number=10&academic_year=2025&person_type=resident'
    );
  });

  it('should not fetch without required parameters', () => {
    const { result } = renderHook(
      () =>
        useHalfDayAssignments({
          blockNumber: undefined,
          academicYear: undefined,
        }),
      { wrapper: createWrapper() }
    );

    expect(result.current.isFetching).toBe(false);
    expect(mockedApi.get).not.toHaveBeenCalled();
  });

  it('should fetch with block params', () => {
    mockedApi.get.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(
      () =>
        useHalfDayAssignments({
          blockNumber: 10,
          academicYear: 2025,
        }),
      { wrapper: createWrapper() }
    );

    expect(result.current.isFetching).toBe(true);
  });

  it('should fetch with date params', () => {
    mockedApi.get.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(
      () =>
        useHalfDayAssignments({
          startDate: '2024-03-01',
          endDate: '2024-03-31',
        }),
      { wrapper: createWrapper() }
    );

    expect(result.current.isFetching).toBe(true);
  });

  it('should handle API errors', async () => {
    const apiError = { message: 'Failed to fetch', status: 500 };
    mockedApi.get.mockRejectedValueOnce(apiError);

    const { result } = renderHook(
      () =>
        useHalfDayAssignments({
          blockNumber: 10,
          academicYear: 2025,
        }),
      { wrapper: createWrapper() }
    );

    await waitFor(
      () => {
        expect(result.current.isError).toBe(true);
      },
      { timeout: 5000 }
    );

    expect(result.current.error).toBeDefined();
  });

  it('should not retry on auth errors', async () => {
    const authError = { message: 'Unauthorized', status: 401 };
    mockedApi.get.mockRejectedValueOnce(authError);

    const { result } = renderHook(
      () =>
        useHalfDayAssignments({
          blockNumber: 10,
          academicYear: 2025,
        }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    // Should not retry auth errors
    expect(mockedApi.get).toHaveBeenCalledTimes(1);
  });

  it('should handle empty results', async () => {
    const emptyResponse: HalfDayAssignmentListResponse = {
      assignments: [],
      total: 0,
      blockNumber: 10,
      academicYear: 2025,
      startDate: '2024-03-01',
      endDate: '2024-03-31',
    };
    mockedApi.get.mockResolvedValueOnce(emptyResponse);

    const { result } = renderHook(
      () =>
        useHalfDayAssignments({
          blockNumber: 10,
          academicYear: 2025,
        }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.assignments).toHaveLength(0);
  });

  it('should show locked assignments', async () => {
    mockedApi.get.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(
      () =>
        useHalfDayAssignments({
          blockNumber: 10,
          academicYear: 2025,
        }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    const assignments = result.current.data?.assignments || [];
    const lockedCount = assignments.filter((a) => a.isLocked).length;
    expect(lockedCount).toBeGreaterThan(0);
  });

  it('should show assignment sources', async () => {
    mockedApi.get.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(
      () =>
        useHalfDayAssignments({
          blockNumber: 10,
          academicYear: 2025,
        }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    const assignments = result.current.data?.assignments || [];
    const sources = new Set(assignments.map((a) => a.source));
    expect(sources).toContain('solver');
    expect(sources).toContain('preload');
  });
});

describe('useHalfDayAssignmentsByBlock', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch by block number and year', async () => {
    mockedApi.get.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(
      () => useHalfDayAssignmentsByBlock(10, 2025),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockedApi.get).toHaveBeenCalledWith(
      '/half-day-assignments?block_number=10&academic_year=2025'
    );
  });

  it('should filter by person type in convenience hook', async () => {
    mockedApi.get.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(
      () => useHalfDayAssignmentsByBlock(10, 2025, 'faculty'),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockedApi.get).toHaveBeenCalledWith(
      '/half-day-assignments?block_number=10&academic_year=2025&person_type=faculty'
    );
  });
});

describe('buildHalfDayAssignmentMap', () => {
  it('should build map with correct keys', () => {
    const map = buildHalfDayAssignmentMap(mockAssignments);

    expect(map.size).toBe(3);
    expect(map.has('person-1_2024-03-01_AM')).toBe(true);
    expect(map.has('person-1_2024-03-01_PM')).toBe(true);
    expect(map.has('person-2_2024-03-01_AM')).toBe(true);
  });

  it('should retrieve assignments by key', () => {
    const map = buildHalfDayAssignmentMap(mockAssignments);

    const assignment = map.get('person-1_2024-03-01_AM');
    expect(assignment).toBeDefined();
    expect(assignment?.activityCode).toBe('IM');
  });

  it('should handle empty array', () => {
    const map = buildHalfDayAssignmentMap([]);

    expect(map.size).toBe(0);
  });

  it('should handle duplicate keys by keeping last', () => {
    const duplicateAssignments: HalfDayAssignment[] = [
      mockAssignments[0],
      {
        ...mockAssignments[0],
        id: 'hda-duplicate',
        activityCode: 'DIFFERENT',
      },
    ];

    const map = buildHalfDayAssignmentMap(duplicateAssignments);

    const assignment = map.get('person-1_2024-03-01_AM');
    expect(assignment?.activityCode).toBe('DIFFERENT');
  });
});

describe('getSlotAssignment', () => {
  it('should retrieve assignment for valid slot', () => {
    const map = buildHalfDayAssignmentMap(mockAssignments);

    const assignment = getSlotAssignment(
      map,
      'person-1',
      '2024-03-01',
      'AM'
    );

    expect(assignment).toBeDefined();
    expect(assignment?.personId).toBe('person-1');
    expect(assignment?.date).toBe('2024-03-01');
    expect(assignment?.timeOfDay).toBe('AM');
  });

  it('should return undefined for missing slot', () => {
    const map = buildHalfDayAssignmentMap(mockAssignments);

    const assignment = getSlotAssignment(
      map,
      'person-999',
      '2024-03-01',
      'AM'
    );

    expect(assignment).toBeUndefined();
  });

  it('should distinguish AM and PM slots', () => {
    const map = buildHalfDayAssignmentMap(mockAssignments);

    const amAssignment = getSlotAssignment(
      map,
      'person-1',
      '2024-03-01',
      'AM'
    );
    const pmAssignment = getSlotAssignment(
      map,
      'person-1',
      '2024-03-01',
      'PM'
    );

    expect(amAssignment?.activityCode).toBe('IM');
    expect(pmAssignment?.activityCode).toBe('LEC');
  });

  it('should handle different dates', () => {
    const multiDateAssignments: HalfDayAssignment[] = [
      mockAssignments[0],
      {
        ...mockAssignments[0],
        id: 'hda-different-date',
        date: '2024-03-02',
        activityCode: 'CLINIC',
      },
    ];

    const map = buildHalfDayAssignmentMap(multiDateAssignments);

    const march1 = getSlotAssignment(map, 'person-1', '2024-03-01', 'AM');
    const march2 = getSlotAssignment(map, 'person-1', '2024-03-02', 'AM');

    expect(march1?.activityCode).toBe('IM');
    expect(march2?.activityCode).toBe('CLINIC');
  });
});
