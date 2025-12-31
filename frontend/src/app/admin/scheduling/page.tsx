'use client';

/**
 * Admin Scheduling Laboratory
 *
 * Private admin GUI for empirical analysis of scheduling modules.
 * Provides configuration, experimentation, metrics, history, and override controls.
 */
import { useState, useCallback, useMemo } from 'react';
import {
  Settings,
  Beaker,
  BarChart3,
  History,
  Shield,
  Play,
  Pause,
  RotateCcw,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Zap,
  Target,
  TrendingUp,
  TrendingDown,
  Minus,
  Lock,
  Unlock,
  Calendar,
  RefreshCw,
  Trash2,
  GitCompare,
  Download,
  ChevronDown,
  ChevronUp,
  Info,
  XCircle,
  Loader2,
} from 'lucide-react';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import {
  useScheduleRuns,
  useRunQueue,
  useConstraintConfigs,
  useScenarioPresets,
  useScheduleMetrics,
  useLockedAssignments,
  useEmergencyHolidays,
  useRollbackPoints,
  useValidateConfiguration,
  useGenerateScheduleRun,
  useQueueExperiments,
  useCancelExperiment,
  useLockAssignment,
  useUnlockAssignment,
  useCreateRollbackPoint,
  useRevertToRollbackPoint,
  useSyncMetadata,
  useTriggerSync,
} from '@/hooks/useAdminScheduling';
import type {
  Algorithm,
  RunConfiguration,
  ConstraintConfig,
  AdminSchedulingTab,
  RiskLevel,
  ConfigWarning,
  RunLogEntry,
  ExperimentRun,
} from '@/types/admin-scheduling';

// ============================================================================
// Constants
// ============================================================================

const ALGORITHMS: { value: Algorithm; label: string; description: string }[] = [
  { value: 'greedy', label: 'Greedy', description: 'Fast heuristic, assigns hardest blocks first' },
  { value: 'cp_sat', label: 'CP-SAT', description: 'Constraint programming, guarantees compliance' },
  { value: 'pulp', label: 'PuLP', description: 'Linear programming, fast for large problems' },
  { value: 'hybrid', label: 'Hybrid', description: 'Combines CP-SAT and PuLP for best results' },
];

const SCENARIO_PRESETS = [
  { id: 'small', name: 'Small', residents: 5, faculty: 2, blocks: 60 },
  { id: 'medium', name: 'Medium', residents: 15, faculty: 5, blocks: 180 },
  { id: 'large', name: 'Large', residents: 30, faculty: 10, blocks: 365 },
];

const TABS: { id: AdminSchedulingTab; label: string; icon: React.ElementType }[] = [
  { id: 'configuration', label: 'Configuration', icon: Settings },
  { id: 'experimentation', label: 'Experimentation', icon: Beaker },
  { id: 'metrics', label: 'Metrics', icon: BarChart3 },
  { id: 'history', label: 'History', icon: History },
  { id: 'overrides', label: 'Overrides', icon: Shield },
];

const DEFAULT_CONFIGURATION: RunConfiguration = {
  algorithm: 'hybrid',
  constraints: [],
  preserveFMIT: true,
  nfPostCallEnabled: true,
  academicYear: '2024-2025',
  blockRange: { start: 1, end: 730 },
  timeoutSeconds: 300,
  dryRun: false,
};

// ============================================================================
// Main Page Component
// ============================================================================

