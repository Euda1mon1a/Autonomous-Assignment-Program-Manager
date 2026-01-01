/**
 * BlockCard Component
 *
 * Displays an individual block/assignment with rotation information,
 * time indicators, and drag-drop support.
 */

import React from 'react';
import { Badge } from '../ui/Badge';

export interface BlockCardProps {
  blockId: string;
  personName: string;
  rotationType: string;
  date: string;
  shift: 'AM' | 'PM' | 'Night';
  duration?: number; // hours
  isConflict?: boolean;
  isWarning?: boolean;
  isDraggable?: boolean;
  onDragStart?: (e: React.DragEvent) => void;
  onDragEnd?: (e: React.DragEvent) => void;
  onClick?: () => void;
  className?: string;
}

const rotationColors: Record<string, string> = {
  clinic: 'bg-blue-100 border-blue-300 text-blue-800',
  inpatient: 'bg-purple-100 border-purple-300 text-purple-800',
  procedures: 'bg-green-100 border-green-300 text-green-800',
  conference: 'bg-yellow-100 border-yellow-300 text-yellow-800',
  call: 'bg-red-100 border-red-300 text-red-800',
  fmit: 'bg-indigo-100 border-indigo-300 text-indigo-800',
  tdy: 'bg-gray-100 border-gray-300 text-gray-800',
  deployment: 'bg-orange-100 border-orange-300 text-orange-800',
  default: 'bg-slate-100 border-slate-300 text-slate-800',
};

const shiftIcons: Record<string, string> = {
  AM: '☀️',
  PM: '🌤️',
  Night: '🌙',
};

export const BlockCard: React.FC<BlockCardProps> = ({
  blockId,
  personName,
  rotationType,
  date,
  shift,
  duration,
  isConflict = false,
  isWarning = false,
  isDraggable = true,
  onDragStart,
  onDragEnd,
  onClick,
  className = '',
}) => {
  const rotationKey = rotationType.toLowerCase();
  const colorClass = rotationColors[rotationKey] || rotationColors.default;

  const handleDragStart = (e: React.DragEvent) => {
    if (!isDraggable) {
      e.preventDefault();
      return;
    }
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('application/json', JSON.stringify({
      blockId,
      personName,
      rotationType,
      date,
      shift,
    }));
    onDragStart?.(e);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onClick?.();
    }
  };

  return (
    <div
      draggable={isDraggable}
      onDragStart={handleDragStart}
      onDragEnd={onDragEnd}
      onClick={onClick}
      onKeyDown={handleKeyDown}
      role="button"
      tabIndex={0}
      aria-label={`Block assignment: ${personName}, ${rotationType}, ${shift} shift on ${date}`}
      className={`
        relative rounded-lg border-2 p-3 transition-all duration-200
        ${colorClass}
        ${isDraggable ? 'cursor-move hover:shadow-md' : 'cursor-pointer'}
        ${isConflict ? 'ring-2 ring-red-500 ring-offset-2' : ''}
        ${isWarning ? 'ring-2 ring-yellow-500 ring-offset-2' : ''}
        ${onClick ? 'hover:scale-105 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2' : ''}
        ${className}
      `}
    >
      {/* Conflict/Warning Indicator */}
      {(isConflict || isWarning) && (
        <div className="absolute -top-2 -right-2">
          <Badge variant={isConflict ? 'destructive' : 'warning'}>
            <span aria-hidden="true">{isConflict ? '⚠️' : '⚡'}</span>
            <span className="sr-only">{isConflict ? 'Conflict detected' : 'Warning'}</span>
          </Badge>
        </div>
      )}

      {/* Shift Indicator */}
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-semibold uppercase tracking-wide">
          {shift}
        </span>
        <span className="text-lg" role="img" aria-label={`${shift} shift`}>
          {shiftIcons[shift]}
        </span>
      </div>

      {/* Person Name */}
      <div className="font-medium text-sm mb-1 truncate" title={personName}>
        {personName}
      </div>

      {/* Rotation Type */}
      <div className="text-xs font-semibold mb-1">
        {rotationType}
      </div>

      {/* Duration (if provided) */}
      {duration && (
        <div className="text-xs text-gray-600 mt-2">
          {duration}h
        </div>
      )}

      {/* Date */}
      <div className="text-xs text-gray-500 mt-1">
        {new Date(date).toLocaleDateString('en-US', {
          month: 'short',
          day: 'numeric',
        })}
      </div>
    </div>
  );
};

export default BlockCard;
