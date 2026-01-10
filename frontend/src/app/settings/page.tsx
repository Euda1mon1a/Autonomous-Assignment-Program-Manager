'use client'

import { useState, useEffect, FormEvent } from 'react'
import { CheckCircle, AlertCircle, Loader2 } from 'lucide-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { get, post, ApiError } from '@/lib/api'
import { ProtectedRoute } from '@/components/ProtectedRoute'

// Backend schema - matches backend/app/schemas/settings.py and SchedulingAlgorithm enum
// Available algorithms: greedy, cpSat, pulp, hybrid (NOT min_conflicts - no implementation exists)
interface Settings {
  schedulingAlgorithm: 'greedy' | 'cpSat' | 'pulp' | 'hybrid'
  workHoursPerWeek: number
  maxConsecutiveDays: number
  minDaysOffPerWeek: number
  pgy1_supervisionRatio: string  // Format: "1:2"
  pgy2_supervisionRatio: string  // Format: "1:4"
  pgy3_supervisionRatio: string  // Format: "1:4"
  enableWeekendScheduling: boolean
  enableHolidayScheduling: boolean
  defaultBlockDurationHours: number
}

const defaultSettings: Settings = {
  schedulingAlgorithm: 'greedy',
  workHoursPerWeek: 80,
  maxConsecutiveDays: 6,
  minDaysOffPerWeek: 1,
  pgy1_supervisionRatio: '1:2',
  pgy2_supervisionRatio: '1:4',
  pgy3_supervisionRatio: '1:4',
  enableWeekendScheduling: true,
  enableHolidayScheduling: false,
  defaultBlockDurationHours: 4,
}

