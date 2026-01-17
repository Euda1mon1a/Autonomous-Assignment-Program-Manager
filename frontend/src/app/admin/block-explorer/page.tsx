'use client'

import { ProtectedRoute } from '@/components/ProtectedRoute'

export default function BlockExplorerPage() {
  return (
    <ProtectedRoute requireAdmin={true}>
      <div className="h-[calc(100vh-10rem)]">
        <iframe
          src="/block-explorer.html"
          className="w-full h-full border-0"
          title="Block Explorer - Schedule Data Visualization"
          allow="fullscreen"
        />
      </div>
    </ProtectedRoute>
  )
}
