/**
 * Tests for useAbsences hook and related absence hooks.
 *
 * Tests data fetching, filtering, mutations, and error handling.
 */
import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';

// Mock the API module
jest.mock('@/lib/api', () => ({
  get: jest.fn(),
  post: jest.fn(),
  put: jest.fn(),
  del: jest.fn(),
}));

import { get, post, put, del } from '@/lib/api';
import {
  useAbsences,
  useCreateAbsence,
  useUpdateAbsence,
  useDeleteAbsence,
} from '@/lib/hooks';

const mockGet = get as jest.MockedFunction<typeof get>;
const mockPost = post as jest.MockedFunction<typeof post>;
const mockPut = put as jest.MockedFunction<typeof put>;
const mockDel = del as jest.MockedFunction<typeof del>;

// Test wrapper with QueryClient
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

// Sample data
const mockAbsences = {
  items: [
    {
      id: '1',
      person_id: 'person-1',
      start_date: '2024-02-01',
      end_date: '2024-02-07',
      absence_type: 'vacation',
      deployment_orders: false,
      tdy_location: null,
      notes: 'Annual leave',
      created_at: '2024-01-15T00:00:00Z',
    },
    {
      id: '2',
      person_id: 'person-2',
      start_date: '2024-03-01',
      end_date: '2024-03-15',
      absence_type: 'deployment',
      deployment_orders: true,
      tdy_location: null,
      notes: 'Military training',
      created_at: '2024-02-01T00:00:00Z',
    },
  ],
  total: 2,
};

describe('useAbsences', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch absences data successfully', async () => {
    mockGet.mockResolvedValueOnce(mockAbsences);

    const { result } = renderHook(() => useAbsences(), {
      wrapper: createWrapper(),
    });

    // Initially loading
    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockAbsences);
    expect(result.current.data?.items).toHaveLength(2);
    expect(mockGet).toHaveBeenCalledWith('/api/absences');
  });

  it('should fetch absences with person_id filter', async () => {
    const filteredAbsences = {
      items: [mockAbsences.items[0]],
      total: 1,
    };
    mockGet.mockResolvedValueOnce(filteredAbsences);

    const { result } = renderHook(() => useAbsences(1), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockGet).toHaveBeenCalledWith('/api/absences?person_id=1');
    expect(result.current.data?.items).toHaveLength(1);
  });

  it('should handle API errors', async () => {
    const error = { message: 'Network error', status: 500 };
    mockGet.mockRejectedValueOnce(error);

    const { result } = renderHook(() => useAbsences(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toEqual(error);
  });

  it('should refetch on person_id change', async () => {
    mockGet.mockResolvedValue(mockAbsences);

    const { result, rerender } = renderHook(
      ({ personId }) => useAbsences(personId),
      {
        wrapper: createWrapper(),
        initialProps: { personId: undefined as number | undefined },
      }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    // Change person filter
    rerender({ personId: 123 });

    await waitFor(() => {
      expect(mockGet).toHaveBeenCalledTimes(2);
    });
  });

  it('should return empty list when no absences exist', async () => {
    mockGet.mockResolvedValueOnce({ items: [], total: 0 });

    const { result } = renderHook(() => useAbsences(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.items).toHaveLength(0);
    expect(result.current.data?.total).toBe(0);
  });
});

describe('useCreateAbsence', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should create an absence successfully', async () => {
    const newAbsence = {
      id: '3',
      person_id: 'person-3',
      start_date: '2024-04-01',
      end_date: '2024-04-05',
      absence_type: 'conference',
      deployment_orders: false,
      notes: 'Medical conference',
      created_at: '2024-03-01T00:00:00Z',
    };
    mockPost.mockResolvedValueOnce(newAbsence);

    const { result } = renderHook(() => useCreateAbsence(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      await result.current.mutateAsync({
        person_id: 'person-3',
        start_date: '2024-04-01',
        end_date: '2024-04-05',
        absence_type: 'conference',
        notes: 'Medical conference',
      });
    });

    expect(mockPost).toHaveBeenCalledWith('/absences', {
      person_id: 'person-3',
      start_date: '2024-04-01',
      end_date: '2024-04-05',
      absence_type: 'conference',
      notes: 'Medical conference',
    });
    expect(result.current.isSuccess).toBe(true);
  });

  it('should create a deployment absence', async () => {
    const deploymentAbsence = {
      id: '4',
      person_id: 'person-4',
      start_date: '2024-05-01',
      end_date: '2024-06-15',
      absence_type: 'deployment',
      deployment_orders: true,
      notes: 'Annual training',
      created_at: '2024-04-01T00:00:00Z',
    };
    mockPost.mockResolvedValueOnce(deploymentAbsence);

    const { result } = renderHook(() => useCreateAbsence(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      await result.current.mutateAsync({
        person_id: 'person-4',
        start_date: '2024-05-01',
        end_date: '2024-06-15',
        absence_type: 'deployment',
        deployment_orders: true,
        notes: 'Annual training',
      });
    });

    expect(result.current.isSuccess).toBe(true);
  });

  it('should handle creation errors', async () => {
    const error = { message: 'Invalid date range', status: 400 };
    mockPost.mockRejectedValueOnce(error);

    const { result } = renderHook(() => useCreateAbsence(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      try {
        await result.current.mutateAsync({
          person_id: 'person-1',
          start_date: '2024-02-10',
          end_date: '2024-02-01', // End before start
          absence_type: 'vacation',
        });
      } catch (e) {
        // Expected to throw
      }
    });

    expect(result.current.isError).toBe(true);
    expect(result.current.error).toEqual(error);
  });
});

describe('useUpdateAbsence', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should update an absence successfully', async () => {
    const updatedAbsence = {
      ...mockAbsences.items[0],
      end_date: '2024-02-10',
      notes: 'Extended leave',
    };
    mockPut.mockResolvedValueOnce(updatedAbsence);

    const { result } = renderHook(() => useUpdateAbsence(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      await result.current.mutateAsync({
        id: '1',
        data: { end_date: '2024-02-10', notes: 'Extended leave' },
      });
    });

    expect(mockPut).toHaveBeenCalledWith('/absences/1', {
      end_date: '2024-02-10',
      notes: 'Extended leave',
    });
    expect(result.current.isSuccess).toBe(true);
  });

  it('should handle update errors', async () => {
    const error = { message: 'Not found', status: 404 };
    mockPut.mockRejectedValueOnce(error);

    const { result } = renderHook(() => useUpdateAbsence(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      try {
        await result.current.mutateAsync({
          id: 'nonexistent',
          data: { notes: 'Updated' },
        });
      } catch (e) {
        // Expected to throw
      }
    });

    expect(result.current.isError).toBe(true);
  });
});

describe('useDeleteAbsence', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should delete an absence successfully', async () => {
    mockDel.mockResolvedValueOnce(undefined);

    const { result } = renderHook(() => useDeleteAbsence(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      await result.current.mutateAsync('1');
    });

    expect(mockDel).toHaveBeenCalledWith('/absences/1');
    expect(result.current.isSuccess).toBe(true);
  });

  it('should handle delete errors', async () => {
    const error = { message: 'Not found', status: 404 };
    mockDel.mockRejectedValueOnce(error);

    const { result } = renderHook(() => useDeleteAbsence(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      try {
        await result.current.mutateAsync('nonexistent');
      } catch (e) {
        // Expected to throw
      }
    });

    expect(result.current.isError).toBe(true);
  });
});
