'use client';

/**
 * TournamentCard Component
 *
 * Displays a tournament with its status, rankings, and payoff matrix.
 */
import { useState } from 'react';
import { useTournamentResults } from '@/hooks/useGameTheory';
import { PayoffMatrix } from './PayoffMatrix';
import { STATUS_COLORS } from '@/types/game-theory';
import type { Tournament } from '@/types/game-theory';

interface TournamentCardProps {
  tournament: Tournament;
}

export function TournamentCard({ tournament }: TournamentCardProps) {
  const [showDetails, setShowDetails] = useState(false);
  const { data: results } = useTournamentResults(
    showDetails && tournament.status === 'completed' ? tournament.id : undefined
  );

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
      {/* Header */}
      <div
        className="p-4 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50"
        onClick={() => setShowDetails(!showDetails)}
      >
        <div className="flex items-center justify-between">
          <div>
            <h4 className="font-medium text-gray-900 dark:text-white">
              {tournament.name}
            </h4>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {tournament.turns_per_match} turns x {tournament.repetitions} reps
              {tournament.winner_strategy_name && (
                <span className="ml-2 text-green-600 dark:text-green-400">
                  Winner: {tournament.winner_strategy_name}
                </span>
              )}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <span
              className="px-2 py-1 text-xs rounded-full font-medium"
              style={{
                backgroundColor: STATUS_COLORS[tournament.status] + '20',
                color: STATUS_COLORS[tournament.status],
              }}
            >
              {tournament.status}
            </span>
            <svg
              className={`w-5 h-5 text-gray-400 transition-transform ${
                showDetails ? 'rotate-180' : ''
              }`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </div>
        </div>
      </div>

      {/* Details */}
      {showDetails && (
        <div className="border-t border-gray-200 dark:border-gray-700 p-4 space-y-6">
          {/* Rankings */}
          {results?.rankings && results.rankings.length > 0 && (
            <div>
              <h5 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                Rankings
              </h5>
              <div className="space-y-2">
                {results.rankings.map((ranking) => (
                  <div
                    key={ranking.strategy_id}
                    className={`flex items-center justify-between p-3 rounded ${
                      ranking.rank === 1
                        ? 'bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800'
                        : 'bg-gray-50 dark:bg-gray-700/50'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <span
                        className={`w-6 h-6 flex items-center justify-center rounded-full text-xs font-bold ${
                          ranking.rank === 1
                            ? 'bg-yellow-400 text-yellow-900'
                            : ranking.rank === 2
                            ? 'bg-gray-300 text-gray-700'
                            : ranking.rank === 3
                            ? 'bg-orange-400 text-orange-900'
                            : 'bg-gray-200 text-gray-600'
                        }`}
                      >
                        {ranking.rank}
                      </span>
                      <span className="font-medium text-gray-900 dark:text-white">
                        {ranking.strategy_name}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 text-sm">
                      <span className="text-gray-500 dark:text-gray-400">
                        Score: <span className="font-medium text-gray-700 dark:text-gray-300">{ranking.average_score.toFixed(2)}</span>
                      </span>
                      <span className="text-gray-500 dark:text-gray-400">
                        Coop: <span className="font-medium text-gray-700 dark:text-gray-300">{(ranking.cooperation_rate * 100).toFixed(0)}%</span>
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Payoff Matrix */}
          {tournament.status === 'completed' && (
            <div>
              <h5 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                Payoff Matrix
              </h5>
              <PayoffMatrix tournamentId={tournament.id} />
            </div>
          )}

          {/* Loading/Pending states */}
          {tournament.status === 'pending' && (
            <p className="text-sm text-gray-500 text-center py-4">
              Tournament pending...
            </p>
          )}
          {tournament.status === 'running' && (
            <div className="flex items-center justify-center gap-2 py-4">
              <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
              <span className="text-sm text-blue-500">Tournament running...</span>
            </div>
          )}
          {tournament.status === 'failed' && tournament.error_message && (
            <div className="p-3 bg-red-50 dark:bg-red-900/20 rounded text-sm text-red-700 dark:text-red-300">
              Error: {tournament.error_message}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
