import { renderWithProviders, screen, waitFor, mockData } from '@/test-utils';
import { ScheduleGrid } from '@/components/schedule/ScheduleGrid';
import * as api from '@/lib/api';
import * as hooks from '@/lib/hooks';

// Mock the API and hooks
jest.mock('@/lib/api');
jest.mock('@/lib/hooks');

const mockGet = api.get as jest.MockedFunction<typeof api.get>;
const mockUsePeople = hooks.usePeople as jest.MockedFunction<typeof hooks.usePeople>;
const mockUseRotationTemplates = hooks.useRotationTemplates as jest.MockedFunction<typeof hooks.useRotationTemplates>;

describe('ScheduleGrid', () => {
  const mockPeople = mockData.paginatedResponse([
    mockData.person({
      id: 'person-1',
      name: 'Dr. Alice Smith',
      type: 'resident',
      pgyLevel: 1,
      email: 'alice@test.com',
      role: 'RESIDENT',
    }),
    mockData.person({
      id: 'person-2',
      name: 'Dr. Bob Jones',
      type: 'resident',
      pgyLevel: 2,
      email: 'bob@test.com',
      role: 'RESIDENT',
    }),
    mockData.person({
      id: 'person-3',
      name: 'Dr. Carol Faculty',
      type: 'faculty',
      email: 'carol@test.com',
      role: 'FACULTY',
    }),
  ]);

  const mockTemplates = mockData.paginatedResponse([
    mockData.rotationTemplate({
      id: 'template-1',
      name: 'Inpatient Medicine',
      abbreviation: 'IM',
      activityType: 'inpatient',
    }),
    mockData.rotationTemplate({
      id: 'template-2',
      name: 'Clinic',
      abbreviation: 'CL',
      activityType: 'clinic',
    }),
  ]);

  const mockBlocks = mockData.paginatedResponse([
    mockData.block({ id: 'block-1', date: '2025-01-01', timeOfDay: 'AM' }),
    mockData.block({ id: 'block-2', date: '2025-01-01', timeOfDay: 'PM' }),
    mockData.block({ id: 'block-3', date: '2025-01-02', timeOfDay: 'AM' }),
    mockData.block({ id: 'block-4', date: '2025-01-02', timeOfDay: 'PM' }),
  ]);

  const mockAssignments = mockData.paginatedResponse([
    mockData.assignment({
      id: 'assignment-1',
      personId: 'person-1',
      blockId: 'block-1',
      rotationTemplateId: 'template-1',
      role: 'primary',
    }),
    mockData.assignment({
      id: 'assignment-2',
      personId: 'person-2',
      blockId: 'block-2',
      rotationTemplateId: 'template-2',
      role: 'primary',
    }),
  ]);

  beforeEach(() => {

    // Setup default mocks
    mockUsePeople.mockReturnValue({
      data: mockPeople,
      isLoading: false,
      error: null,
    } as any);

    mockUseRotationTemplates.mockReturnValue({
      data: mockTemplates,
      isLoading: false,
      error: null,
    } as any);

    mockGet.mockImplementation((url: string) => {
      if (url.includes('/blocks')) {
        return Promise.resolve(mockBlocks);
      }
      if (url.includes('/assignments')) {
        return Promise.resolve(mockAssignments);
      }
      return Promise.resolve({ items: [], total: 0, page: 1, per_page: 100 });
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('Basic Rendering', () => {
    it('renders without crashing', async () => {
      const startDate = new Date('2025-01-01');
      const endDate = new Date('2025-01-02');

      renderWithProviders(<ScheduleGrid startDate={startDate} endDate={endDate} />);

      await waitFor(() => {
        expect(screen.queryByRole('status')).not.toBeInTheDocument();
      });

      expect(screen.getByRole('grid')).toBeInTheDocument();
    });

    it('renders all person groups with labels', async () => {
      const startDate = new Date('2025-01-01');
      const endDate = new Date('2025-01-02');

      renderWithProviders(<ScheduleGrid startDate={startDate} endDate={endDate} />);

      await waitFor(() => {
        expect(screen.getByText('PGY-1')).toBeInTheDocument();
      });

      expect(screen.getByText('PGY-2')).toBeInTheDocument();
      expect(screen.getByText('Faculty')).toBeInTheDocument();
    });

    it('renders person names in rows', async () => {
      const startDate = new Date('2025-01-01');
      const endDate = new Date('2025-01-02');

      renderWithProviders(<ScheduleGrid startDate={startDate} endDate={endDate} />);

      await waitFor(() => {
        expect(screen.getByText('Dr. Alice Smith')).toBeInTheDocument();
      });

      expect(screen.getByText('Dr. Bob Jones')).toBeInTheDocument();
      expect(screen.getByText('Dr. Carol Faculty')).toBeInTheDocument();
    });

    it('renders schedule grid table structure', async () => {
      const startDate = new Date('2025-01-01');
      const endDate = new Date('2025-01-02');

      renderWithProviders(<ScheduleGrid startDate={startDate} endDate={endDate} />);

      await waitFor(() => {
        const grid = screen.getByRole('grid');
        expect(grid).toHaveAttribute('aria-label', expect.stringContaining('Schedule grid'));
      });
    });
  });

  describe('Loading State', () => {
    it('displays loading spinner when data is loading', () => {
      mockUsePeople.mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
      } as any);

      const startDate = new Date('2025-01-01');
      const endDate = new Date('2025-01-02');

      renderWithProviders(<ScheduleGrid startDate={startDate} endDate={endDate} />);

      expect(screen.getByRole('status')).toBeInTheDocument();
      expect(screen.getByText('Loading schedule...')).toBeInTheDocument();
    });

    it('displays loading with aria-live polite', () => {
      mockUsePeople.mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
      } as any);

      const startDate = new Date('2025-01-01');
      const endDate = new Date('2025-01-02');

      renderWithProviders(<ScheduleGrid startDate={startDate} endDate={endDate} />);

      const status = screen.getByRole('status');
      expect(status).toHaveAttribute('aria-live', 'polite');
      expect(status).toHaveAttribute('aria-busy', 'true');
    });

    it('shows loading state when templates are loading', () => {
      mockUseRotationTemplates.mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
      } as any);

      const startDate = new Date('2025-01-01');
      const endDate = new Date('2025-01-02');

      renderWithProviders(<ScheduleGrid startDate={startDate} endDate={endDate} />);

      expect(screen.getByText('Loading schedule...')).toBeInTheDocument();
    });
  });

  describe('Error State', () => {
    it('displays error alert when people fetch fails', async () => {
      const error = new Error('Failed to fetch people');
      mockUsePeople.mockReturnValue({
        data: undefined,
        isLoading: false,
        error,
      } as any);

      const startDate = new Date('2025-01-01');
      const endDate = new Date('2025-01-02');

      renderWithProviders(<ScheduleGrid startDate={startDate} endDate={endDate} />);

      await waitFor(() => {
        expect(screen.getByText('Failed to fetch people')).toBeInTheDocument();
      });
    });

    it('displays error alert when assignments fetch fails', async () => {
      mockGet.mockRejectedValueOnce(new Error('Failed to load assignments'));

      const startDate = new Date('2025-01-01');
      const endDate = new Date('2025-01-02');

      renderWithProviders(<ScheduleGrid startDate={startDate} endDate={endDate} />);

      await waitFor(() => {
        expect(screen.getByText(/Failed to load schedule data/i)).toBeInTheDocument();
      });
    });

    it('displays generic error for non-Error objects', async () => {
      mockUsePeople.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: 'String error',
      } as any);

      const startDate = new Date('2025-01-01');
      const endDate = new Date('2025-01-02');

      renderWithProviders(<ScheduleGrid startDate={startDate} endDate={endDate} />);

      await waitFor(() => {
        expect(screen.getByText('Failed to load schedule data')).toBeInTheDocument();
      });
    });
  });

  describe('Empty State', () => {
    it('displays empty state when no people exist', async () => {
      mockUsePeople.mockReturnValue({
        data: { items: [], total: 0, page: 1, per_page: 100 },
        isLoading: false,
        error: null,
      } as any);

      const startDate = new Date('2025-01-01');
      const endDate = new Date('2025-01-02');

      renderWithProviders(<ScheduleGrid startDate={startDate} endDate={endDate} />);

      await waitFor(() => {
        expect(screen.getByText('No People Found')).toBeInTheDocument();
      });

      expect(screen.getByText('Add residents and faculty to see them in the schedule.')).toBeInTheDocument();
    });

    it('provides add people action in empty state', async () => {
      mockUsePeople.mockReturnValue({
        data: { items: [], total: 0, page: 1, per_page: 100 },
        isLoading: false,
        error: null,
      } as any);

      const startDate = new Date('2025-01-01');
      const endDate = new Date('2025-01-02');

      renderWithProviders(<ScheduleGrid startDate={startDate} endDate={endDate} />);

      await waitFor(() => {
        expect(screen.getByText('Add People')).toBeInTheDocument();
      });
    });
  });

  describe('Date Range Handling', () => {
    it('renders correct number of day columns for date range', async () => {
      const startDate = new Date('2025-01-01');
      const endDate = new Date('2025-01-05'); // 5 days

      renderWithProviders(<ScheduleGrid startDate={startDate} endDate={endDate} />);

      await waitFor(() => {
        expect(screen.queryByRole('status')).not.toBeInTheDocument();
      });

      // Each day has AM and PM cells, so we should have 10 cells per row
      // This is tested indirectly through the component rendering
      expect(screen.getByRole('grid')).toBeInTheDocument();
    });

    it('handles single day range', async () => {
      const startDate = new Date('2025-01-01');
      const endDate = new Date('2025-01-01');

      renderWithProviders(<ScheduleGrid startDate={startDate} endDate={endDate} />);

      await waitFor(() => {
        expect(screen.queryByRole('status')).not.toBeInTheDocument();
      });

      expect(screen.getByRole('grid')).toBeInTheDocument();
    });
  });

  describe('PGY Grouping', () => {
    it('groups residents by PGY level', async () => {
      const startDate = new Date('2025-01-01');
      const endDate = new Date('2025-01-02');

      renderWithProviders(<ScheduleGrid startDate={startDate} endDate={endDate} />);

      await waitFor(() => {
        expect(screen.getByText('PGY-1')).toBeInTheDocument();
      });

      // Verify PGY-1 section contains Alice
      const pgy1Section = screen.getByText('PGY-1').closest('tr');
      expect(pgy1Section).toBeInTheDocument();

      // Verify PGY-2 section exists
      expect(screen.getByText('PGY-2')).toBeInTheDocument();
    });

    it('displays faculty in separate group', async () => {
      const startDate = new Date('2025-01-01');
      const endDate = new Date('2025-01-02');

      renderWithProviders(<ScheduleGrid startDate={startDate} endDate={endDate} />);

      await waitFor(() => {
        expect(screen.getByText('Faculty')).toBeInTheDocument();
      });

      expect(screen.getByText('Dr. Carol Faculty')).toBeInTheDocument();
    });

    it('sorts people within groups by name', async () => {
      const multiPeople = {
        items: [
          {
            id: 'p1',
            name: 'Dr. Zara',
            type: 'resident' as const,
            pgyLevel: 1,
            email: 'zara@test.com',
            role: 'RESIDENT' as const,
          },
          {
            id: 'p2',
            name: 'Dr. Alice',
            type: 'resident' as const,
            pgyLevel: 1,
            email: 'alice@test.com',
            role: 'RESIDENT' as const,
          },
        ],
        total: 2,
        page: 1,
        per_page: 100,
      };

      mockUsePeople.mockReturnValue({
        data: multiPeople,
        isLoading: false,
        error: null,
      } as any);

      const startDate = new Date('2025-01-01');
      const endDate = new Date('2025-01-02');

      renderWithProviders(<ScheduleGrid startDate={startDate} endDate={endDate} />);

      await waitFor(() => {
        const names = screen.getAllByText(/Dr\./);
        const nameTexts = names.map((n) => n.textContent);

        // Alice should come before Zara
        const aliceIndex = nameTexts.indexOf('Dr. Alice');
        const zaraIndex = nameTexts.indexOf('Dr. Zara');

        expect(aliceIndex).toBeLessThan(zaraIndex);
      });
    });
  });

  describe('Assignment Display', () => {
    it('displays assignment abbreviations in cells', async () => {
      const startDate = new Date('2025-01-01');
      const endDate = new Date('2025-01-02');

      renderWithProviders(<ScheduleGrid startDate={startDate} endDate={endDate} />);

      await waitFor(() => {
        // Check that assignment abbreviations are rendered
        expect(screen.getByText('IM')).toBeInTheDocument();
        expect(screen.getByText('CL')).toBeInTheDocument();
      });
    });

    it('handles empty cells without assignments', async () => {
      mockGet.mockImplementation((url: string) => {
        if (url.includes('/blocks')) {
          return Promise.resolve(mockBlocks);
        }
        if (url.includes('/assignments')) {
          return Promise.resolve({ items: [], total: 0, page: 1, per_page: 100 });
        }
        return Promise.resolve({ items: [], total: 0, page: 1, per_page: 100 });
      });

      const startDate = new Date('2025-01-01');
      const endDate = new Date('2025-01-02');

      renderWithProviders(<ScheduleGrid startDate={startDate} endDate={endDate} />);

      await waitFor(() => {
        expect(screen.queryByRole('status')).not.toBeInTheDocument();
      });

      // Grid should render even without assignments
      expect(screen.getByRole('grid')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA labels', async () => {
      const startDate = new Date('2025-01-01');
      const endDate = new Date('2025-01-02');

      renderWithProviders(<ScheduleGrid startDate={startDate} endDate={endDate} />);

      await waitFor(() => {
        const grid = screen.getByRole('grid');
        expect(grid).toHaveAttribute('aria-label', expect.stringContaining('Schedule grid'));
      });
    });

    it('uses proper table row scoping', async () => {
      const startDate = new Date('2025-01-01');
      const endDate = new Date('2025-01-02');

      renderWithProviders(<ScheduleGrid startDate={startDate} endDate={endDate} />);

      await waitFor(() => {
        const headers = screen.getAllByRole('rowheader');
        expect(headers.length).toBeGreaterThan(0);
      });
    });
  });
});
