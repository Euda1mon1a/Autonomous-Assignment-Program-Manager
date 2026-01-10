/**
 * Tests for useAbsences hook
 * Tests absence management, leave calendar, military leave, and approvals
 */
import { renderHook, waitFor, act } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import {
  useAbsence,
  useAbsenceList,
  useAbsences,
  useLeaveCalendar,
  useMilitaryLeave,
  useLeaveBalance,
  useAbsenceCreate,
  useAbsenceUpdate,
  useAbsenceApprove,
  useAbsenceDelete,
  AbsenceStatus,
} from '@/hooks/useAbsences'
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

describe('useAbsence', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Initial State', () => {
    it('should initialize with loading state', () => {
      mockedApi.get.mockImplementation(() => new Promise(() => {}))

      const { result } = renderHook(() => useAbsence('absence-123'), {
        wrapper: createWrapper(),
      })

      expect(result.current.isLoading).toBe(true)
      expect(result.current.data).toBeUndefined()
      expect(result.current.error).toBeNull()
    })

    it('should not fetch when id is empty', () => {
      const { result } = renderHook(() => useAbsence(''), {
        wrapper: createWrapper(),
      })

      expect(result.current.isLoading).toBe(false)
      expect(mockedApi.get).not.toHaveBeenCalled()
    })
  })

  describe('Success Scenarios', () => {
    it('should fetch absence successfully', async () => {
      const mockAbsence = {
        id: 'absence-123',
        personId: 'person-1',
        personName: 'Dr. Smith',
        startDate: '2024-01-01',
        endDate: '2024-01-07',
        absenceType: 'vacation',
        reason: 'Family trip',
        status: AbsenceStatus.APPROVED,
      }

      mockedApi.get.mockResolvedValue(mockAbsence)

      const { result } = renderHook(() => useAbsence('absence-123'), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data).toEqual(mockAbsence)
      expect(mockedApi.get).toHaveBeenCalledWith('/absences/absence-123')
    })

    it('should fetch absence with deployment orders', async () => {
      const mockAbsence = {
        id: 'absence-123',
        personId: 'person-1',
        personName: 'Dr. Smith',
        startDate: '2024-03-01',
        endDate: '2024-09-01',
        absenceType: 'deployment',
        deploymentOrders: true,
        notes: 'Overseas deployment',
        status: AbsenceStatus.APPROVED,
      }

      mockedApi.get.mockResolvedValue(mockAbsence)

      const { result } = renderHook(() => useAbsence('absence-123'), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data?.absenceType).toBe('deployment')
      expect(result.current.data?.deploymentOrders).toBe(true)
    })
  })

  describe('Error Handling', () => {
    it('should handle fetch errors', async () => {
      const error = { message: 'Absence not found', status: 404 }
      mockedApi.get.mockRejectedValue(error)

      const { result } = renderHook(() => useAbsence('absence-123'), {
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

      const { result } = renderHook(() => useAbsence('absence-123'), {
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

      const { result } = renderHook(() => useAbsence('absence-123'), {
        wrapper: createWrapper(),
      })

      expect(result.current.isLoading).toBe(true)
      expect(result.current.isFetching).toBe(true)

      act(() => {
        resolvePromise!({
          id: 'absence-123',
          personId: 'person-1',
          absenceType: 'vacation',
        })
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })
    })
  })

  describe('Edge Cases', () => {
    it('should handle sick leave absence', async () => {
      const mockAbsence = {
        id: 'absence-123',
        personId: 'person-1',
        startDate: '2024-01-01',
        endDate: '2024-01-03',
        absenceType: 'sick',
        status: AbsenceStatus.APPROVED,
      }

      mockedApi.get.mockResolvedValue(mockAbsence)

      const { result } = renderHook(() => useAbsence('absence-123'), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data?.absenceType).toBe('sick')
    })

    it('should handle conference absence', async () => {
      const mockAbsence = {
        id: 'absence-123',
        personId: 'person-1',
        startDate: '2024-06-10',
        endDate: '2024-06-14',
        absenceType: 'conference',
        notes: 'National Conference',
        status: AbsenceStatus.APPROVED,
      }

      mockedApi.get.mockResolvedValue(mockAbsence)

      const { result } = renderHook(() => useAbsence('absence-123'), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data?.absenceType).toBe('conference')
    })
  })
})

describe('useAbsenceList', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Success Scenarios', () => {
    it('should fetch absence list successfully', async () => {
      const mockAbsences = {
        items: [
          {
            id: 'absence-1',
            personId: 'person-1',
            absenceType: 'vacation',
            startDate: '2024-01-01',
            endDate: '2024-01-07',
          },
          {
            id: 'absence-2',
            personId: 'person-2',
            absenceType: 'sick',
            startDate: '2024-01-15',
            endDate: '2024-01-17',
          },
        ],
        total: 2,
      }

      mockedApi.get.mockResolvedValue(mockAbsences)

      const { result } = renderHook(() => useAbsenceList(), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data).toEqual(mockAbsences)
      expect(result.current.data?.items).toHaveLength(2)
    })

    it('should filter by personId', async () => {
      mockedApi.get.mockResolvedValue({ items: [], total: 0 })

      const { result } = renderHook(
        () => useAbsenceList({ personId: 'person-1' }),
        {
          wrapper: createWrapper(),
        }
      )

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(mockedApi.get).toHaveBeenCalledWith(
        expect.stringContaining('personId=person-1')
      )
    })

    it('should filter by date range', async () => {
      mockedApi.get.mockResolvedValue({ items: [], total: 0 })

      const { result } = renderHook(
        () =>
          useAbsenceList({
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

      expect(mockedApi.get).toHaveBeenCalledWith(
        expect.stringContaining('startDate=2024-01-01')
      )
      expect(mockedApi.get).toHaveBeenCalledWith(
        expect.stringContaining('endDate=2024-01-31')
      )
    })

    it('should filter by absence type', async () => {
      mockedApi.get.mockResolvedValue({ items: [], total: 0 })

      const { result } = renderHook(
        () => useAbsenceList({ absenceType: 'vacation' }),
        {
          wrapper: createWrapper(),
        }
      )

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(mockedApi.get).toHaveBeenCalledWith(
        expect.stringContaining('absenceType=vacation')
      )
    })
  })

  describe('Error Handling', () => {
    it('should handle fetch errors', async () => {
      const error = { message: 'Failed to fetch absences', status: 500 }
      mockedApi.get.mockRejectedValue(error)

      const { result } = renderHook(() => useAbsenceList(), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
      })

      expect(result.current.error).toEqual(error)
    })
  })

  describe('Edge Cases', () => {
    it('should handle empty absence list', async () => {
      mockedApi.get.mockResolvedValue({ items: [], total: 0 })

      const { result } = renderHook(() => useAbsenceList(), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data?.items).toEqual([])
      expect(result.current.data?.total).toBe(0)
    })
  })
})

describe('useLeaveCalendar', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Success Scenarios', () => {
    it('should fetch leave calendar successfully', async () => {
      const mockCalendar = {
        startDate: '2024-01-01',
        endDate: '2024-01-31',
        entries: [
          {
            facultyId: 'faculty-1',
            facultyName: 'Dr. Smith',
            leave_type: 'vacation',
            startDate: '2024-01-10',
            endDate: '2024-01-17',
            is_blocking: true,
            has_fmit_conflict: false,
          },
        ],
        conflictCount: 0,
      }

      mockedApi.get.mockResolvedValue(mockCalendar)

      const { result } = renderHook(
        () => useLeaveCalendar('2024-01-01', '2024-01-31'),
        {
          wrapper: createWrapper(),
        }
      )

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data).toEqual(mockCalendar)
      expect(result.current.data?.entries).toHaveLength(1)
    })

    it('should detect FMIT conflicts', async () => {
      const mockCalendar = {
        startDate: '2024-01-01',
        endDate: '2024-01-31',
        entries: [
          {
            facultyId: 'faculty-1',
            facultyName: 'Dr. Smith',
            leave_type: 'deployment',
            startDate: '2024-01-15',
            endDate: '2024-07-15',
            is_blocking: true,
            has_fmit_conflict: true,
          },
        ],
        conflictCount: 1,
      }

      mockedApi.get.mockResolvedValue(mockCalendar)

      const { result } = renderHook(
        () => useLeaveCalendar('2024-01-01', '2024-01-31'),
        {
          wrapper: createWrapper(),
        }
      )

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data?.conflictCount).toBe(1)
      expect(result.current.data?.entries[0].has_fmit_conflict).toBe(true)
    })
  })

  describe('Error Handling', () => {
    it('should handle fetch errors', async () => {
      const error = { message: 'Failed to fetch calendar', status: 500 }
      mockedApi.get.mockRejectedValue(error)

      const { result } = renderHook(
        () => useLeaveCalendar('2024-01-01', '2024-01-31'),
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

  describe('Edge Cases', () => {
    it('should not fetch when dates are empty', () => {
      const { result } = renderHook(() => useLeaveCalendar('', ''), {
        wrapper: createWrapper(),
      })

      expect(result.current.isLoading).toBe(false)
      expect(mockedApi.get).not.toHaveBeenCalled()
    })
  })
})

describe('useMilitaryLeave', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Success Scenarios', () => {
    it('should fetch military leave successfully', async () => {
      const mockAbsences = {
        items: [
          {
            id: 'absence-1',
            personId: 'person-1',
            absenceType: 'deployment',
            startDate: '2024-03-01',
            endDate: '2024-09-01',
          },
          {
            id: 'absence-2',
            personId: 'person-1',
            absenceType: 'tdy',
            startDate: '2024-10-01',
            endDate: '2024-10-14',
          },
          {
            id: 'absence-3',
            personId: 'person-1',
            absenceType: 'vacation',
            startDate: '2024-11-01',
            endDate: '2024-11-07',
          },
        ],
        total: 3,
      }

      mockedApi.get.mockResolvedValue(mockAbsences)

      const { result } = renderHook(() => useMilitaryLeave('person-1'), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      // Should only include deployment and tdy, filter out vacation
      expect(result.current.data?.items).toHaveLength(2)
      expect(result.current.data?.total).toBe(2)
    })

    it('should handle no military leave', async () => {
      const mockAbsences = {
        items: [
          {
            id: 'absence-1',
            personId: 'person-1',
            absenceType: 'vacation',
            startDate: '2024-01-01',
            endDate: '2024-01-07',
          },
        ],
        total: 1,
      }

      mockedApi.get.mockResolvedValue(mockAbsences)

      const { result } = renderHook(() => useMilitaryLeave('person-1'), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data?.items).toHaveLength(0)
      expect(result.current.data?.total).toBe(0)
    })
  })
})

describe('useLeaveBalance', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Success Scenarios', () => {
    it('should fetch leave balance successfully', async () => {
      const mockBalance = {
        personId: 'person-1',
        personName: 'Dr. Smith',
        vacation_days: 10,
        sick_days: 5,
        personal_days: 3,
        total_days_taken: 12,
        total_days_allocated: 30,
      }

      mockedApi.get.mockResolvedValue(mockBalance)

      const { result } = renderHook(() => useLeaveBalance('person-1'), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data).toEqual(mockBalance)
      expect(result.current.data?.vacation_days).toBe(10)
    })
  })

  describe('Error Handling', () => {
    it('should handle 404 errors', async () => {
      const error = { message: 'Not implemented', status: 404 }
      mockedApi.get.mockRejectedValue(error)

      const { result } = renderHook(() => useLeaveBalance('person-1'), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
      })

      expect(result.current.error?.status).toBe(404)
    })
  })

  describe('Edge Cases', () => {
    it('should not fetch when personId is empty', () => {
      const { result } = renderHook(() => useLeaveBalance(''), {
        wrapper: createWrapper(),
      })

      expect(result.current.isLoading).toBe(false)
      expect(mockedApi.get).not.toHaveBeenCalled()
    })
  })
})

