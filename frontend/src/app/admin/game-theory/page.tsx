'use client';

/**
 * Game Theory Admin Dashboard
 *
 * Axelrod-style Prisoner's Dilemma simulations for
 * empirically testing scheduling and resilience configurations.
 */
import { useState } from 'react';
import {
  useStrategies,
  useTournaments,
  useEvolutions,
  useGameTheorySummary,
  useCreateDefaultStrategies,
  useCreateTournament,
  useCreateEvolution,
  useValidateStrategy,
  useAnalyzeConfig,
} from '@/hooks/useGameTheory';
import { EvolutionChart } from '@/components/game-theory/EvolutionChart';
import { StrategyCard } from '@/components/game-theory/StrategyCard';
import { TournamentCard } from '@/components/game-theory/TournamentCard';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { STRATEGY_LABELS, STATUS_COLORS } from '@/types/game-theory';
import type { ConfigStrategy, TournamentCreate, EvolutionCreate, GameTheorySummary, Tournament, Evolution, ConfigAnalysisRequest, ConfigAnalysisResult } from '@/types/game-theory';

export default function GameTheoryPage() {
  const [activeTab, setActiveTab] = useState<'overview' | 'strategies' | 'tournaments' | 'evolution' | 'analysis'>('overview');
  const [selectedStrategies, setSelectedStrategies] = useState<string[]>([]);
  // const [showTournamentModal, setShowTournamentModal] = useState(false);
  // const [showEvolutionModal, setShowEvolutionModal] = useState(false);

  const { data: summary, isLoading: summaryLoading } = useGameTheorySummary();
  const { data: strategies, isLoading: strategiesLoading } = useStrategies();
  const { data: tournaments, isLoading: tournamentsLoading } = useTournaments();
  const { data: evolutions, isLoading: evolutionsLoading } = useEvolutions();

  const createDefaults = useCreateDefaultStrategies();
  const createTournament = useCreateTournament();
  const createEvolution = useCreateEvolution();
  const validateStrategy = useValidateStrategy();
  const analyzeConfig = useAnalyzeConfig();

  const handleCreateDefaults = (): void => {
    createDefaults.mutate();
  };

  const handleCreateTournament = (): void => {
    if (selectedStrategies.length < 2) {
      alert('Select at least 2 strategies');
      return;
    }

    const tournamentData: TournamentCreate = {
      name: `Tournament ${new Date().toLocaleString()}`,
      strategy_ids: selectedStrategies,
      turns_per_match: 200,
      repetitions: 10,
    };

    createTournament.mutate(tournamentData, {
      onSuccess: (): void => {
        setSelectedStrategies([]);
        // setShowTournamentModal(false);
      },
    });
  };

  const handleCreateEvolution = (): void => {
    if (selectedStrategies.length < 2) {
      alert('Select at least 2 strategies');
      return;
    }

    // Create initial composition with equal distribution
    const composition: Record<string, number> = {};
    const countPerStrategy: number = Math.floor(100 / selectedStrategies.length);
    selectedStrategies.forEach((id: string): void => {
      composition[id] = countPerStrategy;
    });

    const evolutionData: EvolutionCreate = {
      name: `Evolution ${new Date().toLocaleString()}`,
      initial_composition: composition,
      max_generations: 500,
      mutation_rate: 0.01,
    };

    createEvolution.mutate(evolutionData, {
      onSuccess: (): void => {
        setSelectedStrategies([]);
        // setShowEvolutionModal(false);
      },
    });
  };

  const toggleStrategySelection = (id: string): void => {
    setSelectedStrategies((prev: string[]): string[] =>
      prev.includes(id) ? prev.filter((s: string): boolean => s !== id) : [...prev, id]
    );
  };

  if (summaryLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Game Theory Analysis
          </h1>
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-300">
            Axelrod&apos;s Prisoner&apos;s Dilemma simulations for testing configurations
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleCreateDefaults}
            disabled={createDefaults.isPending}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {createDefaults.isPending ? 'Creating...' : 'Create Default Strategies'}
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        <nav className="flex space-x-8">
          {(['overview', 'strategies', 'tournaments', 'evolution', 'analysis'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`py-4 px-1 border-b-2 font-medium text-sm capitalize ${
                activeTab === tab
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-600 hover:text-gray-700 dark:text-gray-300 dark:hover:text-gray-200'
              }`}
            >
              {tab}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <OverviewTab summary={summary} />
      )}

      {activeTab === 'strategies' && (
        <StrategiesTab
          strategies={strategies?.strategies || []}
          isLoading={strategiesLoading}
          selectedStrategies={selectedStrategies}
          onToggleSelection={toggleStrategySelection}
          onValidate={(id) => validateStrategy.mutate({ strategy_id: id })}
        />
      )}

      {activeTab === 'tournaments' && (
        <TournamentsTab
          tournaments={tournaments?.tournaments || []}
          isLoading={tournamentsLoading}
          strategies={strategies?.strategies || []}
          selectedStrategies={selectedStrategies}
          onToggleSelection={toggleStrategySelection}
          onCreateTournament={handleCreateTournament}
          isCreating={createTournament.isPending}
        />
      )}

      {activeTab === 'evolution' && (
        <EvolutionTab
          evolutions={evolutions?.simulations || []}
          isLoading={evolutionsLoading}
          strategies={strategies?.strategies || []}
          selectedStrategies={selectedStrategies}
          onToggleSelection={toggleStrategySelection}
          onCreateEvolution={handleCreateEvolution}
          isCreating={createEvolution.isPending}
        />
      )}

      {activeTab === 'analysis' && (
        <AnalysisTab
          onAnalyze={(config) => analyzeConfig.mutate(config)}
          isAnalyzing={analyzeConfig.isPending}
          result={analyzeConfig.data}
        />
      )}
    </div>
  );
}

