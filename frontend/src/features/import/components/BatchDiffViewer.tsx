import type {
  ImportConflictDetail,
  StagedAssignmentResponse,
} from "@/types/import";
import { StagedAssignmentStatus } from "@/types/import";
import { AlertTriangle, ArrowRight, Check, Copy, X } from "lucide-react";
import { useMemo } from "react";

interface BatchDiffViewerProps {
  assignments: StagedAssignmentResponse[];
  conflicts: ImportConflictDetail[];
  isLoading: boolean;
}

export function BatchDiffViewer({
  assignments,
  conflicts,
  isLoading,
}: BatchDiffViewerProps) {
  // Create a quick lookup for conflicts by staged ID
  const conflictMap = useMemo(() => {
    const map = new Map<string, ImportConflictDetail>();
    conflicts.forEach((c) => map.set(c.staged_assignment_id, c));
    return map;
  }, [conflicts]);

  if (isLoading) {
    return (
      <div className="h-96 w-full bg-slate-800/30 rounded-xl animate-pulse" />
    );
  }

  return (
    <div className="space-y-4">
      <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900/50">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-800/50 text-slate-400 uppercase text-xs">
            <tr>
              <th className="px-4 py-3 font-medium w-12">#</th>
              <th className="px-4 py-3 font-medium">Person</th>
              <th className="px-4 py-3 font-medium">Date</th>
              <th className="px-4 py-3 font-medium">Change</th>
              <th className="px-4 py-3 font-medium w-24 text-center">Type</th>
              <th className="px-4 py-3 font-medium w-24 text-center">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {assignments.map((assignment) => {
              const conflict = conflictMap.get(assignment.id);
              const isOverwrite = conflict?.conflict_type === "overwrite";
              const isDuplicate = conflict?.conflict_type === "duplicate";
              const isNew = !conflict;

              return (
                <tr
                  key={assignment.id}
                  className={`
                    transition-colors
                    ${
                      isOverwrite
                        ? "bg-orange-500/5 hover:bg-orange-500/10"
                        : ""
                    }
                    ${
                      isDuplicate
                        ? "bg-yellow-500/5 hover:bg-yellow-500/10"
                        : ""
                    }
                    ${isNew ? "hover:bg-slate-800/30" : ""}
                  `}
                >
                  <td className="px-4 py-3 text-slate-500 text-xs font-mono">
                    {assignment.row_number}
                  </td>
                  <td className="px-4 py-3 font-medium text-white">
                    {assignment.person_name}
                    {assignment.matched_person_name &&
                      assignment.matched_person_name !==
                        assignment.person_name && (
                        <div className="text-xs text-slate-500 flex items-center gap-1 mt-0.5">
                          <ArrowRight className="w-3 h-3" />
                          Matched: {assignment.matched_person_name}
                        </div>
                      )}
                  </td>
                  <td className="px-4 py-3 text-slate-300">
                    {assignment.assignment_date}
                    {assignment.slot && (
                      <span className="ml-2 text-xs bg-slate-800 px-1.5 py-0.5 rounded text-slate-400">
                        {assignment.slot}
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-3">
                      {isOverwrite && conflict?.existing_rotation ? (
                        <>
                          <span className="text-red-400 line-through decoration-red-500/50">
                            {conflict.existing_rotation}
                          </span>
                          <ArrowRight className="w-4 h-4 text-slate-600" />
                          <span className="text-green-400 font-medium">
                            {assignment.rotation_name}
                          </span>
                        </>
                      ) : (
                        <span className="text-green-400 font-medium">
                          {assignment.rotation_name}
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-center">
                    {isOverwrite && (
                      <div
                        className="flex justify-center"
                        title="Overwrite Existing"
                      >
                        <AlertTriangle className="w-4 h-4 text-orange-400" />
                      </div>
                    )}
                    {isDuplicate && (
                      <div
                        className="flex justify-center"
                        title="Exact Duplicate (No Change)"
                      >
                        <Copy className="w-4 h-4 text-slate-500" />
                      </div>
                    )}
                    {isNew && (
                      <div
                        className="flex justify-center"
                        title="New Assignment"
                      >
                        <div className="w-2 h-2 rounded-full bg-green-500" />
                      </div>
                    )}
                  </td>
                  <td className="px-4 py-3 text-center">
                    {assignment.status === StagedAssignmentStatus.APPROVED && (
                      <Check className="w-4 h-4 text-green-500 mx-auto" />
                    )}
                    {assignment.status === StagedAssignmentStatus.SKIPPED && (
                      <X className="w-4 h-4 text-slate-500 mx-auto" />
                    )}
                    {assignment.status === StagedAssignmentStatus.PENDING && (
                      <div className="w-2 h-2 rounded-full border border-slate-500 mx-auto" />
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Legend */}
      <div className="flex gap-6 justify-end text-xs text-slate-500 px-2">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-green-500" />
          <span>New</span>
        </div>
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-3 h-3 text-orange-400" />
          <span>Overwrite</span>
        </div>
        <div className="flex items-center gap-2">
          <Copy className="w-3 h-3 text-slate-500" />
          <span>Duplicate (No Action)</span>
        </div>
      </div>
    </div>
  );
}
