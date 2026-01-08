/**
 * Absence Management Hooks
 *
 * Comprehensive hooks for managing resident and faculty absences (vacation,
 * conferences, illness, military deployment, etc.) with React Query caching,
 * military leave support, and leave balance tracking.
 *
 * @module hooks/useAbsences
 */
import { useQuery, useMutation, useQueryClient, UseQueryOptions } from '@tanstack/react-query'
import { get, post, put, del, ApiError } from '@/lib/api'
import type {
  Absence,
  AbsenceCreate,
  AbsenceUpdate,
  AbsenceType,
  AwayFromProgramSummary,
  AllResidentsAwayStatus,
  AwayFromProgramCheck,
} from '@/types/api'

// ============================================================================
// Types
// ============================================================================

/**
 * Generic list response with pagination metadata
 */
export interface ListResponse<T> {
  /** Array of items in the response */
  items: T[]
  /** Total number of items across all pages */
  total: number
  /** Current page number (optional for non-paginated responses) */
  page?: number
  /** Items per page (optional for non-paginated responses) */
  page_size?: number
}

/**
 * Filters for querying absences
 */
export interface AbsenceFilters {
  /** Filter by specific person ID */
  person_id?: string
  /** Filter absences starting from this date (ISO 8601 format: YYYY-MM-DD) */
  start_date?: string
  /** Filter absences ending by this date (ISO 8601 format: YYYY-MM-DD) */
  end_date?: string
  /** Filter by specific absence type */
  absence_type?: string | AbsenceType
}

/**
 * Status of an absence approval workflow
 */
export enum AbsenceStatus {
  /** Absence request is pending review */
  PENDING = 'pending',
  /** Absence request has been approved */
  APPROVED = 'approved',
  /** Absence request has been rejected */
  REJECTED = 'rejected',
  /** Absence request has been cancelled */
  CANCELLED = 'cancelled',
}

/**
 * Leave balance information for a person
 */
export interface LeaveBalance {
  /** ID of the person */
  person_id: string
  /** Name of the person */
  person_name: string
  /** Available vacation days remaining */
  vacation_days: number
  /** Available sick days remaining */
  sick_days: number
  /** Available personal days remaining */
  personal_days: number
  /** Total leave days taken this year */
  total_days_taken: number
  /** Total leave days allocated for the year */
  total_days_allocated: number
  /** Timestamp when balance was last updated */
  last_updated?: string
}

/**
 * Request for approving an absence
 */
export interface AbsenceApprovalRequest {
  /** ID of the absence to approve */
  absence_id: string
  /** Whether to approve (true) or reject (false) */
  approved: boolean
  /** Optional comments about the decision */
  comments?: string
  /** ID of the user approving/rejecting */
  approved_by?: string
}

/**
 * Calendar entry showing leave information
 */
export interface LeaveCalendarEntry {
  /** ID of the faculty/person */
  faculty_id: string
  /** Name of the faculty/person */
  faculty_name: string
  /** Type of leave */
  leave_type: string
  /** Start date of leave */
  start_date: string
  /** End date of leave */
  end_date: string
  /** Whether this leave blocks assignments */
  is_blocking: boolean
  /** Whether there's a conflict with FMIT */
  has_fmit_conflict: boolean
}

/**
 * Response from leave calendar endpoint
 */
export interface LeaveCalendarResponse {
  /** Start date of calendar period */
  start_date: string
  /** End date of calendar period */
  end_date: string
  /** Array of leave entries in the period */
  entries: LeaveCalendarEntry[]
  /** Total number of conflicts detected */
  conflict_count: number
}

// ============================================================================
// Query Keys
// ============================================================================

/**
 * Query key factory for absence-related queries.
 * Provides consistent, type-safe query keys for React Query.
 */
