# Praxis CLI Patterns

## Overview

The Praxis CLI (`praxis` command) is built with Click and Rich. It manages workspace state, session lifecycle, constraint visualization, deliberation capture, trust chain operations, bundle export, learning pipeline interaction, domain management, and MCP proxy -- all from the terminal.

## Key File

| File     | Purpose                                                     |
| -------- | ----------------------------------------------------------- |
| `cli.py` | All Click commands, workspace state management, Rich output |

Entry point: `praxis = "praxis.cli:main"` (defined in `pyproject.toml`)

## Command Groups

### Session Commands

```
praxis session create [--domain coc] [--template moderate]
praxis session show
praxis session pause [--reason "..."]
praxis session resume
praxis session end [--summary "..."]
praxis session list [--state active] [--workspace-id ...]
```

### Deliberation Commands

```
praxis deliberation decide <decision> <rationale> [--type scope] [--alternative ...] [--confidence 0.8]
praxis deliberation observe <observation> [--actor ai]
praxis deliberation escalate <issue> [--context "..."]
praxis deliberation timeline [--type decision] [--limit 50]
```

Decision type validation: the `--type` flag is validated against the domain YAML's `capture.decision_types`. Invalid types produce clean error messages listing valid options.

### Constraint Commands

```
praxis constraint show             # 5-dimension gauge bars
praxis constraint check <action> [--resource path]
praxis constraint held
praxis constraint approve <id>
praxis constraint deny <id>
```

### Trust Commands

```
praxis trust chain
praxis trust verify
praxis trust delegate <delegate_id>
praxis trust export [--output bundle.zip]
```

### Domain Commands

```
praxis domain list
praxis domain show <name>
praxis domain validate <name>
praxis domain export <name> [--output domain.zip]
praxis domain import <path.zip>
praxis domain diff <domain1> <domain2>
praxis domain calibration <name>
```

### Learning Commands (CO Layer 5)

```
praxis learn review [--domain coc] [--status pending]
praxis learn approve <proposal_id> [--approved-by human]
praxis learn reject <proposal_id> [--rejected-by human] [--reason "..."]
praxis learn analyze [--domain coc]
```

### MCP Proxy Command

```
praxis mcp serve [--config .praxis/mcp-servers.json] [name:command ...]
```

Reads server config from JSON file or positional arguments. Creates constraint enforcer from active session. Launches stdio proxy.

## Session Persistence

Sessions are persisted to the DataFlow database via db_ops. The CLI reads/writes `current-session.json` as a local cache, with the database as the authoritative source.

## Rich Output

Gauge bars for constraints use block characters with color coding:

- Green: < 70% (AUTO_APPROVED)
- Yellow: 70-89% (FLAGGED)
- Orange: 90-99% (HELD)
- Red: >= 100% (BLOCKED)
