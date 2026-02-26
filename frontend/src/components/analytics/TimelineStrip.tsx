'use client';

interface TimelineBlock {
  id: string | number;
  name: string;
  weeks: number;
  icon?: string;
  status: 'not_started' | 'in_progress' | 'completed' | 'mixed';
  completedCount?: number;
  totalCount?: number;
}

interface TimelineStripProps {
  blocks: TimelineBlock[];
  title?: string;
  onBlockClick?: (blockId: string | number) => void;
}

function getBlockStatusColor(status: string): string {
  switch (status) {
    case 'completed':
      return 'bg-green-500/20 border-green-500/40 text-green-300';
    case 'in_progress':
      return 'bg-amber-500/20 border-amber-500/40 text-amber-300';
    case 'mixed':
      return 'bg-indigo-500/20 border-indigo-500/40 text-indigo-300';
    default:
      return 'bg-slate-700/30 border-slate-600/40 text-slate-400';
  }
}

export function TimelineStrip({ blocks, title, onBlockClick }: TimelineStripProps) {
  const totalWeeks = blocks.reduce((sum, b) => sum + b.weeks, 0);

  return (
    <div className="space-y-3">
      {title && <h3 className="text-lg font-semibold text-white">{title}</h3>}
      <div className="flex gap-1 overflow-x-auto pb-2">
        {blocks.map((block) => {
          const widthPct = (block.weeks / totalWeeks) * 100;
          const statusColor = getBlockStatusColor(block.status);
          return (
            <button
              key={block.id}
              onClick={() => onBlockClick?.(block.id)}
              className={`flex-shrink-0 border rounded-lg p-2 text-center transition-all hover:scale-105 cursor-pointer ${statusColor}`}
              style={{ minWidth: `${Math.max(widthPct, 4)}%`, flexBasis: `${widthPct}%` }}
              title={`${block.name} (${block.weeks}w)`}
            >
              {block.icon && <span className="text-lg">{block.icon}</span>}
              <p className="text-xs font-medium truncate mt-1">{block.name}</p>
              <p className="text-[10px] opacity-70">
                {block.weeks}w
                {block.completedCount !== undefined && block.totalCount !== undefined && (
                  <> &middot; {block.completedCount}/{block.totalCount}</>
                )}
              </p>
            </button>
          );
        })}
      </div>
    </div>
  );
}
