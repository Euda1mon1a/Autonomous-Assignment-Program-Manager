# Office.js AI-Navigable State Machine — Architecture Roadmap

> **Status:** Planning (documentation only)
> **Created:** 2026-02-25
> **Depends on:** [Excel Stateful Round-Trip Roadmap](excel-stateful-roundtrip-roadmap.md) Phase 2 (UUID Anchoring)
> **MPL:** MEDIUM #33
> **Origin:** Architectural observation that the hidden metadata layer designed for deterministic import also creates a perfectly structured context window for an LLM agent operating inside Excel via Office.js

---

## Problem Statement

Coordinators currently operate in a disconnected loop: export schedule → edit in Excel → re-import. The Excel file is treated as a dumb visual grid — no programmatic assistance, no validation feedback, no AI support during editing. Meanwhile, the stateful round-trip roadmap is embedding rich machine-readable metadata (`__SYS_META__`, `__REF__`, `__ANCHORS__`) into the exported workbook for deterministic import.

## Insight

Modern Excel is no longer a static grid. Via the Office.js API, it is a scriptable, AI-navigable state machine. Because Office.js is web-native (running a WebKit2 instance on macOS), it bypasses the historical nightmare of Mac VBA macros. It interacts directly with the Excel Document Object Model, meaning it can read and write to `veryHidden` sheets and zero-width columns that human users cannot access via the UI.

By embedding relational state (UUIDs) and domain vocabulary (`activities.code`) into those hidden layers, we haven't just built an offline client for a human coordinator — **we have built a perfectly structured context window for an AI agent.**

---

## 1. What Already Exists

| Component | File | Status |
|-----------|------|--------|
| `__SYS_META__` veryHidden sheet | `backend/app/services/excel_metadata.py:36-46` | **LIVE** — JSON blob in cell A1 |
| `__REF__` veryHidden sheet + Named Ranges | `excel_metadata.py:63-99` | **LIVE** — `ValidRotations`, `ValidActivities` |
| `compute_row_hash()` (MD5 change detection) | `excel_metadata.py:131-143` | **LIVE** — `person_id\|rot1\|rot2\|days` |
| `__ANCHORS__` sheet (UUID + hash per row) | `xml_to_xlsx_converter.py` (~line 500) | **CODE EXISTS** — not wired into export pipeline |
| `ImportBatch` → `ImportStagedAssignment` staging | `backend/app/models/import_staging.py` | **LIVE** — STAGED→APPROVED→APPLIED states |
| Full diff/validation/draft pipeline | `backend/app/services/half_day_import_service.py` | **LIVE** — `stage_block_template2()` → `preview_batch()` → `create_draft_from_batch()` |
| Fuzzy name matching (0.85 threshold) | `import_staging_service.py` | **LIVE** — `difflib.SequenceMatcher` |
| `ExportMetadata` dataclass with `block_map` | `excel_metadata.py:14-33` | **LIVE** — ready for annual workbook |

**Key insight:** Phases 1–2 of the Excel roadmap are the prerequisite for AI navigation. The hidden metadata IS the AI's context window. No additional "AI-specific" metadata is needed — the same UUIDs and reference data that enable deterministic import also enable deterministic AI editing.

---

## 2. Office.js Technical Feasibility

Research confirmed (Feb 2026) via Microsoft Learn docs and GitHub issues:

| Capability | macOS Support | API | Min Version |
|-----------|--------------|-----|-------------|
| Read/write veryHidden sheets | Yes (WebKit2 runtime) | `worksheet.visibility = Excel.SheetVisibility.veryHidden` | ExcelApi 1.2 |
| Read/write hidden columns | Yes | `range.columnHidden = true` or `format.columnWidth = 0` | ExcelApi 1.2 |
| Read/write cell values in hidden areas | Yes | `range.values` — unaffected by visibility state | ExcelApi 1.1 |
| Data Validation (set/read/repair) | Yes | `range.dataValidation` (list, number, date, custom formula) | ExcelApi 1.8 |
| Detect invalid cells | Yes | `range.dataValidation.getInvalidCellsOrNullObject()` | ExcelApi 1.9 |
| Network calls (to FastAPI backend) | Yes | Fetch/XHR with CORS, HTTPS required in production | N/A |
| SSO (Microsoft Entra ID) | Yes | `Office.auth.getAccessToken()` | IdentityAPI 1.3 |

### macOS-Specific Notes

- **Runtime:** WebKit2 (Safari engine), not WebView2 (Chromium, Windows only)
- **API surface is identical** across platforms — the abstraction layer hides webview differences
- **Limitation:** Content add-ins become static during pan/zoom/scroll (WebKit2 limitation)
- **Debugging:** Safari Web Inspector (not Edge DevTools)
- **No plans** from Microsoft to switch macOS to WebView2

