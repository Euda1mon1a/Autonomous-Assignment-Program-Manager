'use client';

/**
 * WhatIfAnalysis Component
 *
 * Form to input proposed changes and visualize predicted impacts
 * with recommendation summary.
 */

import { useState } from 'react';
import {
  Plus,
  Trash2,
  Play,
  AlertTriangle,
  CheckCircle,
  Info,
  XCircle,
  TrendingUp,
  TrendingDown,
} from 'lucide-react';
import { useWhatIfAnalysis, useScheduleVersions } from './hooks';
import type { ProposedChange, ChangeType, WhatIfAnalysisRequest } from './types';
import { CHANGE_TYPE_LABELS, METRIC_CATEGORY_LABELS } from './types';

// ============================================================================
// Types
// ============================================================================

interface WhatIfAnalysisProps {
  baseVersionId?: string;
  className?: string;
}

// ============================================================================
// Sub-Components
// ============================================================================

/**
 * Change type selector
 */
function ChangeTypeSelector({
  value,
  onChange,
}: {
  value: ChangeType;
  onChange: (type: ChangeType) => void;
}) {
  const changeTypes: ChangeType[] = [
    'add_shift',
    'remove_shift',
    'swap_shifts',
    'add_constraint',
    'modify_rotation',
    'adjust_staffing',
  ];

  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value as ChangeType)}
      className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
    >
      {changeTypes.map((type) => (
        <option key={type} value={type}>
          {CHANGE_TYPE_LABELS[type]}
        </option>
      ))}
    </select>
  );
}

/**
 * Change editor
 */
