# Claude Code Model Context Reference

> **Last Updated:** 2025-12-30
> **Purpose:** Quick reference for model selection when spawning agents in Claude Code CLI

---

## Context Window Limits

All Claude 4.5 models share the same standard context window:

| Model | Standard Context | Extended Context | Max Output |
|-------|------------------|------------------|------------|
| **Claude Haiku 4.5** | 200K tokens | N/A | 64K tokens |
| **Claude Sonnet 4.5** | 200K tokens | 1M tokens (beta) | 64K tokens |
| **Claude Opus 4.5** | 200K tokens | N/A | 64K tokens |

**Key Facts:**
- All models have **200K token standard context**
- Only **Sonnet 4.5** can access extended 1M context (beta, requires special header)
- All models can output up to **64K tokens** per response

---

## Token Consumption Differences

While context limits are identical, **consumption rates differ significantly** based on reasoning depth:

### Pricing Comparison

| Model | Input Cost | Output Cost | Relative Cost |
|-------|------------|-------------|---------------|
| Haiku 4.5 | $1/1M tokens | $5/1M tokens | 1x (baseline) |
| Sonnet 4.5 | $3/1M tokens | $15/1M tokens | 3x |
| Opus 4.5 | Higher | Higher | ~10x+ |

### Consumption Patterns

| Model | Pattern | Description |
|-------|---------|-------------|
| **Haiku** | Light | Minimal internal reasoning, fast responses |
| **Sonnet** | Moderate | Balanced reasoning depth |
| **Opus** | Heavy | Deep extended thinking, highest token usage |

---

## Hidden Token Consumption (Extended Thinking)

Opus and other models with extended thinking generate **hidden reasoning tokens** that count against usage:

```
Visible Response:     500 tokens
Internal Reasoning: 3,000 tokens
────────────────────────────────
Actual Billed:      3,500 output tokens
```

**Important:** You're billed for ALL tokens generated, not just what you see.

### Opus Effort Parameter

Only Opus 4.5 supports the `effort` parameter to control reasoning depth:

| Effort Level | Token Usage | Performance |
|--------------|-------------|-------------|
| Low | Minimal | Basic tasks |
| Medium | 76% less than High | Matches Sonnet peak |
| High | Maximum | Full reasoning capability |

**Recommendation:** Use "medium effort" for most Opus tasks to balance capability and cost.

---

## Model Selection Guide for Agent Spawning

### Quick Decision Matrix

| Task Type | Recommended Model | Rationale |
|-----------|-------------------|-----------|
| Simple file operations | `haiku` | Fastest, cheapest |
| Code formatting/linting | `haiku` | Low complexity |
| Standard code generation | `sonnet` | Best balance |
| Test writing | `sonnet` | Good capability/cost |
| Complex debugging | `opus` | Needs deep reasoning |
| Architecture decisions | `opus` | Strategic thinking |
| Security audits | `opus` | Thorough analysis |

### Capability Comparison

| Benchmark | Haiku | Sonnet | Opus |
|-----------|-------|--------|------|
| SWE-bench (relative) | 73.3% | 100% (baseline) | Higher |
| Speed | Fastest | Fast | Slowest |
| Cost efficiency | Best | Good | Expensive |
| Complex reasoning | Limited | Good | Excellent |

---

## Task Tool Model Parameter

When using the `Task` tool to spawn agents, specify the model:

```json
{
  "subagent_type": "Explore",
  "model": "haiku",
  "prompt": "Find all API endpoints..."
}
```

### Available Options

| Value | Behavior |
|-------|----------|
| `haiku` | Use Claude Haiku 4.5 |
| `sonnet` | Use Claude Sonnet 4.5 (default) |
| `opus` | Use Claude Opus 4.5 |
| (omitted) | Inherits from parent or defaults to Sonnet |

### Special Model Aliases

| Alias | Behavior |
|-------|----------|
| `opusplan` | Opus for planning, Sonnet for execution |

---

## Practical Examples

### Cost-Optimized Agent Spawning

```
# Use haiku for simple exploration
Task(subagent_type="Explore", model="haiku", prompt="List all test files")

# Use sonnet for standard development (default)
Task(subagent_type="general-purpose", prompt="Implement the feature")

# Use opus for complex analysis
Task(subagent_type="Plan", model="opus", prompt="Design the architecture")
```

### Parallel Agent Strategy

For complex tasks requiring multiple agents:

1. **Exploration phase**: Spawn multiple `haiku` agents in parallel for fast codebase scanning
2. **Analysis phase**: Use `sonnet` for synthesizing findings
3. **Critical decisions**: Escalate to `opus` only when deep reasoning is required

---

## Cost Optimization Tips

1. **Default to Sonnet** - Best general-purpose choice
2. **Use Haiku for volume** - When spawning many agents for simple tasks
3. **Reserve Opus for complexity** - Architecture, security, complex debugging
4. **Leverage effort parameter** - Use medium effort with Opus when possible
5. **Batch similar tasks** - Reduce agent spawn overhead

---

## Summary

| Aspect | Haiku | Sonnet | Opus |
|--------|-------|--------|------|
| Context limit | 200K | 200K (1M beta) | 200K |
| Token consumption | Low | Medium | High |
| Speed | Fastest | Fast | Slowest |
| Cost | Cheapest | Moderate | Expensive |
| Reasoning | Basic | Good | Excellent |
| Best for | Simple tasks | General dev | Complex reasoning |

**Key Insight:** Same context container, different fill rates. Choose based on task complexity, not context needs.

---

## References

- [Claude Models Overview](https://docs.anthropic.com/en/docs/about-claude/models)
- [Claude Code Model Configuration](https://docs.anthropic.com/en/docs/claude-code/settings)
- [Extended Thinking Documentation](https://docs.anthropic.com/en/docs/build-with-claude/extended-thinking)

---

*This document is maintained as a quick reference. For detailed API documentation, consult the official Anthropic docs.*
