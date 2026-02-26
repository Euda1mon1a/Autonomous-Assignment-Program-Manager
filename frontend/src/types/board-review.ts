/**
 * Board Review Curriculum Planner Types
 *
 * Tripler AMC Family Medicine Board Review — 78 sessions, 202 FMCAs, 5 ABFM domains.
 * camelCase keys (frontend convention), snake_case enum values (Gorgon's Gaze).
 *
 * @see docs/design/BOARD_REVIEW_CURRICULUM_DESIGN.md
 */

// ============ Enums (snake_case values) ============

export type SessionStatus = 'not_started' | 'in_progress' | 'completed';

export type AbfmDomainCode = 'ACD' | 'CCM' | 'UEC' | 'PC' | 'FOC';

export type BoardReviewTab = 'dashboard' | 'curriculum' | 'analytics' | 'ite';

// ============ Core Types ============

export interface AbfmDomain {
  code: AbfmDomainCode;
  name: string;
  color: string;
  target: number; // ABFM blueprint target percentage
  description: string;
}

export interface BoardReviewBlock {
  id: number;
  name: string;
  weeks: number;
  icon: string;
  sessions: BoardReviewSession[];
}

export interface DomainFmcaMapping {
  [domain: string]: string[]; // domain code → list of FMCA names
}

export interface BoardReviewSession {
  id: number;
  title: string;
  domains: DomainFmcaMapping;
  presenter: string;
  status: SessionStatus;
  date: string;
  notes: string;
}

export interface SessionUpdate {
  sessionId: number;
  status?: SessionStatus;
  presenter?: string;
  date?: string;
  notes?: string;
}

// ============ Dashboard Types ============

export interface DomainCoverage {
  code: AbfmDomainCode;
  name: string;
  color: string;
  target: number;
  touches: number; // number of sessions that touch this domain
  completed: number; // sessions completed in this domain
  percentage: number; // touches / total sessions as percentage of curriculum
}

export interface BoardReviewDashboard {
  totalSessions: number;
  completedSessions: number;
  inProgressSessions: number;
  notStartedSessions: number;
  completionRate: number;
  domainCoverage: DomainCoverage[];
  currentBlock: string | null;
  nextSession: string | null;
}

// ============ Analytics Types ============

export interface BlockDomainCount {
  blockId: number;
  blockName: string;
  counts: Record<AbfmDomainCode, number>;
}

export interface HeatMapCell {
  row: string;
  col: string;
  value: number;
}

export interface FmcaGapItem {
  fmca: string;
  domain: AbfmDomainCode;
  covered: boolean;
  sessionIds: number[];
}

// ============ ITE Types ============

export interface IteScores {
  ACD: number | null;
  CCM: number | null;
  UEC: number | null;
  PC: number | null;
  FOC: number | null;
}

export interface IteRemediationItem {
  domain: AbfmDomainCode;
  domainName: string;
  score: number | null;
  priority: 'low' | 'medium' | 'high';
  sessions: Array<{
    id: number;
    title: string;
    blockName: string;
    status: SessionStatus;
  }>;
}

// ============ Filter Types ============

export interface BoardReviewFilters {
  domain?: AbfmDomainCode | '';
  status?: SessionStatus | '';
  search?: string;
}

// ============ Tab Config ============

export interface TabConfig {
  id: BoardReviewTab;
  label: string;
  description: string;
}
