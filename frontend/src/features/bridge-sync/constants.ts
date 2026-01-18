/**
 * BridgeSync Constants
 *
 * Mock data and utilities for the bridge sync visualization.
 */

import type { BridgeNode, BridgeEdge, DataPacket, SyncStats } from './types';

/**
 * Initial node configuration
 */
export const INITIAL_NODES: BridgeNode[] = [
  // Sources (left side)
  {
    id: 'python',
    label: 'Python Backend',
    type: 'source',
    position: { x: -3, y: 1, z: 0 },
    status: 'active',
    throughput: 45,
  },
  {
    id: 'database',
    label: 'PostgreSQL',
    type: 'source',
    position: { x: -3, y: 0, z: 0 },
    status: 'active',
    throughput: 120,
  },
  {
    id: 'solver',
    label: 'CP-SAT Solver',
    type: 'source',
    position: { x: -3, y: -1, z: 0 },
    status: 'processing',
    throughput: 8,
  },

  // Processors (middle)
  {
    id: 'api',
    label: 'FastAPI',
    type: 'processor',
    position: { x: 0, y: 0.5, z: 0 },
    status: 'active',
    throughput: 200,
  },
  {
    id: 'cache',
    label: 'Redis Cache',
    type: 'processor',
    position: { x: 0, y: -0.5, z: 0 },
    status: 'active',
    throughput: 500,
  },

  // Targets (right side)
  {
    id: 'websocket',
    label: 'WebSocket',
    type: 'target',
    position: { x: 3, y: 0.5, z: 0 },
    status: 'active',
    throughput: 60,
  },
  {
    id: 'frontend',
    label: 'React/Three.js',
    type: 'target',
    position: { x: 3, y: -0.5, z: 0 },
    status: 'active',
    throughput: 30,
  },
];

/**
 * Edge configuration
 */
export const INITIAL_EDGES: BridgeEdge[] = [
  // Source → Processor
  { id: 'e1', source: 'python', target: 'api', active: true, packetCount: 0 },
  { id: 'e2', source: 'database', target: 'api', active: true, packetCount: 0 },
  { id: 'e3', source: 'database', target: 'cache', active: true, packetCount: 0 },
  { id: 'e4', source: 'solver', target: 'api', active: true, packetCount: 0 },

  // Processor → Target
  { id: 'e5', source: 'api', target: 'websocket', active: true, packetCount: 0 },
  { id: 'e6', source: 'api', target: 'frontend', active: true, packetCount: 0 },
  { id: 'e7', source: 'cache', target: 'frontend', active: true, packetCount: 0 },
];

/**
 * Packet type colors
 */
export const PACKET_COLORS: Record<DataPacket['type'], string> = {
  schedule: '#22c55e', // green
  constraint: '#3b82f6', // blue
  solution: '#eab308', // yellow
  validation: '#a855f7', // purple
};

/**
 * Node type colors
 */
export const NODE_COLORS: Record<BridgeNode['type'], string> = {
  source: '#ef4444', // red
  processor: '#06b6d4', // cyan
  target: '#22c55e', // green
};

/**
 * Generate a random packet
 */
export function generatePacket(
  source: DataPacket['source'],
  target: DataPacket['target']
): DataPacket {
  const types: DataPacket['type'][] = [
    'schedule',
    'constraint',
    'solution',
    'validation',
  ];
  const type = types[Math.floor(Math.random() * types.length)];

  return {
    id: `pkt-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    type,
    size: Math.floor(Math.random() * 5000) + 100,
    timestamp: new Date(),
    source,
    target,
    status: 'pending',
    progress: 0,
  };
}

/**
 * Generate initial stats
 */
export function generateStats(): SyncStats {
  return {
    packetsPerSecond: 45 + Math.floor(Math.random() * 20),
    bytesPerSecond: 128000 + Math.floor(Math.random() * 50000),
    latencyMs: 12 + Math.floor(Math.random() * 8),
    errorRate: Math.random() * 0.02,
    uptime: 99.7 + Math.random() * 0.3,
  };
}
