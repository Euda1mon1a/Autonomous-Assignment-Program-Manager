/**
 * useResilience Hook Tests
 *
 * Tests for resilience monitoring hooks including:
 * - System health status
 * - Vulnerability analysis
 * - Defense level monitoring
 * - Circuit breaker status
 * - MTF compliance
 * - Unified critical index
 * - Emergency coverage requests
 */
import { renderHook, waitFor } from '@/test-utils'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactNode } from 'react'
import * as api from '@/lib/api'
import * as resilienceApi from '@/api/resilience'
import {
  useSystemHealth,
  useVulnerabilityReport,
  useDefenseLevel,
  useUtilizationThreshold,
  useBurnoutRt,
  useEmergencyCoverage,
  useCircuitBreakers,
  useBreakerHealth,
  useMTFCompliance,
  useUnifiedCriticalIndex,
  useBlastRadiusReport,
  useStigmergyPatterns,
} from '@/hooks/useResilience'
import {
  HealthCheckResponse,
  VulnerabilityReportResponse,
  DefenseLevelResponse,
  UtilizationThresholdResponse,
  BurnoutRtResponse,
  EmergencyCoverageResponse,
  AllBreakersStatusResponse,
  BreakerHealthResponse,
  MTFComplianceResponse,
  UnifiedCriticalIndexResponse,
  BlastRadiusReportResponse,
  StigmergyPatternsResponse,
  OverallStatus,
  DefenseLevel,
  UtilizationLevel,
  CircuitState,
  BreakerSeverity,
} from '@/types/resilience'

// Mock the api modules
jest.mock('@/lib/api')
jest.mock('@/api/resilience')

const mockedApi = api as jest.Mocked<typeof api>
const mockedResilienceApi = resilienceApi as jest.Mocked<typeof resilienceApi>

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

// Mock data
const mockHealthResponse: HealthCheckResponse = {
  timestamp: '2026-02-06T12:00:00Z',
  overallStatus: OverallStatus.HEALTHY,
  utilization: {
    utilizationRate: 0.65,
    level: UtilizationLevel.GREEN,
    bufferRemaining: 0.35,
    waitTimeMultiplier: 1.2,
    safeCapacity: 100,
    currentDemand: 65,
    theoreticalCapacity: 120,
  },
  defenseLevel: DefenseLevel.PREVENTION,
  redundancyStatus: [
    {
      service: 'inpatient',
      status: 'healthy',
      available: 8,
      minimumRequired: 6,
      buffer: 2,
    },
  ],
  loadSheddingLevel: 'NORMAL' as any,
  activeFallbacks: [],
  crisisMode: false,
  n1Pass: true,
  n2Pass: true,
  phaseTransitionRisk: 'low',
  immediateActions: [],
  watchItems: [],
}

const mockVulnerabilityResponse: VulnerabilityReportResponse = {
  analyzedAt: '2026-02-06T12:00:00Z',
  periodStart: '2026-02-01T00:00:00Z',
  periodEnd: '2026-02-28T23:59:59Z',
  n1Pass: true,
  n2Pass: true,
  phaseTransitionRisk: 'low',
  n1Vulnerabilities: [],
  n2FatalPairs: [],
  mostCriticalFaculty: [
    {
      facultyId: 'faculty-1',
      facultyName: 'Dr. Smith',
      centralityScore: 0.85,
      servicesCovered: 5,
      uniqueCoverageSlots: 12,
      replacementDifficulty: 0.9,
      riskLevel: 'high',
    },
  ],
  recommendedActions: ['Cross-train additional faculty for critical services'],
}

const mockDefenseLevelResponse: DefenseLevelResponse = {
  level: DefenseLevel.PREVENTION,
  levelNumber: 1,
  description: 'Normal operations - all systems functioning',
  recommendedActions: ['Continue monitoring'],
  escalationThreshold: 0.9,
}

const mockUtilizationResponse: UtilizationThresholdResponse = {
  utilizationRate: 0.65,
  level: UtilizationLevel.GREEN,
  aboveThreshold: false,
  bufferRemaining: 0.35,
  waitTimeMultiplier: 1.2,
  message: 'Healthy buffer remaining',
  recommendations: ['No action needed'],
}

