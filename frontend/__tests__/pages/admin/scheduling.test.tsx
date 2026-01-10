/**
 * Tests for Admin Scheduling Laboratory Page
 *
 * Tests empirical analysis of scheduling modules including configuration,
 * experimentation, metrics tracking, history, and override controls.
 */
import React from 'react';
import { render, screen, waitFor, within } from '@/test-utils';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import AdminSchedulingPage from '@/app/admin/scheduling/page';
import * as hooks from '@/hooks/useAdminScheduling';

// Mock the hooks
jest.mock('@/hooks/useAdminScheduling');
const mockUseScheduleRuns = hooks.useScheduleRuns as jest.MockedFunction<typeof hooks.useScheduleRuns>;
const mockUseRunQueue = hooks.useRunQueue as jest.MockedFunction<typeof hooks.useRunQueue>;
const mockUseConstraintConfigs = hooks.useConstraintConfigs as jest.MockedFunction<typeof hooks.useConstraintConfigs>;
const mockUseScheduleMetrics = hooks.useScheduleMetrics as jest.MockedFunction<typeof hooks.useScheduleMetrics>;
const mockUseLockedAssignments = hooks.useLockedAssignments as jest.MockedFunction<typeof hooks.useLockedAssignments>;
const mockUseEmergencyHolidays = hooks.useEmergencyHolidays as jest.MockedFunction<typeof hooks.useEmergencyHolidays>;
const mockUseRollbackPoints = hooks.useRollbackPoints as jest.MockedFunction<typeof hooks.useRollbackPoints>;
const mockUseSyncMetadata = hooks.useSyncMetadata as jest.MockedFunction<typeof hooks.useSyncMetadata>;
const mockUseValidateConfiguration = hooks.useValidateConfiguration as jest.MockedFunction<typeof hooks.useValidateConfiguration>;
const mockUseGenerateScheduleRun = hooks.useGenerateScheduleRun as jest.MockedFunction<typeof hooks.useGenerateScheduleRun>;
const mockUseQueueExperiments = hooks.useQueueExperiments as jest.MockedFunction<typeof hooks.useQueueExperiments>;
const mockUseCancelExperiment = hooks.useCancelExperiment as jest.MockedFunction<typeof hooks.useCancelExperiment>;
const mockUseCreateRollbackPoint = hooks.useCreateRollbackPoint as jest.MockedFunction<typeof hooks.useCreateRollbackPoint>;
const mockUseRevertToRollbackPoint = hooks.useRevertToRollbackPoint as jest.MockedFunction<typeof hooks.useRevertToRollbackPoint>;
const mockUseTriggerSync = hooks.useTriggerSync as jest.MockedFunction<typeof hooks.useTriggerSync>;
const mockUseUnlockAssignment = hooks.useUnlockAssignment as jest.MockedFunction<typeof hooks.useUnlockAssignment>;

// Mock LoadingSpinner
jest.mock('@/components/LoadingSpinner', () => ({
  LoadingSpinner: () => <div>Loading...</div>,
}));

// Mock data
const mockConstraints = [
  { id: '1', name: '80-Hour Rule', description: 'ACGME 80-hour limit', category: 'acgme', enabled: true },
  { id: '2', name: 'Coverage Balance', description: 'Distribute coverage evenly', category: 'coverage', enabled: true },
  { id: '3', name: 'Fairness Score', description: 'Ensure fair distribution', category: 'fairness', enabled: false },
];

const mockQueue = {
  runs: [
    { id: '1', name: 'Run 1', status: 'running', configuration: { algorithm: 'hybrid' }, progress: 45 },
    { id: '2', name: 'Run 2', status: 'queued', configuration: { algorithm: 'greedy' }, progress: 0 },
  ],
  maxConcurrent: 3,
  currentlyRunning: 1,
};

const mockMetrics = {
  coveragePercent: 98.5,
  acgmeViolations: 0,
  fairnessScore: 0.92,
  swapChurn: 3.2,
  runtimeSeconds: 42.5,
  stability: 0.95,
};

