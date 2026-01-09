/**
 * Procedures and Credentialing Hooks
 *
 * React Query hooks for managing procedure credentialing data:
 * - Procedure catalog management (CRUD operations)
 * - Faculty credentials tracking
 * - Credential status monitoring
 * - Qualified faculty lookups
 *
 * @module hooks/useProcedures
 */

import { useQuery, useMutation, useQueryClient, UseQueryResult, UseMutationResult, UseQueryOptions } from '@tanstack/react-query';
import { get, post, put, del, ApiError } from '@/lib/api';

// ============================================================================
// Types - Aligned with backend schemas
// ============================================================================

/**
 * Procedure complexity levels
 */
export type ProcedureComplexity = 'basic' | 'standard' | 'advanced' | 'complex';

/**
 * Credential status types
 */
export type CredentialStatus = 'active' | 'expired' | 'suspended' | 'pending';

/**
 * Competency level for credentials
 */
export type CompetencyLevel = 'trainee' | 'qualified' | 'expert' | 'master';

/**
 * Procedure entity representing a medical procedure requiring credentialed supervision
 */
export interface Procedure {
  id: string;
  name: string;
  description: string | null;
  category: string | null;
  specialty: string | null;
  supervision_ratio: number;
  requires_certification: boolean;
  complexity_level: ProcedureComplexity;
  min_pgy_level: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/**
 * Minimal procedure info for embedding in other responses
 */
export interface ProcedureSummary {
  id: string;
  name: string;
  specialty: string | null;
  category: string | null;
}

/**
 * Data required to create a new procedure
 */
export interface ProcedureCreate {
  name: string;
  description?: string | null;
  category?: string | null;
  specialty?: string | null;
  supervision_ratio?: number;
  requires_certification?: boolean;
  complexity_level?: ProcedureComplexity;
  min_pgy_level?: number;
  is_active?: boolean;
}

/**
 * Data for updating an existing procedure
 */
export interface ProcedureUpdate {
  name?: string | null;
  description?: string | null;
  category?: string | null;
  specialty?: string | null;
  supervision_ratio?: number | null;
  requires_certification?: boolean | null;
  complexity_level?: ProcedureComplexity | null;
  min_pgy_level?: number | null;
  is_active?: boolean | null;
}

/**
 * Credential entity representing faculty qualification to supervise a procedure
 */
export interface Credential {
  id: string;
  person_id: string;
  procedure_id: string;
  status: CredentialStatus;
  competency_level: CompetencyLevel;
  issued_date: string | null;
  expiration_date: string | null;
  last_verified_date: string | null;
  max_concurrent_residents: number | null;
  max_per_week: number | null;
  max_per_academic_year: number | null;
  notes: string | null;
  is_valid: boolean;
  created_at: string;
  updated_at: string;
}

/**
 * Credential with embedded procedure details
 */
export interface CredentialWithProcedure extends Credential {
  procedure: ProcedureSummary;
}

/**
 * Minimal person info for embedding in credential responses
 */
export interface PersonSummary {
  id: string;
  name: string;
  type: string;
}

/**
 * Data required to create a new credential
 */
export interface CredentialCreate {
  person_id: string;
  procedure_id: string;
  status?: CredentialStatus;
  competency_level?: CompetencyLevel;
  issued_date?: string | null;
  expiration_date?: string | null;
  last_verified_date?: string | null;
  max_concurrent_residents?: number | null;
  max_per_week?: number | null;
  max_per_academic_year?: number | null;
  notes?: string | null;
}

/**
 * Data for updating an existing credential
 */
export interface CredentialUpdate {
  status?: CredentialStatus | null;
  competency_level?: CompetencyLevel | null;
  expiration_date?: string | null;
  last_verified_date?: string | null;
  max_concurrent_residents?: number | null;
  max_per_week?: number | null;
  max_per_academic_year?: number | null;
  notes?: string | null;
}

/**
 * Summary of a faculty member's credentials
 */
export interface FacultyCredentialSummary {
  person_id: string;
  person_name: string;
  total_credentials: number;
  active_credentials: number;
  expiring_soon: number;
  procedures: ProcedureSummary[];
}

/**
 * Response for qualified faculty lookup
 */
export interface QualifiedFacultyResponse {
  procedure_id: string;
  procedure_name: string;
  qualified_faculty: PersonSummary[];
  total: number;
}

/**
 * Generic list response wrapper
 */
export interface ListResponse<T> {
  items: T[];
  total: number;
}

/**
 * Filters for querying procedures
 */
export interface ProcedureFilters {
  specialty?: string;
  category?: string;
  is_active?: boolean;
  complexity_level?: ProcedureComplexity;
}

/**
 * Filters for querying credentials
 */
export interface CredentialFilters {
  person_id?: string;
  procedure_id?: string;
  status?: CredentialStatus;
  include_expired?: boolean;
}

// ============================================================================
// Query Keys
// ============================================================================

export const procedureKeys = {
  all: ['procedures'] as const,
  lists: () => [...procedureKeys.all, 'list'] as const,
  list: (filters?: ProcedureFilters) => [...procedureKeys.lists(), filters] as const,
  details: () => [...procedureKeys.all, 'detail'] as const,
  detail: (id: string) => [...procedureKeys.details(), id] as const,
  specialties: () => [...procedureKeys.all, 'specialties'] as const,
  categories: () => [...procedureKeys.all, 'categories'] as const,
};

export const credentialKeys = {
  all: ['credentials'] as const,
  lists: () => [...credentialKeys.all, 'list'] as const,
  list: (filters?: CredentialFilters) => [...credentialKeys.lists(), filters] as const,
  detail: (id: string) => [...credentialKeys.all, 'detail', id] as const,
  byPerson: (personId: string, filters?: { status?: string; include_expired?: boolean }) =>
    [...credentialKeys.all, 'by-person', personId, filters] as const,
  byProcedure: (procedureId: string, filters?: { status?: string; include_expired?: boolean }) =>
    [...credentialKeys.all, 'by-procedure', procedureId, filters] as const,
  qualified: (procedureId: string) => [...credentialKeys.all, 'qualified', procedureId] as const,
  summary: (personId: string) => [...credentialKeys.all, 'summary', personId] as const,
  expiring: (days: number) => [...credentialKeys.all, 'expiring', days] as const,
};

// ============================================================================
// Procedure Query Hooks
// ============================================================================

/**
 * Fetches a list of procedures with optional filtering.
 *
 * This hook retrieves all procedures matching the provided filters,
 * supporting filtering by specialty, category, active status, and complexity level.
 *
 * @param filters - Optional filters for specialty, category, is_active, complexity_level
 * @param options - Optional React Query configuration options
 * @returns Query result containing:
 *   - `data`: List response with procedures and total count
 *   - `isLoading`: Whether the initial fetch is in progress
 *   - `error`: Any error that occurred during fetch
 *   - `refetch`: Function to manually refetch the list
 *
 * @example
 * ```tsx
 * function ProcedureCatalog() {
 *   const { data, isLoading } = useProcedures({ specialty: 'Sports Medicine' });
 *
 *   if (isLoading) return <Spinner />;
 *
 *   return (
 *     <ProcedureList
 *       procedures={data.items}
 *       total={data.total}
 *     />
 *   );
 * }
 * ```
 */
export function useProcedures(
  filters?: ProcedureFilters,
  options?: Omit<UseQueryOptions<ListResponse<Procedure>, ApiError>, 'queryKey' | 'queryFn'>
): UseQueryResult<ListResponse<Procedure>, ApiError> {
  const params = new URLSearchParams();
  if (filters?.specialty) params.set('specialty', filters.specialty);
  if (filters?.category) params.set('category', filters.category);
  if (filters?.isActive !== undefined) params.set('is_active', String(filters.isActive));
  if (filters?.complexity_level) params.set('complexity_level', filters.complexity_level);
  const queryString = params.toString();

  return useQuery<ListResponse<Procedure>, ApiError>({
    queryKey: procedureKeys.list(filters),
    queryFn: () => get<ListResponse<Procedure>>(`/procedures${queryString ? `?${queryString}` : ''}`),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    ...options,
  });
}

/**
 * Fetches a single procedure by ID.
 *
 * This hook retrieves detailed information about a specific procedure,
 * including all configuration options like supervision ratios and PGY requirements.
 *
 * @param id - The UUID of the procedure to fetch
 * @param options - Optional React Query configuration options
 * @returns Query result containing:
 *   - `data`: The procedure details
 *   - `isLoading`: Whether the fetch is in progress
 *   - `error`: Any error that occurred
 *   - `refetch`: Function to manually refetch the procedure
 *
 * @example
 * ```tsx
 * function ProcedureDetails({ procedureId }: Props) {
 *   const { data, isLoading, error } = useProcedure(procedureId);
 *
 *   if (isLoading) return <Skeleton />;
 *   if (error) return <ErrorMessage error={error} />;
 *
 *   return (
 *     <ProcedureCard
 *       procedure={data}
 *       showCredentialedFaculty
 *     />
 *   );
 * }
 * ```
 */
export function useProcedure(
  id: string,
  options?: Omit<UseQueryOptions<Procedure, ApiError>, 'queryKey' | 'queryFn'>
): UseQueryResult<Procedure, ApiError> {
  return useQuery<Procedure, ApiError>({
    queryKey: procedureKeys.detail(id),
    queryFn: () => get<Procedure>(`/procedures/${id}`),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    enabled: !!id,
    ...options,
  });
}

// ============================================================================
// Credential Query Hooks
// ============================================================================

/**
 * Fetches credentials with optional filtering by person or procedure.
 *
 * This hook retrieves credentials based on the provided filters.
 * If person_id is provided, fetches credentials for that person.
 * If procedure_id is provided, fetches credentials for that procedure.
 *
 * @param filters - Optional filters for person_id, procedure_id, status, include_expired
 * @param options - Optional React Query configuration options
 * @returns Query result containing:
 *   - `data`: List response with credentials and total count
 *   - `isLoading`: Whether the fetch is in progress
 *   - `error`: Any error that occurred
 *
 * @example
 * ```tsx
 * function CredentialList({ personId }: Props) {
 *   const { data, isLoading } = useCredentials({ person_id: personId });
 *
 *   if (isLoading) return <Spinner />;
 *
 *   return <CredentialTable credentials={data.items} />;
 * }
 * ```
 */
export function useCredentials(
  filters?: CredentialFilters,
  options?: Omit<UseQueryOptions<ListResponse<Credential>, ApiError>, 'queryKey' | 'queryFn'>
): UseQueryResult<ListResponse<Credential>, ApiError> {
  // Determine which endpoint to use based on filters
  let endpoint = '/credentials';
  const params = new URLSearchParams();

  if (filters?.personId) {
    endpoint = `/credentials/by-person/${filters.personId}`;
  } else if (filters?.procedure_id) {
    endpoint = `/credentials/by-procedure/${filters.procedure_id}`;
  }

  if (filters?.status) params.set('status', filters.status);
  if (filters?.include_expired !== undefined) params.set('include_expired', String(filters.include_expired));
  const queryString = params.toString();

  return useQuery<ListResponse<Credential>, ApiError>({
    queryKey: credentialKeys.list(filters),
    queryFn: () => get<ListResponse<Credential>>(`${endpoint}${queryString ? `?${queryString}` : ''}`),
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 15 * 60 * 1000, // 15 minutes
    ...options,
  });
}

/**
 * Fetches a single credential by ID.
 *
 * This hook retrieves detailed information about a specific credential,
 * including status, competency level, and expiration information.
 *
 * @param id - The UUID of the credential to fetch
 * @param options - Optional React Query configuration options
 * @returns Query result containing:
 *   - `data`: The credential details
 *   - `isLoading`: Whether the fetch is in progress
 *   - `error`: Any error that occurred
 *
 * @example
 * ```tsx
 * function CredentialDetails({ credentialId }: Props) {
 *   const { data, isLoading, error } = useCredential(credentialId);
 *
 *   if (isLoading) return <Skeleton />;
 *   if (error) return <ErrorMessage error={error} />;
 *
 *   return <CredentialCard credential={data} />;
 * }
 * ```
 */
export function useCredential(
  id: string,
  options?: Omit<UseQueryOptions<Credential, ApiError>, 'queryKey' | 'queryFn'>
): UseQueryResult<Credential, ApiError> {
  return useQuery<Credential, ApiError>({
    queryKey: credentialKeys.detail(id),
    queryFn: () => get<Credential>(`/credentials/${id}`),
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 15 * 60 * 1000, // 15 minutes
    enabled: !!id,
    ...options,
  });
}

/**
 * Fetches credentials for a specific faculty member.
 *
 * This hook retrieves all credentials for a faculty member, showing which
 * procedures they are qualified to supervise. Supports filtering by status
 * and whether to include expired credentials.
 *
 * @param facultyId - The UUID of the faculty member (optional - if not provided, uses current user context)
 * @param filterOptions - Optional status filter and include_expired flag
 * @param options - Optional React Query configuration options
 * @returns Query result containing:
 *   - `data`: List response with credentials and total count
 *   - `isLoading`: Whether the fetch is in progress
 *   - `error`: Any error that occurred
 *
 * @example
 * ```tsx
 * function FacultyCredentials({ facultyId }: Props) {
 *   const { data, isLoading } = useFacultyCredentials(facultyId);
 *
 *   const expiringSoon = data?.items.filter(
 *     cred => cred.expiration_date && new Date(cred.expiration_date) < addDays(new Date(), 30)
 *   );
 *
 *   return (
 *     <div>
 *       {expiringSoon?.length > 0 && (
 *         <Alert variant="warning">
 *           {expiringSoon.length} credential(s) expiring soon
 *         </Alert>
 *       )}
 *       <CredentialTable credentials={data?.items} />
 *     </div>
 *   );
 * }
 * ```
 */
export function useFacultyCredentials(
  facultyId?: string,
  filterOptions?: { status?: CredentialStatus; include_expired?: boolean },
  options?: Omit<UseQueryOptions<ListResponse<Credential>, ApiError>, 'queryKey' | 'queryFn'>
): UseQueryResult<ListResponse<Credential>, ApiError> {
  const params = new URLSearchParams();
  if (filterOptions?.status) params.set('status', filterOptions.status);
  if (filterOptions?.include_expired !== undefined) params.set('include_expired', String(filterOptions.include_expired));
  const queryString = params.toString();

  return useQuery<ListResponse<Credential>, ApiError>({
    queryKey: credentialKeys.byPerson(facultyId || '', filterOptions),
    queryFn: () => get<ListResponse<Credential>>(
      `/credentials/by-person/${facultyId}${queryString ? `?${queryString}` : ''}`
    ),
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 15 * 60 * 1000, // 15 minutes
    enabled: !!facultyId,
    ...options,
  });
}

/**
 * Fetches faculty members qualified to supervise a specific procedure.
 *
 * This hook retrieves all faculty members with active, valid credentials
 * for a given procedure. Useful for finding available supervisors.
 *
 * @param procedureId - The UUID of the procedure
 * @param options - Optional React Query configuration options
 * @returns Query result containing:
 *   - `data`: Response with procedure info and list of qualified faculty
 *   - `isLoading`: Whether the fetch is in progress
 *   - `error`: Any error that occurred
 *
 * @example
 * ```tsx
 * function SupervisorSelector({ procedureId, onSelect }: Props) {
 *   const { data, isLoading } = useQualifiedFaculty(procedureId);
 *
 *   if (isLoading) return <Spinner />;
 *
 *   if (data.total === 0) {
 *     return <Alert variant="warning">No qualified faculty available</Alert>;
 *   }
 *
 *   return (
 *     <Select label="Select Supervisor" onChange={onSelect}>
 *       {data.qualified_faculty.map(faculty => (
 *         <option key={faculty.id} value={faculty.id}>
 *           {faculty.name}
 *         </option>
 *       ))}
 *     </Select>
 *   );
 * }
 * ```
 */
export function useQualifiedFaculty(
  procedureId: string,
  options?: Omit<UseQueryOptions<QualifiedFacultyResponse, ApiError>, 'queryKey' | 'queryFn'>
): UseQueryResult<QualifiedFacultyResponse, ApiError> {
  return useQuery<QualifiedFacultyResponse, ApiError>({
    queryKey: credentialKeys.qualified(procedureId),
    queryFn: () => get<QualifiedFacultyResponse>(`/credentials/qualified-faculty/${procedureId}`),
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 15 * 60 * 1000, // 15 minutes
    enabled: !!procedureId,
    ...options,
  });
}

/**
 * Fetches a summary of a faculty member's credentials.
 *
 * This hook provides a high-level overview of a faculty member's credentials,
 * including counts of active, total, and expiring credentials.
 *
 * @param personId - The UUID of the faculty member
 * @param options - Optional React Query configuration options
 * @returns Query result containing credential summary
 *
 * @example
 * ```tsx
 * function FacultyCredentialBadges({ personId }: Props) {
 *   const { data, isLoading } = useFacultyCredentialSummary(personId);
 *
 *   if (isLoading) return <Skeleton />;
 *
 *   return (
 *     <div className="flex gap-2">
 *       <Badge variant="success">{data.active_credentials} Active</Badge>
 *       {data.expiring_soon > 0 && (
 *         <Badge variant="warning">{data.expiring_soon} Expiring Soon</Badge>
 *       )}
 *     </div>
 *   );
 * }
 * ```
 */
export function useFacultyCredentialSummary(
  personId: string,
  options?: Omit<UseQueryOptions<FacultyCredentialSummary, ApiError>, 'queryKey' | 'queryFn'>
): UseQueryResult<FacultyCredentialSummary, ApiError> {
  return useQuery<FacultyCredentialSummary, ApiError>({
    queryKey: credentialKeys.summary(personId),
    queryFn: () => get<FacultyCredentialSummary>(`/credentials/summary/${personId}`),
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 15 * 60 * 1000, // 15 minutes
    enabled: !!personId,
    ...options,
  });
}

// ============================================================================
// Credential Mutation Hooks
// ============================================================================

/**
 * Creates a new credential for a faculty member.
 *
 * This mutation hook grants a faculty member credentials to supervise
 * a specific procedure. Automatically refreshes all credential queries.
 *
 * @returns Mutation object containing:
 *   - `mutate`: Function to create a credential
 *   - `mutateAsync`: Async version returning a Promise
 *   - `isPending`: Whether creation is in progress
 *   - `isSuccess`: Whether creation completed successfully
 *   - `isError`: Whether an error occurred
 *   - `error`: Any error that occurred
 *   - `data`: The created credential
 *
 * @example
 * ```tsx
 * function GrantCredentialForm({ facultyId }: Props) {
 *   const { mutate, isPending } = useCreateCredential();
 *
 *   const handleSubmit = (formData: CredentialCreate) => {
 *     mutate(formData, {
 *       onSuccess: (newCredential) => {
 *         toast.success('Credential granted successfully');
 *         navigate(`/credentials/${newCredential.id}`);
 *       },
 *       onError: (error) => {
 *         toast.error(`Failed to grant credential: ${error.message}`);
 *       },
 *     });
 *   };
 *
 *   return <CredentialForm onSubmit={handleSubmit} loading={isPending} />;
 * }
 * ```
 */
export function useCreateCredential(): UseMutationResult<Credential, ApiError, CredentialCreate> {
  const queryClient = useQueryClient();

  return useMutation<Credential, ApiError, CredentialCreate>({
    mutationFn: (data) => post<Credential>('/credentials', data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: credentialKeys.all });
      queryClient.invalidateQueries({ queryKey: credentialKeys.byPerson(data.personId) });
      queryClient.invalidateQueries({ queryKey: credentialKeys.byProcedure(data.procedure_id) });
      queryClient.invalidateQueries({ queryKey: credentialKeys.qualified(data.procedure_id) });
      queryClient.invalidateQueries({ queryKey: credentialKeys.summary(data.personId) });
    },
  });
}

