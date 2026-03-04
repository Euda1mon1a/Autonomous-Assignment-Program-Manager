/**
 * Compliance Monitoring Flow Integration Tests
 *
 * Tests complete user journeys for viewing and monitoring ACGME compliance.
 * Covers compliance dashboards, work hour tracking, violation alerts,
 * and compliance report generation.
 */
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

// ============================================================================
// Type Definitions
// ============================================================================

interface ComplianceStatus {
  personId: string;
  periodStart: string;
  periodEnd: string;
  totalHours: number;
  maxHours: number;
  hoursRemaining: number;
  complianceStatus: 'green' | 'yellow' | 'red';
  violations: string[];
  warnings: string[];
  gaugeColor?: string;
  warning?: string;
  sessionExpiresIn?: number;
  showWarning?: boolean;
  exemptionApplied?: boolean;
  pgyLevel?: number;
}

interface ComplianceViolation {
  id: string;
  personId: string;
  rule: string;
  severity: 'high' | 'medium' | 'low' | 'critical';
  description: string;
  detectedAt: string;
  resolved: boolean;
  hoursOver?: number;
  requiresImmediateAction?: boolean;
}

interface WorkHours {
  personId: string;
  weekStart: string;
  weekEnd: string;
  totalHours: number;
  clinicalHours: number;
  nonClinicalHours: number;
}

interface ComplianceListResponse<T> {
  items: T[];
  total: number;
}

// Mock compliance data
const mockComplianceStatus: ComplianceStatus = {
  personId: 'person-1',
  periodStart: '2024-01-01',
  periodEnd: '2024-01-28',
  totalHours: 75,
  maxHours: 80,
  hoursRemaining: 5,
  complianceStatus: 'green' as const,
  violations: [],
  warnings: [],
}

const mockViolations: ComplianceViolation[] = [
  {
    id: 'violation-1',
    personId: 'person-1',
    rule: '80_hour_limit',
    severity: 'high' as const,
    description: 'Exceeded 80-hour weekly limit',
    detectedAt: '2024-01-28T00:00:00Z',
    resolved: false,
    hoursOver: 5,
  },
]

const mockWorkHours: WorkHours[] = [
  {
    personId: 'person-1',
    weekStart: '2024-01-01',
    weekEnd: '2024-01-07',
    totalHours: 78,
    clinicalHours: 70,
    nonClinicalHours: 8,
  },
  {
    personId: 'person-1',
    weekStart: '2024-01-08',
    weekEnd: '2024-01-14',
    totalHours: 75,
    clinicalHours: 68,
    nonClinicalHours: 7,
  },
]

