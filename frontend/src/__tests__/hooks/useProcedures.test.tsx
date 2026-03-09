/**
 * useProcedures Hook Tests
 *
 * Tests for procedure and credential management hooks including CRUD operations,
 * queries, mutations, and error handling.
 */
import { renderHook, waitFor } from '@/test-utils'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactNode } from 'react'
import * as api from '@/lib/api'
import {
  useProcedures,
  useProcedure,
  useCreateProcedure,
  useUpdateProcedure,
  useDeleteProcedure,
  useFacultyCredentials,
  useUpdateCredential,
  useQualifiedFaculty,
  useCreateCredential,
  useDeleteCredential,
  type Procedure,
  type ProcedureCreate,
  type ProcedureUpdate,
  type ListResponse,
  type Credential,
  type CredentialCreate,
  type CredentialUpdate,
  type QualifiedFacultyResponse,
  type PersonSummary,
} from '@/hooks/useProcedures'

// Mock the api module
jest.mock('@/lib/api')

const mockedApi = api as jest.Mocked<typeof api>

// Mock data
const mockProcedures: Procedure[] = [
  {
    id: 'proc-1',
    name: 'Arthroscopy',
    description: 'Minimally invasive joint surgery',
    category: 'Surgical',
    specialty: 'Sports Medicine',
    supervisionRatio: 2,
    requiresCertification: true,
    complexityLevel: 'advanced',
    minPgyLevel: 3,
    isActive: true,
    createdAt: '2026-01-15T10:00:00Z',
    updatedAt: '2026-01-15T10:00:00Z',
  },
  {
    id: 'proc-2',
    name: 'Joint Injection',
    description: 'Intra-articular injection',
    category: 'Non-Surgical',
    specialty: 'Sports Medicine',
    supervisionRatio: 1,
    requiresCertification: false,
    complexityLevel: 'basic',
    minPgyLevel: 1,
    isActive: true,
    createdAt: '2026-01-10T08:00:00Z',
    updatedAt: '2026-01-10T08:00:00Z',
  },
]

const mockCredentials: Credential[] = [
  {
    id: 'cred-1',
    personId: 'person-1',
    procedureId: 'proc-1',
    status: 'active',
    competencyLevel: 'expert',
    issuedDate: '2025-01-01',
    expirationDate: '2027-01-01',
    lastVerifiedDate: '2026-01-01',
    maxConcurrentResidents: 2,
    maxPerWeek: 5,
    maxPerAcademicYear: 100,
    notes: 'Highly experienced',
    isValid: true,
    createdAt: '2025-01-01T00:00:00Z',
    updatedAt: '2026-01-01T00:00:00Z',
  },
]

const mockQualifiedFaculty: PersonSummary[] = [
  { id: 'person-1', name: 'Dr. Smith', type: 'faculty' },
  { id: 'person-2', name: 'Dr. Jones', type: 'faculty' },
]

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
  })
}

// Wrapper component with QueryClientProvider
function createWrapper() {
  const queryClient = createTestQueryClient()
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    )
  }
}

