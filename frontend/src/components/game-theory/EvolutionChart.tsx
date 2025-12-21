'use client';

/**
 * EvolutionChart Component
 *
 * Visualizes population dynamics over generations in a Moran process.
 * Shows how strategies rise and fall over evolutionary time.
 */
import { useEvolutionResults } from '@/hooks/useGameTheory';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { STRATEGY_COLORS } from '@/types/game-theory';

interface EvolutionChartProps {
  evolutionId: string;
}

export function EvolutionChart({ evolutionId }: EvolutionChartProps) {
  const { data: results, isLoading, error } = useEvolutionResults(evolutionId);

  if (isLoading) return <LoadingSpinner />;
  if (error) return <p className="text-red-500 text-sm">Failed to load results</p>;
  if (!results?.population_history?.length) return <p className="text-gray-500 text-sm">No data</p>;

  // Get all strategy names from the history
  const allStrategies = new Set<string>();
  results.population_history.forEach((snapshot) => {
    Object.keys(snapshot.populations).forEach((s) => allStrategies.add(s));
  });
  const strategies = Array.from(allStrategies);

  // Get total population for percentage calculation
  const getTotalPop = (populations: Record<string, number>) =>
    Object.values(populations).reduce((sum, v) => sum + v, 0);

  // Chart dimensions
  const width = 600;
  const height = 200;
  const padding = { top: 10, right: 10, bottom: 30, left: 40 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;

  // X scale
  const maxGen = Math.max(...results.population_history.map((s) => s.generation));
  const xScale = (gen: number) => padding.left + (gen / maxGen) * chartWidth;

  // Y scale (0 to 100%)
  const yScale = (pct: number) => padding.top + (1 - pct) * chartHeight;

  // Generate stacked area paths
  const generatePaths = () => {
    const paths: { strategy: string; d: string; color: string }[] = [];

    strategies.forEach((strategy, strategyIndex) => {
      const points: string[] = [];

      // Forward pass (top of area)
      results.population_history.forEach((snapshot, i) => {
        const total = getTotalPop(snapshot.populations);
        let cumulative = 0;

        // Sum up all strategies before this one
        for (let j = 0; j <= strategyIndex; j++) {
          cumulative += (snapshot.populations[strategies[j]] || 0) / total;
        }

        const x = xScale(snapshot.generation);
        const y = yScale(cumulative);
        points.push(`${i === 0 ? 'M' : 'L'} ${x} ${y}`);
      });

      // Backward pass (bottom of area)
      for (let i = results.population_history.length - 1; i >= 0; i--) {
        const snapshot = results.population_history[i];
        const total = getTotalPop(snapshot.populations);
        let cumulative = 0;

        // Sum up all strategies before this one (not including)
        for (let j = 0; j < strategyIndex; j++) {
          cumulative += (snapshot.populations[strategies[j]] || 0) / total;
        }

        const x = xScale(snapshot.generation);
        const y = yScale(cumulative);
        points.push(`L ${x} ${y}`);
      }

      points.push('Z');

      // Get color for strategy
      const colorKey = strategy.toLowerCase().replace(/[^a-z]/g, '_');
      const color = Object.entries(STRATEGY_COLORS).find(([key]) =>
        colorKey.includes(key.toLowerCase())
      )?.[1] || '#6b7280';

      paths.push({
        strategy,
        d: points.join(' '),
        color,
      });
    });

    return paths;
  };

  const paths = generatePaths();

  return (
    <div className="space-y-4">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="w-full max-w-2xl"
        style={{ minHeight: '200px' }}
      >
        {/* Y-axis */}
        <line
          x1={padding.left}
          y1={padding.top}
          x2={padding.left}
          y2={height - padding.bottom}
          stroke="#9ca3af"
          strokeWidth="1"
        />
        {/* Y-axis labels */}
        {[0, 25, 50, 75, 100].map((pct) => (
          <g key={pct}>
            <line
              x1={padding.left - 5}
              y1={yScale(pct / 100)}
              x2={padding.left}
              y2={yScale(pct / 100)}
              stroke="#9ca3af"
              strokeWidth="1"
            />
            <text
              x={padding.left - 8}
              y={yScale(pct / 100)}
              textAnchor="end"
              alignmentBaseline="middle"
              className="text-xs fill-gray-500"
            >
              {pct}%
            </text>
          </g>
        ))}

        {/* X-axis */}
        <line
          x1={padding.left}
          y1={height - padding.bottom}
          x2={width - padding.right}
          y2={height - padding.bottom}
          stroke="#9ca3af"
          strokeWidth="1"
        />
        {/* X-axis label */}
        <text
          x={(width - padding.left - padding.right) / 2 + padding.left}
          y={height - 5}
          textAnchor="middle"
          className="text-xs fill-gray-500"
        >
          Generations
        </text>

        {/* Stacked areas */}
        {paths.map((path) => (
          <path
            key={path.strategy}
            d={path.d}
            fill={path.color}
            opacity="0.8"
          />
        ))}
      </svg>

      {/* Legend */}
      <div className="flex flex-wrap gap-3 justify-center">
        {strategies.map((strategy) => {
          const colorKey = strategy.toLowerCase().replace(/[^a-z]/g, '_');
          const color = Object.entries(STRATEGY_COLORS).find(([key]) =>
            colorKey.includes(key.toLowerCase())
          )?.[1] || '#6b7280';

          return (
            <div key={strategy} className="flex items-center gap-1">
              <div
                className="w-3 h-3 rounded"
                style={{ backgroundColor: color }}
              />
              <span className="text-xs text-gray-600 dark:text-gray-400">
                {strategy.length > 20 ? strategy.slice(0, 20) + '...' : strategy}
              </span>
            </div>
          );
        })}
      </div>

      {/* Winner announcement */}
      {results.winner_strategy_name && (
        <div className="text-center p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
          <p className="text-sm text-green-800 dark:text-green-200">
            <strong>Winner:</strong> {results.winner_strategy_name}
            {results.is_evolutionarily_stable && ' (Evolutionarily Stable)'}
          </p>
        </div>
      )}
    </div>
  );
}
