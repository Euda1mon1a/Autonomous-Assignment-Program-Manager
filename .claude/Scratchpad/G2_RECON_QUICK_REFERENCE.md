# G2 RECON - Quick Reference Card

**Operation**: Session Artifact Cleanup
**Date**: 2025-12-31
**Status**: Intelligence Complete

---

## 30-Second Summary

- **234 files**, 5.9 MB in OVERNIGHT_BURN
- **218 markdown**, **1 JSON registry**, **10 session directories**
- **All files are valuable** - no deletions recommended
- **Add .gitignore** to prevent future growth (5 minutes, zero risk)
- **Keep all files locally** - they're reference material

---

## File Triage (Decisions Made)

```
KEEP          → 3 files (entry points)
ARCHIVE       → 231 files (reference material)
DELETE        → 0 files (nothing outdated)
CONDITIONS    → FILE_REGISTRY.json (regenerate quarterly)
```

---

## Top 10 Largest Files

| File | Size | Type | Archive? |
|------|------|------|----------|
| FILE_REGISTRY.json | 561 KB | JSON | Yes (conditional) |
| agents-scheduler-enhanced.md | 69 KB | Markdown | Yes |
| SESSION_9_SKILLS/ | 704 KB | Directory | Yes (all) |
| SESSION_8_MCP/ | 672 KB | Directory | Yes (all) |
| SESSION_10_AGENTS/ | 664 KB | Directory | Yes (all) |
| SESSION_6_API_DOCS/ | 488 KB | Directory | Yes (all) |
| SESSION_5_TESTING/ | 464 KB | Directory | Yes (all) |
| SESSION_4_SECURITY/ | 444 KB | Directory | Yes (all) |
| SESSION_7_RESILIENCE/ | 444 KB | Directory | Yes (all) |
| SESSION_3_ACGME/ | 400 KB | Directory | Yes (all) |

---

## 5-Minute Setup

```bash
# 1. Edit .gitignore
nano .gitignore

# 2. Add at end:
.claude/Scratchpad/OVERNIGHT_BURN/
.claude/Scratchpad/CURRENT/
.claude/Scratchpad/*_SESSION*.md
.claude/Scratchpad/*_REPORT.md

# 3. Commit
git add .gitignore
git commit -m "docs: Exclude Scratchpad from git"

# 4. Verify
git status
```

---

## 15-Minute Setup (With Backup)

```bash
# 1-3 above, plus:

# 4. Backup
zip -r .claude_scratchpad_backup_2025-12-31.zip .claude/Scratchpad/

# 5. Verify
unzip -t .claude_scratchpad_backup_2025-12-31.zip | head -5
ls -lh .claude_scratchpad_backup_2025-12-31.zip
```

---

## Session Directory Guide

| Session | Topic | Size | Priority | Use Case |
|---------|-------|------|----------|----------|
| SESSION_1 | Backend patterns | 344 KB | P0 | Architecture reference |
| SESSION_2 | Frontend patterns | 384 KB | P0 | Component patterns, accessibility |
| SESSION_3 | ACGME rules | 400 KB | P1 | Compliance requirements |
| SESSION_4 | Security | 444 KB | P0 | HIPAA/encryption audit |
| SESSION_5 | Testing | 464 KB | P1 | Pytest patterns, fixtures |
| SESSION_6 | API docs | 488 KB | P1 | Endpoint reference |
| SESSION_7 | Resilience | 444 KB | P2 | Advanced concepts |
| SESSION_8 | MCP tools | 672 KB | P1 | Tool documentation |
| SESSION_9 | Skills | 704 KB | P1 | Agent skill specs |
| SESSION_10 | Agents | 664 KB | P0 | Current agent design |

---

## What To Do With Each Type

### Archive (Keep Locally)
- ✅ Session documentation
- ✅ Pattern references
- ✅ Compliance materials
- ✅ Agent specifications
- ✅ Research documents

### Keep in Git (Don't Exclude)
- ✅ CLAUDE.md (project guidelines)
- ✅ docs/ (architecture, guides)
- ✅ Backend/frontend code