describe('useProcedures', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch all procedures when no filters provided', async () => {
    const mockResponse: ListResponse<Procedure> = {
      items: mockProcedures,
      total: mockProcedures.length,
    }
    mockedApi.get.mockResolvedValueOnce(mockResponse)

    const { result } = renderHook(
      () => useProcedures(),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.items).toHaveLength(2)
    expect(result.current.data?.total).toBe(2)
    expect(mockedApi.get).toHaveBeenCalledWith('/procedures')
  })

  it('should fetch procedures with specialty filter', async () => {
    const filteredProcedures = mockProcedures.filter(p => p.specialty === 'Sports Medicine')
    const mockResponse: ListResponse<Procedure> = {
      items: filteredProcedures,
      total: filteredProcedures.length,
    }
    mockedApi.get.mockResolvedValueOnce(mockResponse)

    const { result } = renderHook(
      () => useProcedures({ specialty: 'Sports Medicine' }),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.items).toHaveLength(2)
    expect(mockedApi.get).toHaveBeenCalledWith('/procedures?specialty=Sports+Medicine')
  })

  it('should fetch procedures with multiple filters', async () => {
    const mockResponse: ListResponse<Procedure> = {
      items: [mockProcedures[0]],
      total: 1,
    }
    mockedApi.get.mockResolvedValueOnce(mockResponse)

    const { result } = renderHook(
      () => useProcedures({
        specialty: 'Sports Medicine',
        category: 'Surgical',
        isActive: true,
        complexityLevel: 'advanced',
      }),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.items).toHaveLength(1)
    expect(mockedApi.get).toHaveBeenCalledWith(
      '/procedures?specialty=Sports+Medicine&category=Surgical&is_active=true&complexity_level=advanced'
    )
  })

  it('should handle errors when fetching procedures', async () => {
    const apiError = Object.assign(
      new Error('Failed to fetch procedures'),
      { status: 500 }
    )
    mockedApi.get.mockRejectedValueOnce(apiError)

    const { result } = renderHook(
      () => useProcedures(),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(apiError)
  })
})

describe('useProcedure', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch a single procedure by ID', async () => {
    const mockProcedure = mockProcedures[0]
    mockedApi.get.mockResolvedValueOnce(mockProcedure)

    const { result } = renderHook(
      () => useProcedure('proc-1'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockProcedure)
    expect(mockedApi.get).toHaveBeenCalledWith('/procedures/proc-1')
  })

  it('should not fetch when ID is empty', async () => {
    const { result } = renderHook(
      () => useProcedure(''),
      { wrapper: createWrapper() }
    )

    expect(result.current.isFetching).toBe(false)
    expect(mockedApi.get).not.toHaveBeenCalled()
  })

  it('should handle errors when fetching a single procedure', async () => {
    const apiError = Object.assign(
      new Error('Procedure not found'),
      { status: 404 }
    )
    mockedApi.get.mockRejectedValueOnce(apiError)

    const { result } = renderHook(
      () => useProcedure('nonexistent-id'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(apiError)
  })
})

describe('useCreateProcedure', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should create a new procedure successfully', async () => {
    const newProcedure: ProcedureCreate = {
      name: 'ACL Reconstruction',
      description: 'Anterior cruciate ligament reconstruction',
      category: 'Surgical',
      specialty: 'Sports Medicine',
      supervisionRatio: 2,
      requiresCertification: true,
      complexityLevel: 'complex',
      minPgyLevel: 4,
      isActive: true,
    }

    const mockResponse: Procedure = {
      id: 'proc-3',
      name: newProcedure.name,
      description: newProcedure.description ?? null,
      category: newProcedure.category ?? null,
      specialty: newProcedure.specialty ?? null,
      supervisionRatio: newProcedure.supervisionRatio ?? 1,
      requiresCertification: newProcedure.requiresCertification ?? false,
      complexityLevel: newProcedure.complexityLevel ?? 'basic',
      minPgyLevel: newProcedure.minPgyLevel ?? 1,
      isActive: newProcedure.isActive ?? true,
      createdAt: '2026-02-06T10:00:00Z',
      updatedAt: '2026-02-06T10:00:00Z',
    }
    mockedApi.post.mockResolvedValueOnce(mockResponse)

    const { result } = renderHook(
      () => useCreateProcedure(),
      { wrapper: createWrapper() }
    )

    result.current.mutate(newProcedure)

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockResponse)
    expect(mockedApi.post).toHaveBeenCalledWith('/procedures', newProcedure)
  })

  it('should handle creation errors', async () => {
    const apiError = Object.assign(
      new Error('Procedure name already exists'),
      { status: 409 }
    )
    mockedApi.post.mockRejectedValueOnce(apiError)

    const { result } = renderHook(
      () => useCreateProcedure(),
      { wrapper: createWrapper() }
    )

    result.current.mutate({
      name: 'Duplicate Procedure',
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(apiError)
  })

  it('should invalidate procedure queries on success', async () => {
    const queryClient = createTestQueryClient()
    const invalidateSpy = jest.spyOn(queryClient, 'invalidateQueries')

    const mockResponse: Procedure = {
      id: 'proc-3',
      name: 'Test Procedure',
      description: null,
      category: null,
      specialty: null,
      supervisionRatio: 1,
      requiresCertification: false,
      complexityLevel: 'basic',
      minPgyLevel: 1,
      isActive: true,
      createdAt: '2026-02-06T10:00:00Z',
      updatedAt: '2026-02-06T10:00:00Z',
    }
    mockedApi.post.mockResolvedValueOnce(mockResponse)

    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    )

    const { result } = renderHook(() => useCreateProcedure(), { wrapper })

    result.current.mutate({ name: 'Test Procedure' })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ['procedures'],
    })
  })
})