/**
 * Updates an existing credential.
 *
 * This mutation hook modifies credential details such as status,
 * competency level, expiration date, or notes.
 *
 * @returns Mutation object containing:
 *   - `mutate`: Function to update a credential
 *   - `mutateAsync`: Async version returning a Promise
 *   - `isPending`: Whether update is in progress
 *   - `isSuccess`: Whether update completed successfully
 *   - `error`: Any error that occurred
 *   - `data`: The updated credential
 *
 * @example
 * ```tsx
 * function EditCredentialForm({ credential }: Props) {
 *   const { mutate, isPending } = useUpdateCredential();
 *
 *   const handleUpdate = (updates: CredentialUpdate) => {
 *     mutate(
 *       { id: credential.id, data: updates },
 *       {
 *         onSuccess: () => {
 *           toast.success('Credential updated');
 *         },
 *         onError: (error) => {
 *           toast.error(`Update failed: ${error.message}`);
 *         },
 *       }
 *     );
 *   };
 *
 *   return <CredentialForm initialData={credential} onSubmit={handleUpdate} />;
 * }
 * ```
 */
export function useUpdateCredential(): UseMutationResult<Credential, ApiError, { id: string; data: CredentialUpdate }> {
  const queryClient = useQueryClient();

  return useMutation<Credential, ApiError, { id: string; data: CredentialUpdate }>({
    mutationFn: ({ id, data }) => put<Credential>(`/credentials/${id}`, data),
    onSuccess: (data, { id }) => {
      queryClient.invalidateQueries({ queryKey: credentialKeys.all });
      queryClient.invalidateQueries({ queryKey: credentialKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: credentialKeys.byPerson(data.personId) });
      queryClient.invalidateQueries({ queryKey: credentialKeys.byProcedure(data.procedure_id) });
      queryClient.invalidateQueries({ queryKey: credentialKeys.qualified(data.procedure_id) });
      queryClient.invalidateQueries({ queryKey: credentialKeys.summary(data.personId) });
    },
  });
}

