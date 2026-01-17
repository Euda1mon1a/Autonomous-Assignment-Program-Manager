'use client'

import { ProtectedRoute } from '@/components/ProtectedRoute'

export default function SchemaVisualizerPage() {
  return (
    <ProtectedRoute requireAdmin={true}>
      <div className="h-[calc(100vh-10rem)]">
        <iframe
          src="/schema-visualizer.html"
          className="w-full h-full border-0"
          title="Database Schema Visualizer"
          allow="fullscreen"
        />
      </div>
    </ProtectedRoute>
  )
}
