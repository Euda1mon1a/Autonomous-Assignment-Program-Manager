/**
 * Admin Scheduling Types
 *
 * Types for the admin scheduling laboratory interface including
 * run configuration, experimentation, metrics, and manual overrides.
 */

// ============================================================================
// Algorithm & Configuration Types
// ============================================================================

export type Algorithm = 'greedy' | 'cpSat' | 'pulp' | 'hybrid';

export interface ConstraintConfig {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
  category: 'acgme' | 'coverage' | 'fairness' | 'custom';
  severity: 'hard' | 'soft';
}

export interface RunConfiguration {
  algorithm: Algorithm;
  constraints: ConstraintConfig[];
  preserveFMIT: boolean;
  nfPostCallEnabled: boolean;
  academicYear: string;
  blockRange: {
    start: number;
    end: number;
  };
  timeoutSeconds: number;
  dryRun: boolean;
}

// ============================================================================
// Data Provenance Types
// ============================================================================

export type DataSource = 'manual' | 'import' | 'system' | 'migration';

export interface SyncMetadata {
  lastSyncTime: string;
  syncStatus: 'synced' | 'pending' | 'error';
  sourceSystem: string;
  recordsAffected: number;
}

export interface DataProvenanceInfo {
  source: DataSource;
  importedAt?: string;
  importedBy?: string;
  modifiedAt?: string;
  modifiedBy?: string;
  seedCleanupMode: 'none' | 'soft' | 'hard';
}

// ============================================================================
// Experimentation Types
// ============================================================================

export interface ScenarioPreset {
  id: string;
  name: string;
  description: string;
  size: 'small' | 'medium' | 'large';
  residentCount: number;
  facultyCount: number;
  blockCount: number;
  constraints: string[];
}

export interface PermutationConfig {
  algorithms: Algorithm[];
  constraintSets: string[][];
  scenarioPresets: string[];
}

export interface ExperimentRun {
  id: string;
  name: string;
  status: 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';
  configuration: RunConfiguration;
  queuedAt: string;
  startedAt?: string;
  completedAt?: string;
  progress?: number;
  result?: RunResult;
}

export interface RunQueue {
  runs: ExperimentRun[];
  maxConcurrent: number;
  currentlyRunning: number;
}

// ============================================================================
// Metrics & Results Types
// ============================================================================

export interface RunResult {
  runId: string;
  status: 'success' | 'partial' | 'failed';
  coveragePercent: number;
  acgmeViolations: number;
  fairnessScore: number;
  swapChurn: number;
  runtimeSeconds: number;
  stability: number;
  blocksAssigned: number;
  totalBlocks: number;
  timestamp: string;
}

export interface MetricsTrend {
  metric: string;
  values: {
    timestamp: string;
    value: number;
  }[];
  trend: 'improving' | 'stable' | 'declining';
}

export interface ComparisonData {
  runA: RunResult;
  runB: RunResult;
  differences: {
    metric: string;
    delta: number;
    percentChange: number;
    winner: 'A' | 'B' | 'tie';
  }[];
}

// ============================================================================
// Run Log Types
// ============================================================================

export interface RunLogEntry {
  id: string;
  runId: string;
  algorithm: Algorithm;
  timestamp: string;
  status: 'success' | 'partial' | 'failed';
  configuration: RunConfiguration;
  result: RunResult;
  notes?: string;
  tags?: string[];
  /** Coverage percentage achieved (0-100) */
  coverage?: number;
  /** Number of constraint violations */
  violations?: number;
  /** Duration of the run (e.g., "2m 30s") */
  duration?: string;
}

export interface RunLogFilters {
  runId?: string;
  algorithms?: Algorithm[];
  dateRange?: {
    start: string;
    end: string;
  };
  status?: ('success' | 'partial' | 'failed')[];
  tags?: string[];
}

// ============================================================================
// Manual Override Types
// ============================================================================

export interface LockedAssignment {
  id: string;
  personId: string;
  personName: string;
  blockId: string;
  blockDate: string;
  rotationId: string;
  rotationName: string;
  lockedAt: string;
  lockedBy: string;
  reason: string;
  expiresAt?: string;
}

export interface EmergencyHoliday {
  id: string;
  date: string;
  name: string;
  type: 'federal' | 'state' | 'custom';
  affectsScheduling: boolean;
  createdAt: string;
  createdBy: string;
}

export interface RollbackPoint {
  id: string;
  createdAt: string;
  createdBy: string;
  description: string;
  runId?: string;
  assignmentCount: number;
  canRevert: boolean;
}

export interface RevertRequest {
  rollbackPointId: string;
  reason: string;
  dryRun: boolean;
}

// ============================================================================
// Safety & Warning Types
// ============================================================================

export type RiskLevel = 'low' | 'medium' | 'high' | 'critical';

export interface ConfigWarning {
  id: string;
  type: 'constraint_conflict' | 'coverage_risk' | 'compliance_risk' | 'performance_risk';
  severity: RiskLevel;
  message: string;
  details?: string;
  affectedAreas?: string[];
}

export interface SafetyCheck {
  id: string;
  name: string;
  passed: boolean;
  message: string;
  severity: RiskLevel;
  canProceed: boolean;
  requiresConfirmation: boolean;
}

export interface ConfirmationModalProps {
  title: string;
  message: string;
  warnings: ConfigWarning[];
  onConfirm: () => void;
  onCancel: () => void;
  confirmLabel?: string;
  cancelLabel?: string;
  isDangerous?: boolean;
}

// ============================================================================
// API Response Types
// ============================================================================

export interface ScheduleRunsResponse {
  runs: RunLogEntry[];
  total: number;
  page: number;
  pageSize: number;
}

export interface RunComparisonResponse {
  comparison: ComparisonData;
  insights: string[];
  recommendation?: string;
}

export interface ValidationResponse {
  isValid: boolean;
  warnings: ConfigWarning[];
  safetyChecks: SafetyCheck[];
  estimatedRuntime?: number;
  estimatedCoverage?: number;
}

// ============================================================================
// State Types
// ============================================================================

export type AdminSchedulingTab =
  | 'configuration'
  | 'experimentation'
  | 'metrics'
  | 'history'
  | 'overrides';

export interface AdminSchedulingState {
  activeTab: AdminSchedulingTab;
  configuration: RunConfiguration;
  isRunning: boolean;
  lastRun?: RunResult;
  warnings: ConfigWarning[];
  queue: RunQueue;
  selectedRuns: string[];
  comparisonMode: boolean;
}
