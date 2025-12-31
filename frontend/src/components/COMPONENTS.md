# Component Library Documentation

A comprehensive, reusable component library for the Residency Scheduler application built with React, TypeScript, and TailwindCSS.

## Table of Contents

1. [UI Primitives](#ui-primitives)
2. [Scheduling Components](#scheduling-components)
3. [Data Display](#data-display)
4. [Form Components](#form-components)
5. [Layout Components](#layout-components)
6. [Usage Examples](#usage-examples)

---

## UI Primitives

Located in `/components/ui/`

### Button
Multi-variant button component with loading states.

**Variants:** `primary`, `secondary`, `danger`, `ghost`, `outline`, `success`
**Sizes:** `sm`, `md`, `lg`

```tsx
import { Button, IconButton } from '@/components';

<Button variant="primary" size="md" isLoading>
  Save Changes
</Button>

<IconButton variant="ghost" size="sm">
  <TrashIcon />
</IconButton>
```

### Badge
Labels, tags, and status indicators.

**Variants:** `default`, `primary`, `success`, `warning`, `danger`, `info`
**Sizes:** `sm`, `md`, `lg`

```tsx
import { Badge, NumericBadge } from '@/components';

<Badge variant="success" dot>Active</Badge>
<NumericBadge count={5} variant="danger" />
```

### Avatar
User avatars with image, initials fallback, and status indicator.

**Sizes:** `xs`, `sm`, `md`, `lg`, `xl`
**Status:** `online`, `offline`, `away`, `busy`

```tsx
import { Avatar, AvatarGroup } from '@/components';

<Avatar src="/avatar.jpg" name="Dr. Smith" status="online" size="md" />
<AvatarGroup avatars={residents} max={3} />
```

### Dropdown
Dropdown menu with keyboard navigation.

```tsx
import { Dropdown, SelectDropdown } from '@/components';

<Dropdown
  trigger={<Button>Actions</Button>}
  items={[
    { label: 'Edit', value: 'edit', icon: <EditIcon /> },
    { label: 'Delete', value: 'delete', danger: true },
  ]}
  onSelect={(value) => console.log(value)}
/>
```

### Card
Container components with headers, footers, and content sections.

```tsx
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components';

<Card shadow="md" hover>
  <CardHeader>
    <CardTitle>Compliance Status</CardTitle>
    <CardDescription>ACGME compliance overview</CardDescription>
  </CardHeader>
  <CardContent>
    {/* Content */}
  </CardContent>
  <CardFooter>
    <Button>View Details</Button>
  </CardFooter>
</Card>
```

### Input
Text input with label, error, and icon support.

```tsx
import { Input } from '@/components';

<Input
  label="Email"
  type="email"
  placeholder="you@example.com"
  error="Invalid email"
  leftIcon={<MailIcon />}
/>
```

### Alert
Important message display with variants.

**Variants:** `info`, `success`, `warning`, `error`

```tsx
import { Alert } from '@/components';

<Alert variant="success" title="Success" dismissible onDismiss={() => {}}>
  Your changes have been saved.
</Alert>
```

### Tooltip
Contextual information on hover.

**Positions:** `top`, `bottom`, `left`, `right`

```tsx
import { Tooltip } from '@/components';

<Tooltip content="This is helpful info" position="top">
  <Button>Hover me</Button>
</Tooltip>
```

### Tabs
Organize content into separate views.

**Variants:** `default`, `pills`

```tsx
import { Tabs } from '@/components';

<Tabs
  tabs={[
    { id: 'tab1', label: 'Overview', content: <Overview /> },
    { id: 'tab2', label: 'Details', content: <Details /> },
  ]}
  variant="pills"
/>
```

---

## Scheduling Components

Located in `/components/scheduling/`

### TimeSlot
AM/PM schedule block display.

```tsx
import { TimeSlot, TimeSlotGrid } from '@/components';

<TimeSlot
  date={new Date()}
  period="AM"
  rotation="Clinic"
  person="Dr. Smith"
  onClick={() => {}}
/>
```

### ResidentCard
Resident information card with compliance tracking.

```tsx
import { ResidentCard, ResidentListItem } from '@/components';

<ResidentCard
  id="123"
  name="Dr. Jane Smith"
  role="RESIDENT"
  pgyLevel={2}
  currentRotation="Inpatient"
  hoursThisWeek={65}
  maxHours={80}
  complianceStatus="compliant"
/>
```

### RotationBadge
Rotation type badges with consistent styling.

**Types:** `clinic`, `inpatient`, `call`, `leave`, `procedure`, `conference`, `admin`, `research`, `vacation`, `sick`

```tsx
import { RotationBadge, RotationLegend } from '@/components';

<RotationBadge type="clinic" label="Clinic" showDot />
<RotationLegend types={['clinic', 'inpatient', 'call']} />
```

### ComplianceIndicator
ACGME compliance status indicators.

**Status:** `compliant`, `warning`, `violation`, `pending`

```tsx
import { ComplianceIndicator, ComplianceCard, ComplianceSummary } from '@/components';

<ComplianceIndicator
  status="warning"
  rule="80-Hour Rule"
  message="75/80 hours this week"
  showLabel
/>

<ComplianceCard
  status="violation"
  rule="1-in-7 Rule"
  message="No day off in 8 days"
  actions={<Button size="sm">Fix Schedule</Button>}
/>
```

### CoverageMatrix
Staffing level visualization.

```tsx
import { CoverageMatrix, CoverageSummary } from '@/components';

<CoverageMatrix
  slots={coverageSlots}
  dateRange={{ start: new Date(), end: new Date() }}
  showWarnings
/>

<CoverageSummary slots={coverageSlots} />
```

### BlockTimeline
Schedule block timeline visualization.

```tsx
import { BlockTimeline, MultiPersonTimeline } from '@/components';

<BlockTimeline
  blocks={scheduleBlocks}
  startDate={new Date('2025-01-01')}
  endDate={new Date('2025-12-31')}
  showLabels
/>
```

---

## Data Display

Located in `/components/data-display/`

### DataTable
Table with sorting and filtering.

```tsx
import { DataTable, CompactTable } from '@/components';

<DataTable
  data={residents}
  columns={[
    {
      key: 'name',
      header: 'Name',
      accessor: (r) => r.name,
      sortable: true,
    },
    {
      key: 'role',
      header: 'Role',
      accessor: (r) => <Badge>{r.role}</Badge>,
    },
  ]}
  keyExtractor={(r) => r.id}
  onRowClick={(r) => navigate(`/residents/${r.id}`)}
/>
```

### StatCard
Key metrics display.

```tsx
import { StatCard, StatGrid, CompactStat } from '@/components';

<StatCard
  label="Total Residents"
  value={24}
  change={12}
  changeLabel="vs last month"
  trend="up"
  icon={<UserIcon />}
  variant="success"
/>

<StatGrid
  stats={[stat1, stat2, stat3]}
  columns={3}
/>
```

### ChartWrapper
Consistent chart presentation.

```tsx
import { ChartWrapper } from '@/components';

<ChartWrapper
  title="Work Hours Trend"
  description="Weekly work hours over time"
  actions={<Button size="sm">Export</Button>}
  loading={isLoading}
  error={error}
>
  <LineChart data={data} />
</ChartWrapper>
```

### Pagination
Page navigation with size selector.

```tsx
import { Pagination, SimplePagination } from '@/components';

<Pagination
  currentPage={currentPage}
  totalPages={totalPages}
  onPageChange={setCurrentPage}
  totalItems={100}
  pageSize={10}
  showPageSize
  onPageSizeChange={setPageSize}
/>
```

---

## Form Components

Located in `/components/form/`

### DateRangePicker
Date range selection with presets.

```tsx
import { DateRangePicker, DateRangePresets } from '@/components';

<DateRangePicker
  value={{ start: new Date(), end: new Date() }}
  onChange={setDateRange}
  label="Select Date Range"
/>

<DateRangePresets onSelect={setDateRange} />
```

### MultiSelect
Multiple option selection with search.

```tsx
import { MultiSelect } from '@/components';

<MultiSelect
  options={[
    { label: 'Resident', value: 'resident' },
    { label: 'Faculty', value: 'faculty' },
  ]}
  value={selected}
  onChange={setSelected}
  label="Select Roles"
  searchable
  maxDisplay={3}
/>
```

### SearchInput
Search with debounce and suggestions.

```tsx
import { SearchInput, SearchWithSuggestions } from '@/components';

<SearchInput
  value={query}
  onChange={setQuery}
  onSearch={performSearch}
  placeholder="Search residents..."
  debounceMs={300}
  showClearButton
/>

<SearchWithSuggestions
  value={query}
  onChange={setQuery}
  suggestions={suggestions}
  onSuggestionSelect={handleSelect}
/>
```

### FilterPanel
Advanced filtering interface.

```tsx
import { FilterPanel, ActiveFilters } from '@/components';

<FilterPanel
  filters={[
    {
      key: 'role',
      label: 'Role',
      type: 'select',
      options: roleOptions,
      value: selectedRole,
    },
  ]}
  onFilterChange={updateFilter}
  onClearAll={clearFilters}
  activeFiltersCount={3}
  collapsible
/>

<ActiveFilters
  filters={activeFilters}
  onRemove={removeFilter}
/>
```

---

## Layout Components

Located in `/components/layout/`

### Container
Page container with max width.

**Max Widths:** `sm`, `md`, `lg`, `xl`, `2xl`, `full`

```tsx
import { Container, Section, PageHeader } from '@/components';

<Container maxWidth="lg" padding center>
  <PageHeader
    title="Schedule Management"
    description="Manage resident schedules and assignments"
    actions={<Button>Generate Schedule</Button>}
  />
  <Section spacing="md">
    {/* Content */}
  </Section>
</Container>
```

### Grid
Responsive grid layouts.

**Columns:** 1, 2, 3, 4, 6, 12
**Gap:** `none`, `xs`, `sm`, `md`, `lg`, `xl`

```tsx
import { Grid, GridItem, AutoGrid } from '@/components';

<Grid columns={3} gap="md" responsive>
  <div>Item 1</div>
  <GridItem colSpan={2}>Item 2 (spans 2 columns)</GridItem>
</Grid>

<AutoGrid minWidth={250} gap="md">
  {items.map(item => <Card>{item}</Card>)}
</AutoGrid>
```

### Stack
Flexbox layouts.

**Direction:** `row`, `column`
**Spacing:** `none`, `xs`, `sm`, `md`, `lg`, `xl`

```tsx
import { Stack, HStack, VStack, Spacer, Divider } from '@/components';

<Stack direction="column" spacing="md" align="center">
  <div>Item 1</div>
  <div>Item 2</div>
</Stack>

<HStack spacing="sm" justify="between">
  <div>Left</div>
  <Spacer />
  <div>Right</div>
</HStack>

<VStack spacing="lg">
  <div>Top</div>
  <Divider />
  <div>Bottom</div>
</VStack>
```

### Sidebar
Side navigation and content panels.

**Positions:** `left`, `right`
**Widths:** `sm`, `md`, `lg`

```tsx
import { Sidebar, SidebarItem, SidebarSection } from '@/components';

<Sidebar position="left" collapsible width="md">
  <SidebarSection title="Navigation">
    <SidebarItem
      icon={<HomeIcon />}
      label="Dashboard"
      active
      badge={5}
    />
    <SidebarItem
      icon={<CalendarIcon />}
      label="Schedule"
    />
  </SidebarSection>
</Sidebar>
```

---

## Usage Examples

### Complete Form Example

```tsx
import {
  Container,
  PageHeader,
  Card,
  VStack,
  Input,
  MultiSelect,
  DateRangePicker,
  Button,
  Alert,
} from '@/components';

function CreateAssignment() {
  return (
    <Container maxWidth="lg">
      <PageHeader title="Create Assignment" />

      <Card>
        <VStack spacing="lg">
          <Alert variant="info">
            Fill out the form to create a new assignment.
          </Alert>

          <Input
            label="Resident Name"
            placeholder="Select resident..."
            required
          />

          <MultiSelect
            label="Rotations"
            options={rotationOptions}
            value={selected}
            onChange={setSelected}
            searchable
          />

          <DateRangePicker
            label="Assignment Period"
            value={dateRange}
            onChange={setDateRange}
          />

          <HStack justify="end" spacing="sm">
            <Button variant="outline">Cancel</Button>
            <Button variant="primary">Create Assignment</Button>
          </HStack>
        </VStack>
      </Card>
    </Container>
  );
}
```

### Dashboard Example

```tsx
import {
  Container,
  PageHeader,
  Grid,
  StatCard,
  Card,
  DataTable,
  ComplianceIndicator,
} from '@/components';

function Dashboard() {
  return (
    <Container maxWidth="2xl">
      <PageHeader
        title="Dashboard"
        description="Overview of residency program"
      />

      <StatGrid
        columns={4}
        stats={[
          {
            label: 'Total Residents',
            value: 24,
            trend: 'up',
            change: 12,
            icon: <UserIcon />,
          },
          // ... more stats
        ]}
      />

      <Grid columns={2} gap="md" className="mt-6">
        <Card>
          <CardHeader>
            <CardTitle>Recent Assignments</CardTitle>
          </CardHeader>
          <CardContent>
            <DataTable data={assignments} columns={columns} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Compliance Status</CardTitle>
          </CardHeader>
          <CardContent>
            <ComplianceSummary items={complianceItems} />
          </CardContent>
        </Card>
      </Grid>
    </Container>
  );
}
```

---

## Component Count Summary

### Total Components: 60+

**UI Primitives (9):**
- Button, IconButton
- Badge, NumericBadge
- Avatar, AvatarGroup
- Dropdown, SelectDropdown
- Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter
- Input
- Alert
- Tooltip
- Tabs

**Scheduling (13):**
- TimeSlot, TimeSlotGrid
- ResidentCard, ResidentListItem
- RotationBadge, RotationLegend
- ComplianceIndicator, ComplianceCard, ComplianceSummary
- CoverageMatrix, CoverageSummary
- BlockTimeline, MultiPersonTimeline

**Data Display (8):**
- DataTable, CompactTable
- StatCard, CompactStat, StatGrid
- ChartWrapper
- Pagination, SimplePagination

**Forms (8):**
- DateRangePicker, DateRangePresets
- MultiSelect
- SearchInput, SearchWithSuggestions
- FilterPanel, ActiveFilters

**Layout (17):**
- Container, Section, PageHeader
- Grid, GridItem, AutoGrid
- Stack, HStack, VStack, Spacer, Divider
- Sidebar, SidebarItem, SidebarSection

**Loading States (13):**
- Spinner, ButtonSpinner, PageSpinner
- SkeletonText, SkeletonAvatar, SkeletonButton, SkeletonCard
- ProgressBar, ProgressCircle
- PageLoader, CardLoader, TableLoader, InlineLoader

---

## Best Practices

### TypeScript
All components are fully typed with TypeScript for type safety and autocomplete.

### Accessibility
Components include proper ARIA labels, keyboard navigation, and focus management.

### Responsive Design
Components use Tailwind's responsive classes and work on all screen sizes.

### Consistent Styling
All components follow the design system defined in `tailwind.config.ts`.

### Composition
Components are designed to be composed together for complex UIs.

---

## Import Patterns

```tsx
// Import individual components
import { Button, Card } from '@/components';

// Import from specific categories
import { DataTable } from '@/components/data-display';
import { ResidentCard } from '@/components/scheduling';

// Import everything (not recommended)
import * as Components from '@/components';
```

---

## Contributing

When adding new components:

1. Follow existing patterns and naming conventions
2. Add TypeScript types for all props
3. Include JSDoc comments with examples
4. Export from category index file
5. Update this documentation
6. Consider accessibility requirements
7. Test responsive behavior

---

**Last Updated:** 2025-12-31
**Version:** 1.0.0
