'use client';

/**
 * FMIT Block Schedule Import Page
 *
 * Admin interface for importing FMIT attending schedules from Excel files.
 * Parses block schedules and displays:
 * - Resident roster by template (R1, R2, R3)
 * - FMIT weekly faculty assignments
 * - Daily assignments with AM/PM slots
 * - Parsing warnings for fuzzy name matches
 */

import { useState, useCallback, useRef } from 'react';
import {
  Upload,
  FileSpreadsheet,
  AlertCircle,
  AlertTriangle,
  CheckCircle,
  Users,
  Calendar,
  ChevronDown,
  ChevronRight,
  X,
  Loader2,
  RefreshCw,
} from 'lucide-react';
import { useFmitImport } from '@/hooks/useFmitImport';
import { useToast } from '@/contexts/ToastContext';
import type {
  BlockParseResponse,
  ResidentRosterItem,
  ParsedFMITWeek,
} from '@/types/fmit-import';

// ============================================================================
// Sub-Components
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
              key={`${week.block_number}-${week.week_number}`}
              className="border-b border-slate-800 hover:bg-slate-800/50"
            >
              <td className="px-4 py-3 text-white">Week {week.week_number}</td>
              <td className="px-4 py-3">
                <span className="font-medium text-white">
                  {week.faculty_name || <span className="text-slate-500 italic">Unassigned</span>}
                </span>
              </td>
              <td className="px-4 py-3 text-slate-300">
                {week.start_date && week.end_date
                  ? `${week.start_date} - ${week.end_date}`
                  : <span className="text-slate-500">-</span>}
              </td>
              <td className="px-4 py-3">
                {week.is_holiday_call ? (
                  <span className="text-xs px-2 py-1 bg-amber-500/20 text-amber-400 rounded">
                    Holiday
                  </span>
                ) : (
                  <span className="text-slate-500">-</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

interface ParseResultsProps {
  data: BlockParseResponse;
  onReset: () => void;
}

function ParseResults({ data, onReset }: ParseResultsProps) {
  const [activeTab, setActiveTab] = useState<'roster' | 'fmit' | 'warnings'>('fmit');

  return (
    <div className="space-y-6">
      {/* Summary Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          {data.success ? (
            <div className="flex items-center gap-2 text-green-400">
              <CheckCircle className="w-5 h-5" />
              <span className="font-medium">Parse Successful</span>
            </div>
          ) : (
            <div className="flex items-center gap-2 text-red-400">
              <AlertCircle className="w-5 h-5" />
              <span className="font-medium">Parse Completed with Errors</span>
            </div>
          )}
        </div>
        <button
          onClick={onReset}
          className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          Import Another
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-4 bg-slate-800/50 border border-slate-700 rounded-lg">
          <div className="text-2xl font-bold text-white">{data.block_number}</div>
          <div className="text-sm text-slate-400">Block Number</div>
        </div>
        <div className="p-4 bg-slate-800/50 border border-slate-700 rounded-lg">
          <div className="text-2xl font-bold text-white">{data.total_residents}</div>
          <div className="text-sm text-slate-400">Residents</div>
        </div>
        <div className="p-4 bg-slate-800/50 border border-slate-700 rounded-lg">
          <div className="text-2xl font-bold text-white">{data.fmit_schedule.length}</div>
          <div className="text-sm text-slate-400">FMIT Weeks</div>
        </div>
        <div className="p-4 bg-slate-800/50 border border-slate-700 rounded-lg">
          <div className="text-2xl font-bold text-white">{data.total_assignments}</div>
          <div className="text-sm text-slate-400">Assignments</div>
        </div>
      </div>

      {/* Block Date Range */}
      {(data.start_date || data.end_date) && (
        <div className="flex items-center gap-2 text-slate-300">
          <Calendar className="w-4 h-4 text-slate-400" />
          <span>
            Block {data.block_number}: {data.start_date || '?'} - {data.end_date || '?'}
          </span>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-slate-700">
        <div className="flex gap-1">
          <button
            onClick={() => setActiveTab('fmit')}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'fmit'
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
            onClick={() => setActiveTab('roster')}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'roster'
                ? 'border-blue-500 text-blue-400'
                : 'border-transparent text-slate-400 hover:text-white'
            }`}
          >
            <div className="flex items-center gap-2">
              <Users className="w-4 h-4" />
              Roster ({data.total_residents})
            </div>
          </button>
          <button
            onClick={() => setActiveTab('warnings')}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'warnings'
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
        {activeTab === 'fmit' && (
          <div className="bg-slate-800/30 border border-slate-700 rounded-lg overflow-hidden">
            <FmitScheduleTable schedule={data.fmit_schedule} />
          </div>
        )}

        {activeTab === 'roster' && (
          <div className="space-y-4">
            {Object.entries(data.residents_by_template).map(([template, residents]) => (
              <RosterSection
                key={template}
                title={template}
                residents={residents}
                defaultExpanded={template === 'R1'}
              />
            ))}
            {Object.keys(data.residents_by_template).length === 0 && (
              <div className="text-center py-8 text-slate-400">
                No residents found in this block
              </div>
            )}
          </div>
        )}

        {activeTab === 'warnings' && (
          <div className="space-y-4">
            {data.errors.length > 0 && (
              <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
                <h4 className="font-medium text-red-400 mb-2 flex items-center gap-2">
                  <AlertCircle className="w-4 h-4" />
                  Errors ({data.errors.length})
                </h4>
                <ul className="space-y-1 text-sm text-red-300">
                  {data.errors.map((error, idx) => (
                    <li key={idx}>{error}</li>
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
                <CheckCircle className="w-8 h-8" />
                <span>No warnings or errors</span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// Main Page Component
// ============================================================================

export default function FmitImportPage() {
  const { toast } = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Form state
  const [file, setFile] = useState<File | null>(null);
  const [blockNumber, setBlockNumber] = useState<number>(1);
  const [includeFmit, setIncludeFmit] = useState(true);
  const [dragActive, setDragActive] = useState(false);

  // Import hook
  const { parseBlock, isLoading, data, error, reset } = useFmitImport({
    onSuccess: (result) => {
      toast.success(
        `Parsed Block ${result.block_number}: ${result.total_residents} residents, ${result.fmit_schedule.length} FMIT weeks`
      );
    },
    onError: (err) => {
      toast.error(`Parse failed: ${err.message}`);
    },
  });

  // Handlers
  const handleFileSelect = useCallback((selectedFile: File) => {
    // Validate file type
    const validExtensions = ['.xlsx', '.xls'];
    const isValidType = validExtensions.some((ext) =>
      selectedFile.name.toLowerCase().endsWith(ext)
    );

    if (!isValidType) {
      toast.error('Please select an Excel file (.xlsx or .xls)');
      return;
    }

    // Validate file size (max 10MB)
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
    if (!file) {
      toast.error('Please select a file first');
      return;
    }

    parseBlock({
      file,
      blockNumber,
      includeFmit,
    });
  }, [file, blockNumber, includeFmit, parseBlock, toast]);

  const handleReset = useCallback(() => {
    reset();
    setFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, [reset]);

  // If we have results, show them
  if (data) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
        <header className="border-b border-slate-700/50 bg-slate-900/80 backdrop-blur-sm sticky top-0 z-50">
          <div className="max-w-5xl mx-auto px-4 py-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-blue-500 to-cyan-600 rounded-lg">
                <FileSpreadsheet className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">FMIT Schedule Import</h1>
                <p className="text-sm text-slate-400">Parse block schedules from Excel</p>
              </div>
            </div>
          </div>
        </header>

        <main className="max-w-5xl mx-auto px-4 py-8">
          <ParseResults data={data} onReset={handleReset} />
        </main>
      </div>
    );
  }

  // Upload form
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <header className="border-b border-slate-700/50 bg-slate-900/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-3xl mx-auto px-4 py-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gradient-to-br from-blue-500 to-cyan-600 rounded-lg">
              <FileSpreadsheet className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">FMIT Schedule Import</h1>
              <p className="text-sm text-slate-400">Parse block schedules from Excel</p>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 py-8">
        <div className="space-y-6">
          {/* Block Number Selection */}
          <div className="p-6 bg-slate-800/50 border border-slate-700 rounded-xl">
            <h2 className="text-lg font-semibold text-white mb-4">Block Settings</h2>

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
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
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
                    className="w-4 h-4 rounded border-slate-600 bg-slate-900 text-blue-500 focus:ring-blue-500 focus:ring-offset-0"
                  />
                  <span className="text-slate-300">Include FMIT attending schedule</span>
                </label>
              </div>
            </div>
          </div>

          {/* File Upload */}
          <div className="p-6 bg-slate-800/50 border border-slate-700 rounded-xl">
            <h2 className="text-lg font-semibold text-white mb-4">Upload Schedule</h2>

            <div
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              className={`
                border-2 border-dashed rounded-lg p-8 text-center transition-colors
                ${dragActive ? 'border-blue-500 bg-blue-500/10' : 'border-slate-600 hover:border-slate-500'}
                ${error ? 'border-red-500/50 bg-red-500/5' : ''}
              `}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".xlsx,.xls"
                onChange={handleFileInputChange}
                className="hidden"
                aria-label="Select Excel file"
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
                  <p className="text-lg font-medium text-slate-300 mb-2">
                    Drag and drop your Excel file here
                  </p>
                  <p className="text-sm text-slate-500 mb-4">or click to browse</p>
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium transition-colors"
                    disabled={isLoading}
                  >
                    Select File
                  </button>
                  <p className="text-xs text-slate-500 mt-4">
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
          </div>

          {/* Submit Button */}
          <div className="flex justify-end">
            <button
              onClick={handleSubmit}
              disabled={!file || isLoading}
              className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white rounded-lg font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed"
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
            </button>
          </div>

          {/* Info Box */}
          <div className="p-4 bg-slate-800/30 border border-slate-700 rounded-lg">
            <h3 className="font-medium text-slate-300 mb-2">About FMIT Import</h3>
            <ul className="text-sm text-slate-400 space-y-1">
              <li>
                - Parses block schedules from Excel files with anchor-based fuzzy-tolerant parsing
              </li>
              <li>- Extracts resident roster grouped by rotation template (R1, R2, R3)</li>
              <li>- Identifies FMIT attending weekly assignments</li>
              <li>- Handles column shifts, merged cells, and name typos with fuzzy matching</li>
            </ul>
          </div>
        </div>
      </main>
    </div>
  );
}
