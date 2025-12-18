'use client'

import { useState, useEffect, FormEvent } from 'react'
import { CheckCircle, AlertCircle, Loader2 } from 'lucide-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { get, post, ApiError } from '@/lib/api'
import { ProtectedRoute } from '@/components/ProtectedRoute'

// Backend schema - matches backend/app/schemas/settings.py
interface Settings {
  scheduling_algorithm: 'greedy' | 'min_conflicts' | 'cp_sat'
  work_hours_per_week: number
  max_consecutive_days: number
  min_days_off_per_week: number
  pgy1_supervision_ratio: string  // Format: "1:2"
  pgy2_supervision_ratio: string  // Format: "1:4"
  pgy3_supervision_ratio: string  // Format: "1:4"
  enable_weekend_scheduling: boolean
  enable_holiday_scheduling: boolean
  default_block_duration_hours: number
}

const defaultSettings: Settings = {
  scheduling_algorithm: 'greedy',
  work_hours_per_week: 80,
  max_consecutive_days: 6,
  min_days_off_per_week: 1,
  pgy1_supervision_ratio: '1:2',
  pgy2_supervision_ratio: '1:4',
  pgy3_supervision_ratio: '1:4',
  enable_weekend_scheduling: true,
  enable_holiday_scheduling: false,
  default_block_duration_hours: 4,
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
                  value={settings.work_hours_per_week}
                  onChange={(e) =>
                    updateSetting('work_hours_per_week', parseInt(e.target.value) || 80)
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
                  value={settings.max_consecutive_days}
                  onChange={(e) =>
                    updateSetting('max_consecutive_days', parseInt(e.target.value) || 6)
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
                  value={settings.min_days_off_per_week}
                  onChange={(e) =>
                    updateSetting('min_days_off_per_week', parseInt(e.target.value) || 1)
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
                  value={settings.pgy1_supervision_ratio}
                  onChange={(e) =>
                    updateSetting('pgy1_supervision_ratio', e.target.value)
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
                  value={settings.pgy2_supervision_ratio}
                  onChange={(e) =>
                    updateSetting('pgy2_supervision_ratio', e.target.value)
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
                  value={settings.pgy3_supervision_ratio}
                  onChange={(e) =>
                    updateSetting('pgy3_supervision_ratio', e.target.value)
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
                  value={settings.scheduling_algorithm}
                  onChange={(e) =>
                    updateSetting(
                      'scheduling_algorithm',
                      e.target.value as 'greedy' | 'min_conflicts' | 'cp_sat'
                    )
                  }
                >
                  <option value="greedy">Greedy (Fast)</option>
                  <option value="min_conflicts">Min Conflicts (Balanced)</option>
                  <option value="cp_sat">CP-SAT (Optimal)</option>
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  Greedy is fastest, CP-SAT finds optimal solution but slower
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Default Block Duration (hours)
                </label>
                <input
                  type="number"
                  className="input-field w-full"
                  value={settings.default_block_duration_hours}
                  onChange={(e) =>
                    updateSetting('default_block_duration_hours', parseInt(e.target.value) || 4)
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
                    checked={settings.enable_weekend_scheduling}
                    onChange={(e) =>
                      updateSetting('enable_weekend_scheduling', e.target.checked)
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
                    checked={settings.enable_holiday_scheduling}
                    onChange={(e) =>
                      updateSetting('enable_holiday_scheduling', e.target.checked)
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
