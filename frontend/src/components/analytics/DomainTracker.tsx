'use client';

interface DomainConfig {
  code: string;
  name: string;
  color: string;
  target: number;
  current: number;
  completed?: number;
  label?: string;
}

interface DomainTrackerProps {
  domains: DomainConfig[];
  title?: string;
}

export function DomainTracker({ domains, title }: DomainTrackerProps) {
  return (
    <div className="space-y-4">
      {title && (
        <h3 className="text-lg font-semibold text-white">{title}</h3>
      )}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        {domains.map((domain) => {
          const pct = Math.min(domain.current, 100);
          const targetPct = Math.min(domain.target, 100);
          return (
            <div
              key={domain.code}
              className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-4"
            >
              <div className="flex items-center justify-between mb-2">
                <span
                  className="text-sm font-semibold"
                  style={{ color: domain.color }}
                >
                  {domain.code}
                </span>
                <span className="text-xs text-slate-400">
                  {domain.current}%{' '}
                  <span className="text-slate-500">/ {domain.target}%</span>
                </span>
              </div>
              <p className="text-xs text-slate-400 mb-3 line-clamp-1">
                {domain.label ?? domain.name}
              </p>
              <div className="relative h-2 bg-slate-700 rounded-full overflow-hidden">
                <div
                  className="absolute inset-y-0 left-0 rounded-full transition-all duration-500"
                  style={{
                    width: `${pct}%`,
                    backgroundColor: domain.color,
                    opacity: 0.8,
                  }}
                />
                {/* Target marker */}
                <div
                  className="absolute top-0 bottom-0 w-0.5 bg-white/60"
                  style={{ left: `${targetPct}%` }}
                  title={`Target: ${domain.target}%`}
                />
              </div>
              {domain.completed !== undefined && (
                <p className="text-xs text-slate-500 mt-2">
                  {domain.completed} completed
                </p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
