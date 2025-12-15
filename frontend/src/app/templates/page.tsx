'use client'

import { useState } from 'react'
import { Plus, RefreshCw, FileText } from 'lucide-react'
import { useRotationTemplates, useDeleteTemplate } from '@/lib/hooks'
import { CardSkeleton } from '@/components/skeletons'
import { CreateTemplateModal } from '@/components/CreateTemplateModal'
import { EditTemplateModal } from '@/components/EditTemplateModal'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { EmptyState } from '@/components/EmptyState'
import type { RotationTemplate } from '@/types/api'

export default function TemplatesPage() {
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [editingTemplate, setEditingTemplate] = useState<RotationTemplate | null>(null)

  const { data, isLoading, isError, error, refetch } = useRotationTemplates()
  const deleteTemplate = useDeleteTemplate()

  const handleDelete = (id: string, name: string) => {
    if (confirm(`Are you sure you want to delete "${name}"?`)) {
      deleteTemplate.mutate(id)
    }
  }

  return (
    <ProtectedRoute>
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Rotation Templates</h1>
          <p className="text-gray-600">Define reusable activity patterns with constraints</p>
        </div>
        <button
          onClick={() => setIsCreateModalOpen(true)}
          className="btn-primary flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          New Template
        </button>
      </div>

      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <CardSkeleton key={i} />
          ))}
        </div>
      ) : isError ? (
        <div className="card flex flex-col items-center justify-center h-64 text-center">
          <p className="text-gray-600 mb-4">
            {error?.message || 'Failed to load templates'}
          </p>
          <button
            onClick={() => refetch()}
            className="btn-primary flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Retry
          </button>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {data?.items?.length === 0 ? (
            <div className="col-span-full card">
              <EmptyState
                icon={FileText}
                title="No rotation templates"
                description="Create templates to define reusable activity patterns with constraints"
                action={{
                  label: 'Create Template',
                  onClick: () => setIsCreateModalOpen(true),
                }}
              />
            </div>
          ) : (
            data?.items?.map((template: RotationTemplate) => (
              <TemplateCard
                key={template.id}
                template={template}
                onEdit={() => setEditingTemplate(template)}
                onDelete={() => handleDelete(template.id, template.name)}
              />
            ))
          )}
        </div>
      )}

      {/* Create Template Modal */}
      <CreateTemplateModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
      />

        {/* Edit Template Modal */}
        <EditTemplateModal
          isOpen={editingTemplate !== null}
          onClose={() => setEditingTemplate(null)}
          template={editingTemplate}
        />
      </div>
    </ProtectedRoute>
  )
}

function TemplateCard({
  template,
  onEdit,
  onDelete,
}: {
  template: RotationTemplate
  onEdit: () => void
  onDelete: () => void
}) {
  const activityColors: Record<string, string> = {
    clinic: 'bg-blue-100 text-blue-800',
    inpatient: 'bg-purple-100 text-purple-800',
    procedure: 'bg-red-100 text-red-800',
    conference: 'bg-gray-100 text-gray-800',
    elective: 'bg-green-100 text-green-800',
    call: 'bg-orange-100 text-orange-800',
  }

  const colorClass = activityColors[template.activity_type] || 'bg-gray-100 text-gray-800'

  return (
    <div className="card hover:shadow-lg transition-shadow">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="font-semibold text-gray-900">{template.name}</h3>
          <span className={`inline-block px-2 py-1 rounded text-xs mt-1 ${colorClass}`}>
            {template.activity_type}
          </span>
        </div>
        {template.abbreviation && (
          <span className="bg-gray-100 px-2 py-1 rounded text-sm font-mono">
            {template.abbreviation}
          </span>
        )}
      </div>

      <div className="space-y-2 text-sm">
        {template.max_residents && (
          <div className="flex justify-between">
            <span className="text-gray-500">Max Residents:</span>
            <span className="font-medium">{template.max_residents}</span>
          </div>
        )}
        <div className="flex justify-between">
          <span className="text-gray-500">Supervision Ratio:</span>
          <span className="font-medium">1:{template.max_supervision_ratio}</span>
        </div>
        {template.requires_specialty && (
          <div className="flex justify-between">
            <span className="text-gray-500">Requires:</span>
            <span className="font-medium text-amber-700">{template.requires_specialty}</span>
          </div>
        )}
      </div>

      <div className="mt-4 pt-4 border-t flex gap-2">
        <button
          onClick={onEdit}
          className="text-blue-600 hover:underline text-sm"
        >
          Edit
        </button>
        <button
          onClick={onDelete}
          className="text-red-600 hover:underline text-sm"
        >
          Delete
        </button>
      </div>
    </div>
  )
}
