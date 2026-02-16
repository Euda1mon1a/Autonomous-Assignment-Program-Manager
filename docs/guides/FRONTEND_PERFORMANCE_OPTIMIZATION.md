# Frontend Performance Optimization Roadmap

**Created:** 2025-12-31
**Source:** SESSION_2_FRONTEND Performance Audit
**Status:** Action Plan with Metrics
**Target:** 20-30% bundle reduction + improved Core Web Vitals

---

## Executive Summary

**Current State:**
- Bundle size: ~4.8 MB uncompressed (1.2 MB gzipped estimated)
- Time to Interactive (TTI): 3.5-4.5s (⚠️ Should be <3.5s)
- Largest Contentful Paint (LCP): 2.0-3.0s (Marginal, <2.5s target)
- Code splitting: Minimal (only Plotly dynamic import)
- Memoization: 1 component using React.memo (need 50+)

**Priority Actions:**
1. Lazy-load Plotly & Recharts (40% of overhead)
2. Add component memoization (high re-renders)
3. Split schedule views (unused code loaded)
4. Optimize query cache timing

---

## Section 1: Top 5 Performance Bottlenecks

### Bottleneck #1: Plotly Bundle (3.5 MB uncompressed)

**Impact:** 700 KB gzipped - 58% of charting overhead

**Current Loading:**
```typescript
// src/features/heatmap/HeatmapView.tsx
const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });
// ✓ Already using dynamic import
```

**Issue:** Confirm it's truly lazy-loaded:
```bash
# Check if Plotly is in main bundle
npm run build
# Look for heatmap chunk separately from main chunk
```

**Optimization:** (Already partially done, verify full implementation)
```typescript
// Ensure no eager imports
// ✗ WRONG - bundles immediately
import Plot from 'react-plotly.js';

// ✓ CORRECT - only loaded when needed
const Plot = dynamic(() => import('react-plotly.js'), {
  ssr: false,
  loading: () => <div className="h-96 bg-gray-100 animate-pulse" />,
});
```

**Expected Impact:** 58% → 0% in main bundle (heatmap loads separately)

---

### Bottleneck #2: Recharts Bundle (800 KB uncompressed)

**Impact:** 160 KB gzipped - used in 14 files

**Current Loading:** ✗ Always bundled

```typescript
// Used in:
// - ScheduleSummary.tsx
// - HealthStatus.tsx
// - CoverageTrendChart.tsx
// - AlgorithmComparisonChart.tsx
// - AnalyticsDashboard.tsx
// - +9 other files
```

**Optimization:**

```typescript
// Option 1: Lazy-load at route level
// frontend/src/app/dashboard/page.tsx
'use client';

import dynamic from 'next/dynamic';

const DashboardContent = dynamic(
  () => import('@/components/dashboard/DashboardContent'),
  {
    ssr: false,
    loading: () => <DashboardSkeleton />,
  }
);

// Option 2: Lazy-load per component
// frontend/src/components/ScheduleSummary.tsx
import dynamic from 'next/dynamic';

const Chart = dynamic(() => import('recharts').then(mod => mod.AreaChart), {
  loading: () => <div className="h-32 bg-gray-100" />,
  ssr: false,
});

// Keep recharts import minimal for non-chart parts
```

**Expected Impact:** 160 KB → 0 KB in main bundle (charts load on dashboard visit)

---

### Bottleneck #3: Schedule View Components (150 KB uncompressed)

**Impact:** 30-40 KB gzipped - all views loaded even if one active

**Current Loading:** All 4 views imported eagerly

```typescript
// frontend/src/app/schedule/page.tsx
import ScheduleGrid from './ScheduleGrid';
import MonthView from './MonthView';
import WeekView from './WeekView';
import DayView from './DayView';

// All loaded even though user sees only ONE view
```

**Optimization:**

```typescript
// Lazy-load views by type
const ScheduleGrid = dynamic(() => import('./ScheduleGrid'), { ssr: false });
const MonthView = dynamic(() => import('./MonthView'), { ssr: false });
const WeekView = dynamic(() => import('./WeekView'), { ssr: false });
const DayView = dynamic(() => import('./DayView'), { ssr: false });

// Render with Suspense
return (
  <Suspense fallback={<ScheduleSkeleton />}>
    {currentView === 'block' && <ScheduleGrid ... />}
    {currentView === 'month' && <MonthView ... />}
    {currentView === 'week' && <WeekView ... />}
    {currentView === 'day' && <DayView ... />}
  </Suspense>
);
```

**Expected Impact:** 30-40 KB → Loaded only when selected view active

---

### Bottleneck #4: Large Component Files (650+ lines)

