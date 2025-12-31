import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { WhatIfAnalysis } from '@/features/analytics/WhatIfAnalysis';
import { analyticsMockFactories, analyticsMockResponses } from './analytics-mocks';
import { createWrapper } from '../../utils/test-utils';
import * as api from '@/lib/api';

// Mock the api module
jest.mock('@/lib/api', () => ({
  get: jest.fn(),
  post: jest.fn(),
}));

const mockedApi = api as jest.Mocked<typeof api>;

describe('WhatIfAnalysis', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockedApi.get.mockResolvedValue(analyticsMockResponses.versions);
  });

  describe('Initial Rendering', () => {
    it('should render title and description', async () => {
      render(<WhatIfAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('What-If Analysis')).toBeInTheDocument();
      });
      expect(
        screen.getByText(/Predict the impact of proposed changes to your schedule/)
      ).toBeInTheDocument();
    });

    it('should render base version selector', async () => {
      render(<WhatIfAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Base Version')).toBeInTheDocument();
      });
    });

    it('should render analysis scope selector', async () => {
      render(<WhatIfAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Analysis Scope')).toBeInTheDocument();
      });
    });

    it('should render all scope options', async () => {
      render(<WhatIfAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Immediate')).toBeInTheDocument();
        expect(screen.getByText('Week')).toBeInTheDocument();
        expect(screen.getByText('Month')).toBeInTheDocument();
        expect(screen.getByText('Quarter')).toBeInTheDocument();
      });
    });

    it('should render proposed changes section', async () => {
      render(<WhatIfAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Proposed Changes')).toBeInTheDocument();
      });
    });

    it('should show empty state when no changes added', async () => {
      render(<WhatIfAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText(/No changes added yet/)).toBeInTheDocument();
      });
    });
  });

  describe('Version Selection', () => {
    it('should load available versions', async () => {
      render(<WhatIfAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(mockedApi.get).toHaveBeenCalledWith('/analytics/versions');
      });
    });

    it('should display version options in selector', async () => {
      render(<WhatIfAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        const select = screen.getByRole('combobox');
        expect(select).toBeInTheDocument();
      });
    });

    it('should allow selecting a base version', async () => {
      const user = userEvent.setup();

      render(<WhatIfAnalysis />, { wrapper: createWrapper() });

      // Wait for versions to load and populate the select
      await waitFor(() => {
        const select = screen.getByRole('combobox');
        expect(select.querySelectorAll('option').length).toBeGreaterThan(1);
      });

      const versionSelect = screen.getByRole('combobox');
      await user.selectOptions(versionSelect, 'v1');

      expect(versionSelect).toHaveValue('v1');
    });

    it('should use provided baseVersionId as initial value', async () => {
      render(<WhatIfAnalysis baseVersionId="v2" />, { wrapper: createWrapper() });

      await waitFor(() => {
        const select = screen.getByRole('combobox');
        expect(select).toHaveValue('v2');
      });
    });
  });

  describe('Analysis Scope Selection', () => {
    it('should default to week scope', async () => {
      const { container } = render(<WhatIfAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        const weekButton = screen.getByText('Week');
        expect(weekButton).toHaveClass('bg-blue-600');
        expect(weekButton).toHaveClass('text-white');
      });
    });

    it('should allow changing scope', async () => {
      const user = userEvent.setup();

      render(<WhatIfAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Month')).toBeInTheDocument();
      });

      const monthButton = screen.getByText('Month');
      await user.click(monthButton);

      expect(monthButton).toHaveClass('bg-blue-600');
      expect(monthButton).toHaveClass('text-white');
    });
  });

  describe('Adding Changes', () => {
    it('should show Add Change button', async () => {
      render(<WhatIfAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Add Change')).toBeInTheDocument();
      });
    });

    it('should add a change when Add Change button clicked', async () => {
      const user = userEvent.setup();

      render(<WhatIfAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Add Change')).toBeInTheDocument();
      });

      const addButton = screen.getByText('Add Change');
      await user.click(addButton);

      // Should show change editor
      await waitFor(() => {
        expect(screen.getByText('Change Type')).toBeInTheDocument();
        expect(screen.getByText('Description')).toBeInTheDocument();
      });
    });

    it('should display change number badge', async () => {
      const user = userEvent.setup();

      render(<WhatIfAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Add Change')).toBeInTheDocument();
      });

      const addButton = screen.getByText('Add Change');
      await user.click(addButton);

      await waitFor(() => {
        expect(screen.getByText('1')).toBeInTheDocument();
      });
    });

    it('should allow removing a change', async () => {
      const user = userEvent.setup();

      render(<WhatIfAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Add Change')).toBeInTheDocument();
      });

      // Add a change
      const addButton = screen.getByText('Add Change');
      await user.click(addButton);

      await waitFor(() => {
        expect(screen.getByText('Change Type')).toBeInTheDocument();
      });

      // Remove the change
      const removeButton = screen.getByTitle('Remove change');
      await user.click(removeButton);

      await waitFor(() => {
        expect(screen.queryByText('Change Type')).not.toBeInTheDocument();
        expect(screen.getByText(/No changes added yet/)).toBeInTheDocument();
      });
    });

    it('should allow editing change description', async () => {
      const user = userEvent.setup();

      render(<WhatIfAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Add Change')).toBeInTheDocument();
      });

      const addButton = screen.getByText('Add Change');
      await user.click(addButton);

      await waitFor(() => {
        expect(screen.getByPlaceholderText('Describe the proposed change...')).toBeInTheDocument();
      });

      const descriptionInput = screen.getByPlaceholderText('Describe the proposed change...');
      await user.type(descriptionInput, 'Add extra night shift');

      expect(descriptionInput).toHaveValue('Add extra night shift');
    });

    it('should show all change type options', async () => {
      const user = userEvent.setup();

      render(<WhatIfAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Add Change')).toBeInTheDocument();
      });

      const addButton = screen.getByText('Add Change');
      await user.click(addButton);

      // Wait for the change type selector to appear
      await waitFor(() => {
        expect(screen.getByRole('combobox', { name: /select change type/i })).toBeInTheDocument();
      });

      const select = screen.getByRole('combobox', { name: /select change type/i });

      // Check if options are in the select
      const options = Array.from(select.querySelectorAll('option'));
      const optionTexts = options.map((opt) => opt.textContent);

      expect(optionTexts).toContain('Add Shift');
      expect(optionTexts).toContain('Remove Shift');
      expect(optionTexts).toContain('Swap Shifts');
      expect(optionTexts).toContain('Add Constraint');
      expect(optionTexts).toContain('Modify Rotation');
      expect(optionTexts).toContain('Adjust Staffing');
    });
  });

  describe('Running Analysis', () => {
    it('should disable run button when no version selected', async () => {
      render(<WhatIfAnalysis />, { wrapper: createWrapper() });

      await waitFor(() => {
        const runButton = screen.getByText('Run What-If Analysis');
        expect(runButton).toBeDisabled();
      });
    });

    it('should disable run button when no changes added', async () => {
      render(<WhatIfAnalysis baseVersionId="v1" />, { wrapper: createWrapper() });

      await waitFor(() => {
        const runButton = screen.getByText('Run What-If Analysis');
        expect(runButton).toBeDisabled();
      });
    });

    it('should enable run button when version and changes are present', async () => {
      const user = userEvent.setup();

      render(<WhatIfAnalysis baseVersionId="v1" />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Add Change')).toBeInTheDocument();
      });

      // Add a change
      const addButton = screen.getByText('Add Change');
      await user.click(addButton);

      // Fill in description
      await waitFor(() => {
        expect(screen.getByPlaceholderText('Describe the proposed change...')).toBeInTheDocument();
      });

      const descriptionInput = screen.getByPlaceholderText('Describe the proposed change...');
      await user.type(descriptionInput, 'Test change');

      await waitFor(() => {
        const runButton = screen.getByText('Run What-If Analysis');
        expect(runButton).not.toBeDisabled();
      });
    });

    it('should call API with correct parameters when analysis run', async () => {
      const user = userEvent.setup();
      mockedApi.post.mockResolvedValue(analyticsMockResponses.whatIfAnalysis);

      render(<WhatIfAnalysis baseVersionId="v1" />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Add Change')).toBeInTheDocument();
      });

      // Add a change
      const addButton = screen.getByText('Add Change');
      await user.click(addButton);

      // Fill in description
      await waitFor(() => {
        expect(screen.getByPlaceholderText('Describe the proposed change...')).toBeInTheDocument();
      });

      const descriptionInput = screen.getByPlaceholderText('Describe the proposed change...');
      await user.type(descriptionInput, 'Test change');

      // Run analysis
      await waitFor(() => {
        const runButton = screen.getByText('Run What-If Analysis');
        expect(runButton).not.toBeDisabled();
      });

      const runButton = screen.getByText('Run What-If Analysis');
      await user.click(runButton);

      await waitFor(() => {
        expect(mockedApi.post).toHaveBeenCalledWith('/analytics/what-if', {
          baseVersionId: 'v1',
          changes: expect.arrayContaining([
            expect.objectContaining({
              description: 'Test change',
            }),
          ]),
          analysisScope: 'week',
        });
      });
    });

    it('should show loading state when running analysis', async () => {
      const user = userEvent.setup();
      mockedApi.post.mockImplementation(() => new Promise(() => {})); // Never resolves

      render(<WhatIfAnalysis baseVersionId="v1" />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Add Change')).toBeInTheDocument();
      });

      // Add a change
      const addButton = screen.getByText('Add Change');
      await user.click(addButton);

      // Fill in description
      await waitFor(() => {
        expect(screen.getByPlaceholderText('Describe the proposed change...')).toBeInTheDocument();
      });

      const descriptionInput = screen.getByPlaceholderText('Describe the proposed change...');
      await user.type(descriptionInput, 'Test change');

      // Run analysis
      const runButton = screen.getByText('Run What-If Analysis');
      await user.click(runButton);

      await waitFor(() => {
        expect(screen.getByText('Running Analysis...')).toBeInTheDocument();
      });
    });
  });

  describe('Results Display', () => {
    beforeEach(() => {
      mockedApi.post.mockResolvedValue(analyticsMockResponses.whatIfAnalysis);
    });

    it('should display results after successful analysis', async () => {
      const user = userEvent.setup();

      render(<WhatIfAnalysis baseVersionId="v1" />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Add Change')).toBeInTheDocument();
      });

      // Add a change and run analysis
      const addButton = screen.getByText('Add Change');
      await user.click(addButton);

      const descriptionInput = screen.getByPlaceholderText('Describe the proposed change...');
      await user.type(descriptionInput, 'Test change');

      const runButton = screen.getByText('Run What-If Analysis');
      await user.click(runButton);

      await waitFor(() => {
        expect(screen.getByText('Analysis Results')).toBeInTheDocument();
      });
    });

    it('should display recommendation', async () => {
      const user = userEvent.setup();

      render(<WhatIfAnalysis baseVersionId="v1" />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Add Change')).toBeInTheDocument();
      });

      // Add a change and run analysis
      const addButton = screen.getByText('Add Change');
      await user.click(addButton);

      const descriptionInput = screen.getByPlaceholderText('Describe the proposed change...');
      await user.type(descriptionInput, 'Test change');

      const runButton = screen.getByText('Run What-If Analysis');
      await user.click(runButton);

      await waitFor(() => {
        expect(screen.getByText('Recommended')).toBeInTheDocument();
      });
    });

    it('should display confidence score', async () => {
      const user = userEvent.setup();

      render(<WhatIfAnalysis baseVersionId="v1" />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Add Change')).toBeInTheDocument();
      });

      // Add a change and run analysis
      const addButton = screen.getByText('Add Change');
      await user.click(addButton);

      const descriptionInput = screen.getByPlaceholderText('Describe the proposed change...');
      await user.type(descriptionInput, 'Test change');

      const runButton = screen.getByText('Run What-If Analysis');
      await user.click(runButton);

      await waitFor(() => {
        expect(screen.getByText('Prediction Confidence')).toBeInTheDocument();
        expect(screen.getByText('85%')).toBeInTheDocument();
      });
    });

    it('should display warnings when present', async () => {
      const user = userEvent.setup();

      render(<WhatIfAnalysis baseVersionId="v1" />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Add Change')).toBeInTheDocument();
      });

      // Add a change and run analysis
      const addButton = screen.getByText('Add Change');
      await user.click(addButton);

      const descriptionInput = screen.getByPlaceholderText('Describe the proposed change...');
      await user.type(descriptionInput, 'Test change');

      const runButton = screen.getByText('Run What-If Analysis');
      await user.click(runButton);

      await waitFor(() => {
        expect(screen.getByText('Warnings')).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    it('should display error message when analysis fails', async () => {
      const user = userEvent.setup();
      mockedApi.post.mockRejectedValue(new Error('Analysis failed'));

      render(<WhatIfAnalysis baseVersionId="v1" />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Add Change')).toBeInTheDocument();
      });

      // Add a change and run analysis
      const addButton = screen.getByText('Add Change');
      await user.click(addButton);

      const descriptionInput = screen.getByPlaceholderText('Describe the proposed change...');
      await user.type(descriptionInput, 'Test change');

      const runButton = screen.getByText('Run What-If Analysis');
      await user.click(runButton);

      await waitFor(() => {
        expect(screen.getByText('Analysis failed. Please try again.')).toBeInTheDocument();
      });
    });
  });
});
