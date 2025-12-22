'use client'

import { DailyManifest } from '@/features/daily-manifest'
import { ProtectedRoute } from '@/components/ProtectedRoute'

export default function DailyManifestPage() {
  return (
    <ProtectedRoute>
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Daily Manifest</h1>
          <p className="text-gray-600">View today&apos;s staff assignments and locations</p>
        </div>
        <DailyManifest />
      </div>
    </ProtectedRoute>
  )
}
