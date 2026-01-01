import { render, screen, waitFor } from '@/test-utils';
import userEvent from '@testing-library/user-event';
import { TimelineControls } from '@/features/fmit-timeline/TimelineControls';
import type { TimelineFilters, TimelineViewMode, DateRange } from '@/features/fmit-timeline/types';
import { createWrapper } from '../../utils/test-utils';

describe('TimelineControls', () => {
  const mockOnFiltersChange = jest.fn();
  const mockOnDateRangeChange = jest.fn();
  const mockOnViewModeChange = jest.fn();
  const mockOnAcademicYearChange = jest.fn();

  const defaultFilters: TimelineFilters = {
    view_mode: 'monthly',
  };

  const defaultDateRange: DateRange = {
    start: '2024-07-01',
    end: '2025-06-30',
  };

  const defaultViewMode: TimelineViewMode = 'monthly';

  const mockFaculty = [
    { id: 'fac-1', name: 'Dr. Smith', specialty: 'Internal Medicine' },
    { id: 'fac-2', name: 'Dr. Jones', specialty: 'Pediatrics' },
  ];

  const mockRotations = [
    { id: 'rot-1', name: 'Inpatient Medicine' },
    { id: 'rot-2', name: 'Clinic' },
  ];

  const mockAcademicYears = [
    { id: 'ay-2024', label: '2024-2025', start_date: '2024-07-01', end_date: '2025-06-30' },
    { id: 'ay-2025', label: '2025-2026', start_date: '2025-07-01', end_date: '2026-06-30' },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Initial Rendering', () => {
    it('should render date range inputs', () => {
      render(
        <TimelineControls
          filters={defaultFilters}
          onFiltersChange={mockOnFiltersChange}
          dateRange={defaultDateRange}
          onDateRangeChange={mockOnDateRangeChange}
          viewMode={defaultViewMode}
          onViewModeChange={mockOnViewModeChange}
        />,
        { wrapper: createWrapper() }
      );

      const startInput = screen.getByDisplayValue('2024-07-01');
      const endInput = screen.getByDisplayValue('2025-06-30');

      expect(startInput).toBeInTheDocument();
      expect(endInput).toBeInTheDocument();
    });

    it('should render view mode toggle buttons', () => {
      render(
        <TimelineControls
          filters={defaultFilters}
          onFiltersChange={mockOnFiltersChange}
          dateRange={defaultDateRange}
          onDateRangeChange={mockOnDateRangeChange}
          viewMode={defaultViewMode}
          onViewModeChange={mockOnViewModeChange}
        />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('Weekly')).toBeInTheDocument();
      expect(screen.getByText('Monthly')).toBeInTheDocument();
      expect(screen.getByText('Quarterly')).toBeInTheDocument();
    });

    it('should render filters toggle button', () => {
      render(
        <TimelineControls
          filters={defaultFilters}
          onFiltersChange={mockOnFiltersChange}
          dateRange={defaultDateRange}
          onDateRangeChange={mockOnDateRangeChange}
          viewMode={defaultViewMode}
          onViewModeChange={mockOnViewModeChange}
        />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('Filters')).toBeInTheDocument();
    });

    it('should render academic year selector when provided', () => {
      render(
        <TimelineControls
          filters={defaultFilters}
          onFiltersChange={mockOnFiltersChange}
          dateRange={defaultDateRange}
          onDateRangeChange={mockOnDateRangeChange}
          viewMode={defaultViewMode}
          onViewModeChange={mockOnViewModeChange}
          academicYears={mockAcademicYears}
          onAcademicYearChange={mockOnAcademicYearChange}
        />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('Academic Year:')).toBeInTheDocument();
      expect(screen.getByDisplayValue('Custom Range')).toBeInTheDocument();
    });

    it('should display active filter count badge', () => {
      const filtersWithSelections: TimelineFilters = {
        view_mode: 'monthly',
        faculty_ids: ['fac-1', 'fac-2'],
        rotation_ids: ['rot-1'],
      };

      render(
        <TimelineControls
          filters={filtersWithSelections}
          onFiltersChange={mockOnFiltersChange}
          dateRange={defaultDateRange}
          onDateRangeChange={mockOnDateRangeChange}
          viewMode={defaultViewMode}
          onViewModeChange={mockOnViewModeChange}
        />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('3')).toBeInTheDocument();
    });
  });

  describe('Date Range Interactions', () => {
    it('should call onDateRangeChange when start date is changed', async () => {
      const user = userEvent.setup();

      render(
        <TimelineControls
          filters={defaultFilters}
          onFiltersChange={mockOnFiltersChange}
          dateRange={defaultDateRange}
          onDateRangeChange={mockOnDateRangeChange}
          viewMode={defaultViewMode}
          onViewModeChange={mockOnViewModeChange}
        />,
        { wrapper: createWrapper() }
      );

      const startInput = screen.getByDisplayValue('2024-07-01');
      await user.clear(startInput);
      await user.type(startInput, '2024-08-01');

      await waitFor(() => {
        expect(mockOnDateRangeChange).toHaveBeenCalledWith({
          start: '2024-08-01',
          end: '2025-06-30',
        });
      });
    });

    it('should call onDateRangeChange when end date is changed', async () => {
      const user = userEvent.setup();

      render(
        <TimelineControls
          filters={defaultFilters}
          onFiltersChange={mockOnFiltersChange}
          dateRange={defaultDateRange}
          onDateRangeChange={mockOnDateRangeChange}
          viewMode={defaultViewMode}
          onViewModeChange={mockOnViewModeChange}
        />,
        { wrapper: createWrapper() }
      );

      const endInput = screen.getByDisplayValue('2025-06-30');
      await user.clear(endInput);
      await user.type(endInput, '2025-12-31');

      await waitFor(() => {
        expect(mockOnDateRangeChange).toHaveBeenCalledWith({
          start: '2024-07-01',
          end: '2025-12-31',
        });
      });
    });
  });

  describe('View Mode Interactions', () => {
    it('should call onViewModeChange when view mode button is clicked', async () => {
      const user = userEvent.setup();

      render(
        <TimelineControls
          filters={defaultFilters}
          onFiltersChange={mockOnFiltersChange}
          dateRange={defaultDateRange}
          onDateRangeChange={mockOnDateRangeChange}
          viewMode={defaultViewMode}
          onViewModeChange={mockOnViewModeChange}
        />,
        { wrapper: createWrapper() }
      );

      const weeklyButton = screen.getByText('Weekly');
      await user.click(weeklyButton);

      expect(mockOnViewModeChange).toHaveBeenCalledWith('weekly');
    });

    it('should highlight currently selected view mode', () => {
      const { container } = render(
        <TimelineControls
          filters={defaultFilters}
          onFiltersChange={mockOnFiltersChange}
          dateRange={defaultDateRange}
          onDateRangeChange={mockOnDateRangeChange}
          viewMode="weekly"
          onViewModeChange={mockOnViewModeChange}
        />,
        { wrapper: createWrapper() }
      );

      const weeklyButton = screen.getByText('Weekly');
      expect(weeklyButton).toHaveClass('bg-blue-600', 'text-white');
    });
  });

  describe('Academic Year Selection', () => {
    it('should call onAcademicYearChange and update date range when academic year is selected', async () => {
      const user = userEvent.setup();

      render(
        <TimelineControls
          filters={defaultFilters}
          onFiltersChange={mockOnFiltersChange}
          dateRange={defaultDateRange}
          onDateRangeChange={mockOnDateRangeChange}
          viewMode={defaultViewMode}
          onViewModeChange={mockOnViewModeChange}
          academicYears={mockAcademicYears}
          onAcademicYearChange={mockOnAcademicYearChange}
        />,
        { wrapper: createWrapper() }
      );

      const select = screen.getByDisplayValue('Custom Range');
      await user.selectOptions(select, 'ay-2024');

      expect(mockOnAcademicYearChange).toHaveBeenCalledWith('ay-2024');
      expect(mockOnDateRangeChange).toHaveBeenCalledWith({
        start: '2024-07-01',
        end: '2025-06-30',
      });
    });

    it('should call onAcademicYearChange with null when Custom Range is selected', async () => {
      const user = userEvent.setup();

      render(
        <TimelineControls
          filters={defaultFilters}
          onFiltersChange={mockOnFiltersChange}
          dateRange={defaultDateRange}
          onDateRangeChange={mockOnDateRangeChange}
          viewMode={defaultViewMode}
          onViewModeChange={mockOnViewModeChange}
          academicYears={mockAcademicYears}
          selectedAcademicYear="ay-2024"
          onAcademicYearChange={mockOnAcademicYearChange}
        />,
        { wrapper: createWrapper() }
      );

      const select = screen.getByDisplayValue('2024-2025');
      await user.selectOptions(select, '');

      expect(mockOnAcademicYearChange).toHaveBeenCalledWith(null);
    });
  });

  describe('Filter Panel Interactions', () => {
    it('should toggle filter panel when filters button is clicked', async () => {
      const user = userEvent.setup();

      render(
        <TimelineControls
          filters={defaultFilters}
          onFiltersChange={mockOnFiltersChange}
          dateRange={defaultDateRange}
          onDateRangeChange={mockOnDateRangeChange}
          viewMode={defaultViewMode}
          onViewModeChange={mockOnViewModeChange}
          availableFaculty={mockFaculty}
          availableRotations={mockRotations}
        />,
        { wrapper: createWrapper() }
      );

      // Initially filters panel is hidden
      expect(screen.queryByText('Workload Status')).not.toBeInTheDocument();

      // Click to open
      const filtersButton = screen.getByText('Filters');
      await user.click(filtersButton);

      // Panel should be visible
      await waitFor(() => {
        expect(screen.getByText('Workload Status')).toBeInTheDocument();
      });

      // Click to close
      await user.click(filtersButton);

      // Panel should be hidden again
      await waitFor(() => {
        expect(screen.queryByText('Workload Status')).not.toBeInTheDocument();
      });
    });

    it('should toggle faculty selection', async () => {
      const user = userEvent.setup();

      render(
        <TimelineControls
          filters={defaultFilters}
          onFiltersChange={mockOnFiltersChange}
          dateRange={defaultDateRange}
          onDateRangeChange={mockOnDateRangeChange}
          viewMode={defaultViewMode}
          onViewModeChange={mockOnViewModeChange}
          availableFaculty={mockFaculty}
        />,
        { wrapper: createWrapper() }
      );

      // Open filter panel
      await user.click(screen.getByText('Filters'));

      // Select a faculty member
      const facultyCheckbox = screen.getByLabelText(/Dr. Smith/);
      await user.click(facultyCheckbox);

      expect(mockOnFiltersChange).toHaveBeenCalledWith({
        view_mode: 'monthly',
        faculty_ids: ['fac-1'],
      });
    });

    it('should toggle rotation selection', async () => {
      const user = userEvent.setup();

      render(
        <TimelineControls
          filters={defaultFilters}
          onFiltersChange={mockOnFiltersChange}
          dateRange={defaultDateRange}
          onDateRangeChange={mockOnDateRangeChange}
          viewMode={defaultViewMode}
          onViewModeChange={mockOnViewModeChange}
          availableRotations={mockRotations}
        />,
        { wrapper: createWrapper() }
      );

      // Open filter panel
      await user.click(screen.getByText('Filters'));

      // Select a rotation
      const rotationCheckbox = screen.getByLabelText(/Inpatient Medicine/);
      await user.click(rotationCheckbox);

      expect(mockOnFiltersChange).toHaveBeenCalledWith({
        view_mode: 'monthly',
        rotation_ids: ['rot-1'],
      });
    });

    it('should toggle workload status filters', async () => {
      const user = userEvent.setup();

      render(
        <TimelineControls
          filters={defaultFilters}
          onFiltersChange={mockOnFiltersChange}
          dateRange={defaultDateRange}
          onDateRangeChange={mockOnDateRangeChange}
          viewMode={defaultViewMode}
          onViewModeChange={mockOnViewModeChange}
        />,
        { wrapper: createWrapper() }
      );

      // Open filter panel
      await user.click(screen.getByText('Filters'));

      // Click on workload status filter
      const overloadedButton = screen.getByText('Overloaded');
      await user.click(overloadedButton);

      expect(mockOnFiltersChange).toHaveBeenCalledWith({
        view_mode: 'monthly',
        workload_status: ['overloaded'],
      });
    });

    it('should clear all filters when clear button is clicked', async () => {
      const user = userEvent.setup();

      const filtersWithData: TimelineFilters = {
        view_mode: 'monthly',
        faculty_ids: ['fac-1'],
        rotation_ids: ['rot-1'],
      };

      render(
        <TimelineControls
          filters={filtersWithData}
          onFiltersChange={mockOnFiltersChange}
          dateRange={defaultDateRange}
          onDateRangeChange={mockOnDateRangeChange}
          viewMode={defaultViewMode}
          onViewModeChange={mockOnViewModeChange}
          availableFaculty={mockFaculty}
          availableRotations={mockRotations}
        />,
        { wrapper: createWrapper() }
      );

      // Open filter panel
      await user.click(screen.getByText('Filters'));

      // Click clear all filters button
      const clearButton = screen.getByText('Clear all filters');
      await user.click(clearButton);

      expect(mockOnFiltersChange).toHaveBeenCalledWith({
        view_mode: 'monthly',
      });
    });
  });

  describe('Loading State', () => {
    it('should disable inputs when loading', () => {
      render(
        <TimelineControls
          filters={defaultFilters}
          onFiltersChange={mockOnFiltersChange}
          dateRange={defaultDateRange}
          onDateRangeChange={mockOnDateRangeChange}
          viewMode={defaultViewMode}
          onViewModeChange={mockOnViewModeChange}
          isLoading={true}
        />,
        { wrapper: createWrapper() }
      );

      const startInput = screen.getByDisplayValue('2024-07-01');
      const endInput = screen.getByDisplayValue('2025-06-30');
      const weeklyButton = screen.getByText('Weekly');
      const filtersButton = screen.getByText('Filters');

      expect(startInput).toBeDisabled();
      expect(endInput).toBeDisabled();
      expect(weeklyButton).toBeDisabled();
      expect(filtersButton).toBeDisabled();
    });
  });

  describe('Empty States', () => {
    it('should display no faculty message when list is empty', async () => {
      const user = userEvent.setup();

      render(
        <TimelineControls
          filters={defaultFilters}
          onFiltersChange={mockOnFiltersChange}
          dateRange={defaultDateRange}
          onDateRangeChange={mockOnDateRangeChange}
          viewMode={defaultViewMode}
          onViewModeChange={mockOnViewModeChange}
          availableFaculty={[]}
        />,
        { wrapper: createWrapper() }
      );

      // Open filter panel
      await user.click(screen.getByText('Filters'));

      expect(screen.getByText('No faculty available')).toBeInTheDocument();
    });

    it('should display no rotations message when list is empty', async () => {
      const user = userEvent.setup();

      render(
        <TimelineControls
          filters={defaultFilters}
          onFiltersChange={mockOnFiltersChange}
          dateRange={defaultDateRange}
          onDateRangeChange={mockOnDateRangeChange}
          viewMode={defaultViewMode}
          onViewModeChange={mockOnViewModeChange}
          availableRotations={[]}
        />,
        { wrapper: createWrapper() }
      );

      // Open filter panel
      await user.click(screen.getByText('Filters'));

      expect(screen.getByText('No rotations available')).toBeInTheDocument();
    });
  });
});
