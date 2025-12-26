<!--
Systematic debugging for complex issues.
Enforces explore-plan-debug-fix workflow to prevent premature fixes.
-->

Invoke the systematic-debugger skill for debugging.

***REMOVED******REMOVED*** Arguments

- `$ARGUMENTS` - Bug description or error message

***REMOVED******REMOVED*** Workflow

1. **Explore** - Read code, understand system (NO FIXES YET)
2. **Plan** - Form hypotheses, identify root cause
3. **Debug** - Add logging, reproduce issue
4. **Fix** - Make minimal change to fix root cause
5. **Verify** - Run tests, confirm fix works

***REMOVED******REMOVED*** Rules

- No fixing until exploration complete
- Document findings at each step
- Minimal changes only
