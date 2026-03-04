/**
 * useHealth Hook Tests
 *
 * Tests for health check hooks including liveness, readiness, and detailed health.
 */
import { renderHook, waitFor } from '@/test-utils'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactNode } from 'react'
import * as api from '@/lib/api'
import {
  useHealthLive,
  useHealthReady,
  useHealthDetailed,
  useHealthDashboard,
  useHealthDeep,
  useServiceHealth,
  type HealthLiveResponse,
  type HealthReadyResponse,
  type HealthDetailedResponse,
  type HealthDashboardResponse,
  type HealthDeepResponse,
  type ServiceHealth,
} from '@/hooks/useHealth'

// Mock the api module
jest.mock('@/lib/api')

const mockedApi = api as jest.Mocked<typeof api>

// Mock data
const mockLiveResponse: HealthLiveResponse = {
  status: 'healthy',
  timestamp: '2026-02-05T12:00:00Z',
  service: 'residency-scheduler-api',
}

const mockReadyResponse: HealthReadyResponse = {
  status: 'healthy',
  timestamp: '2026-02-05T12:00:00Z',
  database: true,
  redis: true,
}

const mockDetailedResponse: HealthDetailedResponse = {
  status: 'healthy',
  timestamp: '2026-02-05T12:00:00Z',
  services: {
    database: {
      status: 'healthy',
      latencyMs: 5,
      message: 'PostgreSQL connection active',
      lastChecked: '2026-02-05T12:00:00Z',
    },
    redis: {
      status: 'healthy',
      latencyMs: 2,
      message: 'Redis connection active',
      lastChecked: '2026-02-05T12:00:00Z',
    },
    celery: {
      status: 'healthy',
      latencyMs: 10,
      message: '3 workers active',
      lastChecked: '2026-02-05T12:00:00Z',
    },
  },
  uptimeSeconds: 86400,
  version: '1.0.0',
}

const mockDegradedResponse: HealthDetailedResponse = {
  status: 'degraded',
  timestamp: '2026-02-05T12:00:00Z',
  services: {
    database: {
      status: 'healthy',
      latencyMs: 5,
    },
    redis: {
      status: 'degraded',
      latencyMs: 150,
      message: 'High latency detected',
    },
    celery: {
      status: 'healthy',
      latencyMs: 10,
    },
  },
}

const mockServiceHealth: ServiceHealth = {
  status: 'healthy',
  latencyMs: 5,
  message: 'PostgreSQL connection active',
  lastChecked: '2026-02-05T12:00:00Z',
}

const mockDashboardResponse: HealthDashboardResponse = {
  overallStatus: 'healthy',
  timestamp: '2026-02-05T12:00:00Z',
  uptimeSeconds: 86400,
  version: '1.2.3',
  environment: 'test',
  summary: {
    totalServices: 3,
    healthyCount: 3,
    degradedCount: 0,
    unhealthyCount: 0,
    avgResponseTimeMs: 12,
  },
  metrics: {
    historyEnabled: true,
    historySize: 10,
    uptimePercentage: 99.9,
  },
  services: {
    database: {
      name: 'database',
      status: 'healthy',
      responseTimeMs: 8,
      lastCheck: '2026-02-05T12:00:00Z',
    },
    redis: {
      name: 'redis',
      status: 'healthy',
      responseTimeMs: 4,
      lastCheck: '2026-02-05T12:00:00Z',
    },
    celery: {
      name: 'celery',
      status: 'healthy',
      responseTimeMs: 20,
      lastCheck: '2026-02-05T12:00:00Z',
    },
  },
  alerts: [],
}

const mockDeepResponse: HealthDeepResponse = {
  status: 'healthy',
  timestamp: '2026-02-05T12:00:00Z',
  service: 'residency-scheduler-api',
  version: '1.2.3',
  checks: {
    database: {
      connected: true,
      status: 'ok',
      responseTimeMs: 12,
      timestamp: '2026-02-05T12:00:00Z',
      error: null,
      warning: null,
      details: null,
    },
    redis: {
      connected: true,
      status: 'ok',
      responseTimeMs: 4,
      timestamp: '2026-02-05T12:00:00Z',
      error: null,
      warning: null,
      details: null,
    },
  },
}

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

