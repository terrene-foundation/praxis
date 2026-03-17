# Praxis Domain Engine

## Overview

Praxis hosts domain-specific CO applications. Each domain is a YAML configuration layer on top of the runtime -- constraint templates, workflow phases, capture rules, knowledge classification, anti-amnesia rules, and domain procedural rules. No code execution in domain configs.

## Key Files

| File                        | Purpose                                                                       |
| --------------------------- | ----------------------------------------------------------------------------- |
| `domains/loader.py`         | `DomainLoader` -- discover, load, validate, cache; knowledge + export helpers |
| `domains/schema.py`         | JSON Schema definitions for domain YAML validation                            |
| `domains/{name}/domain.yml` | Domain configuration file                                                     |
| `core/anti_amnesia.py`      | `AntiAmnesiaInjector` -- load and filter anti-amnesia rules                   |
| `core/rules.py`             | `DomainRuleEngine` -- evaluate procedural rules against records               |

## The Six Domains

| Domain   | Name              | Description                         |
| -------- | ----------------- | ----------------------------------- |
| `coc`    | CO for Codegen    | Software development workflows      |
| `coe`    | CO for Education  | Learning and assessment workflows   |
| `cog`    | CO for Governance | Organizational governance workflows |
| `cor`    | CO for Research   | Research collaboration workflows    |
| `cocomp` | CO for Compliance | Compliance verification workflows   |
| `cof`    | CO for Finance    | Financial operations workflows      |

## Extended YAML Schema

Every `domain.yml` must have: `name`, `display_name`, `description`, `version`, `constraint_templates`, `phases`, `capture`.

Optional sections:

### Knowledge Classification

```yaml
knowledge:
  classification:
    - type: institutional # institutional or generic
      content: "Always run tests before committing"
      priority: P0 # P0, P1, P2
    - type: generic
      content: "Follow Python PEP 8"
      priority: P2
```

- `get_institutional_knowledge(domain)` -- returns only institutional entries
- `get_knowledge_for_phase(domain, phase)` -- progressive disclosure: early phases get P0/P1 only, later phases get all

### Anti-Amnesia Rules

```yaml
anti_amnesia:
  - priority: P0
    rule: "Never skip the test suite"
    trigger: always # always, on_write, on_deploy, on_commit, on_session_start
```

Loaded by `AntiAmnesiaInjector`. Filtered by trigger, sorted by priority. `format_for_context()` produces AI context text.

### Domain Procedural Rules

```yaml
rules:
  - name: require_alternatives
    type: alternatives_present
    params:
      applies_to: ["scope", "architecture"]
  - name: rationale_depth
    type: rationale_depth
    params:
      min_words: 15
  - name: require_citations
    type: citation_required
    params:
      applies_to: ["methodology"]
  - name: require_precedent
    type: precedent_required
```

Four rule types: `alternatives_present`, `rationale_depth`, `citation_required`, `precedent_required`. Rules produce advisory warnings (not blocks).

### Constraint Rationale

When updating constraints via API, a `rationale` field documents why the change was made, creating an audit trail.

## Domain Export/Import/Diff

CLI commands:

- `praxis domain export <name>` -- packages domain as ZIP
- `praxis domain import <path>` -- imports domain from ZIP, validates schema
- `praxis domain diff <domain1> <domain2>` -- compares templates, phases, capture rules, decision types

## DomainLoader API

```python
from praxis.domains.loader import DomainLoader

loader = DomainLoader()
domains = loader.list_domains()
config = loader.load_domain("coc")         # DomainConfig (frozen)
template = loader.get_constraint_template("coc", "moderate")
errors = loader.validate_domain("coc")     # [] if valid
loader.reload("coc")                        # clear cache
```
