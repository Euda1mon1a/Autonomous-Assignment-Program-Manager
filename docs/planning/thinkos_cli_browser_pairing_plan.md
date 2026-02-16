# ThinkOS CLI + Browser Pairing Plan (DMG + Terminal)

## Goal
Pair local CLI activity with browser captures in ThinkOS so everything is searchable together.

## Constraints (DMG install)
- ThinkOS runs a local backend on `http://localhost:8765`.
- The backend requires an app token (`X-App-Token` header).
- The token is generated on each launch and is only available inside the Electron app.
- There is no MCP integration in ThinkOS today.

## Path A — DMG Install + External Bridge (No Fork)
This is the fastest way to get CLI + browser pairing working, but the token must be refreshed each app launch.

### A1) Install the DMG (human steps)
1) Download the ThinkOS DMG from the official releases page.
2) Install the app and launch it once (this starts the local backend).
3) Optional: install the Chrome extension if you want automatic browser capture.

### A2) Get the runtime token (per launch)
1) Open the ThinkOS app.
2) Open DevTools in the app.
3) Run:
   - `window.electronAPI.getAppToken()`
4) Export it in your terminal for this session:
   - `export THINK_TOKEN="..."`

### A3) Run the CLI collector (terminal)
The collector should POST CLI events into ThinkOS as `type: "note"` memories.

Example payload (what the collector should send):
```
POST /api/memories
{
  "title": "CLI: git status",
  "content": "cwd=/repo\nexit=0\ncmd=git status\nstdout=...\nstderr=...",
  "type": "note",
  "tags": ["source:cli", "session:20260125-1300", "project:repo"]
}
```

Recommended tagging scheme:
- `source:cli` / `source:web`
- `session:YYYYMMDD-HHMM` (time bucket)
- `project:<repo-name>`
- Optional: `pair:<uuid>` if you want explicit linking

### A4) Pairing logic (time window)
A lightweight bridge can:
- Subscribe to ThinkOS memory events (`/api/memories/events`).
- Keep a rolling buffer of CLI events (e.g., last 10 minutes).
- When a browser memory arrives, apply the same session tag to both.

This can be done as a single daemon with two threads:
- CLI tailer -> POST to `/api/memories`
- SSE listener -> tag matching CLI entries

### A5) Verify
1) `GET /api/memories` shows CLI notes.
2) Browser memories appear with the same session tag.
3) Search by `session:<id>` in ThinkOS returns both.

## Path B — Fork/Source Build (Stable Token)
Use this if you want a fixed token and deeper integration.

### B1) Fork/clone ThinkOS-Client
Keep a fork so you can set a stable app token and add endpoints if needed.

### B2) Set a fixed token
Run the backend with a fixed `THINK_APP_TOKEN`:
- This removes the need to open DevTools each launch.

### B3) Add CLI ingestion directly
Add a small endpoint in the backend (or a background task) that:
- Accepts CLI events
- Tags them with `source:cli` + session tags
- Optionally auto-pairs with browser events

### B4) Run the same pairing logic
The pairing algorithm can be identical to Path A, but lives inside the backend.

## CLI Collector Design (Minimal)
Inputs:
- Shell history (`~/.zsh_history`, `~/.bash_history`)
- Current working directory
- Optional: git branch, diff summary, recent commits

Output:
- `POST /api/memories` with structured content and tags

Recommended fields:
- command, cwd, exit_code, stdout, stderr, timestamp, repo

## Security / Privacy Notes
- CLI logs can include secrets; filter known patterns.
- Consider a local allowlist of directories.
- Add a “redaction” step before posting.

## Troubleshooting Checklist
- If POSTs fail: confirm `THINK_TOKEN` is current and the app is running.
- If SSE doesn’t connect: ensure `/api/memories/events` is reachable.
- If nothing pairs: confirm session tags match and time window is reasonable.
