import React, { useState, useRef, useEffect, useMemo } from 'react';
import { Canvas, useFrame, useThree, ThreeEvent } from '@react-three/fiber';
import { OrbitControls, Text, Html, Stars, Grid } from '@react-three/drei';
import { useSpring, animated, config } from '@react-spring/three';
import * as THREE from 'three';

// --- Types ---

interface Position {
  x: number;
  y: number;
  z: number;
}

interface VoxelData {
  id: string;
  position: Position;
  person: string;
  activity: string;
  color: string;
  isConflict: boolean;
  conflictStackIndex?: number; // Order in the stack for 2D view
}

interface AnimatedVoxelProps {
  data: VoxelData;
  is3D: boolean;
  isSelected: boolean;
  onClick: (e: ThreeEvent<MouseEvent>) => void;
  onHover: (e: ThreeEvent<PointerEvent>) => void;
}

// --- Data ---

const AXIS_LABELS = {
  x: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
  y: ["Dr. Smith", "Dr. Jones", "Dr. Lee", "Dr. Patel", "Dr. Garcia"],
  z: ["Clinic", "Inpatient", "Procedures", "Call", "Leave"]
};

const RAW_VOXELS: VoxelData[] = [
  // Week 1 - Dense Monday
  { id: '1', position: { x: 0, y: 0, z: 0 }, person: "Dr. Smith", activity: "Clinic", color: "#3B82F6", isConflict: false },
  { id: '2', position: { x: 0, y: 1, z: 0 }, person: "Dr. Jones", activity: "Clinic", color: "#3B82F6", isConflict: false },
  { id: '3', position: { x: 0, y: 2, z: 1 }, person: "Dr. Lee", activity: "Inpatient", color: "#8B5CF6", isConflict: false },
  { id: '4', position: { x: 0, y: 3, z: 1 }, person: "Dr. Patel", activity: "Inpatient", color: "#8B5CF6", isConflict: false },
  { id: '5', position: { x: 0, y: 4, z: 2 }, person: "Dr. Garcia", activity: "Procedures", color: "#EF4444", isConflict: false },

  // Tuesday - Normal
  { id: '6', position: { x: 1, y: 0, z: 1 }, person: "Dr. Smith", activity: "Inpatient", color: "#8B5CF6", isConflict: false },
  { id: '7', position: { x: 1, y: 1, z: 2 }, person: "Dr. Jones", activity: "Procedures", color: "#EF4444", isConflict: false },
  { id: '8', position: { x: 1, y: 2, z: 0 }, person: "Dr. Lee", activity: "Clinic", color: "#3B82F6", isConflict: false },
  { id: '9', position: { x: 1, y: 3, z: 3 }, person: "Dr. Patel", activity: "Call", color: "#F97316", isConflict: false },

  // Wednesday - CONFLICT DAY
  { id: '10', position: { x: 2, y: 0, z: 0 }, person: "Dr. Smith", activity: "Clinic", color: "#3B82F6", isConflict: true },
  { id: '11', position: { x: 2, y: 0, z: 1 }, person: "Dr. Smith", activity: "Inpatient", color: "#8B5CF6", isConflict: true },
  { id: '12', position: { x: 2, y: 1, z: 0 }, person: "Dr. Jones", activity: "Clinic", color: "#3B82F6", isConflict: false },
  { id: '13', position: { x: 2, y: 2, z: 3 }, person: "Dr. Lee", activity: "Call", color: "#F97316", isConflict: false },
  { id: '14', position: { x: 2, y: 3, z: 2 }, person: "Dr. Patel", activity: "Procedures", color: "#EF4444", isConflict: false },
  { id: '15', position: { x: 2, y: 4, z: 1 }, person: "Dr. Garcia", activity: "Inpatient", color: "#8B5CF6", isConflict: false },

  // Thursday
  { id: '16', position: { x: 3, y: 0, z: 2 }, person: "Dr. Smith", activity: "Procedures", color: "#EF4444", isConflict: false },
  { id: '17', position: { x: 3, y: 1, z: 1 }, person: "Dr. Jones", activity: "Inpatient", color: "#8B5CF6", isConflict: false },
  { id: '18', position: { x: 3, y: 2, z: 0 }, person: "Dr. Lee", activity: "Clinic", color: "#3B82F6", isConflict: false },
  { id: '19', position: { x: 3, y: 4, z: 3 }, person: "Dr. Garcia", activity: "Call", color: "#F97316", isConflict: false },

  // Friday - Light day with leave
  { id: '20', position: { x: 4, y: 0, z: 4 }, person: "Dr. Smith", activity: "Leave", color: "#F59E0B", isConflict: false },
  { id: '21', position: { x: 4, y: 1, z: 0 }, person: "Dr. Jones", activity: "Clinic", color: "#3B82F6", isConflict: false },
  { id: '22', position: { x: 4, y: 3, z: 4 }, person: "Dr. Patel", activity: "Leave", color: "#F59E0B", isConflict: false },
  { id: '23', position: { x: 4, y: 4, z: 2 }, person: "Dr. Garcia", activity: "Procedures", color: "#EF4444", isConflict: false },

  // Saturday - Weekend call only
  { id: '24', position: { x: 5, y: 2, z: 3 }, person: "Dr. Lee", activity: "Call", color: "#F97316", isConflict: false },

  // Sunday - Weekend call only
  { id: '25', position: { x: 6, y: 0, z: 3 }, person: "Dr. Smith", activity: "Call", color: "#F97316", isConflict: false },
];

