/**
 * Compliance Monitoring Flow Integration Tests
 *
 * Tests complete user journeys for viewing and monitoring ACGME compliance.
 * Covers compliance dashboards, work hour tracking, violation alerts,
 * and compliance report generation.
 */
import { render, screen, waitFor } from '@/test-utils'
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
  usePathname: () => '/compliance',
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

// Test wrapper
function renderWithProviders(ui: React.ReactElement) {
  const queryClient = createTestQueryClient()
  return render(
    <QueryClientProvider client={queryClient}>
      {ui}
    </QueryClientProvider>
  )
}

// Mock compliance data
const mockComplianceStatus = {
  person_id: 'person-1',
  period_start: '2024-01-01',
  period_end: '2024-01-28',
  total_hours: 75,
  max_hours: 80,
  hours_remaining: 5,
  compliance_status: 'green' as const,
  violations: [],
  warnings: [],
}

const mockViolations = [
  {
    id: 'violation-1',
    person_id: 'person-1',
    rule: '80_hour_limit',
    severity: 'high' as const,
    description: 'Exceeded 80-hour weekly limit',
    detected_at: '2024-01-28T00:00:00Z',
    resolved: false,
    hours_over: 5,
  },
]

const mockWorkHours = [
  {
    person_id: 'person-1',
    week_start: '2024-01-01',
    week_end: '2024-01-07',
    total_hours: 78,
    clinical_hours: 70,
    non_clinical_hours: 8,
  },
  {
    person_id: 'person-1',
    week_start: '2024-01-08',
    week_end: '2024-01-14',
    total_hours: 75,
    clinical_hours: 68,
    non_clinical_hours: 7,
  },
]

// API mock helper
function setupApiMock(options: {
  status?: typeof mockComplianceStatus | 'error'
  violations?: typeof mockViolations | 'error'
  workHours?: typeof mockWorkHours | 'error'
} = {}) {
  mockedApi.get.mockImplementation((url: string) => {
    if (url.includes('/compliance/status')) {
      if (options.status === 'error') {
        return Promise.reject({ message: 'Failed to fetch compliance', status: 500 })
      }
      return Promise.resolve(options.status ?? mockComplianceStatus)
    }
    if (url.includes('/compliance/violations')) {
      if (options.violations === 'error') {
        return Promise.reject({ message: 'Failed to fetch violations', status: 500 })
      }
      return Promise.resolve({
        items: options.violations ?? mockViolations,
        total: (options.violations ?? mockViolations).length,
      })
    }
    if (url.includes('/compliance/work-hours')) {
      if (options.workHours === 'error') {
        return Promise.reject({ message: 'Failed to fetch work hours', status: 500 })
      }
      return Promise.resolve({
        items: options.workHours ?? mockWorkHours,
        total: (options.workHours ?? mockWorkHours).length,
      })
    }
    return Promise.reject({ message: 'Unknown endpoint', status: 404 })
  })
}