### Critical Limitation: No Offline Mode

Office.js add-ins are fundamentally web applications. The add-in HTML/JS loads from your web server and `office.js` loads from Microsoft's CDN. Without internet, the add-in **will not load** (cached versions work for a few days only). There is no official offline mode (GitHub issues #3487, #5588 — still on backlog).

**Implication:** The openpyxl Python pipeline and `fill_template_osa.py` AppleScript pipeline remain essential for disconnected operations. Office.js is an enhancement, not a replacement.

---

## 3. Three-Pipeline Architecture

The Office.js add-in is a third pipeline alongside the existing two:

| Pipeline | Engine | Preserves CF? | Requires Excel.app? | AI-Navigable? | Offline? |
|----------|--------|--------------|---------------------|---------------|---------|
| **openpyxl** (Python backend) | Direct xlsx write | No (rewrites CF) | No | No | Yes |
| **fill_template_osa.py** (AppleScript) | Excel.app via osascript | Yes (100%) | Yes (macOS only) | No | Yes |
| **Office.js add-in** (proposed) | Excel DOM via WebKit2 | Yes (100%) | Yes (macOS + Windows) | **Yes** | **No** |

All three share:
- Same backend: FastAPI → PostgreSQL
- Same import pipeline: `ImportBatch` → `ImportStagedAssignment` → draft → apply
- Same hidden metadata: `__SYS_META__`, `__REF__`, `__ANCHORS__`

The add-in is the only pipeline that enables real-time AI interaction inside the live workbook.

---

## 4. Threat Model & Sandbox Rules

Mixing a probabilistic LLM with a deterministic PostgreSQL schema introduces edge cases. Safety relies on the hidden columns acting as a cryptographic tether.

### Risk 1: Hash Desync (The Diffing Breaker)

**Threat:** LLM edits a row but leaves the old MD5 hash in `__ANCHORS__` Column C intact. Backend sees matching hash → silently skips all of the AI's edits.

**Root cause:** LLMs cannot calculate MD5 hashes.

**Mitigation — "Delete the Hash" Rule:**

1. The add-in's TypeScript wrapper for cell writes auto-clears the corresponding anchor hash:

```typescript
async function writeScheduleCell(
  context: Excel.RequestContext,
  row: number,
  col: number,
  value: string,
) {
  const sheet = context.workbook.worksheets.getItem("Block 10");
  sheet.getCell(row, col).values = [[value]];
  // Auto-clear hash in __ANCHORS__ for this row
  const anchors = context.workbook.worksheets.getItem("__ANCHORS__");
  anchors.getCell(row, 3).values = [[""]]; // Column C = hash
  await context.sync();
}
```

2. Backend behavior (`half_day_import_service.py`): blank Column C → force full row parse. This is the same path used for legacy files without anchors.

3. The system prompt (embedded in `__SYS_META__`) also instructs the LLM: "IF YOU MODIFY A ROW, the add-in will auto-clear its hash." Belt and suspenders — structural enforcement + prompt instruction.

### Risk 2: UUID Scrambling (Relational Forgery)

**Threat:** LLM accidentally shifts hidden UUID columns when inserting/deleting rows, causing the backend to UPSERT against the wrong person.

**Mitigation — Structural Protection:**

1. **Spatial isolation:** UUIDs live in `__ANCHORS__` (separate veryHidden sheet), NOT in hidden columns of the visible grid. Row insertions on the visible sheet don't shift anchor data.

2. **API boundary:** The add-in exposes `writeScheduleCell(row, col, value)` — not raw range access. The wrapper refuses writes to `__ANCHORS__`, `__REF__`, or `__SYS_META__`:

```typescript
const PROTECTED_SHEETS = ["__ANCHORS__", "__REF__", "__SYS_META__"];

function assertWritable(sheetName: string): void {
  if (PROTECTED_SHEETS.includes(sheetName)) {
    throw new Error(`Write refused: ${sheetName} is a protected metadata sheet`);
  }
}
```

3. **Import-side defense:** `half_day_import_service.py` validates `person_id` exists in the database before upserting. A scrambled UUID that doesn't match any person is rejected, not silently applied.

### Risk 3: CUI Spillage (DoD / DHA Compliance)

**Threat:** The master schedule contains CUI (Controlled Unclassified Information) — `DEP` for deployments, `LV` for leave, `SIC` for medical absence, plus names. Routing through a commercial Claude API on a BYOD Mac is data spillage / OPSEC violation.

**Mitigation — Three-Tier Deployment:**

