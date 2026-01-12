'use client';

import { useState, useMemo, useCallback } from 'react';
import { format, startOfWeek, addWeeks, addDays, subWeeks, startOfMonth, endOfMonth } from 'date-fns';
import { useQuery } from '@tanstack/react-query';
import { ChevronLeft, ChevronRight, Calendar, Download, Printer, User } from 'lucide-react';
import { useRouter } from 'next/navigation';

import { RiskBar, type RiskTier } from '@/components/ui/RiskBar';
import { PersonSelector } from '@/components/schedule/PersonSelector';
import { PersonalScheduleCard, type ScheduleAssignment } from '@/components/schedule/PersonalScheduleCard';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { ErrorAlert } from '@/components/ErrorAlert';
import { EmptyState } from '@/components/EmptyState';
import { ScheduleLegend } from '@/components/schedule/ScheduleLegend';
import { WorkHoursCalculator } from '@/components/schedule/WorkHoursCalculator';
import { PageBreadcrumbs } from '@/components/common/Breadcrumbs';
import { CopyUrlButton } from '@/components/common/CopyToClipboard';
import { useKeyboardShortcut } from '@/components/common/KeyboardShortcutHelp';
import { get } from '@/lib/api';
import { ListResponse, usePeople, useRotationTemplates } from '@/lib/hooks';
import type { Assignment, Block, Person, RotationTemplate } from '@/types/api';

/**
 * Personal Schedule Hub - Unified schedule viewing component
 *
 * Consolidates my-schedule and schedule/[personId] routes into a single hub.
 *
 * Tier-based access control:
 * - Tier 0: Read-only, defaults to self, no person selector
 * - Tier 1+: Person selector visible, can view others' schedules
 *
 * WCAG 2.1 AA compliant with proper focus management and contrast ratios.
 */

export type ViewRange = 'week' | '2weeks' | 'month';

export interface PersonalScheduleHubProps {
  /** The calculated risk tier for the current user */
  tier: RiskTier;
  /** Initial person ID to display (defaults to current user) */
  initialPersonId?: string | null;
  /** Current user's person ID (for defaulting) */
  currentUserPersonId?: string | null;
  /** Custom tooltip for the risk bar */
  riskBarTooltip?: string;
}

