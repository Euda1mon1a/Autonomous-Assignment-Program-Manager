"use client";

import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { useToast } from "@/contexts/ToastContext";
import { BulkImportModal } from "@/features/import-export/BulkImportModal";
import { useImport } from "@/features/import-export/useImport";
import { ImportHistoryTable } from "@/features/import/components/ImportHistoryTable";
import { useImportBatches, useRollbackBatch } from "@/hooks/useImport";
import { FileText, Upload } from "lucide-react";
import { useState } from "react";

export default function ImportPage() {
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const { toast } = useToast();

  // Use pagination state
  const [page, setPage] = useState(1);
  const pageSize = 10;

  // Fetch batches
  const {
    data: batchesData,
    isLoading: isBatchesLoading,
    isError: isBatchesError,
    refetch: refetchBatches,
  } = useImportBatches(page);

  // Rollback mutation
  const rollbackMutation = useRollbackBatch();

  // Import hook just for the modal logic mostly
  const { reset } = useImport({
    onComplete: (result) => {
      setIsUploadModalOpen(false);
      reset();
      toast.success(
        `Import complete: ${result.successCount} records processed`
      );
      refetchBatches();
    },
    onError: (error) => {
      toast.error(`Import failed: ${error.message}`);
    },
  });

  const handleRollback = (id: string) => {
    if (
      confirm(
        "Are you sure you want to rollback this import? This will revert all changes made by this batch."
      )
    ) {
      rollbackMutation.mutate(
        { id },
        {
          onSuccess: () => {
            toast.success("Batch rolled back successfully");
          },
          onError: (error) => {
            toast.error(
              `Rollback failed: ${
                error instanceof Error ? error.message : "Unknown error"
              }`
            );
          },
        }
      );
    }
  };

  return (
    <div className="container mx-auto py-8 px-4 space-y-8">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Data Import</h1>
          <p className="text-slate-300">
            Upload schedules, people, and absences. Review staged changes before
            applying.
          </p>
        </div>
        <Button
          onClick={() => setIsUploadModalOpen(true)}
          className="bg-blue-600 hover:bg-blue-500 text-white"
        >
          <Upload className="w-4 h-4 mr-2" />
          New Import
        </Button>
      </div>

      {isBatchesError && (
        <Alert variant="error" title="Error loading history">
          Failed to load import history. Please try refreshing the page.
        </Alert>
      )}

      <div className="space-y-4">
        <h2 className="text-xl font-semibold text-white">Import History</h2>

        {batchesData?.items &&
        batchesData.items.length === 0 &&
        !isBatchesLoading ? (
          <div className="flex flex-col items-center justify-center h-64 border border-dashed border-slate-700 rounded-xl bg-slate-900/50">
            <FileText className="w-12 h-12 text-slate-600 mb-4" />
            <h3 className="text-lg font-medium text-slate-300">
              No Import History
            </h3>
            <p className="text-slate-300">Upload a schedule to get started</p>
          </div>
        ) : (
          <ImportHistoryTable
            batches={batchesData?.items || []}
            isLoading={isBatchesLoading}
            onRollback={handleRollback}
          />
        )}

        {/* Simple pagination controls if needed */}
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
      />
    </div>
  );
}
