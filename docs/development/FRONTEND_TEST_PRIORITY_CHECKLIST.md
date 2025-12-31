# Frontend Test Implementation Priority Checklist

**G2_RECON Generated:** 2025-12-31
**Purpose:** Actionable checklist for test implementation prioritized by medical system criticality

---

## PHASE 1: CRITICAL MEDICAL SYSTEM TESTS (Week 1-2)

### Block 1.1: Resilience Framework Components (20h)

#### Component: ResilienceDashboard.tsx
- [ ] Setup test file: `__tests__/components/resilience/ResilienceDashboard.test.tsx`
- [ ] Test: Render dashboard with health data
- [ ] Test: Display all key metrics (Rt, utilization, defense level)
- [ ] Test: Handle missing data gracefully
- [ ] Test: Refresh health status on API call
- [ ] Test: Responsive layout (desktop/mobile)
- [ ] Accessibility: Tab navigation, ARIA labels
- **Estimated:** 3 hours

#### Component: HealthStatusIndicator.tsx
- [ ] Setup test file: `__tests__/components/resilience/HealthStatusIndicator.test.tsx`
- [ ] Test: Render correct status (GREEN/YELLOW/ORANGE/RED/BLACK)
- [ ] Test: Color coding matches design system
- [ ] Test: Pulse animation on alert state
- [ ] Test: Tooltip displays explanation
- [ ] Accessibility: Color should not be only indicator
- **Estimated:** 2 hours

#### Component: EarlyWarningPanel.tsx
- [ ] Setup test file: `__tests__/components/resilience/EarlyWarningPanel.test.tsx`
- [ ] Test: Display early warnings
- [ ] Test: Filter by severity
- [ ] Test: Acknowledge warning (state update)
- [ ] Test: Disable acknowledged warnings from view
- [ ] Test: Sort by timestamp
- [ ] Test: Responsive card layout
- **Estimated:** 3 hours

#### Component: BurnoutRtDisplay.tsx
- [ ] Setup test file: `__tests__/components/resilience/BurnoutRtDisplay.test.tsx`
- [ ] Test: Calculate and display Rt value
- [ ] Test: Show trend (increasing/decreasing)
- [ ] Test: Color coding (safe/warning/critical)
- [ ] Test: Handle invalid data
- [ ] Test: Format number display (2 decimals)
- [ ] Test: Accessibility: Screen reader description
- **Estimated:** 2 hours

#### Component: DefenseLevel.tsx
- [ ] Setup test file: `__tests__/components/resilience/DefenseLevel.test.tsx`
- [ ] Test: Render all 5 defense levels
- [ ] Test: Highlight current defense level
- [ ] Test: Display defense mechanisms at each level
- [ ] Test: Color gradient visualization
- [ ] Test: Responsive breakdown
- **Estimated:** 2 hours

#### Component: N1ContingencyMap.tsx
- [ ] Setup test file: `__tests__/components/resilience/N1ContingencyMap.test.tsx`
- [ ] Test: Render contingency analysis
- [ ] Test: Show impact of N-1 failures
- [ ] Test: Highlight critical failures
- [ ] Test: Display mitigation strategies
- [ ] Test: Visualization performance
- [ ] Test: Interactive node selection
- **Estimated:** 4 hours

#### Component: UtilizationGauge.tsx
- [ ] Setup test file: `__tests__/components/resilience/UtilizationGauge.test.tsx`
- [ ] Test: Display utilization percentage
- [ ] Test: Gauge color zones (safe/warning/critical)
- [ ] Test: Animate to new value
- [ ] Test: Handle edge cases (0%, 100%, >100%)
- [ ] Test: Accessibility: Label + aria-valuenow
- **Estimated:** 2 hours

#### Summary for 1.1
- **Files to Create:** 7 test files
- **Total Hours:** 20
- **Blocker Test:** HealthStatusIndicator (foundation for others)

---

### Block 1.2: Drag-and-Drop Scheduling (24h)