export function PersonalScheduleHub({
  tier,
  initialPersonId,
  currentUserPersonId,
  riskBarTooltip,
}: PersonalScheduleHubProps) {
  const router = useRouter();

  // State for selected person - default to initialPersonId or currentUserPersonId
  const [selectedPersonId, setSelectedPersonId] = useState<string | null>(
    initialPersonId ?? currentUserPersonId ?? null
  );

  // View state
  const [viewRange, setViewRange] = useState<ViewRange>('2weeks');
  const [currentDate, setCurrentDate] = useState(() => new Date());

  // Calculate date range based on selected view
  const dateRange = useMemo(() => {
    const weekStart = startOfWeek(currentDate, { weekStartsOn: 1 });

    switch (viewRange) {
      case 'week':
        return { start: weekStart, end: addDays(weekStart, 6) };
      case '2weeks':
        return { start: weekStart, end: addDays(weekStart, 13) };
      case 'month':
        return { start: startOfMonth(currentDate), end: endOfMonth(currentDate) };
    }
  }, [viewRange, currentDate]);

  const startDateStr = format(dateRange.start, 'yyyy-MM-dd');
  const endDateStr = format(dateRange.end, 'yyyy-MM-dd');

  // Fetch people data for selector (only needed for tier 1+)
  const {
    data: peopleData,
    isLoading: peopleLoading,
    error: peopleError,
  } = usePeople();

  // Fetch blocks and assignments data
  const {
    data: blocksData,
    isLoading: blocksLoading,
    error: blocksError,
  } = useQuery<ListResponse<Block>>({
    queryKey: ['blocks', startDateStr, endDateStr],
    queryFn: () => get<ListResponse<Block>>(`/blocks?startDate=${startDateStr}&endDate=${endDateStr}`),
    staleTime: 5 * 60 * 1000,
  });

  const {
    data: assignmentsData,
    isLoading: assignmentsLoading,
    error: assignmentsError,
  } = useQuery<ListResponse<Assignment>>({
    queryKey: ['assignments', startDateStr, endDateStr],
    queryFn: () => get<ListResponse<Assignment>>(`/assignments?startDate=${startDateStr}&endDate=${endDateStr}`),
    staleTime: 60 * 1000,
  });

  const { data: templatesData, isLoading: templatesLoading } = useRotationTemplates();

  // Find the selected person's record
  const selectedPerson = useMemo<Person | null>(() => {
    if (!selectedPersonId || !peopleData?.items) return null;
    return peopleData.items.find((person) => person.id === selectedPersonId) ?? null;
  }, [selectedPersonId, peopleData]);

  // Transform assignments to PersonalScheduleCard format
  const selectedPersonAssignments = useMemo<ScheduleAssignment[]>(() => {
    if (!selectedPersonId || !blocksData?.items || !assignmentsData?.items) {
      return [];
    }

    const blockMap = new Map<string, Block>();
    blocksData.items.forEach((block) => blockMap.set(block.id, block));

    const templateMap = new Map<string, RotationTemplate>();
    templatesData?.items?.forEach((template) => templateMap.set(template.id, template));

    const assignments: ScheduleAssignment[] = [];

    assignmentsData.items
      .filter((assignment) => assignment.personId === selectedPersonId)
      .forEach((assignment) => {
        const block = blockMap.get(assignment.blockId);
        if (!block) return;

        const template = assignment.rotationTemplateId
          ? templateMap.get(assignment.rotationTemplateId)
          : null;

        assignments.push({
          id: assignment.id,
          date: block.date,
          timeOfDay: block.timeOfDay as 'AM' | 'PM',
          activity: template?.activityType ?? 'default',
          abbreviation:
            assignment.activityOverride ??
            template?.displayAbbreviation ??
            template?.abbreviation ??
            template?.name?.substring(0, 3).toUpperCase() ??
            '???',
          role: (assignment.role as 'primary' | 'supervising' | 'backup') ?? 'primary',
          notes: assignment.notes,
        });
      });

    return assignments.sort((a, b) => {
      if (a.date !== b.date) return a.date.localeCompare(b.date);
      return a.timeOfDay === 'AM' ? -1 : 1;
    });
  }, [selectedPersonId, blocksData, assignmentsData, templatesData]);

  // Navigation handlers
  const handlePrev = useCallback(() => {
    switch (viewRange) {
      case 'week':
        setCurrentDate((d) => subWeeks(d, 1));
        break;
      case '2weeks':
        setCurrentDate((d) => subWeeks(d, 2));
        break;
      case 'month':
        setCurrentDate((d) => new Date(d.getFullYear(), d.getMonth() - 1, 1));
        break;
    }
  }, [viewRange]);

  const handleNext = useCallback(() => {
    switch (viewRange) {
      case 'week':
        setCurrentDate((d) => addWeeks(d, 1));
        break;
      case '2weeks':
        setCurrentDate((d) => addWeeks(d, 2));
        break;
      case 'month':
        setCurrentDate((d) => new Date(d.getFullYear(), d.getMonth() + 1, 1));
        break;
    }
  }, [viewRange]);

  const handleToday = useCallback(() => setCurrentDate(new Date()), []);

  // Listen for keyboard shortcut to go to today
  useKeyboardShortcut('go-to-today', handleToday);

  const handlePrint = useCallback(() => window.print(), []);

  const handleExport = useCallback(() => {
    if (!selectedPerson || selectedPersonAssignments.length === 0) return;

    // Create CSV content
    const headers = ['Date', 'Day', 'Time', 'Activity', 'Role', 'Notes'];
    const rows = selectedPersonAssignments.map((a) => [
      a.date,
      format(new Date(a.date), 'EEEE'),
      a.timeOfDay,
      a.activity,
      a.role,
      a.notes ?? '',
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map((row) => row.map((cell) => `"${cell}"`).join(',')),
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    const personName = selectedPerson.name.replace(/\s+/g, '-').toLowerCase();
    link.download = `schedule-${personName}-${startDateStr}-to-${endDateStr}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  }, [selectedPerson, selectedPersonAssignments, startDateStr, endDateStr]);

  // Handle person selection with URL update (for tier 1+)
  const handlePersonSelect = useCallback(
    (personId: string) => {
      setSelectedPersonId(personId);
      // Update URL without full navigation (shallow routing)
      if (personId !== currentUserPersonId) {
        router.replace(`/my-schedule?person=${personId}`, { scroll: false });
      } else {
        router.replace('/my-schedule', { scroll: false });
      }
    },
    [currentUserPersonId, router]
  );

  // Loading state
  const isLoading = blocksLoading || assignmentsLoading || peopleLoading || templatesLoading;
  const error = blocksError ?? assignmentsError ?? peopleError;

  // Determine page title based on context
  const isViewingOther = selectedPersonId && selectedPersonId !== currentUserPersonId;
  const pageTitle = isViewingOther && selectedPerson
    ? `${selectedPerson.name}'s Schedule`
    : 'My Schedule';

  // Determine risk bar label based on tier and action
  const getRiskBarLabel = (): string => {
    if (tier === 0) return 'Read-only';
    if (tier === 1) return isViewingOther ? 'Viewing Other' : 'Scoped Changes';
    return 'High Impact';
  };

  return (
    <div className="flex flex-col min-h-screen bg-gray-50">
      {/* Risk Bar - always visible, color based on tier */}
      <RiskBar
        tier={tier}
        label={getRiskBarLabel()}
        tooltip={riskBarTooltip ?? (isViewingOther
          ? `You are viewing ${selectedPerson?.name ?? 'another person'}'s schedule. Actions available based on your role.`
          : undefined)}
      />

      <div className="max-w-5xl mx-auto px-4 py-8 w-full">
        {/* Breadcrumbs */}
        <PageBreadcrumbs className="mb-4" />

        {/* Header */}
        <div className="mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center gap-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{pageTitle}</h1>
              <p className="text-gray-600 mt-1">
                {isViewingOther && selectedPerson
                  ? `${selectedPerson.type === 'resident' ? `PGY-${selectedPerson.pgyLevel}` : 'Faculty'} rotation schedule`
                  : 'Your personal rotation schedule'}
              </p>
            </div>

            {/* Person Selector - only renders for tier 1+ */}
            <PersonSelector
              people={peopleData?.items ?? []}
              selectedPersonId={selectedPersonId}
              onSelect={handlePersonSelect}
              tier={tier}
              isLoading={peopleLoading}
              className="ml-4"
            />
          </div>

          <div className="flex items-center gap-2">
            <CopyUrlButton label="Share" size="sm" variant="outline" />
          </div>
        </div>

        {/* Controls */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            {/* Navigation */}
            <div className="flex items-center gap-2">
              <button
                onClick={handlePrev}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
                title="Previous"
                aria-label="Previous period"
              >
                <ChevronLeft className="w-5 h-5 text-gray-600" />
              </button>
              <button
                onClick={handleNext}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
                title="Next"
                aria-label="Next period"
              >
                <ChevronRight className="w-5 h-5 text-gray-600" />
              </button>
              <button
                onClick={handleToday}
                className="px-3 py-1.5 text-sm font-medium text-blue-600 hover:bg-blue-50 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
                aria-label="Go to today"
              >
                Today
              </button>
              <span className="text-gray-300 mx-2" aria-hidden="true">|</span>
              <span className="font-medium text-gray-900">
                {format(dateRange.start, 'MMM d')} - {format(dateRange.end, 'MMM d, yyyy')}
              </span>
            </div>

            {/* Range selector and actions */}
            <div className="flex items-center gap-3">
              {/* Range toggle */}
              <div
                className="inline-flex rounded-lg border border-gray-200 bg-gray-50 p-1"
                role="radiogroup"
                aria-label="View range"
              >
                {(['week', '2weeks', 'month'] as ViewRange[]).map((range) => (
                  <button
                    key={range}
                    onClick={() => setViewRange(range)}
                    role="radio"
                    aria-checked={viewRange === range}
                    className={`px-3 py-1 rounded-md text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                      viewRange === range
                        ? 'bg-white text-blue-600 shadow-sm'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    {range === 'week' ? '1 Week' : range === '2weeks' ? '2 Weeks' : 'Month'}
                  </button>
                ))}
              </div>

              {/* Actions */}
              <div className="flex items-center gap-1">
                <button
                  onClick={handleExport}
                  disabled={selectedPersonAssignments.length === 0}
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-blue-500"
                  title="Export to CSV"
                  aria-label="Export schedule to CSV"
                >
                  <Download className="w-5 h-5 text-gray-600" />
                </button>
                <button
                  onClick={handlePrint}
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors print:hidden focus:outline-none focus:ring-2 focus:ring-blue-500"
                  title="Print"
                  aria-label="Print schedule"
                >
                  <Printer className="w-5 h-5 text-gray-600" />
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Content */}
        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <LoadingSpinner />
            <span className="ml-3 text-gray-600">Loading schedule...</span>
          </div>
        )}

        {error && (
          <ErrorAlert
            message={error instanceof Error ? error.message : 'Failed to load schedule'}
          />
        )}

        {!isLoading && !error && !selectedPerson && !selectedPersonId && (
          <EmptyState
            title="Profile Not Found"
            description="We couldn't find a person profile linked to your account. Please contact your administrator."
            icon={Calendar}
          />
        )}

        {!isLoading && !error && !selectedPerson && selectedPersonId && (
          <EmptyState
            title="Person Not Found"
            description="The selected person could not be found. They may have been removed from the system."
            icon={User}
          />
        )}

        {!isLoading && !error && selectedPerson && (
          <>
            {/* Schedule Legend */}
            <ScheduleLegend compact className="mb-4" />

            <PersonalScheduleCard
              person={selectedPerson}
              assignments={selectedPersonAssignments}
              startDate={dateRange.start}
              endDate={dateRange.end}
              showHeader={false}
            />
          </>
        )}

        {/* Work Hours & Summary Stats */}
        {!isLoading && !error && selectedPerson && selectedPersonAssignments.length > 0 && (
          <div className="mt-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Work Hours Calculator */}
            <div className="lg:col-span-1">
              <WorkHoursCalculator
                assignments={selectedPersonAssignments}
                showDetails={true}
              />
            </div>

            {/* Summary stats grid */}
            <div className="lg:col-span-2 grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                <div className="text-2xl font-bold text-gray-900">
                  {selectedPersonAssignments.length}
                </div>
                <div className="text-sm text-gray-500">Total assignments</div>
              </div>
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                <div className="text-2xl font-bold text-blue-600">
                  {selectedPersonAssignments.filter((a) => a.activity.toLowerCase().includes('clinic')).length}
                </div>
                <div className="text-sm text-gray-500">Clinic sessions</div>
              </div>
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                <div className="text-2xl font-bold text-purple-600">
                  {selectedPersonAssignments.filter((a) => a.activity.toLowerCase().includes('inpatient')).length}
                </div>
                <div className="text-sm text-gray-500">Inpatient sessions</div>
              </div>
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                <div className="text-2xl font-bold text-orange-600">
                  {selectedPersonAssignments.filter((a) => a.activity.toLowerCase().includes('call')).length}
                </div>
                <div className="text-sm text-gray-500">Call shifts</div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
