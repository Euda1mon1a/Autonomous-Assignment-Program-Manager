/**
 * useCallAssignments Hook Tests
 *
 * Tests for call assignment management hooks including list, single fetch,
 * coverage reports, and CRUD mutations.
 */
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';
import * as api from '@/lib/api';
import {
  useCallAssignments,
  useCallAssignment,
  useCallAssignmentsByPerson,
  useCallAssignmentsByDate,
  useCreateCallAssignment,
  useUpdateCallAssignment,
  useDeleteCallAssignment,
  useCoverageReport,
} from '@/hooks/useCallAssignments';
import type {
  CallAssignment,
  CallAssignmentListResponse,
  CallCoverageReport,
} from '@/types/call-assignment';

// Mock the api module
jest.mock('@/lib/api');

const mockedApi = api as jest.Mocked<typeof api>;

// Mock data
const mockCallAssignment: CallAssignment = {
  id: 'call-1',
  personId: 'person-1',
  personName: 'Dr. Jane Smith',
  date: '2024-03-01',
  callType: 'overnight',
  blockId: 'block-1',
  postCallStatus: 'available',
  createdAt: '2024-01-01T00:00:00Z',
  updatedAt: '2024-01-01T00:00:00Z',
};

const mockCallAssignments: CallAssignment[] = [
  mockCallAssignment,
  {
    id: 'call-2',
    personId: 'person-2',
    personName: 'Dr. John Doe',
    date: '2024-03-02',
    callType: 'overnight',
    blockId: 'block-1',
    postCallStatus: 'available',
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
  },
];

const mockCoverageReport: CallCoverageReport = {
  startDate: '2024-03-01',
  endDate: '2024-03-31',
  totalDays: 31,
  coveredDays: 28,
  uncoveredDays: 3,
  coverageRate: 0.9,
  assignmentsByType: {
    overnight: 20,
    weekend: 8,
  },
  assignmentsByPerson: {
    'person-1': 14,
    'person-2': 14,
  },
  gapDates: ['2024-03-10', '2024-03-15', '2024-03-22'],
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

describe('useCallAssignments', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch call assignments successfully', async () => {
    const mockResponse: CallAssignmentListResponse = {
      items: mockCallAssignments,
      total: 2,
    };
    mockedApi.get.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(() => useCallAssignments(), {
      wrapper: createWrapper(),
    });

    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.items).toHaveLength(2);
    expect(result.current.data?.total).toBe(2);
    expect(mockedApi.get).toHaveBeenCalledWith('/call-assignments');
  });

  it('should fetch call assignments with filters', async () => {
    const mockResponse: CallAssignmentListResponse = {
      items: [mockCallAssignment],
      total: 1,
    };
    mockedApi.get.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(
      () =>
        useCallAssignments({
          startDate: '2024-03-01',
          endDate: '2024-03-31',
          personId: 'person-1',
        }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockedApi.get).toHaveBeenCalledWith(
      '/call-assignments?start_date=2024-03-01&end_date=2024-03-31&person_id=person-1'
    );
  });

  it('should handle API errors', async () => {
    const apiError = { message: 'Failed to fetch', status: 500 };
    mockedApi.get.mockRejectedValueOnce(apiError);

    const { result } = renderHook(() => useCallAssignments(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toEqual(apiError);
  });

  it('should handle empty results', async () => {
    const mockResponse: CallAssignmentListResponse = {
      items: [],
      total: 0,
    };
    mockedApi.get.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(() => useCallAssignments(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.items).toHaveLength(0);
    expect(result.current.data?.total).toBe(0);
  });
});

describe('useCallAssignment', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch single call assignment', async () => {
    mockedApi.get.mockResolvedValueOnce(mockCallAssignment);

    const { result } = renderHook(() => useCallAssignment('call-1'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockCallAssignment);
    expect(mockedApi.get).toHaveBeenCalledWith('/call-assignments/call-1');
  });

  it('should not fetch if ID is empty', () => {
    const { result } = renderHook(() => useCallAssignment(''), {
      wrapper: createWrapper(),
    });

    expect(result.current.isFetching).toBe(false);
    expect(mockedApi.get).not.toHaveBeenCalled();
  });
});

