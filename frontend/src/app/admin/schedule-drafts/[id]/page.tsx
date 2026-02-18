"use client";

import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { useToast } from "@/contexts/ToastContext";
import {
  useAcknowledgeFlag,
  useApproveBreakGlass,
  useBulkAcknowledgeFlags,
  useDiscardDraft,
  usePublishDraft,
  useScheduleDraft,
  useScheduleDraftPreview,
} from "@/hooks/useScheduleDrafts";
import {
  DraftAssignmentChangeType,
  DraftAssignmentResponse,
  DraftFlagResponse,
  DraftFlagSeverity,
  DraftFlagType,
  ScheduleDraftStatus,
} from "@/types/schedule-draft";
import { format } from "date-fns";
import {
  AlertTriangle,
  AlertOctagon,
  ArrowLeft,
  BadgeX,
  Check,
  CheckCircle,
  Clock,
  Minus,
  Pen,
  Plus,
  Send,
  Shield,
  ShieldCheck,
  Trash2,
  XCircle,
} from "lucide-react";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";

const flagTypeConfig: Record<
  DraftFlagType,
  { label: string; color: string; icon: React.ElementType }
> = {
  [DraftFlagType.CONFLICT]: {
    label: "Conflict",
    color: "text-red-400 bg-red-900/20 border-red-900/50",
    icon: XCircle,
  },
  [DraftFlagType.ACGME_VIOLATION]: {
    label: "ACGME",
    color: "text-orange-400 bg-orange-900/20 border-orange-900/50",
    icon: AlertTriangle,
  },
  [DraftFlagType.COVERAGE_GAP]: {
    label: "Coverage Gap",
    color: "text-yellow-400 bg-yellow-900/20 border-yellow-900/50",
    icon: Clock,
  },
  [DraftFlagType.MANUAL_REVIEW]: {
    label: "Review",
    color: "text-blue-400 bg-blue-900/20 border-blue-900/50",
    icon: Pen,
  },
  [DraftFlagType.LOCK_WINDOW_VIOLATION]: {
    label: "Lock Window",
    color: "text-red-400 bg-red-900/20 border-red-900/50",
    icon: AlertOctagon,
  },
  [DraftFlagType.CREDENTIAL_MISSING]: {
    label: "Missing Credential",
    color: "text-purple-400 bg-purple-900/20 border-purple-900/50",
    icon: BadgeX,
  },
};

const severityConfig: Record<DraftFlagSeverity, { label: string; color: string }> = {
  [DraftFlagSeverity.ERROR]: { label: "Error", color: "text-red-400" },
  [DraftFlagSeverity.WARNING]: { label: "Warning", color: "text-yellow-400" },
  [DraftFlagSeverity.INFO]: { label: "Info", color: "text-blue-400" },
};

const changeTypeConfig: Record<
  DraftAssignmentChangeType,
  { label: string; color: string; icon: React.ElementType }
> = {
  [DraftAssignmentChangeType.ADD]: {
    label: "Add",
    color: "text-green-400 bg-green-900/20",
    icon: Plus,
  },
  [DraftAssignmentChangeType.MODIFY]: {
    label: "Modify",
    color: "text-yellow-400 bg-yellow-900/20",
    icon: Pen,
  },
  [DraftAssignmentChangeType.DELETE]: {
    label: "Delete",
    color: "text-red-400 bg-red-900/20",
    icon: Minus,
  },
};

function FlagCard({
  flag,
  onAcknowledge,
  isAcknowledging,
}: {
  flag: DraftFlagResponse;
  onAcknowledge: (flagId: string) => void;
  isAcknowledging: boolean;
}) {
  const typeConfig = flagTypeConfig[flag.flagType];
  const Icon = typeConfig.icon;
  const isAcked = !!flag.acknowledgedAt;

  return (
    <div
      className={`border rounded-lg p-4 ${isAcked ? "bg-slate-800/30 border-slate-700" : typeConfig.color}`}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <Icon
            className={`w-5 h-5 mt-0.5 ${isAcked ? "text-slate-500" : ""}`}
          />
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span
                className={`text-sm font-medium ${isAcked ? "text-slate-400" : ""}`}
              >
                {typeConfig.label}
              </span>
              <span
                className={`text-xs px-1.5 py-0.5 rounded ${severityConfig[flag.severity].color} bg-slate-800/50`}
              >
                {severityConfig[flag.severity].label}
              </span>
            </div>
            <p className={`text-sm ${isAcked ? "text-slate-500" : "text-slate-300"}`}>
              {flag.message}
            </p>
            {flag.affectedDate && (
              <p className="text-xs text-slate-500">
                Date: {flag.affectedDate}
                {flag.personName && ` | Person: ${flag.personName}`}
              </p>
            )}
          </div>
        </div>
        {!isAcked && (
          <Button
            size="sm"
            variant="outline"
            onClick={() => onAcknowledge(flag.id)}
            disabled={isAcknowledging}
            className="shrink-0"
          >
            <Check className="w-3 h-3 mr-1" />
            Acknowledge
          </Button>
        )}
        {isAcked && (
          <span className="text-xs text-green-400 flex items-center gap-1">
            <CheckCircle className="w-3 h-3" />
            Acknowledged
          </span>
        )}
      </div>
    </div>
  );
}

