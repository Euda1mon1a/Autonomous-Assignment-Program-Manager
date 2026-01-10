/**
 * Tests for useSchedule hook
 * Tests schedule fetching, generation, validation, rotation templates, and assignments
 */
import { renderHook, waitFor, act } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import {
  useSchedule,
  useGenerateSchedule,
  useValidateSchedule,
  useRotationTemplates,
  useRotationTemplate,
  useCreateTemplate,
  useUpdateTemplate,
  useDeleteTemplate,
  useAssignments,
  useCreateAssignment,
  useUpdateAssignment,
  useDeleteAssignment,
} from '@/hooks/useSchedule'
import * as api from '@/lib/api'
import React from 'react'

// Mock API module
jest.mock('@/lib/api')

const mockedApi = api as jest.Mocked<typeof api>

// Create wrapper with QueryClient
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

describe('useSchedule', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Initial State', () => {
    it('should initialize with loading state', () => {
      mockedApi.get.mockImplementation(() => new Promise(() => {}))

      const startDate = new Date('2024-01-01')
      const endDate = new Date('2024-01-31')

      const { result } = renderHook(() => useSchedule(startDate, endDate), {
        wrapper: createWrapper(),
      })

      expect(result.current.isLoading).toBe(true)
      expect(result.current.data).toBeUndefined()
      expect(result.current.error).toBeNull()
    })

    it('should use correct query key format', async () => {
      mockedApi.get.mockResolvedValue({ items: [], total: 0 })

      const startDate = new Date('2024-01-01')
      const endDate = new Date('2024-01-31')

      const { result } = renderHook(() => useSchedule(startDate, endDate), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(mockedApi.get).toHaveBeenCalledWith(
        expect.stringContaining('/assignments?startDate=2024-01-01&endDate=2024-01-31')
      )
    })
  })

  describe('Success Scenarios', () => {
    it('should fetch schedule successfully', async () => {
      const mockSchedule = {
        items: [
          {
            id: 'assignment-1',
            personId: 'person-1',
            rotationTemplateId: 'rotation-1',
            startDate: '2024-01-01',
            endDate: '2024-01-07',
          },
        ],
        total: 1,
      }

      mockedApi.get.mockResolvedValue(mockSchedule)

      const startDate = new Date('2024-01-01')
      const endDate = new Date('2024-01-31')

      const { result } = renderHook(() => useSchedule(startDate, endDate), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data).toEqual(mockSchedule)
      expect(result.current.data?.items).toHaveLength(1)
      expect(result.current.data?.total).toBe(1)
    })

    it('should handle empty schedule', async () => {
      mockedApi.get.mockResolvedValue({ items: [], total: 0 })

      const startDate = new Date('2024-01-01')
      const endDate = new Date('2024-01-31')

      const { result } = renderHook(() => useSchedule(startDate, endDate), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data?.items).toEqual([])
      expect(result.current.data?.total).toBe(0)
    })

    it('should refetch on date range change', async () => {
      mockedApi.get.mockResolvedValue({ items: [], total: 0 })

      const { result, rerender } = renderHook(
        ({ start, end }) => useSchedule(start, end),
        {
          wrapper: createWrapper(),
          initialProps: {
            start: new Date('2024-01-01'),
            end: new Date('2024-01-31'),
          },
        }
      )

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(mockedApi.get).toHaveBeenCalledTimes(1)

      // Change date range
      rerender({
        start: new Date('2024-02-01'),
        end: new Date('2024-02-28'),
      })

      await waitFor(() => {
        expect(mockedApi.get).toHaveBeenCalledTimes(2)
      })
    })
  })

  describe('Error Handling', () => {
    it('should handle fetch errors', async () => {
      const error = { message: 'Network error', status: 500 }
      mockedApi.get.mockRejectedValue(error)

      const startDate = new Date('2024-01-01')
      const endDate = new Date('2024-01-31')

      const { result } = renderHook(() => useSchedule(startDate, endDate), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
      })

      expect(result.current.error).toEqual(error)
    })

    it('should handle unauthorized errors', async () => {
      const error = { message: 'Unauthorized', status: 401 }
      mockedApi.get.mockRejectedValue(error)

      const startDate = new Date('2024-01-01')
      const endDate = new Date('2024-01-31')

      const { result } = renderHook(() => useSchedule(startDate, endDate), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
      })

      expect(result.current.error?.status).toBe(401)
    })
  })

  describe('Loading States', () => {
    it('should show loading during fetch', async () => {
      let resolvePromise: (value: any) => void
      const promise = new Promise((resolve) => {
        resolvePromise = resolve
      })

      mockedApi.get.mockReturnValue(promise as any)

      const startDate = new Date('2024-01-01')
      const endDate = new Date('2024-01-31')

      const { result } = renderHook(() => useSchedule(startDate, endDate), {
        wrapper: createWrapper(),
      })

      expect(result.current.isLoading).toBe(true)
      expect(result.current.isFetching).toBe(true)

      act(() => {
        resolvePromise!({ items: [], total: 0 })
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
        expect(result.current.isFetching).toBe(false)
      })
    })

    it('should show background fetching', async () => {
      mockedApi.get.mockResolvedValue({ items: [], total: 0 })

      const startDate = new Date('2024-01-01')
      const endDate = new Date('2024-01-31')

      const { result } = renderHook(() => useSchedule(startDate, endDate), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      // Trigger refetch
      act(() => {
        result.current.refetch()
      })

      expect(result.current.isFetching).toBe(true)
    })
  })

  describe('Edge Cases', () => {
    it('should handle large date ranges', async () => {
      mockedApi.get.mockResolvedValue({ items: [], total: 0 })

      const startDate = new Date('2024-01-01')
      const endDate = new Date('2024-12-31')

      const { result } = renderHook(() => useSchedule(startDate, endDate), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(mockedApi.get).toHaveBeenCalledWith(
        expect.stringContaining('startDate=2024-01-01&endDate=2024-12-31')
      )
    })

    it('should handle single day range', async () => {
      mockedApi.get.mockResolvedValue({ items: [], total: 0 })

      const date = new Date('2024-01-01')

      const { result } = renderHook(() => useSchedule(date, date), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })
    })

    it('should handle reversed date range', async () => {
      mockedApi.get.mockResolvedValue({ items: [], total: 0 })

      const startDate = new Date('2024-01-31')
      const endDate = new Date('2024-01-01')

      const { result } = renderHook(() => useSchedule(startDate, endDate), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      // Should still make request even with reversed dates
      expect(mockedApi.get).toHaveBeenCalled()
    })
  })
})

