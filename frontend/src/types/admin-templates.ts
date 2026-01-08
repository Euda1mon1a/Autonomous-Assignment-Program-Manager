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
 * - time_off: ACGME-protected rest (off, recovery) - does NOT count toward away-from-program
 * - absence: Days away from program (absence activity type) - counts toward 28-day limit
 * - educational: Structured learning (conference, education, lecture)
 */
export type TemplateCategory = 'rotation' | 'time_off' | 'absence' | 'educational';

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
    value: 'time_off',
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
  activity_type: ActivityType;
  template_category: TemplateCategory;
  abbreviation: string | null;
  display_abbreviation: string | null;
  font_color: string | null;
  background_color: string | null;
  clinic_location: string | null;
  max_residents: number | null;
  requires_specialty: string | null;
  requires_procedure_credential: boolean;
  supervision_required: boolean;
  max_supervision_ratio: number | null;
  /** True for half-block rotations (14 days instead of 28) */
  is_block_half_rotation?: boolean;
  /** True if rotation includes weekend work (Night Float, FMIT, etc.) */
  includes_weekend_work?: boolean;
  created_at: string;
  is_archived?: boolean;
  archived_at?: string | null;
  archived_by?: string | null;
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
  rotation_template_id: string;
  preference_type: PreferenceType;
  weight: PreferenceWeight;
  config_json: Record<string, unknown>;
  is_active: boolean;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface RotationPreferenceCreate {
  preference_type: PreferenceType;
  weight: PreferenceWeight;
  config_json?: Record<string, unknown>;
  is_active?: boolean;
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
  rotation_template_id: string;
  /** Number of FM clinic half-days per block (default: 4) */
  fm_clinic_halfdays: number;
  /** Number of specialty half-days per block (default: 5) */
  specialty_halfdays: number;
  /** Name of the specialty (e.g., "Neurology", "Dermatology") */
  specialty_name: string | null;
  /** Number of academic/lecture half-days per block (default: 1) */
  academics_halfdays: number;
  /** Number of elective/buffer half-days per block (default: 0) */
  elective_halfdays: number;
  /** Minimum consecutive specialty days to batch together */
  min_consecutive_specialty: number;
  /** Prefer FM + specialty on same day when possible */
  prefer_combined_clinic_days: boolean;
  /** Calculated total half-days */
  total_halfdays: number;
  /** True if total equals standard block (10 half-days) */
  is_balanced: boolean;
}

export interface HalfDayRequirementCreate {
  fm_clinic_halfdays?: number;
  specialty_halfdays?: number;
  specialty_name?: string | null;
  academics_halfdays?: number;
  elective_halfdays?: number;
  min_consecutive_specialty?: number;
  prefer_combined_clinic_days?: boolean;
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
  | 'update_activity_type'
  | 'update_supervision'
  | 'update_max_residents';

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
    type: 'update_activity_type',
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
    type: 'update_max_residents',
    label: 'Set Max Residents',
    description: 'Update maximum residents for selected templates',
    isDangerous: false,
    requiresConfirmation: true,
  },
];

// ============================================================================
// Filter & Sort Types
// ============================================================================

export type SortField = 'name' | 'activity_type' | 'created_at';
export type SortDirection = 'asc' | 'desc';

export interface TemplateFilters {
  activity_type: ActivityType | '';
  template_category: TemplateCategory | '';
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
  template_ids: string[];
}

export interface BulkUpdateRequest {
  template_ids: string[];
  updates: Partial<Pick<RotationTemplate, 'activity_type' | 'supervision_required' | 'max_residents'>>;
}

// ============================================================================
// Batch Operation Types (API)
// ============================================================================

/**
 * Request for batch delete operation - atomic all-or-nothing
 */
export interface BatchTemplateDeleteRequest {
  template_ids: string[];
  dry_run?: boolean;
}

/**
 * Single template update in a batch operation
 */
export interface BatchTemplateUpdateItem {
  template_id: string;
  updates: TemplateUpdateRequest;
}

/**
 * Request for batch update operation - atomic all-or-nothing
 */
export interface BatchTemplateUpdateRequest {
  templates: BatchTemplateUpdateItem[];
  dry_run?: boolean;
}

/**
 * Result for a single operation in a batch
 */
export interface BatchOperationResult {
  index: number;
  template_id: string;
  success: boolean;
  error: string | null;
}

/**
 * Response from batch operations
 */
export interface BatchTemplateResponse {
  operation_type: 'delete' | 'update' | 'create' | 'archive' | 'restore';
  total: number;
  succeeded: number;
  failed: number;
  results: BatchOperationResult[];
  dry_run: boolean;
  created_ids?: string[] | null;
}

/**
 * Request for batch create operation - atomic all-or-nothing
 */
export interface BatchTemplateCreateRequest {
  templates: TemplateCreateRequest[];
  dry_run?: boolean;
}

/**
 * Request for batch archive operation
 */
export interface BatchArchiveRequest {
  template_ids: string[];
  dry_run?: boolean;
}

/**
 * Request for batch restore operation
 */
export interface BatchRestoreRequest {
  template_ids: string[];
  dry_run?: boolean;
}

/**
 * Request for checking conflicts before operations
 */
export interface ConflictCheckRequest {
  template_ids: string[];
  operation: 'delete' | 'archive' | 'update';
}

/**
 * Single conflict item
 */
export interface TemplateConflict {
  template_id: string;
  template_name: string;
  conflict_type: 'has_assignments' | 'name_collision' | 'referenced_by';
  description: string;
  severity: 'warning' | 'error';
  blocking: boolean;
}

/**
 * Response from conflict check
 */
export interface ConflictCheckResponse {
  has_conflicts: boolean;
  conflicts: TemplateConflict[];
  can_proceed: boolean;
}

/**
 * Request for template export
 */
export interface TemplateExportRequest {
  template_ids: string[];
  include_patterns?: boolean;
  include_preferences?: boolean;
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
  exported_at: string;
  total: number;
}

export interface TemplateCreateRequest {
  name: string;
  activity_type: ActivityType;
  template_category?: TemplateCategory;
  abbreviation?: string | null;
  display_abbreviation?: string | null;
  font_color?: string | null;
  background_color?: string | null;
  clinic_location?: string | null;
  max_residents?: number | null;
  requires_specialty?: string | null;
  requires_procedure_credential?: boolean;
  supervision_required?: boolean;
  max_supervision_ratio?: number | null;
  is_block_half_rotation?: boolean;
}

export interface TemplateUpdateRequest {
  name?: string;
  activity_type?: ActivityType;
  template_category?: TemplateCategory;
  abbreviation?: string | null;
  display_abbreviation?: string | null;
  font_color?: string | null;
  background_color?: string | null;
  clinic_location?: string | null;
  max_residents?: number | null;
  requires_specialty?: string | null;
  requires_procedure_credential?: boolean;
  supervision_required?: boolean;
  max_supervision_ratio?: number | null;
  is_block_half_rotation?: boolean;
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
