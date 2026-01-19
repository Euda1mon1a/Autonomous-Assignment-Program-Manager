/**
 * PEC (Program Evaluation Committee) Types
 *
 * TypeScript interfaces for PEC operations following camelCase conventions.
 * Backend uses snake_case; axios interceptor handles conversion automatically.
 *
 * @see docs/design/PEC_OPERATIONS_DESIGN.md
 */

// ============ Core Types ============

export type PecMeetingType = 'quarterly' | 'annual' | 'special' | 'sentinel';
export type PecMeetingStatus = 'scheduled' | 'in_progress' | 'completed' | 'cancelled';
export type PecAgendaStatus = 'pending' | 'discussed' | 'deferred' | 'skipped';
export type PecActionPriority = 'low' | 'medium' | 'high' | 'critical';
export type PecActionStatus = 'open' | 'in_progress' | 'completed' | 'deferred' | 'cancelled';
export type PecDecisionType =
  | 'ProgramChange'
  | 'CurriculumChange'
  | 'PolicyChange'
  | 'NoChange'
  | 'Remediation'
  | 'Recognition';
export type PecAttendanceRole =
  | 'PD'
  | 'APD'
  | 'CoreFaculty'
  | 'ResidentRep'
  | 'Staff'
  | 'Guest';
export type PecCommandDisposition = 'Pending' | 'Approved' | 'Disapproved' | 'Modified';
export type PecDataSliceType =
  | 'RESIDENT_COHORT'
  | 'ROTATION'
  | 'SITE'
  | 'OUTCOME_KPI'
  | 'FACULTY'
  | 'CURRICULUM';
export type PecEvidenceSourceType =
  | 'BLOCK_METRICS'
  | 'ROTATION_EVALS'
  | 'DUTY_HOURS'
  | 'WELLNESS'
  | 'EXAM_SCORES'
  | 'INCIDENT_REPORTS'
  | 'SCHEDULE';

// ============ Meeting ============

export interface PecMeeting {
  id: string;
  meetingDate: string;
  academicYear: string; // "AY25-26"
  meetingType: PecMeetingType;
  focusAreas: string[];
  status: PecMeetingStatus;
  location?: string;
  notes?: string;
  createdById: string;
  createdAt: string;
  updatedAt: string;
  // Counts for list views
  attendanceCount: number;
  agendaItemCount: number;
  decisionCount: number;
  openActionCount: number;
}

export interface PecMeetingCreate {
  meetingDate: string;
  academicYear: string;
  meetingType?: PecMeetingType;
  focusAreas?: string[];
  location?: string;
  notes?: string;
}

export interface PecMeetingUpdate {
  meetingDate?: string;
  meetingType?: PecMeetingType;
  focusAreas?: string[];
  status?: PecMeetingStatus;
  location?: string;
  notes?: string;
}

export interface PecMeetingFilters {
  academicYear?: string;
  status?: PecMeetingStatus;
  meetingType?: PecMeetingType;
}

// ============ Attendance ============

export interface PecAttendance {
  id: string;
  meetingId: string;
  personId: string;
  personName: string;
  role: PecAttendanceRole;
  attended: boolean;
  notes?: string;
}

export interface PecAttendanceCreate {
  personId: string;
  role: PecAttendanceRole;
  attended?: boolean;
  notes?: string;
}

// ============ Agenda Item ============

export interface PecAgendaItem {
  id: string;
  meetingId: string;
  order: number;
  title: string;
  description?: string;
  durationMinutes: number;
  dataSliceType?: PecDataSliceType;
  dataSliceKey?: string;
  status: PecAgendaStatus;
  discussionNotes?: string;
}

export interface PecAgendaItemCreate {
  title: string;
  description?: string;
  durationMinutes?: number;
  dataSlice?: {
    type: PecDataSliceType;
    key: string;
  };
}

export interface PecAgendaItemUpdate {
  title?: string;
  description?: string;
  durationMinutes?: number;
  status?: PecAgendaStatus;
  discussionNotes?: string;
}

// ============ Decision ============

export interface PecEvidenceRef {
  sourceType: PecEvidenceSourceType;
  sourceId?: string;
  hyperlink?: string;
}

export interface PecDecision {
  id: string;
  meetingId: string;
  agendaItemId?: string;
  decisionType: PecDecisionType;
  summary: string;
  rationale: string;
  evidenceRefs: PecEvidenceRef[];
  requiresCommandApproval: boolean;
  commandDisposition?: PecCommandDisposition;
  commandNotes?: string;
  commandApprovedBy?: string;
  commandApprovedAt?: string;
  createdById: string;
  createdAt: string;
}

export interface PecDecisionCreate {
  agendaItemId?: string;
  decisionType: PecDecisionType;
  summary: string;
  rationale: string;
  evidenceRefs?: PecEvidenceRef[];
  requiresCommandApproval?: boolean;
}

// ============ Action Item ============

export interface PecActionItem {
  id: string;
  meetingId: string;
  decisionId?: string;
  description: string;
  ownerPersonId: string;
  ownerName: string;
  dueDate?: string;
  priority: PecActionPriority;
  status: PecActionStatus;
  completionNote?: string;
  completedAt?: string;
  createdAt: string;
  updatedAt: string;
  isOverdue: boolean;
}

export interface PecActionItemCreate {
  decisionId?: string;
  description: string;
  ownerPersonId: string;
  dueDate?: string;
  priority?: PecActionPriority;
}

export interface PecActionItemUpdate {
  description?: string;
  ownerPersonId?: string;
  dueDate?: string;
  priority?: PecActionPriority;
  status?: PecActionStatus;
  completionNote?: string;
}

export interface PecActionFilters {
  status?: PecActionStatus;
  priority?: PecActionPriority;
  ownerId?: string;
  overdue?: boolean;
}

// ============ Dashboard & Analytics ============

export interface PecDashboard {
  academicYear: string;
  totalResidents: number;
  residentsByPgy: Record<string, number>;
  upcomingMeetings: PecMeeting[];
  recentDecisions: PecDecision[];
  openActionItems: PecActionItem[];
  metrics: PecDashboardMetrics;
}

export interface PecDashboardMetrics {
  meetingsThisYear: number;
  decisionsThisYear: number;
  openActions: number;
  overdueActions: number;
  commandPendingCount: number;
  avgActionCompletionDays: number;
}

export interface ResidentPerformanceSlice {
  residentId: string;
  residentName: string;
  pgyLevel: number;
  academicYear: string;
  metrics: {
    overallScore: number;
    trajectory: number[]; // Monthly scores
    milestoneProgress: Record<string, number>;
    caseVolume: number;
    evaluationCount: number;
  };
  flags: PecFlag[];
}

export interface RotationQualitySlice {
  rotationId: string;
  rotationName: string;
  academicYear: string;
  metrics: {
    avgResidentRating: number;
    avgFacultyRating: number;
    caseVolumeAdequacy: number;
    educationalValue: number;
  };
  concerns: string[];
  recommendations: string[];
}

export interface PecFlag {
  type: 'Remediation' | 'Concern' | 'Recognition' | 'Improvement';
  date: string;
  summary: string;
  resolved: boolean;
}

// ============ API Response Types ============

export interface PecMeetingListResponse {
  items: PecMeeting[];
  total: number;
  page: number;
  pageSize: number;
}

export interface PecActionListResponse {
  items: PecActionItem[];
  total: number;
  page: number;
  pageSize: number;
}