describe('useUpdateProcedure', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should update a procedure successfully', async () => {
    const updates: ProcedureUpdate = {
      description: 'Updated description',
      complexityLevel: 'complex',
    }

    const mockResponse: Procedure = {
      ...mockProcedures[0],
      description: updates.description ?? mockProcedures[0].description,
      complexityLevel: updates.complexityLevel ?? mockProcedures[0].complexityLevel,
      updatedAt: '2026-02-06T10:00:00Z',
    }
    mockedApi.put.mockResolvedValueOnce(mockResponse)

    const { result } = renderHook(
      () => useUpdateProcedure(),
      { wrapper: createWrapper() }
    )

    result.current.mutate({ id: 'proc-1', data: updates })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockResponse)
    expect(mockedApi.put).toHaveBeenCalledWith('/procedures/proc-1', updates)
  })

  it('should handle update errors', async () => {
    const apiError = Object.assign(
      new Error('Validation failed'),
      { status: 422 }
    )
    mockedApi.put.mockRejectedValueOnce(apiError)

    const { result } = renderHook(
      () => useUpdateProcedure(),
      { wrapper: createWrapper() }
    )

    result.current.mutate({
      id: 'proc-1',
      data: { supervisionRatio: -1 },
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(apiError)
  })

  it('should invalidate related queries on success', async () => {
    const queryClient = createTestQueryClient()
    const invalidateSpy = jest.spyOn(queryClient, 'invalidateQueries')

    const mockResponse: Procedure = mockProcedures[0]
    mockedApi.put.mockResolvedValueOnce(mockResponse)

    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    )

    const { result } = renderHook(() => useUpdateProcedure(), { wrapper })

    result.current.mutate({
      id: 'proc-1',
      data: { description: 'Updated' },
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ['procedures'],
    })
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ['procedures', 'detail', 'proc-1'],
    })
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ['credentials'],
    })
  })
})

describe('useDeleteProcedure', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should delete a procedure successfully', async () => {
    mockedApi.del.mockResolvedValueOnce(undefined)

    const { result } = renderHook(
      () => useDeleteProcedure(),
      { wrapper: createWrapper() }
    )

    result.current.mutate('proc-1')

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.del).toHaveBeenCalledWith('/procedures/proc-1')
  })

  it('should handle delete errors (conflict)', async () => {
    const apiError = Object.assign(
      new Error('Cannot delete: procedure has active credentials'),
      { status: 409 }
    )
    mockedApi.del.mockRejectedValueOnce(apiError)

    const { result } = renderHook(
      () => useDeleteProcedure(),
      { wrapper: createWrapper() }
    )

    result.current.mutate('proc-1')

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(apiError)
  })

  it('should invalidate procedure and credential queries on success', async () => {
    const queryClient = createTestQueryClient()
    const invalidateSpy = jest.spyOn(queryClient, 'invalidateQueries')

    mockedApi.del.mockResolvedValueOnce(undefined)

    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    )

    const { result } = renderHook(() => useDeleteProcedure(), { wrapper })

    result.current.mutate('proc-1')

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ['procedures'],
    })
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ['credentials'],
    })
  })
})

