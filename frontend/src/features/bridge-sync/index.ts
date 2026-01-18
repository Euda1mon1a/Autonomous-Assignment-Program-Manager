/**
 * BridgeSync Feature
 *
 * Real-time Python→Three.js data sync visualization.
 */

export { BridgeSyncVisualizer } from './BridgeSyncVisualizer';
export { default } from './BridgeSyncVisualizer';

// Types
export type {
  DataPacket,
  ConnectionStatus,
  BridgeNode,
  BridgeEdge,
  SyncStats,
  BridgeState,
  BridgeSyncVisualizerProps,
} from './types';

// Constants
export {
  INITIAL_NODES,
  INITIAL_EDGES,
  PACKET_COLORS,
  NODE_COLORS,
  generatePacket,
  generateStats,
} from './constants';

// Components (for advanced usage)
export { BridgeNode3D } from './components/BridgeNode3D';
export { BridgeEdge3D } from './components/BridgeEdge3D';
export { DataPacket3D } from './components/DataPacket3D';
export { StatsPanel } from './components/StatsPanel';
