/**
 * Mock Data for Audit Feature Tests
 *
 * Provides realistic test data for audit log components
 */

import type {
  AuditLogEntry,
  AuditLogResponse,
  AuditStatistics,
  AuditUser,
  TimelineEvent,
} from '@/features/audit/types';

// ============================================================================
// Mock Users
// ============================================================================

export const mockUsers: AuditUser[] = [
  {
    id: 'user-1',
    name: 'Dr. Sarah Chen',
    email: 'sarah.chen@hospital.edu',
    role: 'Program Director',
  },
  {
    id: 'user-2',
    name: 'Dr. Michael Rodriguez',
    email: 'michael.rodriguez@hospital.edu',
    role: 'Chief Resident',
  },
  {
    id: 'user-3',
    name: 'Dr. Emily Johnson',
    email: 'emily.johnson@hospital.edu',
    role: 'Faculty',
  },
  {
    id: 'user-4',
    name: 'Admin User',
    email: 'admin@hospital.edu',
    role: 'Administrator',
  },
];

// ============================================================================
// Mock Audit Log Entries
// ============================================================================

export const mockAuditLogs: AuditLogEntry[] = [
  {
    id: 'audit-1',
    timestamp: '2025-12-17T10:30:00Z',
    entityType: 'assignment',
    entityId: 'assign-123',
    entityName: 'Dr. John Doe - ICU',
    action: 'create',
    severity: 'info',
    user: mockUsers[0],
    changes: [
      {
        field: 'assignmentDate',
        oldValue: null,
        newValue: '2025-12-20',
        displayName: 'Assignment Date',
      },
      {
        field: 'rotation',
        oldValue: null,
        newValue: 'ICU',
        displayName: 'Rotation',
      },
    ],
    metadata: {
      duration: '2 weeks',
      shift: 'day',
    },
    ipAddress: '192.168.1.100',
    sessionId: 'session-abc123',
    reason: 'New resident assignment for December',
  },
  {
    id: 'audit-2',
    timestamp: '2025-12-17T09:15:00Z',
    entityType: 'person',
    entityId: 'person-456',
    entityName: 'Dr. Jane Smith',
    action: 'update',
    severity: 'info',
    user: mockUsers[1],
    changes: [
      {
        field: 'pgyLevel',
        oldValue: 2,
        newValue: 3,
        displayName: 'PGY Level',
      },
    ],
    ipAddress: '192.168.1.101',
    reason: 'Annual progression update',
  },
  {
    id: 'audit-3',
    timestamp: '2025-12-17T08:45:00Z',
    entityType: 'assignment',
    entityId: 'assign-789',
    entityName: 'Dr. Mike Wilson - ER',
    action: 'override',
    severity: 'warning',
    user: mockUsers[0],
    acgmeOverride: true,
    acgmeJustification: 'Emergency coverage needed due to unexpected absence. Resident agreed to extra shift.',
    changes: [
      {
        field: 'hours_worked',
        oldValue: 78,
        newValue: 82,
        displayName: 'Hours Worked',
      },
    ],
    reason: 'ACGME hour limit override for emergency coverage',
  },
  {
    id: 'audit-4',
    timestamp: '2025-12-16T16:20:00Z',
    entityType: 'absence',
    entityId: 'absence-101',
    entityName: 'Dr. Alice Brown - Vacation',
    action: 'delete',
    severity: 'info',
    user: mockUsers[2],
    changes: [
      {
        field: 'startDate',
        oldValue: '2025-12-25',
        newValue: null,
        displayName: 'Start Date',
      },
      {
        field: 'endDate',
        oldValue: '2025-12-27',
        newValue: null,
        displayName: 'End Date',
      },
    ],
    reason: 'Vacation request cancelled by resident',
  },
  {
    id: 'audit-5',
    timestamp: '2025-12-16T14:00:00Z',
    entityType: 'scheduleRun',
    entityId: 'schedule-202',
    entityName: 'January 2026 Schedule',
    action: 'scheduleGenerate',
    severity: 'info',
    user: mockUsers[0],
    metadata: {
      totalAssignments: 245,
      residents_count: 35,
      violations: 0,
      generation_time: '3.2s',
    },
    reason: 'Monthly schedule generation for January',
  },
  {
    id: 'audit-6',
    timestamp: '2025-12-16T13:30:00Z',
    entityType: 'rotationTemplate',
    entityId: 'template-303',
    entityName: 'ICU Rotation Template',
    action: 'update',
    severity: 'info',
    user: mockUsers[2],
    changes: [
      {
        field: 'min_residents',
        oldValue: 3,
        newValue: 4,
        displayName: 'Minimum Residents',
      },
      {
        field: 'maxResidents',
        oldValue: 6,
        newValue: 7,
        displayName: 'Maximum Residents',
      },
    ],
    reason: 'Increased capacity for ICU rotation',
  },
  {
    id: 'audit-7',
    timestamp: '2025-12-16T11:00:00Z',
    entityType: 'assignment',
    entityId: 'assign-404',
    entityName: 'Dr. Tom Anderson - Surgery',
    action: 'override',
    severity: 'critical',
    user: mockUsers[0],
    acgmeOverride: true,
    acgmeJustification: 'Critical staffing shortage. Multiple attendings consulted. Resident well-rested and volunteered.',
    changes: [
      {
        field: 'consecutive_days',
        oldValue: 6,
        newValue: 7,
        displayName: 'Consecutive Days',
      },
    ],
    reason: 'Emergency staffing requirement due to multiple sick calls',
  },
  {
    id: 'audit-8',
    timestamp: '2025-12-15T17:45:00Z',
    entityType: 'person',
    entityId: 'person-505',
    action: 'bulkImport',
    severity: 'info',
    user: mockUsers[3],
    metadata: {
      count: 15,
      source: 'CSV Import',
      duplicates_skipped: 2,
    },
    reason: 'Importing new incoming residents for July',
  },
  {
    id: 'audit-9',
    timestamp: '2025-12-15T15:20:00Z',
    entityType: 'block',
    entityId: 'block-606',
    entityName: 'December 2025 Block 2',
    action: 'create',
    severity: 'info',
    user: mockUsers[0],
    changes: [
      {
        field: 'startDate',
        oldValue: null,
        newValue: '2025-12-15',
        displayName: 'Start Date',
      },
      {
        field: 'endDate',
        oldValue: null,
        newValue: '2025-12-28',
        displayName: 'End Date',
      },
    ],
    reason: 'Creating new block schedule period',
  },
  {
    id: 'audit-10',
    timestamp: '2025-12-15T14:00:00Z',
    entityType: 'system',
    entityId: 'system-707',
    action: 'login',
    severity: 'info',
    user: mockUsers[1],
    ipAddress: '192.168.1.105',
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
    reason: 'User login',
  },
  {
    id: 'audit-11',
    timestamp: '2025-12-15T10:30:00Z',
    entityType: 'assignment',
    entityId: 'assign-808',
    action: 'bulkDelete',
    severity: 'warning',
    user: mockUsers[0],
    metadata: {
      count: 12,
      reason: 'Schedule revision',
    },
    reason: 'Removing assignments for schedule regeneration',
  },
  {
    id: 'audit-12',
    timestamp: '2025-12-14T16:00:00Z',
    entityType: 'scheduleRun',
    entityId: 'schedule-909',
    entityName: 'December 2025 Schedule',
    action: 'scheduleValidate',
    severity: 'warning',
    user: mockUsers[0],
    metadata: {
      violations: 3,
      warnings: 7,
      passed: false,
    },
    reason: 'Schedule validation found ACGME violations',
  },
  {
    id: 'audit-13',
    timestamp: '2025-12-14T14:30:00Z',
    entityType: 'absence',
    entityId: 'absence-1010',
    entityName: 'Dr. Rachel Green - Sick Leave',
    action: 'restore',
    severity: 'info',
    user: mockUsers[2],
    reason: 'Restored accidentally deleted absence record',
  },
  {
    id: 'audit-14',
    timestamp: '2025-12-14T10:00:00Z',
    entityType: 'system',
    entityId: 'system-1111',
    action: 'export',
    severity: 'info',
    user: mockUsers[0],
    metadata: {
      format: 'CSV',
      records: 150,
      dateRange: '2025-11-01 to 2025-12-01',
    },
    reason: 'Monthly compliance report export',
  },
  {
    id: 'audit-15',
    timestamp: '2025-12-13T13:00:00Z',
    entityType: 'person',
    entityId: 'person-1212',
    entityName: 'Dr. James Wilson',
    action: 'create',
    severity: 'info',
    user: mockUsers[3],
    changes: [
      {
        field: 'name',
        oldValue: null,
        newValue: 'Dr. James Wilson',
        displayName: 'Name',
      },
      {
        field: 'type',
        oldValue: null,
        newValue: 'resident',
        displayName: 'Type',
      },
      {
        field: 'pgyLevel',
        oldValue: null,
        newValue: 1,
        displayName: 'PGY Level',
      },
    ],
    reason: 'New resident added to program',
  },
];

