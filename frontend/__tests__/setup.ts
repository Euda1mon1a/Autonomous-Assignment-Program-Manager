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
// 2. Add extensive polyfills (TextEncoder, ReadableStream, MessagePort, etc.)
// 3. Configure transformIgnorePatterns for all ESM dependencies
// 4. Uncomment the MSW setup below
//
// import { server } from '@/mocks/server'
// beforeAll(() => server.listen({ onUnhandledRequest: 'warn' }))
// afterEach(() => server.resetHandlers())
// afterAll(() => server.close())

// ============================================================================
// Browser API Mocks
// ============================================================================

// Mock localStorage with actual storage functionality
const createLocalStorageMock = () => {
  let store: Record<string, string> = {}
  return {
    getItem: jest.fn((key: string) => store[key] || null),
    setItem: jest.fn((key: string, value: string) => {
      store[key] = value
    }),
    removeItem: jest.fn((key: string) => {
      delete store[key]
    }),
    clear: jest.fn(() => {
      store = {}
    }),
    // Expose store for testing
    _getStore: () => store,
  }
}

const localStorageMock = createLocalStorageMock()
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

// Mock scrollIntoView for components that use it (not available in jsdom)
Element.prototype.scrollIntoView = jest.fn()

// ============================================================================
// Next.js Module Mocks
// ============================================================================
// Inlined to avoid circular require() when mock files import from the module
// they're mocking (e.g., `import type { NextRouter } from 'next/router'`).

// Mock next/router (Pages Router)
jest.mock('next/router', () => ({
  useRouter: jest.fn(() => ({
    route: '/',
    pathname: '/',
    query: {},
    asPath: '/',
    push: jest.fn(),
    replace: jest.fn(),
    reload: jest.fn(),
    back: jest.fn(),
    forward: jest.fn(),
    prefetch: jest.fn(),
    beforePopState: jest.fn(),
    events: {
      on: jest.fn(),
      off: jest.fn(),
      emit: jest.fn(),
    },
    isFallback: false,
    isLocaleDomain: false,
    isReady: true,
    isPreview: false,
  })),
  withRouter: (Component: any) => Component,
}))

// Mock next/navigation (App Router)
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(() => ({
    push: jest.fn(),
    replace: jest.fn(),
    refresh: jest.fn(),
    back: jest.fn(),
    forward: jest.fn(),
    prefetch: jest.fn(),
  })),
  usePathname: jest.fn(() => '/'),
  useSearchParams: jest.fn(() => ({
    get: jest.fn(),
    getAll: jest.fn(),
    has: jest.fn(),
    keys: jest.fn(),
    values: jest.fn(),
    entries: jest.fn(),
    forEach: jest.fn(),
    toString: jest.fn(() => ''),
  })),
  useParams: jest.fn(() => ({})),
  redirect: jest.fn(),
  notFound: jest.fn(),
}))

// Mock next/image
jest.mock('next/image', () => {
  const React = require('react')
  return {
    __esModule: true,
    default: React.forwardRef(function MockImage(props: any, ref: any) {
      // eslint-disable-next-line @next/next/no-img-element, jsx-a11y/alt-text
      return React.createElement('img', { ...props, ref })
    }),
  }
})

// Mock next/link
jest.mock('next/link', () => {
  const React = require('react')
  return {
    __esModule: true,
    default: React.forwardRef(function MockLink(
      { children, href, ...props }: any,
      ref: any
    ) {
      return React.createElement('a', { href, ...props, ref }, children)
    }),
  }
})

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
