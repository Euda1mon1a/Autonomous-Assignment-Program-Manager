import { renderHook, waitFor } from '@testing-library/react'
import { useResilience } from '@/hooks/useResilience'
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

describe('useResilience', () => {
  beforeEach(() => {
    queryClient.clear()
    global.fetch = jest.fn()
  })

  describe('Fetching Resilience Data', () => {
    it('should fetch resilience metrics', async () => {
      const mockData = {
        utilization: 0.75,
        n_minus_1_viable: true,
        defense_level: 'GREEN',
      }
      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      })

      const { result } = renderHook(() => useResilience(), { wrapper })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))
      expect(result.current.data).toEqual(mockData)
    })

    it('should handle loading state', () => {
      ;(global.fetch as jest.Mock).mockImplementation(
        () => new Promise(() => {})
      )

      const { result } = renderHook(() => useResilience(), { wrapper })

      expect(result.current.isLoading).toBe(true)
      expect(result.current.data).toBeUndefined()
    })

    it('should handle error state', async () => {
      ;(global.fetch as jest.Mock).mockRejectedValueOnce(
        new Error('API Error')
      )

      const { result } = renderHook(() => useResilience(), { wrapper })

      await waitFor(() => expect(result.current.isError).toBe(true))
      expect(result.current.error).toBeDefined()
    })
  })

  describe('Defense Level Classification', () => {
    it('should classify GREEN defense level', async () => {
      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ utilization: 0.6, defense_level: 'GREEN' }),
      })

      const { result } = renderHook(() => useResilience(), { wrapper })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))
      expect(result.current.data?.defense_level).toBe('GREEN')
    })

    it('should classify YELLOW defense level', async () => {
      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ utilization: 0.75, defense_level: 'YELLOW' }),
      })

      const { result } = renderHook(() => useResilience(), { wrapper })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))
      expect(result.current.data?.defense_level).toBe('YELLOW')
    })

    it('should classify RED defense level', async () => {
      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ utilization: 0.9, defense_level: 'RED' }),
      })

      const { result } = renderHook(() => useResilience(), { wrapper })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))
      expect(result.current.data?.defense_level).toBe('RED')
    })
  })

  describe('N-1 Contingency', () => {
    it('should report n-1 viable status', async () => {
      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ n_minus_1_viable: true }),
      })

      const { result } = renderHook(() => useResilience(), { wrapper })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))
      expect(result.current.data?.n_minus_1_viable).toBe(true)
    })

    it('should report n-1 failure', async () => {
      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ n_minus_1_viable: false }),
      })

      const { result } = renderHook(() => useResilience(), { wrapper })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))
      expect(result.current.data?.n_minus_1_viable).toBe(false)
    })
  })

  describe('Auto-refresh', () => {
    it('should support refetch', async () => {
      ;(global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({ utilization: 0.7 }),
      })

      const { result } = renderHook(() => useResilience(), { wrapper })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      await result.current.refetch()

      expect(global.fetch).toHaveBeenCalledTimes(2)
    })
  })
})