describe('useGenerateSchedule', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Success Scenarios', () => {
    it('should generate schedule successfully', async () => {
      const mockResponse = {
        status: 'success' as const,
        message: 'Schedule generated successfully',
        totalBlocks_assigned: 100,
        totalBlocks: 100,
        validation: {
          valid: true,
          totalViolations: 0,
          violations: [],
          coverageRate: 1.0,
          statistics: null,
        },
      }

      mockedApi.post.mockResolvedValue(mockResponse)

      const { result } = renderHook(() => useGenerateSchedule(), {
        wrapper: createWrapper(),
      })

      act(() => {
        result.current.mutate({
          startDate: '2024-01-01',
          endDate: '2024-12-31',
          algorithm: 'hybrid',
        })
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data).toEqual(mockResponse)
      expect(result.current.data?.status).toBe('success')
    })

    it('should handle partial schedule generation', async () => {
      const mockResponse = {
        status: 'partial' as const,
        message: 'Partial schedule generated',
        totalBlocks_assigned: 80,
        totalBlocks: 100,
        validation: {
          valid: false,
          totalViolations: 1,
          violations: [{ type: 'coverage', severity: 'HIGH' as const, personId: null, personName: null, blockId: null, message: 'Coverage gap in week 10', details: null }],
          coverageRate: 0.8,
          statistics: null,
        },
      }

      mockedApi.post.mockResolvedValue(mockResponse)

      const { result } = renderHook(() => useGenerateSchedule(), {
        wrapper: createWrapper(),
      })

      act(() => {
        result.current.mutate({
          startDate: '2024-01-01',
          endDate: '2024-12-31',
        })
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data?.status).toBe('partial')
      expect(result.current.data?.totalBlocks_assigned).toBe(80)
    })
  })

  describe('Error Handling', () => {
    it('should handle generation errors', async () => {
      const error = { message: 'Generation failed', status: 500 }
      mockedApi.post.mockRejectedValue(error)

      const { result } = renderHook(() => useGenerateSchedule(), {
        wrapper: createWrapper(),
      })

      act(() => {
        result.current.mutate({
          startDate: '2024-01-01',
          endDate: '2024-12-31',
        })
      })

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
      })

      expect(result.current.error).toEqual(error)
    })

    it('should handle timeout errors', async () => {
      const error = { message: 'Solver timeout', status: 408 }
      mockedApi.post.mockRejectedValue(error)

      const { result } = renderHook(() => useGenerateSchedule(), {
        wrapper: createWrapper(),
      })

      act(() => {
        result.current.mutate({
          startDate: '2024-01-01',
          endDate: '2024-12-31',
          timeout_seconds: 60,
        })
      })

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
      })

      expect(result.current.error?.status).toBe(408)
    })
  })

  describe('Loading States', () => {
    it('should show pending during generation', async () => {
      let resolvePromise: (value: any) => void
      const promise = new Promise((resolve) => {
        resolvePromise = resolve
      })

      mockedApi.post.mockReturnValue(promise as any)

      const { result } = renderHook(() => useGenerateSchedule(), {
        wrapper: createWrapper(),
      })

      act(() => {
        result.current.mutate({
          startDate: '2024-01-01',
          endDate: '2024-12-31',
        })
      })

      expect(result.current.isPending).toBe(true)

      act(() => {
        resolvePromise!({
          status: 'success',
          message: 'Done',
          totalBlocks_assigned: 100,
          totalBlocks: 100,
          validation: { valid: true, totalViolations: 0, violations: [], coverageRate: 1.0, statistics: null },
        })
      })

      await waitFor(() => {
        expect(result.current.isPending).toBe(false)
      })
    })
  })
})

