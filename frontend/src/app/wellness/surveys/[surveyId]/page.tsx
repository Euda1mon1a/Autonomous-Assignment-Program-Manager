'use client';

/**
 * Individual Survey Page
 *
 * Renders a specific survey for completion.
 * Features:
 * - Question-by-question flow
 * - Progress indicator
 * - Score result on completion
 * - Achievement notifications
 *
 * @route /wellness/surveys/[surveyId]
 */

import React, { useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { useSurvey, useSubmitSurvey } from '@/features/wellness/hooks/useWellness';
import { SURVEY_TYPE_DISPLAY, type SurveyQuestion } from '@/features/wellness/types';

export default function SurveyPage() {
  const _router = useRouter();
  const params = useParams();
  const surveyId = params?.surveyId as string;

  const { data: survey, isLoading, error } = useSurvey(surveyId);
  const submitSurvey = useSubmitSurvey();

  const [currentIndex, setCurrentIndex] = useState(0);
  const [responses, setResponses] = useState<Record<string, number | string>>({});
  const [showResult, setShowResult] = useState(false);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-cyan-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="mt-4 text-gray-400">Loading survey...</p>
        </div>
      </div>
    );
  }

  if (error || !survey) {
    return (
      <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
        <div className="text-center">
          <p className="text-4xl mb-4">&#x26A0;</p>
          <p className="text-gray-400 mb-4">Survey not found or unavailable.</p>
          <Link
            href="/wellness"
            className="text-cyan-400 hover:text-cyan-300"
          >
            &larr; Back to Wellness Hub
          </Link>
        </div>
      </div>
    );
  }

  const questions = survey.questions || [];
  const currentQuestion = questions[currentIndex];
  const progress = questions.length > 0 ? ((currentIndex + 1) / questions.length) * 100 : 0;
  const isLastQuestion = currentIndex === questions.length - 1;
  const typeInfo = SURVEY_TYPE_DISPLAY[survey.surveyType] || {
    label: survey.surveyType,
    color: 'gray',
  };

  const handleResponse = (questionId: string, value: number | string) => {
    setResponses((prev) => ({ ...prev, [questionId]: value }));
  };

  const handleNext = async () => {
    if (isLastQuestion) {
      // Submit survey
      try {
        const result = await submitSurvey.mutateAsync({
          surveyId: survey.id,
          data: { responses },
        });

        if (result.success) {
          setShowResult(true);
        }
      } catch {
        // Error handled by mutation
      }
    } else {
      setCurrentIndex((prev) => prev + 1);
    }
  };

  const handlePrevious = () => {
    if (currentIndex > 0) {
      setCurrentIndex((prev) => prev - 1);
    }
  };

  const canProceed = currentQuestion && responses[currentQuestion.id] !== undefined;

  if (showResult && submitSurvey.data) {
    const result = submitSurvey.data;
    return (
      <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center p-6">
        <div className="max-w-md w-full text-center">
          {/* Success Animation */}
          <div className="w-20 h-20 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
            <span className="text-4xl">&#x2713;</span>
          </div>

          <h1 className="text-2xl font-bold mb-2">Survey Complete!</h1>
          <p className="text-gray-400 mb-6">{survey.displayName}</p>

          {/* Score */}
          {result.score !== undefined && result.score !== null && (
            <div className="bg-gray-800 rounded-lg p-6 mb-6">
              <p className="text-sm text-gray-400 mb-2">Your Score</p>
              <p className="text-4xl font-bold">{result.score}</p>
              {result.scoreInterpretation && (
                <p className={`text-lg capitalize mt-2 ${
                  result.scoreInterpretation === 'low' ? 'text-green-400' :
                  result.scoreInterpretation === 'moderate' ? 'text-yellow-400' :
                  'text-red-400'
                }`}>
                  {result.scoreInterpretation}
                </p>
              )}
            </div>
          )}

          {/* Points Earned */}
          <div className="flex items-center justify-center gap-2 text-amber-400 text-xl mb-6">
            <span>+{result.pointsEarned}</span>
            <span className="text-base text-gray-400">points earned</span>
          </div>

          {/* Streak Update */}
          {result.streakUpdated && result.currentStreak > 0 && (
            <div className="bg-orange-900/20 border border-orange-600/30 rounded-lg p-4 mb-6">
              <p className="text-orange-400 flex items-center justify-center gap-2">
                <span>&#x1F525;</span>
                {result.currentStreak}-week streak!
              </p>
            </div>
          )}

          {/* New Achievements */}
          {result.newAchievements && result.newAchievements.length > 0 && (
            <div className="bg-amber-900/20 border border-amber-600/30 rounded-lg p-4 mb-6">
              <p className="text-amber-400 font-medium mb-2">New Achievement!</p>
              {result.newAchievements.map((achievement) => (
                <p key={achievement} className="text-white capitalize">
                  {achievement.replace(/_/g, ' ')}
                </p>
              ))}
            </div>
          )}

          <Link
            href="/wellness"
            className="inline-block px-6 py-3 bg-cyan-600 hover:bg-cyan-500 text-white font-medium rounded-lg transition-colors"
          >
            Back to Wellness Hub
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-2xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <Link
              href="/wellness"
              className="text-gray-400 hover:text-white transition-colors"
            >
              &larr; Cancel
            </Link>
            <span
              className={`
                px-2 py-1 rounded text-xs font-medium
                bg-${typeInfo.color}-900/50 text-${typeInfo.color}-400
              `}
            >
              {typeInfo.label}
            </span>
          </div>
        </div>
      </header>

      {/* Progress Bar */}
      <div className="h-1 bg-gray-800">
        <div
          className="h-full bg-cyan-500 transition-all duration-300"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Survey Content */}
      <main className="max-w-2xl mx-auto px-6 py-8">
        {/* Survey Title */}
        <div className="text-center mb-8">
          <h1 className="text-xl font-semibold mb-2">{survey.displayName}</h1>
          {survey.instructions && (
            <p className="text-gray-400 text-sm">{survey.instructions}</p>
          )}
        </div>

        {/* Question */}
        {currentQuestion && (
          <QuestionRenderer
            question={currentQuestion}
            value={responses[currentQuestion.id]}
            onChange={(value) => handleResponse(currentQuestion.id, value)}
          />
        )}

        {/* Navigation */}
        <div className="flex items-center justify-between mt-8">
          <button
            onClick={handlePrevious}
            disabled={currentIndex === 0}
            className="px-4 py-2 text-gray-400 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed"
          >
            &larr; Previous
          </button>

          <span className="text-sm text-gray-500">
            {currentIndex + 1} of {questions.length}
          </span>

          <button
            onClick={handleNext}
            disabled={!canProceed || submitSurvey.isPending}
            className="px-6 py-2 bg-cyan-600 hover:bg-cyan-500 text-white font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {submitSurvey.isPending
              ? 'Submitting...'
              : isLastQuestion
              ? 'Submit'
              : 'Next'}
          </button>
        </div>
      </main>
    </div>
  );
}

