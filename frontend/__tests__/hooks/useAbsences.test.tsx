/**
 * Comprehensive tests for useAbsences hooks
 *
 * Tests all absence management hooks including fetching, filtering, CRUD operations,
 * military leave, leave balance, leave calendar, and approval workflows.
 */
import { renderHook, waitFor, act } from '@testing-library/react'
import {
  useAbsence,
  useAbsences,
  useAbsenceList,
  useAbsenceCreate,
  useAbsenceUpdate,
  useAbsenceDelete,
  useAbsenceApprove,
  useMilitaryLeave,
  useLeaveBalance,
  useLeaveCalendar,
  useCreateAbsence,
  useUpdateAbsence,
  useDeleteAbsence,
} from '@/hooks/useAbsences'
import { createWrapper, mockFactories, mockResponses } from '../utils/test-utils'
import * as api from '@/lib/api'

// Mock the api module
jest.mock('@/lib/api', () => ({
  get: jest.fn(),
  post: jest.fn(),
  put: jest.fn(),
  del: jest.fn(),
}))

const mockedApi = api as jest.Mocked<typeof api>

describe('useAbsences Hooks', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  // ============================================================================
  // Query Hooks - Basic Fetching
  // ============================================================================

  describe('useAbsenceList', () => {
    it('should fetch all absences without filters', async () => {
      const mockData = mockResponses.listAbsences
      mockedApi.get.mockResolvedValueOnce(mockData)

      const { result } = renderHook(
        () => useAbsenceList(),
        { wrapper: createWrapper() }
      )

      expect(result.current.isLoading).toBe(true)

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(mockedApi.get).toHaveBeenCalledWith('/absences')
      expect(result.current.data?.items).toHaveLength(1)
      expect(result.current.data?.total).toBe(1)
    })

    it('should filter absences by person_id', async () => {
      const personAbsences = {
        items: [mockFactories.absence({ person_id: 'person-123' })],
        total: 1,
      }
      mockedApi.get.mockResolvedValueOnce(personAbsences)

      const { result } = renderHook(
        () => useAbsenceList({ person_id: 'person-123' }),
        { wrapper: createWrapper() }
      )

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(mockedApi.get).toHaveBeenCalledWith('/absences?person_id=person-123')
      expect(result.current.data).toEqual(personAbsences)
    })

    it('should filter absences by date range', async () => {
      const dateFilteredAbsences = {
        items: [
          mockFactories.absence({
            start_date: '2024-02-01',
            end_date: '2024-02-07',
          }),
        ],
        total: 1,
      }
      mockedApi.get.mockResolvedValueOnce(dateFilteredAbsences)

      const { result } = renderHook(
        () => useAbsenceList({
          start_date: '2024-02-01',
          end_date: '2024-02-28',
        }),
        { wrapper: createWrapper() }
      )

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(mockedApi.get).toHaveBeenCalledWith(
        '/absences?start_date=2024-02-01&end_date=2024-02-28'
      )
      expect(result.current.data).toEqual(dateFilteredAbsences)
    })

    it('should filter absences by absence_type', async () => {
      const vacationAbsences = {
        items: [mockFactories.absence({ absence_type: 'vacation' })],
        total: 1,
      }
      mockedApi.get.mockResolvedValueOnce(vacationAbsences)

      const { result } = renderHook(
        () => useAbsenceList({ absence_type: 'vacation' }),
        { wrapper: createWrapper() }
      )

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(mockedApi.get).toHaveBeenCalledWith('/absences?absence_type=vacation')
      expect(result.current.data?.items[0].absence_type).toBe('vacation')
    })

    it('should combine multiple filters', async () => {
      const filteredAbsences = {
        items: [
          mockFactories.absence({
            person_id: 'person-123',
            start_date: '2024-02-01',
            absence_type: 'deployment',
          }),
        ],
        total: 1,
      }
      mockedApi.get.mockResolvedValueOnce(filteredAbsences)

      const { result } = renderHook(
        () => useAbsenceList({
          person_id: 'person-123',
          start_date: '2024-02-01',
          end_date: '2024-06-30',
          absence_type: 'deployment',
        }),
        { wrapper: createWrapper() }
      )

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(mockedApi.get).toHaveBeenCalledWith(
        '/absences?person_id=person-123&start_date=2024-02-01&end_date=2024-06-30&absence_type=deployment'
      )
    })

    it('should handle API errors gracefully', async () => {
      const apiError = { message: 'Server error', status: 500 }
      mockedApi.get.mockRejectedValueOnce(apiError)

      const { result } = renderHook(
        () => useAbsenceList(),
        { wrapper: createWrapper() }
      )

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
      })

      expect(result.current.error).toEqual(apiError)
    })
  })

  describe('useAbsence', () => {
    it('should fetch a single absence by ID', async () => {
      const mockAbsence = mockFactories.absence({ id: 'absence-1' })
      mockedApi.get.mockResolvedValueOnce(mockAbsence)

      const { result } = renderHook(
        () => useAbsence('absence-1'),
        { wrapper: createWrapper() }
      )

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(mockedApi.get).toHaveBeenCalledWith('/absences/absence-1')
      expect(result.current.data).toEqual(mockAbsence)
    })

    it('should not fetch when ID is empty', async () => {
      const { result } = renderHook(
        () => useAbsence(''),
        { wrapper: createWrapper() }
      )

      // Query should not be enabled
      expect(mockedApi.get).not.toHaveBeenCalled()
      expect(result.current.isFetching).toBe(false)
    })

    it('should handle 404 not found errors', async () => {
      const notFoundError = { message: 'Absence not found', status: 404 }
      mockedApi.get.mockRejectedValueOnce(notFoundError)

      const { result } = renderHook(
        () => useAbsence('non-existent'),
        { wrapper: createWrapper() }
      )

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
      })

      expect(result.current.error).toEqual(notFoundError)
    })
  })

  describe('useAbsences (legacy)', () => {
    it('should fetch all absences when no personId provided', async () => {
      mockedApi.get.mockResolvedValueOnce(mockResponses.listAbsences)

      const { result } = renderHook(
        () => useAbsences(),
        { wrapper: createWrapper() }
      )

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(mockedApi.get).toHaveBeenCalledWith('/absences')
      expect(result.current.data?.items).toHaveLength(1)
    })

    it('should filter by person ID', async () => {
      const personAbsences = {
        items: [mockFactories.absence({ person_id: 'person-1' })],
        total: 1,
      }
      mockedApi.get.mockResolvedValueOnce(personAbsences)

      const { result } = renderHook(
        () => useAbsences(1),
        { wrapper: createWrapper() }
      )

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(mockedApi.get).toHaveBeenCalledWith('/absences?person_id=1')
      expect(result.current.data).toEqual(personAbsences)
    })

    it('should refetch when person ID changes', async () => {
      mockedApi.get.mockResolvedValue(mockResponses.listAbsences)

      const { result, rerender } = renderHook(
        ({ personId }) => useAbsences(personId),
        {
          wrapper: createWrapper(),
          initialProps: { personId: undefined as number | undefined },
        }
      )

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(mockedApi.get).toHaveBeenCalledTimes(1)
      expect(mockedApi.get).toHaveBeenCalledWith('/absences')

      // Change person ID
      rerender({ personId: 123 })

      await waitFor(() => {
        expect(mockedApi.get).toHaveBeenCalledTimes(2)
      })

      expect(mockedApi.get).toHaveBeenLastCalledWith('/absences?person_id=123')
    })
  })

  // ============================================================================
  // Specialized Query Hooks
  // ============================================================================

  describe('useMilitaryLeave', () => {
    it('should fetch and filter military leave types (deployment and TDY)', async () => {
      const allAbsences = {
        items: [
          mockFactories.absence({ absence_type: 'deployment' }),
          mockFactories.absence({ absence_type: 'tdy' }),
          mockFactories.absence({ absence_type: 'vacation' }),
          mockFactories.absence({ absence_type: 'sick' }),
        ],
        total: 4,
      }
      mockedApi.get.mockResolvedValueOnce(allAbsences)

      const { result } = renderHook(
        () => useMilitaryLeave(),
        { wrapper: createWrapper() }
      )

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      // Should filter to only deployment and TDY
      expect(result.current.data?.items).toHaveLength(2)
      expect(result.current.data?.total).toBe(2)
      expect(result.current.data?.items.every(
        a => a.absence_type === 'deployment' || a.absence_type === 'tdy'
      )).toBe(true)
    })

    it('should filter military leave by person', async () => {
      const personMilitaryLeave = {
        items: [
          mockFactories.absence({ person_id: 'person-123', absence_type: 'deployment' }),
        ],
        total: 1,
      }
      mockedApi.get.mockResolvedValueOnce(personMilitaryLeave)

      const { result } = renderHook(
        () => useMilitaryLeave('person-123'),
        { wrapper: createWrapper() }
      )

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(mockedApi.get).toHaveBeenCalledWith('/absences?person_id=person-123')
      expect(result.current.data?.items).toHaveLength(1)
      expect(result.current.data?.items[0].absence_type).toBe('deployment')
    })

    it('should return empty array when no military leave exists', async () => {
      const noMilitaryLeave = {
        items: [
          mockFactories.absence({ absence_type: 'vacation' }),
          mockFactories.absence({ absence_type: 'conference' }),
        ],
        total: 2,
      }
      mockedApi.get.mockResolvedValueOnce(noMilitaryLeave)

      const { result } = renderHook(
        () => useMilitaryLeave(),
        { wrapper: createWrapper() }
      )

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data?.items).toHaveLength(0)
      expect(result.current.data?.total).toBe(0)
    })
  })

  describe('useLeaveCalendar', () => {
    it('should fetch leave calendar for date range', async () => {
      const mockCalendar = {
        start_date: '2024-01-01',
        end_date: '2024-01-31',
        entries: [
          {
            faculty_id: 'fac-1',
            faculty_name: 'Dr. Smith',
            leave_type: 'vacation',
            start_date: '2024-01-15',
            end_date: '2024-01-20',
            is_blocking: true,
            has_fmit_conflict: false,
          },
        ],
        conflict_count: 0,
      }
      mockedApi.get.mockResolvedValueOnce(mockCalendar)

      const { result } = renderHook(
        () => useLeaveCalendar('2024-01-01', '2024-01-31'),
        { wrapper: createWrapper() }
      )

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(mockedApi.get).toHaveBeenCalledWith(
        '/leave/calendar?start_date=2024-01-01&end_date=2024-01-31'
      )
      expect(result.current.data).toEqual(mockCalendar)
    })

    it('should not fetch when dates are missing', async () => {
      const { result } = renderHook(
        () => useLeaveCalendar('', ''),
        { wrapper: createWrapper() }
      )

      expect(mockedApi.get).not.toHaveBeenCalled()
      expect(result.current.isFetching).toBe(false)
    })

    it('should show FMIT conflicts in calendar', async () => {
      const calendarWithConflicts = {
        start_date: '2024-02-01',
        end_date: '2024-02-28',
        entries: [
          {
            faculty_id: 'fac-1',
            faculty_name: 'Dr. Jones',
            leave_type: 'deployment',
            start_date: '2024-02-10',
            end_date: '2024-02-25',
            is_blocking: true,
            has_fmit_conflict: true,
          },
        ],
        conflict_count: 1,
      }
      mockedApi.get.mockResolvedValueOnce(calendarWithConflicts)

      const { result } = renderHook(
        () => useLeaveCalendar('2024-02-01', '2024-02-28'),
        { wrapper: createWrapper() }
      )

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data?.conflict_count).toBe(1)
      expect(result.current.data?.entries[0].has_fmit_conflict).toBe(true)
    })
  })

  describe('useLeaveBalance', () => {
    it('should fetch leave balance for a person', async () => {
      const mockBalance = {
        person_id: 'person-123',
        person_name: 'Dr. Smith',
        vacation_days: 15,
        sick_days: 10,
        personal_days: 3,
        total_days_taken: 8,
        total_days_allocated: 28,
        last_updated: '2024-01-15T10:00:00Z',
      }
      mockedApi.get.mockResolvedValueOnce(mockBalance)

      const { result } = renderHook(
        () => useLeaveBalance('person-123'),
        { wrapper: createWrapper() }
      )

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(mockedApi.get).toHaveBeenCalledWith('/absences/balance/person-123')
      expect(result.current.data).toEqual(mockBalance)
    })

    it('should not retry on 404 (endpoint not implemented)', async () => {
      const notImplementedError = { message: 'Not found', status: 404 }
      mockedApi.get.mockRejectedValueOnce(notImplementedError)

      const { result } = renderHook(
        () => useLeaveBalance('person-123'),
        { wrapper: createWrapper() }
      )

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
      })

      // Should only try once (no retries on 404)
      expect(mockedApi.get).toHaveBeenCalledTimes(1)
      expect(result.current.error?.status).toBe(404)
    })

    it('should not fetch when personId is empty', async () => {
      const { result } = renderHook(
        () => useLeaveBalance(''),
        { wrapper: createWrapper() }
      )

      expect(mockedApi.get).not.toHaveBeenCalled()
      expect(result.current.isFetching).toBe(false)
    })
  })

  // ============================================================================
  // Mutation Hooks - Create, Update, Delete
  // ============================================================================

  describe('useAbsenceCreate', () => {
    it('should create a new absence', async () => {
      const newAbsence = mockFactories.absence({
        person_id: 'person-1',
        start_date: '2024-02-01',
        end_date: '2024-02-07',
        absence_type: 'vacation',
      })
      mockedApi.post.mockResolvedValueOnce(newAbsence)

      const { result } = renderHook(
        () => useAbsenceCreate(),
        { wrapper: createWrapper() }
      )

      await act(async () => {
        result.current.mutate({
          person_id: 'person-1',
          start_date: '2024-02-01',
          end_date: '2024-02-07',
          absence_type: 'vacation',
        })
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(mockedApi.post).toHaveBeenCalledWith('/absences', {
        person_id: 'person-1',
        start_date: '2024-02-01',
        end_date: '2024-02-07',
        absence_type: 'vacation',
      })
      expect(result.current.data).toEqual(newAbsence)
    })

    it('should create deployment absence with orders', async () => {
      const deploymentAbsence = mockFactories.absence({
        absence_type: 'deployment',
        deployment_orders: true,
      })
      mockedApi.post.mockResolvedValueOnce(deploymentAbsence)

      const { result } = renderHook(
        () => useAbsenceCreate(),
        { wrapper: createWrapper() }
      )

      await act(async () => {
        result.current.mutate({
          person_id: 'person-1',
          start_date: '2024-03-01',
          end_date: '2024-06-30',
          absence_type: 'deployment',
          deployment_orders: true,
          notes: 'Military deployment',
        })
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(mockedApi.post).toHaveBeenCalledWith('/absences', expect.objectContaining({
        absence_type: 'deployment',
        deployment_orders: true,
      }))
    })

    it('should handle validation errors', async () => {
      const validationError = { message: 'End date must be after start date', status: 400 }
      mockedApi.post.mockRejectedValueOnce(validationError)

      const { result } = renderHook(
        () => useAbsenceCreate(),
        { wrapper: createWrapper() }
      )

      await act(async () => {
        result.current.mutate({
          person_id: 'person-1',
          start_date: '2024-02-07',
          end_date: '2024-02-01', // Invalid: end before start
          absence_type: 'vacation',
        })
      })

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
      })

      expect(result.current.error).toEqual(validationError)
    })
  })

  describe('useAbsenceUpdate', () => {
    it('should update an existing absence', async () => {
      const updatedAbsence = mockFactories.absence({ end_date: '2024-02-14' })
      mockedApi.put.mockResolvedValueOnce(updatedAbsence)

      const { result } = renderHook(
        () => useAbsenceUpdate(),
        { wrapper: createWrapper() }
      )

      await act(async () => {
        result.current.mutate({
          id: 'absence-1',
          data: { end_date: '2024-02-14' },
        })
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(mockedApi.put).toHaveBeenCalledWith('/absences/absence-1', { end_date: '2024-02-14' })
      expect(result.current.data).toEqual(updatedAbsence)
    })

    it('should update absence type and related fields', async () => {
      const updatedAbsence = mockFactories.absence({
        absence_type: 'tdy',
        tdy_location: 'San Antonio',
      })
      mockedApi.put.mockResolvedValueOnce(updatedAbsence)

      const { result } = renderHook(
        () => useAbsenceUpdate(),
        { wrapper: createWrapper() }
      )

      await act(async () => {
        result.current.mutate({
          id: 'absence-1',
          data: {
            absence_type: 'tdy',
            tdy_location: 'San Antonio',
          },
        })
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data?.absence_type).toBe('tdy')
      expect(result.current.data?.tdy_location).toBe('San Antonio')
    })

    it('should handle not found errors', async () => {
      const notFoundError = { message: 'Absence not found', status: 404 }
      mockedApi.put.mockRejectedValueOnce(notFoundError)

      const { result } = renderHook(
        () => useAbsenceUpdate(),
        { wrapper: createWrapper() }
      )

      await act(async () => {
        result.current.mutate({
          id: 'non-existent',
          data: { end_date: '2024-02-14' },
        })
      })

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
      })

      expect(result.current.error).toEqual(notFoundError)
    })
  })

  describe('useAbsenceDelete', () => {
    it('should delete an absence', async () => {
      mockedApi.del.mockResolvedValueOnce(undefined)

      const { result } = renderHook(
        () => useAbsenceDelete(),
        { wrapper: createWrapper() }
      )

      await act(async () => {
        result.current.mutate('absence-1')
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(mockedApi.del).toHaveBeenCalledWith('/absences/absence-1')
    })

    it('should handle not found errors on delete', async () => {
      const notFoundError = { message: 'Absence not found', status: 404 }
      mockedApi.del.mockRejectedValueOnce(notFoundError)

      const { result } = renderHook(
        () => useAbsenceDelete(),
        { wrapper: createWrapper() }
      )

      await act(async () => {
        result.current.mutate('non-existent')
      })

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
      })

      expect(result.current.error).toEqual(notFoundError)
    })
  })

  describe('useAbsenceApprove', () => {
    it('should approve an absence request', async () => {
      const approvedAbsence = mockFactories.absence({
        id: 'absence-1',
        notes: 'Approved - adequate coverage',
      })
      mockedApi.post.mockResolvedValueOnce(approvedAbsence)

      const { result } = renderHook(
        () => useAbsenceApprove(),
        { wrapper: createWrapper() }
      )

      await act(async () => {
        result.current.mutate({
          absence_id: 'absence-1',
          approved: true,
          comments: 'Approved - adequate coverage',
        })
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(mockedApi.post).toHaveBeenCalledWith(
        '/absences/absence-1/approve',
        expect.objectContaining({
          absence_id: 'absence-1',
          approved: true,
          comments: 'Approved - adequate coverage',
        })
      )
    })

    it('should reject an absence request', async () => {
      const rejectedAbsence = mockFactories.absence({
        id: 'absence-1',
        notes: 'Rejected - insufficient coverage',
      })
      mockedApi.post.mockResolvedValueOnce(rejectedAbsence)

      const { result } = renderHook(
        () => useAbsenceApprove(),
        { wrapper: createWrapper() }
      )

      await act(async () => {
        result.current.mutate({
          absence_id: 'absence-1',
          approved: false,
          comments: 'Rejected - insufficient coverage',
        })
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(mockedApi.post).toHaveBeenCalledWith(
        '/absences/absence-1/approve',
        expect.objectContaining({
          approved: false,
        })
      )
    })

    it('should not retry on 404 (endpoint not implemented)', async () => {
      const notImplementedError = { message: 'Not found', status: 404 }
      mockedApi.post.mockRejectedValueOnce(notImplementedError)

      const { result } = renderHook(
        () => useAbsenceApprove(),
        { wrapper: createWrapper() }
      )

      await act(async () => {
        result.current.mutate({
          absence_id: 'absence-1',
          approved: true,
        })
      })

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
      })

      // Should only try once (no retries on 404)
      expect(mockedApi.post).toHaveBeenCalledTimes(1)
      expect(result.current.error?.status).toBe(404)
    })
  })

  // ============================================================================
  // Legacy Exports (Backwards Compatibility)
  // ============================================================================

  describe('Legacy exports', () => {
    it('useCreateAbsence should work as alias for useAbsenceCreate', async () => {
      const newAbsence = mockFactories.absence()
      mockedApi.post.mockResolvedValueOnce(newAbsence)

      const { result } = renderHook(
        () => useCreateAbsence(),
        { wrapper: createWrapper() }
      )

      await act(async () => {
        result.current.mutate({
          person_id: 'person-1',
          start_date: '2024-02-01',
          end_date: '2024-02-07',
          absence_type: 'vacation',
        })
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(mockedApi.post).toHaveBeenCalledWith('/absences', expect.any(Object))
    })

    it('useUpdateAbsence should work as alias for useAbsenceUpdate', async () => {
      const updatedAbsence = mockFactories.absence()
      mockedApi.put.mockResolvedValueOnce(updatedAbsence)

      const { result } = renderHook(
        () => useUpdateAbsence(),
        { wrapper: createWrapper() }
      )

      await act(async () => {
        result.current.mutate({
          id: 'absence-1',
          data: { end_date: '2024-02-14' },
        })
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(mockedApi.put).toHaveBeenCalled()
    })

    it('useDeleteAbsence should work as alias for useAbsenceDelete', async () => {
      mockedApi.del.mockResolvedValueOnce(undefined)

      const { result } = renderHook(
        () => useDeleteAbsence(),
        { wrapper: createWrapper() }
      )

      await act(async () => {
        result.current.mutate('absence-1')
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(mockedApi.del).toHaveBeenCalledWith('/absences/absence-1')
    })
  })
})