const mockBurnoutRtResponse: BurnoutRtResponse = {
  rt: 0.75,
  status: 'stable',
  secondaryCases: 2,
  timeWindowDays: 28,
  confidenceInterval: {
    lower: 0.65,
    upper: 0.85,
  },
  interventions: ['Continue current support programs'],
}

const mockEmergencyCoverageResponse: EmergencyCoverageResponse = {
  status: 'success',
  replacementsFound: 5,
  coverageGaps: 0,
  requiresManualReview: false,
  details: [
    {
      date: '2026-02-10',
      originalAssignment: 'Inpatient Ward',
      replacement: 'Dr. Johnson',
      status: 'replaced',
    },
  ],
}

const mockCircuitBreakersResponse: AllBreakersStatusResponse = {
  totalBreakers: 3,
  closedBreakers: 3,
  openBreakers: 0,
  halfOpenBreakers: 0,
  openBreakerNames: [],
  halfOpenBreakerNames: [],
  breakers: [
    {
      name: 'schedule_generation',
      state: CircuitState.CLOSED,
      failureRate: 0.05,
      successRate: 0.95,
      totalRequests: 100,
      successfulRequests: 95,
      failedRequests: 5,
      rejectedRequests: 0,
      consecutiveFailures: 0,
      consecutiveSuccesses: 10,
      openedAt: null,
      lastFailureTime: null,
      lastSuccessTime: '2026-02-06T11:00:00Z',
      recentTransitions: [],
    },
  ],
  overallHealth: 'healthy',
  recommendations: [],
  checkedAt: '2026-02-06T12:00:00Z',
}

const mockBreakerHealthResponse: BreakerHealthResponse = {
  totalBreakers: 3,
  metrics: {
    totalRequests: 300,
    totalFailures: 15,
    totalRejections: 0,
    overallFailureRate: 0.05,
    breakersAboveThreshold: 0,
    averageFailureRate: 0.05,
    maxFailureRate: 0.08,
    unhealthiestBreaker: null,
  },
  breakersNeedingAttention: [],
  trendAnalysis: 'stable',
  severity: BreakerSeverity.HEALTHY,
  recommendations: [],
  analyzedAt: '2026-02-06T12:00:00Z',
}

const mockMTFComplianceResponse: MTFComplianceResponse = {
  drrsCategory: 'C1',
  missionCapability: 'Fully mission capable',
  personnelRating: 'P1',
  capabilityRating: 'S1',
  circuitBreaker: null,
  executiveSummary: 'All systems operational',
  deficiencies: [],
  ironDomeStatus: 'green',
  severity: 'healthy',
}

const mockUnifiedCriticalIndexResponse: UnifiedCriticalIndexResponse = {
  analyzedAt: '2026-02-06T12:00:00Z',
  totalFaculty: 20,
  overallIndex: 0.45,
  riskLevel: 'moderate',
  riskConcentration: 0.3,
  criticalCount: 3,
  universalCriticalCount: 1,
  patternDistribution: {
    universal_critical: 1,
    structural_burnout: 2,
    low_risk: 17,
  },
  topPriority: ['faculty-1', 'faculty-2'],
  topCriticalFaculty: [
    {
      facultyId: 'faculty-1',
      facultyName: 'Dr. Smith',
      compositeIndex: 0.85,
      riskPattern: 'universal_critical' as any,
      confidence: 0.9,
      domainScores: {},
      domainAgreement: 0.95,
      leadingDomain: 'contingency',
      conflictDetails: [],
      recommendedInterventions: ['immediate_protection' as any],
      priorityRank: 1,
    },
  ],
  contributingFactors: {
    contingency: 0.4,
    epidemiology: 0.25,
    hub_centrality: 0.35,
  },
  trend: 'stable',
  topConcerns: ['Dr. Smith requires immediate protection'],
  recommendations: ['Implement cross-training program'],
  severity: 'moderate',
}