#### Component: ScheduleDragProvider.tsx
- [ ] Setup test file: `__tests__/components/schedule/drag/ScheduleDragProvider.test.tsx`
- [ ] Test: Provider wraps children correctly
- [ ] Test: Context provides drag state
- [ ] Test: Dispatch drag start action
- [ ] Test: Dispatch drag over action
- [ ] Test: Dispatch drop action
- [ ] Test: Validation before allowing drop
- [ ] Test: Compliance check on drop
- [ ] Test: Handle drag cancel
- [ ] Test: Update Redux store on valid drop
- **Estimated:** 4 hours

#### Component: DraggableBlockCell.tsx
- [ ] Setup test file: `__tests__/components/schedule/drag/DraggableBlockCell.test.tsx`
- [ ] Test: Render cell with data
- [ ] Test: Show rotation badge
- [ ] Test: Show person name
- [ ] Test: Drag events fire
- [ ] Test: Highlight on drag over
- [ ] Test: Style changes for different rotation types
- [ ] Test: Keyboard drag (Space to pick up)
- [ ] Test: Accessibility: Draggable button role
- **Estimated:** 5 hours

#### Component: ResidentAcademicYearView.tsx
- [ ] Setup test file: `__tests__/components/schedule/drag/ResidentAcademicYearView.test.tsx`
- [ ] Test: Render 365 days for resident
- [ ] Test: Show assignments for selected resident
- [ ] Test: Navigate between blocks (day/week/month)
- [ ] Test: Filter by rotation type
- [ ] Test: Drag assignment between days
- [ ] Test: Validate compliance on drag end
- [ ] Test: Show violations in red
- [ ] Test: Undo drag operation (Ctrl-Z)
- [ ] Test: Responsive layout
- **Estimated:** 7 hours

#### Component: FacultyInpatientWeeksView.tsx
- [ ] Setup test file: `__tests__/components/schedule/drag/FacultyInpatientWeeksView.test.tsx`
- [ ] Test: Render 52 weeks for faculty
- [ ] Test: Show inpatient weeks only
- [ ] Test: Drag week assignment
- [ ] Test: Show coverage matrix (how many faculty per week)
- [ ] Test: Handle multi-week swaps
- [ ] Test: Validate supervisor ratios
- [ ] Test: Show conflicts in summary
- [ ] Test: Responsive grid layout
- **Estimated:** 8 hours

#### Summary for 1.2
- **Files to Create:** 4 test files
- **Total Hours:** 24
- **Blocker Test:** ScheduleDragProvider (foundation)
- **Integration Test:** Combined drag-drop workflow

---

### Block 1.3: Swap Marketplace Enhancements (16h)

#### Feature: Auto-Matching Algorithm
- [ ] Test file: `__tests__/features/swap-marketplace/auto-matcher.test.tsx`
- [ ] Test: Find matching swaps (A wants X, B wants A)
- [ ] Test: Handle time zone conflicts
- [ ] Test: Validate compliance for both parties
- [ ] Test: Rank matches by quality
- [ ] Test: Prevent swap loops (A↔B↔A↔B)
- [ ] Test: Multi-person swaps (3-way)
- [ ] Test: Performance: Match 1000 requests in <100ms
- [ ] Test: Edge case: No matches found
- **Estimated:** 6 hours

#### Feature: Swap Workflows
- [ ] Test file: `__tests__/features/swap-marketplace/swap-workflow.test.tsx`
- [ ] Test: Request creation flow
- [ ] Test: Auto-match notification
- [ ] Test: Approval workflow
- [ ] Test: Cancellation and refusal
- [ ] Test: 24-hour rollback window
- [ ] Test: State transitions (pending → approved → executed)
- [ ] Test: Audit trail creation
- [ ] Test: Notification to both parties
- **Estimated:** 6 hours

#### Feature: SwapRequestForm Enhancements
- [ ] Test file: `__tests__/features/swap-marketplace/SwapRequestForm.test.tsx`
- [ ] Test: Form validation (required fields)
- [ ] Test: Date picker (prevent past dates)
- [ ] Test: Reason text field (max 500 chars)
- [ ] Test: Submit creates request
- [ ] Test: Error handling
- [ ] Test: Loading state during submission
- [ ] Test: Success feedback
- **Estimated:** 4 hours

