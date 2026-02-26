'use client';

interface HeatMapCell {
  row: string;
  col: string;
  value: number;
}

interface ColumnConfig {
  key: string;
  label: string;
  color?: string;
}

interface HeatMapTableProps {
  cells: HeatMapCell[];
  columns: ColumnConfig[];
  rows: string[];
  title?: string;
  maxValue?: number;
}

function getCellColor(value: number, max: number, color?: string): string {
  if (value === 0) return 'bg-slate-800/30';
  const intensity = Math.min(value / Math.max(max, 1), 1);
  if (color) {
    const alpha = 0.15 + intensity * 0.6;
    return `bg-opacity-${Math.round(alpha * 100)}`;
  }
  if (intensity < 0.25) return 'bg-slate-700/40';
  if (intensity < 0.5) return 'bg-indigo-900/40';
  if (intensity < 0.75) return 'bg-indigo-700/40';
  return 'bg-indigo-500/40';
}

export function HeatMapTable({ cells, columns, rows, title, maxValue }: HeatMapTableProps) {
  const cellMap = new Map<string, number>();
  let computedMax = maxValue ?? 0;
  for (const cell of cells) {
    cellMap.set(`${cell.row}|${cell.col}`, cell.value);
    if (!maxValue && cell.value > computedMax) computedMax = cell.value;
  }

  return (
    <div className="space-y-3">
      {title && <h3 className="text-lg font-semibold text-white">{title}</h3>}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-700/50">
              <th className="px-3 py-2 text-left text-xs font-medium text-slate-400">
                Block
              </th>
              {columns.map((col) => (
                <th
                  key={col.key}
                  className="px-3 py-2 text-center text-xs font-medium"
                  style={{ color: col.color ?? '#94a3b8' }}
                >
                  {col.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row} className="border-b border-slate-700/20">
                <td className="px-3 py-2 text-xs text-slate-300 whitespace-nowrap">
                  {row}
                </td>
                {columns.map((col) => {
                  const val = cellMap.get(`${row}|${col.key}`) ?? 0;
                  return (
                    <td key={col.key} className="px-3 py-2 text-center">
                      <span
                        className={`inline-block w-8 h-8 leading-8 rounded text-xs font-medium ${
                          val > 0 ? 'text-white' : 'text-slate-600'
                        } ${getCellColor(val, computedMax)}`}
                        style={
                          val > 0
                            ? {
                                backgroundColor: col.color
                                  ? `${col.color}${Math.round((0.15 + (val / Math.max(computedMax, 1)) * 0.6) * 255)
                                      .toString(16)
                                      .padStart(2, '0')}`
                                  : undefined,
                              }
                            : undefined
                        }
                      >
                        {val}
                      </span>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
