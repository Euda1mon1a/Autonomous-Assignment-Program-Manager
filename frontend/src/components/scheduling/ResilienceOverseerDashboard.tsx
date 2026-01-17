import React, { useState, useEffect } from 'react';
import {
  Shield,
  AlertTriangle,
  Activity,
  Clock,
  Zap,
  TrendingUp,
  AlertOctagon,
  LayoutGrid,
  Flame
} from 'lucide-react';

// --- Types ---

interface CircuitBreaker {
  name: string;
  state: 'CLOSED' | 'HALF_OPEN' | 'OPEN';
  tripCount: number;
  lastTrip: string;
}

interface Vulnerability {
  id: number;
  personName: string;
  hoursThisWeek: number;
  projectedHours: number;
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  violationTime: number | null;
}

interface DashboardData {
  defenseLevel: 'NORMAL' | 'DEGRADED' | 'N_MINUS_1' | 'N_MINUS_2' | 'CRITICAL';
  utilizationRate: number;
  burnoutRt: number;
  circuitBreakers: CircuitBreaker[];
  vulnerabilities: Vulnerability[];
}

interface Rotation {
  name: string;
  utilization: number;
  staff: number;
  required: number;
  status: string;
}

// --- UI Components ---

interface CardProps {
  children: React.ReactNode;
  className?: string;
}

const Card: React.FC<CardProps> = ({ children, className = "" }) => (
  <div className={`bg-zinc-950 border border-zinc-800 rounded-lg overflow-hidden relative ${className}`}>
    {children}
  </div>
);

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'warning' | 'danger' | 'success' | 'info' | 'critical';
  className?: string;
}

