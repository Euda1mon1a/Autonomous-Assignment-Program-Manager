/**
 * Template Library Constants
 *
 * Predefined categories, system templates, and configuration constants.
 */

import type { CategoryInfo, PredefinedTemplate, TemplateCategory } from './types';

// Category definitions with metadata
export const TEMPLATE_CATEGORIES: CategoryInfo[] = [
  {
    id: 'schedule',
    name: 'Schedule Templates',
    description: 'Full schedule templates covering multiple weeks',
    icon: 'Calendar',
    color: 'blue',
  },
  {
    id: 'assignment',
    name: 'Assignment Patterns',
    description: 'Reusable assignment patterns for specific activities',
    icon: 'ClipboardList',
    color: 'green',
  },
  {
    id: 'rotation',
    name: 'Rotation Templates',
    description: 'Complete rotation schedules for training blocks',
    icon: 'RefreshCw',
    color: 'purple',
  },
  {
    id: 'call',
    name: 'Call Schedules',
    description: 'On-call and night coverage schedules',
    icon: 'Phone',
    color: 'orange',
  },
  {
    id: 'clinic',
    name: 'Clinic Templates',
    description: 'Outpatient clinic assignment patterns',
    icon: 'Building2',
    color: 'teal',
  },
  {
    id: 'custom',
    name: 'Custom Templates',
    description: 'User-created custom templates',
    icon: 'Puzzle',
    color: 'gray',
  },
];

// Category color mappings for styling
export const CATEGORY_COLORS: Record<TemplateCategory, { bg: string; text: string; border: string }> = {
  schedule: {
    bg: 'bg-blue-50',
    text: 'text-blue-700',
    border: 'border-blue-200',
  },
  assignment: {
    bg: 'bg-green-50',
    text: 'text-green-700',
    border: 'border-green-200',
  },
  rotation: {
    bg: 'bg-purple-50',
    text: 'text-purple-700',
    border: 'border-purple-200',
  },
  call: {
    bg: 'bg-orange-50',
    text: 'text-orange-700',
    border: 'border-orange-200',
  },
  clinic: {
    bg: 'bg-teal-50',
    text: 'text-teal-700',
    border: 'border-teal-200',
  },
  custom: {
    bg: 'bg-gray-50',
    text: 'text-gray-700',
    border: 'border-gray-200',
  },
};

// Status color mappings
export const STATUS_COLORS: Record<string, { bg: string; text: string }> = {
  draft: { bg: 'bg-yellow-100', text: 'text-yellow-800' },
  active: { bg: 'bg-green-100', text: 'text-green-800' },
  archived: { bg: 'bg-gray-100', text: 'text-gray-800' },
};

// Visibility icons and labels
export const VISIBILITY_OPTIONS = [
  { value: 'private', label: 'Private', icon: 'Lock', description: 'Only you can see this template' },
  { value: 'shared', label: 'Shared', icon: 'Users', description: 'Visible to selected users' },
  { value: 'public', label: 'Public', icon: 'Globe', description: 'Visible to everyone' },
] as const;

