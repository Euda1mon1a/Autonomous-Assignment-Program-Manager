'use client';

import { CheckCircle, XCircle } from 'lucide-react';

interface GapItem {
  name: string;
  category: string;
  categoryColor?: string;
  covered: boolean;
  count?: number;
}

interface GapAnalysisProps {
  items: GapItem[];
  title?: string;
  coveredLabel?: string;
  uncoveredLabel?: string;
}

export function GapAnalysis({
  items,
  title,
  coveredLabel = 'Covered',
  uncoveredLabel = 'Gap',
}: GapAnalysisProps) {
  const covered = items.filter((i) => i.covered);
  const uncovered = items.filter((i) => !i.covered);
  const pct = items.length > 0 ? Math.round((covered.length / items.length) * 100) : 0;

  // Group uncovered by category
  const uncoveredByCategory = uncovered.reduce<Record<string, GapItem[]>>((acc, item) => {
    if (!acc[item.category]) acc[item.category] = [];
    acc[item.category].push(item);
    return acc;
  }, {});

  return (
    <div className="space-y-4">
      {title && <h3 className="text-lg font-semibold text-white">{title}</h3>}

      {/* Summary bar */}
      <div className="flex items-center gap-4">
        <div className="flex-1 h-3 bg-slate-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-green-500/70 rounded-full transition-all duration-500"
            style={{ width: `${pct}%` }}
          />
        </div>
        <span className="text-sm text-slate-300 whitespace-nowrap">
          {covered.length}/{items.length} {coveredLabel} ({pct}%)
        </span>
      </div>

      {/* Uncovered items */}
      {uncovered.length > 0 && (
        <div className="space-y-3">
          <p className="text-sm font-medium text-red-400">
            {uncovered.length} {uncoveredLabel}(s)
          </p>
          {Object.entries(uncoveredByCategory).map(([category, categoryItems]) => (
            <div key={category} className="space-y-1">
              <p
                className="text-xs font-semibold"
                style={{ color: categoryItems[0]?.categoryColor ?? '#94a3b8' }}
              >
                {category}
              </p>
              <div className="flex flex-wrap gap-1">
                {categoryItems.map((item) => (
                  <span
                    key={item.name}
                    className="flex items-center gap-1 px-2 py-0.5 text-xs bg-red-500/10 text-red-300 rounded border border-red-500/20"
                  >
                    <XCircle className="w-3 h-3" />
                    {item.name}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {uncovered.length === 0 && (
        <div className="flex items-center gap-2 text-green-400 text-sm">
          <CheckCircle className="w-5 h-5" />
          All items covered
        </div>
      )}
    </div>
  );
}
