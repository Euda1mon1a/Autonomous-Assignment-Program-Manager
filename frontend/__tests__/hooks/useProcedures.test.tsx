import { renderHook, waitFor, act } from '@testing-library/react'
import { useProcedures, useProcedure, useCreateProcedure, useUpdateProcedure, useDeleteProcedure, useCredentials } from '@/hooks/useProcedures'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactNode } from 'react'
import * as api from '@/lib/api'

jest.mock('@/lib/api')

const mockedApi = api as jest.Mocked<typeof api>

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
})

const wrapper = ({ children }: { children: ReactNode }) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
)

describe('useProcedures', () => {
  beforeEach(() => {
    queryClient.clear()
    jest.clearAllMocks()
  })

  describe('Fetch Procedures', () => {
    it('should fetch all procedures', async () => {
      const mockProcedures = {
        items: [
          { id: '1', name: 'LP', category: 'neuro', specialty: 'neurology', supervisionRatio: 2, requiresCertification: false, complexityLevel: 'standard', minPgyLevel: 1, isActive: true, createdAt: '2024-01-01T00:00:00Z', updatedAt: '2024-01-01T00:00:00Z', description: null },
          { id: '2', name: 'Intubation', category: 'airway', specialty: 'emergency', supervisionRatio: 1, requiresCertification: true, complexityLevel: 'advanced', minPgyLevel: 2, isActive: true, createdAt: '2024-01-01T00:00:00Z', updatedAt: '2024-01-01T00:00:00Z', description: null },
        ],
        total: 2,
      }
      mockedApi.get.mockResolvedValueOnce(mockProcedures)

      const { result } = renderHook(() => useProcedures(), { wrapper })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))
      expect(result.current.data?.items).toHaveLength(2)
    })

    it('should filter by category', async () => {
      const mockProcedures = {
        items: [
          { id: '1', name: 'LP', category: 'neuro', specialty: 'neurology', supervisionRatio: 2, requiresCertification: false, complexityLevel: 'standard', minPgyLevel: 1, isActive: true, createdAt: '2024-01-01T00:00:00Z', updatedAt: '2024-01-01T00:00:00Z', description: null },
        ],
        total: 1,
      }
      mockedApi.get.mockResolvedValueOnce(mockProcedures)

      const { result } = renderHook(
        () => useProcedures({ category: 'neuro' }),
        { wrapper }
      )

      await waitFor(() => expect(result.current.isSuccess).toBe(true))
      expect(result.current.data?.items[0].category).toBe('neuro')
    })
  })

  describe('Single Procedure', () => {
    it('should fetch a single procedure by ID', async () => {
      const mockProcedure = {
        id: 'proc-1',
        name: 'Lumbar Puncture',
        description: 'CSF collection procedure',
        category: 'neuro',
        specialty: 'neurology',
        supervisionRatio: 2,
        requiresCertification: false,
        complexityLevel: 'standard',
        minPgyLevel: 1,
        isActive: true,
        createdAt: '2024-01-01T00:00:00Z',
        updatedAt: '2024-01-01T00:00:00Z',
      }
      mockedApi.get.mockResolvedValueOnce(mockProcedure)

      const { result } = renderHook(() => useProcedure('proc-1'), { wrapper })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))
      expect(result.current.data?.name).toBe('Lumbar Puncture')
    })
  })

  describe('Create Procedure', () => {
    it('should create a new procedure', async () => {
      const newProcedure = {
        id: 'proc-new',
        name: 'New Procedure',
        description: 'Test procedure',
        category: 'test',
        specialty: null,
        supervisionRatio: 1,
        requiresCertification: false,
        complexityLevel: 'basic',
        minPgyLevel: 1,
        isActive: true,
        createdAt: '2024-01-01T00:00:00Z',
        updatedAt: '2024-01-01T00:00:00Z',
      }
      mockedApi.post.mockResolvedValueOnce(newProcedure)

      const { result } = renderHook(() => useCreateProcedure(), { wrapper })

      await act(async () => {
        result.current.mutate({
          name: 'New Procedure',
          description: 'Test procedure',
        })
      })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))
      expect(result.current.data?.name).toBe('New Procedure')
    })
  })

  describe('Update Procedure', () => {
    it('should update an existing procedure', async () => {
      const updatedProcedure = {
        id: 'proc-1',
        name: 'Updated Procedure',
        description: 'Updated description',
        category: 'test',
        specialty: null,
        supervisionRatio: 1,
        requiresCertification: true,
        complexityLevel: 'advanced',
        minPgyLevel: 2,
        isActive: true,
        createdAt: '2024-01-01T00:00:00Z',
        updatedAt: '2024-01-02T00:00:00Z',
      }
      mockedApi.put.mockResolvedValueOnce(updatedProcedure)

      const { result } = renderHook(() => useUpdateProcedure(), { wrapper })

      await act(async () => {
        result.current.mutate({
          id: 'proc-1',
          data: { name: 'Updated Procedure' },
        })
      })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))
      expect(result.current.data?.name).toBe('Updated Procedure')
    })
  })

  describe('Delete Procedure', () => {
    it('should delete a procedure', async () => {
      mockedApi.del.mockResolvedValueOnce(undefined)

      const { result } = renderHook(() => useDeleteProcedure(), { wrapper })

      await act(async () => {
        result.current.mutate('proc-1')
      })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))
    })
  })

  describe('Credentials', () => {
    it('should fetch credentials for a person', async () => {
      const mockCredentials = {
        items: [
          {
            id: 'cred-1',
            personId: 'person-1',
            procedureId: 'proc-1',
            status: 'active',
            competencyLevel: 'qualified',
            issued_date: '2024-01-01',
            expirationDate: '2025-01-01',
            last_verified_date: '2024-06-01',
            max_concurrent_residents: 3,
            max_per_week: null,
            max_per_academicYear: null,
            notes: null,
            is_valid: true,
            createdAt: '2024-01-01T00:00:00Z',
            updatedAt: '2024-01-01T00:00:00Z',
          },
        ],
        total: 1,
      }
      mockedApi.get.mockResolvedValueOnce(mockCredentials)

      const { result } = renderHook(() => useCredentials({ personId: 'person-1' }), { wrapper })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))
      expect(result.current.data?.items).toHaveLength(1)
      expect(result.current.data?.items[0].status).toBe('active')
    })
  })

  describe('Error Handling', () => {
    it('should handle API errors gracefully', async () => {
      const apiError = { message: 'Server error', status: 500 }
      mockedApi.get.mockRejectedValueOnce(apiError)

      const { result } = renderHook(() => useProcedures(), { wrapper })

      await waitFor(() => expect(result.current.isError).toBe(true))
      expect(result.current.error).toEqual(apiError)
    })

    it('should handle not found errors', async () => {
      const apiError = { message: 'Procedure not found', status: 404 }
      mockedApi.get.mockRejectedValueOnce(apiError)

      const { result } = renderHook(() => useProcedure('non-existent'), { wrapper })

      await waitFor(() => expect(result.current.isError).toBe(true))
      expect((result.current.error as { status: number }).status).toBe(404)
    })
  })

  describe('Loading States', () => {
    it('should show loading state while fetching', async () => {
      mockedApi.get.mockImplementation(() => new Promise(() => {})) // Never resolves

      const { result } = renderHook(() => useProcedures(), { wrapper })

      expect(result.current.isLoading).toBe(true)
    })
  })
})
