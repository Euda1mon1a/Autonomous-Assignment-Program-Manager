/**
 * TypeScript types for Gamified Wellness & Survey Collection
 *
 * IMPORTANT: Frontend uses camelCase, API uses snake_case.
 * The axios interceptor in lib/api.ts auto-converts between them.
 */

// ============================================================================
// Enums
// ============================================================================

export type SurveyType =
  | 'burnout'
  | 'stress'
  | 'sleep'
  | 'efficacy'
  | 'pulse'
  | 'hopfield'
  | 'custom';

export type SurveyFrequency = 'daily' | 'weekly' | 'biweekly' | 'block' | 'annual';

export type TransactionType =
  | 'survey'
  | 'streak'
  | 'achievement'
  | 'block_bonus'
  | 'admin'
  | 'redemption';

export type AchievementCode =
  | 'first_checkin'
  | 'points_100'
  | 'points_500'
  | 'points_1000'
  | 'weekly_warrior'
  | 'consistency_king'
  | 'data_hero'
  | 'research_champion'
  | 'faculty_mentor'
  | 'iron_resident';

// ============================================================================
// Survey Types
// ============================================================================

export interface QuestionOption {
  value: number | string;
  label: string;
  score?: number;
}

export interface SurveyQuestion {
  id: string;
  text: string;
  questionType: 'likert' | 'multiple_choice' | 'slider' | 'text' | 'emoji_scale';
  required: boolean;
  options?: QuestionOption[];
  minValue?: number;
  maxValue?: number;
  minLabel?: string;
  maxLabel?: string;
}

export interface Survey {
  id: string;
  name: string;
  displayName: string;
  surveyType: SurveyType;
  description?: string;
  instructions?: string;
  pointsValue: number;
  estimatedSeconds: number;
  frequency: SurveyFrequency;
  questions: SurveyQuestion[];
  isActive: boolean;
  createdAt: string;
}

export interface SurveyListItem {
  id: string;
  name: string;
  displayName: string;
  surveyType: SurveyType;
  pointsValue: number;
  estimatedSeconds: number;
  frequency: SurveyFrequency;
  isAvailable: boolean;
  nextAvailableAt?: string;
  completedThisPeriod: boolean;
}

export interface SurveyResponseCreate {
  responses: Record<string, number | string>;
  blockNumber?: number;
  academicYear?: number;
}

export interface SurveySubmissionResult {
  success: boolean;
  responseId?: string;
  score?: number;
  scoreInterpretation?: string;
  pointsEarned: number;
  newAchievements: string[];
  streakUpdated: boolean;
  currentStreak: number;
  message: string;
}

export interface SurveyResponseSummary {
  id: string;
  surveyId: string;
  surveyName: string;
  surveyType: SurveyType;
  score?: number;
  scoreInterpretation?: string;
  submittedAt: string;
  blockNumber?: number;
  academicYear?: number;
}

// ============================================================================
// Account Types
// ============================================================================

export interface AchievementInfo {
  code: AchievementCode;
  name: string;
  description: string;
  icon: string;
  earned: boolean;
  earnedAt?: string;
  progress?: number;
  criteria?: string;
}

export interface WellnessAccount {
  personId: string;
  pointsBalance: number;
  pointsLifetime: number;
  currentStreakWeeks: number;
  longestStreakWeeks: number;
  lastActivityDate?: string;
  streakStartDate?: string;
  leaderboardOptIn: boolean;
  displayName?: string;
  researchConsent: boolean;
  achievements: AchievementInfo[];
  surveysCompletedThisWeek: number;
  surveysAvailable: number;
}

// ============================================================================
// Leaderboard Types
// ============================================================================

export interface LeaderboardEntry {
  rank: number;
  displayName: string;
  points: number;
  streak: number;
  isYou: boolean;
}

export interface LeaderboardResponse {
  entries: LeaderboardEntry[];
  totalParticipants: number;
  yourRank?: number;
  yourPoints?: number;
  snapshotDate?: string;
}

// ============================================================================
// Points Types
// ============================================================================

export interface PointTransaction {
  id: string;
  points: number;
  balanceAfter: number;
  transactionType: TransactionType;
  source: string;
  createdAt: string;
}

export interface PointHistoryResponse {
  transactions: PointTransaction[];
  total: number;
  page: number;
  pageSize: number;
  currentBalance: number;
}

// ============================================================================
// Hopfield Types
// ============================================================================

export interface HopfieldPositionCreate {
  xPosition: number;
  yPosition: number;
  zPosition?: number;
  confidence?: number;
  notes?: string;
  blockNumber?: number;
  academicYear?: number;
}

export interface HopfieldPositionResult {
  success: boolean;
  positionId?: string;
  basinDepth?: number;
  energyValue?: number;
  stabilityScore?: number;
  nearestAttractorType?: string;
  pointsEarned: number;
  message: string;
}

export interface HopfieldAttractor {
  id: string;
  x: number;
  y: number;
  type: 'global_minimum' | 'local_minimum' | 'spurious' | 'metastable';
  energy: number;
  label?: string;
}

export interface HopfieldLandscapeData {
  xGrid: number[];
  yGrid: number[];
  energyGrid: number[][];
  attractors: HopfieldAttractor[];
  currentPosition?: {
    x: number;
    y: number;
    energy: number;
    basinDepth: number;
  };
  aggregatePositions?: Array<{
    x: number;
    y: number;
    count: number;
  }>;
  computedAt: string;
  blockNumber?: number;
  academicYear?: number;
}

