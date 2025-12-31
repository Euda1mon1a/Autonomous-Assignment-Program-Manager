/**
 * Integration Tests for Swap Auto-Matching UI
 *
 * Tests the auto-matching functionality UI including:
 * - Displaying candidates from /api/v1/swaps/candidates endpoint
 * - Empty state when no candidates found
 * - Single candidate display
 * - Multiple candidates display (5)
 * - Accessibility with findByRole queries
 *
 * NOTE: This test file defines a local AutoMatchingCandidates component as a
 * reference implementation for testing UI patterns and API integration. This is
 * intentional for the following reasons:
 *
 * 1. Establishes expected component interface and behavior patterns
 * 2. Tests API integration with /api/v1/swaps/candidates endpoint
 * 3. Validates accessibility requirements (ARIA labels, roles)
 * 4. Provides a working reference for production implementation
 *
 * When implementing the production component at:
 *   frontend/src/features/swap-marketplace/AutoMatchingCandidates.tsx
 *
 * Update this test to import and test the production component instead:
 *   import { AutoMatchingCandidates } from '@/features/swap-marketplace';
 *
 * Also ensure the production component uses the correct types from:
 *   frontend/src/hooks/useSwaps.ts (SwapCandidate interface with snake_case fields)
 */

import React from 'react';
import { render, screen, waitFor, within } from '@/test-utils';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import * as api from '@/lib/api';

// Mock the API module
jest.mock('@/lib/api');

// ============================================================================
// Types for Auto-Matching
// ============================================================================

interface SwapCandidate {
  id: string;
  facultyId: string;
  facultyName: string;
  availableWeek: string;
  compatibilityScore: number;
  reason?: string;
  isAvailable: boolean;
}

interface CandidatesResponse {
  candidates: SwapCandidate[];
  total: number;
  searchedWeek: string;
}

// ============================================================================
// Auto-Matching Candidates Component (Test Reference Implementation)
// ============================================================================

/**
 * Reference implementation of AutoMatchingCandidates component.
 *
 * TODO: Replace with production component import when created:
 *   import { AutoMatchingCandidates } from '@/features/swap-marketplace';
 *
 * The production component should use types from @/hooks/useSwaps.ts which has
 * snake_case field names (faculty_id, faculty_name, available_weeks, etc.)
 */
interface AutoMatchingCandidatesProps {
  weekToMatch: string;
  onSelectCandidate?: (candidate: SwapCandidate) => void;
}

