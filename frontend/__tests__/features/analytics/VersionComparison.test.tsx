import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { VersionComparison } from '@/features/analytics/VersionComparison';
import { analyticsMockFactories, analyticsMockResponses } from './analytics-mocks';
import { createWrapper } from '../../utils/test-utils';
import * as api from '@/lib/api';

// Mock the api module
jest.mock('@/lib/api', () => ({
  get: jest.fn(),
  post: jest.fn(),
}));

const mockedApi = api as jest.Mocked<typeof api>;

describe('VersionComparison', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Initial State', () => {
    beforeEach(() => {
      mockedApi.get.mockResolvedValue(analyticsMockResponses.versions);
    });

    it('should render title', async () => {
      render(<VersionComparison />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Compare Schedule Versions')).toBeInTheDocument();
      });
    });

    it('should display empty state message when no versions selected', async () => {
      render(<VersionComparison />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Select two versions to compare')).toBeInTheDocument();
      });
    });

    it('should render version selectors', async () => {
      render(<VersionComparison />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Version A (Baseline)')).toBeInTheDocument();
        expect(screen.getByText('Version B (Comparison)')).toBeInTheDocument();
      });
    });
  });

  describe('Version Selection', () => {
    beforeEach(() => {
      mockedApi.get.mockResolvedValue(analyticsMockResponses.versions);
    });

    it('should load available versions', async () => {
      render(<VersionComparison />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(mockedApi.get).toHaveBeenCalledWith('/analytics/versions');
      });
    });

    it('should display version options in selectors', async () => {
      render(<VersionComparison />, { wrapper: createWrapper() });

      await waitFor(() => {
        const selects = screen.getAllByRole('combobox');
        expect(selects).toHaveLength(2);
      });
    });

    it('should allow selecting Version A', async () => {
      const user = userEvent.setup();

      render(<VersionComparison />, { wrapper: createWrapper() });

      // Wait for versions to load and select to be enabled
      await waitFor(() => {
        const selects = screen.getAllByRole('combobox');
        expect(selects[0]).not.toBeDisabled();
      });

      const versionASelect = screen.getAllByRole('combobox')[0];
      await user.selectOptions(versionASelect, 'v1');

      expect(versionASelect).toHaveValue('v1');
    });

    it('should allow selecting Version B', async () => {
      const user = userEvent.setup();

      render(<VersionComparison />, { wrapper: createWrapper() });

      // Wait for versions to load and select to be enabled
      await waitFor(() => {
        const selects = screen.getAllByRole('combobox');
        expect(selects[1]).not.toBeDisabled();
      });

      const versionBSelect = screen.getAllByRole('combobox')[1];
      await user.selectOptions(versionBSelect, 'v2');

      expect(versionBSelect).toHaveValue('v2');
    });
  });

  describe('Comparison Display', () => {
    beforeEach(() => {
      mockedApi.get.mockImplementation((url) => {
        if (url.includes('/versions/compare')) {
          return Promise.resolve(analyticsMockResponses.versionComparison);
        }
        return Promise.resolve(analyticsMockResponses.versions);
      });
    });

    it('should display loading state when fetching comparison', async () => {
      mockedApi.get.mockImplementation((url) => {
        if (url.includes('/versions/compare')) {
          return new Promise(() => {}); // Never resolves
        }
        return Promise.resolve(analyticsMockResponses.versions);
      });

      render(<VersionComparison versionAId="v1" versionBId="v2" />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByText('Comparing versions...')).toBeInTheDocument();
      });
    });

    it('should display impact assessment', async () => {
      render(<VersionComparison versionAId="v1" versionBId="v2" />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByText('Positive Impact')).toBeInTheDocument();
      });
    });

    it('should show affected residents count', async () => {
      const mockComparison = analyticsMockFactories.versionComparison({
        impactAssessment: analyticsMockFactories.impactAssessment({
          affectedResidents: 15,
        }),
      });

      mockedApi.get.mockImplementation((url) => {
        if (url.includes('/versions/compare')) {
          return Promise.resolve(mockComparison);
        }
        return Promise.resolve(analyticsMockResponses.versions);
      });

      render(<VersionComparison versionAId="v1" versionBId="v2" />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByText(/15 residents affected/)).toBeInTheDocument();
      });
    });

    it('should display metric changes section', async () => {
      render(<VersionComparison versionAId="v1" versionBId="v2" />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByText('Metric Changes')).toBeInTheDocument();
      });
    });

    it('should display metric deltas', async () => {
      render(<VersionComparison versionAId="v1" versionBId="v2" />, {
        wrapper: createWrapper(),
      });

      // Wait for comparison data to load
      await waitFor(() => {
        expect(screen.getByText('Metric Changes')).toBeInTheDocument();
      });

      // Check that delta rows are displayed using getAllByText since there may be multiple
      await waitFor(() => {
        expect(screen.getAllByText('Version A').length).toBeGreaterThan(0);
        expect(screen.getAllByText('Version B').length).toBeGreaterThan(0);
      }, { timeout: 3000 });
    });

    it('should show recommendation when available', async () => {
      const mockComparison = analyticsMockFactories.versionComparison({
        recommendation: 'This version shows improved metrics',
      });

      mockedApi.get.mockImplementation((url) => {
        if (url.includes('/versions/compare')) {
          return Promise.resolve(mockComparison);
        }
        return Promise.resolve(analyticsMockResponses.versions);
      });

      render(<VersionComparison versionAId="v1" versionBId="v2" />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByText('This version shows improved metrics')).toBeInTheDocument();
      });
    });
  });

  describe('Impact Assessment Display', () => {
    beforeEach(() => {
      mockedApi.get.mockImplementation((url) => {
        if (url.includes('/versions/compare')) {
          return Promise.resolve(analyticsMockResponses.versionComparison);
        }
        return Promise.resolve(analyticsMockResponses.versions);
      });
    });

    it('should show positive impact indicator', async () => {
      const mockComparison = analyticsMockFactories.versionComparison({
        impactAssessment: analyticsMockFactories.impactAssessment({
          overallImpact: 'positive',
        }),
      });

      mockedApi.get.mockImplementation((url) => {
        if (url.includes('/versions/compare')) {
          return Promise.resolve(mockComparison);
        }
        return Promise.resolve(analyticsMockResponses.versions);
      });

      render(<VersionComparison versionAId="v1" versionBId="v2" />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByText('Positive Impact')).toBeInTheDocument();
      });
    });

    it('should show negative impact indicator', async () => {
      const mockComparison = analyticsMockFactories.versionComparison({
        impactAssessment: analyticsMockFactories.impactAssessment({
          overallImpact: 'negative',
        }),
      });

      mockedApi.get.mockImplementation((url) => {
        if (url.includes('/versions/compare')) {
          return Promise.resolve(mockComparison);
        }
        return Promise.resolve(analyticsMockResponses.versions);
      });

      render(<VersionComparison versionAId="v1" versionBId="v2" />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByText('Negative Impact')).toBeInTheDocument();
      });
    });

    it('should display risk level', async () => {
      const mockComparison = analyticsMockFactories.versionComparison({
        impactAssessment: analyticsMockFactories.impactAssessment({
          riskLevel: 'medium',
        }),
      });

      mockedApi.get.mockImplementation((url) => {
        if (url.includes('/versions/compare')) {
          return Promise.resolve(mockComparison);
        }
        return Promise.resolve(analyticsMockResponses.versions);
      });

      render(<VersionComparison versionAId="v1" versionBId="v2" />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByText(/Medium Risk/)).toBeInTheDocument();
      });
    });

    it('should display impact bars for fairness, coverage, and compliance', async () => {
      render(<VersionComparison versionAId="v1" versionBId="v2" />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByText('Fairness Impact')).toBeInTheDocument();
        expect(screen.getByText('Coverage Impact')).toBeInTheDocument();
        expect(screen.getByText('Compliance Impact')).toBeInTheDocument();
      });
    });

    it('should expand/collapse impact assessment details', async () => {
      const user = userEvent.setup();

      render(<VersionComparison versionAId="v1" versionBId="v2" />, {
        wrapper: createWrapper(),
      });

      // Wait for impact assessment to load
      await waitFor(() => {
        expect(screen.getByText('Positive Impact')).toBeInTheDocument();
      });

      // Should show details by default (expanded: true)
      await waitFor(() => {
        expect(screen.getByText('Fairness Impact')).toBeInTheDocument();
      });

      // Click to collapse - use a broader query for the button
      const toggleButton = screen.getByRole('button', { name: /positive impact.*click to collapse/i });
      await user.click(toggleButton);

      // After collapsing, details should be hidden
      await waitFor(() => {
        expect(screen.queryByText('Fairness Impact')).not.toBeInTheDocument();
      });
    });
  });

  describe('Category Filtering', () => {
    beforeEach(() => {
      mockedApi.get.mockImplementation((url) => {
        if (url.includes('/versions/compare')) {
          return Promise.resolve(analyticsMockResponses.versionComparison);
        }
        return Promise.resolve(analyticsMockResponses.versions);
      });
    });

    it('should show category filter buttons', async () => {
      render(<VersionComparison versionAId="v1" versionBId="v2" />, {
        wrapper: createWrapper(),
      });

      // Wait for comparison to load by checking for Metric Changes section
      await waitFor(() => {
        expect(screen.getByText('Metric Changes')).toBeInTheDocument();
      });

      // Now check for category filter buttons
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /filter by all categories/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /filter by fairness/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /filter by coverage/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /filter by compliance/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /filter by workload/i })).toBeInTheDocument();
      });
    });

    it('should allow filtering by category', async () => {
      const user = userEvent.setup();

      render(<VersionComparison versionAId="v1" versionBId="v2" />, {
        wrapper: createWrapper(),
      });

      // Wait for comparison to load
      await waitFor(() => {
        expect(screen.getByText('Metric Changes')).toBeInTheDocument();
      });

      // Click fairness filter button using aria-label
      const fairnessButton = screen.getByRole('button', { name: /filter by fairness/i });
      await user.click(fairnessButton);

      // Button should now be selected
      expect(fairnessButton).toHaveClass('bg-white');
      expect(fairnessButton).toHaveClass('text-blue-600');
    });
  });

  describe('Error Handling', () => {
    beforeEach(() => {
      mockedApi.get.mockResolvedValue(analyticsMockResponses.versions);
    });

    it('should display error message when comparison fetch fails', async () => {
      mockedApi.get.mockImplementation((url) => {
        if (url.includes('/versions/compare')) {
          return Promise.reject(new Error('API Error'));
        }
        return Promise.resolve(analyticsMockResponses.versions);
      });

      render(<VersionComparison versionAId="v1" versionBId="v2" />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByText('Failed to load comparison data')).toBeInTheDocument();
      });
    });
  });

  describe('API Integration', () => {
    beforeEach(() => {
      mockedApi.get.mockImplementation((url) => {
        if (url.includes('/versions/compare')) {
          return Promise.resolve(analyticsMockResponses.versionComparison);
        }
        return Promise.resolve(analyticsMockResponses.versions);
      });
    });

    it('should fetch comparison with correct version IDs', async () => {
      render(<VersionComparison versionAId="v1" versionBId="v2" />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(mockedApi.get).toHaveBeenCalledWith(
          expect.stringContaining('/analytics/versions/compare?version_a=v1&version_b=v2')
        );
      });
    });

    it('should not fetch comparison when only one version selected', async () => {
      render(<VersionComparison versionAId="v1" />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(mockedApi.get).toHaveBeenCalledWith('/analytics/versions');
      });

      expect(mockedApi.get).not.toHaveBeenCalledWith(
        expect.stringContaining('/analytics/versions/compare')
      );
    });
  });
});
