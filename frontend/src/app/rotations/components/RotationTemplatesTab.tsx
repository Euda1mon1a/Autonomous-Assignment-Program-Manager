'use client'

import { useState, useMemo } from 'react'
import { Plus, Search, ChevronDown, Pencil, X } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { get } from '@/lib/api'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { ErrorAlert } from '@/components/ErrorAlert'
import { EmptyState } from '@/components/EmptyState'
import { EditTemplateModal } from '@/components/EditTemplateModal'
import { CreateTemplateModal } from '@/components/CreateTemplateModal'
import { RotationWeeklyGrid } from '@/components/schedule/RotationWeeklyGrid'
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
 * RotationTemplatesTab - Displays rotation templates with inline activity grid editor.
 *
 * Clicking a rotation card expands the 4-week activity grid below the cards list.
 * The grid editor lets coordinators paint activities onto half-day slots.
 */
export function RotationTemplatesTab({
  canEdit,
  canDelete: _canDelete,
}: RotationTemplatesTabProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [activityTypeFilter, setActivityTypeFilter] = useState<string | null>(null)
  const [expandedTemplateId, setExpandedTemplateId] = useState<string | null>(null)
  const [editingTemplate, setEditingTemplate] = useState<RotationTemplate | null>(null)
  const [isEditModalOpen, setIsEditModalOpen] = useState(false)
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)

  // Handle template card click: expand/collapse grid
  const handleCardClick = (template: RotationTemplate) => {
    if (expandedTemplateId === template.id) {
      setExpandedTemplateId(null)
    } else {
      setExpandedTemplateId(template.id)
    }
  }

  // Handle edit metadata (pencil icon)
  const handleEditMetadata = (e: React.MouseEvent, template: RotationTemplate) => {
    e.stopPropagation()
    setEditingTemplate(template)
    setIsEditModalOpen(true)
  }

  // Handle modal close
  const handleCloseModal = () => {
    setIsEditModalOpen(false)
    setEditingTemplate(null)
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

  // Memoize templates array
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

  // Get expanded template
  const expandedTemplate = useMemo(() => {
    if (!expandedTemplateId) return null
    return templates.find((t) => t.id === expandedTemplateId) ?? null
  }, [templates, expandedTemplateId])

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
              placeholder="Search rotations..."
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
            onClick={() => setIsCreateModalOpen(true)}
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
          title="No rotations found"
          description={
            searchQuery || activityTypeFilter
              ? 'Try adjusting your filters'
              : 'Create your first rotation template to get started'
          }
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filteredTemplates.map((template) => {
            const isExpanded = expandedTemplateId === template.id

            return (
              <div
                key={template.id}
                onClick={() => handleCardClick(template)}
                className={`bg-white rounded-lg border p-4 transition-all cursor-pointer ${
                  isExpanded
                    ? 'border-blue-400 ring-2 ring-blue-200 shadow-md'
                    : 'border-gray-200 hover:shadow-md hover:border-blue-300'
                }`}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault()
                    handleCardClick(template)
                  }
                }}
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
                      <button
                        type="button"
                        onClick={(e) => handleEditMetadata(e, template)}
                        className="p-1 rounded hover:bg-gray-100 transition-colors"
                        title="Edit template metadata"
                      >
                        <Pencil className="h-4 w-4 text-gray-400 hover:text-blue-500" />
                      </button>
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

                {isExpanded && (
                  <div className="mt-2 text-xs text-blue-600 font-medium">
                    Editing activity pattern below...
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      {/* Expanded: 4-week grid editor */}
      {expandedTemplate && (
        <div className="bg-white rounded-lg border border-blue-200 shadow-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                {expandedTemplate.name}
              </h3>
              <p className="text-sm text-gray-500">
                {expandedTemplate.activityType === 'inpatient'
                  ? 'Inpatient rotation - preloaded pattern (solver will not modify)'
                  : 'Outpatient rotation - solver input defaults'}
              </p>
            </div>
            <button
              type="button"
              onClick={() => setExpandedTemplateId(null)}
              className="p-2 hover:bg-gray-100 rounded transition-colors"
              aria-label="Close editor"
            >
              <X className="w-5 h-5 text-gray-500" />
            </button>
          </div>

          <RotationWeeklyGrid
            templateId={expandedTemplate.id}
            rotationType={expandedTemplate.activityType}
            canEdit={canEdit}
            onClose={() => setExpandedTemplateId(null)}
          />
        </div>
      )}

      {/* Edit Template Modal */}
      <EditTemplateModal
        isOpen={isEditModalOpen}
        onClose={handleCloseModal}
        template={editingTemplate}
      />

      {/* Create Template Modal */}
      <CreateTemplateModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
      />
    </div>
  )
}
