/**
 * BridgeSync 3D Visualizer
 *
 * Real-time visualization of data flow between Python backend and React frontend.
 * Shows packets traveling through the system architecture.
 *
 * @route Part of /admin/labs/optimization or /admin/labs/data
 */

'use client';

import { useState, useCallback, useEffect, useRef, Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { PerspectiveCamera, OrbitControls, Stars } from '@react-three/drei';
import * as THREE from 'three';
import { BridgeNode3D } from './components/BridgeNode3D';
import { BridgeEdge3D } from './components/BridgeEdge3D';
import { DataPacket3D } from './components/DataPacket3D';
import { StatsPanel } from './components/StatsPanel';
import {
  INITIAL_NODES,
  INITIAL_EDGES,
  generatePacket,
  generateStats,
} from './constants';
import type {
  BridgeSyncVisualizerProps,
  BridgeNode,
  BridgeEdge,
  DataPacket,
  SyncStats,
  ConnectionStatus,
} from './types';

// Packet with position info for 3D rendering
interface ActivePacket extends DataPacket {
  startPos: THREE.Vector3;
  endPos: THREE.Vector3;
}

export function BridgeSyncVisualizer({
  className = '',
}: BridgeSyncVisualizerProps): JSX.Element {
  const [nodes] = useState<BridgeNode[]>(INITIAL_NODES);
  const [edges] = useState<BridgeEdge[]>(INITIAL_EDGES);
  const [packets, setPackets] = useState<ActivePacket[]>([]);
  const [stats, setStats] = useState<SyncStats>(generateStats);
  const [connection, setConnection] = useState<ConnectionStatus>('connecting');
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;

    // Simulate connection
    const connectTimer = setTimeout(() => {
      if (mountedRef.current) setConnection('connected');
    }, 1500);

    // Generate packets periodically
    const packetInterval = setInterval(() => {
      if (!mountedRef.current || connection !== 'connected') return;

      // Pick a random edge
      const edge = INITIAL_EDGES[Math.floor(Math.random() * INITIAL_EDGES.length)];
      const sourceNode = nodes.find((n) => n.id === edge.source);
      const targetNode = nodes.find((n) => n.id === edge.target);

      if (!sourceNode || !targetNode) return;

      // Create packet
      const packet = generatePacket(
        sourceNode.id as DataPacket['source'],
        targetNode.id as DataPacket['target']
      );

      const activePacket: ActivePacket = {
        ...packet,
        startPos: new THREE.Vector3(
          sourceNode.position.x,
          sourceNode.position.y,
          sourceNode.position.z
        ),
        endPos: new THREE.Vector3(
          targetNode.position.x,
          targetNode.position.y,
          targetNode.position.z
        ),
      };

      setPackets((prev) => [...prev, activePacket]);
    }, 200);

    // Update stats periodically
    const statsInterval = setInterval(() => {
      if (mountedRef.current) setStats(generateStats());
    }, 2000);

    return () => {
      mountedRef.current = false;
      clearTimeout(connectTimer);
      clearInterval(packetInterval);
      clearInterval(statsInterval);
    };
  }, [connection, nodes]);

  const handlePacketComplete = useCallback((id: string) => {
    setPackets((prev) => prev.filter((p) => p.id !== id));
  }, []);

  return (
    <div className={`relative w-full h-screen bg-[#0a0a0f] ${className}`}>
      {/* 3D Canvas */}
      <Canvas shadows gl={{ antialias: true }}>
        <PerspectiveCamera makeDefault position={[0, 2, 8]} fov={60} />
        <color attach="background" args={['#0a0a0f']} />

        {/* Lighting */}
        <ambientLight intensity={0.3} />
        <directionalLight position={[5, 10, 5]} intensity={0.6} />
        <pointLight position={[-3, 3, 0]} intensity={0.5} color="#06b6d4" />
        <pointLight position={[3, 3, 0]} intensity={0.5} color="#22c55e" />

        <Suspense fallback={null}>
          {/* Edges */}
          {edges.map((edge) => (
            <BridgeEdge3D key={edge.id} edge={edge} nodes={nodes} />
          ))}

          {/* Nodes */}
          {nodes.map((node) => (
            <BridgeNode3D key={node.id} node={node} />
          ))}

          {/* Packets */}
          {packets.map((packet) => (
            <DataPacket3D
              key={packet.id}
              packet={packet}
              startPos={packet.startPos}
              endPos={packet.endPos}
              onComplete={handlePacketComplete}
            />
          ))}

          {/* Background stars */}
          <Stars
            radius={50}
            depth={50}
            count={1500}
            factor={4}
            saturation={0}
            fade
            speed={0.5}
          />
        </Suspense>

        <OrbitControls
          enablePan={false}
          maxDistance={15}
          minDistance={4}
          autoRotate
          autoRotateSpeed={0.2}
        />
      </Canvas>

      {/* Stats Panel */}
      <StatsPanel stats={stats} connection={connection} />

      {/* Info Panel */}
      <div className="absolute bottom-4 right-4 max-w-xs bg-slate-950/90 border border-slate-800 p-4 rounded-xl backdrop-blur-md text-white">
        <h3 className="text-sm font-semibold text-cyan-400 mb-2">
          What is BridgeSync?
        </h3>
        <p className="text-xs text-slate-400 leading-relaxed">
          BridgeSync visualizes real-time data flow between the Python backend
          (FastAPI, CP-SAT solver, PostgreSQL) and the React/Three.js frontend.
          Watch packets travel through the system architecture as schedules,
          constraints, and solutions sync across the bridge.
        </p>
      </div>
    </div>
  );
}

export default BridgeSyncVisualizer;