describe('useValidateSchedule', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Success Scenarios', () => {
    it('should validate compliant schedule', async () => {
      const mockValidation = {
        valid: true,
        totalViolations: 0,
        violations: [],
        coverageRate: 1.0,
        statistics: null,
      }

      mockedApi.get.mockResolvedValue(mockValidation)

      const { result } = renderHook(
        () => useValidateSchedule('2024-01-01', '2024-01-31'),
        {
          wrapper: createWrapper(),
        }
      )

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data?.valid).toBe(true)
      expect(result.current.data?.violations).toHaveLength(0)
    })

    it('should detect violations', async () => {
      const mockValidation = {
        valid: false,
        totalViolations: 1,
        violations: [{ type: 'hours', severity: 'CRITICAL' as const, personId: 'person-1', personName: 'Dr. Smith', blockId: null, message: '80-hour rule violated', details: null }],
        coverageRate: 0.95,
        statistics: null,
      }

      mockedApi.get.mockResolvedValue(mockValidation)

      const { result } = renderHook(
        () => useValidateSchedule('2024-01-01', '2024-01-31'),
        {
          wrapper: createWrapper(),
        }
      )

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data?.valid).toBe(false)
      expect(result.current.data?.violations).toHaveLength(1)
    })
  })

  describe('Error Handling', () => {
    it('should handle validation errors', async () => {
      const error = { message: 'Validation failed', status: 500 }
      mockedApi.get.mockRejectedValue(error)

      const { result } = renderHook(
        () => useValidateSchedule('2024-01-01', '2024-01-31'),
        {
          wrapper: createWrapper(),
        }
      )

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
      })

      expect(result.current.error).toEqual(error)
    })
  })
})

describe('useRotationTemplates', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Success Scenarios', () => {
    it('should fetch rotation templates', async () => {
      const mockTemplates = {
        items: [
          {
            id: 'template-1',
            name: 'Inpatient Rotation',
            duration_weeks: 4,
            specialty: 'Internal Medicine',
          },
        ],
        total: 1,
      }

      mockedApi.get.mockResolvedValue(mockTemplates)

      const { result } = renderHook(() => useRotationTemplates(), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data).toEqual(mockTemplates)
      expect(result.current.data?.items).toHaveLength(1)
    })
  })
})

describe('useAssignments', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Success Scenarios', () => {
    it('should fetch assignments with filters', async () => {
      const mockAssignments = {
        items: [
          {
            id: 'assignment-1',
            personId: 'person-1',
            rotationTemplateId: 'rotation-1',
          },
        ],
        total: 1,
      }

      mockedApi.get.mockResolvedValue(mockAssignments)

      const { result } = renderHook(
        () =>
          useAssignments({
            personId: 'person-1',
            startDate: '2024-01-01',
            endDate: '2024-01-31',
          }),
        {
          wrapper: createWrapper(),
        }
      )

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data).toEqual(mockAssignments)
      expect(mockedApi.get).toHaveBeenCalledWith(
        expect.stringContaining('personId=person-1')
      )
    })
  })
})

describe('useCreateAssignment', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Success Scenarios', () => {
    it('should create assignment successfully', async () => {
      const mockAssignment = {
        id: 'assignment-1',
        personId: 'person-1',
        rotationTemplateId: 'rotation-1',
        startDate: '2024-01-01',
        endDate: '2024-01-07',
      }

      mockedApi.post.mockResolvedValue(mockAssignment)

      const { result } = renderHook(() => useCreateAssignment(), {
        wrapper: createWrapper(),
      })

      act(() => {
        result.current.mutate({
          personId: 'person-1',
          rotationId: 'rotation-1',
          startDate: '2024-01-01',
          endDate: '2024-01-07',
        } as any)
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data).toEqual(mockAssignment)
    })
  })

  describe('Error Handling', () => {
    it('should handle conflict errors', async () => {
      const error = { message: 'Assignment conflict', status: 409 }
      mockedApi.post.mockRejectedValue(error)

      const { result } = renderHook(() => useCreateAssignment(), {
        wrapper: createWrapper(),
      })

      act(() => {
        result.current.mutate({
          personId: 'person-1',
          rotationId: 'rotation-1',
          startDate: '2024-01-01',
          endDate: '2024-01-07',
        } as any)
      })

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
      })

      expect(result.current.error?.status).toBe(409)
    })
  })
})
