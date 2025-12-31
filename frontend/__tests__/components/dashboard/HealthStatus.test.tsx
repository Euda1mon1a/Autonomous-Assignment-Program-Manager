/**
 * Tests for HealthStatus Dashboard Widget
 *
 * Tests the system health status widget which displays:
 * - Connection status (API reachability)
 * - Database health
 * - Redis health
 * - Overall system status
 */

import { render, screen, waitFor } from '@/test-utils'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { HealthStatus } from '@/components/dashboard/HealthStatus'

// Mock the useHealthReady hook
jest.mock('@/hooks/useHealth', () => ({
  useHealthReady: jest.fn(),
}))

import { useHealthReady } from '@/hooks/useHealth'

const mockedUseHealthReady = useHealthReady as jest.MockedFunction<typeof useHealthReady>

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

describe('HealthStatus', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Loading State', () => {
    it('should show loading skeleton when fetching data', () => {
      mockedUseHealthReady.mockReturnValue({
        data: undefined,
        isLoading: true,
        isError: false,
        error: null,
      } as ReturnType<typeof useHealthReady>)

      render(<HealthStatus />, { wrapper: createWrapper() })

      expect(screen.getByText('System Health')).toBeInTheDocument()
      // Should show loading skeletons
      const skeletons = document.querySelectorAll('.animate-pulse')
      expect(skeletons.length).toBeGreaterThan(0)
    })
  })

  describe('Error State', () => {
    it('should show error message when API is unreachable', () => {
      mockedUseHealthReady.mockReturnValue({
        data: undefined,
        isLoading: false,
        isError: true,
        error: new Error('Network error'),
      } as ReturnType<typeof useHealthReady>)

      render(<HealthStatus />, { wrapper: createWrapper() })

      expect(screen.getByText('Connection Failed')).toBeInTheDocument()
      expect(screen.getByText('Disconnected')).toBeInTheDocument()
    })

    it('should display the error message from the error object', () => {
      mockedUseHealthReady.mockReturnValue({
        data: undefined,
        isLoading: false,
        isError: true,
        error: new Error('Unable to reach API server'),
      } as ReturnType<typeof useHealthReady>)

      render(<HealthStatus />, { wrapper: createWrapper() })

      expect(screen.getByText('Unable to reach API server')).toBeInTheDocument()
    })
  })

  describe('Healthy State', () => {
    const healthyData = {
      status: 'healthy' as const,
      timestamp: new Date().toISOString(),
      database: true,
      redis: true,
    }

    it('should show all systems operational when healthy', () => {
      mockedUseHealthReady.mockReturnValue({
        data: healthyData,
        isLoading: false,
        isError: false,
        error: null,
      } as ReturnType<typeof useHealthReady>)

      render(<HealthStatus />, { wrapper: createWrapper() })

      expect(screen.getByText('All Systems Operational')).toBeInTheDocument()
      expect(screen.getByText('Connected')).toBeInTheDocument()
    })

    it('should show database as healthy', () => {
      mockedUseHealthReady.mockReturnValue({
        data: healthyData,
        isLoading: false,
        isError: false,
        error: null,
      } as ReturnType<typeof useHealthReady>)

      render(<HealthStatus />, { wrapper: createWrapper() })

      expect(screen.getByText('Database')).toBeInTheDocument()
      expect(screen.getAllByText('Healthy')[0]).toBeInTheDocument()
    })

    it('should show redis as healthy', () => {
      mockedUseHealthReady.mockReturnValue({
        data: healthyData,
        isLoading: false,
        isError: false,
        error: null,
      } as ReturnType<typeof useHealthReady>)

      render(<HealthStatus />, { wrapper: createWrapper() })

      expect(screen.getByText('Cache (Redis)')).toBeInTheDocument()
    })

    it('should display last checked timestamp', () => {
      mockedUseHealthReady.mockReturnValue({
        data: healthyData,
        isLoading: false,
        isError: false,
        error: null,
      } as ReturnType<typeof useHealthReady>)

      render(<HealthStatus />, { wrapper: createWrapper() })

      expect(screen.getByText(/Last checked:/)).toBeInTheDocument()
    })
  })

  describe('Unhealthy State', () => {
    it('should show system issues when database is down', () => {
      mockedUseHealthReady.mockReturnValue({
        data: {
          status: 'unhealthy' as const,
          timestamp: new Date().toISOString(),
          database: false,
          redis: true,
        },
        isLoading: false,
        isError: false,
        error: null,
      } as ReturnType<typeof useHealthReady>)

      render(<HealthStatus />, { wrapper: createWrapper() })

      expect(screen.getByText('System Issues Detected')).toBeInTheDocument()
    })

    it('should show unhealthy status for database', () => {
      mockedUseHealthReady.mockReturnValue({
        data: {
          status: 'unhealthy' as const,
          timestamp: new Date().toISOString(),
          database: false,
          redis: true,
        },
        isLoading: false,
        isError: false,
        error: null,
      } as ReturnType<typeof useHealthReady>)

      render(<HealthStatus />, { wrapper: createWrapper() })

      expect(screen.getByText('Unhealthy')).toBeInTheDocument()
    })

    it('should show system issues when redis is down', () => {
      mockedUseHealthReady.mockReturnValue({
        data: {
          status: 'unhealthy' as const,
          timestamp: new Date().toISOString(),
          database: true,
          redis: false,
        },
        isLoading: false,
        isError: false,
        error: null,
      } as ReturnType<typeof useHealthReady>)

      render(<HealthStatus />, { wrapper: createWrapper() })

      expect(screen.getByText('System Issues Detected')).toBeInTheDocument()
    })
  })

  describe('Partial Unhealthy State', () => {
    it('should show connected but with issues when API responds but services are down', () => {
      mockedUseHealthReady.mockReturnValue({
        data: {
          status: 'unhealthy' as const,
          timestamp: new Date().toISOString(),
          database: false,
          redis: false,
        },
        isLoading: false,
        isError: false,
        error: null,
      } as ReturnType<typeof useHealthReady>)

      render(<HealthStatus />, { wrapper: createWrapper() })

      // Still connected to API, just services are down
      expect(screen.getByText('Connected')).toBeInTheDocument()
      expect(screen.getByText('System Issues Detected')).toBeInTheDocument()
    })
  })

  describe('Refresh Behavior', () => {
    it('should pass correct refetch interval to hook', () => {
      mockedUseHealthReady.mockReturnValue({
        data: {
          status: 'healthy' as const,
          timestamp: new Date().toISOString(),
          database: true,
          redis: true,
        },
        isLoading: false,
        isError: false,
        error: null,
      } as ReturnType<typeof useHealthReady>)

      render(<HealthStatus />, { wrapper: createWrapper() })

      // Verify hook was called with refetch interval
      expect(mockedUseHealthReady).toHaveBeenCalledWith(
        expect.objectContaining({
          refetchInterval: 30000,
        })
      )
    })
  })
})
