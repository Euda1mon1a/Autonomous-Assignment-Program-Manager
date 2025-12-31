# Performance Optimization Quick Reference

**Session 23 - Performance Optimization Implementation**

## Quick File Index

### Backend Optimization

#### Database Layer (`/backend/app/db/`)
- `query_cache.py` - Redis-based query caching
- `connection_pool.py` - Optimized connection pooling
- `batch_operations.py` - Bulk database operations
- `explain_analyzer.py` - SQL query analysis
- `materialized_views.py` - Materialized view management

#### Caching Layer (`/backend/app/cache/`)
- `cache_manager.py` - Unified cache interface
- `schedule_cache.py` - Schedule-specific caching
- `compliance_cache.py` - ACGME compliance caching
- `person_cache.py` - Person data caching
- `distributed_lock.py` - Distributed locking
- `compression.py` - Cache value compression

#### Async Utilities (`/backend/app/async_utils/`)
- `task_queue.py` - Priority task queue
- `parallel_executor.py` - Parallel async execution
- `semaphore_pool.py` - Resource pooling & rate limiting
- `batch_processor.py` - Batch data processing

#### Schedule Optimizer (`/backend/app/scheduling/optimizer/`)
- `constraint_pruning.py` - Early constraint pruning
- `solution_cache.py` - Solution caching
- `parallel_solver.py` - Parallel solver execution
- `incremental_update.py` - Incremental updates

### Frontend Optimization

#### Utils (`/frontend/src/utils/`)
- `virtual-scroll.ts` - Virtual scrolling for large lists
- `lazy-loader.ts` - Component lazy loading
- `memoization.ts` - Function memoization
- `debounce.ts` - Debounce/throttle utilities

#### Hooks (`/frontend/src/hooks/`)
- `useInfiniteQuery.ts` - Infinite scroll hook
- `useOptimisticUpdate.ts` - Optimistic UI updates

### Tests (`/backend/tests/`)
- `test_query_cache.py` - Query cache tests
- `test_batch_operations.py` - Batch operation tests
- `test_async_utils.py` - Async utility tests
- `test_schedule_optimizer.py` - Optimizer tests

## Common Usage Patterns

### 1. Cache a Database Query

```python
from app.db.query_cache import get_query_cache

cache = get_query_cache()

# Cache a query result
result = await cache.get_or_fetch(
    key="schedule:2024-01-01",
    fetch_fn=lambda: fetch_schedule_from_db(date),
    ttl=timedelta(hours=1)
)

# Invalidate cache
await cache.invalidate("schedule:*")
```

### 2. Bulk Insert Records

```python
from app.db.batch_operations import BatchOperations

batch_ops = BatchOperations(db, batch_size=1000)

# Bulk insert
records = [{"id": "1", "name": "Test"}, ...]
await batch_ops.bulk_insert(MyModel, records)

# Bulk upsert
await batch_ops.bulk_upsert(
    MyModel,
    records,
    conflict_columns=["id"],
    update_columns=["name", "updated_at"]
)
```

### 3. Parallel Execution

```python
from app.async_utils.parallel_executor import ParallelExecutor

executor = ParallelExecutor(max_concurrent=10)

# Map function over items in parallel
results = await executor.map(
    async_function,
    items
)

# Run coroutines in parallel
result1, result2 = await executor.run_parallel(
    coroutine1(),
    coroutine2()
)
```

### 4. Rate Limiting

```python
from app.async_utils.semaphore_pool import RateLimiter

limiter = RateLimiter(rate=10, per=1.0)  # 10 per second

# Use rate limiter
async with limiter:
    await api_call()
```

### 5. Virtual Scrolling (Frontend)

```typescript
import { useVirtualScroll } from '@/utils/virtual-scroll';

function MyList({ items }) {
  const { visibleItems, handleScroll, totalHeight, offsetTop } =
    useVirtualScroll(items, {
      itemHeight: 50,
      viewportHeight: 600,
      overscan: 5,
    });

  return (
    <div onScroll={handleScroll} style={{ height: 600, overflow: 'auto' }}>
      <div style={{ height: totalHeight }}>
        <div style={{ transform: `translateY(${offsetTop}px)` }}>
          {visibleItems.map(({ index, item }) => (
            <div key={index} style={{ height: 50 }}>
              {item.name}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
```

### 6. Debounced Search (Frontend)

```typescript
import { useDebouncedCallback } from '@/utils/debounce';

function SearchInput() {
  const debouncedSearch = useDebouncedCallback(
    async (query: string) => {
      const results = await api.search(query);
      setResults(results);
    },
    300
  );

  return (
    <input
      onChange={(e) => debouncedSearch(e.target.value)}
      placeholder="Search..."
    />
  );
}
```

### 7. Optimistic Updates (Frontend)