const Badge: React.FC<BadgeProps> = ({ children, variant = "default", className = "" }) => {
  const variants = {
    default: "bg-zinc-800 text-zinc-300 border-zinc-700",
    warning: "bg-amber-950/40 text-amber-400 border-amber-900/50",
    danger: "bg-red-950/40 text-red-400 border-red-900/50",
    success: "bg-emerald-950/40 text-emerald-400 border-emerald-900/50",
    info: "bg-blue-950/40 text-blue-400 border-blue-900/50",
    critical: "bg-rose-950/50 text-rose-500 border-rose-900 animate-pulse"
  };
  return (
    <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${variants[variant]} ${className}`}>
      {children}
    </span>
  );
};

// --- Helper: Countdown Timer Component ---
interface CountDownTimerProps {
  initialSeconds: number;
}

const CountDownTimer: React.FC<CountDownTimerProps> = ({ initialSeconds }) => {
  const [seconds, setSeconds] = useState(initialSeconds);

  useEffect(() => {
    const interval = setInterval(() => {
      setSeconds(s => (s > 0 ? s - 1 : 0));
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const format = (s: number) => {
    const h = Math.floor(s / 3600).toString().padStart(2, '0');
    const m = Math.floor((s % 3600) / 60).toString().padStart(2, '0');
    const sec = (s % 60).toString().padStart(2, '0');
    return `${h}:${m}:${sec}`;
  };

  return <span className="font-mono text-red-400 tracking-widest">{format(seconds)}</span>;
};

// --- Helper: Readiness Gauge Component ---
interface ReadinessGaugeProps {
  level: DashboardData['defenseLevel'];
}

const ReadinessGauge: React.FC<ReadinessGaugeProps> = ({ level }) => {
  const map: Record<string, { angle: number; color: string; label: string }> = {
    "NORMAL": { angle: 25, color: "#10b981", label: "Normal" },
    "DEGRADED": { angle: 65, color: "#3b82f6", label: "Degraded" },
    "N_MINUS_1": { angle: 100, color: "#eab308", label: "N-1" },
    "N_MINUS_2": { angle: 135, color: "#f97316", label: "N-2" },
    "CRITICAL": { angle: 165, color: "#ef4444", label: "Critical" }
  };

  const current = map[level] || map["NORMAL"];

  return (
    <div className="relative w-full h-32 flex items-end justify-center overflow-hidden">
      <svg viewBox="0 0 200 110" className="w-full h-full">
        <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="#27272a" strokeWidth="12" strokeLinecap="round" />
        <path d="M 20 100 A 80 80 0 0 1 60 45" fill="none" stroke="#10b981" strokeWidth="12" strokeOpacity={level === 'NORMAL' ? 1 : 0.2} />
        <path d="M 62 43 A 80 80 0 0 1 100 20" fill="none" stroke="#3b82f6" strokeWidth="12" strokeOpacity={level === 'DEGRADED' ? 1 : 0.2} />
        <path d="M 100 20 A 80 80 0 0 1 138 43" fill="none" stroke="#eab308" strokeWidth="12" strokeOpacity={level === 'N_MINUS_1' ? 1 : 0.2} />
        <path d="M 140 45 A 80 80 0 0 1 180 100" fill="none" stroke="#ef4444" strokeWidth="12" strokeOpacity={level === 'CRITICAL' || level === 'N_MINUS_2' ? 1 : 0.2} />

        <g style={{ transform: `rotate(${current.angle - 90}deg)`, transformOrigin: "100px 100px", transition: "transform 1s ease-out" }}>
          <path d="M 100 100 L 100 35" stroke="white" strokeWidth="2" />
          <circle cx="100" cy="100" r="4" fill="white" />
        </g>
      </svg>
      <div className="absolute bottom-0 text-center">
        <div className="text-[10px] uppercase text-zinc-500 font-bold tracking-widest mb-1">DEFCON Level</div>
        <div className="text-xl font-black uppercase tracking-tighter" style={{ color: current.color }}>
          {current.label}
        </div>
      </div>
    </div>
  );
};

// --- Mock Data Generators ---

const generateMockData = (): DashboardData => ({
  defenseLevel: ["NORMAL", "DEGRADED", "N_MINUS_1", "N_MINUS_2", "CRITICAL"][Math.floor(Math.random() * 3)] as DashboardData['defenseLevel'],
  utilizationRate: 0.88,
  burnoutRt: 1.15,
  circuitBreakers: [
    { name: "ACGME Constraints", state: "CLOSED", tripCount: 0, lastTrip: "N/A" },
    { name: "Leave Balancer", state: "HALF_OPEN", tripCount: 4, lastTrip: "14:02Z" },
    { name: "Shift Optimizer", state: "CLOSED", tripCount: 1, lastTrip: "09:00Z" },
    { name: "Crisis Failover", state: "OPEN", tripCount: 12, lastTrip: "08:45Z" },
  ],
  vulnerabilities: [
    { id: 1, personName: "Maj. Miller", hoursThisWeek: 78, projectedHours: 84, riskLevel: "CRITICAL", violationTime: 3400 },
    { id: 2, personName: "Capt. Davis", hoursThisWeek: 68, projectedHours: 72, riskLevel: "HIGH", violationTime: null },
    { id: 3, personName: "Lt. Smith", hoursThisWeek: 60, projectedHours: 65, riskLevel: "MEDIUM", violationTime: null }
  ]
});

const ROTATIONS: Rotation[] = [
  { name: "Trauma ICU", utilization: 105, staff: 4, required: 5, status: "Gap" },
  { name: "Emergency Rm", utilization: 82, staff: 8, required: 8, status: "Nominal" },
  { name: "Operating Rm", utilization: 94, staff: 12, required: 12, status: "Fragile" },
  { name: "Radiology", utilization: 45, staff: 3, required: 2, status: "Surplus" },
];

// --- Main Component ---

export default function ResilienceOverseerDashboard() {
  const [data, setData] = useState<DashboardData>(generateMockData());

  // Simulate Live Data Pulse
  useEffect(() => {
    const interval = setInterval(() => {
      setData(prev => ({
        ...prev,
        burnoutRt: +(Math.random() * (1.3 - 0.8) + 0.8).toFixed(2),
        circuitBreakers: prev.circuitBreakers.map(cb =>
          Math.random() > 0.95 ? { ...cb, state: cb.state === "CLOSED" ? "HALF_OPEN" : "CLOSED" } as CircuitBreaker : cb
        )
      }));
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-black text-zinc-100 p-4 md:p-6 font-sans selection:bg-blue-500/30">

      {/* Header */}
      <header className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4 border-b border-zinc-900 pb-6">
        <div>
          <div className="flex items-center gap-2 text-blue-500 mb-1">
            <Shield size={20} className="animate-pulse" />
            <span className="text-xs font-bold tracking-[0.25em] uppercase text-blue-500/80">Med-Ops Command</span>
          </div>
          <h1 className="text-2xl font-light tracking-tight text-white">Residency <span className="font-bold text-zinc-100">Overseer</span></h1>
        </div>

        <div className="bg-zinc-900/50 border border-zinc-800 px-4 py-2 rounded flex items-center gap-4">
          <div className="text-right">
            <p className="text-[9px] text-zinc-500 font-bold uppercase tracking-wider">System Clock</p>
            <p className="font-mono text-sm text-zinc-300">{new Date().toLocaleDateString('en-US', { day: '2-digit', month: 'short', year: 'numeric' }).toUpperCase()} - {new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false })} Z</p>
          </div>
          <Clock className="text-zinc-600" size={18} />
        </div>
      </header>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

        {/* LEFT COLUMN: Status & Threats */}
        <div className="lg:col-span-4 space-y-6">

          {/* DEFCON / Readiness Gauge */}
          <Card className="p-6 bg-gradient-to-b from-zinc-900 to-zinc-950">
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-xs font-bold text-zinc-400 uppercase tracking-widest">System Readiness</h3>
              <Activity className="text-zinc-600" size={16} />
            </div>
            <ReadinessGauge level={data.defenseLevel} />
          </Card>

          {/* Burnout Rt Indicator */}
          <Card className="p-6 flex flex-col justify-between relative overflow-hidden">
            <div className="absolute top-0 right-0 p-3 opacity-10">
              <TrendingUp size={80} />
            </div>
            <div>
              <h3 className="text-xs font-bold text-zinc-400 uppercase tracking-widest flex items-center gap-2">
                Burnout Rt (Reproduction)
                <span className="text-[9px] bg-zinc-800 px-1 rounded text-zinc-500 cursor-help" title="Rate at which burnout spreads between residents">?</span>
              </h3>
              <div className="mt-4 flex items-baseline gap-3">
                <span className={`text-5xl font-mono font-bold tracking-tighter ${data.burnoutRt >= 1 ? 'text-amber-500' : 'text-emerald-500'}`}>
                  {data.burnoutRt}
                </span>
                <span className="text-xs font-bold text-zinc-500 uppercase">
                  {data.burnoutRt >= 1 ? 'Spreading' : 'Contained'}
                </span>
              </div>
            </div>
            <div className="mt-4 w-full bg-zinc-800 h-1 rounded-full overflow-hidden">
              <div
                className={`h-full transition-all duration-1000 ${data.burnoutRt >= 1 ? 'bg-amber-500' : 'bg-emerald-500'}`}
                style={{ width: `${(data.burnoutRt / 2) * 100}%` }}
              />
            </div>
            <p className="text-[10px] text-zinc-600 mt-2">Target: &lt; 1.0 | Threshold: 1.5</p>
          </Card>

          {/* Threat Cards */}
          <div className="space-y-3">
            <h3 className="text-xs font-bold text-zinc-500 uppercase tracking-widest pl-1">Active Threats</h3>

            {data.vulnerabilities.map(vuln => (
              <Card
                key={vuln.id}
                className={`p-4 border-l-4 ${
                  vuln.riskLevel === 'CRITICAL'
                    ? 'border-l-red-500 border-red-500/50 shadow-[0_0_15px_rgba(239,68,68,0.1)] animate-[pulse_3s_ease-in-out_infinite]'
                    : vuln.riskLevel === 'HIGH' ? 'border-l-amber-500' : 'border-l-zinc-700'
                }`}
              >
                <div className="flex justify-between items-start">
                  <div>
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-bold text-zinc-200">{vuln.personName}</p>
                      {vuln.riskLevel === 'CRITICAL' && <Flame size={12} className="text-red-500 fill-red-500" />}
                    </div>
                    <p className="text-[10px] text-zinc-500 uppercase mt-0.5">Proj: {vuln.projectedHours} hrs</p>
                  </div>
                  <Badge variant={vuln.riskLevel === 'CRITICAL' ? 'danger' : 'warning'}>
                    {vuln.riskLevel}
                  </Badge>
                </div>

                {vuln.riskLevel === 'CRITICAL' && vuln.violationTime && (
                  <div className="mt-3 pt-3 border-t border-zinc-800 flex items-center justify-between">
                    <span className="text-[10px] font-bold text-red-400 uppercase tracking-wider">Violation In:</span>
                    <div className="bg-red-950/30 px-2 py-1 rounded border border-red-900/30">
                      <CountDownTimer initialSeconds={vuln.violationTime} />
                    </div>
                  </div>
                )}
              </Card>
            ))}
          </div>
        </div>

        {/* MIDDLE COLUMN: Heatmap */}
        <div className="lg:col-span-5 space-y-6">
          <Card className="p-6 h-full border-zinc-800 flex flex-col">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-sm font-bold text-zinc-400 uppercase tracking-widest">Global Coverage Map</h3>
              <LayoutGrid size={18} className="text-zinc-600" />
            </div>

            <div className="space-y-6 flex-grow">
              {ROTATIONS.map((rot, i) => (
                <div key={i} className="space-y-2">
                  <div className="flex justify-between text-xs items-end">
                    <span className="font-medium text-zinc-300 flex items-center gap-2">
                      {rot.name}
                      {rot.utilization > 100 && <AlertOctagon size={12} className="text-amber-500" />}
                    </span>
                    <span className="font-mono text-zinc-500">
                      <span className={rot.utilization > 100 ? "text-amber-400" : rot.utilization < 80 ? "text-red-400" : "text-emerald-400"}>
                        {rot.utilization}%
                      </span>
                    </span>
                  </div>

                  {/* Heatmap Strip */}
                  <div className="grid grid-cols-20 gap-0.5 h-6">
                    {[...Array(20)].map((_, j) => {
                      const threshold = (j + 1) * 5;
                      const isFilled = threshold <= rot.utilization;
                      const isOverload = threshold > 100;

                      let bg = "bg-zinc-800/50";
                      if (isFilled) {
                         if (isOverload) bg = "bg-amber-500";
                         else if (rot.utilization < 80) bg = "bg-red-900";
                         else bg = "bg-emerald-500";
                      }

                      return (
                        <div key={j} className={`rounded-[1px] ${bg} ${isFilled ? 'opacity-100' : 'opacity-30'}`} />
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>

            {/* Legend */}
            <div className="mt-8 pt-6 border-t border-zinc-800">
              <div className="flex justify-between text-[10px] uppercase text-zinc-500 font-bold mb-2">
                <span>Critical Gap (&lt;80%)</span>
                <span>Optimal</span>
                <span>Over-Sat (&gt;100%)</span>
              </div>
              <div className="h-2 rounded-full w-full bg-gradient-to-r from-red-900 via-emerald-500 to-amber-500 opacity-80" />
            </div>
          </Card>
        </div>

        {/* RIGHT COLUMN: Circuit Breakers */}
        <div className="lg:col-span-3 space-y-6">
          <Card className="p-6 h-full border-zinc-800 bg-zinc-950">
             <div className="flex items-center gap-2 mb-6">
              <Zap size={16} className="text-yellow-500" />
              <h3 className="text-sm font-bold text-zinc-400 uppercase tracking-widest">Circuit Breakers</h3>
            </div>

            <div className="space-y-4">
              {data.circuitBreakers.map((cb, idx) => {
                const isClosed = cb.state === "CLOSED";
                const isHalf = cb.state === "HALF_OPEN";
                const isOpen = cb.state === "OPEN";

                return (
                  <div key={idx} className="bg-zinc-900/50 rounded p-3 border border-zinc-800/50">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-xs font-bold text-zinc-300">{cb.name}</span>
                      {isClosed && <div className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.6)]" />}
                      {isHalf && <div className="w-2 h-2 rounded-full bg-yellow-500 animate-pulse" />}
                      {isOpen && <div className="w-2 h-2 rounded-full bg-red-600 animate-ping" />}
                    </div>

                    <div className="flex items-center justify-between text-[10px] uppercase tracking-wider">
                      <span className={`
                        font-bold
                        ${isClosed ? 'text-emerald-500' : ''}
                        ${isHalf ? 'text-yellow-500' : ''}
                        ${isOpen ? 'text-red-500' : ''}
                      `}>
                        {cb.state.replace('_', ' ')}
                      </span>
                      <span className="text-zinc-600">Trips: {cb.tripCount}</span>
                    </div>

                    {/* Visual Breaker Switch Representation */}
                    <div className="mt-3 relative h-1 bg-zinc-800 rounded-full w-full">
                       <div className={`absolute top-1/2 -translate-y-1/2 w-3 h-3 rounded shadow transition-all duration-300
                         ${isClosed ? 'left-[95%] bg-emerald-500' : ''}
                         ${isHalf ? 'left-[50%] bg-yellow-500' : ''}
                         ${isOpen ? 'left-[0%] bg-red-500' : ''}
                       `} />
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="mt-8 p-4 rounded bg-red-950/10 border border-red-900/20">
              <div className="flex items-center gap-2 text-red-400 mb-2">
                <AlertTriangle size={14} />
                <span className="text-[10px] font-bold uppercase">Manual Override</span>
              </div>
              <button className="w-full bg-red-900/20 hover:bg-red-900/40 text-red-500 border border-red-900/50 rounded py-2 text-xs font-bold uppercase transition-colors">
                Force Reset All
              </button>
            </div>
          </Card>
        </div>

      </div>

      {/* Footer */}
      <footer className="mt-12 pt-6 border-t border-zinc-900 flex flex-col md:flex-row justify-between items-center text-zinc-600 gap-4">
        <div className="flex items-center gap-6 text-[10px] font-bold uppercase tracking-[0.15em]">
          <div className="flex items-center gap-2">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-emerald-500/80">Uplink Stable</span>
          </div>
          <span>Latency: 12ms</span>
        </div>
        <div className="text-[10px] font-mono text-zinc-700">
          SECURE CHANNEL // UNCLASSIFIED // SIMULATION MODE
        </div>
      </footer>
    </div>
  );
}
