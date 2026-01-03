"use client";

import { ImportHistoryTable } from "@/features/import/components/ImportHistoryTable";
import {
  useImportBatches,
  useRollbackBatch,
  useStageImport,
} from "@/hooks/useImport";
import { FileText, Upload } from "lucide-react";
import { useRouter } from "next/navigation";
// import { ProtectedRoute } from '@/components/ProtectedRoute'; // Assumed to exist or will be added

export default function ImportPage() {
  const router = useRouter();
  const { data, isLoading } = useImportBatches();
  const stageImportMutation = useStageImport();
  const rollbackMutation = useRollbackBatch();

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      const formData = new FormData();
      formData.append("file", file);

      const result = await stageImportMutation.mutateAsync(formData);
      // Redirect to review page immediately
      router.push(`/import/${result.batch_id}`);
    } catch (error) {
      console.error("Failed to stage file:", error);
      alert("Failed to upload file. Please try again.");
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-400">
              Import Management
            </h1>
            <p className="text-slate-400 mt-2">
              Staged import workflow with conflict detection and rollback.
            </p>
          </div>

          <div>
            <label className="cursor-pointer inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium transition-colors shadow-lg shadow-blue-900/20">
              <Upload className="w-4 h-4" />
              Upload Schedule
              <input
                type="file"
                accept=".xlsx,.xls"
                className="hidden"
                onChange={handleFileUpload}
                disabled={stageImportMutation.isPending}
              />
            </label>
            {stageImportMutation.isPending && (
              <div className="text-xs text-blue-400 text-right mt-1">
                Uploading...
              </div>
            )}
          </div>
        </div>

        {/* History Table */}
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-white flex items-center gap-2">
            <FileText className="w-5 h-5 text-slate-500" />
            Import History
          </h2>

          <ImportHistoryTable
            batches={data?.items || []}
            isLoading={isLoading}
            onRollback={(id) => {
              if (
                confirm(
                  "Are you sure you want to rollback this batch? This will revert all changes made by this import."
                )
              ) {
                rollbackMutation.mutate({ id });
              }
            }}
          />
        </div>
      </div>
    </div>
  );
}
