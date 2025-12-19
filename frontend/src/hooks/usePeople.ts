/**
 * People Management Hooks
 *
 * Hooks for managing people (residents, faculty, staff) with
 * React Query caching and optimistic updates.
 */
import { useQuery, useMutation, useQueryClient, UseQueryOptions } from '@tanstack/react-query'
import { get, post, put, del, ApiError } from '@/lib/api'
import type {
  Person,
  PersonCreate,
  PersonUpdate,
} from '@/types/api'

// ============================================================================
// Types
// ============================================================================

/**
 * Person role types in the residency system
 */
export type PersonType = 'resident' | 'faculty'

/**
 * Person status types
 */
export type PersonStatus = 'active' | 'inactive' | 'on_leave'

/**
 * Certification status types
 */
export type CertificationStatus = 'current' | 'expiring_soon' | 'expired' | 'pending'

/**
 * Certification type for BLS, ACLS, PALS, etc.
 */
export interface CertificationType {
  id: string
  name: string
  full_name?: string
}

/**
 * Person certification record
 */
export interface PersonCertification {
  id: string
  person_id: string
  certification_type_id: string
  certification_number?: string
  issued_date: string
  expiration_date: string
  status: CertificationStatus
  verified_by?: string
  verified_date?: string
  document_url?: string
  days_until_expiration: number
  is_expired: boolean
  is_expiring_soon: boolean
  created_at: string
  updated_at: string
  certification_type?: CertificationType
}

/**
 * Generic list response with pagination
 */
export interface ListResponse<T> {
  items: T[]
  total: number
}

/**
 * Filters for querying people
 */
export interface PeopleFilters {
  role?: string
  pgy_level?: number
}

// ============================================================================
// Query Keys
// ============================================================================

export const peopleQueryKeys = {
  people: (filters?: PeopleFilters) => ['people', filters] as const,
  person: (id: string) => ['people', id] as const,
  residents: (pgyLevel?: number) => ['residents', pgyLevel] as const,
  faculty: (specialty?: string) => ['faculty', specialty] as const,
  certifications: (personId: string) => ['certifications', 'person', personId] as const,
}

// ============================================================================
// People Hooks
// ============================================================================

/**
 * Fetches a list of people with optional filtering by role and PGY level.
 *
 * This hook retrieves people records including residents, faculty, and staff.
 * Supports filtering by role (resident, faculty, staff) and PGY level for
 * residents. Used for building person selectors, directories, and reports.
 *
 * @param filters - Optional filters for role and PGY level
 * @param options - Optional React Query configuration options
 * @returns Query result containing:
 *   - `data`: List of people matching the filters
 *   - `isLoading`: Whether the fetch is in progress
 *   - `error`: Any error that occurred
 *   - `refetch`: Function to manually refetch people
 *
 * @example
 * ```tsx
 * function PeopleDirectory() {
 *   const { data, isLoading } = usePeople({ role: 'resident' });
 *
 *   if (isLoading) return <Spinner />;
 *
 *   return (
 *     <PeopleGrid
 *       people={data.items}
 *       total={data.total}
 *     />
 *   );
 * }
 * ```
 *
 * @example
 * ```tsx
 * // Filter by PGY level
 * function PGY3Residents() {
 *   const { data } = usePeople({ role: 'resident', pgy_level: 3 });
 *   return <ResidentList residents={data.items} />;
 * }
 * ```
 *
 * @see usePerson - For fetching a single person
 * @see useResidents - Specialized hook for residents only
 * @see useFaculty - Specialized hook for faculty only
 */
export function usePeople(
  filters?: PeopleFilters,
  options?: Omit<UseQueryOptions<ListResponse<Person>, ApiError>, 'queryKey' | 'queryFn'>
) {
  const params = new URLSearchParams()
  if (filters?.role) params.set('role', filters.role)
  if (filters?.pgy_level !== undefined) params.set('pgy_level', String(filters.pgy_level))
  const queryString = params.toString()

  return useQuery<ListResponse<Person>, ApiError>({
    queryKey: ['people', filters],
    queryFn: () => get<ListResponse<Person>>(`/people${queryString ? `?${queryString}` : ''}`),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    ...options,
  })
}

