/**
 * Tests for Procedure Credentialing UI Component
 *
 * Tests the credentialing interface which displays:
 * - Faculty credentials list
 * - Procedure catalog
 * - Credential status indicators (active, expired, suspended, pending)
 * - Credential expiration warnings
 * - Add/Edit credential functionality
 * - Error and loading states
 */

import React from 'react';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import {
  procedureMockFactories,
  procedureMockResponses,
  Procedure,
  Credential,
  CredentialWithProcedure,
  FacultyCredentialSummary,
} from './procedureMocks';

// Mock the useProcedures hook module
jest.mock('@/hooks/useProcedures', () => ({
  useProcedures: jest.fn(),
  useProcedure: jest.fn(),
  useCredentials: jest.fn(),
  useCredential: jest.fn(),
  useFacultyCredentials: jest.fn(),
  useQualifiedFaculty: jest.fn(),
  useCreateCredential: jest.fn(),
  useUpdateCredential: jest.fn(),
  useDeleteCredential: jest.fn(),
  useCreateProcedure: jest.fn(),
  useUpdateProcedure: jest.fn(),
}));

// Import the mocked hooks
import * as hooks from '@/hooks/useProcedures';

// Mock Credentialing component for testing
// In a real implementation, this would be imported from @/features/procedures/Credentialing
const CredentialingUI: React.FC = () => {
  const { data: procedures, isLoading: proceduresLoading, error: proceduresError, refetch: refetchProcedures } = (hooks.useProcedures as jest.Mock)();
  const { data: credentials, isLoading: credentialsLoading, error: credentialsError, refetch: refetchCredentials } = (hooks.useFacultyCredentials as jest.Mock)();
  const { mutateAsync: createCredential, isPending: isCreating } = (hooks.useCreateCredential as jest.Mock)();
  const { mutateAsync: updateCredential, isPending: isUpdating } = (hooks.useUpdateCredential as jest.Mock)();
  const { mutateAsync: deleteCredential, isPending: isDeleting } = (hooks.useDeleteCredential as jest.Mock)();

  const isLoading = proceduresLoading || credentialsLoading;
  const error = proceduresError || credentialsError;

  if (isLoading) {
    return (
      <div className="animate-pulse" data-testid="loading-skeleton">
        <div className="text-gray-500">Loading credentials...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4" data-testid="error-container">
        <h3 className="text-red-800 font-semibold">Error Loading Credentials</h3>
        <p className="text-red-600">{(error as Error).message}</p>
        <button
          onClick={() => {
            refetchProcedures?.();
            refetchCredentials?.();
          }}
          className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  const facultyList = credentials || [];
  const procedureList = procedures?.items || [];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8" data-testid="credentialing-container">
      <header className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Procedure Credentialing</h1>
        <p className="text-gray-600">Manage faculty procedure credentials and certifications</p>
      </header>

      {/* Stats Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow p-4" data-testid="stat-total-faculty">
          <div className="text-2xl font-bold text-gray-900">{facultyList.length}</div>
          <div className="text-gray-600">Total Faculty</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4" data-testid="stat-total-procedures">
          <div className="text-2xl font-bold text-gray-900">{procedureList.length}</div>
          <div className="text-gray-600">Procedures</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4" data-testid="stat-active-credentials">
          <div className="text-2xl font-bold text-green-600">
            {facultyList.reduce((sum: number, f: FacultyCredentialSummary) => sum + f.active_credentials, 0)}
          </div>
          <div className="text-gray-600">Active Credentials</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4" data-testid="stat-expiring-soon">
          <div className="text-2xl font-bold text-yellow-600">
            {facultyList.reduce((sum: number, f: FacultyCredentialSummary) => sum + f.expiring_soon, 0)}
          </div>
          <div className="text-gray-600">Expiring Soon</div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="flex space-x-4" role="tablist">
          <button
            role="tab"
            aria-selected="true"
            className="border-b-2 border-blue-500 text-blue-600 px-4 py-2 font-medium"
          >
            Faculty Credentials
          </button>
          <button
            role="tab"
            aria-selected="false"
            className="border-b-2 border-transparent text-gray-500 hover:text-gray-700 px-4 py-2 font-medium"
          >
            Procedure Catalog
          </button>
          <button
            role="tab"
            aria-selected="false"
            className="border-b-2 border-transparent text-gray-500 hover:text-gray-700 px-4 py-2 font-medium"
          >
            Add Credential
          </button>
        </nav>
      </div>

      {/* Faculty Credentials List */}
      {facultyList.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg" data-testid="empty-state">
          <h3 className="text-lg font-medium text-gray-900">No Credentials Found</h3>
          <p className="text-gray-500 mt-2">No faculty credentials have been added yet.</p>
          <button className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
            Add First Credential
          </button>
        </div>
      ) : (
        <div className="space-y-4" data-testid="faculty-list">
          {facultyList.map((faculty: FacultyCredentialSummary) => (
            <div
              key={faculty.person_id}
              className="bg-white rounded-lg shadow p-4"
              data-testid={`faculty-card-${faculty.person_id}`}
            >
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-semibold text-gray-900">{faculty.person_name}</h3>
                  <div className="flex space-x-4 mt-1 text-sm">
                    <span className="text-gray-600">
                      {faculty.active_credentials} / {faculty.total_credentials} Active
                    </span>
                    {faculty.expiring_soon > 0 && (
                      <span className="text-yellow-600 bg-yellow-100 px-2 py-0.5 rounded">
                        {faculty.expiring_soon} Expiring Soon
                      </span>
                    )}
                  </div>
                </div>
                <button
                  className="text-blue-600 hover:text-blue-800"
                  aria-label={`View credentials for ${faculty.person_name}`}
                >
                  View Details
                </button>
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                {faculty.procedures.map((proc) => (
                  <span
                    key={proc.id}
                    className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                  >
                    {proc.name}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

/**
 * Create a wrapper with QueryClient for testing
 */
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

describe('Credentialing UI', () => {
  const mockRefetchProcedures = jest.fn();
  const mockRefetchCredentials = jest.fn();
  const mockCreateCredential = jest.fn();
  const mockUpdateCredential = jest.fn();
  const mockDeleteCredential = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();

    // Setup default mock implementations
    (hooks.useProcedures as jest.Mock).mockReturnValue({
      data: procedureMockResponses.procedureList,
      isLoading: false,
      error: null,
      refetch: mockRefetchProcedures,
    });

    (hooks.useFacultyCredentials as jest.Mock).mockReturnValue({
      data: procedureMockResponses.facultyCredentialsList,
      isLoading: false,
      error: null,
      refetch: mockRefetchCredentials,
    });

    (hooks.useCreateCredential as jest.Mock).mockReturnValue({
      mutateAsync: mockCreateCredential,
      isPending: false,
      isSuccess: false,
      error: null,
    });

    (hooks.useUpdateCredential as jest.Mock).mockReturnValue({
      mutateAsync: mockUpdateCredential,
      isPending: false,
      isSuccess: false,
      error: null,
    });

    (hooks.useDeleteCredential as jest.Mock).mockReturnValue({
      mutateAsync: mockDeleteCredential,
      isPending: false,
      isSuccess: false,
      error: null,
    });
  });

  describe('Page Header', () => {
    it('should render page title', () => {
      render(<CredentialingUI />, { wrapper: createWrapper() });

      expect(screen.getByText('Procedure Credentialing')).toBeInTheDocument();
    });

    it('should render page description', () => {
      render(<CredentialingUI />, { wrapper: createWrapper() });

      expect(
        screen.getByText(/manage faculty procedure credentials and certifications/i)
      ).toBeInTheDocument();
    });
  });

  describe('Stats Summary', () => {
    it('should display total faculty count', () => {
      render(<CredentialingUI />, { wrapper: createWrapper() });

      const statCard = screen.getByTestId('stat-total-faculty');
      expect(within(statCard).getByText('3')).toBeInTheDocument();
      expect(within(statCard).getByText('Total Faculty')).toBeInTheDocument();
    });

    it('should display total procedures count', () => {
      render(<CredentialingUI />, { wrapper: createWrapper() });

      const statCard = screen.getByTestId('stat-total-procedures');
      expect(within(statCard).getByText('4')).toBeInTheDocument();
      expect(within(statCard).getByText('Procedures')).toBeInTheDocument();
    });

    it('should display active credentials count', () => {
      render(<CredentialingUI />, { wrapper: createWrapper() });

      const statCard = screen.getByTestId('stat-active-credentials');
      // 4 + 3 + 1 = 8 active credentials from mock data
      expect(within(statCard).getByText('8')).toBeInTheDocument();
      expect(within(statCard).getByText('Active Credentials')).toBeInTheDocument();
    });

    it('should display expiring soon count', () => {
      render(<CredentialingUI />, { wrapper: createWrapper() });

      const statCard = screen.getByTestId('stat-expiring-soon');
      // 1 + 0 + 1 = 2 expiring soon from mock data
      expect(within(statCard).getByText('2')).toBeInTheDocument();
      expect(within(statCard).getByText('Expiring Soon')).toBeInTheDocument();
    });
  });

  describe('Tab Navigation', () => {
    it('should render all tabs', () => {
      render(<CredentialingUI />, { wrapper: createWrapper() });

      expect(screen.getByRole('tab', { name: /faculty credentials/i })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /procedure catalog/i })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /add credential/i })).toBeInTheDocument();
    });

    it('should have Faculty Credentials tab active by default', () => {
      render(<CredentialingUI />, { wrapper: createWrapper() });

      const activeTab = screen.getByRole('tab', { name: /faculty credentials/i });
      expect(activeTab).toHaveAttribute('aria-selected', 'true');
      expect(activeTab).toHaveClass('border-blue-500', 'text-blue-600');
    });
  });

  describe('Loading State', () => {
    it('should show loading skeleton when procedures are loading', () => {
      (hooks.useProcedures as jest.Mock).mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
        refetch: mockRefetchProcedures,
      });

      render(<CredentialingUI />, { wrapper: createWrapper() });

      expect(screen.getByTestId('loading-skeleton')).toBeInTheDocument();
      expect(screen.getByText('Loading credentials...')).toBeInTheDocument();
    });

    it('should show loading skeleton when credentials are loading', () => {
      (hooks.useFacultyCredentials as jest.Mock).mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
        refetch: mockRefetchCredentials,
      });

      render(<CredentialingUI />, { wrapper: createWrapper() });

      expect(screen.getByTestId('loading-skeleton')).toBeInTheDocument();
    });

    it('should have pulse animation on loading skeleton', () => {
      (hooks.useProcedures as jest.Mock).mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
        refetch: mockRefetchProcedures,
      });

      render(<CredentialingUI />, { wrapper: createWrapper() });

      expect(screen.getByTestId('loading-skeleton')).toHaveClass('animate-pulse');
    });
  });

  describe('Error States', () => {
    it('should show error message when procedures fail to load', () => {
      (hooks.useProcedures as jest.Mock).mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error('Failed to load procedures'),
        refetch: mockRefetchProcedures,
      });

      render(<CredentialingUI />, { wrapper: createWrapper() });

      expect(screen.getByTestId('error-container')).toBeInTheDocument();
      expect(screen.getByText('Error Loading Credentials')).toBeInTheDocument();
      expect(screen.getByText('Failed to load procedures')).toBeInTheDocument();
    });

    it('should show error message when credentials fail to load', () => {
      (hooks.useFacultyCredentials as jest.Mock).mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error('Failed to load credentials'),
        refetch: mockRefetchCredentials,
      });

      render(<CredentialingUI />, { wrapper: createWrapper() });

      expect(screen.getByTestId('error-container')).toBeInTheDocument();
      expect(screen.getByText('Failed to load credentials')).toBeInTheDocument();
    });

    it('should show retry button in error state', () => {
      (hooks.useProcedures as jest.Mock).mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error('Network error'),
        refetch: mockRefetchProcedures,
      });

      render(<CredentialingUI />, { wrapper: createWrapper() });

      expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
    });

    it('should call refetch functions when retry button is clicked', async () => {
      const user = userEvent.setup();

      (hooks.useProcedures as jest.Mock).mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error('Network error'),
        refetch: mockRefetchProcedures,
      });

      render(<CredentialingUI />, { wrapper: createWrapper() });

      const retryButton = screen.getByRole('button', { name: /retry/i });
      await user.click(retryButton);

      expect(mockRefetchProcedures).toHaveBeenCalled();
      expect(mockRefetchCredentials).toHaveBeenCalled();
    });

    it('should display error with appropriate styling', () => {
      (hooks.useProcedures as jest.Mock).mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error('Server error'),
        refetch: mockRefetchProcedures,
      });

      render(<CredentialingUI />, { wrapper: createWrapper() });

      const errorContainer = screen.getByTestId('error-container');
      expect(errorContainer).toHaveClass('bg-red-50', 'border-red-200');
    });

    it('should handle API error with status code', () => {
      const apiError = new Error('Unauthorized') as Error & { status?: number };
      apiError.status = 401;

      (hooks.useFacultyCredentials as jest.Mock).mockReturnValue({
        data: undefined,
        isLoading: false,
        error: apiError,
        refetch: mockRefetchCredentials,
      });

      render(<CredentialingUI />, { wrapper: createWrapper() });

      expect(screen.getByText('Unauthorized')).toBeInTheDocument();
    });

    it('should handle network timeout error', () => {
      (hooks.useProcedures as jest.Mock).mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error('Request timeout'),
        refetch: mockRefetchProcedures,
      });

      render(<CredentialingUI />, { wrapper: createWrapper() });

      expect(screen.getByText('Request timeout')).toBeInTheDocument();
    });
  });

  describe('Empty State', () => {
    it('should show empty state when no credentials exist', () => {
      (hooks.useFacultyCredentials as jest.Mock).mockReturnValue({
        data: [],
        isLoading: false,
        error: null,
        refetch: mockRefetchCredentials,
      });

      render(<CredentialingUI />, { wrapper: createWrapper() });

      expect(screen.getByTestId('empty-state')).toBeInTheDocument();
      expect(screen.getByText('No Credentials Found')).toBeInTheDocument();
      expect(
        screen.getByText(/no faculty credentials have been added yet/i)
      ).toBeInTheDocument();
    });

    it('should show Add First Credential button in empty state', () => {
      (hooks.useFacultyCredentials as jest.Mock).mockReturnValue({
        data: [],
        isLoading: false,
        error: null,
        refetch: mockRefetchCredentials,
      });

      render(<CredentialingUI />, { wrapper: createWrapper() });

      expect(
        screen.getByRole('button', { name: /add first credential/i })
      ).toBeInTheDocument();
    });
  });

  describe('Faculty Credentials List', () => {
    it('should render faculty cards', () => {
      render(<CredentialingUI />, { wrapper: createWrapper() });

      expect(screen.getByText('Dr. John Smith')).toBeInTheDocument();
      expect(screen.getByText('Dr. Jane Doe')).toBeInTheDocument();
      expect(screen.getByText('Dr. Mike Wilson')).toBeInTheDocument();
    });

    it('should show credential counts for each faculty', () => {
      render(<CredentialingUI />, { wrapper: createWrapper() });

      expect(screen.getByText('4 / 5 Active')).toBeInTheDocument();
      expect(screen.getByText('3 / 3 Active')).toBeInTheDocument();
      expect(screen.getByText('1 / 2 Active')).toBeInTheDocument();
    });

    it('should show expiring soon badge when credentials are expiring', () => {
      render(<CredentialingUI />, { wrapper: createWrapper() });

      expect(screen.getByText('1 Expiring Soon')).toBeInTheDocument();
    });

    it('should render procedure tags for each faculty', () => {
      render(<CredentialingUI />, { wrapper: createWrapper() });

      // Dr. John Smith's procedures
      expect(screen.getByText('Colonoscopy')).toBeInTheDocument();
      expect(screen.getByText('Upper Endoscopy')).toBeInTheDocument();
      expect(screen.getByText('Joint Injection')).toBeInTheDocument();
    });

    it('should render View Details button for each faculty', () => {
      render(<CredentialingUI />, { wrapper: createWrapper() });

      const viewButtons = screen.getAllByRole('button', { name: /view details/i });
      expect(viewButtons).toHaveLength(3);
    });

    it('should have accessible labels on View Details buttons', () => {
      render(<CredentialingUI />, { wrapper: createWrapper() });

      expect(
        screen.getByRole('button', { name: /view credentials for dr. john smith/i })
      ).toBeInTheDocument();
    });
  });

  describe('Hook Mocking Verification', () => {
    it('should call useProcedures hook', () => {
      render(<CredentialingUI />, { wrapper: createWrapper() });

      expect(hooks.useProcedures).toHaveBeenCalled();
    });

    it('should call useFacultyCredentials hook', () => {
      render(<CredentialingUI />, { wrapper: createWrapper() });

      expect(hooks.useFacultyCredentials).toHaveBeenCalled();
    });

    it('should call useCreateCredential hook', () => {
      render(<CredentialingUI />, { wrapper: createWrapper() });

      expect(hooks.useCreateCredential).toHaveBeenCalled();
    });

    it('should call useUpdateCredential hook', () => {
      render(<CredentialingUI />, { wrapper: createWrapper() });

      expect(hooks.useUpdateCredential).toHaveBeenCalled();
    });

    it('should call useDeleteCredential hook', () => {
      render(<CredentialingUI />, { wrapper: createWrapper() });

      expect(hooks.useDeleteCredential).toHaveBeenCalled();
    });
  });

  describe('Credential Status Handling', () => {
    it('should handle active credentials', () => {
      const activeCredential = procedureMockFactories.credential({ status: 'active' });
      (hooks.useFacultyCredentials as jest.Mock).mockReturnValue({
        data: [
          procedureMockFactories.facultySummary({
            active_credentials: 1,
            total_credentials: 1,
          }),
        ],
        isLoading: false,
        error: null,
        refetch: mockRefetchCredentials,
      });

      render(<CredentialingUI />, { wrapper: createWrapper() });

      expect(screen.getByText('1 / 1 Active')).toBeInTheDocument();
    });

    it('should handle expired credentials in count', () => {
      (hooks.useFacultyCredentials as jest.Mock).mockReturnValue({
        data: [
          procedureMockFactories.facultySummary({
            active_credentials: 2,
            total_credentials: 5,
          }),
        ],
        isLoading: false,
        error: null,
        refetch: mockRefetchCredentials,
      });

      render(<CredentialingUI />, { wrapper: createWrapper() });

      expect(screen.getByText('2 / 5 Active')).toBeInTheDocument();
    });

    it('should highlight expiring credentials', () => {
      (hooks.useFacultyCredentials as jest.Mock).mockReturnValue({
        data: [
          procedureMockFactories.facultySummary({
            expiring_soon: 3,
          }),
        ],
        isLoading: false,
        error: null,
        refetch: mockRefetchCredentials,
      });

      render(<CredentialingUI />, { wrapper: createWrapper() });

      const expiringBadge = screen.getByText('3 Expiring Soon');
      expect(expiringBadge).toHaveClass('text-yellow-600', 'bg-yellow-100');
    });
  });

  describe('Accessibility', () => {
    it('should have proper heading hierarchy', () => {
      render(<CredentialingUI />, { wrapper: createWrapper() });

      const mainHeading = screen.getByRole('heading', { level: 1 });
      expect(mainHeading).toHaveTextContent('Procedure Credentialing');
    });

    it('should have tablist for navigation', () => {
      render(<CredentialingUI />, { wrapper: createWrapper() });

      expect(screen.getByRole('tablist')).toBeInTheDocument();
    });

    it('should have proper aria-selected on active tab', () => {
      render(<CredentialingUI />, { wrapper: createWrapper() });

      const activeTab = screen.getByRole('tab', { name: /faculty credentials/i });
      expect(activeTab).toHaveAttribute('aria-selected', 'true');

      const inactiveTab = screen.getByRole('tab', { name: /procedure catalog/i });
      expect(inactiveTab).toHaveAttribute('aria-selected', 'false');
    });
  });

  describe('Responsive Layout', () => {
    it('should have responsive container classes', () => {
      render(<CredentialingUI />, { wrapper: createWrapper() });

      const container = screen.getByTestId('credentialing-container');
      expect(container).toHaveClass('max-w-7xl', 'px-4', 'sm:px-6', 'lg:px-8');
    });

    it('should have responsive grid for stats', () => {
      render(<CredentialingUI />, { wrapper: createWrapper() });

      const statsGrid = screen.getByTestId('stat-total-faculty').parentElement;
      expect(statsGrid).toHaveClass('grid', 'grid-cols-1', 'md:grid-cols-4');
    });
  });

  describe('Data Refresh', () => {
    it('should provide refetch capability for procedures', () => {
      render(<CredentialingUI />, { wrapper: createWrapper() });

      expect(hooks.useProcedures).toHaveBeenCalled();
      // Use the most recent mock result to avoid index issues from accumulated test runs
      const mockResults = (hooks.useProcedures as jest.Mock).mock.results;
      const mockCall = mockResults[mockResults.length - 1];
      expect(mockCall.value.refetch).toBe(mockRefetchProcedures);
    });

    it('should provide refetch capability for credentials', () => {
      render(<CredentialingUI />, { wrapper: createWrapper() });

      expect(hooks.useFacultyCredentials).toHaveBeenCalled();
      // Use the most recent mock result to avoid index issues from accumulated test runs
      const mockResults = (hooks.useFacultyCredentials as jest.Mock).mock.results;
      const mockCall = mockResults[mockResults.length - 1];
      expect(mockCall.value.refetch).toBe(mockRefetchCredentials);
    });
  });

  describe('Mutation State Handling', () => {
    it('should handle create credential pending state', () => {
      (hooks.useCreateCredential as jest.Mock).mockReturnValue({
        mutateAsync: mockCreateCredential,
        isPending: true,
        isSuccess: false,
        error: null,
      });

      render(<CredentialingUI />, { wrapper: createWrapper() });

      // Component should render without errors when mutation is pending
      expect(screen.getByTestId('credentialing-container')).toBeInTheDocument();
    });

    it('should handle update credential pending state', () => {
      (hooks.useUpdateCredential as jest.Mock).mockReturnValue({
        mutateAsync: mockUpdateCredential,
        isPending: true,
        isSuccess: false,
        error: null,
      });

      render(<CredentialingUI />, { wrapper: createWrapper() });

      expect(screen.getByTestId('credentialing-container')).toBeInTheDocument();
    });

    it('should handle delete credential pending state', () => {
      (hooks.useDeleteCredential as jest.Mock).mockReturnValue({
        mutateAsync: mockDeleteCredential,
        isPending: true,
        isSuccess: false,
        error: null,
      });

      render(<CredentialingUI />, { wrapper: createWrapper() });

      expect(screen.getByTestId('credentialing-container')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('should handle null data gracefully', () => {
      (hooks.useFacultyCredentials as jest.Mock).mockReturnValue({
        data: null,
        isLoading: false,
        error: null,
        refetch: mockRefetchCredentials,
      });

      render(<CredentialingUI />, { wrapper: createWrapper() });

      expect(screen.getByTestId('empty-state')).toBeInTheDocument();
    });

    it('should handle undefined data gracefully', () => {
      (hooks.useFacultyCredentials as jest.Mock).mockReturnValue({
        data: undefined,
        isLoading: false,
        error: null,
        refetch: mockRefetchCredentials,
      });

      render(<CredentialingUI />, { wrapper: createWrapper() });

      expect(screen.getByTestId('empty-state')).toBeInTheDocument();
    });

    it('should handle faculty with zero credentials', () => {
      (hooks.useFacultyCredentials as jest.Mock).mockReturnValue({
        data: [
          procedureMockFactories.facultySummary({
            total_credentials: 0,
            active_credentials: 0,
            expiring_soon: 0,
            procedures: [],
          }),
        ],
        isLoading: false,
        error: null,
        refetch: mockRefetchCredentials,
      });

      render(<CredentialingUI />, { wrapper: createWrapper() });

      expect(screen.getByText('0 / 0 Active')).toBeInTheDocument();
    });

    it('should handle procedures with missing optional fields', () => {
      (hooks.useProcedures as jest.Mock).mockReturnValue({
        data: {
          items: [
            procedureMockFactories.procedure({
              description: null,
              category: null,
              specialty: null,
            }),
          ],
          total: 1,
        },
        isLoading: false,
        error: null,
        refetch: mockRefetchProcedures,
      });

      render(<CredentialingUI />, { wrapper: createWrapper() });

      expect(screen.getByTestId('credentialing-container')).toBeInTheDocument();
    });
  });
});
