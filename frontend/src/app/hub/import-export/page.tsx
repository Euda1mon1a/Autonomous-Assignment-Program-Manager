'use client';

/**
 * Unified Import/Export Hub
 *
 * Consolidates all import and export functionality into a single page:
 * - Staged Import (general schedule/people/absence imports with staging)
 * - Block Import (TRIPLER format block schedules)
 * - FMIT Import (FMIT attending schedules)
 * - Export (schedules, people, assignments)
 *
 * Implements tiered access control with RiskBar:
 * - Tier 0: Export only (green)
 * - Tier 1/2: Import actions (amber/red)
 */

import { useState, useCallback, useRef, useMemo } from 'react';
import {
  Upload,
  Download,
  FileSpreadsheet,
  FileText,
  Calendar,
  AlertTriangle,
  CheckCircle2,
  ArrowRight,
  Loader2,
  RefreshCw,
  X,
  ChevronDown,
  ChevronRight,
  AlertCircle,
  Users,
} from 'lucide-react';

// Components
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { RiskBar, useRiskTierFromRoles, type RiskTier } from '@/components/ui/RiskBar';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Alert } from '@/components/ui/Alert';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/contexts/ToastContext';

// Import hooks and components
import { ImportHistoryTable } from '@/features/import/components/ImportHistoryTable';
import { BulkImportModal } from '@/features/import-export/BulkImportModal';
import {
  ExportPanel,
  PEOPLE_EXPORT_COLUMNS,
  ASSIGNMENT_EXPORT_COLUMNS,
  SCHEDULE_EXPORT_COLUMNS,
} from '@/features/import-export';
import {
  useImportBatches,
  useRollbackBatch,
} from '@/hooks/useImport';
import { useFmitImport } from '@/hooks/useFmitImport';
import type {
  ResidentRosterItem,
  ParsedFMITWeek,
} from '@/types/fmit-import';

// ============================================================================
// Types
// ============================================================================

type HubTab = 'staged' | 'block' | 'fmit' | 'export';

interface TabConfig {
  id: HubTab;
  label: string;
  icon: React.ReactNode;
  description: string;
  tier: RiskTier;
}

// ============================================================================
// Tab Configuration
// ============================================================================

const TAB_CONFIG: TabConfig[] = [
  {
    id: 'staged',
    label: 'Staged Import',
    icon: <Upload className="w-4 h-4" />,
    description: 'General schedule, people, and absence imports with staging and review',
    tier: 1,
  },
  {
    id: 'block',
    label: 'Block Import',
    icon: <FileSpreadsheet className="w-4 h-4" />,
    description: 'TRIPLER format block schedules with rotation extraction',
    tier: 1,
  },
  {
    id: 'fmit',
    label: 'FMIT Import',
    icon: <Calendar className="w-4 h-4" />,
    description: 'FMIT attending schedules from Excel',
    tier: 1,
  },
  {
    id: 'export',
    label: 'Export',
    icon: <Download className="w-4 h-4" />,
    description: 'Export schedules, people, and reports',
    tier: 0,
  },
];

// ============================================================================
// Helper: Get max tier for current user based on actions available
// ============================================================================

function getMaxTierForTab(tabId: HubTab, userTier: RiskTier): RiskTier {
  const tabConfig = TAB_CONFIG.find((t) => t.id === tabId);
  if (!tabConfig) return 0;
  // User can only access up to their own tier
  return Math.min(tabConfig.tier, userTier) as RiskTier;
}

// ============================================================================
// Sub-Components: Block Import
// ============================================================================

interface ParsedAssignment {
  rotation: string;
  secondaryRotation: string | null;
  name: string;
  pgyLevel: number;
  block: number;
  role: string;
}

interface ParsedAbsence {
  name: string;
  dates: string[];
  type: string;
}

interface ParseResult {
  assignments: ParsedAssignment[];
  absences: ParsedAbsence[];
  fmitWeeks: { name: string; dates: string[] }[];
  blockNumber: number;
  warnings: string[];
}

interface BlockImportTabProps {
  userTier: RiskTier;
}