/**
 * Fetches detailed information for a specific person.
 *
 * This hook retrieves complete details for a single person including
 * name, role, contact information, PGY level (if resident), specialty,
 * and preferences. Used for profile pages, editing, and detailed views.
 *
 * @param id - The UUID of the person to fetch
 * @param options - Optional React Query configuration options
 * @returns Query result containing:
 *   - `data`: The person record with all details
 *   - `isLoading`: Whether the fetch is in progress
 *   - `error`: Any error that occurred
 *   - `refetch`: Function to manually refetch the person
 *
 * @example
 * ```tsx
 * function PersonProfile({ personId }: Props) {
 *   const { data, isLoading, error } = usePerson(personId);
 *
 *   if (isLoading) return <ProfileSkeleton />;
 *   if (error) return <ErrorMessage error={error} />;
 *
 *   return (
 *     <ProfileCard
 *       person={data}
 *       onEdit={() => navigate(`/people/${personId}/edit`)}
 *     />
 *   );
 * }
 * ```
 *
 * @see usePeople - For fetching multiple people
 * @see useUpdatePerson - For modifying person details
 */
export function usePerson(
  id: string,
  options?: Omit<UseQueryOptions<Person, ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<Person, ApiError>({
    queryKey: peopleQueryKeys.person(id),
    queryFn: () => get<Person>(`/people/${id}`),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    enabled: !!id,
    ...options,
  })
}

/**
 * Fetches residents with optional filtering by PGY level.
 *
 * This specialized hook retrieves only residents, with optional filtering
 * by post-graduate year (PGY) level. Useful for building resident-specific
 * selectors, cohort views, and PGY-based reports.
 *
 * @param pgyLevel - Optional PGY level to filter residents (1-7)
 * @param options - Optional React Query configuration options
 * @returns Query result containing:
 *   - `data`: List of residents matching the PGY level
 *   - `isLoading`: Whether the fetch is in progress
 *   - `error`: Any error that occurred
 *   - `refetch`: Function to manually refetch residents
 *
 * @example
 * ```tsx
 * function ResidentSelector({ onSelect }: Props) {
 *   const { data, isLoading } = useResidents();
 *
 *   if (isLoading) return <SelectSkeleton />;
 *
 *   return (
 *     <Select label="Select Resident" onChange={onSelect}>
 *       {data.items.map(resident => (
 *         <option key={resident.id} value={resident.id}>
 *           {resident.name} (PGY-{resident.pgy_level})
 *         </option>
 *       ))}
 *     </Select>
 *   );
 * }
 * ```
 *
 * @example
 * ```tsx
 * // Fetch only PGY-1 residents
 * function InternList() {
 *   const { data } = useResidents(1);
 *   return <ResidentGrid residents={data.items} title="Interns" />;
 * }
 * ```
 *
 * @see usePeople - For fetching all people including non-residents
 * @see useFaculty - For fetching faculty members
 */
export function useResidents(
  pgyLevel?: number,
  options?: Omit<UseQueryOptions<ListResponse<Person>, ApiError>, 'queryKey' | 'queryFn'>
) {
  const params = pgyLevel !== undefined ? `?pgy_level=${pgyLevel}` : ''

  return useQuery<ListResponse<Person>, ApiError>({
    queryKey: peopleQueryKeys.residents(pgyLevel),
    queryFn: () => get<ListResponse<Person>>(`/people/residents${params}`),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    ...options,
  })
}

/**
 * Fetches faculty members with optional filtering by specialty.
 *
 * This specialized hook retrieves only faculty members, with optional
 * filtering by medical specialty. Used for building faculty-specific
 * selectors, attending assignment forms, and specialty-based views.
 *
 * @param specialty - Optional specialty to filter faculty (e.g., "Cardiology")
 * @param options - Optional React Query configuration options
 * @returns Query result containing:
 *   - `data`: List of faculty matching the specialty
 *   - `isLoading`: Whether the fetch is in progress
 *   - `error`: Any error that occurred
 *   - `refetch`: Function to manually refetch faculty
 *
 * @example
 * ```tsx
 * function AttendingSelector({ onSelect }: Props) {
 *   const { data, isLoading } = useFaculty();
 *
 *   if (isLoading) return <SelectSkeleton />;
 *
 *   return (
 *     <Select label="Select Attending" onChange={onSelect}>
 *       {data.items.map(faculty => (
 *         <option key={faculty.id} value={faculty.id}>
 *           {faculty.name} - {faculty.specialty}
 *         </option>
 *       ))}
 *     </Select>
 *   );
 * }
 * ```
 *
 * @example
 * ```tsx
 * // Fetch only cardiology faculty
 * function CardiologyFaculty() {
 *   const { data } = useFaculty('Cardiology');
 *   return <FacultyList faculty={data.items} specialty="Cardiology" />;
 * }
 * ```
 *
 * @see usePeople - For fetching all people including non-faculty
 * @see useResidents - For fetching residents
 */