**Impact:** Slower parsing, worse caching

**Files Affected:**
- FacultyInpatientWeeksView.tsx (650 lines)
- ResidentAcademicYearView.tsx (640 lines)
- ConfigurationPresets.tsx (495 lines)
- LoadingStates.tsx (495 lines)

**Optimization:**

```typescript
// BEFORE: Single 650-line file
// FacultyInpatientWeeksView.tsx

// AFTER: Split into modules
FacultyInpatientWeeksView/
├── FacultyInpatientWeeksView.tsx      (150 lines - container)
├── WeekGrid.tsx                       (200 lines - layout)
├── FacultyRow.tsx                     (100 lines - component)
├── hooks.ts                           (80 lines - state management)
├── utils.ts                           (50 lines - helpers)
└── index.ts
```

**Expected Impact:** Faster builds, better incremental caching, smaller chunks

---

### Bottleneck #5: No Memoization (Only 1 memoized component)

**Impact:** Unnecessary re-renders on parent updates

**High-Rerender Components:**
- ConflictCard (rendered 100+ times per list)
- SwapRequestCard (rendered in marketplace)
- AssignmentCard (rendered in schedule)
- PersonRow (rendered in tables)

**Optimization:**

```typescript
// BEFORE: No memoization
export function ConflictCard({ conflict, onSelect }) {
  return (
    <div onClick={() => onSelect(conflict)}>
      {conflict.title}  {/* Re-renders even if unchanged */}
    </div>
  );
}

// AFTER: Memoized with memo()
import { memo } from 'react';

export const ConflictCard = memo(function ConflictCard({
  conflict,
  onSelect,
}: ConflictCardProps) {
  return (
    <div onClick={() => onSelect(conflict)}>
      {conflict.title}
    </div>
  );
});
```

**Expected Impact:** 50-100 ms faster list re-renders

---

## Section 2: Implementation Plan (Phased)

### Phase 1: Immediate (This Week) - 2-3 Hours

**Priority 1.1: Add Bundle Analyzer**

```bash
npm install --save-dev @next/bundle-analyzer
```

**next.config.js:**
```javascript
const withBundleAnalyzer = require('@next/bundle-analyzer')({
  enabled: process.env.ANALYZE === 'true',
});

module.exports = withBundleAnalyzer(nextConfig);
```

**Run analysis:**
```bash
ANALYZE=true npm run build
# Generates .next/analyze/ with bundle visualization
```

**Priority 1.2: Verify Plotly Lazy Loading**

```bash
# Ensure plotly is separate chunk
npm run build

# Check chunk sizes
# main.js should NOT include plotly code
# heatmap.js (or _next/chunks/something.js) should include plotly

# Expected split:
# main.js: 300-400 KB
# heatmap.js: 850 KB (plotly)
```

**Priority 1.3: Set Request Timeouts**

```typescript
// frontend/src/lib/api.ts
const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  timeout: 5000,  // 5 second timeout
});

// Implement exponential backoff
const retryInstance = axiosRetry(api, {
  retries: 3,
  retryDelay: axiosRetry.exponentialDelay,
  retryCondition: (error) => {
    return (
      axiosRetry.isNetworkOrIdempotentRequestError(error) &&
      error.response?.status !== 401  // Don't retry auth errors
    );
  },
});
```

---

### Phase 2: Short Term (Next 2 Weeks) - 5-7 Hours

**Priority 2.1: Lazy-Load Recharts**

```typescript
// Create lazy chart wrapper
// frontend/src/components/charts/LazyLineChart.tsx

import dynamic from 'next/dynamic';
import { Suspense } from 'react';

const RechartLineChart = dynamic(() =>
  import('recharts').then(mod => ({
    default: function Chart(props) {
      const { LineChart, XAxis, YAxis, CartesianGrid, Tooltip, Legend, Line } = mod;
      return (
        <LineChart {...props}>
          <CartesianGrid />
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="value" stroke="#8884d8" />
        </LineChart>
      );
    }
  }),
  { ssr: false }
);

export function LazyLineChart(props) {
  return (
    <Suspense fallback={<div className="h-64 bg-gray-100 animate-pulse" />}>
      <RechartLineChart {...props} />
    </Suspense>
  );
}
```

**Priority 2.2: Split Schedule Views**

