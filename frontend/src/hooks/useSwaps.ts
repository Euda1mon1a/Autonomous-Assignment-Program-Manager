/**
 * Swap Management Hooks
 *
 * Hooks for managing schedule swap requests, approvals, rejections,
 * and auto-matching with React Query caching and optimistic updates.
 */
import { useQuery, useMutation, useQueryClient, UseQueryOptions } from '@tanstack/react-query'
import { get, post, put, del, ApiError } from '@/lib/api'

// ============================================================================
// Types
// ============================================================================

export interface ListResponse<T> {
  items: T[]
  total: number
}

/**
 * Status of a swap request
 */
export enum SwapStatus {
  PENDING = 'pending',
  APPROVED = 'approved',
  REJECTED = 'rejected',
  EXECUTED = 'executed',
  CANCELLED = 'cancelled',
}

/**
 * Type of swap being requested
 */
export enum SwapType {
  ONE_TO_ONE = 'one_to_one',
  ABSORB = 'absorb',
}

/**
 * Swap request data structure
 */
export interface SwapRequest {
  id: string
  source_faculty_id: string
  source_faculty_name: string
  source_week: string
  target_faculty_id?: string
  target_faculty_name?: string
  target_week?: string
  swap_type: SwapType
  status: SwapStatus
  requested_at: string
  requested_by_id?: string
  approved_at?: string
  approved_by_id?: string
  executed_at?: string
  executed_by_id?: string
  reason?: string
  notes?: string
}

/**
 * Request data for creating a swap
 */
export interface SwapCreateRequest {
  source_faculty_id: string
  source_week: string
  target_faculty_id?: string
  target_week?: string
  swap_type: SwapType
  reason?: string
  auto_match?: boolean
}

/**
 * Response after creating a swap
 */
export interface SwapCreateResponse {
  success: boolean
  request_id: string
  message: string
  candidates_notified?: number
}

/**
 * Request data for approving a swap
 */
export interface SwapApproveRequest {
  swap_id: string
  notes?: string
}

/**
 * Response after approving/rejecting a swap
 */
export interface SwapActionResponse {
  success: boolean
  message: string
  swap_id: string
}

/**
 * Request data for rejecting a swap
 */
export interface SwapRejectRequest {
  swap_id: string
  notes?: string
  reason?: string
}

/**
 * Swap candidate data structure
 */
export interface SwapCandidate {
  faculty_id: string
  faculty_name: string
  available_weeks: string[]
  compatibility_score: number
  constraints_met: boolean
  reason?: string
}

/**
 * Request data for auto-matching
 */
export interface AutoMatchRequest {
  source_faculty_id: string
  source_week: string
  max_candidates?: number
  prefer_one_to_one?: boolean
}

/**
 * Response from auto-match operation
 */
export interface AutoMatchResponse {
  success: boolean
  candidates: SwapCandidate[]
  total_candidates: number
  message: string
}

/**
 * Filters for swap list queries
 */
export interface SwapFilters {
  status?: SwapStatus[]
  swap_type?: SwapType[]
  source_faculty_id?: string
  target_faculty_id?: string
  start_date?: string
  end_date?: string
}

// ============================================================================
// Query Keys
// ============================================================================

export const swapQueryKeys = {
  all: ['swaps'] as const,
  lists: () => [...swapQueryKeys.all, 'list'] as const,
  list: (filters?: SwapFilters) => [...swapQueryKeys.lists(), filters] as const,
  details: () => [...swapQueryKeys.all, 'detail'] as const,
  detail: (id: string) => [...swapQueryKeys.details(), id] as const,
  candidates: (sourceId: string, sourceWeek: string) =>
    [...swapQueryKeys.all, 'candidates', sourceId, sourceWeek] as const,
}

// ============================================================================
// Query Hooks
// ============================================================================

