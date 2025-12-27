/**
 * Layer Control Panel
 *
 * Advanced controls for toggling spectral layers and constraint types
 * with visual feedback and statistics per layer.
 */

"use client";

import React from "react";

import {
  SpectralLayer,
  ConstraintType,
  LayerVisibility,
  ConstraintVisibility,
  HolographicDataset,
  CONSTRAINT_COLORS,
  LAYER_COLORS,
} from "./types";

// ============================================================================
// Helper Functions
// ============================================================================

function rgbToHex(r: number, g: number, b: number): string {
  const toHex = (n: number) =>
    Math.round(Math.min(255, Math.max(0, n * 255)))
      .toString(16)
      .padStart(2, "0");
  return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
}

// ============================================================================
// Layer Descriptions
// ============================================================================

const LAYER_DESCRIPTIONS: Record<SpectralLayer, string> = {
  quantum: "Probabilistic constraint states and superposition",
  temporal: "Time-evolving schedule dynamics",
  topological: "Structural constraint relationships",
  spectral: "Frequency-domain patterns and oscillations",
  evolutionary: "Game-theoretic strategy evolution",
  gravitational: "Constraint attraction/repulsion fields",
  phase: "Schedule state transitions",
  thermodynamic: "Energy and entropy of schedules",
};

const CONSTRAINT_DESCRIPTIONS: Record<ConstraintType, string> = {
  acgme: "ACGME regulatory compliance (80-hour rule, supervision)",
  fairness: "Workload equity and distribution balance",
  fatigue: "Burnout risk and work intensity monitoring",
  temporal: "Time-based conflicts and sequencing",
  preference: "Individual preferences and requests",
  coverage: "Staffing requirements and coverage gaps",
  skill: "Credential and qualification requirements",
  custom: "User-defined custom constraints",
};

// ============================================================================
// Props
// ============================================================================

interface LayerControlPanelProps {
  layerVisibility: LayerVisibility;
  constraintVisibility: ConstraintVisibility;
  onToggleLayer: (layer: SpectralLayer) => void;
  onToggleConstraint: (type: ConstraintType) => void;
  onSetAllLayersVisible: (visible: boolean) => void;
  onSetAllConstraintsVisible: (visible: boolean) => void;
  data?: HolographicDataset;
  className?: string;
}

// ============================================================================
// Component
// ============================================================================

