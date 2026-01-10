'use client';

/**
 * StrategyCard Component
 *
 * Displays a configuration strategy with its game-theoretic properties.
 */
import type { ConfigStrategy } from '@/types/game-theory';
import { STRATEGY_COLORS, STRATEGY_LABELS } from '@/types/game-theory';

interface StrategyCardProps {
  strategy: ConfigStrategy;
  isSelected: boolean;
  onToggle: () => void;
  onValidate: () => void;
}

export function StrategyCard({ strategy, isSelected, onToggle, onValidate }: StrategyCardProps) {
  const color = STRATEGY_COLORS[strategy.strategyType] || '#6b7280';
  const label = STRATEGY_LABELS[strategy.strategyType] || strategy.strategyType;

  return (
    <div
      className={`relative bg-white dark:bg-gray-800 rounded-lg shadow p-4 border-2 transition-colors cursor-pointer ${
        isSelected ? 'border-blue-500' : 'border-transparent hover:border-gray-300'
      }`}
      onClick={onToggle}
    >
      {/* Selection indicator */}
      {isSelected && (
        <div className="absolute top-2 right-2 w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center">
          <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
          </svg>
        </div>
      )}

      {/* Header */}
      <div className="flex items-center gap-2 mb-3">
        <div
          className="w-3 h-3 rounded-full"
          style={{ backgroundColor: color }}
        />
        <h4 className="font-medium text-gray-900 dark:text-white text-sm">
          {strategy.name}
        </h4>
      </div>

      {/* Type badge */}
      <span
        className="inline-block px-2 py-0.5 text-xs rounded-full mb-2"
        style={{ backgroundColor: color + '20', color }}
      >
        {label}
      </span>

      {/* Description */}
      {strategy.description && (
        <p className="text-xs text-gray-500 dark:text-gray-400 mb-3 line-clamp-2">
          {strategy.description}
        </p>
      )}

      {/* Config details */}
      <div className="grid grid-cols-2 gap-2 text-xs mb-3">
        <div>
          <span className="text-gray-500 dark:text-gray-400">Utilization:</span>
          <span className="ml-1 font-medium text-gray-700 dark:text-gray-300">
            {(strategy.utilizationTarget * 100).toFixed(0)}%
          </span>
        </div>
        <div>
          <span className="text-gray-500 dark:text-gray-400">Cross-zone:</span>
          <span className="ml-1 font-medium text-gray-700 dark:text-gray-300">
            {strategy.crossZoneBorrowing ? 'Yes' : 'No'}
          </span>
        </div>
        <div>
          <span className="text-gray-500 dark:text-gray-400">Sacrifice:</span>
          <span className="ml-1 font-medium text-gray-700 dark:text-gray-300 capitalize">
            {strategy.sacrificeWillingness}
          </span>
        </div>
        <div>
          <span className="text-gray-500 dark:text-gray-400">Defense Lvl:</span>
          <span className="ml-1 font-medium text-gray-700 dark:text-gray-300">
            {strategy.defenseActivationThreshold}
          </span>
        </div>
      </div>

      {/* Stats */}
      {strategy.tournamentsParticipated > 0 && (
        <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 pt-2 border-t border-gray-200 dark:border-gray-700">
          <span>{strategy.tournamentsParticipated} tournaments</span>
          <span>{strategy.totalWins} wins</span>
          {strategy.averageScore !== null && (
            <span>Avg: {strategy.averageScore.toFixed(2)}</span>
          )}
        </div>
      )}

      {/* Actions */}
      <div className="mt-3 pt-2 border-t border-gray-200 dark:border-gray-700">
        <button
          onClick={(e) => {
            e.stopPropagation();
            onValidate();
          }}
          className="text-xs text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
        >
          Validate against TFT
        </button>
      </div>
    </div>
  );
}