function BlockImportTab({ userTier }: BlockImportTabProps) {
  const { toast } = useToast();
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [parseResult, setParseResult] = useState<ParseResult | null>(null);
  const [isImporting, setIsImporting] = useState(false);
  const [importComplete, setImportComplete] = useState(false);

  const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setParseResult(null);
      setImportComplete(false);
    }
  }, []);

  const handleUpload = useCallback(async () => {
    if (!file) return;

    setIsUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('/api/v1/block-assignments/parse-block-sheet', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to parse file');
      }

      const data = await response.json();
      setParseResult(data.parsed);
      toast.success(`Parsed ${data.parsed.assignments.length} assignments`);
    } catch (error) {
      toast.error(`Upload failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsUploading(false);
    }
  }, [file, toast]);

  const handleImport = useCallback(async () => {
    if (!parseResult || userTier < 1) return;

    setIsImporting(true);
    try {
      const response = await fetch('/api/v1/block-assignments/import-block-sheet', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          assignments: parseResult.assignments,
          absences: parseResult.absences,
          blockNumber: parseResult.blockNumber,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to import');
      }

      const result = await response.json();
      setImportComplete(true);
      toast.success(`Imported ${result.assignmentsCreated} assignments, ${result.absencesCreated} absences`);
    } catch (error) {
      toast.error(`Import failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsImporting(false);
    }
  }, [parseResult, toast, userTier]);

  const handleReset = useCallback(() => {
    setFile(null);
    setParseResult(null);
    setImportComplete(false);
  }, []);

  const isReadOnly = userTier < 1;

  return (
    <div className="space-y-6">
      {isReadOnly && (
        <Alert variant="info">
          You have read-only access. Contact your administrator for import permissions.
        </Alert>
      )}

      {/* Upload Section */}
      <Card className="p-6 bg-slate-800 border-slate-700">
        <h3 className="text-lg font-semibold text-white mb-4">Upload TRIPLER Block Schedule</h3>
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <label className="block">
              <span className="sr-only">Choose xlsx file</span>
              <input
                type="file"
                accept=".xlsx,.xls"
                onChange={handleFileChange}
                disabled={isReadOnly}
                className="block w-full text-sm text-slate-300
                  file:mr-4 file:py-2 file:px-4
                  file:rounded-md file:border-0
                  file:text-sm file:font-semibold
                  file:bg-blue-600 file:text-white
                  hover:file:bg-blue-500
                  cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
              />
            </label>
          </div>
          <Button
            onClick={handleUpload}
            disabled={!file || isUploading || isReadOnly}
            className="bg-blue-600 hover:bg-blue-500"
          >
            {isUploading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Parsing...
              </>
            ) : (
              <>
                <Upload className="w-4 h-4 mr-2" />
                Parse File
              </>
            )}
          </Button>
        </div>
        {file && (
          <p className="mt-2 text-sm text-slate-400">
            <FileSpreadsheet className="w-4 h-4 inline mr-1" />
            {file.name}
          </p>
        )}
      </Card>

      {/* Two-Panel View */}
      {parseResult && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Panel: Source Data */}
          <Card className="p-6 bg-slate-800 border-slate-700">
            <h3 className="text-xl font-semibold text-white mb-4">Source Data</h3>
            <div className="overflow-x-auto max-h-[400px] overflow-y-auto">
              <table className="min-w-full text-sm">
                <thead className="bg-slate-700 sticky top-0">
                  <tr>
                    <th className="px-3 py-2 text-left text-slate-300">Rotation</th>
                    <th className="px-3 py-2 text-left text-slate-300">Role</th>
                    <th className="px-3 py-2 text-left text-slate-300">PGY</th>
                    <th className="px-3 py-2 text-left text-slate-300">Name</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-700">
                  {parseResult.assignments.map((a, idx) => (
                    <tr key={idx} className="hover:bg-slate-700/50">
                      <td className="px-3 py-2 text-white font-medium">{a.rotation}</td>
                      <td className="px-3 py-2 text-slate-300">{a.role}</td>
                      <td className="px-3 py-2 text-slate-300">{a.pgyLevel}</td>
                      <td className="px-3 py-2 text-slate-300">{a.name}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          {/* Right Panel: Extracted Constraints */}
          <Card className="p-6 bg-slate-800 border-slate-700">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-semibold text-white">Extracted Constraints</h3>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleReset}
                className="text-slate-400"
              >
                <RefreshCw className="w-4 h-4 mr-1" />
                Reset
              </Button>
            </div>

            {/* Rotations Summary */}
            <div className="mb-6">
              <h4 className="text-lg font-medium text-blue-400 mb-2">
                Rotations ({parseResult.assignments.length})
              </h4>
              <div className="space-y-1 max-h-32 overflow-y-auto">
                {parseResult.assignments.slice(0, 10).map((a, idx) => (
                  <div key={idx} className="flex items-center text-sm">
                    <CheckCircle2 className="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
                    <span className="text-slate-300">{a.name}</span>
                    <ArrowRight className="w-3 h-3 mx-2 text-slate-500" />
                    <span className="text-white font-medium">{a.rotation}</span>
                  </div>
                ))}
                {parseResult.assignments.length > 10 && (
                  <p className="text-sm text-slate-400">
                    ...and {parseResult.assignments.length - 10} more
                  </p>
                )}
              </div>
            </div>

            {/* Absences Summary */}
            <div className="mb-6">
              <h4 className="text-lg font-medium text-amber-400 mb-2">
                Absences ({parseResult.absences.length})
              </h4>
              {parseResult.absences.length > 0 ? (
                <div className="space-y-1 max-h-24 overflow-y-auto">
                  {parseResult.absences.slice(0, 5).map((abs, idx) => (
                    <div key={idx} className="flex items-center text-sm">
                      <AlertTriangle className="w-4 h-4 text-amber-500 mr-2 flex-shrink-0" />
                      <span className="text-slate-300">{abs.name}:</span>
                      <span className="text-white ml-2">{abs.dates.join(', ')}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-slate-400">No absences detected</p>
              )}
            </div>

            {/* Warnings */}
            {parseResult.warnings.length > 0 && (
              <Alert variant="warning" className="mb-4">
                <ul className="list-disc list-inside text-sm">
                  {parseResult.warnings.map((w, idx) => (
                    <li key={idx}>{w}</li>
                  ))}
                </ul>
              </Alert>
            )}

            {/* Import Button */}
            <div className="pt-4 border-t border-slate-700">
              {!importComplete ? (
                <Button
                  onClick={handleImport}
                  disabled={isImporting || isReadOnly}
                  className="w-full bg-green-600 hover:bg-green-500"
                >
                  {isImporting ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Importing...
                    </>
                  ) : (
                    'Import to Database'
                  )}
                </Button>
              ) : (
                <Alert variant="success">
                  <CheckCircle2 className="w-4 h-4 inline mr-2" />
                  Import complete! Block {parseResult.blockNumber} data is now in the database.
                </Alert>
              )}
            </div>
          </Card>
        </div>
      )}

      {/* Block Info */}
      {parseResult && (
        <Card className="p-4 bg-slate-800/50 border-slate-700">
          <p className="text-sm text-slate-300">
            <span className="font-medium text-white">Block {parseResult.blockNumber}</span>
            {' - '}
            {parseResult.assignments.length} residents
            {' - '}
            {parseResult.absences.length} absence periods
            {' - '}
            {parseResult.fmitWeeks.length} FMIT assignments
          </p>
        </Card>
      )}
    </div>
  );
}

// ============================================================================
// Sub-Components: FMIT Import
// ============================================================================

interface RosterSectionProps {
  title: string;
  residents: ResidentRosterItem[];
  defaultExpanded?: boolean;
}

function RosterSection({ title, residents, defaultExpanded = false }: RosterSectionProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  return (
    <div className="border border-slate-700 rounded-lg overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between px-4 py-3 bg-slate-800/50 hover:bg-slate-800 transition-colors"
      >
        <div className="flex items-center gap-2">
          {isExpanded ? (
            <ChevronDown className="w-4 h-4 text-slate-400" />
          ) : (
            <ChevronRight className="w-4 h-4 text-slate-400" />
          )}
          <span className="font-medium text-white">{title}</span>
          <span className="text-sm text-slate-400">({residents.length} residents)</span>
        </div>
      </button>
      {isExpanded && (
        <div className="p-4 space-y-2">
          {residents.map((resident, idx) => (
            <div
              key={`${resident.name}-${idx}`}
              className="flex items-center justify-between py-2 px-3 bg-slate-900/50 rounded"
            >
              <div className="flex items-center gap-3">
                <span className="text-white">{resident.name}</span>
                <span className="text-xs px-2 py-0.5 bg-slate-700 text-slate-300 rounded">
                  {resident.role}
                </span>
              </div>
              {resident.confidence < 1.0 && (
                <span className="text-xs text-amber-400 flex items-center gap-1">
                  <AlertTriangle className="w-3 h-3" />
                  {Math.round(resident.confidence * 100)}% match
                </span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

interface FmitScheduleTableProps {
  schedule: ParsedFMITWeek[];
}

function FmitScheduleTable({ schedule }: FmitScheduleTableProps) {
  if (schedule.length === 0) {
    return (
      <div className="text-center py-8 text-slate-400">
        No FMIT schedule found in this block
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-slate-700">
            <th className="px-4 py-3 text-left text-sm font-medium text-slate-400">Week</th>
            <th className="px-4 py-3 text-left text-sm font-medium text-slate-400">Faculty</th>
            <th className="px-4 py-3 text-left text-sm font-medium text-slate-400">Date Range</th>
            <th className="px-4 py-3 text-left text-sm font-medium text-slate-400">Holiday Call</th>
          </tr>
        </thead>
        <tbody>
          {schedule.map((week) => (
            <tr
              key={`${week.blockNumber}-${week.weekNumber}`}
              className="border-b border-slate-800 hover:bg-slate-800/50"
            >
              <td className="px-4 py-3 text-white">Week {week.weekNumber}</td>
              <td className="px-4 py-3">
                <span className="font-medium text-white">
                  {week.facultyName || <span className="text-slate-300 italic">Unassigned</span>}
                </span>
              </td>
              <td className="px-4 py-3 text-slate-300">
                {week.startDate && week.endDate
                  ? `${week.startDate} - ${week.endDate}`
                  : <span className="text-slate-300">-</span>}
              </td>
              <td className="px-4 py-3">
                {week.isHolidayCall ? (
                  <span className="text-xs px-2 py-1 bg-amber-500/20 text-amber-400 rounded">
                    Holiday
                  </span>
                ) : (
                  <span className="text-slate-300">-</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

interface FmitImportTabProps {
  userTier: RiskTier;
}

function FmitImportTab({ userTier }: FmitImportTabProps) {
  const { toast } = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Form state
  const [file, setFile] = useState<File | null>(null);
  const [blockNumber, setBlockNumber] = useState<number>(1);
  const [includeFmit, setIncludeFmit] = useState(true);
  const [dragActive, setDragActive] = useState(false);
  const [activeResultTab, setActiveResultTab] = useState<'fmit' | 'roster' | 'warnings'>('fmit');

  // Import hook
  const { parseBlock, isLoading, data, error, reset } = useFmitImport({
    onSuccess: (result) => {
      toast.success(
        `Parsed Block ${result.blockNumber}: ${result.totalResidents} residents, ${result.fmitSchedule.length} FMIT weeks`
      );
    },
    onError: (err) => {
      toast.error(`Parse failed: ${err.message}`);
    },
  });

  const handleFileSelect = useCallback((selectedFile: File) => {
    const validExtensions = ['.xlsx', '.xls'];
    const isValidType = validExtensions.some((ext) =>
      selectedFile.name.toLowerCase().endsWith(ext)
    );

    if (!isValidType) {
      toast.error('Please select an Excel file (.xlsx or .xls)');
      return;
    }

    const maxSize = 10 * 1024 * 1024;
    if (selectedFile.size > maxSize) {
      toast.error('File size exceeds 10MB limit');
      return;
    }

    setFile(selectedFile);
  }, [toast]);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragActive(false);

      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile) {
        handleFileSelect(droppedFile);
      }
    },
    [handleFileSelect]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
  }, []);

  const handleFileInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const selectedFile = e.target.files?.[0];
      if (selectedFile) {
        handleFileSelect(selectedFile);
      }
    },
    [handleFileSelect]
  );

  const handleSubmit = useCallback(() => {
    if (!file || userTier < 1) {
      toast.error(userTier < 1 ? 'You need import permissions' : 'Please select a file first');
      return;
    }

    parseBlock({
      file,
      blockNumber,
      includeFmit,
    });
  }, [file, blockNumber, includeFmit, parseBlock, toast, userTier]);

  const handleReset = useCallback(() => {
    reset();
    setFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, [reset]);

  const isReadOnly = userTier < 1;

  // Show results if we have data
  if (data) {
    return (
      <div className="space-y-6">
        {/* Summary Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            {data.success ? (
              <div className="flex items-center gap-2 text-green-400">
                <CheckCircle2 className="w-5 h-5" />
                <span className="font-medium">Parse Successful</span>
              </div>
            ) : (
              <div className="flex items-center gap-2 text-red-400">
                <AlertCircle className="w-5 h-5" />
                <span className="font-medium">Parse Completed with Errors</span>
              </div>
            )}
          </div>
          <Button
            onClick={handleReset}
            variant="outline"
            className="flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Import Another
          </Button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="p-4 bg-slate-800/50 border-slate-700">
            <div className="text-2xl font-bold text-white">{data.blockNumber}</div>
            <div className="text-sm text-slate-400">Block Number</div>
          </Card>
          <Card className="p-4 bg-slate-800/50 border-slate-700">
            <div className="text-2xl font-bold text-white">{data.totalResidents}</div>
            <div className="text-sm text-slate-400">Residents</div>
          </Card>
          <Card className="p-4 bg-slate-800/50 border-slate-700">
            <div className="text-2xl font-bold text-white">{data.fmitSchedule.length}</div>
            <div className="text-sm text-slate-400">FMIT Weeks</div>
          </Card>
          <Card className="p-4 bg-slate-800/50 border-slate-700">
            <div className="text-2xl font-bold text-white">{data.totalAssignments}</div>
            <div className="text-sm text-slate-400">Assignments</div>
          </Card>
        </div>

        {/* Block Date Range */}
        {(data.startDate || data.endDate) && (
          <div className="flex items-center gap-2 text-slate-300">
            <Calendar className="w-4 h-4 text-slate-400" />
            <span>
              Block {data.blockNumber}: {data.startDate || '?'} - {data.endDate || '?'}
            </span>
          </div>
        )}

        {/* Tabs */}
        <div className="border-b border-slate-700">
          <div className="flex gap-1">
            <button
              onClick={() => setActiveResultTab('fmit')}
              className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                activeResultTab === 'fmit'
                  ? 'border-blue-500 text-blue-400'
                  : 'border-transparent text-slate-400 hover:text-white'
              }`}
            >
              <div className="flex items-center gap-2">
                <Calendar className="w-4 h-4" />
                FMIT Schedule
              </div>
            </button>
            <button
              onClick={() => setActiveResultTab('roster')}
              className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                activeResultTab === 'roster'
                  ? 'border-blue-500 text-blue-400'
                  : 'border-transparent text-slate-400 hover:text-white'
              }`}
            >
              <div className="flex items-center gap-2">
                <Users className="w-4 h-4" />
                Roster ({data.totalResidents})
              </div>
            </button>
            <button
              onClick={() => setActiveResultTab('warnings')}
              className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                activeResultTab === 'warnings'
                  ? 'border-blue-500 text-blue-400'
                  : 'border-transparent text-slate-400 hover:text-white'
              }`}
            >
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4" />
                Warnings ({data.warnings.length + data.errors.length})
              </div>
            </button>
          </div>
        </div>

        {/* Tab Content */}
        <div className="min-h-[300px]">
          {activeResultTab === 'fmit' && (
            <Card className="bg-slate-800/30 border-slate-700 overflow-hidden">
              <FmitScheduleTable schedule={data.fmitSchedule} />
            </Card>
          )}

          {activeResultTab === 'roster' && (
            <div className="space-y-4">
              {Object.entries(data.residentsByTemplate).map(([template, residents]) => (
                <RosterSection
                  key={template}
                  title={template}
                  residents={residents}
                  defaultExpanded={template === 'R1'}
                />
              ))}
              {Object.keys(data.residentsByTemplate).length === 0 && (
                <div className="text-center py-8 text-slate-400">
                  No residents found in this block
                </div>
              )}
            </div>
          )}

          {activeResultTab === 'warnings' && (
            <div className="space-y-4">
              {data.errors.length > 0 && (
                <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
                  <h4 className="font-medium text-red-400 mb-2 flex items-center gap-2">
                    <AlertCircle className="w-4 h-4" />
                    Errors ({data.errors.length})
                  </h4>
                  <ul className="space-y-1 text-sm text-red-300">
                    {data.errors.map((err, idx) => (
                      <li key={idx}>{err}</li>
                    ))}
                  </ul>
                </div>
              )}
              {data.warnings.length > 0 && (
                <div className="p-4 bg-amber-500/10 border border-amber-500/30 rounded-lg">
                  <h4 className="font-medium text-amber-400 mb-2 flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4" />
                    Warnings ({data.warnings.length})
                  </h4>
                  <ul className="space-y-1 text-sm text-amber-300">
                    {data.warnings.map((warning, idx) => (
                      <li key={idx}>{warning}</li>
                    ))}
                  </ul>
                </div>
              )}
              {data.errors.length === 0 && data.warnings.length === 0 && (
                <div className="text-center py-8 text-green-400 flex flex-col items-center gap-2">
                  <CheckCircle2 className="w-8 h-8" />
                  <span>No warnings or errors</span>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    );
  }

  // Upload form
  return (
    <div className="space-y-6">
      {isReadOnly && (
        <Alert variant="info">
          You have read-only access. Contact your administrator for import permissions.
        </Alert>
      )}

      {/* Block Number Selection */}
      <Card className="p-6 bg-slate-800/50 border-slate-700">
        <h3 className="text-lg font-semibold text-white mb-4">Block Settings</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label
              htmlFor="blockNumber"
              className="block text-sm font-medium text-slate-300 mb-2"
            >
              Block Number
            </label>
            <select
              id="blockNumber"
              value={blockNumber}
              onChange={(e) => setBlockNumber(Number(e.target.value))}
              disabled={isReadOnly}
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
            >
              {Array.from({ length: 13 }, (_, i) => i + 1).map((num) => (
                <option key={num} value={num}>
                  Block {num}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-end">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={includeFmit}
                onChange={(e) => setIncludeFmit(e.target.checked)}
                disabled={isReadOnly}
                className="w-4 h-4 rounded border-slate-600 bg-slate-900 text-blue-500 focus:ring-blue-500 focus:ring-offset-0"
              />
              <span className="text-slate-300">Include FMIT attending schedule</span>
            </label>
          </div>
        </div>
      </Card>

      {/* File Upload */}
      <Card className="p-6 bg-slate-800/50 border-slate-700">
        <h3 className="text-lg font-semibold text-white mb-4">Upload Schedule</h3>

        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          className={`
            border-2 border-dashed rounded-lg p-8 text-center transition-colors
            ${dragActive ? 'border-blue-500 bg-blue-500/10' : 'border-slate-600 hover:border-slate-500'}
            ${error ? 'border-red-500/50 bg-red-500/5' : ''}
            ${isReadOnly ? 'opacity-50 cursor-not-allowed' : ''}
          `}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".xlsx,.xls"
            onChange={handleFileInputChange}
            className="hidden"
            aria-label="Select Excel file"
            disabled={isReadOnly}
          />

          {file ? (
            <div className="space-y-4">
              <div className="flex items-center justify-center gap-3">
                <FileSpreadsheet className="w-10 h-10 text-green-400" />
                <div className="text-left">
                  <p className="font-medium text-white">{file.name}</p>
                  <p className="text-sm text-slate-400">
                    {(file.size / 1024).toFixed(1)} KB
                  </p>
                </div>
                <button
                  onClick={() => {
                    setFile(null);
                    if (fileInputRef.current) {
                      fileInputRef.current.value = '';
                    }
                  }}
                  className="p-1 text-slate-400 hover:text-white transition-colors"
                  aria-label="Remove file"
                  disabled={isReadOnly}
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>
          ) : (
            <>
              <Upload
                className={`w-12 h-12 mx-auto mb-4 ${
                  dragActive ? 'text-blue-400' : 'text-slate-500'
                }`}
              />
              <p className="text-lg font-medium text-slate-200 mb-2">
                Drag and drop your Excel file here
              </p>
              <p className="text-sm text-slate-300 mb-4">or click to browse</p>
              <button
                onClick={() => fileInputRef.current?.click()}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
                disabled={isLoading || isReadOnly}
              >
                Select File
              </button>
              <p className="text-xs text-slate-300 mt-4">
                Supported formats: .xlsx, .xls (max 10MB)
              </p>
            </>
          )}
        </div>

        {/* Error Display */}
        {error && (
          <div className="mt-4 flex items-start gap-2 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400">
            <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <span>{error.message}</span>
          </div>
        )}
      </Card>

      {/* Submit Button */}
      <div className="flex justify-end">
        <Button
          onClick={handleSubmit}
          disabled={!file || isLoading || isReadOnly}
          className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Parsing...
            </>
          ) : (
            <>
              <Upload className="w-5 h-5" />
              Parse Block Schedule
            </>
          )}
        </Button>
      </div>
    </div>
  );
}

// ============================================================================
// Sub-Components: Staged Import Tab
// ============================================================================

interface StagedImportTabProps {
  userTier: RiskTier;
}

function StagedImportTab({ userTier }: StagedImportTabProps) {
  const { toast } = useToast();
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [page, setPage] = useState(1);
  const pageSize = 10;

  const {
    data: batchesData,
    isLoading: isBatchesLoading,
    isError: isBatchesError,
    refetch: refetchBatches,
  } = useImportBatches(page);

  const rollbackMutation = useRollbackBatch();

  const handleRollback = (id: string) => {
    if (userTier < 2) {
      toast.error('Rollback requires elevated permissions');
      return;
    }

    if (
      confirm(
        'Are you sure you want to rollback this import? This will revert all changes made by this batch.'
      )
    ) {
      rollbackMutation.mutate(
        { id },
        {
          onSuccess: () => {
            toast.success('Batch rolled back successfully');
          },
          onError: (err) => {
            toast.error(
              `Rollback failed: ${
                err instanceof Error ? err.message : 'Unknown error'
              }`
            );
          },
        }
      );
    }
  };

  const isReadOnly = userTier < 1;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-xl font-semibold text-white">Staged Imports</h3>
          <p className="text-slate-400 text-sm">
            Upload schedules, people, and absences. Review staged changes before applying.
          </p>
        </div>
        <Button
          onClick={() => setIsUploadModalOpen(true)}
          disabled={isReadOnly}
          className="bg-blue-600 hover:bg-blue-500 text-white"
        >
          <Upload className="w-4 h-4 mr-2" />
          New Import
        </Button>
      </div>

      {isReadOnly && (
        <Alert variant="info">
          You have read-only access. Contact your administrator for import permissions.
        </Alert>
      )}

      {isBatchesError && (
        <Alert variant="error" title="Error loading history">
          Failed to load import history. Please try refreshing the page.
        </Alert>
      )}

      {/* History Table */}
      <div className="space-y-4">
        <h4 className="text-lg font-medium text-white flex items-center gap-2">
          <FileText className="w-5 h-5 text-slate-500" />
          Import History
        </h4>

        {batchesData?.items && batchesData.items.length === 0 && !isBatchesLoading ? (
          <div className="flex flex-col items-center justify-center h-64 border border-dashed border-slate-700 rounded-xl bg-slate-900/50">
            <FileText className="w-12 h-12 text-slate-600 mb-4" />
            <h3 className="text-lg font-medium text-slate-300">No Import History</h3>
            <p className="text-slate-300">Upload a schedule to get started</p>
          </div>
        ) : (
          <ImportHistoryTable
            batches={batchesData?.items || []}
            isLoading={isBatchesLoading}
            onRollback={handleRollback}
          />
        )}

        {/* Pagination */}
        {batchesData && batchesData.total > pageSize && (
          <div className="flex justify-end gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1 || isBatchesLoading}
            >
              Previous
            </Button>
            <span className="flex items-center text-sm text-slate-300">
              Page {page}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => p + 1)}
              disabled={!batchesData.hasNext || isBatchesLoading}
            >
              Next
            </Button>
          </div>
        )}
      </div>

      <BulkImportModal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        onSuccess={() => {
          setIsUploadModalOpen(false);
          refetchBatches();
          toast.success('Import staged successfully');
        }}
      />
    </div>
  );
}

// ============================================================================
// Sub-Components: Export Tab
// ============================================================================

interface ExportTabProps {
  userTier: RiskTier;
}

function ExportTab({ userTier: _userTier }: ExportTabProps) {
  const [exportType, setExportType] = useState<'schedules' | 'people' | 'assignments'>('schedules');

  // Mock data - in production, this would come from API queries
  const exportData: Record<string, unknown>[] = [];
  const columns = useMemo(() => {
    switch (exportType) {
      case 'schedules':
        return SCHEDULE_EXPORT_COLUMNS;
      case 'people':
        return PEOPLE_EXPORT_COLUMNS;
      case 'assignments':
        return ASSIGNMENT_EXPORT_COLUMNS;
      default:
        return [];
    }
  }, [exportType]);

  return (
    <div className="space-y-6">
      {/* Export Type Selection */}
      <Card className="p-6 bg-slate-800/50 border-slate-700">
        <h3 className="text-lg font-semibold text-white mb-4">Select Data to Export</h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={() => setExportType('schedules')}
            className={`p-4 rounded-lg border-2 transition-colors text-left ${
              exportType === 'schedules'
                ? 'border-blue-500 bg-blue-500/10'
                : 'border-slate-700 hover:border-slate-600'
            }`}
          >
            <Calendar className={`w-6 h-6 mb-2 ${exportType === 'schedules' ? 'text-blue-400' : 'text-slate-400'}`} />
            <p className="font-medium text-white">Schedules</p>
            <p className="text-sm text-slate-400">Export full schedule data</p>
          </button>

          <button
            onClick={() => setExportType('people')}
            className={`p-4 rounded-lg border-2 transition-colors text-left ${
              exportType === 'people'
                ? 'border-blue-500 bg-blue-500/10'
                : 'border-slate-700 hover:border-slate-600'
            }`}
          >
            <Users className={`w-6 h-6 mb-2 ${exportType === 'people' ? 'text-blue-400' : 'text-slate-400'}`} />
            <p className="font-medium text-white">People</p>
            <p className="text-sm text-slate-400">Export residents and faculty</p>
          </button>

          <button
            onClick={() => setExportType('assignments')}
            className={`p-4 rounded-lg border-2 transition-colors text-left ${
              exportType === 'assignments'
                ? 'border-blue-500 bg-blue-500/10'
                : 'border-slate-700 hover:border-slate-600'
            }`}
          >
            <FileText className={`w-6 h-6 mb-2 ${exportType === 'assignments' ? 'text-blue-400' : 'text-slate-400'}`} />
            <p className="font-medium text-white">Assignments</p>
            <p className="text-sm text-slate-400">Export assignment records</p>
          </button>
        </div>
      </Card>

      {/* Export Panel */}
      <Card className="p-6 bg-slate-800/50 border-slate-700">
        <h3 className="text-lg font-semibold text-white mb-4">Export Options</h3>
        <ExportPanel
          data={exportData}
          columns={columns}
          filename={`${exportType}-export`}
          variant="panel"
          title={`Export ${exportType.charAt(0).toUpperCase() + exportType.slice(1)}`}
          subtitle={`Download ${exportType} data in your preferred format`}
        />
      </Card>

      {/* Info Box */}
      <Card className="p-4 bg-slate-800/30 border-slate-700">
        <h4 className="font-medium text-slate-200 mb-2">About Exports</h4>
        <ul className="text-sm text-slate-300 space-y-1">
          <li>- Exports include all visible data based on your permissions</li>
          <li>- Choose from CSV, Excel, JSON, or PDF formats</li>
          <li>- Large exports may take a moment to generate</li>
          <li>- Date formats follow ISO 8601 standard (YYYY-MM-DD)</li>
        </ul>
      </Card>
    </div>
  );
}

// ============================================================================
// Main Hub Component
// ============================================================================

export default function ImportExportHub() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<HubTab>('staged');

  // Determine user's permission tier based on their roles
  const userRoles = useMemo(() => {
    if (!user) return [];
    // Handle both array and string role formats
    return Array.isArray(user.role) ? user.role : [user.role];
  }, [user]);

  const userTier = useRiskTierFromRoles(userRoles);

  // Get the current tab's risk tier (based on what user can do)
  const currentRiskTier = getMaxTierForTab(activeTab, userTier);

  // Filter tabs based on user permissions (everyone can see all tabs, but actions are gated)
  const availableTabs = TAB_CONFIG;

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
        {/* Risk Bar - shows current permission level for this page */}
        <RiskBar
          tier={currentRiskTier}
          tooltip={
            currentRiskTier === 0
              ? 'Export-only access. You can download data but cannot import.'
              : currentRiskTier === 1
              ? 'You can import data which will be staged for review.'
              : 'Full access including rollback operations.'
          }
        />

        {/* Header */}
        <header className="border-b border-slate-700/50 bg-slate-900/80 backdrop-blur-sm">
          <div className="max-w-7xl mx-auto px-4 py-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-gradient-to-br from-blue-500 to-cyan-600 rounded-xl">
                <FileSpreadsheet className="w-8 h-8 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">Import / Export Hub</h1>
                <p className="text-slate-400">
                  Manage schedule imports, block schedules, FMIT data, and exports
                </p>
              </div>
            </div>
          </div>
        </header>

        {/* Tab Navigation */}
        <div className="border-b border-slate-700/50 bg-slate-900/50">
          <div className="max-w-7xl mx-auto px-4">
            <nav className="flex gap-1" role="tablist" aria-label="Import/Export sections">
              {availableTabs.map((tab) => {
                const isActive = activeTab === tab.id;
                const tabTier = getMaxTierForTab(tab.id, userTier);

                return (
                  <button
                    key={tab.id}
                    role="tab"
                    aria-selected={isActive}
                    aria-controls={`panel-${tab.id}`}
                    onClick={() => setActiveTab(tab.id)}
                    className={`
                      flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors
                      ${isActive
                        ? 'border-blue-500 text-blue-400 bg-blue-500/5'
                        : 'border-transparent text-slate-400 hover:text-white hover:bg-slate-800/50'
                      }
                    `}
                  >
                    {tab.icon}
                    <span>{tab.label}</span>
                    {/* Show tier indicator for import tabs */}
                    {tab.tier > 0 && (
                      <span
                        className={`text-xs px-1.5 py-0.5 rounded ${
                          tabTier >= tab.tier
                            ? 'bg-amber-500/20 text-amber-400'
                            : 'bg-slate-700 text-slate-500'
                        }`}
                      >
                        {tabTier >= tab.tier ? 'Write' : 'View'}
                      </span>
                    )}
                  </button>
                );
              })}
            </nav>
          </div>
        </div>

        {/* Tab Content */}
        <main className="max-w-7xl mx-auto px-4 py-8">
          <div
            role="tabpanel"
            id={`panel-${activeTab}`}
            aria-labelledby={activeTab}
          >
            {activeTab === 'staged' && <StagedImportTab userTier={userTier} />}
            {activeTab === 'block' && <BlockImportTab userTier={userTier} />}
            {activeTab === 'fmit' && <FmitImportTab userTier={userTier} />}
            {activeTab === 'export' && <ExportTab userTier={userTier} />}
          </div>
        </main>
      </div>
    </ProtectedRoute>
  );
}