export default function AdminSchedulingPage() {
  const [activeTab, setActiveTab] = useState<AdminSchedulingTab>('configuration');
  const [configuration, setConfiguration] = useState<RunConfiguration>(DEFAULT_CONFIGURATION);
  const [selectedRuns, setSelectedRuns] = useState<string[]>([]);
  const [comparisonMode, setComparisonMode] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [pendingAction, setPendingAction] = useState<(() => void) | null>(null);

  // Queries
  const { data: constraints, isLoading: constraintsLoading } = useConstraintConfigs();
  const { data: queue, isLoading: queueLoading } = useRunQueue();
  const { data: metrics, isLoading: metricsLoading } = useScheduleMetrics();
  const { data: runs, isLoading: runsLoading } = useScheduleRuns();
  const { data: locks } = useLockedAssignments();
  const { data: holidays } = useEmergencyHolidays();
  const { data: rollbackPoints } = useRollbackPoints();
  const { data: syncMeta } = useSyncMetadata();

  // Mutations
  const validateConfig = useValidateConfiguration();
  const generateRun = useGenerateScheduleRun();
  const queueExperiments = useQueueExperiments();
  const cancelExperiment = useCancelExperiment();
  const createRollback = useCreateRollbackPoint();
  const revertRollback = useRevertToRollbackPoint();
  const triggerSync = useTriggerSync();
  const unlockAssignment = useUnlockAssignment();

  const handleConfigChange = useCallback((updates: Partial<RunConfiguration>) => {
    setConfiguration(prev => ({ ...prev, ...updates }));
  }, []);

  const handleValidateAndRun = useCallback(async () => {
    const validation = await validateConfig.mutateAsync(configuration);
    if (!validation.isValid) {
      setShowConfirmModal(true);
      setPendingAction(() => () => generateRun.mutate(configuration));
      return;
    }
    generateRun.mutate(configuration);
  }, [configuration, validateConfig, generateRun]);

  // Performance: Memoize computed isRunning state to avoid recalculation on every render
  const isRunning = useMemo(() =>
    generateRun.isPending || (queue?.currentlyRunning ?? 0) > 0,
    [generateRun.isPending, queue?.currentlyRunning]
  );

  // Performance: Memoize filtered and sorted data arrays
  const processedRuns = useMemo(() =>
    (runs?.runs || []).slice().sort((a, b) =>
      new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
    ),
    [runs?.runs]
  );

  // Performance: Memoize active constraints count
  const activeConstraintsCount = useMemo(() =>
    configuration.constraints.filter(c => c.enabled).length,
    [configuration.constraints]
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <header className="border-b border-slate-700/50 bg-slate-900/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-violet-500 to-purple-600 rounded-lg">
                <Beaker className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">
                  Scheduling Laboratory
                </h1>
                <p className="text-sm text-slate-400">
                  Empirical analysis of scheduling algorithms
                </p>
              </div>
            </div>

            {/* Status Indicators */}
            <div className="flex items-center gap-4">
              <StatusBadge
                status={isRunning ? 'running' : 'idle'}
                count={queue?.currentlyRunning}
              />
              <StatusBadge
                status={syncMeta?.syncStatus || 'synced'}
                label="Sync"
              />
            </div>
          </div>

          {/* Tabs */}
          <nav className="flex gap-1 mt-4 -mb-px overflow-x-auto">
            {TABS.map(tab => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`
                    flex items-center gap-2 px-4 py-2.5 text-sm font-medium rounded-t-lg
                    transition-all duration-200
                    ${isActive
                      ? 'bg-slate-800 text-white border-t border-x border-slate-700'
                      : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                    }
                  `}
                >
                  <Icon className="w-4 h-4" />
                  <span className="hidden sm:inline">{tab.label}</span>
                </button>
              );
            })}
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {activeTab === 'configuration' && (
          <ConfigurationPanel
            configuration={configuration}
            constraints={constraints || []}
            isLoading={constraintsLoading}
            onChange={handleConfigChange}
            onRun={handleValidateAndRun}
            onValidate={() => validateConfig.mutate(configuration)}
            isRunning={isRunning}
            isValidating={validateConfig.isPending}
            validationResult={validateConfig.data}
          />
        )}

        {activeTab === 'experimentation' && (
          <ExperimentationPanel
            configuration={configuration}
            queue={queue}
            isLoading={queueLoading}
            onQueueExperiments={(configs) => queueExperiments.mutate(configs)}
            onCancelExperiment={(id) => cancelExperiment.mutate(id)}
            isQueuing={queueExperiments.isPending}
          />
        )}

        {activeTab === 'metrics' && (
          <MetricsPanel
            metrics={metrics}
            isLoading={metricsLoading}
            runs={processedRuns}
          />
        )}

        {activeTab === 'history' && (
          <HistoryPanel
            runs={processedRuns}
            isLoading={runsLoading}
            selectedRuns={selectedRuns}
            comparisonMode={comparisonMode}
            onSelectRun={(id) => {
              if (comparisonMode) {
                setSelectedRuns(prev =>
                  prev.includes(id)
                    ? prev.filter(r => r !== id)
                    : prev.length < 2 ? [...prev, id] : [prev[1], id]
                );
              }
            }}
            onToggleComparison={() => {
              setComparisonMode(prev => !prev);
              setSelectedRuns([]);
            }}
          />
        )}

        {activeTab === 'overrides' && (
          <OverridesPanel
            locks={locks || []}
            holidays={holidays || []}
            rollbackPoints={rollbackPoints || []}
            syncMeta={syncMeta}
            onCreateRollback={(desc) => createRollback.mutate({ description: desc })}
            onRevert={(pointId, reason) => revertRollback.mutate({
              rollbackPointId: pointId,
              reason,
              dryRun: false,
            })}
            onSync={() => triggerSync.mutate()}
            onUnlock={(lockId) => unlockAssignment.mutate(lockId)}
            isCreatingRollback={createRollback.isPending}
            isReverting={revertRollback.isPending}
            isSyncing={triggerSync.isPending}
            isUnlocking={unlockAssignment.isPending}
          />
        )}
      </main>

      {/* Confirmation Modal */}
      {showConfirmModal && (
        <ConfirmationModal
          title="Configuration Warnings"
          message="There are warnings with your configuration. Do you want to proceed anyway?"
          warnings={validateConfig.data?.warnings || []}
          onConfirm={() => {
            pendingAction?.();
            setShowConfirmModal(false);
            setPendingAction(null);
          }}
          onCancel={() => {
            setShowConfirmModal(false);
            setPendingAction(null);
          }}
        />
      )}
    </div>
  );
}

// ============================================================================
// Status Badge Component
// ============================================================================

function StatusBadge({
  status,
  label,
  count,
}: {
  status: string;
  label?: string;
  count?: number;
}) {
  // Performance: Memoize status color calculation to avoid recalculation on every render
  const statusColor = useMemo(() => {
    switch (status) {
      case 'running':
        return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
      case 'synced':
        return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
      case 'pending':
        return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
      case 'error':
        return 'bg-red-500/20 text-red-400 border-red-500/30';
      default:
        return 'bg-slate-500/20 text-slate-400 border-slate-500/30';
    }
  }, [status]);

  return (
    <div className={`
      flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-medium
      ${statusColor}
    `}>
      {status === 'running' && <Loader2 className="w-3 h-3 animate-spin" />}
      {status === 'synced' && <CheckCircle2 className="w-3 h-3" />}
      {status === 'pending' && <Clock className="w-3 h-3" />}
      {status === 'error' && <XCircle className="w-3 h-3" />}
      {status === 'idle' && <Pause className="w-3 h-3" />}
      <span>{label || status}</span>
      {count !== undefined && count > 0 && (
        <span className="ml-1 px-1.5 py-0.5 bg-white/10 rounded">
          {count}
        </span>
      )}
    </div>
  );
}

// ============================================================================
// Configuration Panel
// ============================================================================

