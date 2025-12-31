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
        gcTime: 0,
        staleTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
    logger: {
      log: console.log,
      warn: console.warn,
      // Don't log errors during tests to avoid noise
      error: () => {},
    },
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

export const mockData = {
  /**
   * Create a mock person (resident or faculty)
   */
  person: (overrides?: Partial<any>) => ({
    id: 'person-1',
    name: 'Dr. Test Person',
    email: 'test@example.com',
    role: 'RESIDENT',
    type: 'resident',
    pgy_level: 1,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    ...overrides,
  }),

  /**
   * Create a mock rotation template
   */
  rotationTemplate: (overrides?: Partial<any>) => ({
    id: 'template-1',
    name: 'Inpatient Medicine',
    abbreviation: 'IM',
    activity_type: 'inpatient',
    background_color: '#e0e7ff',
    font_color: '#4338ca',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    ...overrides,
  }),

  /**
   * Create a mock block
   */
  block: (overrides?: Partial<any>) => ({
    id: 'block-1',
    date: '2024-01-01',
    time_of_day: 'AM',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    ...overrides,
  }),

  /**
   * Create a mock assignment
   */
  assignment: (overrides?: Partial<any>) => ({
    id: 'assignment-1',
    person_id: 'person-1',
    block_id: 'block-1',
    rotation_template_id: 'template-1',
    role: 'primary',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    ...overrides,
  }),

  /**
   * Create a mock swap request
   */
  swapRequest: (overrides?: Partial<any>) => ({
    id: 'swap-1',
    requester_id: 'person-1',
    target_id: 'person-2',
    requester_block_id: 'block-1',
    target_block_id: 'block-2',
    status: 'pending',
    swap_type: 'one_to_one',
    reason: 'Test swap request',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    ...overrides,
  }),

  /**
   * Create a mock absence
   */
  absence: (overrides?: Partial<any>) => ({
    id: 'absence-1',
    person_id: 'person-1',
    start_date: '2024-01-01',
    end_date: '2024-01-01',
    reason: 'Vacation',
    status: 'approved',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    ...overrides,
  }),

  /**
   * Create a paginated response
   */
  paginatedResponse: <T,>(items: T[], overrides?: Partial<any>) => ({
    items,
    total: items.length,
    page: 1,
    per_page: 100,
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
  const error: any = new Error(message);
  error.response = { status };
  return Promise.reject(error);
}

/**
 * Create a mock delayed API response (for testing loading states)
 */
export function mockApiDelayed<T>(data: T, delayMs = 100): Promise<T> {
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
  const timeout = options?.timeout || 3000;
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
  queryByText: (text: string) => HTMLElement | null = () => null
): Promise<void> {
  await waitFor(
    () => {
      const loading = queryByText(/loading/i);
      expect(loading).not.toBeInTheDocument();
    },
    { timeout: 5000 }
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
export function setupUser() {
  return userEvent.setup();
}

/**
 * Type into an input field
 */
export async function typeIntoField(user: ReturnType<typeof userEvent.setup>, input: HTMLElement, text: string) {
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
) {
  await user.click(select);
  await user.click(await waitForElement(() => document.querySelector(`[role="option"]`)));
}

// ============================================================================
// Re-export commonly used testing utilities
// ============================================================================

export * from '@testing-library/react';
export { userEvent };
export { default as userEventLib } from '@testing-library/user-event';
