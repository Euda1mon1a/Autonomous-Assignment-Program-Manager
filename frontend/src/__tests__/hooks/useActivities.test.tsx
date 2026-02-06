/**
 * useActivities Hook Tests
 *
 * Tests for activity management hooks including list, detail, CRUD,
 * archive, and utility hooks like activitiesMap and activitiesByCategory.
 */
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';
import * as api from '@/lib/api';
import {
  useActivities,
  useActivity,
  useCreateActivity,
  useUpdateActivity,
  useDeleteActivity,
  useArchiveActivity,
  useActivitiesMap,
  useActivitiesByCategory,
  useClinicalActivities,
} from '@/hooks/useActivities';

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
const mockActivities = [
  {
    id: 'activity-1',
    name: 'Inpatient Medicine',
    code: 'IM',
    displayAbbreviation: 'IM',
    activityCategory: 'clinical' as const,
    fontColor: '#000000',
    backgroundColor: '#FFFFFF',
    requiresSupervision: true,
    isProtected: false,
    countsTowardClinicalHours: true,
    displayOrder: 1,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
  },
  {
    id: 'activity-2',
    name: 'Lecture',
    code: 'LEC',
    displayAbbreviation: 'LEC',
    activityCategory: 'educational' as const,
    fontColor: '#0000FF',
    backgroundColor: '#E0E0FF',
    requiresSupervision: false,
    isProtected: true,
    countsTowardClinicalHours: false,
    displayOrder: 2,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
  },
  {
    id: 'activity-3',
    name: 'Continuity Clinic',
    code: 'C',
    displayAbbreviation: 'C',
    activityCategory: 'clinical' as const,
    fontColor: '#00FF00',
    backgroundColor: '#E0FFE0',
    requiresSupervision: true,
    isProtected: false,
    countsTowardClinicalHours: true,
    displayOrder: 3,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
  },
];

describe('useActivities', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch all activities successfully', async () => {
    mockedApi.get.mockResolvedValueOnce({
      activities: mockActivities,
      total: 3,
    });

    const { result } = renderHook(() => useActivities(), {
      wrapper: createWrapper(),
    });

    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.activities).toHaveLength(3);
    expect(result.current.data?.total).toBe(3);
    expect(mockedApi.get).toHaveBeenCalledWith('/activities');
  });

  it('should filter by category using snake_case query param', async () => {
    const clinicalActivities = mockActivities.filter(
      (a) => a.activityCategory === 'clinical'
    );

    mockedApi.get.mockResolvedValueOnce({
      activities: clinicalActivities,
      total: 2,
    });

    const { result } = renderHook(() => useActivities('clinical'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.activities).toHaveLength(2);
    expect(mockedApi.get).toHaveBeenCalledWith(
      expect.stringContaining('category=clinical')
    );
  });

  it('should include archived activities when requested', async () => {
    mockedApi.get.mockResolvedValueOnce({
      activities: mockActivities,
      total: 3,
    });

    const { result } = renderHook(
      () => useActivities(undefined, { includeArchived: true }),
      {
        wrapper: createWrapper(),
      }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    // URL param must use snake_case
    expect(mockedApi.get).toHaveBeenCalledWith(
      expect.stringContaining('include_archived=true')
    );
  });

  it('should handle empty results', async () => {
    mockedApi.get.mockResolvedValueOnce({
      activities: [],
      total: 0,
    });

    const { result } = renderHook(() => useActivities(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.activities).toHaveLength(0);
  });

  it('should handle API errors', async () => {
    const apiError = { message: 'Server error', status: 500 };
    mockedApi.get.mockRejectedValueOnce(apiError);

    const { result } = renderHook(() => useActivities(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toEqual(apiError);
  });
});

describe('useActivity', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch single activity', async () => {
    mockedApi.get.mockResolvedValueOnce(mockActivities[0]);

    const { result } = renderHook(() => useActivity('activity-1'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockActivities[0]);
    expect(mockedApi.get).toHaveBeenCalledWith('/activities/activity-1');
  });

  it('should be disabled when id is not provided', () => {
    const { result } = renderHook(() => useActivity(''), {
      wrapper: createWrapper(),
    });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.isFetching).toBe(false);
  });
});

describe('useCreateActivity', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should create activity and invalidate cache', async () => {
    const newActivity = mockActivities[0];
    mockedApi.post.mockResolvedValueOnce(newActivity);

    const queryClient = createTestQueryClient();
    const invalidateSpy = jest.spyOn(queryClient, 'invalidateQueries');

    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );

    const { result } = renderHook(() => useCreateActivity(), { wrapper });

    const createData = {
      name: 'Inpatient Medicine',
      code: 'IM',
      displayAbbreviation: 'IM',
      activityCategory: 'clinical' as const,
      fontColor: '#000000',
      backgroundColor: '#FFFFFF',
      requiresSupervision: true,
      isProtected: false,
      countsTowardClinicalHours: true,
      displayOrder: 1,
    };

    await result.current.mutateAsync(createData);

    expect(mockedApi.post).toHaveBeenCalledWith('/activities', expect.any(Object));
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ['activities'],
    });
  });
});

