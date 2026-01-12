/**
 * Schedule Management Hooks
 *
 * Hooks for schedule generation, validation, rotation templates,
 * and assignment management with React Query caching.
 */
import { ApiError, del, get, post, put } from "@/lib/api";
import type {
  Assignment,
  AssignmentCreate,
  AssignmentUpdate,
  RotationTemplate,
  RotationTemplateCreate,
  RotationTemplateUpdate,
  ValidationResult,
} from "@/types/api";
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

export interface AssignmentFilters {
  startDate?: string;
  endDate?: string;
  personId?: string;
  role?: string;
  pageSize?: number;
}

export interface ScheduleGenerateRequest {
  startDate: string;
  endDate: string;
  pgyLevels?: number[];
  rotationTemplateIds?: string[];
  algorithm?: "greedy" | "cpSat" | "pulp" | "hybrid";
  timeout_seconds?: number;
}

export interface ScheduleGenerateResponse {
  status: "success" | "partial" | "failed";
  message: string;
  totalBlocks_assigned: number;
  totalBlocks: number;
  validation: ValidationResult;
  run_id?: string;
  solverStats?: {
    totalResidents?: number;
    coverageRate?: number;
    solve_time?: number;
    iterations?: number;
    branches?: number;
    conflicts?: number;
    [key: string]: unknown;
  };
}

// ============================================================================
// Query Keys
// ============================================================================

export const scheduleQueryKeys = {
  schedule: (startDate: string, endDate: string) =>
    ["schedule", startDate, endDate] as const,
  rotationTemplates: (activityType?: string) =>
    ["rotation-templates", activityType] as const,
  rotationTemplate: (id: string) => ["rotation-templates", id] as const,
  validation: (startDate: string, endDate: string) =>
    ["validation", startDate, endDate] as const,
  assignments: (filters?: AssignmentFilters) =>
    ["assignments", filters] as const,
};

// ============================================================================
// Schedule Hooks
// ============================================================================

/**
 * Fetches schedule assignments for a specified date range.
 *
 * This hook retrieves all assignments within the given time period, providing
 * the data needed for calendar views and schedule displays. It uses React Query
 * for automatic caching, background refetching, and optimistic updates.
 *
 * @param startDate - The start date of the schedule range
 * @param endDate - The end date of the schedule range
 * @param options - Optional React Query configuration options
 * @returns Query result containing:
 *   - `data`: List response with assignments and total count
 *   - `isLoading`: Whether the initial fetch is in progress
 *   - `isFetching`: Whether any fetch is in progress (including background)
 *   - `error`: Any error that occurred during fetch
 *   - `refetch`: Function to manually refetch the schedule
 *
 * @example
 * ```tsx
 * function ScheduleCalendar() {
 *   const startDate = new Date('2024-01-01');
 *   const endDate = new Date('2024-01-31');
 *   const { data, isLoading, error } = useSchedule(startDate, endDate);
 *
 *   if (isLoading) return <Spinner />;
 *   if (error) return <ErrorAlert error={error} />;
 *
 *   return (
 *     <Calendar
 *       assignments={data.items}
 *       total={data.total}
 *     />
 *   );
 * }
 * ```
 *
 * @see useAssignments - For more advanced filtering options
 * @see useGenerateSchedule - For creating new schedules
 */
export function useSchedule(
  startDate: Date,
  endDate: Date,
  options?: Omit<
    UseQueryOptions<ListResponse<Assignment>, ApiError>,
    "queryKey" | "queryFn"
  >
) {
  const startIso = startDate.toISOString();
  const endIso = endDate.toISOString();
  const startDateStr = startDate.toISOString().split("T")[0];
  const endDateStr = endDate.toISOString().split("T")[0];

  return useQuery<ListResponse<Assignment>, ApiError>({
    queryKey: ["schedule", startIso, endIso],
    queryFn: () =>
      get<ListResponse<Assignment>>(
        `/assignments?start_date=${startDateStr}&end_date=${endDateStr}&page_size=5000`
      ),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    refetchOnWindowFocus: true,
    ...options,
  });
}

