'use client';

import { useState, useMemo } from 'react';
import {
  Calendar,
  Clock,
  AlertTriangle,
  CheckCircle,
  ChevronLeft,
  ChevronRight,
  X,
  Play,
} from 'lucide-react';
import type { ScheduleTemplate, AssignmentPattern, TemplatePreviewConfig } from '../types';
import {
  DAY_OF_WEEK_LABELS,
  DAY_OF_WEEK_SHORT,
  CATEGORY_COLORS,
} from '../constants';

interface TemplatePreviewProps {
  template: ScheduleTemplate;
  onApply?: (config: TemplatePreviewConfig) => void;
  onClose?: () => void;
  isLoading?: boolean;
}

export function TemplatePreview({
  template,
  onApply,
  onClose,
  isLoading = false,
}: TemplatePreviewProps) {
  const [startDate, setStartDate] = useState(() => {
    const today = new Date();
    // Start from next occurrence of the template's start day
    const daysUntilStart = (template.startDayOfWeek - today.getDay() + 7) % 7 || 7;
    const start = new Date(today);
    start.setDate(today.getDate() + daysUntilStart);
    return start;
  });
  const [showConflicts, setShowConflicts] = useState(true);
  const [highlightPatterns, setHighlightPatterns] = useState(true);

  const categoryColors = CATEGORY_COLORS[template.category];

  // Calculate end date based on duration
  const endDate = useMemo(() => {
    const end = new Date(startDate);
    end.setDate(startDate.getDate() + template.durationWeeks * 7 - 1);
    return end;
  }, [startDate, template.durationWeeks]);

  // Generate preview calendar data
  const calendarWeeks = useMemo(() => {
    const weeks: Date[][] = [];
    const current = new Date(startDate);

    for (let week = 0; week < template.durationWeeks; week++) {
      const weekDays: Date[] = [];
      for (let day = 0; day < 7; day++) {
        weekDays.push(new Date(current));
        current.setDate(current.getDate() + 1);
      }
      weeks.push(weekDays);
    }

    return weeks;
  }, [startDate, template.durationWeeks]);

  // Get patterns for a specific day
  const getPatternsForDay = (dayOfWeek: number): AssignmentPattern[] => {
    return template.patterns.filter((p) => p.dayOfWeek === dayOfWeek);
  };

  const handleApply = () => {
    onApply?.({
      startDate,
      endDate,
      showConflicts,
      highlightPatterns,
    });
  };

  const handlePreviousWeek = () => {
    const newStart = new Date(startDate);
    newStart.setDate(startDate.getDate() - 7);
    setStartDate(newStart);
  };

  const handleNextWeek = () => {
    const newStart = new Date(startDate);
    newStart.setDate(startDate.getDate() + 7);
    setStartDate(newStart);
  };

  const formatDate = (date: Date): string => {
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  // Pattern summary
  const patternSummary = useMemo(() => {
    const byDay = template.patterns.reduce((acc, p) => {
      acc[p.dayOfWeek] = (acc[p.dayOfWeek] || 0) + 1;
      return acc;
    }, {} as Record<number, number>);

    const byActivity = template.patterns.reduce((acc, p) => {
      acc[p.activityType] = (acc[p.activityType] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return { byDay, byActivity };
  }, [template.patterns]);

  return (
    <div className="bg-white rounded-lg shadow-lg max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col" role="dialog" aria-labelledby="template-preview-title" aria-modal="true">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b">
        <div>
          <h2 id="template-preview-title" className="text-lg font-semibold">{template.name}</h2>
          <p className="text-sm text-gray-500">Preview and apply template</p>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded"
            aria-label="Close preview"
          >
            <X className="w-5 h-5" aria-hidden="true" />
          </button>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {/* Template Info */}
        <div className={`p-4 rounded-lg ${categoryColors.bg} ${categoryColors.border} border`}>
          <div className="flex flex-wrap gap-4 text-sm">
            <div className="flex items-center gap-2">
              <Calendar className={`w-4 h-4 ${categoryColors.text}`} aria-hidden="true" />
              <span>
                {template.durationWeeks} week{template.durationWeeks !== 1 ? 's' : ''}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <Clock className={`w-4 h-4 ${categoryColors.text}`} aria-hidden="true" />
              <span>{template.patterns.length} patterns</span>
            </div>
            {template.requiresSupervision && (
              <div className="flex items-center gap-2 text-amber-600">
                <AlertTriangle className="w-4 h-4" aria-hidden="true" />
                <span>Requires supervision</span>
              </div>
            )}
          </div>
          {template.description && (
            <p className="mt-2 text-sm text-gray-600">{template.description}</p>
          )}
        </div>

        {/* Date Selection */}
        <div className="space-y-3">
          <h3 className="font-medium">Application Period</h3>
          <div className="flex items-center gap-4">
            <button
              onClick={handlePreviousWeek}
              className="p-2 hover:bg-gray-100 rounded"
              aria-label="Previous week"
              title="Previous week"
            >
              <ChevronLeft className="w-5 h-5" aria-hidden="true" />
            </button>

            <div className="flex-1 text-center">
              <div className="font-medium">
                {formatDate(startDate)} - {formatDate(endDate)}
              </div>
              <div className="text-sm text-gray-500">
                {template.durationWeeks} week{template.durationWeeks !== 1 ? 's' : ''}
              </div>
            </div>

            <button
              onClick={handleNextWeek}
              className="p-2 hover:bg-gray-100 rounded"
              aria-label="Next week"
              title="Next week"
            >
              <ChevronRight className="w-5 h-5" aria-hidden="true" />
            </button>
          </div>

          <div className="flex items-center gap-4">
            <label className="block text-sm">
              <span className="text-gray-600">Start Date:</span>
              <input
                type="date"
                value={startDate.toISOString().split('T')[0]}
                onChange={(e) => setStartDate(new Date(e.target.value))}
                className="ml-2 px-2 py-1 border rounded"
              />
            </label>
          </div>
        </div>

        {/* Preview Options */}
        <div className="flex gap-4">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={showConflicts}
              onChange={(e) => setShowConflicts(e.target.checked)}
              className="rounded border-gray-300"
            />
            <span className="text-sm text-gray-700">Show potential conflicts</span>
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={highlightPatterns}
              onChange={(e) => setHighlightPatterns(e.target.checked)}
              className="rounded border-gray-300"
            />
            <span className="text-sm text-gray-700">Highlight patterns</span>
          </label>
        </div>

        {/* Calendar Preview */}
        <div className="space-y-2">
          <h3 className="font-medium">Schedule Preview</h3>
          <div className="border rounded-lg overflow-hidden">
            {/* Day headers */}
            <div className="grid grid-cols-7 bg-gray-50 border-b">
              {DAY_OF_WEEK_SHORT.map((day, index) => (
                <div
                  key={day}
                  className={`py-2 text-center text-sm font-medium ${
                    index === 0 || index === 6 ? 'text-gray-400' : 'text-gray-700'
                  }`}
                >
                  {day}
                </div>
              ))}
            </div>

            {/* Week rows */}
            {calendarWeeks.map((week, weekIndex) => (
              <div key={weekIndex} className="grid grid-cols-7 border-b last:border-b-0">
                {week.map((date, dayIndex) => {
                  const patterns = getPatternsForDay(dayIndex);
                  const isWeekend = dayIndex === 0 || dayIndex === 6;
                  const hasPatterns = patterns.length > 0;

                  return (
                    <div
                      key={date.toISOString()}
                      className={`min-h-[80px] p-1 border-r last:border-r-0 ${
                        isWeekend && !template.allowWeekends
                          ? 'bg-gray-50'
                          : hasPatterns && highlightPatterns
                          ? categoryColors.bg
                          : ''
                      }`}
                    >
                      <div
                        className={`text-xs font-medium mb-1 ${
                          isWeekend ? 'text-gray-400' : 'text-gray-600'
                        }`}
                      >
                        {date.getDate()}
                      </div>

                      {hasPatterns && (
                        <div className="space-y-0.5">
                          {patterns.slice(0, 3).map((pattern) => (
                            <div
                              key={pattern.id}
                              className={`text-xs px-1 py-0.5 rounded truncate ${
                                highlightPatterns
                                  ? `${categoryColors.text} bg-white/50`
                                  : 'bg-gray-100 text-gray-600'
                              }`}
                              title={`${pattern.name} (${pattern.timeOfDay})`}
                            >
                              {pattern.timeOfDay !== 'ALL' && (
                                <span className="font-medium">{pattern.timeOfDay}: </span>
                              )}
                              {pattern.name}
                            </div>
                          ))}
                          {patterns.length > 3 && (
                            <div className="text-xs text-gray-500 px-1">
                              +{patterns.length - 3} more
                            </div>
                          )}
                        </div>
                      )}

                      {isWeekend && !template.allowWeekends && !hasPatterns && (
                        <div className="text-xs text-gray-400 italic">No coverage</div>
                      )}
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
        </div>

        {/* Pattern Summary */}
        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 bg-gray-50 rounded-lg">
            <h4 className="font-medium text-sm mb-2">Patterns by Day</h4>
            <div className="space-y-1">
              {DAY_OF_WEEK_LABELS.map((day, index) => (
                <div key={day} className="flex justify-between text-sm">
                  <span className="text-gray-600">{day}</span>
                  <span className="font-medium">{patternSummary.byDay[index] || 0}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="p-4 bg-gray-50 rounded-lg">
            <h4 className="font-medium text-sm mb-2">Patterns by Activity</h4>
            <div className="space-y-1">
              {Object.entries(patternSummary.byActivity).map(([activity, count]) => (
                <div key={activity} className="flex justify-between text-sm">
                  <span className="text-gray-600 capitalize">{activity}</span>
                  <span className="font-medium">{count}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Validation Messages */}
        <div className="space-y-2">
          {!template.allowWeekends && (
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <CheckCircle className="w-4 h-4 text-green-500" aria-hidden="true" />
              Weekend assignments excluded
            </div>
          )}
          {!template.allowHolidays && (
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <CheckCircle className="w-4 h-4 text-green-500" aria-hidden="true" />
              Holiday assignments excluded
            </div>
          )}
          {template.requiresSupervision && (
            <div className="flex items-center gap-2 text-sm text-amber-600">
              <AlertTriangle className="w-4 h-4" aria-hidden="true" />
              Supervision required for all assignments
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      {onApply && (
        <div className="p-4 border-t flex justify-end gap-3">
          {onClose && (
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg"
              aria-label="Cancel"
            >
              Cancel
            </button>
          )}
          <button
            onClick={handleApply}
            disabled={isLoading}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            aria-label="Apply template"
          >
            <Play className="w-4 h-4" aria-hidden="true" />
            {isLoading ? 'Applying...' : 'Apply Template'}
          </button>
        </div>
      )}
    </div>
  );
}

interface PatternPreviewGridProps {
  patterns: AssignmentPattern[];
  highlightPatterns?: boolean;
}

export function PatternPreviewGrid({
  patterns,
  highlightPatterns = true,
}: PatternPreviewGridProps) {
  const patternsByDay = patterns.reduce((acc, pattern) => {
    const day = pattern.dayOfWeek;
    if (!acc[day]) acc[day] = { AM: [], PM: [], ALL: [] };
    acc[day][pattern.timeOfDay].push(pattern);
    return acc;
  }, {} as Record<number, Record<'AM' | 'PM' | 'ALL', AssignmentPattern[]>>);

  return (
    <div className="border rounded-lg overflow-hidden">
      <div className="grid grid-cols-8 bg-gray-50 border-b">
        <div className="py-2 px-2 text-sm font-medium text-gray-500">Time</div>
        {DAY_OF_WEEK_SHORT.map((day) => (
          <div key={day} className="py-2 text-center text-sm font-medium text-gray-700">
            {day}
          </div>
        ))}
      </div>

      {(['AM', 'PM', 'ALL'] as const).map((timeOfDay) => (
        <div key={timeOfDay} className="grid grid-cols-8 border-b last:border-b-0">
          <div className="py-2 px-2 text-sm font-medium text-gray-500 border-r bg-gray-50">
            {timeOfDay === 'ALL' ? 'All Day' : timeOfDay}
          </div>
          {[0, 1, 2, 3, 4, 5, 6].map((dayIndex) => {
            const dayPatterns = patternsByDay[dayIndex]?.[timeOfDay] || [];
            return (
              <div
                key={dayIndex}
                className={`py-2 px-1 border-r last:border-r-0 ${
                  dayPatterns.length > 0 && highlightPatterns ? 'bg-blue-50' : ''
                }`}
              >
                {dayPatterns.map((pattern) => (
                  <div
                    key={pattern.id}
                    className="text-xs px-1 py-0.5 bg-blue-100 text-blue-700 rounded mb-0.5 truncate"
                    title={pattern.name}
                  >
                    {pattern.name}
                  </div>
                ))}
              </div>
            );
          })}
        </div>
      ))}
    </div>
  );
}
