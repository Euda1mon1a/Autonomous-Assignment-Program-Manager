/**
 * Mock data factories for conflict resolution tests
 * Provides reusable mock data for conflict-related tests
 */

import type {
  Conflict,
  ConflictSeverity,
  ConflictType,
  ConflictStatus,
  ResolutionMethod,
  ResolutionSuggestion,
  ResolutionChange,
  ManualOverride,
  ConflictHistoryEntry,
  ConflictPattern,
  ConflictStatistics,
  ConflictFilters,
  AbsenceConflictDetails,
  SchedulingOverlapDetails,
  ACGMEViolationDetails,
  CapacityExceededDetails,
  BatchResolutionRequest,
  BatchResolutionResult,
} from '@/features/conflicts/types';

/**
 * Mock data factories
 */
export const conflictsMockFactories = {
  conflict: (overrides: Partial<Conflict> = {}): Conflict => ({
    id: 'conflict-1',
    type: 'absence_conflict' as ConflictType,
    severity: 'high' as ConflictSeverity,
    status: 'unresolved' as ConflictStatus,
    title: 'Assignment during absence',
    description: 'Dr. Smith is assigned while on vacation',
    affectedPersonIds: ['person-1'],
    affectedAssignmentIds: ['assignment-1'],
    affectedBlockIds: ['block-1'],
    conflictDate: '2024-02-15',
    conflictSession: 'AM',
    detectedAt: '2024-02-10T10:00:00Z',
    detectedBy: 'system',
    details: {
      personName: 'Dr. John Smith',
      personId: 'person-1',
      absenceType: 'vacation',
      absenceStart: '2024-02-14',
      absenceEnd: '2024-02-18',
      assignmentRotation: 'Inpatient Medicine',
    } as AbsenceConflictDetails,
    ...overrides,
  }),

  schedulingOverlapConflict: (overrides: Partial<Conflict> = {}): Conflict => ({
    id: 'conflict-2',
    type: 'scheduling_overlap',
    severity: 'critical',
    status: 'unresolved',
    title: 'Double-booked time slot',
    description: 'Dr. Doe is assigned to two rotations at the same time',
    affectedPersonIds: ['person-2'],
    affectedAssignmentIds: ['assignment-2', 'assignment-3'],
    affectedBlockIds: ['block-2'],
    conflictDate: '2024-02-20',
    conflictSession: 'PM',
    detectedAt: '2024-02-15T14:30:00Z',
    detectedBy: 'system',
    details: {
      personName: 'Dr. Jane Doe',
      personId: 'person-2',
      firstAssignment: {
        id: 'assignment-2',
        rotationName: 'Clinic',
        location: 'Main Hospital',
      },
      secondAssignment: {
        id: 'assignment-3',
        rotationName: 'ER',
        location: 'Emergency Department',
      },
    } as SchedulingOverlapDetails,
    ...overrides,
  }),

  acgmeViolationConflict: (overrides: Partial<Conflict> = {}): Conflict => ({
    id: 'conflict-3',
    type: 'acgmeViolation',
    severity: 'critical',
    status: 'unresolved',
    title: 'ACGME duty hour violation',
    description: 'Dr. Johnson exceeds 80-hour weekly limit',
    affectedPersonIds: ['person-3'],
    affectedAssignmentIds: ['assignment-4'],
    affectedBlockIds: ['block-3'],
    conflictDate: '2024-02-22',
    detectedAt: '2024-02-20T16:00:00Z',
    detectedBy: 'validation',
    details: {
      personName: 'Dr. Bob Johnson',
      personId: 'person-3',
      violationType: '80-hour weekly limit',
      currentValue: 85,
      limitValue: 80,
      unit: 'hours',
      periodStart: '2024-02-15',
      periodEnd: '2024-02-22',
    } as ACGMEViolationDetails,
    ...overrides,
  }),

  capacityExceededConflict: (overrides: Partial<Conflict> = {}): Conflict => ({
    id: 'conflict-4',
    type: 'capacity_exceeded',
    severity: 'medium',
    status: 'unresolved',
    title: 'Rotation capacity exceeded',
    description: 'Inpatient rotation has too many assigned residents',
    affectedPersonIds: ['person-4', 'person-5', 'person-6'],
    affectedAssignmentIds: ['assignment-5', 'assignment-6', 'assignment-7'],
    affectedBlockIds: ['block-4'],
    conflictDate: '2024-02-25',
    detectedAt: '2024-02-23T09:00:00Z',
    detectedBy: 'system',
    details: {
      rotationName: 'Inpatient Medicine',
      rotationId: 'rotation-1',
      currentCount: 5,
      maxCapacity: 4,
      assignedPeople: [
        { id: 'person-4', name: 'Dr. Alice Brown' },
        { id: 'person-5', name: 'Dr. Charlie Davis' },
        { id: 'person-6', name: 'Dr. Eve Wilson' },
      ],
    } as CapacityExceededDetails,
    ...overrides,
  }),

  resolutionChange: (overrides: Partial<ResolutionChange> = {}): ResolutionChange => ({
    type: 'reassign',
    entityType: 'assignment',
    entityId: 'assignment-1',
    description: 'Reassign Dr. Smith to different date',
    fromPersonId: 'person-1',
    fromPersonName: 'Dr. John Smith',
    toPersonId: 'person-2',
    toPersonName: 'Dr. Jane Doe',
    ...overrides,
  }),

  resolutionSuggestion: (overrides: Partial<ResolutionSuggestion> = {}): ResolutionSuggestion => ({
    id: 'suggestion-1',
    conflictId: 'conflict-1',
    method: 'manual_reassign' as ResolutionMethod,
    title: 'Reassign to available resident',
    description: 'Reassign this rotation to Dr. Doe who is available',
    impactScore: 15,
    confidence: 85,
    changes: [conflictsMockFactories.resolutionChange()],
    sideEffects: ['Dr. Doe will have 1 extra shift this month'],
    recommended: true,
    ...overrides,
  }),

  manualOverride: (overrides: Partial<ManualOverride> = {}): ManualOverride => ({
    conflictId: 'conflict-1',
    overrideType: 'temporary',
    reason: 'emergency_coverage',
    justification: 'Required for emergency coverage during unexpected absence',
    expiresAt: '2024-03-01T00:00:00Z',
    isAcgmeRelated: false,
    supervisorApprovalRequired: true,
    supervisorApproved: false,
    ...overrides,
  }),

  conflictHistoryEntry: (overrides: Partial<ConflictHistoryEntry> = {}): ConflictHistoryEntry => ({
    id: 'history-1',
    conflictId: 'conflict-1',
    action: 'detected',
    timestamp: '2024-02-10T10:00:00Z',
    userId: 'system',
    userName: 'System',
    changes: {},
    notes: 'Conflict automatically detected during validation',
    ...overrides,
  }),

  conflictPattern: (overrides: Partial<ConflictPattern> = {}): ConflictPattern => ({
    id: 'pattern-1',
    type: 'absence_conflict',
    frequency: 5,
    firstOccurrence: '2024-01-15T00:00:00Z',
    lastOccurrence: '2024-02-10T00:00:00Z',
    affectedPeople: [
      { id: 'person-1', name: 'Dr. John Smith', occurrenceCount: 3 },
      { id: 'person-2', name: 'Dr. Jane Doe', occurrenceCount: 2 },
    ],
    rootCause: 'Vacation periods not properly blocked in schedule',
    suggestedPrevention: 'Implement automatic blocking of vacation periods during scheduling',
    ...overrides,
  }),

  conflictStatistics: (overrides: Partial<ConflictStatistics> = {}): ConflictStatistics => ({
    totalConflicts: 24,
    bySeverity: {
      critical: 3,
      high: 8,
      medium: 10,
      low: 3,
    },
    byType: {
      scheduling_overlap: 5,
      acgmeViolation: 3,
      supervision_missing: 2,
      capacity_exceeded: 4,
      absence_conflict: 6,
      qualification_mismatch: 2,
      consecutive_duty: 1,
      rest_period: 1,
      coverage_gap: 0,
    },
    byStatus: {
      unresolved: 12,
      pending_review: 5,
      resolved: 6,
      ignored: 1,
    },
    resolutionRate: 75.5,
    averageResolutionTimeHours: 18.5,
    mostAffectedPeople: [
      { id: 'person-1', name: 'Dr. John Smith', conflictCount: 5 },
      { id: 'person-2', name: 'Dr. Jane Doe', conflictCount: 4 },
      { id: 'person-3', name: 'Dr. Bob Johnson', conflictCount: 3 },
    ],
    trendingUp: false,
    ...overrides,
  }),

  conflictFilters: (overrides: Partial<ConflictFilters> = {}): ConflictFilters => ({
    types: ['absence_conflict', 'scheduling_overlap'],
    severities: ['critical', 'high'],
    statuses: ['unresolved'],
    dateRange: {
      start: '2024-02-01',
      end: '2024-02-28',
    },
    ...overrides,
  }),

  batchResolutionRequest: (
    overrides: Partial<BatchResolutionRequest> = {}
  ): BatchResolutionRequest => ({
    conflictIds: ['conflict-1', 'conflict-2', 'conflict-3'],
    resolutionMethod: 'manual_reassign',
    notes: 'Batch resolution for similar conflicts',
    ...overrides,
  }),

  batchResolutionResult: (
    overrides: Partial<BatchResolutionResult> = {}
  ): BatchResolutionResult => ({
    total: 3,
    successful: 2,
    failed: 1,
    results: [
      {
        conflictId: 'conflict-1',
        success: true,
        message: 'Successfully resolved',
        resolution: conflictsMockFactories.resolutionSuggestion(),
      },
      {
        conflictId: 'conflict-2',
        success: true,
        message: 'Successfully resolved',
      },
      {
        conflictId: 'conflict-3',
        success: false,
        message: 'Failed to resolve: No available alternatives',
      },
    ],
    ...overrides,
  }),
};

