'use client';

/**
 * Wellness Hub Page
 *
 * Main page for the gamified research data collection platform.
 * Features:
 * - Survey completion tracking
 * - Points & streaks display
 * - Achievement gallery
 * - Anonymous leaderboard
 * - Survey history
 *
 * @route /wellness
 */

import React, { useState } from 'react';
import Link from 'next/link';
import {
  useWellnessAccount,
  useAvailableSurveys,
  useLeaderboard,
  useSurveyHistory,
  useLeaderboardOptIn,
} from '@/features/wellness/hooks/useWellness';
import {
  SURVEY_TYPE_DISPLAY,
  ACHIEVEMENT_DEFINITIONS,
  type AchievementInfo,
  type SurveyListItem,
  type LeaderboardEntry,
} from '@/features/wellness/types';

type TabId = 'surveys' | 'achievements' | 'leaderboard' | 'history';

export default function WellnessPage() {
  const [activeTab, setActiveTab] = useState<TabId>('surveys');
  const { data: account, isLoading: accountLoading } = useWellnessAccount();
  const { data: surveys, isLoading: surveysLoading } = useAvailableSurveys();
  const { data: leaderboard, isLoading: leaderboardLoading } = useLeaderboard();
  const { data: history, isLoading: historyLoading } = useSurveyHistory(1, 10);

  const isLoading = accountLoading || surveysLoading;

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-900 text-white p-6">
        <div className="max-w-4xl mx-auto">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-800 rounded w-1/3 mb-6" />
            <div className="h-32 bg-gray-800 rounded mb-6" />
            <div className="grid grid-cols-3 gap-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-24 bg-gray-800 rounded" />
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gradient-to-r from-gray-800 to-gray-900 border-b border-gray-700">
        <div className="max-w-4xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold flex items-center gap-3">
                <span className="text-3xl">&#x1F3E5;</span>
                Wellness Check-In
              </h1>
              <p className="text-gray-400 text-sm mt-1">
                Track your wellbeing, earn points, contribute to research
              </p>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-amber-400">
                {account?.pointsBalance ?? 0}
                <span className="text-sm font-normal text-gray-400 ml-1">pts</span>
              </div>
              {(account?.currentStreakWeeks ?? 0) > 0 && (
                <div className="text-sm text-orange-400 flex items-center justify-end gap-1">
                  <span>&#x1F525;</span>
                  {account?.currentStreakWeeks}-week streak
                </div>
              )}
            </div>
          </div>

          {/* Progress bar to next milestone */}
          <div className="mt-4">
            <div className="flex items-center justify-between text-xs text-gray-400 mb-1">
              <span>Progress to next badge</span>
              <span>{account?.pointsLifetime ?? 0} / {getNextMilestone(account?.pointsLifetime ?? 0)}</span>
            </div>
            <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-cyan-500 to-purple-500 transition-all duration-500"
                style={{
                  width: `${getProgressPercentage(account?.pointsLifetime ?? 0)}%`,
                }}
              />
            </div>
          </div>
        </div>
      </header>

      {/* Tab Navigation */}
      <nav className="bg-gray-800/50 border-b border-gray-700">
        <div className="max-w-4xl mx-auto px-6">
          <div className="flex gap-1">
            {(['surveys', 'achievements', 'leaderboard', 'history'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`
                  px-4 py-3 text-sm font-medium transition-colors capitalize
                  ${activeTab === tab
                    ? 'text-cyan-400 border-b-2 border-cyan-400'
                    : 'text-gray-400 hover:text-white'
                  }
                `}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-6 py-6">
        {activeTab === 'surveys' && (
          <SurveysTab surveys={surveys ?? []} />
        )}
        {activeTab === 'achievements' && (
          <AchievementsTab achievements={account?.achievements ?? []} />
        )}
        {activeTab === 'leaderboard' && (
          <LeaderboardTab
            leaderboard={leaderboard}
            isLoading={leaderboardLoading}
            isOptedIn={account?.leaderboardOptIn ?? false}
            displayName={account?.displayName}
          />
        )}
        {activeTab === 'history' && (
          <HistoryTab history={history} isLoading={historyLoading} />
        )}
      </main>
    </div>
  );
}

// ============================================================================
// Helper Functions
// ============================================================================

function getNextMilestone(points: number): number {
  if (points < 100) return 100;
  if (points < 500) return 500;
  if (points < 1000) return 1000;
  return 2000;
}

function getProgressPercentage(points: number): number {
  const next = getNextMilestone(points);
  const prev = points < 100 ? 0 : points < 500 ? 100 : points < 1000 ? 500 : 1000;
  return Math.min(100, ((points - prev) / (next - prev)) * 100);
}

// ============================================================================
// Tab Components
// ============================================================================

function SurveysTab({ surveys }: { surveys: SurveyListItem[] }) {
  const available = surveys.filter((s) => s.isAvailable);
  const completed = surveys.filter((s) => s.completedThisPeriod);

  return (
    <div className="space-y-6">
      {/* Weekly Goal */}
      <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-medium text-gray-300">
            <span className="mr-2">&#x1F3AF;</span>
            This Week&apos;s Goal
          </h3>
          <span className="text-sm text-gray-400">
            {completed.length} / {surveys.length} complete
          </span>
        </div>
        <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-green-500 transition-all duration-500"
            style={{
              width: `${surveys.length > 0 ? (completed.length / surveys.length) * 100 : 0}%`,
            }}
          />
        </div>
      </div>

      {/* Available Surveys */}
      {available.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <span>&#x1F4CB;</span>
            Available Now
          </h2>
          <div className="grid gap-4 sm:grid-cols-2">
            {available.map((survey) => (
              <SurveyCard key={survey.id} survey={survey} />
            ))}
          </div>
        </div>
      )}

      {/* Completed Surveys */}
      {completed.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2 text-gray-400">
            <span>&#x2705;</span>
            Completed This Week
          </h2>
          <div className="grid gap-4 sm:grid-cols-2">
            {completed.map((survey) => (
              <SurveyCard key={survey.id} survey={survey} completed />
            ))}
          </div>
        </div>
      )}

      {surveys.length === 0 && (
        <div className="text-center py-12 text-gray-400">
          <p className="text-4xl mb-4">&#x1F389;</p>
          <p>No surveys available right now. Check back soon!</p>
        </div>
      )}
    </div>
  );
}