```typescript
// frontend/src/app/schedule/page.tsx
import dynamic from 'next/dynamic';
import { Suspense } from 'react';

const ScheduleGrid = dynamic(() => import('./ScheduleGrid'), { ssr: false });
const MonthView = dynamic(() => import('./MonthView'), { ssr: false });
const WeekView = dynamic(() => import('./WeekView'), { ssr: false });
const DayView = dynamic(() => import('./DayView'), { ssr: false });

export default function SchedulePage() {
  const [currentView, setCurrentView] = useState<ViewType>('month');

  return (
    <div>
      <ViewToggle value={currentView} onChange={setCurrentView} />

      <Suspense fallback={<ScheduleSkeleton />}>
        {currentView === 'block' && <ScheduleGrid {...props} />}
        {currentView === 'month' && <MonthView {...props} />}
        {currentView === 'week' && <WeekView {...props} />}
        {currentView === 'day' && <DayView {...props} />}
      </Suspense>
    </div>
  );
}
```

**Priority 2.3: Add Component Memoization (Top 10)**

```typescript
// Memoize repeated list components
export const ConflictCard = memo(ConflictCardContent);
export const SwapRequestCard = memo(SwapRequestCardContent);
export const AssignmentCard = memo(AssignmentCardContent);
export const PersonRow = memo(PersonRowContent);
export const ScheduleCell = memo(ScheduleCellContent);

// Add useCallback to handlers
const handleSelect = useCallback((item) => {
  setSelected(item);
}, []);

// Use useMemo for derived data
const filteredItems = useMemo(
  () => items.filter(item => matches(item, filters)),
  [items, filters]
);
```

---

### Phase 3: Medium Term (Next Month) - 8-10 Hours

**Priority 3.1: Decompose Large Components**

```typescript
// BEFORE: FacultyInpatientWeeksView.tsx (650 lines)
// AFTER: Split into 5 focused files

// FacultyInpatientWeeksView.tsx (container, 150 lines)
// WeekGrid.tsx (layout, 200 lines)
// FacultyRow.tsx (row component, 100 lines)
// TimeSlot.tsx (cell component, 80 lines)
// hooks.ts (state management, 80 lines)
```

**Priority 3.2: Optimize Framer Motion Usage**

```typescript
// Replace simple Framer Motion with CSS
// BEFORE: Heavy Framer Motion import for opacity change
import { motion } from 'framer-motion';

<motion.div
  initial={{ opacity: 0 }}
  animate={{ opacity: 1 }}
  transition={{ duration: 0.3 }}
>
  {content}
</motion.div>

// AFTER: CSS transition (native, 0 KB bundle impact)
<div className="opacity-0 animate-fade-in">
  {content}
</div>

// Tailwind CSS
@layer components {
  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }

  .animate-fade-in {
    animation: fadeIn 0.3s ease-in;
  }
}
```

**Priority 3.3: Implement Web Vitals Monitoring**

```typescript
// frontend/src/lib/web-vitals.ts
import { getCLS, getFID, getFCP, getLCP, getTTFB } from 'web-vitals';

export function initWebVitals() {
  getCLS(metric => {
    console.log('CLS:', metric.value);
    // Send to analytics
  });

  getFID(metric => {
    console.log('FID:', metric.value);
  });

  getFCP(metric => {
    console.log('FCP:', metric.value);
  });

  getLCP(metric => {
    console.log('LCP:', metric.value);
  });

  getTTFB(metric => {
    console.log('TTFB:', metric.value);
  });
}

// Usage in root layout
export default function RootLayout({ children }) {
  useEffect(() => {
    initWebVitals();
  }, []);

  return <>{children}</>;
}
```

---

## Section 3: Memoization Strategy

### Which Components to Memoize?

**Memoize if:**
- ✓ Rendered in a list (100+ instances)
- ✓ Has expensive computations
- ✓ Parent re-renders frequently
- ✓ Pure component (same props = same output)

**Don't memoize if:**
- ✗ Page-level component
- ✗ Always has different props
- ✗ Simple presentational component

### Memoization Template

```typescript
import { memo, useMemo, useCallback } from 'react';

interface CardProps {
  item: Item;
  onSelect: (item: Item) => void;
  isSelected: boolean;
}

/**
 * Card component for rendering list items.
 * Memoized to prevent unnecessary re-renders when parent updates.
 */
export const Card = memo(function Card({
  item,
  onSelect,
  isSelected,
}: CardProps) {
  // Don't create new styles on every render
  const cardClass = useMemo(
    () => isSelected ? 'ring-2 ring-blue-500' : 'border border-gray-200',
    [isSelected]
  );

  // Don't create new function on every render
  const handleClick = useCallback(() => {
    onSelect(item);
  }, [item, onSelect]);

  return (
    <div
      onClick={handleClick}
      className={cardClass}
    >
      {item.title}
    </div>
  );
});

// IMPORTANT: Set display name for React DevTools
Card.displayName = 'Card';
```

### List Optimization Pattern

