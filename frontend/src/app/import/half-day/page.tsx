"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  CheckCircle2,
  FileSpreadsheet,
  Filter,
  Loader2,
  Play,
  Plus,
  Upload,
  XCircle,
} from "lucide-react";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { useToast } from "@/contexts/ToastContext";
import {
  useCreateHalfDayDraft,
  useHalfDayImportPreview,
  useStageHalfDayImport,
} from "@/hooks/useHalfDayImport";
import type {
  HalfDayDiffEntry,
  HalfDayDiffType,
  HalfDayDraftErrorDetail,
  HalfDayImportDraftResponse,
  HalfDayPreviewFilters,
} from "@/types/half-day-import";

const PAGE_SIZE = 50;

const DIFF_TYPE_OPTIONS: Array<{
  label: string;
  value: "all" | HalfDayDiffType;
}> = [
  { label: "All", value: "all" },
  { label: "Added", value: "added" },
  { label: "Removed", value: "removed" },
  { label: "Modified", value: "modified" },
];

const ERROR_FILTER_OPTIONS = [
  { label: "All", value: "all" },
  { label: "With Errors", value: "with" },
  { label: "Without Errors", value: "without" },
];

function isValidUuid(value: string) {
  return /^[0-9a-fA-F-]{36}$/.test(value);
}

function getDiffBadge(diffType: HalfDayDiffType) {
  switch (diffType) {
    case "added":
      return "bg-green-500/20 text-green-300 border border-green-500/30";
    case "removed":
      return "bg-red-500/20 text-red-300 border border-red-500/30";
    case "modified":
      return "bg-blue-500/20 text-blue-300 border border-blue-500/30";
    default:
      return "bg-slate-700/40 text-slate-300 border border-slate-700/60";
  }
}

function parseDraftError(error: unknown): HalfDayDraftErrorDetail | null {
  if (!error || typeof error !== "object") return null;

  const detail = (error as { detail?: unknown }).detail;
  if (detail && typeof detail === "object") {
    const message = (detail as { message?: unknown }).message;
    const errorCode = (detail as { errorCode?: unknown }).errorCode;
    const failedIds = (detail as { failedIds?: unknown }).failedIds;
    return {
      message:
        typeof message === "string" ? message : "Draft creation failed",
      errorCode: typeof errorCode === "string" ? errorCode : undefined,
      failedIds: Array.isArray(failedIds)
        ? failedIds.map((id) => String(id))
        : undefined,
    };
  }

  const message = (error as { message?: unknown }).message;
  if (typeof message === "string") {
    return { message };
  }

  return null;
}

