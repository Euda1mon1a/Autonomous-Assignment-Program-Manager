/**
 * Absence Management Hooks
 *
 * Hooks for managing resident and faculty absences (vacation,
 * conferences, illness, etc.) with React Query caching.
 */
import { useQuery, useMutation, useQueryClient, UseQueryOptions } from '@tanstack/react-query'
import { get, post, put, del, ApiError } from '@/lib/api'
import type {
  Absence,
  AbsenceCreate,
  AbsenceUpdate,
} from '@/types/api'

// ============================================================================
// Types
// ============================================================================

export interface ListResponse<T> {
  items: T[]
  total: number
}

export interface AbsenceFilters {
  person_id?: string
  start_date?: string
  end_date?: string
  absence_type?: string
}

// ============================================================================
// Query Keys
// ============================================================================

export const absenceQueryKeys = {
  absences: (filters?: AbsenceFilters) => ['absences', filters] as const,
  absence: (id: string) => ['absences', id] as const,
}

// ============================================================================
// Absence Hooks
// ============================================================================

/**
 * Fetches absences with optional filtering by person.
 *
 * This hook retrieves absence records including vacation, conferences,
 * illness, and other time off. Absences are used by the schedule generator
 * to ensure residents aren't assigned during unavailable periods.
 *
 * @param personId - Optional person ID to filter absences
 * @param options - Optional React Query configuration options
 * @returns Query result containing:
 *   - `data`: List of absences with person and date information
 *   - `isLoading`: Whether the fetch is in progress
 *   - `error`: Any error that occurred
 *   - `refetch`: Function to manually refetch absences
 *
 * @example
 * ```tsx
 * function AbsenceCalendar({ residentId }: Props) {
 *   const { data, isLoading } = useAbsences(residentId);
 *
 *   if (isLoading) return <Spinner />;
 *
 *   return (
 *     <AbsenceList
 *       absences={data.items}
 *       onEdit={(id) => navigate(`/absences/${id}/edit`)}
 *     />
 *   );
 * }
 * ```
 *
 * @example
 * ```tsx
 * // Fetch all absences across all people
 * function AllAbsences() {
 *   const { data } = useAbsences();
 *   return <AbsenceTable absences={data.items} />;
 * }
 * ```
 *
 * @see useAbsence - For fetching a single absence
 * @see useCreateAbsence - For adding new absences
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
 * Fetches detailed information for a specific absence record.
 *
 * This hook retrieves complete details for a single absence including
 * dates, type, reason, and approval status. Used for viewing and editing
 * absence records.
 *
 * @param id - The UUID of the absence to fetch
 * @param options - Optional React Query configuration options
 * @returns Query result containing:
 *   - `data`: The absence record with all details
 *   - `isLoading`: Whether the fetch is in progress
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
 * @see useAbsences - For fetching multiple absences
 * @see useUpdateAbsence - For modifying absence details
 */
export function useAbsence(
  id: string,
  options?: Omit<UseQueryOptions<Absence, ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<Absence, ApiError>({
    queryKey: absenceQueryKeys.absence(id),
    queryFn: () => get<Absence>(`/absences/${id}`),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    enabled: !!id,
    ...options,
  })
}

/**
 * Creates a new absence record for a person.
 *
 * This mutation hook records planned or unplanned absences that affect
 * schedule availability. Creating an absence automatically invalidates
 * schedule queries since it impacts availability and may require
 * coverage adjustments.
 *
 * @returns Mutation object containing:
 *   - `mutate`: Function to create an absence
 *   - `mutateAsync`: Async version returning a Promise
 *   - `isLoading`: Whether creation is in progress
 *   - `error`: Any error that occurred (e.g., overlapping absences)
 *   - `data`: The created absence with generated ID
 *
 * @example
 * ```tsx
 * function RequestAbsenceForm({ personId }: Props) {
 *   const { mutate, isLoading } = useCreateAbsence();
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
 *   return <AbsenceForm onSubmit={handleSubmit} loading={isLoading} />;
 * }
 * ```
 *
 * @see useUpdateAbsence - For modifying existing absences
 * @see useAbsences - List is auto-refreshed after creation
 */
export function useCreateAbsence() {
  const queryClient = useQueryClient()

  return useMutation<Absence, ApiError, AbsenceCreate>({
    mutationFn: (data) => post<Absence>('/absences', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['absences'] })
      // Absences affect schedule availability
      queryClient.invalidateQueries({ queryKey: ['schedule'] })
    },
  })
}

/**
 * Updates an existing absence record with new details.
 *
 * This mutation hook modifies absence information such as dates, type,
 * or reason. Useful for adjusting vacation dates, updating approval status,
 * or correcting absence details. Automatically refreshes schedule data.
 *
 * @returns Mutation object containing:
 *   - `mutate`: Function to update an absence
 *   - `mutateAsync`: Async version returning a Promise
 *   - `isLoading`: Whether update is in progress
 *   - `error`: Any error that occurred
 *   - `data`: The updated absence
 *
 * @example
 * ```tsx
 * function EditAbsenceForm({ absenceId }: Props) {
 *   const { mutate, isLoading } = useUpdateAbsence();
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
 * @see useCreateAbsence - For creating new absences
 */
export function useUpdateAbsence() {
  const queryClient = useQueryClient()

  return useMutation<Absence, ApiError, { id: string; data: AbsenceUpdate }>({
    mutationFn: ({ id, data }) => put<Absence>(`/absences/${id}`, data),
    onSuccess: (data, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['absences'] })
      queryClient.invalidateQueries({ queryKey: absenceQueryKeys.absence(id) })
      queryClient.invalidateQueries({ queryKey: ['schedule'] })
    },
  })
}

/**
 * Deletes an absence record from the system.
 *
 * This mutation hook removes an absence, making the person available
 * again for scheduling during that period. Automatically invalidates
 * schedule queries since availability has changed.
 *
 * @returns Mutation object containing:
 *   - `mutate`: Function to delete an absence by ID
 *   - `mutateAsync`: Async version returning a Promise
 *   - `isLoading`: Whether deletion is in progress
 *   - `error`: Any error that occurred
 *
 * @example
 * ```tsx
 * function AbsenceActions({ absence }: Props) {
 *   const { mutate, isLoading } = useDeleteAbsence();
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
 *       loading={isLoading}
 *       variant="outline"
 *     >
 *       Cancel Absence
 *     </Button>
 *   );
 * }
 * ```
 *
 * @see useAbsences - List is auto-refreshed after deletion
 * @see useCreateAbsence - For adding new absences
 */
export function useDeleteAbsence() {
  const queryClient = useQueryClient()

  return useMutation<void, ApiError, string>({
    mutationFn: (id) => del(`/absences/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['absences'] })
      queryClient.invalidateQueries({ queryKey: ['schedule'] })
    },
  })
}