describe('useAbsenceCreate', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Success Scenarios', () => {
    it('should create absence successfully', async () => {
      const mockAbsence = {
        id: 'absence-123',
        personId: 'person-1',
        startDate: '2024-01-01',
        endDate: '2024-01-07',
        absenceType: 'vacation',
        reason: 'Family trip',
        status: AbsenceStatus.PENDING,
      }

      mockedApi.post.mockResolvedValue(mockAbsence)

      const { result } = renderHook(() => useAbsenceCreate(), {
        wrapper: createWrapper(),
      })

      act(() => {
        result.current.mutate({
          personId: 'person-1',
          startDate: '2024-01-01',
          endDate: '2024-01-07',
          absenceType: 'vacation',
          reason: 'Family trip',
        } as any)
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data).toEqual(mockAbsence)
    })

    it('should create deployment absence', async () => {
      const mockAbsence = {
        id: 'absence-123',
        personId: 'person-1',
        startDate: '2024-03-01',
        endDate: '2024-09-01',
        absenceType: 'deployment',
        deploymentOrders: true,
        status: AbsenceStatus.APPROVED,
      }

      mockedApi.post.mockResolvedValue(mockAbsence)

      const { result } = renderHook(() => useAbsenceCreate(), {
        wrapper: createWrapper(),
      })

      act(() => {
        result.current.mutate({
          personId: 'person-1',
          startDate: '2024-03-01',
          endDate: '2024-09-01',
          absenceType: 'deployment',
          deploymentOrders: true,
        } as any)
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data?.absenceType).toBe('deployment')
    })
  })

  describe('Error Handling', () => {
    it('should handle overlapping absence errors', async () => {
      const error = { message: 'Overlapping absence exists', status: 409 }
      mockedApi.post.mockRejectedValue(error)

      const { result } = renderHook(() => useAbsenceCreate(), {
        wrapper: createWrapper(),
      })

      act(() => {
        result.current.mutate({
          personId: 'person-1',
          startDate: '2024-01-01',
          endDate: '2024-01-07',
          absenceType: 'vacation',
        } as any)
      })

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
      })

      expect(result.current.error?.status).toBe(409)
    })

    it('should handle validation errors', async () => {
      const error = { message: 'Invalid date range', status: 400 }
      mockedApi.post.mockRejectedValue(error)

      const { result } = renderHook(() => useAbsenceCreate(), {
        wrapper: createWrapper(),
      })

      act(() => {
        result.current.mutate({
          personId: 'person-1',
          startDate: '2024-01-07',
          endDate: '2024-01-01', // Invalid: end before start
          absenceType: 'vacation',
        } as any)
      })

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
      })

      expect(result.current.error?.status).toBe(400)
    })
  })

  describe('Loading States', () => {
    it('should show pending during creation', async () => {
      let resolvePromise: (value: any) => void
      const promise = new Promise((resolve) => {
        resolvePromise = resolve
      })

      mockedApi.post.mockReturnValue(promise as any)

      const { result } = renderHook(() => useAbsenceCreate(), {
        wrapper: createWrapper(),
      })

      act(() => {
        result.current.mutate({
          personId: 'person-1',
          startDate: '2024-01-01',
          endDate: '2024-01-07',
          absenceType: 'vacation',
        } as any)
      })

      expect(result.current.isPending).toBe(true)

      act(() => {
        resolvePromise!({
          id: 'absence-123',
          personId: 'person-1',
          absenceType: 'vacation',
        })
      })

      await waitFor(() => {
        expect(result.current.isPending).toBe(false)
      })
    })
  })
})

