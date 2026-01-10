/**
 * Tests for Admin Game Theory Page
 *
 * Tests Axelrod-style Prisoner's Dilemma simulations for
 * scheduling configuration testing, tournaments, evolution, and analysis.
 */
import React from 'react';
import { render, screen, waitFor } from '@/test-utils';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import GameTheoryPage from '@/app/admin/game-theory/page';
import * as hooks from '@/hooks/useGameTheory';

// Mock the hooks
jest.mock('@/hooks/useGameTheory');
const mockUseGameTheorySummary = hooks.useGameTheorySummary as jest.MockedFunction<typeof hooks.useGameTheorySummary>;
const mockUseStrategies = hooks.useStrategies as jest.MockedFunction<typeof hooks.useStrategies>;
const mockUseTournaments = hooks.useTournaments as jest.MockedFunction<typeof hooks.useTournaments>;
const mockUseEvolutions = hooks.useEvolutions as jest.MockedFunction<typeof hooks.useEvolutions>;
const mockUseCreateDefaultStrategies = hooks.useCreateDefaultStrategies as jest.MockedFunction<typeof hooks.useCreateDefaultStrategies>;
const mockUseCreateTournament = hooks.useCreateTournament as jest.MockedFunction<typeof hooks.useCreateTournament>;
const mockUseCreateEvolution = hooks.useCreateEvolution as jest.MockedFunction<typeof hooks.useCreateEvolution>;
const mockUseValidateStrategy = hooks.useValidateStrategy as jest.MockedFunction<typeof hooks.useValidateStrategy>;
const mockUseAnalyzeConfig = hooks.useAnalyzeConfig as jest.MockedFunction<typeof hooks.useAnalyzeConfig>;

// Mock component dependencies
jest.mock('@/components/LoadingSpinner', () => ({
  LoadingSpinner: () => <div>Loading...</div>,
}));

jest.mock('@/components/game-theory/PayoffMatrix', () => ({
  PayoffMatrix: () => <div>Payoff Matrix</div>,
}));

jest.mock('@/components/game-theory/EvolutionChart', () => ({
  EvolutionChart: () => <div>Evolution Chart</div>,
}));

jest.mock('@/components/game-theory/StrategyCard', () => ({
  StrategyCard: ({ strategy, isSelected, onToggle }: any) => (
    <div data-testid={`strategy-${strategy.id}`}>
      <span>{strategy.name}</span>
      <input
        type="checkbox"
        checked={isSelected}
        onChange={onToggle}
        aria-label={`Select ${strategy.name}`}
      />
    </div>
  ),
}));

jest.mock('@/components/game-theory/TournamentCard', () => ({
  TournamentCard: ({ tournament }: any) => (
    <div data-testid={`tournament-${tournament.id}`}>
      <span>{tournament.name}</span>
      <span>{tournament.status}</span>
    </div>
  ),
}));

// Mock data
const mockSummary = {
  total_strategies: 5,
  total_tournaments: 10,
  completed_tournaments: 8,
  total_evolutions: 6,
  completed_evolutions: 4,
  best_performing_strategy: 'Tit for Tat',
  best_strategy_score: 3.2,
  recent_tournaments: [
    { id: '1', name: 'Tournament 1', status: 'completed' },
    { id: '2', name: 'Tournament 2', status: 'running' },
  ],
  recent_evolutions: [
    { id: '1', name: 'Evolution 1', status: 'completed', winner: 'Tit for Tat' },
  ],
};

const mockStrategies = {
  strategies: [
    { id: 'tft', name: 'Tit for Tat', description: 'Cooperative strategy', enabled: true },
    { id: 'ad', name: 'Always Defect', description: 'Aggressive strategy', enabled: true },
    { id: 'ac', name: 'Always Cooperate', description: 'Peaceful strategy', enabled: true },
  ],
};

const mockTournaments = {
  tournaments: [
    { id: '1', name: 'Tournament 1', status: 'completed' },
  ],
};

