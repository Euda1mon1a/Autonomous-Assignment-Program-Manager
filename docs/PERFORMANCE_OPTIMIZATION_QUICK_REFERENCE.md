***REMOVED*** Performance Optimization Quick Reference

**Session 23 - Performance Optimization Implementation**

***REMOVED******REMOVED*** Quick File Index

***REMOVED******REMOVED******REMOVED*** Backend Optimization

***REMOVED******REMOVED******REMOVED******REMOVED*** Database Layer (`/backend/app/db/`)
- `query_cache.py` - Redis-based query caching
- `connection_pool.py` - Optimized connection pooling
- `batch_operations.py` - Bulk database operations
- `explain_analyzer.py` - SQL query analysis
- `materialized_views.py` - Materialized view management

***REMOVED******REMOVED******REMOVED******REMOVED*** Caching Layer (`/backend/app/cache/`)
- `cache_manager.py` - Unified cache interface
- `schedule_cache.py` - Schedule-specific caching
- `compliance_cache.py` - ACGME compliance caching
- `person_cache.py` - Person data caching
- `distributed_lock.py` - Distributed locking
- `compression.py` - Cache value compression

***REMOVED******REMOVED******REMOVED******REMOVED*** Async Utilities (`/backend/app/async_utils/`)
- `task_queue.py` - Priority task queue
- `parallel_executor.py` - Parallel async execution
- `semaphore_pool.py` - Resource pooling & rate limiting
- `batch_processor.py` - Batch data processing

***REMOVED******REMOVED******REMOVED******REMOVED*** Schedule Optimizer (`/backend/app/scheduling/optimizer/`)
- `constraint_pruning.py` - Early constraint pruning
- `solution_cache.py` - Solution caching
- `parallel_solver.py` - Parallel solver execution
- `incremental_update.py` - Incremental updates

***REMOVED******REMOVED******REMOVED*** Frontend Optimization

***REMOVED******REMOVED******REMOVED******REMOVED*** Utils (`/frontend/src/utils/`)
- `virtual-scroll.ts` - Virtual scrolling for large lists
- `lazy-loader.ts` - Component lazy loading
- `memoization.ts` - Function memoization
- `debounce.ts` - Debounce/throttle utilities

***REMOVED******REMOVED******REMOVED******REMOVED*** Hooks (`/frontend/src/hooks/`)
- `useInfiniteQuery.ts` - Infinite scroll hook
- `useOptimisticUpdate.ts` - Optimistic UI updates

***REMOVED******REMOVED******REMOVED*** Tests (`/backend/tests/`)
- `test_query_cache.py` - Query cache tests
- `test_batch_operations.py` - Batch operation tests
- `test_async_utils.py` - Async utility tests
- `test_schedule_optimizer.py` - Optimizer tests

***REMOVED******REMOVED*** Common Usage Patterns

***REMOVED******REMOVED******REMOVED*** 1. Cache a Database Query

```python
from app.db.query_cache import get_query_cache

cache = get_query_cache()

***REMOVED*** Cache a query result
result = await cache.get_or_fetch(
    key="schedule:2024-01-01",
    fetch_fn=lambda: fetch_schedule_from_db(date),
    ttl=timedelta(hours=1)
)

***REMOVED*** Invalidate cache
await cache.invalidate("schedule:*")
```

***REMOVED******REMOVED******REMOVED*** 2. Bulk Insert Records

```python
from app.db.batch_operations import BatchOperations

batch_ops = BatchOperations(db, batch_size=1000)

***REMOVED*** Bulk insert
records = [{"id": "1", "name": "Test"}, ...]
await batch_ops.bulk_insert(MyModel, records)

***REMOVED*** Bulk upsert
await batch_ops.bulk_upsert(
    MyModel,
    records,
    conflict_columns=["id"],
    update_columns=["name", "updated_at"]
)
```

***REMOVED******REMOVED******REMOVED*** 3. Parallel Execution

```python
from app.async_utils.parallel_executor import ParallelExecutor

executor = ParallelExecutor(max_concurrent=10)

***REMOVED*** Map function over items in parallel
results = await executor.map(
    async_function,
    items
)

***REMOVED*** Run coroutines in parallel
result1, result2 = await executor.run_parallel(
    coroutine1(),
    coroutine2()
)
```

***REMOVED******REMOVED******REMOVED*** 4. Rate Limiting

```python
from app.async_utils.semaphore_pool import RateLimiter

limiter = RateLimiter(rate=10, per=1.0)  ***REMOVED*** 10 per second

***REMOVED*** Use rate limiter
async with limiter:
    await api_call()
```

***REMOVED******REMOVED******REMOVED*** 5. Virtual Scrolling (Frontend)

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

***REMOVED******REMOVED******REMOVED*** 6. Debounced Search (Frontend)

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

***REMOVED******REMOVED******REMOVED*** 7. Optimistic Updates (Frontend)

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

***REMOVED******REMOVED*** Performance Monitoring

***REMOVED******REMOVED******REMOVED*** Backend Metrics

