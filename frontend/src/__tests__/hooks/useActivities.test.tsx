/**
 * useActivities Hook Tests
 *
 * Tests for activity management hooks including list, CRUD operations,
 * archive, and derived hooks (map, by category, clinical, protected).
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
  useProtectedActivities,
} from '@/hooks/useActivities';
import type { Activity, ActivityListResponse } from '@/types/activity';

// Mock the api module
jest.mock('@/lib/api');

const mockedApi = api as jest.Mocked<typeof api>;

// Mock data
const mockActivities: Activity[] = [
  {
    id: 'activity-1',
    name: 'Inpatient Medicine',
    code: 'IM',
    displayAbbreviation: 'IM',
    activityCategory: 'clinical',
    fontColor: '#000000',
    backgroundColor: '#E3F2FD',
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
    activityCategory: 'educational',
    fontColor: '#000000',
    backgroundColor: '#FFF9C4',
    requiresSupervision: false,
    isProtected: true,
    countsTowardClinicalHours: false,
    displayOrder: 2,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
  },
  {
    id: 'activity-3',
    name: 'Clinic',
    code: 'CLINIC',
    displayAbbreviation: 'C',
    activityCategory: 'clinical',
    fontColor: '#000000',
    backgroundColor: '#C8E6C9',
    requiresSupervision: true,
    isProtected: false,
    countsTowardClinicalHours: true,
    displayOrder: 3,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
  },
];

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

describe('useActivities', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch all activities successfully', async () => {
    const mockResponse: ActivityListResponse = {
      activities: mockActivities,
      total: 3,
    };
    mockedApi.get.mockResolvedValueOnce(mockResponse);

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

  it('should fetch activities by category', async () => {
    const clinicalActivities = mockActivities.filter(
      (a) => a.activityCategory === 'clinical'
    );
    const mockResponse: ActivityListResponse = {
      activities: clinicalActivities,
      total: 2,
    };
    mockedApi.get.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(() => useActivities('clinical'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockedApi.get).toHaveBeenCalledWith('/activities?category=clinical');
    expect(result.current.data?.activities).toHaveLength(2);
  });

  it('should fetch including archived activities', async () => {
    const mockResponse: ActivityListResponse = {
      activities: mockActivities,
      total: 3,
    };
    mockedApi.get.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(
      () => useActivities('', { includeArchived: true }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockedApi.get).toHaveBeenCalledWith(
      '/activities?include_archived=true'
    );
  });

  it('should handle API errors', async () => {
    const apiError = { message: 'Failed to fetch', status: 500 };
    mockedApi.get.mockRejectedValueOnce(apiError);

    const { result } = renderHook(() => useActivities(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toEqual(apiError);
  });

  it('should handle empty results', async () => {
    const mockResponse: ActivityListResponse = {
      activities: [],
      total: 0,
    };
    mockedApi.get.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(() => useActivities(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.activities).toHaveLength(0);
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

  it('should not fetch if ID is empty', () => {
    const { result } = renderHook(() => useActivity(''), {
      wrapper: createWrapper(),
    });

    expect(result.current.isFetching).toBe(false);
    expect(mockedApi.get).not.toHaveBeenCalled();
  });
});

describe('useCreateActivity', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should create activity', async () => {
    const newActivity = mockActivities[0];
    mockedApi.post.mockResolvedValueOnce(newActivity);

    const { result } = renderHook(() => useCreateActivity(), {
      wrapper: createWrapper(),
    });

    const createData = {
      name: 'Inpatient Medicine',
      code: 'IM',
      displayAbbreviation: 'IM',
      activityCategory: 'clinical' as const,
      fontColor: '#000000',
      backgroundColor: '#E3F2FD',
      requiresSupervision: true,
      isProtected: false,
      countsTowardClinicalHours: true,
      displayOrder: 1,
    };

    result.current.mutate(createData);

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockedApi.post).toHaveBeenCalledWith('/activities', {
      name: 'Inpatient Medicine',
      code: 'IM',
      displayAbbreviation: 'IM',
      activity_category: 'clinical',
      fontColor: '#000000',
      backgroundColor: '#E3F2FD',
      requires_supervision: true,
      isProtected: false,
      counts_toward_clinical_hours: true,
      display_order: 1,
    });
  });

  it('should invalidate queries on success', async () => {
    mockedApi.post.mockResolvedValueOnce(mockActivities[0]);

    const queryClient = createTestQueryClient();
    const invalidateSpy = jest.spyOn(queryClient, 'invalidateQueries');

    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );

    const { result } = renderHook(() => useCreateActivity(), { wrapper });

    result.current.mutate({
      name: 'Test',
      code: 'TEST',
      displayAbbreviation: 'T',
      activityCategory: 'clinical',
      displayOrder: 1,
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(invalidateSpy).toHaveBeenCalled();
  });
});

describe('useUpdateActivity', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should update activity', async () => {
    const updatedActivity = {
      ...mockActivities[0],
      name: 'Updated Name',
    };
    mockedApi.put.mockResolvedValueOnce(updatedActivity);

    const { result } = renderHook(() => useUpdateActivity(), {
      wrapper: createWrapper(),
    });

    result.current.mutate({
      activityId: 'activity-1',
      data: { name: 'Updated Name' },
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockedApi.put).toHaveBeenCalledWith('/activities/activity-1', {
      name: 'Updated Name',
    });
  });

  it('should convert camelCase to snake_case for API', async () => {
    mockedApi.put.mockResolvedValueOnce(mockActivities[0]);

    const { result } = renderHook(() => useUpdateActivity(), {
      wrapper: createWrapper(),
    });

    result.current.mutate({
      activityId: 'activity-1',
      data: {
        requiresSupervision: false,
        countsTowardClinicalHours: false,
      },
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockedApi.put).toHaveBeenCalledWith('/activities/activity-1', {
      requires_supervision: false,
      counts_toward_clinical_hours: false,
    });
  });
});

describe('useDeleteActivity', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should delete activity', async () => {
    mockedApi.del.mockResolvedValueOnce(undefined);

    const { result } = renderHook(() => useDeleteActivity(), {
      wrapper: createWrapper(),
    });

    result.current.mutate('activity-1');

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockedApi.del).toHaveBeenCalledWith('/activities/activity-1');
  });

  it('should handle deletion errors', async () => {
    const apiError = {
      message: 'Cannot delete: activity in use',
      status: 409,
    };
    mockedApi.del.mockRejectedValueOnce(apiError);

    const { result } = renderHook(() => useDeleteActivity(), {
      wrapper: createWrapper(),
    });

    result.current.mutate('activity-1');

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toEqual(apiError);
  });
});

describe('useArchiveActivity', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should archive activity', async () => {
    const archivedActivity = {
      ...mockActivities[0],
      isArchived: true,
    };
    mockedApi.put.mockResolvedValueOnce(archivedActivity);

    const { result } = renderHook(() => useArchiveActivity(), {
      wrapper: createWrapper(),
    });

    result.current.mutate('activity-1');

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockedApi.put).toHaveBeenCalledWith(
      '/activities/activity-1/archive',
      {}
    );
  });
});

describe('useActivitiesMap', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should return activities as a map', async () => {
    const mockResponse: ActivityListResponse = {
      activities: mockActivities,
      total: 3,
    };
    mockedApi.get.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(() => useActivitiesMap(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current).toBeDefined();
    });

    expect(result.current?.['activity-1']).toEqual(mockActivities[0]);
    expect(result.current?.['activity-2']).toEqual(mockActivities[1]);
    expect(result.current?.['activity-3']).toEqual(mockActivities[2]);
  });
});

describe('useActivitiesByCategory', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should group activities by category', async () => {
    const mockResponse: ActivityListResponse = {
      activities: mockActivities,
      total: 3,
    };
    mockedApi.get.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(() => useActivitiesByCategory(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toBeDefined();
    expect(result.current.data?.clinical).toHaveLength(2);
    expect(result.current.data?.educational).toHaveLength(1);
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
    const mockResponse: ActivityListResponse = {
      activities: clinicalActivities,
      total: 2,
    };
    mockedApi.get.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(() => useClinicalActivities(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockedApi.get).toHaveBeenCalledWith('/activities?category=clinical');
  });
});

describe('useProtectedActivities', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should return only protected activities', async () => {
    const mockResponse: ActivityListResponse = {
      activities: mockActivities,
      total: 3,
    };
    mockedApi.get.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(() => useProtectedActivities(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toBeDefined();
    const protectedActivities = result.current.data || [];
    expect(protectedActivities).toHaveLength(1);
    expect(protectedActivities[0].code).toBe('LEC');
  });
});