export function useFaculty(
  specialty?: string,
  options?: Omit<UseQueryOptions<ListResponse<Person>, ApiError>, 'queryKey' | 'queryFn'>
) {
  const params = specialty ? `?specialty=${encodeURIComponent(specialty)}` : ''

  return useQuery<ListResponse<Person>, ApiError>({
    queryKey: peopleQueryKeys.faculty(specialty),
    queryFn: () => get<ListResponse<Person>>(`/people/faculty${params}`),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    ...options,
  })
}

/**
 * Creates a new person record in the system.
 *
 * This mutation hook adds a new resident, faculty member, or staff person
 * to the system. Required fields typically include name, role, and contact
 * information. For residents, PGY level is required. Automatically refreshes
 * all people-related queries.
 *
 * @returns Mutation object containing:
 *   - `mutate`: Function to create a person
 *   - `mutateAsync`: Async version returning a Promise
 *   - `isPending`: Whether creation is in progress
 *   - `isSuccess`: Whether creation completed successfully
 *   - `isError`: Whether an error occurred
 *   - `error`: Any error that occurred (e.g., duplicate email)
 *   - `data`: The created person with generated ID
 *
 * @example
 * ```tsx
 * function NewPersonForm() {
 *   const { mutate, isPending } = useCreatePerson();
 *
 *   const handleSubmit = (formData: PersonCreate) => {
 *     mutate(formData, {
 *       onSuccess: (newPerson) => {
 *         toast.success(`Added ${newPerson.name}`);
 *         navigate(`/people/${newPerson.id}`);
 *       },
 *       onError: (error) => {
 *         if (error.status === 409) {
 *           toast.error('Email already exists');
 *         } else {
 *           toast.error(`Failed to add person: ${error.message}`);
 *         }
 *       },
 *     });
 *   };
 *
 *   return <PersonForm onSubmit={handleSubmit} loading={isPending} />;
 * }
 * ```
 *
 * @see useUpdatePerson - For modifying existing people
 * @see usePeople - List is auto-refreshed after creation
 */
export function useCreatePerson() {
  const queryClient = useQueryClient()

  return useMutation<Person, ApiError, PersonCreate>({
    mutationFn: (data) => post<Person>('/people', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['people'] })
      queryClient.invalidateQueries({ queryKey: ['residents'] })
      queryClient.invalidateQueries({ queryKey: ['faculty'] })
    },
  })
}

/**
 * Updates an existing person record with new details.
 *
 * This mutation hook modifies person information such as contact details,
 * role changes, PGY level advancement, or preferences. Automatically
 * refreshes all related queries to maintain UI consistency.
 *
 * @returns Mutation object containing:
 *   - `mutate`: Function to update a person
 *   - `mutateAsync`: Async version returning a Promise
 *   - `isPending`: Whether update is in progress
 *   - `isSuccess`: Whether update completed successfully
 *   - `isError`: Whether an error occurred
 *   - `error`: Any error that occurred
 *   - `data`: The updated person
 *
 * @example
 * ```tsx
 * function EditPersonForm({ personId }: Props) {
 *   const { mutate, isPending } = useUpdatePerson();
 *   const { data: person } = usePerson(personId);
 *
 *   const handleUpdate = (updates: PersonUpdate) => {
 *     mutate(
 *       { id: personId, data: updates },
 *       {
 *         onSuccess: () => {
 *           toast.success('Profile updated');
 *           navigate(`/people/${personId}`);
 *         },
 *         onError: (error) => {
 *           toast.error(`Update failed: ${error.message}`);
 *         },
 *       }
 *     );
 *   };
 *
 *   return <PersonForm initialData={person} onSubmit={handleUpdate} />;
 * }
 * ```
 *
 * @example
 * ```tsx
 * // Advance resident to next PGY level
 * function AdvancePGYButton({ resident }: Props) {
 *   const { mutate } = useUpdatePerson();
 *
 *   const handleAdvance = () => {
 *     mutate({
 *       id: resident.id,
 *       data: { pgy_level: resident.pgy_level + 1 },
 *     });
 *   };
 *
 *   return <Button onClick={handleAdvance}>Advance to PGY-{resident.pgy_level + 1}</Button>;
 * }
 * ```
 *
 * @see usePerson - Query is auto-refreshed after update
 * @see useCreatePerson - For creating new people
 */
export function useUpdatePerson() {
  const queryClient = useQueryClient()

  return useMutation<Person, ApiError, { id: string; data: PersonUpdate }>({
    mutationFn: ({ id, data }) => put<Person>(`/people/${id}`, data),
    onSuccess: (data, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['people'] })
      queryClient.invalidateQueries({ queryKey: peopleQueryKeys.person(id) })
      queryClient.invalidateQueries({ queryKey: ['residents'] })
      queryClient.invalidateQueries({ queryKey: ['faculty'] })
    },
  })
}

