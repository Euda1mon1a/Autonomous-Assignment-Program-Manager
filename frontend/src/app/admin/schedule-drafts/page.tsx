"use client";

import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { useToast } from "@/contexts/ToastContext";
import {
  useDiscardDraft,
  useRollbackDraft,
  useScheduleDrafts,
} from "@/hooks/useScheduleDrafts";
import {
  DraftSourceType,
  ScheduleDraftListItem,
  ScheduleDraftStatus,
} from "@/types/schedule-draft";
import { format } from "date-fns";
import {
  AlertTriangle,
  CheckCircle,
  Clock,
  Eye,
  FileText,
  RotateCcw,
  Trash2,
  XCircle,
} from "lucide-react";
import Link from "next/link";
import { useState } from "react";

const statusConfig: Record<
  ScheduleDraftStatus,
  { label: string; color: string; icon: React.ElementType }
> = {
  [ScheduleDraftStatus.DRAFT]: {
    label: "Draft",
    color: "bg-blue-900/30 text-blue-400 border-blue-900/50",
    icon: Clock,
  },
  [ScheduleDraftStatus.PUBLISHED]: {
    label: "Published",
    color: "bg-green-900/30 text-green-400 border-green-900/50",
    icon: CheckCircle,
  },
  [ScheduleDraftStatus.ROLLED_BACK]: {
    label: "Rolled Back",
    color: "bg-orange-900/30 text-orange-400 border-orange-900/50",
    icon: RotateCcw,
  },
  [ScheduleDraftStatus.DISCARDED]: {
    label: "Discarded",
    color: "bg-slate-800/50 text-slate-400 border-slate-700",
    icon: XCircle,
  },
};

const sourceConfig: Record<DraftSourceType, { label: string; color: string }> =
  {
    [DraftSourceType.SOLVER]: {
      label: "Solver",
      color: "bg-purple-900/30 text-purple-400",
    },
    [DraftSourceType.MANUAL]: {
      label: "Manual",
      color: "bg-cyan-900/30 text-cyan-400",
    },
    [DraftSourceType.SWAP]: {
      label: "Swap",
      color: "bg-yellow-900/30 text-yellow-400",
    },
  [DraftSourceType.IMPORT]: {
    label: "Import",
    color: "bg-pink-900/30 text-pink-400",
  },
  [DraftSourceType.RESILIENCE]: {
    label: "Resilience",
    color: "bg-red-900/30 text-red-400",
  },
};

function DraftStatusBadge({ status }: { status: ScheduleDraftStatus }) {
  const config = statusConfig[status];
  const Icon = config.icon;
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-md border ${config.color}`}
    >
      <Icon className="w-3 h-3" />
      {config.label}
    </span>
  );
}

function SourceBadge({ source }: { source: DraftSourceType }) {
  const config = sourceConfig[source];
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 text-xs font-medium rounded ${config.color}`}
    >
      {config.label}
    </span>
  );
}

function DraftRow({
  draft,
  onRollback,
  onDiscard,
}: {
  draft: ScheduleDraftListItem;
  onRollback: (id: string) => void;
  onDiscard: (id: string) => void;
}) {
  const hasUnackedFlags =
    draft.flagsTotal > 0 && draft.flagsAcknowledged < draft.flagsTotal;

  return (
    <tr className="border-b border-slate-800 hover:bg-slate-800/30 transition-colors">
      <td className="px-4 py-3">
        <div className="flex flex-col gap-1">
          <span className="text-sm text-white font-medium">
            Block {draft.targetBlock || "N/A"}
          </span>
          <span className="text-xs text-slate-500">
            {draft.targetStartDate} to {draft.targetEndDate}
          </span>
        </div>
      </td>
      <td className="px-4 py-3">
        <div className="flex items-center gap-2">
          <DraftStatusBadge status={draft.status} />
          <SourceBadge source={draft.sourceType} />
        </div>
      </td>
      <td className="px-4 py-3">
        <div className="flex flex-col gap-1 text-xs">
          <span className="text-green-400">+{draft.counts.added} added</span>
          <span className="text-yellow-400">
            ~{draft.counts.modified} modified
          </span>
          <span className="text-red-400">-{draft.counts.deleted} deleted</span>
        </div>
      </td>
      <td className="px-4 py-3">
        {draft.flagsTotal > 0 ? (
          <div className="flex items-center gap-2">
            {hasUnackedFlags && (
              <AlertTriangle className="w-4 h-4 text-orange-400" />
            )}
            <span
              className={`text-sm ${hasUnackedFlags ? "text-orange-400" : "text-green-400"}`}
            >
              {draft.flagsAcknowledged}/{draft.flagsTotal}
            </span>
          </div>
        ) : (
          <span className="text-sm text-slate-500">None</span>
        )}
      </td>
      <td className="px-4 py-3">
        <span className="text-sm text-slate-400">
          {format(new Date(draft.createdAt), "MMM d, HH:mm")}
        </span>
      </td>
      <td className="px-4 py-3">
        <div className="flex items-center gap-2">
          {draft.status === ScheduleDraftStatus.DRAFT && (
            <Link href={`/admin/schedule-drafts/${draft.id}`}>
              <Button
                size="sm"
                variant="outline"
                className="text-blue-400"
                onClick={() => {}}
              >
                <Eye className="w-3 h-3 mr-1" />
                Review
              </Button>
            </Link>
          )}
          {draft.status === ScheduleDraftStatus.PUBLISHED && (
            <Button
              size="sm"
              variant="outline"
              className="text-orange-400"
              onClick={() => onRollback(draft.id)}
            >
              <RotateCcw className="w-3 h-3 mr-1" />
              Rollback
            </Button>
          )}
          {draft.status === ScheduleDraftStatus.DRAFT && (
            <Button
              size="sm"
              variant="ghost"
              className="text-red-400 hover:text-red-300"
              onClick={() => onDiscard(draft.id)}
            >
              <Trash2 className="w-3 h-3" />
            </Button>
          )}
        </div>
      </td>
    </tr>
  );
}

