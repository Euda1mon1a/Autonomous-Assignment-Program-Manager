import React, { useState, useMemo, useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import {
  OrbitControls,
  Stars,
  Html,
  Sparkles
} from '@react-three/drei';
import * as THREE from 'three';
import {
  Activity,
  Wind,
  Zap,
  RotateCcw,
  Maximize2,
  Play,
  Pause,
  Shuffle
} from 'lucide-react';

// --- Types & Constants ---

interface FoamCell {
  id: number;
  resident: string;
  rotation: string;
  block: number;
  volume: number;
  pressure: number;
  position: THREE.Vector3;
  velocity: THREE.Vector3;
  isSwapping: boolean;
  targetPos: THREE.Vector3 | null;
}

interface FilmData {
  id: string;
  a: THREE.Vector3;
  b: THREE.Vector3;
  pA: number;
  pB: number;
  idxA: number;
  idxB: number;
}

interface T1Record {
  time: string;
  pair: string;
}

const COLORS = {
  underload: new THREE.Color('#3b82f6'), // Blue
  balanced: new THREE.Color('#10b981'),  // Green
  overload: new THREE.Color('#ef4444'),  // Red
  filmSafe: new THREE.Color('#10b981'),
  filmWarn: new THREE.Color('#eab308'),
  filmCritical: new THREE.Color('#ef4444'),
};

const RESIDENTS = ['Maj. Miller', 'Capt. Chen', 'Lt. Smith', 'Maj. Wilson', 'Dr. House', 'Capt. Davis', 'Lt. Dan', 'Dr. Grey'];
const ROTATIONS = ['Trauma ICU', 'ER', 'Ortho', 'Cardio', 'Neuro', 'Gen Surg'];

// --- Helper Functions ---

const generateFoamData = (count = 18): FoamCell[] => {
  const cells: FoamCell[] = [];
  for (let i = 0; i < count; i++) {
    // Distribute in a rough sphere
    const theta = Math.random() * Math.PI * 2;
    const phi = Math.acos((Math.random() * 2) - 1);
    const r = 3 + Math.random() * 2;

    const x = r * Math.sin(phi) * Math.cos(theta);
    const y = r * Math.sin(phi) * Math.sin(theta);
    const z = r * Math.cos(phi);

    // Random workload stats
    const pressure = (Math.random() * 2 - 1); // -1 to 1

    cells.push({
      id: i,
      resident: RESIDENTS[i % RESIDENTS.length],
      rotation: ROTATIONS[i % ROTATIONS.length],
      block: Math.floor(i / 3) + 1,
      volume: 0.8 + Math.random() * 0.4,
      pressure: pressure,
      position: new THREE.Vector3(x, y, z),
      velocity: new THREE.Vector3(0, 0, 0),
      isSwapping: false,
      targetPos: null
    });
  }
  return cells;
};

// --- 3D Components ---

interface BubbleProps {
  data: FoamCell;
  isSelected: boolean;
  onClick: (id: number) => void;
}

const Bubble: React.FC<BubbleProps> = ({ data, isSelected, onClick }) => {
  const mesh = useRef<THREE.Mesh>(null);

  // Color logic based on pressure
  const color = useMemo(() => {
    const c = new THREE.Color();
    if (data.pressure < -0.3) c.copy(COLORS.underload);
    else if (data.pressure > 0.3) c.copy(COLORS.overload);
    else c.copy(COLORS.balanced);
    return c;
  }, [data.pressure]);

  useFrame((state, delta) => {
    if (!mesh.current) return;

    // Smooth movement to physics position
    mesh.current.position.lerp(data.position, 0.1);

    // Breathing animation
    const breathe = Math.sin(state.clock.elapsedTime * 2 + data.id) * 0.05;
    const scale = isSelected ? 1.2 : 1.0;
    mesh.current.scale.setScalar(data.volume * scale + breathe);

    // Rotation
    mesh.current.rotation.y += delta * 0.2;
    mesh.current.rotation.z += delta * 0.1;
  });

  return (
    <group>
      <mesh
        ref={mesh}
        onClick={(e) => { e.stopPropagation(); onClick(data.id); }}
      >
        <sphereGeometry args={[1, 32, 32]} />
        {/* Soap Bubble Material */}
        <meshPhysicalMaterial
          color={color}
          metalness={0.1}
          roughness={0.1}
          transmission={0.9}
          thickness={0.5}
          envMapIntensity={1.5}
          clearcoat={1}
          clearcoatRoughness={0.1}
          ior={1.5}
          iridescence={1}
          iridescenceIOR={1.3}
          iridescenceThicknessRange={[100, 400]}
        />

        {isSelected && (
          <mesh>
             <sphereGeometry args={[1.1, 32, 32]} />
             <meshBasicMaterial color="white" wireframe transparent opacity={0.1} />
          </mesh>
        )}
      </mesh>

      {/* Floating Label */}
      <Html position={[data.position.x, data.position.y + 1.2, data.position.z]} center distanceFactor={10} style={{ pointerEvents: 'none' }}>
        <div className={`text-[10px] font-mono whitespace-nowrap px-2 py-1 rounded bg-black/60 backdrop-blur-sm border ${isSelected ? 'border-white text-white' : 'border-white/20 text-white/70'}`}>
          {data.resident}
        </div>
      </Html>
    </group>
  );
};

interface FilmProps {
  start: THREE.Vector3;
  end: THREE.Vector3;
  pressureA: number;
  pressureB: number;
}

const Film: React.FC<FilmProps> = ({ start, end, pressureA: _pressureA, pressureB: _pressureB }) => {
  const ref = useRef<THREE.Mesh>(null);
  const dist = start.distanceTo(end);
  const mid = start.clone().add(end).multiplyScalar(0.5);

  // Calculate stress on the film (difference in pressure)
  const stress = Math.abs(_pressureA - _pressureB);
  const isCritical = stress > 0.8;

  useFrame((state) => {
    if (!ref.current) return;

    // Orient cylinder
    ref.current.position.copy(mid);
    ref.current.lookAt(end);
    ref.current.rotateX(Math.PI / 2);

    // Pulse critical films
    if (isCritical && ref.current.material instanceof THREE.MeshStandardMaterial) {
      const pulse = (Math.sin(state.clock.elapsedTime * 10) + 1) * 0.5;
      ref.current.material.opacity = 0.3 + (pulse * 0.4);
      ref.current.material.emissiveIntensity = pulse;
    }
  });

  // Only render if close enough
  if (dist > 3.5) return null;

  return (
    <mesh ref={ref}>
      <cylinderGeometry args={[0.1 * (1/dist), 0.1 * (1/dist), dist, 8]} />
      <meshStandardMaterial
        color={isCritical ? COLORS.filmCritical : COLORS.filmSafe}
        transparent
        opacity={0.3}
        depthWrite={false}
        emissive={isCritical ? COLORS.filmCritical : new THREE.Color('black')}
      />
    </mesh>
  );
};

interface FoamSimulationProps {
  cells: FoamCell[];
  setCells: React.Dispatch<React.SetStateAction<FoamCell[]>>;
  isRunning: boolean;
  onFilmsUpdate: (films: FilmData[]) => void;
}

const FoamSimulation: React.FC<FoamSimulationProps> = ({ cells, setCells: _setCells, isRunning, onFilmsUpdate }) => {
  // Simple force-directed graph physics
  useFrame((state, delta) => {
    if (!isRunning) return;

    const films: FilmData[] = [];

    // 1. Calculate Forces
    for (let i = 0; i < cells.length; i++) {
      const a = cells[i];
      if (a.isSwapping) continue; // Skip physics if animating a swap

      const force = new THREE.Vector3(0, 0, 0);

      // Center gravity (hold the cluster together)
      force.add(a.position.clone().multiplyScalar(-0.5));

      for (let j = 0; j < cells.length; j++) {
        if (i === j) continue;
        const b = cells[j];
        const dir = new THREE.Vector3().subVectors(a.position, b.position);
        const dist = dir.length();

        // Repulsion (Bubbles taking up space)
        if (dist < 2.5) {
          const strength = (2.5 - dist) * 4;
          force.add(dir.normalize().multiplyScalar(strength));
        }

        // Film recording (for visuals)
        if (i < j && dist < 3.5) {
          films.push({
            id: `${i}-${j}`,
            a: a.position,
            b: b.position,
            pA: a.pressure,
            pB: b.pressure,
            idxA: i,
            idxB: j
          });
        }
      }

      // Apply
      a.velocity.add(force.multiplyScalar(delta));
      a.velocity.multiplyScalar(0.9); // Damping
      a.position.add(a.velocity.clone().multiplyScalar(delta));
    }

    // Pass films up to parent for T1 logic
    if (state.clock.elapsedTime % 0.5 < 0.1) {
       onFilmsUpdate(films);
    }
  });

  return null;
};

// --- UI Components ---

interface PanelProps {
  children: React.ReactNode;
  title: string;
  className?: string;
}

const Panel: React.FC<PanelProps> = ({ children, title, className = "" }) => (
  <div className={`bg-zinc-950/80 backdrop-blur-md border border-zinc-800 p-4 rounded-lg pointer-events-auto ${className}`}>
    <h3 className="text-zinc-500 text-[10px] font-bold uppercase tracking-widest mb-3 border-b border-zinc-800 pb-2 flex items-center gap-2">
      {title}
    </h3>
    {children}
  </div>
);

interface StatBarProps {
  label: string;
  value: number;
  color?: string;
  max?: number;
}

const StatBar: React.FC<StatBarProps> = ({ label, value, color = "bg-blue-500", max = 100 }) => (
  <div className="mb-2">
    <div className="flex justify-between text-[10px] uppercase text-zinc-400 mb-1">
      <span>{label}</span>
      <span>{value.toFixed(0)}%</span>
    </div>
    <div className="h-1 bg-zinc-800 rounded-full overflow-hidden">
      <div className={`h-full ${color} transition-all duration-500`} style={{ width: `${Math.min(value, max)}%` }} />
    </div>
  </div>
);

// --- Main Component ---

export default function FoamTopologyVisualizer() {
  const [cells, setCells] = useState<FoamCell[]>(() => generateFoamData(20));
  const [films, setFilms] = useState<FilmData[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [isRunning, setIsRunning] = useState(true);
  const [lastT1, setLastT1] = useState<T1Record | null>(null);

  const selectedCell = cells.find(c => c.id === selectedId);
  const criticalFilms = films.filter(f => Math.abs(f.pA - f.pB) > 0.8);

  // T1 Event: Swap positions of two stressed neighbors
  const triggerT1Event = () => {
    if (criticalFilms.length === 0) return;

    // Pick the most critical film
    const targetFilm = criticalFilms.sort((a,b) => Math.abs(b.pA - b.pB) - Math.abs(a.pA - a.pB))[0];

    const idxA = targetFilm.idxA;
    const idxB = targetFilm.idxB;

    // Create swap animation
    const newCells = [...cells];
    const cellA = newCells[idxA];
    const cellB = newCells[idxB];

    // Swap actual data (simulating schedule swap)
    const tempResident = cellA.resident;
    cellA.resident = cellB.resident;
    cellB.resident = tempResident;

    // Swap pressures to simulate load balancing
    const avgPressure = (cellA.pressure + cellB.pressure) / 2;
    cellA.pressure = avgPressure;
    cellB.pressure = avgPressure;

    // Visual Effect: Swap positions
    const posA = cellA.position.clone();
    const posB = cellB.position.clone();

    cellA.position.copy(posB);
    cellB.position.copy(posA);

    cellA.velocity.add(new THREE.Vector3((Math.random()-0.5)*5, (Math.random()-0.5)*5, (Math.random()-0.5)*5));
    cellB.velocity.add(new THREE.Vector3((Math.random()-0.5)*5, (Math.random()-0.5)*5, (Math.random()-0.5)*5));

    setCells(newCells);
    setLastT1({ time: new Date().toLocaleTimeString(), pair: `${cellA.resident} ↔ ${cellB.resident}` });
  };

  return (
    <div className="w-full h-screen bg-black text-white overflow-hidden relative font-sans selection:bg-blue-500/30">

      {/* 3D Scene */}
      <div className="absolute inset-0 z-0">
        <Canvas camera={{ position: [0, 0, 14], fov: 45 }}>
          <color attach="background" args={['#050505']} />
          <fog attach="fog" args={['#050505', 10, 25]} />

          <ambientLight intensity={0.5} />
          <pointLight position={[10, 10, 10]} intensity={1.5} color="#4f46e5" />
          <pointLight position={[-10, -10, -10]} intensity={0.5} color="#ec4899" />

          <Stars radius={100} depth={50} count={5000} factor={4} saturation={0} fade speed={1} />
          <Sparkles count={50} scale={10} size={2} speed={0.4} opacity={0.5} />

          <group>
            <FoamSimulation
              cells={cells}
              setCells={setCells}
              isRunning={isRunning}
              onFilmsUpdate={setFilms}
            />

            {cells.map(cell => (
              <Bubble
                key={cell.id}
                data={cell}
                isSelected={selectedId === cell.id}
                onClick={setSelectedId}
              />
            ))}

            {films.map(film => (
              <Film
                key={film.id}
                start={film.a}
                end={film.b}
                pressureA={film.pA}
                pressureB={film.pB}
              />
            ))}
          </group>

          <OrbitControls
            enablePan={false}
            minDistance={5}
            maxDistance={20}
            autoRotate={isRunning}
            autoRotateSpeed={0.5}
          />
        </Canvas>
      </div>

      {/* --- HUD Overlay --- */}

      {/* Header */}
      <div className="absolute top-0 left-0 w-full p-6 z-10 pointer-events-none">
        <div className="flex justify-between items-start">
          <div>
            <div className="flex items-center gap-2 text-blue-500 mb-1">
              <Zap size={18} fill="currentColor" className="animate-pulse" />
              <span className="text-[10px] font-bold tracking-[0.3em] uppercase">Med-Ops Command</span>
            </div>
            <h1 className="text-3xl font-light tracking-tight">Foam Topology <span className="font-bold">Scheduler</span></h1>
          </div>
          <div className="flex gap-4 pointer-events-auto">
             <button
                onClick={() => setIsRunning(!isRunning)}
                className="bg-zinc-900 border border-zinc-700 p-2 rounded hover:bg-zinc-800 transition-colors"
             >
               {isRunning ? <Pause size={20} /> : <Play size={20} />}
             </button>
          </div>
        </div>
      </div>

      {/* Left Panel - Selection Details */}
      <div className="absolute left-6 top-32 w-64 space-y-4 pointer-events-none">
        {selectedCell ? (
          <Panel title="Assignment Manifest" className="animate-in slide-in-from-left-4 fade-in duration-300">
            <div className="space-y-4">
              <div className="flex items-center gap-3 mb-2">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-lg
                  ${selectedCell.pressure > 0.3 ? 'bg-red-500/20 text-red-500 border border-red-500' :
                    selectedCell.pressure < -0.3 ? 'bg-blue-500/20 text-blue-500 border border-blue-500' :
                    'bg-emerald-500/20 text-emerald-500 border border-emerald-500'}`}
                >
                  {selectedCell.resident.charAt(0)}
                </div>
                <div>
                  <h2 className="font-bold text-lg leading-none">{selectedCell.resident}</h2>
                  <p className="text-xs text-zinc-500 uppercase">{selectedCell.rotation}</p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="bg-zinc-900 p-2 rounded">
                  <p className="text-zinc-500 uppercase text-[9px]">Block</p>
                  <p className="font-mono text-sm">{selectedCell.block}</p>
                </div>
                <div className="bg-zinc-900 p-2 rounded">
                  <p className="text-zinc-500 uppercase text-[9px]">Volume</p>
                  <p className="font-mono text-sm">{selectedCell.volume.toFixed(2)}</p>
                </div>
              </div>

              <div className="mt-2">
                <StatBar
                  label="Workload Pressure"
                  value={(selectedCell.pressure + 1) * 50}
                  color={selectedCell.pressure > 0.3 ? "bg-red-500" : "bg-blue-500"}
                />
              </div>
            </div>
          </Panel>
        ) : (
          <Panel title="System Status" className="opacity-70">
            <div className="flex flex-col items-center justify-center py-8 text-zinc-600 gap-2">
              <Activity size={32} />
              <p className="text-xs uppercase tracking-widest">Select a Bubble</p>
            </div>
          </Panel>
        )}
      </div>

      {/* Right Panel - Topology Controls */}
      <div className="absolute right-6 top-32 w-72 space-y-4 pointer-events-none">

        {/* T1 Stats */}
        <Panel title="Topology Physics">
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div className="text-center">
              <div className="text-2xl font-mono font-bold text-zinc-200">{films.length}</div>
              <div className="text-[9px] uppercase text-zinc-500 tracking-wider">Active Films</div>
            </div>
            <div className="text-center">
              <div className={`text-2xl font-mono font-bold ${criticalFilms.length > 0 ? 'text-red-500 animate-pulse' : 'text-emerald-500'}`}>
                {criticalFilms.length}
              </div>
              <div className="text-[9px] uppercase text-zinc-500 tracking-wider">T1 Candidates</div>
            </div>
          </div>

          <button
            onClick={triggerT1Event}
            disabled={criticalFilms.length === 0}
            className={`w-full py-3 rounded text-xs font-bold uppercase tracking-widest flex items-center justify-center gap-2 border transition-all duration-300
              ${criticalFilms.length > 0
                ? 'bg-red-500/10 text-red-500 border-red-500 hover:bg-red-500 hover:text-white cursor-pointer shadow-[0_0_15px_rgba(239,68,68,0.3)]'
                : 'bg-zinc-900 text-zinc-600 border-zinc-800 cursor-not-allowed'}`}
          >
            <Shuffle size={14} />
            Execute T1 Swap
          </button>

          {lastT1 && (
            <div className="mt-4 p-2 bg-zinc-900 rounded border border-zinc-800 flex items-start gap-2">
               <RotateCcw size={14} className="text-emerald-500 mt-0.5" />
               <div>
                 <p className="text-[10px] text-zinc-500 uppercase">Last Optimization</p>
                 <p className="text-xs font-mono text-emerald-400">{lastT1.pair}</p>
                 <p className="text-[9px] text-zinc-600">{lastT1.time}</p>
               </div>
            </div>
          )}
        </Panel>

        <Panel title="Stress Histogram">
          <div className="h-24 flex items-end gap-1 justify-between px-2">
            {[...Array(10)].map((_, i) => {
              const h = 20 + Math.random() * 80;
              let bg = "bg-blue-500";
              if (i > 4) bg = "bg-emerald-500";
              if (i > 7) bg = "bg-red-500";
              return (
                <div key={i} className={`w-full rounded-t-sm opacity-60 ${bg}`} style={{ height: `${h}%` }} />
              );
            })}
          </div>
          <div className="flex justify-between text-[9px] uppercase text-zinc-500 mt-2">
            <span>Underload</span>
            <span>Balanced</span>
            <span>Overload</span>
          </div>
        </Panel>

      </div>

      {/* Footer / Legend */}
      <div className="absolute bottom-6 left-6 right-6 flex justify-between items-end pointer-events-none">
         <div className="flex gap-6 pointer-events-auto bg-zinc-950/80 p-3 rounded-full border border-zinc-800 backdrop-blur-md">
           <div className="flex items-center gap-2 text-[10px] uppercase font-bold text-zinc-400">
              <div className="w-3 h-3 rounded-full bg-blue-500 border border-white/20" />
              Low Pressure
           </div>
           <div className="flex items-center gap-2 text-[10px] uppercase font-bold text-zinc-400">
              <div className="w-3 h-3 rounded-full bg-emerald-500 border border-white/20" />
              Optimal
           </div>
           <div className="flex items-center gap-2 text-[10px] uppercase font-bold text-zinc-400">
              <div className="w-3 h-3 rounded-full bg-red-500 border border-white/20 animate-pulse" />
              Critical
           </div>
         </div>

         <div className="text-right">
            <div className="flex items-center justify-end gap-2 text-zinc-500">
              <Wind size={14} />
              <span className="text-[10px] font-mono">SIMULATION_SPEED: 1.0x</span>
            </div>
            <div className="flex items-center justify-end gap-2 text-zinc-500 mt-1">
              <Maximize2 size={14} />
              <span className="text-[10px] font-mono">VIEWPORT: 3D_CANVAS</span>
            </div>
         </div>
      </div>

    </div>
  );
}