/**
 * Deletes a person record from the system.
 *
 * This mutation hook permanently removes a person. Use with caution as
 * this may be irreversible depending on backend constraints. People with
 * existing assignments or absences may not be deletable to maintain
 * data integrity.
 *
 * @returns Mutation object containing:
 *   - `mutate`: Function to delete a person by ID
 *   - `mutateAsync`: Async version returning a Promise
 *   - `isPending`: Whether deletion is in progress
 *   - `isSuccess`: Whether deletion completed successfully
 *   - `isError`: Whether an error occurred
 *   - `error`: Any error that occurred (e.g., person has assignments)
 *
 * @example
 * ```tsx
 * function PersonActions({ person }: Props) {
 *   const { mutate, isPending } = useDeletePerson();
 *
 *   const handleDelete = () => {
 *     if (confirm(`Delete ${person.name}? This cannot be undone.`)) {
 *       mutate(person.id, {
 *         onSuccess: () => {
 *           toast.success('Person removed');
 *           navigate('/people');
 *         },
 *         onError: (error) => {
 *           if (error.status === 409) {
 *             toast.error('Cannot delete: person has existing assignments');
 *           } else {
 *             toast.error(`Failed to delete: ${error.message}`);
 *           }
 *         },
 *       });
 *     }
 *   };
 *
 *   return (
 *     <Button
 *       onClick={handleDelete}
 *       loading={isPending}
 *       variant="danger"
 *     >
 *       Delete Person
 *     </Button>
 *   );
 * }
 * ```
 *
 * @see usePeople - List is auto-refreshed after deletion
 * @see useCreatePerson - For adding new people
 */
export function useDeletePerson() {
  const queryClient = useQueryClient()

  return useMutation<void, ApiError, string>({
    mutationFn: (id) => del(`/people/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['people'] })
      queryClient.invalidateQueries({ queryKey: ['residents'] })
      queryClient.invalidateQueries({ queryKey: ['faculty'] })
    },
  })
}

/**
 * Fetches certifications for a specific person (BLS, ACLS, PALS, etc.).
 *
 * This hook retrieves all certification records for a given person, including
 * certification type, issue/expiration dates, status, and expiration warnings.
 * Used for displaying certification status, compliance checking, and renewal
 * tracking for residents and faculty.
 *
 * @param personId - The UUID of the person whose certifications to fetch
 * @param options - Optional React Query configuration options
 * @returns Query result containing:
 *   - `data`: List of certifications with type details and expiration info
 *   - `isLoading`: Whether the fetch is in progress
 *   - `error`: Any error that occurred
 *   - `refetch`: Function to manually refetch certifications
 *
 * @example
 * ```tsx
 * function PersonCertifications({ personId }: Props) {
 *   const { data, isLoading, error } = useCertifications(personId);
 *
 *   if (isLoading) return <CertificationsSkeleton />;
 *   if (error) return <ErrorMessage error={error} />;
 *
 *   const expiringSoon = data.items.filter(cert => cert.is_expiring_soon);
 *   const expired = data.items.filter(cert => cert.is_expired);
 *
 *   return (
 *     <div>
 *       <h2>Certifications</h2>
 *       {expiringSoon.length > 0 && (
 *         <Alert variant="warning">
 *           {expiringSoon.length} certification(s) expiring soon
 *         </Alert>
 *       )}
 *       {expired.length > 0 && (
 *         <Alert variant="danger">
 *           {expired.length} certification(s) expired
 *         </Alert>
 *       )}
 *       <CertificationsList certifications={data.items} />
 *     </div>
 *   );
 * }
 * ```
 *
 * @example
 * ```tsx
 * // Display certification badges
 * function CertificationBadges({ personId }: Props) {
 *   const { data } = useCertifications(personId);
 *
 *   return (
 *     <div className="flex gap-2">
 *       {data?.items.map(cert => (
 *         <Badge
 *           key={cert.id}
 *           variant={cert.is_expired ? 'danger' : cert.is_expiring_soon ? 'warning' : 'success'}
 *         >
 *           {cert.certification_type?.name}
 *           {cert.is_expiring_soon && ` (${cert.days_until_expiration}d)`}
 *         </Badge>
 *       ))}
 *     </div>
 *   );
 * }
 * ```
 *
 * @see usePerson - For fetching person details
 * @see useUpdatePerson - Certifications are part of person compliance
 */
export function useCertifications(
  personId: string,
  options?: Omit<UseQueryOptions<ListResponse<PersonCertification>, ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<ListResponse<PersonCertification>, ApiError>({
    queryKey: peopleQueryKeys.certifications(personId),
    queryFn: () => get<ListResponse<PersonCertification>>(`/certifications/by-person/${personId}`),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    enabled: !!personId,
    ...options,
  })
}
