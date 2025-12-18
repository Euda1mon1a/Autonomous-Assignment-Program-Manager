# Task: Cascade - [Topic]

## Metadata
- **Status:** pending
- **Pattern:** parallel-diverge | sequential | cross-pollination | validation-loop
- **Priority:** medium
- **Created:** YYYY-MM-DD
- **Requester:** Claude (session-id)

## Objective
[Clear, single-sentence goal requiring multiple advisors]

## Context
[Background information for the cascade]

## Cascade Definition

### Stage 1: [Name]
- **Agent:** comet | atlas
- **Target:** [Advisor - must be accessible by agent]
- **Query:**
  ```
  [The prompt for this stage]
  ```
- **Output Variable:** $STAGE1_RESULT

### Stage 2: [Name]
- **Agent:** comet | atlas
- **Target:** [Advisor]
- **Depends On:** Stage 1 (or "parallel with Stage 1")
- **Query:**
  ```
  [The prompt, may include $STAGE1_RESULT]
  ```
- **Output Variable:** $STAGE2_RESULT

### Stage 3: [Name] (if needed)
- **Agent:** comet | atlas
- **Target:** [Advisor]
- **Depends On:** [Previous stages]
- **Query:**
  ```
  [The prompt]
  ```
- **Output Variable:** $STAGE3_RESULT

## Access Matrix Check
Verify routing is valid:
- [ ] ChatGPT queries routed through Comet (not Atlas)
- [ ] Perplexity queries routed through Atlas (not Comet)
- [ ] Gemini/Claude queries can use either agent

## Expected Final Output
[What Claude needs from the completed cascade]

## Failure Handling
If a stage fails:
- [ ] Document failure mode
- [ ] Attempt alternative routing if available
- [ ] Return partial results with failure notes

---

## Execution Log

### Stage 1 Results
**Agent:**
**Executed:** YYYY-MM-DD HH:MM
**Status:** pending | success | failed
**Result:**

### Stage 2 Results
**Agent:**
**Executed:** YYYY-MM-DD HH:MM
**Status:** pending | success | failed
**Result:**

### Stage 3 Results (if applicable)
**Agent:**
**Executed:** YYYY-MM-DD HH:MM
**Status:** pending | success | failed
**Result:**

---

## Final Synthesis
<!-- For Claude to complete after reviewing all stage results -->

**Combined Insights:**

**Conflicts Between Advisors:**

**Recommendation:**

**Completed:** YYYY-MM-DD HH:MM