### Exclude from Git (Add to .gitignore)
- ⚠️ .claude/Scratchpad/OVERNIGHT_BURN/
- ⚠️ .claude/Scratchpad/CURRENT/
- ⚠️ .claude/Scratchpad/*_SESSION*.md
- ⚠️ .claude/Scratchpad/*_REPORT.md

---

## Decision Tree

```
Do you want to keep session artifacts?
├─ YES (recommended)
│  ├─ Add .gitignore? → YES (5 min, zero risk)
│  │  └─ Create backup? → OPTIONAL (10 min)
│  └─ Delete anything? → NO
│
└─ NO (not recommended)
   ├─ Archive to cloud? → OPTIONAL
   └─ Delete files? → DO NOT (lose reference)
```

---

## Risk Levels

| Action | Risk | Time | Reversible |
|--------|------|------|-----------|
| Add .gitignore | NONE | 5 min | Yes |
| Create backup | NONE | 10 min | Yes |
| Archive to zip | LOW | 15 min | Yes |
| Delete files | HIGH | Immediate | No |
| Move to cloud | LOW | 30 min | Yes |

---

## File Count Summary

```
Total files:        234
├─ Markdown:        218 (average 27 KB each)
├─ JSON:            1 (561 KB registry)
├─ Session dirs:    10 (5.2 MB total)
└─ Research:        1 (40 KB)

Compression potential: 70% (5.9 MB → 1.8 MB with gzip)
```

---

## Important Files to Know

### Must Keep
- `00_MASTER_START_HERE.md` - Entry point
- `SESSION_10_AGENTS/` - Current design
- `SESSION_4_SECURITY/` - Compliance
- `SESSION_3_ACGME/` - Regulations

### Valuable Reference
- `SESSION_1_BACKEND/` - Architecture
- `SESSION_2_FRONTEND/` - UI patterns
- `SESSION_8_MCP/` - Tool docs
- `SESSION_9_SKILLS/` - Agent guide

### Optional (Nice to Have)
- `FILE_REGISTRY.json` - Searchable index
- `SESSION_7_RESILIENCE/` - Advanced topics
- `DEVCOM_RESEARCH/` - Frontier concepts

---

## Growth Projection

```
Current size:       5.9 MB (234 files)
Per major session:  300-400 KB
Per year (10 sess): 3-5 MB additional
5-year projection:  25-30 MB (without cleanup)
```

**Impact of .gitignore**: Stops git tracking, allows local growth

---

## Approval Checklist

- [ ] Read this summary
- [ ] Read EXECUTIVE_SUMMARY.md for details
- [ ] Decide: Keep files locally? → **YES**
- [ ] Decide: Add .gitignore? → **YES**
- [ ] Decide: Create backup? → **OPTIONAL**
- [ ] Ready to implement? → **APPROVE**

---

## Status Indicators

| Item | Status | What's Next |
|------|--------|-------------|
| Intelligence | ✅ Complete | Proceed to decision |
| Risk Assessment | ✅ Complete | All low/none risk |
| Recommendations | ✅ Complete | Ready to implement |
| Implementation | ⏳ Awaiting | Approve .gitignore |
| Documentation | ✅ Complete | 3 documents created |

---

## Contact/Reference

**For full inventory**: `G2_RECON_SESSION_ARTIFACT_MANIFEST.md`
**For implementation**: `GITIGNORE_RECOMMENDATIONS.md`
**For executive summary**: `G2_RECON_EXECUTIVE_SUMMARY.md`
**This quick ref**: `G2_RECON_QUICK_REFERENCE.md`

---

## Final Recommendation

**Keep all files. Add .gitignore. No deletions.**

**Time to implement**: 5-15 minutes
**Risk level**: Minimal (all reversible)
**Approval needed**: For .gitignore commit

---

**Operation Status**: READY FOR IMPLEMENTATION
**Clearance**: G2_RECON Intelligence Complete
