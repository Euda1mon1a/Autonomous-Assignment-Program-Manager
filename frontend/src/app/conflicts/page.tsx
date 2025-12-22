'use client'

import { ConflictDashboard } from '@/features/conflicts'
import { ProtectedRoute } from '@/components/ProtectedRoute'

export default function ConflictsPage() {
  return (
    <ProtectedRoute>
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Schedule Conflicts</h1>
          <p className="text-gray-600">View and resolve scheduling conflicts</p>
        </div>
        <ConflictDashboard />
      </div>
    </ProtectedRoute>
  )
}
