'use client';

import { useState } from 'react';
import {
  Calendar,
  Clock,
  Copy,
  Edit2,
  Eye,
  Globe,
  Lock,
  MoreVertical,
  Share2,
  Trash2,
  Users,
} from 'lucide-react';
import type { ScheduleTemplate } from '../types';
import { CATEGORY_COLORS, STATUS_COLORS, DAY_OF_WEEK_SHORT } from '../constants';

interface TemplateCardProps {
  template: ScheduleTemplate;
  onEdit?: (template: ScheduleTemplate) => void;
  onDelete?: (template: ScheduleTemplate) => void;
  onDuplicate?: (template: ScheduleTemplate) => void;
  onShare?: (template: ScheduleTemplate) => void;
  onPreview?: (template: ScheduleTemplate) => void;
  onApply?: (template: ScheduleTemplate) => void;
  showActions?: boolean;
}

export function TemplateCard({
  template,
  onEdit,
  onDelete,
  onDuplicate,
  onShare,
  onPreview,
  onApply,
  showActions = true,
}: TemplateCardProps) {
  const [showMenu, setShowMenu] = useState(false);

  const categoryColors = CATEGORY_COLORS[template.category];
  const statusColors = STATUS_COLORS[template.status];

  const VisibilityIcon = template.visibility === 'public'
    ? Globe
    : template.visibility === 'shared'
    ? Users
    : Lock;

  const handleMenuClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    setShowMenu(!showMenu);
  };

  const handleAction = (action: () => void) => {
    setShowMenu(false);
    action();
  };

  // Get day coverage summary
  const dayCoverage = template.patterns.reduce((acc, pattern) => {
    acc[pattern.dayOfWeek] = true;
    return acc;
  }, {} as Record<number, boolean>);

  return (
    <div
      className={`card hover:shadow-lg transition-all cursor-pointer border ${categoryColors.border}`}
      onClick={() => onPreview?.(template)}
    >
      {/* Header */}
      <div className="flex justify-between items-start mb-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="font-semibold text-gray-900 truncate">{template.name}</h3>
            <VisibilityIcon className="w-4 h-4 text-gray-400 flex-shrink-0" aria-hidden="true" />
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            <span
              className={`inline-block px-2 py-0.5 rounded text-xs ${categoryColors.bg} ${categoryColors.text}`}
            >
              {template.category}
            </span>
            <span
              className={`inline-block px-2 py-0.5 rounded text-xs ${statusColors.bg} ${statusColors.text}`}
            >
              {template.status}
            </span>
          </div>
        </div>

        {showActions && (
          <div className="relative">
            <button
              onClick={handleMenuClick}
              className="p-1 hover:bg-gray-100 rounded"
              aria-label="Template actions"
              aria-haspopup="menu"
              aria-expanded={showMenu}
            >
              <MoreVertical className="w-4 h-4 text-gray-500" aria-hidden="true" />
            </button>

            {showMenu && (
              <>
                <div
                  className="fixed inset-0 z-10"
                  onClick={() => setShowMenu(false)}
                />
                <div className="absolute right-0 top-full mt-1 w-48 bg-white rounded-lg shadow-lg border z-20 py-1" role="menu">
                  {onPreview && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleAction(() => onPreview(template));
                      }}
                      className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 flex items-center gap-2"
                      role="menuitem"
                    >
                      <Eye className="w-4 h-4" aria-hidden="true" />
                      Preview
                    </button>
                  )}
                  {onEdit && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleAction(() => onEdit(template));
                      }}
                      className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 flex items-center gap-2"
                      role="menuitem"
                    >
                      <Edit2 className="w-4 h-4" aria-hidden="true" />
                      Edit
                    </button>
                  )}
                  {onDuplicate && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleAction(() => onDuplicate(template));
                      }}
                      className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 flex items-center gap-2"
                      role="menuitem"
                    >
                      <Copy className="w-4 h-4" aria-hidden="true" />
                      Duplicate
                    </button>
                  )}
                  {onShare && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleAction(() => onShare(template));
                      }}
                      className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 flex items-center gap-2"
                      role="menuitem"
                    >
                      <Share2 className="w-4 h-4" aria-hidden="true" />
                      Share
                    </button>
                  )}
                  {onDelete && (
                    <>
                      <hr className="my-1" />
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleAction(() => onDelete(template));
                        }}
                        className="w-full px-4 py-2 text-left text-sm hover:bg-red-50 text-red-600 flex items-center gap-2"
                        role="menuitem"
                      >
                        <Trash2 className="w-4 h-4" aria-hidden="true" />
                        Delete
                      </button>
                    </>
                  )}
                </div>
              </>
            )}
          </div>
        )}
      </div>

      {/* Description */}
      {template.description && (
        <p className="text-sm text-gray-600 mb-3 line-clamp-2">{template.description}</p>
      )}

      {/* Stats */}
      <div className="grid grid-cols-2 gap-2 text-sm mb-3">
        <div className="flex items-center gap-1.5 text-gray-600">
          <Calendar className="w-4 h-4" aria-hidden="true" />
          <span>{template.durationWeeks} week{template.durationWeeks !== 1 ? 's' : ''}</span>
        </div>
        <div className="flex items-center gap-1.5 text-gray-600">
          <Clock className="w-4 h-4" aria-hidden="true" />
          <span>{template.patterns.length} patterns</span>
        </div>
      </div>

      {/* Day coverage indicators */}
      <div className="flex gap-1 mb-3">
        {DAY_OF_WEEK_SHORT.map((day, index) => (
          <div
            key={day}
            className={`flex-1 text-center py-1 rounded text-xs font-medium ${
              dayCoverage[index]
                ? `${categoryColors.bg} ${categoryColors.text}`
                : 'bg-gray-50 text-gray-400'
            }`}
          >
            {day.charAt(0)}
          </div>
        ))}
      </div>

      {/* Tags */}
      {template.tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-3">
          {template.tags.slice(0, 3).map((tag) => (
            <span
              key={tag}
              className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs"
            >
              #{tag}
            </span>
          ))}
          {template.tags.length > 3 && (
            <span className="px-2 py-0.5 text-gray-500 text-xs">
              +{template.tags.length - 3} more
            </span>
          )}
        </div>
      )}

      {/* Footer */}
      <div className="flex justify-between items-center pt-3 border-t text-xs text-gray-500">
        <span>Used {template.usageCount} times</span>
        {onApply && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onApply(template);
            }}
            className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
            aria-label={`Apply template ${template.name}`}
          >
            Apply
          </button>
        )}
      </div>
    </div>
  );
}
