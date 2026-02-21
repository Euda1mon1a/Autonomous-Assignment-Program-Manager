# AAPM Celery Worker SIGSEGV Crash Loop

> Documented: 2026-02-18
> Status: ACTIVE — crashing every 5 min, needs fix

## Symptom

Celery worker segfaults (signal 11) every time `run_scheduled_exports` task runs. Beat schedules this task every 5 minutes. Worker PID increments continuously (3690+ ForkPoolWorkers created). 705 SIGSEGV crashes logged today alone. Error log at `~/.openclaw/logs/aapm-celery-worker.err.log` (259 KB and growing).

```
[ERROR/MainProcess] Process 'ForkPoolWorker-XXXX' pid:YYYYY exited with 'signal 11 (SIGSEGV)'
billiard.exceptions.WorkerLostError: Worker exited prematurely: signal 11 (SIGSEGV)
```

## Root Cause Analysis

The task at `app/exports/jobs.py:24` (`run_scheduled_exports`) calls `asyncio.run()` inside a **forked** celery worker process. On macOS, `fork()` + `asyncio.run()` (which creates a new event loop and initializes ObjC runtime objects) is a known cause of SIGSEGV. The billiard library (celery's process pool) uses `fork` pool by default.

The crash happens immediately — the worker never gets far enough to log "No export jobs due" or any task-level output.

**Also affected:** `periodic_health_check` (resilience task) — same pattern, `asyncio.run()` in forked worker.

## Recommended Fixes (choose one)

### Option A: Set fork-safety env var (quick, may not fix all cases)
Add to celery worker LaunchAgent plist or env:
```
OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
```

### Option B: Switch to solo pool (safest, loses concurrency)
Change celery worker launch args:
```
--pool=solo
```
This runs all tasks in the main process (no fork). Safe for macOS. Loses parallelism but AAPM has low task volume.

### Option C: Switch to threads pool (keeps some concurrency)
```
--pool=threads --concurrency=2
```
Threads are fork-safe on macOS. asyncio event loops work in threads.

### Option D: Disable the crashing task (if exports not needed)
Remove or comment out `export-run-scheduled` from `celery_app.py` beat_schedule (line 121). No export jobs are likely configured since AAPM was just deployed.

## Affected Files

- `~/workspace/aapm/backend/app/exports/jobs.py` — the crashing task
- `~/workspace/aapm/backend/app/core/celery_app.py:121` — beat schedule (every 5 min)
- `~/workspace/aapm/backend/app/resilience/tasks.py` — also uses asyncio.run() in fork
- Celery worker LaunchAgent or start script — for pool/env changes

## Notes

- 705 crashes in ~14 hours = 1 crash every ~72 seconds (some cycles hit both export + health_check)
- Worker concurrency is set to 4 in celery_app.py
- Python 3.12.12 in venv at `~/workspace/aapm/backend/.venv`
- No data loss — tasks just fail silently (no export jobs configured)
- Consider also wrapping asyncio calls with `nest_asyncio` or refactoring to sync SQLAlchemy