const mockBlastRadiusResponse: BlastRadiusReportResponse = {
  generatedAt: '2026-02-06T12:00:00Z',
  totalZones: 5,
  zonesHealthy: 4,
  zonesDegraded: 1,
  zonesCritical: 0,
  containmentActive: false,
  containmentLevel: 'none' as any,
  zonesIsolated: 0,
  activeBorrowingRequests: 0,
  pendingBorrowingRequests: 0,
  zoneReports: [
    {
      zoneId: 'zone-1',
      zoneName: 'Inpatient Ward',
      zoneType: 'inpatient' as any,
      checkedAt: '2026-02-06T12:00:00Z',
      status: 'green' as any,
      containmentLevel: 'none' as any,
      isSelfSufficient: true,
      hasSurplus: true,
      availableFaculty: 8,
      minimumRequired: 6,
      optimalRequired: 7,
      capacityRatio: 1.14,
      facultyBorrowed: 0,
      facultyLent: 1,
      netBorrowing: -1,
      activeIncidents: 0,
      servicesAffected: [],
      recommendations: [],
    },
  ],
  recommendations: [],
}

const mockStigmergyResponse: StigmergyPatternsResponse = {
  patterns: [
    {
      popularSlots: [['clinic_morning', 5.2]],
      unpopularSlots: [['call_weekend', -3.8]],
      neutralSlots: [['admin_afternoon', 0.1]],
      strongSwapPairs: [['faculty-1', 'faculty-2', 0.85]],
      totalPatterns: 3,
    },
  ],
  total: 1,
}

describe('useSystemHealth', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch system health successfully', async () => {
    mockedResilienceApi.fetchSystemHealth.mockResolvedValueOnce(mockHealthResponse)

    const { result } = renderHook(() => useSystemHealth(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockHealthResponse)
    expect(result.current.data?.overallStatus).toBe(OverallStatus.HEALTHY)
    expect(mockedResilienceApi.fetchSystemHealth).toHaveBeenCalledTimes(1)
  })

  it('should handle health check errors', async () => {
    const apiError = Object.assign(new Error('Health check failed'), {
      status: 500,
    })
    mockedResilienceApi.fetchSystemHealth.mockRejectedValueOnce(apiError)

    const { result } = renderHook(() => useSystemHealth(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(apiError)
  })

  it('should support custom options', async () => {
    mockedResilienceApi.fetchSystemHealth.mockResolvedValueOnce(mockHealthResponse)

    const { result } = renderHook(
      () => useSystemHealth({ enabled: false }),
      { wrapper: createWrapper() }
    )

    expect(result.current.isFetching).toBe(false)
    expect(mockedResilienceApi.fetchSystemHealth).not.toHaveBeenCalled()
  })
})

describe('useVulnerabilityReport', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch vulnerability report without params', async () => {
    mockedResilienceApi.fetchVulnerabilityReport.mockResolvedValueOnce(
      mockVulnerabilityResponse
    )

    const { result } = renderHook(() => useVulnerabilityReport(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockVulnerabilityResponse)
    expect(result.current.data?.n1Pass).toBe(true)
    expect(mockedResilienceApi.fetchVulnerabilityReport).toHaveBeenCalledWith(undefined)
  })

  it('should fetch vulnerability report with date range and N-2 flag', async () => {
    mockedResilienceApi.fetchVulnerabilityReport.mockResolvedValueOnce(
      mockVulnerabilityResponse
    )

    const params = {
      startDate: '2026-02-01',
      endDate: '2026-02-28',
      include_n2: true,
    }

    const { result } = renderHook(() => useVulnerabilityReport(params), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedResilienceApi.fetchVulnerabilityReport).toHaveBeenCalledWith(params)
  })

  it('should handle vulnerability report errors', async () => {
    const apiError = Object.assign(new Error('Analysis failed'), {
      status: 500,
    })
    mockedResilienceApi.fetchVulnerabilityReport.mockRejectedValueOnce(apiError)

    const { result } = renderHook(() => useVulnerabilityReport(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(apiError)
  })
})