export const absenceQueryKeys = {
  /** All absence queries */
  all: () => ['absences'] as const,
  /** List queries with optional filters */
  lists: () => [...absenceQueryKeys.all(), 'list'] as const,
  /** List query with specific filters */
  list: (filters?: AbsenceFilters) => [...absenceQueryKeys.lists(), filters] as const,
  /** Detail queries */
  details: () => [...absenceQueryKeys.all(), 'detail'] as const,
  /** Single absence by ID */
  detail: (id: string) => [...absenceQueryKeys.details(), id] as const,
  /** Leave balance queries */
  balances: () => [...absenceQueryKeys.all(), 'balance'] as const,
  /** Leave balance for specific person */
  balance: (personId: string) => [...absenceQueryKeys.balances(), personId] as const,
  /** Leave calendar queries */
  calendars: () => [...absenceQueryKeys.all(), 'calendar'] as const,
  /** Leave calendar for date range */
  calendar: (startDate: string, endDate: string) =>
    [...absenceQueryKeys.calendars(), startDate, endDate] as const,
  /** Military leave queries */
  military: () => [...absenceQueryKeys.all(), 'military'] as const,
}

// ============================================================================
// Absence Query Hooks
// ============================================================================

/**
 * Fetches a single absence record by ID.
 *
 * This hook retrieves complete details for a single absence including
 * dates, type, reason, deployment orders, and approval status. Used for
 * viewing and editing absence records.
 *
 * @param id - The UUID of the absence to fetch
 * @param options - Optional React Query configuration options
 * @returns Query result containing:
 *   - `data`: The absence record with all details
 *   - `isLoading`: Whether the fetch is in progress
 *   - `isFetching`: Whether any fetch is in progress (including background)
 *   - `error`: Any error that occurred
 *   - `refetch`: Function to manually refetch the absence
 *
 * @example
 * ```tsx
 * function AbsenceDetail({ absenceId }: Props) {
 *   const { data, isLoading, error } = useAbsence(absenceId);
 *
 *   if (isLoading) return <LoadingState />;
 *   if (error) return <ErrorMessage error={error} />;
 *   if (!data) return <NotFound />;
 *
 *   return (
 *     <AbsenceCard
 *       absence={data}
 *       onEdit={() => navigate(`/absences/${absenceId}/edit`)}
 *     />
 *   );
 * }
 * ```
 *
 * @see useAbsenceList - For fetching multiple absences
 * @see useAbsenceUpdate - For modifying absence details
 */
export function useAbsence(
  id: string,
  options?: Omit<UseQueryOptions<Absence, ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<Absence, ApiError>({
    queryKey: absenceQueryKeys.detail(id),
    queryFn: () => get<Absence>(`/absences/${id}`),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    enabled: !!id,
    ...options,
  })
}

/**
 * Fetches a list of absences with comprehensive filtering support.
 *
 * This hook retrieves absence records with support for filtering by person,
 * date range, and absence type. Absences include vacation, conferences,
 * illness, military deployments, TDY, and other time off. Results are used
 * by the schedule generator to ensure people aren't assigned during
 * unavailable periods.
 *
 * @param filters - Optional filters for person, dates, and absence type
 * @param options - Optional React Query configuration options
 * @returns Query result containing:
 *   - `data`: List response with absences and total count
 *   - `isLoading`: Whether the initial fetch is in progress
 *   - `isFetching`: Whether any fetch is in progress
 *   - `error`: Any error that occurred
 *   - `refetch`: Function to manually refetch absences
 *
 * @example
 * ```tsx
 * // Fetch all absences for a specific person
 * function PersonAbsences({ personId }: Props) {
 *   const { data, isLoading } = useAbsenceList({ person_id: personId });
 *
 *   if (isLoading) return <Spinner />;
 *
 *   return (
 *     <AbsenceTable
 *       absences={data.items}
 *       total={data.total}
 *     />
 *   );
 * }
 * ```
 *
 * @example
 * ```tsx
 * // Filter by date range and absence type
 * function VacationCalendar() {
 *   const { data } = useAbsenceList({
 *     start_date: '2024-01-01',
 *     end_date: '2024-12-31',
 *     absence_type: 'vacation',
 *   });
 *
 *   return <Calendar absences={data.items} />;
 * }
 * ```
 *
 * @see useAbsence - For fetching a single absence
 * @see useAbsences - Simplified hook filtering by person only
 * @see useMilitaryLeave - Specialized hook for military/deployment absences
 */
