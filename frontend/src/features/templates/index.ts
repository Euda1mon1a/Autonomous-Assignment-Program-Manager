/**
 * Template Library Feature
 *
 * Complete template library system for schedule templates,
 * assignment patterns, and template management.
 *
 * Features:
 * - Schedule template creation and management
 * - Assignment pattern templates
 * - Template categories and search
 * - Template preview and customization
 * - Share and duplicate templates
 *
 * Usage:
 * ```tsx
 * import { TemplateLibrary } from '@/features/templates';
 *
 * function TemplatesPage() {
 *   return <TemplateLibrary onTemplateApplied={(result) => // console.log(result)} />;
 * }
 * ```
 */

// Types
export type {
  TemplateCategory,
  TemplateVisibility,
  TemplateStatus,
  AssignmentPattern,
  ScheduleTemplate,
  ScheduleTemplateCreate,
  ScheduleTemplateUpdate,
  TemplatePreviewConfig,
  TemplateApplicationResult,
  TemplateConflict,
  TemplateFilters,
  CategoryInfo,
  TemplateShareRequest,
  TemplateDuplicateRequest,
  TemplateListResponse,
  TemplateStatistics,
  PredefinedTemplate,
} from './types';

// Constants
export {
  TEMPLATE_CATEGORIES,
  CATEGORY_COLORS,
  STATUS_COLORS,
  VISIBILITY_OPTIONS,
  PREDEFINED_TEMPLATES,
  DAY_OF_WEEK_LABELS,
  DAY_OF_WEEK_SHORT,
  ACTIVITY_TYPE_OPTIONS,
  ROLE_OPTIONS,
  TIME_OF_DAY_OPTIONS,
  DEFAULT_TEMPLATE_VALUES,
} from './constants';

// Hooks
export {
  templateQueryKeys,
  useTemplates,
  useTemplate,
  usePredefinedTemplates,
  useTemplateStatistics,
  useCreateTemplate,
  useUpdateTemplate,
  useDeleteTemplate,
  useDuplicateTemplate,
  useShareTemplate,
  useApplyTemplate,
  useImportPredefinedTemplate,
  useTemplateFilters,
  usePatternEditor,
} from './hooks';

// Components
export {
  TemplateCard,
  TemplateSearch,
  TemplateCategories,
  CategoryBadge,
  PatternEditor,
  TemplateEditor,
  TemplatePreview,
  PatternPreviewGrid,
  TemplateShareModal,
  TemplateList,
  PredefinedTemplateCard,
  TemplateLibrary,
} from './components';
