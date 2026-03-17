# Praxis Constraint System

## Overview

The constraint system enforces the five CO constraint dimensions at runtime. Every action is evaluated against the session's constraint envelope, and the MOST RESTRICTIVE verdict across all dimensions is returned. This is not observational -- actions flow through the constraint enforcer before they can proceed.

## Key Files

| File                 | Purpose                                                                      |
| -------------------- | ---------------------------------------------------------------------------- |
| `core/constraint.py` | `ConstraintEnforcer` (5-dimension eval) + `HeldActionManager` (approve/deny) |
| `trust/gradient.py`  | `evaluate_action` -> `GradientVerdict` (pure function, single source)        |
| `api/middleware.py`  | `enforce_constraints` -> pre-handler gate (BLOCKED=403, HELD=202)            |

## The Five Dimensions

These are the canonical CO constraint dimensions. The names and order must not change:

1. **Financial** -- spending limits (`max_spend`, `current_spend`), auto-accumulates spend from context
2. **Operational** -- action allow/block lists (`allowed_actions`, `blocked_actions`)
3. **Temporal** -- time limits (`max_duration_minutes`, `elapsed_minutes`), auto-tracks from wall clock
4. **Data Access** -- path allow/block lists (`allowed_paths`, `blocked_paths`)
5. **Communication** -- channel allow/block lists (`allowed_channels`, `blocked_channels`)

## Gradient Thresholds (Normative)

These are CO specification values. They are hardcoded and MUST NOT be made configurable:

| Utilization | Level           | Meaning                                      |
| ----------- | --------------- | -------------------------------------------- |
| < 70%       | `AUTO_APPROVED` | Action proceeds without human review         |
| 70-89%      | `FLAGGED`       | Action proceeds but is flagged for awareness |
| 90-99%      | `HELD`          | Action is held for human approval            |
| >= 100%     | `BLOCKED`       | Action is rejected outright                  |

Non-finite values (NaN, Inf) map to BLOCKED.

### Gradient Source Consolidation

`trust/gradient.py` is the single authoritative source for gradient thresholds and level definitions. `core/constraint.py` imports from it. There are NOT two independent implementations.

## Temporal Auto-Tracking

`ConstraintEnforcer` records its start time on initialization. On every `evaluate()` call, it computes `elapsed_minutes` from the wall clock automatically. No manual elapsed time tracking needed by callers.

## Financial Spend Accumulation

When `context` contains a `cost` key, the enforcer adds it to `current_spend` automatically. The projected spend (current + action cost) is used for gradient evaluation.

## DB Persistence

When `session_id` is set on the ConstraintEnforcer, every evaluation is persisted to the `ConstraintEvent` table via `db_ops.db_create()`. When `session_id` is empty/None, events are tracked in-memory only.

## Enforcement Middleware

`api/middleware.py` provides `enforce_constraints()` for pre-handler constraint evaluation:

```python
result = enforce_constraints(enforcer, held_manager, session_id, action="write", resource="/src/main.py")
if result is not None:
    return result  # BLOCKED (403) or HELD (202)
# Proceed with handler logic
```

## HeldActionManager

When an evaluation returns `HELD`, the action must wait for human approval.

```python
from praxis.core.constraint import HeldActionManager

manager = HeldActionManager(use_db=True)  # Persists to HeldAction table

# Create a held action
held = manager.hold(session_id, action, resource, verdict)

# List pending actions
pending = manager.get_pending(session_id=session_id)

# Human approves or denies
held = manager.approve(held.held_id, approved_by="supervisor")
held = manager.deny(held.held_id, denied_by="supervisor")

# Already-resolved actions raise ValueError
```

## Constraint Tightening

Constraints can only be tightened, never loosened. `SessionManager.update_constraints()` checks all 5 dimensions. Same invariant is enforced in `DelegationRecord` creation.

## Constraint Templates

Three built-in templates in `SessionManager`:

| Template   | max_spend | max_duration | allowed_actions             |
| ---------- | --------- | ------------ | --------------------------- |
| strict     | $10       | 30 min       | read only                   |
| moderate   | $100      | 120 min      | read, write, execute        |
| permissive | $1000     | 480 min      | all including delete/deploy |

Domain-specific templates override these via `DomainLoader.get_constraint_template(domain, template)`.