function SurveyCard({
  survey,
  completed = false,
}: {
  survey: SurveyListItem;
  completed?: boolean;
}) {
  const typeInfo = SURVEY_TYPE_DISPLAY[survey.surveyType] || {
    label: survey.surveyType,
    color: 'gray',
  };

  return (
    <Link
      href={completed ? '#' : `/wellness/surveys/${survey.id}`}
      className={`
        block bg-gray-800 rounded-lg p-4 border transition-all
        ${completed
          ? 'border-gray-700 opacity-60 cursor-default'
          : 'border-gray-700 hover:border-cyan-600 hover:bg-gray-750'
        }
      `}
      onClick={(e) => completed && e.preventDefault()}
    >
      <div className="flex items-start justify-between">
        <div>
          <span
            className={`
              inline-block px-2 py-0.5 rounded text-xs font-medium mb-2
              bg-${typeInfo.color}-900/50 text-${typeInfo.color}-400
            `}
          >
            {typeInfo.label}
          </span>
          <h3 className="font-medium">{survey.displayName}</h3>
          <p className="text-sm text-gray-400 mt-1">
            ~{Math.ceil(survey.estimatedSeconds / 60)} min
          </p>
        </div>
        <div className="text-right">
          <span className="text-amber-400 font-semibold">
            +{survey.pointsValue}
          </span>
          <span className="text-gray-400 text-sm ml-1">pts</span>
          {completed && (
            <div className="text-green-400 text-sm mt-1">&#x2713; Done</div>
          )}
        </div>
      </div>
    </Link>
  );
}

