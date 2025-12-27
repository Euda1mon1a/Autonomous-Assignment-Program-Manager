/**
 * Holographic Constraint Manifold Renderer
 *
 * A 3D visualization component that projects N-dimensional constraint data
 * into an interactive 3D space for multi-spectral observation.
 *
 * The "holographic" metaphor enables viewing:
 * - Multiple wavelengths (constraint types) simultaneously
 * - Spectral layers (quantum, temporal, evolutionary, etc.)
 * - Constraint tensions and correlations as spatial relationships
 *
 * Technical implementation:
 * - Canvas-based 3D rendering with isometric projection
 * - Optional Three.js/React Three Fiber for enhanced WebGL rendering
 * - WebXR foundation for immersive VR viewing
 */

"use client";

import React, {
  useRef,
  useEffect,
  useState,
  useMemo,
  useCallback,
} from "react";
import { format } from "date-fns";

import {
  ManifoldPoint,
  HolographicDataset,
  SpectralLayer,
  ConstraintType,
  LayerVisibility,
  ConstraintVisibility,
  CameraState,
  CONSTRAINT_COLORS,
  LAYER_COLORS,
} from "./types";
import {
  useHolographicData,
  useHolographicState,
  useFilteredManifoldPoints,
  useAnimationFrame,
  usePointInteraction,
} from "./hooks";

// ============================================================================
// Constants
// ============================================================================

const POINT_BASE_SIZE = 8;
const CAMERA_SPEED = 0.01;
const ZOOM_SPEED = 0.1;
const WORLD_SCALE = 30; // Scale factor for 3D projection

// Color helper
function rgbToHex(r: number, g: number, b: number): string {
  const toHex = (n: number) =>
    Math.round(Math.min(255, Math.max(0, n * 255)))
      .toString(16)
      .padStart(2, "0");
  return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
}

function hexToRgb(hex: string): [number, number, number] {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  if (!result) return [1, 1, 1];
  return [
    parseInt(result[1], 16) / 255,
    parseInt(result[2], 16) / 255,
    parseInt(result[3], 16) / 255,
  ];
}

// ============================================================================
// 3D Projection Utilities
// ============================================================================

interface Point3D {
  x: number;
  y: number;
  z: number;
}

interface Point2D {
  x: number;
  y: number;
}

interface Camera3D {
  position: Point3D;
  rotation: { yaw: number; pitch: number };
  fov: number;
  zoom: number;
}

/**
 * Project 3D point to 2D screen coordinates using perspective projection
 */
function project3DTo2D(
  point: Point3D,
  camera: Camera3D,
  canvasWidth: number,
  canvasHeight: number
): Point2D & { depth: number; scale: number } {
  // Apply camera rotation (simplified)
  const cosYaw = Math.cos(camera.rotation.yaw);
  const sinYaw = Math.sin(camera.rotation.yaw);
  const cosPitch = Math.cos(camera.rotation.pitch);
  const sinPitch = Math.sin(camera.rotation.pitch);

  // Translate relative to camera
  let dx = point.x - camera.position.x;
  let dy = point.y - camera.position.y;
  let dz = point.z - camera.position.z;

  // Rotate around Y axis (yaw)
  const rotX = dx * cosYaw - dz * sinYaw;
  const rotZ = dx * sinYaw + dz * cosYaw;
  dx = rotX;
  dz = rotZ;

  // Rotate around X axis (pitch)
  const rotY = dy * cosPitch - dz * sinPitch;
  const rotZ2 = dy * sinPitch + dz * cosPitch;
  dy = rotY;
  dz = rotZ2;

  // Prevent division by zero and points behind camera
  const depth = Math.max(dz, 0.1);

  // Perspective projection
  const focalLength = canvasHeight / (2 * Math.tan((camera.fov * Math.PI) / 360));
  const scale = (focalLength / depth) * camera.zoom;

  const screenX = canvasWidth / 2 + dx * scale;
  const screenY = canvasHeight / 2 - dy * scale;

  return { x: screenX, y: screenY, depth, scale };
}

/**
 * Draw a 3D point as a glowing sphere
 */
