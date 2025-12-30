# Frontend Test Coverage - Priority Checklist
## Session 026 - Implementation Tracking

**Goal:** 60% → 90% coverage over 6 weeks
**Generated:** 2025-12-30

---

## Phase 1: Infrastructure (Week 1) ⚠️ CRITICAL

### Config Fixes
- [ ] Update `jest.config.js` - expand `collectCoverageFrom` to all src files
- [ ] Verify `tsconfig.jest.json` path aliases match main `tsconfig.json`
- [ ] Run coverage and establish TRUE baseline percentage
- [ ] Document baseline in this file: `__%` (current: unknown)

### Missing Source Files (Orphaned Tests)
- [ ] Create `src/features/resilience/` directory and components:
  - [ ] `HealthStatusIndicator.tsx` - Referenced by `health-status.test.tsx`
  - [ ] `ContingencyAnalysis.tsx` - Referenced by `contingency-analysis.test.tsx`
  - [ ] `HubVisualization.tsx` - Referenced by `HubViz.test.tsx`
  - [ ] Main resilience hub component - Referenced by `resilience-hub.test.tsx`
- [ ] Create `src/hooks/useProcedures.ts`:
  - [ ] Export `useProcedures` hook
  - [ ] Export `useProcedure` hook
  - [ ] Export `useCredentials` hook
- [ ] Review `__tests__/features/fmit/FMITDetection.test.tsx`:
  - [ ] Determine if source should exist or test should be removed
  - [ ] Create `src/features/fmit-timeline/FMITDetection.tsx` OR delete test

### Test Suite Health
- [ ] Fix all 89 failing test suites
- [ ] Achieve > 95% test pass rate
- [ ] Reduce test execution time to < 60 seconds if possible

**Exit Criteria:** All tests passing, accurate coverage baseline established

---

## Phase 2: Core User Flows (Weeks 2-3) 🎯 HIGH PRIORITY

Target: 40% → 70% coverage

### Week 2: Navigation & Schedule Views

#### Day 1-2: Navigation Components
- [ ] `src/components/Navigation.tsx`
  - [ ] Basic rendering
  - [ ] Active route highlighting
  - [ ] Mobile responsive behavior
  - [ ] Accessibility (keyboard navigation)
- [ ] `src/components/UserMenu.tsx`
  - [ ] Menu toggle
  - [ ] Logout functionality
  - [ ] User info display
  - [ ] Dropdown interactions
- [ ] `src/components/MobileNav.tsx`
  - [ ] Drawer open/close
  - [ ] Route navigation
  - [ ] Touch interactions
- [ ] `src/contexts/ToastContext.tsx`
  - [ ] Show/hide toasts
  - [ ] Multiple toast handling
  - [ ] Auto-dismiss timers
  - [ ] Toast types (success, error, warning)

#### Day 3-5: Schedule Views
- [ ] `src/components/schedule/ScheduleGrid.tsx`
  - [ ] Grid rendering with data
  - [ ] Cell click interactions
  - [ ] Drag-and-drop (if applicable)
  - [ ] Empty state
  - [ ] Loading state
- [ ] `src/components/schedule/MonthView.tsx`
  - [ ] Month navigation
  - [ ] Date cell rendering
  - [ ] Assignment display
  - [ ] Click handling
- [ ] `src/components/schedule/WeekView.tsx`
  - [ ] Week navigation
  - [ ] Day columns
  - [ ] Assignment rows
  - [ ] Time slots
- [ ] `src/components/schedule/ScheduleHeader.tsx`
  - [ ] Title display
  - [ ] View switcher
  - [ ] Date range display
  - [ ] Action buttons
- [ ] `src/components/schedule/ScheduleLegend.tsx`
  - [ ] Color key display
  - [ ] Rotation types
  - [ ] Toggle visibility

### Week 3: Modals, Loading, Forms

#### Day 1-2: Modals & Dialogs
- [ ] `src/components/Modal.tsx`
  - [ ] Open/close
  - [ ] Outside click to close
  - [ ] Escape key to close
  - [ ] Focus trap
  - [ ] Accessibility (ARIA labels)
- [ ] Enhance `src/components/ConfirmDialog.tsx` (has basic tests)
  - [ ] Add confirmation callback tests
  - [ ] Add cancellation tests
  - [ ] Add keyboard interaction tests
