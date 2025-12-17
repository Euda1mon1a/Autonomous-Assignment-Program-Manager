/**
 * Heatmap View Component
 *
 * Main visualization component that renders the interactive Plotly heatmap
 * with hover tooltips, click handlers, and responsive sizing.
 */

'use client';

import React, { useMemo } from 'react';
import dynamic from 'next/dynamic';
import { Loader2, AlertCircle } from 'lucide-react';
import type { HeatmapData, HeatmapCellClickData } from './types';

// Dynamically import Plotly to avoid SSR issues
const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

export interface HeatmapViewProps {
  data: HeatmapData;
  onCellClick?: (cellData: HeatmapCellClickData) => void;
  isLoading?: boolean;
  error?: Error | null;
  height?: number | string;
  width?: number | string;
}

export function HeatmapView({
  data,
  onCellClick,
  isLoading = false,
  error = null,
  height = 600,
  width = '100%',
}: HeatmapViewProps) {
  // Prepare Plotly data configuration
  const plotData = useMemo(() => {
    if (!data || !data.z_values || data.z_values.length === 0) {
      return [];
    }

    const colorscale = data.color_scale?.colors
      ? data.color_scale.colors.map((color, index, arr) => [
          index / (arr.length - 1),
          color,
        ])
      : [
          [0, '#ef4444'],
          [0.5, '#fbbf24'],
          [1, '#22c55e'],
        ];

    return [
      {
        type: 'heatmap' as const,
        x: data.x_labels,
        y: data.y_labels,
        z: data.z_values,
        colorscale: colorscale,
        colorbar: {
          title: {
            text: data.color_scale?.labels?.[1] || 'Value',
            side: 'right',
          },
          tickvals: data.color_scale
            ? [data.color_scale.min, data.color_scale.max]
            : undefined,
          ticktext: data.color_scale?.labels
            ? [data.color_scale.labels[0], data.color_scale.labels[data.color_scale.labels.length - 1]]
            : undefined,
        },
        hovertemplate:
          '<b>%{x}</b><br>' +
          '<b>%{y}</b><br>' +
          'Value: %{z}<br>' +
          '<extra></extra>',
        showscale: true,
      },
    ];
  }, [data]);

  // Prepare Plotly layout configuration
  const plotLayout = useMemo(() => {
    return {
      title: {
        text: data?.title || '',
        font: {
          size: 16,
          color: '#374151',
        },
      },
      xaxis: {
        title: {
          text: data?.x_axis_label || '',
          font: {
            size: 12,
            color: '#6b7280',
          },
        },
        tickangle: -45,
        side: 'bottom' as const,
        automargin: true,
      },
      yaxis: {
        title: {
          text: data?.y_axis_label || '',
          font: {
            size: 12,
            color: '#6b7280',
          },
        },
        automargin: true,
      },
      margin: {
        l: 120,
        r: 80,
        t: 80,
        b: 120,
      },
      paper_bgcolor: 'white',
      plot_bgcolor: 'white',
      annotations: data?.annotations || [],
      autosize: true,
    };
  }, [data]);

  // Plotly configuration
  const plotConfig = useMemo(() => {
    return {
      responsive: true,
      displayModeBar: true,
      displaylogo: false,
      modeBarButtonsToRemove: [
        'pan2d',
        'select2d',
        'lasso2d',
        'autoScale2d',
        'toggleSpikelines',
      ],
      toImageButtonOptions: {
        format: 'png' as const,
        filename: 'heatmap',
        height: 800,
        width: 1200,
        scale: 2,
      },
    };
  }, []);

  // Handle cell click events
  const handleClick = (event: any) => {
    if (!onCellClick || !event.points || event.points.length === 0) {
      return;
    }

    const point = event.points[0];
    const cellData: HeatmapCellClickData = {
      x: point.x,
      y: point.y,
      value: point.z,
      pointIndex: [point.pointIndex[0], point.pointIndex[1]],
    };

    onCellClick(cellData);
  };

  // Loading state
  if (isLoading) {
    return (
      <div
        className="flex items-center justify-center bg-gray-50 rounded-lg border border-gray-200"
        style={{ height }}
      >
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
          <p className="text-sm text-gray-600">Loading heatmap...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div
        className="flex items-center justify-center bg-red-50 rounded-lg border border-red-200"
        style={{ height }}
      >
        <div className="flex flex-col items-center gap-3 p-6 text-center">
          <AlertCircle className="w-8 h-8 text-red-600" />
          <div>
            <p className="text-sm font-medium text-red-900">Failed to load heatmap</p>
            <p className="text-sm text-red-700 mt-1">{error.message}</p>
          </div>
        </div>
      </div>
    );
  }

  // Empty data state
  if (!data || !data.z_values || data.z_values.length === 0) {
    return (
      <div
        className="flex items-center justify-center bg-gray-50 rounded-lg border border-gray-200"
        style={{ height }}
      >
        <div className="flex flex-col items-center gap-3 p-6 text-center">
          <AlertCircle className="w-8 h-8 text-gray-400" />
          <div>
            <p className="text-sm font-medium text-gray-900">No data available</p>
            <p className="text-sm text-gray-600 mt-1">
              Adjust your filters or date range to view data
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Render heatmap
  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
      <Plot
        data={plotData}
        layout={plotLayout}
        config={plotConfig}
        onClick={handleClick}
        style={{ width, height }}
        useResizeHandler={true}
        className="w-full"
      />
    </div>
  );
}

/**
 * Skeleton loader for heatmap
 */
export function HeatmapViewSkeleton({ height = 600 }: { height?: number | string }) {
  return (
    <div
      className="bg-gray-50 rounded-lg border border-gray-200 animate-pulse"
      style={{ height }}
    >
      <div className="p-6 space-y-4">
        <div className="h-6 bg-gray-200 rounded w-1/3" />
        <div className="grid grid-cols-10 gap-2">
          {Array.from({ length: 50 }).map((_, i) => (
            <div key={i} className="h-12 bg-gray-200 rounded" />
          ))}
        </div>
      </div>
    </div>
  );
}