describe('useHealthLive', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch liveness status successfully', async () => {
    mockedApi.get.mockResolvedValueOnce(mockLiveResponse)

    const { result } = renderHook(
      () => useHealthLive(),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockLiveResponse)
    expect(result.current.data?.status).toBe('healthy')
    expect(mockedApi.get).toHaveBeenCalledWith('/health/live')
  })

  it('should show loading state while fetching', async () => {
    mockedApi.get.mockResolvedValueOnce(mockLiveResponse)

    const { result } = renderHook(
      () => useHealthLive(),
      { wrapper: createWrapper() }
    )

    expect(result.current.isLoading).toBe(true)

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })
  })

  it('should handle unhealthy status', async () => {
    const unhealthyResponse: HealthLiveResponse = {
      status: 'unhealthy',
      timestamp: '2026-02-05T12:00:00Z',
      service: 'residency-scheduler-api',
    }
    mockedApi.get.mockResolvedValueOnce(unhealthyResponse)

    const { result } = renderHook(
      () => useHealthLive(),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.status).toBe('unhealthy')
  })

  it('should respect enabled flag', async () => {
    const { result } = renderHook(
      () => useHealthLive({ enabled: false }),
      { wrapper: createWrapper() }
    )

    expect(result.current.isFetching).toBe(false)
    expect(mockedApi.get).not.toHaveBeenCalled()
  })

  it('should support custom refetch interval', async () => {
    mockedApi.get.mockResolvedValueOnce(mockLiveResponse)

    const { result } = renderHook(
      () => useHealthLive({ refetchInterval: 5000 }),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toBeDefined()
  })
})

describe('useHealthReady', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch readiness status successfully', async () => {
    mockedApi.get.mockResolvedValueOnce(mockReadyResponse)

    const { result } = renderHook(
      () => useHealthReady(),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockReadyResponse)
    expect(result.current.data?.database).toBe(true)
    expect(result.current.data?.redis).toBe(true)
    expect(mockedApi.get).toHaveBeenCalledWith('/health/ready')
  })

  it('should handle database down scenario', async () => {
    const notReadyResponse: HealthReadyResponse = {
      status: 'unhealthy',
      timestamp: '2026-02-05T12:00:00Z',
      database: false,
      redis: true,
    }
    mockedApi.get.mockResolvedValueOnce(notReadyResponse)

    const { result } = renderHook(
      () => useHealthReady(),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.status).toBe('unhealthy')
    expect(result.current.data?.database).toBe(false)
    expect(result.current.data?.redis).toBe(true)
  })

  it('should handle redis down scenario', async () => {
    const notReadyResponse: HealthReadyResponse = {
      status: 'unhealthy',
      timestamp: '2026-02-05T12:00:00Z',
      database: true,
      redis: false,
    }
    mockedApi.get.mockResolvedValueOnce(notReadyResponse)

    const { result } = renderHook(
      () => useHealthReady(),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.database).toBe(true)
    expect(result.current.data?.redis).toBe(false)
  })

  it('should respect enabled flag', async () => {
    const { result } = renderHook(
      () => useHealthReady({ enabled: false }),
      { wrapper: createWrapper() }
    )

    expect(result.current.isFetching).toBe(false)
    expect(mockedApi.get).not.toHaveBeenCalled()
  })

  it('should support custom refetch interval', async () => {
    mockedApi.get.mockResolvedValueOnce(mockReadyResponse)

    const { result } = renderHook(
      () => useHealthReady({ refetchInterval: 30000 }),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toBeDefined()
  })
})

