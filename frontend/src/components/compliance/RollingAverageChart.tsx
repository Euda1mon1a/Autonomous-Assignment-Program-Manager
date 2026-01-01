/**
 * RollingAverageChart Component
 *
 * Visualization of 4-week rolling average work hours
 */

import React from 'react';

export interface WeekData {
  weekStart: string;
  weekEnd: string;
  hours: number;
  rollingAverage: number;
}

export interface RollingAverageChartProps {
  data: WeekData[];
  maxHours?: number;
  warningThreshold?: number;
  className?: string;
}

export const RollingAverageChart: React.FC<RollingAverageChartProps> = ({
  data,
  maxHours = 80,
  warningThreshold = 70,
  className = '',
}) => {
  if (data.length === 0) {
    return (
      <div className={`rolling-average-chart bg-white rounded-lg shadow p-6 text-center text-gray-500 ${className}`} role="status">
        No data available
      </div>
    );
  }

  const maxValue = Math.max(...data.map(d => Math.max(d.hours, d.rollingAverage)), maxHours);
  const chartHeight = 200;

  const getBarHeight = (hours: number) => {
    return (hours / maxValue) * chartHeight;
  };

  const getBarColor = (hours: number) => {
    if (hours >= maxHours) return 'bg-red-500';
    if (hours >= warningThreshold) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  return (
    <div className={`rolling-average-chart bg-white rounded-lg shadow-lg p-6 ${className}`} role="region" aria-label="4-week rolling average work hours chart">
      {/* Header */}
      <div className="mb-6">
        <h3 className="text-lg font-bold mb-1">4-Week Rolling Average</h3>
        <p className="text-sm text-gray-600">Work hours per week with rolling 4-week average</p>
      </div>

      {/* Legend */}
      <div className="flex gap-4 mb-4 text-sm" role="list" aria-label="Chart legend">
        <div className="flex items-center gap-2" role="listitem">
          <div className="w-4 h-4 bg-blue-500 rounded" aria-hidden="true"></div>
          <span>Weekly Hours</span>
        </div>
        <div className="flex items-center gap-2" role="listitem">
          <div className="w-4 h-2 bg-purple-500 rounded-full" aria-hidden="true"></div>
          <span>Rolling Avg</span>
        </div>
        <div className="flex items-center gap-2" role="listitem">
          <div className="w-4 h-0.5 bg-red-500" aria-hidden="true"></div>
          <span>80h Limit</span>
        </div>
      </div>

      {/* Chart */}
      <div className="relative" style={{ height: chartHeight + 60 }} role="img" aria-label={`Bar chart showing weekly work hours and 4-week rolling average from ${new Date(data[0].weekStart).toLocaleDateString()} to ${new Date(data[data.length - 1].weekEnd).toLocaleDateString()}`}>
        {/* Y-axis grid lines */}
        {[0, 20, 40, 60, 80, 100].map(value => {
          if (value > maxValue) return null;
          const top = chartHeight - (value / maxValue) * chartHeight;

          return (
            <div
              key={value}
              className="absolute left-0 right-0 border-t border-gray-200"
              style={{ top: `${top}px` }}
              aria-hidden="true"
            >
              <span className="absolute -left-8 -top-2 text-xs text-gray-500">
                {value}h
              </span>
            </div>
          );
        })}

        {/* 80-hour limit line */}
        {maxHours <= maxValue && (
          <div
            className="absolute left-0 right-0 border-t-2 border-red-500 border-dashed z-10"
            style={{ top: `${chartHeight - getBarHeight(maxHours)}px` }}
            aria-hidden="true"
          >
            <span className="absolute right-0 -top-5 text-xs text-red-600 font-semibold">
              80h Limit
            </span>
          </div>
        )}

        {/* Bars and Line */}
        <div className="absolute inset-0 flex items-end justify-around px-12">
          {data.map((week, idx) => {
            const barHeight = getBarHeight(week.hours);
            const avgHeight = getBarHeight(week.rollingAverage);

            return (
              <div
                key={idx}
                className="relative flex-1 flex flex-col items-center"
                style={{ maxWidth: '60px' }}
              >
                {/* Weekly Hours Bar */}
                <div
                  className={`w-full rounded-t transition-all ${getBarColor(week.hours)}`}
                  style={{ height: `${barHeight}px` }}
                  title={`Week ${idx + 1}: ${week.hours}h`}
                  aria-hidden="true"
                />

                {/* Rolling Average Dot */}
                <div
                  className="absolute w-3 h-3 bg-purple-500 rounded-full border-2 border-white"
                  style={{ bottom: `${avgHeight - 6}px` }}
                  title={`Rolling avg: ${week.rollingAverage.toFixed(1)}h`}
                  aria-hidden="true"
                />

                {/* Week Label */}
                <div className="mt-2 text-xs text-gray-600 text-center">
                  <div>{new Date(week.weekStart).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Rolling Average Line */}
        <svg
          className="absolute inset-0 pointer-events-none"
          style={{ paddingLeft: '48px', paddingRight: '48px' }}
          aria-hidden="true"
        >
          <polyline
            points={data.map((week, idx) => {
              const x = ((idx + 0.5) / data.length) * 100;
              const y = ((maxValue - week.rollingAverage) / maxValue) * chartHeight;
              return `${x}%,${y}`;
            }).join(' ')}
            fill="none"
            stroke="rgb(168, 85, 247)"
            strokeWidth="2"
            strokeDasharray="4"
          />
        </svg>
      </div>

      {/* Summary Stats */}
      <div className="mt-6 grid grid-cols-3 gap-4 text-center border-t pt-4">
        <div>
          <div className="text-2xl font-bold text-gray-900">
            {data[data.length - 1]?.hours.toFixed(1)}h
          </div>
          <div className="text-xs text-gray-600">Current Week</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-purple-600">
            {data[data.length - 1]?.rollingAverage.toFixed(1)}h
          </div>
          <div className="text-xs text-gray-600">Rolling Avg</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-gray-900">
            {maxHours}h
          </div>
          <div className="text-xs text-gray-600">Limit</div>
        </div>
      </div>
    </div>
  );
};

export default RollingAverageChart;