// Pre-process to calculate 2D stack indices
const TEST_VOXELS = (() => {
  const map = new Map<string, number>();
  return RAW_VOXELS.map(v => {
    const key = `${v.position.x}-${v.position.y}`;
    const count = map.get(key) || 0;
    map.set(key, count + 1);
    return { ...v, conflictStackIndex: count };
  });
})();

// --- Components ---

const GridSystem = ({ is3D }: { is3D: boolean }) => {
  return (
    <group>
      {/* Floor Grid */}
      <Grid
        position={[3, -0.5, 2]}
        args={[14, 10]}
        cellSize={1.1}
        cellThickness={0.5}
        cellColor="#334155"
        sectionSize={1.1 * 5}
        sectionThickness={1}
        sectionColor="#475569"
        fadeDistance={30}
        infiniteGrid={false}
      />

      {/* X Axis Labels (Days) */}
      {AXIS_LABELS.x.map((label, i) => (
        <Text
          key={`x-${i}`}
          position={[i * 1.1, -0.5, -1.5]}
          rotation={[-Math.PI / 4, 0, 0]}
          fontSize={0.3}
          color="#94a3b8"
          anchorX="center"
          anchorY="middle"
        >
          {label}
        </Text>
      ))}

      {/* Y Axis Labels (People) */}
      {AXIS_LABELS.y.map((label, i) => (
        <Text
          key={`y-${i}`}
          position={[-1.5, i * 1.1, 0]}
          rotation={[0, 0, 0]}
          fontSize={0.3}
          color="#94a3b8"
          anchorX="right"
          anchorY="middle"
        >
          {label}
        </Text>
      ))}

      {/* Z Axis Labels (Activities) - Only show in 3D mode clearly */}
      {is3D && AXIS_LABELS.z.map((label, i) => (
        <Text
          key={`z-${i}`}
          position={[-1, -0.5, i * 1.1]}
          rotation={[0, Math.PI / 4, 0]}
          fontSize={0.25}
          color="#64748b"
          anchorX="right"
          anchorY="middle"
        >
          {label}
        </Text>
      ))}
    </group>
  );
};

