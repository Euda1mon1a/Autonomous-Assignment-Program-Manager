import { render, screen, waitFor } from '@/test-utils';
import userEvent from '@testing-library/user-event';
import { TimelineRow, AssignmentTooltip } from '@/features/fmit-timeline/TimelineRow';
import type {
  FacultyTimelineRow,
  TimePeriod,
  TimelineAssignment,
  AssignmentTooltipData,
} from '@/features/fmit-timeline/types';
import { createWrapper } from '../../utils/test-utils';

describe('TimelineRow', () => {
  const mockOnAssignmentHover = jest.fn();
  const mockOnAssignmentClick = jest.fn();

  const mockPeriods: TimePeriod[] = [
    {
      label: 'Week 1',
      start_date: '2024-07-01',
      end_date: '2024-07-07',
      is_current: false,
    },
    {
      label: 'Week 2',
      start_date: '2024-07-08',
      end_date: '2024-07-14',
      is_current: true,
    },
    {
      label: 'Week 3',
      start_date: '2024-07-15',
      end_date: '2024-07-21',
      is_current: false,
    },
  ];

  const mockAssignment: TimelineAssignment = {
    id: 'assign-1',
    assignment_id: 'assign-1',
    faculty_id: 'fac-1',
    faculty_name: 'Dr. Smith',
    rotation_name: 'Inpatient Medicine',
    rotation_id: 'rot-1',
    start_date: '2024-07-01',
    end_date: '2024-07-14',
    status: 'scheduled',
    activity_type: 'Clinical',
    hours_per_week: 40,
    color: '#3b82f6',
    notes: 'Standard rotation',
  };

  const mockRow: FacultyTimelineRow = {
    faculty_id: 'fac-1',
    faculty_name: 'Dr. John Smith',
    specialty: 'Internal Medicine',
    workload_status: 'on-track',
    total_hours: 160,
    utilization_percentage: 75,
    assignments: [mockAssignment],
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Initial Rendering', () => {
    it('should render faculty name', () => {
      render(
        <TimelineRow
          row={mockRow}
          periods={mockPeriods}
        />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('Dr. John Smith')).toBeInTheDocument();
    });

    it('should render specialty', () => {
      render(
        <TimelineRow
          row={mockRow}
          periods={mockPeriods}
        />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('Internal Medicine')).toBeInTheDocument();
    });

    it('should render workload status badge', () => {
      render(
        <TimelineRow
          row={mockRow}
          periods={mockPeriods}
        />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('On Track')).toBeInTheDocument();
    });

    it('should render utilization percentage', () => {
      render(
        <TimelineRow
          row={mockRow}
          periods={mockPeriods}
        />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('75%')).toBeInTheDocument();
    });

    it('should render total hours', () => {
      render(
        <TimelineRow
          row={mockRow}
          periods={mockPeriods}
        />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('160 hrs total')).toBeInTheDocument();
    });

    it('should render assignment block', () => {
      render(
        <TimelineRow
          row={mockRow}
          periods={mockPeriods}
        />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('Inpatient Medicine')).toBeInTheDocument();
    });
  });

  describe('Workload Status Indicators', () => {
    it('should display check icon for on-track status', () => {
      render(
        <TimelineRow
          row={mockRow}
          periods={mockPeriods}
        />,
        { wrapper: createWrapper() }
      );

      const badge = screen.getByText('On Track').closest('div');
      expect(badge).toBeInTheDocument();
    });

    it('should display alert icon for overloaded status', () => {
      const overloadedRow: FacultyTimelineRow = {
        ...mockRow,
        workload_status: 'overloaded',
        utilization_percentage: 120,
      };

      render(
        <TimelineRow
          row={overloadedRow}
          periods={mockPeriods}
        />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('Overloaded')).toBeInTheDocument();
    });

    it('should display clock icon for underutilized status', () => {
      const underutilizedRow: FacultyTimelineRow = {
        ...mockRow,
        workload_status: 'underutilized',
        utilization_percentage: 45,
      };

      render(
        <TimelineRow
          row={underutilizedRow}
          periods={mockPeriods}
        />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('Underutilized')).toBeInTheDocument();
    });
  });

  describe('Assignment Block Rendering', () => {
    it('should render multiple assignment blocks', () => {
      const rowWithMultipleAssignments: FacultyTimelineRow = {
        ...mockRow,
        assignments: [
          mockAssignment,
          {
            ...mockAssignment,
            id: 'assign-2',
            assignment_id: 'assign-2',
            rotation_name: 'Clinic',
            start_date: '2024-07-15',
            end_date: '2024-07-21',
          },
        ],
      };

      render(
        <TimelineRow
          row={rowWithMultipleAssignments}
          periods={mockPeriods}
        />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('Inpatient Medicine')).toBeInTheDocument();
      expect(screen.getByText('Clinic')).toBeInTheDocument();
    });

    it('should display empty state when no assignments', () => {
      const emptyRow: FacultyTimelineRow = {
        ...mockRow,
        assignments: [],
      };

      render(
        <TimelineRow
          row={emptyRow}
          periods={mockPeriods}
        />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('No assignments')).toBeInTheDocument();
    });

    it('should display assignment status indicator dot', () => {
      const { container } = render(
        <TimelineRow
          row={mockRow}
          periods={mockPeriods}
        />,
        { wrapper: createWrapper() }
      );

      // Check for status indicator dot
      const statusDot = container.querySelector('.absolute.top-1.right-1');
      expect(statusDot).toBeInTheDocument();
    });
  });

  describe('Assignment Interactions', () => {
    it('should call onAssignmentHover when hovering over assignment', async () => {
      const user = userEvent.setup();

      render(
        <TimelineRow
          row={mockRow}
          periods={mockPeriods}
          onAssignmentHover={mockOnAssignmentHover}
        />,
        { wrapper: createWrapper() }
      );

      const assignmentBlock = screen.getByText('Inpatient Medicine');
      await user.hover(assignmentBlock.closest('div')!);

      await waitFor(() => {
        expect(mockOnAssignmentHover).toHaveBeenCalled();
        const callArg = mockOnAssignmentHover.mock.calls[0][0];
        expect(callArg).toHaveProperty('assignment');
        expect(callArg).toHaveProperty('position');
      });
    });

    it('should call onAssignmentHover with null when mouse leaves assignment', async () => {
      const user = userEvent.setup();

      render(
        <TimelineRow
          row={mockRow}
          periods={mockPeriods}
          onAssignmentHover={mockOnAssignmentHover}
        />,
        { wrapper: createWrapper() }
      );

      const assignmentBlock = screen.getByText('Inpatient Medicine').closest('div')!;

      await user.hover(assignmentBlock);
      await user.unhover(assignmentBlock);

      await waitFor(() => {
        expect(mockOnAssignmentHover).toHaveBeenCalledWith(null);
      });
    });

    it('should call onAssignmentClick when assignment is clicked', async () => {
      const user = userEvent.setup();

      render(
        <TimelineRow
          row={mockRow}
          periods={mockPeriods}
          onAssignmentClick={mockOnAssignmentClick}
        />,
        { wrapper: createWrapper() }
      );

      const assignmentBlock = screen.getByText('Inpatient Medicine');
      await user.click(assignmentBlock);

      expect(mockOnAssignmentClick).toHaveBeenCalledWith(mockAssignment);
    });
  });

  describe('Timeline Grid', () => {
    it('should render background grid for each period', () => {
      const { container } = render(
        <TimelineRow
          row={mockRow}
          periods={mockPeriods}
        />,
        { wrapper: createWrapper() }
      );

      // Check for grid lines (one per period)
      const gridLines = container.querySelectorAll('.flex-1.border-r.border-gray-100');
      expect(gridLines.length).toBe(mockPeriods.length);
    });

    it('should highlight current period', () => {
      const { container } = render(
        <TimelineRow
          row={mockRow}
          periods={mockPeriods}
        />,
        { wrapper: createWrapper() }
      );

      // Check for current period highlight (Week 2 is current)
      const currentPeriod = container.querySelector('.bg-blue-50\\/30');
      expect(currentPeriod).toBeInTheDocument();
    });
  });

  describe('Utilization Bar', () => {
    it('should render utilization bar with correct width', () => {
      const { container } = render(
        <TimelineRow
          row={mockRow}
          periods={mockPeriods}
        />,
        { wrapper: createWrapper() }
      );

      const utilizationBar = container.querySelector('.h-1\\.5.rounded-full.transition-all');
      expect(utilizationBar).toHaveStyle({ width: '75%' });
    });

    it('should cap utilization bar at 100%', () => {
      const overloadedRow: FacultyTimelineRow = {
        ...mockRow,
        utilization_percentage: 120,
        workload_status: 'overloaded',
      };

      const { container } = render(
        <TimelineRow
          row={overloadedRow}
          periods={mockPeriods}
        />,
        { wrapper: createWrapper() }
      );

      const utilizationBar = container.querySelector('.h-1\\.5.rounded-full.transition-all');
      expect(utilizationBar).toHaveStyle({ width: '100%' });
    });
  });
});