export default function ScheduleDraftsPage() {
  const { toast } = useToast();
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<
    ScheduleDraftStatus | undefined
  >();
  const pageSize = 20;

  const {
    data: draftsData,
    isLoading,
    isError,
  } = useScheduleDrafts(page, statusFilter, pageSize);

  const rollbackMutation = useRollbackDraft();
  const discardMutation = useDiscardDraft();

  const handleRollback = (id: string) => {
    if (
      confirm(
        "Are you sure you want to rollback this schedule? This will undo all published changes."
      )
    ) {
      rollbackMutation.mutate(
        { draftId: id, reason: "User requested rollback" },
        {
          onSuccess: () => {
            toast.success("Schedule rolled back successfully");
          },
          onError: (error) => {
            toast.error(
              `Rollback failed: ${error instanceof Error ? error.message : "Unknown error"}`
            );
          },
        }
      );
    }
  };

  const handleDiscard = (id: string) => {
    if (confirm("Are you sure you want to discard this draft?")) {
      discardMutation.mutate(id, {
        onSuccess: () => {
          toast.success("Draft discarded");
        },
        onError: (error) => {
          toast.error(
            `Discard failed: ${error instanceof Error ? error.message : "Unknown error"}`
          );
        },
      });
    }
  };

  return (
    <div className="container mx-auto py-8 px-4 space-y-8">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">
            Schedule Drafts
          </h1>
          <p className="text-slate-300">
            Review and publish schedule changes before they go live.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={statusFilter || ""}
            onChange={(e) =>
              setStatusFilter(
                e.target.value
                  ? (e.target.value as ScheduleDraftStatus)
                  : undefined
              )
            }
            className="bg-slate-800 border border-slate-700 text-slate-300 rounded-md px-3 py-2 text-sm"
          >
            <option value="">All Statuses</option>
            <option value="draft">Draft</option>
            <option value="published">Published</option>
            <option value="rolled_back">Rolled Back</option>
            <option value="discarded">Discarded</option>
          </select>
        </div>
      </div>

      {isError && (
        <Alert variant="error" title="Error loading drafts">
          Failed to load schedule drafts. Please try refreshing the page.
        </Alert>
      )}

      <div className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden">
        {draftsData?.items && draftsData.items.length === 0 && !isLoading ? (
          <div className="flex flex-col items-center justify-center h-64">
            <FileText className="w-12 h-12 text-slate-600 mb-4" />
            <h3 className="text-lg font-medium text-slate-300">
              No Schedule Drafts
            </h3>
            <p className="text-slate-500">
              Drafts will appear here when schedules are generated or edited.
            </p>
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-slate-800/50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                  Block / Dates
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                  Changes
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                  Flags
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                  Created
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-slate-400">
                    Loading drafts...
                  </td>
                </tr>
              ) : (
                draftsData?.items.map((draft) => (
                  <DraftRow
                    key={draft.id}
                    draft={draft}
                    onRollback={handleRollback}
                    onDiscard={handleDiscard}
                  />
                ))
              )}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      {draftsData && draftsData.total > pageSize && (
        <div className="flex justify-end gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1 || isLoading}
          >
            Previous
          </Button>
          <span className="flex items-center text-sm text-slate-300">
            Page {page} of {Math.ceil(draftsData.total / pageSize)}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage((p) => p + 1)}
            disabled={!draftsData.hasNext || isLoading}
          >
            Next
          </Button>
        </div>
      )}
    </div>
  );
}