```typescript
import { memo, useMemo, useCallback } from 'react';
import { VirtualizedList } from 'react-window';

interface ListProps {
  items: Item[];
  onSelect: (item: Item) => void;
  selectedId: string | null;
}

/**
 * Virtualized list with memoized items.
 * Only renders visible items for performance.
 */
export function List({ items, onSelect, selectedId }: ListProps) {
  // Memoize handler to prevent child re-renders
  const handleSelect = useCallback((item: Item) => {
    onSelect(item);
  }, [onSelect]);

  const Row = useCallback(({ index, style }) => {
    const item = items[index];
    return (
      <div style={style}>
        <MemoizedCard
          item={item}
          onSelect={handleSelect}
          isSelected={item.id === selectedId}
        />
      </div>
    );
  }, [items, handleSelect, selectedId]);

  return (
    <VirtualizedList
      height={600}
      itemCount={items.length}
      itemSize={100}
      width="100%"
    >
      {Row}
    </VirtualizedList>
  );
}
```

---

## Section 4: Bundle Size Monitoring

### Configuration

```bash
# Install bundle analyzer
npm install --save-dev @next/bundle-analyzer
```

**next.config.js:**
```javascript
const withBundleAnalyzer = require('@next/bundle-analyzer')({
  enabled: process.env.ANALYZE === 'true',
});

module.exports = withBundleAnalyzer({
  // ... other config
  webpack: (config, context) => {
    // Track bundle size
    config.plugins.push(
      new (require('webpack-bundle-analyzer')).BundleAnalyzerPlugin({
        analyzerMode: 'disabled',
        generateStatsFile: true,
        statsFilename: 'build-stats.json',
      })
    );
    return config;
  },
});
```

### Monitor Bundle Growth

```bash
# Generate stats before and after changes
npm run build -- --stats
# Creates .next/build-stats.json

# Analyze with bundle-analyzer
ANALYZE=true npm run build
# Opens interactive visualization
```

### GitHub Actions Workflow

```yaml
name: Bundle Size Check

on: [pull_request]

jobs:
  bundle-size:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node
        uses: actions/setup-node@v3
        with:
          node-version: 18

      - name: Install dependencies
        run: npm ci

      - name: Build
        run: npm run build

      - name: Analyze bundle
        run: npm run build:analyze

      - name: Check bundle size
        run: |
          SIZE=$(stat -f%z .next/static/chunks/main-*.js)
          if [ $SIZE -gt 500000 ]; then
            echo "❌ Bundle size too large: $SIZE bytes"
            exit 1
          fi
          echo "✓ Bundle size OK: $SIZE bytes"
```

---

## Section 5: Performance Metrics & Targets

### Current vs Target

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| **FCP** | 1.5-2.0s | <1.8s | ⚠️ Marginal |
| **LCP** | 2.0-3.0s | <2.5s | ⚠️ Marginal |
| **TTI** | 3.5-4.5s | <3.5s | ✗ FAIL |
| **CLS** | <0.1 | <0.1 | ✓ PASS |
| **JS Parse** | 1.0-1.5s | <0.8s | ⚠️ High |
| **Bundle** | 4.8 MB (1.2 MB gz) | 3.0 MB (800 KB gz) | 🎯 -37% |

### Monitoring with Lighthouse

```bash
# Install Lighthouse
npm install -g lighthouse

# Run audit
lighthouse http://localhost:3000 --view --output=html

# CI integration
npm run test:lighthouse -- http://localhost:3000
```

### Real User Monitoring (RUM)

```typescript
// Use web-vitals library
import { getCLS, getFID, getFCP, getLCP, getTTFB } from 'web-vitals';

function sendMetric(metric) {
  // Send to analytics service
  fetch('/api/metrics', {
    method: 'POST',
    body: JSON.stringify({
      name: metric.name,
      value: metric.value,
      rating: metric.rating,
      timestamp: new Date().toISOString(),
    }),
  });
}

getCLS(sendMetric);
getFID(sendMetric);
getFCP(sendMetric);
getLCP(sendMetric);
getTTFB(sendMetric);
```

---

## Success Criteria

```checklist
[ ] Bundle size ≤ 800 KB gzipped
[ ] Time to Interactive < 3.5 seconds
[ ] Largest Contentful Paint < 2.5 seconds
[ ] First Contentful Paint < 1.8 seconds
[ ] No layout shift (CLS < 0.1)
[ ] 50+ components using React.memo
[ ] All list items virtualized (if 50+ items)
[ ] Zero N+1 query issues
[ ] Recharts lazy-loaded
[ ] All views code-split
```

---

**Document Version:** 1.0
**Last Updated:** 2025-12-31
**Review Cycle:** Monthly
**Target Completion:** Q1 2026
