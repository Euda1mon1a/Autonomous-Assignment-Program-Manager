# Codex App Server Integration Guide

> **Last Updated:** 2026-02-05 | **Status:** Planning | **Author:** AAPM Architecture Team

---

## Executive Summary

The release of OpenAI's [Codex App Server](https://developers.openai.com/codex/app-server) documentation provides a powerful architectural blueprint for the next stage of AI orchestration in AAPM. This document outlines how to integrate the Codex App Server into our existing Claude Code + MCP + GitHub ecosystem, with specific attention to DoD/DHA data security requirements for medical residency scheduling.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture Comparison](#architecture-comparison)
3. [Unified Agent Orchestration](#unified-agent-orchestration)
4. [Medical Data Security Considerations](#medical-data-security-considerations)
5. [Protocol Deep Dive](#protocol-deep-dive)
6. [Integration Architecture](#integration-architecture)
7. [Implementation Roadmap](#implementation-roadmap)
8. [References](#references)

---

## Overview

### What is the Codex App Server?

OpenAI's coding agent Codex exists across many surfaces: the web app, CLI, IDE extensions, and the macOS app. Under the hood, they're all powered by the same **Codex harness**—the agent loop and logic that underlies all Codex experiences.

The [Codex App Server](https://developers.openai.com/codex/app-server) is a **client-friendly, bidirectional JSON-RPC API** that exposes this harness as a stable, UI-friendly event stream. It serves as the critical link between different Codex surfaces and enables:

- Full functionality of the agent loop
- Sign in with ChatGPT integration
- Model discovery and configuration management
- Thread-based conversation management
- Approval workflows for sensitive operations

### Why This Matters for AAPM

The App Server allows us to move beyond treating Codex as just an IDE plugin and start treating it as a **portable service** within the AAPM stack. Key benefits:

| Benefit | Description |
|---------|-------------|
| **Consistent Agent Behavior** | Same engine across terminal, web dashboard, and automated jobs |
| **Stateful Threads** | Long-lived conversation threads vs. ephemeral context |
| **Approval Intercepts** | Configurable approval flows for sensitive operations |
| **Local Control** | Self-hosted harness for tighter PII/PHI control |
| **Open Source** | Full source available at [github.com/openai/codex](https://github.com/openai/codex) |

---

## Architecture Comparison

### Current vs. Proposed Workflow

| Feature | Current Claude Code Workflow | Codex App Server Integration |
|---------|------------------------------|------------------------------|
| **Protocol** | Model Context Protocol (MCP) | Bidirectional JSON-RPC 2.0 |
| **Logic Location** | Primarily within LLM context | Long-lived process (stateful threads) |
| **Tool Execution** | Client-driven (AAPM provides tools) | Server-driven (agent requests tool use) |
| **Remote Capability** | Harder to run headless | Native support for remote TUI connections |
| **State Management** | Per-session | Persistent thread history |
| **Approval Model** | MCP tool permissions | Fine-grained per-operation approvals |

### Complementary Architecture

The Codex App Server **complements** rather than replaces our existing MCP infrastructure:

```
┌─────────────────────────────────────────────────────────────────┐
│                        AAPM Orchestration Layer                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ Claude Code  │    │ Codex App    │    │   MCP        │      │
│  │   (Primary)  │◄──►│   Server     │◄──►│   Server     │      │
│  │              │    │  (Delegate)  │    │  (34+ Tools) │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                   │                   │               │
│         └───────────────────┼───────────────────┘               │
│                             ▼                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                  Residency Scheduler Backend              │   │
│  │  (FastAPI + SQLAlchemy + PostgreSQL + CP-SAT Solver)     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Unified Agent Orchestration

### Moltbot Integration Pattern

Instead of manual context switching between Claude Code and Codex, run the Codex App Server as a background process on the Mac mini M4 Pro. Custom Moltbot agents can "talk" to this server via JSON-RPC to delegate complex code generation tasks while main logic stays in the Python/Next.js environment.

```python
# Example: Moltbot delegating to Codex App Server
import asyncio
import json
from typing import AsyncGenerator

class CodexAppServerClient:
    """Client for communicating with Codex App Server via JSON-RPC."""

    def __init__(self, process: asyncio.subprocess.Process):
        self.process = process
        self.request_id = 0

    async def initialize(self, client_info: dict) -> dict:
        """Initialize the App Server connection."""
        return await self._request("initialize", {
            "client": client_info,
            "capabilities": {}
        })

    async def start_thread(self, model: str = "codex-1") -> dict:
        """Start a new conversation thread."""
        return await self._request("thread/start", {
            "model": model,
            "instructions": "You are assisting with AAPM residency scheduling."
        })

    async def start_turn(
        self,
        thread_id: str,
        user_input: str,
        cwd: str | None = None
    ) -> dict:
        """Begin a turn in the conversation."""
        params = {
            "threadId": thread_id,
            "input": [{"type": "text", "text": user_input}]
        }
        if cwd:
            params["cwd"] = cwd
        return await self._request("turn/start", params)

    async def stream_events(self) -> AsyncGenerator[dict, None]:
        """Stream events from the App Server."""
        while True:
            line = await self.process.stdout.readline()
            if not line:
                break
            event = json.loads(line.decode())
            yield event
            if event.get("method") == "turn/completed":
                break

    async def respond_approval(
        self,
        request_id: int,
        decision: str
    ) -> None:
        """Respond to an approval request."""
        response = {
            "id": request_id,
            "result": {"decision": decision}
        }
        self.process.stdin.write(
            (json.dumps(response) + "\n").encode()
        )
        await self.process.stdin.drain()

    async def _request(self, method: str, params: dict) -> dict:
        """Send a JSON-RPC request."""
        self.request_id += 1
        request = {
            "id": self.request_id,
            "method": method,
            "params": params
        }
        self.process.stdin.write(
            (json.dumps(request) + "\n").encode()
        )
        await self.process.stdin.drain()

        # Read response
        response_line = await self.process.stdout.readline()
        return json.loads(response_line.decode())
```

### Cross-Platform Consistency

Because the App Server is the same engine used in the Codex macOS app and web runtime, agent behavior is identical whether triggering tasks from:

- Terminal (local development)
- Web dashboard (coordinator interface)
- Automated cron job (CI/CD or scheduled generation)
- Mobile device (remote monitoring)

---

## Medical Data Security Considerations

### OPSEC/PERSEC Compliance

For DoD/DHA physicians, the "bidirectional" nature of the App Server provides significant upgrades for PII/PHI protection.

#### Approval Intercepts

Configure the App Server to trigger "User Approval" requests before executing any tool that might interact with sensitive residency data:

```python
# Approval configuration for sensitive operations
SENSITIVE_OPERATIONS = {
    "file_write": ["*.json", "*.sql", "schedules/*"],
    "shell_command": ["psql", "pg_dump", "alembic"],
    "api_call": ["/api/v1/people/*", "/api/v1/schedules/*"]
}

async def approval_handler(event: dict) -> str:
    """
    Handle approval requests for sensitive operations.

    Returns 'accept' or 'decline' based on operation and context.
    """
    operation = event.get("params", {}).get("operation")
    target = event.get("params", {}).get("target")

    # Log all approval requests for audit trail
    await log_approval_request(operation, target)

    # Check against sensitive patterns
    if is_sensitive_operation(operation, target):
        # For automated systems, decline by default
        # For interactive systems, prompt user
        if is_automated_context():
            return "decline"
        else:
            return await prompt_user_approval(operation, target)

    return "accept"
```

#### Local Control Benefits

By hosting the server logic on your own hardware via the [open-source implementation](https://github.com/openai/codex/tree/main/codex-rs/app-server), you maintain tighter control over the "harness" that processes code:

| Security Aspect | Cloud Plugin | Self-Hosted App Server |
|-----------------|--------------|------------------------|
| Data residency | Provider-controlled | Local-controlled |
| Audit logging | Limited | Full control |
| Network isolation | Internet required | Air-gapped possible |
| Approval policies | Provider defaults | Custom policies |

### Integration with Existing Security

The App Server integration must respect our existing security architecture:

```
┌─────────────────────────────────────────────────────────────────┐
│                      Security Boundary                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────┐    ┌────────────┐    ┌────────────┐            │
│  │  JWT Auth  │    │  RBAC      │    │  Audit     │            │
│  │  (httpOnly)│    │  (8 roles) │    │  Logging   │            │
│  └─────┬──────┘    └─────┬──────┘    └─────┬──────┘            │
│        │                 │                 │                    │
│        └─────────────────┼─────────────────┘                    │
│                          ▼                                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Codex App Server (Local)                     │   │
│  │  - Approval intercepts for sensitive ops                  │   │
│  │  - No PHI/PII in context window                          │   │
│  │  - Synthetic IDs for all demos                           │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Protocol Deep Dive

### JSON-RPC 2.0 Protocol

The App Server uses JSON-RPC 2.0 (omitting the `"jsonrpc":"2.0"` header for brevity) over stdio with JSONL streaming.

#### Initialization Handshake

```json
// Client → Server: Initialize
{
  "id": 1,
  "method": "initialize",
  "params": {
    "client": {
      "name": "aapm-moltbot",
      "version": "1.0.0"
    },
    "capabilities": {}
  }
}

// Server → Client: Initialize Response
{
  "id": 1,
  "result": {
    "serverInfo": {
      "name": "codex-app-server",
      "version": "2.0.0"
    },
    "capabilities": {
      "approvals": true,
      "threads": true
    }
  }
}

// Client → Server: Initialized Notification
{
  "method": "initialized"
}
```

#### Thread Lifecycle

```json
// Start a new thread
{
  "id": 2,
  "method": "thread/start",
  "params": {
    "model": "codex-1",
    "instructions": "Assist with AAPM scheduling tasks."
  }
}

// Response includes thread ID
{
  "id": 2,
  "result": {
    "threadId": "thread_abc123",
    "model": "codex-1"
  }
}

// Start a turn
{
  "id": 3,
  "method": "turn/start",
  "params": {
    "threadId": "thread_abc123",
    "input": [{"type": "text", "text": "Review the ACGME compliance for Block 10"}]
  }
}
```

#### Event Stream

After `turn/start`, the server streams events:

```json
// Item started
{"method": "item/started", "params": {"itemId": "item_1", "type": "agentMessage"}}

// Message delta (streaming)
{"method": "item/agentMessage/delta", "params": {"itemId": "item_1", "delta": "Analyzing "}}
{"method": "item/agentMessage/delta", "params": {"itemId": "item_1", "delta": "Block 10..."}}

// Item completed
{"method": "item/completed", "params": {"itemId": "item_1"}}

// Turn completed
{"method": "turn/completed", "params": {"turnId": "turn_1", "status": "completed"}}
```

#### Approval Flow

When the agent requests a sensitive operation:

```json
// Server → Client: Approval Request
{
  "id": 100,
  "method": "approval/requested",
  "params": {
    "operation": "shell_command",
    "command": "alembic upgrade head",
    "cwd": "/home/user/aapm/backend"
  }
}

// Client → Server: Approval Response
{
  "id": 100,
  "result": {
    "decision": "accept",
    "acceptSettings": {
      "allowFutureSimilar": false
    }
  }
}
```

### Schema Generation

Generate type bindings for your language:

```bash
# TypeScript schema
codex app-server generate-ts --out ./schemas

# JSON Schema bundle
codex app-server generate-json-schema --out ./schemas
```

---

## Integration Architecture

### Deployment Topology

```
┌─────────────────────────────────────────────────────────────────┐
│                    Mac mini M4 Pro (Home Server)                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐    ┌─────────────────┐                     │
│  │ Codex App       │    │ PostgreSQL      │                     │
│  │ Server (daemon) │    │ (schedules DB)  │                     │
│  └────────┬────────┘    └────────┬────────┘                     │
│           │                      │                               │
│           └──────────┬───────────┘                               │
│                      │                                           │
│  ┌───────────────────┴───────────────────┐                      │
│  │         AAPM Backend (FastAPI)         │                      │
│  │  - MCP Server (34+ tools)             │                      │
│  │  - Moltbot orchestration              │                      │
│  │  - Codex client bindings              │                      │
│  └───────────────────┬───────────────────┘                      │
│                      │                                           │
└──────────────────────┼──────────────────────────────────────────┘
                       │
          ┌────────────┼────────────┐
          │            │            │
          ▼            ▼            ▼
     ┌────────┐   ┌────────┐   ┌────────┐
     │ VS Code│   │  iPad  │   │ CI/CD  │
     │  Local │   │ Remote │   │ GitHub │
     └────────┘   └────────┘   └────────┘
```

### Headless Scheduling Use Case

Refactor AAPM deployment to run a headless Codex server for remote code operations:

```python
# Example: Remote schedule generation via Codex
async def generate_schedule_remote(
    block_id: int,
    academic_year: str
) -> ScheduleResult:
    """
    Generate schedule using Codex agent, runnable from any device.

    This allows initiating large-scale operations (like schema migrations
    or schedule generation) from an iPad while on clinical duty, with
    the agent running persistently on the M4 Pro at home.
    """
    async with CodexAppServerClient.connect() as codex:
        # Start dedicated thread for this generation
        thread = await codex.start_thread(
            model="codex-1",
            instructions=f"""
            You are generating a schedule for Block {block_id} of {academic_year}.
            Use the MCP tools available to:
            1. Validate ACGME constraints
            2. Run the CP-SAT solver
            3. Verify coverage requirements
            4. Generate audit trail
            """
        )

        # Execute generation
        await codex.start_turn(
            thread_id=thread["threadId"],
            user_input=f"Generate optimized schedule for Block {block_id}",
            cwd="/home/user/aapm/backend"
        )

        # Stream results with approval handling
        async for event in codex.stream_events():
            if event.get("method") == "approval/requested":
                # Auto-approve safe operations, escalate others
                decision = await evaluate_approval(event["params"])
                await codex.respond_approval(event["id"], decision)

            if event.get("method") == "turn/completed":
                return parse_schedule_result(event)
```

---

## Implementation Roadmap

### Phase 1: Proof of Concept (1-2 weeks)

- [ ] Install and configure Codex App Server locally
- [ ] Generate TypeScript bindings for AAPM
- [ ] Create basic Python client wrapper
- [ ] Test initialization and thread management
- [ ] Document approval flow integration points

### Phase 2: Security Integration (2-3 weeks)

- [ ] Implement approval intercepts for sensitive operations
- [ ] Integrate with existing JWT/RBAC system
- [ ] Add audit logging for all Codex operations
- [ ] Test against OPSEC/PERSEC requirements
- [ ] Document security configuration

### Phase 3: Moltbot Integration (2-4 weeks)

- [ ] Create Moltbot-Codex bridge service
- [ ] Implement delegation patterns for code generation
- [ ] Add thread persistence for long-running tasks
- [ ] Test cross-platform consistency
- [ ] Document orchestration patterns

### Phase 4: Production Deployment (2-3 weeks)

- [ ] Deploy to Mac mini M4 Pro
- [ ] Configure systemd/launchd daemon
- [ ] Set up monitoring and alerting
- [ ] Test remote access from various devices
- [ ] Document operational procedures

---

## References

### Official Documentation

- [Codex App Server Documentation](https://developers.openai.com/codex/app-server)
- [Unlocking the Codex Harness: How We Built the App Server](https://openai.com/index/unlocking-the-codex-harness/)
- [Codex GitHub Repository](https://github.com/openai/codex)
- [App Server README](https://github.com/openai/codex/blob/main/codex-rs/app-server/README.md)

### Related AAPM Documentation

- [MCP Tool Guide](../api/MCP_TOOL_GUIDE.md)
- [MCP IDE Integration](../MCP_IDE_INTEGRATION.md)
- [Personal Infrastructure](../PERSONAL_INFRASTRUCTURE.md)

### External Resources

- [Codex Changelog](https://developers.openai.com/codex/changelog/)
- [Use Codex with the Agents SDK](https://developers.openai.com/codex/guides/agents-sdk/)
- [Unrolling the Codex Agent Loop](https://openai.com/index/unrolling-the-codex-agent-loop/)

---

## Appendix A: Quick Reference

### Codex App Server CLI Commands

```bash
# Start the App Server
codex app-server

# Generate TypeScript schema
codex app-server generate-ts --out ./schemas

# Generate JSON Schema
codex app-server generate-json-schema --out ./schemas
```

### Key JSON-RPC Methods

| Method | Direction | Purpose |
|--------|-----------|---------|
| `initialize` | Client → Server | Start handshake |
| `initialized` | Client → Server | Complete handshake |
| `thread/start` | Client → Server | New conversation |
| `thread/resume` | Client → Server | Continue conversation |
| `thread/fork` | Client → Server | Branch conversation |
| `thread/compact` | Client → Server | Trigger compaction |
| `turn/start` | Client → Server | Begin user turn |
| `turn/interrupt` | Client → Server | Cancel turn |
| `item/started` | Server → Client | Item notification |
| `item/completed` | Server → Client | Item notification |
| `item/agentMessage/delta` | Server → Client | Streaming message |
| `turn/completed` | Server → Client | Turn finished |
| `approval/requested` | Server → Client | Approval needed |

### Authentication Options

| Mode | Use Case |
|------|----------|
| `apiKey` | Programmatic access with OpenAI API key |
| `chatgpt` | Interactive use with ChatGPT OAuth |

---

*This document is part of the AAPM Architecture Documentation. For questions or updates, contact the AAPM Architecture Team.*