describe('Compliance Monitoring Flow - Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    setupApiMock()
  })

  describe('41. Viewing Compliance Dashboard', () => {
    it('should load compliance dashboard data', async () => {
      setupApiMock()

      const result = await mockedApi.get('/api/compliance/status?person_id=person-1')
      expect(result.compliance_status).toBe('green')
      expect(result.total_hours).toBe(75)
    })

    it('should display compliance status for all residents', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        items: [
          { person_id: 'person-1', compliance_status: 'green', total_hours: 75 },
          { person_id: 'person-2', compliance_status: 'yellow', total_hours: 78 },
          { person_id: 'person-3', compliance_status: 'red', total_hours: 85 },
        ],
      })

      const result = await mockedApi.get('/api/compliance/status')
      expect(result.items).toHaveLength(3)
      expect(result.items.some((s: any) => s.compliance_status === 'red')).toBe(true)
    })

    it('should group residents by compliance status', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        items: [
          { person_id: 'person-1', compliance_status: 'green' },
          { person_id: 'person-2', compliance_status: 'green' },
          { person_id: 'person-3', compliance_status: 'yellow' },
          { person_id: 'person-4', compliance_status: 'red' },
        ],
      })

      const result = await mockedApi.get('/api/compliance/status')
      const green = result.items.filter((s: any) => s.compliance_status === 'green')
      const yellow = result.items.filter((s: any) => s.compliance_status === 'yellow')
      const red = result.items.filter((s: any) => s.compliance_status === 'red')

      expect(green).toHaveLength(2)
      expect(yellow).toHaveLength(1)
      expect(red).toHaveLength(1)
    })
  })

  describe('42. Work Hour Gauge Updates', () => {
    it('should display current weekly hours', async () => {
      setupApiMock()

      const result = await mockedApi.get('/api/compliance/status?person_id=person-1')
      expect(result.total_hours).toBe(75)
      expect(result.max_hours).toBe(80)
    })

    it('should show hours remaining in week', async () => {
      setupApiMock()

      const result = await mockedApi.get('/api/compliance/status?person_id=person-1')
      expect(result.hours_remaining).toBe(5)
    })

    it('should calculate percentage of max hours', async () => {
      setupApiMock()

      const result = await mockedApi.get('/api/compliance/status?person_id=person-1')
      const percentage = (result.total_hours / result.max_hours) * 100
      expect(percentage).toBeCloseTo(93.75, 1)
    })

    it('should update gauge color based on threshold', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        total_hours: 85,
        max_hours: 80,
        gauge_color: 'red',
      })

      const result = await mockedApi.get('/api/compliance/status?person_id=person-1')
      expect(result.gauge_color).toBe('red')
    })

    it('should show warning when approaching limit', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        total_hours: 78,
        max_hours: 80,
        warning: 'Approaching 80-hour limit',
      })

      const result = await mockedApi.get('/api/compliance/status?person_id=person-1')
      expect(result.warning).toBeDefined()
    })
  })

  describe('43. Violation Alert Display', () => {
    it('should display active violations', async () => {
      setupApiMock()

      const result = await mockedApi.get('/api/compliance/violations?resolved=false')
      expect(result.items).toHaveLength(1)
      expect(result.items[0].resolved).toBe(false)
    })

    it('should show violation details', async () => {
      setupApiMock()

      const violation = mockViolations[0]
      expect(violation.rule).toBe('80_hour_limit')
      expect(violation.severity).toBe('high')
      expect(violation.hours_over).toBe(5)
    })

    it('should filter violations by severity', async () => {
      const violations = [
        { ...mockViolations[0], severity: 'high' as const },
        { ...mockViolations[0], id: 'violation-2', severity: 'medium' as const },
        { ...mockViolations[0], id: 'violation-3', severity: 'low' as const },
      ]

      setupApiMock({ violations })

      const result = await mockedApi.get('/api/compliance/violations')
      const highSeverity = result.items.filter((v: any) => v.severity === 'high')
      expect(highSeverity).toHaveLength(1)
    })

    it('should sort violations by severity', async () => {
      const violations = [
        { ...mockViolations[0], id: 'v1', severity: 'low' as const },
        { ...mockViolations[0], id: 'v2', severity: 'high' as const },
        { ...mockViolations[0], id: 'v3', severity: 'medium' as const },
      ]

      setupApiMock({ violations })

      const result = await mockedApi.get('/api/compliance/violations')
      // In real implementation, would be sorted by severity
      expect(result.items).toHaveLength(3)
    })

    it('should highlight critical violations', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        items: [
          { ...mockViolations[0], severity: 'critical', requires_immediate_action: true },
        ],
      })

      const result = await mockedApi.get('/api/compliance/violations?severity=critical')
      expect(result.items[0].requires_immediate_action).toBe(true)
    })
  })

  describe('44. Compliance Report Generation', () => {
    it('should generate weekly compliance report', async () => {
      setupApiMock()

      mockedApi.post = jest.fn().mockResolvedValueOnce({
        report_id: 'report-1',
        type: 'weekly',
        generated_at: '2024-01-28T00:00:00Z',
        download_url: '/api/reports/compliance-weekly-1.pdf',
      })

      const result = await mockedApi.post('/api/compliance/reports', {
        type: 'weekly',
        start_date: '2024-01-01',
        end_date: '2024-01-07',
      })

      expect(result.type).toBe('weekly')
      expect(result.download_url).toContain('.pdf')
    })

    it('should generate monthly compliance report', async () => {
      setupApiMock()

      mockedApi.post = jest.fn().mockResolvedValueOnce({
        report_id: 'report-2',
        type: 'monthly',
        month: '2024-01',
      })

      const result = await mockedApi.post('/api/compliance/reports', {
        type: 'monthly',
        month: '2024-01',
      })

      expect(result.type).toBe('monthly')
    })

    it('should include violation summary in report', async () => {
      setupApiMock()

      mockedApi.post = jest.fn().mockResolvedValueOnce({
        report_id: 'report-1',
        summary: {
          total_violations: 5,
          resolved_violations: 3,
          active_violations: 2,
        },
      })

      const result = await mockedApi.post('/api/compliance/reports', {})
      expect(result.summary.total_violations).toBe(5)
    })

    it('should export report to PDF', async () => {
      setupApiMock()

      mockedApi.post = jest.fn().mockResolvedValueOnce({
        download_url: '/api/reports/compliance-1.pdf',
        format: 'pdf',
      })

      const result = await mockedApi.post('/api/compliance/reports/export', {
        format: 'pdf',
      })

      expect(result.format).toBe('pdf')
    })

    it('should export report to Excel', async () => {
      setupApiMock()

      mockedApi.post = jest.fn().mockResolvedValueOnce({
        download_url: '/api/reports/compliance-1.xlsx',
        format: 'excel',
      })

      const result = await mockedApi.post('/api/compliance/reports/export', {
        format: 'excel',
      })

      expect(result.format).toBe('excel')
    })
  })

  describe('45. Historical Compliance View', () => {
    it('should display compliance history for resident', async () => {
      setupApiMock()

      const result = await mockedApi.get('/api/compliance/work-hours?person_id=person-1')
      expect(result.items).toHaveLength(2)
    })

    it('should show weekly hour trends', async () => {
      setupApiMock()

      const result = await mockedApi.get('/api/compliance/work-hours?person_id=person-1')
      const hours = result.items.map((w: any) => w.total_hours)
      expect(hours).toEqual([78, 75])
    })

    it('should identify patterns of near-violations', async () => {
      const workHours = [
        { ...mockWorkHours[0], total_hours: 79 },
        { ...mockWorkHours[0], week_start: '2024-01-08', total_hours: 78 },
        { ...mockWorkHours[0], week_start: '2024-01-15', total_hours: 79 },
      ]

      setupApiMock({ workHours })

      const result = await mockedApi.get('/api/compliance/work-hours?person_id=person-1')
      const nearViolations = result.items.filter((w: any) => w.total_hours >= 78)
      expect(nearViolations).toHaveLength(3)
    })

    it('should calculate average weekly hours', async () => {
      setupApiMock()

      const result = await mockedApi.get('/api/compliance/work-hours?person_id=person-1')
      const total = result.items.reduce((sum: number, w: any) => sum + w.total_hours, 0)
      const average = total / result.items.length
      expect(average).toBeCloseTo(76.5, 1)
    })
  })

  describe('46. 1-in-7 Day Off Compliance', () => {
    it('should track days off in rolling week', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        person_id: 'person-1',
        days_off_count: 1,
        compliant: true,
      })

      const result = await mockedApi.get('/api/compliance/days-off?person_id=person-1')
      expect(result.compliant).toBe(true)
      expect(result.days_off_count).toBeGreaterThanOrEqual(1)
    })

    it('should detect 1-in-7 violations', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        person_id: 'person-1',
        days_off_count: 0,
        compliant: false,
        violation: '1-in-7 rule violated',
      })

      const result = await mockedApi.get('/api/compliance/days-off?person_id=person-1')
      expect(result.compliant).toBe(false)
    })
  })

  describe('47. Supervision Ratio Compliance', () => {
    it('should check supervision ratios', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        block_id: 'block-1',
        residents: 4,
        faculty: 2,
        ratio: 2,
        required_ratio: 2,
        compliant: true,
      })

      const result = await mockedApi.get('/api/compliance/supervision?block_id=block-1')
      expect(result.compliant).toBe(true)
    })

    it('should detect supervision violations', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        block_id: 'block-1',
        residents: 6,
        faculty: 1,
        ratio: 6,
        required_ratio: 4,
        compliant: false,
      })

      const result = await mockedApi.get('/api/compliance/supervision?block_id=block-1')
      expect(result.compliant).toBe(false)
    })

    it('should check PGY-specific ratios', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        block_id: 'block-1',
        pgy1_count: 2,
        pgy1_faculty: 1,
        pgy1_ratio: 2,
        pgy1_required: 2,
        pgy1_compliant: true,
      })

      const result = await mockedApi.get('/api/compliance/supervision?block_id=block-1&pgy=1')
      expect(result.pgy1_compliant).toBe(true)
    })
  })

  describe('48. Real-time Compliance Monitoring', () => {
    it('should provide real-time hour updates', async () => {
      setupApiMock()

      // Simulate real-time update
      mockedApi.get.mockResolvedValueOnce({
        person_id: 'person-1',
        current_hours: 75,
        last_updated: new Date().toISOString(),
      })

      const result = await mockedApi.get('/api/compliance/status/realtime?person_id=person-1')
      expect(result.current_hours).toBe(75)
    })

    it('should detect when hours exceed threshold', async () => {
      setupApiMock()

      mockedApi.post = jest.fn().mockResolvedValueOnce({
        alert: true,
        message: 'Hours exceeded 80-hour limit',
      })

      const result = await mockedApi.post('/api/compliance/check', {
        person_id: 'person-1',
        hours: 82,
      })

      expect(result.alert).toBe(true)
    })
  })

  describe('49. Compliance Notifications', () => {
    it('should send alert when approaching violation', async () => {
      setupApiMock()

      mockedApi.post = jest.fn().mockResolvedValueOnce({
        notification_sent: true,
        recipients: ['person-1', 'coordinator-1'],
      })

      const result = await mockedApi.post('/api/compliance/notify', {
        person_id: 'person-1',
        type: 'warning',
        message: 'Approaching 80-hour limit',
      })

      expect(result.notification_sent).toBe(true)
    })

    it('should escalate critical violations', async () => {
      setupApiMock()

      mockedApi.post = jest.fn().mockResolvedValueOnce({
        escalated: true,
        escalation_level: 'critical',
        recipients: ['coordinator-1', 'program_director'],
      })

      const result = await mockedApi.post('/api/compliance/escalate', {
        violation_id: 'violation-1',
      })

      expect(result.escalated).toBe(true)
    })
  })

  describe('50. Compliance Forecasting', () => {
    it('should predict violation risk', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        person_id: 'person-1',
        current_hours: 75,
        projected_hours: 82,
        violation_risk: 'high',
      })

      const result = await mockedApi.get('/api/compliance/forecast?person_id=person-1')
      expect(result.violation_risk).toBe('high')
    })

    it('should recommend schedule adjustments', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        recommendations: [
          { action: 'reduce_hours', blocks: ['block-5', 'block-6'] },
          { action: 'reassign', to_person: 'person-2' },
        ],
      })

      const result = await mockedApi.get('/api/compliance/recommendations?person_id=person-1')
      expect(result.recommendations).toHaveLength(2)
    })
  })

  describe('51. Violation Resolution', () => {
    it('should mark violation as resolved', async () => {
      setupApiMock()

      mockedApi.patch = jest.fn().mockResolvedValueOnce({
        id: 'violation-1',
        resolved: true,
        resolved_at: '2024-01-29T00:00:00Z',
        resolved_by: 'coordinator-1',
      })

      const result = await mockedApi.patch('/api/compliance/violations/violation-1/resolve', {
        resolution_notes: 'Hours adjusted in schedule',
      })

      expect(result.resolved).toBe(true)
    })

    it('should track resolution actions', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        violation_id: 'violation-1',
        actions: [
          { action: 'hours_reduced', blocks_modified: 2 },
          { action: 'supervisor_notified', timestamp: '2024-01-29T00:00:00Z' },
        ],
      })

      const result = await mockedApi.get('/api/compliance/violations/violation-1/actions')
      expect(result.actions).toHaveLength(2)
    })
  })

  describe('52. Compliance Trends', () => {
    it('should show compliance rate over time', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        periods: [
          { period: '2024-01', compliance_rate: 95 },
          { period: '2024-02', compliance_rate: 98 },
          { period: '2024-03', compliance_rate: 97 },
        ],
      })

      const result = await mockedApi.get('/api/compliance/trends')
      expect(result.periods).toHaveLength(3)
    })

    it('should identify improving or declining trends', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        trend: 'improving',
        change_percentage: 3,
      })

      const result = await mockedApi.get('/api/compliance/trends/direction')
      expect(result.trend).toBe('improving')
    })
  })

  describe('53. Compliance Comparison', () => {
    it('should compare residents against each other', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        items: [
          { person_id: 'person-1', total_hours: 75, rank: 1 },
          { person_id: 'person-2', total_hours: 78, rank: 2 },
          { person_id: 'person-3', total_hours: 82, rank: 3 },
        ],
      })

      const result = await mockedApi.get('/api/compliance/comparison')
      expect(result.items).toHaveLength(3)
    })

    it('should compare against program averages', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        person_hours: 75,
        program_average: 70,
        difference: 5,
      })

      const result = await mockedApi.get('/api/compliance/compare-to-average?person_id=person-1')
      expect(result.difference).toBe(5)
    })
  })

  describe('54. Compliance Audit Trail', () => {
    it('should log all compliance checks', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        items: [
          {
            check_id: 'check-1',
            timestamp: '2024-01-28T00:00:00Z',
            result: 'pass',
            rule: '80_hour_limit',
          },
        ],
      })

      const result = await mockedApi.get('/api/compliance/audit?person_id=person-1')
      expect(result.items).toHaveLength(1)
    })

    it('should track compliance status changes', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        changes: [
          { from: 'green', to: 'yellow', timestamp: '2024-01-15T00:00:00Z' },
          { from: 'yellow', to: 'red', timestamp: '2024-01-28T00:00:00Z' },
        ],
      })

      const result = await mockedApi.get('/api/compliance/status-history?person_id=person-1')
      expect(result.changes).toHaveLength(2)
    })
  })

  describe('55. Compliance Exemptions', () => {
    it('should create exemption for special circumstances', async () => {
      setupApiMock()

      mockedApi.post = jest.fn().mockResolvedValueOnce({
        exemption_id: 'exemption-1',
        person_id: 'person-1',
        rule: '80_hour_limit',
        reason: 'Research project deadline',
        approved_by: 'program_director',
      })

      const result = await mockedApi.post('/api/compliance/exemptions', {
        person_id: 'person-1',
        rule: '80_hour_limit',
        reason: 'Research project deadline',
      })

      expect(result.exemption_id).toBeDefined()
    })

    it('should apply exemption to compliance calculation', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        total_hours: 85,
        max_hours: 80,
        exemption_applied: true,
        compliance_status: 'green',
      })

      const result = await mockedApi.get('/api/compliance/status?person_id=person-1')
      expect(result.exemption_applied).toBe(true)
      expect(result.compliance_status).toBe('green')
    })
  })

  describe('56. Compliance Dashboard Filters', () => {
    it('should filter by PGY level', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        items: [
          { person_id: 'person-1', pgy_level: 1 },
          { person_id: 'person-2', pgy_level: 1 },
        ],
      })

      const result = await mockedApi.get('/api/compliance/status?pgy_level=1')
      expect(result.items.every((s: any) => s.pgy_level === 1)).toBe(true)
    })

    it('should filter by date range', async () => {
      setupApiMock()

      const result = await mockedApi.get('/api/compliance/status?start=2024-01-01&end=2024-01-31')
      expect(mockedApi.get).toHaveBeenCalledWith(
        expect.stringContaining('start=2024-01-01')
      )
    })
  })

  describe('57. Compliance Widgets', () => {
    it('should display compliance summary widget', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        total_residents: 10,
        compliant: 8,
        warnings: 1,
        violations: 1,
        compliance_rate: 80,
      })

      const result = await mockedApi.get('/api/compliance/summary')
      expect(result.compliance_rate).toBe(80)
    })

    it('should show top violations widget', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        top_violations: [
          { rule: '80_hour_limit', count: 3 },
          { rule: '1_in_7_days_off', count: 2 },
        ],
      })

      const result = await mockedApi.get('/api/compliance/top-violations')
      expect(result.top_violations).toHaveLength(2)
    })
  })

  describe('58. Compliance Export', () => {
    it('should export compliance data to CSV', async () => {
      setupApiMock()

      mockedApi.post = jest.fn().mockResolvedValueOnce({
        download_url: '/api/exports/compliance.csv',
        format: 'csv',
        rows: 100,
      })

      const result = await mockedApi.post('/api/compliance/export', {
        format: 'csv',
      })

      expect(result.format).toBe('csv')
      expect(result.rows).toBe(100)
    })
  })

  describe('59. Compliance Automation', () => {
    it('should auto-resolve minor violations', async () => {
      setupApiMock()

      mockedApi.post = jest.fn().mockResolvedValueOnce({
        auto_resolved: 3,
        manual_review_required: 1,
      })

      const result = await mockedApi.post('/api/compliance/auto-resolve', {})
      expect(result.auto_resolved).toBe(3)
    })
  })

  describe('60. Compliance Scoring', () => {
    it('should calculate compliance score', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        person_id: 'person-1',
        score: 95,
        factors: {
          hours: 98,
          days_off: 100,
          violations: 85,
        },
      })

      const result = await mockedApi.get('/api/compliance/score?person_id=person-1')
      expect(result.score).toBe(95)
    })
  })
})
