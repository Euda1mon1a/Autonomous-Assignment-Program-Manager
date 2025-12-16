import '@testing-library/jest-dom'

// ============================================================================
// MSW Server Setup (Disabled - see note below)
// ============================================================================
//
// MSW v2 requires Node.js fetch APIs that have compatibility issues with
// Jest's jsdom environment. The mock handlers are defined in src/mocks/handlers.ts
// and can be enabled when using a test runner with better ESM/fetch support
// (like Vitest) or when running in Node.js >= 18 with --experimental-vm-modules.
//
// For Jest tests, we use jest.mock() to mock API modules directly, which is
// more reliable and works across all Node.js versions.
//
// To enable MSW in the future:
// 1. Use Node.js >= 18
// 2. Add --experimental-vm-modules to jest
// 3. Uncomment the MSW setup below
//
// import { server } from '@/mocks/server'
// beforeAll(() => server.listen({ onUnhandledRequest: 'warn' }))
// afterEach(() => server.resetHandlers())
// afterAll(() => server.close())

// ============================================================================
// Browser API Mocks
// ============================================================================

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
}
Object.defineProperty(window, 'localStorage', { value: localStorageMock })

// Mock window.location for auth redirect tests
const locationMock = {
  href: '',
  assign: jest.fn(),
  replace: jest.fn(),
  reload: jest.fn(),
}
Object.defineProperty(window, 'location', {
  value: locationMock,
  writable: true,
})

// Mock matchMedia for responsive components
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
})

// Mock ResizeObserver for components that use it
global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}))

// Mock IntersectionObserver for lazy loading components
global.IntersectionObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}))

// ============================================================================
// Global Test Cleanup
// ============================================================================

// Reset mocks before each test
beforeEach(() => {
  jest.clearAllMocks()
  locationMock.href = ''
})

// ============================================================================
// Export mock utilities for use in tests
// ============================================================================

export { localStorageMock, locationMock }
