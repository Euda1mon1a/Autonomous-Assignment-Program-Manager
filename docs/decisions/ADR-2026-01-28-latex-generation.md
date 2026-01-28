# ADR: LaTeX Generation for Military Documents

**Date:** 2026-01-28
**Status:** DEFERRED
**PR:** #772 (closed without merge - research archived)

---

## Context

PR #772 evaluated Python-to-LaTeX libraries for automated MFR (Memoranda for Record) generation. The research is comprehensive and well-documented.

### Current State
- **ReportLab 4.4.7** already in requirements.txt (PDF generation)
- **Jinja2 3.1.6** already in requirements.txt (templating)
- Export factory supports: CSV, JSON, XML (no PDF/LaTeX)
- No LaTeX dependencies or templates

### Research Findings (from PR #772)
| Approach | Recommendation |
|----------|----------------|
| **Jinja2 + LaTeX templates** | Best for standardized MFRs |
| **PyLaTeX** | Good for complex dynamic reports |
| **pylatexenc** | Required for input sanitization |
| **ReportLab** | Keep for existing reports |

### Recommended Hybrid (per research)
| Document Type | Method |
|---------------|--------|
| MFRs | Jinja2 + LaTeX templates |
| Compliance Reports | PyLaTeX |
| Clinical Summaries | Keep ReportLab |
| Formal Letters | Jinja2 + LaTeX templates |

---

## Decision

**DEFER** LaTeX integration until:
1. AR 25-50 MFR generation becomes a concrete requirement
2. ReportLab proves insufficient for compliance documentation

### Rationale

1. **No immediate need** - Current PDF needs are met by ReportLab
2. **Dependency overhead** - LaTeX runtime adds ~500MB to Docker images
3. **Operational complexity** - LaTeX compilation requires separate service/container
4. **Research preserved** - PR #772 research doc available if needed later

---

## Action Items

- [x] Review PR #772 research (this ADR)
- [x] Archive research doc locally
- [x] Close PR without merge
- [ ] Revisit when MFR auto-generation becomes priority

---

## Research Location

The full 635-line research document is available at:
- **PR:** https://github.com/[repo]/pull/772
- **Branch:** `claude/research-latex-generation-THEPp`
- **File:** `docs/research/latex-generation-research.md`

To retrieve later:
```bash
git fetch origin claude/research-latex-generation-THEPp
git show origin/claude/research-latex-generation-THEPp:docs/research/latex-generation-research.md
```

---

## References

- ReportLab: Currently in use for PDF generation
- Jinja2: Already in stack for templating
- AR 25-50: Army Correspondence regulations
- ACGME: Compliance reporting requirements
