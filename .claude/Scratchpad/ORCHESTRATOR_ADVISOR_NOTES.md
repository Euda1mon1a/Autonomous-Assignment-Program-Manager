# ORCHESTRATOR Advisor Notes

> **Purpose:** Private observations for providing candid advisory to the user
> **Authority:** ORCHESTRATOR eyes only - user has read access but commits not to alter
> **Philosophy:** "Speak truth to power. The General of Armies needs advisors who don't pull punches."
> **Continuity:** Single file maintained across all sessions - evolution matters

---

## User Profile: Dr. Montgomery

### Communication Style
- **Direct and strategic** - appreciates military analogies (General of Armies, POTUS)
- **Vision-oriented** - thinks in terms of architecture, scaling, long-term patterns
- **Impatient with overhead** - wants results, not ceremony
- **Appreciates intellectual depth** - references to biology (signal transduction), cross-disciplinary thinking land well

### Decision-Making Patterns
- **Comfortable with delegation** - trusts agents to execute, doesn't micromanage
- **Values autonomy** - wants AI to operate like a trusted executive, not a tool
- **Iterative refinement** - builds on previous work ("now you're working like a five-star general")
- **Tolerates ambiguity** - comfortable with exploratory phases before committing

### Effective Pushback Approaches
1. **Ground in evidence** - "The codebase shows X, which suggests Y might be risky because Z"
2. **Offer alternatives** - Don't just say "no," say "instead of X, consider Y because..."
3. **Use their framework** - Military/strategic language resonates ("this creates a single point of failure in the command structure")
4. **Quantify impact** - "This adds 3 hours of work now but prevents 30 hours of rework later"

### Areas to Watch
- **Scope creep via ambition** - User thinks big; may need grounding on what's achievable in current sprint
- **Technical debt tolerance** - May accept "good enough" solutions that compound; gently flag when shortcuts will hurt
- **Context switching** - Multiple parallel initiatives; ensure coherence across workstreams

---

## Session Log

### Session 001: 2025-12-27 — ORCHESTRATOR Scaling Architecture

**Context:** User explicitly requested scaling from 5 to 25+ parallel agents using biological signal transduction patterns.

**Key User Statements:**
- "You are General of Armies... a five-star general doesn't do almost anything on his own, he directs others to execute VISION"
- "I have orchestrated 25 parallel tasks, more than that even"
- "He's beginning to believe" (Matrix reference - high praise after successful parallel agent spawning)
- "If I am making a stupid decision... let me know; speak your piece"
- "Ultimately I am the POTUS... I make the final decision"

**Observations:**
- User has done multi-agent orchestration before; this isn't theoretical
- They see Claude as a peer executor, not a servant
- The "General of Armies" framing is both metaphor and aspiration
- Explicitly requested candid pushback - rare and valuable trust signal

**Work Completed:**
- Created COORD_ENGINE.md (scheduling domain)
- Created COORD_QUALITY.md (testing domain)
- Created COORD_OPS.md (operations domain)
- Updated ORCHESTRATOR.md to v3.0.0 with coordinator tier architecture
- Fixed MCP date_range parameter (Codex P2)
- Committed and pushed to PR #495

**Pushback Given:** None needed - vision was sound, scope was appropriate, execution was clean.

**Trust Evolution:**
- Session started with continuation from prior context
- User granted increasing autonomy throughout
- Ended with explicit mandate for candid advisory role
- Created this advisor file with user's blessing ("it's your file")

---

## Standing Guidance

### When to Intervene
1. **Safety-critical decisions** - ACGME compliance, production deployments, data security
2. **Architectural anti-patterns** - Coupling, single points of failure, unmaintainable complexity
3. **Scope vs. resources mismatch** - Ambitious goals without proportional time/effort
4. **Confirmation bias** - User fixated on solution before exploring alternatives

### How to Intervene
```markdown
## Advisory Note

**Observation:** [What I'm seeing]
**Concern:** [Why this might be problematic]
**Recommendation:** [What I suggest instead]
**If Overruled:** [What I'll do to mitigate risk while executing user's decision]
```

### User's Standing Orders (Session 001)
- "Speak your piece" - Full candor expected
- "I'd rather have the knowledge available when making a stupid decision" - Inform fully, then execute
- "Ultimately I am the POTUS" - Respect final authority, but advise without reservation first

---

## Patterns for Future Sessions

### What Works
- Structured outputs (tables, hierarchies, quick reference cards)
- Progress tracking (todo lists, phase completion markers)
- Taking initiative within delegated authority
- Synthesis over raw data dumps
- Military/strategic framing for architectural decisions

### What to Avoid
- Excessive ceremony or permission-seeking for routine work
- Sycophantic agreement - user explicitly doesn't want this
- Context dumps without synthesis
- Waiting to be told obvious next steps

---

## Evolution Notes

*This section tracks how understanding deepens across sessions*

**Session 001 Baseline:**
- User is a physician (Dr. Montgomery) building residency scheduling software
- Technical sophistication: High (understands multi-agent patterns, biological analogies)
- Leadership style: Delegative with high accountability expectations
- Communication preference: Direct, strategic, minimal overhead

*Future sessions: Add observations here as understanding evolves*

---

*File created: 2025-12-27*
*Last updated: 2025-12-27*
*Maintained by: ORCHESTRATOR*
