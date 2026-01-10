/**
 * Test Utilities - Comprehensive testing helpers
 *
 * Provides:
 * - Custom render with all providers (QueryClient, Router, Theme)
 * - Mock data factories
 * - API mock helpers
 * - User event setup
 * - Async test helpers
 */

import React, { ReactElement } from 'react';
import { render, RenderOptions, RenderResult, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';

// ============================================================================
// Test Configuration Constants
// ============================================================================

// Query Client Configuration
const GC_TIME_MS = 0; // Garbage collection time (disabled for tests)
const STALE_TIME_MS = 0; // Stale time (immediate for tests)

// Timeout Configuration
const DEFAULT_TIMEOUT_MS = 3000; // 3 seconds - Default timeout for element queries
const LOADING_TIMEOUT_MS = 5000; // 5 seconds - Timeout for loading states
const DEFAULT_DELAY_MS = 100; // 100ms - Default delay for API mocks

// Pagination Configuration
const DEFAULT_PER_PAGE = 100; // Default items per page in tests

// ============================================================================
// Test Query Client
// ============================================================================

/**
 * Create a fresh QueryClient for testing with sensible defaults
 */
export function createTestQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: GC_TIME_MS,
        staleTime: STALE_TIME_MS,
      },
      mutations: {
        retry: false,
      },
    },
    // Note: logger was removed in TanStack Query v5
    // Errors are handled by the global error handler instead
  });
}

// ============================================================================
// Test Providers Wrapper
// ============================================================================

interface TestProvidersProps {
  children: React.ReactNode;
  queryClient?: QueryClient;
}

/**
 * Wrapper component that provides all necessary contexts for testing
 */
export function TestProviders({ children, queryClient }: TestProvidersProps) {
  const client = queryClient || createTestQueryClient();

  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

// ============================================================================
// Custom Render
// ============================================================================

interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  queryClient?: QueryClient;
}

/**
 * Custom render function that wraps components with all necessary providers
 *
 * @example
 * const { user } = renderWithProviders(<MyComponent />);
 * await user.click(screen.getByRole('button'));
 */
export function renderWithProviders(
  ui: ReactElement,
  options?: CustomRenderOptions
): RenderResult & { user: ReturnType<typeof userEvent.setup> } {
  const { queryClient, ...renderOptions } = options || {};

  const Wrapper = ({ children }: { children: React.ReactNode }) => (
    <TestProviders queryClient={queryClient}>{children}</TestProviders>
  );

  return {
    ...render(ui, { wrapper: Wrapper, ...renderOptions }),
    user: userEvent.setup(),
  };
}

// ============================================================================
// Mock Data Factories
// ============================================================================

// Mock data types
export interface MockPerson {
  id: string;
  name: string;
  email: string;
  role: string;
  type: string;
  pgyLevel?: number;
  createdAt: string;
  updatedAt: string;
}

export interface MockRotationTemplate {
  id: string;
  name: string;
  abbreviation: string;
  activityType: string;
  backgroundColor: string;
  fontColor: string;
  createdAt: string;
  updatedAt: string;
}

export interface MockBlock {
  id: string;
  date: string;
  timeOfDay: string;
  createdAt: string;
  updatedAt: string;
}

export interface MockAssignment {
  id: string;
  personId: string;
  blockId: string;
  rotationTemplateId: string;
  role: string;
  createdAt: string;
  updatedAt: string;
}

export interface MockSwapRequest {
  id: string;
  requester_id: string;
  target_id: string;
  requester_blockId: string;
  target_blockId: string;
  status: string;
  swapType: string;
  reason: string;
  createdAt: string;
  updatedAt: string;
}

export interface MockAbsence {
  id: string;
  personId: string;
  startDate: string;
  endDate: string;
  reason: string;
  status: string;
  createdAt: string;
  updatedAt: string;
}

export interface MockPaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
}