describe('useDefenseLevel', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch defense level for valid coverage rate', async () => {
    mockedApi.post.mockResolvedValueOnce(mockDefenseLevelResponse)

    const { result } = renderHook(() => useDefenseLevel(0.85), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockDefenseLevelResponse)
    expect(mockedApi.post).toHaveBeenCalledWith('/resilience/defense-level', {
      coverageRate: 0.85,
    })
  })

  it('should not fetch when coverage rate is invalid', async () => {
    const { result } = renderHook(() => useDefenseLevel(-0.5), {
      wrapper: createWrapper(),
    })

    expect(result.current.isFetching).toBe(false)
    expect(mockedApi.post).not.toHaveBeenCalled()
  })

  it('should not fetch when coverage rate exceeds 1.0', async () => {
    const { result } = renderHook(() => useDefenseLevel(1.5), {
      wrapper: createWrapper(),
    })

    expect(result.current.isFetching).toBe(false)
    expect(mockedApi.post).not.toHaveBeenCalled()
  })

  it('should handle defense level errors', async () => {
    const apiError = Object.assign(new Error('Defense level calculation failed'), {
      status: 500,
    })
    mockedApi.post.mockRejectedValueOnce(apiError)

    const { result } = renderHook(() => useDefenseLevel(0.75), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(apiError)
  })
})

describe('useUtilizationThreshold', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch utilization threshold with required params', async () => {
    mockedApi.post.mockResolvedValueOnce(mockUtilizationResponse)

    const params = {
      available_faculty: 10,
      required_blocks: 65,
    }

    const { result } = renderHook(() => useUtilizationThreshold(params), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockUtilizationResponse)
    expect(mockedApi.post).toHaveBeenCalledWith(
      '/resilience/utilization-threshold',
      params
    )
  })

  it('should fetch utilization threshold with optional params', async () => {
    mockedApi.post.mockResolvedValueOnce(mockUtilizationResponse)

    const params = {
      available_faculty: 10,
      required_blocks: 65,
      blocks_per_faculty_per_day: 2,
      days_in_period: 28,
    }

    const { result } = renderHook(() => useUtilizationThreshold(params), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.post).toHaveBeenCalledWith(
      '/resilience/utilization-threshold',
      params
    )
  })

  it('should not fetch when available_faculty is zero', async () => {
    const params = {
      available_faculty: 0,
      required_blocks: 65,
    }

    const { result } = renderHook(() => useUtilizationThreshold(params), {
      wrapper: createWrapper(),
    })

    expect(result.current.isFetching).toBe(false)
    expect(mockedApi.post).not.toHaveBeenCalled()
  })

  it('should not fetch when required_blocks is negative', async () => {
    const params = {
      available_faculty: 10,
      required_blocks: -5,
    }

    const { result } = renderHook(() => useUtilizationThreshold(params), {
      wrapper: createWrapper(),
    })

    expect(result.current.isFetching).toBe(false)
    expect(mockedApi.post).not.toHaveBeenCalled()
  })
})

describe('useBurnoutRt', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch burnout Rt with provider IDs', async () => {
    mockedApi.post.mockResolvedValueOnce(mockBurnoutRtResponse)

    const providerIds = ['provider-1', 'provider-2', 'provider-3']

    const { result } = renderHook(() => useBurnoutRt(providerIds), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockBurnoutRtResponse)
    expect(mockedApi.post).toHaveBeenCalledWith('/resilience/burnout/rt', {
      burned_out_provider_ids: providerIds,
      time_window_days: 28,
    })
  })

  it('should fetch burnout Rt with custom time window', async () => {
    mockedApi.post.mockResolvedValueOnce(mockBurnoutRtResponse)

    const providerIds = ['provider-1']
    const timeWindow = 14

    const { result } = renderHook(() => useBurnoutRt(providerIds, timeWindow), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.post).toHaveBeenCalledWith('/resilience/burnout/rt', {
      burned_out_provider_ids: providerIds,
      time_window_days: timeWindow,
    })
  })

  it('should not fetch when provider IDs list is empty', async () => {
    const { result } = renderHook(() => useBurnoutRt([]), {
      wrapper: createWrapper(),
    })

    expect(result.current.isFetching).toBe(false)
    expect(mockedApi.post).not.toHaveBeenCalled()
  })

  it('should handle burnout Rt errors', async () => {
    const apiError = Object.assign(new Error('Rt calculation failed'), {
      status: 500,
    })
    mockedApi.post.mockRejectedValueOnce(apiError)

    const { result } = renderHook(() => useBurnoutRt(['provider-1']), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(apiError)
  })
})