export function useAbsenceList(
  filters?: AbsenceFilters,
  options?: Omit<UseQueryOptions<ListResponse<Absence>, ApiError>, 'queryKey' | 'queryFn'>
) {
  const params = new URLSearchParams()
  if (filters?.person_id) params.set('person_id', filters.person_id)
  if (filters?.start_date) params.set('start_date', filters.start_date)
  if (filters?.end_date) params.set('end_date', filters.end_date)
  if (filters?.absence_type) params.set('absence_type', filters.absence_type.toString())
  const queryString = params.toString()

  return useQuery<ListResponse<Absence>, ApiError>({
    queryKey: absenceQueryKeys.list(filters),
    queryFn: () => get<ListResponse<Absence>>(`/absences${queryString ? `?${queryString}` : ''}`),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    ...options,
  })
}

/**
 * Fetches absences with optional filtering by person (simplified version).
 *
 * This is a simplified hook that filters absences by person ID only.
 * For more comprehensive filtering including date ranges and absence types,
 * use `useAbsenceList` instead.
 *
 * @param personId - Optional person ID to filter absences
 * @param options - Optional React Query configuration options
 * @returns Query result with absence list
 *
 * @deprecated Use `useAbsenceList({ person_id: personId })` for better type safety
 *
 * @example
 * ```tsx
 * function PersonAbsenceList({ residentId }: Props) {
 *   const { data, isLoading } = useAbsences(residentId);
 *
 *   if (isLoading) return <Spinner />;
 *
 *   return <AbsenceList absences={data.items} />;
 * }
 * ```
 *
 * @see useAbsenceList - For comprehensive filtering options
 * @see useAbsence - For fetching a single absence
 */
export function useAbsences(
  personId?: number,
  options?: Omit<UseQueryOptions<ListResponse<Absence>, ApiError>, 'queryKey' | 'queryFn'>
) {
  const params = personId !== undefined ? `?person_id=${personId}` : ''

  return useQuery<ListResponse<Absence>, ApiError>({
    queryKey: ['absences', personId],
    queryFn: () => get<ListResponse<Absence>>(`/absences${params}`),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    ...options,
  })
}

/**
 * Fetches leave calendar showing all absences in a date range.
 *
 * This hook retrieves a calendar view of leave records including conflict
 * indicators for FMIT (Force Management Integrated Tool) overlap. Useful
 * for visualizing team availability and identifying coverage gaps.
 *
 * @param startDate - Start date for calendar period (ISO 8601: YYYY-MM-DD)
 * @param endDate - End date for calendar period (ISO 8601: YYYY-MM-DD)
 * @param options - Optional React Query configuration options
 * @returns Query result containing:
 *   - `data`: Calendar response with entries and conflict count
 *   - `isLoading`: Whether the fetch is in progress
 *   - `error`: Any error that occurred
 *
 * @example
 * ```tsx
 * function LeaveCalendarView() {
 *   const { data, isLoading } = useLeaveCalendar('2024-01-01', '2024-01-31');
 *
 *   if (isLoading) return <CalendarSkeleton />;
 *
 *   return (
 *     <Calendar
 *       entries={data.entries}
 *       conflicts={data.conflict_count}
 *       startDate={data.start_date}
 *       endDate={data.end_date}
 *     />
 *   );
 * }
 * ```
 *
 * @see useAbsenceList - For list view of absences
 */
export function useLeaveCalendar(
  startDate: string,
  endDate: string,
  options?: Omit<UseQueryOptions<LeaveCalendarResponse, ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<LeaveCalendarResponse, ApiError>({
    queryKey: absenceQueryKeys.calendar(startDate, endDate),
    queryFn: () => get<LeaveCalendarResponse>(
      `/leave/calendar?start_date=${startDate}&end_date=${endDate}`
    ),
    staleTime: 2 * 60 * 1000, // 2 minutes (shorter for calendar views)
    gcTime: 10 * 60 * 1000, // 10 minutes
    enabled: !!startDate && !!endDate,
    ...options,
  })
}

