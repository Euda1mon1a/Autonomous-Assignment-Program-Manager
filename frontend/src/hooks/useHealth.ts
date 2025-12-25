/**
 * Health Check Hooks
 *
 * Hooks for monitoring system health status including
 * database, Redis, and Celery services.
 */
import { useQuery } from '@tanstack/react-query'
import { get } from '@/lib/api'

// ============================================================================
// Types
// ============================================================================

export interface ServiceHealth {
  status: 'healthy' | 'unhealthy' | 'degraded'
  latency_ms?: number
  message?: string
  last_checked?: string
}

export interface HealthLiveResponse {
  status: 'healthy' | 'unhealthy'
  timestamp: string
  service: string
}

export interface HealthReadyResponse {
  status: 'healthy' | 'unhealthy'
  timestamp: string
  database: boolean
  redis: boolean
}

export interface HealthDetailedResponse {
  status: 'healthy' | 'unhealthy' | 'degraded'
  timestamp: string
  services: {
    database: ServiceHealth
    redis: ServiceHealth
    celery: ServiceHealth
  }
  uptime_seconds?: number
  version?: string
}

// ============================================================================
// Query Keys
// ============================================================================

export const healthQueryKeys = {
  all: ['health'] as const,
  live: () => [...healthQueryKeys.all, 'live'] as const,
  ready: () => [...healthQueryKeys.all, 'ready'] as const,
  detailed: () => [...healthQueryKeys.all, 'detailed'] as const,
  service: (name: string) => [...healthQueryKeys.all, 'service', name] as const,
}

// ============================================================================
// Health Check Hooks
// ============================================================================

/**
 * Lightweight liveness check for the API.
 *
 * This hook performs a simple ping to verify the API is responding.
 * Useful for connection status indicators.
 *
 * @param options - Query options
 * @returns Query result with liveness status
 *
 * @example
 * ```tsx
 * function ConnectionIndicator() {
 *   const { data, isError } = useHealthLive();
 *   return <Badge color={isError ? 'red' : 'green'}>API</Badge>;
 * }
 * ```
 */
export function useHealthLive(options?: { enabled?: boolean; refetchInterval?: number }) {
  return useQuery({
    queryKey: healthQueryKeys.live(),
    queryFn: async (): Promise<HealthLiveResponse> => {
      const response = await get<HealthLiveResponse>('/health/live')
      return response
    },
    staleTime: 10_000, // 10 seconds
    refetchInterval: options?.refetchInterval ?? 30_000, // 30 seconds default
    retry: 1,
    enabled: options?.enabled ?? true,
  })
}

/**
 * Readiness check including database and Redis status.
 *
 * This hook checks if the application is ready to serve requests
 * by verifying critical dependencies.
 *
 * @param options - Query options
 * @returns Query result with readiness status
 *
 * @example
 * ```tsx
 * function ReadinessStatus() {
 *   const { data } = useHealthReady();
 *   return (
 *     <div>
 *       <p>Database: {data?.database ? 'OK' : 'DOWN'}</p>
 *       <p>Redis: {data?.redis ? 'OK' : 'DOWN'}</p>
 *     </div>
 *   );
 * }
 * ```
 */
export function useHealthReady(options?: { enabled?: boolean; refetchInterval?: number }) {
  return useQuery({
    queryKey: healthQueryKeys.ready(),
    queryFn: async (): Promise<HealthReadyResponse> => {
      const response = await get<HealthReadyResponse>('/health/ready')
      return response
    },
    staleTime: 15_000, // 15 seconds
    refetchInterval: options?.refetchInterval ?? 60_000, // 1 minute default
    retry: 1,
    enabled: options?.enabled ?? true,
  })
}

/**
 * Detailed health check with all service statuses.
 *
 * This hook fetches comprehensive health information including
 * latency metrics and service-specific details. Use sparingly
 * as it's more resource-intensive than liveness/readiness probes.
 *
 * @param options - Query options
 * @returns Query result with detailed health status
 *
 * @example
 * ```tsx
 * function HealthDashboard() {
 *   const { data, isLoading } = useHealthDetailed();
 *
 *   if (isLoading) return <Spinner />;
 *
 *   return (
 *     <div>
 *       <h2>System Health: {data?.status}</h2>
 *       {Object.entries(data?.services ?? {}).map(([name, svc]) => (
 *         <ServiceCard key={name} name={name} {...svc} />
 *       ))}
 *     </div>
 *   );
 * }
 * ```
 */
export function useHealthDetailed(options?: { enabled?: boolean; refetchInterval?: number }) {
  return useQuery({
    queryKey: healthQueryKeys.detailed(),
    queryFn: async (): Promise<HealthDetailedResponse> => {
      const response = await get<HealthDetailedResponse>('/health/detailed')
      return response
    },
    staleTime: 30_000, // 30 seconds
    refetchInterval: options?.refetchInterval ?? 120_000, // 2 minutes default
    retry: 1,
    enabled: options?.enabled ?? true,
  })
}

/**
 * Check health of a specific service.
 *
 * @param serviceName - Name of the service (database, redis, celery)
 * @param options - Query options
 * @returns Query result with service health status
 */
export function useServiceHealth(
  serviceName: 'database' | 'redis' | 'celery',
  options?: { enabled?: boolean }
) {
  return useQuery({
    queryKey: healthQueryKeys.service(serviceName),
    queryFn: async (): Promise<ServiceHealth> => {
      const response = await get<ServiceHealth>(`/health/services/${serviceName}`)
      return response
    },
    staleTime: 30_000,
    retry: 1,
    enabled: options?.enabled ?? true,
  })
}