/**
 * Mock API responses
 */
export const conflictsMockResponses = {
  conflicts: {
    items: [
      conflictsMockFactories.conflict(),
      conflictsMockFactories.schedulingOverlapConflict(),
      conflictsMockFactories.acgmeViolationConflict(),
    ],
    total: 3,
  },

  statistics: conflictsMockFactories.conflictStatistics(),

  suggestions: [
    conflictsMockFactories.resolutionSuggestion(),
    conflictsMockFactories.resolutionSuggestion({
      id: 'suggestion-2',
      method: 'cancel_assignment',
      title: 'Cancel assignment',
      description: 'Cancel this assignment and leave slot empty',
      impactScore: 30,
      confidence: 70,
      recommended: false,
    }),
  ],

  history: [
    conflictsMockFactories.conflictHistoryEntry(),
    conflictsMockFactories.conflictHistoryEntry({
      id: 'history-2',
      action: 'updated',
      timestamp: '2024-02-11T11:00:00Z',
      userId: 'user-1',
      userName: 'Admin User',
      changes: {
        status: { from: 'unresolved', to: 'pending_review' },
      },
      notes: 'Marked for manual review',
    }),
    conflictsMockFactories.conflictHistoryEntry({
      id: 'history-3',
      action: 'resolved',
      timestamp: '2024-02-12T14:30:00Z',
      userId: 'user-1',
      userName: 'Admin User',
      changes: {
        status: { from: 'pending_review', to: 'resolved' },
      },
      notes: 'Reassigned to alternative resident',
    }),
  ],

  patterns: [
    conflictsMockFactories.conflictPattern(),
    conflictsMockFactories.conflictPattern({
      id: 'pattern-2',
      type: 'scheduling_overlap',
      frequency: 3,
      rootCause: 'Manual scheduling without validation',
      suggestedPrevention: 'Enable real-time conflict detection during scheduling',
    }),
  ],

  batchResult: conflictsMockFactories.batchResolutionResult(),
};