function ConfigurationPanel({
  configuration,
  constraints,
  isLoading,
  onChange,
  onRun,
  onValidate,
  isRunning,
  isValidating,
  validationResult,
}: {
  configuration: RunConfiguration;
  constraints: ConstraintConfig[];
  isLoading: boolean;
  onChange: (updates: Partial<RunConfiguration>) => void;
  onRun: () => void;
  onValidate: () => void;
  isRunning: boolean;
  isValidating: boolean;
  validationResult?: { isValid: boolean; warnings: ConfigWarning[] };
}) {
  const [expandedSections, setExpandedSections] = useState({
    algorithm: true,
    constraints: true,
    options: true,
    dateRange: true,
  });

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }));
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Left Column: Configuration */}
      <div className="lg:col-span-2 space-y-6">
        {/* Algorithm Selection */}
        <ConfigSection
          title="Algorithm Selection"
          icon={Zap}
          expanded={expandedSections.algorithm}
          onToggle={() => toggleSection('algorithm')}
        >
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {ALGORITHMS.map(algo => (
              <button
                key={algo.value}
                onClick={() => onChange({ algorithm: algo.value })}
                className={`
                  p-4 rounded-lg border transition-all
                  ${configuration.algorithm === algo.value
                    ? 'bg-violet-500/20 border-violet-500 text-white'
                    : 'bg-slate-800/50 border-slate-700 text-slate-300 hover:border-slate-600'
                  }
                `}
              >
                <div className="font-medium">{algo.label}</div>
                <div className="text-xs text-slate-400 mt-1">{algo.description}</div>
              </button>
            ))}
          </div>
        </ConfigSection>

        {/* Constraint Toggles */}
        <ConfigSection
          title="Constraint Set"
          icon={Target}
          expanded={expandedSections.constraints}
          onToggle={() => toggleSection('constraints')}
          badge={constraints.filter(c => c.enabled).length}
        >
          <div className="space-y-2">
            {constraints.length === 0 ? (
              <EmptyState message="No constraints available" />
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {constraints.map(constraint => (
                  <ConstraintToggle
                    key={constraint.id}
                    constraint={constraint}
                    enabled={configuration.constraints.find(c => c.id === constraint.id)?.enabled ?? constraint.enabled}
                    onToggle={(enabled) => {
                      const updated = configuration.constraints.map(c =>
                        c.id === constraint.id ? { ...c, enabled } : c
                      );
                      if (!updated.find(c => c.id === constraint.id)) {
                        updated.push({ ...constraint, enabled });
                      }
                      onChange({ constraints: updated });
                    }}
                  />
                ))}
              </div>
            )}
          </div>
        </ConfigSection>

        {/* Options */}
        <ConfigSection
          title="Options"
          icon={Settings}
          expanded={expandedSections.options}
          onToggle={() => toggleSection('options')}
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <ToggleOption
              label="Preserve FMIT Assignments"
              description="Keep existing FMIT faculty assignments"
              enabled={configuration.preserveFMIT}
              onChange={(enabled) => onChange({ preserveFMIT: enabled })}
            />
            <ToggleOption
              label="NF Post-Call Constraint"
              description="Apply Night Float post-call rules"
              enabled={configuration.nfPostCallEnabled}
              onChange={(enabled) => onChange({ nfPostCallEnabled: enabled })}
            />
            <ToggleOption
              label="Dry Run Mode"
              description="Validate without making changes"
              enabled={configuration.dryRun}
              onChange={(enabled) => onChange({ dryRun: enabled })}
              warning={!configuration.dryRun}
            />
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-300">
                Timeout (seconds)
              </label>
              <input
                type="number"
                value={configuration.timeoutSeconds}
                onChange={(e) => onChange({ timeoutSeconds: parseInt(e.target.value) || 300 })}
                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white"
                min={30}
                max={3600}
              />
            </div>
          </div>
        </ConfigSection>

        {/* Date Range */}
        <ConfigSection
          title="Academic Year & Block Range"
          icon={Calendar}
          expanded={expandedSections.dateRange}
          onToggle={() => toggleSection('dateRange')}
        >
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-300">Academic Year</label>
              <select
                value={configuration.academicYear}
                onChange={(e) => onChange({ academicYear: e.target.value })}
                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white"
              >
                <option value="2023-2024">2023-2024</option>
                <option value="2024-2025">2024-2025</option>
                <option value="2025-2026">2025-2026</option>
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-300">Start Block</label>
              <input
                type="number"
                value={configuration.blockRange.start}
                onChange={(e) => onChange({
                  blockRange: { ...configuration.blockRange, start: parseInt(e.target.value) || 1 }
                })}
                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white"
                min={1}
                max={730}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-300">End Block</label>
              <input
                type="number"
                value={configuration.blockRange.end}
                onChange={(e) => onChange({
                  blockRange: { ...configuration.blockRange, end: parseInt(e.target.value) || 730 }
                })}
                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white"
                min={1}
                max={730}
              />
            </div>
          </div>
          <div className="mt-4 flex items-center gap-2 text-sm text-slate-400">
            <Info className="w-4 h-4" />
            <span>730 blocks = 365 days (AM/PM sessions)</span>
          </div>
        </ConfigSection>
      </div>

      {/* Right Column: Actions & Validation */}
      <div className="space-y-6">
        {/* Run Actions */}
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Run Schedule</h3>

          <div className="space-y-4">
            <button
              onClick={onValidate}
              disabled={isValidating}
              className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors disabled:opacity-50"
            >
              {isValidating ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <CheckCircle2 className="w-4 h-4" />
              )}
              Validate Configuration
            </button>

            <button
              onClick={onRun}
              disabled={isRunning}
              className={`
                w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-medium transition-all
                ${configuration.dryRun
                  ? 'bg-amber-600 hover:bg-amber-500 text-white'
                  : 'bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-500 hover:to-purple-500 text-white'
                }
                disabled:opacity-50 disabled:cursor-not-allowed
              `}
            >
              {isRunning ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Running...
                </>
              ) : (
                <>
                  <Play className="w-5 h-5" />
                  {configuration.dryRun ? 'Run Dry Run' : 'Generate Schedule'}
                </>
              )}
            </button>
          </div>

          {/* Validation Result */}
          {validationResult && (
            <div className={`
              mt-4 p-4 rounded-lg border
              ${validationResult.isValid
                ? 'bg-emerald-500/10 border-emerald-500/30'
                : 'bg-amber-500/10 border-amber-500/30'
              }
            `}>
              <div className="flex items-center gap-2 mb-2">
                {validationResult.isValid ? (
                  <>
                    <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                    <span className="font-medium text-emerald-400">Valid Configuration</span>
                  </>
                ) : (
                  <>
                    <AlertTriangle className="w-5 h-5 text-amber-400" />
                    <span className="font-medium text-amber-400">
                      {validationResult.warnings.length} Warning(s)
                    </span>
                  </>
                )}
              </div>
              {validationResult.warnings.length > 0 && (
                <ul className="text-sm text-slate-300 space-y-1">
                  {validationResult.warnings.slice(0, 3).map((w, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="text-amber-400">•</span>
                      {w.message}
                    </li>
                  ))}
                  {validationResult.warnings.length > 3 && (
                    <li className="text-slate-500">
                      +{validationResult.warnings.length - 3} more...
                    </li>
                  )}
                </ul>
              )}
            </div>
          )}
        </div>

        {/* Quick Stats */}
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Configuration Summary</h3>
          <dl className="space-y-3 text-sm">
            <div className="flex justify-between">
              <dt className="text-slate-400">Algorithm</dt>
              <dd className="text-white font-medium">{configuration.algorithm.toUpperCase()}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-400">Blocks</dt>
              <dd className="text-white font-medium">
                {configuration.blockRange.end - configuration.blockRange.start + 1}
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-400">Constraints</dt>
              <dd className="text-white font-medium">
                {configuration.constraints.filter(c => c.enabled).length} active
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-400">Mode</dt>
              <dd className={`font-medium ${configuration.dryRun ? 'text-amber-400' : 'text-emerald-400'}`}>
                {configuration.dryRun ? 'Dry Run' : 'Live'}
              </dd>
            </div>
          </dl>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Experimentation Panel