/**
 * Fetches a single swap request by ID.
 *
 * This hook retrieves detailed information about a specific swap request,
 * including all participants, dates, status, and history. It uses React Query
 * for automatic caching and background refetching.
 *
 * @param id - The UUID of the swap request to fetch
 * @param options - Optional React Query configuration options
 * @returns Query result containing:
 *   - `data`: The swap request details
 *   - `isLoading`: Whether the initial fetch is in progress
 *   - `isFetching`: Whether any fetch is in progress (including background)
 *   - `error`: Any error that occurred during fetch
 *   - `refetch`: Function to manually refetch the swap request
 *
 * @example
 * ```tsx
 * function SwapDetails({ swapId }: Props) {
 *   const { data, isLoading, error } = useSwapRequest(swapId);
 *
 *   if (isLoading) return <Spinner />;
 *   if (error) return <ErrorAlert error={error} />;
 *
 *   return (
 *     <SwapCard
 *       swap={data}
 *       showActions={data.status === 'pending'}
 *     />
 *   );
 * }
 * ```
 *
 * @see useSwapList - For fetching multiple swap requests
 * @see useSwapApprove - For approving a swap request
 */
export function useSwapRequest(
  id: string,
  options?: Omit<UseQueryOptions<SwapRequest, ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<SwapRequest, ApiError>({
    queryKey: swapQueryKeys.detail(id),
    queryFn: () => get<SwapRequest>(`/swaps/${id}`),
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    enabled: !!id,
    ...options,
  })
}

/**
 * Fetches a list of swap requests with optional filtering.
 *
 * This hook retrieves all swap requests matching the provided filters,
 * enabling views like "My Requests", "Pending Approvals", or "All Swaps".
 * Results are automatically cached and updated when related mutations occur.
 *
 * @param filters - Optional filters for status, type, participants, dates
 * @param options - Optional React Query configuration options
 * @returns Query result containing:
 *   - `data`: List response with swap requests and total count
 *   - `isLoading`: Whether the initial fetch is in progress
 *   - `error`: Any error that occurred during fetch
 *   - `refetch`: Function to manually refetch the list
 *
 * @example
 * ```tsx
 * function PendingSwaps() {
 *   const { data, isLoading } = useSwapList({
 *     status: [SwapStatus.PENDING],
 *     target_faculty_id: currentUserId,
 *   });
 *
 *   if (isLoading) return <LoadingSkeleton />;
 *
 *   return (
 *     <SwapList
 *       swaps={data.items}
 *       total={data.total}
 *       emptyMessage="No pending requests"
 *     />
 *   );
 * }
 * ```
 *
 * @example
 * ```tsx
 * // Filter by date range
 * function UpcomingSwaps() {
 *   const { data } = useSwapList({
 *     start_date: '2024-01-01',
 *     end_date: '2024-06-30',
 *     status: [SwapStatus.APPROVED, SwapStatus.EXECUTED],
 *   });
 *
 *   return <SwapCalendar swaps={data.items} />;
 * }
 * ```
 *
 * @see useSwapRequest - For fetching a single swap request
 * @see SwapFilters - Available filter options
 */
export function useSwapList(
  filters?: SwapFilters,
  options?: Omit<UseQueryOptions<ListResponse<SwapRequest>, ApiError>, 'queryKey' | 'queryFn'>
) {
  const params = new URLSearchParams()

  if (filters?.status) {
    filters.status.forEach(s => params.append('status', s))
  }
  if (filters?.swap_type) {
    filters.swap_type.forEach(t => params.append('swap_type', t))
  }
  if (filters?.source_faculty_id) {
    params.set('source_faculty_id', filters.source_faculty_id)
  }
  if (filters?.target_faculty_id) {
    params.set('target_faculty_id', filters.target_faculty_id)
  }
  if (filters?.start_date) {
    params.set('start_date', filters.start_date)
  }
  if (filters?.end_date) {
    params.set('end_date', filters.end_date)
  }

  const queryString = params.toString()

  return useQuery<ListResponse<SwapRequest>, ApiError>({
    queryKey: swapQueryKeys.list(filters),
    queryFn: () => get<ListResponse<SwapRequest>>(`/swaps${queryString ? `?${queryString}` : ''}`),
    staleTime: 60 * 1000, // 1 minute
    gcTime: 10 * 60 * 1000, // 10 minutes
    ...options,
  })
}