#### Summary for 1.3
- **Files to Create/Update:** 3 test files
- **Total Hours:** 16
- **Blocker Test:** Auto-matcher algorithm

---

## PHASE 2: HIGH-PRIORITY FEATURES (Week 3-4)

### Block 2.1: Compliance Components (20h)

#### Component: CompliancePanel.tsx
- [ ] Test file: `__tests__/components/compliance/CompliancePanel.test.tsx`
- [ ] Test: Display all compliance metrics
- [ ] Test: Show violations in red
- [ ] Test: Show warnings in yellow
- [ ] Test: Expand/collapse sections
- [ ] Test: Sort violations by severity
- [ ] Test: 4-week rolling average calculation
- [ ] Test: Responsive layout
- **Estimated:** 3 hours

#### Component: WorkHourGauge.tsx
- [ ] Test file: `__tests__/components/compliance/WorkHourGauge.test.tsx`
- [ ] Test: Display hours as gauge
- [ ] Test: Calculate rolling 4-week average
- [ ] Test: Show zones: safe (<60h), warning (60-80h), violation (>80h)
- [ ] Test: Animate gauge on value change
- [ ] Test: Display trend (up/down/flat)
- [ ] Test: Handle partial week data
- **Estimated:** 2 hours

#### Component: SupervisionRatio.tsx
- [ ] Test file: `__tests__/components/compliance/SupervisionRatio.test.tsx`
- [ ] Test: Display faculty:resident ratio
- [ ] Test: Calculate ratio correctly (by PGY level)
- [ ] Test: PGY-1: 1:2, PGY-2/3: 1:4
- [ ] Test: Show violations when ratio exceeded
- [ ] Test: Highlight required faculty additions
- **Estimated:** 2 hours

#### Component: ViolationAlert.tsx
- [ ] Test file: `__tests__/components/compliance/ViolationAlert.test.tsx`
- [ ] Test: Display violation message
- [ ] Test: Show violation type (80-hour, 1-in-7, supervision)
- [ ] Test: Highlight affected people
- [ ] Test: Show remediation steps
- [ ] Test: Dismissible (24h until reappear)
- [ ] Test: Critical styling
- **Estimated:** 2 hours

#### Component: RollingAverageChart.tsx
- [ ] Test file: `__tests__/components/compliance/RollingAverageChart.test.tsx`
- [ ] Test: Display line chart of rolling average
- [ ] Test: Calculate 4-week rolling average
- [ ] Test: Show threshold line (80h)
- [ ] Test: Hover tooltip shows week details
- [ ] Test: Responsive sizing
- [ ] Test: Handle incomplete data
- **Estimated:** 3 hours

#### Component: DayOffIndicator.tsx
- [ ] Test file: `__tests__/components/compliance/DayOffIndicator.test.tsx`
- [ ] Test: Display day off status
- [ ] Test: Show when 1-in-7 violated
- [ ] Test: Highlight grace period
- [ ] Test: Show upcoming required days off
- **Estimated:** 2 hours

#### Component: ComplianceTimeline.tsx
- [ ] Test file: `__tests__/components/compliance/ComplianceTimeline.test.tsx`
- [ ] Test: Display timeline of compliance events
- [ ] Test: Show violations chronologically
- [ ] Test: Show remediation actions
- [ ] Test: Filter by violation type
- [ ] Test: Export timeline (audit trail)
- **Estimated:** 2 hours

#### Component: ComplianceReport.tsx
- [ ] Test file: `__tests__/components/compliance/ComplianceReport.test.tsx`
- [ ] Test: Generate compliance report
- [ ] Test: Export to PDF
- [ ] Test: Include metrics, violations, timeline
- [ ] Test: Performance: Generate for 50 residents <500ms
- **Estimated:** 2 hours

