import type { ImportBatchListItem } from "@/types/import";
import { ImportBatchStatus } from "@/types/import";
import { format } from "date-fns";
import { ArrowRight, FileText, RotateCcw } from "lucide-react";
import { useRouter } from "next/navigation";

interface ImportHistoryTableProps {
  batches: ImportBatchListItem[];
  onRollback: (id: string) => void;
  isLoading: boolean;
}

function getStatusBadge(status: ImportBatchStatus) {
  switch (status) {
    case ImportBatchStatus.STAGED:
      return (
        <span className="px-2 py-1 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 text-xs font-medium">
          Staged
        </span>
      );
    case ImportBatchStatus.APPROVED:
      return (
        <span className="px-2 py-1 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 text-xs font-medium">
          Approved
        </span>
      );
    case ImportBatchStatus.APPLIED:
      return (
        <span className="px-2 py-1 rounded-full bg-green-500/10 text-green-400 border border-green-500/20 text-xs font-medium">
          Applied
        </span>
      );
    case ImportBatchStatus.ROLLED_BACK:
      return (
        <span className="px-2 py-1 rounded-full bg-slate-500/10 text-slate-400 border border-slate-500/20 text-xs font-medium">
          Rolled Back
        </span>
      );
    case ImportBatchStatus.FAILED:
      return (
        <span className="px-2 py-1 rounded-full bg-red-500/10 text-red-400 border border-red-500/20 text-xs font-medium">
          Failed
        </span>
      );
    case ImportBatchStatus.REJECTED:
      return (
        <span className="px-2 py-1 rounded-full bg-slate-500/10 text-slate-400 border border-slate-500/20 text-xs font-medium line-through">
          Rejected
        </span>
      );
    default:
      return null;
  }
}

export function ImportHistoryTable({
  batches,
  onRollback,
  isLoading,
}: ImportHistoryTableProps) {
  const router = useRouter();

  if (isLoading) {
    return (
      <div className="h-64 w-full bg-slate-800/30 rounded-xl animate-pulse" />
    );
  }

  if (batches.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 border border-dashed border-slate-700 rounded-xl">
        <FileText className="w-12 h-12 text-slate-600 mb-4" />
        <h3 className="text-lg font-medium text-slate-300">
          No Import History
        </h3>
        <p className="text-slate-500">Upload a schedule to get started</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/50">
      <table className="w-full text-left text-sm">
        <thead className="bg-slate-800/50 text-slate-400 uppercase text-xs">
          <tr>
            <th className="px-6 py-4 font-medium">Date</th>
            <th className="px-6 py-4 font-medium">Filename</th>
            <th className="px-6 py-4 font-medium">Target</th>
            <th className="px-6 py-4 font-medium">Status</th>
            <th className="px-6 py-4 font-medium text-center">Changes</th>
            <th className="px-6 py-4 font-medium text-right">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800">
          {batches.map((batch) => (
            <tr
              key={batch.id}
              className="hover:bg-slate-800/30 transition-colors"
            >
              <td className="px-6 py-4 whitespace-nowrap text-slate-300">
                {format(new Date(batch.createdAt), "MMM d, yyyy HH:mm")}
              </td>
              <td className="px-6 py-4 whitespace-nowrap font-medium text-white flex items-center gap-2">
                <FileText className="w-4 h-4 text-slate-500" />
                {batch.filename || "Untitled Batch"}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-slate-400">
                {batch.targetStartDate ? (
                  <span>
                    {batch.targetStartDate} → {batch.targetEndDate}
                  </span>
                ) : (
                  <span className="text-slate-600 italic">No date range</span>
                )}
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                {getStatusBadge(batch.status)}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-center">
                <div className="flex items-center justify-center gap-3">
                  <span className="text-green-400" title="Applied/Approved">
                    +{batch.counts.approved + batch.counts.applied}
                  </span>
                  <span className="text-slate-600">|</span>
                  <span className="text-red-400" title="Failed">
                    {batch.counts.failed + batch.errorCount}
                  </span>
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-right">
                <div className="flex items-center justify-end gap-2">
                  {batch.status === ImportBatchStatus.STAGED && (
                    <button
                      onClick={() => router.push(`/import/${batch.id}`)}
                      className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-md text-xs font-medium transition-colors flex items-center gap-1"
                    >
                      Review
                      <ArrowRight className="w-3 h-3" />
                    </button>
                  )}
                  {batch.status === ImportBatchStatus.APPLIED && (
                    <button
                      onClick={() => onRollback(batch.id)}
                      className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-md text-xs font-medium transition-colors border border-slate-700 hover:border-slate-600 flex items-center gap-1"
                    >
                      <RotateCcw className="w-3 h-3" />
                      Rollback
                    </button>
                  )}
                  {batch.status !== ImportBatchStatus.STAGED && (
                    <button
                      onClick={() => router.push(`/import/${batch.id}`)}
                      className="p-1.5 text-slate-500 hover:text-white transition-colors"
                      title="View Details"
                    >
                      <FileText className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