const mockEvolutions = {
  simulations: [
    { id: '1', name: 'Evolution 1', status: 'completed', generations_completed: 500, winnerStrategyName: 'Tit for Tat' },
  ],
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

describe('GameTheoryPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();

    // Default mock implementations
    mockUseGameTheorySummary.mockReturnValue({
      data: mockSummary,
      isLoading: false,
    } as any);

    mockUseStrategies.mockReturnValue({
      data: mockStrategies,
      isLoading: false,
    } as any);

    mockUseTournaments.mockReturnValue({
      data: mockTournaments,
      isLoading: false,
    } as any);

    mockUseEvolutions.mockReturnValue({
      data: mockEvolutions,
      isLoading: false,
    } as any);

    mockUseCreateDefaultStrategies.mockReturnValue({
      mutate: jest.fn(),
      isPending: false,
    } as any);

    mockUseCreateTournament.mockReturnValue({
      mutate: jest.fn(),
      isPending: false,
    } as any);

    mockUseCreateEvolution.mockReturnValue({
      mutate: jest.fn(),
      isPending: false,
    } as any);

    mockUseValidateStrategy.mockReturnValue({
      mutate: jest.fn(),
      isPending: false,
    } as any);

    mockUseAnalyzeConfig.mockReturnValue({
      mutate: jest.fn(),
      isPending: false,
      data: undefined,
    } as any);
  });

  describe('Page Rendering', () => {
    it('should render page title', () => {
      render(<GameTheoryPage />, { wrapper: createWrapper() });

      expect(screen.getByText('Game Theory Analysis')).toBeInTheDocument();
    });

    it('should render page description', () => {
      render(<GameTheoryPage />, { wrapper: createWrapper() });

      expect(screen.getByText(/Axelrod's Prisoner's Dilemma/i)).toBeInTheDocument();
    });

    it('should render Create Default Strategies button', () => {
      render(<GameTheoryPage />, { wrapper: createWrapper() });

      expect(screen.getByRole('button', { name: /Create Default Strategies/i })).toBeInTheDocument();
    });

    it('should render all tabs', () => {
      render(<GameTheoryPage />, { wrapper: createWrapper() });

      expect(screen.getByText('overview')).toBeInTheDocument();
      expect(screen.getByText('strategies')).toBeInTheDocument();
      expect(screen.getByText('tournaments')).toBeInTheDocument();
      expect(screen.getByText('evolution')).toBeInTheDocument();
      expect(screen.getByText('analysis')).toBeInTheDocument();
    });

    it('should start on overview tab', () => {
      render(<GameTheoryPage />, { wrapper: createWrapper() });

      const overviewTab = screen.getByText('overview').closest('button');
      expect(overviewTab).toHaveClass('border-blue-500');
    });

    it('should show loading state', () => {
      mockUseGameTheorySummary.mockReturnValue({
        data: undefined,
        isLoading: true,
      } as any);

      render(<GameTheoryPage />, { wrapper: createWrapper() });

      expect(screen.getByText('Loading...')).toBeInTheDocument();
    });
  });

  describe('Overview Tab', () => {
    it('should display statistics cards', () => {
      render(<GameTheoryPage />, { wrapper: createWrapper() });

      expect(screen.getByText('Strategies')).toBeInTheDocument();
      expect(screen.getByText('5')).toBeInTheDocument();

      expect(screen.getByText('Tournaments')).toBeInTheDocument();
      expect(screen.getByText('8')).toBeInTheDocument();

      expect(screen.getByText('Evolutions')).toBeInTheDocument();
      expect(screen.getByText('4')).toBeInTheDocument();
    });

    it('should display best performing strategy', () => {
      render(<GameTheoryPage />, { wrapper: createWrapper() });

      expect(screen.getByText('Best Strategy')).toBeInTheDocument();
      expect(screen.getByText('Tit for Tat')).toBeInTheDocument();
      expect(screen.getByText(/Score: 3\.2/i)).toBeInTheDocument();
    });

    it('should show recent tournaments', () => {
      render(<GameTheoryPage />, { wrapper: createWrapper() });

      expect(screen.getByText('Recent Tournaments')).toBeInTheDocument();
      expect(screen.getByText('Tournament 1')).toBeInTheDocument();
      expect(screen.getByText('Tournament 2')).toBeInTheDocument();
    });

    it('should show recent evolutions', () => {
      render(<GameTheoryPage />, { wrapper: createWrapper() });

      expect(screen.getByText('Recent Evolutions')).toBeInTheDocument();
      expect(screen.getByText('Evolution 1')).toBeInTheDocument();
    });

    it('should display explanation section', () => {
      render(<GameTheoryPage />, { wrapper: createWrapper() });

      expect(screen.getByText('About Game Theory Testing')).toBeInTheDocument();
      expect(screen.getByText(/Robert Axelrod/i)).toBeInTheDocument();
    });
  });

  describe('Strategies Tab', () => {
    it('should switch to strategies tab', async () => {
      const user = userEvent.setup();
      render(<GameTheoryPage />, { wrapper: createWrapper() });

      const strategiesTab = screen.getByText('strategies').closest('button');
      await user.click(strategiesTab!);

      expect(strategiesTab).toHaveClass('border-blue-500');
    });

    it('should display all strategies', async () => {
      const user = userEvent.setup();
      render(<GameTheoryPage />, { wrapper: createWrapper() });

      await user.click(screen.getByText('strategies').closest('button')!);

      expect(screen.getByText('Tit for Tat')).toBeInTheDocument();
      expect(screen.getByText('Always Defect')).toBeInTheDocument();
      expect(screen.getByText('Always Cooperate')).toBeInTheDocument();
    });

    it('should show strategy count', async () => {
      const user = userEvent.setup();
      render(<GameTheoryPage />, { wrapper: createWrapper() });

      await user.click(screen.getByText('strategies').closest('button')!);

      expect(screen.getByText(/3 strategies/i)).toBeInTheDocument();
    });

    it('should show selected count', async () => {
      const user = userEvent.setup();
      render(<GameTheoryPage />, { wrapper: createWrapper() });

      await user.click(screen.getByText('strategies').closest('button')!);

      // Initially no strategies selected
      expect(screen.getByText(/0 selected/i)).toBeInTheDocument();
    });

    it('should allow strategy selection', async () => {
      const user = userEvent.setup();
      render(<GameTheoryPage />, { wrapper: createWrapper() });

      await user.click(screen.getByText('strategies').closest('button')!);

      const checkbox = screen.getByLabelText('Select Tit for Tat');
      await user.click(checkbox);

      expect(checkbox).toBeChecked();
    });

    it('should show empty state when no strategies', async () => {
      const user = userEvent.setup();
      mockUseStrategies.mockReturnValue({
        data: { strategies: [] },
        isLoading: false,
      } as any);

      render(<GameTheoryPage />, { wrapper: createWrapper() });

      await user.click(screen.getByText('strategies').closest('button')!);

      expect(screen.getByText(/No strategies yet/i)).toBeInTheDocument();
    });
  });

  describe('Tournaments Tab', () => {
    it('should switch to tournaments tab', async () => {
      const user = userEvent.setup();
      render(<GameTheoryPage />, { wrapper: createWrapper() });

      const tournamentsTab = screen.getByText('tournaments').closest('button');
      await user.click(tournamentsTab!);

      expect(tournamentsTab).toHaveClass('border-blue-500');
    });

    it('should show tournament creation section', async () => {
      const user = userEvent.setup();
      render(<GameTheoryPage />, { wrapper: createWrapper() });

      await user.click(screen.getByText('tournaments').closest('button')!);

      expect(screen.getByText('Create New Tournament')).toBeInTheDocument();
      expect(screen.getByText(/Select strategies below/i)).toBeInTheDocument();
    });

    it('should allow strategy selection for tournament', async () => {
      const user = userEvent.setup();
      render(<GameTheoryPage />, { wrapper: createWrapper() });

      await user.click(screen.getByText('tournaments').closest('button')!);

      const strategyButtons = screen.getAllByRole('button').filter(btn =>
        btn.textContent?.includes('Tit for Tat') ||
        btn.textContent?.includes('Always')
      );

      expect(strategyButtons.length).toBeGreaterThan(0);
    });

    it('should show run tournament button', async () => {
      const user = userEvent.setup();
      render(<GameTheoryPage />, { wrapper: createWrapper() });

      await user.click(screen.getByText('tournaments').closest('button')!);

      expect(screen.getByRole('button', { name: /Run Tournament/i })).toBeInTheDocument();
    });

    it('should disable run button with fewer than 2 strategies', async () => {
      const user = userEvent.setup();
      render(<GameTheoryPage />, { wrapper: createWrapper() });

      await user.click(screen.getByText('tournaments').closest('button')!);

      const runButton = screen.getByRole('button', { name: /Run Tournament/i });
      expect(runButton).toBeDisabled();
    });

    it('should show tournament history', async () => {
      const user = userEvent.setup();
      render(<GameTheoryPage />, { wrapper: createWrapper() });

      await user.click(screen.getByText('tournaments').closest('button')!);

      expect(screen.getByText('Tournament History')).toBeInTheDocument();
    });

    it('should show empty state when no tournaments', async () => {
      const user = userEvent.setup();
      mockUseTournaments.mockReturnValue({
        data: { tournaments: [] },
        isLoading: false,
      } as any);

      render(<GameTheoryPage />, { wrapper: createWrapper() });

      await user.click(screen.getByText('tournaments').closest('button')!);

      expect(screen.getByText('No tournaments yet')).toBeInTheDocument();
    });
  });

  describe('Evolution Tab', () => {
    it('should switch to evolution tab', async () => {
      const user = userEvent.setup();
      render(<GameTheoryPage />, { wrapper: createWrapper() });

      const evolutionTab = screen.getByText('evolution').closest('button');
      await user.click(evolutionTab!);

      expect(evolutionTab).toHaveClass('border-blue-500');
    });

    it('should show evolution creation section', async () => {
      const user = userEvent.setup();
      render(<GameTheoryPage />, { wrapper: createWrapper() });

      await user.click(screen.getByText('evolution').closest('button')!);

      expect(screen.getByText('Create Evolutionary Simulation')).toBeInTheDocument();
      expect(screen.getByText(/Moran process/i)).toBeInTheDocument();
    });

    it('should show start evolution button', async () => {
      const user = userEvent.setup();
      render(<GameTheoryPage />, { wrapper: createWrapper() });

      await user.click(screen.getByText('evolution').closest('button')!);

      expect(screen.getByRole('button', { name: /Start Evolution/i })).toBeInTheDocument();
    });

    it('should display evolution history', async () => {
      const user = userEvent.setup();
      render(<GameTheoryPage />, { wrapper: createWrapper() });

      await user.click(screen.getByText('evolution').closest('button')!);

      expect(screen.getByText('Evolution History')).toBeInTheDocument();
      expect(screen.getAllByText('Evolution 1')[0]).toBeInTheDocument();
    });

    it('should show evolution chart for completed simulations', async () => {
      const user = userEvent.setup();
      render(<GameTheoryPage />, { wrapper: createWrapper() });

      await user.click(screen.getByText('evolution').closest('button')!);

      expect(screen.getByText('Evolution Chart')).toBeInTheDocument();
    });
  });

  describe('Analysis Tab', () => {
    it('should switch to analysis tab', async () => {
      const user = userEvent.setup();
      render(<GameTheoryPage />, { wrapper: createWrapper() });

      const analysisTab = screen.getByText('analysis').closest('button');
      await user.click(analysisTab!);

      expect(analysisTab).toHaveClass('border-blue-500');
    });

    it('should show configuration analysis form', async () => {
      const user = userEvent.setup();
      render(<GameTheoryPage />, { wrapper: createWrapper() });

      await user.click(screen.getByText('analysis').closest('button')!);

      expect(screen.getByText('Analyze Configuration')).toBeInTheDocument();
      expect(screen.getByText('Utilization Target')).toBeInTheDocument();
      expect(screen.getByText('Defense Activation Threshold')).toBeInTheDocument();
      expect(screen.getByText('Sacrifice Willingness')).toBeInTheDocument();
    });

    it('should have configuration controls', async () => {
      const user = userEvent.setup();
      render(<GameTheoryPage />, { wrapper: createWrapper() });

      await user.click(screen.getByText('analysis').closest('button')!);

      expect(screen.getByRole('slider')).toBeInTheDocument();
      expect(screen.getAllByRole('combobox').length).toBeGreaterThan(0);
      expect(screen.getByRole('checkbox')).toBeInTheDocument();
    });

    it('should show analyze configuration button', async () => {
      const user = userEvent.setup();
      render(<GameTheoryPage />, { wrapper: createWrapper() });

      await user.click(screen.getByText('analysis').closest('button')!);

      expect(screen.getByRole('button', { name: /Analyze Configuration/i })).toBeInTheDocument();
    });

    it('should display analysis results when available', async () => {
      const user = userEvent.setup();
      const mockResults = {
        config_name: 'Test Config',
        averageScore: 3.5,
        cooperationRate: 0.75,
        strategy_classification: 'tft',
        recommendation: 'Good configuration',
        matchup_results: {
          'Always Defect': { score: 2.5, outcome: 'win' },
        },
      };

      mockUseAnalyzeConfig.mockReturnValue({
        mutate: jest.fn(),
        isPending: false,
        data: mockResults,
      } as any);

      render(<GameTheoryPage />, { wrapper: createWrapper() });

      await user.click(screen.getByText('analysis').closest('button')!);

      expect(screen.getByText('Analysis Results: Test Config')).toBeInTheDocument();
      expect(screen.getByText('3.50')).toBeInTheDocument();
      expect(screen.getByText('75%')).toBeInTheDocument();
    });

    it('should show matchup results', async () => {
      const user = userEvent.setup();
      const mockResults = {
        config_name: 'Test Config',
        averageScore: 3.5,
        cooperationRate: 0.75,
        strategy_classification: 'tft',
        recommendation: 'Good configuration',
        matchup_results: {
          'Always Defect': { score: 2.5, outcome: 'win' },
        },
      };

      mockUseAnalyzeConfig.mockReturnValue({
        mutate: jest.fn(),
        isPending: false,
        data: mockResults,
      } as any);

      render(<GameTheoryPage />, { wrapper: createWrapper() });

      await user.click(screen.getByText('analysis').closest('button')!);

      expect(screen.getByText('Performance vs Standard Opponents')).toBeInTheDocument();
      expect(screen.getByText('Always Defect')).toBeInTheDocument();
    });
  });

  describe('Create Default Strategies', () => {
    it('should call create mutation when button clicked', async () => {
      const user = userEvent.setup();
      const mockMutate = jest.fn();
      mockUseCreateDefaultStrategies.mockReturnValue({
        mutate: mockMutate,
        isPending: false,
      } as any);

      render(<GameTheoryPage />, { wrapper: createWrapper() });

      const createButton = screen.getByRole('button', { name: /Create Default Strategies/i });
      await user.click(createButton);

      expect(mockMutate).toHaveBeenCalled();
    });

    it('should show loading state when creating', () => {
      mockUseCreateDefaultStrategies.mockReturnValue({
        mutate: jest.fn(),
        isPending: true,
      } as any);

      render(<GameTheoryPage />, { wrapper: createWrapper() });

      expect(screen.getByText('Creating...')).toBeInTheDocument();
    });

    it('should disable button when pending', () => {
      mockUseCreateDefaultStrategies.mockReturnValue({
        mutate: jest.fn(),
        isPending: true,
      } as any);

      render(<GameTheoryPage />, { wrapper: createWrapper() });

      const createButton = screen.getByRole('button', { name: /Creating.../i });
      expect(createButton).toBeDisabled();
    });
  });

  describe('Accessibility', () => {
    it('should have proper heading hierarchy', () => {
      render(<GameTheoryPage />, { wrapper: createWrapper() });

      const heading = screen.getByRole('heading', { name: /Game Theory Analysis/i });
      expect(heading).toBeInTheDocument();
      expect(heading.tagName).toBe('H1');
    });

    it('should have accessible tabs', () => {
      render(<GameTheoryPage />, { wrapper: createWrapper() });

      const tabs = screen.getAllByRole('button').filter(btn =>
        btn.classList.contains('border-b-2')
      );
      expect(tabs.length).toBe(5);
    });

    it('should have accessible strategy checkboxes', async () => {
      const user = userEvent.setup();
      render(<GameTheoryPage />, { wrapper: createWrapper() });

      await user.click(screen.getByText('strategies').closest('button')!);

      const checkboxes = screen.getAllByRole('checkbox');
      expect(checkboxes.length).toBeGreaterThan(0);
    });
  });

  describe('Responsive Layout', () => {
    it('should have mobile-friendly layout', () => {
      const { container } = render(<GameTheoryPage />, { wrapper: createWrapper() });

      expect(container.querySelector('[class*="space-y"]')).toBeInTheDocument();
    });

    it('should have grid layouts', () => {
      const { container } = render(<GameTheoryPage />, { wrapper: createWrapper() });

      expect(container.querySelector('[class*="grid"]')).toBeInTheDocument();
    });
  });
});