/**
 * Fetches potential swap candidates for auto-matching.
 *
 * This hook queries the system to find compatible faculty members who can
 * take over a shift, either through one-to-one swap or absorption. The results
 * include compatibility scores and constraint validation status.
 *
 * @param sourceId - ID of faculty member requesting the swap
 * @param sourceWeek - Week to be swapped (ISO date string)
 * @param options - Optional React Query configuration options
 * @returns Query result containing:
 *   - `data`: List of compatible candidates with scores
 *   - `isLoading`: Whether the search is in progress
 *   - `error`: Any error that occurred
 *   - `refetch`: Function to manually re-search for candidates
 *
 * @example
 * ```tsx
 * function SwapCandidateSelector({ facultyId, week }: Props) {
 *   const { data, isLoading } = useSwapCandidates(facultyId, week);
 *
 *   if (isLoading) return <SearchingSpinner />;
 *
 *   return (
 *     <CandidateList
 *       candidates={data.items}
 *       onSelect={(candidate) => createSwap(candidate)}
 *     />
 *   );
 * }
 * ```
 *
 * @see useAutoMatch - For automatic matching mutation
 * @see useSwapCreate - For creating a swap with selected candidate
 */
export function useSwapCandidates(
  sourceId: string,
  sourceWeek: string,
  options?: Omit<UseQueryOptions<ListResponse<SwapCandidate>, ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<ListResponse<SwapCandidate>, ApiError>({
    queryKey: swapQueryKeys.candidates(sourceId, sourceWeek),
    queryFn: () => get<ListResponse<SwapCandidate>>(
      `/swaps/candidates?source_faculty_id=${sourceId}&source_week=${sourceWeek}`
    ),
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
    enabled: !!sourceId && !!sourceWeek,
    ...options,
  })
}

// ============================================================================
// Mutation Hooks
// ============================================================================

/**
 * Creates a new swap request.
 *
 * This mutation hook submits a request to swap a schedule assignment, either
 * to a specific target faculty member or to the general marketplace. Supports
 * automatic candidate notification and matching.
 *
 * @returns Mutation object containing:
 *   - `mutate`: Function to create a swap request
 *   - `mutateAsync`: Async version returning a Promise
 *   - `isLoading`: Whether the creation is in progress
 *   - `error`: Any error that occurred (e.g., conflicts, validation)
 *   - `data`: The creation response with request ID
 *
 * @example
 * ```tsx
 * function CreateSwapForm() {
 *   const { mutate, isLoading } = useSwapCreate();
 *
 *   const handleSubmit = (formData: SwapCreateRequest) => {
 *     mutate(formData, {
 *       onSuccess: (result) => {
 *         toast.success(`Swap request created: ${result.request_id}`);
 *         if (result.candidates_notified) {
 *           toast.info(`Notified ${result.candidates_notified} candidates`);
 *         }
 *         navigate('/swaps/my-requests');
 *       },
 *       onError: (error) => {
 *         toast.error(`Failed to create swap: ${error.message}`);
 *       },
 *     });
 *   };
 *
 *   return <SwapForm onSubmit={handleSubmit} loading={isLoading} />;
 * }
 * ```
 *
 * @example
 * ```tsx
 * // One-to-one swap with specific target
 * const createOneToOne = () => {
 *   mutate({
 *     source_faculty_id: 'faculty-123',
 *     source_week: '2024-03-01',
 *     target_faculty_id: 'faculty-456',
 *     target_week: '2024-03-08',
 *     swap_type: SwapType.ONE_TO_ONE,
 *     reason: 'Family emergency',
 *   });
 * };
 *
 * // Absorb swap with auto-matching
 * const createAbsorb = () => {
 *   mutate({
 *     source_faculty_id: 'faculty-123',
 *     source_week: '2024-03-01',
 *     swap_type: SwapType.ABSORB,
 *     auto_match: true,
 *   });
 * };
 * ```
 *
 * @see useSwapApprove - For approving created swaps
 * @see useSwapList - List is auto-refreshed after creation
 */
