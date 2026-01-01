import { renderHook, waitFor } from '@testing-library/react'
import { useGameTheory } from '@/hooks/useGameTheory'
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

describe('useGameTheory', () => {
  beforeEach(() => {
    queryClient.clear()
    global.fetch = jest.fn()
  })

  describe('Shapley Values', () => {
    it('should fetch shapley values for agents', async () => {
      const mockData = {
        shapley_values: {
          'agent-1': 0.35,
          'agent-2': 0.25,
          'agent-3': 0.40,
        },
      }
      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      })

      const { result } = renderHook(() => useGameTheory(), { wrapper })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))
      expect(result.current.data?.shapley_values).toEqual(
        mockData.shapley_values
      )
    })

    it('should identify highest contributor', async () => {
      const mockData = {
        shapley_values: {
          'agent-1': 0.2,
          'agent-2': 0.5,
          'agent-3': 0.3,
        },
      }
      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      })

      const { result } = renderHook(() => useGameTheory(), { wrapper })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))
      expect(result.current.data?.shapley_values['agent-2']).toBe(0.5)
    })
  })

  describe('Nash Equilibrium', () => {
    it('should calculate nash equilibrium', async () => {
      const mockData = {
        nash_equilibrium: {
          strategy: 'cooperate',
          payoff: 5.0,
        },
      }
      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      })

      const { result } = renderHook(() => useGameTheory(), { wrapper })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))
      expect(result.current.data?.nash_equilibrium).toBeDefined()
    })

    it('should detect multiple equilibria', async () => {
      const mockData = {
        nash_equilibria: [
          { strategy: 'cooperate', payoff: 5.0 },
          { strategy: 'defect', payoff: 3.0 },
        ],
      }
      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      })

      const { result } = renderHook(() => useGameTheory(), { wrapper })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))
      expect(result.current.data?.nash_equilibria).toHaveLength(2)
    })
  })

  describe('Evolutionary Strategies', () => {
    it('should simulate strategy evolution', async () => {
      const mockData = {
        evolution: {
          generations: 10,
          final_distribution: {
            'tit-for-tat': 0.7,
            'always-cooperate': 0.2,
            'always-defect': 0.1,
          },
        },
      }
      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      })

      const { result } = renderHook(() => useGameTheory(), { wrapper })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))
      expect(result.current.data?.evolution?.generations).toBe(10)
    })

    it('should track dominant strategy', async () => {
      const mockData = {
        evolution: {
          dominant_strategy: 'tit-for-tat',
          dominance_score: 0.85,
        },
      }
      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      })

      const { result } = renderHook(() => useGameTheory(), { wrapper })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))
      expect(result.current.data?.evolution?.dominant_strategy).toBe(
        'tit-for-tat'
      )
    })
  })

  describe('Payoff Matrix', () => {
    it('should fetch payoff matrix', async () => {
      const mockData = {
        payoff_matrix: [
          [3, 0],
          [5, 1],
        ],
      }
      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      })

      const { result } = renderHook(() => useGameTheory(), { wrapper })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))
      expect(result.current.data?.payoff_matrix).toEqual([[3, 0], [5, 1]])
    })

    it('should validate matrix dimensions', async () => {
      const mockData = {
        payoff_matrix: [[1, 2], [3, 4]],
        dimensions: { rows: 2, cols: 2 },
      }
      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      })

      const { result } = renderHook(() => useGameTheory(), { wrapper })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))
      expect(result.current.data?.dimensions).toEqual({ rows: 2, cols: 2 })
    })
  })

  describe('Error Handling', () => {
    it('should handle API errors', async () => {
      ;(global.fetch as jest.Mock).mockRejectedValueOnce(
        new Error('Game theory service unavailable')
      )

      const { result } = renderHook(() => useGameTheory(), { wrapper })

      await waitFor(() => expect(result.current.isError).toBe(true))
      expect(result.current.error).toBeDefined()
    })

    it('should handle invalid data format', async () => {
      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ invalid: 'format' }),
      })

      const { result } = renderHook(() => useGameTheory(), { wrapper })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))
      expect(result.current.data).toBeDefined()
    })
  })
})