- [ ] `src/components/GenerateScheduleDialog.tsx`
  - [ ] Form validation
  - [ ] API call on submit
  - [ ] Loading state
  - [ ] Success/error handling

#### Day 3: Loading & Error States
- [ ] `src/components/LoadingSpinner.tsx`
  - [ ] Renders with different sizes
  - [ ] Custom colors
  - [ ] Accessibility (aria-label)
- [ ] `src/components/LoadingStates.tsx`
  - [ ] Different loading states
  - [ ] Conditional rendering
- [ ] `src/components/EmptyState.tsx`
  - [ ] Message display
  - [ ] Icon rendering
  - [ ] Call-to-action button
- [ ] `src/components/ErrorAlert.tsx`
  - [ ] Error message display
  - [ ] Dismiss functionality
  - [ ] Different error types

#### Day 4-5: Form Components
- [ ] `src/components/forms/Input.tsx`
  - [ ] Text input
  - [ ] Number input
  - [ ] Validation states (error, success)
  - [ ] Disabled state
  - [ ] onChange handler
- [ ] `src/components/forms/Select.tsx`
  - [ ] Option rendering
  - [ ] Selection change
  - [ ] Placeholder
  - [ ] Disabled state
- [ ] `src/components/forms/TextArea.tsx`
  - [ ] Multi-line input
  - [ ] Character count
  - [ ] Resize behavior
  - [ ] Validation
- [ ] Enhance `src/components/forms/DatePicker.tsx` (has basic tests)
  - [ ] Add keyboard navigation tests
  - [ ] Add min/max date tests
  - [ ] Add disabled dates tests

**Week 2-3 Exit Criteria:** 70% coverage achieved, all core user flows tested

---

## Phase 3: Feature Modules (Weeks 4-5) 📦 MEDIUM PRIORITY

Target: 70% → 85% coverage

### Week 4: Complete Partially-Covered Features

#### Day 1-2: Conflicts Feature (20% → 90%)
- [ ] `src/features/conflicts/ConflictCard.tsx`
  - [ ] Display conflict details
  - [ ] Action buttons
  - [ ] Severity indicators
- [ ] `src/features/conflicts/ConflictHistory.tsx`
  - [ ] Timeline rendering
  - [ ] Filter by date
  - [ ] Resolution status
- [ ] `src/features/conflicts/ConflictResolutionSuggestions.tsx`
  - [ ] Suggestion list
  - [ ] Apply suggestion
  - [ ] AI-generated suggestions
- [ ] `src/features/conflicts/BatchResolution.tsx`
  - [ ] Multi-select conflicts
  - [ ] Bulk resolution
  - [ ] Progress indicator
- [ ] `src/features/conflicts/ManualOverrideModal.tsx`
  - [ ] Override form
  - [ ] Validation
  - [ ] Confirmation

#### Day 3-4: Import/Export Feature (11% → 90%)
- [ ] `src/features/import-export/BulkImportModal.tsx`
  - [ ] File upload
  - [ ] File validation
  - [ ] Preview data
  - [ ] Import execution
- [ ] `src/features/import-export/ImportPreview.tsx`
  - [ ] Data table rendering
  - [ ] Column mapping
  - [ ] Error highlighting
- [ ] `src/features/import-export/ImportProgressIndicator.tsx`
  - [ ] Progress bar
  - [ ] Status messages
  - [ ] Cancel import
- [ ] `src/features/import-export/useExport.ts`
  - [ ] Export data hook
  - [ ] Format selection (CSV, Excel, PDF)
  - [ ] Error handling
- [ ] `src/features/import-export/useImport.ts`
  - [ ] Import data hook
  - [ ] Validation
  - [ ] Success/error callbacks
- [ ] `src/features/import-export/validation.ts`
  - [ ] Validate CSV structure
  - [ ] Validate data types
  - [ ] Validate required fields

#### Day 5: Call Roster Feature (43% → 90%)
- [ ] `src/features/call-roster/CallCalendarDay.tsx`
  - [ ] Day rendering
  - [ ] On-call display
  - [ ] Click to view details
- [ ] `src/features/call-roster/CallRoster.tsx` (main component)
  - [ ] Month view
  - [ ] Navigate months
  - [ ] Filter by role
  - [ ] Print view
