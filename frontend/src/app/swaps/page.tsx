'use client'

import { SwapMarketplace } from '@/features/swap-marketplace'
import { ProtectedRoute } from '@/components/ProtectedRoute'

export default function SwapsPage() {
  return (
    <ProtectedRoute>
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Swap Marketplace</h1>
          <p className="text-gray-600">Browse and manage schedule swap requests</p>
        </div>
        <SwapMarketplace />
      </div>
    </ProtectedRoute>
  )
}
