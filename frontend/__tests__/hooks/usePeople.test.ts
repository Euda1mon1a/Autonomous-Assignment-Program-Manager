/**
 * Tests for usePeople hook and related people hooks.
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
  usePeople,
  useResidents,
  useFaculty,
  useCreatePerson,
  useUpdatePerson,
  useDeletePerson,
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
const mockPeople = {
  items: [
    {
      id: '1',
      name: 'Dr. Jane Smith',
      type: 'resident',
      email: 'jane@hospital.org',
      pgy_level: 2,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    },
    {
      id: '2',
      name: 'Dr. John Doe',
      type: 'faculty',
      email: 'john@hospital.org',
      performs_procedures: true,
      specialties: ['Sports Medicine'],
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    },
  ],
  total: 2,
};

const mockResidents = {
  items: [mockPeople.items[0]],
  total: 1,
};

const mockFaculty = {
  items: [mockPeople.items[1]],
  total: 1,
};

describe('usePeople', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch people data successfully', async () => {
    mockGet.mockResolvedValueOnce(mockPeople);

    const { result } = renderHook(() => usePeople(), {
      wrapper: createWrapper(),
    });

    // Initially loading
    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockPeople);
    expect(result.current.data?.items).toHaveLength(2);
    expect(mockGet).toHaveBeenCalledWith('/api/people');
  });

  it('should fetch people with role filter', async () => {
    mockGet.mockResolvedValueOnce(mockResidents);

    const { result } = renderHook(
      () => usePeople({ role: 'resident' }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockGet).toHaveBeenCalledWith('/api/people?role=resident');
    expect(result.current.data?.items).toHaveLength(1);
    expect(result.current.data?.items[0].type).toBe('resident');
  });

  it('should fetch people with pgy_level filter', async () => {
    mockGet.mockResolvedValueOnce(mockResidents);

    const { result } = renderHook(
      () => usePeople({ pgy_level: 2 }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockGet).toHaveBeenCalledWith('/api/people?pgy_level=2');
  });

  it('should handle API errors', async () => {
    const error = { message: 'Network error', status: 500 };
    mockGet.mockRejectedValueOnce(error);

    const { result } = renderHook(() => usePeople(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toEqual(error);
  });

  it('should refetch on filter change', async () => {
    mockGet.mockResolvedValue(mockPeople);

    const { result, rerender } = renderHook(
      ({ filters }) => usePeople(filters),
      {
        wrapper: createWrapper(),
        initialProps: { filters: undefined as any },
      }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    // Change filters
    rerender({ filters: { role: 'faculty' } });

    await waitFor(() => {
      expect(mockGet).toHaveBeenCalledTimes(2);
    });
  });
});

describe('useResidents', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch residents successfully', async () => {
    mockGet.mockResolvedValueOnce(mockResidents);

    const { result } = renderHook(() => useResidents(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.items).toHaveLength(1);
    expect(result.current.data?.items[0].type).toBe('resident');
    expect(mockGet).toHaveBeenCalledWith('/people/residents');
  });

  it('should filter by PGY level', async () => {
    mockGet.mockResolvedValueOnce(mockResidents);

    const { result } = renderHook(() => useResidents(2), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockGet).toHaveBeenCalledWith('/people/residents?pgy_level=2');
  });
});

describe('useFaculty', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch faculty successfully', async () => {
    mockGet.mockResolvedValueOnce(mockFaculty);

    const { result } = renderHook(() => useFaculty(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.items).toHaveLength(1);
    expect(result.current.data?.items[0].type).toBe('faculty');
    expect(mockGet).toHaveBeenCalledWith('/people/faculty');
  });

  it('should filter by specialty', async () => {
    mockGet.mockResolvedValueOnce(mockFaculty);

    const { result } = renderHook(() => useFaculty('Sports Medicine'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockGet).toHaveBeenCalledWith('/people/faculty?specialty=Sports%20Medicine');
  });
});

describe('useCreatePerson', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should create a person successfully', async () => {
    const newPerson = {
      id: '3',
      name: 'Dr. New Person',
      type: 'resident',
      email: 'new@hospital.org',
      pgy_level: 1,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    };
    mockPost.mockResolvedValueOnce(newPerson);

    const { result } = renderHook(() => useCreatePerson(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      await result.current.mutateAsync({
        name: 'Dr. New Person',
        type: 'resident',
        email: 'new@hospital.org',
        pgy_level: 1,
      });
    });

    expect(mockPost).toHaveBeenCalledWith('/people', {
      name: 'Dr. New Person',
      type: 'resident',
      email: 'new@hospital.org',
      pgy_level: 1,
    });
    expect(result.current.isSuccess).toBe(true);
  });

  it('should handle creation errors', async () => {
    const error = { message: 'Validation failed', status: 400 };
    mockPost.mockRejectedValueOnce(error);

    const { result } = renderHook(() => useCreatePerson(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      try {
        await result.current.mutateAsync({
          name: 'Dr. Invalid',
          type: 'resident',
        } as any);
      } catch (e) {
        // Expected to throw
      }
    });

    expect(result.current.isError).toBe(true);
    expect(result.current.error).toEqual(error);
  });
});

describe('useUpdatePerson', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should update a person successfully', async () => {
    const updatedPerson = {
      ...mockPeople.items[0],
      name: 'Dr. Updated Name',
    };
    mockPut.mockResolvedValueOnce(updatedPerson);

    const { result } = renderHook(() => useUpdatePerson(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      await result.current.mutateAsync({
        id: '1',
        data: { name: 'Dr. Updated Name' },
      });
    });

    expect(mockPut).toHaveBeenCalledWith('/people/1', { name: 'Dr. Updated Name' });
    expect(result.current.isSuccess).toBe(true);
  });

  it('should handle update errors', async () => {
    const error = { message: 'Not found', status: 404 };
    mockPut.mockRejectedValueOnce(error);

    const { result } = renderHook(() => useUpdatePerson(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      try {
        await result.current.mutateAsync({
          id: 'nonexistent',
          data: { name: 'Ghost' },
        });
      } catch (e) {
        // Expected to throw
      }
    });

    expect(result.current.isError).toBe(true);
  });
});

describe('useDeletePerson', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should delete a person successfully', async () => {
    mockDel.mockResolvedValueOnce(undefined);

    const { result } = renderHook(() => useDeletePerson(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      await result.current.mutateAsync('1');
    });

    expect(mockDel).toHaveBeenCalledWith('/people/1');
    expect(result.current.isSuccess).toBe(true);
  });

  it('should handle delete errors', async () => {
    const error = { message: 'Not found', status: 404 };
    mockDel.mockRejectedValueOnce(error);

    const { result } = renderHook(() => useDeletePerson(), {
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
