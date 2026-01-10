import { renderHook, waitFor } from '@testing-library/react'
import { useStrategies, useGameTheorySummary } from '@/hooks/useGameTheory'
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

describe('useGameTheory hooks', () => {
  beforeEach(() => {
    queryClient.clear()
    jest.clearAllMocks()
  })

  describe('useGameTheorySummary', () => {
    it('should fetch game theory summary', async () => {
      const mockData = {
        totalStrategies: 10,
        totalTournaments: 25,
        totalEvolutions: 5,
        activeSimulations: 2,
        recentWinners: ['Tit for Tat', 'Generous Tit for Tat'],
      }
      mockedApi.get.mockResolvedValueOnce(mockData)

      const { result } = renderHook(() => useGameTheorySummary(), { wrapper })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))
      expect(result.current.data?.totalStrategies).toBe(10)
      expect(result.current.data?.totalTournaments).toBe(25)
    })

    it('should handle API errors', async () => {
      const error = { message: 'Game theory service unavailable', status: 500 }
      mockedApi.get.mockRejectedValueOnce(error)

      const { result } = renderHook(() => useGameTheorySummary(), { wrapper })

      await waitFor(() => expect(result.current.isError).toBe(true))
      expect(result.current.error).toEqual(error)
    })
  })

  describe('useStrategies', () => {
    it('should fetch active strategies by default', async () => {
      const mockData = {
        strategies: [
          { id: '1', name: 'Tit for Tat', isActive: true },
          { id: '2', name: 'Always Cooperate', isActive: true },
        ],
        total: 2,
      }
      mockedApi.get.mockResolvedValueOnce(mockData)

      const { result } = renderHook(() => useStrategies(), { wrapper })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))
      expect(result.current.data?.strategies).toHaveLength(2)
      expect(mockedApi.get).toHaveBeenCalledWith(
        '/v1/game-theory/strategies?active_only=true'
      )
    })

    it('should fetch all strategies when activeOnly is false', async () => {
      const mockData = {
        strategies: [
          { id: '1', name: 'Tit for Tat', isActive: true },
          { id: '2', name: 'Inactive Strategy', isActive: false },
        ],
        total: 2,
      }
      mockedApi.get.mockResolvedValueOnce(mockData)

      const { result } = renderHook(() => useStrategies(false), { wrapper })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))
      expect(mockedApi.get).toHaveBeenCalledWith(
        '/v1/game-theory/strategies?active_only=false'
      )
    })
  })
})