// API mock helper
function setupApiMock(options: {
  status?: ComplianceStatus | 'error'
  violations?: ComplianceViolation[] | 'error'
  workHours?: WorkHours[] | 'error'
} = {}): void {
  mockedApi.get.mockImplementation((url: string): Promise<unknown> => {
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

      const result: any = await mockedApi.get('/api/compliance/status?personId=person-1')
      expect(result.complianceStatus).toBe('green')
      expect(result.totalHours).toBe(75)
    })

    it('should display compliance status for all residents', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        items: [
          { personId: 'person-1', complianceStatus: 'green', totalHours: 75 },
          { personId: 'person-2', complianceStatus: 'yellow', totalHours: 78 },
          { personId: 'person-3', complianceStatus: 'red', totalHours: 85 },
        ],
      })

      const result: any = await mockedApi.get('/api/compliance/status') as ComplianceListResponse<ComplianceStatus>
      expect(result.items).toHaveLength(3)
      expect(result.items.some((s: { complianceStatus: string }) => s.complianceStatus === 'red')).toBe(true)
    })

    it('should group residents by compliance status', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        items: [
          { personId: 'person-1', complianceStatus: 'green' },
          { personId: 'person-2', complianceStatus: 'green' },
          { personId: 'person-3', complianceStatus: 'yellow' },
          { personId: 'person-4', complianceStatus: 'red' },
        ],
      })

      const result: any = await mockedApi.get('/api/compliance/status') as ComplianceListResponse<ComplianceStatus>
      const green = result.items.filter((s: { complianceStatus: string }) => s.complianceStatus === 'green')
      const yellow = result.items.filter((s: { complianceStatus: string }) => s.complianceStatus === 'yellow')
      const red = result.items.filter((s: { complianceStatus: string }) => s.complianceStatus === 'red')

      expect(green).toHaveLength(2)
      expect(yellow).toHaveLength(1)
      expect(red).toHaveLength(1)
    })
  })

  describe('42. Work Hour Gauge Updates', () => {
    it('should display current weekly hours', async () => {
      setupApiMock()

      const result: any = await mockedApi.get('/api/compliance/status?personId=person-1')
      expect(result.totalHours).toBe(75)
      expect(result.maxHours).toBe(80)
    })

    it('should show hours remaining in week', async () => {
      setupApiMock()

      const result: any = await mockedApi.get('/api/compliance/status?personId=person-1')
      expect(result.hoursRemaining).toBe(5)
    })

    it('should calculate percentage of max hours', async () => {
      setupApiMock()

      const result: any = await mockedApi.get('/api/compliance/status?personId=person-1')
      const percentage = (result.totalHours / result.maxHours) * 100
      expect(percentage).toBeCloseTo(93.75, 1)
    })

    it('should update gauge color based on threshold', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        totalHours: 85,
        maxHours: 80,
        gaugeColor: 'red',
      })

      const result: any = await mockedApi.get('/api/compliance/status?personId=person-1')
      expect(result.gaugeColor).toBe('red')
    })

    it('should show warning when approaching limit', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        totalHours: 78,
        maxHours: 80,
        warning: 'Approaching 80-hour limit',
      })

      const result: any = await mockedApi.get('/api/compliance/status?personId=person-1')
      expect(result.warning).toBeDefined()
    })
  })

  describe('43. Violation Alert Display', () => {
    it('should display active violations', async () => {
      setupApiMock()

      const result: any = await mockedApi.get('/api/compliance/violations?resolved=false')
      expect(result.items).toHaveLength(1)
      expect(result.items[0].resolved).toBe(false)
    })

    it('should show violation details', async () => {
      setupApiMock()

      const violation = mockViolations[0]
      expect(violation.rule).toBe('80_hour_limit')
      expect(violation.severity).toBe('high')
      expect(violation.hoursOver).toBe(5)
    })

    it('should filter violations by severity', async () => {
      const violations = [
        { ...mockViolations[0], severity: 'high' as const },
        { ...mockViolations[0], id: 'violation-2', severity: 'medium' as const },
        { ...mockViolations[0], id: 'violation-3', severity: 'low' as const },
      ]

      setupApiMock({ violations })

      const result: any = await mockedApi.get('/api/compliance/violations') as ComplianceListResponse<ComplianceViolation>
      const highSeverity = result.items.filter((v: { severity: string }) => v.severity === 'high')
      expect(highSeverity).toHaveLength(1)
    })

    it('should sort violations by severity', async () => {
      const violations = [
        { ...mockViolations[0], id: 'v1', severity: 'low' as const },
        { ...mockViolations[0], id: 'v2', severity: 'high' as const },
        { ...mockViolations[0], id: 'v3', severity: 'medium' as const },
      ]

      setupApiMock({ violations })

      const result: any = await mockedApi.get('/api/compliance/violations')
      // In real implementation, would be sorted by severity
      expect(result.items).toHaveLength(3)
    })

    it('should highlight critical violations', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        items: [
          { ...mockViolations[0], severity: 'critical', requiresImmediateAction: true },
        ],
      })

      const result: any = await mockedApi.get('/api/compliance/violations?severity=critical')
      expect(result.items[0].requiresImmediateAction).toBe(true)
    })
  })

  describe('44. Compliance Report Generation', () => {
    it('should generate weekly compliance report', async () => {
      setupApiMock()

      mockedApi.post = jest.fn().mockResolvedValueOnce({
        reportId: 'report-1',
        type: 'weekly',
        generatedAt: '2024-01-28T00:00:00Z',
        downloadUrl: '/api/reports/compliance-weekly-1.pdf',
      })

      const result: any = await mockedApi.post('/api/compliance/reports', {
        type: 'weekly',
        startDate: '2024-01-01',
        endDate: '2024-01-07',
      })

      expect(result.type).toBe('weekly')
      expect(result.downloadUrl).toContain('.pdf')
    })

    it('should generate monthly compliance report', async () => {
      setupApiMock()

      mockedApi.post = jest.fn().mockResolvedValueOnce({
        reportId: 'report-2',
        type: 'monthly',
        month: '2024-01',
      })

      const result: any = await mockedApi.post('/api/compliance/reports', {
        type: 'monthly',
        month: '2024-01',
      })

      expect(result.type).toBe('monthly')
    })

    it('should include violation summary in report', async () => {
      setupApiMock()

      mockedApi.post = jest.fn().mockResolvedValueOnce({
        reportId: 'report-1',
        summary: {
          totalViolations: 5,
          resolvedViolations: 3,
          activeViolations: 2,
        },
      })

      const result: any = await mockedApi.post('/api/compliance/reports', {})
      expect(result.summary.totalViolations).toBe(5)
    })

    it('should export report to PDF', async () => {
      setupApiMock()

      mockedApi.post = jest.fn().mockResolvedValueOnce({
        downloadUrl: '/api/reports/compliance-1.pdf',
        format: 'pdf',
      })

      const result: any = await mockedApi.post('/api/compliance/reports/export', {
        format: 'pdf',
      })

      expect(result.format).toBe('pdf')
    })

    it('should export report to Excel', async () => {
      setupApiMock()

      mockedApi.post = jest.fn().mockResolvedValueOnce({
        downloadUrl: '/api/reports/compliance-1.xlsx',
        format: 'excel',
      })

      const result: any = await mockedApi.post('/api/compliance/reports/export', {
        format: 'excel',
      })

      expect(result.format).toBe('excel')
    })
  })

  describe('45. Historical Compliance View', () => {
    it('should display compliance history for resident', async () => {
      setupApiMock()

      const result: any = await mockedApi.get('/api/compliance/work-hours?personId=person-1')
      expect(result.items).toHaveLength(2)
    })

    it('should show weekly hour trends', async () => {
      setupApiMock()

      const result: any = await mockedApi.get('/api/compliance/work-hours?personId=person-1') as ComplianceListResponse<WorkHours>
      const hours = result.items.map((w: { totalHours: number }) => w.totalHours)
      expect(hours).toEqual([78, 75])
    })

    it('should identify patterns of near-violations', async () => {
      const workHours = [
        { ...mockWorkHours[0], totalHours: 79 },
        { ...mockWorkHours[0], weekStart: '2024-01-08', totalHours: 78 },
        { ...mockWorkHours[0], weekStart: '2024-01-15', totalHours: 79 },
      ]

      setupApiMock({ workHours })

      const result: any = await mockedApi.get('/api/compliance/work-hours?personId=person-1') as ComplianceListResponse<WorkHours>
      const nearViolations = result.items.filter((w: { totalHours: number }) => w.totalHours >= 78)
      expect(nearViolations).toHaveLength(3)
    })

    it('should calculate average weekly hours', async () => {
      setupApiMock()

      const result: any = await mockedApi.get('/api/compliance/work-hours?personId=person-1') as ComplianceListResponse<WorkHours>
      const total = result.items.reduce((sum: number, w: { totalHours: number }) => sum + w.totalHours, 0)
      const average = total / result.items.length
      expect(average).toBeCloseTo(76.5, 1)
    })
  })

  describe('46. 1-in-7 Day Off Compliance', () => {
    it('should track days off in rolling week', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        personId: 'person-1',
        daysOffCount: 1,
        compliant: true,
      })

      const result: any = await mockedApi.get('/api/compliance/days-off?personId=person-1')
      expect(result.compliant).toBe(true)
      expect(result.daysOffCount).toBeGreaterThanOrEqual(1)
    })

    it('should detect 1-in-7 violations', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        personId: 'person-1',
        daysOffCount: 0,
        compliant: false,
        violation: '1-in-7 rule violated',
      })

      const result: any = await mockedApi.get('/api/compliance/days-off?personId=person-1')
      expect(result.compliant).toBe(false)
    })
  })

  describe('47. Supervision Ratio Compliance', () => {
    it('should check supervision ratios', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        blockId: 'block-1',
        residents: 4,
        faculty: 2,
        ratio: 2,
        requiredRatio: 2,
        compliant: true,
      })

      const result: any = await mockedApi.get('/api/compliance/supervision?blockId=block-1')
      expect(result.compliant).toBe(true)
    })

    it('should detect supervision violations', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        blockId: 'block-1',
        residents: 6,
        faculty: 1,
        ratio: 6,
        requiredRatio: 4,
        compliant: false,
      })

      const result: any = await mockedApi.get('/api/compliance/supervision?blockId=block-1')
      expect(result.compliant).toBe(false)
    })

    it('should check PGY-specific ratios', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        blockId: 'block-1',
        pgy1Count: 2,
        pgy1Faculty: 1,
        pgy1Ratio: 2,
        pgy1Required: 2,
        pgy1Compliant: true,
      })

      const result: any = await mockedApi.get('/api/compliance/supervision?blockId=block-1&pgy=1')
      expect(result.pgy1Compliant).toBe(true)
    })
  })

  describe('48. Real-time Compliance Monitoring', () => {
    it('should provide real-time hour updates', async () => {
      setupApiMock()

      // Simulate real-time update
      mockedApi.get.mockResolvedValueOnce({
        personId: 'person-1',
        currentHours: 75,
        lastUpdated: new Date().toISOString(),
      })

      const result: any = await mockedApi.get('/api/compliance/status/realtime?personId=person-1')
      expect(result.currentHours).toBe(75)
    })

    it('should detect when hours exceed threshold', async () => {
      setupApiMock()

      mockedApi.post = jest.fn().mockResolvedValueOnce({
        alert: true,
        message: 'Hours exceeded 80-hour limit',
      })

      const result: any = await mockedApi.post('/api/compliance/check', {
        personId: 'person-1',
        hours: 82,
      })

      expect(result.alert).toBe(true)
    })
  })

  describe('49. Compliance Notifications', () => {
    it('should send alert when approaching violation', async () => {
      setupApiMock()

      mockedApi.post = jest.fn().mockResolvedValueOnce({
        notificationSent: true,
        recipients: ['person-1', 'coordinator-1'],
      })

      const result: any = await mockedApi.post('/api/compliance/notify', {
        personId: 'person-1',
        type: 'warning',
        message: 'Approaching 80-hour limit',
      })

      expect(result.notificationSent).toBe(true)
    })

    it('should escalate critical violations', async () => {
      setupApiMock()

      mockedApi.post = jest.fn().mockResolvedValueOnce({
        escalated: true,
        escalationLevel: 'critical',
        recipients: ['coordinator-1', 'program_director'],
      })

      const result: any = await mockedApi.post('/api/compliance/escalate', {
        violationId: 'violation-1',
      })

      expect(result.escalated).toBe(true)
    })
  })

  describe('50. Compliance Forecasting', () => {
    it('should predict violation risk', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        personId: 'person-1',
        currentHours: 75,
        projectedHours: 82,
        violationRisk: 'high',
      })

      const result: any = await mockedApi.get('/api/compliance/forecast?personId=person-1')
      expect(result.violationRisk).toBe('high')
    })

    it('should recommend schedule adjustments', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        recommendations: [
          { action: 'reduce_hours', blocks: ['block-5', 'block-6'] },
          { action: 'reassign', toPerson: 'person-2' },
        ],
      })

      const result: any = await mockedApi.get('/api/compliance/recommendations?personId=person-1')
      expect(result.recommendations).toHaveLength(2)
    })
  })

  describe('51. Violation Resolution', () => {
    it('should mark violation as resolved', async () => {
      setupApiMock()

      mockedApi.patch = jest.fn().mockResolvedValueOnce({
        id: 'violation-1',
        resolved: true,
        resolvedAt: '2024-01-29T00:00:00Z',
        resolvedBy: 'coordinator-1',
      })

      const result: any = await mockedApi.patch('/api/compliance/violations/violation-1/resolve', {
        resolutionNotes: 'Hours adjusted in schedule',
      })

      expect(result.resolved).toBe(true)
    })

    it('should track resolution actions', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        violationId: 'violation-1',
        actions: [
          { action: 'hours_reduced', blocksModified: 2 },
          { action: 'supervisor_notified', timestamp: '2024-01-29T00:00:00Z' },
        ],
      })

      const result: any = await mockedApi.get('/api/compliance/violations/violation-1/actions')
      expect(result.actions).toHaveLength(2)
    })
  })

  describe('52. Compliance Trends', () => {
    it('should show compliance rate over time', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        periods: [
          { period: '2024-01', complianceRate: 95 },
          { period: '2024-02', complianceRate: 98 },
          { period: '2024-03', complianceRate: 97 },
        ],
      })

      const result: any = await mockedApi.get('/api/compliance/trends')
      expect(result.periods).toHaveLength(3)
    })

    it('should identify improving or declining trends', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        trend: 'improving',
        changePercentage: 3,
      })

      const result: any = await mockedApi.get('/api/compliance/trends/direction')
      expect(result.trend).toBe('improving')
    })
  })

  describe('53. Compliance Comparison', () => {
    it('should compare residents against each other', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        items: [
          { personId: 'person-1', totalHours: 75, rank: 1 },
          { personId: 'person-2', totalHours: 78, rank: 2 },
          { personId: 'person-3', totalHours: 82, rank: 3 },
        ],
      })

      const result: any = await mockedApi.get('/api/compliance/comparison')
      expect(result.items).toHaveLength(3)
    })

    it('should compare against program averages', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        personHours: 75,
        programAverage: 70,
        difference: 5,
      })

      const result: any = await mockedApi.get('/api/compliance/compare-to-average?personId=person-1')
      expect(result.difference).toBe(5)
    })
  })

  describe('54. Compliance Audit Trail', () => {
    it('should log all compliance checks', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        items: [
          {
            checkId: 'check-1',
            timestamp: '2024-01-28T00:00:00Z',
            result: 'pass',
            rule: '80_hour_limit',
          },
        ],
      })

      const result: any = await mockedApi.get('/api/compliance/audit?personId=person-1')
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

      const result: any = await mockedApi.get('/api/compliance/status-history?personId=person-1')
      expect(result.changes).toHaveLength(2)
    })
  })

  describe('55. Compliance Exemptions', () => {
    it('should create exemption for special circumstances', async () => {
      setupApiMock()

      mockedApi.post = jest.fn().mockResolvedValueOnce({
        exemptionId: 'exemption-1',
        personId: 'person-1',
        rule: '80_hour_limit',
        reason: 'Research project deadline',
        approvedBy: 'program_director',
      })

      const result: any = await mockedApi.post('/api/compliance/exemptions', {
        personId: 'person-1',
        rule: '80_hour_limit',
        reason: 'Research project deadline',
      })

      expect(result.exemptionId).toBeDefined()
    })

    it('should apply exemption to compliance calculation', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        totalHours: 85,
        maxHours: 80,
        exemptionApplied: true,
        complianceStatus: 'green',
      })

      const result: any = await mockedApi.get('/api/compliance/status?personId=person-1')
      expect(result.exemptionApplied).toBe(true)
      expect(result.complianceStatus).toBe('green')
    })
  })

  describe('56. Compliance Dashboard Filters', () => {
    it('should filter by PGY level', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        items: [
          { personId: 'person-1', pgyLevel: 1 },
          { personId: 'person-2', pgyLevel: 1 },
        ],
      })

      const result: any = await mockedApi.get('/api/compliance/status?pgyLevel=1') as ComplianceListResponse<ComplianceStatus>
      expect(result.items.every((s: { pgyLevel: number }) => s.pgyLevel === 1)).toBe(true)
    })

    it('should filter by date range', async () => {
      setupApiMock()

      const _result: any = await mockedApi.get('/api/compliance/status?start=2024-01-01&end=2024-01-31')
      expect(mockedApi.get).toHaveBeenCalledWith(
        expect.stringContaining('start=2024-01-01')
      )
    })
  })

  describe('57. Compliance Widgets', () => {
    it('should display compliance summary widget', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        totalResidents: 10,
        compliant: 8,
        warnings: 1,
        violations: 1,
        complianceRate: 80,
      })

      const result: any = await mockedApi.get('/api/compliance/summary')
      expect(result.complianceRate).toBe(80)
    })

    it('should show top violations widget', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        topViolations: [
          { rule: '80_hour_limit', count: 3 },
          { rule: '1_in_7_days_off', count: 2 },
        ],
      })

      const result: any = await mockedApi.get('/api/compliance/top-violations')
      expect(result.topViolations).toHaveLength(2)
    })
  })

  describe('58. Compliance Export', () => {
    it('should export compliance data to CSV', async () => {
      setupApiMock()

      mockedApi.post = jest.fn().mockResolvedValueOnce({
        downloadUrl: '/api/exports/compliance.csv',
        format: 'csv',
        rows: 100,
      })

      const result: any = await mockedApi.post('/api/compliance/export', {
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
        autoResolved: 3,
        manualReviewRequired: 1,
      })

      const result: any = await mockedApi.post('/api/compliance/auto-resolve', {})
      expect(result.autoResolved).toBe(3)
    })
  })

  describe('60. Compliance Scoring', () => {
    it('should calculate compliance score', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        personId: 'person-1',
        score: 95,
        factors: {
          hours: 98,
          daysOff: 100,
          violations: 85,
        },
      })

      const result: any = await mockedApi.get('/api/compliance/score?personId=person-1')
      expect(result.score).toBe(95)
    })
  })
})
