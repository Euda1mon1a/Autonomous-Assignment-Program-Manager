/**
 * Sovereign Portal Feature
 *
 * Unified command dashboard for scheduling system monitoring.
 */

export { SovereignPortal } from './SovereignPortal';
export { default } from './SovereignPortal';

// Types
export type {
  PanelId,
  PanelConfig,
  SystemStatus,
  SystemAlert,
  SpatialMetrics,
  FairnessMetrics,
  SolverMetrics,
  FragilityMetrics,
  DashboardState,
  SovereignPortalProps,
  PanelProps,
} from './types';

// Constants
export {
  PANEL_CONFIGS,
  STATUS_COLORS,
  STATUS_BG_COLORS,
  SYSTEM_STATUS_COLORS,
  generateMockDashboardState,
  computeSystemStatus,
  formatTimestamp,
} from './constants';

// Components (for advanced usage)
export { Panel } from './components/Panel';
export { StatusBadge } from './components/StatusBadge';
export { AlertFeed } from './components/AlertFeed';
export { SpatialMini } from './components/SpatialMini';
export { FairnessMini } from './components/FairnessMini';
export { SolverMini } from './components/SolverMini';
export { FragilityMini } from './components/FragilityMini';
