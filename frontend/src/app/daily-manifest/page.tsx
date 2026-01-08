'use client'

import { DailyManifest } from '@/features/daily-manifest'
import { ProtectedRoute } from '@/components/ProtectedRoute'

export default function DailyManifestPage() {
  return (
    <ProtectedRoute>
      <div className="max-w-7xl mx-auto px-4 py-8">
        <DailyManifest />
      </div>
    </ProtectedRoute>
  )
}
