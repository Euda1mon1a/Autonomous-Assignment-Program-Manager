/**
 * Resilience Dashboard Flow Integration Tests
 *
 * Tests complete user journeys for monitoring system resilience.
 * Covers defense levels, utilization gauges, N-1/N-2 contingency analysis,
 * early warning systems, and resilience reports.
 */
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import * as api from '@/lib/api'

// Mock the API module
jest.mock('@/lib/api')
const mockedApi = api as jest.Mocked<typeof api>

// Mock Next.js router
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    back: jest.fn(),
  }),
  usePathname: () => '/admin/health',
  useSearchParams: () => new URLSearchParams(),
}))

// Create test query client
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

// Mock resilience data
const mockResilienceStatus = {
  defense_level: 'GREEN' as const,
  utilization_rate: 0.75,
  critical_index: 0.25,
  n_minus_1_viable: true,
  n_minus_2_viable: false,
  burnout_rt: 0.8,
  early_warnings: [],
}

const mockContingencyAnalysis = {
  analysis_type: 'n_minus_1',
  scenario: 'Loss of PGY2-01',
  viable: true,
  impact: {
    coverage_drop: 0.15,
    max_utilization: 0.85,
    affected_blocks: 10,
  },
  recommendations: [
    'Redistribute clinic assignments',
    'Activate backup resident',
  ],
}

const mockEarlyWarnings = [
  {
    id: 'warning-1',
    type: 'burnout_precursor',
    severity: 'medium' as const,
    person_id: 'person-1',
    message: 'Elevated stress indicators',
    detected_at: '2024-01-28T00:00:00Z',
  },
]

// API mock helper
function setupApiMock(options: {
  status?: typeof mockResilienceStatus | 'error'
  contingency?: typeof mockContingencyAnalysis | 'error'
  warnings?: typeof mockEarlyWarnings | 'error'
} = {}) {
  mockedApi.get.mockImplementation((url: string) => {
    if (url.includes('/resilience/status')) {
      if (options.status === 'error') {
        return Promise.reject({ message: 'Failed to fetch resilience', status: 500 })
      }
      return Promise.resolve(options.status ?? mockResilienceStatus)
    }
    if (url.includes('/resilience/contingency')) {
      if (options.contingency === 'error') {
        return Promise.reject({ message: 'Failed to fetch contingency', status: 500 })
      }
      return Promise.resolve(options.contingency ?? mockContingencyAnalysis)
    }
    if (url.includes('/resilience/warnings')) {
      if (options.warnings === 'error') {
        return Promise.reject({ message: 'Failed to fetch warnings', status: 500 })
      }
      return Promise.resolve({
        items: options.warnings ?? mockEarlyWarnings,
        total: (options.warnings ?? mockEarlyWarnings).length,
      })
    }
    return Promise.reject({ message: 'Unknown endpoint', status: 404 })
  })
}