// ============================================================================
// Mock Paginated Response
// ============================================================================

export const mockAuditLogResponse: AuditLogResponse = {
  items: mockAuditLogs.slice(0, 10),
  total: mockAuditLogs.length,
  page: 1,
  pageSize: 10,
  totalPages: 2,
};

// ============================================================================
// Mock Statistics
// ============================================================================

export const mockStatistics: AuditStatistics = {
  totalEntries: 150,
  entriesByAction: {
    create: 35,
    update: 45,
    delete: 12,
    override: 8,
    restore: 3,
    bulkImport: 5,
    bulkDelete: 4,
    scheduleGenerate: 15,
    scheduleValidate: 15,
    login: 5,
    logout: 2,
    export: 1,
  },
  entriesByEntityType: {
    assignment: 60,
    person: 30,
    absence: 20,
    rotationTemplate: 15,
    scheduleRun: 20,
    block: 3,
    system: 2,
  },
  entriesBySeverity: {
    info: 130,
    warning: 15,
    critical: 5,
  },
  acgmeOverrideCount: 8,
  uniqueUsers: 12,
  dateRange: {
    start: '2025-11-01',
    end: '2025-12-17',
  },
};

// ============================================================================
// Mock Timeline Events
// ============================================================================

export const mockTimelineEvents: TimelineEvent[] = mockAuditLogs.map((log) => ({
  id: log.id,
  timestamp: log.timestamp,
  title: `${log.entityName || log.entityType} ${log.action}`,
  description: log.reason || `${log.action} ${log.entityType}`,
  entityType: log.entityType,
  action: log.action,
  severity: log.severity,
  user: log.user,
}));

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Get a subset of mock logs for testing
 */
export function getMockLogs(count: number = 5): AuditLogEntry[] {
  return mockAuditLogs.slice(0, count);
}

/**
 * Get mock logs filtered by entity type
 */
export function getMockLogsByEntityType(entityType: string): AuditLogEntry[] {
  return mockAuditLogs.filter((log) => log.entityType === entityType);
}

/**
 * Get mock logs with ACGME overrides
 */
export function getMockACGMEOverrideLogs(): AuditLogEntry[] {
  return mockAuditLogs.filter((log) => log.acgmeOverride);
}

/**
 * Get mock logs by severity
 */
export function getMockLogsBySeverity(severity: string): AuditLogEntry[] {
  return mockAuditLogs.filter((log) => log.severity === severity);
}

/**
 * Create a mock audit log entry with custom properties
 */
export function createMockAuditLog(
  overrides: Partial<AuditLogEntry> = {}
): AuditLogEntry {
  return {
    id: `audit-${Date.now()}`,
    timestamp: new Date().toISOString(),
    entityType: 'assignment',
    entityId: 'entity-123',
    action: 'create',
    severity: 'info',
    user: mockUsers[0],
    ...overrides,
  };
}