function drawPoint(
  ctx: CanvasRenderingContext2D,
  screenPos: Point2D & { scale: number },
  color: [number, number, number],
  opacity: number,
  size: number,
  glowIntensity: number,
  isHovered: boolean,
  isSelected: boolean,
  severity: number
): void {
  const radius = Math.max(2, size * screenPos.scale * 0.5);
  const hexColor = rgbToHex(color[0], color[1], color[2]);

  // Draw glow
  if (glowIntensity > 0 || isSelected) {
    const gradient = ctx.createRadialGradient(
      screenPos.x,
      screenPos.y,
      0,
      screenPos.x,
      screenPos.y,
      radius * 3
    );

    const glowColor =
      severity > 0.8
        ? "rgba(255, 80, 80, 0.4)"
        : `rgba(${color[0] * 255}, ${color[1] * 255}, ${color[2] * 255}, ${glowIntensity * 0.3})`;

    gradient.addColorStop(0, glowColor);
    gradient.addColorStop(1, "transparent");

    ctx.fillStyle = gradient;
    ctx.beginPath();
    ctx.arc(screenPos.x, screenPos.y, radius * 3, 0, Math.PI * 2);
    ctx.fill();
  }

  // Draw main point
  ctx.globalAlpha = opacity;
  ctx.fillStyle = hexColor;
  ctx.beginPath();
  ctx.arc(screenPos.x, screenPos.y, radius, 0, Math.PI * 2);
  ctx.fill();

  // Draw highlight
  const highlightGradient = ctx.createRadialGradient(
    screenPos.x - radius * 0.3,
    screenPos.y - radius * 0.3,
    0,
    screenPos.x,
    screenPos.y,
    radius
  );
  highlightGradient.addColorStop(0, "rgba(255, 255, 255, 0.4)");
  highlightGradient.addColorStop(1, "transparent");
  ctx.fillStyle = highlightGradient;
  ctx.fill();

  // Selection/hover ring
  if (isSelected) {
    ctx.strokeStyle = "#ffffff";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(screenPos.x, screenPos.y, radius + 4, 0, Math.PI * 2);
    ctx.stroke();
  } else if (isHovered) {
    ctx.strokeStyle = "rgba(255, 255, 255, 0.6)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.arc(screenPos.x, screenPos.y, radius + 2, 0, Math.PI * 2);
    ctx.stroke();
  }

  ctx.globalAlpha = 1;
}

/**
 * Draw grid plane
 */
function drawGrid(
  ctx: CanvasRenderingContext2D,
  camera: Camera3D,
  canvasWidth: number,
  canvasHeight: number,
  gridSize: number = 10,
  gridSpacing: number = 1
): void {
  ctx.strokeStyle = "rgba(60, 80, 120, 0.2)";
  ctx.lineWidth = 0.5;

  const halfSize = gridSize / 2;

  // Draw grid lines along X
  for (let i = -halfSize; i <= halfSize; i += gridSpacing) {
    const start = project3DTo2D(
      { x: i, y: -halfSize, z: 0 },
      camera,
      canvasWidth,
      canvasHeight
    );
    const end = project3DTo2D(
      { x: i, y: halfSize, z: 0 },
      camera,
      canvasWidth,
      canvasHeight
    );

    if (start.depth > 0 && end.depth > 0) {
      ctx.beginPath();
      ctx.moveTo(start.x, start.y);
      ctx.lineTo(end.x, end.y);
      ctx.stroke();
    }
  }

  // Draw grid lines along Y
  for (let i = -halfSize; i <= halfSize; i += gridSpacing) {
    const start = project3DTo2D(
      { x: -halfSize, y: i, z: 0 },
      camera,
      canvasWidth,
      canvasHeight
    );
    const end = project3DTo2D(
      { x: halfSize, y: i, z: 0 },
      camera,
      canvasWidth,
      canvasHeight
    );

    if (start.depth > 0 && end.depth > 0) {
      ctx.beginPath();
      ctx.moveTo(start.x, start.y);
      ctx.lineTo(end.x, end.y);
      ctx.stroke();
    }
  }
}

/**
 * Draw axis indicators
 */