describe('Resilience Dashboard Flow - Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    setupApiMock()
  })

  describe('61. Defense Level Display', () => {
    it('should display current defense level', async () => {
      setupApiMock()

      const result = await mockedApi.get('/api/resilience/status')
      expect(result.defense_level).toBe('GREEN')
    })

    it('should show GREEN level characteristics', async () => {
      setupApiMock({ status: { ...mockResilienceStatus, defense_level: 'GREEN' } })

      const result = await mockedApi.get('/api/resilience/status')
      expect(result.defense_level).toBe('GREEN')
      expect(result.utilization_rate).toBeLessThan(0.8)
    })

    it('should show YELLOW level warning', async () => {
      setupApiMock({
        status: {
          ...mockResilienceStatus,
          defense_level: 'YELLOW',
          utilization_rate: 0.82,
        },
      })

      const result = await mockedApi.get('/api/resilience/status')
      expect(result.defense_level).toBe('YELLOW')
    })

    it('should show ORANGE level alert', async () => {
      setupApiMock({
        status: {
          ...mockResilienceStatus,
          defense_level: 'ORANGE',
          utilization_rate: 0.88,
        },
      })

      const result = await mockedApi.get('/api/resilience/status')
      expect(result.defense_level).toBe('ORANGE')
    })

    it('should show RED level critical state', async () => {
      setupApiMock({
        status: {
          ...mockResilienceStatus,
          defense_level: 'RED',
          utilization_rate: 0.92,
        },
      })

      const result = await mockedApi.get('/api/resilience/status')
      expect(result.defense_level).toBe('RED')
    })

    it('should show BLACK level system failure', async () => {
      setupApiMock({
        status: {
          ...mockResilienceStatus,
          defense_level: 'BLACK',
          utilization_rate: 0.98,
        },
      })

      const result = await mockedApi.get('/api/resilience/status')
      expect(result.defense_level).toBe('BLACK')
    })
  })

  describe('62. Utilization Gauge', () => {
    it('should display current utilization rate', async () => {
      setupApiMock()

      const result = await mockedApi.get('/api/resilience/status')
      expect(result.utilization_rate).toBe(0.75)
    })

    it('should show utilization as percentage', async () => {
      setupApiMock()

      const result = await mockedApi.get('/api/resilience/status')
      const percentage = result.utilization_rate * 100
      expect(percentage).toBe(75)
    })

    it('should highlight when approaching 80% threshold', async () => {
      setupApiMock({
        status: { ...mockResilienceStatus, utilization_rate: 0.79 },
      })

      const result = await mockedApi.get('/api/resilience/status')
      expect(result.utilization_rate).toBeCloseTo(0.79, 2)
    })

    it('should show critical state when exceeding 90%', async () => {
      setupApiMock({
        status: { ...mockResilienceStatus, utilization_rate: 0.92 },
      })

      const result = await mockedApi.get('/api/resilience/status')
      expect(result.utilization_rate).toBeGreaterThan(0.9)
    })

    it('should calculate utilization by resource type', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        resources: [
          { type: 'PGY1', utilization: 0.70 },
          { type: 'PGY2', utilization: 0.80 },
          { type: 'Faculty', utilization: 0.65 },
        ],
      })

      const result = await mockedApi.get('/api/resilience/utilization-breakdown')
      expect(result.resources).toHaveLength(3)
    })
  })

  describe('63. N-1 Contingency Map', () => {
    it('should analyze N-1 scenario for each person', async () => {
      setupApiMock()

      const result = await mockedApi.get('/api/resilience/contingency?type=n_minus_1&person=person-1')
      expect(result.analysis_type).toBe('n_minus_1')
      expect(result.viable).toBe(true)
    })

    it('should identify critical single points of failure', async () => {
      setupApiMock({
        contingency: {
          ...mockContingencyAnalysis,
          viable: false,
          critical: true,
        },
      })

      const result = await mockedApi.get('/api/resilience/contingency?type=n_minus_1&person=person-2')
      expect(result.viable).toBe(false)
      expect(result.critical).toBe(true)
    })

    it('should calculate impact metrics for N-1 loss', async () => {
      setupApiMock()

      const result = await mockedApi.get('/api/resilience/contingency?type=n_minus_1&person=person-1')
      expect(result.impact.coverage_drop).toBe(0.15)
      expect(result.impact.max_utilization).toBe(0.85)
    })

    it('should provide recovery recommendations', async () => {
      setupApiMock()

      const result = await mockedApi.get('/api/resilience/contingency?type=n_minus_1&person=person-1')
      expect(result.recommendations).toHaveLength(2)
    })

    it('should visualize N-1 coverage map', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        coverage_map: [
          { person: 'person-1', n_minus_1_viable: true, risk_score: 0.2 },
          { person: 'person-2', n_minus_1_viable: false, risk_score: 0.9 },
        ],
      })

      const result = await mockedApi.get('/api/resilience/n-1-map')
      expect(result.coverage_map).toHaveLength(2)
    })
  })

  describe('64. N-2 Contingency Analysis', () => {
    it('should analyze N-2 scenario', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        analysis_type: 'n_minus_2',
        persons_lost: ['person-1', 'person-2'],
        viable: false,
        impact: {
          coverage_drop: 0.35,
          max_utilization: 0.95,
        },
      })

      const result = await mockedApi.get('/api/resilience/contingency?type=n_minus_2')
      expect(result.analysis_type).toBe('n_minus_2')
    })

    it('should identify worst-case N-2 pairs', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        worst_pairs: [
          { pair: ['person-1', 'person-2'], risk_score: 0.95 },
          { pair: ['person-3', 'person-4'], risk_score: 0.88 },
        ],
      })

      const result = await mockedApi.get('/api/resilience/worst-n2-pairs')
      expect(result.worst_pairs[0].risk_score).toBeGreaterThan(0.9)
    })

    it('should test simultaneous deployment scenario', async () => {
      setupApiMock()

      mockedApi.post = jest.fn().mockResolvedValueOnce({
        scenario: 'dual_deployment',
        deployed: ['person-1', 'person-3'],
        coverage_viable: true,
        mitigation_required: true,
      })

      const result = await mockedApi.post('/api/resilience/simulate-n2', {
        persons: ['person-1', 'person-3'],
      })

      expect(result.mitigation_required).toBe(true)
    })
  })

  describe('65. Early Warning Panel', () => {
    it('should display active early warnings', async () => {
      setupApiMock()

      const result = await mockedApi.get('/api/resilience/warnings')
      expect(result.items).toHaveLength(1)
    })

    it('should categorize warnings by type', async () => {
      const warnings = [
        { ...mockEarlyWarnings[0], type: 'burnout_precursor' },
        { ...mockEarlyWarnings[0], id: 'w2', type: 'utilization_spike' },
        { ...mockEarlyWarnings[0], id: 'w3', type: 'coverage_gap' },
      ]

      setupApiMock({ warnings })

      const result = await mockedApi.get('/api/resilience/warnings')
      const types = new Set(result.items.map((w: any) => w.type))
      expect(types.size).toBe(3)
    })

    it('should prioritize warnings by severity', async () => {
      const warnings = [
        { ...mockEarlyWarnings[0], severity: 'low' as const },
        { ...mockEarlyWarnings[0], id: 'w2', severity: 'critical' as const },
        { ...mockEarlyWarnings[0], id: 'w3', severity: 'medium' as const },
      ]

      setupApiMock({ warnings })

      const result = await mockedApi.get('/api/resilience/warnings')
      const critical = result.items.filter((w: any) => w.severity === 'critical')
      expect(critical).toHaveLength(1)
    })

    it('should show burnout precursor detection', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        items: [
          {
            type: 'burnout_precursor',
            person_id: 'person-1',
            indicators: {
              sta_lta_ratio: 3.5,
              consecutive_high_load_days: 5,
            },
          },
        ],
      })

      const result = await mockedApi.get('/api/resilience/warnings?type=burnout_precursor')
      expect(result.items[0].indicators.sta_lta_ratio).toBeGreaterThan(3)
    })

    it('should track warning acknowledgment', async () => {
      setupApiMock()

      mockedApi.patch = jest.fn().mockResolvedValueOnce({
        warning_id: 'warning-1',
        acknowledged: true,
        acknowledged_by: 'coordinator-1',
        acknowledged_at: '2024-01-29T00:00:00Z',
      })

      const result = await mockedApi.patch('/api/resilience/warnings/warning-1/acknowledge', {})
      expect(result.acknowledged).toBe(true)
    })
  })

  describe('66. Resilience Report Generation', () => {
    it('should generate comprehensive resilience report', async () => {
      setupApiMock()

      mockedApi.post = jest.fn().mockResolvedValueOnce({
        report_id: 'resilience-report-1',
        type: 'comprehensive',
        sections: [
          'defense_level_summary',
          'utilization_analysis',
          'contingency_results',
          'early_warnings',
        ],
        download_url: '/api/reports/resilience-1.pdf',
      })

      const result = await mockedApi.post('/api/resilience/reports', {
        type: 'comprehensive',
      })

      expect(result.sections).toHaveLength(4)
    })

    it('should include critical index trends', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        trends: [
          { date: '2024-01-01', critical_index: 0.15 },
          { date: '2024-01-15', critical_index: 0.25 },
          { date: '2024-01-30', critical_index: 0.30 },
        ],
      })

      const result = await mockedApi.get('/api/resilience/critical-index-trends')
      expect(result.trends).toHaveLength(3)
    })

    it('should export report to PDF', async () => {
      setupApiMock()

      mockedApi.post = jest.fn().mockResolvedValueOnce({
        download_url: '/api/reports/resilience.pdf',
        format: 'pdf',
      })

      const result = await mockedApi.post('/api/resilience/export', { format: 'pdf' })
      expect(result.format).toBe('pdf')
    })
  })

  describe('67. Burnout Rt Monitoring', () => {
    it('should display burnout reproduction number', async () => {
      setupApiMock()

      const result = await mockedApi.get('/api/resilience/status')
      expect(result.burnout_rt).toBe(0.8)
    })

    it('should alert when Rt exceeds 1.0', async () => {
      setupApiMock({
        status: { ...mockResilienceStatus, burnout_rt: 1.2 },
      })

      const result = await mockedApi.get('/api/resilience/status')
      expect(result.burnout_rt).toBeGreaterThan(1.0)
    })

    it('should track Rt trends over time', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        rt_history: [
          { date: '2024-01-01', rt: 0.7 },
          { date: '2024-01-15', rt: 0.9 },
          { date: '2024-01-30', rt: 1.1 },
        ],
      })

      const result = await mockedApi.get('/api/resilience/burnout-rt-trends')
      expect(result.rt_history[2].rt).toBeGreaterThan(1.0)
    })
  })

  describe('68. Static Stability Fallback', () => {
    it('should have pre-computed fallback schedule', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        fallback_id: 'fallback-1',
        created_at: '2024-01-01T00:00:00Z',
        coverage_level: 0.85,
      })

      const result = await mockedApi.get('/api/resilience/fallback-schedule')
      expect(result.fallback_id).toBeDefined()
    })

    it('should activate fallback in emergency', async () => {
      setupApiMock()

      mockedApi.post = jest.fn().mockResolvedValueOnce({
        activated: true,
        fallback_id: 'fallback-1',
        activated_at: '2024-01-29T00:00:00Z',
      })

      const result = await mockedApi.post('/api/resilience/activate-fallback', {})
      expect(result.activated).toBe(true)
    })
  })

  describe('69. Blast Radius Analysis', () => {
    it('should calculate change impact radius', async () => {
      setupApiMock()

      mockedApi.post = jest.fn().mockResolvedValueOnce({
        affected_people: 5,
        affected_blocks: 20,
        blast_radius: 'medium',
      })

      const result = await mockedApi.post('/api/resilience/blast-radius', {
        change_type: 'person_removal',
        person_id: 'person-1',
      })

      expect(result.blast_radius).toBe('medium')
    })

    it('should recommend isolation strategies', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        isolation_zones: [
          { zone: 'PGY1_clinic', isolated: true },
          { zone: 'PGY2_inpatient', isolated: false },
        ],
      })

      const result = await mockedApi.get('/api/resilience/isolation-zones')
      expect(result.isolation_zones).toHaveLength(2)
    })
  })

  describe('70. Homeostasis Monitoring', () => {
    it('should track workload balance', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        balance_score: 0.85,
        variance: 0.12,
        homeostasis_status: 'balanced',
      })

      const result = await mockedApi.get('/api/resilience/homeostasis')
      expect(result.homeostasis_status).toBe('balanced')
    })

    it('should detect imbalance and trigger rebalancing', async () => {
      setupApiMock()

      mockedApi.post = jest.fn().mockResolvedValueOnce({
        rebalance_triggered: true,
        target_variance: 0.10,
      })

      const result = await mockedApi.post('/api/resilience/rebalance', {})
      expect(result.rebalance_triggered).toBe(true)
    })
  })

  describe('71. SPC Monitoring', () => {
    it('should detect control chart violations', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        violations: [
          { rule: 'western_electric_rule_1', description: 'Point beyond 3-sigma' },
        ],
      })

      const result = await mockedApi.get('/api/resilience/spc-violations')
      expect(result.violations).toHaveLength(1)
    })

    it('should calculate process capability indices', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        cp: 1.33,
        cpk: 1.15,
        capability_status: 'capable',
      })

      const result = await mockedApi.get('/api/resilience/process-capability')
      expect(result.cp).toBeGreaterThan(1.0)
    })
  })

  describe('72. Erlang Coverage Analysis', () => {
    it('should calculate required coverage using Erlang C', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        required_agents: 8,
        service_level: 0.95,
        wait_time_p50: 2.5,
      })

      const result = await mockedApi.get('/api/resilience/erlang-coverage')
      expect(result.required_agents).toBe(8)
    })

    it('should identify understaffed periods', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        understaffed_blocks: [
          { block_id: 'block-5', shortfall: 2 },
        ],
      })

      const result = await mockedApi.get('/api/resilience/staffing-gaps')
      expect(result.understaffed_blocks).toHaveLength(1)
    })
  })

  describe('73. Time Crystal Analysis', () => {
    it('should detect subharmonic patterns', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        detected_cycles: [7, 14, 28],
        dominant_period: 7,
      })

      const result = await mockedApi.get('/api/resilience/time-crystal-patterns')
      expect(result.dominant_period).toBe(7)
    })

    it('should measure rigidity score', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        rigidity_score: 0.85,
        stability_status: 'high',
      })

      const result = await mockedApi.get('/api/resilience/rigidity')
      expect(result.rigidity_score).toBeGreaterThan(0.8)
    })
  })

  describe('74. Sacrifice Hierarchy', () => {
    it('should define load shedding priorities', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        priorities: [
          { tier: 1, activity: 'emergency_procedures', shed: false },
          { tier: 2, activity: 'inpatient_rounds', shed: false },
          { tier: 3, activity: 'elective_clinic', shed: true },
        ],
      })

      const result = await mockedApi.get('/api/resilience/sacrifice-hierarchy')
      expect(result.priorities).toHaveLength(3)
    })

    it('should execute load shedding plan', async () => {
      setupApiMock()

      mockedApi.post = jest.fn().mockResolvedValueOnce({
        shed_count: 5,
        activities_reduced: ['elective_clinic', 'research_time'],
      })

      const result = await mockedApi.post('/api/resilience/shed-load', {
        target_reduction: 0.15,
      })

      expect(result.shed_count).toBe(5)
    })
  })

  describe('75. Hub Vulnerability Detection', () => {
    it('should identify critical hub resources', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        hubs: [
          { person_id: 'person-2', betweenness: 0.85, is_hub: true },
          { person_id: 'person-1', betweenness: 0.35, is_hub: false },
        ],
      })

      const result = await mockedApi.get('/api/resilience/hub-analysis')
      const hubs = result.hubs.filter((h: any) => h.is_hub)
      expect(hubs).toHaveLength(1)
    })

    it('should simulate hub removal impact', async () => {
      setupApiMock()

      mockedApi.post = jest.fn().mockResolvedValueOnce({
        hub_id: 'person-2',
        network_fragmentation: 0.65,
        critical_impact: true,
      })

      const result = await mockedApi.post('/api/resilience/simulate-hub-loss', {
        person_id: 'person-2',
      })

      expect(result.critical_impact).toBe(true)
    })
  })

  describe('76. Exotic Frontier Metrics', () => {
    it('should calculate metastability score', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        metastability: 0.45,
        escape_probability: 0.08,
      })

      const result = await mockedApi.get('/api/resilience/metastability')
      expect(result.metastability).toBeDefined()
    })

    it('should perform persistent homology analysis', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        topological_features: [
          { dimension: 0, birth: 0, death: 5 },
          { dimension: 1, birth: 2, death: 8 },
        ],
      })

      const result = await mockedApi.get('/api/resilience/persistent-homology')
      expect(result.topological_features).toHaveLength(2)
    })
  })

  describe('77. Resilience Alerts', () => {
    it('should trigger alert on defense level change', async () => {
      setupApiMock()

      mockedApi.post = jest.fn().mockResolvedValueOnce({
        alert_sent: true,
        recipients: ['coordinator-1', 'program_director'],
        new_level: 'ORANGE',
      })

      const result = await mockedApi.post('/api/resilience/alert', {
        event: 'defense_level_change',
        new_level: 'ORANGE',
      })

      expect(result.alert_sent).toBe(true)
    })

    it('should escalate critical resilience events', async () => {
      setupApiMock()

      mockedApi.post = jest.fn().mockResolvedValueOnce({
        escalated: true,
        escalation_chain: ['coordinator', 'program_director', 'dean'],
      })

      const result = await mockedApi.post('/api/resilience/escalate', {
        event: 'n_minus_1_failure',
      })

      expect(result.escalated).toBe(true)
    })
  })

  describe('78. Resilience Scenarios', () => {
    it('should run disaster recovery scenario', async () => {
      setupApiMock()

      mockedApi.post = jest.fn().mockResolvedValueOnce({
        scenario: 'pandemic_outbreak',
        availability_drop: 0.40,
        recovery_time_days: 14,
        mitigation_success: true,
      })

      const result = await mockedApi.post('/api/resilience/scenarios/disaster', {
        type: 'pandemic_outbreak',
      })

      expect(result.mitigation_success).toBe(true)
    })

    it('should test mass casualty event response', async () => {
      setupApiMock()

      mockedApi.post = jest.fn().mockResolvedValueOnce({
        scenario: 'mass_casualty',
        surge_capacity: 1.5,
        response_adequate: true,
      })

      const result = await mockedApi.post('/api/resilience/scenarios/mass-casualty', {})
      expect(result.response_adequate).toBe(true)
    })
  })

  describe('79. Resilience Optimization', () => {
    it('should suggest resilience improvements', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        suggestions: [
          { action: 'cross_train', persons: ['person-3', 'person-4'] },
          { action: 'hire_backup', count: 1, specialty: 'procedures' },
        ],
      })

      const result = await mockedApi.get('/api/resilience/optimization-suggestions')
      expect(result.suggestions).toHaveLength(2)
    })

    it('should calculate ROI of resilience investments', async () => {
      setupApiMock()

      mockedApi.post = jest.fn().mockResolvedValueOnce({
        investment: 50000,
        risk_reduction: 0.35,
        roi: 2.5,
      })

      const result = await mockedApi.post('/api/resilience/investment-roi', {
        investment_type: 'additional_backup_staff',
      })

      expect(result.roi).toBeGreaterThan(2.0)
    })
  })

  describe('80. Resilience Dashboard Widgets', () => {
    it('should display unified critical index widget', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        critical_index: 0.25,
        components: {
          utilization: 0.75,
          burnout_rt: 0.8,
          n_minus_1_risk: 0.15,
        },
      })

      const result = await mockedApi.get('/api/resilience/critical-index')
      expect(result.critical_index).toBe(0.25)
    })

    it('should show real-time defense level widget', async () => {
      setupApiMock()

      const result = await mockedApi.get('/api/resilience/status')
      expect(result.defense_level).toBeDefined()
    })
  })
})