/**
 * Fetches military-specific leave including deployments and TDY.
 *
 * This specialized hook retrieves only military-related absences such as
 * deployments and temporary duty (TDY) assignments. Useful for military
 * medical facilities tracking operational readiness and personnel availability.
 *
 * @param personId - Optional person ID to filter military leave
 * @param options - Optional React Query configuration options
 * @returns Query result containing:
 *   - `data`: List of military/deployment absences
 *   - `isLoading`: Whether the fetch is in progress
 *   - `error`: Any error that occurred
 *
 * @example
 * ```tsx
 * function MilitaryLeaveTracker({ facultyId }: Props) {
 *   const { data, isLoading } = useMilitaryLeave(facultyId);
 *
 *   if (isLoading) return <Spinner />;
 *
 *   const deployments = data.items.filter(a => a.absence_type === 'deployment');
 *   const tdyAssignments = data.items.filter(a => a.absence_type === 'tdy');
 *
 *   return (
 *     <div>
 *       <DeploymentList deployments={deployments} />
 *       <TDYList assignments={tdyAssignments} />
 *     </div>
 *   );
 * }
 * ```
 *
 * @see useAbsenceList - For all absence types with flexible filtering
 * @see useAbsence - For single absence details
 */
export function useMilitaryLeave(
  personId?: string,
  options?: Omit<UseQueryOptions<ListResponse<Absence>, ApiError>, 'queryKey' | 'queryFn'>
) {
  const params = new URLSearchParams()
  if (personId) params.set('person_id', personId)
  // Filter for military-specific absence types
  // Note: Backend should support comma-separated values or we fetch and filter client-side
  const queryString = params.toString()

  return useQuery<ListResponse<Absence>, ApiError>({
    queryKey: [...absenceQueryKeys.military(), personId],
    queryFn: async () => {
      const response = await get<ListResponse<Absence>>(
        `/absences${queryString ? `?${queryString}` : ''}`
      )
      // Client-side filtering for military leave types
      return {
        ...response,
        items: response.items.filter(
          absence => absence.absence_type === 'deployment' || absence.absence_type === 'tdy'
        ),
        total: response.items.filter(
          absence => absence.absence_type === 'deployment' || absence.absence_type === 'tdy'
        ).length,
      }
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    ...options,
  })
}

/**
 * Fetches leave balance for a specific person.
 *
 * This hook retrieves the available leave days (vacation, sick, personal)
 * for a person, including days taken and remaining. Useful for tracking
 * leave accrual and ensuring personnel don't exceed their allocated time off.
 *
 * Note: This endpoint may not be implemented yet on the backend.
 * Returns mock data or 404 until backend support is added.
 *
 * @param personId - The UUID of the person to fetch balance for
 * @param options - Optional React Query configuration options
 * @returns Query result containing:
 *   - `data`: Leave balance with available days and usage
 *   - `isLoading`: Whether the fetch is in progress
 *   - `error`: Any error that occurred (may be 404 if not implemented)
 *
 * @example
 * ```tsx
 * function LeaveBalanceWidget({ personId }: Props) {
 *   const { data, isLoading, error } = useLeaveBalance(personId);
 *
 *   if (isLoading) return <Skeleton />;
 *   if (error?.status === 404) return <NotImplementedMessage />;
 *
 *   return (
 *     <BalanceCard
 *       vacation={data.vacation_days}
 *       sick={data.sick_days}
 *       personal={data.personal_days}
 *       used={data.total_days_taken}
 *       total={data.total_days_allocated}
 *     />
 *   );
 * }
 * ```
 *
 * @see useAbsenceList - For viewing actual absences taken
 */
export function useLeaveBalance(
  personId: string,
  options?: Omit<UseQueryOptions<LeaveBalance, ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<LeaveBalance, ApiError>({
    queryKey: absenceQueryKeys.balance(personId),
    queryFn: () => get<LeaveBalance>(`/absences/balance/${personId}`),
    staleTime: 10 * 60 * 1000, // 10 minutes (balance doesn't change frequently)
    gcTime: 60 * 60 * 1000, // 1 hour
    enabled: !!personId,
    retry: (failureCount, error) => {
      // Don't retry on 404 (endpoint not implemented)
      if (error?.status === 404) return false
      return failureCount < 2
    },
    ...options,
  })
}

// ============================================================================
// Absence Mutation Hooks
// ============================================================================

/**
 * Creates a new absence record for a person.
 *
 * This mutation hook records planned or unplanned absences that affect
 * schedule availability. Creating an absence automatically invalidates
 * schedule queries since it impacts availability and may require
 * coverage adjustments. Supports all absence types including vacation,
 * sick leave, conferences, military deployments, and TDY.
 *
 * @returns Mutation object containing:
 *   - `mutate`: Function to create an absence
 *   - `mutateAsync`: Async version returning a Promise
 *   - `isPending`: Whether creation is in progress
 *   - `error`: Any error that occurred (e.g., overlapping absences)
 *   - `data`: The created absence with generated ID
 *
 * @example
 * ```tsx
 * function RequestAbsenceForm({ personId }: Props) {
 *   const { mutate, isPending } = useAbsenceCreate();
 *
 *   const handleSubmit = (formData: AbsenceCreate) => {
 *     mutate(formData, {
 *       onSuccess: (newAbsence) => {
 *         toast.success('Absence request submitted');
 *         navigate('/absences');
 *       },
 *       onError: (error) => {
 *         if (error.status === 409) {
 *           toast.error('Overlapping absence already exists');
 *         } else {
 *           toast.error(`Failed to create absence: ${error.message}`);
 *         }
 *       },
 *     });
 *   };
 *
 *   return <AbsenceForm onSubmit={handleSubmit} loading={isPending} />;
 * }
 * ```
 *
 * @example
 * ```tsx
 * // Create military deployment absence
 * function DeploymentForm() {
 *   const { mutate } = useAbsenceCreate();
 *
 *   const handleDeploy = () => {
 *     mutate({
 *       person_id: 'abc-123',
 *       start_date: '2024-03-01',
 *       end_date: '2024-09-01',
 *       absence_type: 'deployment',
 *       deployment_orders: true,
 *       notes: 'Overseas deployment',
 *     });
 *   };
 * }
 * ```
 *
 * @see useAbsenceUpdate - For modifying existing absences
 * @see useAbsenceList - List is auto-refreshed after creation
 */
export function useAbsenceCreate() {
  const queryClient = useQueryClient()

  return useMutation<Absence, ApiError, AbsenceCreate>({
    mutationFn: (data) => post<Absence>('/absences', data),
    onSuccess: () => {
      // Invalidate all absence-related queries
      queryClient.invalidateQueries({ queryKey: absenceQueryKeys.all() })
      // Absences affect schedule availability
      queryClient.invalidateQueries({ queryKey: ['schedule'] })
      // May affect leave balances
      queryClient.invalidateQueries({ queryKey: absenceQueryKeys.balances() })
    },
  })
}

/**
 * Updates an existing absence record with new details.
 *
 * This mutation hook modifies absence information such as dates, type,
 * or reason. Useful for adjusting vacation dates, updating TDY locations,
 * adding deployment orders, or correcting absence details. Automatically
 * refreshes schedule data and leave balances.
 *
 * @returns Mutation object containing:
 *   - `mutate`: Function to update an absence
 *   - `mutateAsync`: Async version returning a Promise
 *   - `isPending`: Whether update is in progress
 *   - `error`: Any error that occurred
 *   - `data`: The updated absence
 *
 * @example
 * ```tsx
 * function EditAbsenceForm({ absenceId }: Props) {
 *   const { mutate, isPending } = useAbsenceUpdate();
 *   const { data: absence } = useAbsence(absenceId);
 *
 *   const handleUpdate = (updates: AbsenceUpdate) => {
 *     mutate(
 *       { id: absenceId, data: updates },
 *       {
 *         onSuccess: () => {
 *           toast.success('Absence updated');
 *           navigate(`/absences/${absenceId}`);
 *         },
 *         onError: (error) => {
 *           toast.error(`Update failed: ${error.message}`);
 *         },
 *       }
 *     );
 *   };
 *
 *   return <AbsenceForm initialData={absence} onSubmit={handleUpdate} />;
 * }
 * ```
 *
 * @see useAbsence - Query is auto-refreshed after update
 * @see useAbsenceCreate - For creating new absences
 */
export function useAbsenceUpdate() {
  const queryClient = useQueryClient()

  return useMutation<Absence, ApiError, { id: string; data: AbsenceUpdate }>({
    mutationFn: ({ id, data }) => put<Absence>(`/absences/${id}`, data),
    onSuccess: (data, { id }) => {
      // Invalidate all absence-related queries
      queryClient.invalidateQueries({ queryKey: absenceQueryKeys.all() })
      // Invalidate specific absence
      queryClient.invalidateQueries({ queryKey: absenceQueryKeys.detail(id) })
      // Absences affect schedules
      queryClient.invalidateQueries({ queryKey: ['schedule'] })
      // May affect leave balances
      queryClient.invalidateQueries({ queryKey: absenceQueryKeys.balances() })
    },
  })
}

/**
 * Approves or rejects an absence request.
 *
 * This mutation hook handles the approval workflow for absence requests.
 * Used by coordinators and administrators to approve or reject time off
 * requests. Upon approval, the absence becomes official and blocks schedule
 * assignments during that period.
 *
 * Note: This endpoint may not be implemented yet on the backend.
 * Will return 404 until backend support is added.
 *
 * @returns Mutation object containing:
 *   - `mutate`: Function to approve/reject an absence
 *   - `mutateAsync`: Async version returning a Promise
 *   - `isPending`: Whether the approval is in progress
 *   - `error`: Any error that occurred (may be 404 if not implemented)
 *   - `data`: The updated absence with approval status
 *
 * @example
 * ```tsx
 * function AbsenceApprovalActions({ absence }: Props) {
 *   const { mutate: approve, isPending } = useAbsenceApprove();
 *
 *   const handleApprove = () => {
 *     approve({
 *       absence_id: absence.id,
 *       approved: true,
 *       comments: 'Approved - adequate coverage available',
 *     }, {
 *       onSuccess: () => {
 *         toast.success('Absence approved');
 *       },
 *       onError: (error) => {
 *         if (error.status === 404) {
 *           toast.error('Approval feature not yet implemented');
 *         } else {
 *           toast.error(`Approval failed: ${error.message}`);
 *         }
 *       },
 *     });
 *   };
 *
 *   const handleReject = () => {
 *     approve({
 *       absence_id: absence.id,
 *       approved: false,
 *       comments: 'Rejected - insufficient coverage',
 *     });
 *   };
 *
 *   return (
 *     <div>
 *       <Button onClick={handleApprove} disabled={isPending}>
 *         Approve
 *       </Button>
 *       <Button onClick={handleReject} disabled={isPending} variant="outline">
 *         Reject
 *       </Button>
 *     </div>
 *   );
 * }
 * ```
 *
 * @see useAbsence - For fetching absence details
 * @see useAbsenceUpdate - For general absence modifications
 */
export function useAbsenceApprove() {
  const queryClient = useQueryClient()

  return useMutation<Absence, ApiError, AbsenceApprovalRequest>({
    mutationFn: (request) => post<Absence>(`/absences/${request.absence_id}/approve`, request),
    onSuccess: (data, { absence_id }) => {
      // Invalidate all absence queries
      queryClient.invalidateQueries({ queryKey: absenceQueryKeys.all() })
      // Invalidate specific absence
      queryClient.invalidateQueries({ queryKey: absenceQueryKeys.detail(absence_id) })
      // Approved absences affect schedules
      queryClient.invalidateQueries({ queryKey: ['schedule'] })
    },
    retry: (failureCount, error) => {
      // Don't retry on 404 (endpoint not implemented)
      if (error?.status === 404) return false
      return failureCount < 2
    },
  })
}

/**
 * Deletes an absence record from the system.
 *
 * This mutation hook removes an absence, making the person available
 * again for scheduling during that period. Automatically invalidates
 * schedule queries since availability has changed. Use with caution as
 * deletion may be irreversible.
 *
 * @returns Mutation object containing:
 *   - `mutate`: Function to delete an absence by ID
 *   - `mutateAsync`: Async version returning a Promise
 *   - `isPending`: Whether deletion is in progress
 *   - `error`: Any error that occurred
 *
 * @example
 * ```tsx
 * function AbsenceActions({ absence }: Props) {
 *   const { mutate, isPending } = useAbsenceDelete();
 *
 *   const handleCancel = () => {
 *     if (confirm('Cancel this absence request?')) {
 *       mutate(absence.id, {
 *         onSuccess: () => {
 *           toast.success('Absence cancelled');
 *         },
 *         onError: (error) => {
 *           toast.error(`Failed to cancel: ${error.message}`);
 *         },
 *       });
 *     }
 *   };
 *
 *   return (
 *     <Button
 *       onClick={handleCancel}
 *       loading={isPending}
 *       variant="outline"
 *     >
 *       Cancel Absence
 *     </Button>
 *   );
 * }
 * ```
 *
 * @see useAbsenceList - List is auto-refreshed after deletion
 * @see useAbsenceCreate - For adding new absences
 */
export function useAbsenceDelete() {
  const queryClient = useQueryClient()

  return useMutation<void, ApiError, string>({
    mutationFn: (id) => del(`/absences/${id}`),
    onSuccess: () => {
      // Invalidate all absence queries
      queryClient.invalidateQueries({ queryKey: absenceQueryKeys.all() })
      // Absences affect schedules
      queryClient.invalidateQueries({ queryKey: ['schedule'] })
      // May affect leave balances
      queryClient.invalidateQueries({ queryKey: absenceQueryKeys.balances() })
    },
  })
}

// ============================================================================
// Away-From-Program Compliance Hooks
// ============================================================================

/**
 * Query key factory for away-from-program compliance queries.
 */
export const awayComplianceQueryKeys = {
  all: () => ['away-compliance'] as const,
  dashboard: (academicYear?: number) => [...awayComplianceQueryKeys.all(), 'dashboard', academicYear] as const,
  summary: (personId: string, academicYear?: number) =>
    [...awayComplianceQueryKeys.all(), 'summary', personId, academicYear] as const,
  check: (personId: string, additionalDays?: number, academicYear?: number) =>
    [...awayComplianceQueryKeys.all(), 'check', personId, additionalDays, academicYear] as const,
}

/**
 * Fetches away-from-program compliance dashboard for all residents.
 *
 * This hook retrieves the compliance status for all residents, showing
 * days used toward the 28-day away-from-program limit per academic year.
 * Residents exceeding 28 days must extend their training.
 *
 * Threshold status:
 * - `ok`: 0-20 days used
 * - `warning`: 21-27 days used (approaching limit)
 * - `critical`: 28 days used (at limit)
 * - `exceeded`: 29+ days used (training extension required)
 *
 * @param academicYear - Academic year start (e.g., 2025 for July 2025 - June 2026)
 * @param options - Optional React Query configuration options
 * @returns Query result containing:
 *   - `data`: Dashboard with all residents' compliance status
 *   - `isLoading`: Whether the fetch is in progress
 *   - `error`: Any error that occurred
 *
 * @example
 * ```tsx
 * function ComplianceDashboard() {
 *   const { data, isLoading } = useAwayComplianceDashboard();
 *
 *   if (isLoading) return <Spinner />;
 *
 *   return (
 *     <div>
 *       <h2>Away-From-Program Compliance ({data.academic_year})</h2>
 *       <StatusSummary counts={data.summary.by_status} />
 *       <ResidentTable residents={data.residents} />
 *     </div>
 *   );
 * }
 * ```
 */
export function useAwayComplianceDashboard(
  academicYear?: number,
  options?: Omit<UseQueryOptions<AllResidentsAwayStatus, ApiError>, 'queryKey' | 'queryFn'>
) {
  const params = academicYear ? `?academic_year=${academicYear}` : ''

  return useQuery<AllResidentsAwayStatus, ApiError>({
    queryKey: awayComplianceQueryKeys.dashboard(academicYear),
    queryFn: () => get<AllResidentsAwayStatus>(`/absences/compliance/away-from-program${params}`),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    ...options,
  })
}

/**
 * Fetches away-from-program summary for a specific resident.
 *
 * This hook retrieves detailed away-from-program tracking for a single
 * resident, including days used, days remaining, threshold status, and
 * a list of contributing absences.
 *
 * @param personId - UUID of the resident
 * @param academicYear - Optional academic year start
 * @param options - Optional React Query configuration options
 * @returns Query result containing:
 *   - `data`: Summary with days used, remaining, and absences
 *   - `isLoading`: Whether the fetch is in progress
 *   - `error`: Any error that occurred
 *
 * @example
 * ```tsx
 * function ResidentAwayStatus({ residentId }: Props) {
 *   const { data, isLoading } = useAwayFromProgramSummary(residentId);
 *
 *   if (isLoading) return <Spinner />;
 *
 *   return (
 *     <ProgressBar
 *       current={data.days_used}
 *       max={data.max_days}
 *       status={data.threshold_status}
 *     />
 *   );
 * }
 * ```
 */
export function useAwayFromProgramSummary(
  personId: string,
  academicYear?: number,
  options?: Omit<UseQueryOptions<AwayFromProgramSummary, ApiError>, 'queryKey' | 'queryFn'>
) {
  const params = academicYear ? `?academic_year=${academicYear}` : ''

  return useQuery<AwayFromProgramSummary, ApiError>({
    queryKey: awayComplianceQueryKeys.summary(personId, academicYear),
    queryFn: () => get<AwayFromProgramSummary>(`/absences/residents/${personId}/away-from-program${params}`),
    staleTime: 5 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
    enabled: !!personId,
    ...options,
  })
}

/**
 * Checks away-from-program threshold before creating a new absence.
 *
 * This hook previews what the threshold status would be after adding
 * additional days. Useful for warning users before they create an
 * absence that would push them over the limit.
 *
 * @param personId - UUID of the resident
 * @param additionalDays - Days to add for preview
 * @param academicYear - Optional academic year start
 * @param options - Optional React Query configuration options
 * @returns Query result containing:
 *   - `data`: Check result with current/projected days and status
 *   - `isLoading`: Whether the check is in progress
 *   - `error`: Any error that occurred
 *
 * @example
 * ```tsx
 * function AbsenceWarning({ residentId, newAbsenceDays }: Props) {
 *   const { data } = useAwayThresholdCheck(residentId, newAbsenceDays);
 *
 *   if (data?.threshold_status === 'exceeded') {
 *     return (
 *       <Alert type="error">
 *         This absence would exceed the 28-day limit!
 *         Training extension will be required.
 *       </Alert>
 *     );
 *   }
 *
 *   return null;
 * }
 * ```
 */
export function useAwayThresholdCheck(
  personId: string,
  additionalDays: number = 0,
  academicYear?: number,
  options?: Omit<UseQueryOptions<AwayFromProgramCheck, ApiError>, 'queryKey' | 'queryFn'>
) {
  const params = new URLSearchParams()
  if (additionalDays) params.set('additional_days', additionalDays.toString())
  if (academicYear) params.set('academic_year', academicYear.toString())
  const queryString = params.toString()

  return useQuery<AwayFromProgramCheck, ApiError>({
    queryKey: awayComplianceQueryKeys.check(personId, additionalDays, academicYear),
    queryFn: () =>
      get<AwayFromProgramCheck>(
        `/absences/residents/${personId}/away-from-program/check${queryString ? `?${queryString}` : ''}`
      ),
    staleTime: 2 * 60 * 1000, // 2 minutes (shorter since this is preview)
    gcTime: 10 * 60 * 1000,
    enabled: !!personId,
    ...options,
  })
}

// ============================================================================
// Legacy Exports (for backwards compatibility)
// ============================================================================

/**
 * @deprecated Use `useAbsenceCreate` instead
 */
export const useCreateAbsence = useAbsenceCreate

/**
 * @deprecated Use `useAbsenceUpdate` instead
 */
export const useUpdateAbsence = useAbsenceUpdate

/**
 * @deprecated Use `useAbsenceDelete` instead
 */
export const useDeleteAbsence = useAbsenceDelete