#### Summary for 2.1
- **Files to Create:** 8 test files
- **Total Hours:** 20
- **Critical:** All tests required for regulatory compliance

---

### Block 2.2: Scheduling Components (16h)

#### Component: BlockTimeline.tsx
- [ ] Test file: `__tests__/components/scheduling/BlockTimeline.test.tsx`
- [ ] Test: Display timeline view
- [ ] Test: Show blocks chronologically
- [ ] Test: Color code by rotation
- [ ] Test: Navigate between time periods
- [ ] Test: Show assignments on each block
- **Estimated:** 3 hours

#### Component: ResidentCard.tsx
- [ ] Test file: `__tests__/components/scheduling/ResidentCard.test.tsx`
- [ ] Test: Display resident name + PGY level
- [ ] Test: Show work hours
- [ ] Test: Show compliance status
- [ ] Test: Highlight if in violation
- [ ] Test: Click to view personal schedule
- **Estimated:** 2 hours

#### Component: TimeSlot.tsx
- [ ] Test file: `__tests__/components/scheduling/TimeSlot.test.tsx`
- [ ] Test: Render time slot
- [ ] Test: Show rotation badge
- [ ] Test: Hover shows details
- [ ] Test: Click opens edit modal
- **Estimated:** 2 hours

#### Component: RotationBadge.tsx
- [ ] Test file: `__tests__/components/scheduling/RotationBadge.test.tsx`
- [ ] Test: Display rotation name
- [ ] Test: Show correct color
- [ ] Test: Size variants (small/medium/large)
- [ ] Test: Tooltip on hover
- **Estimated:** 1 hour

#### Component: ComplianceIndicator.tsx
- [ ] Test file: `__tests__/components/scheduling/ComplianceIndicator.test.tsx`
- [ ] Test: Display compliance status
- [ ] Test: Green (compliant), Yellow (warning), Red (violation)
- [ ] Test: Show reason on hover
- [ ] Test: Update on data change
- **Estimated:** 2 hours

#### Component: CoverageMatrix.tsx
- [ ] Test file: `__tests__/components/scheduling/CoverageMatrix.test.tsx`
- [ ] Test: Display coverage grid
- [ ] Test: Show faculty availability
- [ ] Test: Highlight gaps
- [ ] Test: Calculate coverage percentages
- [ ] Test: Performance: 50 faculty × 365 days
- [ ] Test: Export to CSV
- **Estimated:** 4 hours

#### Summary for 2.2
- **Files to Create:** 6 test files
- **Total Hours:** 16
- **Integration:** Test together in scheduling workflows

---

### Block 2.3: Schedule Views (32h)

#### High-Priority Schedule Components
- [ ] `BlockCard.tsx` - 2 hours
- [ ] `MonthView.tsx` - 4 hours
- [ ] `WeekView.tsx` - 4 hours
- [ ] `TimelineView.tsx` - 4 hours
- [ ] `MyScheduleWidget.tsx` - 3 hours
- [ ] `PersonalScheduleCard.tsx` - 2 hours
- [ ] `EditAssignmentModal.tsx` - 4 hours
- [ ] `ScheduleFilters.tsx` - 3 hours
- [ ] `WorkHoursCalculator.tsx` - 3 hours
- [ ] `ConflictHighlight.tsx` - 2 hours
- [ ] `ScheduleGrid.tsx` (regression) - 2 hours

#### Test Strategy
- Unit tests for calculations
- Integration tests for views
- Visual regression tests for layout
- Performance tests for large datasets (365 days × 50 people)

#### Summary for 2.3
- **Files to Create/Update:** 11 test files
- **Total Hours:** 32
- **Critical Path:** Month/Week/Timeline views

---

## PHASE 3: MEDIUM-PRIORITY FEATURES (Week 5-6)

### Block 3.1: UI Component Library (24h)

#### Critical UI Components (accessibility focus)

**Forms:**
- [ ] `Button.tsx` - 2 hours
- [ ] `Input.tsx` - 2 hours
- [ ] `Select.tsx` - 3 hours
- [ ] `DatePicker.tsx` - 3 hours

