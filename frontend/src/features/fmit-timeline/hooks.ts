/**
 * React Query Hooks for FMIT Timeline Feature
 *
 * Provides data fetching, caching, and mutation hooks
 * for timeline visualization operations.
 */

import { useQuery, useQueryClient, UseQueryOptions } from '@tanstack/react-query';
import { get, ApiError } from '@/lib/api';
import type {
  TimelineResponse,
  FacultyTimelineResponse,
  TimelineFilters,
  TimelineMetrics,
  DateRange,
} from './types';

// Backend API response types
interface PersonApiResponse {
  id: string;
  name: string;
  specialties?: string[];
  primaryDuty?: string;
}

interface RotationTemplateApiResponse {
  id: string;
  name?: string;
  activityType?: string;
}

interface ApiListResponse<T> {
  items?: T[];
}

// ============================================================================
// Query Keys
// ============================================================================

export const timelineQueryKeys = {
  all: ['fmit-timeline'] as const,
  timeline: (filters?: TimelineFilters) => ['fmit-timeline', 'all', filters] as const,
  faculty: (facultyId: string, dateRange?: DateRange) =>
    ['fmit-timeline', 'faculty', facultyId, dateRange] as const,
  metrics: (dateRange?: DateRange) => ['fmit-timeline', 'metrics', dateRange] as const,
};

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Build query string from filters
 */
function buildQueryString(filters?: TimelineFilters): string {
  if (!filters) return '';

  const params = new URLSearchParams();

  if (filters.startDate) {
    params.set('start_date', filters.startDate);
  }
  if (filters.endDate) {
    params.set('end_date', filters.endDate);
  }
  if (filters.facultyIds?.length) {
    params.set('faculty_ids', filters.facultyIds.join(','));
  }
  if (filters.rotationIds?.length) {
    params.set('rotation_ids', filters.rotationIds.join(','));
  }
  if (filters.specialty) {
    params.set('specialty', filters.specialty);
  }
  if (filters.workloadStatus?.length) {
    params.set('workload_status', filters.workloadStatus.join(','));
  }
  if (filters.viewMode) {
    params.set('view_mode', filters.viewMode);
  }

  return params.toString();
}

// ============================================================================
// Query Hooks
// ============================================================================

/**
 * Fetch FMIT timeline data with filters
 *
 * @param filters - Timeline filters (date range, faculty, rotations, etc.)
 * @param options - React Query options
 * @returns Timeline data with faculty rows and assignments
 *
 * @example
 * const { data, isLoading } = useFMITTimeline({
 *   startDate: '2024-07-01',
 *   endDate: '2024-12-31',
 *   viewMode: 'monthly'
 * });
 */
export function useFMITTimeline(
  filters: TimelineFilters,
  options?: Omit<UseQueryOptions<TimelineResponse, ApiError>, 'queryKey' | 'queryFn'>
) {
  const queryString = buildQueryString(filters);

  return useQuery<TimelineResponse, ApiError>({
    queryKey: timelineQueryKeys.timeline(filters),
    queryFn: () =>
      get<TimelineResponse>(`/visualization/fmit-timeline${queryString ? `?${queryString}` : ''}`),
    staleTime: 60 * 1000, // 1 minute
    gcTime: 5 * 60 * 1000, // 5 minutes
    ...options,
  });
}

/**
 * Fetch timeline for a single faculty member
 *
 * @param facultyId - Faculty member ID
 * @param dateRange - Optional date range filter
 * @param options - React Query options
 * @returns Faculty timeline with assignments and metrics
 *
 * @example
 * const { data } = useFacultyTimeline('faculty-123', {
 *   start: '2024-07-01',
 *   end: '2024-12-31'
 * });
 */
export function useFacultyTimeline(
  facultyId: string,
  dateRange?: DateRange,
  options?: Omit<UseQueryOptions<FacultyTimelineResponse, ApiError>, 'queryKey' | 'queryFn'>
) {
  const params = new URLSearchParams();
  if (dateRange?.start) {
    params.set('start_date', dateRange.start);
  }
  if (dateRange?.end) {
    params.set('end_date', dateRange.end);
  }
  const queryString = params.toString();

  return useQuery<FacultyTimelineResponse, ApiError>({
    queryKey: timelineQueryKeys.faculty(facultyId, dateRange),
    queryFn: () =>
      get<FacultyTimelineResponse>(
        `/visualization/fmit-timeline/faculty/${facultyId}${queryString ? `?${queryString}` : ''}`
      ),
    staleTime: 60 * 1000, // 1 minute
    gcTime: 5 * 60 * 1000, // 5 minutes
    enabled: !!facultyId,
    ...options,
  });
}

/**
 * Fetch timeline metrics (aggregate statistics)
 *
 * @param dateRange - Optional date range filter
 * @param options - React Query options
 * @returns Aggregate metrics for timeline period
 *
 * @example
 * const { data: metrics } = useTimelineMetrics({
 *   start: '2024-07-01',
 *   end: '2024-12-31'
 * });
 */