function drawAxes(
  ctx: CanvasRenderingContext2D,
  camera: Camera3D,
  canvasWidth: number,
  canvasHeight: number,
  axisLength: number = 3
): void {
  const origin = project3DTo2D({ x: 0, y: 0, z: 0 }, camera, canvasWidth, canvasHeight);

  // X axis (red)
  const xEnd = project3DTo2D({ x: axisLength, y: 0, z: 0 }, camera, canvasWidth, canvasHeight);
  if (origin.depth > 0 && xEnd.depth > 0) {
    ctx.strokeStyle = "#ff4444";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(origin.x, origin.y);
    ctx.lineTo(xEnd.x, xEnd.y);
    ctx.stroke();
  }

  // Y axis (green)
  const yEnd = project3DTo2D({ x: 0, y: axisLength, z: 0 }, camera, canvasWidth, canvasHeight);
  if (origin.depth > 0 && yEnd.depth > 0) {
    ctx.strokeStyle = "#44ff44";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(origin.x, origin.y);
    ctx.lineTo(yEnd.x, yEnd.y);
    ctx.stroke();
  }

  // Z axis (blue)
  const zEnd = project3DTo2D({ x: 0, y: 0, z: axisLength }, camera, canvasWidth, canvasHeight);
  if (origin.depth > 0 && zEnd.depth > 0) {
    ctx.strokeStyle = "#4444ff";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(origin.x, origin.y);
    ctx.lineTo(zEnd.x, zEnd.y);
    ctx.stroke();
  }
}

// ============================================================================
// Main Component Props
// ============================================================================

interface HolographicManifoldProps {
  /** Initial date range start */
  startDate?: Date;
  /** Initial date range end */
  endDate?: Date;
  /** Callback when a point is clicked */
  onPointClick?: (point: ManifoldPoint) => void;
  /** Callback when a point is hovered */
  onPointHover?: (point: ManifoldPoint | null) => void;
  /** Use mock data for development */
  useMockData?: boolean;
  /** Custom class name */
  className?: string;
  /** Show controls panel */
  showControls?: boolean;
  /** Show legend panel */
  showLegend?: boolean;
  /** Show statistics panel */
  showStats?: boolean;
}

// ============================================================================
// Main Component
// ============================================================================

