'use client';

import React from 'react';
import { RotationBadge, RotationType } from './RotationBadge';

export interface TimelineBlock {
  id: string;
  startDate: Date;
  endDate: Date;
  rotation: RotationType;
  label: string;
  person?: string;
}

export interface BlockTimelineProps {
  blocks: TimelineBlock[];
  startDate: Date;
  endDate: Date;
  showLabels?: boolean;
  className?: string;
}

/**
 * BlockTimeline component for visualizing schedule blocks over time
 *
 * @example
 * ```tsx
 * <BlockTimeline
 *   blocks={scheduleBlocks}
 *   startDate={new Date('2025-01-01')}
 *   endDate={new Date('2025-12-31')}
 *   showLabels
 * />
 * ```
 */
export function BlockTimeline({
  blocks,
  startDate,
  endDate,
  showLabels = true,
  className = '',
}: BlockTimelineProps) {
  const totalDays = Math.ceil(
    (endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24)
  );

  const getBlockPosition = (block: TimelineBlock) => {
    const blockStart = Math.max(block.startDate.getTime(), startDate.getTime());
    const blockEnd = Math.min(block.endDate.getTime(), endDate.getTime());

    const start = (blockStart - startDate.getTime()) / (1000 * 60 * 60 * 24);
    const duration = (blockEnd - blockStart) / (1000 * 60 * 60 * 24);

    return {
      left: `${(start / totalDays) * 100}%`,
      width: `${(duration / totalDays) * 100}%`,
    };
  };

  return (
    <div className={`relative ${className}`}>
      {/* Timeline Bar */}
      <div className="relative h-12 bg-gray-100 rounded-lg overflow-hidden">
        {blocks.map((block) => {
          const position = getBlockPosition(block);

          return (
            <div
              key={block.id}
              className="absolute h-full"
              style={position}
            >
              <div className="h-full p-1">
                <RotationBadge
                  type={block.rotation}
                  label={showLabels ? block.label : ''}
                  size="sm"
                  className="h-full flex items-center justify-center overflow-hidden text-ellipsis whitespace-nowrap"
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* Date Labels */}
      <div className="flex justify-between mt-2 text-xs text-gray-600">
        <span>{startDate.toLocaleDateString()}</span>
        <span>{endDate.toLocaleDateString()}</span>
      </div>
    </div>
  );
}

/**
 * Multi-person timeline view
 */
export function MultiPersonTimeline({
  timelines,
  startDate,
  endDate,
  className = '',
}: {
  timelines: Array<{
    personId: string;
    personName: string;
    blocks: TimelineBlock[];
  }>;
  startDate: Date;
  endDate: Date;
  className?: string;
}) {
  return (
    <div className={`space-y-4 ${className}`}>
      {timelines.map((timeline) => (
        <div key={timeline.personId}>
          <h4 className="text-sm font-medium text-gray-900 mb-2">
            {timeline.personName}
          </h4>
          <BlockTimeline
            blocks={timeline.blocks}
            startDate={startDate}
            endDate={endDate}
            showLabels={false}
          />
        </div>
      ))}
    </div>
  );
}