// Predefined system templates
export const PREDEFINED_TEMPLATES: PredefinedTemplate[] = [
  {
    templateKey: 'standard-weekday-clinic',
    name: 'Standard Weekday Clinic',
    description: 'Basic weekday clinic schedule with morning and afternoon sessions',
    category: 'clinic',
    visibility: 'public',
    status: 'active',
    durationWeeks: 1,
    startDayOfWeek: 1, // Monday
    patterns: [
      {
        id: 'pattern-1',
        name: 'Morning Clinic',
        dayOfWeek: 1,
        timeOfDay: 'AM',
        activityType: 'clinic',
        role: 'primary',
      },
      {
        id: 'pattern-2',
        name: 'Afternoon Clinic',
        dayOfWeek: 1,
        timeOfDay: 'PM',
        activityType: 'clinic',
        role: 'primary',
      },
      {
        id: 'pattern-3',
        name: 'Morning Clinic',
        dayOfWeek: 2,
        timeOfDay: 'AM',
        activityType: 'clinic',
        role: 'primary',
      },
      {
        id: 'pattern-4',
        name: 'Afternoon Clinic',
        dayOfWeek: 2,
        timeOfDay: 'PM',
        activityType: 'clinic',
        role: 'primary',
      },
      {
        id: 'pattern-5',
        name: 'Morning Clinic',
        dayOfWeek: 3,
        timeOfDay: 'AM',
        activityType: 'clinic',
        role: 'primary',
      },
      {
        id: 'pattern-6',
        name: 'Afternoon Clinic',
        dayOfWeek: 3,
        timeOfDay: 'PM',
        activityType: 'clinic',
        role: 'primary',
      },
      {
        id: 'pattern-7',
        name: 'Morning Clinic',
        dayOfWeek: 4,
        timeOfDay: 'AM',
        activityType: 'clinic',
        role: 'primary',
      },
      {
        id: 'pattern-8',
        name: 'Afternoon Clinic',
        dayOfWeek: 4,
        timeOfDay: 'PM',
        activityType: 'clinic',
        role: 'primary',
      },
      {
        id: 'pattern-9',
        name: 'Morning Clinic',
        dayOfWeek: 5,
        timeOfDay: 'AM',
        activityType: 'clinic',
        role: 'primary',
      },
      {
        id: 'pattern-10',
        name: 'Afternoon Clinic',
        dayOfWeek: 5,
        timeOfDay: 'PM',
        activityType: 'clinic',
        role: 'primary',
      },
    ],
    requiresSupervision: true,
    allowWeekends: false,
    allowHolidays: false,
    tags: ['clinic', 'weekday', 'standard'],
    usageCount: 0,
    isPublic: true,
    version: 1,
    isSystem: true,
  },
  {
    templateKey: 'weekly-call-rotation',
    name: 'Weekly Call Rotation',
    description: '7-day call rotation template with alternating coverage',
    category: 'call',
    visibility: 'public',
    status: 'active',
    durationWeeks: 1,
    startDayOfWeek: 0, // Sunday
    patterns: [
      {
        id: 'call-pattern-1',
        name: 'Weekend Call',
        dayOfWeek: 0,
        timeOfDay: 'ALL',
        activityType: 'call',
        role: 'primary',
        notes: 'Weekend call coverage',
      },
      {
        id: 'call-pattern-2',
        name: 'Weeknight Call',
        dayOfWeek: 1,
        timeOfDay: 'PM',
        activityType: 'call',
        role: 'primary',
      },
      {
        id: 'call-pattern-3',
        name: 'Weeknight Call',
        dayOfWeek: 2,
        timeOfDay: 'PM',
        activityType: 'call',
        role: 'primary',
      },
      {
        id: 'call-pattern-4',
        name: 'Weeknight Call',
        dayOfWeek: 3,
        timeOfDay: 'PM',
        activityType: 'call',
        role: 'primary',
      },
      {
        id: 'call-pattern-5',
        name: 'Weeknight Call',
        dayOfWeek: 4,
        timeOfDay: 'PM',
        activityType: 'call',
        role: 'primary',
      },
      {
        id: 'call-pattern-6',
        name: 'Weeknight Call',
        dayOfWeek: 5,
        timeOfDay: 'PM',
        activityType: 'call',
        role: 'primary',
      },
      {
        id: 'call-pattern-7',
        name: 'Weekend Call',
        dayOfWeek: 6,
        timeOfDay: 'ALL',
        activityType: 'call',
        role: 'primary',
        notes: 'Weekend call coverage',
      },
    ],
    requiresSupervision: false,
    allowWeekends: true,
    allowHolidays: true,
    tags: ['call', 'overnight', 'rotation'],
    usageCount: 0,
    isPublic: true,
    version: 1,
    isSystem: true,
  },
  {
    templateKey: 'inpatient-rotation-block',
    name: 'Inpatient Rotation Block',
    description: '4-week inpatient rotation template with daily coverage',
    category: 'rotation',
    visibility: 'public',
    status: 'active',
    durationWeeks: 4,
    startDayOfWeek: 1, // Monday
    patterns: [
      {
        id: 'inpatient-1',
        name: 'Inpatient Service',
        dayOfWeek: 1,
        timeOfDay: 'ALL',
        activityType: 'inpatient',
        role: 'primary',
      },
      {
        id: 'inpatient-2',
        name: 'Inpatient Service',
        dayOfWeek: 2,
        timeOfDay: 'ALL',
        activityType: 'inpatient',
        role: 'primary',
      },
      {
        id: 'inpatient-3',
        name: 'Inpatient Service',
        dayOfWeek: 3,
        timeOfDay: 'ALL',
        activityType: 'inpatient',
        role: 'primary',
      },
      {
        id: 'inpatient-4',
        name: 'Inpatient Service',
        dayOfWeek: 4,
        timeOfDay: 'ALL',
        activityType: 'inpatient',
        role: 'primary',
      },
      {
        id: 'inpatient-5',
        name: 'Inpatient Service',
        dayOfWeek: 5,
        timeOfDay: 'ALL',
        activityType: 'inpatient',
        role: 'primary',
      },
    ],
    maxResidentsPerDay: 4,
    requiresSupervision: true,
    allowWeekends: false,
    allowHolidays: false,
    tags: ['inpatient', 'rotation', 'block'],
    usageCount: 0,
    isPublic: true,
    version: 1,
    isSystem: true,
  },
  {
    templateKey: 'procedure-day-template',
    name: 'Procedure Day Template',
    description: 'Template for procedure-focused days with supervision requirements',
    category: 'assignment',
    visibility: 'public',
    status: 'active',
    durationWeeks: 1,
    startDayOfWeek: 1, // Monday
    patterns: [
      {
        id: 'proc-1',
        name: 'Morning Procedures',
        dayOfWeek: 2,
        timeOfDay: 'AM',
        activityType: 'procedure',
        role: 'primary',
        requiredPgyLevels: [2, 3, 4],
      },
      {
        id: 'proc-2',
        name: 'Afternoon Procedures',
        dayOfWeek: 2,
        timeOfDay: 'PM',
        activityType: 'procedure',
        role: 'primary',
        requiredPgyLevels: [2, 3, 4],
      },
      {
        id: 'proc-3',
        name: 'Morning Procedures',
        dayOfWeek: 4,
        timeOfDay: 'AM',
        activityType: 'procedure',
        role: 'primary',
        requiredPgyLevels: [2, 3, 4],
      },
      {
        id: 'proc-4',
        name: 'Afternoon Procedures',
        dayOfWeek: 4,
        timeOfDay: 'PM',
        activityType: 'procedure',
        role: 'primary',
        requiredPgyLevels: [2, 3, 4],
      },
    ],
    maxResidentsPerDay: 2,
    requiresSupervision: true,
    allowWeekends: false,
    allowHolidays: false,
    tags: ['procedure', 'supervision', 'senior'],
    usageCount: 0,
    isPublic: true,
    version: 1,
    isSystem: true,
  },
];