/**
 * Generates a new schedule using constraint satisfaction algorithms.
 *
 * This mutation hook triggers the schedule generation engine, which uses
 * various algorithms (greedy, CP-SAT, PuLP, or hybrid) to create optimal
 * resident rotation assignments while respecting ACGME rules, preferences,
 * and rotation requirements.
 *
 * @returns Mutation object containing:
 *   - `mutate`: Function to trigger schedule generation
 *   - `mutateAsync`: Async version returning a Promise
 *   - `isPending`: Whether generation is in progress
 *   - `isSuccess`: Whether generation completed successfully
 *   - `isError`: Whether an error occurred
 *   - `error`: Any error that occurred during generation
 *   - `data`: Generation response with statistics and validation results
 *
 * @example
 * ```tsx
 * function ScheduleGenerator() {
 *   const { mutate, isPending, data } = useGenerateSchedule();
 *
 *   const handleGenerate = () => {
 *     mutate({
 *       startDate: '2024-07-01',
 *       endDate: '2024-06-30',
 *       pgyLevels: [1, 2, 3],
 *       algorithm: 'hybrid',
 *       timeout_seconds: 300,
 *     }, {
 *       onSuccess: (result) => {
 *         if (result.status === 'success') {
 *           toast.success(`Generated ${result.totalBlocks_assigned} assignments`);
 *         } else {
 *           toast.warning('Partial schedule generated - review needed');
 *         }
 *       },
 *     });
 *   };
 *
 *   return (
 *     <div>
 *       <GenerateButton onClick={handleGenerate} loading={isPending} />
 *       {data && <GenerationStats stats={data.solverStats} />}
 *     </div>
 *   );
 * }
 * ```
 *
 * @see useValidateSchedule - For validating generated schedules
 * @see ScheduleGenerateRequest - Input parameters for generation
 */
export function useGenerateSchedule() {
  const queryClient = useQueryClient();

  return useMutation<
    ScheduleGenerateResponse,
    ApiError,
    ScheduleGenerateRequest
  >({
    mutationFn: (request) =>
      post<ScheduleGenerateResponse>("/schedule/generate", request),
    onSuccess: () => {
      // Invalidate schedule queries for the affected date range
      queryClient.invalidateQueries({ queryKey: ["schedule"] });
      queryClient.invalidateQueries({ queryKey: ["validation"] });
      queryClient.invalidateQueries({ queryKey: ["assignments"] });
    },
  });
}

/**
 * Validates schedule compliance with ACGME duty hour regulations.
 *
 * This hook checks the current schedule against all ACGME rules including
 * 80-hour work weeks, mandatory rest periods, and maximum shift durations.
 * It provides detailed violation reports for review and correction.
 *
 * @param startDate - Start date for validation range (ISO format)
 * @param endDate - End date for validation range (ISO format)
 * @param options - Optional React Query configuration options
 * @returns Query result containing:
 *   - `data`: Validation result with violations and warnings
 *   - `isLoading`: Whether validation is in progress
 *   - `error`: Any error that occurred during validation
 *   - `refetch`: Function to manually revalidate
 *
 * @example
 * ```tsx
 * function ScheduleValidator({ scheduleId }: Props) {
 *   const { data, isLoading } = useValidateSchedule(
 *     '2024-01-01',
 *     '2024-01-31'
 *   );
 *
 *   if (isLoading) return <ValidatingSpinner />;
 *
 *   return (
 *     <ValidationReport
 *       violations={data.violations}
 *       warnings={data.warnings}
 *       isCompliant={data.is_compliant}
 *     />
 *   );
 * }
 * ```
 *
 * @see useSchedule - For fetching the schedule being validated
 * @see useGenerateSchedule - Returns validation results after generation
 */
export function useValidateSchedule(
  startDate: string,
  endDate: string,
  options?: Omit<
    UseQueryOptions<ValidationResult, ApiError>,
    "queryKey" | "queryFn"
  >
) {
  return useQuery<ValidationResult, ApiError>({
    queryKey: scheduleQueryKeys.validation(startDate, endDate),
    queryFn: () =>
      get<ValidationResult>(
        `/schedule/validate?start_date=${startDate}&end_date=${endDate}`
      ),
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    ...options,
  });
}