export const mockData = {
  /**
   * Create a mock person (resident or faculty)
   */
  person: (overrides?: Partial<MockPerson>): MockPerson => ({
    id: 'person-1',
    name: 'Dr. Test Person',
    email: 'test@example.com',
    role: 'RESIDENT',
    type: 'resident',
    pgyLevel: 1,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
    ...overrides,
  }),

  /**
   * Create a mock rotation template
   */
  rotationTemplate: (overrides?: Partial<MockRotationTemplate>): MockRotationTemplate => ({
    id: 'template-1',
    name: 'Inpatient Medicine',
    abbreviation: 'IM',
    activityType: 'inpatient',
    backgroundColor: '#e0e7ff',
    fontColor: '#4338ca',
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
    ...overrides,
  }),

  /**
   * Create a mock block
   */
  block: (overrides?: Partial<MockBlock>): MockBlock => ({
    id: 'block-1',
    date: '2024-01-01',
    timeOfDay: 'AM',
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
    ...overrides,
  }),

  /**
   * Create a mock assignment
   */
  assignment: (overrides?: Partial<MockAssignment>): MockAssignment => ({
    id: 'assignment-1',
    personId: 'person-1',
    blockId: 'block-1',
    rotationTemplateId: 'template-1',
    role: 'primary',
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
    ...overrides,
  }),

  /**
   * Create a mock swap request
   */
  swapRequest: (overrides?: Partial<MockSwapRequest>): MockSwapRequest => ({
    id: 'swap-1',
    requester_id: 'person-1',
    target_id: 'person-2',
    requester_blockId: 'block-1',
    target_blockId: 'block-2',
    status: 'pending',
    swapType: 'oneToOne',
    reason: 'Test swap request',
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
    ...overrides,
  }),

  /**
   * Create a mock absence
   */
  absence: (overrides?: Partial<MockAbsence>): MockAbsence => ({
    id: 'absence-1',
    personId: 'person-1',
    startDate: '2024-01-01',
    endDate: '2024-01-01',
    reason: 'Vacation',
    status: 'approved',
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
    ...overrides,
  }),

  /**
   * Create a paginated response
   */
  paginatedResponse: <T,>(items: T[], overrides?: Partial<MockPaginatedResponse<T>>): MockPaginatedResponse<T> => ({
    items,
    total: items.length,
    page: 1,
    per_page: DEFAULT_PER_PAGE,
    ...overrides,
  }),
};

// ============================================================================
// API Mock Helpers
// ============================================================================

/**
 * Create a mock successful API response
 */
export function mockApiSuccess<T>(data: T): Promise<T> {
  return Promise.resolve(data);
}

/**
 * Create a mock failed API response
 */
export function mockApiError(message: string, status = 500): Promise<never> {
  const error = new Error(message) as Error & { response?: { status: number } };
  error.response = { status };
  return Promise.reject(error);
}

/**
 * Create a mock delayed API response (for testing loading states)
 */
export function mockApiDelayed<T>(data: T, delayMs = DEFAULT_DELAY_MS): Promise<T> {
  return new Promise((resolve) => {
    setTimeout(() => resolve(data), delayMs);
  });
}

// ============================================================================
// Async Test Helpers
// ============================================================================

/**
 * Wait for an element to appear with better error messages
 */
export async function waitForElement(
  callback: () => HTMLElement | null,
  options?: { timeout?: number; errorMessage?: string }
): Promise<HTMLElement> {
  const timeout = options?.timeout || DEFAULT_TIMEOUT_MS;
  const errorMessage = options?.errorMessage || 'Element not found';

  try {
    let element: HTMLElement | null = null;
    await waitFor(
      () => {
        element = callback();
        expect(element).toBeInTheDocument();
      },
      { timeout }
    );
    return element!;
  } catch (error) {
    throw new Error(errorMessage);
  }
}

/**
 * Wait for loading to finish
 */
export async function waitForLoadingToFinish(
  queryByText: (text: string | RegExp) => HTMLElement | null = () => null
): Promise<void> {
  await waitFor(
    () => {
      const loading = queryByText(/loading/i);
      expect(loading).not.toBeInTheDocument();
    },
    { timeout: LOADING_TIMEOUT_MS }
  );
}

/**
 * Wait for a specific number of API calls
 */
export async function waitForApiCalls(mockFn: jest.Mock, expectedCalls: number): Promise<void> {
  await waitFor(() => {
    expect(mockFn).toHaveBeenCalledTimes(expectedCalls);
  });
}

// ============================================================================
// User Event Helpers
// ============================================================================

/**
 * Setup user event with default options
 */
export function setupUser(): ReturnType<typeof userEvent.setup> {
  return userEvent.setup();
}

/**
 * Type into an input field
 */
export async function typeIntoField(user: ReturnType<typeof userEvent.setup>, input: HTMLElement, text: string): Promise<void> {
  await user.clear(input);
  await user.type(input, text);
}

/**
 * Select an option from a select element
 */
export async function selectOption(
  user: ReturnType<typeof userEvent.setup>,
  select: HTMLElement,
  optionText: string
): Promise<void> {
  await user.click(select);
  await user.click(await waitForElement(() => document.querySelector(`[role="option"]`)));
}

// ============================================================================
// Re-export commonly used testing utilities
// ============================================================================

export * from '@testing-library/react';
export { userEvent };
export { default as userEventLib } from '@testing-library/user-event';
