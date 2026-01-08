"use client";

/**
 * Block Assignment Export Modal.
 *
 * Allows admins to export block assignments in CSV or Excel format
 * with various filter and grouping options.
 */

import { useState, useCallback } from "react";
import { useMutation } from "@tanstack/react-query";
import { Download, FileSpreadsheet, FileText, Loader2 } from "lucide-react";
import { Modal } from "@/components/Modal";
import { exportBlockAssignments, downloadBlob } from "@/api/block-assignment-import";
import type {
  BlockAssignmentExportRequest,
  ExportFormat,
} from "@/types/block-assignment-import";

interface BlockAssignmentExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  /** Default academic year (current if not provided) */
  defaultAcademicYear?: number;
}

/**
 * Calculate current academic year.
 * Academic year starts July 1:
 * - July-December = current calendar year
 * - January-June = previous calendar year
 */
function getCurrentAcademicYear(): number {
  const now = new Date();
  if (now.getMonth() >= 6) {
    return now.getFullYear();
  }
  return now.getFullYear() - 1;
}

export function BlockAssignmentExportModal({
  isOpen,
  onClose,
  defaultAcademicYear,
}: BlockAssignmentExportModalProps) {
  // Form state
  const [academicYear, setAcademicYear] = useState<number>(
    defaultAcademicYear ?? getCurrentAcademicYear()
  );
  const [format, setFormat] = useState<ExportFormat>("csv");
  const [includePgyLevel, setIncludePgyLevel] = useState(true);
  const [includeLeaveStatus, setIncludeLeaveStatus] = useState(false);
  const [blockNumbers, setBlockNumbers] = useState<string>("");

  // Export mutation
  const exportMutation = useMutation({
    mutationFn: async () => {
      const request: BlockAssignmentExportRequest = {
        format,
        academic_year: academicYear,
        include_pgy_level: includePgyLevel,
        include_leave_status: includeLeaveStatus,
      };

      // Parse block numbers if provided
      if (blockNumbers.trim()) {
        const blocks = blockNumbers
          .split(",")
          .map((b) => parseInt(b.trim(), 10))
          .filter((b) => !isNaN(b) && b >= 0 && b <= 13);
        if (blocks.length > 0) {
          request.block_numbers = blocks;
        }
      }

      const blob = (await exportBlockAssignments(request)) as Blob;

      // Generate filename
      const timestamp = new Date().toISOString().split("T")[0];
      const filename = `block_assignments_${academicYear}_${timestamp}.${format}`;

      downloadBlob(blob, filename);
    },
    onSuccess: () => {
      onClose();
    },
  });

  const handleExport = useCallback(() => {
    exportMutation.mutate();
  }, [exportMutation]);

  const handleClose = useCallback(() => {
    if (!exportMutation.isPending) {
      onClose();
    }
  }, [exportMutation.isPending, onClose]);

  // Generate year options (current year +/- 2)
  const currentYear = getCurrentAcademicYear();
  const yearOptions = [
    currentYear - 2,
    currentYear - 1,
    currentYear,
    currentYear + 1,
  ];

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Export Block Assignments"
      maxWidth="max-w-lg"
    >
      <div className="space-y-6">
        {/* Academic Year */}
        <div>
          <label
            htmlFor="academic-year"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Academic Year
          </label>
          <select
            id="academic-year"
            value={academicYear}
            onChange={(e) => setAcademicYear(parseInt(e.target.value, 10))}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            {yearOptions.map((year) => (
              <option key={year} value={year}>
                AY {year}-{year + 1}
              </option>
            ))}
          </select>
        </div>

        {/* Format Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Export Format
          </label>
          <div className="grid grid-cols-2 gap-3">
            <button
              type="button"
              onClick={() => setFormat("csv")}
              className={`flex items-center justify-center gap-2 px-4 py-3 rounded-lg border-2 transition-all ${
                format === "csv"
                  ? "border-blue-500 bg-blue-50 text-blue-700"
                  : "border-gray-200 hover:border-gray-300 text-gray-600"
              }`}
            >
              <FileText className="w-5 h-5" />
              <span className="font-medium">CSV</span>
            </button>
            <button
              type="button"
              onClick={() => setFormat("xlsx")}
              className={`flex items-center justify-center gap-2 px-4 py-3 rounded-lg border-2 transition-all ${
                format === "xlsx"
                  ? "border-green-500 bg-green-50 text-green-700"
                  : "border-gray-200 hover:border-gray-300 text-gray-600"
              }`}
            >
              <FileSpreadsheet className="w-5 h-5" />
              <span className="font-medium">Excel</span>
            </button>
          </div>
          <p className="mt-2 text-xs text-gray-500">
            {format === "xlsx"
              ? "Excel format includes color-coding by rotation type"
              : "CSV is compatible with all spreadsheet applications"}
          </p>
        </div>

        {/* Block Filter */}
        <div>
          <label
            htmlFor="block-numbers"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Block Numbers (optional)
          </label>
          <input
            id="block-numbers"
            type="text"
            value={blockNumbers}
            onChange={(e) => setBlockNumbers(e.target.value)}
            placeholder="e.g., 1, 2, 3 (leave empty for all)"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
          <p className="mt-1 text-xs text-gray-500">
            Comma-separated block numbers (0-13). Leave empty to export all.
          </p>
        </div>

        {/* Options */}
        <div className="space-y-3">
          <label className="block text-sm font-medium text-gray-700">
            Include Columns
          </label>
          <div className="space-y-2">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={includePgyLevel}
                onChange={(e) => setIncludePgyLevel(e.target.checked)}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700">PGY Level</span>
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={includeLeaveStatus}
                onChange={(e) => setIncludeLeaveStatus(e.target.checked)}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700">Leave Status</span>
            </label>
          </div>
        </div>

        {/* Error Message */}
        {exportMutation.isError && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-700">
              {exportMutation.error instanceof Error
                ? exportMutation.error.message
                : "Export failed. Please try again."}
            </p>
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
          <button
            type="button"
            onClick={handleClose}
            disabled={exportMutation.isPending}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleExport}
            disabled={exportMutation.isPending}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            {exportMutation.isPending ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Exporting...
              </>
            ) : (
              <>
                <Download className="w-4 h-4" />
                Export
              </>
            )}
          </button>
        </div>
      </div>
    </Modal>
  );
}
