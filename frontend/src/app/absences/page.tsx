'use client'

import { useState, useMemo } from 'react'
import { Plus, Calendar, List, RefreshCw, Upload, Grid } from 'lucide-react'
import { format, addDays } from 'date-fns'
import { useAbsences, usePeople, useDeleteAbsence, useUpdateAbsence } from '@/lib/hooks'
import { CardSkeleton } from '@/components/skeletons'
import { AddAbsenceModal } from '@/components/AddAbsenceModal'
import { AbsenceCalendar } from '@/components/AbsenceCalendar'
import { AbsenceList } from '@/components/AbsenceList'
import { AbsenceGrid, type PersonTypeFilter } from '@/components/absence/AbsenceGrid'
import { BlockNavigation } from '@/components/schedule/BlockNavigation'
import { Modal } from '@/components/Modal'
import { Select, DatePicker, TextArea } from '@/components/forms'
import { ExportButton } from '@/components/ExportButton'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { useToast } from '@/contexts/ToastContext'
import { BulkImportModal } from '@/features/import-export/BulkImportModal'
import type { Absence } from '@/types/api'

const absenceExportColumns = [
  { key: 'person_name', header: 'Person' },
  { key: 'absence_type', header: 'Type' },
  { key: 'start_date', header: 'Start Date' },
  { key: 'end_date', header: 'End Date' },
  { key: 'notes', header: 'Notes' },
]

type ViewMode = 'calendar' | 'list' | 'grid'
type AbsenceTypeFilter = 'all' | 'vacation' | 'sick' | 'conference' | 'personal' | 'medical' | 'deployment' | 'tdy' | 'family_emergency' | 'bereavement' | 'emergency_leave' | 'convalescent' | 'maternity_paternity'

const absenceTypeOptions = [
  // Planned leave
  { value: 'vacation', label: 'Vacation' },
  { value: 'conference', label: 'Conference' },
  // Medical
  { value: 'sick', label: 'Sick' },
  { value: 'medical', label: 'Medical Leave' },
  { value: 'convalescent', label: 'Convalescent' },
  { value: 'maternity_paternity', label: 'Parental Leave' },
  // Emergency (blocking - Hawaii reality: 7+ days travel)
  { value: 'family_emergency', label: 'Family Emergency' },
  { value: 'emergency_leave', label: 'Emergency Leave' },
  { value: 'bereavement', label: 'Bereavement' },
  // Military
  { value: 'deployment', label: 'Deployment' },
  { value: 'tdy', label: 'TDY' },
]

// Get initial date range (today + 27 days for a block period)
function getInitialDateRange() {
  const today = new Date()
  return { start: today, end: addDays(today, 27) }
}

