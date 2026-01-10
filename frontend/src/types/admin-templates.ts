/**
 * Admin Templates Types
 *
 * Types for the admin rotation templates management interface including
 * template listing, bulk operations, preference management, and pattern editing.
 */

// ============================================================================
// Core Template Types
// ============================================================================

export type ActivityType =
  | 'clinic'
  | 'inpatient'
  | 'procedure'
  | 'procedures'
  | 'conference'
  | 'education'
  | 'lecture'
  | 'outpatient'
  | 'absence'
  | 'off'
  | 'recovery';

/**
 * Template category for UI grouping and filtering.
 *
 * - rotation: Clinical work (clinic, inpatient, outpatient, procedure)
 * - timeOff: ACGME-protected rest (off, recovery) - does NOT count toward away-from-program
 * - absence: Days away from program (absence activity type) - counts toward 28-day limit
 * - educational: Structured learning (conference, education, lecture)
 */
export type TemplateCategory = 'rotation' | 'timeOff' | 'absence' | 'educational';

export interface TemplateCategoryConfig {
  value: TemplateCategory;
  label: string;
  description: string;
  icon: string;
  activityTypes: ActivityType[];
}

export const TEMPLATE_CATEGORY_CONFIGS: TemplateCategoryConfig[] = [
  {
    value: 'rotation',
    label: 'Clinical Rotations',
    description: 'Assignable clinical work',
    icon: 'Stethoscope',
    activityTypes: ['clinic', 'inpatient', 'outpatient', 'procedure', 'procedures'],
  },
  {
    value: 'timeOff',
    label: 'Time Off',
    description: 'ACGME-protected rest (does NOT count toward away-from-program)',
    icon: 'Moon',
    activityTypes: ['off', 'recovery'],
  },
  {
    value: 'absence',
    label: 'Absences',
    description: 'Days away from program (counts toward 28-day limit)',
    icon: 'CalendarX',
    activityTypes: ['absence'],
  },
  {
    value: 'educational',
    label: 'Educational',
    description: 'Structured learning activities',
    icon: 'GraduationCap',
    activityTypes: ['conference', 'education', 'lecture'],
  },
];

export function getTemplateCategoryConfig(category: TemplateCategory): TemplateCategoryConfig {
  return TEMPLATE_CATEGORY_CONFIGS.find((c) => c.value === category) || TEMPLATE_CATEGORY_CONFIGS[0];
}

export function getCategoryForActivityType(activityType: ActivityType): TemplateCategory {
  for (const config of TEMPLATE_CATEGORY_CONFIGS) {
    if (config.activityTypes.includes(activityType)) {
      return config.value;
    }
  }
  return 'rotation'; // Default
}

export type PatternType = 'regular' | 'split' | 'mirrored' | 'alternating';
export type SettingType = 'inpatient' | 'outpatient';

export interface RotationTemplate {
  id: string;
  name: string;
  activityType: ActivityType;
  templateCategory: TemplateCategory;
  abbreviation: string | null;
  displayAbbreviation: string | null;
  fontColor: string | null;
  backgroundColor: string | null;
  clinicLocation: string | null;
  maxResidents: number | null;
  requiresSpecialty: string | null;
  requiresProcedureCredential: boolean;
  supervisionRequired: boolean;
  maxSupervisionRatio: number | null;
  /** True for half-block rotations (14 days instead of 28) */
  isBlockHalfRotation?: boolean;
  /** True if rotation includes weekend work (Night Float, FMIT, etc.) */
  includesWeekendWork?: boolean;
  createdAt: string;
  isArchived?: boolean;
  archivedAt?: string | null;
  archivedBy?: string | null;
}

export interface RotationTemplateListResponse {
  items: RotationTemplate[];
  total: number;
}

// ============================================================================
// Preference Types
// ============================================================================

export type PreferenceType =
  | 'full_day_grouping'
  | 'consecutive_specialty'
  | 'avoid_isolated'
  | 'preferred_days'
  | 'avoid_friday_pm'
  | 'balance_weekly';

