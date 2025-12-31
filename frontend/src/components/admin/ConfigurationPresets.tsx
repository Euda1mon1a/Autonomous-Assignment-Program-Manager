'use client'

import { useState, useCallback, useEffect } from 'react'
import {
  Save,
  FolderOpen,
  Trash2,
  Check,
  ChevronDown,
  Star,
  Clock,
  Loader2,
  Download,
  Upload,
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

// Storage key for presets
const PRESETS_STORAGE_KEY = 'admin_scheduling_presets'

export interface SchedulingPreset {
  id: string
  name: string
  description?: string
  isDefault?: boolean
  createdAt: string
  updatedAt: string
  configuration: {
    algorithm: string
    constraints: Array<{ id: string; enabled: boolean }>
    preserveFMIT: boolean
    nfPostCallEnabled: boolean
    academicYear: string
    blockRange: { start: number; end: number }
    timeoutSeconds: number
    dryRun: boolean
  }
}

// Built-in presets that ship with the system
const BUILT_IN_PRESETS: SchedulingPreset[] = [
  {
    id: 'quick-start-small',
    name: 'Quick Start (Small)',
    description: 'Fast generation for small programs (5 residents, 60 blocks)',
    isDefault: true,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    configuration: {
      algorithm: 'greedy',
      constraints: [],
      preserveFMIT: true,
      nfPostCallEnabled: true,
      academicYear: '2024-2025',
      blockRange: { start: 1, end: 60 },
      timeoutSeconds: 60,
      dryRun: true,
    },
  },
  {
    id: 'balanced-medium',
    name: 'Balanced (Medium)',
    description: 'Balanced approach for medium programs with CP-SAT',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    configuration: {
      algorithm: 'hybrid',
      constraints: [],
      preserveFMIT: true,
      nfPostCallEnabled: true,
      academicYear: '2024-2025',
      blockRange: { start: 1, end: 365 },
      timeoutSeconds: 300,
      dryRun: true,
    },
  },
  {
    id: 'full-year-production',
    name: 'Full Year (Production)',
    description: 'Complete academic year scheduling with all constraints',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    configuration: {
      algorithm: 'hybrid',
      constraints: [],
      preserveFMIT: true,
      nfPostCallEnabled: true,
      academicYear: '2024-2025',
      blockRange: { start: 1, end: 730 },
      timeoutSeconds: 600,
      dryRun: false,
    },
  },
]

interface ConfigurationPresetsProps {
  /** Current configuration to save */
  currentConfiguration: SchedulingPreset['configuration']
  /** Callback when a preset is loaded */
  onLoadPreset: (configuration: SchedulingPreset['configuration']) => void
  /** Additional CSS classes */
  className?: string
}

/**
 * Configuration Presets Component
 *
 * Allows admins to save, load, and manage scheduling configuration presets.
 * Includes built-in presets and user-created presets stored in localStorage.
 */
export function ConfigurationPresets({
  currentConfiguration,
  onLoadPreset,
  className = '',
}: ConfigurationPresetsProps) {
  const [presets, setPresets] = useState<SchedulingPreset[]>([])
  const [isDropdownOpen, setIsDropdownOpen] = useState(false)
  const [isSaveModalOpen, setIsSaveModalOpen] = useState(false)
  const [newPresetName, setNewPresetName] = useState('')
  const [newPresetDescription, setNewPresetDescription] = useState('')
  const [isSaving, setIsSaving] = useState(false)
  const [recentlyLoaded, setRecentlyLoaded] = useState<string | null>(null)

  // Load presets from localStorage on mount
  useEffect(() => {
    const loadPresets = () => {
      try {
        const stored = localStorage.getItem(PRESETS_STORAGE_KEY)
        const userPresets = stored ? JSON.parse(stored) : []
        setPresets([...BUILT_IN_PRESETS, ...userPresets])
      } catch (error) {
        // console.error('Failed to load presets:', error)
        setPresets(BUILT_IN_PRESETS)
      }
    }
    loadPresets()
  }, [])

  // Save user presets to localStorage
  const savePresetsToStorage = useCallback((allPresets: SchedulingPreset[]) => {
    const userPresets = allPresets.filter(
      (p) => !BUILT_IN_PRESETS.find((bp) => bp.id === p.id)
    )
    try {
      localStorage.setItem(PRESETS_STORAGE_KEY, JSON.stringify(userPresets))
    } catch (error) {
      // console.error('Failed to save presets:', error)
    }
  }, [])

  // Save current configuration as a new preset
  const handleSavePreset = useCallback(() => {
    if (!newPresetName.trim()) return

    setIsSaving(true)

    const newPreset: SchedulingPreset = {
      id: `user-${Date.now()}`,
      name: newPresetName.trim(),
      description: newPresetDescription.trim() || undefined,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      configuration: { ...currentConfiguration },
    }

    setTimeout(() => {
      const updatedPresets = [...presets, newPreset]
      setPresets(updatedPresets)
      savePresetsToStorage(updatedPresets)
      setNewPresetName('')
      setNewPresetDescription('')
      setIsSaveModalOpen(false)
      setIsSaving(false)
    }, 300)
  }, [newPresetName, newPresetDescription, currentConfiguration, presets, savePresetsToStorage])

  // Load a preset
  const handleLoadPreset = useCallback(
    (preset: SchedulingPreset) => {
      onLoadPreset(preset.configuration)
      setRecentlyLoaded(preset.id)
      setIsDropdownOpen(false)

      // Clear the "loaded" indicator after 2 seconds
      setTimeout(() => setRecentlyLoaded(null), 2000)
    },
    [onLoadPreset]
  )

  // Delete a user preset
  const handleDeletePreset = useCallback(
    (presetId: string) => {
      const updatedPresets = presets.filter((p) => p.id !== presetId)
      setPresets(updatedPresets)
      savePresetsToStorage(updatedPresets)
    },
    [presets, savePresetsToStorage]
  )

  // Export presets to JSON file
  const handleExportPresets = useCallback(() => {
    const userPresets = presets.filter(
      (p) => !BUILT_IN_PRESETS.find((bp) => bp.id === p.id)
    )
    const blob = new Blob([JSON.stringify(userPresets, null, 2)], {
      type: 'application/json',
    })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `scheduling-presets-${new Date().toISOString().split('T')[0]}.json`
    link.click()
    URL.revokeObjectURL(url)
  }, [presets])

  // Import presets from JSON file
  const handleImportPresets = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0]
      if (!file) return

      const reader = new FileReader()
      reader.onload = (e) => {
        try {
          const imported = JSON.parse(e.target?.result as string)
          if (Array.isArray(imported)) {
            const newPresets = imported.map((p: SchedulingPreset) => ({
              ...p,
              id: `imported-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
            }))
            const updatedPresets = [...presets, ...newPresets]
            setPresets(updatedPresets)
            savePresetsToStorage(updatedPresets)
          }
        } catch (error) {
          // console.error('Failed to import presets:', error)
        }
      }
      reader.readAsText(file)
      event.target.value = '' // Reset input
    },
    [presets, savePresetsToStorage]
  )

  const builtInPresets = presets.filter((p) =>
    BUILT_IN_PRESETS.find((bp) => bp.id === p.id)
  )
  const userPresets = presets.filter(
    (p) => !BUILT_IN_PRESETS.find((bp) => bp.id === p.id)
  )

  return (
    <div className={`relative ${className}`}>
      <div className="flex items-center gap-2">
        {/* Load Preset Dropdown */}
        <div className="relative">
          <button
            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
            className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm font-medium transition-colors"
          >
            <FolderOpen className="w-4 h-4" />
            Load Preset
            <ChevronDown
              className={`w-4 h-4 transition-transform ${isDropdownOpen ? 'rotate-180' : ''}`}
            />
          </button>

          <AnimatePresence>
            {isDropdownOpen && (
              <>
                {/* Backdrop */}
                <div
                  className="fixed inset-0 z-40"
                  onClick={() => setIsDropdownOpen(false)}
                />

                {/* Dropdown */}
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="absolute top-full left-0 mt-2 w-80 bg-slate-800 border border-slate-700 rounded-lg shadow-xl z-50 overflow-hidden"
                >
                  <div className="p-2 border-b border-slate-700">
                    <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
                      Built-in Presets
                    </span>
                  </div>
                  <div className="max-h-64 overflow-y-auto">
                    {builtInPresets.map((preset) => (
                      <PresetItem
                        key={preset.id}
                        preset={preset}
                        isLoaded={recentlyLoaded === preset.id}
                        onLoad={() => handleLoadPreset(preset)}
                        isBuiltIn
                      />
                    ))}
                  </div>

                  {userPresets.length > 0 && (
                    <>
                      <div className="p-2 border-y border-slate-700">
                        <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
                          Your Presets
                        </span>
                      </div>
                      <div className="max-h-48 overflow-y-auto">
                        {userPresets.map((preset) => (
                          <PresetItem
                            key={preset.id}
                            preset={preset}
                            isLoaded={recentlyLoaded === preset.id}
                            onLoad={() => handleLoadPreset(preset)}
                            onDelete={() => handleDeletePreset(preset.id)}
                          />
                        ))}
                      </div>
                    </>
                  )}

                  {/* Import/Export */}
                  <div className="p-2 border-t border-slate-700 flex gap-2">
                    <label className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg text-xs font-medium transition-colors cursor-pointer">
                      <Upload className="w-3.5 h-3.5" />
                      Import
                      <input
                        type="file"
                        accept=".json"
                        className="hidden"
                        onChange={handleImportPresets}
                      />
                    </label>
                    <button
                      onClick={handleExportPresets}
                      disabled={userPresets.length === 0}
                      className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg text-xs font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <Download className="w-3.5 h-3.5" />
                      Export
                    </button>
                  </div>
                </motion.div>
              </>
            )}
          </AnimatePresence>
        </div>

        {/* Save Current Configuration */}
        <button
          onClick={() => setIsSaveModalOpen(true)}
          className="flex items-center gap-2 px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white rounded-lg text-sm font-medium transition-colors"
        >
          <Save className="w-4 h-4" />
          Save as Preset
        </button>
      </div>

      {/* Save Modal */}
      <AnimatePresence>
        {isSaveModalOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
              onClick={() => setIsSaveModalOpen(false)}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-md"
            >
              <div className="bg-slate-800 border border-slate-700 rounded-xl shadow-2xl p-6">
                <h3 className="text-lg font-semibold text-white mb-4">
                  Save Configuration Preset
                </h3>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-1">
                      Preset Name
                    </label>
                    <input
                      type="text"
                      value={newPresetName}
                      onChange={(e) => setNewPresetName(e.target.value)}
                      placeholder="e.g., My Custom Configuration"
                      className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 text-sm focus:ring-2 focus:ring-violet-500 focus:border-violet-500"
                      autoFocus
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-1">
                      Description (optional)
                    </label>
                    <textarea
                      value={newPresetDescription}
                      onChange={(e) => setNewPresetDescription(e.target.value)}
                      placeholder="Describe when to use this configuration..."
                      rows={2}
                      className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 text-sm focus:ring-2 focus:ring-violet-500 focus:border-violet-500"
                    />
                  </div>
                </div>

                <div className="flex gap-3 mt-6">
                  <button
                    onClick={() => setIsSaveModalOpen(false)}
                    className="flex-1 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm font-medium transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSavePreset}
                    disabled={!newPresetName.trim() || isSaving}
                    className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isSaving ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Saving...
                      </>
                    ) : (
                      <>
                        <Save className="w-4 h-4" />
                        Save Preset
                      </>
                    )}
                  </button>
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  )
}

// Individual preset item in the dropdown
function PresetItem({
  preset,
  isLoaded,
  isBuiltIn,
  onLoad,
  onDelete,
}: {
  preset: SchedulingPreset
  isLoaded: boolean
  isBuiltIn?: boolean
  onLoad: () => void
  onDelete?: () => void
}) {
  return (
    <div className="group flex items-center gap-2 p-2 hover:bg-slate-700/50 transition-colors">
      <button onClick={onLoad} className="flex-1 text-left min-w-0">
        <div className="flex items-center gap-2">
          {preset.isDefault && <Star className="w-3.5 h-3.5 text-amber-400" />}
          <span className="text-sm font-medium text-white truncate">
            {preset.name}
          </span>
          {isLoaded && <Check className="w-4 h-4 text-emerald-400" />}
        </div>
        {preset.description && (
          <p className="text-xs text-slate-400 truncate mt-0.5">
            {preset.description}
          </p>
        )}
        <div className="flex items-center gap-2 mt-1 text-xs text-slate-500">
          <span className="uppercase">{preset.configuration.algorithm}</span>
          <span>•</span>
          <span>
            {preset.configuration.blockRange.end - preset.configuration.blockRange.start + 1} blocks
          </span>
        </div>
      </button>
      {!isBuiltIn && onDelete && (
        <button
          onClick={(e) => {
            e.stopPropagation()
            onDelete()
          }}
          className="p-1.5 opacity-0 group-hover:opacity-100 hover:bg-red-500/20 text-red-400 rounded transition-all"
          title="Delete preset"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      )}
    </div>
  )
}