describe('useHealthDetailed', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch detailed health status successfully', async () => {
    mockedApi.get.mockResolvedValueOnce(mockDetailedResponse)

    const { result } = renderHook(
      () => useHealthDetailed(),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockDetailedResponse)
    expect(result.current.data?.status).toBe('healthy')
    expect(result.current.data?.services.database.status).toBe('healthy')
    expect(result.current.data?.services.redis.status).toBe('healthy')
    expect(result.current.data?.services.celery.status).toBe('healthy')
    expect(mockedApi.get).toHaveBeenCalledWith('/health/detailed')
  })

  it('should include uptime and version info', async () => {
    mockedApi.get.mockResolvedValueOnce(mockDetailedResponse)

    const { result } = renderHook(
      () => useHealthDetailed(),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.uptimeSeconds).toBe(86400)
    expect(result.current.data?.version).toBe('1.0.0')
  })

  it('should handle degraded system status', async () => {
    mockedApi.get.mockResolvedValueOnce(mockDegradedResponse)

    const { result } = renderHook(
      () => useHealthDetailed(),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.status).toBe('degraded')
    expect(result.current.data?.services.redis.status).toBe('degraded')
    expect(result.current.data?.services.redis.message).toContain('High latency')
  })

  it('should include latency metrics for each service', async () => {
    mockedApi.get.mockResolvedValueOnce(mockDetailedResponse)

    const { result } = renderHook(
      () => useHealthDetailed(),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    const services = result.current.data?.services
    expect(services?.database.latencyMs).toBe(5)
    expect(services?.redis.latencyMs).toBe(2)
    expect(services?.celery.latencyMs).toBe(10)
  })

  it('should respect enabled flag', async () => {
    const { result } = renderHook(
      () => useHealthDetailed({ enabled: false }),
      { wrapper: createWrapper() }
    )

    expect(result.current.isFetching).toBe(false)
    expect(mockedApi.get).not.toHaveBeenCalled()
  })

  it('should support custom refetch interval', async () => {
    mockedApi.get.mockResolvedValueOnce(mockDetailedResponse)

    const { result } = renderHook(
      () => useHealthDetailed({ refetchInterval: 5000 }),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toBeDefined()
  })
})

describe('useHealthDashboard', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch dashboard health summary', async () => {
    mockedApi.get.mockResolvedValueOnce(mockDashboardResponse)

    const { result } = renderHook(
      () => useHealthDashboard(),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.overallStatus).toBe('healthy')
    expect(result.current.data?.summary.totalServices).toBe(3)
    expect(result.current.data?.services.database.status).toBe('healthy')
    expect(mockedApi.get).toHaveBeenCalledWith('/health/dashboard')
  })
})

describe('useHealthDeep', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch deep health checks', async () => {
    mockedApi.get.mockResolvedValueOnce(mockDeepResponse)

    const { result } = renderHook(
      () => useHealthDeep(),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.checks.database.connected).toBe(true)
    expect(result.current.data?.checks.redis.responseTimeMs).toBe(4)
    expect(mockedApi.get).toHaveBeenCalledWith('/health/deep')
  })
})

describe('useServiceHealth', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch database health status', async () => {
    mockedApi.get.mockResolvedValueOnce(mockServiceHealth)

    const { result } = renderHook(
      () => useServiceHealth('database'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockServiceHealth)
    expect(mockedApi.get).toHaveBeenCalledWith('/health/services/database')
  })

  it('should fetch redis health status', async () => {
    const redisHealth: ServiceHealth = {
      status: 'healthy',
      latencyMs: 2,
      message: 'Redis connection active',
    }
    mockedApi.get.mockResolvedValueOnce(redisHealth)

    const { result } = renderHook(
      () => useServiceHealth('redis'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.status).toBe('healthy')
    expect(mockedApi.get).toHaveBeenCalledWith('/health/services/redis')
  })

  it('should fetch celery health status', async () => {
    const celeryHealth: ServiceHealth = {
      status: 'healthy',
      latencyMs: 10,
      message: '3 workers active',
    }
    mockedApi.get.mockResolvedValueOnce(celeryHealth)

    const { result } = renderHook(
      () => useServiceHealth('celery'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.message).toContain('workers active')
    expect(mockedApi.get).toHaveBeenCalledWith('/health/services/celery')
  })

  it('should handle unhealthy service status', async () => {
    const unhealthyService: ServiceHealth = {
      status: 'unhealthy',
      message: 'Connection timeout',
    }
    mockedApi.get.mockResolvedValueOnce(unhealthyService)

    const { result } = renderHook(
      () => useServiceHealth('database'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.status).toBe('unhealthy')
    expect(result.current.data?.message).toContain('timeout')
  })

  it('should handle degraded service status', async () => {
    const degradedService: ServiceHealth = {
      status: 'degraded',
      latencyMs: 150,
      message: 'High latency detected',
    }
    mockedApi.get.mockResolvedValueOnce(degradedService)

    const { result } = renderHook(
      () => useServiceHealth('redis'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.status).toBe('degraded')
    expect(result.current.data?.latencyMs).toBe(150)
  })

  it('should respect enabled flag', async () => {
    const { result } = renderHook(
      () => useServiceHealth('database', { enabled: false }),
      { wrapper: createWrapper() }
    )

    expect(result.current.isFetching).toBe(false)
    expect(mockedApi.get).not.toHaveBeenCalled()
  })
})
