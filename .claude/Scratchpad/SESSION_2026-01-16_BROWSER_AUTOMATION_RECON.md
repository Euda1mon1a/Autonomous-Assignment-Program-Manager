# Browser Automation Reconnaissance

**Date:** 2026-01-16
**Purpose:** Evaluate browser automation capabilities for AI research skills

---

## Objective

Probe browser automation tools to determine:
1. Which research platforms support automation
2. What tools work vs. are blocked
3. Inform skill development for `/perplexity-research` or similar

---

## Platform: Perplexity (perplexity.ai)

### Tools Tested

| Tool | Status | Error |
|------|--------|-------|
| `navigate` | :white_check_mark: Works | Can navigate to any URL |
| `tabs_create_mcp` | :white_check_mark: Works | Can create tabs |
| URL-based search | :white_check_mark: Works | `perplexity.ai/search?q=...` triggers search |
| `read_page` | :x: Blocked | ExtensionsSettings policy |
| `get_page_text` | :x: Blocked | ExtensionsSettings policy |
| `computer` (screenshot) | :x: Blocked | ExtensionsSettings policy |
| `javascript_tool` | :x: Blocked | ExtensionsSettings policy |
| `find` | :x: Blocked | ExtensionsSettings policy |
| `form_input` | :x: Blocked | Depends on read_page refs |

### Root Cause

Perplexity uses Chrome's **ExtensionsSettings enterprise policy** to block ALL content script injection. This is a site-wide security measure that prevents any extension from:
- Reading page content (DOM, accessibility tree)
- Executing JavaScript
- Taking screenshots
- Interacting with elements

### Workarounds Identified

1. **URL-based navigation only** - Can open searches, user reads results
2. **Use WebSearch tool** - Built-in Claude tool bypasses browser
3. **Hybrid approach** - Navigate for user, gather via WebSearch

---

## Platform: Google AI Studio (aistudio.google.com)

**Status:** :white_check_mark: FULLY AUTOMATABLE

### Tools Tested

| Tool | Status | Notes |
|------|--------|-------|
| `navigate` | :white_check_mark: Works | Full navigation |
| `read_page` | :white_check_mark: Works | Full DOM access |
| `computer` (screenshot) | :white_check_mark: Works | Screenshots captured |
| `find` | :white_check_mark: Works | Element search works |
| `form_input` | :white_check_mark: Works | Via click + type (DIV textboxes) |

### Notes
- Logged in as user automatically (Google SSO)
- Full access to Gemini 3, API keys, playground
- Can create apps, monitor usage, access docs

---

## Platform: Google Gemini (gemini.google.com)

**Status:** :white_check_mark: FULLY AUTOMATABLE

### Tools Tested

| Tool | Status | Notes |
|------|--------|-------|
| `navigate` | :white_check_mark: Works | Full navigation |
| `read_page` | :white_check_mark: Works | Full DOM access |
| `computer` (screenshot) | :white_check_mark: Works | Screenshots captured |
| `find` | :white_check_mark: Works | Element search works |
| `form_input` | :heavy_minus_sign: Partial | DIV textbox requires click + type |
| Click + Type | :white_check_mark: Works | Full prompt entry |
| Submit (Enter) | :white_check_mark: Works | Query submission |
| Scroll | :white_check_mark: Works | Response navigation |

### Capabilities Confirmed
- Enter research queries
- Submit to Gemini 3 with "Thinking" mode
- Scroll through responses
- Click "Sources" to expand citations
- Read source URLs from sidebar
- Full end-to-end research workflow

---

## Time Crystal Research - Demo Results

Successfully executed full research workflow on Gemini. Query:
> "Is there academic research on applying discrete time crystal physics concepts to distributed systems?"

### Key Findings from Gemini

**1. Stroboscopic Observation = Consistency Model**
- Floquet periods in physics = Snapshot Consistency / Periodic State Synchronization in CS
- State-at-Checkpoint models mathematically identical

**2. Symmetry Breaking = Consensus**
- DTTSB (Discrete Time-Translation Symmetry Breaking) parallels Paxos/Raft leader election
- Many-Body Localization (MBL) = Fault Tolerance

**3. Concept Mapping Table**

| Concept | Distributed Systems (CS) | Discrete Time Crystals (Physics) |
|---------|--------------------------|----------------------------------|
| Driving Force | Heartbeats / Clock Ticks | Periodic Hamiltonian (Kicks) |
| State Update | Logical Clocks (Lamport) | Floquet Unitary Evolution |
| Consistency | Eventual / Sequential | Subharmonic Rigidity |
| Failure Mode | Partition / Byzantine Fault | Thermalization (Entropy) |

### Source Papers (with URLs)

1. **"Route to Extend the Lifetime of a Discrete Time Crystal in a Finite Spin Chain without Disorder"** (MDPI)
   - https://www.mdpi.com/2218-2004/9/2/25

2. **"Realization of a discrete time crystal on 57 qubits of a quantum computer"** (Stanford/Google, 2021)
   - https://pmc.ncbi.nlm.nih.gov/articles/PMC8890700/

3. **"First Passage Problem: Asymptotic Corrections due to Discrete Sampling"** (arXiv, 2025)
   - https://arxiv.org/html/2510.10226v1
   - Directly applicable to timeout/heartbeat modeling

### Validation for Codebase

The `stroboscopic_manager.py` approach is **academically grounded**:
- Stroboscopic observation windows = discrete checkpoints
- Breaking continuous update symmetry = DTC's DTTSB
- This is a nascent but legitimate crossover field

---

## Platform: Google Scholar

**Status:** Not yet tested

---

## Skill Design Implications

### Recommended: Gemini-Based Research Skill

Given Perplexity blocks automation but Gemini allows full access:

```yaml
skill: /deep-research
platform: gemini.google.com
capabilities:
  - Enter complex research queries
  - Use "Thinking" mode for deep reasoning
  - Scroll and capture full responses
  - Extract source URLs with citations
  - Export findings to scratchpad
```

### Fallback Strategy
1. Primary: Gemini (full automation)
2. Secondary: Google AI Studio (API-based queries)
3. Tertiary: WebSearch (built-in, no browser needed)

---

## Next Steps

1. ~~Test Google AI Studio~~ :white_check_mark: Done - Works
2. ~~Test Google Gemini~~ :white_check_mark: Done - Works
3. Test Google Scholar
4. Create `/deep-research` skill using Gemini
5. Document skill for human users

---

*Updated: 2026-01-16 - Gemini research workflow validated*
