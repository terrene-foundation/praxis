# Praxis Learning Pipeline

## Overview

CO Layer 5: Continuous Learning. The observe-analyze-propose-formalize pipeline allows domain configurations to evolve based on observed session patterns. All proposals require explicit human approval.

## Key Files

| File                         | Purpose                                                 |
| ---------------------------- | ------------------------------------------------------- |
| `core/learning.py`           | `LearningPipeline` -- four-stage pipeline               |
| `core/learning_observers.py` | Observer functions -- wire session activity to pipeline |
| `persistence/models.py`      | 3 DataFlow models for pipeline data                     |

## Four Stages

### 1. Observe

Record observations for targets declared in domain YAML `observation_targets`. Three built-in observers:

- `observe_constraint_evaluation()` -- after every ConstraintEnforcer.evaluate()
- `observe_held_action_resolution()` -- after held action approve/deny
- `observe_session_lifecycle()` -- on session create/end/pause/resume

Observers catch ALL exceptions silently -- observation is non-critical.

### 2. Analyze

Five pattern detectors with minimum sample thresholds:

| Detector            | Detects                                           | Min Samples |
| ------------------- | ------------------------------------------------- | ----------- |
| `unused_constraint` | Dimensions with 0% utilization across evaluations | 5           |
| `rubber_stamp`      | >95% approval rate, <5s avg review time           | 5           |
| `boundary_pressure` | >50% of evaluations at >80% utilization           | 10          |
| `always_approved`   | Action type 100% AUTO_APPROVED                    | 10          |
| `never_reached`     | Template exists but never used                    | 3           |

### 3. Propose

Map patterns to proposals (confidence >= 0.3 required):

- `unused_constraint` -> `remove`
- `rubber_stamp` -> `loosen`
- `boundary_pressure` -> `loosen`
- `always_approved` -> `tighten`
- `never_reached` -> `remove`

### 4. Formalize

Approve/reject proposals. Approval generates a YAML diff recommendation (NOT auto-applied).

## Human Approval Gate

Nothing is auto-applied. All proposals start as "pending". `formalize()` generates a diff for humans to manually apply.

## Persistence

Three models via `db_ops.py`:

- `LearningObservation` -- raw data points
- `LearningPattern` -- detected patterns with confidence scores
- `LearningEvolutionProposal` -- proposed changes with status tracking