export function useSwapCreate() {
  const queryClient = useQueryClient()

  return useMutation<SwapCreateResponse, ApiError, SwapCreateRequest>({
    mutationFn: (request) => post<SwapCreateResponse>('/swaps', request),
    onSuccess: () => {
      // Invalidate all swap lists to show the new request
      queryClient.invalidateQueries({ queryKey: swapQueryKeys.lists() })
    },
  })
}

/**
 * Approves a pending swap request.
 *
 * This mutation hook approves a swap request, allowing it to be executed
 * and applied to the schedule. Approval triggers validation to ensure the
 * swap maintains ACGME compliance and schedule integrity.
 *
 * @returns Mutation object containing:
 *   - `mutate`: Function to approve a swap request
 *   - `mutateAsync`: Async version returning a Promise
 *   - `isLoading`: Whether approval is in progress
 *   - `error`: Any error that occurred (e.g., validation failure)
 *   - `data`: The approval response with updated swap status
 *
 * @example
 * ```tsx
 * function SwapApprovalCard({ swap }: Props) {
 *   const { mutate, isLoading } = useSwapApprove();
 *
 *   const handleApprove = () => {
 *     mutate(
 *       {
 *         swap_id: swap.id,
 *         notes: 'Approved - coverage confirmed',
 *       },
 *       {
 *         onSuccess: () => {
 *           toast.success('Swap request approved');
 *           // Trigger calendar refresh
 *           queryClient.invalidateQueries({ queryKey: ['schedule'] });
 *         },
 *         onError: (error) => {
 *           if (error.status === 409) {
 *             toast.error('Cannot approve: creates ACGME violation');
 *           } else {
 *             toast.error(`Approval failed: ${error.message}`);
 *           }
 *         },
 *       }
 *     );
 *   };
 *
 *   return (
 *     <Card>
 *       <SwapDetails swap={swap} />
 *       <ApproveButton
 *         onClick={handleApprove}
 *         loading={isLoading}
 *         disabled={swap.status !== 'pending'}
 *       />
 *     </Card>
 *   );
 * }
 * ```
 *
 * @see useSwapReject - For rejecting swap requests
 * @see useSwapRequest - Detail query is auto-refreshed after approval
 */
export function useSwapApprove() {
  const queryClient = useQueryClient()

  return useMutation<SwapActionResponse, ApiError, SwapApproveRequest>({
    mutationFn: ({ swap_id, notes }) =>
      post<SwapActionResponse>(`/swaps/${swap_id}/approve`, { notes }),
    onSuccess: (data) => {
      // Invalidate the specific swap and all lists
      queryClient.invalidateQueries({ queryKey: swapQueryKeys.detail(data.swap_id) })
      queryClient.invalidateQueries({ queryKey: swapQueryKeys.lists() })
      // Also invalidate schedule queries as the swap affects the schedule
      queryClient.invalidateQueries({ queryKey: ['schedule'] })
      queryClient.invalidateQueries({ queryKey: ['assignments'] })
    },
  })
}