describe('useFacultyCredentials', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch credentials for a faculty member', async () => {
    const mockResponse: ListResponse<Credential> = {
      items: mockCredentials,
      total: 1,
    }
    mockedApi.get.mockResolvedValueOnce(mockResponse)

    const { result } = renderHook(
      () => useFacultyCredentials('person-1'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.items).toHaveLength(1)
    expect(result.current.data?.total).toBe(1)
    expect(mockedApi.get).toHaveBeenCalledWith('/credentials/by-person/person-1')
  })

  it('should fetch credentials with status filter', async () => {
    const mockResponse: ListResponse<Credential> = {
      items: mockCredentials,
      total: 1,
    }
    mockedApi.get.mockResolvedValueOnce(mockResponse)

    const { result } = renderHook(
      () => useFacultyCredentials('person-1', { status: 'active' }),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.get).toHaveBeenCalledWith(
      '/credentials/by-person/person-1?status=active'
    )
  })

  it('should not fetch when facultyId is not provided', async () => {
    const { result } = renderHook(
      () => useFacultyCredentials(undefined),
      { wrapper: createWrapper() }
    )

    expect(result.current.isFetching).toBe(false)
    expect(mockedApi.get).not.toHaveBeenCalled()
  })

  it('should handle errors when fetching credentials', async () => {
    const apiError = Object.assign(
      new Error('Failed to fetch credentials'),
      { status: 500 }
    )
    mockedApi.get.mockRejectedValueOnce(apiError)

    const { result } = renderHook(
      () => useFacultyCredentials('person-1'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(apiError)
  })
})

describe('useQualifiedFaculty', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch qualified faculty for a procedure', async () => {
    const mockResponse: QualifiedFacultyResponse = {
      procedureId: 'proc-1',
      procedureName: 'Arthroscopy',
      qualifiedFaculty: mockQualifiedFaculty,
      total: 2,
    }
    mockedApi.get.mockResolvedValueOnce(mockResponse)

    const { result } = renderHook(
      () => useQualifiedFaculty('proc-1'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.qualifiedFaculty).toHaveLength(2)
    expect(result.current.data?.total).toBe(2)
    expect(mockedApi.get).toHaveBeenCalledWith('/credentials/qualified-faculty/proc-1')
  })

  it('should not fetch when procedureId is empty', async () => {
    const { result } = renderHook(
      () => useQualifiedFaculty(''),
      { wrapper: createWrapper() }
    )

    expect(result.current.isFetching).toBe(false)
    expect(mockedApi.get).not.toHaveBeenCalled()
  })

  it('should handle errors when fetching qualified faculty', async () => {
    const apiError = Object.assign(
      new Error('Procedure not found'),
      { status: 404 }
    )
    mockedApi.get.mockRejectedValueOnce(apiError)

    const { result } = renderHook(
      () => useQualifiedFaculty('nonexistent-proc'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(apiError)
  })
})

describe('useCreateCredential', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should create a new credential successfully', async () => {
    const newCredential: CredentialCreate = {
      personId: 'person-2',
      procedureId: 'proc-1',
      status: 'active',
      competencyLevel: 'qualified',
      issuedDate: '2026-02-01',
      expirationDate: '2028-02-01',
    }

    const mockResponse: Credential = {
      id: 'cred-2',
      personId: newCredential.personId,
      procedureId: newCredential.procedureId,
      status: newCredential.status ?? 'active',
      competencyLevel: newCredential.competencyLevel ?? 'qualified',
      issuedDate: newCredential.issuedDate ?? null,
      expirationDate: newCredential.expirationDate ?? null,
      lastVerifiedDate: null,
      maxConcurrentResidents: null,
      maxPerWeek: null,
      maxPerAcademicYear: null,
      notes: null,
      isValid: true,
      createdAt: '2026-02-06T10:00:00Z',
      updatedAt: '2026-02-06T10:00:00Z',
    }
    mockedApi.post.mockResolvedValueOnce(mockResponse)

    const { result } = renderHook(
      () => useCreateCredential(),
      { wrapper: createWrapper() }
    )

    result.current.mutate(newCredential)

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockResponse)
    expect(mockedApi.post).toHaveBeenCalledWith('/credentials', newCredential)
  })

  it('should invalidate related credential queries on success', async () => {
    const queryClient = createTestQueryClient()
    const invalidateSpy = jest.spyOn(queryClient, 'invalidateQueries')

    const mockResponse: Credential = mockCredentials[0]
    mockedApi.post.mockResolvedValueOnce(mockResponse)

    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    )

    const { result } = renderHook(() => useCreateCredential(), { wrapper })

    result.current.mutate({
      personId: 'person-1',
      procedureId: 'proc-1',
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ['credentials'],
    })
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ['credentials', 'by-person', 'person-1', undefined],
    })
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ['credentials', 'by-procedure', 'proc-1', undefined],
    })
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ['credentials', 'qualified', 'proc-1'],
    })
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ['credentials', 'summary', 'person-1'],
    })
  })
})