function AssignmentRow({ assignment }: { assignment: DraftAssignmentResponse }) {
  const config = changeTypeConfig[assignment.changeType];
  const Icon = config.icon;

  return (
    <tr className="border-b border-slate-800 hover:bg-slate-800/30">
      <td className="px-3 py-2">
        <span
          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs ${config.color}`}
        >
          <Icon className="w-3 h-3" />
          {config.label}
        </span>
      </td>
      <td className="px-3 py-2 text-sm text-slate-300">
        {assignment.personName || assignment.personId.slice(0, 8)}
      </td>
      <td className="px-3 py-2 text-sm text-slate-400">
        {assignment.assignmentDate}
      </td>
      <td className="px-3 py-2 text-sm text-slate-400">
        {assignment.timeOfDay || "Full Day"}
      </td>
      <td className="px-3 py-2 text-sm text-slate-300">
        {assignment.activityCode || assignment.rotationName || "-"}
      </td>
    </tr>
  );
}

export default function ScheduleDraftReviewPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  const { toast } = useToast();

  const [overrideComment, setOverrideComment] = useState("");
  const [breakGlassReason, setBreakGlassReason] = useState("");

  const { data: draft, isLoading: isDraftLoading } = useScheduleDraft(id);
  const { data: preview, isLoading: isPreviewLoading } =
    useScheduleDraftPreview(id);

  const publishMutation = usePublishDraft();
  const discardMutation = useDiscardDraft();
  const ackFlagMutation = useAcknowledgeFlag();
  const bulkAckMutation = useBulkAcknowledgeFlags();
  const approveBreakGlassMutation = useApproveBreakGlass();

  const handleApproveBreakGlass = () => {
    if (!breakGlassReason.trim() || breakGlassReason.trim().length < 10) {
      toast.error("Break-glass reason must be at least 10 characters");
      return;
    }

    approveBreakGlassMutation.mutate(
      { draftId: id, reason: breakGlassReason.trim() },
      {
        onSuccess: () => {
          toast.success("Break-glass approval granted");
          setBreakGlassReason("");
        },
        onError: (error) => {
          toast.error(
            `Approval failed: ${error instanceof Error ? error.message : "Unknown error"}`
          );
        },
      }
    );
  };

  const handlePublish = () => {
    const hasUnackedFlags =
      draft && draft.flagsTotal > 0 && draft.flagsAcknowledged < draft.flagsTotal;

    if (needsBreakGlass) {
      toast.error(
        "Break-glass approval is required before publishing. Use the approval button below."
      );
      return;
    }

    if (hasUnackedFlags && !overrideComment.trim()) {
      toast.error(
        "Please acknowledge all flags or provide an override comment"
      );
      return;
    }

    publishMutation.mutate(
      {
        draftId: id,
        payload: {
          overrideComment: overrideComment.trim() || undefined,
          validateAcgme: true,
        },
      },
      {
        onSuccess: (result) => {
          toast.success(
            `Published ${result.publishedCount} assignments successfully`
          );
          router.push("/admin/schedule-drafts");
        },
        onError: (error) => {
          toast.error(
            `Publish failed: ${error instanceof Error ? error.message : "Unknown error"}`
          );
        },
      }
    );
  };

  const handleDiscard = () => {
    if (confirm("Are you sure you want to discard this draft?")) {
      discardMutation.mutate(id, {
        onSuccess: () => {
          toast.success("Draft discarded");
          router.push("/admin/schedule-drafts");
        },
        onError: (error) => {
          toast.error(
            `Discard failed: ${error instanceof Error ? error.message : "Unknown error"}`
          );
        },
      });
    }
  };

  const handleAcknowledgeFlag = (flagId: string) => {
    ackFlagMutation.mutate(
      { draftId: id, flagId },
      {
        onSuccess: () => {
          toast.success("Flag acknowledged");
        },
        onError: (error) => {
          toast.error(
            `Failed to acknowledge: ${error instanceof Error ? error.message : "Unknown error"}`
          );
        },
      }
    );
  };

  const handleAcknowledgeAll = () => {
    const unackedFlags =
      preview?.flags.filter((f) => !f.acknowledgedAt).map((f) => f.id) || [];
    if (unackedFlags.length === 0) return;

    bulkAckMutation.mutate(
      { draftId: id, flagIds: unackedFlags },
      {
        onSuccess: (result) => {
          toast.success(`Acknowledged ${result.acknowledgedCount} flags`);
        },
        onError: (error) => {
          toast.error(
            `Failed: ${error instanceof Error ? error.message : "Unknown error"}`
          );
        },
      }
    );
  };

  if (isDraftLoading) {
    return (
      <div className="container mx-auto py-8 text-white">
        Loading draft details...
      </div>
    );
  }

  if (!draft) {
    return (
      <div className="container mx-auto py-8 text-white">Draft not found</div>
    );
  }

  // Only allow review for drafts in DRAFT status
  if (draft.status !== ScheduleDraftStatus.DRAFT) {
    return (
      <div className="container mx-auto py-8 px-4">
        <Button
          variant="ghost"
          onClick={() => router.push("/admin/schedule-drafts")}
          className="mb-4 text-slate-400"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Drafts
        </Button>
        <Alert title="Draft Already Processed">
          This draft has already been {draft.status}. You can view it in the
          history.
        </Alert>
      </div>
    );
  }

  const hasUnackedFlags =
    draft.flagsTotal > 0 && draft.flagsAcknowledged < draft.flagsTotal;
  const unackedCount = draft.flagsTotal - draft.flagsAcknowledged;
  const lockWindowFlag = preview?.flags?.find(
    (flag) => flag.flagType === DraftFlagType.LOCK_WINDOW_VIOLATION
  );
  const needsBreakGlass = !!lockWindowFlag && !draft.approvedAt;

  return (
    <div className="container mx-auto py-8 px-4 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4 mb-2">
        <Button
          variant="ghost"
          onClick={() => router.push("/admin/schedule-drafts")}
          className="text-slate-400 hover:text-white"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back
        </Button>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          Review Schedule Draft
          <span className="text-sm font-normal text-slate-500 bg-slate-800 px-2 py-1 rounded ml-2">
            Block {draft.targetBlock || "N/A"}
          </span>
        </h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Metadata & Actions */}
        <div className="space-y-6">
          {/* Draft Details Card */}
          <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6 space-y-4">
            <h2 className="text-lg font-semibold text-white">Draft Details</h2>

            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-500">Created</span>
                <span className="text-slate-300">
                  {format(new Date(draft.createdAt), "MMM d, yyyy HH:mm")}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Date Range</span>
                <span className="text-slate-300">
                  {draft.targetStartDate} to {draft.targetEndDate}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Source</span>
                <span className="text-slate-300 capitalize">
                  {draft.sourceType}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Changes</span>
                <span className="text-slate-300">
                  +{preview?.addCount || 0} ~{preview?.modifyCount || 0} -{preview?.deleteCount || 0}
                </span>
              </div>
            </div>

            <div className="pt-4 border-t border-slate-800 space-y-3">
              <Button
                onClick={handlePublish}
                className="w-full bg-green-600 hover:bg-green-500 text-white"
                disabled={publishMutation.isPending || needsBreakGlass}
                title={
                  needsBreakGlass
                    ? "Break-glass approval required before publish"
                    : undefined
                }
              >
                <Send className="w-4 h-4 mr-2" />
                {publishMutation.isPending ? "Publishing..." : "Publish to Live"}
              </Button>

              <Button
                variant="danger"
                onClick={handleDiscard}
                className="w-full bg-red-900/20 text-red-400 hover:bg-red-900/40 border border-red-900/50"
                disabled={discardMutation.isPending}
              >
                <Trash2 className="w-4 h-4 mr-2" />
                Discard Draft
              </Button>
            </div>
          </div>

          {/* Break-Glass Approval (lock window) */}
          {lockWindowFlag && (
            <div
              className={`border rounded-xl p-4 space-y-3 ${
                draft.approvedAt
                  ? "bg-green-900/10 border-green-900/50"
                  : "bg-red-900/10 border-red-900/50"
              }`}
            >
              {draft.approvedAt ? (
                <>
                  <p className="text-sm text-green-300 flex items-center gap-2">
                    <ShieldCheck className="w-4 h-4" />
                    Break-glass approved
                  </p>
                  <div className="text-xs text-slate-400 space-y-1">
                    <p>Reason: {draft.approvalReason}</p>
                    <p>
                      Approved:{" "}
                      {format(new Date(draft.approvedAt), "MMM d, yyyy HH:mm")}
                    </p>
                    {draft.lockDateAtApproval && (
                      <p>Lock date at approval: {draft.lockDateAtApproval}</p>
                    )}
                  </div>
                </>
              ) : (
                <>
                  <p className="text-sm text-red-300">
                    <AlertOctagon className="w-4 h-4 inline mr-1" />
                    {lockWindowFlag.message ||
                      "This draft touches the lock window. Break-glass approval is required before publish."}
                  </p>
                  <textarea
                    value={breakGlassReason}
                    onChange={(e) => setBreakGlassReason(e.target.value)}
                    placeholder="Break-glass reason (min 10 characters)"
                    className="w-full bg-slate-800 border border-slate-700 rounded-md p-2 text-sm text-slate-300 placeholder:text-slate-500"
                    rows={3}
                  />
                  <Button
                    onClick={handleApproveBreakGlass}
                    disabled={
                      approveBreakGlassMutation.isPending ||
                      breakGlassReason.trim().length < 10
                    }
                    className="w-full bg-amber-600 hover:bg-amber-500 text-white"
                  >
                    <Shield className="w-4 h-4 mr-2" />
                    {approveBreakGlassMutation.isPending
                      ? "Approving..."
                      : "Approve Break-Glass"}
                  </Button>
                </>
              )}
            </div>
          )}

          {/* Override Comment (if flags exist) */}
          {hasUnackedFlags && (
            <div className="bg-orange-900/10 border border-orange-900/50 rounded-xl p-4 space-y-3">
              <p className="text-sm text-orange-300">
                <AlertTriangle className="w-4 h-4 inline mr-1" />
                {unackedCount} unacknowledged flag{unackedCount > 1 ? "s" : ""}.
                Acknowledge all or provide override comment to publish.
              </p>
              <textarea
                value={overrideComment}
                onChange={(e) => setOverrideComment(e.target.value)}
                placeholder="Override comment (required if not acknowledging all flags)"
                className="w-full bg-slate-800 border border-slate-700 rounded-md p-2 text-sm text-slate-300 placeholder:text-slate-500"
                rows={3}
              />
            </div>
          )}
        </div>

        {/* Right Column - Flags & Assignments */}
        <div className="lg:col-span-2 space-y-6">
          {/* Flags Section */}
          {preview?.flags && preview.flags.length > 0 && (
            <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6 space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-white">
                  Review Flags ({preview.flags.length})
                </h2>
                {hasUnackedFlags && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={handleAcknowledgeAll}
                    disabled={bulkAckMutation.isPending}
                  >
                    <Check className="w-3 h-3 mr-1" />
                    Acknowledge All
                  </Button>
                )}
              </div>

              <div className="space-y-3 max-h-96 overflow-y-auto">
                {preview.flags.map((flag) => (
                  <FlagCard
                    key={flag.id}
                    flag={flag}
                    onAcknowledge={handleAcknowledgeFlag}
                    isAcknowledging={ackFlagMutation.isPending}
                  />
                ))}
              </div>
            </div>
          )}

          {/* ACGME Warnings */}
          {preview?.acgmeViolations && preview.acgmeViolations.length > 0 && (
            <Alert variant="warning" title="ACGME Compliance Warnings">
              <ul className="list-disc list-inside text-sm space-y-1 mt-2">
                {preview.acgmeViolations.map((violation) => (
                  <li key={violation}>{violation}</li>
                ))}
              </ul>
            </Alert>
          )}

          {/* Assignments Table */}
          <div className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden">
            <div className="p-4 border-b border-slate-800">
              <h2 className="text-lg font-semibold text-white">
                Staged Assignments ({preview?.assignments?.length || 0})
              </h2>
            </div>

            {isPreviewLoading ? (
              <div className="p-8 text-center text-slate-400">
                Loading assignments...
              </div>
            ) : preview?.assignments && preview.assignments.length > 0 ? (
              <div className="max-h-[500px] overflow-y-auto">
                <table className="w-full">
                  <thead className="bg-slate-800/50 sticky top-0">
                    <tr>
                      <th className="px-3 py-2 text-left text-xs font-medium text-slate-400 uppercase">
                        Type
                      </th>
                      <th className="px-3 py-2 text-left text-xs font-medium text-slate-400 uppercase">
                        Person
                      </th>
                      <th className="px-3 py-2 text-left text-xs font-medium text-slate-400 uppercase">
                        Date
                      </th>
                      <th className="px-3 py-2 text-left text-xs font-medium text-slate-400 uppercase">
                        Time
                      </th>
                      <th className="px-3 py-2 text-left text-xs font-medium text-slate-400 uppercase">
                        Activity
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {preview.assignments.map((assignment) => (
                      <AssignmentRow
                        key={assignment.id}
                        assignment={assignment}
                      />
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="p-8 text-center text-slate-500">
                No assignments in this draft
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
