import { renderHook, waitFor, act } from '@testing-library/react'
import { useProcedures } from '@/hooks/useProcedures'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactNode } from 'react'

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
    global.fetch = jest.fn()
  })

  describe('Fetch Procedures', () => {
    it('should fetch all procedures', async () => {
      const mockProcedures = [
        { id: '1', name: 'LP', category: 'neuro', required_count: 5 },
        { id: '2', name: 'Intubation', category: 'airway', required_count: 10 },
      ]
      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ procedures: mockProcedures }),
      })

      const { result } = renderHook(() => useProcedures(), { wrapper })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))
      expect(result.current.data?.procedures).toHaveLength(2)
    })

    it('should filter by category', async () => {
      const mockProcedures = [
        { id: '1', name: 'LP', category: 'neuro' },
      ]
      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ procedures: mockProcedures }),
      })

      const { result } = renderHook(
        () => useProcedures({ category: 'neuro' }),
        { wrapper }
      )

      await waitFor(() => expect(result.current.isSuccess).toBe(true))
      expect(result.current.data?.procedures[0].category).toBe('neuro')
    })
  })

  describe('Log Procedure', () => {
    it('should log a completed procedure', async () => {
      const mockLog = {
        id: 'log-1',
        procedure_id: 'proc-1',
        resident_id: 'res-1',
        date: '2025-01-15',
        success: true,
      }
      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockLog,
      })

      const { result } = renderHook(() => useProcedures(), { wrapper })

      await act(async () => {
        await result.current.logProcedure({
          procedure_id: 'proc-1',
          resident_id: 'res-1',
          date: '2025-01-15',
          success: true,
        })
      })

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/procedures/log'),
        expect.objectContaining({
          method: 'POST',
        })
      )
    })

    it('should include supervisor information', async () => {
      const mockLog = {
        id: 'log-1',
        supervisor_id: 'faculty-1',
      }
      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockLog,
      })

      const { result } = renderHook(() => useProcedures(), { wrapper })

      await act(async () => {
        await result.current.logProcedure({
          procedure_id: 'proc-1',
          resident_id: 'res-1',
          supervisor_id: 'faculty-1',
        })
      })

      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          body: expect.stringContaining('faculty-1'),
        })
      )
    })
  })

  describe('Progress Tracking', () => {
    it('should fetch procedure progress for resident', async () => {
      const mockProgress = {
        resident_id: 'res-1',
        procedures: [
          { id: 'proc-1', completed: 3, required: 5, percentage: 0.6 },
          { id: 'proc-2', completed: 10, required: 10, percentage: 1.0 },
        ],
      }
      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockProgress,
      })

      const { result } = renderHook(
        () => useProcedures({ residentId: 'res-1' }),
        { wrapper }
      )

      await waitFor(() => expect(result.current.progress).toBeDefined())
      expect(result.current.progress?.procedures).toHaveLength(2)
    })

    it('should identify completed procedures', async () => {
      const mockProgress = {
        procedures: [
          { id: 'proc-1', completed: 5, required: 5, is_complete: true },
          { id: 'proc-2', completed: 3, required: 10, is_complete: false },
        ],
      }
      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockProgress,
      })

      const { result } = renderHook(
        () => useProcedures({ residentId: 'res-1' }),
        { wrapper }
      )

      await waitFor(() => {
        const complete = result.current.progress?.procedures.filter(
          (p) => p.is_complete
        )
        expect(complete).toHaveLength(1)
      })
    })
  })

  describe('Validation', () => {
    it('should validate procedure eligibility', async () => {
      const mockEligibility = {
        eligible: true,
        reason: 'Resident has required prerequisites',
      }
      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockEligibility,
      })

      const { result } = renderHook(() => useProcedures(), { wrapper })

      await act(async () => {
        const eligible = await result.current.checkEligibility(
          'res-1',
          'proc-1'
        )
        expect(eligible).toBe(true)
      })
    })

    it('should prevent duplicate logging', async () => {
      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 409,
        json: async () => ({ error: 'Procedure already logged for this date' }),
      })

      const { result } = renderHook(() => useProcedures(), { wrapper })

      await act(async () => {
        try {
          await result.current.logProcedure({
            procedure_id: 'proc-1',
            resident_id: 'res-1',
            date: '2025-01-15',
          })
        } catch (e: any) {
          expect(e.message).toContain('already logged')
        }
      })
    })
  })

  describe('Statistics', () => {
    it('should calculate procedure statistics', async () => {
      const mockStats = {
        total_procedures: 50,
        success_rate: 0.92,
        average_per_month: 4.2,
      }
      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockStats,
      })

      const { result } = renderHook(
        () => useProcedures({ residentId: 'res-1' }),
        { wrapper }
      )

      await waitFor(() => {
        expect(result.current.stats?.success_rate).toBe(0.92)
      })
    })

    it('should track procedures by category', async () => {
      const mockStats = {
        by_category: {
          neuro: 10,
          airway: 15,
          vascular: 8,
        },
      }
      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockStats,
      })

      const { result } = renderHook(
        () => useProcedures({ residentId: 'res-1' }),
        { wrapper }
      )

      await waitFor(() => {
        expect(result.current.stats?.by_category?.airway).toBe(15)
      })
    })
  })
})
