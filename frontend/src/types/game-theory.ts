/**
 * TypeScript types for Game Theory API.
 *
 * Based on Axelrod's Prisoner's Dilemma framework for
 * testing scheduling and resilience configurations.
 */

export type StrategyType =
  | 'cooperative'
  | 'aggressive'
  | 'tit_for_tat'
  | 'grudger'
  | 'pavlov'
  | 'random'
  | 'suspicious_tft'
  | 'forgiving_tft'
  | 'custom';

export type SimulationStatus =
  | 'pending'
  | 'running'
  | 'completed'
  | 'failed'
  | 'cancelled';

// Strategy types
export interface ConfigStrategy {
  id: string;
  name: string;
  description: string | null;
  strategyType: StrategyType;
  createdAt: string;

  utilizationTarget: number;
  crossZoneBorrowing: boolean;
  sacrificeWillingness: 'low' | 'medium' | 'high';
  defenseActivationThreshold: number;
  responseTimeoutMs: number;

  initialAction: 'cooperate' | 'defect';
  forgivenessProbability: number;
  retaliationMemory: number;
  isStochastic: boolean;

  tournamentsParticipated: number;
  totalMatches: number;
  totalWins: number;
  averageScore: number | null;
  cooperationRate: number | null;
  isActive: boolean;
}

export interface StrategyCreate {
  name: string;
  description?: string;
  strategyType: StrategyType;
  utilizationTarget?: number;
  crossZoneBorrowing?: boolean;
  sacrificeWillingness?: 'low' | 'medium' | 'high';
  defenseActivationThreshold?: number;
  responseTimeoutMs?: number;
  initialAction?: 'cooperate' | 'defect';
  forgivenessProbability?: number;
  retaliationMemory?: number;
  isStochastic?: boolean;
}

export interface StrategyListResponse {
  strategies: ConfigStrategy[];
  total: number;
}

// Tournament types
export interface Tournament {
  id: string;
  name: string;
  description: string | null;
  createdAt: string;
  createdBy: string | null;

  turnsPerMatch: number;
  repetitions: number;
  noise: number;

  strategyIds: string[] | null;
  status: SimulationStatus;

  startedAt: string | null;
  completedAt: string | null;
  errorMessage: string | null;

  celeryTaskId: string | null;
  totalMatches: number | null;
  winnerStrategyId: string | null;
  winnerStrategyName: string | null;
}

export interface TournamentCreate {
  name: string;
  description?: string;
  strategyIds: string[];
  turnsPerMatch?: number;
  repetitions?: number;
  noise?: number;
  payoffCc?: number;
  payoffCd?: number;
  payoffDc?: number;
  payoffDd?: number;
}

export interface TournamentRanking {
  rank: number;
  strategyId: string;
  strategyName: string;
  totalScore: number;
  averageScore: number;
  wins: number;
  losses: number;
  ties: number;
  cooperationRate: number;
}

export interface TournamentResults {
  id: string;
  name: string;
  status: SimulationStatus;
  completedAt: string | null;
  rankings: TournamentRanking[];
  payoffMatrix: Record<string, Record<string, number>>;
  totalMatches: number;
  totalTurns: number;
  averageCooperationRate: number;
}

export interface TournamentListResponse {
  tournaments: Tournament[];
  total: number;
}

// Evolution types
export interface Evolution {
  id: string;
  name: string;
  description: string | null;
  createdAt: string;
  createdBy: string | null;

  initialPopulationSize: number;
  turnsPerInteraction: number;
  maxGenerations: number;
  mutationRate: number;

  status: SimulationStatus;
  startedAt: string | null;
  completedAt: string | null;
  errorMessage: string | null;

  celeryTaskId: string | null;
  generationsCompleted: number;
  winnerStrategyId: string | null;
  winnerStrategyName: string | null;
  isEvolutionarilyStable: boolean | null;
}

export interface EvolutionCreate {
  name: string;
  description?: string;
  initialComposition: Record<string, number>;
  turnsPerInteraction?: number;
  maxGenerations?: number;
  mutationRate?: number;
}

export interface PopulationSnapshot {
  generation: number;
  populations: Record<string, number>;
}

export interface EvolutionResults {
  id: string;
  name: string;
  status: SimulationStatus;
  completedAt: string | null;
  generationsCompleted: number;
  winnerStrategyName: string | null;
  isEvolutionarilyStable: boolean | null;
  populationHistory: PopulationSnapshot[];
  finalPopulation: Record<string, number>;
}

export interface EvolutionListResponse {
  simulations: Evolution[];
  total: number;
}

// Validation types
export interface ValidationRequest {
  strategyId: string;
  turns?: number;
  repetitions?: number;
  passThreshold?: number;
}

export interface ValidationResult {
  id: string;
  strategyId: string;
  strategyName: string;
  validatedAt: string;
  turns: number;
  repetitions: number;
  passed: boolean;
  averageScore: number;
  cooperationRate: number;
  passThreshold: number;
  assessment: string;
  recommendation: string | null;
}

// Analysis types
export interface ConfigAnalysisRequest {
  utilizationTarget?: number;
  crossZoneBorrowing?: boolean;
  sacrificeWillingness?: 'low' | 'medium' | 'high';
  defenseActivationThreshold?: number;
}

export interface ConfigAnalysisResult {
  configName: string;
  matchupResults: Record<string, {
    score: number;
    cooperationRate: number;
    outcome: 'win' | 'loss' | 'tie';
  }>;
  averageScore: number;
  cooperationRate: number;
  recommendation: string;
  strategyClassification: StrategyType;
}

// Summary types
export interface GameTheorySummary {
  totalStrategies: number;
  totalTournaments: number;
  completedTournaments: number;
  totalEvolutions: number;
  completedEvolutions: number;
  bestPerformingStrategy: string | null;
  bestStrategyScore: number;
  recentTournaments: {
    id: string;
    name: string;
    status: SimulationStatus;
    winner: string | null;
  }[];
  recentEvolutions: {
    id: string;
    name: string;
    status: SimulationStatus;
    winner: string | null;
  }[];
}

// Color mapping for strategy types
export const STRATEGY_COLORS: Record<StrategyType, string> = {
  cooperative: '#22c55e',    // green
  aggressive: '#ef4444',     // red
  tit_for_tat: '#3b82f6',    // blue
  grudger: '#f97316',        // orange
  pavlov: '#8b5cf6',         // purple
  random: '#6b7280',         // gray
  suspicious_tft: '#eab308', // yellow
  forgiving_tft: '#06b6d4',  // cyan
  custom: '#ec4899',         // pink
};

// Strategy type labels
export const STRATEGY_LABELS: Record<StrategyType, string> = {
  cooperative: 'Cooperative',
  aggressive: 'Aggressive',
  tit_for_tat: 'Tit for Tat',
  grudger: 'Grudger',
  pavlov: 'Pavlov',
  random: 'Random',
  suspicious_tft: 'Suspicious TFT',
  forgiving_tft: 'Forgiving TFT',
  custom: 'Custom',
};

// Status colors
export const STATUS_COLORS: Record<SimulationStatus, string> = {
  pending: '#6b7280',   // gray
  running: '#3b82f6',   // blue
  completed: '#22c55e', // green
  failed: '#ef4444',    // red
  cancelled: '#f97316', // orange
};
