/**
 * MSW Server Setup for Node.js (Jest tests)
 *
 * This file sets up the MSW server for use in Jest tests.
 * Import and use this in test setup files.
 */
import { setupServer } from 'msw/node'
import { handlers } from './handlers'

/**
 * Setup MSW server with default handlers
 *
 * The server intercepts all HTTP requests and responds with
 * mock data defined in handlers.ts
 */
export const server = setupServer(...handlers)

/**
 * Reset handlers to initial state
 * Call this in beforeEach or afterEach to reset any runtime handler overrides
 */
export function resetHandlers() {
  server.resetHandlers()
}

/**
 * Add additional handlers at runtime
 * Useful for testing specific scenarios like errors
 *
 * @param additionalHandlers - Array of MSW handlers to add
 */
export function useHandlers(...additionalHandlers: Parameters<typeof server.use>) {
  server.use(...additionalHandlers)
}