```python
***REMOVED*** Query cache stats
cache = get_query_cache()
stats = await cache.get_metrics()
***REMOVED*** Returns: { hits, misses, hit_rate, total_queries }

***REMOVED*** Connection pool stats
pool = get_connection_pool()
metrics = await pool.get_metrics()
***REMOVED*** Returns: { active, idle, utilization, avg_checkout_time }

***REMOVED*** Task queue stats
queue = get_task_queue()
stats = await queue.get_stats()
***REMOVED*** Returns: { completed, failed, active_tasks, success_rate }
```

***REMOVED******REMOVED******REMOVED*** Frontend Metrics

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

***REMOVED******REMOVED*** Configuration

***REMOVED******REMOVED******REMOVED*** Environment Variables

```bash
***REMOVED*** Redis cache
REDIS_URL=redis://localhost:6379/0

***REMOVED*** Database pool
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
DB_ECHO=false

***REMOVED*** Cache settings
CACHE_DEFAULT_TTL=900  ***REMOVED*** 15 minutes
CACHE_MAX_CONNECTIONS=50
```

***REMOVED******REMOVED******REMOVED*** Tuning Parameters

***REMOVED******REMOVED******REMOVED******REMOVED*** Query Cache
- `default_ttl`: 900 seconds (15 min)
- Adjust based on data update frequency

***REMOVED******REMOVED******REMOVED******REMOVED*** Connection Pool
- `pool_size`: 20
- `max_overflow`: 10
- Increase for high-concurrency workloads

***REMOVED******REMOVED******REMOVED******REMOVED*** Batch Operations
- `batch_size`: 1000
- Decrease for memory-constrained environments

***REMOVED******REMOVED******REMOVED******REMOVED*** Parallel Executor
- `max_concurrent`: 10
- Set to number of CPU cores × 2

***REMOVED******REMOVED*** Troubleshooting

***REMOVED******REMOVED******REMOVED*** High Memory Usage
1. Reduce cache TTL
2. Implement LRU eviction
3. Reduce batch sizes
4. Check for memory leaks in cache

***REMOVED******REMOVED******REMOVED*** Slow Queries
1. Check `explain_analyzer` output
2. Add recommended indexes
3. Use materialized views
4. Increase cache hit rate

***REMOVED******REMOVED******REMOVED*** Cache Misses
1. Review cache key generation
2. Increase TTL if appropriate
3. Implement cache warming
4. Check invalidation patterns

***REMOVED******REMOVED******REMOVED*** Connection Pool Exhaustion
1. Increase `pool_size`
2. Increase `max_overflow`
3. Reduce connection hold time
4. Check for connection leaks

***REMOVED******REMOVED*** Best Practices

***REMOVED******REMOVED******REMOVED*** DO
✅ Cache expensive queries
✅ Use bulk operations for large datasets
✅ Implement proper error handling
✅ Monitor performance metrics
✅ Test with realistic data volumes
✅ Invalidate cache on data changes
✅ Use virtual scrolling for lists > 100 items
✅ Debounce user input handlers

***REMOVED******REMOVED******REMOVED*** DON'T
❌ Cache rapidly changing data
❌ Use synchronous operations in async code
❌ Ignore cache invalidation
❌ Skip performance testing
❌ Over-optimize prematurely
❌ Cache without TTL
❌ Render large lists without virtualization
❌ Skip error boundaries in lazy loading

***REMOVED******REMOVED*** Testing

***REMOVED******REMOVED******REMOVED*** Run Performance Tests

```bash
***REMOVED*** All optimization tests
cd backend
pytest tests/test_query_cache.py -v
pytest tests/test_batch_operations.py -v
pytest tests/test_async_utils.py -v
pytest tests/test_schedule_optimizer.py -v

***REMOVED*** With coverage
pytest --cov=app.db --cov=app.cache --cov=app.async_utils

***REMOVED*** Performance benchmarks
pytest -m performance
```

***REMOVED******REMOVED******REMOVED*** Load Testing

```bash
***REMOVED*** Use k6 or locust for load testing
k6 run scenarios/optimized-queries.js
```

***REMOVED******REMOVED*** Migration Guide

***REMOVED******REMOVED******REMOVED*** Adopting Query Cache

1. Identify slow queries using `explain_analyzer`
2. Add caching wrapper to query functions
3. Implement invalidation on data changes
4. Monitor hit rates
5. Tune TTL based on metrics

***REMOVED******REMOVED******REMOVED*** Implementing Virtual Scrolling

1. Identify large lists (> 100 items)
2. Replace with virtual scroll component
3. Measure rendering performance
4. Adjust overscan and item height
5. Test scroll smoothness

***REMOVED******REMOVED*** Related Documentation

- [PERFORMANCE_OPTIMIZATION_SUMMARY.md](../PERFORMANCE_OPTIMIZATION_SUMMARY.md) - Full implementation details
- [CLAUDE.md](../CLAUDE.md) - Project guidelines
- [API Documentation](api/) - API reference

***REMOVED******REMOVED*** Support

For issues or questions:
1. Check this quick reference
2. Review comprehensive summary
3. Check test files for usage examples
4. Consult module docstrings

---

**Last Updated:** 2025-12-31
**Session:** 23 - Performance Optimization
**Files Created:** 23 implementation + 4 test files