- [ ] Enhance `src/features/call-roster/hooks.ts`
  - [ ] Add more test scenarios
  - [ ] Test error cases
  - [ ] Test loading states

### Week 5: Hooks & FMIT Timeline

#### Day 1-2: FMIT Timeline (17% → 90%)
- [ ] `src/features/fmit-timeline/FMITTimeline.tsx`
  - [ ] Timeline rendering
  - [ ] Resident rows
  - [ ] Block periods
  - [ ] Compliance indicators
- [ ] `src/features/fmit-timeline/TimelineControls.tsx`
  - [ ] Date range selector
  - [ ] View options
  - [ ] Export button
- [ ] `src/features/fmit-timeline/TimelineRow.tsx`
  - [ ] Resident info
  - [ ] Block cells
  - [ ] Color coding
  - [ ] Click interactions

#### Day 3-4: Untested Hooks (0% → 90%)
- [ ] `src/hooks/useBlocks.ts`
  - [ ] Fetch blocks
  - [ ] Create block
  - [ ] Update block
  - [ ] Delete block
  - [ ] Error handling
- [ ] `src/hooks/useClaudeChat.ts`
  - [ ] Send message
  - [ ] Receive response
  - [ ] Chat history
  - [ ] WebSocket connection
- [ ] `src/hooks/useGameTheory.ts`
  - [ ] Fetch simulations
  - [ ] Run simulation
  - [ ] Results parsing
- [ ] `src/hooks/useHealth.ts`
  - [ ] Health check
  - [ ] Status updates
  - [ ] Alert thresholds
- [ ] `src/hooks/useRAG.ts`
  - [ ] Search query
  - [ ] Result handling
  - [ ] Relevance scoring
- [ ] `src/hooks/useResilience.ts`
  - [ ] Resilience metrics
  - [ ] N-1/N-2 analysis
  - [ ] Defense levels
- [ ] `src/hooks/useAdminScheduling.ts`
  - [ ] Generate schedule
  - [ ] Configuration
  - [ ] Validation
  - [ ] Progress tracking
- [ ] `src/hooks/useWebSocket.ts`
  - [ ] Connection management
  - [ ] Message handling
  - [ ] Reconnect logic
  - [ ] Event listeners

#### Day 5: Admin & Dashboard Components
- [ ] `src/components/admin/AlgorithmComparisonChart.tsx`
- [ ] `src/components/admin/ClaudeCodeChat.tsx`
- [ ] `src/components/admin/ConfigurationPresets.tsx`
- [ ] `src/components/admin/CoverageTrendChart.tsx`
- [ ] `src/components/admin/MCPCapabilitiesPanel.tsx`
- [ ] `src/components/dashboard/QuickActions.tsx`
- [ ] `src/components/dashboard/ScheduleSummary.tsx`
- [ ] `src/components/dashboard/UpcomingAbsences.tsx`
- [ ] `src/components/dashboard/UpcomingAssignmentsPreview.tsx`

**Week 4-5 Exit Criteria:** 85% coverage achieved, all major features tested

---

## Phase 4: Supporting Components (Week 6) 🎨 POLISH

Target: 85% → 90%+ coverage

### Common Components
- [ ] `src/components/common/Breadcrumbs.tsx`
- [ ] `src/components/common/CopyToClipboard.tsx`
- [ ] `src/components/common/KeyboardShortcutHelp.tsx`
- [ ] `src/components/common/ProgressIndicator.tsx`

### Game Theory Components
- [ ] `src/components/game-theory/EvolutionChart.tsx`
- [ ] `src/components/game-theory/PayoffMatrix.tsx`
- [ ] `src/components/game-theory/StrategyCard.tsx`
- [ ] `src/components/game-theory/TournamentCard.tsx`

### Schedule Supporting Components
- [ ] `src/components/schedule/MyScheduleWidget.tsx`
- [ ] `src/components/schedule/PersonalScheduleCard.tsx`
- [ ] `src/components/schedule/QuickSwapButton.tsx`
- [ ] `src/components/schedule/WorkHoursCalculator.tsx`

### Contexts
- [ ] `src/contexts/ClaudeChatContext.tsx`

### Skeleton Loaders (Nice-to-Have)
- [ ] `src/components/skeletons/CalendarSkeleton.tsx`
- [ ] `src/components/skeletons/CardSkeleton.tsx`
- [ ] `src/components/skeletons/ComplianceCardSkeleton.tsx`
- [ ] `src/components/skeletons/PersonCardSkeleton.tsx`
- [ ] `src/components/skeletons/TableRowSkeleton.tsx`