function AchievementsTab({ achievements }: { achievements: AchievementInfo[] }) {
  const earned = achievements.filter((a) => a.earned);
  const locked = achievements.filter((a) => !a.earned);

  return (
    <div className="space-y-8">
      {/* Earned Achievements */}
      <div>
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <span>&#x1F3C6;</span>
          Earned ({earned.length})
        </h2>
        {earned.length > 0 ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {earned.map((achievement) => (
              <AchievementCard key={achievement.code} achievement={achievement} />
            ))}
          </div>
        ) : (
          <p className="text-gray-400 text-sm">
            Complete surveys to earn your first badge!
          </p>
        )}
      </div>

      {/* Locked Achievements */}
      <div>
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2 text-gray-400">
          <span>&#x1F512;</span>
          Locked ({locked.length})
        </h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {locked.map((achievement) => (
            <AchievementCard key={achievement.code} achievement={achievement} locked />
          ))}
        </div>
      </div>
    </div>
  );
}

function AchievementCard({
  achievement,
  locked = false,
}: {
  achievement: AchievementInfo;
  locked?: boolean;
}) {
  const definition = ACHIEVEMENT_DEFINITIONS[achievement.code] || {
    name: achievement.name,
    description: achievement.description,
    icon: 'StarIcon',
    criteria: achievement.criteria,
  };

  return (
    <div
      className={`
        bg-gray-800 rounded-lg p-4 border
        ${locked ? 'border-gray-700 opacity-50' : 'border-amber-600/50'}
      `}
    >
      <div className="flex items-center gap-3 mb-2">
        <div
          className={`
            w-10 h-10 rounded-full flex items-center justify-center text-xl
            ${locked ? 'bg-gray-700' : 'bg-amber-900/50'}
          `}
        >
          {locked ? '&#x1F512;' : '&#x1F3C5;'}
        </div>
        <div>
          <h3 className={`font-medium ${locked ? 'text-gray-400' : 'text-white'}`}>
            {definition.name}
          </h3>
          {achievement.earnedAt && (
            <p className="text-xs text-gray-500">
              Earned {new Date(achievement.earnedAt).toLocaleDateString()}
            </p>
          )}
        </div>
      </div>
      <p className="text-sm text-gray-400">{definition.description}</p>
      {locked && (
        <p className="text-xs text-gray-500 mt-2 italic">
          {definition.criteria}
        </p>
      )}
    </div>
  );
}

function LeaderboardTab({
  leaderboard,
  isLoading,
  isOptedIn,
  displayName,
}: {
  leaderboard: ReturnType<typeof useLeaderboard>['data'];
  isLoading: boolean;
  isOptedIn: boolean;
  displayName?: string;
}) {
  const optIn = useLeaderboardOptIn();
  const [newDisplayName, setNewDisplayName] = useState(displayName || '');

  const handleOptIn = async () => {
    await optIn.mutateAsync({
      optIn: true,
      displayName: newDisplayName || undefined,
    });
  };

  const handleOptOut = async () => {
    await optIn.mutateAsync({ optIn: false });
  };

  if (!isOptedIn) {
    return (
      <div className="max-w-md mx-auto text-center py-12">
        <p className="text-4xl mb-4">&#x1F3C6;</p>
        <h2 className="text-xl font-semibold mb-2">Join the Leaderboard</h2>
        <p className="text-gray-400 mb-6">
          Compete anonymously with other participants. Your real name is never shown.
        </p>
        <div className="mb-4">
          <input
            type="text"
            placeholder="Choose a display name..."
            value={newDisplayName}
            onChange={(e) => setNewDisplayName(e.target.value)}
            className="w-full px-4 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500"
            maxLength={50}
          />
        </div>
        <button
          onClick={handleOptIn}
          disabled={optIn.isPending}
          className="px-6 py-2 bg-cyan-600 hover:bg-cyan-500 text-white font-medium rounded-lg transition-colors disabled:opacity-50"
        >
          {optIn.isPending ? 'Joining...' : 'Join Leaderboard'}
        </button>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="space-y-2">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="h-14 bg-gray-800 rounded animate-pulse" />
        ))}
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">
          <span className="mr-2">&#x1F3C6;</span>
          Engagement Leaderboard
        </h2>
        <button
          onClick={handleOptOut}
          className="text-sm text-gray-400 hover:text-gray-300"
        >
          Leave leaderboard
        </button>
      </div>

      <div className="bg-gray-800 rounded-lg overflow-hidden">
        {leaderboard?.entries.map((entry, index) => (
          <LeaderboardRow key={index} entry={entry} />
        ))}
      </div>

      {leaderboard?.yourRank && leaderboard.yourRank > 20 && (
        <div className="mt-4 text-center text-gray-400">
          <p>Your rank: #{leaderboard.yourRank} with {leaderboard.yourPoints} points</p>
        </div>
      )}

      <p className="text-center text-gray-500 text-sm mt-4">
        {leaderboard?.totalParticipants ?? 0} total participants
      </p>
    </div>
  );
}