// Day of week labels
export const DAY_OF_WEEK_LABELS = [
  'Sunday',
  'Monday',
  'Tuesday',
  'Wednesday',
  'Thursday',
  'Friday',
  'Saturday',
];

export const DAY_OF_WEEK_SHORT = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

// Activity type options for pattern editor
export const ACTIVITY_TYPE_OPTIONS = [
  { value: 'clinic', label: 'Clinic' },
  { value: 'inpatient', label: 'Inpatient' },
  { value: 'procedure', label: 'Procedure' },
  { value: 'conference', label: 'Conference' },
  { value: 'elective', label: 'Elective' },
  { value: 'call', label: 'Call' },
];

// Role options
export const ROLE_OPTIONS = [
  { value: 'primary', label: 'Primary' },
  { value: 'supervising', label: 'Supervising' },
  { value: 'backup', label: 'Backup' },
];

// Time of day options
export const TIME_OF_DAY_OPTIONS = [
  { value: 'AM', label: 'Morning (AM)' },
  { value: 'PM', label: 'Afternoon (PM)' },
  { value: 'ALL', label: 'All Day' },
];

// Default values for new templates
export const DEFAULT_TEMPLATE_VALUES = {
  durationWeeks: 1,
  startDayOfWeek: 1,
  requiresSupervision: true,
  allowWeekends: false,
  allowHolidays: false,
  visibility: 'private' as const,
  status: 'draft' as const,
  category: 'custom' as const,
};
