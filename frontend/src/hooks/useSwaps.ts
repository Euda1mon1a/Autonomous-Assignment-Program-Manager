/**
 * Swap Management Hooks
 *
 * Hooks for managing schedule swap requests, approvals, rejections,
 * and auto-matching with React Query caching and optimistic updates.
 */
import { ApiError, get, post } from "@/lib/api";
import {
  useMutation,
  useQuery,
  useQueryClient,
  UseQueryOptions,
} from "@tanstack/react-query";

// ============================================================================
// Types
// ============================================================================

export interface ListResponse<T> {
  items: T[];
  total: number;
}

/**
 * Status of a swap request
 */
export enum SwapStatus {
  PENDING = "pending",
  APPROVED = "approved",
  REJECTED = "rejected",
  EXECUTED = "executed",
  CANCELLED = "cancelled",
}

/**
 * Type of swap being requested
 */
export enum SwapType {
  ONE_TO_ONE = "oneToOne",
  ABSORB = "absorb",
}

/**
 * Swap request data structure
 */
export interface SwapRequest {
  id: string;
  sourceFacultyId: string;
  sourceFacultyName: string;
  sourceWeek: string;
  targetFacultyId?: string;
  targetFacultyName?: string;
  targetWeek?: string;
  swapType: SwapType;
  status: SwapStatus;
  requestedAt: string;
  requestedById?: string;
  approved_at?: string;
  approved_by_id?: string;
  executedAt?: string;
  executed_by_id?: string;
  reason?: string;
  notes?: string;
}

/**
 * Request data for creating a swap
 */
export interface SwapCreateRequest {
  sourceFacultyId: string;
  sourceWeek: string;
  targetFacultyId?: string;
  targetWeek?: string;
  swapType: SwapType;
  reason?: string;
  auto_match?: boolean;
}

/**
 * Response after creating a swap
 */
export interface SwapCreateResponse {
  success: boolean;
  requestId: string;
  message: string;
  candidatesNotified?: number;
}

/**
 * Request data for approving a swap
 */
export interface SwapApproveRequest {
  swapId: string;
  notes?: string;
}

/**
 * Response after approving/rejecting a swap
 */
export interface SwapActionResponse {
  success: boolean;
  message: string;
  swapId: string;
}

/**
 * Request data for rejecting a swap
 */
export interface SwapRejectRequest {
  swapId: string;
  notes?: string;
  reason?: string;
}

/**
 * Swap candidate data structure
 */
export interface SwapCandidate {
  facultyId: string;
  facultyName: string;
  available_weeks: string[];
  compatibility_score: number;
  constraints_met: boolean;
  reason?: string;
}

/**
 * Request data for auto-matching
 */
export interface AutoMatchRequest {
  sourceFacultyId: string;
  sourceWeek: string;
  max_candidates?: number;
  prefer_oneToOne?: boolean;
}

/**
 * Response from auto-match operation
 */
export interface AutoMatchResponse {
  success: boolean;
  candidates: SwapCandidate[];
  total_candidates: number;
  message: string;
}

/**
 * Filters for swap list queries
 */
export interface SwapFilters {
  status?: SwapStatus[];
  swapType?: SwapType[];
  sourceFacultyId?: string;
  targetFacultyId?: string;
  startDate?: string;
  endDate?: string;
}

// ============================================================================
// Query Keys
// ============================================================================