export function HolographicManifold({
  startDate = new Date(),
  endDate = new Date(Date.now() + 14 * 24 * 60 * 60 * 1000),
  onPointClick,
  onPointHover,
  useMockData = true,
  className = "",
  showControls = true,
  showLegend = true,
  showStats = true,
}: HolographicManifoldProps): JSX.Element {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Data and state hooks
  const { data, isLoading, error, refetch } = useHolographicData({
    startDate: format(startDate, "yyyy-MM-dd"),
    endDate: format(endDate, "yyyy-MM-dd"),
    useMockData,
  });

  const {
    state,
    toggleLayer,
    toggleConstraint,
    selectPoint,
    hoverPoint,
    setAnimating,
    setAnimationSpeed,
    setAllLayersVisible,
    setAllConstraintsVisible,
  } = useHolographicState();

  const filteredPoints = useFilteredManifoldPoints(
    data?.manifoldPoints,
    state.layerVisibility,
    state.constraintVisibility
  );

  const { selectedPoint, hoveredPoint } = usePointInteraction(filteredPoints);

  // Camera state
  const [camera, setCamera] = useState<Camera3D>({
    position: { x: 0, y: 0, z: 15 },
    rotation: { yaw: 0.3, pitch: 0.2 },
    fov: 60,
    zoom: 1,
  });

  // Interaction state
  const [isDragging, setIsDragging] = useState(false);
  const [lastMouse, setLastMouse] = useState({ x: 0, y: 0 });
  const [animationTime, setAnimationTime] = useState(0);

  // Canvas resize handler
  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        canvas.width = width * window.devicePixelRatio;
        canvas.height = height * window.devicePixelRatio;
        canvas.style.width = `${width}px`;
        canvas.style.height = `${height}px`;
      }
    });

    resizeObserver.observe(container);
    return () => resizeObserver.disconnect();
  }, []);

  // Animation loop
  useAnimationFrame(
    (deltaTime) => {
      if (state.isAnimating) {
        setAnimationTime((t) => t + deltaTime * state.animationSpeed);

        // Auto-rotate camera slowly
        setCamera((prev) => ({
          ...prev,
          rotation: {
            ...prev.rotation,
            yaw: prev.rotation.yaw + deltaTime * 0.05 * state.animationSpeed,
          },
        }));
      }
    },
    state.isAnimating
  );

  // Render loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;

    // Clear with dark background
    ctx.fillStyle = "#0a0a14";
    ctx.fillRect(0, 0, width, height);

    // Draw background nebula effect
    const gradient = ctx.createRadialGradient(
      width / 2,
      height / 2,
      0,
      width / 2,
      height / 2,
      Math.max(width, height) / 2
    );
    gradient.addColorStop(0, "rgba(30, 40, 80, 0.3)");
    gradient.addColorStop(0.5, "rgba(20, 25, 50, 0.2)");
    gradient.addColorStop(1, "transparent");
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, width, height);

    // Draw grid
    drawGrid(ctx, camera, width, height, 20, 2);

    // Draw axes
    drawAxes(ctx, camera, width, height, 5);

    // Sort points by depth for proper rendering order
    const pointsWithScreen = filteredPoints.map((point) => {
      const pos3D: Point3D = {
        x: point.position.x,
        y: point.position.y,
        z: point.position.z,
      };
      const screenPos = project3DTo2D(pos3D, camera, width, height);
      return { point, screenPos };
    });

    pointsWithScreen.sort((a, b) => b.screenPos.depth - a.screenPos.depth);

    // Draw points
    for (const { point, screenPos } of pointsWithScreen) {
      if (screenPos.depth <= 0) continue;

      // Pulse effect for animated points
      let opacity = point.visual.opacity;
      let size = point.visual.size * POINT_BASE_SIZE;

      if (state.isAnimating && point.severity > 0.5) {
        const pulse = Math.sin(animationTime * 3 + point.severity * 10) * 0.2;
        size *= 1 + pulse;
      }

      const isHovered = hoveredPoint?.id === point.id || state.hoveredPointId === point.id;
      const isSelected =
        selectedPoint?.id === point.id || state.selectedPointId === point.id;

      drawPoint(
        ctx,
        screenPos,
        point.visual.color,
        opacity,
        size,
        point.visual.glowIntensity,
        isHovered,
        isSelected,
        point.severity
      );
    }
  }, [filteredPoints, camera, animationTime, state, hoveredPoint, selectedPoint]);

  // Mouse handlers
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    setIsDragging(true);
    setLastMouse({ x: e.clientX, y: e.clientY });
  }, []);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  const handleMouseMove = useCallback(
    (e: React.MouseEvent) => {
      const canvas = canvasRef.current;
      if (!canvas) return;

      if (isDragging) {
        const dx = e.clientX - lastMouse.x;
        const dy = e.clientY - lastMouse.y;

        if (e.shiftKey) {
          // Pan camera
          setCamera((prev) => ({
            ...prev,
            position: {
              x: prev.position.x - dx * 0.02,
              y: prev.position.y + dy * 0.02,
              z: prev.position.z,
            },
          }));
        } else {
          // Rotate camera
          setCamera((prev) => ({
            ...prev,
            rotation: {
              yaw: prev.rotation.yaw + dx * CAMERA_SPEED,
              pitch: Math.max(
                -Math.PI / 2.5,
                Math.min(Math.PI / 2.5, prev.rotation.pitch + dy * CAMERA_SPEED)
              ),
            },
          }));
        }

        setLastMouse({ x: e.clientX, y: e.clientY });
      } else {
        // Hit testing for hover
        const rect = canvas.getBoundingClientRect();
        const mouseX =
          (e.clientX - rect.left) * window.devicePixelRatio;
        const mouseY =
          (e.clientY - rect.top) * window.devicePixelRatio;

        let closestPoint: ManifoldPoint | null = null;
        let closestDist = Infinity;

        for (const point of filteredPoints) {
          const pos3D: Point3D = {
            x: point.position.x,
            y: point.position.y,
            z: point.position.z,
          };
          const screenPos = project3DTo2D(
            pos3D,
            camera,
            canvas.width,
            canvas.height
          );

          if (screenPos.depth <= 0) continue;

          const dist = Math.sqrt(
            (mouseX - screenPos.x) ** 2 + (mouseY - screenPos.y) ** 2
          );
          const hitRadius =
            point.visual.size * POINT_BASE_SIZE * screenPos.scale * 0.5 + 5;

          if (dist < hitRadius && dist < closestDist) {
            closestDist = dist;
            closestPoint = point;
          }
        }

        if (closestPoint?.id !== state.hoveredPointId) {
          hoverPoint(closestPoint?.id || null);
          onPointHover?.(closestPoint);
        }
      }
    },
    [
      isDragging,
      lastMouse,
      camera,
      filteredPoints,
      state.hoveredPointId,
      hoverPoint,
      onPointHover,
    ]
  );

  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? 1 + ZOOM_SPEED : 1 - ZOOM_SPEED;
    setCamera((prev) => ({
      ...prev,
      zoom: Math.max(0.2, Math.min(5, prev.zoom * delta)),
    }));
  }, []);

  const handleClick = useCallback(() => {
    if (state.hoveredPointId) {
      selectPoint(state.hoveredPointId);
      const point = filteredPoints.find((p) => p.id === state.hoveredPointId);
      if (point) {
        onPointClick?.(point);
      }
    } else {
      selectPoint(null);
    }
  }, [state.hoveredPointId, selectPoint, filteredPoints, onPointClick]);

  // Reset camera
  const resetCamera = useCallback(() => {
    setCamera({
      position: { x: 0, y: 0, z: 15 },
      rotation: { yaw: 0.3, pitch: 0.2 },
      fov: 60,
      zoom: 1,
    });
  }, []);

  // Loading state
  if (isLoading) {
    return (
      <div
        className={`flex items-center justify-center h-[600px] bg-gray-900 rounded-lg ${className}`}
      >
        <div className="text-center">
          <div className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full mx-auto mb-4" />
          <div className="text-white">Loading holographic manifold...</div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div
        className={`flex items-center justify-center h-[600px] bg-gray-900 rounded-lg ${className}`}
      >
        <div className="text-center">
          <div className="text-red-500 text-lg mb-2">
            Error loading holographic data
          </div>
          <button
            onClick={() => refetch()}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const currentPoint =
    filteredPoints.find((p) => p.id === state.hoveredPointId) ||
    filteredPoints.find((p) => p.id === state.selectedPointId);

  return (
    <div
      ref={containerRef}
      className={`relative w-full h-[600px] bg-gray-900 rounded-lg overflow-hidden ${className}`}
    >
      {/* Controls Panel */}
      {showControls && (
        <div className="absolute top-4 left-4 z-10 bg-gray-800/90 p-4 rounded-lg text-white text-sm max-w-xs">
          <h3 className="font-bold mb-3 text-blue-400">Holographic Manifold</h3>

          <div className="space-y-2 text-gray-300 text-xs mb-4">
            <p>Drag: Rotate view</p>
            <p>Shift+Drag: Pan</p>
            <p>Scroll: Zoom</p>
            <p>Click: Select point</p>
          </div>

          <div className="flex gap-2 mb-4">
            <button
              onClick={resetCamera}
              className="px-2 py-1 bg-gray-700 rounded text-xs hover:bg-gray-600"
            >
              Reset View
            </button>
            <button
              onClick={() => setAnimating(!state.isAnimating)}
              className={`px-2 py-1 rounded text-xs ${
                state.isAnimating
                  ? "bg-blue-600 hover:bg-blue-500"
                  : "bg-gray-700 hover:bg-gray-600"
              }`}
            >
              {state.isAnimating ? "Pause" : "Animate"}
            </button>
          </div>

          {/* Layer toggles */}
          <div className="border-t border-gray-700 pt-3">
            <div className="flex justify-between items-center mb-2">
              <span className="text-gray-400 text-xs">Spectral Layers</span>
              <div className="flex gap-1">
                <button
                  onClick={() => setAllLayersVisible(true)}
                  className="text-xs text-blue-400 hover:text-blue-300"
                >
                  All
                </button>
                <span className="text-gray-600">|</span>
                <button
                  onClick={() => setAllLayersVisible(false)}
                  className="text-xs text-gray-400 hover:text-gray-300"
                >
                  None
                </button>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-1">
              {(Object.keys(state.layerVisibility) as SpectralLayer[]).map(
                (layer) => (
                  <button
                    key={layer}
                    onClick={() => toggleLayer(layer)}
                    className={`px-2 py-1 rounded text-xs text-left ${
                      state.layerVisibility[layer]
                        ? "bg-blue-600/50 text-white"
                        : "bg-gray-700/50 text-gray-500"
                    }`}
                  >
                    {layer.charAt(0).toUpperCase() + layer.slice(0, 4)}
                  </button>
                )
              )}
            </div>
          </div>
        </div>
      )}

      {/* Legend Panel */}
      {showLegend && (
        <div className="absolute top-4 right-4 z-10 bg-gray-800/90 p-4 rounded-lg text-white text-sm">
          <h4 className="font-bold mb-3 text-purple-400">Constraint Types</h4>
          <div className="space-y-1">
            {(Object.entries(CONSTRAINT_COLORS) as [ConstraintType, [number, number, number]][]).map(
              ([type, color]) => (
                <button
                  key={type}
                  onClick={() => toggleConstraint(type)}
                  className={`flex items-center gap-2 w-full px-2 py-1 rounded text-xs ${
                    state.constraintVisibility[type]
                      ? "hover:bg-gray-700/50"
                      : "opacity-40"
                  }`}
                >
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: rgbToHex(color[0], color[1], color[2]) }}
                  />
                  <span className="capitalize">{type}</span>
                </button>
              )
            )}
          </div>
        </div>
      )}

      {/* Stats Panel */}
      {showStats && data && (
        <div className="absolute bottom-4 left-4 z-10 bg-gray-800/90 p-3 rounded-lg text-white text-sm">
          <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
            <span className="text-gray-400">Total Constraints:</span>
            <span>{data.globalStats.totalUniqueConstraints}</span>
            <span className="text-gray-400">Visible Points:</span>
            <span>{filteredPoints.length}</span>
            <span className="text-gray-400">Health Score:</span>
            <span
              className={
                data.globalStats.overallHealth > 0.7
                  ? "text-green-400"
                  : data.globalStats.overallHealth > 0.4
                  ? "text-yellow-400"
                  : "text-red-400"
              }
            >
              {(data.globalStats.overallHealth * 100).toFixed(1)}%
            </span>
            <span className="text-gray-400">Projection:</span>
            <span className="uppercase">{data.globalStats.projectionMethod}</span>
          </div>
        </div>
      )}

      {/* Point Tooltip */}
      {currentPoint && (
        <div className="absolute bottom-4 right-4 z-10 bg-gray-800/95 p-4 rounded-lg text-white text-sm max-w-xs">
          <div className="flex items-start gap-2">
            <div
              className="w-4 h-4 rounded-full mt-0.5 flex-shrink-0"
              style={{
                backgroundColor: rgbToHex(
                  currentPoint.visual.color[0],
                  currentPoint.visual.color[1],
                  currentPoint.visual.color[2]
                ),
              }}
            />
            <div>
              <div className="font-bold text-white">{currentPoint.label}</div>
              <div className="text-gray-400 text-xs mt-1">
                <span className="capitalize">{currentPoint.type}</span>
                {" • "}
                <span className="capitalize">{currentPoint.layer}</span>
              </div>
              <div className="mt-2 grid grid-cols-2 gap-x-3 gap-y-1 text-xs">
                <span className="text-gray-500">Severity:</span>
                <span
                  className={
                    currentPoint.severity > 0.8
                      ? "text-red-400"
                      : currentPoint.severity > 0.5
                      ? "text-yellow-400"
                      : "text-green-400"
                  }
                >
                  {(currentPoint.severity * 100).toFixed(0)}%
                </span>
                <span className="text-gray-500">Status:</span>
                <span
                  className={
                    currentPoint.status.isCritical
                      ? "text-red-400"
                      : currentPoint.status.isViolated
                      ? "text-yellow-400"
                      : "text-green-400"
                  }
                >
                  {currentPoint.status.isCritical
                    ? "Critical"
                    : currentPoint.status.isViolated
                    ? "Violated"
                    : "Satisfied"}
                </span>
                <span className="text-gray-500">Tension:</span>
                <span>{currentPoint.status.tension.toFixed(2)}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Main Canvas */}
      <canvas
        ref={canvasRef}
        className="w-full h-full cursor-grab active:cursor-grabbing"
        onMouseDown={handleMouseDown}
        onMouseUp={handleMouseUp}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseUp}
        onWheel={handleWheel}
        onClick={handleClick}
      />

      {/* Axis Legend */}
      <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 text-gray-500 text-xs flex gap-4">
        <span>
          <span className="text-red-400">X</span>: PC1
        </span>
        <span>
          <span className="text-green-400">Y</span>: PC2
        </span>
        <span>
          <span className="text-blue-400">Z</span>: PC3
        </span>
      </div>
    </div>
  );
}

export default HolographicManifold;