export function useTimelineMetrics(
  dateRange?: DateRange,
  options?: Omit<UseQueryOptions<TimelineMetrics, ApiError>, 'queryKey' | 'queryFn'>
) {
  const params = new URLSearchParams();
  if (dateRange?.start) {
    params.set('start_date', dateRange.start);
  }
  if (dateRange?.end) {
    params.set('end_date', dateRange.end);
  }
  const queryString = params.toString();

  return useQuery<TimelineMetrics, ApiError>({
    queryKey: timelineQueryKeys.metrics(dateRange),
    queryFn: () =>
      get<TimelineMetrics>(
        `/visualization/fmit-timeline/metrics${queryString ? `?${queryString}` : ''}`
      ),
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
    ...options,
  });
}

/**
 * Fetch available faculty for filtering
 */
export function useAvailableFaculty(
  specialty?: string,
  options?: Omit<
    UseQueryOptions<PersonApiResponse[] | ApiListResponse<PersonApiResponse>, ApiError, Array<{ id: string; name: string; specialty: string }>>,
    'queryKey' | 'queryFn' | 'select'
  >
) {
  const params = specialty ? `?specialty=${encodeURIComponent(specialty)}` : '';

  return useQuery({
    queryKey: ['fmit-timeline', 'faculty-list', specialty],
    queryFn: () => get<PersonApiResponse[] | ApiListResponse<PersonApiResponse>>(`/people/faculty${params}`),
    staleTime: 10 * 60 * 1000, // 10 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    select: (data: PersonApiResponse[] | ApiListResponse<PersonApiResponse>): Array<{ id: string; name: string; specialty: string }> => {
      // Handle both array response and object with items array
      const items = Array.isArray(data) ? data : data.items || [];
      return items.map((person: PersonApiResponse) => ({
        id: person.id,
        name: person.name,
        specialty: person.specialties?.[0] || person.primaryDuty || 'General',
      }));
    },
    ...options,
  });
}

/**
 * Fetch available rotations for filtering
 */
export function useAvailableRotations(
  options?: Omit<UseQueryOptions<RotationTemplateApiResponse[] | ApiListResponse<RotationTemplateApiResponse>, ApiError, Array<{ id: string; name: string }>>, 'queryKey' | 'queryFn' | 'select'>
) {
  return useQuery({
    queryKey: ['fmit-timeline', 'rotations'],
    queryFn: () => get<RotationTemplateApiResponse[] | ApiListResponse<RotationTemplateApiResponse>>('/rotation-templates'),
    staleTime: 10 * 60 * 1000, // 10 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    select: (data: RotationTemplateApiResponse[] | ApiListResponse<RotationTemplateApiResponse>): Array<{ id: string; name: string }> => {
      // Handle both array response and object with items array
      const items = Array.isArray(data) ? data : data.items || [];
      return items.map((template: RotationTemplateApiResponse) => ({
        id: template.id,
        name: template.name || template.activityType || '',
      }));
    },
    ...options,
  });
}

/**
 * Fetch academic years for year selector
 */
export function useAcademicYears(
  options?: Omit<
    UseQueryOptions<Array<{ id: string; label: string; startDate: string; endDate: string }>, ApiError>,
    'queryKey' | 'queryFn'
  >
) {
  return useQuery<Array<{ id: string; label: string; startDate: string; endDate: string }>, ApiError>({
    queryKey: ['fmit-timeline', 'academic-years'],
    queryFn: async () => {
      // Generate academic years based on current date
      // In a real implementation, this might come from an API
      const currentYear = new Date().getFullYear();
      const years = [];

      for (let i = -2; i <= 2; i++) {
        const year = currentYear + i;
        years.push({
          id: `${year}-${year + 1}`,
          label: `${year}-${year + 1}`,
          startDate: `${year}-07-01`,
          endDate: `${year + 1}-06-30`,
        });
      }

      return years;
    },
    staleTime: 30 * 60 * 1000, // 30 minutes
    gcTime: 60 * 60 * 1000, // 1 hour
    ...options,
  });
}

// ============================================================================
// Utility Hooks
// ============================================================================

/**
 * Prefetch timeline data for better UX
 */
export function usePrefetchTimeline() {
  const queryClient = useQueryClient();

  return (filters: TimelineFilters) => {
    const queryString = buildQueryString(filters);
    queryClient.prefetchQuery({
      queryKey: timelineQueryKeys.timeline(filters),
      queryFn: () =>
        get<TimelineResponse>(`/visualization/fmit-timeline${queryString ? `?${queryString}` : ''}`),
      staleTime: 60 * 1000,
    });
  };
}

/**
 * Invalidate all timeline queries (useful after schedule changes)
 */
export function useInvalidateTimeline() {
  const queryClient = useQueryClient();

  return () => {
    queryClient.invalidateQueries({ queryKey: timelineQueryKeys.all });
  };
}
