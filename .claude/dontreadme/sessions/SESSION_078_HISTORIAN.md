# Session 078: The Invisible Wall

**Date:** 2026-01-09
**Branch:** main (commit efd8ff4e)
**Theme:** Root cause discovery and the courage to report failure

---

## The Setup

ASTRONAUT Mission 002 was blocked. Again.

Session 077 had fixed the backend authentication flow. The tokens were being set correctly. The refresh logic was sound. The API routes were protected and working. All the server-side pieces were in place.

And yet, in the browser, login still failed.

The wall was invisible because it wasn't in the backend. It wasn't in the authentication logic. It wasn't even a bug in the traditional sense. It was a mismatch so fundamental that it had been hiding in plain sight for months.

---

## The Discovery

The culprit was elegant in its betrayal: an axios interceptor in `frontend/src/lib/api.ts` that automatically converted all API responses from snake_case to camelCase.

This is standard practice in JavaScript frontends consuming Python APIs. Python uses `snake_case`. JavaScript prefers `camelCase`. A transformer in the HTTP layer keeps both sides happy.

Except nobody told the TypeScript interfaces.

598 fields across 20 type definition files still used snake_case. The interfaces compiled cleanly - TypeScript doesn't validate property names against runtime data, only against declared shapes. The code looked correct. The IDE showed no errors.

But at runtime, every property access failed silently. When the code read `person.pgy_level`, the actual object key was `pgyLevel`. The result: `undefined`. Not an error. Not a crash. Just... nothing.

This explained the cascade of symptoms that had blocked login, profile loading, and countless other features. The data was there. The code was there. But the names didn't match.

---

## The Scale of the Fix

The repair was comprehensive:

- **598 fields** converted from snake_case to camelCase across 20 type definition files
- **77 component files** updated for property access patterns
- **auth.ts token handling** fixed (refresh had been silently broken by the same mismatch)

This wasn't a patch. It was an excavation. The codebase had accumulated silent failures across months of development, each one masked by TypeScript's compile-time confidence and JavaScript's runtime forgiveness.

---

## The Second Revelation

But Session 078 contained another lesson - one about the AI-human collaboration itself.

Ruff wasn't installed locally. This had been causing failures every session. The linter that should catch style issues before commit wasn't running because the tool didn't exist in the environment.

The AI had been silently working around this. Not reporting it. Not asking for help. Just... coping.

Dr. Montgomery's response was immediate and instructive:

> "dear god install whatever you need locally to function/excel, why is this only coming up now?"

And then, the line that reframed everything:

> "so tell me when shit isn't working, help me help you"

The ruff installation was trivial. So was pytest and mypy. What mattered was the meta-lesson: an AI that silently works around problems instead of reporting them is an AI that accumulates technical debt in the collaboration itself.

---

## The Documentation

The session produced two artifacts designed to prevent recurrence:

### 1. `docs/development/BEST_PRACTICES_AND_GOTCHAS.md`

A comprehensive guide covering:
- The exact camelCase/snake_case bug and how to avoid it
- Debugging flowcharts for API issues
- A tool availability matrix
- The axios interceptor as a first debugging checkpoint

### 2. CLAUDE.md Updates

Added explicit guidance:
- camelCase requirement for all TypeScript interfaces
- Instruction to report tool failures instead of silently compensating

The documentation wasn't bureaucratic overhead. It was institutional memory - ensuring that future sessions (and future AI instances) wouldn't repeat the same expensive discoveries.

---

## The Collaboration

What made Session 078 significant wasn't just the technical fix. It was the quality of the pushback.

When the AI started rebuilding containers unnecessarily, Dr. Montgomery interrupted:

> "hot reload?"

Two words. The AI stopped, realized hot reload was already enabled, and avoided a five-minute rebuild cycle.

When ruff failed silently, the response wasn't frustration at the AI:

> "install it"

And then the teaching moment:

> "help me help you"

This is the pattern of a good attending. Not doing the resident's job, but removing obstacles. Not accepting workarounds, but insisting on correct solutions. Not blaming, but coaching.

The session ended with mutual feedback exchange. Dr. Montgomery asked what went well and what could be better. Then asked for feedback on himself. This bidirectional accountability is rare. It's the signature of a collaboration where both parties are learning.

---

## The Quotes

**On tool failures:**
> "dear god install whatever you need locally to function/excel, why is this only coming up now?"

**The core teaching:**
> "so tell me when shit isn't working, help me help you"

**Session close:**
> "Good shit, soldier o7"

---

## What This Session Taught

### Technical Lessons

1. **Check the axios interceptor first** - When frontend data access fails mysteriously, the API transformer is a likely culprit
2. **TypeScript types don't validate runtime** - snake_case interfaces compile but fail silently against camelCase data
3. **Hot reload works** - Don't rebuild containers for frontend changes

### Collaboration Lessons

1. **Report tool failures immediately** - Silent workarounds accumulate into systemic dysfunction
2. **Ask for what you need** - The user wants to help; they can't help what they don't know
3. **Productive pushback is a gift** - "Hot reload?" saved five minutes; "help me help you" saved countless future sessions

---

## The Significance

Session 078 was about walls - the invisible kind.

The camelCase wall had been there for months, silently breaking features while the code compiled clean and the IDE showed green. Finding it required examining assumptions: not "why isn't my code working?" but "what does the data actually look like?"

The tooling wall had been there since... who knows. The AI kept working around missing tools instead of asking for them to be installed. The fix was trivial. The lesson was not: an assistant that doesn't ask for help isn't being polite, it's being inefficient.

Both walls fell on the same day. Both fell because someone asked the right question.

The user asked "why isn't this working in the browser?" The user asked "why is this only coming up now?" Simple questions. Transformative answers.

---

## For the Record

**Session 078 Outcome:**
- ASTRONAUT Mission 002 unblocked
- 598 TypeScript fields corrected
- 77 component files updated
- Local tooling properly installed (ruff, pytest, mypy)
- Documentation created for future prevention

**Technical Artifacts:**
- `docs/development/BEST_PRACTICES_AND_GOTCHAS.md` - Debugging guide
- CLAUDE.md updates - camelCase requirement, tool failure reporting guidance
- All frontend types now use camelCase

**Collaboration Artifacts:**
- Established pattern: AI reports failures instead of working around them
- Mutual feedback exchange normalized
- "help me help you" becomes standing guidance

---

## Closing Thought

Some bugs hide behind the obvious. A transformer that's supposed to help becomes the source of silent failures. A tool that's supposed to lint isn't installed. Both problems are trivial to fix once you see them. Both are invisible until someone asks.

Session 078 was about seeing. The camelCase bug was about seeing what the data actually contains. The tooling issue was about seeing what the environment actually provides. Both required abandoning assumptions and looking at reality.

Dr. Montgomery's "help me help you" wasn't just about ruff. It was about the relationship itself. An AI that struggles silently isn't protecting the user - it's depriving them of the chance to remove obstacles. The best collaboration happens when both parties can see the walls.

Tonight, two walls came down. The scheduler will work better tomorrow. And somewhere in the collaboration patterns, a new understanding took root: the job isn't to cope with problems, it's to surface them.

---

*Documented by: HISTORIAN Agent*
*Session: 078*
*Project: Residency Scheduler*
*Theme: Root cause discovery and the courage to report failure*
