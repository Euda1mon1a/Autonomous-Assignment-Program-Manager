/**
 * Template Library Types
 *
 * Defines types for the schedule template library system including
 * schedule templates, assignment patterns, categories, and sharing.
 */

// Template Categories
export type TemplateCategory =
  | 'schedule'
  | 'assignment'
  | 'rotation'
  | 'call'
  | 'clinic'
  | 'custom';

export type TemplateVisibility = 'private' | 'shared' | 'public';

export type TemplateStatus = 'draft' | 'active' | 'archived';

// Assignment Pattern for templates
export interface AssignmentPattern {
  id: string;
  name: string;
  dayOfWeek: number; // 0-6, where 0 is Sunday
  timeOfDay: 'AM' | 'PM' | 'ALL';
  rotationTemplateId?: string;
  activityType: string;
  role: 'primary' | 'supervising' | 'backup';
  requiredPgyLevels?: number[];
  notes?: string;
}

// Schedule Template - main template type
export interface ScheduleTemplate {
  id: string;
  name: string;
  description?: string;
  category: TemplateCategory;
  visibility: TemplateVisibility;
  status: TemplateStatus;

  // Template configuration
  durationWeeks: number;
  startDayOfWeek: number; // 0-6
  patterns: AssignmentPattern[];

  // Constraints
  maxResidentsPerDay?: number;
  requiresSupervision: boolean;
  allowWeekends: boolean;
  allowHolidays: boolean;

  // Metadata
  tags: string[];
  createdBy: string;
  createdAt: string;
  updatedAt: string;
  usageCount: number;

  // Sharing
  sharedWith?: string[];
  isPublic: boolean;

  // Source tracking (for duplicated templates)
  sourceTemplateId?: string;
  version: number;
}

// Template for creating a new schedule template
export interface ScheduleTemplateCreate {
  name: string;
  description?: string;
  category: TemplateCategory;
  visibility?: TemplateVisibility;
  durationWeeks: number;
  startDayOfWeek?: number;
  patterns?: Omit<AssignmentPattern, 'id'>[];
  maxResidentsPerDay?: number;
  requiresSupervision?: boolean;
  allowWeekends?: boolean;
  allowHolidays?: boolean;
  tags?: string[];
}

// Template for updating a schedule template
export interface ScheduleTemplateUpdate {
  name?: string;
  description?: string;
  category?: TemplateCategory;
  visibility?: TemplateVisibility;
  status?: TemplateStatus;
  durationWeeks?: number;
  startDayOfWeek?: number;
  patterns?: AssignmentPattern[];
  maxResidentsPerDay?: number;
  requiresSupervision?: boolean;
  allowWeekends?: boolean;
  allowHolidays?: boolean;
  tags?: string[];
  sharedWith?: string[];
  isPublic?: boolean;
}

// Template preview configuration
export interface TemplatePreviewConfig {
  startDate: Date;
  endDate: Date;
  showConflicts: boolean;
  highlightPatterns: boolean;
}

// Template application result
export interface TemplateApplicationResult {
  success: boolean;
  assignmentsCreated: number;
  assignmentsFailed: number;
  conflicts: TemplateConflict[];
  warnings: string[];
}

// Template conflict during application
export interface TemplateConflict {
  date: string;
  timeOfDay: 'AM' | 'PM';
  patternName: string;
  conflictType: 'overlap' | 'constraint_violation' | 'absence' | 'capacity';
  message: string;
  resolution?: 'skip' | 'override' | 'manual';
}

// Template search/filter options
export interface TemplateFilters {
  category?: TemplateCategory;
  visibility?: TemplateVisibility;
  status?: TemplateStatus;
  searchQuery?: string;
  tags?: string[];
  createdBy?: string;
  sortBy?: 'name' | 'createdAt' | 'updatedAt' | 'usageCount';
  sortOrder?: 'asc' | 'desc';
}

// Category metadata for UI display
export interface CategoryInfo {
  id: TemplateCategory;
  name: string;
  description: string;
  icon: string;
  color: string;
}

// Template share request
export interface TemplateShareRequest {
  templateId: string;
  userIds?: string[];
  makePublic?: boolean;
}

// Template duplicate request
export interface TemplateDuplicateRequest {
  templateId: string;
  newName?: string;
  includePatterns?: boolean;
}

// Template list response
export interface TemplateListResponse {
  items: ScheduleTemplate[];
  total: number;
  page: number;
  pageSize: number;
}

// Template statistics
export interface TemplateStatistics {
  totalTemplates: number;
  byCategory: Record<TemplateCategory, number>;
  byStatus: Record<TemplateStatus, number>;
  mostUsed: ScheduleTemplate[];
  recentlyCreated: ScheduleTemplate[];
}

// Predefined template (system templates)
export interface PredefinedTemplate extends Omit<ScheduleTemplate, 'id' | 'createdBy' | 'createdAt' | 'updatedAt'> {
  templateKey: string;
  isSystem: true;
}