// ============================================================================

function ExperimentationPanel({
  configuration,
  queue,
  isLoading,
  onQueueExperiments,
  onCancelExperiment,
  isQueuing,
}: {
  configuration: RunConfiguration;
  queue?: { runs: ExperimentRun[]; maxConcurrent: number; currentlyRunning: number };
  isLoading: boolean;
  onQueueExperiments: (configs: RunConfiguration[]) => void;
  onCancelExperiment: (id: string) => void;
  isQueuing: boolean;
}) {
  const [selectedAlgorithms, setSelectedAlgorithms] = useState<Algorithm[]>(['greedy', 'hybrid']);
  const [selectedPreset, setSelectedPreset] = useState<string>('medium');

  const handleQueuePermutations = () => {
    const configs = selectedAlgorithms.map(algo => ({
      ...configuration,
      algorithm: algo,
    }));
    onQueueExperiments(configs);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Left: Permutation Runner */}
      <div className="space-y-6">
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Beaker className="w-5 h-5 text-violet-400" />
            Permutation Runner
          </h3>

          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-slate-300 block mb-2">
                Algorithm Combinations
              </label>
              <div className="flex flex-wrap gap-2">
                {ALGORITHMS.map(algo => (
                  <button
                    key={algo.value}
                    onClick={() => {
                      setSelectedAlgorithms(prev =>
                        prev.includes(algo.value)
                          ? prev.filter(a => a !== algo.value)
                          : [...prev, algo.value]
                      );
                    }}
                    className={`
                      px-3 py-1.5 rounded-lg text-sm font-medium transition-all
                      ${selectedAlgorithms.includes(algo.value)
                        ? 'bg-violet-500 text-white'
                        : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                      }
                    `}
                  >
                    {algo.label}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="text-sm font-medium text-slate-300 block mb-2">
                Scenario Preset
              </label>
              <div className="grid grid-cols-3 gap-2">
                {SCENARIO_PRESETS.map(preset => (
                  <button
                    key={preset.id}
                    onClick={() => setSelectedPreset(preset.id)}
                    className={`
                      p-3 rounded-lg border text-left transition-all
                      ${selectedPreset === preset.id
                        ? 'bg-violet-500/20 border-violet-500 text-white'
                        : 'bg-slate-800 border-slate-700 text-slate-300 hover:border-slate-600'
                      }
                    `}
                  >
                    <div className="font-medium">{preset.name}</div>
                    <div className="text-xs text-slate-400 mt-1">
                      {preset.residents}R / {preset.faculty}F
                    </div>
                  </button>
                ))}
              </div>
            </div>

            <button
              onClick={handleQueuePermutations}
              disabled={isQueuing || selectedAlgorithms.length === 0}
              className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-500 hover:to-purple-500 text-white rounded-lg font-medium transition-all disabled:opacity-50"
            >
              {isQueuing ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Play className="w-5 h-5" />
              )}
              Queue {selectedAlgorithms.length} Experiment(s)
            </button>
          </div>
        </div>
      </div>

      {/* Right: Run Queue */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <Clock className="w-5 h-5 text-blue-400" />
            Run Queue
          </h3>
          <span className="text-sm text-slate-400">
            {queue?.currentlyRunning || 0} / {queue?.maxConcurrent || 3} running
          </span>
        </div>

        <div className="space-y-2 max-h-96 overflow-y-auto">
          {!queue?.runs?.length ? (
            <EmptyState message="No experiments in queue" />
          ) : (
            queue.runs.map(run => (
              <div
                key={run.id}
                className="flex items-center justify-between p-3 bg-slate-800 rounded-lg border border-slate-700"
              >
                <div className="flex items-center gap-3">
                  <StatusIndicator status={run.status} />
                  <div>
                    <div className="text-sm font-medium text-white">{run.name}</div>
                    <div className="text-xs text-slate-400">
                      {run.configuration.algorithm.toUpperCase()} • {run.status}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {run.status === 'running' && run.progress !== undefined && (
                    <div className="w-16 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-violet-500 transition-all"
                        style={{ width: `${run.progress}%` }}
                      />
                    </div>
                  )}
                  {(run.status === 'queued' || run.status === 'running') && (
                    <button
                      onClick={() => onCancelExperiment(run.id)}
                      className="p-1.5 text-slate-400 hover:text-red-400 transition-colors"
                    >
                      <XCircle className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Metrics Panel
// ============================================================================

function MetricsPanel({
  metrics,
  isLoading,
  runs,
}: {
  metrics?: {
    coveragePercent: number;
    acgmeViolations: number;
    fairnessScore: number;
    swapChurn: number;
    runtimeSeconds: number;
    stability: number;
  };
  isLoading: boolean;
  runs: RunLogEntry[];
}) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
      </div>
    );
  }

  const metricsCards = [
    {
      label: 'Coverage',
      value: metrics?.coveragePercent ?? 0,
      format: (v: number) => `${v.toFixed(1)}%`,
      target: 100,
      color: 'emerald',
      icon: Target,
    },
    {
      label: 'ACGME Violations',
      value: metrics?.acgmeViolations ?? 0,
      format: (v: number) => v.toString(),
      target: 0,
      inverse: true,
      color: 'red',
      icon: AlertTriangle,
    },
    {
      label: 'Fairness Score',
      value: metrics?.fairnessScore ?? 0,
      format: (v: number) => `${(v * 100).toFixed(0)}%`,
      target: 1,
      color: 'blue',
      icon: BarChart3,
    },
    {
      label: 'Swap Churn',
      value: metrics?.swapChurn ?? 0,
      format: (v: number) => `${v.toFixed(1)}%`,
      target: 5,
      inverse: true,
      color: 'amber',
      icon: RefreshCw,
    },
    {
      label: 'Runtime',
      value: metrics?.runtimeSeconds ?? 0,
      format: (v: number) => `${v.toFixed(1)}s`,
      target: 60,
      inverse: true,
      color: 'purple',
      icon: Clock,
    },
    {
      label: 'Stability',
      value: metrics?.stability ?? 0,
      format: (v: number) => `${(v * 100).toFixed(0)}%`,
      target: 1,
      color: 'cyan',
      icon: Shield,
    },
  ];

  return (
    <div className="space-y-6">
      {/* Metric Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {metricsCards.map(metric => {
          const Icon = metric.icon;
          const isGood = metric.inverse
            ? metric.value <= metric.target
            : metric.value >= metric.target;

          return (
            <div
              key={metric.label}
              className="bg-slate-800/50 border border-slate-700 rounded-xl p-4"
            >
              <div className="flex items-center justify-between mb-2">
                <Icon className={`w-5 h-5 text-${metric.color}-400`} />
                {isGood ? (
                  <TrendingUp className="w-4 h-4 text-emerald-400" />
                ) : (
                  <TrendingDown className="w-4 h-4 text-red-400" />
                )}
              </div>
              <div className="text-2xl font-bold text-white">
                {metric.format(metric.value)}
              </div>
              <div className="text-sm text-slate-400">{metric.label}</div>
            </div>
          );
        })}
      </div>

      {/* Charts Placeholder */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Coverage Trend</h3>
          <div className="h-64 flex items-center justify-center border border-dashed border-slate-600 rounded-lg">
            <span className="text-slate-500">Chart placeholder - Coverage over time</span>
          </div>
        </div>
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Algorithm Comparison</h3>
          <div className="h-64 flex items-center justify-center border border-dashed border-slate-600 rounded-lg">
            <span className="text-slate-500">Chart placeholder - Algorithm performance</span>
          </div>
        </div>
      </div>

      {/* Recent Runs Table */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Recent Runs</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-700">
                <th className="text-left py-3 px-4 text-slate-400 font-medium">Run ID</th>
                <th className="text-left py-3 px-4 text-slate-400 font-medium">Algorithm</th>
                <th className="text-left py-3 px-4 text-slate-400 font-medium">Status</th>
                <th className="text-left py-3 px-4 text-slate-400 font-medium">Coverage</th>
                <th className="text-left py-3 px-4 text-slate-400 font-medium">Violations</th>
                <th className="text-left py-3 px-4 text-slate-400 font-medium">Runtime</th>
              </tr>
            </thead>
            <tbody>
              {runs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-500">
                    No runs recorded yet
                  </td>
                </tr>
              ) : (
                runs.slice(0, 5).map(run => (
                  <tr key={run.id} className="border-b border-slate-700/50 hover:bg-slate-800/50">
                    <td className="py-3 px-4 text-white font-mono text-xs">
                      {run.runId.slice(0, 8)}...
                    </td>
                    <td className="py-3 px-4 text-white">{run.algorithm.toUpperCase()}</td>
                    <td className="py-3 px-4">
                      <StatusBadge status={run.status} />
                    </td>
                    <td className="py-3 px-4 text-white">
                      {run.result?.coveragePercent?.toFixed(1)}%
                    </td>
                    <td className="py-3 px-4 text-white">{run.result?.acgmeViolations}</td>
                    <td className="py-3 px-4 text-white">
                      {run.result?.runtimeSeconds?.toFixed(2)}s
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// History Panel
// ============================================================================

function HistoryPanel({
  runs,
  isLoading,
  selectedRuns,
  comparisonMode,
  onSelectRun,
  onToggleComparison,
}: {
  runs: RunLogEntry[];
  isLoading: boolean;
  selectedRuns: string[];
  comparisonMode: boolean;
  onSelectRun: (id: string) => void;
  onToggleComparison: () => void;
}) {
  const [filters, setFilters] = useState({
    algorithm: '',
    status: '',
    dateRange: '',
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
      </div>
    );
  }

  const filteredRuns = runs.filter(run => {
    if (filters.algorithm && run.algorithm !== filters.algorithm) return false;
    if (filters.status && run.status !== filters.status) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Filters & Actions */}
      <div className="flex flex-wrap items-center gap-4 bg-slate-800/50 border border-slate-700 rounded-xl p-4">
        <select
          value={filters.algorithm}
          onChange={(e) => setFilters(prev => ({ ...prev, algorithm: e.target.value }))}
          className="px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm"
        >
          <option value="">All Algorithms</option>
          {ALGORITHMS.map(a => (
            <option key={a.value} value={a.value}>{a.label}</option>
          ))}
        </select>

        <select
          value={filters.status}
          onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
          className="px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm"
        >
          <option value="">All Statuses</option>
          <option value="success">Success</option>
          <option value="partial">Partial</option>
          <option value="failed">Failed</option>
        </select>

        <div className="flex-1" />

        <button
          onClick={onToggleComparison}
          className={`
            flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all
            ${comparisonMode
              ? 'bg-violet-600 text-white'
              : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
            }
          `}
        >
          <GitCompare className="w-4 h-4" />
          {comparisonMode ? `Compare (${selectedRuns.length}/2)` : 'Compare Runs'}
        </button>

        <button
          className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg text-sm font-medium transition-all"
        >
          <Download className="w-4 h-4" />
          Export
        </button>
      </div>

      {/* Run List */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-slate-800">
              {comparisonMode && (
                <th className="w-12 py-3 px-4"></th>
              )}
              <th className="text-left py-3 px-4 text-slate-400 font-medium">Run ID</th>
              <th className="text-left py-3 px-4 text-slate-400 font-medium">Date</th>
              <th className="text-left py-3 px-4 text-slate-400 font-medium">Algorithm</th>
              <th className="text-left py-3 px-4 text-slate-400 font-medium">Status</th>
              <th className="text-left py-3 px-4 text-slate-400 font-medium">Coverage</th>
              <th className="text-left py-3 px-4 text-slate-400 font-medium">Violations</th>
              <th className="text-left py-3 px-4 text-slate-400 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredRuns.length === 0 ? (
              <tr>
                <td colSpan={comparisonMode ? 8 : 7} className="py-12 text-center text-slate-500">
                  No runs match your filters
                </td>
              </tr>
            ) : (
              filteredRuns.map(run => (
                <tr
                  key={run.id}
                  onClick={() => comparisonMode && onSelectRun(run.id)}
                  className={`
                    border-b border-slate-700/50 transition-colors
                    ${comparisonMode ? 'cursor-pointer' : ''}
                    ${selectedRuns.includes(run.id) ? 'bg-violet-500/10' : 'hover:bg-slate-800/50'}
                  `}
                >
                  {comparisonMode && (
                    <td className="py-3 px-4">
                      <div className={`
                        w-5 h-5 rounded border-2 flex items-center justify-center
                        ${selectedRuns.includes(run.id)
                          ? 'bg-violet-500 border-violet-500'
                          : 'border-slate-600'
                        }
                      `}>
                        {selectedRuns.includes(run.id) && (
                          <CheckCircle2 className="w-3 h-3 text-white" />
                        )}
                      </div>
                    </td>
                  )}
                  <td className="py-3 px-4 text-white font-mono text-xs">
                    {run.runId.slice(0, 8)}...
                  </td>
                  <td className="py-3 px-4 text-slate-300">
                    {new Date(run.timestamp).toLocaleString()}
                  </td>
                  <td className="py-3 px-4 text-white">{run.algorithm.toUpperCase()}</td>
                  <td className="py-3 px-4">
                    <StatusBadge status={run.status} />
                  </td>
                  <td className="py-3 px-4 text-white">
                    {run.result?.coveragePercent?.toFixed(1)}%
                  </td>
                  <td className="py-3 px-4 text-white">{run.result?.acgmeViolations}</td>
                  <td className="py-3 px-4">
                    <button className="p-1.5 text-slate-400 hover:text-white transition-colors">
                      <Info className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Comparison View */}
      {comparisonMode && selectedRuns.length === 2 && (
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Run Comparison</h3>
          <div className="grid grid-cols-2 gap-6">
            {selectedRuns.map((runId, idx) => {
              const run = runs.find(r => r.id === runId);
              if (!run) return null;
              return (
                <div key={runId} className="space-y-4">
                  <div className="flex items-center gap-2">
                    <span className={`
                      w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold
                      ${idx === 0 ? 'bg-blue-500' : 'bg-purple-500'} text-white
                    `}>
                      {String.fromCharCode(65 + idx)}
                    </span>
                    <span className="text-white font-mono text-sm">{run.runId.slice(0, 12)}</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div className="bg-slate-800 p-3 rounded-lg">
                      <div className="text-slate-400">Coverage</div>
                      <div className="text-white font-medium">
                        {run.result?.coveragePercent?.toFixed(1)}%
                      </div>
                    </div>
                    <div className="bg-slate-800 p-3 rounded-lg">
                      <div className="text-slate-400">Violations</div>
                      <div className="text-white font-medium">{run.result?.acgmeViolations}</div>
                    </div>
                    <div className="bg-slate-800 p-3 rounded-lg">
                      <div className="text-slate-400">Runtime</div>
                      <div className="text-white font-medium">
                        {run.result?.runtimeSeconds?.toFixed(2)}s
                      </div>
                    </div>
                    <div className="bg-slate-800 p-3 rounded-lg">
                      <div className="text-slate-400">Fairness</div>
                      <div className="text-white font-medium">
                        {((run.result?.fairnessScore ?? 0) * 100).toFixed(0)}%
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Overrides Panel
// ============================================================================

function OverridesPanel({
  locks,
  holidays,
  rollbackPoints,
  syncMeta,
  onCreateRollback,
  onRevert,
  onSync,
  onUnlock,
  isCreatingRollback,
  isReverting,
  isSyncing,
  isUnlocking,
}: {
  locks: { id: string; personName: string; blockDate: string; rotationName: string; reason: string }[];
  holidays: { id: string; date: string; name: string; type: string }[];
  rollbackPoints: { id: string; createdAt: string; description: string; assignmentCount: number; canRevert: boolean }[];
  syncMeta?: { lastSyncTime: string; syncStatus: string; sourceSystem: string };
  onCreateRollback: (description: string) => void;
  onRevert: (pointId: string, reason: string) => void;
  onSync: () => void;
  onUnlock: (lockId: string) => void;
  isCreatingRollback: boolean;
  isReverting: boolean;
  isSyncing: boolean;
  isUnlocking: boolean;
}) {
  const [rollbackDescription, setRollbackDescription] = useState('');
  const [revertPointId, setRevertPointId] = useState('');
  const [revertReason, setRevertReason] = useState('');
  const [showRevertConfirm, setShowRevertConfirm] = useState(false);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Locked Assignments */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Lock className="w-5 h-5 text-amber-400" />
          Locked Assignments
        </h3>
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {locks.length === 0 ? (
            <EmptyState message="No locked assignments" />
          ) : (
            locks.map(lock => (
              <div
                key={lock.id}
                className="flex items-center justify-between p-3 bg-slate-800 rounded-lg border border-slate-700"
              >
                <div>
                  <div className="text-sm font-medium text-white">{lock.personName}</div>
                  <div className="text-xs text-slate-400">
                    {lock.rotationName} • {lock.blockDate}
                  </div>
                </div>
                <button
                  className="p-1.5 text-slate-400 hover:text-amber-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  onClick={() => onUnlock(lock.id)}
                  disabled={isUnlocking}
                  aria-label={`Unlock assignment for ${lock.personName}`}
                >
                  <Unlock className="w-4 h-4" />
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Emergency Holidays */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Calendar className="w-5 h-5 text-red-400" />
          Emergency Holidays
        </h3>
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {holidays.length === 0 ? (
            <EmptyState message="No emergency holidays" />
          ) : (
            holidays.map(holiday => (
              <div
                key={holiday.id}
                className="flex items-center justify-between p-3 bg-slate-800 rounded-lg border border-slate-700"
              >
                <div>
                  <div className="text-sm font-medium text-white">{holiday.name}</div>
                  <div className="text-xs text-slate-400">
                    {holiday.date} • {holiday.type}
                  </div>
                </div>
                <button className="p-1.5 text-slate-400 hover:text-red-400 transition-colors">
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))
          )}
        </div>
        <button className="mt-4 w-full flex items-center justify-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg text-sm font-medium transition-all">
          <Calendar className="w-4 h-4" />
          Add Emergency Holiday
        </button>
      </div>

      {/* Rollback Points */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <RotateCcw className="w-5 h-5 text-blue-400" />
          Rollback Points
        </h3>

        {/* Create New Rollback */}
        <div className="flex gap-2 mb-4">
          <input
            type="text"
            value={rollbackDescription}
            onChange={(e) => setRollbackDescription(e.target.value)}
            placeholder="Snapshot description..."
            className="flex-1 px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm placeholder-slate-500"
          />
          <button
            onClick={() => {
              onCreateRollback(rollbackDescription);
              setRollbackDescription('');
            }}
            disabled={isCreatingRollback || !rollbackDescription}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-all disabled:opacity-50"
          >
            {isCreatingRollback ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Create'}
          </button>
        </div>

        <div className="space-y-2 max-h-48 overflow-y-auto">
          {rollbackPoints.length === 0 ? (
            <EmptyState message="No rollback points" />
          ) : (
            rollbackPoints.map(point => (
              <div
                key={point.id}
                className="flex items-center justify-between p-3 bg-slate-800 rounded-lg border border-slate-700"
              >
                <div>
                  <div className="text-sm font-medium text-white">{point.description}</div>
                  <div className="text-xs text-slate-400">
                    {new Date(point.createdAt).toLocaleString()} • {point.assignmentCount} assignments
                  </div>
                </div>
                <button
                  onClick={() => {
                    setRevertPointId(point.id);
                    setShowRevertConfirm(true);
                  }}
                  disabled={!point.canRevert}
                  className="px-3 py-1.5 bg-amber-600 hover:bg-amber-500 text-white rounded-lg text-xs font-medium transition-all disabled:opacity-50"
                >
                  Revert
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Data Sync */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <RefreshCw className="w-5 h-5 text-emerald-400" />
          Data Provenance
        </h3>

        <div className="space-y-4">
          <div className="p-4 bg-slate-800 rounded-lg border border-slate-700">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-slate-400">Last Sync</span>
              <StatusBadge status={syncMeta?.syncStatus || 'synced'} />
            </div>
            <div className="text-white font-medium">
              {syncMeta?.lastSyncTime
                ? new Date(syncMeta.lastSyncTime).toLocaleString()
                : 'Never'}
            </div>
            <div className="text-xs text-slate-500 mt-1">
              Source: {syncMeta?.sourceSystem || 'Unknown'}
            </div>
          </div>

          <button
            onClick={onSync}
            disabled={isSyncing}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg font-medium transition-all disabled:opacity-50"
          >
            {isSyncing ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <RefreshCw className="w-4 h-4" />
            )}
            Trigger Sync
          </button>
        </div>
      </div>

      {/* Revert Confirmation Modal */}
      {showRevertConfirm && (
        <ConfirmationModal
          title="Confirm Rollback"
          message="Are you sure you want to revert to this rollback point? This action cannot be undone."
          warnings={[{
            id: '1',
            type: 'coverage_risk',
            severity: 'high',
            message: 'All schedule changes since this point will be lost.',
          }]}
          onConfirm={() => {
            onRevert(revertPointId, revertReason || 'Manual rollback');
            setShowRevertConfirm(false);
            setRevertPointId('');
            setRevertReason('');
          }}
          onCancel={() => {
            setShowRevertConfirm(false);
            setRevertPointId('');
            setRevertReason('');
          }}
          isDangerous
        />
      )}
    </div>
  );
}

// ============================================================================
// Utility Components
// ============================================================================

function ConfigSection({
  title,
  icon: Icon,
  expanded,
  onToggle,
  badge,
  children,
}: {
  title: string;
  icon: React.ElementType;
  expanded: boolean;
  onToggle: () => void;
  badge?: number;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-slate-800/50 border border-slate-700 rounded-xl overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between p-4 hover:bg-slate-800/50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <Icon className="w-5 h-5 text-violet-400" />
          <span className="font-medium text-white">{title}</span>
          {badge !== undefined && (
            <span className="px-2 py-0.5 bg-violet-500/20 text-violet-400 text-xs rounded-full">
              {badge}
            </span>
          )}
        </div>
        {expanded ? (
          <ChevronUp className="w-5 h-5 text-slate-400" />
        ) : (
          <ChevronDown className="w-5 h-5 text-slate-400" />
        )}
      </button>
      {expanded && (
        <div className="p-4 pt-0 border-t border-slate-700/50">
          {children}
        </div>
      )}
    </div>
  );
}

function ConstraintToggle({
  constraint,
  enabled,
  onToggle,
}: {
  constraint: ConstraintConfig;
  enabled: boolean;
  onToggle: (enabled: boolean) => void;
}) {
  const categoryColors: Record<string, string> = {
    acgme: 'bg-red-500/20 text-red-400',
    coverage: 'bg-emerald-500/20 text-emerald-400',
    fairness: 'bg-blue-500/20 text-blue-400',
    custom: 'bg-purple-500/20 text-purple-400',
  };

  return (
    <button
      onClick={() => onToggle(!enabled)}
      className={`
        flex items-center justify-between p-3 rounded-lg border transition-all text-left
        ${enabled
          ? 'bg-slate-700/50 border-violet-500/50'
          : 'bg-slate-800/50 border-slate-700 opacity-60'
        }
      `}
    >
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-white truncate">
            {constraint.name}
          </span>
          <span className={`px-1.5 py-0.5 text-xs rounded ${categoryColors[constraint.category] || 'bg-slate-600 text-slate-300'}`}>
            {constraint.category}
          </span>
        </div>
        <p className="text-xs text-slate-400 mt-1 truncate">{constraint.description}</p>
      </div>
      <div className={`
        w-8 h-5 rounded-full p-0.5 transition-colors ml-3 flex-shrink-0
        ${enabled ? 'bg-violet-500' : 'bg-slate-600'}
      `}>
        <div className={`
          w-4 h-4 rounded-full bg-white transition-transform
          ${enabled ? 'translate-x-3' : 'translate-x-0'}
        `} />
      </div>
    </button>
  );
}

function ToggleOption({
  label,
  description,
  enabled,
  onChange,
  warning,
}: {
  label: string;
  description: string;
  enabled: boolean;
  onChange: (enabled: boolean) => void;
  warning?: boolean;
}) {
  return (
    <button
      onClick={() => onChange(!enabled)}
      className="flex items-start gap-3 p-3 rounded-lg bg-slate-800/50 border border-slate-700 text-left hover:border-slate-600 transition-colors"
    >
      <div className={`
        w-8 h-5 rounded-full p-0.5 transition-colors flex-shrink-0 mt-0.5
        ${enabled ? (warning ? 'bg-amber-500' : 'bg-violet-500') : 'bg-slate-600'}
      `}>
        <div className={`
          w-4 h-4 rounded-full bg-white transition-transform
          ${enabled ? 'translate-x-3' : 'translate-x-0'}
        `} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium text-white">{label}</div>
        <p className="text-xs text-slate-400 mt-0.5">{description}</p>
      </div>
    </button>
  );
}

function StatusIndicator({ status }: { status: string }) {
  const colors: Record<string, string> = {
    queued: 'bg-slate-500',
    running: 'bg-amber-500 animate-pulse',
    completed: 'bg-emerald-500',
    failed: 'bg-red-500',
    cancelled: 'bg-slate-600',
  };

  return (
    <div className={`w-2.5 h-2.5 rounded-full ${colors[status] || 'bg-slate-500'}`} />
  );
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="py-8 text-center text-slate-500 text-sm">
      {message}
    </div>
  );
}

function ConfirmationModal({
  title,
  message,
  warnings,
  onConfirm,
  onCancel,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  isDangerous = false,
}: {
  title: string;
  message: string;
  warnings: ConfigWarning[];
  onConfirm: () => void;
  onCancel: () => void;
  confirmLabel?: string;
  cancelLabel?: string;
  isDangerous?: boolean;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="bg-slate-800 border border-slate-700 rounded-xl shadow-2xl max-w-md w-full p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className={`p-2 rounded-lg ${isDangerous ? 'bg-red-500/20' : 'bg-amber-500/20'}`}>
            <AlertTriangle className={`w-5 h-5 ${isDangerous ? 'text-red-400' : 'text-amber-400'}`} />
          </div>
          <h3 className="text-lg font-semibold text-white">{title}</h3>
        </div>

        <p className="text-slate-300 mb-4">{message}</p>

        {warnings.length > 0 && (
          <div className="bg-slate-900/50 rounded-lg p-3 mb-4 space-y-2">
            {warnings.map((warning, i) => (
              <div key={i} className="flex items-start gap-2 text-sm">
                <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
                <span className="text-slate-300">{warning.message}</span>
              </div>
            ))}
          </div>
        )}

        <div className="flex gap-3 justify-end">
          <button
            onClick={onCancel}
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm font-medium transition-colors"
          >
            {cancelLabel}
          </button>
          <button
            onClick={onConfirm}
            className={`
              px-4 py-2 rounded-lg text-sm font-medium transition-colors
              ${isDangerous
                ? 'bg-red-600 hover:bg-red-500 text-white'
                : 'bg-amber-600 hover:bg-amber-500 text-white'
              }
            `}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