export const swapQueryKeys = {
  all: ["swaps"] as const,
  lists: () => [...swapQueryKeys.all, "list"] as const,
  list: (filters?: SwapFilters) => [...swapQueryKeys.lists(), filters] as const,
  details: () => [...swapQueryKeys.all, "detail"] as const,
  detail: (id: string) => [...swapQueryKeys.details(), id] as const,
  candidates: (sourceId: string, sourceWeek: string) =>
    [...swapQueryKeys.all, "candidates", sourceId, sourceWeek] as const,
};

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
  options?: Omit<UseQueryOptions<SwapRequest, ApiError>, "queryKey" | "queryFn">
) {
  return useQuery<SwapRequest, ApiError>({
    queryKey: swapQueryKeys.detail(id),
    queryFn: () => get<SwapRequest>(`/swaps/${id}`),
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    enabled: !!id,
    ...options,
  });
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
 *     targetFacultyId: currentUserId,
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
 *     startDate: '2024-01-01',
 *     endDate: '2024-06-30',
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
  options?: Omit<
    UseQueryOptions<ListResponse<SwapRequest>, ApiError>,
    "queryKey" | "queryFn"
  >
) {
  const params = new URLSearchParams();

  if (filters?.status) {
    filters.status.forEach((s) => params.append("status", s));
  }
  if (filters?.swapType) {
    filters.swapType.forEach((t) => params.append("swapType", t));
  }
  if (filters?.sourceFacultyId) {
    params.set("sourceFacultyId", filters.sourceFacultyId);
  }
  if (filters?.targetFacultyId) {
    params.set("targetFacultyId", filters.targetFacultyId);
  }
  if (filters?.startDate) {
    params.set("startDate", filters.startDate);
  }
  if (filters?.endDate) {
    params.set("endDate", filters.endDate);
  }

  const queryString = params.toString();

  return useQuery<ListResponse<SwapRequest>, ApiError>({
    queryKey: swapQueryKeys.list(filters),
    queryFn: () =>
      get<ListResponse<SwapRequest>>(
        `/swaps${queryString ? `?${queryString}` : ""}`
      ),
    staleTime: 60 * 1000, // 1 minute
    gcTime: 10 * 60 * 1000, // 10 minutes
    ...options,
  });
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
  options?: Omit<
    UseQueryOptions<ListResponse<SwapCandidate>, ApiError>,
    "queryKey" | "queryFn"
  >
) {
  return useQuery<ListResponse<SwapCandidate>, ApiError>({
    queryKey: swapQueryKeys.candidates(sourceId, sourceWeek),
    queryFn: () =>
      get<ListResponse<SwapCandidate>>(
        `/swaps/candidates?source_faculty_id=${sourceId}&source_week=${sourceWeek}`
      ),
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
    enabled: !!sourceId && !!sourceWeek,
    ...options,
  });
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
 *   - `isPending`: Whether the creation is in progress
 *   - `isSuccess`: Whether creation completed successfully
 *   - `isError`: Whether an error occurred
 *   - `error`: Any error that occurred (e.g., conflicts, validation)
 *   - `data`: The creation response with request ID
 *
 * @example
 * ```tsx
 * function CreateSwapForm() {
 *   const { mutate, isPending } = useSwapCreate();
 *
 *   const handleSubmit = (formData: SwapCreateRequest) => {
 *     mutate(formData, {
 *       onSuccess: (result) => {
 *         toast.success(`Swap request created: ${result.requestId}`);
 *         if (result.candidatesNotified) {
 *           toast.info(`Notified ${result.candidatesNotified} candidates`);
 *         }
 *         navigate('/swaps/my-requests');
 *       },
 *       onError: (error) => {
 *         toast.error(`Failed to create swap: ${error.message}`);
 *       },
 *     });
 *   };
 *
 *   return <SwapForm onSubmit={handleSubmit} loading={isPending} />;
 * }
 * ```
 *
 * @example
 * ```tsx
 * // One-to-one swap with specific target
 * const createOneToOne = () => {
 *   mutate({
 *     sourceFacultyId: 'faculty-123',
 *     sourceWeek: '2024-03-01',
 *     targetFacultyId: 'faculty-456',
 *     targetWeek: '2024-03-08',
 *     swapType: SwapType.ONE_TO_ONE,
 *     reason: 'Family emergency',
 *   });
 * };
 *
 * // Absorb swap with auto-matching
 * const createAbsorb = () => {
 *   mutate({
 *     sourceFacultyId: 'faculty-123',
 *     sourceWeek: '2024-03-01',
 *     swapType: SwapType.ABSORB,
 *     auto_match: true,
 *   });
 * };
 * ```
 *
 * @see useSwapApprove - For approving created swaps
 * @see useSwapList - List is auto-refreshed after creation
 */
export function useSwapCreate() {
  const queryClient = useQueryClient();

  return useMutation<SwapCreateResponse, ApiError, SwapCreateRequest>({
    mutationFn: (request) => post<SwapCreateResponse>("/swaps", request),
    onSuccess: () => {
      // Invalidate all swap lists to show the new request
      queryClient.invalidateQueries({ queryKey: swapQueryKeys.lists() });
    },
  });
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
 *   - `isPending`: Whether approval is in progress
 *   - `isSuccess`: Whether approval completed successfully
 *   - `isError`: Whether an error occurred
 *   - `error`: Any error that occurred (e.g., validation failure)
 *   - `data`: The approval response with updated swap status
 *
 * @example
 * ```tsx
 * function SwapApprovalCard({ swap }: Props) {
 *   const { mutate, isPending } = useSwapApprove();
 *
 *   const handleApprove = () => {
 *     mutate(
 *       {
 *         swapId: swap.id,
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
 *         loading={isPending}
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
  const queryClient = useQueryClient();

  return useMutation<SwapActionResponse, ApiError, SwapApproveRequest>({
    mutationFn: ({ swapId, notes }) =>
      post<SwapActionResponse>(`/swaps/${swapId}/approve`, { notes }),
    onSuccess: (data) => {
      // Invalidate the specific swap and all lists
      queryClient.invalidateQueries({
        queryKey: swapQueryKeys.detail(data.swapId),
      });
      queryClient.invalidateQueries({ queryKey: swapQueryKeys.lists() });
      // Also invalidate schedule queries as the swap affects the schedule
      queryClient.invalidateQueries({ queryKey: ["schedule"] });
      queryClient.invalidateQueries({ queryKey: ["assignments"] });
    },
  });
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
 *   - `isPending`: Whether rejection is in progress
 *   - `isSuccess`: Whether rejection completed successfully
 *   - `isError`: Whether an error occurred
 *   - `error`: Any error that occurred
 *   - `data`: The rejection response with updated swap status
 *
 * @example
 * ```tsx
 * function SwapRejectDialog({ swap }: Props) {
 *   const { mutate, isPending } = useSwapReject();
 *   const [reason, setReason] = useState('');
 *
 *   const handleReject = () => {
 *     mutate(
 *       {
 *         swapId: swap.id,
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
 *       <RejectButton onClick={handleReject} loading={isPending} />
 *     </Dialog>
 *   );
 * }
 * ```
 *
 * @see useSwapApprove - For approving swap requests
 * @see useSwapRequest - Detail query is auto-refreshed after rejection
 */
export function useSwapReject() {
  const queryClient = useQueryClient();

  return useMutation<SwapActionResponse, ApiError, SwapRejectRequest>({
    mutationFn: ({ swapId, notes, reason }) =>
      post<SwapActionResponse>(`/swaps/${swapId}/reject`, { notes, reason }),
    onSuccess: (data) => {
      // Invalidate the specific swap and all lists
      queryClient.invalidateQueries({
        queryKey: swapQueryKeys.detail(data.swapId),
      });
      queryClient.invalidateQueries({ queryKey: swapQueryKeys.lists() });
    },
  });
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
 *   - `isPending`: Whether matching is in progress
 *   - `isSuccess`: Whether matching completed successfully
 *   - `isError`: Whether an error occurred
 *   - `error`: Any error that occurred
 *   - `data`: Auto-match results with ranked candidates
 *
 * @example
 * ```tsx
 * function AutoMatchDialog({ facultyId, week }: Props) {
 *   const { mutate, isPending, data } = useAutoMatch();
 *
 *   const handleAutoMatch = () => {
 *     mutate(
 *       {
 *         sourceFacultyId: facultyId,
 *         sourceWeek: week,
 *         max_candidates: 10,
 *         prefer_oneToOne: true,
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
 *       <AutoMatchButton onClick={handleAutoMatch} loading={isPending} />
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
  const queryClient = useQueryClient();

  return useMutation<AutoMatchResponse, ApiError, AutoMatchRequest>({
    mutationFn: (request) =>
      post<AutoMatchResponse>("/swaps/auto-match", request),
    onSuccess: (data, variables) => {
      // Invalidate candidates query for this source/week
      queryClient.invalidateQueries({
        queryKey: swapQueryKeys.candidates(
          variables.sourceFacultyId,
          variables.sourceWeek
        ),
      });
    },
  });
}

// ============================================================================
// Admin Swap Execution Types
// ============================================================================

/**
 * Request for executing a swap (admin force swap)
 */
export interface SwapExecuteRequest {
  sourceFacultyId: string;
  sourceWeek: string; // ISO date
  targetFacultyId: string;
  targetWeek?: string; // ISO date, required for one-to-one
  swapType: SwapType;
  reason?: string;
}

/**
 * Result of swap validation
 */
export interface SwapValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
  backToBackConflict: boolean;
  externalConflict?: string;
}

/**
 * Response from swap execution
 */
export interface SwapExecuteResponse {
  success: boolean;
  swapId: string | null;
  message: string;
  validation: SwapValidationResult;
}

/**
 * Request for rolling back a swap
 */
export interface SwapRollbackRequest {
  swapId: string;
  reason: string;
}

/**
 * Response from swap rollback
 */
export interface SwapRollbackResponse {
  success: boolean;
  message: string;
  swapId: string;
}

// ============================================================================
// Admin Swap Mutation Hooks
// ============================================================================

/**
 * Validates a swap without executing it (dry run).
 *
 * This hook checks if a proposed swap would be valid, returning any errors
 * or warnings that would prevent or affect the swap.
 *
 * @returns Mutation object for validating swaps
 *
 * @example
 * ```tsx
 * const { mutate: validate, data: validation } = useValidateSwap();
 *
 * const handleDryRun = () => {
 *   validate({
 *     sourceFacultyId: 'uuid',
 *     sourceWeek: '2024-03-01',
 *     targetFacultyId: 'uuid',
 *     swapType: SwapType.ONE_TO_ONE,
 *   });
 * };
 *
 * if (validation && !validation.valid) {
 *   showWarnings(validation.errors);
 * }
 * ```
 */
export function useValidateSwap() {
  return useMutation<SwapValidationResult, ApiError, SwapExecuteRequest>({
    mutationFn: (request) =>
      post<SwapValidationResult>("/swaps/validate", request),
  });
}

/**
 * Executes a swap between two faculty members.
 *
 * This hook performs the actual swap operation, transferring assignments
 * between faculty members. Should typically be preceded by validation.
 *
 * @returns Mutation object for executing swaps
 *
 * @example
 * ```tsx
 * const { mutate: executeSwap, isPending } = useExecuteSwap();
 *
 * const handleExecute = () => {
 *   executeSwap({
 *     sourceFacultyId: sourceFacultyId,
 *     sourceWeek: '2024-03-01',
 *     targetFacultyId: targetFacultyId,
 *     targetWeek: '2024-03-08',
 *     swapType: SwapType.ONE_TO_ONE,
 *     reason: 'Admin force swap',
 *   }, {
 *     onSuccess: (result) => {
 *       toast.success(`Swap executed: ${result.swapId}`);
 *     },
 *     onError: (error) => {
 *       toast.error(`Swap failed: ${error.message}`);
 *     },
 *   });
 * };
 * ```
 */
export function useExecuteSwap() {
  const queryClient = useQueryClient();

  return useMutation<SwapExecuteResponse, ApiError, SwapExecuteRequest>({
    mutationFn: (request) =>
      post<SwapExecuteResponse>("/swaps/execute", request),
    onSuccess: () => {
      // Invalidate all related queries
      queryClient.invalidateQueries({ queryKey: swapQueryKeys.lists() });
      queryClient.invalidateQueries({ queryKey: ["schedule"] });
      queryClient.invalidateQueries({ queryKey: ["assignments"] });
      queryClient.invalidateQueries({ queryKey: ["blocks"] });
    },
  });
}

/**
 * Rolls back a previously executed swap.
 *
 * This hook reverses a swap that was executed within the rollback window
 * (typically 24 hours). Requires a reason for audit trail.
 *
 * @returns Mutation object for rolling back swaps
 *
 * @example
 * ```tsx
 * const { mutate: rollback, isPending } = useRollbackSwap();
 *
 * const handleRollback = () => {
 *   rollback({
 *     swapId: swapId,
 *     reason: 'Executed in error',
 *   }, {
 *     onSuccess: () => {
 *       toast.success('Swap rolled back');
 *     },
 *   });
 * };
 * ```
 */
export function useRollbackSwap() {
  const queryClient = useQueryClient();

  return useMutation<SwapRollbackResponse, ApiError, SwapRollbackRequest>({
    mutationFn: ({ swapId, reason }) =>
      post<SwapRollbackResponse>(`/swaps/${swapId}/rollback`, { reason }),
    onSuccess: (data) => {
      // Invalidate all related queries
      queryClient.invalidateQueries({
        queryKey: swapQueryKeys.detail(data.swapId),
      });
      queryClient.invalidateQueries({ queryKey: swapQueryKeys.lists() });
      queryClient.invalidateQueries({ queryKey: ["schedule"] });
      queryClient.invalidateQueries({ queryKey: ["assignments"] });
    },
  });
}