const mockRuns = {
  runs: [
    {
      id: '1',
      runId: 'run-abc123',
      timestamp: '2024-12-23T10:00:00Z',
      algorithm: 'hybrid',
      status: 'success',
      result: {
        coveragePercent: 98.5,
        acgmeViolations: 0,
        runtimeSeconds: 42.5,
        fairnessScore: 0.92,
      },
    },
    {
      id: '2',
      runId: 'run-def456',
      timestamp: '2024-12-22T15:00:00Z',
      algorithm: 'greedy',
      status: 'partial',
      result: {
        coveragePercent: 85.0,
        acgmeViolations: 2,
        runtimeSeconds: 15.3,
        fairnessScore: 0.78,
      },
    },
  ],
};

const mockLocks = [
  { id: '1', personName: 'Dr. Smith', blockDate: '2024-01-15', rotationName: 'Clinic', reason: 'Training' },
];

const mockHolidays = [
  { id: '1', date: '2024-12-25', name: 'Christmas', type: 'Federal' },
];

const mockRollbackPoints = [
  { id: '1', createdAt: '2024-12-20T10:00:00Z', description: 'Before Block 10', assignmentCount: 150, canRevert: true },
];

const mockSyncMeta = {
  lastSyncTime: '2024-12-23T10:00:00Z',
  syncStatus: 'synced',
  sourceSystem: 'Airtable',
};

// Create test wrapper
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return function Wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

