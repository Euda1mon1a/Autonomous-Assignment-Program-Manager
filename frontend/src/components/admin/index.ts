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