describe('useUpdateCredential', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should update a credential status successfully', async () => {
    const updates: CredentialUpdate = {
      status: 'expired',
      notes: 'Credential has expired',
    }

    const mockResponse: Credential = {
      ...mockCredentials[0],
      status: updates.status ?? mockCredentials[0].status,
      notes: updates.notes ?? mockCredentials[0].notes,
      updatedAt: '2026-02-06T10:00:00Z',
    }
    mockedApi.put.mockResolvedValueOnce(mockResponse)

    const { result } = renderHook(
      () => useUpdateCredential(),
      { wrapper: createWrapper() }
    )

    result.current.mutate({ id: 'cred-1', data: updates })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockResponse)
    expect(mockedApi.put).toHaveBeenCalledWith('/credentials/cred-1', updates)
  })

  it('should handle credential update errors', async () => {
    const apiError = Object.assign(
      new Error('Credential not found'),
      { status: 404 }
    )
    mockedApi.put.mockRejectedValueOnce(apiError)

    const { result } = renderHook(
      () => useUpdateCredential(),
      { wrapper: createWrapper() }
    )

    result.current.mutate({
      id: 'nonexistent-cred',
      data: { status: 'active' },
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(apiError)
  })

  it('should invalidate related queries on success', async () => {
    const queryClient = createTestQueryClient()
    const invalidateSpy = jest.spyOn(queryClient, 'invalidateQueries')

    const mockResponse: Credential = mockCredentials[0]
    mockedApi.put.mockResolvedValueOnce(mockResponse)

    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    )

    const { result } = renderHook(() => useUpdateCredential(), { wrapper })

    result.current.mutate({
      id: 'cred-1',
      data: { status: 'suspended' },
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ['credentials'],
    })
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ['credentials', 'detail', 'cred-1'],
    })
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ['credentials', 'by-person', mockResponse.personId, undefined],
    })
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ['credentials', 'by-procedure', mockResponse.procedureId, undefined],
    })
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ['credentials', 'qualified', mockResponse.procedureId],
    })
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ['credentials', 'summary', mockResponse.personId],
    })
  })
})

describe('useDeleteCredential', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should delete a credential successfully', async () => {
    mockedApi.del.mockResolvedValueOnce(undefined)

    const { result } = renderHook(
      () => useDeleteCredential(),
      { wrapper: createWrapper() }
    )

    result.current.mutate('cred-1')

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.del).toHaveBeenCalledWith('/credentials/cred-1')
  })

  it('should handle delete errors', async () => {
    const apiError = Object.assign(
      new Error('Permission denied'),
      { status: 403 }
    )
    mockedApi.del.mockRejectedValueOnce(apiError)

    const { result } = renderHook(
      () => useDeleteCredential(),
      { wrapper: createWrapper() }
    )

    result.current.mutate('cred-1')

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(apiError)
  })

  it('should invalidate credential queries on success', async () => {
    const queryClient = createTestQueryClient()
    const invalidateSpy = jest.spyOn(queryClient, 'invalidateQueries')

    mockedApi.del.mockResolvedValueOnce(undefined)

    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    )

    const { result } = renderHook(() => useDeleteCredential(), { wrapper })

    result.current.mutate('cred-1')

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ['credentials'],
    })
  })
})
