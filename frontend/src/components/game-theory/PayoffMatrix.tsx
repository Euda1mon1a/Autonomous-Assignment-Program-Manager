'use client';

/**
 * PayoffMatrix Component
 *
 * Visualizes tournament results as a heatmap showing
 * average payoffs between all strategy pairs.
 */
import { useTournamentResults } from '@/hooks/useGameTheory';
import { LoadingSpinner } from '@/components/LoadingSpinner';

interface PayoffMatrixProps {
  tournamentId: string;
}

export function PayoffMatrix({ tournamentId }: PayoffMatrixProps) {
  const { data: results, isLoading, error } = useTournamentResults(tournamentId);

  if (isLoading) return <LoadingSpinner />;
  if (error) return <p className="text-red-500 text-sm">Failed to load results</p>;
  if (!results?.payoffMatrix) return null;

  const strategies = Object.keys(results.payoffMatrix);
  const maxPayoff = Math.max(
    ...strategies.flatMap((s) =>
      Object.values(results.payoffMatrix[s] || {})
    )
  );
  const minPayoff = Math.min(
    ...strategies.flatMap((s) =>
      Object.values(results.payoffMatrix[s] || {})
    )
  );

  const getColor = (value: number): string => {
    const normalized = (value - minPayoff) / (maxPayoff - minPayoff || 1);
    // Green for high, red for low
    const r = Math.round(255 * (1 - normalized));
    const g = Math.round(255 * normalized);
    return `rgb(${r}, ${g}, 100)`;
  };

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm">
        <thead>
          <tr>
            <th className="p-2 text-left text-gray-500 dark:text-gray-400">vs</th>
            {strategies.map((s) => (
              <th
                key={s}
                className="p-2 text-xs text-gray-700 dark:text-gray-300 font-medium"
                style={{ writingMode: 'vertical-rl', textOrientation: 'mixed', maxWidth: '80px' }}
              >
                {s.length > 15 ? s.slice(0, 15) + '...' : s}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {strategies.map((row) => (
            <tr key={row}>
              <td className="p-2 text-xs font-medium text-gray-700 dark:text-gray-300 whitespace-nowrap">
                {row.length > 20 ? row.slice(0, 20) + '...' : row}
              </td>
              {strategies.map((col) => {
                const value = results.payoffMatrix[row]?.[col] ?? 0;
                return (
                  <td
                    key={col}
                    className="p-2 text-center text-xs font-mono"
                    style={{
                      backgroundColor: getColor(value),
                      color: value > (maxPayoff + minPayoff) / 2 ? '#000' : '#fff',
                    }}
                    title={`${row} vs ${col}: ${value.toFixed(2)}`}
                  >
                    {value.toFixed(1)}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
      <div className="mt-2 flex items-center justify-center gap-2 text-xs text-gray-500">
        <span>Low ({minPayoff.toFixed(1)})</span>
        <div
          className="w-24 h-3 rounded"
          style={{
            background: `linear-gradient(to right, rgb(255, 0, 100), rgb(0, 255, 100))`,
          }}
        />
        <span>High ({maxPayoff.toFixed(1)})</span>
      </div>
    </div>
  );
}