describe('useEmergencyCoverage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should request emergency coverage successfully', async () => {
    mockedResilienceApi.requestEmergencyCoverage.mockResolvedValueOnce(
      mockEmergencyCoverageResponse
    )

    const { result } = renderHook(() => useEmergencyCoverage(), {
      wrapper: createWrapper(),
    })

    const request = {
      personId: 'person-123',
      startDate: '2026-02-10',
      endDate: '2026-02-15',
      reason: 'TDY assignment',
      isDeployment: false,
    }

    result.current.mutate(request)

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockEmergencyCoverageResponse)
    // Check that the function was called (React Query adds extra params)
    expect(mockedResilienceApi.requestEmergencyCoverage).toHaveBeenCalled()
    const callArgs = mockedResilienceApi.requestEmergencyCoverage.mock.calls[0][0]
    expect(callArgs).toEqual(request)
  })

  it('should handle emergency coverage errors', async () => {
    const apiError = Object.assign(new Error('Coverage request failed'), {
      status: 500,
    })
    mockedResilienceApi.requestEmergencyCoverage.mockRejectedValueOnce(apiError)

    const { result } = renderHook(() => useEmergencyCoverage(), {
      wrapper: createWrapper(),
    })

    const request = {
      personId: 'person-123',
      startDate: '2026-02-10',
      endDate: '2026-02-15',
      reason: 'Emergency',
      isDeployment: true,
    }

    result.current.mutate(request)

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(apiError)
  })

  it('should invalidate related queries on success', async () => {
    const queryClient = createTestQueryClient()
    const invalidateSpy = jest.spyOn(queryClient, 'invalidateQueries')

    mockedResilienceApi.requestEmergencyCoverage.mockResolvedValueOnce(
      mockEmergencyCoverageResponse
    )

    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    )

    const { result } = renderHook(() => useEmergencyCoverage(), { wrapper })

    const request = {
      personId: 'person-123',
      startDate: '2026-02-10',
      endDate: '2026-02-15',
      reason: 'Test',
      isDeployment: false,
    }

    result.current.mutate(request)

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['schedule'] })
    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['assignments'] })
    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['absences'] })
    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['validation'] })
  })
})

describe('useCircuitBreakers', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch all circuit breakers status', async () => {
    mockedApi.get.mockResolvedValueOnce(mockCircuitBreakersResponse)

    const { result } = renderHook(() => useCircuitBreakers(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockCircuitBreakersResponse)
    expect(result.current.data?.totalBreakers).toBe(3)
    expect(mockedApi.get).toHaveBeenCalledWith('/resilience/circuit-breakers')
  })

  it('should handle circuit breaker fetch errors', async () => {
    const apiError = Object.assign(new Error('Failed to fetch breakers'), {
      status: 500,
    })
    mockedApi.get.mockRejectedValueOnce(apiError)

    const { result } = renderHook(() => useCircuitBreakers(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(apiError)
  })

  it('should respect enabled flag', async () => {
    const { result } = renderHook(() => useCircuitBreakers({ enabled: false }), {
      wrapper: createWrapper(),
    })

    expect(result.current.isFetching).toBe(false)
    expect(mockedApi.get).not.toHaveBeenCalled()
  })
})

describe('useBreakerHealth', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch breaker health metrics', async () => {
    mockedApi.get.mockResolvedValueOnce(mockBreakerHealthResponse)

    const { result } = renderHook(() => useBreakerHealth(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockBreakerHealthResponse)
    expect(result.current.data?.severity).toBe(BreakerSeverity.HEALTHY)
    expect(mockedApi.get).toHaveBeenCalledWith('/resilience/circuit-breakers/health')
  })

  it('should handle breaker health errors', async () => {
    const apiError = Object.assign(new Error('Health metrics unavailable'), {
      status: 503,
    })
    mockedApi.get.mockRejectedValueOnce(apiError)

    const { result } = renderHook(() => useBreakerHealth(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(apiError)
  })
})