export default function HalfDayImportPage() {
  const router = useRouter();
  const { toast } = useToast();

  const [step, setStep] = useState<"upload" | "preview" | "draft">("upload");
  const [batchId, setBatchId] = useState<string | null>(null);
  const [stageWarnings, setStageWarnings] = useState<string[]>([]);

  const [file, setFile] = useState<File | null>(null);
  const [blockNumber, setBlockNumber] = useState<string>("10");
  const [academicYear, setAcademicYear] = useState<string>(
    String(new Date().getFullYear())
  );
  const [notes, setNotes] = useState<string>("");

  const [draftNotes, setDraftNotes] = useState<string>("");
  const [draftResult, setDraftResult] = useState<
    HalfDayImportDraftResponse | null
  >(null);
  const [draftError, setDraftError] = useState<HalfDayDraftErrorDetail | null>(
    null
  );

  const [page, setPage] = useState(1);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [diffTypeFilter, setDiffTypeFilter] = useState<
    "all" | HalfDayDiffType
  >("all");
  const [activityCodeFilter, setActivityCodeFilter] = useState<string>("");
  const [errorFilter, setErrorFilter] = useState<
    "all" | "with" | "without"
  >("all");
  const [personIdFilter, setPersonIdFilter] = useState<string>("");

  const stageMutation = useStageHalfDayImport();
  const draftMutation = useCreateHalfDayDraft();

  const previewFilters: HalfDayPreviewFilters = useMemo(() => {
    const filters: HalfDayPreviewFilters = {};
    if (diffTypeFilter !== "all") {
      filters.diffType = diffTypeFilter;
    }
    if (activityCodeFilter.trim()) {
      filters.activityCode = activityCodeFilter.trim();
    }
    if (errorFilter === "with") {
      filters.hasErrors = true;
    }
    if (errorFilter === "without") {
      filters.hasErrors = false;
    }
    if (personIdFilter.trim() && isValidUuid(personIdFilter.trim())) {
      filters.personId = personIdFilter.trim();
    }
    return filters;
  }, [activityCodeFilter, diffTypeFilter, errorFilter, personIdFilter]);

  const previewQuery = useHalfDayImportPreview(
    batchId,
    page,
    PAGE_SIZE,
    previewFilters
  );

  const previewData = previewQuery.data;
  const diffs = previewData?.diffs ?? [];
  const totalDiffs = previewData?.totalDiffs ?? 0;
  const totalPages = Math.max(1, Math.ceil(totalDiffs / PAGE_SIZE));

  const selectedCount = selectedIds.size;
  const selectableOnPage = diffs.filter(
    (diff) => diff.stagedId && diff.errors.length === 0
  );
  const selectableIdsOnPage = selectableOnPage
    .map((diff) => diff.stagedId)
    .filter((id): id is string => Boolean(id));

  const failedIdSet = useMemo(() => {
    if (!draftError?.failedIds) return new Set<string>();
    return new Set(draftError.failedIds);
  }, [draftError]);

  useEffect(() => {
    setSelectedIds(new Set());
    setPage(1);
    setDraftError(null);
    setDraftResult(null);
  }, [batchId]);

  useEffect(() => {
    setPage(1);
  }, [diffTypeFilter, activityCodeFilter, errorFilter, personIdFilter]);

  const toggleSelected = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const handleSelectPage = () => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      selectableIdsOnPage.forEach((id) => next.add(id));
      return next;
    });
  };

  const handleClearSelection = () => {
    setSelectedIds(new Set());
  };

  const handleStage = async () => {
    if (!file) {
      toast.error("Select a Block Template2 Excel file first.");
      return;
    }

    const blockValue = Number(blockNumber);
    const yearValue = Number(academicYear);

    if (!blockValue || blockValue < 1 || blockValue > 26) {
      toast.error("Block number must be between 1 and 26.");
      return;
    }

    if (!yearValue || yearValue < 2000) {
      toast.error("Academic year must be a valid year.");
      return;
    }

    try {
      const result = await stageMutation.mutateAsync({
        file,
        blockNumber: blockValue,
        academicYear: yearValue,
        notes: notes.trim() || undefined,
      });

      if (!result.batchId) {
        toast.error("Staging completed but batch ID is missing.");
        return;
      }

      setBatchId(result.batchId);
      setStageWarnings(result.warnings || []);
      setStep("preview");
    } catch (error) {
      toast.error(error);
    }
  };

  const handleCreateDraft = async () => {
    if (!batchId) return;
    if (selectedIds.size === 0) {
      toast.warning("Select at least one diff row to draft.");
      return;
    }

    try {
      const result = await draftMutation.mutateAsync({
        batchId,
        payload: {
          stagedIds: Array.from(selectedIds),
          notes: draftNotes.trim() || undefined,
        },
      });
      setDraftResult(result);
      setDraftError(null);
      setStep("draft");
    } catch (error) {
      const parsed = parseDraftError(error);
      if (parsed) {
        setDraftError(parsed);
        toast.error(parsed.message);
      } else {
        toast.error(error);
      }
    }
  };

  const metrics = previewData?.metrics;

  const renderDiffRow = (diff: HalfDayDiffEntry, index: number) => {
    const hasErrors = diff.errors.length > 0;
    const stagedId = diff.stagedId ?? "";
    const isSelected = stagedId ? selectedIds.has(stagedId) : false;
    const isFailed = stagedId ? failedIdSet.has(stagedId) : false;

    return (
      <tr
        key={`${stagedId}-${index}`}
        className={`border-b border-slate-800/70 ${
          hasErrors ? "bg-red-950/20" : "bg-slate-900/40"
        } ${isFailed ? "ring-1 ring-red-500/40" : ""}`}
      >
        <td className="px-4 py-3">
          <input
            type="checkbox"
            className="h-4 w-4 rounded border-slate-600 bg-slate-900 text-blue-500 disabled:opacity-50"
            disabled={!stagedId || hasErrors}
            checked={isSelected}
            onChange={() => stagedId && toggleSelected(stagedId)}
          />
        </td>
        <td className="px-4 py-3 text-sm text-slate-200">
          <div className="font-medium text-white">{diff.personName}</div>
          {diff.personId && (
            <div className="text-xs text-slate-500">{diff.personId}</div>
          )}
        </td>
        <td className="px-4 py-3 text-sm text-slate-300">
          <div>{diff.assignmentDate}</div>
          <div className="text-xs text-slate-500">{diff.timeOfDay}</div>
        </td>
        <td className="px-4 py-3 text-sm">
          <span
            className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-semibold ${getDiffBadge(
              diff.diffType
            )}`}
          >
            {diff.diffType}
          </span>
        </td>
        <td className="px-4 py-3 text-sm text-slate-200">
          <div className="text-slate-500 text-xs">Excel</div>
          <div className="font-medium text-emerald-300">
            {diff.excelValue || "—"}
          </div>
        </td>
        <td className="px-4 py-3 text-sm text-slate-200">
          <div className="text-slate-500 text-xs">Current</div>
          <div className="font-medium text-slate-100">
            {diff.currentValue || "—"}
          </div>
        </td>
        <td className="px-4 py-3 text-xs text-slate-400">
          {diff.warnings.length > 0 && (
            <div className="mb-2">
              <div className="text-amber-300 font-semibold uppercase text-[10px]">
                Warnings
              </div>
              <ul className="space-y-1">
                {diff.warnings.map((warning, warningIndex) => (
                  <li key={warningIndex}>• {warning}</li>
                ))}
              </ul>
            </div>
          )}
          {diff.errors.length > 0 && (
            <div>
              <div className="text-red-300 font-semibold uppercase text-[10px]">
                Errors
              </div>
              <ul className="space-y-1">
                {diff.errors.map((error, errorIndex) => (
                  <li key={errorIndex}>• {error}</li>
                ))}
              </ul>
            </div>
          )}
          {diff.errors.length === 0 && diff.warnings.length === 0 && (
            <span className="text-slate-600">—</span>
          )}
        </td>
      </tr>
    );
  };

  return (
    <ProtectedRoute requireAdmin>
      <div className="min-h-screen bg-slate-950 text-slate-200 p-8">
        <div className="max-w-7xl mx-auto space-y-8">
          <button
            onClick={() => router.push("/import")}
            className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors text-sm"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Imports
          </button>

          <div className="flex flex-col gap-4">
            <div className="flex items-start justify-between gap-6">
              <div>
                <h1 className="text-3xl font-bold text-white">
                  Half-Day Excel Import
                </h1>
                <p className="text-slate-400 mt-2 max-w-2xl">
                  Stage Block Template2 half-day schedules, review slot-level
                  diffs, and draft changes with full rollback protection.
                </p>
              </div>
              <div className="flex items-center gap-2">
                <span
                  className={`px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wide ${
                    step === "upload"
                      ? "bg-blue-500/20 text-blue-300 border border-blue-500/30"
                      : "bg-slate-800 text-slate-400 border border-slate-700"
                  }`}
                >
                  1. Upload
                </span>
                <span
                  className={`px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wide ${
                    step === "preview"
                      ? "bg-blue-500/20 text-blue-300 border border-blue-500/30"
                      : "bg-slate-800 text-slate-400 border border-slate-700"
                  }`}
                >
                  2. Preview
                </span>
                <span
                  className={`px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wide ${
                    step === "draft"
                      ? "bg-blue-500/20 text-blue-300 border border-blue-500/30"
                      : "bg-slate-800 text-slate-400 border border-slate-700"
                  }`}
                >
                  3. Draft
                </span>
              </div>
            </div>
          </div>

          {step === "upload" && (
            <div className="grid grid-cols-1 lg:grid-cols-[2fr_1fr] gap-6">
              <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-6">
                <div className="flex items-center gap-3">
                  <FileSpreadsheet className="w-5 h-5 text-blue-400" />
                  <h2 className="text-xl font-semibold text-white">
                    Block Template2 Upload
                  </h2>
                </div>

                <div className="space-y-4">
                  <label className="flex flex-col gap-2 text-sm text-slate-300">
                    Excel file
                    <input
                      type="file"
                      accept=".xlsx,.xls"
                      onChange={(event) =>
                        setFile(event.target.files?.[0] ?? null)
                      }
                      className="block w-full text-sm text-slate-300 file:mr-4 file:rounded-lg file:border-0 file:bg-blue-600 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-white hover:file:bg-blue-500"
                    />
                  </label>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <label className="flex flex-col gap-2 text-sm text-slate-300">
                      Block number
                      <input
                        type="number"
                        min={1}
                        max={26}
                        value={blockNumber}
                        onChange={(event) => setBlockNumber(event.target.value)}
                        className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </label>
                    <label className="flex flex-col gap-2 text-sm text-slate-300">
                      Academic year
                      <input
                        type="number"
                        min={2000}
                        value={academicYear}
                        onChange={(event) =>
                          setAcademicYear(event.target.value)
                        }
                        className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </label>
                  </div>

                  <label className="flex flex-col gap-2 text-sm text-slate-300">
                    Notes (optional)
                    <textarea
                      value={notes}
                      onChange={(event) => setNotes(event.target.value)}
                      className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[90px]"
                      placeholder="Block 10 Template2 import"
                    />
                  </label>
                </div>

                <div className="flex items-center gap-3">
                  <button
                    onClick={handleStage}
                    disabled={stageMutation.isPending}
                    className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg font-medium transition-colors disabled:opacity-60"
                  >
                    {stageMutation.isPending ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Upload className="w-4 h-4" />
                    )}
                    Stage diff preview
                  </button>
                  {stageMutation.isPending && (
                    <span className="text-xs text-slate-400">
                      Parsing Excel…
                    </span>
                  )}
                </div>
              </div>

              <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4">
                <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
                  Checklist
                </h3>
                <ul className="text-sm text-slate-300 space-y-3">
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-green-400 mt-0.5" />
                    Ensure the Block Template2 sheet is populated for the target
                    block.
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-green-400 mt-0.5" />
                    Verify activity codes match configured Activity templates.
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-green-400 mt-0.5" />
                    Use preview filters to isolate issues before drafting.
                  </li>
                </ul>
              </div>
            </div>
          )}

          {step === "preview" && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-[2fr_1fr] gap-6">
                <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-6">
                  <div className="flex flex-wrap items-center justify-between gap-4">
                    <div>
                      <h2 className="text-xl font-semibold text-white">
                        Diff Preview
                      </h2>
                      <p className="text-sm text-slate-400">
                        Filter, review, and select rows to draft.
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        className="px-3 py-2 rounded-lg border border-slate-700 text-slate-200 text-xs hover:border-slate-500"
                        onClick={handleSelectPage}
                      >
                        Select page
                      </button>
                      <button
                        className="px-3 py-2 rounded-lg border border-slate-700 text-slate-400 text-xs hover:border-slate-500"
                        onClick={handleClearSelection}
                      >
                        Clear selection
                      </button>
                    </div>
                  </div>

                  {stageWarnings.length > 0 && (
                    <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-4 text-sm text-amber-200">
                      <div className="font-semibold uppercase text-[11px] text-amber-300">
                        Stage warnings
                      </div>
                      <ul className="mt-2 space-y-1">
                        {stageWarnings.map((warning, index) => (
                          <li key={index}>• {warning}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {draftError && (
                    <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 text-sm text-red-200">
                      <div className="font-semibold uppercase text-[11px] text-red-300">
                        Draft blocked
                      </div>
                      <p className="mt-2">{draftError.message}</p>
                      {draftError.failedIds && draftError.failedIds.length > 0 && (
                        <p className="mt-2 text-xs text-red-300">
                          Failed rows: {draftError.failedIds.length}
                        </p>
                      )}
                    </div>
                  )}
                  {previewQuery.isError && (
                    <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 text-sm text-red-200">
                      <div className="font-semibold uppercase text-[11px] text-red-300">
                        Preview failed
                      </div>
                      <p className="mt-2">
                        {previewQuery.error?.message ||
                          "Unable to load preview data."}
                      </p>
                    </div>
                  )}

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    <div className="bg-slate-950/60 border border-slate-800 rounded-lg p-3">
                      <div className="text-xs uppercase text-slate-500">
                        Total slots
                      </div>
                      <div className="text-lg font-semibold text-white">
                        {metrics?.totalSlots ?? 0}
                      </div>
                    </div>
                    <div className="bg-slate-950/60 border border-slate-800 rounded-lg p-3">
                      <div className="text-xs uppercase text-slate-500">
                        Changed slots
                      </div>
                      <div className="text-lg font-semibold text-blue-300">
                        {metrics?.changedSlots ?? 0}
                      </div>
                    </div>
                    <div className="bg-slate-950/60 border border-slate-800 rounded-lg p-3">
                      <div className="text-xs uppercase text-slate-500">
                        Added / Removed
                      </div>
                      <div className="text-lg font-semibold text-emerald-300">
                        {(metrics?.added ?? 0) + (metrics?.removed ?? 0)}
                      </div>
                    </div>
                    <div className="bg-slate-950/60 border border-slate-800 rounded-lg p-3">
                      <div className="text-xs uppercase text-slate-500">
                        Manual hours
                      </div>
                      <div className="text-lg font-semibold text-white">
                        {metrics?.manualHours ?? 0}
                      </div>
                    </div>
                  </div>

                  <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-4 space-y-4">
                    <div className="flex items-center gap-2 text-sm font-semibold text-slate-200">
                      <Filter className="w-4 h-4" />
                      Filters
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
                      <label className="text-xs text-slate-400">
                        Diff type
                        <select
                          value={diffTypeFilter}
                          onChange={(event) =>
                            setDiffTypeFilter(
                              event.target.value as "all" | HalfDayDiffType
                            )
                          }
                          className="mt-2 w-full bg-slate-900 border border-slate-700 rounded-lg px-2 py-2 text-slate-200 text-sm"
                        >
                          {DIFF_TYPE_OPTIONS.map((option) => (
                            <option key={option.value} value={option.value}>
                              {option.label}
                            </option>
                          ))}
                        </select>
                      </label>
                      <label className="text-xs text-slate-400">
                        Activity code
                        <input
                          value={activityCodeFilter}
                          onChange={(event) =>
                            setActivityCodeFilter(event.target.value)
                          }
                          placeholder="FMIT"
                          className="mt-2 w-full bg-slate-900 border border-slate-700 rounded-lg px-2 py-2 text-slate-200 text-sm"
                        />
                      </label>
                      <label className="text-xs text-slate-400">
                        Errors
                        <select
                          value={errorFilter}
                          onChange={(event) =>
                            setErrorFilter(
                              event.target.value as "all" | "with" | "without"
                            )
                          }
                          className="mt-2 w-full bg-slate-900 border border-slate-700 rounded-lg px-2 py-2 text-slate-200 text-sm"
                        >
                          {ERROR_FILTER_OPTIONS.map((option) => (
                            <option key={option.value} value={option.value}>
                              {option.label}
                            </option>
                          ))}
                        </select>
                      </label>
                      <label className="text-xs text-slate-400">
                        Person ID
                        <input
                          value={personIdFilter}
                          onChange={(event) =>
                            setPersonIdFilter(event.target.value)
                          }
                          placeholder="UUID"
                          className="mt-2 w-full bg-slate-900 border border-slate-700 rounded-lg px-2 py-2 text-slate-200 text-sm"
                        />
                      </label>
                    </div>
                  </div>

                  <div className="overflow-hidden rounded-xl border border-slate-800">
                    <table className="w-full text-left text-sm">
                      <thead className="bg-slate-900 text-slate-400 text-xs uppercase">
                        <tr>
                          <th className="px-4 py-3">Select</th>
                          <th className="px-4 py-3">Person</th>
                          <th className="px-4 py-3">Date</th>
                          <th className="px-4 py-3">Change</th>
                          <th className="px-4 py-3">Excel</th>
                          <th className="px-4 py-3">Current</th>
                          <th className="px-4 py-3">Validation</th>
                        </tr>
                      </thead>
                      <tbody>
                        {previewQuery.isLoading && (
                          <tr>
                            <td colSpan={7} className="px-4 py-10 text-center">
                              <Loader2 className="w-5 h-5 animate-spin text-blue-400 mx-auto" />
                            </td>
                          </tr>
                        )}
                        {!previewQuery.isLoading && diffs.length === 0 && (
                          <tr>
                            <td colSpan={7} className="px-4 py-10 text-center text-slate-500">
                              No diffs found with the current filters.
                            </td>
                          </tr>
                        )}
                        {diffs.map(renderDiffRow)}
                      </tbody>
                    </table>
                  </div>

                  <div className="flex flex-wrap items-center justify-between gap-3 text-sm text-slate-400">
                    <div>
                      Selected <span className="text-white">{selectedCount}</span> of {totalDiffs}
                    </div>
                    <div className="flex items-center gap-3">
                      <button
                        className="px-3 py-1.5 border border-slate-700 rounded-lg text-slate-300 disabled:opacity-50"
                        disabled={page <= 1}
                        onClick={() => setPage((prev) => Math.max(1, prev - 1))}
                      >
                        Previous
                      </button>
                      <span>
                        Page {page} of {totalPages}
                      </span>
                      <button
                        className="px-3 py-1.5 border border-slate-700 rounded-lg text-slate-300 disabled:opacity-50"
                        disabled={page >= totalPages}
                        onClick={() => setPage((prev) => Math.min(totalPages, prev + 1))}
                      >
                        Next
                      </button>
                    </div>
                  </div>
                </div>

                <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-5">
                  <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
                    Draft controls
                  </h3>
                  <div className="text-sm text-slate-300">
                    Only rows without validation errors can be drafted. Rows with
                    errors are blocked and must be fixed in Excel.
                  </div>

                  <label className="text-xs text-slate-400">
                    Draft notes (optional)
                    <textarea
                      value={draftNotes}
                      onChange={(event) => setDraftNotes(event.target.value)}
                      className="mt-2 w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-100 min-h-[90px]"
                    />
                  </label>

                  <button
                    onClick={handleCreateDraft}
                    disabled={draftMutation.isPending}
                    className="w-full inline-flex items-center justify-center gap-2 bg-green-600 hover:bg-green-500 text-white px-4 py-2 rounded-lg font-medium transition-colors disabled:opacity-60"
                  >
                    {draftMutation.isPending ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Play className="w-4 h-4" />
                    )}
                    Create draft from selection
                  </button>

                  <button
                    onClick={() => setStep("upload")}
                    className="w-full inline-flex items-center justify-center gap-2 border border-slate-700 text-slate-300 px-4 py-2 rounded-lg font-medium hover:border-slate-500"
                  >
                    <Plus className="w-4 h-4" />
                    Start new upload
                  </button>
                </div>
              </div>
            </div>
          )}

          {step === "draft" && draftResult && (
            <div className="grid grid-cols-1 lg:grid-cols-[2fr_1fr] gap-6">
              <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-6">
                <div className="flex items-center gap-3">
                  <CheckCircle2 className="w-6 h-6 text-green-400" />
                  <div>
                    <h2 className="text-xl font-semibold text-white">
                      Draft created
                    </h2>
                    <p className="text-sm text-slate-400">
                      {draftResult.message}
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  <div className="bg-slate-950/60 border border-slate-800 rounded-lg p-4">
                    <div className="text-xs uppercase text-slate-500">Added</div>
                    <div className="text-lg font-semibold text-emerald-300">
                      {draftResult.added}
                    </div>
                  </div>
                  <div className="bg-slate-950/60 border border-slate-800 rounded-lg p-4">
                    <div className="text-xs uppercase text-slate-500">Modified</div>
                    <div className="text-lg font-semibold text-blue-300">
                      {draftResult.modified}
                    </div>
                  </div>
                  <div className="bg-slate-950/60 border border-slate-800 rounded-lg p-4">
                    <div className="text-xs uppercase text-slate-500">Removed</div>
                    <div className="text-lg font-semibold text-red-300">
                      {draftResult.removed}
                    </div>
                  </div>
                  <div className="bg-slate-950/60 border border-slate-800 rounded-lg p-4">
                    <div className="text-xs uppercase text-slate-500">Skipped</div>
                    <div className="text-lg font-semibold text-slate-200">
                      {draftResult.skipped}
                    </div>
                  </div>
                  <div className="bg-slate-950/60 border border-slate-800 rounded-lg p-4">
                    <div className="text-xs uppercase text-slate-500">Failed</div>
                    <div className="text-lg font-semibold text-red-300">
                      {draftResult.failed}
                    </div>
                  </div>
                  <div className="bg-slate-950/60 border border-slate-800 rounded-lg p-4">
                    <div className="text-xs uppercase text-slate-500">Total</div>
                    <div className="text-lg font-semibold text-white">
                      {draftResult.totalSelected}
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4">
                <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
                  Next steps
                </h3>
                <p className="text-sm text-slate-300">
                  Review the draft for accuracy, then publish or rollback in the
                  draft manager.
                </p>
                <button
                  onClick={() =>
                    draftResult.draftId &&
                    router.push(`/admin/schedule-drafts/${draftResult.draftId}`)
                  }
                  disabled={!draftResult.draftId}
                  className="w-full inline-flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg font-medium transition-colors disabled:opacity-60"
                >
                  View draft
                </button>
                <button
                  onClick={() => setStep("preview")}
                  className="w-full inline-flex items-center justify-center gap-2 border border-slate-700 text-slate-300 px-4 py-2 rounded-lg font-medium hover:border-slate-500"
                >
                  Back to preview
                </button>
              </div>
            </div>
          )}

          {step === "draft" && !draftResult && (
            <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 text-slate-300">
              <div className="flex items-center gap-2">
                <XCircle className="w-5 h-5 text-red-400" />
                Draft creation did not complete. Return to preview to try again.
              </div>
            </div>
          )}
        </div>
      </div>
    </ProtectedRoute>
  );
}