**Feedback:**
- [ ] `Alert.tsx` - 2 hours
- [ ] `Badge.tsx` - 1 hour
- [ ] `Spinner.tsx` - 1 hour
- [ ] `ProgressBar.tsx` - 2 hours

**Navigation:**
- [ ] `Card.tsx` - 2 hours
- [ ] `Dropdown.tsx` - 2 hours
- [ ] `Tabs.tsx` - 2 hours

**Other:**
- [ ] `Avatar.tsx` - 1 hour
- [ ] `Switch.tsx` - 1 hour
- [ ] `Tooltip.tsx` - 1 hour

#### Accessibility Requirements
- WCAG 2.1 Level AA compliance
- Keyboard navigation
- Screen reader testing
- Color contrast (4.5:1 for normal text)
- Focus indicators

#### Summary for 3.1
- **Files to Create:** 15 test files
- **Total Hours:** 24
- **Accessibility Audit:** Integrated with tests

---

### Block 3.2: Admin Components (14h)

#### Component: ClaudeCodeChat.tsx
- [ ] Test file: `__tests__/components/admin/ClaudeCodeChat.test.tsx`
- [ ] Test: Render chat interface
- [ ] Test: Send message to Claude
- [ ] Test: Display response
- [ ] Test: Handle errors gracefully
- [ ] Test: Show loading state
- [ ] Test: Scroll to latest message
- **Estimated:** 3 hours

#### Component: MCPCapabilitiesPanel.tsx
- [ ] Test file: `__tests__/components/admin/MCPCapabilitiesPanel.test.tsx`
- [ ] Test: Display available MCP tools
- [ ] Test: Show tool descriptions
- [ ] Test: Filter tools by category
- [ ] Test: Performance: Load 29+ tools
- **Estimated:** 2 hours

#### Component: ConfigurationPresets.tsx
- [ ] Test file: `__tests__/components/admin/ConfigurationPresets.test.tsx`
- [ ] Test: Load preset configurations
- [ ] Test: Apply preset
- [ ] Test: Save custom preset
- [ ] Test: Delete preset
- [ ] Test: Show changes before apply
- **Estimated:** 3 hours

#### Component: AlgorithmComparisonChart.tsx
- [ ] Test file: `__tests__/components/admin/AlgorithmComparisonChart.test.tsx`
- [ ] Test: Display comparison chart
- [ ] Test: Show metrics side-by-side
- [ ] Test: Responsive sizing
- [ ] Test: Handle missing data
- **Estimated:** 2 hours

#### Component: CoverageTrendChart.tsx
- [ ] Test file: `__tests__/components/admin/CoverageTrendChart.test.tsx`
- [ ] Test: Display trend chart
- [ ] Test: Calculate coverage trends
- [ ] Test: Export data
- [ ] Test: Responsive sizing
- **Estimated:** 2 hours

#### Other Admin Features
- [ ] Miscellaneous admin utilities - 2 hours

#### Summary for 3.2
- **Files to Create:** 5 test files
- **Total Hours:** 14

---

### Block 3.3: Feature Components (28h)

#### FMIT Timeline (0% tested, 6h)
- [ ] `FMITTimeline.tsx` - 3 hours
- [ ] `TimelineControls.tsx` - 1 hour
- [ ] `TimelineRow.tsx` - 2 hours

#### Holographic Hub (25% tested, 8h)
- [ ] `HolographicManifold.tsx` - 4 hours
- [ ] `LayerControlPanel.tsx` - 2 hours
- [ ] Shaders validation - 2 hours

#### Daily Manifest (75% tested, 2h)
- [ ] Missing 1 component - 2 hours

#### Import/Export Utilities (8h)
- [ ] `useImport.ts` enhancements - 3 hours
- [ ] `useExport.ts` enhancements - 3 hours
- [ ] Validation utilities - 2 hours

#### Custom Hooks (4h)
- [ ] WebSocket hooks - 2 hours
- [ ] Advanced async patterns - 2 hours

