/**
 * Tests for HeatmapControls component
 * Tests filtering, date range selection, and control interactions
 */

import { render, screen, waitFor } from '@/test-utils';
import userEvent from '@testing-library/user-event';
import { HeatmapControls } from '@/features/heatmap/HeatmapControls';
import { heatmapMockFactories } from './heatmap-mocks';
import { createWrapper } from '../../utils/test-utils';

describe('HeatmapControls', () => {
  const mockFilters = heatmapMockFactories.filters();
  const mockDateRange = heatmapMockFactories.dateRange();
  const mockAvailablePersons = heatmapMockFactories.availablePersons();
  const mockAvailableRotations = heatmapMockFactories.availableRotations();

  const defaultProps = {
    filters: mockFilters,
    onFiltersChange: jest.fn(),
    dateRange: mockDateRange,
    onDateRangeChange: jest.fn(),
    availablePersons: mockAvailablePersons,
    availableRotations: mockAvailableRotations,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Initial Rendering', () => {
    it('should render date range inputs', () => {
      render(<HeatmapControls {...defaultProps} />, { wrapper: createWrapper() });

      expect(screen.getByText('From:')).toBeInTheDocument();
      expect(screen.getByText('To:')).toBeInTheDocument();
      // Verify inputs exist
      const dateInputs = screen.getAllByDisplayValue(/2024-/);
      expect(dateInputs.length).toBeGreaterThanOrEqual(2);
    });

    it('should render group by selector', () => {
      render(<HeatmapControls {...defaultProps} />, { wrapper: createWrapper() });

      expect(screen.getByText('Group by:')).toBeInTheDocument();
    });

    it('should render include FMIT checkbox', () => {
      render(<HeatmapControls {...defaultProps} />, { wrapper: createWrapper() });

      expect(screen.getByText('Include FMIT')).toBeInTheDocument();
    });

    it('should render filters button', () => {
      render(<HeatmapControls {...defaultProps} />, { wrapper: createWrapper() });

      expect(screen.getByText('Filters')).toBeInTheDocument();
    });

    it('should render export button when onExport is provided', () => {
      const onExport = jest.fn();
      render(<HeatmapControls {...defaultProps} onExport={onExport} />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText('Export')).toBeInTheDocument();
    });

    it('should not render export button when onExport is not provided', () => {
      render(<HeatmapControls {...defaultProps} />, { wrapper: createWrapper() });

      expect(screen.queryByText('Export')).not.toBeInTheDocument();
    });
  });

  describe('Date Range Controls', () => {
    it('should display current date range values', () => {
      render(<HeatmapControls {...defaultProps} />, { wrapper: createWrapper() });

      const dateInputs = screen.getAllByDisplayValue(/2024-/) as HTMLInputElement[];

      expect(dateInputs[0].value).toBe('2024-01-01');
      expect(dateInputs[1].value).toBe('2024-01-31');
    });

    it('should call onDateRangeChange when start date changes', async () => {
      const user = userEvent.setup();
      const onDateRangeChange = jest.fn();

      render(
        <HeatmapControls {...defaultProps} onDateRangeChange={onDateRangeChange} />,
        { wrapper: createWrapper() }
      );

      const dateInputs = screen.getAllByDisplayValue(/2024-/);
      const startInput = dateInputs[0];

      // Simulate native date input change
      await user.clear(startInput);
      await user.type(startInput, '2024-02-01');

      // The handler is called multiple times (once per character typed after clear)
      // Check that it was called with the cleared value
      await waitFor(() => {
        expect(onDateRangeChange).toHaveBeenCalled();
      });

      // Check that one of the calls was for clearing the input (start: '')
      expect(onDateRangeChange).toHaveBeenCalledWith({
        start: '',
        end: '2024-01-31',
      });
    });

    it('should call onDateRangeChange when end date changes', async () => {
      const user = userEvent.setup();
      const onDateRangeChange = jest.fn();

      render(
        <HeatmapControls {...defaultProps} onDateRangeChange={onDateRangeChange} />,
        { wrapper: createWrapper() }
      );

      const dateInputs = screen.getAllByDisplayValue(/2024-/);
      const endInput = dateInputs[1];
      await user.clear(endInput);
      await user.type(endInput, '2024-02-28');

      // The handler is called multiple times (once per character typed after clear)
      // Check that it was called with the cleared value
      await waitFor(() => {
        expect(onDateRangeChange).toHaveBeenCalled();
      });

      // Check that one of the calls was for clearing the input (end: '')
      expect(onDateRangeChange).toHaveBeenCalledWith({
        start: '2024-01-01',
        end: '',
      });
    });

    it('should disable date inputs when loading', () => {
      render(<HeatmapControls {...defaultProps} isLoading={true} />, {
        wrapper: createWrapper(),
      });

      const dateInputs = screen.getAllByDisplayValue(/2024-/);

      expect(dateInputs[0]).toBeDisabled();
      expect(dateInputs[1]).toBeDisabled();
    });
  });

  describe('Group By Control', () => {
    it('should display current group by value', () => {
      render(<HeatmapControls {...defaultProps} />, { wrapper: createWrapper() });

      const groupBySelect = screen.getByDisplayValue('By Person') as HTMLSelectElement;
      expect(groupBySelect.value).toBe('person');
    });

    it('should render all group by options', () => {
      render(<HeatmapControls {...defaultProps} />, { wrapper: createWrapper() });

      const groupBySelect = screen.getByDisplayValue('By Person');
      const options = groupBySelect.querySelectorAll('option');

      expect(options).toHaveLength(2);
      expect(options[0]).toHaveTextContent('By Person');
      expect(options[1]).toHaveTextContent('By Rotation');
    });

    it('should call onFiltersChange when group by changes', async () => {
      const user = userEvent.setup();
      const onFiltersChange = jest.fn();

      render(
        <HeatmapControls {...defaultProps} onFiltersChange={onFiltersChange} />,
        { wrapper: createWrapper() }
      );

      const groupBySelect = screen.getByDisplayValue('By Person');
      await user.selectOptions(groupBySelect, 'rotation');

      await waitFor(() => {
        expect(onFiltersChange).toHaveBeenCalledWith({
          ...mockFilters,
          groupBy: 'rotation',
        });
      });
    });

    it('should disable group by selector when loading', () => {
      render(<HeatmapControls {...defaultProps} isLoading={true} />, {
        wrapper: createWrapper(),
      });

      const groupBySelect = screen.getByDisplayValue('By Person');
      expect(groupBySelect).toBeDisabled();
    });
  });

  describe('Include FMIT Control', () => {
    it('should display checked state based on filter', () => {
      const filtersWithFmit = heatmapMockFactories.filters({ includeFmit: true });
      const { container } = render(<HeatmapControls {...defaultProps} filters={filtersWithFmit} />, {
        wrapper: createWrapper(),
      });

      // Find checkbox by type
      const checkboxes = container.querySelectorAll('input[type="checkbox"]');
      const fmitCheckbox = Array.from(checkboxes).find((cb) => {
        const parent = cb.parentElement;
        return parent?.textContent?.includes('Include FMIT');
      }) as HTMLInputElement;

      expect(fmitCheckbox.checked).toBe(true);
    });

    it('should default to true when includeFmit is undefined', () => {
      const filtersWithoutFmit = heatmapMockFactories.filters();
      delete (filtersWithoutFmit as any).includeFmit;

      const { container } = render(<HeatmapControls {...defaultProps} filters={filtersWithoutFmit} />, {
        wrapper: createWrapper(),
      });

      const checkboxes = container.querySelectorAll('input[type="checkbox"]');
      const fmitCheckbox = Array.from(checkboxes).find((cb) => {
        const parent = cb.parentElement;
        return parent?.textContent?.includes('Include FMIT');
      }) as HTMLInputElement;

      expect(fmitCheckbox.checked).toBe(true);
    });

    it('should call onFiltersChange when FMIT checkbox is toggled', async () => {
      const user = userEvent.setup();
      const onFiltersChange = jest.fn();

      const { container } = render(
        <HeatmapControls {...defaultProps} onFiltersChange={onFiltersChange} />,
        { wrapper: createWrapper() }
      );

      const checkboxes = container.querySelectorAll('input[type="checkbox"]');
      const fmitCheckbox = Array.from(checkboxes).find((cb) => {
        const parent = cb.parentElement;
        return parent?.textContent?.includes('Include FMIT');
      });

      await user.click(fmitCheckbox!);

      await waitFor(() => {
        expect(onFiltersChange).toHaveBeenCalledWith({
          ...mockFilters,
          includeFmit: false,
        });
      });
    });

    it('should disable FMIT checkbox when loading', () => {
      const { container } = render(<HeatmapControls {...defaultProps} isLoading={true} />, {
        wrapper: createWrapper(),
      });

      const checkboxes = container.querySelectorAll('input[type="checkbox"]');
      const fmitCheckbox = Array.from(checkboxes).find((cb) => {
        const parent = cb.parentElement;
        return parent?.textContent?.includes('Include FMIT');
      });

      expect(fmitCheckbox).toBeDisabled();
    });
  });

  describe('Filters Panel Toggle', () => {
    it('should not show filters panel by default', () => {
      render(<HeatmapControls {...defaultProps} />, { wrapper: createWrapper() });

      expect(screen.queryByText('People')).not.toBeInTheDocument();
      expect(screen.queryByText('Rotations')).not.toBeInTheDocument();
    });

    it('should show filters panel when filters button is clicked', async () => {
      const user = userEvent.setup();
      render(<HeatmapControls {...defaultProps} />, { wrapper: createWrapper() });

      const filtersButton = screen.getByText('Filters');
      await user.click(filtersButton);

      await waitFor(() => {
        expect(screen.getByText('People')).toBeInTheDocument();
        expect(screen.getByText('Rotations')).toBeInTheDocument();
      });
    });

    it('should hide filters panel when filters button is clicked again', async () => {
      const user = userEvent.setup();
      render(<HeatmapControls {...defaultProps} />, { wrapper: createWrapper() });

      const filtersButton = screen.getByText('Filters');
      await user.click(filtersButton);
      await user.click(filtersButton);

      await waitFor(() => {
        expect(screen.queryByText('People')).not.toBeInTheDocument();
      });
    });

    it('should disable filters button when loading', () => {
      render(<HeatmapControls {...defaultProps} isLoading={true} />, {
        wrapper: createWrapper(),
      });

      const filtersButton = screen.getByText('Filters');
      expect(filtersButton).toBeDisabled();
    });
  });

  describe('Active Filter Count', () => {
    it('should show active filter count badge', async () => {
      const user = userEvent.setup();
      const filtersWithSelections = heatmapMockFactories.filters({
        personIds: ['person-1', 'person-2'],
        rotationIds: ['rotation-1'],
      });

      render(<HeatmapControls {...defaultProps} filters={filtersWithSelections} />, {
        wrapper: createWrapper(),
      });

      const filtersButton = screen.getByText('Filters');
      expect(filtersButton).toBeInTheDocument();

      const badge = screen.getByText('3');
      expect(badge).toBeInTheDocument();
    });

    it('should not show badge when no filters are active', () => {
      const filtersWithNoSelections = heatmapMockFactories.filters({
        personIds: [],
        rotationIds: [],
      });

      render(<HeatmapControls {...defaultProps} filters={filtersWithNoSelections} />, {
        wrapper: createWrapper(),
      });

      expect(screen.queryByText(/^\d+$/)).not.toBeInTheDocument();
    });
  });

  describe('Person Filter', () => {
    it('should render all available persons', async () => {
      const user = userEvent.setup();
      render(<HeatmapControls {...defaultProps} />, { wrapper: createWrapper() });

      const filtersButton = screen.getByText('Filters');
      await user.click(filtersButton);

      await waitFor(() => {
        expect(screen.getByText('Dr. John Smith')).toBeInTheDocument();
        expect(screen.getByText('Dr. Jane Doe')).toBeInTheDocument();
        expect(screen.getByText('Dr. Bob Wilson')).toBeInTheDocument();
      });
    });

    it('should show empty state when no persons available', async () => {
      const user = userEvent.setup();
      render(<HeatmapControls {...defaultProps} availablePersons={[]} />, {
        wrapper: createWrapper(),
      });

      const filtersButton = screen.getByText('Filters');
      await user.click(filtersButton);

      await waitFor(() => {
        expect(screen.getByText('No people available')).toBeInTheDocument();
      });
    });

    it('should call onFiltersChange when person is selected', async () => {
      const user = userEvent.setup();
      const onFiltersChange = jest.fn();

      render(
        <HeatmapControls {...defaultProps} onFiltersChange={onFiltersChange} />,
        { wrapper: createWrapper() }
      );

      const filtersButton = screen.getByText('Filters');
      await user.click(filtersButton);

      await waitFor(() => {
        expect(screen.getByText('Dr. John Smith')).toBeInTheDocument();
      });

      const checkbox = screen.getByLabelText('Dr. John Smith');
      await user.click(checkbox);

      await waitFor(() => {
        expect(onFiltersChange).toHaveBeenCalledWith({
          ...mockFilters,
          personIds: ['person-1'],
        });
      });
    });

    it('should call onFiltersChange when person is unselected', async () => {
      const user = userEvent.setup();
      const onFiltersChange = jest.fn();
      const filtersWithPerson = heatmapMockFactories.filters({
        personIds: ['person-1'],
      });

      render(
        <HeatmapControls
          {...defaultProps}
          filters={filtersWithPerson}
          onFiltersChange={onFiltersChange}
        />,
        { wrapper: createWrapper() }
      );

      const filtersButton = screen.getByText('Filters');
      await user.click(filtersButton);

      await waitFor(() => {
        expect(screen.getByText('Dr. John Smith')).toBeInTheDocument();
      });

      const checkbox = screen.getByLabelText('Dr. John Smith') as HTMLInputElement;
      expect(checkbox.checked).toBe(true);

      await user.click(checkbox);

      await waitFor(() => {
        expect(onFiltersChange).toHaveBeenCalledWith({
          ...filtersWithPerson,
          personIds: [],
        });
      });
    });

    it('should show clear button when persons are selected', async () => {
      const user = userEvent.setup();
      const filtersWithPerson = heatmapMockFactories.filters({
        personIds: ['person-1'],
      });

      render(<HeatmapControls {...defaultProps} filters={filtersWithPerson} />, {
        wrapper: createWrapper(),
      });

      const filtersButton = screen.getByText('Filters');
      await user.click(filtersButton);

      await waitFor(() => {
        const clearButtons = screen.getAllByText('Clear');
        expect(clearButtons.length).toBeGreaterThan(0);
      });
    });

    it('should clear person filters when clear button is clicked', async () => {
      const user = userEvent.setup();
      const onFiltersChange = jest.fn();
      const filtersWithPerson = heatmapMockFactories.filters({
        personIds: ['person-1', 'person-2'],
      });

      render(
        <HeatmapControls
          {...defaultProps}
          filters={filtersWithPerson}
          onFiltersChange={onFiltersChange}
        />,
        { wrapper: createWrapper() }
      );

      const filtersButton = screen.getByText('Filters');
      await user.click(filtersButton);

      await waitFor(() => {
        expect(screen.getByText('People')).toBeInTheDocument();
      });

      const clearButtons = screen.getAllByText('Clear');
      await user.click(clearButtons[0]);

      await waitFor(() => {
        expect(onFiltersChange).toHaveBeenCalledWith({
          ...filtersWithPerson,
          personIds: [],
        });
      });
    });
  });

  describe('Rotation Filter', () => {
    it('should render all available rotations', async () => {
      const user = userEvent.setup();
      render(<HeatmapControls {...defaultProps} />, { wrapper: createWrapper() });

      const filtersButton = screen.getByText('Filters');
      await user.click(filtersButton);

      await waitFor(() => {
        expect(screen.getByText('Clinic')).toBeInTheDocument();
        expect(screen.getByText('Inpatient')).toBeInTheDocument();
        expect(screen.getByText('Procedures')).toBeInTheDocument();
        expect(screen.getByText('Conference')).toBeInTheDocument();
      });
    });

    it('should show empty state when no rotations available', async () => {
      const user = userEvent.setup();
      render(<HeatmapControls {...defaultProps} availableRotations={[]} />, {
        wrapper: createWrapper(),
      });

      const filtersButton = screen.getByText('Filters');
      await user.click(filtersButton);

      await waitFor(() => {
        expect(screen.getByText('No rotations available')).toBeInTheDocument();
      });
    });

    it('should call onFiltersChange when rotation is selected', async () => {
      const user = userEvent.setup();
      const onFiltersChange = jest.fn();

      render(
        <HeatmapControls {...defaultProps} onFiltersChange={onFiltersChange} />,
        { wrapper: createWrapper() }
      );

      const filtersButton = screen.getByText('Filters');
      await user.click(filtersButton);

      await waitFor(() => {
        expect(screen.getByText('Clinic')).toBeInTheDocument();
      });

      const checkbox = screen.getByLabelText('Clinic');
      await user.click(checkbox);

      await waitFor(() => {
        expect(onFiltersChange).toHaveBeenCalledWith({
          ...mockFilters,
          rotationIds: ['rotation-1'],
        });
      });
    });

    it('should call onFiltersChange when rotation is unselected', async () => {
      const user = userEvent.setup();
      const onFiltersChange = jest.fn();
      const filtersWithRotation = heatmapMockFactories.filters({
        rotationIds: ['rotation-1'],
      });

      render(
        <HeatmapControls
          {...defaultProps}
          filters={filtersWithRotation}
          onFiltersChange={onFiltersChange}
        />,
        { wrapper: createWrapper() }
      );

      const filtersButton = screen.getByText('Filters');
      await user.click(filtersButton);

      await waitFor(() => {
        expect(screen.getByText('Clinic')).toBeInTheDocument();
      });

      const checkbox = screen.getByLabelText('Clinic') as HTMLInputElement;
      expect(checkbox.checked).toBe(true);

      await user.click(checkbox);

      await waitFor(() => {
        expect(onFiltersChange).toHaveBeenCalledWith({
          ...filtersWithRotation,
          rotationIds: [],
        });
      });
    });
  });

  describe('Clear All Filters', () => {
    it('should show clear all button when filters are active', async () => {
      const user = userEvent.setup();
      const filtersWithSelections = heatmapMockFactories.filters({
        personIds: ['person-1'],
        rotationIds: ['rotation-1'],
      });

      render(<HeatmapControls {...defaultProps} filters={filtersWithSelections} />, {
        wrapper: createWrapper(),
      });

      const filtersButton = screen.getByText('Filters');
      await user.click(filtersButton);

      await waitFor(() => {
        expect(screen.getByText('Clear all filters')).toBeInTheDocument();
      });
    });

    it('should not show clear all button when no filters are active', async () => {
      const user = userEvent.setup();
      const filtersWithNoSelections = heatmapMockFactories.filters({
        personIds: [],
        rotationIds: [],
      });

      render(<HeatmapControls {...defaultProps} filters={filtersWithNoSelections} />, {
        wrapper: createWrapper(),
      });

      const filtersButton = screen.getByText('Filters');
      await user.click(filtersButton);

      await waitFor(() => {
        expect(screen.queryByText('Clear all filters')).not.toBeInTheDocument();
      });
    });

    it('should reset filters to defaults when clear all is clicked', async () => {
      const user = userEvent.setup();
      const onFiltersChange = jest.fn();
      const filtersWithSelections = heatmapMockFactories.filters({
        personIds: ['person-1'],
        rotationIds: ['rotation-1'],
      });

      render(
        <HeatmapControls
          {...defaultProps}
          filters={filtersWithSelections}
          onFiltersChange={onFiltersChange}
        />,
        { wrapper: createWrapper() }
      );

      const filtersButton = screen.getByText('Filters');
      await user.click(filtersButton);

      await waitFor(() => {
        expect(screen.getByText('Clear all filters')).toBeInTheDocument();
      });

      const clearAllButton = screen.getByText('Clear all filters');
      await user.click(clearAllButton);

      await waitFor(() => {
        expect(onFiltersChange).toHaveBeenCalledWith({
          groupBy: 'person',
          includeFmit: true,
        });
      });
    });
  });

  describe('Export Functionality', () => {
    it('should call onExport when export button is clicked', async () => {
      const user = userEvent.setup();
      const onExport = jest.fn();

      render(<HeatmapControls {...defaultProps} onExport={onExport} />, {
        wrapper: createWrapper(),
      });

      const exportButton = screen.getByText('Export');
      await user.click(exportButton);

      await waitFor(() => {
        expect(onExport).toHaveBeenCalled();
      });
    });

    it('should disable export button when loading', () => {
      const onExport = jest.fn();

      render(<HeatmapControls {...defaultProps} onExport={onExport} isLoading={true} />, {
        wrapper: createWrapper(),
      });

      const exportButton = screen.getByText('Export');
      expect(exportButton).toBeDisabled();
    });
  });
});