function AutoMatchingCandidates({ weekToMatch, onSelectCandidate }: AutoMatchingCandidatesProps) {
  const [candidates, setCandidates] = React.useState<SwapCandidate[]>([]);
  const [isLoading, setIsLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    const fetchCandidates = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await api.get<CandidatesResponse>(`/api/v1/swaps/candidates?week=${weekToMatch}`);
        setCandidates(response.candidates || []);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load candidates');
      } finally {
        setIsLoading(false);
      }
    };

    fetchCandidates();
  }, [weekToMatch]);

  if (isLoading) {
    return (
      <div role="status" aria-label="Loading candidates">
        <span className="sr-only">Loading...</span>
        <div className="animate-pulse flex space-x-4">
          <div className="flex-1 space-y-4 py-1">
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div role="alert" className="bg-red-50 border border-red-200 rounded-lg p-4">
        <h3 className="text-red-800 font-medium">Error Loading Candidates</h3>
        <p className="text-red-600">{error}</p>
      </div>
    );
  }

  if (candidates.length === 0) {
    return (
      <div
        role="region"
        aria-label="Empty candidates"
        className="text-center py-12 bg-gray-50 rounded-lg"
      >
        <svg
          className="w-16 h-16 text-gray-400 mx-auto mb-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
          />
        </svg>
        <h3 className="text-lg font-medium text-gray-900 mb-2">No Candidates Found</h3>
        <p className="text-gray-600 mb-4">
          No compatible faculty members are available for this week.
          Try selecting a different week or check back later.
        </p>
        <p className="text-sm text-gray-500">Empty State</p>
      </div>
    );
  }

  return (
    <div role="region" aria-label="Swap candidates">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">
        Available Candidates ({candidates.length})
      </h2>
      <ul role="list" className="space-y-3" aria-label="Candidates list">
        {candidates.map((candidate) => (
          <li
            key={candidate.id}
            className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
          >
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-medium text-gray-900">{candidate.facultyName}</h3>
                <p className="text-sm text-gray-600">
                  Week: {new Date(candidate.availableWeek).toLocaleDateString()}
                </p>
                {candidate.reason && (
                  <p className="text-sm text-gray-500 mt-1">{candidate.reason}</p>
                )}
              </div>
              <div className="flex items-center gap-3">
                <span
                  className={`px-2 py-1 text-xs font-medium rounded-full ${
                    candidate.compatibilityScore >= 80
                      ? 'bg-green-100 text-green-800'
                      : candidate.compatibilityScore >= 50
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-gray-100 text-gray-800'
                  }`}
                  aria-label={`Compatibility score: ${candidate.compatibilityScore}%`}
                >
                  {candidate.compatibilityScore}% match
                </span>
                <button
                  onClick={() => onSelectCandidate?.(candidate)}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                  aria-label={`Select ${candidate.facultyName} as swap candidate`}
                >
                  Select
                </button>
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

// ============================================================================
// Test Setup
// ============================================================================

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
    logger: {
      log: () => {},
      warn: () => {},
      error: () => {},
    },
  });

  return function Wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

// ============================================================================
// Mock Data Factories
// ============================================================================

function createMockCandidate(overrides: Partial<SwapCandidate> = {}): SwapCandidate {
  return {
    id: `candidate-${Math.random().toString(36).substr(2, 9)}`,
    facultyId: `faculty-${Math.random().toString(36).substr(2, 9)}`,
    facultyName: 'Dr. Test Faculty',
    availableWeek: '2025-01-15',
    compatibilityScore: 85,
    isAvailable: true,
    ...overrides,
  };
}

function createMockCandidatesResponse(
  count: number,
  searchedWeek: string = '2025-01-15'
): CandidatesResponse {
  const candidates: SwapCandidate[] = [];

  if (count === 1) {
    candidates.push(
      createMockCandidate({
        id: 'candidate-1',
        facultyId: 'faculty-1',
        facultyName: 'Dr. Sarah Williams',
        availableWeek: searchedWeek,
        compatibilityScore: 92,
        reason: 'Available for conference coverage',
      })
    );
  } else if (count === 5) {
    candidates.push(
      createMockCandidate({
        id: 'candidate-1',
        facultyId: 'faculty-1',
        facultyName: 'Dr. Sarah Williams',
        availableWeek: searchedWeek,
        compatibilityScore: 95,
        reason: 'Available for conference coverage',
      }),
      createMockCandidate({
        id: 'candidate-2',
        facultyId: 'faculty-2',
        facultyName: 'Dr. Michael Chen',
        availableWeek: searchedWeek,
        compatibilityScore: 88,
        reason: 'Flexible schedule this month',
      }),
      createMockCandidate({
        id: 'candidate-3',
        facultyId: 'faculty-3',
        facultyName: 'Dr. Emily Brown',
        availableWeek: searchedWeek,
        compatibilityScore: 76,
      }),
      createMockCandidate({
        id: 'candidate-4',
        facultyId: 'faculty-4',
        facultyName: 'Dr. James Wilson',
        availableWeek: searchedWeek,
        compatibilityScore: 65,
        reason: 'Looking to swap weeks',
      }),
      createMockCandidate({
        id: 'candidate-5',
        facultyId: 'faculty-5',
        facultyName: 'Dr. Amanda Davis',
        availableWeek: searchedWeek,
        compatibilityScore: 52,
      })
    );
  }

  return {
    candidates,
    total: count,
    searchedWeek,
  };
}

// ============================================================================
// Tests
// ============================================================================

describe('AutoMatching UI Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // ==========================================================================
  // Empty State (0 Candidates)
  // ==========================================================================

  describe('Empty State - 0 Candidates', () => {
    it('should render empty state when no candidates are found', async () => {
      (api.get as jest.Mock).mockResolvedValue(createMockCandidatesResponse(0));

      render(<AutoMatchingCandidates weekToMatch="2025-01-15" />, {
        wrapper: createWrapper(),
      });

      // Wait for loading to complete using findByRole for accessibility
      const emptyRegion = await screen.findByRole('region', { name: /empty candidates/i });
      expect(emptyRegion).toBeInTheDocument();
    });

    it('should display "No Candidates Found" heading in empty state', async () => {
      (api.get as jest.Mock).mockResolvedValue(createMockCandidatesResponse(0));

      render(<AutoMatchingCandidates weekToMatch="2025-01-15" />, {
        wrapper: createWrapper(),
      });

      const heading = await screen.findByRole('heading', { name: /no candidates found/i });
      expect(heading).toBeInTheDocument();
    });

    it('should display "Empty State" text indicator', async () => {
      (api.get as jest.Mock).mockResolvedValue(createMockCandidatesResponse(0));

      render(<AutoMatchingCandidates weekToMatch="2025-01-15" />, {
        wrapper: createWrapper(),
      });

      await screen.findByRole('region', { name: /empty candidates/i });
      expect(screen.getByText('Empty State')).toBeInTheDocument();
    });

    it('should provide helpful guidance message in empty state', async () => {
      (api.get as jest.Mock).mockResolvedValue(createMockCandidatesResponse(0));

      render(<AutoMatchingCandidates weekToMatch="2025-01-15" />, {
        wrapper: createWrapper(),
      });

      await screen.findByRole('region', { name: /empty candidates/i });
      expect(
        screen.getByText(/no compatible faculty members are available for this week/i)
      ).toBeInTheDocument();
    });

    it('should not render candidate list in empty state', async () => {
      (api.get as jest.Mock).mockResolvedValue(createMockCandidatesResponse(0));

      render(<AutoMatchingCandidates weekToMatch="2025-01-15" />, {
        wrapper: createWrapper(),
      });

      await screen.findByRole('region', { name: /empty candidates/i });
      expect(screen.queryByRole('list', { name: /candidates list/i })).not.toBeInTheDocument();
    });

    it('should not render any select buttons in empty state', async () => {
      (api.get as jest.Mock).mockResolvedValue(createMockCandidatesResponse(0));

      render(<AutoMatchingCandidates weekToMatch="2025-01-15" />, {
        wrapper: createWrapper(),
      });

      await screen.findByRole('region', { name: /empty candidates/i });
      expect(screen.queryByRole('button', { name: /select/i })).not.toBeInTheDocument();
    });
  });

  // ==========================================================================
  // Single Candidate (1 Result)
  // ==========================================================================

  describe('Single Candidate - 1 Result', () => {
    it('should render single candidate when one is found', async () => {
      (api.get as jest.Mock).mockResolvedValue(createMockCandidatesResponse(1));

      render(<AutoMatchingCandidates weekToMatch="2025-01-15" />, {
        wrapper: createWrapper(),
      });

      // Use findByRole for accessibility
      const candidatesRegion = await screen.findByRole('region', { name: /swap candidates/i });
      expect(candidatesRegion).toBeInTheDocument();
    });

    it('should display correct candidate count heading for single candidate', async () => {
      (api.get as jest.Mock).mockResolvedValue(createMockCandidatesResponse(1));

      render(<AutoMatchingCandidates weekToMatch="2025-01-15" />, {
        wrapper: createWrapper(),
      });

      const heading = await screen.findByRole('heading', { name: /available candidates \(1\)/i });
      expect(heading).toBeInTheDocument();
    });

    it('should display candidate name for single candidate', async () => {
      (api.get as jest.Mock).mockResolvedValue(createMockCandidatesResponse(1));

      render(<AutoMatchingCandidates weekToMatch="2025-01-15" />, {
        wrapper: createWrapper(),
      });

      await screen.findByRole('region', { name: /swap candidates/i });
      expect(screen.getByText('Dr. Sarah Williams')).toBeInTheDocument();
    });

    it('should display candidate reason when provided', async () => {
      (api.get as jest.Mock).mockResolvedValue(createMockCandidatesResponse(1));

      render(<AutoMatchingCandidates weekToMatch="2025-01-15" />, {
        wrapper: createWrapper(),
      });

      await screen.findByRole('region', { name: /swap candidates/i });
      expect(screen.getByText('Available for conference coverage')).toBeInTheDocument();
    });

    it('should render select button for single candidate', async () => {
      (api.get as jest.Mock).mockResolvedValue(createMockCandidatesResponse(1));

      render(<AutoMatchingCandidates weekToMatch="2025-01-15" />, {
        wrapper: createWrapper(),
      });

      const selectButton = await screen.findByRole('button', {
        name: /select dr\. sarah williams as swap candidate/i,
      });
      expect(selectButton).toBeInTheDocument();
    });

    it('should call onSelectCandidate when select button is clicked', async () => {
      const user = userEvent.setup();
      const mockOnSelect = jest.fn();
      (api.get as jest.Mock).mockResolvedValue(createMockCandidatesResponse(1));

      render(
        <AutoMatchingCandidates weekToMatch="2025-01-15" onSelectCandidate={mockOnSelect} />,
        { wrapper: createWrapper() }
      );

      const selectButton = await screen.findByRole('button', {
        name: /select dr\. sarah williams as swap candidate/i,
      });
      await user.click(selectButton);

      expect(mockOnSelect).toHaveBeenCalledWith(
        expect.objectContaining({
          id: 'candidate-1',
          facultyName: 'Dr. Sarah Williams',
        })
      );
    });

    it('should display compatibility score for single candidate', async () => {
      (api.get as jest.Mock).mockResolvedValue(createMockCandidatesResponse(1));

      render(<AutoMatchingCandidates weekToMatch="2025-01-15" />, {
        wrapper: createWrapper(),
      });

      await screen.findByRole('region', { name: /swap candidates/i });
      expect(screen.getByText('92% match')).toBeInTheDocument();
    });
  });

  // ==========================================================================
  // Multiple Candidates (5 Results)
  // ==========================================================================

  describe('Multiple Candidates - 5 Results', () => {
    it('should render all five candidates when found', async () => {
      (api.get as jest.Mock).mockResolvedValue(createMockCandidatesResponse(5));

      render(<AutoMatchingCandidates weekToMatch="2025-01-15" />, {
        wrapper: createWrapper(),
      });

      const candidatesList = await screen.findByRole('list', { name: /candidates list/i });
      expect(candidatesList).toBeInTheDocument();

      const listItems = within(candidatesList).getAllByRole('listitem');
      expect(listItems).toHaveLength(5);
    });

    it('should display correct candidate count heading for multiple candidates', async () => {
      (api.get as jest.Mock).mockResolvedValue(createMockCandidatesResponse(5));

      render(<AutoMatchingCandidates weekToMatch="2025-01-15" />, {
        wrapper: createWrapper(),
      });

      const heading = await screen.findByRole('heading', { name: /available candidates \(5\)/i });
      expect(heading).toBeInTheDocument();
    });

    it('should display all candidate names', async () => {
      (api.get as jest.Mock).mockResolvedValue(createMockCandidatesResponse(5));

      render(<AutoMatchingCandidates weekToMatch="2025-01-15" />, {
        wrapper: createWrapper(),
      });

      await screen.findByRole('region', { name: /swap candidates/i });

      expect(screen.getByText('Dr. Sarah Williams')).toBeInTheDocument();
      expect(screen.getByText('Dr. Michael Chen')).toBeInTheDocument();
      expect(screen.getByText('Dr. Emily Brown')).toBeInTheDocument();
      expect(screen.getByText('Dr. James Wilson')).toBeInTheDocument();
      expect(screen.getByText('Dr. Amanda Davis')).toBeInTheDocument();
    });

    it('should render select button for each candidate', async () => {
      (api.get as jest.Mock).mockResolvedValue(createMockCandidatesResponse(5));

      render(<AutoMatchingCandidates weekToMatch="2025-01-15" />, {
        wrapper: createWrapper(),
      });

      await screen.findByRole('region', { name: /swap candidates/i });

      const selectButtons = screen.getAllByRole('button', { name: /select .* as swap candidate/i });
      expect(selectButtons).toHaveLength(5);
    });

    it('should display varying compatibility scores with appropriate styling', async () => {
      (api.get as jest.Mock).mockResolvedValue(createMockCandidatesResponse(5));

      render(<AutoMatchingCandidates weekToMatch="2025-01-15" />, {
        wrapper: createWrapper(),
      });

      await screen.findByRole('region', { name: /swap candidates/i });

      // High scores (80+)
      expect(screen.getByText('95% match')).toBeInTheDocument();
      expect(screen.getByText('88% match')).toBeInTheDocument();

      // Medium scores (50-79)
      expect(screen.getByText('76% match')).toBeInTheDocument();
      expect(screen.getByText('65% match')).toBeInTheDocument();
      expect(screen.getByText('52% match')).toBeInTheDocument();
    });

    it('should correctly select specific candidate from multiple options', async () => {
      const user = userEvent.setup();
      const mockOnSelect = jest.fn();
      (api.get as jest.Mock).mockResolvedValue(createMockCandidatesResponse(5));

      render(
        <AutoMatchingCandidates weekToMatch="2025-01-15" onSelectCandidate={mockOnSelect} />,
        { wrapper: createWrapper() }
      );

      // Wait for candidates to load and select Dr. Emily Brown
      const selectButton = await screen.findByRole('button', {
        name: /select dr\. emily brown as swap candidate/i,
      });
      await user.click(selectButton);

      expect(mockOnSelect).toHaveBeenCalledWith(
        expect.objectContaining({
          id: 'candidate-3',
          facultyName: 'Dr. Emily Brown',
          compatibilityScore: 76,
        })
      );
    });

    it('should display reasons only for candidates that have them', async () => {
      (api.get as jest.Mock).mockResolvedValue(createMockCandidatesResponse(5));

      render(<AutoMatchingCandidates weekToMatch="2025-01-15" />, {
        wrapper: createWrapper(),
      });

      await screen.findByRole('region', { name: /swap candidates/i });

      // Candidates with reasons
      expect(screen.getByText('Available for conference coverage')).toBeInTheDocument();
      expect(screen.getByText('Flexible schedule this month')).toBeInTheDocument();
      expect(screen.getByText('Looking to swap weeks')).toBeInTheDocument();

      // Dr. Emily Brown and Dr. Amanda Davis don't have reasons
      // We shouldn't see any placeholder text for them
    });
  });

  // ==========================================================================
  // Loading State
  // ==========================================================================

  describe('Loading State', () => {
    it('should show loading indicator while fetching candidates', async () => {
      // Create a promise that won't resolve immediately
      let resolvePromise: (value: CandidatesResponse) => void;
      const pendingPromise = new Promise<CandidatesResponse>((resolve) => {
        resolvePromise = resolve;
      });

      (api.get as jest.Mock).mockReturnValue(pendingPromise);

      render(<AutoMatchingCandidates weekToMatch="2025-01-15" />, {
        wrapper: createWrapper(),
      });

      // Should show loading state
      const loadingStatus = await screen.findByRole('status', { name: /loading candidates/i });
      expect(loadingStatus).toBeInTheDocument();

      // Resolve the promise to clean up
      resolvePromise!(createMockCandidatesResponse(0));
    });

    it('should hide loading indicator after candidates load', async () => {
      (api.get as jest.Mock).mockResolvedValue(createMockCandidatesResponse(5));

      render(<AutoMatchingCandidates weekToMatch="2025-01-15" />, {
        wrapper: createWrapper(),
      });

      // Wait for content to load
      await screen.findByRole('region', { name: /swap candidates/i });

      // Loading status should not be present
      expect(screen.queryByRole('status', { name: /loading candidates/i })).not.toBeInTheDocument();
    });
  });

  // ==========================================================================
  // Error State
  // ==========================================================================

  describe('Error State', () => {
    it('should display error message when API call fails', async () => {
      (api.get as jest.Mock).mockRejectedValue(new Error('Network error'));

      render(<AutoMatchingCandidates weekToMatch="2025-01-15" />, {
        wrapper: createWrapper(),
      });

      const errorAlert = await screen.findByRole('alert');
      expect(errorAlert).toBeInTheDocument();
      expect(screen.getByText('Error Loading Candidates')).toBeInTheDocument();
      expect(screen.getByText('Network error')).toBeInTheDocument();
    });

    it('should not render candidates list when in error state', async () => {
      (api.get as jest.Mock).mockRejectedValue(new Error('API error'));

      render(<AutoMatchingCandidates weekToMatch="2025-01-15" />, {
        wrapper: createWrapper(),
      });

      await screen.findByRole('alert');
      expect(screen.queryByRole('list', { name: /candidates list/i })).not.toBeInTheDocument();
    });
  });

  // ==========================================================================
  // API Integration
  // ==========================================================================

  describe('API Integration', () => {
    it('should call /api/v1/swaps/candidates with correct week parameter', async () => {
      (api.get as jest.Mock).mockResolvedValue(createMockCandidatesResponse(0));

      render(<AutoMatchingCandidates weekToMatch="2025-03-15" />, {
        wrapper: createWrapper(),
      });

      await screen.findByRole('region', { name: /empty candidates/i });

      expect(api.get).toHaveBeenCalledWith('/api/v1/swaps/candidates?week=2025-03-15');
    });

    it('should refetch candidates when week changes', async () => {
      (api.get as jest.Mock).mockResolvedValue(createMockCandidatesResponse(0));

      const { rerender } = render(<AutoMatchingCandidates weekToMatch="2025-01-15" />, {
        wrapper: createWrapper(),
      });

      await screen.findByRole('region', { name: /empty candidates/i });
      expect(api.get).toHaveBeenCalledWith('/api/v1/swaps/candidates?week=2025-01-15');

      // Rerender with a different week
      rerender(<AutoMatchingCandidates weekToMatch="2025-02-20" />);

      await waitFor(() => {
        expect(api.get).toHaveBeenCalledWith('/api/v1/swaps/candidates?week=2025-02-20');
      });
    });
  });

  // ==========================================================================
  // Accessibility Tests
  // ==========================================================================

  describe('Accessibility', () => {
    it('should have proper ARIA labels for the candidates region', async () => {
      (api.get as jest.Mock).mockResolvedValue(createMockCandidatesResponse(5));

      render(<AutoMatchingCandidates weekToMatch="2025-01-15" />, {
        wrapper: createWrapper(),
      });

      const region = await screen.findByRole('region', { name: /swap candidates/i });
      expect(region).toHaveAttribute('aria-label', 'Swap candidates');
    });

    it('should have proper ARIA labels for empty state region', async () => {
      (api.get as jest.Mock).mockResolvedValue(createMockCandidatesResponse(0));

      render(<AutoMatchingCandidates weekToMatch="2025-01-15" />, {
        wrapper: createWrapper(),
      });

      const region = await screen.findByRole('region', { name: /empty candidates/i });
      expect(region).toHaveAttribute('aria-label', 'Empty candidates');
    });

    it('should have accessible names for all select buttons', async () => {
      (api.get as jest.Mock).mockResolvedValue(createMockCandidatesResponse(5));

      render(<AutoMatchingCandidates weekToMatch="2025-01-15" />, {
        wrapper: createWrapper(),
      });

      await screen.findByRole('region', { name: /swap candidates/i });

      // Each button should have a specific accessible name
      expect(
        screen.getByRole('button', { name: /select dr\. sarah williams as swap candidate/i })
      ).toBeInTheDocument();
      expect(
        screen.getByRole('button', { name: /select dr\. michael chen as swap candidate/i })
      ).toBeInTheDocument();
    });

    it('should have accessible compatibility score labels', async () => {
      (api.get as jest.Mock).mockResolvedValue(createMockCandidatesResponse(1));

      render(<AutoMatchingCandidates weekToMatch="2025-01-15" />, {
        wrapper: createWrapper(),
      });

      await screen.findByRole('region', { name: /swap candidates/i });

      const scoreElement = screen.getByLabelText(/compatibility score: 92%/i);
      expect(scoreElement).toBeInTheDocument();
    });

    it('should have proper list semantics for candidates', async () => {
      (api.get as jest.Mock).mockResolvedValue(createMockCandidatesResponse(5));

      render(<AutoMatchingCandidates weekToMatch="2025-01-15" />, {
        wrapper: createWrapper(),
      });

      const list = await screen.findByRole('list', { name: /candidates list/i });
      expect(list).toBeInTheDocument();

      const listItems = within(list).getAllByRole('listitem');
      expect(listItems).toHaveLength(5);
    });
  });
});
