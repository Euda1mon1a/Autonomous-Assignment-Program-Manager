'use client';

/**
 * QuickPulseWidget - Dashboard widget for quick wellness check-ins
 *
 * Embedded in the main dashboard, shows:
 * - Quick mood selector (emoji scale)
 * - Current streak and points
 * - Available surveys (top 3)
 * - Recent achievements
 */

import React, { useState } from 'react';
import Link from 'next/link';
import { useWidgetData, useSubmitPulse } from '../hooks/useWellness';
import type { QuickPulseSubmit } from '../types';
import { MOOD_EMOJIS, SURVEY_TYPE_DISPLAY } from '../types';

interface QuickPulseWidgetProps {
  className?: string;
}

export function QuickPulseWidget({ className = '' }: QuickPulseWidgetProps) {
  const { data: widgetData, isLoading } = useWidgetData();
  const submitPulse = useSubmitPulse();
  const [selectedMood, setSelectedMood] = useState<1 | 2 | 3 | 4 | 5 | null>(null);
  const [showSuccess, setShowSuccess] = useState(false);

  const handleMoodSelect = async (mood: 1 | 2 | 3 | 4 | 5) => {
    setSelectedMood(mood);

    try {
      const data: QuickPulseSubmit = { mood };
      await submitPulse.mutateAsync(data);
      setShowSuccess(true);
      setTimeout(() => {
        setShowSuccess(false);
        setSelectedMood(null);
      }, 2000);
    } catch {
      // Error handled by mutation
      setSelectedMood(null);
    }
  };

  if (isLoading) {
    return (
      <div className={`bg-gray-800 rounded-lg p-4 ${className}`}>
        <div className="animate-pulse">
          <div className="h-4 bg-gray-700 rounded w-1/2 mb-4" />
          <div className="flex gap-2 justify-center">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="w-10 h-10 bg-gray-700 rounded-full" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-gradient-to-br from-gray-800 to-gray-900 rounded-lg p-4 border border-gray-700 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium text-gray-300 flex items-center gap-2">
          <span className="text-lg">&#x1F321;</span>
          Quick Pulse
        </h3>
        <div className="flex items-center gap-2 text-xs">
          <span className="text-amber-400">
            {widgetData?.pointsBalance ?? 0} pts
          </span>
          {(widgetData?.currentStreak ?? 0) > 0 && (
            <span className="text-orange-400 flex items-center gap-1">
              <span>&#x1F525;</span>
              {widgetData?.currentStreak}w
            </span>
          )}
        </div>
      </div>

      {/* Mood Selector */}
      <div className="text-center mb-4">
        <p className="text-xs text-gray-400 mb-2">How are you feeling?</p>
        <div className="flex gap-2 justify-center">
          {([1, 2, 3, 4, 5] as const).map((mood) => {
            const { label } = MOOD_EMOJIS[mood];
            const isSelected = selectedMood === mood;
            const isDisabled = submitPulse.isPending || !widgetData?.canSubmit;

            return (
              <button
                key={mood}
                onClick={() => handleMoodSelect(mood)}
                disabled={isDisabled}
                className={`
                  w-10 h-10 rounded-full text-2xl transition-all duration-200
                  ${isSelected
                    ? 'ring-2 ring-cyan-400 scale-110'
                    : 'hover:scale-105 hover:bg-gray-700'
                  }
                  ${isDisabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                `}
                title={label}
              >
                {mood === 1 && '&#x1F62B;'}
                {mood === 2 && '&#x1F61F;'}
                {mood === 3 && '&#x1F610;'}
                {mood === 4 && '&#x1F642;'}
                {mood === 5 && '&#x1F60A;'}
              </button>
            );
          })}
        </div>
        {showSuccess && (
          <p className="text-xs text-green-400 mt-2">
            +{submitPulse.data?.pointsEarned ?? 10} pts
          </p>
        )}
      </div>

      {/* Available Surveys */}
      {widgetData?.availableSurveys && widgetData.availableSurveys.length > 0 && (
        <div className="mb-3">
          <p className="text-xs text-gray-500 uppercase tracking-wide mb-2">
            Available Surveys
          </p>
          <div className="flex flex-wrap gap-2">
            {widgetData.availableSurveys.map((survey) => {
              const typeInfo = SURVEY_TYPE_DISPLAY[survey.surveyType] || {
                label: survey.surveyType,
                color: 'gray',
              };
              return (
                <Link
                  key={survey.id}
                  href={`/wellness/surveys/${survey.id}`}
                  className={`
                    px-2 py-1 rounded text-xs
                    bg-${typeInfo.color}-900/30 text-${typeInfo.color}-400
                    border border-${typeInfo.color}-800/50
                    hover:bg-${typeInfo.color}-900/50 transition-colors
                  `}
                >
                  {survey.displayName}
                  <span className="ml-1 opacity-60">+{survey.pointsValue}</span>
                </Link>
              );
            })}
          </div>
        </div>
      )}

      {/* Recent Achievements */}
      {widgetData?.recentAchievements && widgetData.recentAchievements.length > 0 && (
        <div className="border-t border-gray-700 pt-2">
          <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">
            Recent
          </p>
          <div className="flex gap-2">
            {widgetData.recentAchievements.map((achievement) => (
              <span
                key={achievement.code}
                className="text-xs bg-amber-900/30 text-amber-400 px-2 py-0.5 rounded"
                title={achievement.description}
              >
                {achievement.name}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Link to full page */}
      <Link
        href="/wellness"
        className="block text-center text-xs text-cyan-400 hover:text-cyan-300 mt-3"
      >
        View Wellness Hub &rarr;
      </Link>
    </div>
  );
}

export default QuickPulseWidget;