// ============================================================================
// Tab Components
// ============================================================================

function OverviewTab({ summary }: { summary: GameTheorySummary | undefined }) {
  if (!summary) return null;

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Strategies"
          value={summary.totalStrategies}
          subtitle="Configuration strategies"
        />
        <StatCard
          title="Tournaments"
          value={summary.completedTournaments}
          subtitle={`of ${summary.totalTournaments} total`}
        />
        <StatCard
          title="Evolutions"
          value={summary.completedEvolutions}
          subtitle={`of ${summary.totalEvolutions} total`}
        />
        <StatCard
          title="Best Strategy"
          value={summary.bestPerformingStrategy || 'N/A'}
          subtitle={summary.bestStrategyScore ? `Score: ${summary.bestStrategyScore.toFixed(2)}` : ''}
        />
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
            Recent Tournaments
          </h3>
          {summary.recentTournaments?.length > 0 ? (
            <ul className="space-y-3">
              {summary.recentTournaments.map((t) => (
                <li key={t.id} className="flex items-center justify-between">
                  <span className="text-sm text-gray-700 dark:text-gray-300">{t.name}</span>
                  <span
                    className="px-2 py-1 text-xs rounded-full"
                    style={{ backgroundColor: STATUS_COLORS[t.status] + '20', color: STATUS_COLORS[t.status] }}
                  >
                    {t.status}
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-gray-600 dark:text-gray-300">No tournaments yet</p>
          )}
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
            Recent Evolutions
          </h3>
          {summary.recentEvolutions?.length > 0 ? (
            <ul className="space-y-3">
              {summary.recentEvolutions.map((e) => (
                <li key={e.id} className="flex items-center justify-between">
                  <span className="text-sm text-gray-700 dark:text-gray-300">{e.name}</span>
                  <span
                    className="px-2 py-1 text-xs rounded-full"
                    style={{ backgroundColor: STATUS_COLORS[e.status] + '20', color: STATUS_COLORS[e.status] }}
                  >
                    {e.winner || e.status}
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-gray-600 dark:text-gray-300">No evolutions yet</p>
          )}
        </div>
      </div>

      {/* Explanation */}
      <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-6">
        <h3 className="text-lg font-medium text-blue-900 dark:text-blue-100 mb-2">
          About Game Theory Testing
        </h3>
        <p className="text-sm text-blue-800 dark:text-blue-200">
          This system uses Robert Axelrod&apos;s Prisoner&apos;s Dilemma framework to empirically test
          scheduling and resilience configurations. Configurations are mapped to game theory strategies
          (Cooperation = share resources, Defection = hoard resources). The <strong>Tit for Tat</strong> strategy
          consistently wins because it is Nice, Retaliatory, Forgiving, and Clear.
        </p>
      </div>
    </div>
  );
}

function StrategiesTab({
  strategies,
  isLoading,
  selectedStrategies,
  onToggleSelection,
  onValidate,
}: {
  strategies: ConfigStrategy[];
  isLoading: boolean;
  selectedStrategies: string[];
  onToggleSelection: (id: string) => void;
  onValidate: (id: string) => void;
}) {
  if (isLoading) return <LoadingSpinner />;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-600 dark:text-gray-300">
          {strategies.length} strategies | {selectedStrategies.length} selected
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {strategies.map((strategy) => (
          <StrategyCard
            key={strategy.id}
            strategy={strategy}
            isSelected={selectedStrategies.includes(strategy.id)}
            onToggle={() => onToggleSelection(strategy.id)}
            onValidate={() => onValidate(strategy.id)}
          />
        ))}
      </div>

      {strategies.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-600 dark:text-gray-300">No strategies yet. Click &quot;Create Default Strategies&quot; to get started.</p>
        </div>
      )}
    </div>
  );
}

function TournamentsTab({
  tournaments,
  isLoading,
  strategies,
  selectedStrategies,
  onToggleSelection,
  onCreateTournament,
  isCreating,
}: {
  tournaments: Tournament[];
  isLoading: boolean;
  strategies: ConfigStrategy[];
  selectedStrategies: string[];
  onToggleSelection: (id: string) => void;
  onCreateTournament: () => void;
  isCreating: boolean;
}) {
  if (isLoading) return <LoadingSpinner />;

  return (
    <div className="space-y-6">
      {/* Create Tournament */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
          Create New Tournament
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-300 mb-4">
          Select strategies below, then click &quot;Run Tournament&quot; to start a round-robin competition.
        </p>
        <div className="flex flex-wrap gap-2 mb-4">
          {strategies.map((s) => (
            <button
              key={s.id}
              onClick={() => onToggleSelection(s.id)}
              className={`px-3 py-1 text-sm rounded-full border transition-colors ${
                selectedStrategies.includes(s.id)
                  ? 'bg-blue-100 border-blue-500 text-blue-700 dark:bg-blue-900 dark:text-blue-200'
                  : 'bg-gray-100 border-gray-300 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
              }`}
            >
              {s.name}
            </button>
          ))}
        </div>
        <button
          onClick={onCreateTournament}
          disabled={selectedStrategies.length < 2 || isCreating}
          className="px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-lg hover:bg-green-700 disabled:opacity-50"
        >
          {isCreating ? 'Creating...' : `Run Tournament (${selectedStrategies.length} strategies)`}
        </button>
      </div>

      {/* Tournament List */}
      <div className="space-y-4">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white">
          Tournament History
        </h3>
        {tournaments.map((tournament) => (
          <TournamentCard key={tournament.id} tournament={tournament} />
        ))}
        {tournaments.length === 0 && (
          <p className="text-gray-600 dark:text-gray-300 text-center py-8">No tournaments yet</p>
        )}
      </div>
    </div>
  );
}

function EvolutionTab({
  evolutions,
  isLoading,
  strategies,
  selectedStrategies,
  onToggleSelection,
  onCreateEvolution,
  isCreating,
}: {
  evolutions: Evolution[];
  isLoading: boolean;
  strategies: ConfigStrategy[];
  selectedStrategies: string[];
  onToggleSelection: (id: string) => void;
  onCreateEvolution: () => void;
  isCreating: boolean;
}) {
  if (isLoading) return <LoadingSpinner />;

  return (
    <div className="space-y-6">
      {/* Create Evolution */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
          Create Evolutionary Simulation
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-300 mb-4">
          Select strategies to compete in a Moran process. Weak strategies go extinct, strong ones dominate.
        </p>
        <div className="flex flex-wrap gap-2 mb-4">
          {strategies.map((s) => (
            <button
              key={s.id}
              onClick={() => onToggleSelection(s.id)}
              className={`px-3 py-1 text-sm rounded-full border transition-colors ${
                selectedStrategies.includes(s.id)
                  ? 'bg-purple-100 border-purple-500 text-purple-700 dark:bg-purple-900 dark:text-purple-200'
                  : 'bg-gray-100 border-gray-300 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
              }`}
            >
              {s.name}
            </button>
          ))}
        </div>
        <button
          onClick={onCreateEvolution}
          disabled={selectedStrategies.length < 2 || isCreating}
          className="px-4 py-2 text-sm font-medium text-white bg-purple-600 rounded-lg hover:bg-purple-700 disabled:opacity-50"
        >
          {isCreating ? 'Creating...' : `Start Evolution (${selectedStrategies.length} strategies)`}
        </button>
      </div>

      {/* Evolution List */}
      <div className="space-y-4">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white">
          Evolution History
        </h3>
        {evolutions.map((evolution) => (
          <div
            key={evolution.id}
            className="bg-white dark:bg-gray-800 rounded-lg shadow p-4"
          >
            <div className="flex items-center justify-between">
              <div>
                <h4 className="font-medium text-gray-900 dark:text-white">{evolution.name}</h4>
                <p className="text-sm text-gray-600 dark:text-gray-300">
                  {evolution.generationsCompleted} generations | Winner: {evolution.winnerStrategyName || 'TBD'}
                </p>
              </div>
              <span
                className="px-2 py-1 text-xs rounded-full"
                style={{ backgroundColor: STATUS_COLORS[evolution.status as keyof typeof STATUS_COLORS] + '20', color: STATUS_COLORS[evolution.status as keyof typeof STATUS_COLORS] }}
              >
                {evolution.status}
              </span>
            </div>
            {evolution.status === 'completed' && (
              <div className="mt-4">
                <EvolutionChart evolutionId={evolution.id} />
              </div>
            )}
          </div>
        ))}
        {evolutions.length === 0 && (
          <p className="text-gray-600 dark:text-gray-300 text-center py-8">No evolutions yet</p>
        )}
      </div>
    </div>
  );
}

function AnalysisTab({
  onAnalyze,
  isAnalyzing,
  result,
}: {
  onAnalyze: (config: ConfigAnalysisRequest) => void;
  isAnalyzing: boolean;
  result?: ConfigAnalysisResult;
}) {
  const [config, setConfig] = useState<{
    utilization_target: number;
    cross_zone_borrowing: boolean;
    sacrifice_willingness: 'low' | 'medium' | 'high';
    defense_activation_threshold: number;
  }>({
    utilization_target: 0.8,
    cross_zone_borrowing: true,
    sacrifice_willingness: 'medium',
    defense_activation_threshold: 3,
  });

  return (
    <div className="space-y-6">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
          Analyze Configuration
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-300 mb-4">
          Test how your current resilience configuration would perform in game-theoretic terms.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Utilization Target
            </label>
            <input
              type="range"
              min="0.5"
              max="1"
              step="0.05"
              value={config.utilizationTarget}
              onChange={(e) => setConfig({ ...config, utilization_target: parseFloat(e.target.value) })}
              className="w-full"
            />
            <span className="text-sm text-gray-500">{(config.utilizationTarget * 100).toFixed(0)}%</span>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Defense Activation Threshold
            </label>
            <select
              value={config.defenseActivationThreshold}
              onChange={(e) => setConfig({ ...config, defense_activation_threshold: parseInt(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
            >
              {[1, 2, 3, 4, 5].map((level) => (
                <option key={level} value={level}>Level {level}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Sacrifice Willingness
            </label>
            <select
              value={config.sacrificeWillingness}
              onChange={(e) => setConfig({ ...config, sacrifice_willingness: e.target.value as 'low' | 'medium' | 'high' })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              checked={config.crossZoneBorrowing}
              onChange={(e) => setConfig({ ...config, cross_zone_borrowing: e.target.checked })}
              className="mr-2"
            />
            <label className="text-sm text-gray-700 dark:text-gray-300">
              Cross-zone borrowing enabled
            </label>
          </div>
        </div>

        <button
          onClick={() => onAnalyze(config)}
          disabled={isAnalyzing}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {isAnalyzing ? 'Analyzing...' : 'Analyze Configuration'}
        </button>
      </div>

      {/* Results */}
      {result && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
            Analysis Results: {result.configName}
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <p className="text-sm text-gray-600 dark:text-gray-300">Average Score</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {result.averageScore.toFixed(2)}
              </p>
            </div>
            <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <p className="text-sm text-gray-600 dark:text-gray-300">Cooperation Rate</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {(result.cooperationRate * 100).toFixed(0)}%
              </p>
            </div>
            <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <p className="text-sm text-gray-600 dark:text-gray-300">Classification</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white capitalize">
                {STRATEGY_LABELS[result.strategyClassification as keyof typeof STRATEGY_LABELS] || result.strategyClassification}
              </p>
            </div>
          </div>

          <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
            <p className="text-sm text-blue-800 dark:text-blue-200">
              <strong>Recommendation:</strong> {result.recommendation}
            </p>
          </div>

          {/* Matchup Results */}
          <div className="mt-6">
            <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              Performance vs Standard Opponents
            </h4>
            <div className="space-y-2">
              {Object.entries(result.matchupResults).map(([opponent, data]: [string, { score: number; outcome: string }]) => (
                <div
                  key={opponent}
                  className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded"
                >
                  <span className="font-medium text-gray-900 dark:text-white">{opponent}</span>
                  <div className="flex items-center gap-4">
                    <span className="text-sm text-gray-500">
                      Score: {data.score.toFixed(1)}
                    </span>
                    <span
                      className={`px-2 py-1 text-xs rounded ${
                        data.outcome === 'win'
                          ? 'bg-green-100 text-green-800'
                          : data.outcome === 'loss'
                          ? 'bg-red-100 text-red-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {data.outcome}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Utility Components
// ============================================================================

function StatCard({ title, value, subtitle }: { title: string; value: string | number; subtitle?: string }): React.ReactElement {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <p className="text-sm font-medium text-gray-600 dark:text-gray-300">{title}</p>
      <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">{value}</p>
      {subtitle && <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">{subtitle}</p>}
    </div>
  );
}