describe('useAbsenceUpdate', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Success Scenarios', () => {
    it('should update absence successfully', async () => {
      const mockAbsence = {
        id: 'absence-123',
        personId: 'person-1',
        startDate: '2024-01-01',
        endDate: '2024-01-10', // Extended from 7 to 10 days
        absenceType: 'vacation',
        reason: 'Extended family trip',
        status: AbsenceStatus.PENDING,
      }

      mockedApi.put.mockResolvedValue(mockAbsence)

      const { result } = renderHook(() => useAbsenceUpdate(), {
        wrapper: createWrapper(),
      })

      act(() => {
        result.current.mutate({
          id: 'absence-123',
          data: {
            endDate: '2024-01-10',
            reason: 'Extended family trip',
          } as any,
        })
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data).toEqual(mockAbsence)
    })
  })

  describe('Error Handling', () => {
    it('should handle update errors', async () => {
      const error = { message: 'Cannot modify approved absence', status: 400 }
      mockedApi.put.mockRejectedValue(error)

      const { result } = renderHook(() => useAbsenceUpdate(), {
        wrapper: createWrapper(),
      })

      act(() => {
        result.current.mutate({
          id: 'absence-123',
          data: { endDate: '2024-01-10' } as any,
        })
      })

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
      })

      expect(result.current.error).toEqual(error)
    })
  })
})

