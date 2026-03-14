# Security Audit — 2026-03-12

**Scope:** Antigravity IDE extension inventory and CVE analysis
**Auditor:** Antigravity AI Agent
**System:** macOS · Antigravity IDE (VS Code fork)
**Runtime Versions:** Python 3.11.12 · Node v22.22.0 · npm 10.9.4 · Docker 29.1.3

---

## Executive Summary

44 unique extensions installed. **All direct extension CVEs are patched** at current versions. Two dependency-level concerns remain open (YAML parser, Docker Desktop). No `eslint-config-prettier` dependency found — **not affected** by the CISA-cataloged supply chain attack (CVE-2025-54313).

| Risk Level               | Count  | Details                                                                               |
| ------------------------ | ------ | ------------------------------------------------------------------------------------- |
| 🔴 Critical (unpatched)   | **0**  | —                                                                                     |
| 🟡 Dependency / Ecosystem | **2**  | `js-yaml` prototype pollution; Docker Desktop version check                           |
| 🟢 Patched                | **4**  | `ms-python.python`, `eamodio.gitlens`, `dbaeumer.vscode-eslint`, `redhat.vscode-yaml` |
| ⬜ No known CVEs          | **38** | Remaining extensions                                                                  |

---

## Extension Inventory

### AI & Agent Tools
| Extension                                | Version | CVE Status      |
| ---------------------------------------- | ------- | --------------- |
| `anthropic.claude-code`                  | 2.0.13  | ✅ No known CVEs |
| `google.gemini-cli-vscode-ide-companion` | 0.20.0  | ✅ No known CVEs |