```typescript
import { useOptimisticUpdate } from '@/hooks/useOptimisticUpdate';

function UpdateSchedule() {
  const mutation = useOptimisticUpdate({
    queryKey: ['schedule', scheduleId],
    mutationFn: updateSchedule,
    optimisticUpdate: (old, variables) => ({
      ...old,
      ...variables,
    }),
  });

  return (
    <button onClick={() => mutation.mutate({ name: 'New Name' })}>
      Update
    </button>
  );
}
```

## Performance Monitoring

### Backend Metrics

```python
# Query cache stats
cache = get_query_cache()
stats = await cache.get_metrics()
# Returns: { hits, misses, hit_rate, total_queries }

# Connection pool stats
pool = get_connection_pool()
metrics = await pool.get_metrics()
# Returns: { active, idle, utilization, avg_checkout_time }

# Task queue stats
queue = get_task_queue()
stats = await queue.get_stats()
# Returns: { completed, failed, active_tasks, success_rate }
```

### Frontend Metrics

```typescript
// Virtual scroll metrics
const metrics = new VirtualScrollMetrics();
metrics.recordRender(itemCount);
const stats = metrics.getStats();
// Returns: { averageRenderedItems, totalMeasurements }

// Debounce metrics
const monitor = new DebounceMonitor();
const stats = monitor.getStats();
// Returns: { totalCalls, executedCalls, reductionRate }
```

## Configuration

### Environment Variables

```bash
# Redis cache
REDIS_URL=redis://localhost:6379/0

# Database pool
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
DB_ECHO=false

# Cache settings
CACHE_DEFAULT_TTL=900  # 15 minutes
CACHE_MAX_CONNECTIONS=50
```

### Tuning Parameters

#### Query Cache
- `default_ttl`: 900 seconds (15 min)
- Adjust based on data update frequency

#### Connection Pool
- `pool_size`: 20
- `max_overflow`: 10
- Increase for high-concurrency workloads

#### Batch Operations
- `batch_size`: 1000
- Decrease for memory-constrained environments

#### Parallel Executor
- `max_concurrent`: 10
- Set to number of CPU cores × 2

## Troubleshooting

### High Memory Usage
1. Reduce cache TTL
2. Implement LRU eviction
3. Reduce batch sizes
4. Check for memory leaks in cache

### Slow Queries
1. Check `explain_analyzer` output
2. Add recommended indexes
3. Use materialized views
4. Increase cache hit rate

### Cache Misses
1. Review cache key generation
2. Increase TTL if appropriate
3. Implement cache warming
4. Check invalidation patterns

### Connection Pool Exhaustion
1. Increase `pool_size`
2. Increase `max_overflow`
3. Reduce connection hold time
4. Check for connection leaks

## Best Practices

### DO
✅ Cache expensive queries
✅ Use bulk operations for large datasets
✅ Implement proper error handling
✅ Monitor performance metrics
✅ Test with realistic data volumes
✅ Invalidate cache on data changes
✅ Use virtual scrolling for lists > 100 items
✅ Debounce user input handlers

### DON'T
❌ Cache rapidly changing data
❌ Use synchronous operations in async code
❌ Ignore cache invalidation
❌ Skip performance testing
❌ Over-optimize prematurely
❌ Cache without TTL
❌ Render large lists without virtualization
❌ Skip error boundaries in lazy loading

## Testing

### Run Performance Tests

```bash
# All optimization tests
cd backend
pytest tests/test_query_cache.py -v
pytest tests/test_batch_operations.py -v
pytest tests/test_async_utils.py -v
pytest tests/test_schedule_optimizer.py -v

# With coverage
pytest --cov=app.db --cov=app.cache --cov=app.async_utils

# Performance benchmarks
pytest -m performance
```

### Load Testing

```bash
# Use k6 or locust for load testing
k6 run scenarios/optimized-queries.js
```

## Migration Guide

### Adopting Query Cache

1. Identify slow queries using `explain_analyzer`
2. Add caching wrapper to query functions
3. Implement invalidation on data changes
4. Monitor hit rates
5. Tune TTL based on metrics

### Implementing Virtual Scrolling

1. Identify large lists (> 100 items)
2. Replace with virtual scroll component
3. Measure rendering performance
4. Adjust overscan and item height
5. Test scroll smoothness

## Related Documentation

- [PERFORMANCE_OPTIMIZATION_SUMMARY.md](../PERFORMANCE_OPTIMIZATION_SUMMARY.md) - Full implementation details
- [CLAUDE.md](../CLAUDE.md) - Project guidelines
- [API Documentation](api/) - API reference

## Support

For issues or questions:
1. Check this quick reference
2. Review comprehensive summary
3. Check test files for usage examples
4. Consult module docstrings

---

**Last Updated:** 2025-12-31
**Session:** 23 - Performance Optimization
**Files Created:** 23 implementation + 4 test files