export default function AbsencesPage() {
  const [viewMode, setViewMode] = useState<ViewMode>('calendar')
  const [typeFilter, setTypeFilter] = useState<AbsenceTypeFilter>('all')
  const [isAddModalOpen, setIsAddModalOpen] = useState(false)
  const [isBulkImportModalOpen, setIsBulkImportModalOpen] = useState(false)
  const [editingAbsence, setEditingAbsence] = useState<Absence | null>(null)
  const [absenceToDelete, setAbsenceToDelete] = useState<Absence | null>(null)

  // Grid view state
  const [gridDateRange, setGridDateRange] = useState(getInitialDateRange)
  const [personTypeFilter, setPersonTypeFilter] = useState<PersonTypeFilter>('all')
  const [preselectedPersonId, setPreselectedPersonId] = useState<string | undefined>()
  const [preselectedDate, setPreselectedDate] = useState<string | undefined>()

  // Edit form state
  const [editStartDate, setEditStartDate] = useState('')
  const [editEndDate, setEditEndDate] = useState('')
  const [editAbsenceType, setEditAbsenceType] = useState('')
  const [editNotes, setEditNotes] = useState('')

  const { toast } = useToast()
  const { data: absencesData, isLoading: isAbsencesLoading, isError, error, refetch } = useAbsences()
  const { data: peopleData, isLoading: isPeopleLoading } = usePeople()
  const deleteAbsence = useDeleteAbsence()
  const updateAbsence = useUpdateAbsence()

  const people = useMemo(() => peopleData?.items || [], [peopleData?.items])
  const allAbsences = useMemo(() => absencesData?.items || [], [absencesData?.items])

  // Prepare export data with person names resolved
  const exportData = useMemo(() => {
    const peopleMap = new Map(people.map(p => [p.id, p.name]))
    return allAbsences.map(absence => ({
      ...absence,
      person_name: peopleMap.get(absence.person_id) || 'Unknown',
    })) as unknown as Record<string, unknown>[]
  }, [allAbsences, people])

  // Filter absences by type
  const absences = typeFilter === 'all'
    ? allAbsences
    : allAbsences.filter((a) => a.absence_type === typeFilter)

  const handleDeleteClick = (absence: Absence) => {
    setAbsenceToDelete(absence)
  }

  const handleConfirmDelete = () => {
    if (absenceToDelete) {
      deleteAbsence.mutate(absenceToDelete.id)
    }
    setAbsenceToDelete(null)
  }

  const handleEditClick = (absence: Absence) => {
    setEditingAbsence(absence)
    setEditStartDate(absence.start_date)
    setEditEndDate(absence.end_date)
    setEditAbsenceType(absence.absence_type)
    setEditNotes(absence.notes || '')
  }

  const handleEditClose = () => {
    setEditingAbsence(null)
    setEditStartDate('')
    setEditEndDate('')
    setEditAbsenceType('')
    setEditNotes('')
  }

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!editingAbsence) return

    try {
      await updateAbsence.mutateAsync({
        id: editingAbsence.id,
        data: {
          start_date: editStartDate,
          end_date: editEndDate,
          absence_type: editAbsenceType as Absence['absence_type'],
          notes: editNotes || undefined,
        },
      })
      handleEditClose()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to update absence')
    }
  }

  const isLoading = isAbsencesLoading || isPeopleLoading

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Absence Management</h1>
          <p className="text-gray-600">Manage vacation, sick days, and other absences</p>
        </div>
        <div className="flex items-center gap-3">
          <ExportButton
            data={exportData}
            filename="absences"
            columns={absenceExportColumns}
          />
          <button
            onClick={() => setIsBulkImportModalOpen(true)}
            className="btn-secondary flex items-center gap-2"
          >
            <Upload className="w-4 h-4" />
            Bulk Import
          </button>
          <button
            onClick={() => setIsAddModalOpen(true)}
            className="btn-primary flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Add Absence
          </button>
        </div>
      </div>

      {/* Controls Row */}
      <div className="flex flex-wrap items-center gap-4 mb-6">
        {/* View Toggle */}
        <div className="flex gap-1 bg-gray-100 p-1 rounded-lg">
          <button
            onClick={() => setViewMode('calendar')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
              viewMode === 'calendar'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <Calendar className="w-4 h-4" />
            Calendar
          </button>
          <button
            onClick={() => setViewMode('list')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
              viewMode === 'list'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <List className="w-4 h-4" />
            List
          </button>
          <button
            onClick={() => setViewMode('grid')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
              viewMode === 'grid'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <Grid className="w-4 h-4" />
            Grid
          </button>
        </div>

        {/* Type Filter (calendar/list only) */}
        {viewMode !== 'grid' && (
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value as AbsenceTypeFilter)}
            className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Types</option>
            <option value="vacation">Vacation</option>
            <option value="medical">Sick / Medical</option>
            <option value="conference">Conference</option>
            <option value="family_emergency">Personal / Family Emergency</option>
            <option value="deployment">Deployment</option>
            <option value="tdy">TDY</option>
          </select>
        )}

        {/* Person Type Filter (grid only) */}
        {viewMode === 'grid' && (
          <div className="flex gap-1 bg-gray-100 p-1 rounded-lg">
            <button
              onClick={() => setPersonTypeFilter('all')}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                personTypeFilter === 'all'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              All
            </button>
            <button
              onClick={() => setPersonTypeFilter('residents')}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                personTypeFilter === 'residents'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Residents
            </button>
            <button
              onClick={() => setPersonTypeFilter('faculty')}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                personTypeFilter === 'faculty'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Faculty
            </button>
          </div>
        )}
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="grid gap-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <CardSkeleton key={i} />
          ))}
        </div>
      ) : isError ? (
        <div className="card flex flex-col items-center justify-center h-64 text-center">
          <p className="text-gray-600 mb-4">
            {error?.message || 'Failed to load absences'}
          </p>
          <button
            onClick={() => refetch()}
            className="btn-primary flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Retry
          </button>
        </div>
      ) : viewMode === 'calendar' ? (
        <AbsenceCalendar
          absences={absences}
          people={people}
          onAbsenceClick={handleEditClick}
        />
      ) : viewMode === 'list' ? (
        <AbsenceList
          absences={absences}
          people={people}
          onEdit={handleEditClick}
          onDelete={handleDeleteClick}
        />
      ) : (
        <div className="space-y-4">
          <BlockNavigation
            startDate={gridDateRange.start}
            endDate={gridDateRange.end}
            onDateRangeChange={(start, end) => setGridDateRange({ start, end })}
          />
          <AbsenceGrid
            startDate={gridDateRange.start}
            endDate={gridDateRange.end}
            personTypeFilter={personTypeFilter}
            onAddAbsence={(personId, date) => {
              setPreselectedPersonId(personId)
              setPreselectedDate(format(date, 'yyyy-MM-dd'))
              setIsAddModalOpen(true)
            }}
            onEditAbsence={handleEditClick}
          />
        </div>
      )}

      {/* Add Absence Modal */}
      <AddAbsenceModal
        isOpen={isAddModalOpen}
        onClose={() => {
          setIsAddModalOpen(false)
          setPreselectedPersonId(undefined)
          setPreselectedDate(undefined)
        }}
        preselectedPersonId={preselectedPersonId}
        preselectedStartDate={preselectedDate}
        preselectedEndDate={preselectedDate}
      />

      {/* Edit Absence Modal */}
      <Modal
        isOpen={editingAbsence !== null}
        onClose={handleEditClose}
        title="Edit Absence"
      >
        <form onSubmit={handleEditSubmit} className="space-y-4">
          <div className="text-sm text-gray-600 mb-4">
            Editing absence for:{' '}
            <span className="font-medium">
              {people.find((p) => p.id === editingAbsence?.person_id)?.name || 'Unknown'}
            </span>
          </div>

          <Select
            label="Absence Type"
            value={editAbsenceType}
            onChange={(e) => setEditAbsenceType(e.target.value)}
            options={absenceTypeOptions}
          />

          <div className="grid grid-cols-2 gap-4">
            <DatePicker
              label="Start Date"
              value={editStartDate}
              onChange={setEditStartDate}
            />
            <DatePicker
              label="End Date"
              value={editEndDate}
              onChange={setEditEndDate}
            />
          </div>

          <TextArea
            label="Notes"
            value={editNotes}
            onChange={(e) => setEditNotes(e.target.value)}
            placeholder="Optional notes..."
            rows={3}
          />

          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={handleEditClose}
              className="btn-secondary"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={updateAbsence.isPending}
              className="btn-primary disabled:opacity-50"
            >
              {updateAbsence.isPending ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={absenceToDelete !== null}
        onClose={() => setAbsenceToDelete(null)}
        onConfirm={handleConfirmDelete}
        title="Delete Absence"
        message="Are you sure you want to delete this absence record? This action cannot be undone."
        confirmLabel="Delete"
        cancelLabel="Cancel"
        variant="danger"
        isLoading={deleteAbsence.isPending}
      />

      {/* Bulk Import Modal */}
      <BulkImportModal
        isOpen={isBulkImportModalOpen}
        onClose={() => setIsBulkImportModalOpen(false)}
        onSuccess={() => {
          refetch()
          toast.success('Absences imported successfully')
        }}
        defaultDataType="absences"
        title="Bulk Import Absences"
      />
    </div>
  )
}