// ============================================================================
// Rotation Template Hooks
// ============================================================================

/**
 * Fetches all rotation templates available for schedule generation.
 *
 * This hook retrieves the library of rotation templates that define the
 * various clinical rotations, activities, and schedules available for
 * residents. Templates include duration, requirements, and constraints.
 *
 * @param options - Optional React Query configuration options
 * @returns Query result containing:
 *   - `data`: List of all rotation templates
 *   - `isLoading`: Whether the fetch is in progress
 *   - `error`: Any error that occurred
 *   - `refetch`: Function to manually refetch templates
 *
 * @example
 * ```tsx
 * function RotationSelector() {
 *   const { data, isLoading } = useRotationTemplates();
 *
 *   if (isLoading) return <Skeleton />;
 *
 *   return (
 *     <Select label="Select Rotation">
 *       {data.items.map(template => (
 *         <option key={template.id} value={template.id}>
 *           {template.name} ({template.duration_weeks} weeks)
 *         </option>
 *       ))}
 *     </Select>
 *   );
 * }
 * ```
 *
 * @see useRotationTemplate - For fetching a single template
 * @see useCreateTemplate - For creating new templates
 */
export function useRotationTemplates(
  options?: Omit<
    UseQueryOptions<ListResponse<RotationTemplate>, ApiError>,
    "queryKey" | "queryFn"
  >
) {
  return useQuery<ListResponse<RotationTemplate>, ApiError>({
    queryKey: ["rotation-templates"],
    queryFn: () => get<ListResponse<RotationTemplate>>("/rotation-templates"),
    staleTime: 10 * 60 * 1000, // 10 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    ...options,
  });
}

/**
 * Fetches detailed information for a specific rotation template.
 *
 * This hook retrieves full details for a single rotation template including
 * all configuration settings, requirements, and metadata. Useful for editing
 * or displaying template details.
 *
 * @param id - The UUID of the rotation template to fetch
 * @param options - Optional React Query configuration options
 * @returns Query result containing:
 *   - `data`: The rotation template details
 *   - `isLoading`: Whether the fetch is in progress
 *   - `error`: Any error that occurred
 *   - `refetch`: Function to manually refetch the template
 *
 * @example
 * ```tsx
 * function TemplateEditor({ templateId }: Props) {
 *   const { data, isLoading, error } = useRotationTemplate(templateId);
 *
 *   if (isLoading) return <LoadingState />;
 *   if (error) return <ErrorMessage error={error} />;
 *
 *   return (
 *     <TemplateForm
 *       initialData={data}
 *       mode="edit"
 *     />
 *   );
 * }
 * ```
 *
 * @see useRotationTemplates - For fetching all templates
 * @see useUpdateTemplate - For updating template details
 */
export function useRotationTemplate(
  id: string,
  options?: Omit<
    UseQueryOptions<RotationTemplate, ApiError>,
    "queryKey" | "queryFn"
  >
) {
  return useQuery<RotationTemplate, ApiError>({
    queryKey: scheduleQueryKeys.rotationTemplate(id),
    queryFn: () => get<RotationTemplate>(`/rotation-templates/${id}`),
    staleTime: 10 * 60 * 1000, // 10 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    enabled: !!id,
    ...options,
  });
}

/**
 * Creates a new rotation template for use in schedule generation.
 *
 * This mutation hook allows creation of new rotation definitions including
 * duration, requirements, specialty, and scheduling constraints. Templates
 * can then be used when generating resident schedules.
 *
 * @returns Mutation object containing:
 *   - `mutate`: Function to create a template
 *   - `mutateAsync`: Async version returning a Promise
 *   - `isPending`: Whether creation is in progress
 *   - `isSuccess`: Whether creation completed successfully
 *   - `isError`: Whether an error occurred
 *   - `error`: Any error that occurred
 *   - `data`: The created template with generated ID
 *
 * @example
 * ```tsx
 * function NewTemplateForm() {
 *   const { mutate, isPending } = useCreateTemplate();
 *
 *   const handleSubmit = (formData: RotationTemplateCreate) => {
 *     mutate(formData, {
 *       onSuccess: (newTemplate) => {
 *         toast.success(`Created template: ${newTemplate.name}`);
 *         navigate(`/templates/${newTemplate.id}`);
 *       },
 *       onError: (error) => {
 *         toast.error(`Failed to create template: ${error.message}`);
 *       },
 *     });
 *   };
 *
 *   return <TemplateForm onSubmit={handleSubmit} loading={isPending} />;
 * }
 * ```
 *
 * @see useUpdateTemplate - For modifying existing templates
 * @see useRotationTemplates - List is auto-refreshed after creation
 */