describe('useUpdateActivity', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should update activity and invalidate caches', async () => {
    const updatedActivity = { ...mockActivities[0], name: 'Updated Name' };
    mockedApi.put.mockResolvedValueOnce(updatedActivity);

    const queryClient = createTestQueryClient();
    const invalidateSpy = jest.spyOn(queryClient, 'invalidateQueries');

    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );

    const { result } = renderHook(() => useUpdateActivity(), { wrapper });

    const updateData = {
      name: 'Updated Name',
    };

    await result.current.mutateAsync({
      activityId: 'activity-1',
      data: updateData,
    });

    expect(mockedApi.put).toHaveBeenCalledWith(
      '/activities/activity-1',
      expect.any(Object)
    );
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ['activities'],
    });
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ['activities', 'detail', 'activity-1'],
    });
  });
});

describe('useDeleteActivity', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should delete activity and invalidate cache', async () => {
    mockedApi.del.mockResolvedValueOnce(undefined);

    const queryClient = createTestQueryClient();
    const invalidateSpy = jest.spyOn(queryClient, 'invalidateQueries');

    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );

    const { result } = renderHook(() => useDeleteActivity(), { wrapper });

    await result.current.mutateAsync('activity-1');

    expect(mockedApi.del).toHaveBeenCalledWith('/activities/activity-1');
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ['activities'],
    });
  });
});

describe('useArchiveActivity', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should archive activity and invalidate cache', async () => {
    const archivedActivity = { ...mockActivities[0], isArchived: true };
    mockedApi.put.mockResolvedValueOnce(archivedActivity);

    const queryClient = createTestQueryClient();
    const invalidateSpy = jest.spyOn(queryClient, 'invalidateQueries');

    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );

    const { result } = renderHook(() => useArchiveActivity(), { wrapper });

    await result.current.mutateAsync('activity-1');

    expect(mockedApi.put).toHaveBeenCalledWith(
      '/activities/activity-1/archive',
      {}
    );
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ['activities'],
    });
  });
});

describe('useActivitiesMap', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should return activities map keyed by id', async () => {
    mockedApi.get.mockResolvedValueOnce({
      activities: mockActivities,
      total: 3,
    });

    const { result } = renderHook(() => useActivitiesMap(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current).toBeDefined();
    });

    const map = result.current;
    expect(map?.['activity-1']).toEqual(mockActivities[0]);
    expect(map?.['activity-2']).toEqual(mockActivities[1]);
    expect(map?.['activity-3']).toEqual(mockActivities[2]);
  });

  it('should filter map by category', async () => {
    const clinicalActivities = mockActivities.filter(
      (a) => a.activityCategory === 'clinical'
    );

    mockedApi.get.mockResolvedValueOnce({
      activities: clinicalActivities,
      total: 2,
    });

    const { result } = renderHook(() => useActivitiesMap('clinical'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current).toBeDefined();
    });

    const map = result.current;
    expect(Object.keys(map || {})).toHaveLength(2);
    expect(map?.['activity-1']).toBeDefined();
    expect(map?.['activity-2']).toBeUndefined(); // Educational, not clinical
  });
});

describe('useActivitiesByCategory', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should group activities by category', async () => {
    mockedApi.get.mockResolvedValueOnce({
      activities: mockActivities,
      total: 3,
    });

    const { result } = renderHook(() => useActivitiesByCategory(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.data).toBeDefined();
    });

    const grouped = result.current.data;
    expect(grouped?.clinical).toHaveLength(2);
    expect(grouped?.educational).toHaveLength(1);

    // Check correct activities in each group
    expect(grouped?.clinical?.map((a) => a.code)).toContain('IM');
    expect(grouped?.clinical?.map((a) => a.code)).toContain('C');
    expect(grouped?.educational?.[0].code).toBe('LEC');
  });

  it('should handle empty categories', async () => {
    mockedApi.get.mockResolvedValueOnce({
      activities: [mockActivities[0]],
      total: 1,
    });

    const { result } = renderHook(() => useActivitiesByCategory(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.data).toBeDefined();
    });

    const grouped = result.current.data;
    expect(grouped?.clinical).toHaveLength(1);
    expect(grouped?.educational).toBeUndefined();
  });
});

describe('useClinicalActivities', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch only clinical activities', async () => {
    const clinicalActivities = mockActivities.filter(
      (a) => a.activityCategory === 'clinical'
    );

    mockedApi.get.mockResolvedValueOnce({
      activities: clinicalActivities,
      total: 2,
    });

    const { result } = renderHook(() => useClinicalActivities(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.activities).toHaveLength(2);
    expect(result.current.data?.activities.every(
      (a) => a.activityCategory === 'clinical'
    )).toBe(true);
    expect(mockedApi.get).toHaveBeenCalledWith(
      expect.stringContaining('category=clinical')
    );
  });
});
