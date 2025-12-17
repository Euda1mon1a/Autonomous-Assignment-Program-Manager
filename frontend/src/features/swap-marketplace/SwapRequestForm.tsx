'use client';

/**
 * SwapRequestForm Component
 *
 * Form to create a new swap request. Allows faculty to request
 * a swap of their assigned week with another faculty member or
 * to have someone absorb their week.
 */

import { useState } from 'react';
import { format } from 'date-fns';
import {
  Calendar,
  User,
  MessageSquare,
  Send,
  AlertCircle,
  Loader2,
} from 'lucide-react';
import { useCreateSwapRequest, useAvailableWeeks, useFacultyMembers } from './hooks';
import type { CreateSwapRequest } from './types';

// ============================================================================
// Types
// ============================================================================

interface SwapRequestFormProps {
  onSuccess?: () => void;
  onCancel?: () => void;
}

// ============================================================================
// Component
// ============================================================================

export function SwapRequestForm({
  onSuccess,
  onCancel,
}: SwapRequestFormProps) {
  const [weekToOffload, setWeekToOffload] = useState('');
  const [swapMode, setSwapMode] = useState<'specific' | 'auto'>('auto');
  const [targetFacultyId, setTargetFacultyId] = useState('');
  const [reason, setReason] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Fetch data
  const { data: availableWeeks = [], isLoading: weeksLoading, error: weeksError } = useAvailableWeeks();
  const { data: facultyMembers = [], isLoading: facultyLoading, error: facultyError } = useFacultyMembers();
  const createMutation = useCreateSwapRequest();

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!weekToOffload) {
      newErrors.weekToOffload = 'Please select a week to offload';
    }

    if (swapMode === 'specific' && !targetFacultyId) {
      newErrors.targetFacultyId = 'Please select a target faculty member';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    const request: CreateSwapRequest = {
      weekToOffload,
      reason: reason || undefined,
      autoFindCandidates: swapMode === 'auto',
      preferredTargetFacultyId: swapMode === 'specific' ? targetFacultyId : undefined,
    };

    try {
      const response = await createMutation.mutateAsync(request);

      if (response.success) {
        // Reset form
        setWeekToOffload('');
        setSwapMode('auto');
        setTargetFacultyId('');
        setReason('');
        setErrors({});

        onSuccess?.();
      } else {
        setErrors({ submit: response.message });
      }
    } catch (error: any) {
      setErrors({ submit: error.message || 'Failed to create swap request' });
    }
  };

  const handleReset = () => {
    setWeekToOffload('');
    setSwapMode('auto');
    setTargetFacultyId('');
    setReason('');
    setErrors({});
  };

  // Show loading state while fetching data
  if (weeksLoading || facultyLoading) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
          <span className="ml-3 text-gray-600">Loading form data...</span>
        </div>
      </div>
    );
  }

  // Show error state if data fetching failed
  if (weeksError || facultyError) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-6 h-6 text-red-600 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="text-lg font-semibold text-red-900 mb-1">
                Error Loading Form Data
              </h3>
              <p className="text-red-700">
                {weeksError?.message || facultyError?.message}
              </p>
              {onCancel && (
                <button
                  onClick={onCancel}
                  className="mt-3 px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors"
                >
                  Go Back
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <h2 className="text-xl font-semibold mb-4">Create Swap Request</h2>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Week Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            <Calendar className="inline w-4 h-4 mr-1" />
            Week to Offload *
          </label>
          <select
            value={weekToOffload}
            onChange={(e) => setWeekToOffload(e.target.value)}
            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              errors.weekToOffload ? 'border-red-500' : 'border-gray-300'
            }`}
            disabled={createMutation.isPending}
          >
            <option value="">Select a week...</option>
            {availableWeeks.length === 0 && (
              <option value="" disabled>
                No assigned weeks available
              </option>
            )}
            {availableWeeks.map((week) => (
              <option key={week.date} value={week.date}>
                {format(new Date(week.date), 'MMM d, yyyy')}
                {week.hasConflict ? ' (Has Conflict)' : ''}
              </option>
            ))}
          </select>
          {errors.weekToOffload && (
            <p className="mt-1 text-sm text-red-600">{errors.weekToOffload}</p>
          )}
          {availableWeeks.length === 0 && (
            <p className="mt-1 text-sm text-gray-500">
              You currently have no assigned FMIT weeks to swap.
            </p>
          )}
        </div>

        {/* Swap Mode */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Swap Mode
          </label>
          <div className="space-y-2">
            <label className="flex items-start gap-3 p-3 border border-gray-300 rounded-md cursor-pointer hover:bg-gray-50">
              <input
                type="radio"
                name="swapMode"
                value="auto"
                checked={swapMode === 'auto'}
                onChange={(e) => setSwapMode(e.target.value as 'auto')}
                className="mt-1"
                disabled={createMutation.isPending}
              />
              <div>
                <div className="font-medium">Auto-find candidates</div>
                <div className="text-sm text-gray-600">
                  System will notify all eligible faculty members who can take this week
                </div>
              </div>
            </label>
            <label className="flex items-start gap-3 p-3 border border-gray-300 rounded-md cursor-pointer hover:bg-gray-50">
              <input
                type="radio"
                name="swapMode"
                value="specific"
                checked={swapMode === 'specific'}
                onChange={(e) => setSwapMode(e.target.value as 'specific')}
                className="mt-1"
                disabled={createMutation.isPending}
              />
              <div>
                <div className="font-medium">Request specific faculty</div>
                <div className="text-sm text-gray-600">
                  Send request to a specific faculty member
                </div>
              </div>
            </label>
          </div>
        </div>

        {/* Target Faculty (only shown for specific mode) */}
        {swapMode === 'specific' && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <User className="inline w-4 h-4 mr-1" />
              Target Faculty *
            </label>
            <select
              value={targetFacultyId}
              onChange={(e) => setTargetFacultyId(e.target.value)}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.targetFacultyId ? 'border-red-500' : 'border-gray-300'
              }`}
              disabled={createMutation.isPending}
            >
              <option value="">Select faculty member...</option>
              {facultyMembers.map((faculty) => (
                <option key={faculty.id} value={faculty.id}>
                  {faculty.name}
                </option>
              ))}
            </select>
            {errors.targetFacultyId && (
              <p className="mt-1 text-sm text-red-600">{errors.targetFacultyId}</p>
            )}
          </div>
        )}

        {/* Reason */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            <MessageSquare className="inline w-4 h-4 mr-1" />
            Reason / Notes
          </label>
          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Provide a reason for the swap request (optional but recommended)..."
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            rows={4}
            maxLength={500}
            disabled={createMutation.isPending}
          />
          <div className="mt-1 text-sm text-gray-500 text-right">
            {reason.length}/500 characters
          </div>
        </div>

        {/* Submit Error */}
        {errors.submit && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-md flex items-start gap-2">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-red-700">{errors.submit}</p>
          </div>
        )}

        {/* Success Message */}
        {createMutation.isSuccess && !errors.submit && (
          <div className="p-3 bg-green-50 border border-green-200 rounded-md">
            <p className="text-sm text-green-700">
              Swap request created successfully!
              {createMutation.data?.candidatesNotified
                ? ` ${createMutation.data.candidatesNotified} candidate(s) notified.`
                : ''}
            </p>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-3 pt-4 border-t border-gray-200">
          <button
            type="submit"
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={createMutation.isPending || availableWeeks.length === 0}
          >
            {createMutation.isPending ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Creating...
              </>
            ) : (
              <>
                <Send className="w-4 h-4" />
                Create Request
              </>
            )}
          </button>
          <button
            type="button"
            onClick={onCancel || handleReset}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={createMutation.isPending}
          >
            {onCancel ? 'Cancel' : 'Reset'}
          </button>
        </div>
      </form>

      {/* Help Text */}
      <div className="mt-6 p-4 bg-blue-50 rounded-md">
        <h4 className="text-sm font-medium text-blue-900 mb-2">How it works:</h4>
        <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
          <li>Select a week you are assigned to that you want to swap</li>
          <li>Choose to auto-find candidates or request a specific faculty member</li>
          <li>Eligible faculty will be notified and can accept your request</li>
          <li>Once accepted, the swap will be processed by the system</li>
        </ul>
      </div>
    </div>
  );
}
