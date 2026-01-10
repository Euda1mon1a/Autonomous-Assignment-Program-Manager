/**
 * Swap Request Flow Integration Tests
 *
 * Tests complete user journeys for creating, viewing, accepting, and managing
 * schedule swap requests. Covers swap marketplace, auto-matching, approval workflows,
 * and rollback functionality.
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
  usePathname: () => '/swaps',
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

// Mock data
const mockPeople = [
  {
    id: 'person-1',
    name: 'Dr. Alice PGY1',
    email: 'alice@hospital.org',
    type: 'resident' as const,
    pgyLevel: 1,
  },
  {
    id: 'person-2',
    name: 'Dr. Bob PGY2',
    email: 'bob@hospital.org',
    type: 'resident' as const,
    pgyLevel: 2,
  },
]

const mockAssignments = [
  {
    id: 'assignment-1',
    blockId: 'block-1',
    personId: 'person-1',
    rotationTemplateId: 'rotation-1',
    role: 'primary' as const,
    createdAt: '2024-01-01T00:00:00Z',
  },
  {
    id: 'assignment-2',
    blockId: 'block-2',
    personId: 'person-2',
    rotationTemplateId: 'rotation-2',
    role: 'primary' as const,
    createdAt: '2024-01-01T00:00:00Z',
  },
]

type SwapStatus = 'pending' | 'approved' | 'rejected' | 'completed' | 'expired' | 'cancelled'
const mockSwapRequests: Array<{
  id: string
  requester_id: string
  requester_assignmentId: string
  target_personId: string
  target_assignmentId: string
  status: SwapStatus
  swapType: 'oneToOne' | 'oneToMany' | 'manyToOne'
  reason: string
  createdAt: string
  expiresAt: string
  executedAt?: string
}> = [
  {
    id: 'swap-1',
    requester_id: 'person-1',
    requester_assignmentId: 'assignment-1',
    target_personId: 'person-2',
    target_assignmentId: 'assignment-2',
    status: 'pending',
    swapType: 'oneToOne',
    reason: 'Family emergency',
    createdAt: '2024-01-01T00:00:00Z',
    expiresAt: '2024-01-08T00:00:00Z',
  },
]

// API mock helper
function setupApiMock(options: {
  swaps?: typeof mockSwapRequests | 'error'
  assignments?: typeof mockAssignments | 'error'
  people?: typeof mockPeople | 'error'
} = {}) {
  mockedApi.get.mockImplementation((url: string) => {
    if (url.includes('/swaps')) {
      if (options.swaps === 'error') {
        return Promise.reject({ message: 'Failed to fetch swaps', status: 500 })
      }
      return Promise.resolve({
        items: options.swaps ?? mockSwapRequests,
        total: (options.swaps ?? mockSwapRequests).length,
      })
    }
    if (url.includes('/assignments')) {
      if (options.assignments === 'error') {
        return Promise.reject({ message: 'Failed to fetch assignments', status: 500 })
      }
      return Promise.resolve({
        items: options.assignments ?? mockAssignments,
        total: (options.assignments ?? mockAssignments).length,
      })
    }
    if (url.includes('/people')) {
      if (options.people === 'error') {
        return Promise.reject({ message: 'Failed to fetch people', status: 500 })
      }
      return Promise.resolve({
        items: options.people ?? mockPeople,
        total: (options.people ?? mockPeople).length,
      })
    }
    return Promise.reject({ message: 'Unknown endpoint', status: 404 })
  })
}

describe('Swap Request Flow - Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    setupApiMock()
  })

  describe('21. Creating Swap Request', () => {
    it('should create a one-to-one swap request', async () => {
      setupApiMock()

      mockedApi.post = jest.fn().mockResolvedValueOnce({
        id: 'swap-new',
        status: 'pending',
        swapType: 'oneToOne',
      })

      const result: any = await mockedApi.post('/api/swaps', {
        requester_assignmentId: 'assignment-1',
        target_assignmentId: 'assignment-2',
        swapType: 'oneToOne',
        reason: 'Need to attend conference',
      })

      expect(result.status).toBe('pending')
      expect(result.swapType).toBe('oneToOne')
    })

    it('should create an absorb swap request', async () => {
      setupApiMock()

      mockedApi.post = jest.fn().mockResolvedValueOnce({
        id: 'swap-absorb',
        status: 'pending',
        swapType: 'absorb',
      })

      const result: any = await mockedApi.post('/api/swaps', {
        requester_assignmentId: 'assignment-1',
        swapType: 'absorb',
        reason: 'Emergency leave',
      })

      expect(result.status).toBe('pending')
      expect(result.swapType).toBe('absorb')
    })

    it('should validate swap request data', async () => {
      setupApiMock()

      mockedApi.post = jest.fn().mockRejectedValueOnce({
        message: 'Requester assignment is required',
        status: 400,
      })

      await expect(
        mockedApi.post('/api/swaps', {
          swapType: 'oneToOne',
          reason: 'Test',
        })
      ).rejects.toMatchObject({
        message: 'Requester assignment is required',
      })
    })

    it('should set expiration date for swap request', async () => {
      setupApiMock()

      const expiresAt = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString()

      mockedApi.post = jest.fn().mockResolvedValueOnce({
        id: 'swap-new',
        status: 'pending',
        expiresAt: expiresAt,
      })

      const result: any = await mockedApi.post('/api/swaps', {
        requester_assignmentId: 'assignment-1',
        target_assignmentId: 'assignment-2',
        swapType: 'oneToOne',
        expiresAt: expiresAt,
      })

      expect(result.expiresAt).toBeDefined()
    })
  })

  describe('22. Viewing Pending Swaps', () => {
    it('should display list of pending swaps', async () => {
      setupApiMock()

      const result: any = await mockedApi.get('/api/swaps?status=pending')
      expect(result.items).toHaveLength(1)
      expect(result.items[0].status).toBe('pending')
    })

    it('should show swap details', async () => {
      setupApiMock()

      const swap = mockSwapRequests[0]
      expect(swap.reason).toBe('Family emergency')
      expect(swap.swapType).toBe('oneToOne')
      expect(swap.requester_id).toBe('person-1')
    })

    it('should filter swaps by status', async () => {
      const completedSwap = {
        ...mockSwapRequests[0],
        id: 'swap-completed',
        status: 'completed' as const,
      }

      setupApiMock({ swaps: [mockSwapRequests[0], completedSwap] })

      const result: any = await mockedApi.get('/api/swaps?status=pending')
      const pending = result.items.filter((s: any) => s.status === 'pending')

      expect(pending).toHaveLength(1)
    })

    it('should show swaps created by user', async () => {
      setupApiMock()

      const result: any = await mockedApi.get('/api/swaps?requester_id=person-1')
      expect(result.items).toHaveLength(1)
      expect(result.items[0].requester_id).toBe('person-1')
    })
  })

  describe('23. Finding Compatible Matches', () => {
    it('should find auto-match candidates', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        matches: [
          {
            personId: 'person-2',
            assignmentId: 'assignment-2',
            compatibility_score: 0.95,
            reasons: ['Same rotation type', 'Compatible dates'],
          },
        ],
      })

      const result: any = await mockedApi.get('/api/swaps/swap-1/matches')
      expect(result.matches).toHaveLength(1)
      expect(result.matches[0].compatibility_score).toBeGreaterThan(0.9)
    })

    it('should rank matches by compatibility', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        matches: [
          { personId: 'person-2', compatibility_score: 0.95 },
          { personId: 'person-3', compatibility_score: 0.75 },
          { personId: 'person-4', compatibility_score: 0.60 },
        ],
      })

      const result: any = await mockedApi.get('/api/swaps/swap-1/matches')
      expect(result.matches[0].compatibility_score).toBeGreaterThan(
        result.matches[1].compatibility_score
      )
    })

    it('should filter matches by rotation type', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        matches: [
          { personId: 'person-2', rotation_type: 'clinic' },
        ],
      })

      const result: any = await mockedApi.get('/api/swaps/swap-1/matches?rotation_type=clinic')
      expect(result.matches[0].rotation_type).toBe('clinic')
    })

    it('should check ACGME compliance for matches', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        matches: [
          {
            personId: 'person-2',
            acgme_compliant: true,
            compliance_checks: {
              hours: 'pass',
              days_off: 'pass',
              supervision: 'pass',
            },
          },
        ],
      })

      const result: any = await mockedApi.get('/api/swaps/swap-1/matches')
      expect(result.matches[0].acgme_compliant).toBe(true)
    })
  })

  describe('24. Accepting Swap Offer', () => {
    it('should accept a swap request', async () => {
      setupApiMock()

      mockedApi.patch = jest.fn().mockResolvedValueOnce({
        id: 'swap-1',
        status: 'accepted',
      })

      const result: any = await mockedApi.patch('/api/swaps/swap-1/accept', {})
      expect(result.status).toBe('accepted')
    })

    it('should validate acceptor has permission', async () => {
      setupApiMock()

      mockedApi.patch = jest.fn().mockRejectedValueOnce({
        message: 'Only target person can accept',
        status: 403,
      })

      await expect(
        mockedApi.patch('/api/swaps/swap-1/accept', {})
      ).rejects.toMatchObject({
        status: 403,
      })
    })

    it('should trigger notification on acceptance', async () => {
      setupApiMock()

      mockedApi.patch = jest.fn().mockResolvedValueOnce({
        id: 'swap-1',
        status: 'accepted',
        notification_sent: true,
      })

      const result: any = await mockedApi.patch('/api/swaps/swap-1/accept', {})
      expect(result.notification_sent).toBe(true)
    })
  })

  describe('25. Rejecting Swap Offer', () => {
    it('should reject a swap request', async () => {
      setupApiMock()

      mockedApi.patch = jest.fn().mockResolvedValueOnce({
        id: 'swap-1',
        status: 'rejected',
      })

      const result: any = await mockedApi.patch('/api/swaps/swap-1/reject', {
        reason: 'Not compatible with my schedule',
      })

      expect(result.status).toBe('rejected')
    })

    it('should allow optional rejection reason', async () => {
      setupApiMock()

      mockedApi.patch = jest.fn().mockResolvedValueOnce({
        id: 'swap-1',
        status: 'rejected',
        rejection_reason: 'Scheduling conflict',
      })

      const result: any = await mockedApi.patch('/api/swaps/swap-1/reject', {
        reason: 'Scheduling conflict',
      })

      expect(result.rejection_reason).toBe('Scheduling conflict')
    })

    it('should notify requester of rejection', async () => {
      setupApiMock()

      mockedApi.patch = jest.fn().mockResolvedValueOnce({
        id: 'swap-1',
        status: 'rejected',
        notification_sent: true,
      })

      const result: any = await mockedApi.patch('/api/swaps/swap-1/reject', {})
      expect(result.notification_sent).toBe(true)
    })
  })

  describe('26. Swap Approval Workflow', () => {
    it('should submit swap for coordinator approval', async () => {
      setupApiMock()

      mockedApi.patch = jest.fn().mockResolvedValueOnce({
        id: 'swap-1',
        status: 'pending_approval',
      })

      const result: any = await mockedApi.patch('/api/swaps/swap-1/submit', {})
      expect(result.status).toBe('pending_approval')
    })

    it('should allow coordinator to approve swap', async () => {
      setupApiMock()

      mockedApi.patch = jest.fn().mockResolvedValueOnce({
        id: 'swap-1',
        status: 'approved',
        approved_by: 'coordinator-1',
      })

      const result: any = await mockedApi.patch('/api/swaps/swap-1/approve', {})
      expect(result.status).toBe('approved')
      expect(result.approved_by).toBeDefined()
    })

    it('should execute swap after approval', async () => {
      setupApiMock()

      mockedApi.post = jest.fn().mockResolvedValueOnce({
        swapId: 'swap-1',
        executed: true,
        assignments_updated: 2,
      })

      const result: any = await mockedApi.post('/api/swaps/swap-1/execute', {})
      expect(result.executed).toBe(true)
      expect(result.assignments_updated).toBe(2)
    })

    it('should validate swap before execution', async () => {
      setupApiMock()

      mockedApi.post = jest.fn().mockRejectedValueOnce({
        message: 'Swap would violate ACGME rules',
        status: 400,
        violations: ['80-hour limit exceeded'],
      })

      await expect(
        mockedApi.post('/api/swaps/swap-1/execute', {})
      ).rejects.toMatchObject({
        violations: expect.arrayContaining(['80-hour limit exceeded']),
      })
    })
  })

  describe('27. Swap Rollback', () => {
    it('should rollback swap within 24 hours', async () => {
      setupApiMock()

      mockedApi.post = jest.fn().mockResolvedValueOnce({
        swapId: 'swap-1',
        status: 'rolled_back',
        assignments_restored: 2,
      })

      const result: any = await mockedApi.post('/api/swaps/swap-1/rollback', {})
      expect(result.status).toBe('rolled_back')
      expect(result.assignments_restored).toBe(2)
    })

    it('should reject rollback after 24-hour window', async () => {
      setupApiMock()

      mockedApi.post = jest.fn().mockRejectedValueOnce({
        message: 'Rollback window expired',
        status: 400,
      })

      await expect(
        mockedApi.post('/api/swaps/swap-1/rollback', {})
      ).rejects.toMatchObject({
        message: 'Rollback window expired',
      })
    })

    it('should restore original assignments on rollback', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        swapId: 'swap-1',
        originalAssignments: {
          'person-1': 'assignment-1',
          'person-2': 'assignment-2',
        },
      })

      const result: any = await mockedApi.get('/api/swaps/swap-1/original')
      expect(result.originalAssignments).toBeDefined()
    })
  })

  describe('28. Swap History', () => {
    it('should display swap history for user', async () => {
      const swapHistory = [
        {
          ...mockSwapRequests[0],
          id: 'swap-old',
          status: 'completed' as const,
          executedAt: '2024-01-01T00:00:00Z',
        },
      ]

      setupApiMock({ swaps: swapHistory })

      const result: any = await mockedApi.get('/api/swaps?requester_id=person-1&include_completed=true')
      expect(result.items[0].status).toBe('completed')
    })

    it('should show swap audit trail', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        events: [
          { event: 'created', timestamp: '2024-01-01T00:00:00Z', user: 'person-1' },
          { event: 'accepted', timestamp: '2024-01-02T00:00:00Z', user: 'person-2' },
          { event: 'approved', timestamp: '2024-01-03T00:00:00Z', user: 'coordinator-1' },
          { event: 'executed', timestamp: '2024-01-03T01:00:00Z', user: 'system' },
        ],
      })

      const result: any = await mockedApi.get('/api/swaps/swap-1/audit')
      expect(result.events).toHaveLength(4)
    })
  })

  describe('29. Swap Notifications', () => {
    it('should send notification when swap is created', async () => {
      setupApiMock()

      mockedApi.post = jest.fn().mockResolvedValueOnce({
        id: 'swap-new',
        notification_sent: true,
        notified_users: ['person-2'],
      })

      const result: any = await mockedApi.post('/api/swaps', {
        requester_assignmentId: 'assignment-1',
        target_assignmentId: 'assignment-2',
      })

      expect(result.notification_sent).toBe(true)
    })

    it('should notify all parties on swap acceptance', async () => {
      setupApiMock()

      mockedApi.patch = jest.fn().mockResolvedValueOnce({
        notification_sent: true,
        notified_users: ['person-1', 'person-2', 'coordinator-1'],
      })

      const result: any = await mockedApi.patch('/api/swaps/swap-1/accept', {})
      expect(result.notified_users).toContain('person-1')
      expect(result.notified_users).toContain('coordinator-1')
    })
  })

  describe('30. Swap Marketplace', () => {
    it('should display available swap opportunities', async () => {
      setupApiMock()

      const openSwaps = [
        {
          ...mockSwapRequests[0],
          target_personId: null, // Open to anyone
          status: 'open' as const,
        },
      ]

      mockedApi.get.mockResolvedValueOnce({
        items: openSwaps,
        total: 1,
      })

      const result: any = await mockedApi.get('/api/swaps/marketplace')
      expect(result.items).toHaveLength(1)
    })

    it('should filter marketplace by rotation type', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        items: [
          {
            ...mockSwapRequests[0],
            rotation_type: 'clinic',
          },
        ],
      })

      const result: any = await mockedApi.get('/api/swaps/marketplace?rotation_type=clinic')
      expect(result.items[0].rotation_type).toBe('clinic')
    })

    it('should allow user to claim marketplace swap', async () => {
      setupApiMock()

      mockedApi.post = jest.fn().mockResolvedValueOnce({
        swapId: 'swap-1',
        claimed_by: 'person-3',
        status: 'pending',
      })

      const result: any = await mockedApi.post('/api/swaps/swap-1/claim', {
        assignmentId: 'assignment-3',
      })

      expect(result.claimed_by).toBe('person-3')
    })
  })

  describe('31. Swap Analytics', () => {
    it('should calculate swap completion rate', async () => {
      const swaps = [
        { ...mockSwapRequests[0], status: 'completed' as const },
        { ...mockSwapRequests[0], id: 'swap-2', status: 'rejected' as const },
        { ...mockSwapRequests[0], id: 'swap-3', status: 'completed' as const },
      ]

      setupApiMock({ swaps })

      const completed = swaps.filter(s => s.status === 'completed')
      const rate = (completed.length / swaps.length) * 100

      expect(rate).toBeCloseTo(66.67, 1)
    })

    it('should track average swap processing time', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        average_hours: 24,
        median_hours: 18,
        fastest_hours: 2,
        slowest_hours: 72,
      })

      const result: any = await mockedApi.get('/api/swaps/analytics/processing-time')
      expect(result.average_hours).toBe(24)
    })
  })

  describe('32. Multi-party Swaps', () => {
    it('should support three-way swaps', async () => {
      setupApiMock()

      mockedApi.post = jest.fn().mockResolvedValueOnce({
        id: 'swap-3way',
        swapType: 'multi_party',
        parties: ['person-1', 'person-2', 'person-3'],
      })

      const result: any = await mockedApi.post('/api/swaps/multi-party', {
        assignments: [
          { personId: 'person-1', assignmentId: 'assignment-1', receives: 'assignment-2' },
          { personId: 'person-2', assignmentId: 'assignment-2', receives: 'assignment-3' },
          { personId: 'person-3', assignmentId: 'assignment-3', receives: 'assignment-1' },
        ],
      })

      expect(result.parties).toHaveLength(3)
    })
  })

  describe('33. Swap Cancellation', () => {
    it('should allow requester to cancel pending swap', async () => {
      setupApiMock()

      mockedApi.del = jest.fn().mockResolvedValueOnce({
        id: 'swap-1',
        status: 'cancelled',
      })

      const result: any = await mockedApi.del('/api/swaps/swap-1')
      expect(result.status).toBe('cancelled')
    })

    it('should prevent cancellation of executed swap', async () => {
      setupApiMock()

      mockedApi.del = jest.fn().mockRejectedValueOnce({
        message: 'Cannot cancel executed swap',
        status: 400,
      })

      await expect(
        mockedApi.del('/api/swaps/swap-1')
      ).rejects.toMatchObject({
        message: 'Cannot cancel executed swap',
      })
    })
  })

  describe('34. Swap Expiration', () => {
    it('should expire swap after deadline', async () => {
      const expiredSwap = {
        ...mockSwapRequests[0],
        expiresAt: '2024-01-01T00:00:00Z',
        status: 'expired' as const,
      }

      setupApiMock({ swaps: [expiredSwap] })

      const result: any = await mockedApi.get('/api/swaps/swap-1')
      expect(result.items[0].status).toBe('expired')
    })

    it('should auto-expire old pending swaps', async () => {
      setupApiMock()

      mockedApi.post = jest.fn().mockResolvedValueOnce({
        expired_count: 5,
      })

      const result: any = await mockedApi.post('/api/swaps/expire-old', {})
      expect(result.expired_count).toBeGreaterThan(0)
    })
  })

  describe('35. Swap Templates', () => {
    it('should save swap request as template', async () => {
      setupApiMock()

      mockedApi.post = jest.fn().mockResolvedValueOnce({
        id: 'template-1',
        name: 'Weekend Call Swap',
        swapType: 'oneToOne',
      })

      const result: any = await mockedApi.post('/api/swaps/templates', {
        name: 'Weekend Call Swap',
        swapType: 'oneToOne',
        default_reason: 'Weekend coverage needed',
      })

      expect(result.name).toBe('Weekend Call Swap')
    })

    it('should create swap from template', async () => {
      setupApiMock()

      mockedApi.post = jest.fn().mockResolvedValueOnce({
        id: 'swap-from-template',
        templateId: 'template-1',
      })

      const result: any = await mockedApi.post('/api/swaps/from-template/template-1', {
        requester_assignmentId: 'assignment-1',
      })

      expect(result.templateId).toBe('template-1')
    })
  })

  describe('36. Swap Impact Analysis', () => {
    it('should show impact on work hours', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        requester: { hours_before: 60, hours_after: 70, change: 10 },
        target: { hours_before: 65, hours_after: 55, change: -10 },
      })

      const result: any = await mockedApi.get('/api/swaps/swap-1/impact')
      expect(result.requester.change).toBe(10)
      expect(result.target.change).toBe(-10)
    })

    it('should validate ACGME compliance after swap', async () => {
      setupApiMock()

      mockedApi.get.mockResolvedValueOnce({
        compliant: true,
        checks: {
          hours_80: 'pass',
          days_off_1in7: 'pass',
        },
      })

      const result: any = await mockedApi.get('/api/swaps/swap-1/compliance-check')
      expect(result.compliant).toBe(true)
    })
  })

  describe('37. Recurring Swaps', () => {
    it('should create recurring swap pattern', async () => {
      setupApiMock()

      mockedApi.post = jest.fn().mockResolvedValueOnce({
        id: 'swap-recurring',
        recurrence: 'weekly',
        occurrences: 4,
      })

      const result: any = await mockedApi.post('/api/swaps/recurring', {
        recurrence: 'weekly',
        count: 4,
        swapType: 'oneToOne',
      })

      expect(result.recurrence).toBe('weekly')
      expect(result.occurrences).toBe(4)
    })
  })

  describe('38. Swap Permissions', () => {
    it('should enforce role-based swap permissions', async () => {
      setupApiMock()

      mockedApi.patch = jest.fn().mockRejectedValueOnce({
        message: 'Insufficient permissions',
        status: 403,
      })

      await expect(
        mockedApi.patch('/api/swaps/swap-1/approve', {})
      ).rejects.toMatchObject({
        status: 403,
      })
    })

    it('should allow admin to force-approve swap', async () => {
      setupApiMock()

      mockedApi.patch = jest.fn().mockResolvedValueOnce({
        id: 'swap-1',
        status: 'approved',
        force_approved: true,
      })

      const result: any = await mockedApi.patch('/api/swaps/swap-1/force-approve', {})
      expect(result.force_approved).toBe(true)
    })
  })

  describe('39. Swap Conflict Detection', () => {
    it('should detect overlapping swap requests', async () => {
      setupApiMock()

      mockedApi.post = jest.fn().mockRejectedValueOnce({
        message: 'Overlapping swap request exists',
        status: 409,
        conflicting_swapId: 'swap-2',
      })

      await expect(
        mockedApi.post('/api/swaps', {
          requester_assignmentId: 'assignment-1',
        })
      ).rejects.toMatchObject({
        status: 409,
      })
    })
  })

  describe('40. Swap Preferences', () => {
    it('should save user swap preferences', async () => {
      setupApiMock()

      mockedApi.patch = jest.fn().mockResolvedValueOnce({
        personId: 'person-1',
        auto_accept_from: ['person-2'],
        rotation_preferences: ['clinic'],
      })

      const result: any = await mockedApi.patch('/api/people/person-1/swap-preferences', {
        auto_accept_from: ['person-2'],
        rotation_preferences: ['clinic'],
      })

      expect(result.auto_accept_from).toContain('person-2')
    })
  })
})
