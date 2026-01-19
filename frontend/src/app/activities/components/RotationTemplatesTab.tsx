'use client'

import { useState, useMemo } from 'react'
import { Plus, Search, ChevronDown, Pencil } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { get } from '@/lib/api'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { ErrorAlert } from '@/components/ErrorAlert'
import { EmptyState } from '@/components/EmptyState'
import { EditTemplateModal } from '@/components/EditTemplateModal'
import type { RotationTemplate } from '@/types/api'

interface RotationTemplatesTabProps {
  canEdit: boolean
  canDelete: boolean
}

interface ListResponse<T> {
  items: T[]
  total: number
  skip: number
  limit: number
}

/**
 * RotationTemplatesTab - Displays and manages rotation templates
 *
 * Rotation templates define reusable activity patterns for resident scheduling.
 */
export function RotationTemplatesTab({
  canEdit,
  canDelete: _canDelete,
}: RotationTemplatesTabProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [activityTypeFilter, setActivityTypeFilter] = useState<string | null>(null)
  const [selectedTemplate, setSelectedTemplate] = useState<RotationTemplate | null>(null)
  const [isEditModalOpen, setIsEditModalOpen] = useState(false)

  // Handle template card click to open edit modal
  const handleEditTemplate = (template: RotationTemplate) => {
    setSelectedTemplate(template)
    setIsEditModalOpen(true)
  }

  // Handle modal close
  const handleCloseModal = () => {
    setIsEditModalOpen(false)
    setSelectedTemplate(null)
  }

  // Fetch rotation templates
  const {
    data: templatesData,
    isLoading,
    error,
  } = useQuery<ListResponse<RotationTemplate>>({
    queryKey: ['rotation-templates'],
    queryFn: () => get('/rotation-templates'),
  })

  // Memoize templates array to prevent dependency warnings
  const templates = useMemo(
    () => templatesData?.items ?? [],
    [templatesData?.items]
  )

  // Get unique activity types
  const activityTypes = useMemo(() => {
    const types = new Set<string>()
    templates.forEach((t) => {
      if (t.activityType) types.add(t.activityType)
    })
    return Array.from(types).sort()
  }, [templates])

  // Filter templates
  const filteredTemplates = useMemo(() => {
    return templates.filter((template) => {
      const matchesSearch =
        !searchQuery ||
        template.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        template.abbreviation?.toLowerCase().includes(searchQuery.toLowerCase())

      const matchesActivityType =
        !activityTypeFilter || template.activityType === activityTypeFilter

      return matchesSearch && matchesActivityType
    })
  }, [templates, searchQuery, activityTypeFilter])

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (error) {
    return <ErrorAlert message="Failed to load rotation templates" />
  }

  return (
    <div className="space-y-6">
      {/* Toolbar */}
      <div className="flex flex-col sm:flex-row gap-4 justify-between">
        <div className="flex flex-1 gap-4">
          {/* Search */}
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search templates..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Activity type filter */}
          <div className="relative">
            <select
              value={activityTypeFilter ?? ''}
              onChange={(e) =>
                setActivityTypeFilter(e.target.value || null)
              }
              className="appearance-none pl-4 pr-10 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
            >
              <option value="">All Types</option>
              {activityTypes.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
            <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none" />
          </div>
        </div>

        {/* Add button */}
        {canEdit && (
          <button
            type="button"
            onClick={() => {
              // TODO: Implement create template modal
              alert('Create template feature coming soon')
            }}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <Plus className="h-4 w-4" />
            Add Template
          </button>
        )}
      </div>

      {/* Templates grid */}
      {filteredTemplates.length === 0 ? (
        <EmptyState
          title="No templates found"
          description={
            searchQuery || activityTypeFilter
              ? 'Try adjusting your filters'
              : 'Create your first rotation template to get started'
          }
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filteredTemplates.map((template) => (
            <div
              key={template.id}
              onClick={() => canEdit && handleEditTemplate(template)}
              className={`bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow ${
                canEdit ? 'cursor-pointer hover:border-blue-300' : ''
              }`}
              role={canEdit ? 'button' : undefined}
              tabIndex={canEdit ? 0 : undefined}
              onKeyDown={
                canEdit
                  ? (e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault()
                        handleEditTemplate(template)
                      }
                    }
                  : undefined
              }
            >
              <div className="flex justify-between items-start mb-2">
                <h3 className="font-medium text-gray-900">{template.name}</h3>
                <div className="flex items-center gap-2">
                  {template.abbreviation && (
                    <span className="px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-600 rounded">
                      {template.abbreviation}
                    </span>
                  )}
                  {canEdit && (
                    <Pencil className="h-4 w-4 text-gray-400 hover:text-blue-500" />
                  )}
                </div>
              </div>

              {template.activityType && (
                <p className="text-sm text-gray-500 mb-2">{template.activityType}</p>
              )}

              <div className="text-sm text-gray-600 space-y-1">
                {template.maxResidents && (
                  <p>Max Residents: {template.maxResidents}</p>
                )}
                {template.maxSupervisionRatio && (
                  <p>Supervision: {template.maxSupervisionRatio}:1</p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Edit Template Modal */}
      <EditTemplateModal
        isOpen={isEditModalOpen}
        onClose={handleCloseModal}
        template={selectedTemplate}
      />
    </div>
  )
}