// API hooks for settings
function useSettings() {
  return useQuery<Settings, ApiError>({
    queryKey: ['settings'],
    queryFn: () => get<Settings>('/settings'),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

function useUpdateSettings() {
  const queryClient = useQueryClient()

  return useMutation<Settings, ApiError, Settings>({
    mutationFn: (data) => post<Settings>('/settings', data),
    onSuccess: (data) => {
      queryClient.setQueryData(['settings'], data)
    },
  })
}

export default function SettingsPage() {
  const { data: fetchedSettings, isLoading: isLoadingSettings, error: loadError } = useSettings()
  const updateSettingsMutation = useUpdateSettings()

  const [settings, setSettings] = useState<Settings>(defaultSettings)
  const [showSuccess, setShowSuccess] = useState(false)
  const [hasChanges, setHasChanges] = useState(false)

  // Load settings from API when fetched
  useEffect(() => {
    if (fetchedSettings) {
      setSettings(fetchedSettings)
    }
  }, [fetchedSettings])

  const updateSetting = <K extends keyof Settings>(
    field: K,
    value: Settings[K]
  ) => {
    setSettings((prev) => ({
      ...prev,
      [field]: value,
    }))
    setHasChanges(true)
    setShowSuccess(false)
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setShowSuccess(false)

    try {
      await updateSettingsMutation.mutateAsync(settings)
      setHasChanges(false)
      setShowSuccess(true)

      // Hide success message after 3 seconds
      setTimeout(() => setShowSuccess(false), 3000)
    } catch {
      // Error is handled by mutation state
      // Failed to save settings
    }
  }

  const isSaving = updateSettingsMutation.isPending
  const saveError = updateSettingsMutation.error

  // Loading state
  if (isLoadingSettings) {
    return (
      <ProtectedRoute requireAdmin>
        <div className="max-w-7xl mx-auto px-4 py-8">
          <div className="mb-6">
            <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
            <p className="text-gray-600">Configure application settings</p>
          </div>
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
            <span className="ml-3 text-gray-600">Loading settings...</span>
          </div>
        </div>
      </ProtectedRoute>
    )
  }

  return (
    <ProtectedRoute requireAdmin>
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
          <p className="text-gray-600">Configure application settings</p>
        </div>

      {/* Load error */}
      {loadError && (
        <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-yellow-600" />
          <span className="text-yellow-800">Could not load settings from server. Using defaults.</span>
        </div>
      )}

      {/* Save error */}
      {saveError && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-red-600" />
          <span className="text-red-800">Failed to save settings: {saveError.message}</span>
        </div>
      )}

      {/* Success message */}
      {showSuccess && (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-center gap-3">
          <CheckCircle className="w-5 h-5 text-green-600" />
          <span className="text-green-800">Settings saved successfully!</span>
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="grid gap-6 md:grid-cols-2">
          {/* Work Hours Settings */}
          <div className="card">
            <h2 className="font-semibold text-lg mb-4">Work Hours</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Max Work Hours per Week
                </label>
                <input
                  type="number"
                  className="input-field w-full"
                  value={settings.workHoursPerWeek}
                  onChange={(e) =>
                    updateSetting('workHoursPerWeek', parseInt(e.target.value) || 80)
                  }
                  min={40}
                  max={100}
                />
                <p className="text-xs text-gray-500 mt-1">
                  ACGME standard is 80 hours per week
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Max Consecutive Days
                </label>
                <input
                  type="number"
                  className="input-field w-full"
                  value={settings.maxConsecutiveDays}
                  onChange={(e) =>
                    updateSetting('maxConsecutiveDays', parseInt(e.target.value) || 6)
                  }
                  min={1}
                  max={7}
                />
                <p className="text-xs text-gray-500 mt-1">
                  Maximum days before requiring a day off
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Min Days Off per Week
                </label>
                <input
                  type="number"
                  className="input-field w-full"
                  value={settings.minDaysOffPerWeek}
                  onChange={(e) =>
                    updateSetting('minDaysOffPerWeek', parseInt(e.target.value) || 1)
                  }
                  min={1}
                  max={3}
                />
                <p className="text-xs text-gray-500 mt-1">
                  ACGME requires at least 1 day off per week
                </p>
              </div>
            </div>
          </div>

          {/* Supervision Ratios */}
          <div className="card">
            <h2 className="font-semibold text-lg mb-4">Supervision Ratios</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  PGY-1 Supervision Ratio
                </label>
                <select
                  className="input-field w-full"
                  value={settings.pgy1_supervisionRatio}
                  onChange={(e) =>
                    updateSetting('pgy1_supervisionRatio', e.target.value)
                  }
                >
                  <option value="1:1">1:1 (1 faculty per resident)</option>
                  <option value="1:2">1:2 (1 faculty per 2 residents)</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  PGY-2 Supervision Ratio
                </label>
                <select
                  className="input-field w-full"
                  value={settings.pgy2_supervisionRatio}
                  onChange={(e) =>
                    updateSetting('pgy2_supervisionRatio', e.target.value)
                  }
                >
                  <option value="1:2">1:2 (1 faculty per 2 residents)</option>
                  <option value="1:3">1:3 (1 faculty per 3 residents)</option>
                  <option value="1:4">1:4 (1 faculty per 4 residents)</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  PGY-3 Supervision Ratio
                </label>
                <select
                  className="input-field w-full"
                  value={settings.pgy3_supervisionRatio}
                  onChange={(e) =>
                    updateSetting('pgy3_supervisionRatio', e.target.value)
                  }
                >
                  <option value="1:2">1:2 (1 faculty per 2 residents)</option>
                  <option value="1:3">1:3 (1 faculty per 3 residents)</option>
                  <option value="1:4">1:4 (1 faculty per 4 residents)</option>
                </select>
              </div>
            </div>
          </div>

          {/* Scheduling Settings */}
          <div className="card">
            <h2 className="font-semibold text-lg mb-4">Scheduling</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Default Algorithm
                </label>
                <select
                  className="input-field w-full"
                  value={settings.schedulingAlgorithm}
                  onChange={(e) =>
                    updateSetting(
                      'schedulingAlgorithm',
                      e.target.value as 'greedy' | 'cpSat' | 'pulp' | 'hybrid'
                    )
                  }
                >
                  <option value="greedy">Greedy (Fast)</option>
                  <option value="cpSat">CP-SAT (Optimal, OR-Tools)</option>
                  <option value="pulp">PuLP (Linear Programming)</option>
                  <option value="hybrid">Hybrid (CP-SAT + PuLP)</option>
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  Greedy is fastest. CP-SAT guarantees ACGME compliance. Hybrid combines both.
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Default Block Duration (hours)
                </label>
                <input
                  type="number"
                  className="input-field w-full"
                  value={settings.defaultBlockDurationHours}
                  onChange={(e) =>
                    updateSetting('defaultBlockDurationHours', parseInt(e.target.value) || 4)
                  }
                  min={1}
                  max={12}
                />
                <p className="text-xs text-gray-500 mt-1">
                  Standard scheduling block duration
                </p>
              </div>
              <div>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    className="rounded border-gray-300"
                    checked={settings.enableWeekendScheduling}
                    onChange={(e) =>
                      updateSetting('enableWeekendScheduling', e.target.checked)
                    }
                  />
                  <span className="text-sm font-medium text-gray-700">
                    Enable Weekend Scheduling
                  </span>
                </label>
              </div>
              <div>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    className="rounded border-gray-300"
                    checked={settings.enableHolidayScheduling}
                    onChange={(e) =>
                      updateSetting('enableHolidayScheduling', e.target.checked)
                    }
                  />
                  <span className="text-sm font-medium text-gray-700">
                    Enable Holiday Scheduling
                  </span>
                </label>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-6 flex justify-end gap-3">
          {hasChanges && (
            <span className="text-sm text-amber-600 self-center">Unsaved changes</span>
          )}
          <button
            type="submit"
            disabled={isSaving || !hasChanges}
            className="btn-primary disabled:opacity-50"
          >
            {isSaving ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      </form>
      </div>
    </ProtectedRoute>
  )
}