| Tier | Path | CUI-Safe? | AI? | Use Case |
|------|------|-----------|-----|----------|
| **Tier 1: Local-only** | openpyxl + fill_template_osa.py | Yes (no network) | No | Default. Disconnected ops. |
| **Tier 2: On-prem AI** | Office.js + on-prem LLM (vLLM/Ollama) | Yes (no external calls) | Yes | Development, non-CUI data |
| **Tier 3: GCC High** | Office.js + Microsoft Copilot M365 (GCC High) | Yes (IL4/IL5 authorized) | Yes | **Production TAMC** |

**GCC High Details (confirmed Feb 2026):**
- Microsoft 365 Copilot: GA in GCC High since Dec 2025
- Custom Office.js add-ins: Supported in GCC High tenants
- Government CDN required: `https://appsforoffice.gcc.cdn.office.net/appsforoffice/lib/1/hosted/office.js`
- Backend API must be hosted in Azure Government
- Copilot Add-in Actions (agent extensibility): Targeted H1 2026 Wave 2 for GCC High
- AppSource (public store) not accessible — deployment via M365 Admin Center only

**Recommendation:** Build with a pluggable LLM backend (configurable endpoint URL). For development, point at local Ollama. For production TAMC, point at GCC High Copilot or on-prem vLLM.

---

## 5. System Prompt Injection via `__SYS_META__`

The existing `ExportMetadata` dataclass can be extended to carry LLM rules of engagement:

```python
# backend/app/services/excel_metadata.py
@dataclass
class ExportMetadata:
    academic_year: int
    export_timestamp: str
    block_number: int | None = None
    export_version: int = 1
    block_map: dict[str, str] | None = None
    # NEW: AI agent instructions embedded in the workbook
    llm_rules_of_engagement: str | None = None
```

The add-in reads this on startup and uses it as the system prompt for any LLM calls. The backend controls the AI's behavior through the exported file itself — no client-side configuration.

**Default rules (embedded by export):**
```
You are an agent assisting a TAMC residency coordinator. You may read
__SYS_META__ and __REF__ for context. You are authorized to edit the
visible schedule grid (Cols F-BI, Rows 9-69).

UNDER NO CIRCUMSTANCES modify this JSON, the __REF__ arrays, or the
UUIDs in __ANCHORS__. IF YOU MODIFY A ROW, the add-in will auto-clear
its hash in __ANCHORS__.

Valid activity codes: [dynamically populated from __REF__]
Valid rotation codes: [dynamically populated from __REF__]
```

---

## 6. Use Cases Enabled

### 6.1 Smart Cascade Bulk Operations

> "Dr. Vance is deploying. Swap his Tuesday Call with Dr. Stone, fix their post-call days, and change the rest of Vance's week to LV."

The AI reads `__REF__` → knows `CALL`, `PCAT`, `DO`, `LV` are valid codes. Reads `__ANCHORS__` → knows which row is Vance, which is Stone. Executes multi-cell writes via the safe `writeScheduleCell()` wrapper. Hashes auto-cleared. File uploaded → staging table catches any violations → coordinator reviews diff before applying.

### 6.2 Self-Healing Data Validation

If a coordinator accidentally copies/pastes a cell from another workbook and destroys DataValidation dropdowns, the cell is "bricked" for re-import. The AI can:
1. Read `__REF__` Named Ranges (`ValidRotations`, `ValidActivities`)
2. Re-apply DataValidation rules to the visible grid
3. No re-export needed

```typescript
// AI-triggered validation repair
async function repairValidation(context: Excel.RequestContext) {
  const ref = context.workbook.worksheets.getItem("__REF__");
  // Read valid codes, rebuild DataValidation on visible grid
}
```

### 6.3 Local ACGME Pre-Flight

Before uploading, the coordinator asks: "Check if I broke any 1-in-7 rules." The AI reads the visible grid, counts consecutive work days per person, flags violations. Acts as a local linter — cheaper and faster than a round-trip to the CP-SAT solver.

This does NOT replace backend validation. The staging pipeline (`half_day_import_service.py`) remains the authoritative gate. The add-in provides early feedback only.

---

## 7. Implementation Phases

### Phase 0: Prerequisites (already in Excel roadmap)

- [ ] Wire `__ANCHORS__` sheet into the export pipeline (Phase 2 of [Excel Stateful Round-Trip Roadmap](excel-stateful-roundtrip-roadmap.md))
- [ ] Implement DataValidation dropdowns (Phase 3 of Excel roadmap)

These are needed regardless of AI. The add-in reads what the export pipeline writes.

### Phase A: Office.js Add-in Skeleton

- [ ] `office-addin/` directory at repo root (Yeoman `yo office` scaffold, React + TypeScript)
- [ ] Unified JSON manifest (Copilot Add-in Actions compatible)
- [ ] Task pane UI: minimal React panel showing block metadata from `__SYS_META__`
- [ ] `writeScheduleCell()` wrapper with auto-hash-clear
- [ ] Protected sheet guard (refuse writes to `__ANCHORS__`, `__REF__`, `__SYS_META__`)
- [ ] Read `llm_rules_of_engagement` from `__SYS_META__` on init
- [ ] Sideloading for local development

