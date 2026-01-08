'use client';

/**
 * TemplatePatternModal - Modal wrapper for WeeklyGridEditor.
 *
 * Provides a complete editing experience for rotation template weekly patterns:
 * - Loads pattern data from API
 * - Displays WeeklyGridEditor
 * - Handles save/cancel with API integration
 * - Shows loading and error states
 */

import { useState, useEffect, useCallback } from 'react';
import { X, Loader2, AlertCircle, CheckCircle } from 'lucide-react';
import { Modal } from '@/components/Modal';
import { WeeklyGridEditor } from '@/components/WeeklyGridEditor';
import {
  useWeeklyPattern,
  useUpdateWeeklyPattern,
  useAvailableTemplates,
} from '@/hooks/useWeeklyPattern';
import type { WeeklyPatternGrid } from '@/types/weekly-pattern';
import { createEmptyPattern } from '@/types/weekly-pattern';

// ============================================================================
// Types
// ============================================================================

interface TemplatePatternModalProps {
  /** Whether the modal is open */
  isOpen: boolean;
  /** Callback when modal should close */
  onClose: () => void;
  /** ID of the template to edit */
  templateId: string;
  /** Name of the template (for display) */
  templateName: string;
  /** Callback when pattern is successfully saved */
  onSaved?: () => void;
}

// ============================================================================
// Component
// ============================================================================

export function TemplatePatternModal({
  isOpen,
  onClose,
  templateId,
  templateName,
  onSaved,
}: TemplatePatternModalProps) {
  // Local pattern state for editing
  const [localPattern, setLocalPattern] = useState<WeeklyPatternGrid | null>(null);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'success' | 'error'>('idle');

  // Fetch current pattern
  const {
    data: patternData,
    isLoading: isPatternLoading,
    error: patternError,
    refetch: refetchPattern,
  } = useWeeklyPattern(templateId, {
    enabled: isOpen && !!templateId,
  });

  // Fetch available templates for selector
  const {
    data: templates = [],
    isLoading: isTemplatesLoading,
  } = useAvailableTemplates({
    enabled: isOpen,
  });

  // Update mutation
  const updateMutation = useUpdateWeeklyPattern();

  // Initialize local state when pattern loads
  useEffect(() => {
    if (patternData) {
      setLocalPattern(patternData.pattern);
    }
  }, [patternData]);

  // Reset state when modal opens/closes
  useEffect(() => {
    if (!isOpen) {
      setLocalPattern(null);
      setSaveStatus('idle');
    }
  }, [isOpen]);

  // Handle pattern change
  const handlePatternChange = useCallback((pattern: WeeklyPatternGrid) => {
    setLocalPattern(pattern);
    setSaveStatus('idle');
  }, []);

  // Handle save
  const handleSave = useCallback(async () => {
    if (!localPattern) return;

    try {
      await updateMutation.mutateAsync({
        templateId,
        pattern: localPattern,
      });
      setSaveStatus('success');
      onSaved?.();

      // Close after short delay to show success
      setTimeout(() => {
        onClose();
      }, 500);
    } catch (error) {
      setSaveStatus('error');
      console.error('Failed to save pattern:', error);
    }
  }, [templateId, localPattern, updateMutation, onSaved, onClose]);

  // Handle cancel
  const handleCancel = useCallback(() => {
    // Reset to original pattern
    if (patternData) {
      setLocalPattern(patternData.pattern);
    }
    setSaveStatus('idle');
    onClose();
  }, [patternData, onClose]);

  // Handle retry on error
  const handleRetry = useCallback(() => {
    refetchPattern();
    setSaveStatus('idle');
  }, [refetchPattern]);

  const isLoading = isPatternLoading || isTemplatesLoading;
  const isSaving = updateMutation.isPending;

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50"
        onClick={handleCancel}
        aria-hidden="true"
      />

      {/* Modal Content */}
      <div className="relative bg-white rounded-lg shadow-xl w-full max-w-3xl mx-4 max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <div>
            <h2 className="text-lg font-semibold">Edit Weekly Pattern</h2>
            <p className="text-sm text-gray-500">{templateName}</p>
          </div>
          <button
            onClick={handleCancel}
            className="p-1 hover:bg-gray-100 rounded"
            aria-label="Close modal"
            disabled={isSaving}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-4 overflow-y-auto max-h-[calc(90vh-8rem)]">
          {/* Loading State */}
          {isLoading && (
            <div className="flex flex-col items-center justify-center h-48">
              <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
              <p className="mt-2 text-sm text-gray-500">Loading pattern...</p>
            </div>
          )}

          {/* Error State */}
          {patternError && !isLoading && (
            <div className="flex flex-col items-center justify-center h-48">
              <AlertCircle className="w-8 h-8 text-red-500" />
              <p className="mt-2 text-sm text-red-600">
                Failed to load pattern: {patternError.message}
              </p>
              <button
                onClick={handleRetry}
                className="mt-4 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
              >
                Retry
              </button>
            </div>
          )}

          {/* Success State (brief) */}
          {saveStatus === 'success' && (
            <div className="flex flex-col items-center justify-center h-48">
              <CheckCircle className="w-8 h-8 text-green-500" />
              <p className="mt-2 text-sm text-green-600">Pattern saved!</p>
            </div>
          )}

          {/* Save Error State */}
          {saveStatus === 'error' && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
              <div className="flex items-center">
                <AlertCircle className="w-5 h-5 text-red-500 mr-2" />
                <p className="text-sm text-red-700">
                  Failed to save pattern. Please try again.
                </p>
              </div>
            </div>
          )}

          {/* Editor */}
          {!isLoading && !patternError && localPattern && saveStatus !== 'success' && (
            <WeeklyGridEditor
              templateId={templateId}
              pattern={localPattern}
              templates={templates}
              isLoading={false}
              isSaving={isSaving}
              onChange={handlePatternChange}
              onSave={handleSave}
              onCancel={handleCancel}
              showSelector={true}
              readOnly={false}
              showWeekTabs={true}
            />
          )}
        </div>

        {/* Instructions */}
        {!isLoading && !patternError && saveStatus !== 'success' && (
          <div className="px-4 py-3 bg-gray-50 border-t text-xs text-gray-500">
            <p>
              <strong>How to use:</strong> Select a rotation type, then click cells to assign.
              Click a colored cell again to clear it. Changes are saved when you click Save.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export default TemplatePatternModal;
