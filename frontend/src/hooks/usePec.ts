/**
 * PEC (Program Evaluation Committee) React Query Hooks
 *
 * Mock-first implementation. Toggle NEXT_PUBLIC_PEC_MOCK_MODE=false
 * when backend routes are ready.
 *
 * @see docs/design/PEC_OPERATIONS_DESIGN.md
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type {
  PecMeeting,
  PecMeetingFilters,
  PecActionItem,
  PecActionFilters,
  PecDashboard,
  PecDecision,
  PecMeetingCreate,
  PecActionItemCreate,
  PecActionItemUpdate,
} from '@/types/pec';
// import { get, post, patch } from '@/lib/api';
// import type { ApiError } from '@/lib/api';

// ============ Feature Flag ============

const USE_MOCK_DATA = process.env.NEXT_PUBLIC_PEC_MOCK_MODE !== 'false';

// ============ Query Keys ============

export const pecQueryKeys = {
  all: ['pec'] as const,
  dashboard: (academicYear: string) => ['pec', 'dashboard', academicYear] as const,
  meetings: (filters?: PecMeetingFilters) => ['pec', 'meetings', filters] as const,
  meeting: (id: string) => ['pec', 'meeting', id] as const,
  actions: (filters?: PecActionFilters) => ['pec', 'actions', filters] as const,
  action: (id: string) => ['pec', 'action', id] as const,
  decisions: (meetingId: string) => ['pec', 'decisions', meetingId] as const,
};

// ============ Mock Data ============

const MOCK_DASHBOARD: PecDashboard = {
  academicYear: 'AY25-26',
  totalResidents: 18,
  residentsByPgy: { '1': 6, '2': 6, '3': 6 },
  upcomingMeetings: [],
  recentDecisions: [],
  openActionItems: [],
  metrics: {
    meetingsThisYear: 3,
    decisionsThisYear: 12,
    openActions: 8,
    overdueActions: 2,
    commandPendingCount: 1,
    avgActionCompletionDays: 14,
  },
};

const MOCK_MEETINGS: PecMeeting[] = [
  {
    id: 'mtg-001',
    meetingDate: '2026-04-15',
    academicYear: 'AY25-26',
    meetingType: 'quarterly',
    focusAreas: ['PGY-1 Progress', 'OB Curriculum Review'],
    status: 'scheduled',
    location: 'Conference Room A',
    createdById: 'user-001',
    createdAt: '2026-01-10T10:00:00Z',
    updatedAt: '2026-01-10T10:00:00Z',
    attendanceCount: 0,
    agendaItemCount: 5,
    decisionCount: 0,
    openActionCount: 0,
  },
  {
    id: 'mtg-002',
    meetingDate: '2026-01-15',
    academicYear: 'AY25-26',
    meetingType: 'quarterly',
    focusAreas: ['Block 5 Review', 'Wellness Check'],
    status: 'completed',
    location: 'Virtual - Teams',
    createdById: 'user-001',
    createdAt: '2025-12-20T10:00:00Z',
    updatedAt: '2026-01-15T16:00:00Z',
    attendanceCount: 12,
    agendaItemCount: 8,
    decisionCount: 4,
    openActionCount: 3,
  },
  {
    id: 'mtg-003',
    meetingDate: '2025-10-15',
    academicYear: 'AY25-26',
    meetingType: 'annual',
    focusAreas: ['Annual Program Evaluation', 'Curriculum Goals'],
    status: 'completed',
    location: 'Conference Room B',
    createdById: 'user-001',
    createdAt: '2025-09-01T10:00:00Z',
    updatedAt: '2025-10-15T17:00:00Z',
    attendanceCount: 15,
    agendaItemCount: 12,
    decisionCount: 8,
    openActionCount: 2,
  },
];

const MOCK_ACTIONS: PecActionItem[] = [
  {
    id: 'act-001',
    meetingId: 'mtg-002',
    description: 'Review and update OB curriculum case log requirements',
    ownerPersonId: 'person-001',
    ownerName: 'Dr. Smith',
    dueDate: '2026-02-15',
    priority: 'high',
    status: 'open',
    createdAt: '2026-01-15T15:00:00Z',
    updatedAt: '2026-01-15T15:00:00Z',
    isOverdue: false,
  },
  {
    id: 'act-002',
    meetingId: 'mtg-002',
    description: 'Schedule remediation follow-up for PGY-2 resident',
    ownerPersonId: 'person-002',
    ownerName: 'Dr. Jones',
    dueDate: '2026-01-20',
    priority: 'critical',
    status: 'open',
    createdAt: '2026-01-15T15:30:00Z',
    updatedAt: '2026-01-15T15:30:00Z',
    isOverdue: true,
  },
  {
    id: 'act-003',
    meetingId: 'mtg-002',
    description: 'Coordinate wellness survey distribution',
    ownerPersonId: 'person-003',
    ownerName: 'Dr. Williams',
    dueDate: '2026-02-01',
    priority: 'medium',
    status: 'in_progress',
    createdAt: '2026-01-15T16:00:00Z',
    updatedAt: '2026-01-18T10:00:00Z',
    isOverdue: false,
  },
  {
    id: 'act-004',
    meetingId: 'mtg-003',
    description: 'Update program goals documentation',
    ownerPersonId: 'person-001',
    ownerName: 'Dr. Smith',
    dueDate: '2025-12-01',
    priority: 'high',
    status: 'completed',
    completionNote: 'Goals updated and posted to LMS',
    completedAt: '2025-11-28T14:00:00Z',
    createdAt: '2025-10-15T16:00:00Z',
    updatedAt: '2025-11-28T14:00:00Z',
    isOverdue: false,
  },
  {
    id: 'act-005',
    meetingId: 'mtg-003',
    description: 'Submit annual ACGME program update',
    ownerPersonId: 'person-004',
    ownerName: 'Dr. Chen',
    dueDate: '2025-11-15',
    priority: 'critical',
    status: 'completed',
    completionNote: 'Submitted via WebADS',
    completedAt: '2025-11-14T09:00:00Z',
    createdAt: '2025-10-15T16:30:00Z',
    updatedAt: '2025-11-14T09:00:00Z',
    isOverdue: false,
  },
];

const MOCK_DECISIONS: PecDecision[] = [
  {
    id: 'dec-001',
    meetingId: 'mtg-002',
    decisionType: 'CurriculumChange',
    summary: 'Increase minimum OB case log requirement from 200 to 240',
    rationale: 'Analysis shows residents need additional exposure for adequate preparation.',
    evidenceRefs: [{ sourceType: 'BLOCK_METRICS', sourceId: 'block-5' }],
    requiresCommandApproval: true,
    commandDisposition: 'Pending',
    createdById: 'user-001',
    createdAt: '2026-01-15T14:30:00Z',
  },
  {
    id: 'dec-002',
    meetingId: 'mtg-002',
    decisionType: 'PolicyChange',
    summary: 'Implement monthly wellness check-ins for all residents',
    rationale: 'Proactive wellness monitoring supports resident wellbeing.',
    evidenceRefs: [{ sourceType: 'WELLNESS' }],
    requiresCommandApproval: false,
    createdById: 'user-001',
    createdAt: '2026-01-15T15:00:00Z',
  },
];

// ============ Mock API Functions ============

const mockDelay = (ms: number = 300) => new Promise((resolve) => setTimeout(resolve, ms));

async function fetchMockDashboard(academicYear: string): Promise<PecDashboard> {
  await mockDelay();
  return {
    ...MOCK_DASHBOARD,
    academicYear,
    upcomingMeetings: MOCK_MEETINGS.filter((m) => m.status === 'scheduled'),
    recentDecisions: MOCK_DECISIONS.slice(0, 3),
    openActionItems: MOCK_ACTIONS.filter((a) => a.status === 'open' || a.status === 'in_progress'),
  };
}

async function fetchMockMeetings(filters?: PecMeetingFilters): Promise<PecMeeting[]> {
  await mockDelay();
  let meetings = [...MOCK_MEETINGS];
  if (filters?.academicYear) {
    meetings = meetings.filter((m) => m.academicYear === filters.academicYear);
  }
  if (filters?.status) {
    meetings = meetings.filter((m) => m.status === filters.status);
  }
  if (filters?.meetingType) {
    meetings = meetings.filter((m) => m.meetingType === filters.meetingType);
  }
  return meetings.sort(
    (a, b) => new Date(b.meetingDate).getTime() - new Date(a.meetingDate).getTime()
  );
}

async function fetchMockMeeting(id: string): Promise<PecMeeting | null> {
  await mockDelay();
  return MOCK_MEETINGS.find((m) => m.id === id) || null;
}

async function fetchMockActions(filters?: PecActionFilters): Promise<PecActionItem[]> {
  await mockDelay();
  let actions = [...MOCK_ACTIONS];
  if (filters?.status) {
    actions = actions.filter((a) => a.status === filters.status);
  }
  if (filters?.priority) {
    actions = actions.filter((a) => a.priority === filters.priority);
  }
  if (filters?.ownerId) {
    actions = actions.filter((a) => a.ownerPersonId === filters.ownerId);
  }
  if (filters?.overdue) {
    actions = actions.filter((a) => a.isOverdue);
  }
  return actions;
}

async function fetchMockDecisions(meetingId: string): Promise<PecDecision[]> {
  await mockDelay();
  return MOCK_DECISIONS.filter((d) => d.meetingId === meetingId);
}

// ============ Query Hooks ============

export function usePecDashboard(academicYear: string) {
  return useQuery({
    queryKey: pecQueryKeys.dashboard(academicYear),
    queryFn: async () => {
      if (USE_MOCK_DATA) {
        return fetchMockDashboard(academicYear);
      }
      // TODO: Replace with real API call when backend ready
      // return get<PecDashboard>(`/pec/dashboard?academic_year=${academicYear}`);
      return fetchMockDashboard(academicYear);
    },
    enabled: !!academicYear,
    staleTime: 60 * 1000,
  });
}

export function usePecMeetings(filters?: PecMeetingFilters) {
  return useQuery({
    queryKey: pecQueryKeys.meetings(filters),
    queryFn: async () => {
      if (USE_MOCK_DATA) {
        return fetchMockMeetings(filters);
      }
      // TODO: Real API call
      return fetchMockMeetings(filters);
    },
    staleTime: 30 * 1000,
  });
}

export function usePecMeeting(meetingId: string) {
  return useQuery({
    queryKey: pecQueryKeys.meeting(meetingId),
    queryFn: async () => {
      if (USE_MOCK_DATA) {
        return fetchMockMeeting(meetingId);
      }
      // TODO: Real API call
      return fetchMockMeeting(meetingId);
    },
    enabled: !!meetingId,
    staleTime: 30 * 1000,
  });
}

export function usePecActionItems(filters?: PecActionFilters) {
  return useQuery({
    queryKey: pecQueryKeys.actions(filters),
    queryFn: async () => {
      if (USE_MOCK_DATA) {
        return fetchMockActions(filters);
      }
      // TODO: Real API call
      return fetchMockActions(filters);
    },
    staleTime: 30 * 1000,
  });
}

export function usePecDecisions(meetingId: string) {
  return useQuery({
    queryKey: pecQueryKeys.decisions(meetingId),
    queryFn: async () => {
      if (USE_MOCK_DATA) {
        return fetchMockDecisions(meetingId);
      }
      // TODO: Real API call
      return fetchMockDecisions(meetingId);
    },
    enabled: !!meetingId,
    staleTime: 30 * 1000,
  });
}

// ============ Mutation Hooks (Stubs for Phase 2) ============

export function useCreatePecMeeting() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (_data: PecMeetingCreate) => {
      // TODO: Real API call
      // return post<PecMeeting>('/pec/meetings', data);
      throw new Error('Not implemented - backend required');
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: pecQueryKeys.meetings() });
      queryClient.invalidateQueries({ queryKey: pecQueryKeys.all });
    },
  });
}

export function useCreatePecAction() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (_data: PecActionItemCreate & { meetingId: string }) => {
      // TODO: Real API call
      throw new Error('Not implemented - backend required');
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: pecQueryKeys.actions() });
    },
  });
}

export function useUpdatePecActionStatus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (_data: { actionId: string; update: PecActionItemUpdate }) => {
      // TODO: Real API call
      throw new Error('Not implemented - backend required');
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: pecQueryKeys.actions() });
      queryClient.invalidateQueries({ queryKey: pecQueryKeys.all });
    },
  });
}

// ============ Helper Functions ============

export function getMeetingStatusColor(status: string): string {
  switch (status) {
    case 'scheduled':
      return 'text-blue-400 bg-blue-500/10 border-blue-500/30';
    case 'in_progress':
      return 'text-amber-400 bg-amber-500/10 border-amber-500/30';
    case 'completed':
      return 'text-green-400 bg-green-500/10 border-green-500/30';
    case 'cancelled':
      return 'text-slate-400 bg-slate-500/10 border-slate-500/30';
    default:
      return 'text-slate-400 bg-slate-500/10 border-slate-500/30';
  }
}

export function getMeetingTypeLabel(type: string): string {
  switch (type) {
    case 'quarterly':
      return 'Quarterly';
    case 'annual':
      return 'Annual';
    case 'special':
      return 'Special';
    case 'sentinel':
      return 'Sentinel Event';
    default:
      return type;
  }
}

export function getActionPriorityColor(priority: string): string {
  switch (priority) {
    case 'critical':
      return 'text-red-400 bg-red-500/10 border-red-500/30';
    case 'high':
      return 'text-orange-400 bg-orange-500/10 border-orange-500/30';
    case 'medium':
      return 'text-amber-400 bg-amber-500/10 border-amber-500/30';
    case 'low':
      return 'text-slate-400 bg-slate-500/10 border-slate-500/30';
    default:
      return 'text-slate-400 bg-slate-500/10 border-slate-500/30';
  }
}

export function getActionStatusColor(status: string): string {
  switch (status) {
    case 'open':
      return 'text-blue-400 bg-blue-500/10';
    case 'in_progress':
      return 'text-amber-400 bg-amber-500/10';
    case 'completed':
      return 'text-green-400 bg-green-500/10';
    case 'deferred':
      return 'text-purple-400 bg-purple-500/10';
    case 'cancelled':
      return 'text-slate-400 bg-slate-500/10';
    default:
      return 'text-slate-400 bg-slate-500/10';
  }
}

export function getCommandDispositionColor(disposition?: string): string {
  switch (disposition) {
    case 'Approved':
      return 'text-green-400 bg-green-500/10';
    case 'Pending':
      return 'text-amber-400 bg-amber-500/10';
    case 'Disapproved':
      return 'text-red-400 bg-red-500/10';
    case 'Modified':
      return 'text-purple-400 bg-purple-500/10';
    default:
      return 'text-slate-400 bg-slate-500/10';
  }
}
