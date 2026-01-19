/**
 * Hopfield Energy Landscape Types
 *
 * Types for the schedule stability visualization using
 * neural attractor dynamics from Hopfield networks.
 */

/**
 * Military readiness status levels
 */
export type ReadinessStatus = 'white' | 'green' | 'amber' | 'red' | 'black';

/**
 * Energy state for the current schedule position
 */
export interface EnergyState {
  /** Supervision coverage (0-1) */
  coverage: number;
  /** Faculty load balance (0-1) */
  balance: number;
  /** Computed energy level */
  energy: number;
  /** Readiness status */
  status: ReadinessStatus;
}

/**
 * API response types for real data integration
 * Re-exported from exotic-resilience API client
 */
export type {
  HopfieldEnergyResponse,
  EnergyMetricsResponse,
  StabilityLevel,
} from '@/api/exotic-resilience';

/**
 * Props for the main visualizer component
 */
export interface HopfieldVisualizerProps {
  /** Initial coverage value (0-100) */
  initialCoverage?: number;
  /** Initial balance value (0-100) */
  initialBalance?: number;
  /** Show/hide control panel */
  showControls?: boolean;
  /** Custom class name */
  className?: string;
  /** Real API data for metrics display */
  apiData?: import('@/api/exotic-resilience').HopfieldEnergyResponse;
  /** Loading state for API data */
  isLoading?: boolean;
  /** Error state for API data */
  error?: string | null;
  /** Callback to trigger analysis */
  onAnalyze?: () => void;
}

/**
 * Props for the energy surface component
 */
export interface EnergySurfaceProps {
  /** Grid resolution */
  resolution?: number;
}

/**
 * Props for the energy ball component
 */
export interface EnergyBallProps {
  /** Normalized coverage (0-1) */
  coverage: number;
  /** Normalized balance (0-1) */
  balance: number;
  /** Whether gradient descent is active */
  isSettling: boolean;
  /** Callback when ball position updates */
  onPositionUpdate: (coverage: number, balance: number) => void;
}

/**
 * Props for the control panel component
 */
export interface ControlPanelProps {
  /** Current coverage (0-100) */
  coverage: number;
  /** Current balance (0-100) */
  balance: number;
  /** Current energy level */
  energy: number;
  /** Current status */
  status: ReadinessStatus;
  /** Whether settling is active */
  isSettling: boolean;
  /** Coverage change handler */
  onCoverageChange: (value: number) => void;
  /** Balance change handler */
  onBalanceChange: (value: number) => void;
  /** Toggle settling */
  onToggleSettle: () => void;
}

/**
 * Military color mapping for energy levels
 */
export interface MilitaryColor {
  r: number;
  g: number;
  b: number;
}