/**
 * Deletes a credential.
 *
 * This mutation hook permanently removes a credential. Use with caution
 * as this revokes a faculty member's ability to supervise the procedure.
 *
 * @returns Mutation object containing:
 *   - `mutate`: Function to delete a credential by ID
 *   - `mutateAsync`: Async version returning a Promise
 *   - `isPending`: Whether deletion is in progress
 *   - `isSuccess`: Whether deletion completed successfully
 *   - `error`: Any error that occurred
 *
 * @example
 * ```tsx
 * function CredentialActions({ credential }: Props) {
 *   const { mutate, isPending } = useDeleteCredential();
 *
 *   const handleDelete = () => {
 *     if (confirm('Delete this credential? This cannot be undone.')) {
 *       mutate(credential.id, {
 *         onSuccess: () => {
 *           toast.success('Credential removed');
 *           navigate('/credentials');
 *         },
 *         onError: (error) => {
 *           toast.error(`Failed to delete: ${error.message}`);
 *         },
 *       });
 *     }
 *   };
 *
 *   return (
 *     <Button onClick={handleDelete} loading={isPending} variant="danger">
 *       Delete Credential
 *     </Button>
 *   );
 * }
 * ```
 */
export function useDeleteCredential(): UseMutationResult<void, ApiError, string> {
  const queryClient = useQueryClient();

  return useMutation<void, ApiError, string>({
    mutationFn: (id) => del(`/credentials/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: credentialKeys.all });
    },
  });
}

// ============================================================================
// Procedure Mutation Hooks
// ============================================================================

/**
 * Creates a new procedure in the catalog.
 *
 * This mutation hook adds a new medical procedure to the system.
 * New procedures can be assigned supervision requirements and complexity levels.
 *
 * @returns Mutation object containing:
 *   - `mutate`: Function to create a procedure
 *   - `mutateAsync`: Async version returning a Promise
 *   - `isPending`: Whether creation is in progress
 *   - `isSuccess`: Whether creation completed successfully
 *   - `error`: Any error that occurred
 *   - `data`: The created procedure
 *
 * @example
 * ```tsx
 * function NewProcedureForm() {
 *   const { mutate, isPending } = useCreateProcedure();
 *
 *   const handleSubmit = (formData: ProcedureCreate) => {
 *     mutate(formData, {
 *       onSuccess: (newProcedure) => {
 *         toast.success(`Procedure "${newProcedure.name}" created`);
 *         navigate(`/procedures/${newProcedure.id}`);
 *       },
 *       onError: (error) => {
 *         if (error.status === 409) {
 *           toast.error('A procedure with this name already exists');
 *         } else {
 *           toast.error(`Failed to create procedure: ${error.message}`);
 *         }
 *       },
 *     });
 *   };
 *
 *   return <ProcedureForm onSubmit={handleSubmit} loading={isPending} />;
 * }
 * ```
 */
export function useCreateProcedure(): UseMutationResult<Procedure, ApiError, ProcedureCreate> {
  const queryClient = useQueryClient();

  return useMutation<Procedure, ApiError, ProcedureCreate>({
    mutationFn: (data) => post<Procedure>('/procedures', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: procedureKeys.all });
    },
  });
}

/**
 * Updates an existing procedure.
 *
 * This mutation hook modifies procedure details such as name, description,
 * supervision requirements, or complexity level.
 *
 * @returns Mutation object containing:
 *   - `mutate`: Function to update a procedure
 *   - `mutateAsync`: Async version returning a Promise
 *   - `isPending`: Whether update is in progress
 *   - `isSuccess`: Whether update completed successfully
 *   - `error`: Any error that occurred
 *   - `data`: The updated procedure
 *
 * @example
 * ```tsx
 * function EditProcedureForm({ procedure }: Props) {
 *   const { mutate, isPending } = useUpdateProcedure();
 *
 *   const handleUpdate = (updates: ProcedureUpdate) => {
 *     mutate(
 *       { id: procedure.id, data: updates },
 *       {
 *         onSuccess: () => {
 *           toast.success('Procedure updated');
 *           navigate(`/procedures/${procedure.id}`);
 *         },
 *         onError: (error) => {
 *           toast.error(`Update failed: ${error.message}`);
 *         },
 *       }
 *     );
 *   };
 *
 *   return <ProcedureForm initialData={procedure} onSubmit={handleUpdate} />;
 * }
 * ```
 */
export function useUpdateProcedure(): UseMutationResult<Procedure, ApiError, { id: string; data: ProcedureUpdate }> {
  const queryClient = useQueryClient();

  return useMutation<Procedure, ApiError, { id: string; data: ProcedureUpdate }>({
    mutationFn: ({ id, data }) => put<Procedure>(`/procedures/${id}`, data),
    onSuccess: (data, { id }) => {
      queryClient.invalidateQueries({ queryKey: procedureKeys.all });
      queryClient.invalidateQueries({ queryKey: procedureKeys.detail(id) });
      // Also invalidate credentials since procedure info may be embedded
      queryClient.invalidateQueries({ queryKey: credentialKeys.all });
    },
  });
}

/**
 * Deletes a procedure from the catalog.
 *
 * This mutation hook permanently removes a procedure. Use with caution
 * as this may affect existing credentials referencing the procedure.
 *
 * @returns Mutation object containing:
 *   - `mutate`: Function to delete a procedure by ID
 *   - `mutateAsync`: Async version returning a Promise
 *   - `isPending`: Whether deletion is in progress
 *   - `isSuccess`: Whether deletion completed successfully
 *   - `error`: Any error that occurred
 *
 * @example
 * ```tsx
 * function ProcedureActions({ procedure }: Props) {
 *   const { mutate, isPending } = useDeleteProcedure();
 *
 *   const handleDelete = () => {
 *     if (confirm(`Delete "${procedure.name}"? This cannot be undone.`)) {
 *       mutate(procedure.id, {
 *         onSuccess: () => {
 *           toast.success('Procedure removed');
 *           navigate('/procedures');
 *         },
 *         onError: (error) => {
 *           if (error.status === 409) {
 *             toast.error('Cannot delete: procedure has active credentials');
 *           } else {
 *             toast.error(`Failed to delete: ${error.message}`);
 *           }
 *         },
 *       });
 *     }
 *   };
 *
 *   return (
 *     <Button onClick={handleDelete} loading={isPending} variant="danger">
 *       Delete Procedure
 *     </Button>
 *   );
 * }
 * ```
 */
export function useDeleteProcedure(): UseMutationResult<void, ApiError, string> {
  const queryClient = useQueryClient();

  return useMutation<void, ApiError, string>({
    mutationFn: (id) => del(`/procedures/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: procedureKeys.all });
      // Also invalidate credentials since some may have been orphaned
      queryClient.invalidateQueries({ queryKey: credentialKeys.all });
    },
  });
}