export function useCreateTemplate() {
  const queryClient = useQueryClient();

  return useMutation<RotationTemplate, ApiError, RotationTemplateCreate>({
    mutationFn: (data) => post<RotationTemplate>("/rotation-templates", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["rotation-templates"] });
    },
  });
}

/**
 * Updates an existing rotation template with new configuration.
 *
 * This mutation hook modifies rotation template settings such as duration,
 * requirements, or constraints. Changes automatically invalidate related
 * queries to ensure UI consistency.
 *
 * @returns Mutation object containing:
 *   - `mutate`: Function to update a template
 *   - `mutateAsync`: Async version returning a Promise
 *   - `isPending`: Whether update is in progress
 *   - `isSuccess`: Whether update completed successfully
 *   - `isError`: Whether an error occurred
 *   - `error`: Any error that occurred
 *   - `data`: The updated template
 *
 * @example
 * ```tsx
 * function TemplateEditor({ templateId }: Props) {
 *   const { mutate, isPending } = useUpdateTemplate();
 *   const { data: template } = useRotationTemplate(templateId);
 *
 *   const handleSave = (updates: RotationTemplateUpdate) => {
 *     mutate(
 *       { id: templateId, data: updates },
 *       {
 *         onSuccess: () => {
 *           toast.success('Template updated successfully');
 *         },
 *       }
 *     );
 *   };
 *
 *   return <TemplateForm initialData={template} onSubmit={handleSave} />;
 * }
 * ```
 *
 * @see useRotationTemplate - Query is auto-refreshed after update
 * @see useCreateTemplate - For creating new templates
 */
export function useUpdateTemplate() {
  const queryClient = useQueryClient();

  return useMutation<
    RotationTemplate,
    ApiError,
    { id: string; data: RotationTemplateUpdate }
  >({
    mutationFn: ({ id, data }) =>
      put<RotationTemplate>(`/rotation-templates/${id}`, data),
    onSuccess: (data, { id }) => {
      queryClient.invalidateQueries({ queryKey: ["rotation-templates"] });
      queryClient.invalidateQueries({
        queryKey: scheduleQueryKeys.rotationTemplate(id),
      });
    },
  });
}

/**
 * Deletes a rotation template from the system.
 *
 * This mutation hook permanently removes a rotation template. Use with
 * caution as this action cannot be undone. Templates in active use by
 * schedules may not be deletable depending on backend constraints.
 *
 * @returns Mutation object containing:
 *   - `mutate`: Function to delete a template by ID
 *   - `mutateAsync`: Async version returning a Promise
 *   - `isPending`: Whether deletion is in progress
 *   - `isSuccess`: Whether deletion completed successfully
 *   - `isError`: Whether an error occurred
 *   - `error`: Any error that occurred (e.g., template in use)
 *
 * @example
 * ```tsx
 * function TemplateActions({ templateId }: Props) {
 *   const { mutate, isPending } = useDeleteTemplate();
 *
 *   const handleDelete = () => {
 *     if (confirm('Are you sure? This cannot be undone.')) {
 *       mutate(templateId, {
 *         onSuccess: () => {
 *           toast.success('Template deleted');
 *           navigate('/templates');
 *         },
 *         onError: (error) => {
 *           if (error.status === 409) {
 *             toast.error('Cannot delete: template is in use');
 *           }
 *         },
 *       });
 *     }
 *   };
 *
 *   return <DeleteButton onClick={handleDelete} loading={isPending} />;
 * }
 * ```
 *
 * @see useRotationTemplates - List is auto-refreshed after deletion
 */