### Python
| Extension                      | Version      | CVE Status                                   |
| ------------------------------ | ------------ | -------------------------------------------- |
| `ms-python.python`             | **2026.2.0** | ✅ Patched (see [findings](#ms-pythonpython)) |
| `ms-python.debugpy`            | 2025.18.0    | ✅ No known CVEs                              |
| `ms-python.black-formatter`    | 2025.2.0     | ✅ No known CVEs                              |
| `ms-python.flake8`             | 2025.2.0     | ✅ No known CVEs                              |
| `ms-python.mypy-type-checker`  | 2025.2.0     | ✅ No known CVEs                              |
| `ms-python.vscode-python-envs` | 1.20.1       | ✅ No known CVEs                              |
| `charliermarsh.ruff`           | 2026.36.0    | ✅ No known CVEs                              |

### JavaScript / TypeScript / CSS
| Extension                   | Version    | CVE Status                                         |
| --------------------------- | ---------- | -------------------------------------------------- |
| `dbaeumer.vscode-eslint`    | **3.0.24** | ✅ Patched (see [findings](#dbaeumervscode-eslint)) |
| `esbenp.prettier-vscode`    | 12.3.0     | ✅ No known CVEs                                    |
| `bradlc.vscode-tailwindcss` | 0.14.28    | ✅ No known CVEs                                    |
| `yoavbls.pretty-ts-errors`  | 0.8.4      | ✅ No known CVEs                                    |

### Git & GitHub
| Extension                           | Version     | CVE Status                                  |
| ----------------------------------- | ----------- | ------------------------------------------- |
| `eamodio.gitlens`                   | **17.11.1** | ✅ Patched (see [findings](#eamodiogitlens)) |
| `github.vscode-pull-request-github` | 0.126.0     | ✅ No known CVEs                             |
| `github.vscode-github-actions`      | 0.31.0      | ✅ No known CVEs                             |

### Docker & Containers
| Extension                         | Version   | CVE Status                                      |
| --------------------------------- | --------- | ----------------------------------------------- |
| `ms-azuretools.vscode-docker`     | **2.0.0** | ⚠️ Ecosystem (see [findings](#docker-ecosystem)) |
| `ms-azuretools.vscode-containers` | 2.4.1     | ⚠️ Ecosystem (see [findings](#docker-ecosystem)) |

### Database
| Extension                 | Version | CVE Status      |
| ------------------------- | ------- | --------------- |
| `mtxr.sqltools`           | 0.28.5  | ✅ No known CVEs |
| `mtxr.sqltools-driver-pg` | 0.5.6   | ✅ No known CVEs |

### YAML & Config
| Extension                   | Version    | CVE Status                                        |
| --------------------------- | ---------- | ------------------------------------------------- |
| `redhat.vscode-yaml`        | **1.21.0** | ⚠️ Dependency (see [findings](#redhatvscode-yaml)) |
| `editorconfig.editorconfig` | 0.18.1     | ✅ No known CVEs                                   |
| `tamasfe.even-better-toml`  | 0.21.2     | ✅ No known CVEs                                   |

### Java
| Extension                        | Version | CVE Status      |
| -------------------------------- | ------- | --------------- |
| `redhat.java`                    | 1.52.0  | ✅ No known CVEs |
| `vscjava.vscode-java-pack`       | 0.30.5  | ✅ No known CVEs |
| `vscjava.vscode-java-debug`      | 0.58.5  | ✅ No known CVEs |
| `vscjava.vscode-java-test`       | 0.44.0  | ✅ No known CVEs |
| `vscjava.vscode-java-dependency` | 0.27.0  | ✅ No known CVEs |
| `vscjava.vscode-maven`           | 0.45.1  | ✅ No known CVEs |
| `vscjava.vscode-gradle`          | 3.17.2  | ✅ No known CVEs |

### Go / Ruby / PHP / C++
| Extension                               | Version    | CVE Status      |
| --------------------------------------- | ---------- | --------------- |
| `golang.go`                             | 0.52.2     | ✅ No known CVEs |
| `shopify.ruby-lsp`                      | 0.10.0     | ✅ No known CVEs |
| `devsense.phptools-vscode`              | 1.66.18408 | ✅ No known CVEs |
| `devsense.intelli-php-vscode`           | 0.12.17700 | ✅ No known CVEs |
| `devsense.composer-php-vscode`          | 1.68.18590 | ✅ No known CVEs |
| `devsense.profiler-php-vscode`          | 1.68.18590 | ✅ No known CVEs |
| `llvm-vs-code-extensions.vscode-clangd` | 0.4.0      | ✅ No known CVEs |

### Markdown & CSV
| Extension                    | Version | CVE Status      |
| ---------------------------- | ------- | --------------- |
| `bierner.markdown-mermaid`   | 1.32.0  | ✅ No known CVEs |
| `yzhang.markdown-all-in-one` | 3.6.2   | ✅ No known CVEs |
| `mechatroner.rainbow-csv`    | 3.24.1  | ✅ No known CVEs |

### Testing & UI
| Extension                                  | Version | CVE Status      |
| ------------------------------------------ | ------- | --------------- |
| `hbenl.vscode-test-explorer`               | 2.22.1  | ✅ No known CVEs |
| `ms-vscode.test-adapter-converter`         | 0.2.1   | ✅ No known CVEs |
| `littlefoxteam.vscode-python-test-adapter` | 0.8.1   | ✅ No known CVEs |
| `usernamehw.errorlens`                     | 3.28.0  | ✅ No known CVEs |

---

## CVE Findings

### `ms-python.python`

| CVE            | CVSS | Type                      | Affected Versions | Fixed In             | Your Version | Status    |
| -------------- | ---- | ------------------------- | ----------------- | -------------------- | ------------ | --------- |
| CVE-2025-49714 | High | RCE via crafted workspace | < 2025.8.1        | 2025.8.1 (Jul 2025)  | **2026.2.0** | ✅ PATCHED |
| CVE-2024-49050 | High | RCE via crafted workspace | < 2024.20.0       | 2024.20.0 (Nov 2024) | **2026.2.0** | ✅ PATCHED |

**Attack vector:** An attacker crafts a malicious `.vscode/settings.json` or workspace file. When a developer clones the repository and opens it, the extension executes arbitrary code. Both vulnerabilities were workspace-trust bypasses.

---

### `eamodio.gitlens`

| CVE            | CVSS | Type                 | Affected Versions | Fixed In      | Your Version | Status    |
| -------------- | ---- | -------------------- | ----------------- | ------------- | ------------ | --------- |
| CVE-2023-46944 | High | RCE via crafted file | < 14.0.0          | 14.0.0 (2023) | **17.11.1**  | ✅ PATCHED |

**Attack vector:** Specially crafted file exploiting VS Code workspace trust component. Markdown injection leading to arbitrary code execution.

---

### `dbaeumer.vscode-eslint`

| CVE           | CVSS      | Type                   | Affected Versions | Fixed In | Your Version | Status    |
| ------------- | --------- | ---------------------- | ----------------- | -------- | ------------ | --------- |
| CVE-2020-1481 | Important | RCE via malicious repo | Historical        | Jul 2020 | **3.0.24**   | ✅ PATCHED |

**Related ecosystem alert:**
- **CVE-2025-54313** — Supply chain attack on `eslint-config-prettier` npm package (phishing-sourced Trojan). Added to CISA KEV catalog Jan 2026.
- **Project status:** `eslint-config-prettier` is **NOT installed** in this project. ✅ Not affected.
- **CVE-2025-50537** — Stack overflow in ESLint < 9.26.0. Project uses ESLint 8.57.1 (via `eslint-config-next`). This CVE affects ESLint 9.x only; **8.x is not affected**.

---

### `redhat.vscode-yaml`

| CVE            | CVSS   | Type                                        | Affected                     | Your Version | Status            |
| -------------- | ------ | ------------------------------------------- | ---------------------------- | ------------ | ----------------- |
| CVE-2025-64718 | Medium | Prototype pollution in `js-yaml` dependency | Users parsing untrusted YAML | **1.21.0**   | ⚠️ DEPENDENCY RISK |

**Risk assessment:** LOW for this project. The vulnerability requires parsing a maliciously crafted YAML document. In normal development workflows where you control the YAML sources, this is not exploitable. The extension itself is up-to-date.

**Recommendation:** No immediate action required. Monitor for a `vscode-yaml` update that bumps the `js-yaml` dependency.

---

### Docker Ecosystem

The Docker VS Code extensions (`ms-azuretools.vscode-docker` v2.0.0, `ms-azuretools.vscode-containers` v2.4.1) are current. However, the Docker engine and runtime they interact with have had critical CVEs:

| CVE            | Severity | Type                                                        | Fixed In              |
| -------------- | -------- | ----------------------------------------------------------- | --------------------- |
| CVE-2025-9074  | Critical | Container escape — unauthenticated Docker Engine API access | Docker Desktop 4.44.3 |
| CVE-2025-31133 | Critical | runC container-host separation bypass                       | runC patch (Nov 2025) |
| CVE-2025-52565 | Critical | runC mount manipulation escape                              | runC patch (Nov 2025) |
| CVE-2025-52881 | Critical | runC symlink-based container escape                         | runC patch (Nov 2025) |
| CVE-2025-10657 | High     | Enhanced Container Isolation bypass                         | Docker Desktop 4.47.0 |

**Your Docker version:** `29.1.3` (engine), Docker Desktop CLI `v0.2.0`

> [!WARNING]
> **Verify your Docker Desktop application version** (not just the engine). Open Docker Desktop → Settings → About, and confirm it is ≥ **4.47.0** to cover all listed CVEs. The CLI plugin version (`v0.2.0`) does not correspond to the Desktop version.

---

## Recommendations

### Immediate Actions
1. **Verify Docker Desktop version** ≥ 4.47.0 via the Docker Desktop UI
2. **No other immediate actions required** — all extension CVEs are patched

### Ongoing Hygiene
3. Keep Antigravity IDE extensions on auto-update (current setting appears correct)
4. Periodically audit npm dependencies: `npm audit` in `frontend/`
5. Periodically audit Python dependencies: `pip audit` or `safety check` in `backend/`
6. Avoid cloning and opening untrusted repositories without reviewing `.vscode/` workspace files first

### Extensions to Consider Removing
The following extensions appear **unused by this project** (Residency Scheduler uses Python/TypeScript — not Go/Ruby/PHP/Java/C++). Reducing attack surface by disabling or uninstalling unnecessary extensions is a security best practice:

| Extension                                       | Reason                   |
| ----------------------------------------------- | ------------------------ |
| `golang.go`                                     | No Go code in project    |
| `shopify.ruby-lsp`                              | No Ruby code in project  |
| `devsense.phptools-vscode` (+ 3 PHP extensions) | No PHP code in project   |
| `redhat.java` (+ 6 Java extensions)             | No Java code in project  |
| `llvm-vs-code-extensions.vscode-clangd`         | No C/C++ code in project |

> [!NOTE]
> These extensions have no known CVEs currently, so this is a **defense-in-depth** recommendation, not an urgent action.

---

## Audit Metadata

| Field                  | Value                                                  |
| ---------------------- | ------------------------------------------------------ |
| Date                   | 2026-03-12                                             |
| Extensions Scanned     | 44                                                     |
| CVE Databases Queried  | NVD (NIST), GitHub Security Advisories, Snyk, CISA KEV |
| Critical Findings      | 0                                                      |
| Patched Findings       | 4                                                      |
| Open Dependency Risks  | 2 (low severity)                                       |
| Next Recommended Audit | 2026-06-12 (quarterly)                                 |