describe('useMTFCompliance', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch MTF compliance with circuit breaker check', async () => {
    mockedApi.get.mockResolvedValueOnce(mockMTFComplianceResponse)

    const { result } = renderHook(() => useMTFCompliance(true), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockMTFComplianceResponse)
    expect(result.current.data?.drrsCategory).toBe('C1')
    expect(mockedApi.get).toHaveBeenCalledWith(
      '/resilience/mtf-compliance?check_circuit_breaker=true'
    )
  })

  it('should fetch MTF compliance without circuit breaker check', async () => {
    mockedApi.get.mockResolvedValueOnce(mockMTFComplianceResponse)

    const { result } = renderHook(() => useMTFCompliance(false), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.get).toHaveBeenCalledWith(
      '/resilience/mtf-compliance?check_circuit_breaker=false'
    )
  })

  it('should default to checking circuit breaker', async () => {
    mockedApi.get.mockResolvedValueOnce(mockMTFComplianceResponse)

    const { result } = renderHook(() => useMTFCompliance(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.get).toHaveBeenCalledWith(
      '/resilience/mtf-compliance?check_circuit_breaker=true'
    )
  })

  it('should handle MTF compliance errors', async () => {
    const apiError = Object.assign(new Error('Compliance check failed'), {
      status: 500,
    })
    mockedApi.get.mockRejectedValueOnce(apiError)

    const { result } = renderHook(() => useMTFCompliance(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(apiError)
  })
})

describe('useUnifiedCriticalIndex', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch unified critical index with default topN', async () => {
    mockedApi.post.mockResolvedValueOnce(mockUnifiedCriticalIndexResponse)

    const { result } = renderHook(() => useUnifiedCriticalIndex(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockUnifiedCriticalIndexResponse)
    expect(mockedApi.post).toHaveBeenCalledWith('/resilience/unified-critical-index', {
      topN: 5,
      includeDetails: true,
    })
  })

  it('should fetch unified critical index with custom topN', async () => {
    mockedApi.post.mockResolvedValueOnce(mockUnifiedCriticalIndexResponse)

    const { result } = renderHook(() => useUnifiedCriticalIndex(10), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.post).toHaveBeenCalledWith('/resilience/unified-critical-index', {
      topN: 10,
      includeDetails: true,
    })
  })

  it('should handle unified critical index errors', async () => {
    const apiError = Object.assign(new Error('Index calculation failed'), {
      status: 500,
    })
    mockedApi.post.mockRejectedValueOnce(apiError)

    const { result } = renderHook(() => useUnifiedCriticalIndex(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(apiError)
  })
})

describe('useBlastRadiusReport', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch blast radius report', async () => {
    mockedApi.get.mockResolvedValueOnce(mockBlastRadiusResponse)

    const { result } = renderHook(() => useBlastRadiusReport(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockBlastRadiusResponse)
    expect(result.current.data?.totalZones).toBe(5)
    expect(mockedApi.get).toHaveBeenCalledWith('/resilience/tier2/zones/report')
  })

  it('should handle blast radius errors', async () => {
    const apiError = Object.assign(new Error('Zone report failed'), {
      status: 500,
    })
    mockedApi.get.mockRejectedValueOnce(apiError)

    const { result } = renderHook(() => useBlastRadiusReport(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(apiError)
  })
})

describe('useStigmergyPatterns', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch stigmergy patterns', async () => {
    mockedApi.get.mockResolvedValueOnce(mockStigmergyResponse)

    const { result } = renderHook(() => useStigmergyPatterns(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockStigmergyResponse)
    expect(result.current.data?.total).toBe(1)
    expect(mockedApi.get).toHaveBeenCalledWith(
      '/resilience/tier3/stigmergy/patterns'
    )
  })

  it('should handle stigmergy patterns errors', async () => {
    const apiError = Object.assign(new Error('Patterns analysis failed'), {
      status: 500,
    })
    mockedApi.get.mockRejectedValueOnce(apiError)

    const { result } = renderHook(() => useStigmergyPatterns(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(apiError)
  })
})