export function useDeleteTemplate() {
  const queryClient = useQueryClient();

  return useMutation<void, ApiError, string>({
    mutationFn: (id) => del(`/rotation-templates/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["rotation-templates"] });
    },
  });
}

// ============================================================================
// Assignment Hooks
// ============================================================================

/**
 * Fetches assignments with advanced filtering capabilities.
 *
 * This hook provides fine-grained control over assignment queries, allowing
 * filtering by date range, person, role, and other criteria. Ideal for
 * building filtered views, reports, and person-specific schedules.
 *
 * @param filters - Optional filters for date range, person, role, etc.
 * @param options - Optional React Query configuration options
 * @returns Query result containing:
 *   - `data`: List of assignments matching the filters
 *   - `isLoading`: Whether the fetch is in progress
 *   - `error`: Any error that occurred
 *   - `refetch`: Function to manually refetch with current filters
 *
 * @example
 * ```tsx
 * function ResidentSchedule({ residentId }: Props) {
 *   const { data, isLoading } = useAssignments({
 *     personId: residentId,
 *     startDate: '2024-07-01',
 *     endDate: '2024-12-31',
 *     role: 'resident',
 *   });
 *
 *   if (isLoading) return <LoadingSkeleton />;
 *
 *   return (
 *     <AssignmentList
 *       assignments={data.items}
 *       total={data.total}
 *     />
 *   );
 * }
 * ```
 *
 * @see useSchedule - For basic date-range queries
 * @see AssignmentFilters - Available filter options
 */
export function useAssignments(
  filters?: AssignmentFilters,
  options?: Omit<
    UseQueryOptions<ListResponse<Assignment>, ApiError>,
    "queryKey" | "queryFn"
  >
) {
  const params = new URLSearchParams();
  if (filters?.startDate) params.set("start_date", filters.startDate);
  if (filters?.endDate) params.set("end_date", filters.endDate);
  if (filters?.personId) params.set("person_id", filters.personId);
  if (filters?.role) params.set("role", filters.role);
  if (filters?.pageSize) params.set("page_size", filters.pageSize.toString());
  const queryString = params.toString();

  return useQuery<ListResponse<Assignment>, ApiError>({
    queryKey: scheduleQueryKeys.assignments(filters),
    queryFn: () =>
      get<ListResponse<Assignment>>(
        `/assignments${queryString ? `?${queryString}` : ""}`
      ),
    staleTime: 60 * 1000, // 1 minute
    gcTime: 30 * 60 * 1000, // 30 minutes
    ...options,
  });
}

/**
 * Creates a new assignment in the schedule.
 *
 * This mutation hook allows manual creation of schedule assignments,
 * useful for filling gaps, adding special assignments, or making
 * manual adjustments to generated schedules. Automatically triggers
 * validation and cache updates.
 *
 * @returns Mutation object containing:
 *   - `mutate`: Function to create an assignment
 *   - `mutateAsync`: Async version returning a Promise
 *   - `isPending`: Whether creation is in progress
 *   - `isSuccess`: Whether creation completed successfully
 *   - `isError`: Whether an error occurred
 *   - `error`: Any error that occurred (e.g., conflicts, validation)
 *   - `data`: The created assignment with generated ID
 *
 * @example
 * ```tsx
 * function QuickAssignDialog({ date, rotation }: Props) {
 *   const { mutate, isPending } = useCreateAssignment();
 *
 *   const handleAssign = (personId: string) => {
 *     mutate({
 *       personId: personId,
 *       rotationId: rotation.id,
 *       startDate: date,
 *       endDate: addWeeks(date, rotation.duration_weeks),
 *     }, {
 *       onSuccess: () => {
 *         toast.success('Assignment created');
 *         closeDialog();
 *       },
 *       onError: (error) => {
 *         toast.error(`Cannot assign: ${error.message}`);
 *       },
 *     });
 *   };
 *
 *   return <PersonSelector onSelect={handleAssign} loading={isPending} />;
 * }
 * ```
 *
 * @see useUpdateAssignment - For modifying existing assignments
 * @see useValidateSchedule - Validation is auto-triggered after creation
 */
export function useCreateAssignment() {
  const queryClient = useQueryClient();

  return useMutation<Assignment, ApiError, AssignmentCreate>({
    mutationFn: (data) => post<Assignment>("/assignments", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assignments"] });
      queryClient.invalidateQueries({ queryKey: ["schedule"] });
      queryClient.invalidateQueries({ queryKey: ["validation"] });
    },
  });
}

/**
 * Updates an existing assignment with new details.
 *
 * This mutation hook modifies assignment properties such as dates,
 * rotation, or person. Useful for schedule adjustments, swaps, and
 * corrections. Automatically revalidates affected date ranges.
 *
 * @returns Mutation object containing:
 *   - `mutate`: Function to update an assignment
 *   - `mutateAsync`: Async version returning a Promise
 *   - `isPending`: Whether update is in progress
 *   - `isSuccess`: Whether update completed successfully
 *   - `isError`: Whether an error occurred
 *   - `error`: Any error that occurred
 *   - `data`: The updated assignment
 *
 * @example
 * ```tsx
 * function AssignmentEditor({ assignmentId }: Props) {
 *   const { mutate, isPending } = useUpdateAssignment();
 *
 *   const handleUpdate = (updates: AssignmentUpdate) => {
 *     mutate(
 *       { id: assignmentId, data: updates },
 *       {
 *         onSuccess: () => {
 *           toast.success('Assignment updated');
 *         },
 *         onError: (error) => {
 *           toast.error(`Update failed: ${error.message}`);
 *         },
 *       }
 *     );
 *   };
 *
 *   return <AssignmentForm onSubmit={handleUpdate} loading={isPending} />;
 * }
 * ```
 *
 * @see useCreateAssignment - For creating new assignments
 * @see useDeleteAssignment - For removing assignments
 */
export function useUpdateAssignment() {
  const queryClient = useQueryClient();

  return useMutation<
    Assignment,
    ApiError,
    { id: string; data: AssignmentUpdate }
  >({
    mutationFn: ({ id, data }) => put<Assignment>(`/assignments/${id}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assignments"] });
      queryClient.invalidateQueries({ queryKey: ["schedule"] });
      queryClient.invalidateQueries({ queryKey: ["validation"] });
    },
  });
}