**Week 6 Exit Criteria:** 90%+ coverage achieved

---

## Phase 5: Edge Cases & Advanced Features (Stretch Goals) 🚀

### Drag-and-Drop Components
- [ ] `src/components/schedule/drag/DraggableBlockCell.tsx`
- [ ] `src/components/schedule/drag/FacultyInpatientWeeksView.tsx`
- [ ] `src/components/schedule/drag/ResidentAcademicYearView.tsx`
- [ ] `src/components/schedule/drag/ScheduleDragProvider.tsx`

### 3D Visualization (Low Priority)
- [ ] `src/features/voxel-schedule/VoxelScheduleView.tsx`
- [ ] `src/features/holographic-hub/HolographicManifold.tsx`
- [ ] `src/features/holographic-hub/LayerControlPanel.tsx`

### RAG Search
- [ ] `src/components/rag/RAGSearch.tsx`

### Next.js Pages (Integration Tests)
- [ ] `src/app/login/page.tsx`
- [ ] `src/app/page.tsx` (home)
- [ ] `src/app/schedule/page.tsx`
- [ ] `src/app/my-schedule/page.tsx`
- [ ] `src/app/swaps/page.tsx`
- [ ] `src/app/absences/page.tsx`
- [ ] Other pages as needed

---

## Coverage Milestones

### Baseline (Week 1)
- [ ] Establish true baseline: ___%
- [ ] All 89 failing suites fixed
- [ ] Coverage config corrected

### Milestone 1 (Week 3)
- [ ] 70% overall coverage
- [ ] 90%+ coverage on core user flows
- [ ] 100% pass rate on existing tests

### Milestone 2 (Week 5)
- [ ] 85% overall coverage
- [ ] All feature modules > 80% coverage
- [ ] All custom hooks tested

### Final (Week 6)
- [ ] 90%+ overall coverage
- [ ] Statements: 90%+
- [ ] Branches: 85%+
- [ ] Functions: 90%+
- [ ] Lines: 90%+

---

## Testing Best Practices Checklist

For each component/hook, ensure tests cover:

### Component Tests
- [ ] Renders without crashing
- [ ] Renders with required props
- [ ] Renders with optional props
- [ ] Handles user interactions (clicks, typing, etc.)
- [ ] Shows loading state
- [ ] Shows error state
- [ ] Shows empty state
- [ ] Handles edge cases (null, undefined, empty arrays)
- [ ] Accessibility (ARIA labels, keyboard navigation)
- [ ] Responsive behavior (if applicable)

### Hook Tests
- [ ] Returns expected initial state
- [ ] Fetches data successfully
- [ ] Handles loading state
- [ ] Handles error state
- [ ] Handles empty data
- [ ] Triggers mutations/actions
- [ ] Updates state correctly
- [ ] Cleans up on unmount (if applicable)
- [ ] Handles race conditions (if applicable)

### Integration Tests
- [ ] Multiple components work together
- [ ] API calls are made correctly
- [ ] Data flows through the app
- [ ] Error boundaries catch errors
- [ ] Navigation works
- [ ] Auth gates work

---

## Quick Reference Commands

```bash
# Run all tests
npm test

# Run with coverage
npm run test:coverage

# Run specific test file
npm test -- Navigation.test.tsx

# Watch mode
npm run test:watch

# Update snapshots
npm test -- -u

# CI mode
npm run test:ci
```

---

## Notes & Blockers

### Current Blockers
- [ ] ~~Jest config only covering `src/lib`~~ (Phase 1)
- [ ] ~~89 test suites failing due to missing sources~~ (Phase 1)
- [ ] ~~Module resolution errors~~ (Phase 1)

### Decisions Needed
- [ ] Should FMIT feature exist or tests be removed?
- [ ] Priority order for admin features?
- [ ] Should Next.js pages have integration tests?

### Risks
- Test execution time may increase significantly
- Flaky tests in drag-and-drop components
- MSW mocking complexity for WebSocket hooks

---

**Last Updated:** 2025-12-30
**Status:** Phase 1 (Infrastructure) - Ready to start
**Next Action:** Fix `jest.config.js` coverage collection