function LeaderboardRow({ entry }: { entry: LeaderboardEntry }) {
  const getMedalEmoji = (rank: number) => {
    if (rank === 1) return '&#x1F947;';
    if (rank === 2) return '&#x1F948;';
    if (rank === 3) return '&#x1F949;';
    return null;
  };

  const medal = getMedalEmoji(entry.rank);

  return (
    <div
      className={`
        flex items-center justify-between px-4 py-3 border-b border-gray-700 last:border-0
        ${entry.isYou ? 'bg-cyan-900/20' : ''}
      `}
    >
      <div className="flex items-center gap-4">
        <span className="w-8 text-center font-mono text-gray-400">
          {medal ? <span dangerouslySetInnerHTML={{ __html: medal }} /> : entry.rank}
        </span>
        <span className={entry.isYou ? 'text-cyan-400 font-medium' : ''}>
          {entry.displayName}
          {entry.isYou && <span className="ml-2 text-xs">(you)</span>}
        </span>
      </div>
      <div className="flex items-center gap-4 text-sm">
        {entry.streak > 0 && (
          <span className="text-orange-400">
            &#x1F525; {entry.streak}
          </span>
        )}
        <span className="text-amber-400 font-semibold">
          {entry.points.toLocaleString()} pts
        </span>
      </div>
    </div>
  );
}

function HistoryTab({
  history,
  isLoading,
}: {
  history: ReturnType<typeof useSurveyHistory>['data'];
  isLoading: boolean;
}) {
  if (isLoading) {
    return (
      <div className="space-y-2">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="h-16 bg-gray-800 rounded animate-pulse" />
        ))}
      </div>
    );
  }

  if (!history?.responses?.length) {
    return (
      <div className="text-center py-12 text-gray-400">
        <p className="text-4xl mb-4">&#x1F4CA;</p>
        <p>No survey history yet. Complete a survey to get started!</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">
        <span className="mr-2">&#x1F4CA;</span>
        Recent Responses
      </h2>

      <div className="bg-gray-800 rounded-lg overflow-hidden">
        {history.responses.map((response) => {
          const typeInfo = SURVEY_TYPE_DISPLAY[response.surveyType] || {
            label: response.surveyType,
            color: 'gray',
          };

          return (
            <div
              key={response.id}
              className="flex items-center justify-between px-4 py-3 border-b border-gray-700 last:border-0"
            >
              <div>
                <div className="flex items-center gap-2">
                  <span
                    className={`
                      inline-block px-2 py-0.5 rounded text-xs
                      bg-${typeInfo.color}-900/50 text-${typeInfo.color}-400
                    `}
                  >
                    {typeInfo.label}
                  </span>
                  <span className="font-medium">{response.surveyName}</span>
                </div>
                <p className="text-sm text-gray-400 mt-1">
                  {new Date(response.submittedAt).toLocaleDateString(undefined, {
                    weekday: 'short',
                    month: 'short',
                    day: 'numeric',
                  })}
                  {response.blockNumber !== undefined && (
                    <span className="ml-2">Block {response.blockNumber}</span>
                  )}
                </p>
              </div>
              <div className="text-right">
                {response.score !== undefined && response.score !== null && (
                  <div className="font-semibold">{response.score}</div>
                )}
                {response.scoreInterpretation && (
                  <div className={`text-sm capitalize ${
                    response.scoreInterpretation === 'low' ? 'text-green-400' :
                    response.scoreInterpretation === 'moderate' ? 'text-yellow-400' :
                    'text-red-400'
                  }`}>
                    {response.scoreInterpretation}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      <p className="text-center text-gray-500 text-sm">
        Showing {history.responses.length} of {history.total} responses
      </p>
    </div>
  );
}
