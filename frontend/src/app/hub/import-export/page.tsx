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
import { Abbr } from '@/components/ui/Abbr';
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
import { useExportData, type ExportDataType, type ExportFilters } from '@/hooks/useExportData';
import { useBlockRanges } from '@/hooks';
import { formatLocalDate } from '@/lib/date-utils';
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
    description: 'FMIT (Family Medicine Inpatient Team) attending schedules from Excel',
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
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Upload TRIPLER Block Schedule</h3>
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <label className="block">
              <span className="sr-only">Choose xlsx file</span>
              <input
                type="file"
                accept=".xlsx,.xls"
                onChange={handleFileChange}
                disabled={isReadOnly}
                className="block w-full text-sm text-gray-700
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
          <p className="mt-2 text-sm text-gray-500">
            <FileSpreadsheet className="w-4 h-4 inline mr-1" />
            {file.name}
          </p>
        )}
      </Card>

      {/* Two-Panel View */}
      {parseResult && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Panel: Source Data */}
          <Card className="p-6 border-gray-200">
            <h3 className="text-xl font-semibold text-gray-900 mb-4">Source Data</h3>
            <div className="overflow-x-auto max-h-[400px] overflow-y-auto">
              <table className="min-w-full text-sm">
                <thead className="bg-gray-100 sticky top-0">
                  <tr>
                    <th className="px-3 py-2 text-left text-gray-600">Rotation</th>
                    <th className="px-3 py-2 text-left text-gray-600">Role</th>
                    <th className="px-3 py-2 text-left text-gray-600"><Abbr>PGY</Abbr></th>
                    <th className="px-3 py-2 text-left text-gray-600">Name</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {parseResult.assignments.map((a, idx) => (
                    <tr key={`${a.name}-${a.rotation}-${idx}`} className="hover:bg-gray-100/50">
                      <td className="px-3 py-2 text-gray-900 font-medium">{a.rotation}</td>
                      <td className="px-3 py-2 text-gray-600">{a.role}</td>
                      <td className="px-3 py-2 text-gray-600">{a.pgyLevel}</td>
                      <td className="px-3 py-2 text-gray-600">{a.name}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          {/* Right Panel: Extracted Constraints */}
          <Card className="p-6 border-gray-200">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-semibold text-gray-900">Extracted Constraints</h3>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleReset}
                className="text-gray-500"
              >
                <RefreshCw className="w-4 h-4 mr-1" />
                Reset
              </Button>
            </div>

            {/* Rotations Summary */}
            <div className="mb-6">
              <h4 className="text-lg font-medium text-blue-600 mb-2">
                Rotations ({parseResult.assignments.length})
              </h4>
              <div className="space-y-1 max-h-32 overflow-y-auto">
                {parseResult.assignments.slice(0, 10).map((a) => (
                  <div key={`${a.name}-${a.rotation}`} className="flex items-center text-sm">
                    <CheckCircle2 className="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
                    <span className="text-gray-600">{a.name}</span>
                    <ArrowRight className="w-3 h-3 mx-2 text-gray-400" />
                    <span className="text-gray-900 font-medium">{a.rotation}</span>
                  </div>
                ))}
                {parseResult.assignments.length > 10 && (
                  <p className="text-sm text-gray-500">
                    ...and {parseResult.assignments.length - 10} more
                  </p>
                )}
              </div>
            </div>

            {/* Absences Summary */}
            <div className="mb-6">
              <h4 className="text-lg font-medium text-amber-700 mb-2">
                Absences ({parseResult.absences.length})
              </h4>
              {parseResult.absences.length > 0 ? (
                <div className="space-y-1 max-h-24 overflow-y-auto">
                  {parseResult.absences.slice(0, 5).map((abs) => (
                    <div key={`${abs.name}-${abs.dates[0]}`} className="flex items-center text-sm">
                      <AlertTriangle className="w-4 h-4 text-amber-500 mr-2 flex-shrink-0" />
                      <span className="text-gray-600">{abs.name}:</span>
                      <span className="text-gray-900 ml-2">{abs.dates.join(', ')}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-500">No absences detected</p>
              )}
            </div>

            {/* Warnings */}
            {parseResult.warnings.length > 0 && (
              <Alert variant="warning" className="mb-4">
                <ul className="list-disc list-inside text-sm">
                  {parseResult.warnings.map((w) => (
                    <li key={w}>{w}</li>
                  ))}
                </ul>
              </Alert>
            )}

            {/* Import Button */}
            <div className="pt-4 border-t border-gray-200">
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
        <Card className="p-4 border-gray-200">
          <p className="text-sm text-gray-600">
            <span className="font-medium text-gray-900">Block {parseResult.blockNumber}</span>
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
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between px-4 py-3 bg-gray-50 hover:bg-gray-100 transition-colors"
      >
        <div className="flex items-center gap-2">
          {isExpanded ? (
            <ChevronDown className="w-4 h-4 text-gray-500" />
          ) : (
            <ChevronRight className="w-4 h-4 text-gray-500" />
          )}
          <span className="font-medium text-gray-900">{title}</span>
          <span className="text-sm text-gray-500">({residents.length} residents)</span>
        </div>
      </button>
      {isExpanded && (
        <div className="p-4 space-y-2">
          {residents.map((resident, idx) => (
            <div
              key={`${resident.name}-${idx}`}
              className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded"
            >
              <div className="flex items-center gap-3">
                <span className="text-gray-900">{resident.name}</span>
                <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded">
                  {resident.role}
                </span>
              </div>
              {resident.confidence < 1.0 && (
                <span className="text-xs text-amber-700 flex items-center gap-1">
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
      <div className="text-center py-8 text-gray-500">
        No FMIT schedule found in this block
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-gray-200">
            <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Week</th>
            <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Faculty</th>
            <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Date Range</th>
            <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Holiday Call</th>
          </tr>
        </thead>
        <tbody>
          {schedule.map((week) => (
            <tr
              key={`${week.blockNumber}-${week.weekNumber}`}
              className="border-b border-gray-100 hover:bg-gray-50"
            >
              <td className="px-4 py-3 text-gray-900">Week {week.weekNumber}</td>
              <td className="px-4 py-3">
                <span className="font-medium text-gray-900">
                  {week.facultyName || <span className="text-gray-600 italic">Unassigned</span>}
                </span>
              </td>
              <td className="px-4 py-3 text-gray-600">
                {week.startDate && week.endDate
                  ? `${week.startDate} - ${week.endDate}`
                  : <span className="text-gray-600">-</span>}
              </td>
              <td className="px-4 py-3">
                {week.isHolidayCall ? (
                  <span className="text-xs px-2 py-1 bg-amber-100 text-amber-700 rounded">
                    Holiday
                  </span>
                ) : (
                  <span className="text-gray-600">-</span>
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
              <div className="flex items-center gap-2 text-green-600">
                <CheckCircle2 className="w-5 h-5" />
                <span className="font-medium">Parse Successful</span>
              </div>
            ) : (
              <div className="flex items-center gap-2 text-red-700">
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
          <Card className="p-4 border-gray-200">
            <div className="text-2xl font-bold text-gray-900">{data.blockNumber}</div>
            <div className="text-sm text-gray-500">Block Number</div>
          </Card>
          <Card className="p-4 border-gray-200">
            <div className="text-2xl font-bold text-gray-900">{data.totalResidents}</div>
            <div className="text-sm text-gray-500">Residents</div>
          </Card>
          <Card className="p-4 border-gray-200">
            <div className="text-2xl font-bold text-gray-900">{data.fmitSchedule.length}</div>
            <div className="text-sm text-gray-500"><Abbr>FMIT</Abbr> Weeks</div>
          </Card>
          <Card className="p-4 border-gray-200">
            <div className="text-2xl font-bold text-gray-900">{data.totalAssignments}</div>
            <div className="text-sm text-gray-500">Assignments</div>
          </Card>
        </div>

        {/* Block Date Range */}
        {(data.startDate || data.endDate) && (
          <div className="flex items-center gap-2 text-gray-600">
            <Calendar className="w-4 h-4 text-gray-500" />
            <span>
              Block {data.blockNumber}: {data.startDate || '?'} - {data.endDate || '?'}
            </span>
          </div>
        )}

        {/* Tabs */}
        <div className="border-b border-gray-200">
          <div className="flex gap-1">
            <button
              onClick={() => setActiveResultTab('fmit')}
              className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                activeResultTab === 'fmit'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-900'
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
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-900'
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
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-900'
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
            <Card className="border-gray-200 overflow-hidden">
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
                <div className="text-center py-8 text-gray-500">
                  No residents found in this block
                </div>
              )}
            </div>
          )}

          {activeResultTab === 'warnings' && (
            <div className="space-y-4">
              {data.errors.length > 0 && (
                <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                  <h4 className="font-medium text-red-700 mb-2 flex items-center gap-2">
                    <AlertCircle className="w-4 h-4" />
                    Errors ({data.errors.length})
                  </h4>
                  <ul className="space-y-1 text-sm text-red-600">
                    {data.errors.map((err) => (
                      <li key={err}>{err}</li>
                    ))}
                  </ul>
                </div>
              )}
              {data.warnings.length > 0 && (
                <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
                  <h4 className="font-medium text-amber-700 mb-2 flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4" />
                    Warnings ({data.warnings.length})
                  </h4>
                  <ul className="space-y-1 text-sm text-amber-600">
                    {data.warnings.map((warning) => (
                      <li key={warning}>{warning}</li>
                    ))}
                  </ul>
                </div>
              )}
              {data.errors.length === 0 && data.warnings.length === 0 && (
                <div className="text-center py-8 text-green-600 flex flex-col items-center gap-2">
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
      <Card className="p-6 border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Block Settings</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label
              htmlFor="blockNumber"
              className="block text-sm font-medium text-gray-600 mb-2"
            >
              Block Number
            </label>
            <select
              id="blockNumber"
              value={blockNumber}
              onChange={(e) => setBlockNumber(Number(e.target.value))}
              disabled={isReadOnly}
              className="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
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
                className="w-4 h-4 rounded border-gray-300 bg-white text-blue-500 focus:ring-blue-500 focus:ring-offset-0"
              />
              <span className="text-gray-600">Include <Abbr>FMIT</Abbr> attending schedule</span>
            </label>
          </div>
        </div>
      </Card>

      {/* File Upload */}
      <Card className="p-6 border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Upload Schedule</h3>

        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          className={`
            border-2 border-dashed rounded-lg p-8 text-center transition-colors
            ${dragActive ? 'border-blue-500 bg-blue-500/10' : 'border-gray-300 hover:border-gray-400'}
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
                <FileSpreadsheet className="w-10 h-10 text-green-600" />
                <div className="text-left">
                  <p className="font-medium text-gray-900">{file.name}</p>
                  <p className="text-sm text-gray-500">
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
                  className="p-1 text-gray-500 hover:text-gray-900 transition-colors"
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
                  dragActive ? 'text-blue-600' : 'text-gray-400'
                }`}
              />
              <p className="text-lg font-medium text-gray-700 mb-2">
                Drag and drop your Excel file here
              </p>
              <p className="text-sm text-gray-600 mb-4">or click to browse</p>
              <button
                onClick={() => fileInputRef.current?.click()}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
                disabled={isLoading || isReadOnly}
              >
                Select File
              </button>
              <p className="text-xs text-gray-600 mt-4">
                Supported formats: .xlsx, .xls (max 10MB)
              </p>
            </>
          )}
        </div>

        {/* Error Display */}
        {error && (
          <div className="mt-4 flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700">
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
          <h3 className="text-xl font-semibold text-gray-900">Staged Imports</h3>
          <p className="text-gray-500 text-sm">
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
        <h4 className="text-lg font-medium text-gray-900 flex items-center gap-2">
          <FileText className="w-5 h-5 text-gray-400" />
          Import History
        </h4>

        {batchesData?.items && batchesData.items.length === 0 && !isBatchesLoading ? (
          <div className="flex flex-col items-center justify-center h-64 border border-dashed border-gray-300 rounded-xl bg-gray-50">
            <FileText className="w-12 h-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-700">No Import History</h3>
            <p className="text-gray-500">Upload a schedule to get started</p>
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
            <span className="flex items-center text-sm text-gray-600">
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
  const [exportType, setExportType] = useState<ExportDataType>('people');
  const [startDate, setStartDate] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() - 90);
    return formatLocalDate(d);
  });
  const [endDate, setEndDate] = useState(() => formatLocalDate(new Date()));
  const [includeQaSheet, setIncludeQaSheet] = useState(true);
  const [includeOverrides, setIncludeOverrides] = useState(true);

  // Block ranges for the block quick-selector
  const { data: blockRanges } = useBlockRanges();

  const availableAYs = useMemo(() => {
    if (!blockRanges?.length) return [];
    return [...new Set(blockRanges.map((r) => r.academicYear))].sort();
  }, [blockRanges]);

  // Determine current AY from today's date (July 1 = new AY)
  const defaultAY = useMemo(() => {
    const now = new Date();
    const month = now.getMonth() + 1;
    return month < 7 ? now.getFullYear() - 1 : now.getFullYear();
  }, []);

  const [selectedAY, setSelectedAY] = useState(defaultAY);

  const blocksForAY = useMemo(() => {
    if (!blockRanges?.length) return [];
    return blockRanges
      .filter((r) => r.academicYear === selectedAY)
      .sort((a, b) => a.blockNumber - b.blockNumber);
  }, [blockRanges, selectedAY]);

  const handleBlockQuickSelect = useCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value;
    if (!value || !blockRanges?.length) return;
    const [ayStr, blockStr] = value.split(':');
    const range = blockRanges.find(
      (r) => r.academicYear === Number(ayStr) && r.blockNumber === Number(blockStr)
    );
    if (range) {
      setStartDate(range.startDate);
      setEndDate(range.endDate);
    }
  }, [blockRanges]);

  // Build filters — schedule endpoint requires dates
  const filters: ExportFilters | undefined =
    exportType === 'schedules' ? { startDate, endDate } : undefined;

  const { data: exportData = [], isLoading, isError, error } = useExportData(exportType, filters);

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
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Select Data to Export</h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={() => setExportType('schedules')}
            className={`p-4 rounded-lg border-2 transition-colors text-left ${
              exportType === 'schedules'
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <Calendar className={`w-6 h-6 mb-2 ${exportType === 'schedules' ? 'text-blue-600' : 'text-gray-400'}`} />
            <p className="font-medium text-gray-900">Schedules</p>
            <p className="text-sm text-gray-500">Export full schedule data</p>
          </button>

          <button
            onClick={() => setExportType('people')}
            className={`p-4 rounded-lg border-2 transition-colors text-left ${
              exportType === 'people'
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <Users className={`w-6 h-6 mb-2 ${exportType === 'people' ? 'text-blue-600' : 'text-gray-400'}`} />
            <p className="font-medium text-gray-900">People</p>
            <p className="text-sm text-gray-500">Export residents and faculty</p>
          </button>

          <button
            onClick={() => setExportType('assignments')}
            className={`p-4 rounded-lg border-2 transition-colors text-left ${
              exportType === 'assignments'
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <FileText className={`w-6 h-6 mb-2 ${exportType === 'assignments' ? 'text-blue-600' : 'text-gray-400'}`} />
            <p className="font-medium text-gray-900">Assignments</p>
            <p className="text-sm text-gray-500">Export assignment records</p>
          </button>
        </div>
      </Card>

      {/* Date Range (schedules only) */}
      {exportType === 'schedules' && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Date Range</h3>

          {/* Block quick-selector */}
          {blocksForAY.length > 0 && (
            <div className="flex flex-wrap items-end gap-4 mb-4 pb-4 border-b border-gray-200">
              <label className="flex flex-col gap-1">
                <span className="text-sm text-gray-500">Academic Year</span>
                <select
                  value={selectedAY}
                  onChange={(e) => setSelectedAY(Number(e.target.value))}
                  className="px-3 py-2 bg-white border border-gray-300 rounded-lg text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {availableAYs.map((ay) => (
                    <option key={ay} value={ay}>
                      AY {ay}-{String(ay + 1).slice(2)}
                    </option>
                  ))}
                </select>
              </label>
              <label className="flex flex-col gap-1">
                <span className="text-sm text-gray-500">Quick Select Block</span>
                <select
                  onChange={handleBlockQuickSelect}
                  defaultValue=""
                  className="px-3 py-2 bg-white border border-gray-300 rounded-lg text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="" disabled>
                    Select a block...
                  </option>
                  {blocksForAY.map((range) => (
                    <option
                      key={`${range.academicYear}:${range.blockNumber}`}
                      value={`${range.academicYear}:${range.blockNumber}`}
                    >
                      Block {range.blockNumber} ({range.startDate} to {range.endDate})
                    </option>
                  ))}
                </select>
              </label>
            </div>
          )}

          <div className="flex flex-wrap gap-4">
            <label className="flex flex-col gap-1">
              <span className="text-sm text-gray-500">Start Date</span>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="px-3 py-2 bg-white border border-gray-300 rounded-lg text-gray-900"
              />
            </label>
            <label className="flex flex-col gap-1">
              <span className="text-sm text-gray-500">End Date</span>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="px-3 py-2 bg-white border border-gray-300 rounded-lg text-gray-900"
              />
            </label>
          </div>
        </Card>
      )}

      {/* Excel Export Options (schedules only) */}
      {exportType === 'schedules' && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Excel Export Options</h3>
          <p className="text-sm text-gray-500 mb-4">
            These options apply when exporting to Excel (.xlsx) format via the server-side export.
          </p>
          <div className="space-y-3">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={includeQaSheet}
                onChange={(e) => setIncludeQaSheet(e.target.checked)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <div>
                <span className="text-sm font-medium text-gray-900">Include QA Sheet</span>
                <p className="text-xs text-gray-500">Adds a validation/QA worksheet to the exported workbook</p>
              </div>
            </label>
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={includeOverrides}
                onChange={(e) => setIncludeOverrides(e.target.checked)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <div>
                <span className="text-sm font-medium text-gray-900">Include Overrides</span>
                <p className="text-xs text-gray-500">Include override/swap assignments in export data</p>
              </div>
            </label>
          </div>
        </Card>
      )}

      {/* Loading / Error States */}
      {isLoading && (
        <div className="flex items-center gap-2 text-gray-500">
          <Loader2 className="w-4 h-4 animate-spin" />
          <span>Loading export data...</span>
        </div>
      )}
      {isError && (
        <Alert variant="warning">
          {error?.message || 'Failed to load export data'}
        </Alert>
      )}

      {/* Primary Export Action: Server-side XLSX (schedules only) */}
      {exportType === 'schedules' && (
        <Card className="p-6 border-2 border-blue-200 bg-blue-50/30">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Export Block Schedule</h3>
          <p className="text-sm text-gray-500 mb-4">
            Downloads the formatted schedule workbook with color-coded rotations, AM/PM grid, and coverage summary.
          </p>
          <a
            href={`${process.env.NEXT_PUBLIC_API_URL || '/api/v1'}/export/schedule/xlsx?start_date=${startDate}&end_date=${endDate}&include_qa_sheet=${includeQaSheet}&include_overrides=${includeOverrides}`}
            download
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium"
          >
            <Download className="w-5 h-5" />
            Export Schedule (.xlsx)
          </a>
        </Card>
      )}

      {/* Collapsible: Raw Data Export */}
      <details className="group">
        <summary className="flex items-center gap-2 cursor-pointer text-sm text-gray-500 hover:text-gray-700 py-2 select-none">
          <ChevronRight className="w-4 h-4 transition-transform group-open:rotate-90" />
          Advanced: Raw data export (CSV, JSON, Excel)
        </summary>
        <div className="mt-2 space-y-4">
          <Card className="p-6">
            <ExportPanel
              data={exportData}
              columns={columns}
              filename={`${exportType}-export`}
              variant="panel"
              title={`Export ${exportType.charAt(0).toUpperCase() + exportType.slice(1)}`}
              subtitle={`Download ${exportType} data in your preferred format`}
            />
          </Card>
          <p className="text-xs text-gray-400 px-1">
            Raw data exports contain unformatted records. Use the button above for the formatted schedule workbook.
          </p>
        </div>
      </details>
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
      <div className="min-h-screen bg-gray-50">
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
        <header className="border-b border-gray-200 bg-white shadow-sm">
          <div className="max-w-7xl mx-auto px-4 py-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-gradient-to-br from-blue-500 to-cyan-600 rounded-xl">
                <FileSpreadsheet className="w-8 h-8 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Import / Export Hub</h1>
                <p className="text-gray-600">
                  Manage schedule imports, block schedules, FMIT data, and exports
                </p>
              </div>
            </div>
          </div>
        </header>

        {/* Tab Navigation */}
        <div className="border-b border-gray-200 bg-white">
          <div className="max-w-7xl mx-auto px-4">
            <nav className="flex gap-1 overflow-x-auto" role="tablist" aria-label="Import/Export sections">
              {availableTabs.map((tab) => {
                const isActive = activeTab === tab.id;
                const tabTier = getMaxTierForTab(tab.id, userTier);

                return (
                  <button
                    key={tab.id}
                    data-testid={`hub-tab-${tab.id}`}
                    role="tab"
                    aria-selected={isActive}
                    aria-controls={`panel-${tab.id}`}
                    onClick={() => setActiveTab(tab.id)}
                    className={`
                      flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors
                      ${isActive
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
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
                            ? 'bg-amber-100 text-amber-700'
                            : 'bg-gray-100 text-gray-500'
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
