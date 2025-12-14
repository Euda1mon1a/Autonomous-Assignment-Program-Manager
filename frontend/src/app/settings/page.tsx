'use client'

import { useState, useEffect, FormEvent } from 'react'
import { CheckCircle } from 'lucide-react'

interface Settings {
  academicYear: {
    startDate: string
    endDate: string
    blockDuration: number
  }
  acgme: {
    maxWeeklyHours: number
    pgy1SupervisionRatio: number
    pgy23SupervisionRatio: number
  }
  scheduling: {
    defaultAlgorithm: 'greedy' | 'min_conflicts' | 'cp_sat'
  }
}

const defaultSettings: Settings = {
  academicYear: {
    startDate: '2024-07-01',
    endDate: '2025-06-30',
    blockDuration: 28,
  },
  acgme: {
    maxWeeklyHours: 80,
    pgy1SupervisionRatio: 2,
    pgy23SupervisionRatio: 4,
  },
  scheduling: {
    defaultAlgorithm: 'greedy',
  },
}

export default function SettingsPage() {
  const [settings, setSettings] = useState<Settings>(defaultSettings)
  const [isSaving, setIsSaving] = useState(false)
  const [showSuccess, setShowSuccess] = useState(false)
  const [hasChanges, setHasChanges] = useState(false)

  // Load settings from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem('residencySchedulerSettings')
    if (saved) {
      try {
        setSettings(JSON.parse(saved))
      } catch {
        // Use defaults if parsing fails
      }
    }
  }, [])

  const updateSettings = <K extends keyof Settings>(
    section: K,
    field: keyof Settings[K],
    value: Settings[K][keyof Settings[K]]
  ) => {
    setSettings((prev) => ({
      ...prev,
      [section]: {
        ...prev[section],
        [field]: value,
      },
    }))
    setHasChanges(true)
    setShowSuccess(false)
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setIsSaving(true)

    // Simulate API call - in production, this would POST to /api/settings
    await new Promise((resolve) => setTimeout(resolve, 500))

    // Save to localStorage
    localStorage.setItem('residencySchedulerSettings', JSON.stringify(settings))

    setIsSaving(false)
    setHasChanges(false)
    setShowSuccess(true)

    // Hide success message after 3 seconds
    setTimeout(() => setShowSuccess(false), 3000)
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600">Configure application settings</p>
      </div>

      {showSuccess && (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-center gap-3">
          <CheckCircle className="w-5 h-5 text-green-600" />
          <span className="text-green-800">Settings saved successfully!</span>
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="grid gap-6 md:grid-cols-2">
          {/* Academic Year Settings */}
          <div className="card">
            <h2 className="font-semibold text-lg mb-4">Academic Year</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Start Date
                </label>
                <input
                  type="date"
                  className="input-field w-full"
                  value={settings.academicYear.startDate}
                  onChange={(e) =>
                    updateSettings('academicYear', 'startDate', e.target.value)
                  }
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  End Date
                </label>
                <input
                  type="date"
                  className="input-field w-full"
                  value={settings.academicYear.endDate}
                  onChange={(e) =>
                    updateSettings('academicYear', 'endDate', e.target.value)
                  }
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Block Duration (days)
                </label>
                <input
                  type="number"
                  className="input-field w-full"
                  value={settings.academicYear.blockDuration}
                  onChange={(e) =>
                    updateSettings('academicYear', 'blockDuration', parseInt(e.target.value) || 28)
                  }
                  min={1}
                  max={365}
                />
              </div>
            </div>
          </div>

          {/* ACGME Settings */}
          <div className="card">
            <h2 className="font-semibold text-lg mb-4">ACGME Settings</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Max Weekly Hours
                </label>
                <input
                  type="number"
                  className="input-field w-full"
                  value={settings.acgme.maxWeeklyHours}
                  onChange={(e) =>
                    updateSettings('acgme', 'maxWeeklyHours', parseInt(e.target.value) || 80)
                  }
                  min={1}
                  max={168}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  PGY-1 Supervision Ratio
                </label>
                <select
                  className="input-field w-full"
                  value={settings.acgme.pgy1SupervisionRatio}
                  onChange={(e) =>
                    updateSettings('acgme', 'pgy1SupervisionRatio', parseInt(e.target.value))
                  }
                >
                  <option value={2}>1:2 (1 faculty per 2 residents)</option>
                  <option value={1}>1:1 (1 faculty per resident)</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  PGY-2/3 Supervision Ratio
                </label>
                <select
                  className="input-field w-full"
                  value={settings.acgme.pgy23SupervisionRatio}
                  onChange={(e) =>
                    updateSettings('acgme', 'pgy23SupervisionRatio', parseInt(e.target.value))
                  }
                >
                  <option value={4}>1:4 (1 faculty per 4 residents)</option>
                  <option value={3}>1:3 (1 faculty per 3 residents)</option>
                  <option value={2}>1:2 (1 faculty per 2 residents)</option>
                </select>
              </div>
            </div>
          </div>

          {/* Scheduling Algorithm */}
          <div className="card">
            <h2 className="font-semibold text-lg mb-4">Scheduling Algorithm</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Default Algorithm
                </label>
                <select
                  className="input-field w-full"
                  value={settings.scheduling.defaultAlgorithm}
                  onChange={(e) =>
                    updateSettings(
                      'scheduling',
                      'defaultAlgorithm',
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
            </div>
          </div>

          {/* Holidays */}
          <div className="card">
            <h2 className="font-semibold text-lg mb-4">Federal Holidays</h2>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between py-2 border-b">
                <span>New Years Day</span>
                <span className="text-gray-500">Jan 1</span>
              </div>
              <div className="flex justify-between py-2 border-b">
                <span>MLK Day</span>
                <span className="text-gray-500">3rd Mon Jan</span>
              </div>
              <div className="flex justify-between py-2 border-b">
                <span>Presidents Day</span>
                <span className="text-gray-500">3rd Mon Feb</span>
              </div>
              <div className="flex justify-between py-2 border-b">
                <span>Memorial Day</span>
                <span className="text-gray-500">Last Mon May</span>
              </div>
              <div className="flex justify-between py-2 border-b">
                <span>Independence Day</span>
                <span className="text-gray-500">Jul 4</span>
              </div>
              <div className="flex justify-between py-2">
                <span>+ 5 more holidays</span>
                <button type="button" className="text-blue-600 hover:underline">Edit</button>
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
  )
}