export type PreferenceWeight = 'low' | 'medium' | 'high' | 'required';

export interface RotationPreference {
  id: string;
  rotationTemplateId: string;
  preferenceType: PreferenceType;
  weight: PreferenceWeight;
  configJson: Record<string, unknown>;
  isActive: boolean;
  description: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface RotationPreferenceCreate {
  preferenceType: PreferenceType;
  weight: PreferenceWeight;
  configJson?: Record<string, unknown>;
  isActive?: boolean;
  description?: string | null;
}

// ============================================================================
// Half-Day Requirement Types
// ============================================================================

/**
 * Half-day activity distribution requirements for a rotation template.
 * Defines how many half-days should be allocated to each activity type per block.
 */
export interface HalfDayRequirement {
  id: string;
  rotationTemplateId: string;
  /** Number of FM clinic half-days per block (default: 4) */
  fmClinicHalfdays: number;
  /** Number of specialty half-days per block (default: 5) */
  specialtyHalfdays: number;
  /** Name of the specialty (e.g., "Neurology", "Dermatology") */
  specialtyName: string | null;
  /** Number of academic/lecture half-days per block (default: 1) */
  academicsHalfdays: number;
  /** Number of elective/buffer half-days per block (default: 0) */
  electiveHalfdays: number;
  /** Minimum consecutive specialty days to batch together */
  minConsecutiveSpecialty: number;
  /** Prefer FM + specialty on same day when possible */
  preferCombinedClinicDays: boolean;
  /** Calculated total half-days */
  totalHalfdays: number;
  /** True if total equals standard block (10 half-days) */
  isBalanced: boolean;
}

export interface HalfDayRequirementCreate {
  fmClinicHalfdays?: number;
  specialtyHalfdays?: number;
  specialtyName?: string | null;
  academicsHalfdays?: number;
  electiveHalfdays?: number;
  minConsecutiveSpecialty?: number;
  preferCombinedClinicDays?: boolean;
}

// ============================================================================
// Preference Type Definitions for UI
// ============================================================================

export interface PreferenceTypeDefinition {
  type: PreferenceType;
  label: string;
  description: string;
  hasConfig: boolean;
  configSchema?: PreferenceConfigSchema;
}

export interface PreferenceConfigSchema {
  fields: PreferenceConfigField[];
}

export interface PreferenceConfigField {
  name: string;
  label: string;
  type: 'text' | 'number' | 'select' | 'multiselect' | 'checkbox';
  options?: { value: string; label: string }[];
  required?: boolean;
}

export const PREFERENCE_TYPE_DEFINITIONS: PreferenceTypeDefinition[] = [
  {
    type: 'full_day_grouping',
    label: 'Full Day Grouping',
    description: 'Prefer scheduling AM+PM of the same activity type together',
    hasConfig: false,
  },
  {
    type: 'consecutive_specialty',
    label: 'Consecutive Specialty',
    description: 'Group specialty sessions on consecutive days',
    hasConfig: false,
  },
  {
    type: 'avoid_isolated',
    label: 'Avoid Isolated Sessions',
    description: 'Avoid single orphaned half-day sessions',
    hasConfig: false,
  },
  {
    type: 'preferred_days',
    label: 'Preferred Days',
    description: 'Prefer specific activities on specific days of the week',
    hasConfig: true,
    configSchema: {
      fields: [
        {
          name: 'days',
          label: 'Preferred Days',
          type: 'multiselect',
          options: [
            { value: '0', label: 'Sunday' },
            { value: '1', label: 'Monday' },
            { value: '2', label: 'Tuesday' },
            { value: '3', label: 'Wednesday' },
            { value: '4', label: 'Thursday' },
            { value: '5', label: 'Friday' },
            { value: '6', label: 'Saturday' },
          ],
        },
      ],
    },
  },
  {
    type: 'avoid_friday_pm',
    label: 'Avoid Friday PM',
    description: 'Keep Friday afternoon open as travel buffer',
    hasConfig: false,
  },
  {
    type: 'balance_weekly',
    label: 'Balance Weekly',
    description: 'Distribute activities evenly across the week',
    hasConfig: false,
  },
];

// ============================================================================
// Bulk Action Types
// ============================================================================

export type BulkActionType =
  | 'delete'
  | 'update_activityType'
  | 'update_supervision'
  | 'update_maxResidents';

export interface BulkActionConfig {
  type: BulkActionType;
  label: string;
  description: string;
  isDangerous: boolean;
  requiresConfirmation: boolean;
}

export const BULK_ACTIONS: BulkActionConfig[] = [
  {
    type: 'delete',
    label: 'Delete Selected',
    description: 'Permanently delete selected templates',
    isDangerous: true,
    requiresConfirmation: true,
  },
  {
    type: 'update_activityType',
    label: 'Change Activity Type',
    description: 'Update activity type for selected templates',
    isDangerous: false,
    requiresConfirmation: true,
  },
  {
    type: 'update_supervision',
    label: 'Update Supervision',
    description: 'Toggle supervision requirement for selected templates',
    isDangerous: false,
    requiresConfirmation: true,
  },
  {
    type: 'update_maxResidents',
    label: 'Set Max Residents',
    description: 'Update maximum residents for selected templates',
    isDangerous: false,
    requiresConfirmation: true,
  },
];

// ============================================================================
// Filter & Sort Types
// ============================================================================

export type SortField = 'name' | 'activityType' | 'createdAt';
export type SortDirection = 'asc' | 'desc';

export interface TemplateFilters {
  activityType: ActivityType | '';
  templateCategory: TemplateCategory | '';
  search: string;
}

export interface TemplateSort {
  field: SortField;
  direction: SortDirection;
}

// ============================================================================
// State Types
// ============================================================================

export type AdminTemplatesTab = 'list' | 'edit' | 'patterns' | 'preferences';

export interface AdminTemplatesState {
  activeTab: AdminTemplatesTab;
  selectedIds: string[];
  filters: TemplateFilters;
  sort: TemplateSort;
  editingTemplateId: string | null;
  isCreating: boolean;
}

// ============================================================================
// API Request Types
// ============================================================================

export interface BulkDeleteRequest {
  templateIds: string[];
}

export interface BulkUpdateRequest {
  templateIds: string[];
  updates: Partial<Pick<RotationTemplate, 'activityType' | 'supervisionRequired' | 'maxResidents'>>;
}

// ============================================================================
// Batch Operation Types (API)
// ============================================================================

/**
 * Request for batch delete operation - atomic all-or-nothing
 */
export interface BatchTemplateDeleteRequest {
  templateIds: string[];
  dryRun?: boolean;
}

/**
 * Single template update in a batch operation
 */
export interface BatchTemplateUpdateItem {
  templateId: string;
  updates: TemplateUpdateRequest;
}

/**
 * Request for batch update operation - atomic all-or-nothing
 */
export interface BatchTemplateUpdateRequest {
  templates: BatchTemplateUpdateItem[];
  dryRun?: boolean;
}

/**
 * Result for a single operation in a batch
 */
export interface BatchOperationResult {
  index: number;
  templateId: string;
  success: boolean;
  error: string | null;
}

/**
 * Response from batch operations
 */
export interface BatchTemplateResponse {
  operationType: 'delete' | 'update' | 'create' | 'archive' | 'restore';
  total: number;
  succeeded: number;
  failed: number;
  results: BatchOperationResult[];
  dryRun: boolean;
  createdIds?: string[] | null;
}

/**
 * Request for batch create operation - atomic all-or-nothing
 */
export interface BatchTemplateCreateRequest {
  templates: TemplateCreateRequest[];
  dryRun?: boolean;
}

/**
 * Request for batch archive operation
 */
export interface BatchArchiveRequest {
  templateIds: string[];
  dryRun?: boolean;
}

/**
 * Request for batch restore operation
 */
export interface BatchRestoreRequest {
  templateIds: string[];
  dryRun?: boolean;
}

/**
 * Request for checking conflicts before operations
 */
export interface ConflictCheckRequest {
  templateIds: string[];
  operation: 'delete' | 'archive' | 'update';
}

/**
 * Single conflict item
 */
export interface TemplateConflict {
  templateId: string;
  templateName: string;
  conflictType: 'has_assignments' | 'name_collision' | 'referenced_by';
  description: string;
  severity: 'warning' | 'error';
  blocking: boolean;
}

/**
 * Response from conflict check
 */
export interface ConflictCheckResponse {
  hasConflicts: boolean;
  conflicts: TemplateConflict[];
  canProceed: boolean;
}

/**
 * Request for template export
 */
export interface TemplateExportRequest {
  templateIds: string[];
  includePatterns?: boolean;
  includePreferences?: boolean;
}

/**
 * Single template export data
 */
export interface TemplateExportData {
  template: RotationTemplate;
  patterns?: Record<string, unknown>[] | null;
  preferences?: Record<string, unknown>[] | null;
}

/**
 * Response from template export
 */
export interface TemplateExportResponse {
  templates: TemplateExportData[];
  exportedAt: string;
  total: number;
}

export interface TemplateCreateRequest {
  name: string;
  activityType: ActivityType;
  templateCategory?: TemplateCategory;
  abbreviation?: string | null;
  displayAbbreviation?: string | null;
  fontColor?: string | null;
  backgroundColor?: string | null;
  clinicLocation?: string | null;
  maxResidents?: number | null;
  requiresSpecialty?: string | null;
  requiresProcedureCredential?: boolean;
  supervisionRequired?: boolean;
  maxSupervisionRatio?: number | null;
  isBlockHalfRotation?: boolean;
}

export interface TemplateUpdateRequest {
  name?: string;
  activityType?: ActivityType;
  templateCategory?: TemplateCategory;
  abbreviation?: string | null;
  displayAbbreviation?: string | null;
  fontColor?: string | null;
  backgroundColor?: string | null;
  clinicLocation?: string | null;
  maxResidents?: number | null;
  requiresSpecialty?: string | null;
  requiresProcedureCredential?: boolean;
  supervisionRequired?: boolean;
  maxSupervisionRatio?: number | null;
  isBlockHalfRotation?: boolean;
}

// ============================================================================
// Activity Type Display Config
// ============================================================================

export interface ActivityTypeConfig {
  type: ActivityType;
  label: string;
  color: string;
  bgColor: string;
}

export const ACTIVITY_TYPE_CONFIGS: ActivityTypeConfig[] = [
  { type: 'clinic', label: 'Clinic', color: 'text-emerald-400', bgColor: 'bg-emerald-500/20' },
  { type: 'inpatient', label: 'Inpatient', color: 'text-blue-400', bgColor: 'bg-blue-500/20' },
  { type: 'procedure', label: 'Procedure', color: 'text-purple-400', bgColor: 'bg-purple-500/20' },
  { type: 'procedures', label: 'Procedures', color: 'text-purple-400', bgColor: 'bg-purple-500/20' },
  { type: 'conference', label: 'Conference', color: 'text-amber-400', bgColor: 'bg-amber-500/20' },
  { type: 'education', label: 'Education', color: 'text-cyan-400', bgColor: 'bg-cyan-500/20' },
  { type: 'lecture', label: 'Lecture (LEC)', color: 'text-fuchsia-400', bgColor: 'bg-fuchsia-500/20' },
  { type: 'outpatient', label: 'Outpatient', color: 'text-green-400', bgColor: 'bg-green-500/20' },
  { type: 'absence', label: 'Absence', color: 'text-red-400', bgColor: 'bg-red-500/20' },
  { type: 'off', label: 'Off', color: 'text-slate-400', bgColor: 'bg-slate-500/20' },
  { type: 'recovery', label: 'Recovery', color: 'text-orange-400', bgColor: 'bg-orange-500/20' },
];

export function getActivityTypeConfig(type: ActivityType): ActivityTypeConfig {
  return ACTIVITY_TYPE_CONFIGS.find((c) => c.type === type) || ACTIVITY_TYPE_CONFIGS[0];
}