// ============================================================================
// Question Renderer
// ============================================================================

function QuestionRenderer({
  question,
  value,
  onChange,
}: {
  question: SurveyQuestion;
  value: number | string | undefined;
  onChange: (value: number | string) => void;
}) {
  switch (question.questionType) {
    case 'likert':
    case 'multiple_choice':
      return (
        <div className="space-y-3">
          <h2 className="text-lg font-medium mb-6">{question.text}</h2>
          {question.options?.map((option) => (
            <button
              key={String(option.value)}
              onClick={() => onChange(option.value)}
              className={`
                w-full text-left px-4 py-3 rounded-lg border transition-all
                ${value === option.value
                  ? 'border-cyan-500 bg-cyan-900/30'
                  : 'border-gray-700 hover:border-gray-600 bg-gray-800'
                }
              `}
            >
              <div className="flex items-center gap-3">
                <div
                  className={`
                    w-5 h-5 rounded-full border-2 flex items-center justify-center
                    ${value === option.value
                      ? 'border-cyan-500 bg-cyan-500'
                      : 'border-gray-600'
                    }
                  `}
                >
                  {value === option.value && (
                    <div className="w-2 h-2 bg-white rounded-full" />
                  )}
                </div>
                <span>{option.label}</span>
              </div>
            </button>
          ))}
        </div>
      );

    case 'emoji_scale':
      return (
        <div>
          <h2 className="text-lg font-medium mb-6 text-center">{question.text}</h2>
          <div className="flex justify-center gap-4">
            {question.options?.map((option) => (
              <button
                key={String(option.value)}
                onClick={() => onChange(option.value)}
                className={`
                  w-16 h-16 rounded-full text-3xl transition-all
                  ${value === option.value
                    ? 'ring-4 ring-cyan-500 scale-110'
                    : 'hover:scale-105 hover:bg-gray-800'
                  }
                `}
                title={option.label}
              >
                {option.value === 1 && '&#x1F62B;'}
                {option.value === 2 && '&#x1F61F;'}
                {option.value === 3 && '&#x1F610;'}
                {option.value === 4 && '&#x1F642;'}
                {option.value === 5 && '&#x1F60A;'}
              </button>
            ))}
          </div>
          {value !== undefined && (
            <p className="text-center text-gray-400 mt-4">
              {question.options?.find((o) => o.value === value)?.label}
            </p>
          )}
        </div>
      );

    case 'slider':
      return (
        <div>
          <h2 className="text-lg font-medium mb-6">{question.text}</h2>
          <div className="px-4">
            <input
              type="range"
              min={question.minValue ?? 0}
              max={question.maxValue ?? 10}
              value={value as number ?? question.minValue ?? 0}
              onChange={(e) => onChange(parseInt(e.target.value))}
              className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-cyan-500"
            />
            <div className="flex justify-between text-sm text-gray-400 mt-2">
              <span>{question.minLabel ?? question.minValue ?? 0}</span>
              <span className="text-cyan-400 font-semibold">{value ?? '-'}</span>
              <span>{question.maxLabel ?? question.maxValue ?? 10}</span>
            </div>
          </div>
        </div>
      );

    case 'text':
      return (
        <div>
          <h2 className="text-lg font-medium mb-4">{question.text}</h2>
          <textarea
            value={value as string ?? ''}
            onChange={(e) => onChange(e.target.value)}
            className="w-full h-32 px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500 resize-none"
            placeholder="Enter your response..."
          />
        </div>
      );

    default:
      return (
        <div className="text-gray-400">
          Unknown question type: {question.questionType}
        </div>
      );
  }
}