describe('useAbsenceDelete', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Success Scenarios', () => {
    it('should delete absence successfully', async () => {
      mockedApi.del.mockResolvedValue(undefined)

      const { result } = renderHook(() => useAbsenceDelete(), {
        wrapper: createWrapper(),
      })

      act(() => {
        result.current.mutate('absence-123')
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(mockedApi.del).toHaveBeenCalledWith('/absences/absence-123')
    })
  })

  describe('Error Handling', () => {
    it('should handle deletion errors', async () => {
      const error = { message: 'Cannot delete executed absence', status: 400 }
      mockedApi.del.mockRejectedValue(error)

      const { result } = renderHook(() => useAbsenceDelete(), {
        wrapper: createWrapper(),
      })

      act(() => {
        result.current.mutate('absence-123')
      })

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
      })

      expect(result.current.error).toEqual(error)
    })
  })
})

describe('useAbsenceApprove', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Success Scenarios', () => {
    it('should approve absence successfully', async () => {
      const mockAbsence = {
        id: 'absence-123',
        personId: 'person-1',
        startDate: '2024-01-01',
        endDate: '2024-01-07',
        absenceType: 'vacation',
        approvalStatus: AbsenceStatus.APPROVED,
      }

      mockedApi.post.mockResolvedValue(mockAbsence)

      const { result } = renderHook(() => useAbsenceApprove(), {
        wrapper: createWrapper(),
      })

      act(() => {
        result.current.mutate({
          absence_id: 'absence-123',
          approved: true,
          comments: 'Approved - coverage confirmed',
        })
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect((result.current.data as { approvalStatus?: AbsenceStatus })?.approvalStatus).toBe(AbsenceStatus.APPROVED)
    })

    it('should reject absence successfully', async () => {
      const mockAbsence = {
        id: 'absence-123',
        personId: 'person-1',
        startDate: '2024-01-01',
        endDate: '2024-01-07',
        absenceType: 'vacation',
        approvalStatus: AbsenceStatus.REJECTED,
      }

      mockedApi.post.mockResolvedValue(mockAbsence)

      const { result } = renderHook(() => useAbsenceApprove(), {
        wrapper: createWrapper(),
      })

      act(() => {
        result.current.mutate({
          absence_id: 'absence-123',
          approved: false,
          comments: 'Rejected - insufficient coverage',
        })
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect((result.current.data as { approvalStatus?: AbsenceStatus })?.approvalStatus).toBe(AbsenceStatus.REJECTED)
    })
  })

  describe('Error Handling', () => {
    it('should handle 404 for unimplemented endpoint', async () => {
      const error = { message: 'Not implemented', status: 404 }
      mockedApi.post.mockRejectedValue(error)

      const { result } = renderHook(() => useAbsenceApprove(), {
        wrapper: createWrapper(),
      })

      act(() => {
        result.current.mutate({
          absence_id: 'absence-123',
          approved: true,
        })
      })

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
      })

      expect(result.current.error?.status).toBe(404)
    })
  })
})
