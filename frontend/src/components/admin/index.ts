/**
 * Admin Component Exports
 *
 * Re-exports all admin-specific components for easy importing.
 */

export { CoverageTrendChart, MOCK_COVERAGE_DATA } from './CoverageTrendChart';
export type { CoverageDataPoint, CoverageTrendChartProps } from './CoverageTrendChart';

export { AlgorithmComparisonChart, MOCK_ALGORITHM_DATA } from './AlgorithmComparisonChart';
export type { AlgorithmMetrics, AlgorithmComparisonChartProps } from './AlgorithmComparisonChart';

export { default as ClaudeCodeChat } from './ClaudeCodeChat';
export { default as MCPCapabilitiesPanel } from './MCPCapabilitiesPanel';

// Template management components
export { TemplateTable } from './TemplateTable';
export type { TemplateTableProps } from './TemplateTable';

export { BulkActionsToolbar } from './BulkActionsToolbar';
export type { BulkActionsToolbarProps } from './BulkActionsToolbar';

export { PreferenceEditor } from './PreferenceEditor';
export type { PreferenceEditorProps } from './PreferenceEditor';

// Inline editing components
export { EditableCell } from './EditableCell';
export type { EditableCellProps, EditableCellType, SelectOption } from './EditableCell';

export { ColorPickerCell } from './ColorPickerCell';
export type { ColorPickerCellProps } from './ColorPickerCell';

export { BulkProgressModal } from './BulkProgressModal';
export type {
  BulkProgressModalProps,
  BulkProgressItem,
  BulkOperationType,
} from './BulkProgressModal';

// Bulk creation modals
export { BulkCreateModal } from './BulkCreateModal';
export type { BulkCreateModalProps } from './BulkCreateModal';

export { CSVImportModal } from './CSVImportModal';
export type { CSVImportModalProps } from './CSVImportModal';

export { DuplicateTemplateModal } from './DuplicateTemplateModal';
export type { DuplicateTemplateModalProps } from './DuplicateTemplateModal';

// Archive and bulk pattern/preference components
export { ArchivedTemplatesDrawer } from './ArchivedTemplatesDrawer';
export type { ArchivedTemplatesDrawerProps } from './ArchivedTemplatesDrawer';

export { BulkPatternModal } from './BulkPatternModal';
export type { BulkPatternModalProps, SchedulePattern } from './BulkPatternModal';

export { BulkPreferenceModal } from './BulkPreferenceModal';
export type { BulkPreferenceModalProps } from './BulkPreferenceModal';

// Faculty call administration components
export { CallAssignmentTable } from './CallAssignmentTable';
export type { CallAssignmentTableProps } from './CallAssignmentTable';

export { CallBulkActionsToolbar } from './CallBulkActionsToolbar';
export type { CallBulkActionsToolbarProps } from './CallBulkActionsToolbar';

export { PCATPreviewModal, createPCATPreviewData } from './PCATPreviewModal';
export type { PCATPreviewModalProps } from './PCATPreviewModal';

export { EquityPreviewPanel } from './EquityPreviewPanel';
export type { EquityPreviewPanelProps } from './EquityPreviewPanel';
