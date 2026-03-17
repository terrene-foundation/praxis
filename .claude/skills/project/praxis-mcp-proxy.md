# Praxis MCP Proxy

## Overview

MCP proxy that mediates AI tool calls through the Praxis trust layer. Implements "trust as medium" -- every tool call is intercepted, evaluated against constraints, and either forwarded, held, or blocked.

## Key File

| File           | Purpose                                                      |
| -------------- | ------------------------------------------------------------ |
| `mcp/proxy.py` | `PraxisProxy` -- MCP stdio proxy with constraint enforcement |

## Architecture

```
AI -> stdio -> PraxisProxy -> constraint check -> downstream MCP servers
```

Tool namespacing: `server__tool` (e.g., `filesystem__read_file`).

## Tool Dimension Classification

Maps tool names to constraint dimensions via substring matching:

| Dimension     | Keywords                                                |
| ------------- | ------------------------------------------------------- |
| operational   | exec, shell, bash, run, deploy, delete, remove, install |
| data_access   | read_file, write_file, edit, search, glob, file, path   |
| communication | http, fetch, api, url, web, email, send                 |
| financial     | token, cost, billing, credit, spend, budget             |

Order matters: operational checked first (catches destructive actions). Default: operational.

## Verdict Handling

- BLOCKED: return error, don't forward
- HELD: queue for human approval, return held_action_id
- FLAGGED: forward with warning prepended
- AUTO_APPROVED: forward silently

## Auto-Capture

Every tool call (regardless of verdict) produces:

- Audit anchor via `AuditChain.append()` (if available)
- Deliberation observation via `DeliberationEngine.record_observation()` (if available)

## Fallback

When MCP Python SDK not installed, falls back to JSON-RPC 2.0 loop over stdio. Lines >10 MB are dropped.
