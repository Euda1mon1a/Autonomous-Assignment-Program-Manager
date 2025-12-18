***REMOVED*** Task: Cascade - [Topic]

***REMOVED******REMOVED*** Metadata
- **Status:** pending
- **Pattern:** parallel-diverge | sequential | cross-pollination | validation-loop
- **Priority:** medium
- **Created:** YYYY-MM-DD
- **Requester:** Claude (session-id)

***REMOVED******REMOVED*** Objective
[Clear, single-sentence goal requiring multiple advisors]

***REMOVED******REMOVED*** Context
[Background information for the cascade]

***REMOVED******REMOVED*** Cascade Definition

***REMOVED******REMOVED******REMOVED*** Stage 1: [Name]
- **Agent:** comet | atlas
- **Target:** [Advisor - must be accessible by agent]
- **Query:**
  ```
  [The prompt for this stage]
  ```
- **Output Variable:** $STAGE1_RESULT

***REMOVED******REMOVED******REMOVED*** Stage 2: [Name]
- **Agent:** comet | atlas
- **Target:** [Advisor]
- **Depends On:** Stage 1 (or "parallel with Stage 1")
- **Query:**
  ```
  [The prompt, may include $STAGE1_RESULT]
  ```
- **Output Variable:** $STAGE2_RESULT

***REMOVED******REMOVED******REMOVED*** Stage 3: [Name] (if needed)
- **Agent:** comet | atlas
- **Target:** [Advisor]
- **Depends On:** [Previous stages]
- **Query:**
  ```
  [The prompt]
  ```
- **Output Variable:** $STAGE3_RESULT

***REMOVED******REMOVED*** Access Matrix Check
Verify routing is valid:
- [ ] ChatGPT queries routed through Comet (not Atlas)
- [ ] Perplexity queries routed through Atlas (not Comet)
- [ ] Gemini/Claude queries can use either agent

***REMOVED******REMOVED*** Expected Final Output
[What Claude needs from the completed cascade]

***REMOVED******REMOVED*** Failure Handling
If a stage fails:
- [ ] Document failure mode
- [ ] Attempt alternative routing if available
- [ ] Return partial results with failure notes

---

***REMOVED******REMOVED*** Execution Log

***REMOVED******REMOVED******REMOVED*** Stage 1 Results
**Agent:**
**Executed:** YYYY-MM-DD HH:MM
**Status:** pending | success | failed
**Result:**

***REMOVED******REMOVED******REMOVED*** Stage 2 Results
**Agent:**
**Executed:** YYYY-MM-DD HH:MM
**Status:** pending | success | failed
**Result:**

***REMOVED******REMOVED******REMOVED*** Stage 3 Results (if applicable)
**Agent:**
**Executed:** YYYY-MM-DD HH:MM
**Status:** pending | success | failed
**Result:**

---

***REMOVED******REMOVED*** Final Synthesis
<!-- For Claude to complete after reviewing all stage results -->

**Combined Insights:**

**Conflicts Between Advisors:**

**Recommendation:**

**Completed:** YYYY-MM-DD HH:MM
