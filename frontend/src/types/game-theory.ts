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
  strategy_type: StrategyType;
  created_at: string;

  utilization_target: number;
  cross_zone_borrowing: boolean;
  sacrifice_willingness: 'low' | 'medium' | 'high';
  defense_activation_threshold: number;
  response_timeout_ms: number;

  initial_action: 'cooperate' | 'defect';
  forgiveness_probability: number;
  retaliation_memory: number;
  is_stochastic: boolean;

  tournaments_participated: number;
  total_matches: number;
  total_wins: number;
  average_score: number | null;
  cooperation_rate: number | null;
  is_active: boolean;
}

export interface StrategyCreate {
  name: string;
  description?: string;
  strategy_type: StrategyType;
  utilization_target?: number;
  cross_zone_borrowing?: boolean;
  sacrifice_willingness?: 'low' | 'medium' | 'high';
  defense_activation_threshold?: number;
  response_timeout_ms?: number;
  initial_action?: 'cooperate' | 'defect';
  forgiveness_probability?: number;
  retaliation_memory?: number;
  is_stochastic?: boolean;
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
  created_at: string;
  created_by: string | null;

  turns_per_match: number;
  repetitions: number;
  noise: number;

  strategy_ids: string[] | null;
  status: SimulationStatus;

  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;

  celery_task_id: string | null;
  total_matches: number | null;
  winner_strategy_id: string | null;
  winner_strategy_name: string | null;
}

export interface TournamentCreate {
  name: string;
  description?: string;
  strategy_ids: string[];
  turns_per_match?: number;
  repetitions?: number;
  noise?: number;
  payoff_cc?: number;
  payoff_cd?: number;
  payoff_dc?: number;
  payoff_dd?: number;
}

export interface TournamentRanking {
  rank: number;
  strategy_id: string;
  strategy_name: string;
  total_score: number;
  average_score: number;
  wins: number;
  losses: number;
  ties: number;
  cooperation_rate: number;
}

export interface TournamentResults {
  id: string;
  name: string;
  status: SimulationStatus;
  completed_at: string | null;
  rankings: TournamentRanking[];
  payoff_matrix: Record<string, Record<string, number>>;
  total_matches: number;
  total_turns: number;
  average_cooperation_rate: number;
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
  created_at: string;
  created_by: string | null;

  initial_population_size: number;
  turns_per_interaction: number;
  max_generations: number;
  mutation_rate: number;

  status: SimulationStatus;
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;

  celery_task_id: string | null;
  generations_completed: number;
  winner_strategy_id: string | null;
  winner_strategy_name: string | null;
  is_evolutionarily_stable: boolean | null;
}

export interface EvolutionCreate {
  name: string;
  description?: string;
  initial_composition: Record<string, number>;
  turns_per_interaction?: number;
  max_generations?: number;
  mutation_rate?: number;
}

export interface PopulationSnapshot {
  generation: number;
  populations: Record<string, number>;
}

export interface EvolutionResults {
  id: string;
  name: string;
  status: SimulationStatus;
  completed_at: string | null;
  generations_completed: number;
  winner_strategy_name: string | null;
  is_evolutionarily_stable: boolean | null;
  population_history: PopulationSnapshot[];
  final_population: Record<string, number>;
}

export interface EvolutionListResponse {
  simulations: Evolution[];
  total: number;
}

// Validation types
export interface ValidationRequest {
  strategy_id: string;
  turns?: number;
  repetitions?: number;
  pass_threshold?: number;
}

export interface ValidationResult {
  id: string;
  strategy_id: string;
  strategy_name: string;
  validated_at: string;
  turns: number;
  repetitions: number;
  passed: boolean;
  average_score: number;
  cooperation_rate: number;
  pass_threshold: number;
  assessment: string;
  recommendation: string | null;
}

// Analysis types
export interface ConfigAnalysisRequest {
  utilization_target?: number;
  cross_zone_borrowing?: boolean;
  sacrifice_willingness?: 'low' | 'medium' | 'high';
  defense_activation_threshold?: number;
}

export interface ConfigAnalysisResult {
  config_name: string;
  matchup_results: Record<string, {
    score: number;
    cooperation_rate: number;
    outcome: 'win' | 'loss' | 'tie';
  }>;
  average_score: number;
  cooperation_rate: number;
  recommendation: string;
  strategy_classification: StrategyType;
}

// Summary types
export interface GameTheorySummary {
  total_strategies: number;
  total_tournaments: number;
  completed_tournaments: number;
  total_evolutions: number;
  completed_evolutions: number;
  best_performing_strategy: string | null;
  best_strategy_score: number;
  recent_tournaments: {
    id: string;
    name: string;
    status: SimulationStatus;
    winner: string | null;
  }[];
  recent_evolutions: {
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