// ============================================================================
// Additional Utility Hooks
// ============================================================================

/**
 * Fetches credentials expiring within a specified number of days.
 *
 * This hook is useful for building expiration warning dashboards
 * and proactive renewal reminders.
 *
 * @param days - Number of days to look ahead (default: 30)
 * @param options - Optional React Query configuration options
 * @returns Query result containing list of expiring credentials
 *
 * @example
 * ```tsx
 * function ExpiringCredentialsAlert() {
 *   const { data, isLoading } = useExpiringCredentials(30);
 *
 *   if (isLoading || !data?.items.length) return null;
 *
 *   return (
 *     <Alert variant="warning">
 *       <strong>{data.items.length}</strong> credentials expiring in the next 30 days
 *     </Alert>
 *   );
 * }
 * ```
 */
export function useExpiringCredentials(
  days: number = 30,
  options?: Omit<UseQueryOptions<ListResponse<Credential>, ApiError>, 'queryKey' | 'queryFn'>
): UseQueryResult<ListResponse<Credential>, ApiError> {
  return useQuery<ListResponse<Credential>, ApiError>({
    queryKey: credentialKeys.expiring(days),
    queryFn: () => get<ListResponse<Credential>>(`/credentials/expiring?days=${days}`),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    ...options,
  });
}