#### Summary for 3.3
- **Files to Create/Update:** 15+ test files
- **Total Hours:** 28

---

## PHASE 4: PAGE INTEGRATION TESTS (Ongoing)

### Block 4.1: Page Route Tests (40h)

#### Critical Pages (18 missing tests)

**High-Priority Pages:**
- [ ] `/schedule` - 4 hours (main view)
- [ ] `/my-schedule` - 3 hours (personal)
- [ ] `/compliance` - 3 hours (audit trail)
- [ ] `/swaps` - 3 hours (marketplace)
- [ ] `/admin/health` - 2 hours (resilience dashboard)

**Medium-Priority Pages:**
- [ ] `/call-roster` - 2 hours
- [ ] `/conflicts` - 2 hours
- [ ] `/daily-manifest` - 2 hours
- [ ] `/import-export` - 2 hours
- [ ] `/absences` - 2 hours
- [ ] `/templates` - 2 hours

**Lower-Priority Pages:**
- [ ] `/heatmap` - 2 hours
- [ ] `/people` - 2 hours
- [ ] `/settings` - 1 hour
- [ ] `/help` - 1 hour
- [ ] Other pages - 6 hours

#### Test Strategy
- Integration tests (routes + components + API)
- User workflows
- Error scenarios
- Performance baselines

#### Summary for 4.1
- **Files to Create:** 18 test files
- **Total Hours:** 40

---

## SUMMARY TABLE

| Phase | Block | Hours | Status | Priority |
|-------|-------|-------|--------|----------|
| 1 | Resilience Framework | 20 | TODO | CRITICAL |
| 1 | Drag-Drop Scheduling | 24 | TODO | CRITICAL |
| 1 | Swap Marketplace | 16 | TODO | CRITICAL |
| 2 | Compliance Components | 20 | TODO | HIGH |
| 2 | Scheduling Components | 16 | TODO | HIGH |
| 2 | Schedule Views | 32 | TODO | HIGH |
| 3 | UI Components | 24 | TODO | MEDIUM |
| 3 | Admin Components | 14 | TODO | MEDIUM |
| 3 | Feature Components | 28 | TODO | MEDIUM |
| 4 | Page Routes | 40 | TODO | MEDIUM |
| **TOTAL** | | **244** | | |

---

## Quick Start Template

### Test File Structure
```typescript
// __tests__/components/resilience/ResilienceDashboard.test.tsx
import { render, screen } from '@testing-library/react';
import { ResilienceDashboard } from '@/components/resilience';
import { mockResilienceData } from '@/__fixtures__/resilience';

describe('ResilienceDashboard', () => {
  it('renders health status correctly', () => {
    render(<ResilienceDashboard data={mockResilienceData} />);
    expect(screen.getByText(/Health Status/i)).toBeInTheDocument();
  });

  it('handles missing data gracefully', () => {
    render(<ResilienceDashboard data={null} />);
    expect(screen.getByText(/No data/i)).toBeInTheDocument();
  });

  it('displays all metrics', () => {
    const { getByTestId } = render(<ResilienceDashboard data={mockResilienceData} />);
    expect(getByTestId('metric-rt')).toBeInTheDocument();
    expect(getByTestId('metric-utilization')).toBeInTheDocument();
    expect(getByTestId('metric-defense')).toBeInTheDocument();
  });

  it('meets accessibility standards', () => {
    const { container } = render(<ResilienceDashboard data={mockResilienceData} />);
    // Run axe accessibility audit
    expect(container).toBeAccessible();
  });
});
```

---

## Next Steps

1. **Create fixtures** - Mock data for all domains
2. **Setup test utilities** - Helper functions for common tests
3. **Block assignment** - Assign developers to blocks
4. **Weekly check-ins** - Track progress against 244-hour budget
5. **CI/CD integration** - Enforce coverage thresholds

---

**Report Status:** ACTIONABLE
**Last Updated:** 2025-12-31
**Owner:** G2_RECON (Reconnaissance Agent)
