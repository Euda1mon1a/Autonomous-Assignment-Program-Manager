'use client'

import { useState, useMemo } from 'react'
import { Plus, User, Users, GraduationCap, RefreshCw } from 'lucide-react'
import { usePeople, useDeletePerson, type PeopleFilters } from '@/lib/hooks'
import { CardSkeleton } from '@/components/skeletons'
import { AddPersonModal } from '@/components/AddPersonModal'
import { EditPersonModal } from '@/components/EditPersonModal'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { EmptyState } from '@/components/EmptyState'
import { ExportButton } from '@/components/ExportButton'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import type { Person } from '@/types/api'

const peopleExportColumns = [
  { key: 'name', header: 'Name' },
  { key: 'type', header: 'Type' },
  { key: 'pgyLevel', header: 'PGY Level' },
  { key: 'email', header: 'Email' },
]

export default function PeoplePage() {
  const [roleFilter, setRoleFilter] = useState<'all' | 'resident' | 'faculty'>('all')
  const [pgyFilter, setPgyFilter] = useState<number | undefined>(undefined)
  const [isAddModalOpen, setIsAddModalOpen] = useState(false)
  const [editingPerson, setEditingPerson] = useState<Person | null>(null)
  const [personToDelete, setPersonToDelete] = useState<Person | null>(null)

  // Build filters
  const filters: PeopleFilters | undefined =
    roleFilter === 'all' && !pgyFilter
      ? undefined
      : {
          ...(roleFilter !== 'all' && { role: roleFilter }),
          ...(pgyFilter && { pgyLevel: pgyFilter }),
        }

  const { data, isLoading, isError, error, refetch } = usePeople(filters)
  const deletePerson = useDeletePerson()

  // Prepare export data
  const exportData = useMemo(() => {
    return (data?.items || []) as unknown as Record<string, unknown>[]
  }, [data?.items])

  const handleDeleteClick = (person: Person) => {
    setPersonToDelete(person)
  }

  const handleConfirmDelete = () => {
    if (personToDelete) {
      deletePerson.mutate(personToDelete.id)
    }
    setPersonToDelete(null)
  }

  return (
    <ProtectedRoute>
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">People</h1>
          <p className="text-gray-600">Manage residents and faculty</p>
        </div>
        <div className="flex items-center gap-3">
          <ExportButton
            data={exportData}
            filename="people"
            columns={peopleExportColumns}
          />
          <button
            onClick={() => setIsAddModalOpen(true)}
            className="btn-primary flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Add Person
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-4 mb-6">
        {/* Role Filter Tabs */}
        <div className="flex gap-2">
          {(['all', 'resident', 'faculty'] as const).map((role) => (
            <button
              key={role}
              onClick={() => {
                setRoleFilter(role)
                if (role === 'faculty') setPgyFilter(undefined)
              }}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                roleFilter === role
                  ? 'bg-blue-100 text-blue-700'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {role.charAt(0).toUpperCase() + role.slice(1)}
            </button>
          ))}
        </div>

        {/* PGY Level Filter */}
        {roleFilter !== 'faculty' && (
          <select
            value={pgyFilter || ''}
            onChange={(e) => setPgyFilter(e.target.value ? Number(e.target.value) : undefined)}
            className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All PGY Levels</option>
            <option value="1">PGY-1</option>
            <option value="2">PGY-2</option>
            <option value="3">PGY-3</option>
          </select>
        )}
      </div>

      {/* People List */}
      {isLoading ? (
        <div className="grid gap-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <CardSkeleton key={i} />
          ))}
        </div>
      ) : isError ? (
        <div className="card flex flex-col items-center justify-center h-64 text-center">
          <p className="text-gray-600 mb-4">
            {error?.message || 'Failed to load people'}
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
        <div className="grid gap-4">
          {data?.items?.length === 0 ? (
            <div className="card">
              <EmptyState
                icon={Users}
                title="No people added yet"
                description="Add residents and faculty members to start building schedules"
                action={{
                  label: 'Add Person',
                  onClick: () => setIsAddModalOpen(true),
                }}
              />
            </div>
          ) : (
            data?.items?.map((person: Person) => (
              <PersonCard
                key={person.id}
                person={person}
                onEdit={() => setEditingPerson(person)}
                onDelete={() => handleDeleteClick(person)}
              />
            ))
          )}
        </div>
      )}

      {/* Add Person Modal */}
      <AddPersonModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
      />

        {/* Edit Person Modal */}
        <EditPersonModal
          isOpen={editingPerson !== null}
          onClose={() => setEditingPerson(null)}
          person={editingPerson}
        />

        {/* Delete Confirmation Dialog */}
        <ConfirmDialog
          isOpen={personToDelete !== null}
          onClose={() => setPersonToDelete(null)}
          onConfirm={handleConfirmDelete}
          title="Delete Person"
          message={`Are you sure you want to delete ${personToDelete?.name || 'this person'}? This action cannot be undone.`}
          confirmLabel="Delete"
          cancelLabel="Cancel"
          variant="danger"
          isLoading={deletePerson.isPending}
        />
      </div>
    </ProtectedRoute>
  )
}

function PersonCard({
  person,
  onEdit,
  onDelete,
}: {
  person: Person
  onEdit: () => void
  onDelete: () => void
}) {
  const isResident = person.type === 'resident'

  return (
    <div className="card flex items-center justify-between hover:shadow-lg transition-shadow">
      <div className="flex items-center gap-4">
        <div
          className={`p-3 rounded-full ${
            isResident ? 'bg-blue-100' : 'bg-purple-100'
          }`}
        >
          {isResident ? (
            <GraduationCap className="w-6 h-6 text-blue-600" />
          ) : (
            <User className="w-6 h-6 text-purple-600" />
          )}
        </div>
        <div>
          <h3 className="font-semibold text-gray-900">{person.name}</h3>
          <p className="text-sm text-gray-500">
            {isResident ? `PGY-${person.pgyLevel} Resident` : 'Faculty'}
            {person.specialties && person.specialties.length > 0 && (
              <span className="ml-2">
                ({person.specialties.join(', ')})
              </span>
            )}
          </p>
          {person.email && (
            <p className="text-xs text-gray-400">{person.email}</p>
          )}
        </div>
      </div>
      <div className="flex items-center gap-2">
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