/**
 * Deletes an assignment from the schedule.
 *
 * This mutation hook removes an assignment, creating a gap in the schedule
 * that may need to be filled. Automatically triggers validation to identify
 * any coverage issues created by the deletion.
 *
 * @returns Mutation object containing:
 *   - `mutate`: Function to delete an assignment by ID
 *   - `mutateAsync`: Async version returning a Promise
 *   - `isPending`: Whether deletion is in progress
 *   - `isSuccess`: Whether deletion completed successfully
 *   - `isError`: Whether an error occurred
 *   - `error`: Any error that occurred
 *
 * @example
 * ```tsx
 * function AssignmentActions({ assignment }: Props) {
 *   const { mutate, isPending } = useDeleteAssignment();
 *
 *   const handleDelete = () => {
 *     if (confirm('Remove this assignment?')) {
 *       mutate(assignment.id, {
 *         onSuccess: () => {
 *           toast.success('Assignment removed');
 *         },
 *         onError: (error) => {
 *           toast.error(`Failed to delete: ${error.message}`);
 *         },
 *       });
 *     }
 *   };
 *
 *   return (
 *     <IconButton
 *       icon={TrashIcon}
 *       onClick={handleDelete}
 *       loading={isPending}
 *       variant="danger"
 *     />
 *   );
 * }
 * ```
 *
 * @see useCreateAssignment - For filling the gap after deletion
 * @see useValidateSchedule - Validation is auto-triggered after deletion
 */
export function useDeleteAssignment() {
  const queryClient = useQueryClient();

  return useMutation<void, ApiError, string>({
    mutationFn: (id) => del(`/assignments/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assignments"] });
      queryClient.invalidateQueries({ queryKey: ["schedule"] });
      queryClient.invalidateQueries({ queryKey: ["validation"] });
    },
  });
}
