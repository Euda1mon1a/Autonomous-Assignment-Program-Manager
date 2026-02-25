# AAPM Office.js AI Schedule Assistant

This is the Office.js Add-in for AI-assisted TAMC schedule editing (Medium #33).

## Development

```bash
npm install
npm run dev
```

The dev server runs on `http://localhost:3000`. You can sideload `manifest.json` in Excel (Desktop or Online) for testing.

## Features Implemented

* **Phase A (Skeleton)**: React taskpane, manifest, read `__SYS_META__` and `__REF__`, `writeScheduleCell` wrapper.
* **Phase B (LLM Integration)**: Pluggable LLM endpoint UI, system prompt construction from grid snapshot + valid codes, parsed cell writes.
* **Phase C (Local Validation)**: ACGME 1-in-7 rule checking in browser before upload.

## Phase D: GCC High Deployment (Future)

For production deployment to DoD/DHA environments:

1. Update `manifest.json` and `index.html` to use the government CDN: `https://appsforoffice.gcc.cdn.office.net/appsforoffice/lib/1/hosted/office.js`
2. Host the built frontend (`npm run build`) in Azure Government.
3. Deploy via M365 Admin Center (Centralized Deployment) targeting the TAMC coordinator security group.
4. Replace local Ollama endpoint with an approved Copilot/vLLM backend.
