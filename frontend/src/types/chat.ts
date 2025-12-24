// Chat types for Claude Code integration

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
  error?: string;
  codeBlocks?: CodeBlock[];
  artifacts?: ChatArtifact[];
}

export interface CodeBlock {
  language: string;
  code: string;
  filename?: string;
}

export interface ChatArtifact {
  id: string;
  type: 'schedule' | 'analysis' | 'report' | 'configuration';
  title: string;
  data: Record<string, any>;
  createdAt: Date;
}

export interface ChatSession {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: Date;
  updatedAt: Date;
  programId: string;
  adminId: string;
}

export interface ClaudeCodeExecutionContext {
  programId: string;
  adminId: string;
  sessionId: string;
  currentSchedule?: ScheduleContext;
  constraints?: ConstraintContext;
  residents?: ResidentContext[];
}

export interface ScheduleContext {
  academicYear: string;
  weeks: number;
  rotations: RotationContext[];
}

export interface RotationContext {
  id: string;
  name: string;
  residents: string[];
  startDate: Date;
  endDate: Date;
}

export interface ConstraintContext {
  maxHoursPerWeek: number;
  maxConsecutiveDays: number;
  minRestDays: number;
  minRotationLength: number;
  customRules?: string[];
}

export interface ResidentContext {
  id: string;
  name: string;
  preferredRotations?: string[];
  restrictions?: string[];
  absences?: { startDate: Date; endDate: Date }[];
}

export interface ClaudeCodeRequest {
  action: 'generate_schedule' | 'analyze_violations' | 'optimize_fairness' | 'validate_compliance' | 'export_report' | 'custom';
  context: ClaudeCodeExecutionContext;
  parameters?: Record<string, any>;
  userQuery: string;
}

export interface ClaudeCodeResponse {
  success: boolean;
  message: string;
  result?: Record<string, any>;
  artifacts?: ChatArtifact[];
  nextActions?: string[];
  error?: string;
}

export interface StreamUpdate {
  type: 'text' | 'code' | 'artifact' | 'status' | 'error';
  content: string;
  metadata?: Record<string, any>;
}