**Effort:** 2-3 days

### Phase B: LLM Integration

- [ ] Pluggable LLM backend (configurable endpoint URL in add-in settings)
- [ ] System prompt assembly: `llm_rules_of_engagement` + `__REF__` valid codes + visible grid snapshot
- [ ] Chat panel in task pane (coordinator types natural language)
- [ ] LLM response → parsed cell writes via `writeScheduleCell()` wrapper
- [ ] Audit log: every AI edit logged with before/after values in task pane
- [ ] Error handling: LLM attempts to write invalid code → reject + show warning

**Effort:** 3-5 days

### Phase C: Local Pre-Flight Validation

- [ ] TypeScript ACGME rule engine (1-in-7, consecutive days, leave overlap)
- [ ] Read visible grid → validate → show warnings in task pane before upload
- [ ] Optional: call backend `/api/v1/schedules/validate` endpoint for full CP-SAT check

**Effort:** 2-3 days

### Phase D: GCC High Deployment

- [ ] Switch CDN to `https://appsforoffice.gcc.cdn.office.net/...`
- [ ] Host add-in web app in Azure Government
- [ ] Centralized deployment via M365 Admin Center (security group assignment)
- [ ] Copilot Add-in Actions registration (when available in GCC High)

**Effort:** 1-2 days

---

## 8. Dependency Graph

```
Excel Roadmap Phase 1 (LIVE: __SYS_META__ + __REF__)
         |
         v
Excel Roadmap Phase 2 (__ANCHORS__ wired into export)  <-- PREREQUISITE
         |
         +---> Excel Roadmap Phase 3 (DataValidation)
         |
         v
Office.js Phase A (add-in skeleton + protected wrappers)
         |
         v
Office.js Phase B (LLM integration + pluggable backend)
         |
         v
Office.js Phase C (local pre-flight validation)
         |
         v
Office.js Phase D (GCC High deployment)
```

**Bottom line:** The add-in is a natural extension of the existing roadmap, not a parallel effort. Phase 2 (anchors) is the critical gate. Once UUIDs are in the workbook, the AI has a reliable identity system. Everything before that is infrastructure that's needed anyway.

---

## 9. What NOT to Build

| Temptation | Why Not |
|-----------|---------|
| Let the LLM recalculate MD5 hashes | LLMs cannot do MD5. Use the "delete the hash" trick instead. |
| Give the LLM raw `Range` access | UUID scrambling risk. Wrap in `writeScheduleCell()`. |
| Replace openpyxl/AppleScript pipelines | Office.js requires internet. Offline must remain first-class. |
| Build AI features before Phase 2 (anchors) | Without UUIDs, the AI can't reliably identify people. Fuzzy matching + LLM = compounding errors. |
| Route CUI through commercial Claude API | OPSEC violation. Pluggable backend — local/GCC High only for production. |
| Build a custom Excel formula engine | Excel already has formulas. Use Office.js to read/write, not replicate. |
| Attempt multi-workbook coordination | One workbook at a time. Annual workbook = separate sheets, not separate files. |

---

## 10. Open-Source References

| Project | Relevance |
|---------|-----------|
| [Pi for Excel](https://github.com/tmustier/pi-for-excel) | Multi-model sidebar agent — closest to what we would build |
| [sv-excel-agent](https://github.com/SylvianAI/sv-excel-agent) | MCP-based agent for Excel (similar to our MCP server approach) |
| [ExcelAgentTemplate](https://github.com/inoueakimitsu/ExcelAgentTemplate) | Office.js + Python backend + LLM agent pattern |
| [SheetAgent](https://sheetagent.github.io/) | Academic research on generalist spreadsheet agents |

---

## Related Files

- [`docs/architecture/excel-stateful-roundtrip-roadmap.md`](excel-stateful-roundtrip-roadmap.md) — Prerequisite roadmap (Phases 1–4)
- [`docs/architecture/annual-workbook-architecture.md`](annual-workbook-architecture.md) — 14-sheet master workbook design
- `backend/app/services/excel_metadata.py` — `ExportMetadata`, `write_sys_meta_sheet()`, `write_ref_sheet()`, `compute_row_hash()`
- `backend/app/services/xml_to_xlsx_converter.py` — `_write_anchor_sheet()` (exists, not wired)
- `backend/app/models/import_staging.py` — `ImportBatch`, `ImportStagedAssignment`
- `backend/app/services/half_day_import_service.py` — Staging, diff, draft pipeline
- `scripts/scheduling/fill_template_osa.py` — AppleScript pipeline (Pipeline #2)
- `scripts/ops/fill_handjam.py` — openpyxl pipeline (Pipeline #1)
