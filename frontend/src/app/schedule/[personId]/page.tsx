'use client'

import { useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { LoadingSpinner } from '@/components/LoadingSpinner'

/**
 * Person Schedule Page - Redirect to Personal Schedule Hub
 *
 * This route has been consolidated into the Personal Schedule Hub at /my-schedule.
 * It now redirects to /my-schedule?person={personId} for Tier 1+ users.
 *
 * The redirect preserves the person ID in the URL so the hub can display
 * the correct person's schedule.
 *
 * @deprecated Use /my-schedule?person={personId} instead
 */
export default function PersonSchedulePage() {
  const params = useParams()
  const router = useRouter()
  const personId = params.personId as string

  useEffect(() => {
    // Redirect to the unified Personal Schedule Hub with person query param
    if (personId) {
      router.replace(`/my-schedule?person=${personId}`)
    } else {
      router.replace('/my-schedule')
    }
  }, [personId, router])

  // Show loading while redirecting
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="flex flex-col items-center gap-3">
        <LoadingSpinner />
        <span className="text-gray-600">Redirecting to schedule hub...</span>
      </div>
    </div>
  )
}