// Animated Voxel Component
const AnimatedVoxel: React.FC<AnimatedVoxelProps> = ({
  data,
  is3D,
  isSelected,
  onClick,
  onHover
}) => {
  const meshRef = useRef<THREE.Mesh>(null!);

  // Determine target position based on mode
  const targetPos = useMemo(() => {
    if (is3D) {
      // 3D Mode: True coordinates
      return [data.position.x * 1.1, data.position.y * 1.1, data.position.z * 1.1] as [number, number, number];
    } else {
      // 2D Mode: Stacked on X-Y plane (Z flattened)
      // Visual stack offset to show conflicts
      const stackOffset = (data.conflictStackIndex || 0) * 0.15;
      return [
        (data.position.x * 1.1) + stackOffset,
        (data.position.y * 1.1) - stackOffset, // Shift Y slightly down to show stack
        stackOffset * 0.5 // Minimal Z lift to avoid z-fighting
      ] as [number, number, number];
    }
  }, [is3D, data]);

  // Spring Physics
  const { pos, scale } = useSpring({
    pos: targetPos,
    scale: is3D ? 1 : 0.9,
    config: {
      mass: 1,
      tension: 180,
      friction: 12
    },
    // Stagger animation based on Z-layer for "Explosion" effect
    delay: is3D
      ? data.position.z * 50  // Outward: Inner layers first
      : (5 - data.position.z) * 50 // Inward: Outer layers first
  });

  // Conflict pulsing for 3D mode
  useFrame(({ clock }) => {
    if (meshRef.current && data.isConflict && is3D) {
      const t = clock.getElapsedTime();
      const pulse = 0.5 + Math.sin(t * 5) * 0.5;
      const material = meshRef.current.material as THREE.MeshStandardMaterial;
      if (material.emissive) {
         material.emissiveIntensity = 0.5 + pulse * 1.5;
      }
    }
  });

  return (
    <animated.mesh
      ref={meshRef}
      position={pos}
      scale={scale}
      onClick={onClick}
      onPointerOver={onHover}
      onPointerOut={(e) => onHover(e)}
    >
      <boxGeometry args={[0.85, 0.85, 0.85]} />
      <meshStandardMaterial
        color={data.isConflict && is3D ? "#EF4444" : data.color}
        emissive={data.isConflict && is3D ? "#7f1d1d" : "#000000"}
        roughness={0.2}
        metalness={0.1}
      />
      {isSelected && (
        <mesh>
          <boxGeometry args={[0.86, 0.86, 0.86]} />
          <meshBasicMaterial wireframe color="white" toneMapped={false} />
        </mesh>
      )}
    </animated.mesh>
  );
};

const Tooltip = ({ data }: { data: VoxelData }) => (
  <Html
    position={[
      data.position.x * 1.1,
      data.position.y * 1.1 + 0.5,
      data.position.z * 1.1
    ]}
    center
    zIndexRange={[100, 0]}
  >
    <div className="bg-slate-900/95 backdrop-blur text-white px-3 py-2 rounded-lg shadow-xl text-sm whitespace-nowrap border border-slate-700 pointer-events-none transform -translate-y-8 transition-opacity duration-200">
      <div className="font-bold text-base text-blue-100">{data.person}</div>
      <div className="flex items-center gap-2 mt-1">
        <span className="w-2 h-2 rounded-full" style={{ backgroundColor: data.color }} />
        <span className="text-slate-300">{data.activity}</span>
      </div>
      <div className="text-slate-500 text-xs mt-1 uppercase tracking-wider font-mono">
        {AXIS_LABELS.x[data.position.x]} • {AXIS_LABELS.z[data.position.z]}
      </div>
      {data.isConflict && (
        <div className="text-red-400 font-bold mt-2 flex items-center gap-1 text-xs border-t border-slate-700 pt-1">
          <span className="animate-pulse">⚠</span> SCHEDULING CONFLICT
        </div>
      )}
    </div>
  </Html>
);

// Camera animation component
const AnimatedCamera = ({ is3D }: { is3D: boolean }) => {
  const { camera } = useThree();

  // Spring for camera position and target
  useSpring({
    to: {
      pos: is3D ? [8, 8, 8] : [3, 2, 15], // 3D: Isometric, 2D: Front/Top hybrid
      target: is3D ? [2, 1, 2] : [3, 2, 0],
    },
    config: { mass: 1, tension: 120, friction: 14 },
    onChange: ({ value }) => {
      camera.position.set(value.pos[0], value.pos[1], value.pos[2]);
      camera.lookAt(value.target[0], value.target[1], value.target[2]);
    }
  });

  return null;
};

