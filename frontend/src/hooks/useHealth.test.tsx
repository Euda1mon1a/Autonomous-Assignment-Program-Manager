/**
 * Tests for Health Check Hooks
 *
 * Tests system health monitoring including liveness probes,
 * readiness checks, and detailed service health status.
 */
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';
import {
  useHealthLive,
  useHealthReady,
  useHealthDetailed,
  useServiceHealth,
} from './useHealth';
import * as api from '@/lib/api';

// Mock the API module
jest.mock('@/lib/api');

const mockedApi = api as jest.Mocked<typeof api>;

// Test data
const mockHealthLive = {
  status: 'healthy' as const,
  timestamp: '2024-01-01T00:00:00Z',
  service: 'residency-scheduler-api',
};

const mockHealthReady = {
  status: 'healthy' as const,
  timestamp: '2024-01-01T00:00:00Z',
  database: true,
  redis: true,
};

const mockHealthDetailed = {
  status: 'healthy' as const,
  timestamp: '2024-01-01T00:00:00Z',
  services: {
    database: {
      status: 'healthy' as const,
      latencyMs: 12,
      message: 'Connected',
    },
    redis: {
      status: 'healthy' as const,
      latencyMs: 3,
      message: 'Connected',
    },
    celery: {
      status: 'healthy' as const,
      latencyMs: 5,
      message: 'Active',
    },
  },
  uptime_seconds: 86400,
  version: '1.0.0',
};

const mockServiceHealth = {
  status: 'healthy' as const,
  latencyMs: 12,
  message: 'Connected',
};

// Create wrapper with QueryClient
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

describe('useHealthLive', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('fetches liveness status successfully', async () => {
    mockedApi.get.mockResolvedValueOnce(mockHealthLive);

    const { result } = renderHook(() => useHealthLive(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(mockHealthLive);
    expect(mockedApi.get).toHaveBeenCalledWith('/health/live');
  });

  it('handles unhealthy status', async () => {
    const unhealthyResponse = {
      ...mockHealthLive,
      status: 'unhealthy' as const,
    };
    mockedApi.get.mockResolvedValueOnce(unhealthyResponse);

    const { result } = renderHook(() => useHealthLive(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.data?.status).toBe('unhealthy');
    });
  });

  it('respects enabled option', async () => {
    const { result } = renderHook(
      () => useHealthLive({ enabled: false }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(mockedApi.get).not.toHaveBeenCalled();
  });

  it('uses custom refetch interval', async () => {
    mockedApi.get.mockResolvedValue(mockHealthLive);

    renderHook(() => useHealthLive({ refetchInterval: 10000 }), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(mockedApi.get).toHaveBeenCalled();
    });
  });

  it('handles network errors', async () => {
    const error = new Error('Network error');
    mockedApi.get.mockRejectedValueOnce(error);

    const { result } = renderHook(() => useHealthLive(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toBeTruthy();
  });
});

describe('useHealthReady', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('fetches readiness status successfully', async () => {
    mockedApi.get.mockResolvedValueOnce(mockHealthReady);

    const { result } = renderHook(() => useHealthReady(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(mockHealthReady);
    expect(result.current.data?.database).toBe(true);
    expect(result.current.data?.redis).toBe(true);
    expect(mockedApi.get).toHaveBeenCalledWith('/health/ready');
  });

  it('indicates when database is not ready', async () => {
    const notReadyResponse = {
      ...mockHealthReady,
      status: 'unhealthy' as const,
      database: false,
    };
    mockedApi.get.mockResolvedValueOnce(notReadyResponse);

    const { result } = renderHook(() => useHealthReady(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.data?.database).toBe(false);
    });

    expect(result.current.data?.status).toBe('unhealthy');
  });

  it('indicates when redis is not ready', async () => {
    const notReadyResponse = {
      ...mockHealthReady,
      status: 'unhealthy' as const,
      redis: false,
    };
    mockedApi.get.mockResolvedValueOnce(notReadyResponse);

    const { result } = renderHook(() => useHealthReady(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.data?.redis).toBe(false);
    });
  });
});

describe('useHealthDetailed', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('fetches detailed health status successfully', async () => {
    mockedApi.get.mockResolvedValueOnce(mockHealthDetailed);

    const { result } = renderHook(() => useHealthDetailed(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(mockHealthDetailed);
    expect(result.current.data?.services.database.status).toBe('healthy');
    expect(result.current.data?.services.redis.status).toBe('healthy');
    expect(result.current.data?.services.celery.status).toBe('healthy');
    expect(mockedApi.get).toHaveBeenCalledWith('/health/detailed');
  });

  it('shows degraded status when one service is unhealthy', async () => {
    const degradedResponse = {
      ...mockHealthDetailed,
      status: 'degraded' as const,
      services: {
        ...mockHealthDetailed.services,
        celery: {
          status: 'unhealthy' as const,
          latencyMs: undefined,
          message: 'Connection failed',
        },
      },
    };
    mockedApi.get.mockResolvedValueOnce(degradedResponse);

    const { result } = renderHook(() => useHealthDetailed(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.data?.status).toBe('degraded');
    });

    expect(result.current.data?.services.celery.status).toBe('unhealthy');
  });

  it('includes uptime and version information', async () => {
    mockedApi.get.mockResolvedValueOnce(mockHealthDetailed);

    const { result } = renderHook(() => useHealthDetailed(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.data?.uptime_seconds).toBe(86400);
      expect(result.current.data?.version).toBe('1.0.0');
    });
  });

  it('shows latency metrics for each service', async () => {
    mockedApi.get.mockResolvedValueOnce(mockHealthDetailed);

    const { result } = renderHook(() => useHealthDetailed(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.data?.services.database.latencyMs).toBe(12);
      expect(result.current.data?.services.redis.latencyMs).toBe(3);
      expect(result.current.data?.services.celery.latencyMs).toBe(5);
    });
  });
});

describe('useServiceHealth', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('fetches database health successfully', async () => {
    mockedApi.get.mockResolvedValueOnce(mockServiceHealth);

    const { result } = renderHook(() => useServiceHealth('database'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(mockServiceHealth);
    expect(mockedApi.get).toHaveBeenCalledWith('/health/services/database');
  });

  it('fetches redis health successfully', async () => {
    const redisHealth = {
      ...mockServiceHealth,
      latencyMs: 3,
    };
    mockedApi.get.mockResolvedValueOnce(redisHealth);

    const { result } = renderHook(() => useServiceHealth('redis'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.data?.latencyMs).toBe(3);
    });

    expect(mockedApi.get).toHaveBeenCalledWith('/health/services/redis');
  });

  it('fetches celery health successfully', async () => {
    const celeryHealth = {
      ...mockServiceHealth,
      latencyMs: 5,
      message: 'Active',
    };
    mockedApi.get.mockResolvedValueOnce(celeryHealth);

    const { result } = renderHook(() => useServiceHealth('celery'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.data?.message).toBe('Active');
    });

    expect(mockedApi.get).toHaveBeenCalledWith('/health/services/celery');
  });

  it('handles service-specific errors', async () => {
    const error = { status: 503, message: 'Service unavailable' };
    mockedApi.get.mockRejectedValueOnce(error);

    const { result } = renderHook(() => useServiceHealth('database'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });
  });
});