/**
 * Fetches all unique specialties from procedures.
 *
 * Useful for building filter dropdowns and categorization UIs.
 *
 * @param options - Optional React Query configuration options
 * @returns Query result containing list of specialty strings
 */
export function useProcedureSpecialties(
  options?: Omit<UseQueryOptions<string[], ApiError>, 'queryKey' | 'queryFn'>
): UseQueryResult<string[], ApiError> {
  return useQuery<string[], ApiError>({
    queryKey: procedureKeys.specialties(),
    queryFn: () => get<string[]>('/procedures/specialties'),
    staleTime: 10 * 60 * 1000, // 10 minutes
    gcTime: 60 * 60 * 1000, // 1 hour
    ...options,
  });
}

/**
 * Fetches all unique categories from procedures.
 *
 * Useful for building filter dropdowns and categorization UIs.
 *
 * @param options - Optional React Query configuration options
 * @returns Query result containing list of category strings
 */
export function useProcedureCategories(
  options?: Omit<UseQueryOptions<string[], ApiError>, 'queryKey' | 'queryFn'>
): UseQueryResult<string[], ApiError> {
  return useQuery<string[], ApiError>({
    queryKey: procedureKeys.categories(),
    queryFn: () => get<string[]>('/procedures/categories'),
    staleTime: 10 * 60 * 1000, // 10 minutes
    gcTime: 60 * 60 * 1000, // 1 hour
    ...options,
  });
}
