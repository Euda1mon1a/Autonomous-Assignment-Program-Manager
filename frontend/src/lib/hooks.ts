/**
 * React Query Hooks for Residency Scheduler
 *
 * DEPRECATED: This file has been reorganized into domain-specific modules.
 * All hooks are now available from '@/hooks' or their specific domain files.
 *
 * This file maintains backward compatibility by re-exporting all hooks
 * from their new locations. Prefer importing from '@/hooks' directly.
 *
 * New structure:
 * - @/hooks/useSchedule - Schedule, assignments, rotation templates, validation
 * - @/hooks/usePeople - People, residents, faculty management
 * - @/hooks/useAbsences - Absence management
 * - @/hooks/useResilience - Emergency coverage and resilience
 */

// Re-export everything from the new hooks directory
export * from '@/hooks'