describe('AssignmentTooltip', () => {
  const mockTooltipData: AssignmentTooltipData = {
    assignment: {
      id: 'assign-1',
      assignment_id: 'assign-1',
      faculty_id: 'fac-1',
      faculty_name: 'Dr. Smith',
      rotation_name: 'Inpatient Medicine',
      rotation_id: 'rot-1',
      start_date: '2024-07-01',
      end_date: '2024-07-14',
      status: 'in-progress',
      activity_type: 'Clinical',
      hours_per_week: 40,
      color: '#3b82f6',
      notes: 'Standard rotation assignment',
    },
    position: { x: 100, y: 200 },
  };

  it('should render rotation name', () => {
    render(<AssignmentTooltip data={mockTooltipData} />, { wrapper: createWrapper() });

    expect(screen.getByText('Inpatient Medicine')).toBeInTheDocument();
  });

  it('should render faculty name', () => {
    render(<AssignmentTooltip data={mockTooltipData} />, { wrapper: createWrapper() });

    expect(screen.getByText('Dr. Smith')).toBeInTheDocument();
  });

  it('should render start and end dates', () => {
    render(<AssignmentTooltip data={mockTooltipData} />, { wrapper: createWrapper() });

    expect(screen.getByText(/Start:/)).toBeInTheDocument();
    expect(screen.getByText(/End:/)).toBeInTheDocument();
  });

  it('should render hours per week', () => {
    render(<AssignmentTooltip data={mockTooltipData} />, { wrapper: createWrapper() });

    expect(screen.getByText(/Hours\/week:/)).toBeInTheDocument();
    expect(screen.getByText('40')).toBeInTheDocument();
  });

  it('should render assignment status', () => {
    render(<AssignmentTooltip data={mockTooltipData} />, { wrapper: createWrapper() });

    expect(screen.getByText(/Status:/)).toBeInTheDocument();
    expect(screen.getByText('in-progress')).toBeInTheDocument();
  });

  it('should render notes when provided', () => {
    render(<AssignmentTooltip data={mockTooltipData} />, { wrapper: createWrapper() });

    expect(screen.getByText('Standard rotation assignment')).toBeInTheDocument();
  });

  it('should not render notes section when notes are absent', () => {
    const dataWithoutNotes: AssignmentTooltipData = {
      ...mockTooltipData,
      assignment: {
        ...mockTooltipData.assignment,
        notes: undefined,
      },
    };

    render(<AssignmentTooltip data={dataWithoutNotes} />, { wrapper: createWrapper() });

    const notesText = screen.queryByText('Standard rotation assignment');
    expect(notesText).not.toBeInTheDocument();
  });

  it('should position tooltip correctly', () => {
    const { container } = render(<AssignmentTooltip data={mockTooltipData} />, {
      wrapper: createWrapper(),
    });

    const tooltipContainer = container.firstChild as HTMLElement;
    expect(tooltipContainer).toHaveStyle({
      left: '100px',
      top: '200px',
    });
  });
});
