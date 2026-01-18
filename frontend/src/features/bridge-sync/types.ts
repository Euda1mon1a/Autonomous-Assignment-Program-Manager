/**
 * BridgeSync Types
 *
 * Types for real-time Python→Three.js data sync visualization.
 */

/**
 * Data packet traveling through the bridge
 */
export interface DataPacket {
  id: string;
  type: 'schedule' | 'constraint' | 'solution' | 'validation';
  size: number; // bytes
  timestamp: Date;
  source: 'python' | 'database' | 'solver';
  target: 'frontend' | 'cache' | 'websocket';
  status: 'pending' | 'in_transit' | 'delivered' | 'failed';
  progress: number; // 0-1
}

/**
 * Connection status
 */
export type ConnectionStatus = 'connected' | 'connecting' | 'disconnected' | 'error';

/**
 * Bridge node in the visualization
 */
export interface BridgeNode {
  id: string;
  label: string;
  type: 'source' | 'processor' | 'target';
  position: { x: number; y: number; z: number };
  status: 'active' | 'idle' | 'processing' | 'error';
  throughput: number; // packets/sec
}

/**
 * Edge connecting nodes
 */
export interface BridgeEdge {
  id: string;
  source: string;
  target: string;
  active: boolean;
  packetCount: number;
}

/**
 * Sync statistics
 */
export interface SyncStats {
  packetsPerSecond: number;
  bytesPerSecond: number;
  latencyMs: number;
  errorRate: number;
  uptime: number;
}

/**
 * Bridge state
 */
export interface BridgeState {
  connection: ConnectionStatus;
  nodes: BridgeNode[];
  edges: BridgeEdge[];
  packets: DataPacket[];
  stats: SyncStats;
}

/**
 * Props for the main visualizer
 */
export interface BridgeSyncVisualizerProps {
  className?: string;
}
