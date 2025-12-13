'use client'

import { useState } from 'react'
import { Plus, User, GraduationCap } from 'lucide-react'
import { usePeople } from '@/lib/hooks'

export default function PeoplePage() {
  const [filter, setFilter] = useState<'all' | 'resident' | 'faculty'>('all')
  const { data, isLoading } = usePeople(
    filter === 'all' ? undefined : { type: filter }
  )

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">People</h1>
          <p className="text-gray-600">Manage residents and faculty</p>
        </div>
        <button className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" />
          Add Person
        </button>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-2 mb-6">
        {(['all', 'resident', 'faculty'] as const).map((type) => (
          <button
            key={type}
            onClick={() => setFilter(type)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              filter === type
                ? 'bg-blue-100 text-blue-700'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {type.charAt(0).toUpperCase() + type.slice(1)}
          </button>
        ))}
      </div>

      {/* People List */}
      {isLoading ? (
        <div className="card flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      ) : (
        <div className="grid gap-4">
          {data?.items?.length === 0 ? (
            <div className="card text-center py-12 text-gray-500">
              No people found. Add your first resident or faculty member.
            </div>
          ) : (
            data?.items?.map((person: any) => (
              <PersonCard key={person.id} person={person} />
            ))
          )}
        </div>
      )}
    </div>
  )
}

function PersonCard({ person }: { person: any }) {
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
            {isResident ? `PGY-${person.pgy_level} Resident` : 'Faculty'}
            {person.specialties?.length > 0 && (
              <span className="ml-2">
                ({person.specialties.join(', ')})
              </span>
            )}
          </p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <button className="text-blue-600 hover:underline text-sm">Edit</button>
        <button className="text-red-600 hover:underline text-sm">Delete</button>
      </div>
    </div>
  )
}