export function LayerControlPanel({
  layerVisibility,
  constraintVisibility,
  onToggleLayer,
  onToggleConstraint,
  onSetAllLayersVisible,
  onSetAllConstraintsVisible,
  data,
  className = "",
}: LayerControlPanelProps): JSX.Element {
  const layers = Object.keys(layerVisibility) as SpectralLayer[];
  const constraints = Object.keys(constraintVisibility) as ConstraintType[];

  const visibleLayerCount = layers.filter((l) => layerVisibility[l]).length;
  const visibleConstraintCount = constraints.filter(
    (c) => constraintVisibility[c]
  ).length;

  return (
    <div
      className={`bg-gray-900/95 rounded-lg p-4 text-white text-sm ${className}`}
    >
      {/* Spectral Layers Section */}
      <div className="mb-6">
        <div className="flex justify-between items-center mb-3">
          <h3 className="font-bold text-blue-400 flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-gradient-to-r from-purple-500 to-blue-500" />
            Spectral Layers
            <span className="text-gray-500 font-normal text-xs">
              ({visibleLayerCount}/{layers.length})
            </span>
          </h3>
          <div className="flex gap-2">
            <button
              onClick={() => onSetAllLayersVisible(true)}
              className="text-xs text-blue-400 hover:text-blue-300 px-2 py-0.5 rounded bg-blue-900/30"
            >
              Show All
            </button>
            <button
              onClick={() => onSetAllLayersVisible(false)}
              className="text-xs text-gray-400 hover:text-gray-300 px-2 py-0.5 rounded bg-gray-800/50"
            >
              Hide All
            </button>
          </div>
        </div>

        <div className="space-y-1">
          {layers.map((layer) => {
            const color = LAYER_COLORS[layer];
            const count = data?.globalStats.constraintsByLayer[layer] || 0;
            const isVisible = layerVisibility[layer];

            return (
              <button
                key={layer}
                onClick={() => onToggleLayer(layer)}
                className={`w-full flex items-center gap-3 px-3 py-2 rounded transition-all ${
                  isVisible
                    ? "bg-gray-800/80 hover:bg-gray-700/80"
                    : "bg-gray-900/50 opacity-50 hover:opacity-70"
                }`}
              >
                <div className="relative">
                  <div
                    className="w-4 h-4 rounded-full"
                    style={{
                      backgroundColor: rgbToHex(color[0], color[1], color[2]),
                      boxShadow: isVisible
                        ? `0 0 8px ${rgbToHex(color[0], color[1], color[2])}`
                        : "none",
                    }}
                  />
                  {isVisible && (
                    <div className="absolute inset-0 rounded-full animate-ping opacity-20"
                      style={{
                        backgroundColor: rgbToHex(color[0], color[1], color[2]),
                      }}
                    />
                  )}
                </div>
                <div className="flex-1 text-left">
                  <div className="capitalize text-sm">{layer}</div>
                  <div className="text-xs text-gray-500 truncate">
                    {LAYER_DESCRIPTIONS[layer]}
                  </div>
                </div>
                <div className="text-xs text-gray-400 tabular-nums">
                  {count > 0 && `${count}`}
                </div>
                <div
                  className={`w-5 h-5 rounded flex items-center justify-center ${
                    isVisible ? "bg-blue-600" : "bg-gray-700"
                  }`}
                >
                  {isVisible && (
                    <svg
                      className="w-3 h-3"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                  )}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Constraint Types Section */}
      <div>
        <div className="flex justify-between items-center mb-3">
          <h3 className="font-bold text-purple-400 flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-gradient-to-r from-red-500 to-yellow-500" />
            Constraint Types
            <span className="text-gray-500 font-normal text-xs">
              ({visibleConstraintCount}/{constraints.length})
            </span>
          </h3>
          <div className="flex gap-2">
            <button
              onClick={() => onSetAllConstraintsVisible(true)}
              className="text-xs text-purple-400 hover:text-purple-300 px-2 py-0.5 rounded bg-purple-900/30"
            >
              Show All
            </button>
            <button
              onClick={() => onSetAllConstraintsVisible(false)}
              className="text-xs text-gray-400 hover:text-gray-300 px-2 py-0.5 rounded bg-gray-800/50"
            >
              Hide All
            </button>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-1">
          {constraints.map((type) => {
            const color = CONSTRAINT_COLORS[type];
            const count = data?.globalStats.constraintsByType[type] || 0;
            const isVisible = constraintVisibility[type];

            return (
              <button
                key={type}
                onClick={() => onToggleConstraint(type)}
                className={`flex items-center gap-2 px-2 py-1.5 rounded transition-all ${
                  isVisible
                    ? "bg-gray-800/80 hover:bg-gray-700/80"
                    : "bg-gray-900/50 opacity-50 hover:opacity-70"
                }`}
                title={CONSTRAINT_DESCRIPTIONS[type]}
              >
                <div
                  className="w-3 h-3 rounded-full flex-shrink-0"
                  style={{
                    backgroundColor: rgbToHex(color[0], color[1], color[2]),
                    boxShadow: isVisible
                      ? `0 0 6px ${rgbToHex(color[0], color[1], color[2])}`
                      : "none",
                  }}
                />
                <span className="capitalize text-xs truncate">{type}</span>
                {count > 0 && (
                  <span className="text-xs text-gray-500 ml-auto">{count}</span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Statistics Summary */}
      {data && (
        <div className="mt-4 pt-4 border-t border-gray-800">
          <h4 className="text-xs text-gray-500 mb-2">Dataset Summary</h4>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="bg-gray-800/50 rounded p-2">
              <div className="text-gray-400">Total</div>
              <div className="text-lg font-bold">
                {data.globalStats.totalUniqueConstraints}
              </div>
            </div>
            <div className="bg-gray-800/50 rounded p-2">
              <div className="text-gray-400">Health</div>
              <div
                className={`text-lg font-bold ${
                  data.globalStats.overallHealth > 0.7
                    ? "text-green-400"
                    : data.globalStats.overallHealth > 0.4
                    ? "text-yellow-400"
                    : "text-red-400"
                }`}
              >
                {(data.globalStats.overallHealth * 100).toFixed(0)}%
              </div>
            </div>
            <div className="bg-gray-800/50 rounded p-2">
              <div className="text-gray-400">Projection</div>
              <div className="text-sm font-bold uppercase">
                {data.globalStats.projectionMethod}
              </div>
            </div>
            <div className="bg-gray-800/50 rounded p-2">
              <div className="text-gray-400">Quality</div>
              <div className="text-sm font-bold">
                {(data.globalStats.projectionQuality * 100).toFixed(0)}%
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default LayerControlPanel;