export interface HopfieldAggregates {
  totalPositions: number;
  averageX?: number;
  averageY?: number;
  averageBasinDepth?: number;
  averageEnergy?: number;
  computedBasinDepth?: number;
  agreementScore?: number;
  blockNumber?: number;
  academicYear?: number;
}

// ============================================================================
// Quick Pulse Types
// ============================================================================

export interface QuickPulseSubmit {
  mood: 1 | 2 | 3 | 4 | 5;
  energy?: 1 | 2 | 3 | 4 | 5;
  notes?: string;
}

export interface QuickPulseResult {
  success: boolean;
  pointsEarned: number;
  currentStreak: number;
  message: string;
}

export interface QuickPulseWidgetData {
  canSubmit: boolean;
  lastSubmittedAt?: string;
  currentStreak: number;
  pointsBalance: number;
  availableSurveys: SurveyListItem[];
  recentAchievements: AchievementInfo[];
}

// ============================================================================
// Analytics Types (Admin)
// ============================================================================

export interface WellnessAnalytics {
  totalParticipants: number;
  activeThisWeek: number;
  activeThisBlock: number;
  participationRate: number;
  totalResponsesThisWeek: number;
  totalResponsesThisBlock: number;
  averageResponsesPerPerson: number;
  averageBurnoutScore?: number;
  averageStressScore?: number;
  averageSleepScore?: number;
  averageStreak: number;
  longestStreak: number;
  totalPointsEarnedThisWeek: number;
  hopfieldPositionsThisWeek: number;
  averageBasinDepth?: number;
}

// ============================================================================
// UI State Types
// ============================================================================

export interface SurveyFormState {
  surveyId: string;
  responses: Record<string, number | string>;
  currentQuestionIndex: number;
  isSubmitting: boolean;
  error?: string;
}

export interface WellnessPageState {
  activeTab: 'surveys' | 'achievements' | 'leaderboard' | 'hopfield' | 'history';
  isLoading: boolean;
  error?: string;
}

// ============================================================================
// Achievement Definitions (for UI display)
// ============================================================================

export const ACHIEVEMENT_DEFINITIONS: Record<
  AchievementCode,
  { name: string; description: string; icon: string; criteria: string }
> = {
  first_checkin: {
    name: 'First Check-In',
    description: 'Completed your first wellness survey',
    icon: 'CheckBadgeIcon',
    criteria: 'Complete any survey',
  },
  points_100: {
    name: 'Century Club',
    description: 'Earned 100 lifetime points',
    icon: 'StarIcon',
    criteria: 'Accumulate 100 points',
  },
  points_500: {
    name: 'Rising Star',
    description: 'Earned 500 lifetime points',
    icon: 'SparklesIcon',
    criteria: 'Accumulate 500 points',
  },
  points_1000: {
    name: 'Iron Resident',
    description: 'Earned 1000 lifetime points',
    icon: 'TrophyIcon',
    criteria: 'Accumulate 1000 points',
  },
  weekly_warrior: {
    name: 'Weekly Warrior',
    description: 'Maintained a 4-week participation streak',
    icon: 'FireIcon',
    criteria: 'Complete surveys 4 weeks in a row',
  },
  consistency_king: {
    name: 'Consistency King',
    description: 'Maintained an 8-week participation streak',
    icon: 'CrownIcon',
    criteria: 'Complete surveys 8 weeks in a row',
  },
  data_hero: {
    name: 'Data Hero',
    description: 'Completed all surveys in an academic block',
    icon: 'ChartBarIcon',
    criteria: 'Complete MBI-2, PSS-4, Sleep, and GSE-4 in one block',
  },
  research_champion: {
    name: 'Research Champion',
    description: 'Participated for 52 weeks (full academic year)',
    icon: 'AcademicCapIcon',
    criteria: 'Complete surveys for 52 weeks',
  },
  faculty_mentor: {
    name: 'Faculty Mentor',
    description: 'Faculty member with exceptional engagement',
    icon: 'UserGroupIcon',
    criteria: 'Faculty with 500+ points and research consent',
  },
  iron_resident: {
    name: 'Iron Resident',
    description: 'Earned 1000 lifetime points',
    icon: 'TrophyIcon',
    criteria: 'Accumulate 1000 points',
  },
};

// ============================================================================
// Survey Type Display
// ============================================================================

export const SURVEY_TYPE_DISPLAY: Record<SurveyType, { label: string; color: string }> = {
  burnout: { label: 'Burnout', color: 'red' },
  stress: { label: 'Stress', color: 'orange' },
  sleep: { label: 'Sleep', color: 'blue' },
  efficacy: { label: 'Self-Efficacy', color: 'green' },
  pulse: { label: 'Quick Pulse', color: 'purple' },
  hopfield: { label: 'Program Stability', color: 'cyan' },
  custom: { label: 'Custom', color: 'gray' },
};

// ============================================================================
// Mood Emoji Mapping
// ============================================================================

export const MOOD_EMOJIS: Record<1 | 2 | 3 | 4 | 5, { emoji: string; label: string }> = {
  1: { emoji: '1F62B', label: 'Very low' },
  2: { emoji: '1F61F', label: 'Low' },
  3: { emoji: '1F610', label: 'Okay' },
  4: { emoji: '1F642', label: 'Good' },
  5: { emoji: '1F60A', label: 'Great' },
};