function ChangeEditor({
  change,
  onUpdate,
  onRemove,
  index,
}: {
  change: ProposedChange;
  onUpdate: (change: ProposedChange) => void;
  onRemove: () => void;
  index: number;
}) {
  return (
    <div className="p-4 border border-gray-300 rounded-lg bg-gray-50">
      <div className="flex items-start gap-3 mb-3">
        <div className="flex items-center justify-center w-6 h-6 rounded-full bg-blue-100 text-blue-700 text-sm font-semibold flex-shrink-0">
          {index + 1}
        </div>
        <div className="flex-1 space-y-3">
          <div className="flex gap-3">
            <div className="flex-1">
              <label className="block text-xs font-medium text-gray-700 mb-1">Change Type</label>
              <ChangeTypeSelector
                value={change.type}
                onChange={(type) => onUpdate({ ...change, type })}
              />
            </div>
            <button
              type="button"
              onClick={onRemove}
              className="mt-6 p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
              title="Remove change"
            >
              <Trash2 className="w-5 h-5" />
            </button>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Description</label>
            <input
              type="text"
              value={change.description}
              onChange={(e) => onUpdate({ ...change, description: e.target.value })}
              placeholder="Describe the proposed change..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Simplified parameters - in real implementation would be dynamic based on type */}
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Parameters (JSON)</label>
            <textarea
              value={JSON.stringify(change.parameters, null, 2)}
              onChange={(e) => {
                try {
                  const params = JSON.parse(e.target.value);
                  onUpdate({ ...change, parameters: params });
                } catch {
                  // Invalid JSON, ignore
                }
              }}
              placeholder='{"resident_id": "123", "date": "2024-01-15"}'
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg font-mono text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Warning item
 */
function WarningItem({
  warning,
}: {
  warning: {
    severity: 'info' | 'warning' | 'error';
    message: string;
    affectedEntity: string;
    suggestion?: string;
  };
}) {
  const config = {
    info: {
      icon: <Info className="w-5 h-5 text-blue-600" />,
      bg: 'bg-blue-50 border-blue-200',
      text: 'text-blue-900',
    },
    warning: {
      icon: <AlertTriangle className="w-5 h-5 text-yellow-600" />,
      bg: 'bg-yellow-50 border-yellow-200',
      text: 'text-yellow-900',
    },
    error: {
      icon: <XCircle className="w-5 h-5 text-red-600" />,
      bg: 'bg-red-50 border-red-200',
      text: 'text-red-900',
    },
  };

  const style = config[warning.severity];

  return (
    <div className={`p-4 border rounded-lg ${style.bg}`}>
      <div className="flex gap-3">
        {style.icon}
        <div className="flex-1">
          <p className={`text-sm font-semibold ${style.text} mb-1`}>{warning.message}</p>
          <p className="text-xs text-gray-600 mb-2">Affects: {warning.affectedEntity}</p>
          {warning.suggestion && (
            <p className="text-xs text-gray-700 italic">Suggestion: {warning.suggestion}</p>
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * Constraint impact item
 */
function ConstraintImpactItem({
  constraint,
}: {
  constraint: {
    constraintType: string;
    constraintName: string;
    currentValue: number;
    projectedValue: number;
    violated: boolean;
    violationSeverity?: 'minor' | 'major' | 'critical';
  };
}) {
  const isIncrease = constraint.projectedValue > constraint.currentValue;
  const change = constraint.projectedValue - constraint.currentValue;
  const changePercentage = (change / constraint.currentValue) * 100;

  return (
    <div
      className={`p-4 border rounded-lg ${
        constraint.violated ? 'bg-red-50 border-red-200' : 'bg-gray-50 border-gray-200'
      }`}
    >
      <div className="flex items-start justify-between mb-2">
        <div>
          <h4 className="text-sm font-semibold text-gray-900">{constraint.constraintName}</h4>
          <p className="text-xs text-gray-600">{constraint.constraintType}</p>
        </div>
        {constraint.violated && (
          <span className="px-2 py-1 text-xs font-medium bg-red-100 text-red-700 border border-red-300 rounded">
            {constraint.violationSeverity?.toUpperCase()} VIOLATION
          </span>
        )}
      </div>

      <div className="flex items-center gap-3 mt-3">
        <div className="flex-1">
          <p className="text-xs text-gray-600 mb-1">Current</p>
          <p className="text-base font-bold text-gray-900">{constraint.currentValue.toFixed(2)}</p>
        </div>
        {isIncrease ? (
          <TrendingUp className="w-5 h-5 text-gray-400" />
        ) : (
          <TrendingDown className="w-5 h-5 text-gray-400" />
        )}
        <div className="flex-1">
          <p className="text-xs text-gray-600 mb-1">Projected</p>
          <p className="text-base font-bold text-gray-900">{constraint.projectedValue.toFixed(2)}</p>
        </div>
        <div className="flex-shrink-0">
          <span
            className={`text-xs font-medium ${
              constraint.violated ? 'text-red-600' : 'text-gray-600'
            }`}
          >
            {isIncrease ? '+' : ''}
            {changePercentage.toFixed(1)}%
          </span>
        </div>
      </div>
    </div>
  );
}

/**
 * Results panel
 */
function ResultsPanel({
  result,
}: {
  result: {
    predictedImpact: {
      metrics: Record<string, any>;
      comparisonToBaseline: Array<{
        metricName: string;
        delta: number;
        deltaPercentage: number;
        improved: boolean;
      }>;
      warnings: Array<{
        severity: 'info' | 'warning' | 'error';
        message: string;
        affectedEntity: string;
        suggestion?: string;
      }>;
      constraints: Array<{
        constraintType: string;
        constraintName: string;
        currentValue: number;
        projectedValue: number;
        violated: boolean;
        violationSeverity?: 'minor' | 'major' | 'critical';
      }>;
      confidence: number;
    };
    recommendation: {
      approved: boolean;
      reasoning: string;
      alternatives?: string[];
    };
  };
}) {
  const { predictedImpact, recommendation } = result;

  return (
    <div className="space-y-6">
      {/* Recommendation */}
      <div
        className={`p-6 border-2 rounded-lg ${
          recommendation.approved
            ? 'bg-green-50 border-green-200'
            : 'bg-red-50 border-red-200'
        }`}
      >
        <div className="flex items-start gap-3 mb-3">
          {recommendation.approved ? (
            <CheckCircle className="w-6 h-6 text-green-600 flex-shrink-0" />
          ) : (
            <XCircle className="w-6 h-6 text-red-600 flex-shrink-0" />
          )}
          <div className="flex-1">
            <h3 className="text-lg font-bold text-gray-900 mb-1">
              {recommendation.approved ? 'Recommended' : 'Not Recommended'}
            </h3>
            <p className="text-sm text-gray-700">{recommendation.reasoning}</p>
          </div>
        </div>

        {recommendation.alternatives && recommendation.alternatives.length > 0 && (
          <div className="mt-4 pt-4 border-t border-gray-300">
            <h4 className="text-sm font-semibold text-gray-900 mb-2">Alternative Approaches</h4>
            <ul className="space-y-1">
              {recommendation.alternatives.map((alt, index) => (
                <li key={index} className="text-sm text-gray-700 flex gap-2">
                  <span className="text-blue-600">•</span>
                  <span>{alt}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        <div className="mt-4 pt-4 border-t border-gray-300">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-700">Prediction Confidence</span>
            <span className="text-sm font-bold text-gray-900">{predictedImpact.confidence}%</span>
          </div>
          <div className="mt-2 h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-500 transition-all"
              style={{ width: `${predictedImpact.confidence}%` }}
            />
          </div>
        </div>
      </div>

      {/* Warnings */}
      {predictedImpact.warnings.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Warnings</h3>
          <div className="space-y-3">
            {predictedImpact.warnings.map((warning, index) => (
              <WarningItem key={index} warning={warning} />
            ))}
          </div>
        </div>
      )}

      {/* Constraint Impacts */}
      {predictedImpact.constraints.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Constraint Impacts</h3>
          <div className="space-y-3">
            {predictedImpact.constraints.map((constraint, index) => (
              <ConstraintImpactItem key={index} constraint={constraint} />
            ))}
          </div>
        </div>
      )}

      {/* Metric Deltas */}
      {predictedImpact.comparisonToBaseline.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Predicted Metric Changes</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {predictedImpact.comparisonToBaseline.map((delta, index) => (
              <div key={index} className="p-4 border border-gray-200 rounded-lg bg-white">
                <p className="text-sm font-semibold text-gray-900 mb-2">{delta.metricName}</p>
                <div
                  className={`inline-flex items-center gap-1 px-2 py-1 rounded-md ${
                    delta.improved ? 'bg-green-50 text-green-600' : 'bg-red-50 text-red-600'
                  }`}
                >
                  {delta.improved ? (
                    <TrendingUp className="w-4 h-4" />
                  ) : (
                    <TrendingDown className="w-4 h-4" />
                  )}
                  <span className="text-sm font-medium">
                    {delta.improved ? '+' : ''}
                    {delta.delta.toFixed(2)} ({delta.deltaPercentage > 0 ? '+' : ''}
                    {delta.deltaPercentage.toFixed(1)}%)
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function WhatIfAnalysis({ baseVersionId, className = '' }: WhatIfAnalysisProps) {
  const [selectedVersionId, setSelectedVersionId] = useState<string>(baseVersionId || '');
  const [analysisScope, setAnalysisScope] = useState<'immediate' | 'week' | 'month' | 'quarter'>(
    'week'
  );
  const [changes, setChanges] = useState<ProposedChange[]>([]);

  const { data: versions } = useScheduleVersions();
  const { mutate: runAnalysis, data: result, isPending, error } = useWhatIfAnalysis();

  const handleAddChange = () => {
    setChanges([
      ...changes,
      {
        type: 'add_shift',
        description: '',
        parameters: {},
      },
    ]);
  };

  const handleUpdateChange = (index: number, change: ProposedChange) => {
    const newChanges = [...changes];
    newChanges[index] = change;
    setChanges(newChanges);
  };

  const handleRemoveChange = (index: number) => {
    setChanges(changes.filter((_, i) => i !== index));
  };

  const handleRunAnalysis = () => {
    if (!selectedVersionId || changes.length === 0) return;

    const request: WhatIfAnalysisRequest = {
      baseVersionId: selectedVersionId,
      changes,
      analysisScope,
    };

    runAnalysis(request);
  };

  const canRunAnalysis = selectedVersionId && changes.length > 0 && changes.every((c) => c.description);

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Configuration */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">What-If Analysis</h2>
        <p className="text-sm text-gray-600 mb-6">
          Predict the impact of proposed changes to your schedule before implementing them.
        </p>

        <div className="space-y-4">
          {/* Base Version Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Base Version</label>
            <select
              value={selectedVersionId}
              onChange={(e) => setSelectedVersionId(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">Select a version...</option>
              {versions?.map((version) => (
                <option key={version.id} value={version.id}>
                  {version.name} - {new Date(version.createdAt).toLocaleDateString()}
                </option>
              ))}
            </select>
          </div>

          {/* Analysis Scope */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Analysis Scope</label>
            <div className="flex gap-2">
              {(['immediate', 'week', 'month', 'quarter'] as const).map((scope) => (
                <button
                  key={scope}
                  type="button"
                  onClick={() => setAnalysisScope(scope)}
                  className={`
                    flex-1 px-4 py-2 rounded-lg text-sm font-medium transition-colors
                    ${
                      analysisScope === scope
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }
                  `}
                >
                  {scope.charAt(0).toUpperCase() + scope.slice(1)}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Proposed Changes */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Proposed Changes</h3>
          <button
            type="button"
            onClick={handleAddChange}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Add Change
          </button>
        </div>

        {changes.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <Info className="w-12 h-12 mx-auto mb-3 text-gray-400" />
            <p>No changes added yet. Click "Add Change" to get started.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {changes.map((change, index) => (
              <ChangeEditor
                key={index}
                change={change}
                onUpdate={(c) => handleUpdateChange(index, c)}
                onRemove={() => handleRemoveChange(index)}
                index={index}
              />
            ))}
          </div>
        )}

        {/* Run Analysis Button */}
        <div className="mt-6 pt-6 border-t border-gray-200">
          <button
            type="button"
            onClick={handleRunAnalysis}
            disabled={!canRunAnalysis || isPending}
            className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            <Play className="w-5 h-5" />
            {isPending ? 'Running Analysis...' : 'Run What-If Analysis'}
          </button>
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <div className="flex items-center gap-2 text-red-600">
            <AlertTriangle className="w-5 h-5" />
            <p className="text-sm font-medium">Analysis failed. Please try again.</p>
          </div>
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-xl font-bold text-gray-900 mb-6">Analysis Results</h3>
          <ResultsPanel result={result} />
        </div>
      )}
    </div>
  );
}
