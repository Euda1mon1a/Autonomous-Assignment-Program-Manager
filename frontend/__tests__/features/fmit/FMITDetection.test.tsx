/**
 * FMIT Week Detection Tests
 *
 * Tests for verifying that FMIT week conflict detection works correctly,
 * including red conflict alert display when hasConflict=true and proper
 * mocking of schedule context state.
 */

import React from 'react';
import { render, screen, waitFor, within } from '@/test-utils';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { SwapRequestForm } from '@/features/swap-marketplace/SwapRequestForm';
import * as swapHooks from '@/features/swap-marketplace/hooks';

// ============================================================================
// Mock Hooks
// ============================================================================

jest.mock('@/features/swap-marketplace/hooks');

// ============================================================================
// Test Utilities
// ============================================================================

function createTestQueryClient() {
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
  });
}

function createWrapper() {
  const queryClient = createTestQueryClient();

  return function Wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

// ============================================================================
// Mock Data Factories for FMIT Week Detection
// ============================================================================

/**
 * Factory for creating FMIT week data with conflict status
 */
export const fmitMockFactories = {
  /** Create a single FMIT week entry */
  fmitWeek: (overrides: { date?: string; hasConflict?: boolean } = {}) => ({
    date: overrides.date ?? '2025-01-15',
    hasConflict: overrides.hasConflict ?? false,
  }),

  /** Create an array of FMIT weeks with various conflict states */
  fmitWeeksWithConflicts: () => [
    { date: '2025-01-01', hasConflict: false },
    { date: '2025-01-08', hasConflict: false },
    { date: '2025-01-15', hasConflict: true }, // Conflict week
    { date: '2025-01-22', hasConflict: false },
    { date: '2025-01-29', hasConflict: true }, // Another conflict week
    { date: '2025-02-05', hasConflict: false },
  ],

  /** Create weeks without any conflicts */
  fmitWeeksNoConflicts: () => [
    { date: '2025-01-01', hasConflict: false },
    { date: '2025-01-08', hasConflict: false },
    { date: '2025-01-15', hasConflict: false },
  ],

  /** Create weeks where all have conflicts */
  fmitWeeksAllConflicts: () => [
    { date: '2025-01-01', hasConflict: true },
    { date: '2025-01-08', hasConflict: true },
    { date: '2025-01-15', hasConflict: true },
  ],

  /** Create a single week with conflict */
  singleWeekWithConflict: () => [{ date: '2025-01-15', hasConflict: true }],

  /** Create a single week without conflict */
  singleWeekNoConflict: () => [{ date: '2025-01-15', hasConflict: false }],

  /** Empty weeks array */
  emptyWeeks: (): Array<{ date: string; hasConflict: boolean }> => [],
};

/**
 * Mock faculty members for testing
 */
export const mockFacultyMembers = [
  { id: 'faculty-1', name: 'Dr. John Smith' },
  { id: 'faculty-2', name: 'Dr. Jane Doe' },
  { id: 'faculty-3', name: 'Dr. Bob Johnson' },
];

/**
 * Mock successful swap creation response
 */
export const mockSuccessResponse = {
  success: true,
  requestId: 'swap-new-1',
  message: 'Swap request created successfully',
  candidatesNotified: 3,
};

// ============================================================================
// Setup Functions
// ============================================================================

/**
 * Setup default mock implementations for all hooks
 */
function setupDefaultMocks(options: {
  weeks?: Array<{ date: string; hasConflict: boolean }>;
  weeksLoading?: boolean;
  weeksError?: Error | null;
  faculty?: Array<{ id: string; name: string }>;
  facultyLoading?: boolean;
  facultyError?: Error | null;
  mutationPending?: boolean;
  mutationSuccess?: boolean;
  mutationData?: unknown;
} = {}) {
  const {
    weeks = fmitMockFactories.fmitWeeksWithConflicts(),
    weeksLoading = false,
    weeksError = null,
    faculty = mockFacultyMembers,
    facultyLoading = false,
    facultyError = null,
    mutationPending = false,
    mutationSuccess = false,
    mutationData = null,
  } = options;

  const mockMutateAsync = jest.fn().mockResolvedValue(mockSuccessResponse);

  (swapHooks.useAvailableWeeks as jest.Mock).mockReturnValue({
    data: weeks,
    isLoading: weeksLoading,
    error: weeksError,
  });

  (swapHooks.useFacultyMembers as jest.Mock).mockReturnValue({
    data: faculty,
    isLoading: facultyLoading,
    error: facultyError,
  });

  (swapHooks.useCreateSwapRequest as jest.Mock).mockReturnValue({
    mutateAsync: mockMutateAsync,
    isPending: mutationPending,
    isSuccess: mutationSuccess,
    data: mutationData,
    error: null,
  });

  return { mockMutateAsync };
}

// ============================================================================
// Test Suite: FMIT Week Conflict Detection
// ============================================================================

describe('FMIT Week Detection', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // ==========================================================================
  // Conflict Alert Display Tests
  // ==========================================================================

  describe('Red Conflict Alert Display', () => {
    it('should display "(Has Conflict)" text when week hasConflict=true', () => {
      setupDefaultMocks({ weeks: fmitMockFactories.fmitWeeksWithConflicts() });

      render(<SwapRequestForm />, { wrapper: createWrapper() });

      // Verify conflict indicator text is present (may have multiple)
      const conflictTexts = screen.getAllByText(/Has Conflict/);
      expect(conflictTexts.length).toBeGreaterThan(0);
    });

    it('should display conflict indicator for each week with hasConflict=true', () => {
      setupDefaultMocks({ weeks: fmitMockFactories.fmitWeeksWithConflicts() });

      render(<SwapRequestForm />, { wrapper: createWrapper() });

      // Get all occurrences of "Has Conflict" text
      const conflictIndicators = screen.getAllByText(/Has Conflict/);

      // The mock data has 2 weeks with conflicts
      expect(conflictIndicators.length).toBe(2);
    });

    it('should NOT display conflict indicator when week hasConflict=false', () => {
      setupDefaultMocks({ weeks: fmitMockFactories.fmitWeeksNoConflicts() });

      render(<SwapRequestForm />, { wrapper: createWrapper() });

      // Verify no conflict indicator is present
      expect(screen.queryByText(/Has Conflict/)).not.toBeInTheDocument();
    });

    it('should display conflict indicator for single week with conflict', () => {
      setupDefaultMocks({ weeks: fmitMockFactories.singleWeekWithConflict() });

      render(<SwapRequestForm />, { wrapper: createWrapper() });

      expect(screen.getByText(/Has Conflict/)).toBeInTheDocument();
    });

    it('should display conflict indicator in week dropdown option', () => {
      setupDefaultMocks({ weeks: fmitMockFactories.fmitWeeksWithConflicts() });

      render(<SwapRequestForm />, { wrapper: createWrapper() });

      // The week select should contain the conflict text in its options
      const weekSelect = screen.getByRole('combobox') as HTMLSelectElement;
      const options = Array.from(weekSelect.options);

      // Find options that contain conflict indicator
      const conflictOptions = options.filter(opt => opt.textContent?.includes('Has Conflict'));
      expect(conflictOptions.length).toBe(2);
    });
  });

  // ==========================================================================
  // Schedule Context State Mocking Tests
  // ==========================================================================

  describe('Schedule Context State Mocking', () => {
    it('should correctly mock useAvailableWeeks hook with conflict data', () => {
      const mockWeeks = fmitMockFactories.fmitWeeksWithConflicts();
      setupDefaultMocks({ weeks: mockWeeks });

      render(<SwapRequestForm />, { wrapper: createWrapper() });

      // Verify hook was called
      expect(swapHooks.useAvailableWeeks).toHaveBeenCalled();

      // Verify weeks are rendered - find the week select combobox
      const weekSelect = screen.getByRole('combobox') as HTMLSelectElement;

      // Should have placeholder + all weeks (6 weeks + 1 placeholder)
      expect(weekSelect.options.length).toBe(mockWeeks.length + 1);
    });

    it('should handle loading state correctly', () => {
      setupDefaultMocks({ weeksLoading: true });

      render(<SwapRequestForm />, { wrapper: createWrapper() });

      // Should show loading indicator
      expect(screen.getByText(/loading form data/i)).toBeInTheDocument();
    });

    it('should handle error state correctly', () => {
      const mockError = new Error('Failed to fetch FMIT weeks');
      setupDefaultMocks({ weeksError: mockError });

      render(<SwapRequestForm />, { wrapper: createWrapper() });

      // Should display error message
      expect(screen.getByText(/error loading form data/i)).toBeInTheDocument();
      expect(screen.getByText(/failed to fetch fmit weeks/i)).toBeInTheDocument();
    });

    it('should handle empty weeks array', () => {
      setupDefaultMocks({ weeks: fmitMockFactories.emptyWeeks() });

      render(<SwapRequestForm />, { wrapper: createWrapper() });

      // Should show empty state message
      expect(
        screen.getByText(/you currently have no assigned FMIT weeks to swap/i)
      ).toBeInTheDocument();
    });

    it('should update UI when schedule context state changes', () => {
      // Initially empty
      setupDefaultMocks({ weeks: fmitMockFactories.emptyWeeks() });

      const wrapper = createWrapper();
      const { rerender } = render(<SwapRequestForm />, { wrapper });

      expect(
        screen.getByText(/you currently have no assigned FMIT weeks to swap/i)
      ).toBeInTheDocument();

      // Update mock to return weeks with conflicts
      setupDefaultMocks({ weeks: fmitMockFactories.fmitWeeksWithConflicts() });

      rerender(<SwapRequestForm />);

      // Now should show conflict indicator (there may be multiple)
      const conflictTexts = screen.getAllByText(/Has Conflict/);
      expect(conflictTexts.length).toBeGreaterThan(0);
    });
  });

  // ==========================================================================
  // Week Selection with Conflicts
  // ==========================================================================

  describe('Week Selection with Conflicts', () => {
    it('should allow selecting a week with conflict', async () => {
      const user = userEvent.setup();
      const mockWeeks = fmitMockFactories.fmitWeeksWithConflicts();
      const conflictWeek = mockWeeks.find(w => w.hasConflict);
      setupDefaultMocks({ weeks: mockWeeks });

      render(<SwapRequestForm />, { wrapper: createWrapper() });

      const weekSelect = screen.getByRole('combobox');
      await user.selectOptions(weekSelect, conflictWeek!.date);

      expect((weekSelect as HTMLSelectElement).value).toBe(conflictWeek!.date);
    });

    it('should allow selecting a week without conflict', async () => {
      const user = userEvent.setup();
      const mockWeeks = fmitMockFactories.fmitWeeksWithConflicts();
      const noConflictWeek = mockWeeks.find(w => !w.hasConflict);
      setupDefaultMocks({ weeks: mockWeeks });

      render(<SwapRequestForm />, { wrapper: createWrapper() });

      const weekSelect = screen.getByRole('combobox');
      await user.selectOptions(weekSelect, noConflictWeek!.date);

      expect((weekSelect as HTMLSelectElement).value).toBe(noConflictWeek!.date);
    });

    it('should submit swap request for week with conflict', async () => {
      const user = userEvent.setup();
      const mockWeeks = fmitMockFactories.fmitWeeksWithConflicts();
      const conflictWeek = mockWeeks.find(w => w.hasConflict);
      const { mockMutateAsync } = setupDefaultMocks({ weeks: mockWeeks });

      render(<SwapRequestForm />, { wrapper: createWrapper() });

      // Select week with conflict
      const weekSelect = screen.getByRole('combobox');
      await user.selectOptions(weekSelect, conflictWeek!.date);

      // Submit the form
      const submitButton = screen.getByRole('button', { name: /create request/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledWith(
          expect.objectContaining({
            weekToOffload: conflictWeek!.date,
          })
        );
      });
    });
  });

  // ==========================================================================
  // Edge Cases
  // ==========================================================================

  describe('Edge Cases', () => {
    it('should handle all weeks having conflicts', () => {
      setupDefaultMocks({ weeks: fmitMockFactories.fmitWeeksAllConflicts() });

      render(<SwapRequestForm />, { wrapper: createWrapper() });

      const conflictIndicators = screen.getAllByText(/Has Conflict/);
      expect(conflictIndicators.length).toBe(3);
    });

    it('should handle rapid state changes without errors', async () => {
      // Start with no conflicts
      setupDefaultMocks({ weeks: fmitMockFactories.fmitWeeksNoConflicts() });

      const wrapper = createWrapper();
      const { rerender } = render(<SwapRequestForm />, { wrapper });

      // Rapidly change to conflicts
      setupDefaultMocks({ weeks: fmitMockFactories.fmitWeeksAllConflicts() });
      rerender(<SwapRequestForm />);

      // Then back to no conflicts
      setupDefaultMocks({ weeks: fmitMockFactories.fmitWeeksNoConflicts() });
      rerender(<SwapRequestForm />);

      // Finally to mixed
      setupDefaultMocks({ weeks: fmitMockFactories.fmitWeeksWithConflicts() });
      rerender(<SwapRequestForm />);

      // Should show correct state (multiple conflicts possible)
      const conflictTexts = screen.getAllByText(/Has Conflict/);
      expect(conflictTexts.length).toBeGreaterThan(0);
    });

    it('should maintain conflict display after form submission attempt', async () => {
      const user = userEvent.setup();
      setupDefaultMocks({ weeks: fmitMockFactories.fmitWeeksWithConflicts() });

      render(<SwapRequestForm />, { wrapper: createWrapper() });

      // Try to submit without selecting (should fail validation)
      const submitButton = screen.getByRole('button', { name: /create request/i });
      await user.click(submitButton);

      // Conflict indicator should still be visible
      const conflictTexts = screen.getAllByText(/Has Conflict/);
      expect(conflictTexts.length).toBeGreaterThan(0);
    });

    it('should handle week dates at year boundaries', () => {
      const yearBoundaryWeeks = [
        { date: '2024-12-30', hasConflict: true },
        { date: '2025-01-06', hasConflict: false },
      ];
      setupDefaultMocks({ weeks: yearBoundaryWeeks });

      render(<SwapRequestForm />, { wrapper: createWrapper() });

      // Should display both weeks with appropriate conflict status
      const weekSelect = screen.getByRole('combobox') as HTMLSelectElement;
      expect(weekSelect.options.length).toBe(3); // placeholder + 2 weeks
      expect(screen.getByText(/Has Conflict/)).toBeInTheDocument();
    });
  });

  // ==========================================================================
  // Accessibility
  // ==========================================================================

  describe('Accessibility', () => {
    it('should have accessible week selection with conflict information', () => {
      setupDefaultMocks({ weeks: fmitMockFactories.fmitWeeksWithConflicts() });

      render(<SwapRequestForm />, { wrapper: createWrapper() });

      // The week select should be present as a combobox
      const weekSelect = screen.getByRole('combobox');
      expect(weekSelect).toBeInTheDocument();
    });

    it('should include conflict status in week option text for screen readers', () => {
      setupDefaultMocks({ weeks: fmitMockFactories.singleWeekWithConflict() });

      render(<SwapRequestForm />, { wrapper: createWrapper() });

      // The conflict status should be part of the option text
      const weekSelect = screen.getByRole('combobox') as HTMLSelectElement;
      const weekOption = Array.from(weekSelect.options).find(opt =>
        opt.textContent?.includes('Has Conflict')
      );
      expect(weekOption).toBeDefined();
    });
  });

  // ==========================================================================
  // Integration with Other Form Elements
  // ==========================================================================

  describe('Integration with Form Elements', () => {
    it('should allow complete form submission with conflict week', async () => {
      const user = userEvent.setup();
      const mockWeeks = fmitMockFactories.fmitWeeksWithConflicts();
      const conflictWeek = mockWeeks.find(w => w.hasConflict);
      const { mockMutateAsync } = setupDefaultMocks({ weeks: mockWeeks });

      render(<SwapRequestForm onSuccess={jest.fn()} />, { wrapper: createWrapper() });

      // Select week with conflict (first combobox on the page)
      const weekSelect = screen.getByRole('combobox');
      await user.selectOptions(weekSelect, conflictWeek!.date);

      // Add reason - find the textarea
      const reasonTextarea = screen.getByRole('textbox');
      await user.type(reasonTextarea, 'Conflict needs resolution');

      // Submit
      const submitButton = screen.getByRole('button', { name: /create request/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledWith({
          weekToOffload: conflictWeek!.date,
          reason: 'Conflict needs resolution',
          autoFindCandidates: true,
          preferredTargetFacultyId: undefined,
        });
      });
    });

    it('should work with specific faculty mode for conflict week', async () => {
      const user = userEvent.setup();
      const mockWeeks = fmitMockFactories.fmitWeeksWithConflicts();
      const conflictWeek = mockWeeks.find(w => w.hasConflict);
      const { mockMutateAsync } = setupDefaultMocks({ weeks: mockWeeks });

      render(<SwapRequestForm onSuccess={jest.fn()} />, { wrapper: createWrapper() });

      // Select week with conflict (first combobox on the page)
      const weekSelect = screen.getByRole('combobox');
      await user.selectOptions(weekSelect, conflictWeek!.date);

      // Switch to specific mode
      const specificRadio = screen.getByRole('radio', { name: /request specific faculty/i });
      await user.click(specificRadio);

      // Select faculty (now there are 2 comboboxes - week and faculty)
      const allComboboxes = screen.getAllByRole('combobox');
      const facultySelect = allComboboxes[1]; // Second combobox is faculty select
      await user.selectOptions(facultySelect, mockFacultyMembers[0].id);

      // Submit
      const submitButton = screen.getByRole('button', { name: /create request/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledWith({
          weekToOffload: conflictWeek!.date,
          reason: undefined,
          autoFindCandidates: false,
          preferredTargetFacultyId: mockFacultyMembers[0].id,
        });
      });
    });
  });
});

// ============================================================================
// Test Suite: FMIT Week Detection Mock Validation
// ============================================================================

describe('FMIT Detection Mock Validation', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should validate mock data factory produces correct structure', () => {
    const week = fmitMockFactories.fmitWeek({ date: '2025-03-15', hasConflict: true });

    expect(week).toHaveProperty('date', '2025-03-15');
    expect(week).toHaveProperty('hasConflict', true);
  });

  it('should validate weeks with conflicts factory has correct count', () => {
    const weeks = fmitMockFactories.fmitWeeksWithConflicts();
    const conflictCount = weeks.filter(w => w.hasConflict).length;

    expect(conflictCount).toBe(2);
  });

  it('should validate all conflict weeks factory', () => {
    const weeks = fmitMockFactories.fmitWeeksAllConflicts();

    expect(weeks.every(w => w.hasConflict)).toBe(true);
    expect(weeks.length).toBe(3);
  });

  it('should validate no conflicts factory', () => {
    const weeks = fmitMockFactories.fmitWeeksNoConflicts();

    expect(weeks.every(w => !w.hasConflict)).toBe(true);
  });
});
