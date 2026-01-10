/**
 * Tests for Contingency Analysis Display Component
 *
 * Tests the contingency analysis component which displays:
 * - N-1 and N-2 vulnerability analysis
 * - Critical faculty identification
 * - Centrality scores
 * - Fatal pair detection
 * - Recommended mitigation actions
 *
 * NOTE: These tests are skipped because the ContingencyAnalysis component
 * is currently a stub. When the full component is implemented, these tests
 * should be unskipped and may need adjustments based on the final implementation.
 */

import { render, screen, waitFor } from '@/test-utils';
import userEvent from '@testing-library/user-event';
import { ContingencyAnalysis } from '@/features/resilience/ContingencyAnalysis';
import { resilienceMockResponses } from './resilience-mocks';
import { createWrapper } from '../../utils/test-utils';
import * as api from '@/lib/api';

// Mock the api module
jest.mock('@/lib/api', () => ({
  get: jest.fn(),
  post: jest.fn(),
}));

const mockedApi = api as jest.Mocked<typeof api>;

// Skip all tests - component is a stub placeholder
// TODO: Unskip when ContingencyAnalysis is fully implemented
describe.skip('ContingencyAnalysis', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Initial Rendering', () => {
    beforeEach(() => {
      mockedApi.get.mockResolvedValue(resilienceMockResponses.contingencyAnalysis);
    });

    it('should render component title', async () => {
      render(<ContingencyAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Contingency Analysis')).toBeInTheDocument();
      });
    });

    it('should render component description', async () => {
      render(<ContingencyAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(
          screen.getByText(/N-1 and N-2 vulnerability analysis/)
        ).toBeInTheDocument();
      });
    });

    it('should fetch vulnerability report on mount', async () => {
      render(<ContingencyAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(mockedApi.get).toHaveBeenCalledWith(
          expect.stringContaining('/resilience/vulnerability')
        );
      });
    });

    it('should render run analysis button', async () => {
      render(<ContingencyAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /run.*analysis/i })).toBeInTheDocument();
      });
    });

    it('should render date range selector', async () => {
      render(<ContingencyAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByLabelText(/start.*date/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/end.*date/i)).toBeInTheDocument();
      });
    });
  });

  describe('Loading State', () => {
    it('should show loading skeleton while fetching data', async () => {
      mockedApi.get.mockImplementation(() => new Promise(() => {})); // Never resolves

      const { container } = render(<ContingencyAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        const skeletons = container.querySelectorAll('.animate-pulse');
        expect(skeletons.length).toBeGreaterThan(0);
      });
    });

    it('should show loading text', async () => {
      mockedApi.get.mockImplementation(() => new Promise(() => {}));

      render(<ContingencyAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText(/analyzing.*vulnerabilities/i)).toBeInTheDocument();
      });
    });

    it('should disable run analysis button while loading', async () => {
      mockedApi.get.mockImplementation(() => new Promise(() => {}));

      render(<ContingencyAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        const button = screen.getByRole('button', { name: /run.*analysis/i });
        expect(button).toBeDisabled();
      });
    });
  });

  describe('Error State', () => {
    it('should show error message when analysis fails', async () => {
      mockedApi.get.mockRejectedValue(new Error('API Error'));

      render(<ContingencyAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText(/failed to load.*analysis/i)).toBeInTheDocument();
      });
    });

    it('should show retry button on error', async () => {
      mockedApi.get.mockRejectedValue(new Error('Network error'));

      render(<ContingencyAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
      });
    });

    it('should retry fetching data when retry button clicked', async () => {
      const user = userEvent.setup();
      mockedApi.get.mockRejectedValueOnce(new Error('Network error'));
      mockedApi.get.mockResolvedValueOnce(resilienceMockResponses.contingencyAnalysis);

      render(<ContingencyAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
      });

      const retryButton = screen.getByRole('button', { name: /retry/i });
      await user.click(retryButton);

      await waitFor(() => {
        expect(mockedApi.get).toHaveBeenCalledTimes(2);
      });
    });
  });

  describe('N-1/N-2 Summary', () => {
    beforeEach(() => {
      mockedApi.get.mockResolvedValue(resilienceMockResponses.contingencyAnalysis);
    });

    it('should display N-1 pass status with checkmark', async () => {
      render(<ContingencyAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        const n1Status = screen.getByText(/N-1.*Pass/i);
        expect(n1Status).toBeInTheDocument();
        expect(n1Status).toHaveClass('text-green-600');
      });
    });

    it('should display N-2 pass status with checkmark', async () => {
      render(<ContingencyAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        const n2Status = screen.getByText(/N-2.*Pass/i);
        expect(n2Status).toBeInTheDocument();
        expect(n2Status).toHaveClass('text-green-600');
      });
    });

    it('should display N-1 fail status with X icon', async () => {
      mockedApi.get.mockResolvedValue({
        ...resilienceMockResponses.contingencyAnalysis,
        n1Pass: false,
      });

      render(<ContingencyAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        const n1Status = screen.getByText(/N-1.*Fail/i);
        expect(n1Status).toBeInTheDocument();
        expect(n1Status).toHaveClass('text-red-600');
      });
    });

    it('should display phase transition risk', async () => {
      render(<ContingencyAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText(/15%/)).toBeInTheDocument();
        expect(screen.getByText(/transition.*risk/i)).toBeInTheDocument();
      });
    });

    it('should display analysis timestamp', async () => {
      render(<ContingencyAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText(/analyzed/i)).toBeInTheDocument();
      });
    });
  });

  describe('N-1 Vulnerabilities Display', () => {
    beforeEach(() => {
      mockedApi.get.mockResolvedValue(resilienceMockResponses.contingencyAnalysis);
    });

    it('should render N-1 vulnerabilities section', async () => {
      render(<ContingencyAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('N-1 Vulnerabilities')).toBeInTheDocument();
      });
    });

    it('should display all vulnerable faculty members', async () => {
      render(<ContingencyAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText(/faculty-1/i)).toBeInTheDocument();
        expect(screen.getByText(/faculty-2/i)).toBeInTheDocument();
      });
    });

    it('should show affected blocks count for each vulnerability', async () => {
      render(<ContingencyAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText(/5.*block/i)).toBeInTheDocument();
        expect(screen.getByText(/3.*block/i)).toBeInTheDocument();
      });
    });

    it('should display severity badges', async () => {
      render(<ContingencyAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        const mediumBadge = screen.getByText('medium');
        expect(mediumBadge).toHaveClass('bg-yellow-100');

        const lowBadge = screen.getByText('low');
        expect(lowBadge).toHaveClass('bg-green-100');
      });
    });

    it('should sort vulnerabilities by severity', async () => {
      render(<ContingencyAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        const severities = screen.getAllByText(/medium|low/);
        expect(severities[0]).toHaveTextContent('medium');
      });
    });

    it('should show empty state when no vulnerabilities', async () => {
      mockedApi.get.mockResolvedValue({
        ...resilienceMockResponses.contingencyAnalysis,
        n1_vulnerabilities: [],
      });

      render(<ContingencyAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText(/no.*vulnerabilities.*detected/i)).toBeInTheDocument();
      });
    });
  });

  describe('N-2 Fatal Pairs Display', () => {
    beforeEach(() => {
      mockedApi.get.mockResolvedValue(resilienceMockResponses.contingencyAnalysis);
    });

    it('should render N-2 fatal pairs section', async () => {
      render(<ContingencyAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('N-2 Fatal Pairs')).toBeInTheDocument();
      });
    });

    it('should display fatal pair descriptions', async () => {
      render(<ContingencyAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(
          screen.getByText(/simultaneous loss.*would cause.*failure/i)
        ).toBeInTheDocument();
      });
    });

    it('should show faculty pair information', async () => {
      render(<ContingencyAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText(/faculty-1.*\+.*faculty-3/i)).toBeInTheDocument();
      });
    });

    it('should show empty state when no fatal pairs', async () => {
      mockedApi.get.mockResolvedValue({
        ...resilienceMockResponses.contingencyAnalysis,
        n2_fatal_pairs: [],
      });

      render(<ContingencyAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText(/no fatal pairs identified/i)).toBeInTheDocument();
      });
    });

    it('should highlight fatal pairs with warning style', async () => {
      const { container } = render(<ContingencyAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        const fatalPairCard = container.querySelector('[data-testid="fatal-pair"]');
        expect(fatalPairCard).toHaveClass('border-orange-300');
      });
    });
  });

  describe('Critical Faculty Display', () => {
    beforeEach(() => {
      mockedApi.get.mockResolvedValue(resilienceMockResponses.contingencyAnalysis);
    });

    it('should render critical faculty section', async () => {
      render(<ContingencyAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Most Critical Faculty')).toBeInTheDocument();
      });
    });

    it('should display faculty names and IDs', async () => {
      render(<ContingencyAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Dr. Smith')).toBeInTheDocument();
        expect(screen.getByText('Dr. Johnson')).toBeInTheDocument();
      });
    });

    it('should show centrality scores', async () => {
      render(<ContingencyAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText(/0\.85|85%/)).toBeInTheDocument();
        expect(screen.getByText(/0\.72|72%/)).toBeInTheDocument();
      });
    });

    it('should display services covered', async () => {
      render(<ContingencyAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText(/Inpatient.*Procedures.*Emergency/i)).toBeInTheDocument();
        expect(screen.getByText(/Outpatient.*Clinic/i)).toBeInTheDocument();
      });
    });

    it('should show unique coverage slots', async () => {
      render(<ContingencyAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText(/12.*unique/i)).toBeInTheDocument();
        expect(screen.getByText(/8.*unique/i)).toBeInTheDocument();
      });
    });

    it('should display replacement difficulty badges', async () => {
      render(<ContingencyAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        const highBadge = screen.getByText('high');
        expect(highBadge).toHaveClass('bg-red-100');

        const mediumBadge = screen.getByText('medium');
        expect(mediumBadge).toHaveClass('bg-yellow-100');
      });
    });

    it('should show risk level badges', async () => {
      render(<ContingencyAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        const criticalBadge = screen.getByText('critical');
        expect(criticalBadge).toHaveClass('bg-red-600', 'text-white');

        const highBadge = screen.getByText('high');
        expect(highBadge).toHaveClass('bg-orange-100');
      });
    });

    it('should sort faculty by centrality score descending', async () => {
      render(<ContingencyAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        const names = screen.getAllByText(/Dr\. (Smith|Johnson)/);
        expect(names[0]).toHaveTextContent('Dr. Smith');
        expect(names[1]).toHaveTextContent('Dr. Johnson');
      });
    });
  });

  describe('Recommended Actions', () => {
    beforeEach(() => {
      mockedApi.get.mockResolvedValue(resilienceMockResponses.contingencyAnalysis);
    });

    it('should render recommended actions section', async () => {
      render(<ContingencyAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Recommended Actions')).toBeInTheDocument();
      });
    });

    it('should display all recommended actions', async () => {
      render(<ContingencyAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(
          screen.getByText(/Cross-train.*critical services/i)
        ).toBeInTheDocument();
        expect(screen.getByText(/Build backup pool/i)).toBeInTheDocument();
      });
    });

    it('should show action items with checkboxes', async () => {
      render(<ContingencyAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        const checkboxes = screen.getAllByRole('checkbox');
        expect(checkboxes.length).toBeGreaterThan(0);
      });
    });

    it('should allow marking actions as completed', async () => {
      const user = userEvent.setup();
      render(<ContingencyAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText(/Cross-train/i)).toBeInTheDocument();
      });

      const checkbox = screen.getAllByRole('checkbox')[0];
      await user.click(checkbox);

      await waitFor(() => {
        expect(checkbox).toBeChecked();
      });
    });

    it('should show empty state when no recommendations', async () => {
      mockedApi.get.mockResolvedValue({
        ...resilienceMockResponses.contingencyAnalysis,
        recommendedActions: [],
      });

      render(<ContingencyAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText(/no.*action.*required/i)).toBeInTheDocument();
      });
    });
  });

  describe('User Interactions', () => {
    beforeEach(() => {
      mockedApi.post.mockResolvedValue(resilienceMockResponses.contingencyAnalysis);
    });

    it('should run new analysis when button clicked', async () => {
      const user = userEvent.setup();
      mockedApi.get.mockResolvedValue(resilienceMockResponses.contingencyAnalysis);

      render(<ContingencyAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /run.*analysis/i })).toBeInTheDocument();
      });

      const analyzeButton = screen.getByRole('button', { name: /run.*analysis/i });
      await user.click(analyzeButton);

      await waitFor(() => {
        expect(mockedApi.get).toHaveBeenCalledTimes(2);
      });
    });

    it('should update date range and rerun analysis', async () => {
      const user = userEvent.setup();
      mockedApi.get.mockResolvedValue(resilienceMockResponses.contingencyAnalysis);

      render(<ContingencyAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByLabelText(/start.*date/i)).toBeInTheDocument();
      });

      const startDateInput = screen.getByLabelText(/start.*date/i);
      await user.clear(startDateInput);
      await user.type(startDateInput, '2025-01-01');

      await waitFor(() => {
        expect(mockedApi.get).toHaveBeenCalledWith(
          expect.stringContaining('startDate=2025-01-01')
        );
      });
    });

    it('should expand faculty details when clicked', async () => {
      const user = userEvent.setup();
      mockedApi.get.mockResolvedValue(resilienceMockResponses.contingencyAnalysis);

      render(<ContingencyAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Dr. Smith')).toBeInTheDocument();
      });

      const facultyCard = screen.getByText('Dr. Smith').closest('button');
      if (facultyCard) {
        await user.click(facultyCard);

        await waitFor(() => {
          expect(screen.getByText(/detailed.*profile/i)).toBeInTheDocument();
        });
      }
    });

    it('should export analysis results', async () => {
      const user = userEvent.setup();
      mockedApi.get.mockResolvedValue(resilienceMockResponses.contingencyAnalysis);
      mockedApi.post.mockResolvedValue(new Blob(['export data']));

      render(<ContingencyAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /export/i })).toBeInTheDocument();
      });

      const exportButton = screen.getByRole('button', { name: /export/i });
      await user.click(exportButton);

      await waitFor(() => {
        expect(mockedApi.post).toHaveBeenCalledWith(
          expect.stringContaining('/resilience/vulnerability/export'),
          expect.any(Object)
        );
      });
    });
  });

  describe('Filtering and Sorting', () => {
    beforeEach(() => {
      mockedApi.get.mockResolvedValue(resilienceMockResponses.contingencyAnalysis);
    });

    it('should filter vulnerabilities by severity', async () => {
      const user = userEvent.setup();

      render(<ContingencyAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByLabelText(/filter.*severity/i)).toBeInTheDocument();
      });

      const severityFilter = screen.getByLabelText(/filter.*severity/i);
      await user.selectOptions(severityFilter, 'medium');

      await waitFor(() => {
        expect(screen.getByText('medium')).toBeInTheDocument();
        expect(screen.queryByText('low')).not.toBeInTheDocument();
      });
    });

    it('should sort critical faculty by different criteria', async () => {
      const user = userEvent.setup();

      render(<ContingencyAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByLabelText(/sort.*by/i)).toBeInTheDocument();
      });

      const sortSelect = screen.getByLabelText(/sort.*by/i);
      await user.selectOptions(sortSelect, 'services');

      await waitFor(() => {
        const names = screen.getAllByText(/Dr\. (Smith|Johnson)/);
        expect(names[0]).toHaveTextContent('Dr. Smith'); // More services
      });
    });

    it('should search for specific faculty', async () => {
      const user = userEvent.setup();

      render(<ContingencyAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/search.*faculty/i)).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText(/search.*faculty/i);
      await user.type(searchInput, 'Smith');

      await waitFor(() => {
        expect(screen.getByText('Dr. Smith')).toBeInTheDocument();
        expect(screen.queryByText('Dr. Johnson')).not.toBeInTheDocument();
      });
    });
  });

  describe('Visual Indicators', () => {
    beforeEach(() => {
      mockedApi.get.mockResolvedValue(resilienceMockResponses.contingencyAnalysis);
    });

    it('should show vulnerability heatmap', async () => {
      const { container } = render(<ContingencyAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        const heatmap = container.querySelector('[data-testid="vulnerability-heatmap"]');
        expect(heatmap).toBeInTheDocument();
      });
    });

    it('should display centrality score visualization', async () => {
      const { container } = render(<ContingencyAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        const scoreBar = container.querySelector('[data-testid="centrality-bar"]');
        expect(scoreBar).toBeInTheDocument();
      });
    });

    it('should show faculty network graph', async () => {
      const { container } = render(<ContingencyAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        const networkGraph = container.querySelector('[data-testid="faculty-network"]');
        expect(networkGraph).toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    beforeEach(() => {
      mockedApi.get.mockResolvedValue(resilienceMockResponses.contingencyAnalysis);
    });

    it('should have proper heading hierarchy', async () => {
      render(<ContingencyAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        const h2Headers = screen.getAllByRole('heading', { level: 2 });
        expect(h2Headers.length).toBeGreaterThan(0);
      });
    });

    it('should have accessible table for vulnerabilities', async () => {
      const { container } = render(<ContingencyAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        const table = container.querySelector('table');
        expect(table).toBeInTheDocument();
        expect(table).toHaveAttribute('aria-label');
      });
    });

    it('should announce analysis completion to screen readers', async () => {
      const { container } = render(<ContingencyAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        const announcement = container.querySelector('[role="status"]');
        expect(announcement).toBeInTheDocument();
        expect(announcement).toHaveAttribute('aria-live', 'polite');
      });
    });
  });

  describe('Custom ClassName', () => {
    beforeEach(() => {
      mockedApi.get.mockResolvedValue(resilienceMockResponses.contingencyAnalysis);
    });

    it('should apply custom className', async () => {
      const { container } = render(
        <ContingencyAnalysis className="custom-contingency" />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        const element = container.querySelector('.custom-contingency');
        expect(element).toBeInTheDocument();
      });
    });
  });
});
