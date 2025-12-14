'use client'

import { useMemo } from 'react'
import { format } from 'date-fns'
import { Pencil, Trash2 } from 'lucide-react'
import type { Absence, Person } from '@/types/api'

interface AbsenceListProps {
  absences: Absence[]
  people: Person[]
  onEdit: (absence: Absence) => void
  onDelete: (absence: Absence) => void
}

const typeColors: Record<string, string> = {
  vacation: 'bg-green-100 text-green-800',
  sick: 'bg-red-100 text-red-800',
  medical: 'bg-red-100 text-red-800',
  conference: 'bg-blue-100 text-blue-800',
  personal: 'bg-purple-100 text-purple-800',
  family_emergency: 'bg-purple-100 text-purple-800',
  deployment: 'bg-orange-100 text-orange-800',
  tdy: 'bg-yellow-100 text-yellow-800',
}

export function AbsenceList({ absences, people, onEdit, onDelete }: AbsenceListProps) {
  // Create a map of person_id to person for quick lookup
  const personMap = useMemo(() => {
    const map = new Map<string, Person>()
    people.forEach((p) => map.set(p.id, p))
    return map
  }, [people])

  // Sort absences by start date (upcoming first)
  const sortedAbsences = useMemo(() => {
    return [...absences].sort((a, b) => {
      const dateA = new Date(a.start_date)
      const dateB = new Date(b.start_date)
      return dateA.getTime() - dateB.getTime()
    })
  }, [absences])

  if (sortedAbsences.length === 0) {
    return (
      <div className="card text-center py-12 text-gray-500">
        No absences found. Click "Add Absence" to create one.
      </div>
    )
  }

  return (
    <div className="card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Person
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Type
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Start Date
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                End Date
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Notes
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {sortedAbsences.map((absence) => {
              const person = personMap.get(absence.person_id)
              const colorClass = typeColors[absence.absence_type] || typeColors.personal

              return (
                <tr key={absence.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">
                      {person?.name || 'Unknown'}
                    </div>
                    <div className="text-xs text-gray-500">
                      {person?.type === 'resident'
                        ? `PGY-${person.pgy_level}`
                        : person?.type === 'faculty'
                        ? 'Faculty'
                        : ''}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize ${colorClass}`}
                    >
                      {absence.absence_type.replace('_', ' ')}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {format(new Date(absence.start_date), 'MMM d, yyyy')}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {format(new Date(absence.end_date), 'MMM d, yyyy')}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500 max-w-xs truncate">
                    {absence.notes || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => onEdit(absence)}
                        className="text-blue-600 hover:text-blue-800 p-1 hover:bg-blue-50 rounded"
                        title="Edit absence"
                      >
                        <Pencil className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => onDelete(absence)}
                        className="text-red-600 hover:text-red-800 p-1 hover:bg-red-50 rounded"
                        title="Delete absence"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
