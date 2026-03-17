# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""
JSON Schema definitions for domain YAML validation.

The schema defines the required structure of domain.yml files and constraint
template YAML files. All six CO domains must validate against these schemas.
"""

from __future__ import annotations

# The five CO constraint dimensions — canonical names and order.
# See CLAUDE.md: "Financial, Operational, Temporal, Data Access, Communication"
CONSTRAINT_DIMENSIONS = ("financial", "operational", "temporal", "data_access", "communication")

# JSON Schema for the optional rationale block within a constraint template.
# Each key must match one of the five CO constraint dimensions; values are
# human-readable strings explaining WHY that dimension is configured as it is.
RATIONALE_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "financial": {"type": "string", "minLength": 1},
        "operational": {"type": "string", "minLength": 1},
        "temporal": {"type": "string", "minLength": 1},
        "data_access": {"type": "string", "minLength": 1},
        "communication": {"type": "string", "minLength": 1},
    },
    "additionalProperties": False,
}

# JSON Schema for a single constraint template (the five dimensions).
CONSTRAINT_TEMPLATE_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "financial": {
            "type": "object",
            "properties": {
                "max_spend": {"type": "number", "minimum": 0},
            },
            "required": ["max_spend"],
        },
        "operational": {
            "type": "object",
            "properties": {
                "allowed_actions": {"type": "array", "items": {"type": "string"}},
                "max_actions_per_hour": {"type": "integer", "minimum": 1},
            },
            "required": ["allowed_actions", "max_actions_per_hour"],
        },
        "temporal": {
            "type": "object",
            "properties": {
                "max_duration_minutes": {"type": "integer", "minimum": 1},
            },
            "required": ["max_duration_minutes"],
        },
        "data_access": {
            "type": "object",
            "properties": {
                "allowed_paths": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["allowed_paths"],
        },
        "communication": {
            "type": "object",
            "properties": {
                "allowed_channels": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["allowed_channels"],
        },
        "rationale": RATIONALE_SCHEMA,
    },
    "required": list(CONSTRAINT_DIMENSIONS),
    "additionalProperties": False,
}

# JSON Schema for a single workflow phase.
PHASE_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "minLength": 1},
        "display_name": {"type": "string", "minLength": 1},
        "description": {"type": "string", "minLength": 1},
        "approval_gate": {"type": "boolean"},
    },
    "required": ["name", "display_name", "description", "approval_gate"],
}

# JSON Schema for the capture rules section.
CAPTURE_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "auto_capture": {"type": "array", "items": {"type": "string"}, "minItems": 1},
        "decision_types": {"type": "array", "items": {"type": "string"}, "minItems": 1},
        "observation_targets": {"type": "array", "items": {"type": "string"}, "minItems": 1},
    },
    "required": ["auto_capture", "decision_types", "observation_targets"],
}

# JSON Schema for a single anti-amnesia rule.
ANTI_AMNESIA_RULE_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "priority": {"type": "string", "enum": ["P0", "P1", "P2"]},
        "rule": {"type": "string", "minLength": 1},
        "trigger": {
            "type": "string",
            "enum": ["always", "on_write", "on_deploy", "on_commit", "on_session_start"],
        },
    },
    "required": ["priority", "rule", "trigger"],
    "additionalProperties": False,
}

# JSON Schema for the anti-amnesia section.
ANTI_AMNESIA_SCHEMA: dict = {
    "type": "array",
    "items": ANTI_AMNESIA_RULE_SCHEMA,
    "minItems": 1,
}

# Valid knowledge priority levels (P0 = critical, P3 = supplementary)
KNOWLEDGE_PRIORITIES = ("P0", "P1", "P2", "P3")

# Valid knowledge classification types
KNOWLEDGE_TYPES = ("institutional", "generic")

# JSON Schema for a single knowledge entry.
KNOWLEDGE_ENTRY_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "type": {"type": "string", "enum": list(KNOWLEDGE_TYPES)},
        "content": {"type": "string", "minLength": 1},
        "priority": {"type": "string", "enum": list(KNOWLEDGE_PRIORITIES)},
    },
    "required": ["type", "content", "priority"],
    "additionalProperties": False,
}

# JSON Schema for the knowledge section.
KNOWLEDGE_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "classification": {
            "type": "array",
            "items": KNOWLEDGE_ENTRY_SCHEMA,
            "minItems": 1,
        },
    },
    "required": ["classification"],
    "additionalProperties": False,
}

# Valid domain rule types.
DOMAIN_RULE_TYPES = (
    "alternatives_present",
    "rationale_depth",
    "citation_required",
    "precedent_required",
)

# JSON Schema for a single domain rule.
DOMAIN_RULE_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "minLength": 1},
        "type": {"type": "string", "enum": list(DOMAIN_RULE_TYPES)},
        "description": {"type": "string", "minLength": 1},
        "params": {"type": "object"},
    },
    "required": ["name", "type", "description"],
    "additionalProperties": False,
}

# JSON Schema for the rules section.
RULES_SCHEMA: dict = {
    "type": "array",
    "items": DOMAIN_RULE_SCHEMA,
    "minItems": 1,
}

# JSON Schema for the top-level domain.yml file.
DOMAIN_SCHEMA: dict = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "https://terrene.dev/praxis/schemas/domain.json",
    "title": "Praxis CO Domain Configuration",
    "description": "Schema for domain.yml files in each CO domain directory.",
    "type": "object",
    "properties": {
        "name": {"type": "string", "minLength": 1, "maxLength": 50},
        "display_name": {"type": "string", "minLength": 1, "maxLength": 200},
        "description": {"type": "string", "minLength": 1, "maxLength": 2000},
        "version": {"type": "string", "pattern": r"^\d+\.\d+$"},
        "constraint_templates": {
            "type": "object",
            "minProperties": 1,
            "additionalProperties": CONSTRAINT_TEMPLATE_SCHEMA,
        },
        "phases": {
            "type": "array",
            "items": PHASE_SCHEMA,
            "minItems": 1,
        },
        "capture": CAPTURE_SCHEMA,
        "knowledge": KNOWLEDGE_SCHEMA,
        "anti_amnesia": ANTI_AMNESIA_SCHEMA,
        "rules": RULES_SCHEMA,
    },
    "required": [
        "name",
        "display_name",
        "description",
        "version",
        "constraint_templates",
        "phases",
        "capture",
    ],
}
