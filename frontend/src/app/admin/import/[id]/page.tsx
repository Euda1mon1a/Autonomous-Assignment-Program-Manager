"use client";

import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { useToast } from "@/contexts/ToastContext";
import { BatchDiffViewer } from "@/features/import/components/BatchDiffViewer";
import {
  useApplyBatch,
  useDeleteBatch,
  useImportBatch,
  useImportPreview,
} from "@/hooks/useImport";
import { ImportBatchStatus } from "@/types/import";
import { format } from "date-fns";
import { ArrowLeft, Check, Trash2 } from "lucide-react";
import { useParams, useRouter } from "next/navigation";

export default function ImportReviewPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  const { toast } = useToast();

  const { data: batch, isLoading: isBatchLoading } = useImportBatch(id);
  const { data: preview, isLoading: isPreviewLoading } = useImportPreview(id);

  const applyMutation = useApplyBatch();
  const deleteMutation = useDeleteBatch();

  const handleApply = () => {
    applyMutation.mutate(
      { id },
      {
        onSuccess: () => {
          toast.success("Batch applied successfully");
          router.push("/admin/import");
        },
        onError: (error) => {
          toast.error(
            `Failed to apply batch: ${
              error instanceof Error ? error.message : "Unknown error"
            }`
          );
        },
      }
    );
  };

  const handleDelete = () => {
    if (confirm("Are you sure you want to discard this staged import?")) {
      deleteMutation.mutate(id, {
        onSuccess: () => {
          toast.success("Batch discarded");
          router.push("/admin/import");
        },
        onError: (error) => {
          toast.error(
            `Failed to delete batch: ${
              error instanceof Error ? error.message : "Unknown error"
            }`
          );
        },
      });
    }
  };

  if (isBatchLoading) {
    return (
      <div className="container mx-auto py-8 text-white">
        Loading batch details...
      </div>
    );
  }

  if (!batch) {
    return (
      <div className="container mx-auto py-8 text-white">Batch not found</div>
    );
  }

  // Only allow review for staged batches
  if (batch.status !== ImportBatchStatus.STAGED) {
    return (
      <div className="container mx-auto py-8 px-4">
        <Button
          variant="ghost"
          onClick={() => router.push("/admin/import")}
          className="mb-4 text-slate-400"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Imports
        </Button>
        <Alert title="Batch Processed">
          This batch has already been {batch.status}. You can view it in the
          history.
        </Alert>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 px-4 space-y-6">
      <div className="flex items-center gap-4 mb-2">
        <Button
          variant="ghost"
          onClick={() => router.push("/admin/import")}
          className="text-slate-400 hover:text-white"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back
        </Button>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          Review Import Batch
          <span className="text-sm font-normal text-slate-500 bg-slate-800 px-2 py-1 rounded ml-2">
            {batch.filename}
          </span>
        </h1>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Batch Metadata Card */}
        <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6 space-y-4 h-fit">
          <h2 className="text-lg font-semibold text-white mb-4">
            Batch Details
          </h2>

          <div className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-slate-500">Created</span>
              <span className="text-slate-300">
                {format(new Date(batch.createdAt), "MMM d, yyyy HH:mm")}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Target Range</span>
              <span className="text-slate-300">
                {batch.targetStartDate
                  ? `${batch.targetStartDate} → ${batch.targetEndDate}`
                  : "N/A"}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Total Rows</span>
              <span className="text-slate-300">{batch.row_count}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Conflicts</span>
              <span
                className={`font-medium ${
                  preview?.conflictCount ? "text-orange-400" : "text-green-400"
                }`}
              >
                {preview?.conflictCount || 0}
              </span>
            </div>
          </div>

          <div className="pt-4 border-t border-slate-800 space-y-3">
            <Button
              onClick={handleApply}
              className="w-full bg-green-600 hover:bg-green-500 text-white"
              disabled={applyMutation.isPending}
            >
              <Check className="w-4 h-4 mr-2" />
              {applyMutation.isPending ? "Applying..." : "Apply Changes"}
            </Button>

            <Button
              variant="danger"
              onClick={handleDelete}
              className="w-full bg-red-900/20 text-red-400 hover:bg-red-900/40 border border-red-900/50"
              disabled={deleteMutation.isPending}
            >
              <Trash2 className="w-4 h-4 mr-2" />
              Discard Batch
            </Button>
          </div>
        </div>

        {/* Diff Viewer */}
        <div className="md:col-span-2 space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-lg font-semibold text-white">
              Proposed Changes
            </h2>
            <div className="text-sm text-slate-400">
              Showing {preview?.stagedAssignments.length || 0} records
            </div>
          </div>

          {preview?.conflictCount && preview.conflictCount > 0 ? (
            <Alert
              variant="warning"
              className="bg-orange-900/20 border-orange-900/50 text-orange-200"
              title="Conflicts Detected"
            >
              This import contains {preview.conflictCount} conflicts that will
              overwrite existing data. Please review carefully.
            </Alert>
          ) : null}

          <BatchDiffViewer
            assignments={preview?.stagedAssignments || []}
            conflicts={preview?.conflicts || []}
            isLoading={isPreviewLoading}
          />
        </div>
      </div>
    </div>
  );
}
