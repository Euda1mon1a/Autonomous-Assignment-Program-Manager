"use client";

import { BatchDiffViewer } from "@/features/import/components/BatchDiffViewer";
import {
  useApplyBatch,
  useImportBatch,
  useImportPreview,
} from "@/hooks/useImport";
import { ImportBatchStatus } from "@/types/import";
import {
  AlertTriangle,
  ArrowLeft,
  Calendar,
  Loader2,
  Play,
} from "lucide-react";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";

export default function BatchReviewPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const { data: batch, isLoading: isBatchLoading } = useImportBatch(id);
  const { data: preview, isLoading: isPreviewLoading } = useImportPreview(id);

  const applyMutation = useApplyBatch();
  const [isApplying, setIsApplying] = useState(false);

  const handleApply = async () => {
    if (
      !confirm(
        "Are you sure you want to apply these changes? This will modify the live schedule."
      )
    )
      return;

    setIsApplying(true);
    try {
      await applyMutation.mutateAsync({ id });
      setIsApplying(false);
      // Refresh logic is handled by query invalidation, user will see status update
    } catch (error) {
      console.error("Failed to apply:", error);
      setIsApplying(false);
    }
  };

  if (isBatchLoading || isPreviewLoading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
      </div>
    );
  }

  if (!batch || !preview) return <div>Batch not found</div>;

  const isStaged = batch.status === ImportBatchStatus.STAGED;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Breadcrumb / Nav */}
        <button
          onClick={() => router.push("/import")}
          className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors text-sm"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Imports
        </button>

        {/* Header Card */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-white">Import Review</h1>
              <span
                className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide
                        ${
                          isStaged
                            ? "bg-blue-500/20 text-blue-400 border border-blue-500/30"
                            : ""
                        }
                        ${
                          batch.status === ImportBatchStatus.APPLIED
                            ? "bg-green-500/20 text-green-400 border border-green-500/30"
                            : ""
                        }
                        ${
                          batch.status === ImportBatchStatus.FAILED
                            ? "bg-red-500/20 text-red-400 border border-red-500/30"
                            : ""
                        }
                    `}
              >
                {batch.status}
              </span>
            </div>
            <div className="flex items-center gap-6 mt-2 text-slate-400 text-sm">
              <div className="flex items-center gap-2">
                <span className="text-slate-500">File:</span>
                <span className="text-slate-300 font-mono">
                  {batch.filename}
                </span>
              </div>
              {batch.targetStartDate && (
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-slate-500" />
                  <span>
                    {batch.targetStartDate} → {batch.targetEndDate}
                  </span>
                </div>
              )}
            </div>
          </div>

          {isStaged && (
            <div className="flex gap-3">
              <button
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-sm font-medium transition-colors"
                onClick={() => router.push("/import")}
              >
                Cancel
              </button>
              <button
                onClick={handleApply}
                disabled={isApplying}
                className="px-6 py-2 bg-green-600 hover:bg-green-500 text-white rounded-lg text-sm font-medium transition-colors shadow-lg shadow-green-900/20 flex items-center gap-2"
              >
                {isApplying ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Play className="w-4 h-4" />
                )}
                Apply Changes
              </button>
            </div>
          )}
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-4 gap-4">
          <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-4">
            <div className="text-slate-500 text-xs uppercase font-medium">
              New Assignments
            </div>
            <div className="text-2xl font-bold text-green-400 mt-1">
              {preview.newCount}
            </div>
          </div>
          <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-4">
            <div className="text-slate-500 text-xs uppercase font-medium">
              Updates
            </div>
            <div className="text-2xl font-bold text-blue-400 mt-1">
              {preview.updateCount}
            </div>
          </div>
          <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-4">
            <div className="text-slate-500 text-xs uppercase font-medium">
              Conflicts
            </div>
            <div
              className={`text-2xl font-bold mt-1 ${
                preview.conflictCount > 0
                  ? "text-orange-400"
                  : "text-slate-400"
              }`}
            >
              {preview.conflictCount}
            </div>
          </div>
          <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-4">
            <div className="text-slate-500 text-xs uppercase font-medium">
              Violations
            </div>
            <div
              className={`text-2xl font-bold mt-1 ${
                preview.acgmeViolations.length > 0
                  ? "text-red-400"
                  : "text-slate-400"
              }`}
            >
              {preview.acgmeViolations.length}
            </div>
          </div>
        </div>

        {/* ACGME Warnings */}
        {preview.acgmeViolations.length > 0 && (
          <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 flex items-start gap-4">
            <AlertTriangle className="w-5 h-5 text-red-500 mt-0.5" />
            <div>
              <h3 className="text-red-400 font-bold text-sm">
                ACGME Compliance Warnings
              </h3>
              <ul className="mt-2 space-y-1">
                {preview.acgmeViolations.map((v, i) => (
                  <li key={i} className="text-red-300 text-sm">
                    • {v}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {/* Diff Viewer */}
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-white">Change Preview</h2>
          <BatchDiffViewer
            assignments={preview.stagedAssignments}
            conflicts={preview.conflicts}
            isLoading={false}
          />
        </div>
      </div>
    </div>
  );
}