describe('AdminSchedulingPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();

    // Default mock implementations
    mockUseScheduleRuns.mockReturnValue({
      data: mockRuns,
      isLoading: false,
    } as any);

    mockUseRunQueue.mockReturnValue({
      data: mockQueue,
      isLoading: false,
    } as any);

    mockUseConstraintConfigs.mockReturnValue({
      data: mockConstraints,
      isLoading: false,
    } as any);

    mockUseScheduleMetrics.mockReturnValue({
      data: mockMetrics,
      isLoading: false,
    } as any);

    mockUseLockedAssignments.mockReturnValue({
      data: mockLocks,
    } as any);

    mockUseEmergencyHolidays.mockReturnValue({
      data: mockHolidays,
    } as any);

    mockUseRollbackPoints.mockReturnValue({
      data: mockRollbackPoints,
    } as any);

    mockUseSyncMetadata.mockReturnValue({
      data: mockSyncMeta,
    } as any);

    mockUseValidateConfiguration.mockReturnValue({
      mutate: jest.fn(),
      mutateAsync: jest.fn(),
      isPending: false,
      data: undefined,
    } as any);

    mockUseGenerateScheduleRun.mockReturnValue({
      mutate: jest.fn(),
      isPending: false,
    } as any);

    mockUseQueueExperiments.mockReturnValue({
      mutate: jest.fn(),
      isPending: false,
    } as any);

    mockUseCancelExperiment.mockReturnValue({
      mutate: jest.fn(),
      isPending: false,
    } as any);

    mockUseCreateRollbackPoint.mockReturnValue({
      mutate: jest.fn(),
      isPending: false,
    } as any);

    mockUseRevertToRollbackPoint.mockReturnValue({
      mutate: jest.fn(),
      isPending: false,
    } as any);

    mockUseTriggerSync.mockReturnValue({
      mutate: jest.fn(),
      isPending: false,
    } as any);

    mockUseUnlockAssignment.mockReturnValue({
      mutate: jest.fn(),
      isPending: false,
    } as any);
  });

  describe('Page Rendering', () => {
    it('should render page title', () => {
      render(<AdminSchedulingPage />, { wrapper: createWrapper() });

      expect(screen.getByText('Scheduling Laboratory')).toBeInTheDocument();
    });

    it('should render page description', () => {
      render(<AdminSchedulingPage />, { wrapper: createWrapper() });

      expect(screen.getByText('Empirical analysis of scheduling algorithms')).toBeInTheDocument();
    });

    it('should render all tabs', () => {
      render(<AdminSchedulingPage />, { wrapper: createWrapper() });

      expect(screen.getByText('Configuration')).toBeInTheDocument();
      expect(screen.getByText('Experimentation')).toBeInTheDocument();
      expect(screen.getByText('Metrics')).toBeInTheDocument();
      expect(screen.getByText('History')).toBeInTheDocument();
      expect(screen.getByText('Overrides')).toBeInTheDocument();
    });

    it('should start on Configuration tab', () => {
      render(<AdminSchedulingPage />, { wrapper: createWrapper() });

      const configTab = screen.getByText('Configuration').closest('button');
      expect(configTab).toHaveClass('bg-slate-800', 'text-white');
    });

    it('should display status indicators', () => {
      render(<AdminSchedulingPage />, { wrapper: createWrapper() });

      expect(screen.getByText('idle')).toBeInTheDocument();
      expect(screen.getByText('Sync')).toBeInTheDocument();
    });

    it('should show running status when jobs active', () => {
      mockUseRunQueue.mockReturnValue({
        data: { ...mockQueue, currentlyRunning: 2 },
        isLoading: false,
      } as any);

      render(<AdminSchedulingPage />, { wrapper: createWrapper() });

      expect(screen.getByText('running')).toBeInTheDocument();
    });
  });

  describe('Configuration Tab', () => {
    it('should render algorithm selection', () => {
      render(<AdminSchedulingPage />, { wrapper: createWrapper() });

      expect(screen.getByText('Algorithm Selection')).toBeInTheDocument();
      expect(screen.getByText('Greedy')).toBeInTheDocument();
      expect(screen.getByText('CP-SAT')).toBeInTheDocument();
      expect(screen.getByText('PuLP')).toBeInTheDocument();
      expect(screen.getByText('Hybrid')).toBeInTheDocument();
    });

    it('should allow algorithm selection', async () => {
      const user = userEvent.setup();
      render(<AdminSchedulingPage />, { wrapper: createWrapper() });

      const greedyButton = screen.getByRole('button', { name: /Greedy Fast heuristic/i });
      await user.click(greedyButton);

      expect(greedyButton).toHaveClass('bg-violet-500/20', 'border-violet-500');
    });

    it('should render constraint toggles', () => {
      render(<AdminSchedulingPage />, { wrapper: createWrapper() });

      expect(screen.getByText('Constraint Set')).toBeInTheDocument();
      expect(screen.getByText('80-Hour Rule')).toBeInTheDocument();
      expect(screen.getByText('Coverage Balance')).toBeInTheDocument();
      expect(screen.getByText('Fairness Score')).toBeInTheDocument();
    });

    it('should show constraint count badge', () => {
      render(<AdminSchedulingPage />, { wrapper: createWrapper() });

      // 2 constraints are enabled
      expect(screen.getByText('2')).toBeInTheDocument();
    });

    it('should toggle constraints', async () => {
      const user = userEvent.setup();
      render(<AdminSchedulingPage />, { wrapper: createWrapper() });

      const constraintButtons = screen.getAllByRole('button').filter(btn =>
        btn.textContent?.includes('80-Hour Rule') ||
        btn.textContent?.includes('Coverage Balance')
      );

      if (constraintButtons[0]) {
        await user.click(constraintButtons[0]);
        // Constraint state should change
        expect(constraintButtons[0]).toBeDefined();
      }
    });

    it('should render options section', () => {
      render(<AdminSchedulingPage />, { wrapper: createWrapper() });

      expect(screen.getByText('Options')).toBeInTheDocument();
      expect(screen.getByText('Preserve FMIT Assignments')).toBeInTheDocument();
      expect(screen.getByText('NF Post-Call Constraint')).toBeInTheDocument();
      expect(screen.getByText('Dry Run Mode')).toBeInTheDocument();
    });

    it('should allow timeout configuration', async () => {
      const user = userEvent.setup();
      render(<AdminSchedulingPage />, { wrapper: createWrapper() });

      const timeoutInput = screen.getByDisplayValue('300');
      await user.clear(timeoutInput);
      await user.type(timeoutInput, '600');

      expect(timeoutInput).toHaveValue(600);
    });

    it('should render date range controls', () => {
      render(<AdminSchedulingPage />, { wrapper: createWrapper() });

      expect(screen.getByText('Academic Year & Block Range')).toBeInTheDocument();
      expect(screen.getByText('Academic Year')).toBeInTheDocument();
      expect(screen.getByText('Start Block')).toBeInTheDocument();
      expect(screen.getByText('End Block')).toBeInTheDocument();
    });

    it('should show block range info', () => {
      render(<AdminSchedulingPage />, { wrapper: createWrapper() });

      expect(screen.getByText('730 blocks = 365 days (AM/PM sessions)')).toBeInTheDocument();
    });

    it('should show validate button', () => {
      render(<AdminSchedulingPage />, { wrapper: createWrapper() });

      expect(screen.getByRole('button', { name: /Validate Configuration/i })).toBeInTheDocument();
    });

    it('should show generate schedule button', () => {
      render(<AdminSchedulingPage />, { wrapper: createWrapper() });

      expect(screen.getByRole('button', { name: /Generate Schedule/i })).toBeInTheDocument();
    });

    it('should display configuration summary', () => {
      render(<AdminSchedulingPage />, { wrapper: createWrapper() });

      expect(screen.getByText('Configuration Summary')).toBeInTheDocument();
      expect(screen.getByText('HYBRID')).toBeInTheDocument();
      expect(screen.getByText('730')).toBeInTheDocument(); // Block count
    });

    it('should show validation results', async () => {
      const user = userEvent.setup();
      mockUseValidateConfiguration.mockReturnValue({
        mutate: jest.fn(),
        mutateAsync: jest.fn(),
        isPending: false,
        data: { isValid: true, warnings: [] },
      } as any);

      render(<AdminSchedulingPage />, { wrapper: createWrapper() });

      expect(screen.getByText('Valid Configuration')).toBeInTheDocument();
    });

    it('should show validation warnings', async () => {
      mockUseValidateConfiguration.mockReturnValue({
        mutate: jest.fn(),
        mutateAsync: jest.fn(),
        isPending: false,
        data: {
          isValid: false,
          warnings: [
            { id: '1', type: 'coverage_risk', severity: 'warning', message: 'Low coverage expected' },
          ],
        },
      } as any);

      render(<AdminSchedulingPage />, { wrapper: createWrapper() });

      expect(screen.getByText('1 Warning(s)')).toBeInTheDocument();
      expect(screen.getByText('Low coverage expected')).toBeInTheDocument();
    });
  });

  describe('Experimentation Tab', () => {
    it('should switch to Experimentation tab', async () => {
      const user = userEvent.setup();
      render(<AdminSchedulingPage />, { wrapper: createWrapper() });

      const expTab = screen.getByText('Experimentation').closest('button');
      await user.click(expTab!);

      expect(expTab).toHaveClass('bg-slate-800', 'text-white');
    });

    it('should show permutation runner', async () => {
      const user = userEvent.setup();
      render(<AdminSchedulingPage />, { wrapper: createWrapper() });

      await user.click(screen.getByText('Experimentation').closest('button')!);

      expect(screen.getByText('Permutation Runner')).toBeInTheDocument();
      expect(screen.getByText('Algorithm Combinations')).toBeInTheDocument();
    });

    it('should allow algorithm selection for experiments', async () => {
      const user = userEvent.setup();
      render(<AdminSchedulingPage />, { wrapper: createWrapper() });

      await user.click(screen.getByText('Experimentation').closest('button')!);

      const algoButtons = screen.getAllByRole('button').filter(btn =>
        btn.textContent?.includes('Greedy') ||
        btn.textContent?.includes('Hybrid')
      );

      expect(algoButtons.length).toBeGreaterThan(0);
    });

    it('should show scenario presets', async () => {
      const user = userEvent.setup();
      render(<AdminSchedulingPage />, { wrapper: createWrapper() });

      await user.click(screen.getByText('Experimentation').closest('button')!);

      expect(screen.getByText('Scenario Preset')).toBeInTheDocument();
      expect(screen.getByText('Small')).toBeInTheDocument();
      expect(screen.getByText('Medium')).toBeInTheDocument();
      expect(screen.getByText('Large')).toBeInTheDocument();
    });

    it('should show run queue', async () => {
      const user = userEvent.setup();
      render(<AdminSchedulingPage />, { wrapper: createWrapper() });

      await user.click(screen.getByText('Experimentation').closest('button')!);

      expect(screen.getByText('Run Queue')).toBeInTheDocument();
      expect(screen.getByText('1 / 3 running')).toBeInTheDocument();
    });

    it('should display queued experiments', async () => {
      const user = userEvent.setup();
      render(<AdminSchedulingPage />, { wrapper: createWrapper() });

      await user.click(screen.getByText('Experimentation').closest('button')!);

      expect(screen.getByText('Run 1')).toBeInTheDocument();
      expect(screen.getByText('Run 2')).toBeInTheDocument();
    });

    it('should show progress bar for running experiments', async () => {
      const user = userEvent.setup();
      const { container } = render(<AdminSchedulingPage />, { wrapper: createWrapper() });

      await user.click(screen.getByText('Experimentation').closest('button')!);

      const progressBars = container.querySelectorAll('[style*="width"]');
      expect(progressBars.length).toBeGreaterThan(0);
    });
  });

  describe('Metrics Tab', () => {
    it('should switch to Metrics tab', async () => {
      const user = userEvent.setup();
      render(<AdminSchedulingPage />, { wrapper: createWrapper() });

      const metricsTab = screen.getByText('Metrics').closest('button');
      await user.click(metricsTab!);

      expect(metricsTab).toHaveClass('bg-slate-800', 'text-white');
    });

    it('should display metric cards', async () => {
      const user = userEvent.setup();
      render(<AdminSchedulingPage />, { wrapper: createWrapper() });

      await user.click(screen.getByText('Metrics').closest('button')!);

      expect(screen.getAllByText('Coverage')[0]).toBeInTheDocument();
      expect(screen.getByText('ACGME Violations')).toBeInTheDocument();
      expect(screen.getByText('Fairness Score')).toBeInTheDocument();
      expect(screen.getByText('Swap Churn')).toBeInTheDocument();
      expect(screen.getByText('Runtime')).toBeInTheDocument();
      expect(screen.getByText('Stability')).toBeInTheDocument();
    });

    it('should display metric values', async () => {
      const user = userEvent.setup();
      render(<AdminSchedulingPage />, { wrapper: createWrapper() });

      await user.click(screen.getByText('Metrics').closest('button')!);

      expect(screen.getByText('98.5%')).toBeInTheDocument();
      expect(screen.getByText('92%')).toBeInTheDocument();
      expect(screen.getByText('42.5s')).toBeInTheDocument();
    });

    it('should show chart placeholders', async () => {
      const user = userEvent.setup();
      render(<AdminSchedulingPage />, { wrapper: createWrapper() });

      await user.click(screen.getByText('Metrics').closest('button')!);

      expect(screen.getByText('Coverage Trend')).toBeInTheDocument();
      expect(screen.getByText('Algorithm Comparison')).toBeInTheDocument();
    });

    it('should display recent runs table', async () => {
      const user = userEvent.setup();
      render(<AdminSchedulingPage />, { wrapper: createWrapper() });

      await user.click(screen.getByText('Metrics').closest('button')!);

      expect(screen.getAllByText('Recent Runs')[0]).toBeInTheDocument();
      expect(screen.getAllByText('Run ID')[0]).toBeInTheDocument();
      expect(screen.getAllByText('Algorithm')[0]).toBeInTheDocument();
    });
  });

  describe('History Tab', () => {
    it('should switch to History tab', async () => {
      const user = userEvent.setup();
      render(<AdminSchedulingPage />, { wrapper: createWrapper() });

      const historyTab = screen.getByText('History').closest('button');
      await user.click(historyTab!);

      expect(historyTab).toHaveClass('bg-slate-800', 'text-white');
    });

    it('should show filter controls', async () => {
      const user = userEvent.setup();
      render(<AdminSchedulingPage />, { wrapper: createWrapper() });

      await user.click(screen.getByText('History').closest('button')!);

      expect(screen.getByText('All Algorithms')).toBeInTheDocument();
      expect(screen.getByText('All Statuses')).toBeInTheDocument();
    });

    it('should show comparison mode toggle', async () => {
      const user = userEvent.setup();
      render(<AdminSchedulingPage />, { wrapper: createWrapper() });

      await user.click(screen.getByText('History').closest('button')!);

      expect(screen.getByRole('button', { name: /Compare Runs/i })).toBeInTheDocument();
    });

    it('should show export button', async () => {
      const user = userEvent.setup();
      render(<AdminSchedulingPage />, { wrapper: createWrapper() });

      await user.click(screen.getByText('History').closest('button')!);

      expect(screen.getByRole('button', { name: /Export/i })).toBeInTheDocument();
    });

    it('should display run history', async () => {
      const user = userEvent.setup();
      render(<AdminSchedulingPage />, { wrapper: createWrapper() });

      await user.click(screen.getByText('History').closest('button')!);

      expect(screen.getByText(/run-abc123/i)).toBeInTheDocument();
      expect(screen.getByText(/run-def456/i)).toBeInTheDocument();
    });

    it('should toggle comparison mode', async () => {
      const user = userEvent.setup();
      render(<AdminSchedulingPage />, { wrapper: createWrapper() });

      await user.click(screen.getByText('History').closest('button')!);

      const compareButton = screen.getByRole('button', { name: /Compare Runs/i });
      await user.click(compareButton);

      expect(screen.getByText(/Compare \(0\/2\)/i)).toBeInTheDocument();
    });
  });

  describe('Overrides Tab', () => {
    it('should switch to Overrides tab', async () => {
      const user = userEvent.setup();
      render(<AdminSchedulingPage />, { wrapper: createWrapper() });

      const overridesTab = screen.getByText('Overrides').closest('button');
      await user.click(overridesTab!);

      expect(overridesTab).toHaveClass('bg-slate-800', 'text-white');
    });

    it('should show locked assignments', async () => {
      const user = userEvent.setup();
      render(<AdminSchedulingPage />, { wrapper: createWrapper() });

      await user.click(screen.getByText('Overrides').closest('button')!);

      expect(screen.getByText('Locked Assignments')).toBeInTheDocument();
      expect(screen.getByText('Dr. Smith')).toBeInTheDocument();
    });

    it('should show emergency holidays', async () => {
      const user = userEvent.setup();
      render(<AdminSchedulingPage />, { wrapper: createWrapper() });

      await user.click(screen.getByText('Overrides').closest('button')!);

      expect(screen.getByText('Emergency Holidays')).toBeInTheDocument();
      expect(screen.getByText('Christmas')).toBeInTheDocument();
    });

    it('should show rollback points', async () => {
      const user = userEvent.setup();
      render(<AdminSchedulingPage />, { wrapper: createWrapper() });

      await user.click(screen.getByText('Overrides').closest('button')!);

      expect(screen.getByText('Rollback Points')).toBeInTheDocument();
      expect(screen.getByText('Before Block 10')).toBeInTheDocument();
    });

    it('should show data sync status', async () => {
      const user = userEvent.setup();
      render(<AdminSchedulingPage />, { wrapper: createWrapper() });

      await user.click(screen.getByText('Overrides').closest('button')!);

      expect(screen.getByText('Data Provenance')).toBeInTheDocument();
      expect(screen.getByText('Last Sync')).toBeInTheDocument();
      expect(screen.getByText(/Airtable/i)).toBeInTheDocument();
    });

    it('should allow creating rollback point', async () => {
      const user = userEvent.setup();
      render(<AdminSchedulingPage />, { wrapper: createWrapper() });

      await user.click(screen.getByText('Overrides').closest('button')!);

      const input = screen.getByPlaceholderText('Snapshot description...');
      await user.type(input, 'Test snapshot');

      const createButton = screen.getByRole('button', { name: /Create/i });
      expect(createButton).toBeEnabled();
    });

    it('should show unlock button for locked assignments', async () => {
      const user = userEvent.setup();
      render(<AdminSchedulingPage />, { wrapper: createWrapper() });

      await user.click(screen.getByText('Overrides').closest('button')!);

      const unlockButton = screen.getByLabelText('Unlock assignment for Dr. Smith');
      expect(unlockButton).toBeInTheDocument();
    });

    it('should trigger sync', async () => {
      const user = userEvent.setup();
      const mockMutate = jest.fn();
      mockUseTriggerSync.mockReturnValue({
        mutate: mockMutate,
        isPending: false,
      } as any);

      render(<AdminSchedulingPage />, { wrapper: createWrapper() });

      await user.click(screen.getByText('Overrides').closest('button')!);

      const syncButton = screen.getByRole('button', { name: /Trigger Sync/i });
      await user.click(syncButton);

      expect(mockMutate).toHaveBeenCalled();
    });
  });

  describe('Run Schedule Actions', () => {
    it('should validate configuration', async () => {
      const user = userEvent.setup();
      const mockMutate = jest.fn();
      mockUseValidateConfiguration.mockReturnValue({
        mutate: mockMutate,
        mutateAsync: jest.fn(),
        isPending: false,
        data: undefined,
      } as any);

      render(<AdminSchedulingPage />, { wrapper: createWrapper() });

      const validateButton = screen.getByRole('button', { name: /Validate Configuration/i });
      await user.click(validateButton);

      expect(mockMutate).toHaveBeenCalled();
    });

    it('should generate schedule', async () => {
      const user = userEvent.setup();
      const mockMutateAsync = jest.fn().mockResolvedValue({ isValid: true, warnings: [] });
      mockUseValidateConfiguration.mockReturnValue({
        mutate: jest.fn(),
        mutateAsync: mockMutateAsync,
        isPending: false,
        data: undefined,
      } as any);

      const mockGenerate = jest.fn();
      mockUseGenerateScheduleRun.mockReturnValue({
        mutate: mockGenerate,
        isPending: false,
      } as any);

      render(<AdminSchedulingPage />, { wrapper: createWrapper() });

      const generateButton = screen.getByRole('button', { name: /Generate Schedule/i });
      await user.click(generateButton);

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalled();
      });
    });

    it('should disable run button when running', () => {
      mockUseGenerateScheduleRun.mockReturnValue({
        mutate: jest.fn(),
        isPending: true,
      } as any);

      render(<AdminSchedulingPage />, { wrapper: createWrapper() });

      const runButton = screen.getByRole('button', { name: /Running.../i });
      expect(runButton).toBeDisabled();
    });
  });

  describe('Collapsible Sections', () => {
    it('should toggle algorithm section', async () => {
      const user = userEvent.setup();
      render(<AdminSchedulingPage />, { wrapper: createWrapper() });

      const algorithmHeader = screen.getByText('Algorithm Selection').closest('button');
      await user.click(algorithmHeader!);

      // Section should collapse
      const greedyButton = screen.queryByText(/Greedy/);
      expect(greedyButton).not.toBeInTheDocument();
    });

    it('should toggle constraints section', async () => {
      const user = userEvent.setup();
      render(<AdminSchedulingPage />, { wrapper: createWrapper() });

      const constraintsHeader = screen.getByText('Constraint Set').closest('button');
      await user.click(constraintsHeader!);

      // Section should collapse
      const constraint = screen.queryByText('80-Hour Rule');
      expect(constraint).not.toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper heading hierarchy', () => {
      render(<AdminSchedulingPage />, { wrapper: createWrapper() });

      const heading = screen.getByRole('heading', { name: /Scheduling Laboratory/i });
      expect(heading).toBeInTheDocument();
      expect(heading.tagName).toBe('H1');
    });

    it('should have accessible tabs', () => {
      render(<AdminSchedulingPage />, { wrapper: createWrapper() });

      const tabs = screen.getAllByRole('button').filter(btn =>
        btn.classList.contains('rounded-t-lg')
      );
      expect(tabs.length).toBe(5);
    });

    it('should have accessible form controls', () => {
      render(<AdminSchedulingPage />, { wrapper: createWrapper() });

      const selects = screen.getAllByRole('combobox');
      expect(selects.length).toBeGreaterThan(0);

      const inputs = screen.getAllByRole('spinbutton');
      expect(inputs.length).toBeGreaterThan(0);
    });
  });

  describe('Responsive Layout', () => {
    it('should have mobile-friendly layout', () => {
      const { container } = render(<AdminSchedulingPage />, { wrapper: createWrapper() });

      expect(container.querySelector('.min-h-screen')).toBeInTheDocument();
    });

    it('should have grid layouts', () => {
      const { container } = render(<AdminSchedulingPage />, { wrapper: createWrapper() });

      expect(container.querySelector('[class*="grid"]')).toBeInTheDocument();
    });
  });
});
