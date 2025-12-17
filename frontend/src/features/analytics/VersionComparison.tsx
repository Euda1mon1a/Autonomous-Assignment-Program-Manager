'use client';

/**
 * VersionComparison Component
 *
 * Side-by-side comparison of two schedule versions with delta highlighting
 * and impact assessment visualization.
 */

import { useState } from 'react';
import {
  ArrowRight,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle,
  Info,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { useVersionComparison, useScheduleVersions } from './hooks';
import type { MetricDelta, MetricCategory } from './types';
import { METRIC_CATEGORY_LABELS } from './types';

// ============================================================================
// Types
// ============================================================================

interface VersionComparisonProps {
  versionAId?: string;
  versionBId?: string;
  className?: string;
}

// ============================================================================
// Sub-Components
// ============================================================================

/**
 * Version selector dropdown
 */
function VersionSelector({
  selectedVersionId,
  onVersionChange,
  label,
  excludeVersionId,
}: {
  selectedVersionId?: string;
  onVersionChange: (versionId: string) => void;
  label: string;
  excludeVersionId?: string;
}) {
  const { data: versions, isLoading } = useScheduleVersions();

  const availableVersions = versions?.filter((v) => v.id !== excludeVersionId) || [];

  return (
    <div className="flex-1">
      <label className="block text-sm font-medium text-gray-700 mb-2">{label}</label>
      <select
        value={selectedVersionId || ''}
        onChange={(e) => onVersionChange(e.target.value)}
        disabled={isLoading}
        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
      >
        <option value="">Select a version...</option>
        {availableVersions.map((version) => (
          <option key={version.id} value={version.id}>
            {version.name} - {new Date(version.createdAt).toLocaleDateString()} ({version.status})
          </option>
        ))}
      </select>
    </div>
  );
}

/**
 * Delta badge
 */
function DeltaBadge({
  delta,
  deltaPercentage,
  improved,
}: {
  delta: number;
  deltaPercentage: number;
  improved: boolean;
}) {
  const Icon = improved ? TrendingUp : TrendingDown;
  const colorClass = improved ? 'text-green-600 bg-green-50' : 'text-red-600 bg-red-50';

  return (
    <div className={`inline-flex items-center gap-1 px-2 py-1 rounded-md ${colorClass}`}>
      <Icon className="w-4 h-4" />
      <span className="text-xs font-medium">
        {improved ? '+' : ''}
        {delta.toFixed(2)} ({deltaPercentage > 0 ? '+' : ''}
        {deltaPercentage.toFixed(1)}%)
      </span>
    </div>
  );
}

/**
 * Significance badge
 */
function SignificanceBadge({ significance }: { significance: 'major' | 'moderate' | 'minor' }) {
  const config = {
    major: { label: 'Major Change', color: 'bg-purple-100 text-purple-700 border-purple-300' },
    moderate: { label: 'Moderate', color: 'bg-blue-100 text-blue-700 border-blue-300' },
    minor: { label: 'Minor', color: 'bg-gray-100 text-gray-700 border-gray-300' },
  };

  const { label, color } = config[significance];

  return (
    <span className={`inline-block px-2 py-1 text-xs font-medium border rounded ${color}`}>
      {label}
    </span>
  );
}

/**
 * Metric delta row
 */
function MetricDeltaRow({ delta }: { delta: MetricDelta }) {
  return (
    <div className="p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-2">
        <div>
          <h4 className="text-sm font-semibold text-gray-900">{delta.metricName}</h4>
          <p className="text-xs text-gray-500">{METRIC_CATEGORY_LABELS[delta.category]}</p>
        </div>
        <SignificanceBadge significance={delta.significance} />
      </div>

      <div className="flex items-center gap-4 mt-3">
        <div className="flex-1">
          <p className="text-xs text-gray-600 mb-1">Version A</p>
          <p className="text-lg font-bold text-gray-900">{delta.valueA.toFixed(2)}</p>
        </div>
        <ArrowRight className="w-5 h-5 text-gray-400 flex-shrink-0" />
        <div className="flex-1">
          <p className="text-xs text-gray-600 mb-1">Version B</p>
          <p className="text-lg font-bold text-gray-900">{delta.valueB.toFixed(2)}</p>
        </div>
        <div className="flex-shrink-0">
          <DeltaBadge
            delta={delta.delta}
            deltaPercentage={delta.deltaPercentage}
            improved={delta.improved}
          />
        </div>
      </div>
    </div>
  );
}

/**
 * Impact assessment card
 */
function ImpactAssessmentCard({
  impactAssessment,
}: {
  impactAssessment: {
    overallImpact: 'positive' | 'negative' | 'neutral';
    fairnessImpact: number;
    coverageImpact: number;
    complianceImpact: number;
    affectedResidents: number;
    riskLevel: 'low' | 'medium' | 'high';
    recommendations: string[];
  };
}) {
  const [expanded, setExpanded] = useState(true);

  const overallConfig = {
    positive: {
      icon: <CheckCircle className="w-5 h-5 text-green-600" />,
      label: 'Positive Impact',
      color: 'bg-green-50 border-green-200',
      textColor: 'text-green-900',
    },
    negative: {
      icon: <AlertTriangle className="w-5 h-5 text-red-600" />,
      label: 'Negative Impact',
      color: 'bg-red-50 border-red-200',
      textColor: 'text-red-900',
    },
    neutral: {
      icon: <Info className="w-5 h-5 text-gray-600" />,
      label: 'Neutral Impact',
      color: 'bg-gray-50 border-gray-200',
      textColor: 'text-gray-900',
    },
  };

  const riskConfig = {
    low: { label: 'Low Risk', color: 'text-green-600' },
    medium: { label: 'Medium Risk', color: 'text-yellow-600' },
    high: { label: 'High Risk', color: 'text-red-600' },
  };

  const config = overallConfig[impactAssessment.overallImpact];
  const risk = riskConfig[impactAssessment.riskLevel];

  return (
    <div className={`border-2 rounded-lg ${config.color}`}>
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="w-full px-6 py-4 flex items-center justify-between"
      >
        <div className="flex items-center gap-3">
          {config.icon}
          <div className="text-left">
            <h3 className={`text-lg font-semibold ${config.textColor}`}>{config.label}</h3>
            <p className="text-sm text-gray-600">
              {impactAssessment.affectedResidents} residents affected • {risk.label}
            </p>
          </div>
        </div>
        {expanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
      </button>

      {expanded && (
        <div className="px-6 pb-6 space-y-4">
          {/* Impact Bars */}
          <div className="space-y-3">
            <ImpactBar label="Fairness Impact" value={impactAssessment.fairnessImpact} />
            <ImpactBar label="Coverage Impact" value={impactAssessment.coverageImpact} />
            <ImpactBar label="Compliance Impact" value={impactAssessment.complianceImpact} />
          </div>

          {/* Recommendations */}
          {impactAssessment.recommendations.length > 0 && (
            <div className="pt-4 border-t border-gray-300">
              <h4 className="text-sm font-semibold text-gray-900 mb-2">Recommendations</h4>
              <ul className="space-y-2">
                {impactAssessment.recommendations.map((rec, index) => (
                  <li key={index} className="flex gap-2 text-sm text-gray-700">
                    <span className="text-blue-600">•</span>
                    <span>{rec}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * Impact progress bar
 */
function ImpactBar({ label, value }: { label: string; value: number }) {
  const percentage = Math.abs(value);
  const isPositive = value >= 0;
  const barColor = isPositive ? 'bg-green-500' : 'bg-red-500';

  return (
    <div>
      <div className="flex justify-between items-center mb-1">
        <span className="text-sm text-gray-700">{label}</span>
        <span className={`text-sm font-semibold ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
          {isPositive ? '+' : ''}
          {value.toFixed(0)}
        </span>
      </div>
      <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
        <div
          className={`h-full ${barColor} transition-all`}
          style={{ width: `${Math.min(100, percentage)}%` }}
        />
      </div>
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function VersionComparison({
  versionAId: initialVersionA,
  versionBId: initialVersionB,
  className = '',
}: VersionComparisonProps) {
  const [versionAId, setVersionAId] = useState<string | undefined>(initialVersionA);
  const [versionBId, setVersionBId] = useState<string | undefined>(initialVersionB);
  const [selectedCategory, setSelectedCategory] = useState<MetricCategory | 'all'>('all');

  const {
    data: comparison,
    isLoading,
    error,
  } = useVersionComparison(versionAId || '', versionBId || '', {
    enabled: !!versionAId && !!versionBId,
  });

  // Filter deltas by category
  const filteredDeltas =
    selectedCategory === 'all'
      ? comparison?.deltas || []
      : comparison?.deltas.filter((d) => d.category === selectedCategory) || [];

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Version Selectors */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Compare Schedule Versions</h2>
        <div className="flex flex-col sm:flex-row gap-4">
          <VersionSelector
            selectedVersionId={versionAId}
            onVersionChange={setVersionAId}
            label="Version A (Baseline)"
            excludeVersionId={versionBId}
          />
          <VersionSelector
            selectedVersionId={versionBId}
            onVersionChange={setVersionBId}
            label="Version B (Comparison)"
            excludeVersionId={versionAId}
          />
        </div>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="bg-white border border-gray-200 rounded-lg p-12 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">Comparing versions...</p>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <div className="flex items-center gap-2 text-red-600">
            <AlertTriangle className="w-5 h-5" />
            <p className="text-sm font-medium">Failed to load comparison data</p>
          </div>
        </div>
      )}

      {/* Comparison Results */}
      {comparison && (
        <>
          {/* Impact Assessment */}
          <ImpactAssessmentCard impactAssessment={comparison.impactAssessment} />

          {/* Metric Deltas */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-gray-900">Metric Changes</h3>
              {/* Category Filter */}
              <div className="flex items-center gap-1 bg-gray-100 rounded-lg p-1">
                {(['all', 'fairness', 'coverage', 'compliance', 'workload'] as const).map((cat) => (
                  <button
                    key={cat}
                    type="button"
                    onClick={() => setSelectedCategory(cat)}
                    className={`
                      px-3 py-1.5 rounded-md text-xs font-medium transition-colors
                      ${
                        selectedCategory === cat
                          ? 'bg-white text-blue-600 shadow-sm'
                          : 'text-gray-600 hover:text-gray-900'
                      }
                    `}
                  >
                    {cat === 'all' ? 'All' : METRIC_CATEGORY_LABELS[cat as MetricCategory]}
                  </button>
                ))}
              </div>
            </div>

            <div className="grid gap-4">
              {filteredDeltas.length > 0 ? (
                filteredDeltas.map((delta, index) => <MetricDeltaRow key={index} delta={delta} />)
              ) : (
                <p className="text-center text-gray-500 py-8">No metrics to display</p>
              )}
            </div>
          </div>

          {/* Recommendation */}
          {comparison.recommendation && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
              <div className="flex gap-3">
                <Info className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-sm font-semibold text-blue-900 mb-1">Recommendation</h4>
                  <p className="text-sm text-blue-800">{comparison.recommendation}</p>
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {/* Empty State */}
      {!versionAId || !versionBId ? (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-12 text-center">
          <Info className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">Select two versions to compare</p>
        </div>
      ) : null}
    </div>
  );
}
