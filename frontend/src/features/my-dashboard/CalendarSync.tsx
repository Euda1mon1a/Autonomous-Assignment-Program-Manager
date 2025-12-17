'use client';

/**
 * CalendarSync Component
 *
 * Provides calendar synchronization functionality with modal UI.
 * Allows users to export their schedule to various calendar formats
 * (ICS, Google Calendar, Outlook) for mobile and desktop calendar apps.
 */

import { useState } from 'react';
import {
  Calendar,
  Download,
  Link2,
  Smartphone,
  X,
  Loader2,
  CheckCircle,
  AlertCircle,
} from 'lucide-react';
import { useCalendarSync } from './hooks';
import type { CalendarSyncRequest } from './types';

// ============================================================================
// Types
// ============================================================================

interface CalendarSyncProps {
  className?: string;
}

type CalendarFormat = 'ics' | 'google' | 'outlook';

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Validate calendar URL to prevent XSS attacks
 */
function isValidCalendarUrl(url: string): boolean {
  try {
    const parsed = new URL(url);
    const allowedProtocols = ['webcal:', 'https:', 'http:'];
    return allowedProtocols.includes(parsed.protocol);
  } catch {
    return false;
  }
}

// ============================================================================
// Component
// ============================================================================

export function CalendarSync({ className = '' }: CalendarSyncProps) {
  const [showModal, setShowModal] = useState(false);
  const [selectedFormat, setSelectedFormat] = useState<CalendarFormat>('ics');
  const [weeksAhead, setWeeksAhead] = useState(12);

  const syncMutation = useCalendarSync();

  const handleSync = async () => {
    try {
      const result = await syncMutation.mutateAsync({
        format: selectedFormat,
        includeWeeksAhead: weeksAhead,
      });

      if (result.url) {
        // Validate URL before using it
        if (!isValidCalendarUrl(result.url)) {
          throw new Error('Invalid calendar URL');
        }

        // For ICS download or subscription URL
        if (selectedFormat === 'ics') {
          // Trigger download
          window.location.href = result.url;
        } else {
          // Open in new tab for Google/Outlook
          window.open(result.url, '_blank');
        }
      }

      // Close modal after short delay to show success
      setTimeout(() => {
        setShowModal(false);
      }, 2000);
    } catch (error) {
      console.error('Failed to sync calendar:', error);
    }
  };

  return (
    <>
      {/* Sync Button */}
      <button
        onClick={() => setShowModal(true)}
        className={`flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors font-medium ${className}`}
      >
        <Calendar className="w-5 h-5" />
        <span className="hidden sm:inline">Sync to Calendar</span>
        <span className="sm:hidden">Sync</span>
      </button>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full max-h-[90vh] overflow-y-auto">
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <div className="flex items-center gap-3">
                <div className="bg-blue-100 rounded-lg p-2">
                  <Calendar className="w-6 h-6 text-blue-600" />
                </div>
                <h2 className="text-xl font-bold text-gray-900">Sync to Calendar</h2>
              </div>
              <button
                onClick={() => setShowModal(false)}
                className="text-gray-400 hover:text-gray-600 transition-colors"
                disabled={syncMutation.isPending}
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            {/* Content */}
            <div className="p-6 space-y-6">
              {/* Format Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Choose Calendar Format
                </label>
                <div className="space-y-2">
                  <button
                    onClick={() => setSelectedFormat('ics')}
                    className={`w-full flex items-start gap-3 p-4 rounded-lg border-2 transition-all ${
                      selectedFormat === 'ics'
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                    disabled={syncMutation.isPending}
                  >
                    <Download className="w-5 h-5 flex-shrink-0 mt-0.5 text-gray-600" />
                    <div className="text-left">
                      <div className="font-semibold text-gray-900">ICS File Download</div>
                      <div className="text-sm text-gray-600">
                        Download .ics file for Apple Calendar, Outlook, or other apps
                      </div>
                    </div>
                  </button>

                  <button
                    onClick={() => setSelectedFormat('google')}
                    className={`w-full flex items-start gap-3 p-4 rounded-lg border-2 transition-all ${
                      selectedFormat === 'google'
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                    disabled={syncMutation.isPending}
                  >
                    <Link2 className="w-5 h-5 flex-shrink-0 mt-0.5 text-gray-600" />
                    <div className="text-left">
                      <div className="font-semibold text-gray-900">Google Calendar</div>
                      <div className="text-sm text-gray-600">
                        Add events directly to your Google Calendar
                      </div>
                    </div>
                  </button>

                  <button
                    onClick={() => setSelectedFormat('outlook')}
                    className={`w-full flex items-start gap-3 p-4 rounded-lg border-2 transition-all ${
                      selectedFormat === 'outlook'
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                    disabled={syncMutation.isPending}
                  >
                    <Link2 className="w-5 h-5 flex-shrink-0 mt-0.5 text-gray-600" />
                    <div className="text-left">
                      <div className="font-semibold text-gray-900">Outlook Calendar</div>
                      <div className="text-sm text-gray-600">
                        Add events directly to your Outlook Calendar
                      </div>
                    </div>
                  </button>
                </div>
              </div>

              {/* Weeks Ahead Selection */}
              <div>
                <label htmlFor="weeks-ahead" className="block text-sm font-medium text-gray-700 mb-2">
                  Include Next {weeksAhead} Weeks
                </label>
                <input
                  id="weeks-ahead"
                  type="range"
                  min="4"
                  max="52"
                  step="4"
                  value={weeksAhead}
                  onChange={(e) => setWeeksAhead(Number(e.target.value))}
                  className="w-full"
                  disabled={syncMutation.isPending}
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>4 weeks</span>
                  <span>52 weeks</span>
                </div>
              </div>

              {/* Mobile Tip */}
              <div className="flex items-start gap-3 p-3 bg-blue-50 rounded-lg">
                <Smartphone className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                <div className="text-sm text-blue-900">
                  <strong>Mobile Tip:</strong> After syncing, check your calendar app to ensure
                  events appear. You may need to enable calendar sync in your app settings.
                </div>
              </div>

              {/* Error Message */}
              {syncMutation.isError && (
                <div className="flex items-start gap-3 p-3 bg-red-50 border border-red-200 rounded-lg">
                  <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                  <div className="text-sm text-red-900">
                    <strong>Error:</strong> {syncMutation.error?.message}
                  </div>
                </div>
              )}

              {/* Success Message */}
              {syncMutation.isSuccess && (
                <div className="flex items-start gap-3 p-3 bg-green-50 border border-green-200 rounded-lg">
                  <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                  <div className="text-sm text-green-900">
                    <strong>Success!</strong> Your calendar has been synced.
                  </div>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="flex gap-3 p-6 border-t border-gray-200">
              <button
                onClick={() => setShowModal(false)}
                className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={syncMutation.isPending}
              >
                Cancel
              </button>
              <button
                onClick={handleSync}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={syncMutation.isPending || syncMutation.isSuccess}
              >
                {syncMutation.isPending ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Syncing...
                  </>
                ) : syncMutation.isSuccess ? (
                  <>
                    <CheckCircle className="w-5 h-5" />
                    Synced
                  </>
                ) : (
                  <>
                    <Calendar className="w-5 h-5" />
                    Sync Now
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
