/**
 * Constraint Coupling View Component
 *
 * 3D visualization of how constraints interact with each other,
 * showing reinforcing and competing relationships.
 */

'use client';

import React, { useMemo, useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import type {
  ConstraintCouplingData,
  ConstraintNode,
  ConstraintCoupling,
} from './types';
import { CONSTRAINT_CATEGORY_COLORS, COUPLING_TYPE_COLORS } from './types';

interface ConstraintCouplingViewProps {
  data: ConstraintCouplingData;
  selectedConstraintId?: string | null;
  onSelectConstraint?: (id: string) => void;
  width?: number;
  height?: number;
}

export function ConstraintCouplingView({
  data,
  selectedConstraintId,
  onSelectConstraint,
  width = 800,
  height = 600,
}: ConstraintCouplingViewProps) {
  const [viewAngle, setViewAngle] = useState({ theta: 0.3, phi: 0.5 });
  const [zoom, setZoom] = useState(1);
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [showForceField, setShowForceField] = useState(false);

  // Project 3D to 2D with perspective
  const project = useCallback((x: number, y: number, z: number) => {
    // Rotate around Y axis (theta) then X axis (phi)
    const cosTheta = Math.cos(viewAngle.theta);
    const sinTheta = Math.sin(viewAngle.theta);
    const cosPhi = Math.cos(viewAngle.phi);
    const sinPhi = Math.sin(viewAngle.phi);

    // Apply rotations
    const x1 = x * cosTheta - z * sinTheta;
    const z1 = x * sinTheta + z * cosTheta;
    const y1 = y * cosPhi - z1 * sinPhi;
    const z2 = y * sinPhi + z1 * cosPhi;

    // Perspective projection
    const perspective = 10;
    const scale = perspective / (perspective + z2);

    return {
      x: width / 2 + x1 * scale * 50 * zoom,
      y: height / 2 - y1 * scale * 50 * zoom,
      z: z2,
      scale,
    };
  }, [viewAngle, zoom, width, height]);

  // Sort nodes by z-depth for proper rendering order
  const sortedNodes = useMemo(() => {
    return [...data.constraints]
      .map(node => ({
        ...node,
        projected: project(node.position.x, node.position.y, node.position.z),
      }))
      .sort((a, b) => b.projected.z - a.projected.z);
  }, [data.constraints, project]);

  // Get couplings for selected node
  const selectedCouplings = useMemo(() => {
    if (!selectedConstraintId) return [];
    return data.couplings.filter(
      c => c.source === selectedConstraintId || c.target === selectedConstraintId
    );
  }, [data.couplings, selectedConstraintId]);

  // Get coupling statistics
  const stats = useMemo(() => {
    const reinforcing = data.couplings.filter(c => c.type === 'reinforcing').length;
    const competing = data.couplings.filter(c => c.type === 'competing').length;
    const neutral = data.couplings.filter(c => c.type === 'neutral').length;
    const avgStrength = data.couplings.reduce((sum, c) => sum + Math.abs(c.strength), 0) / data.couplings.length;

    return { reinforcing, competing, neutral, avgStrength };
  }, [data.couplings]);

  // Handle drag for rotation
  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (e.buttons !== 1) return;

    setViewAngle(prev => ({
      theta: prev.theta + e.movementX * 0.01,
      phi: Math.max(-Math.PI / 2, Math.min(Math.PI / 2, prev.phi + e.movementY * 0.01)),
    }));
  }, []);

  // Handle wheel for zoom
  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    setZoom(prev => Math.max(0.5, Math.min(3, prev - e.deltaY * 0.001)));
  }, []);

  return (
    <div className="w-full h-full flex flex-col bg-slate-950">
      {/* Header */}
      <div className="p-4 border-b border-slate-800 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white">Constraint Coupling Network</h2>
          <p className="text-sm text-slate-400">
            {data.constraints.length} constraints · {data.couplings.length} couplings
          </p>
        </div>

        <div className="flex items-center gap-4">
          {/* Stats */}
          <div className="flex items-center gap-3 text-xs">
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full" style={{ backgroundColor: COUPLING_TYPE_COLORS.reinforcing }} />
              <span className="text-emerald-400">{stats.reinforcing}</span>
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full" style={{ backgroundColor: COUPLING_TYPE_COLORS.competing }} />
              <span className="text-red-400">{stats.competing}</span>
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full" style={{ backgroundColor: COUPLING_TYPE_COLORS.neutral }} />
              <span className="text-slate-400">{stats.neutral}</span>
            </span>
          </div>

          {/* Toggle force field */}
          <button
            onClick={() => setShowForceField(!showForceField)}
            className={`px-3 py-1 rounded text-sm ${
              showForceField
                ? 'bg-violet-600 text-white'
                : 'bg-slate-800 text-slate-400'
            }`}
          >
            Force Field
          </button>
        </div>
      </div>

      {/* 3D Visualization */}
      <div className="flex-1 relative">
        <svg
          width="100%"
          height="100%"
          viewBox={`0 0 ${width} ${height}`}
          onMouseMove={handleMouseMove}
          onWheel={handleWheel}
          className="cursor-grab active:cursor-grabbing"
        >
          {/* Background gradient */}
          <defs>
            <radialGradient id="bgGradient" cx="50%" cy="50%" r="70%">
              <stop offset="0%" stopColor="#1e1b4b" stopOpacity="0.3" />
              <stop offset="100%" stopColor="#0f172a" stopOpacity="0" />
            </radialGradient>
            <filter id="glow">
              <feGaussianBlur stdDeviation="3" result="coloredBlur" />
              <feMerge>
                <feMergeNode in="coloredBlur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          <rect width="100%" height="100%" fill="url(#bgGradient)" />

          {/* Force field streamlines */}
          {showForceField && data.forceField.streamlines.map((line, i) => (
            <motion.path
              key={`stream-${i}`}
              d={`M ${line.map(p => {
                const proj = project(p.x, p.y, p.z);
                return `${proj.x} ${proj.y}`;
              }).join(' L ')}`}
              fill="none"
              stroke="rgba(139, 92, 246, 0.2)"
              strokeWidth="1"
              initial={{ pathLength: 0 }}
              animate={{ pathLength: 1 }}
              transition={{ duration: 2, delay: i * 0.1 }}
            />
          ))}

          {/* Draw couplings (edges) */}
          <g>
            {data.couplings.map((coupling, i) => {
              const source = data.constraints.find(c => c.constraintId === coupling.source);
              const target = data.constraints.find(c => c.constraintId === coupling.target);
              if (!source || !target) return null;

              const sourceProj = project(source.position.x, source.position.y, source.position.z);
              const targetProj = project(target.position.x, target.position.y, target.position.z);

              const isHighlighted =
                selectedConstraintId === coupling.source ||
                selectedConstraintId === coupling.target;

              const color = COUPLING_TYPE_COLORS[coupling.type];
              const width = Math.abs(coupling.strength) * 3;

              return (
                <motion.line
                  key={`coupling-${i}`}
                  x1={sourceProj.x}
                  y1={sourceProj.y}
                  x2={targetProj.x}
                  y2={targetProj.y}
                  stroke={color}
                  strokeWidth={isHighlighted ? width + 1 : width}
                  strokeOpacity={isHighlighted ? 0.8 : 0.3}
                  initial={{ pathLength: 0 }}
                  animate={{ pathLength: 1 }}
                  transition={{ duration: 0.5, delay: i * 0.01 }}
                />
              );
            })}
          </g>

          {/* Draw constraint nodes */}
          <g>
            {sortedNodes.map((node, i) => {
              const { projected } = node;
              const isSelected = selectedConstraintId === node.constraintId;
              const isHovered = hoveredNode === node.constraintId;
              const isConnected = selectedCouplings.some(
                c => c.source === node.constraintId || c.target === node.constraintId
              );

              const baseRadius = 15 * projected.scale;
              const radius = baseRadius * (isSelected || isHovered ? 1.3 : 1);

              return (
                <g
                  key={node.constraintId}
                  onClick={() => onSelectConstraint?.(node.constraintId)}
                  onMouseEnter={() => setHoveredNode(node.constraintId)}
                  onMouseLeave={() => setHoveredNode(null)}
                  className="cursor-pointer"
                >
                  {/* Glow effect for selected/hovered */}
                  {(isSelected || isHovered || isConnected) && (
                    <circle
                      cx={projected.x}
                      cy={projected.y}
                      r={radius * 2}
                      fill={CONSTRAINT_CATEGORY_COLORS[node.category]}
                      fillOpacity={0.2}
                      filter="url(#glow)"
                    />
                  )}

                  {/* Main node */}
                  <motion.circle
                    cx={projected.x}
                    cy={projected.y}
                    r={radius}
                    fill={CONSTRAINT_CATEGORY_COLORS[node.category]}
                    fillOpacity={isSelected || isConnected ? 1 : 0.7}
                    stroke={isSelected ? '#ffffff' : 'transparent'}
                    strokeWidth={2}
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: i * 0.02 }}
                    whileHover={{ scale: 1.1 }}
                  />

                  {/* Hard/soft indicator */}
                  {node.type === 'hard' && (
                    <circle
                      cx={projected.x}
                      cy={projected.y}
                      r={radius * 0.4}
                      fill="white"
                      fillOpacity={0.8}
                    />
                  )}

                  {/* Satisfaction rate ring */}
                  <circle
                    cx={projected.x}
                    cy={projected.y}
                    r={radius + 3}
                    fill="none"
                    stroke={node.satisfactionRate > 0.9 ? '#22c55e' : node.satisfactionRate > 0.7 ? '#eab308' : '#ef4444'}
                    strokeWidth={2}
                    strokeDasharray={`${node.satisfactionRate * Math.PI * 2 * (radius + 3)} ${Math.PI * 2 * (radius + 3)}`}
                    transform={`rotate(-90 ${projected.x} ${projected.y})`}
                    strokeOpacity={0.8}
                  />

                  {/* Label */}
                  {(isSelected || isHovered) && (
                    <text
                      x={projected.x}
                      y={projected.y + radius + 15}
                      textAnchor="middle"
                      fontSize="11"
                      fill="white"
                      className="pointer-events-none"
                    >
                      {node.name}
                    </text>
                  )}
                </g>
              );
            })}
          </g>
        </svg>

        {/* Legend */}
        <div className="absolute bottom-4 left-4 bg-slate-900/90 backdrop-blur rounded-lg p-3 text-xs space-y-2">
          <div className="text-slate-400 font-medium mb-2">Constraint Categories</div>
          {Object.entries(CONSTRAINT_CATEGORY_COLORS).map(([category, color]) => (
            <div key={category} className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
              <span className="text-slate-300 capitalize">{category}</span>
            </div>
          ))}
          <div className="border-t border-slate-700 mt-2 pt-2">
            <div className="text-slate-400 font-medium mb-2">Coupling Types</div>
            {Object.entries(COUPLING_TYPE_COLORS).map(([type, color]) => (
              <div key={type} className="flex items-center gap-2">
                <span className="w-4 h-0.5 rounded" style={{ backgroundColor: color }} />
                <span className="text-slate-300 capitalize">{type}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Selected constraint details */}
        {selectedConstraintId && (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="absolute top-4 right-4 bg-slate-900/90 backdrop-blur rounded-lg p-4 w-64"
          >
            {(() => {
              const node = data.constraints.find(c => c.constraintId === selectedConstraintId);
              if (!node) return null;

              return (
                <>
                  <div className="flex items-center gap-2 mb-3">
                    <span
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: CONSTRAINT_CATEGORY_COLORS[node.category] }}
                    />
                    <span className="text-white font-medium">{node.name}</span>
                  </div>

                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between">
                      <span className="text-slate-400">Type</span>
                      <span className={node.type === 'hard' ? 'text-red-400' : 'text-yellow-400'}>
                        {node.type.toUpperCase()}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Category</span>
                      <span className="text-slate-300 capitalize">{node.category}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Weight</span>
                      <span className="text-slate-300">{(node.weight * 100).toFixed(0)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Satisfaction</span>
                      <span className={
                        node.satisfactionRate > 0.9 ? 'text-emerald-400' :
                        node.satisfactionRate > 0.7 ? 'text-yellow-400' : 'text-red-400'
                      }>
                        {(node.satisfactionRate * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Violations</span>
                      <span className={node.violations > 0 ? 'text-red-400' : 'text-emerald-400'}>
                        {node.violations}
                      </span>
                    </div>
                  </div>

                  {selectedCouplings.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-slate-700">
                      <div className="text-slate-400 text-xs mb-2">
                        Coupled with ({selectedCouplings.length})
                      </div>
                      <div className="space-y-1 max-h-24 overflow-y-auto">
                        {selectedCouplings.map(coupling => {
                          const otherId = coupling.source === selectedConstraintId ? coupling.target : coupling.source;
                          const other = data.constraints.find(c => c.constraintId === otherId);

                          return (
                            <div
                              key={otherId}
                              className="flex items-center gap-2 text-xs"
                            >
                              <span
                                className="w-2 h-2 rounded-full"
                                style={{ backgroundColor: COUPLING_TYPE_COLORS[coupling.type] }}
                              />
                              <span className="text-slate-300 flex-1 truncate">
                                {other?.name || otherId}
                              </span>
                              <span className={
                                coupling.strength > 0 ? 'text-emerald-400' : 'text-red-400'
                              }>
                                {coupling.strength > 0 ? '+' : ''}{coupling.strength.toFixed(2)}
                              </span>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </>
              );
            })()}
          </motion.div>
        )}

        {/* View controls */}
        <div className="absolute bottom-4 right-4 flex items-center gap-2">
          <button
            onClick={() => setViewAngle({ theta: 0, phi: 0 })}
            className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-sm"
          >
            Reset View
          </button>
          <button
            onClick={() => setZoom(prev => Math.min(3, prev + 0.2))}
            className="w-8 h-8 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded flex items-center justify-center"
          >
            +
          </button>
          <button
            onClick={() => setZoom(prev => Math.max(0.5, prev - 0.2))}
            className="w-8 h-8 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded flex items-center justify-center"
          >
            −
          </button>
        </div>
      </div>
    </div>
  );
}

export default ConstraintCouplingView;
