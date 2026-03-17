# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""
DataFlow model definitions for the Praxis persistence layer.

All five core models are defined here as plain annotated classes.
They are registered with a DataFlow instance via `register_models(db)`,
which is called lazily from `get_db()` on first access.

IMPORTANT:
- Primary key MUST be `id: str` — you provide the UUID value.
- DO NOT define `created_at` or `updated_at` — DataFlow auto-manages these.
"""

from typing import Optional


class Session:
    """A CO collaboration session with persistent identity.

    Sessions track human-AI collaboration workflows with trust state,
    constraint envelopes, and domain context.
    """

    id: str  # UUID4 session_id
    workspace_id: str
    domain: str  # coc|coe|cog|cor|cocomp|cof
    state: str = "creating"  # creating|active|paused|archived
    genesis_id: Optional[str] = None
    constraint_envelope: Optional[str] = None
    session_metadata: Optional[str] = None
    ended_at: Optional[str] = None

    __indexes__ = [
        {"name": "idx_session_workspace", "fields": ["workspace_id"]},
        {"name": "idx_session_state", "fields": ["state"]},
        {"name": "idx_session_domain", "fields": ["domain"]},
    ]


class DeliberationRecord:
    """A record of human-AI deliberation with cryptographic integrity.

    Captures decisions, observations, escalations, and interventions
    with reasoning traces and hash chains for tamper evidence.
    """

    id: str  # UUID4 record_id
    session_id: str
    record_type: str  # decision|observation|escalation|intervention
    content: Optional[str] = None
    reasoning_trace: Optional[str] = None
    reasoning_hash: Optional[str] = None
    parent_record_id: Optional[str] = None
    anchor_id: Optional[str] = None
    actor: str = "human"  # human|ai|system
    confidence: Optional[float] = None

    __indexes__ = [
        {"name": "idx_delib_session", "fields": ["session_id"]},
        {"name": "idx_delib_type", "fields": ["record_type"]},
        {"name": "idx_delib_actor", "fields": ["actor"]},
    ]


class ConstraintEvent:
    """A constraint enforcement event from the trust layer.

    Tracks enforcement of the five CARE constraint dimensions:
    Financial, Operational, Temporal, Data Access, Communication.
    """

    id: str  # UUID4 event_id
    session_id: str
    action: str
    resource: Optional[str] = None
    dimension: str = "operational"  # financial|operational|temporal|data_access|communication
    gradient_result: str = "auto_approved"  # auto_approved|flagged|held|blocked
    utilization: float = 0.0
    resolved_by: Optional[str] = None
    resolution: Optional[str] = None
    resolved_at: Optional[str] = None

    __indexes__ = [
        {"name": "idx_constraint_session", "fields": ["session_id"]},
        {"name": "idx_constraint_dimension", "fields": ["dimension"]},
        {"name": "idx_constraint_gradient", "fields": ["gradient_result"]},
    ]


class TrustChainEntry:
    """An entry in the EATP trust chain.

    Records the cryptographic trust chain: genesis, delegation,
    attestation, anchor, and revocation events with signatures.
    """

    id: str  # UUID4 entry_id
    session_id: str
    entry_type: str  # genesis|delegation|attestation|anchor|revocation
    payload: Optional[str] = None
    signature: Optional[str] = None
    signer_key_id: Optional[str] = None
    parent_hash: Optional[str] = None
    content_hash: Optional[str] = None
    verified: bool = False

    __indexes__ = [
        {"name": "idx_trust_session", "fields": ["session_id"]},
        {"name": "idx_trust_type", "fields": ["entry_type"]},
        {"name": "idx_trust_signer", "fields": ["signer_key_id"]},
    ]


class Workspace:
    """A Praxis workspace with domain and constraint configuration.

    Workspaces group sessions and provide default constraint templates
    and genesis key bindings for trust chain initialization.
    """

    id: str  # UUID4 workspace_id
    name: str
    domain: str = "coc"
    constraint_template: str = "moderate"
    constraint_config: Optional[str] = None
    genesis_key_id: Optional[str] = None

    __indexes__ = [
        {"name": "idx_workspace_name", "fields": ["name"]},
        {"name": "idx_workspace_domain", "fields": ["domain"]},
    ]


class HeldAction:
    """A held action awaiting human approval.

    Created when the constraint enforcer returns a HELD verdict.
    Resolved when a human approves or denies the action.
    """

    id: str  # UUID4 held_id
    session_id: str
    action: str
    resource: Optional[str] = None
    dimension: str = "operational"
    verdict_payload: Optional[str] = None  # Serialized ConstraintVerdict
    resolved: bool = False
    resolved_by: Optional[str] = None
    resolution: Optional[str] = None  # "approved" or "denied"
    resolved_at: Optional[str] = None

    __indexes__ = [
        {"name": "idx_held_session", "fields": ["session_id"]},
        {"name": "idx_held_resolved", "fields": ["resolved"]},
    ]


# ---------------------------------------------------------------------------
# CO Layer 5: Learning Pipeline models
# ---------------------------------------------------------------------------


class LearningObservation:
    """An observation captured by the CO Layer 5 learning pipeline.

    Observations are raw data points collected from session activity:
    constraint evaluations, held action resolutions, session lifecycle
    events, and other observable targets declared in the domain YAML.
    """

    id: str  # UUID4 observation_id
    session_id: str
    domain: str
    target: str  # matches domain YAML observation_targets
    content: Optional[str] = None

    __indexes__ = [
        {"name": "idx_learning_obs_session", "fields": ["session_id"]},
        {"name": "idx_learning_obs_domain", "fields": ["domain"]},
        {"name": "idx_learning_obs_target", "fields": ["target"]},
    ]


class LearningPattern:
    """A recurring pattern detected from accumulated observations.

    Patterns are identified by the analysis engine and carry a confidence
    score based on sample size and consistency of evidence.
    """

    id: str  # UUID4 pattern_id
    domain: str
    pattern_type: (
        str  # unused_constraint, rubber_stamp, boundary_pressure, always_approved, never_reached
    )
    description: str = ""
    confidence: float = 0.0
    evidence: Optional[str] = None  # {"observation_ids": [...]}

    __indexes__ = [
        {"name": "idx_learning_pat_domain", "fields": ["domain"]},
        {"name": "idx_learning_pat_type", "fields": ["pattern_type"]},
    ]


class User:
    """A Praxis user authenticated via Firebase SSO.

    Users are auto-created on first login. The id is the Firebase UID.
    Provider indicates the SSO method (github.com, google.com).
    """

    id: str  # Firebase UID
    email: str
    display_name: str = ""
    photo_url: Optional[str] = None
    provider: str = ""  # github.com, google.com
    role: str = "practitioner"  # practitioner, supervisor, auditor, admin
    last_login_at: Optional[str] = None

    __indexes__ = [
        {"name": "idx_user_email", "fields": ["email"]},
        {"name": "idx_user_provider", "fields": ["provider"]},
        {"name": "idx_user_role", "fields": ["role"]},
    ]


class LearningEvolutionProposal:
    """A proposed change to domain configuration based on observed patterns.

    Proposals are NEVER auto-applied. They require explicit human approval
    before any domain configuration change takes effect. When approved,
    a YAML diff is generated for the human to review and manually apply.
    """

    id: str  # UUID4 proposal_id
    pattern_id: str
    domain: str
    proposal_type: str  # tighten, loosen, remove, add
    target: str = ""  # what to change (e.g., "financial.max_spend")
    current_value: Optional[str] = None  # wrapped in dict for JSON storage
    proposed_value: Optional[str] = None  # wrapped in dict for JSON storage
    rationale: str = ""
    status: str = "pending"  # pending, approved, rejected
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None

    __indexes__ = [
        {"name": "idx_learning_prop_domain", "fields": ["domain"]},
        {"name": "idx_learning_prop_status", "fields": ["status"]},
        {"name": "idx_learning_prop_pattern", "fields": ["pattern_id"]},
    ]


# All model classes — used by register_models()
ALL_MODELS = [
    Session,
    DeliberationRecord,
    ConstraintEvent,
    TrustChainEntry,
    Workspace,
    HeldAction,
    LearningObservation,
    LearningPattern,
    LearningEvolutionProposal,
    User,
]