describe('useCallAssignmentsByPerson', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch call assignments by person', async () => {
    const mockResponse: CallAssignmentListResponse = {
      items: [mockCallAssignment],
      total: 1,
    };
    mockedApi.get.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(
      () => useCallAssignmentsByPerson('person-1'),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockedApi.get).toHaveBeenCalledWith(
      '/call-assignments/by-person/person-1'
    );
  });

  it('should fetch with date range', async () => {
    const mockResponse: CallAssignmentListResponse = {
      items: [mockCallAssignment],
      total: 1,
    };
    mockedApi.get.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(
      () =>
        useCallAssignmentsByPerson('person-1', '2024-03-01', '2024-03-31'),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockedApi.get).toHaveBeenCalledWith(
      '/call-assignments/by-person/person-1?start_date=2024-03-01&end_date=2024-03-31'
    );
  });
});

describe('useCallAssignmentsByDate', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch call assignments by date', async () => {
    const mockResponse: CallAssignmentListResponse = {
      items: [mockCallAssignment],
      total: 1,
    };
    mockedApi.get.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(
      () => useCallAssignmentsByDate('2024-03-01'),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockedApi.get).toHaveBeenCalledWith(
      '/call-assignments/by-date/2024-03-01'
    );
  });
});

describe('useCreateCallAssignment', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should create call assignment', async () => {
    mockedApi.post.mockResolvedValueOnce(mockCallAssignment);

    const { result } = renderHook(() => useCreateCallAssignment(), {
      wrapper: createWrapper(),
    });

    const createData = {
      personId: 'person-1',
      date: '2024-03-01',
      callType: 'overnight' as const,
      blockId: 'block-1',
    };

    result.current.mutate(createData);

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockedApi.post).toHaveBeenCalledWith(
      '/call-assignments',
      createData
    );
  });

  it('should invalidate queries on success', async () => {
    mockedApi.post.mockResolvedValueOnce(mockCallAssignment);

    const queryClient = createTestQueryClient();
    const invalidateSpy = jest.spyOn(queryClient, 'invalidateQueries');

    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );

    const { result } = renderHook(() => useCreateCallAssignment(), {
      wrapper,
    });

    const createData = {
      personId: 'person-1',
      date: '2024-03-01',
      callType: 'overnight' as const,
      blockId: 'block-1',
    };

    result.current.mutate(createData);

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(invalidateSpy).toHaveBeenCalled();
  });
});

describe('useUpdateCallAssignment', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should update call assignment', async () => {
    const updatedAssignment = {
      ...mockCallAssignment,
      postCallStatus: 'pcat' as const,
    };
    mockedApi.put.mockResolvedValueOnce(updatedAssignment);

    const { result } = renderHook(() => useUpdateCallAssignment(), {
      wrapper: createWrapper(),
    });

    result.current.mutate({
      id: 'call-1',
      data: { postCallStatus: 'pcat' },
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockedApi.put).toHaveBeenCalledWith('/call-assignments/call-1', {
      postCallStatus: 'pcat',
    });
  });
});

describe('useDeleteCallAssignment', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should delete call assignment', async () => {
    mockedApi.del.mockResolvedValueOnce(undefined);

    const { result } = renderHook(() => useDeleteCallAssignment(), {
      wrapper: createWrapper(),
    });

    result.current.mutate('call-1');

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockedApi.del).toHaveBeenCalledWith('/call-assignments/call-1');
  });
});

describe('useCoverageReport', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch coverage report', async () => {
    mockedApi.get.mockResolvedValueOnce(mockCoverageReport);

    const { result } = renderHook(
      () => useCoverageReport('2024-03-01', '2024-03-31'),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockCoverageReport);
    expect(mockedApi.get).toHaveBeenCalledWith(
      '/call-assignments/reports/coverage?startDate=2024-03-01&endDate=2024-03-31'
    );
  });

  it('should not fetch if dates are missing', () => {
    const { result } = renderHook(() => useCoverageReport('', ''), {
      wrapper: createWrapper(),
    });

    expect(result.current.isFetching).toBe(false);
    expect(mockedApi.get).not.toHaveBeenCalled();
  });

  it('should show coverage gaps', async () => {
    mockedApi.get.mockResolvedValueOnce(mockCoverageReport);

    const { result } = renderHook(
      () => useCoverageReport('2024-03-01', '2024-03-31'),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.gapDates).toHaveLength(3);
    expect(result.current.data?.coverageRate).toBe(0.9);
  });
});
