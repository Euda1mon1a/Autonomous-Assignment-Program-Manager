'use client'

import { CallRoster } from '@/features/call-roster'
import { ProtectedRoute } from '@/components/ProtectedRoute'

export default function CallRosterPage() {
  return (
    <ProtectedRoute>
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Call Roster</h1>
          <p className="text-gray-600">View who is on call and their contact information</p>
        </div>
        <CallRoster />
      </div>
    </ProtectedRoute>
  )
}
