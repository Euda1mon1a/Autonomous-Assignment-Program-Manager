'use client';

/**
 * Block Schedule Import Page
 *
 * Two-panel interface for importing TRIPLER-format block schedules:
 * - Left: Source spreadsheet view (xlsx verbatim)
 * - Right: Extracted constraints (rotations, absences, FMIT)
 */

import { useState, useCallback } from 'react';
import { Upload, FileSpreadsheet, CheckCircle2, AlertTriangle, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Alert } from '@/components/ui/Alert';
import { useToast } from '@/contexts/ToastContext';
import Link from 'next/link';

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

export default function BlockImportPage() {
  const { toast } = useToast();
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [parseResult, setParseResult] = useState<ParseResult | null>(null);
  const [, setRawData] = useState<string[][]>([]);
  const [isImporting, setIsImporting] = useState(false);
  const [importComplete, setImportComplete] = useState(false);

  const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setParseResult(null);
      setRawData([]);
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
      setRawData(data.rawData || []);
      toast.success(`Parsed ${data.parsed.assignments.length} assignments`);
    } catch (error) {
      toast.error(`Upload failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsUploading(false);
    }
  }, [file, toast]);

  const handleImport = useCallback(async () => {
    if (!parseResult) return;

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
  }, [parseResult, toast]);

  return (
    <div className="container mx-auto py-8 px-4 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Block Schedule Import</h1>
          <p className="text-slate-300">
            Upload the TRIPLER block schedule xlsx to extract rotations, absences, and FMIT assignments.
          </p>
        </div>
      </div>

      {/* Upload Section */}
      <Card className="p-6 bg-slate-800 border-slate-700">
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <label className="block">
              <span className="sr-only">Choose xlsx file</span>
              <input
                type="file"
                accept=".xlsx,.xls"
                onChange={handleFileChange}
                className="block w-full text-sm text-slate-300
                  file:mr-4 file:py-2 file:px-4
                  file:rounded-md file:border-0
                  file:text-sm file:font-semibold
                  file:bg-blue-600 file:text-white
                  hover:file:bg-blue-500
                  cursor-pointer"
              />
            </label>
          </div>
          <Button
            onClick={handleUpload}
            disabled={!file || isUploading}
            className="bg-blue-600 hover:bg-blue-500"
          >
            {isUploading ? (
              <>Parsing...</>
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
            <h2 className="text-xl font-semibold text-white mb-4">Source Data</h2>
            <div className="overflow-x-auto max-h-[500px] overflow-y-auto">
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
            <h2 className="text-xl font-semibold text-white mb-4">Extracted Constraints</h2>

            {/* Rotations Summary */}
            <div className="mb-6">
              <h3 className="text-lg font-medium text-blue-400 mb-2">
                Rotations ({parseResult.assignments.length})
              </h3>
              <div className="space-y-1 max-h-40 overflow-y-auto">
                {parseResult.assignments.map((a, idx) => (
                  <div key={idx} className="flex items-center text-sm">
                    <CheckCircle2 className="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
                    <span className="text-slate-300">{a.name}</span>
                    <ArrowRight className="w-3 h-3 mx-2 text-slate-500" />
                    <span className="text-white font-medium">{a.rotation}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Absences Summary */}
            <div className="mb-6">
              <h3 className="text-lg font-medium text-amber-400 mb-2">
                Absences ({parseResult.absences.length})
              </h3>
              {parseResult.absences.length > 0 ? (
                <div className="space-y-1 max-h-32 overflow-y-auto">
                  {parseResult.absences.map((abs, idx) => (
                    <div key={idx} className="flex items-center text-sm">
                      <AlertTriangle className="w-4 h-4 text-amber-500 mr-2 flex-shrink-0" />
                      <span className="text-slate-300">{abs.name}:</span>
                      <span className="text-white ml-2">{abs.dates.join(', ')}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-slate-400">No absences detected in file</p>
              )}
            </div>

            {/* FMIT Summary */}
            <div className="mb-6">
              <h3 className="text-lg font-medium text-purple-400 mb-2">
                FMIT Weeks ({parseResult.fmitWeeks.length})
              </h3>
              {parseResult.fmitWeeks.length > 0 ? (
                <div className="space-y-1 max-h-32 overflow-y-auto">
                  {parseResult.fmitWeeks.map((fmit, idx) => (
                    <div key={idx} className="text-sm text-slate-300">
                      {fmit.name}: {fmit.dates.join(', ')}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-slate-400">No FMIT weeks detected</p>
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
                  disabled={isImporting}
                  className="w-full bg-green-600 hover:bg-green-500"
                >
                  {isImporting ? 'Importing...' : 'Import to Database'}
                </Button>
              ) : (
                <div className="space-y-3">
                  <Alert variant="success">
                    <CheckCircle2 className="w-4 h-4 inline mr-2" />
                    Import complete! Constraints are now in the database.
                  </Alert>
                  <Link href="/admin/scheduling">
                    <Button type="button" onClick={() => {}} className="w-full bg-blue-600 hover:bg-blue-500">
                      Go to Scheduling <ArrowRight className="w-4 h-4 ml-2" />
                    </Button>
                  </Link>
                </div>
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
            {' • '}
            {parseResult.assignments.length} residents
            {' • '}
            {parseResult.absences.length} absence periods
            {' • '}
            {parseResult.fmitWeeks.length} FMIT assignments
          </p>
        </Card>
      )}
    </div>
  );
}