/**
 * Rejects a pending swap request.
 *
 * This mutation hook rejects a swap request, preventing it from being
 * executed. Rejection is final and the request cannot be re-approved.
 * A reason can optionally be provided for audit trail purposes.
 *
 * @returns Mutation object containing:
 *   - `mutate`: Function to reject a swap request
 *   - `mutateAsync`: Async version returning a Promise
 *   - `isLoading`: Whether rejection is in progress
 *   - `error`: Any error that occurred
 *   - `data`: The rejection response with updated swap status
 *
 * @example
 * ```tsx
 * function SwapRejectDialog({ swap }: Props) {
 *   const { mutate, isLoading } = useSwapReject();
 *   const [reason, setReason] = useState('');
 *
 *   const handleReject = () => {
 *     mutate(
 *       {
 *         swap_id: swap.id,
 *         reason,
 *         notes: 'Coverage not available',
 *       },
 *       {
 *         onSuccess: () => {
 *           toast.info('Swap request rejected');
 *           closeDialog();
 *         },
 *       }
 *     );
 *   };
 *
 *   return (
 *     <Dialog>
 *       <TextArea
 *         label="Reason for rejection"
 *         value={reason}
 *         onChange={setReason}
 *       />
 *       <RejectButton onClick={handleReject} loading={isLoading} />
 *     </Dialog>
 *   );
 * }
 * ```
 *
 * @see useSwapApprove - For approving swap requests
 * @see useSwapRequest - Detail query is auto-refreshed after rejection
 */
export function useSwapReject() {
  const queryClient = useQueryClient()

  return useMutation<SwapActionResponse, ApiError, SwapRejectRequest>({
    mutationFn: ({ swap_id, notes, reason }) =>
      post<SwapActionResponse>(`/swaps/${swap_id}/reject`, { notes, reason }),
    onSuccess: (data) => {
      // Invalidate the specific swap and all lists
      queryClient.invalidateQueries({ queryKey: swapQueryKeys.detail(data.swap_id) })
      queryClient.invalidateQueries({ queryKey: swapQueryKeys.lists() })
    },
  })
}

/**
 * Triggers automatic matching to find compatible swap candidates.
 *
 * This mutation hook uses the scheduling engine's constraint solver to
 * identify faculty members who can take over a shift while maintaining
 * ACGME compliance and schedule integrity. Results are ranked by
 * compatibility score.
 *
 * @returns Mutation object containing:
 *   - `mutate`: Function to trigger auto-matching
 *   - `mutateAsync`: Async version returning a Promise
 *   - `isLoading`: Whether matching is in progress
 *   - `error`: Any error that occurred
 *   - `data`: Auto-match results with ranked candidates
 *
 * @example
 * ```tsx
 * function AutoMatchDialog({ facultyId, week }: Props) {
 *   const { mutate, isLoading, data } = useAutoMatch();
 *
 *   const handleAutoMatch = () => {
 *     mutate(
 *       {
 *         source_faculty_id: facultyId,
 *         source_week: week,
 *         max_candidates: 10,
 *         prefer_one_to_one: true,
 *       },
 *       {
 *         onSuccess: (result) => {
 *           if (result.total_candidates === 0) {
 *             toast.warning('No compatible candidates found');
 *           } else {
 *             toast.success(
 *               `Found ${result.total_candidates} compatible candidates`
 *             );
 *           }
 *         },
 *       }
 *     );
 *   };
 *
 *   return (
 *     <Dialog>
 *       <AutoMatchButton onClick={handleAutoMatch} loading={isLoading} />
 *       {data && (
 *         <CandidateRankingList
 *           candidates={data.candidates}
 *           onSelect={(candidate) => createSwapWith(candidate)}
 *         />
 *       )}
 *     </Dialog>
 *   );
 * }
 * ```
 *
 * @see useSwapCandidates - For querying candidates without mutation
 * @see useSwapCreate - For creating swap with selected candidate
 */
export function useAutoMatch() {
  const queryClient = useQueryClient()

  return useMutation<AutoMatchResponse, ApiError, AutoMatchRequest>({
    mutationFn: (request) => post<AutoMatchResponse>('/swaps/auto-match', request),
    onSuccess: (data, variables) => {
      // Invalidate candidates query for this source/week
      queryClient.invalidateQueries({
        queryKey: swapQueryKeys.candidates(variables.source_faculty_id, variables.source_week)
      })
    },
  })
}