// --- Main App ---

export default function App() {
  const [is3D, setIs3D] = useState(false); // Start in 2D
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  const hoveredVoxel = TEST_VOXELS.find(v => v.id === hoveredId);

  return (
    <div className="w-full h-screen bg-[#0f172a] relative overflow-hidden font-sans selection:bg-blue-500/30">

      {/* Header */}
      <div className="absolute top-0 left-0 w-full p-6 z-10 pointer-events-none">
        <h1 className="text-2xl font-bold text-slate-100 tracking-tight flex items-center gap-2">
          <div className="w-3 h-3 bg-blue-500 rounded-full animate-pulse" />
          Voxel<span className="text-blue-500">Scheduler</span>
        </h1>
        <p className="text-slate-400 text-sm mt-1 ml-5">Autonomous Residency Program Manager</p>
      </div>

      {/* Controls & Legend */}
      <div className="absolute top-6 right-6 z-10 flex flex-col items-end gap-4 pointer-events-none">

        {/* Toggle Button */}
        <button
          onClick={() => setIs3D(!is3D)}
          className={`
            pointer-events-auto px-6 py-3 rounded-lg font-bold transition-all duration-300 shadow-xl border border-white/10
            flex items-center gap-3 group
            ${is3D
              ? 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-indigo-500/20'
              : 'bg-slate-700 hover:bg-slate-600 text-slate-200'
            }
          `}
        >
          <span className="text-xl">{is3D ? '📊' : '🧊'}</span>
          <span>{is3D ? 'Flatten to 2D' : 'Voxelize to 3D'}</span>
        </button>

        {/* Legend */}
        <div className="bg-slate-900/90 backdrop-blur-md p-4 rounded-xl border border-slate-700/50 shadow-2xl w-64 pointer-events-auto">
          <h4 className="font-bold text-slate-100 mb-3 text-sm uppercase tracking-wider">Activity Types</h4>
          <div className="space-y-2 mb-4">
            {['Clinic', 'Inpatient', 'Procedures', 'Call', 'Leave'].map((label) => {
               const color = TEST_VOXELS.find(v => v.activity === label)?.color || '#fff';
               return (
                <div key={label} className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded shadow-sm" style={{ backgroundColor: color }} />
                  <span className="text-slate-300 text-xs font-medium">{label}</span>
                </div>
              );
            })}
          </div>
          <div className="border-t border-slate-700/50 pt-3 text-[10px] text-slate-400">
             {is3D ? 'Rotate: Drag • Pan: Right Click' : '2D Mode: Pan & Zoom Only'}
          </div>
        </div>
      </div>

      <Canvas shadows camera={{ position: [3, 2, 15], fov: 45 }}>
        <color attach="background" args={['#0f172a']} />

        <Stars radius={100} depth={50} count={3000} factor={4} saturation={0} fade speed={0.5} />
        <ambientLight intensity={0.4} />
        <pointLight position={[10, 10, 10]} intensity={1} castShadow />
        <directionalLight position={[-5, 5, 5]} intensity={0.5} color="#aaddff" />

        <AnimatedCamera is3D={is3D} />

        <group position={[-2, 0, -2]}>
          <GridSystem is3D={is3D} />

          {TEST_VOXELS.map((data) => (
            <AnimatedVoxel
              key={data.id}
              data={data}
              is3D={is3D}
              isSelected={selectedId === data.id}
              onClick={(e) => {
                e.stopPropagation();
                setSelectedId(data.id);
              }}
              onHover={(e) => {
                e.stopPropagation();
                setHoveredId(data.id);
                document.body.style.cursor = 'pointer';
              }}
            />
          ))}

          {hoveredVoxel && <Tooltip data={hoveredVoxel} />}
        </group>

        <OrbitControls
          enableRotate={is3D}
          enablePan={true}
          enableZoom={true}
          minPolarAngle={is3D ? 0 : 0}
          maxPolarAngle={is3D ? Math.PI / 2.1 : Math.PI}
          enableDamping
          dampingFactor={0.05}
        />
      </Canvas>
    </div>
  );
}
