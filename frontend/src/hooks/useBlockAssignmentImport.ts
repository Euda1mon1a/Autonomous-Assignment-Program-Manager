/**
 * Hook for block assignment import workflow.
 *
 * Manages:
 * - Multi-step wizard state (upload, preview, importing, complete)
 * - Preview data and row actions
 * - Template creation during import
 * - Import execution
 */
import { useState, useCallback } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  previewBlockAssignmentImport,
  previewBlockAssignmentImportFile,
  executeBlockAssignmentImport,
  quickCreateRotationTemplate,
  downloadImportTemplate,
  downloadBlob,
} from "@/api/block-assignment-import";
import {
  type BlockAssignmentPreviewResponse,
  type BlockAssignmentImportResult,
  type QuickTemplateCreateRequest,
  DuplicateAction,
} from "@/types/block-assignment-import";

export type ImportStep = "upload" | "preview" | "importing" | "complete";

export interface UseBlockAssignmentImportReturn {
  // State
  step: ImportStep;
  isLoading: boolean;
  error: string | null;
  preview: BlockAssignmentPreviewResponse | null;
  result: BlockAssignmentImportResult | null;
  duplicateActions: Record<number, DuplicateAction>;

  // Computed
  canImport: boolean;
  matchedCount: number;
  errorCount: number;

  // Actions
  uploadContent: (content: string, academicYear?: number) => Promise<void>;
  uploadFile: (file: File, academicYear?: number) => Promise<void>;
  setDuplicateAction: (rowNumber: number, action: DuplicateAction) => void;
  setAllDuplicateActions: (action: DuplicateAction) => void;
  createTemplate: (request: QuickTemplateCreateRequest) => Promise<void>;
  executeImport: (updateDuplicates?: boolean) => Promise<void>;
  downloadTemplate: () => Promise<void>;
  reset: () => void;
  goBack: () => void;
}

export function useBlockAssignmentImport(): UseBlockAssignmentImportReturn {
  const queryClient = useQueryClient();

  // State
  const [step, setStep] = useState<ImportStep>("upload");
  const [preview, setPreview] = useState<BlockAssignmentPreviewResponse | null>(
    null
  );
  const [result, setResult] = useState<BlockAssignmentImportResult | null>(
    null
  );
  const [duplicateActions, setDuplicateActions] = useState<
    Record<number, DuplicateAction>
  >({});
  const [error, setError] = useState<string | null>(null);

  // Preview mutation
  const previewMutation = useMutation({
    mutationFn: async ({
      content,
      file,
      academicYear,
    }: {
      content?: string;
      file?: File;
      academicYear?: number;
    }) => {
      if (file) {
        return previewBlockAssignmentImportFile(file, academicYear);
      }
      if (content) {
        return previewBlockAssignmentImport(content, academicYear);
      }
      throw new Error("Either content or file must be provided");
    },
    onSuccess: (data) => {
      setPreview(data);
      setStep("preview");
      setError(null);

      // Initialize duplicate actions
      const initialActions: Record<number, DuplicateAction> = {};
      data.items.forEach((item) => {
        if (item.isDuplicate) {
          initialActions[item.rowNumber] = DuplicateAction.SKIP;
        }
      });
      setDuplicateActions(initialActions);
    },
    onError: (err: Error) => {
      setError(err.message || "Failed to preview import");
    },
  });

  // Import mutation
  const importMutation = useMutation({
    mutationFn: async (updateDuplicates: boolean) => {
      if (!preview) throw new Error("No preview data");

      return executeBlockAssignmentImport({
        previewId: preview.previewId,
        academicYear: preview.academicYear,
        skipDuplicates: !updateDuplicates,
        updateDuplicates: updateDuplicates,
        rowOverrides: duplicateActions,
      });
    },
    onSuccess: (data) => {
      setResult(data);
      setStep("complete");
      setError(null);

      // Invalidate relevant queries
      queryClient.invalidateQueries({ queryKey: ["block-assignments"] });
      queryClient.invalidateQueries({ queryKey: ["block-scheduler"] });
    },
    onError: (err: Error) => {
      setError(err.message || "Failed to execute import");
    },
  });

  // Template creation mutation
  const templateMutation = useMutation({
    mutationFn: quickCreateRotationTemplate,
    onSuccess: () => {
      // Invalidate rotation templates query
      queryClient.invalidateQueries({ queryKey: ["rotation-templates"] });
    },
  });

  // Actions
  const uploadContent = useCallback(
    async (content: string, academicYear?: number) => {
      setError(null);
      await previewMutation.mutateAsync({ content, academicYear });
    },
    [previewMutation]
  );

  const uploadFile = useCallback(
    async (file: File, academicYear?: number) => {
      setError(null);
      await previewMutation.mutateAsync({ file, academicYear });
    },
    [previewMutation]
  );

  const setDuplicateAction = useCallback(
    (rowNumber: number, action: DuplicateAction) => {
      setDuplicateActions((prev) => ({
        ...prev,
        [rowNumber]: action,
      }));
    },
    []
  );

  const setAllDuplicateActions = useCallback(
    (action: DuplicateAction) => {
      if (!preview) return;

      const newActions: Record<number, DuplicateAction> = {};
      preview.items.forEach((item) => {
        if (item.isDuplicate) {
          newActions[item.rowNumber] = action;
        }
      });
      setDuplicateActions(newActions);
    },
    [preview]
  );

  const createTemplate = useCallback(
    async (request: QuickTemplateCreateRequest) => {
      await templateMutation.mutateAsync(request);
    },
    [templateMutation]
  );

  const executeImport = useCallback(
    async (updateDuplicates = false) => {
      setStep("importing");
      await importMutation.mutateAsync(updateDuplicates);
    },
    [importMutation]
  );

  const downloadTemplate = useCallback(async () => {
    const blob = await downloadImportTemplate();
    downloadBlob(blob, "block_assignments_template.csv");
  }, []);

  const reset = useCallback(() => {
    setStep("upload");
    setPreview(null);
    setResult(null);
    setDuplicateActions({});
    setError(null);
  }, []);

  const goBack = useCallback(() => {
    if (step === "preview") {
      setStep("upload");
      setPreview(null);
    } else if (step === "complete") {
      reset();
    }
  }, [step, reset]);

  // Computed values
  const matchedCount = preview?.matchedCount ?? 0;
  const errorCount =
    (preview?.unknownRotationCount ?? 0) +
    (preview?.unknownResidentCount ?? 0) +
    (preview?.invalidCount ?? 0);

  const canImport =
    preview !== null &&
    matchedCount > 0 &&
    preview.unknownRotationCount === 0 &&
    preview.unknownResidentCount === 0 &&
    preview.invalidCount === 0;

  return {
    // State
    step,
    isLoading: previewMutation.isPending || importMutation.isPending,
    error,
    preview,
    result,
    duplicateActions,

    // Computed
    canImport,
    matchedCount,
    errorCount,

    // Actions
    uploadContent,
    uploadFile,
    setDuplicateAction,
    setAllDuplicateActions,
    createTemplate,
    executeImport,
    downloadTemplate,
    reset,
    goBack,
  };
}
