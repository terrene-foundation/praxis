# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""
CO Layer 5: Continuous Learning Pipeline.

Implements the observe-analyze-propose-formalize cycle that allows
domain configurations to evolve based on observed session patterns.

This is the most critical CO conformance feature: without it,
knowledge does not compound across sessions. The pipeline captures
observations during sessions, detects recurring patterns, generates
evolution proposals, and gates all changes through human approval.

Pattern detectors:
    - unused_constraint: dimension never triggered across N sessions
    - rubber_stamp: held actions approved >95% with <5s review time
    - boundary_pressure: actions clustering near constraint boundaries
    - always_approved: action type always AUTO_APPROVED (constraint too loose)
    - never_reached: constraint template that has never been used

All proposals require explicit human approval. Nothing is auto-applied.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


def _now_utc_iso() -> str:
    """Return current UTC time as ISO 8601 string with Z suffix."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


@dataclass
class Observation:
    """A single observation from session monitoring."""

    observation_id: str
    session_id: str
    domain: str
    target: str  # matches domain YAML observation_targets
    content: dict
    created_at: str


@dataclass
class Pattern:
    """A recurring pattern detected from observations."""

    pattern_id: str
    pattern_type: str  # e.g., "unused_constraint", "rubber_stamp", "boundary_pressure"
    description: str
    confidence: float  # 0.0 to 1.0
    evidence: list[str]  # observation_ids that support this pattern
    domain: str
    created_at: str


@dataclass
class EvolutionProposal:
    """A proposed change to domain configuration based on observed patterns."""

    proposal_id: str
    pattern_id: str
    domain: str
    proposal_type: str  # "tighten", "loosen", "remove", "add"
    target: str  # what to change (e.g., "financial.max_spend")
    current_value: Any
    proposed_value: Any
    rationale: str
    status: str = "pending"  # pending, approved, rejected
    reviewed_by: str | None = None
    reviewed_at: str | None = None


# ---------------------------------------------------------------------------
# Valid pattern types and observation targets
# ---------------------------------------------------------------------------

VALID_PATTERN_TYPES = frozenset(
    {
        "unused_constraint",
        "rubber_stamp",
        "boundary_pressure",
        "always_approved",
        "never_reached",
    }
)

# Minimum number of observations required before pattern detection
# triggers for each type. These thresholds ensure statistical relevance.
_MIN_SAMPLES = {
    "unused_constraint": 5,
    "rubber_stamp": 5,
    "boundary_pressure": 10,
    "always_approved": 10,
    "never_reached": 3,
}


# ---------------------------------------------------------------------------
# LearningPipeline
# ---------------------------------------------------------------------------


class LearningPipeline:
    """The observe-analyze-propose-formalize pipeline for CO Layer 5.

    Captures observations from session activity, detects patterns across
    accumulated data, generates evolution proposals from those patterns,
    and applies approved proposals as domain configuration diffs.

    All data is persisted to the DataFlow database via the Learning*
    persistence models.

    Args:
        domain: The CO domain this pipeline operates on (e.g., "coc").
        session_id: Optional session scope. When set, observations are
            attributed to this session. When None, operates across all
            sessions for the domain.
    """

    def __init__(self, domain: str, session_id: str | None = None) -> None:
        self.domain = domain
        self.session_id = session_id
        self._valid_targets: list[str] | None = None

        # Load valid observation targets from domain YAML
        try:
            from praxis.domains.loader import DomainLoader

            loader = DomainLoader()
            config = loader.load_domain(domain)
            capture = config.capture or {}
            self._valid_targets = capture.get("observation_targets")
        except Exception as exc:
            logger.debug(
                "Could not load observation targets for domain '%s': %s",
                domain,
                exc,
            )

    # -- Observe ------------------------------------------------------------

    def observe(self, target: str, content: dict) -> Observation:
        """Record an observation.

        Only records observations for targets declared in the domain
        YAML's ``observation_targets`` list. If no targets are declared,
        all targets are accepted.

        Args:
            target: The observation target (e.g., "constraint_evaluation",
                "held_action_resolution", "session_lifecycle").
            content: Arbitrary observation data dict.

        Returns:
            The created Observation.

        Raises:
            ValueError: If the target is not in the domain's observation_targets.
            ValueError: If no session_id was set and content has no session_id.
        """
        # Validate target against domain YAML
        if self._valid_targets is not None and target not in self._valid_targets:
            raise ValueError(
                f"Observation target '{target}' is not declared in domain "
                f"'{self.domain}' observation_targets. "
                f"Valid targets: {self._valid_targets}"
            )

        session_id = self.session_id or content.get("session_id", "")
        if not session_id:
            raise ValueError(
                "Cannot record observation without a session_id. "
                "Either set session_id on the pipeline or include it in content."
            )

        obs_id = str(uuid.uuid4())
        now = _now_utc_iso()

        observation = Observation(
            observation_id=obs_id,
            session_id=session_id,
            domain=self.domain,
            target=target,
            content=content,
            created_at=now,
        )

        # Persist to database
        from praxis.persistence.db_ops import db_create

        db_create(
            "LearningObservation",
            {
                "id": obs_id,
                "session_id": session_id,
                "domain": self.domain,
                "target": target,
                "content": content,
            },
        )

        logger.info(
            "Recorded observation %s (target=%s, domain=%s, session=%s)",
            obs_id,
            target,
            self.domain,
            session_id,
        )
        return observation

    # -- Analyze ------------------------------------------------------------

    def analyze(self) -> list[Pattern]:
        """Analyze accumulated observations for patterns.

        Runs all five pattern detectors against the observation database
        for this domain and returns any detected patterns.

        Returns:
            List of Pattern instances detected.
        """
        from praxis.persistence.db_ops import db_list

        # Load all observations for this domain
        observations = db_list(
            "LearningObservation",
            filter={"domain": self.domain},
            limit=10000,
        )

        if not observations:
            logger.info("No observations to analyze for domain '%s'", self.domain)
            return []

        patterns: list[Pattern] = []

        # Run each detector
        patterns.extend(self._detect_unused_constraint(observations))
        patterns.extend(self._detect_rubber_stamp(observations))
        patterns.extend(self._detect_boundary_pressure(observations))
        patterns.extend(self._detect_always_approved(observations))
        patterns.extend(self._detect_never_reached(observations))

        # Persist detected patterns
        for pattern in patterns:
            from praxis.persistence.db_ops import db_create

            db_create(
                "LearningPattern",
                {
                    "id": pattern.pattern_id,
                    "domain": self.domain,
                    "pattern_type": pattern.pattern_type,
                    "description": pattern.description,
                    "confidence": pattern.confidence,
                    "evidence": {"observation_ids": pattern.evidence},
                },
            )

        logger.info(
            "Analysis found %d pattern(s) for domain '%s'",
            len(patterns),
            self.domain,
        )
        return patterns

    def _detect_unused_constraint(self, observations: list[dict]) -> list[Pattern]:
        """Detect constraint dimensions that have never been triggered.

        Looks for dimensions where utilization is always 0% across
        constraint_evaluation observations.
        """
        constraint_obs = [o for o in observations if o.get("target") == "constraint_evaluation"]
        if len(constraint_obs) < _MIN_SAMPLES["unused_constraint"]:
            return []

        # Track which dimensions have been triggered (utilization > 0)
        dimension_triggered: dict[str, bool] = {
            "financial": False,
            "operational": False,
            "temporal": False,
            "data_access": False,
            "communication": False,
        }
        dimension_obs_ids: dict[str, list[str]] = {d: [] for d in dimension_triggered}

        for obs in constraint_obs:
            content = obs.get("content") or {}
            dim = content.get("dimension", "")
            util = content.get("utilization", 0.0)
            obs_id = obs.get("id", "")

            if dim in dimension_triggered:
                dimension_obs_ids[dim].append(obs_id)
                if isinstance(util, (int, float)) and util > 0.0:
                    dimension_triggered[dim] = True

        patterns: list[Pattern] = []
        for dim, triggered in dimension_triggered.items():
            if not triggered and len(dimension_obs_ids[dim]) >= _MIN_SAMPLES["unused_constraint"]:
                n = len(dimension_obs_ids[dim])
                confidence = min(1.0, n / 20.0)  # Scales up with more evidence
                patterns.append(
                    Pattern(
                        pattern_id=str(uuid.uuid4()),
                        pattern_type="unused_constraint",
                        description=(
                            f"The '{dim}' constraint dimension has never been "
                            f"triggered (0% utilization) across {n} evaluations."
                        ),
                        confidence=confidence,
                        evidence=dimension_obs_ids[dim][:50],  # Cap evidence list
                        domain=self.domain,
                        created_at=_now_utc_iso(),
                    )
                )

        return patterns

    def _detect_rubber_stamp(self, observations: list[dict]) -> list[Pattern]:
        """Detect held actions that are routinely approved without review.

        Looks for >95% approval rate with <5 second average review time.
        """
        held_obs = [o for o in observations if o.get("target") == "held_action_resolution"]
        if len(held_obs) < _MIN_SAMPLES["rubber_stamp"]:
            return []

        approved_count = 0
        total_count = len(held_obs)
        total_review_seconds = 0.0
        obs_ids: list[str] = []

        for obs in held_obs:
            content = obs.get("content") or {}
            obs_ids.append(obs.get("id", ""))
            if content.get("resolution") == "approved":
                approved_count += 1
            review_time = content.get("review_time_seconds", 0.0)
            if isinstance(review_time, (int, float)):
                total_review_seconds += review_time

        if total_count == 0:
            return []

        approval_rate = approved_count / total_count
        avg_review_time = total_review_seconds / total_count

        patterns: list[Pattern] = []
        if approval_rate > 0.95 and avg_review_time < 5.0:
            confidence = min(1.0, total_count / 20.0)
            patterns.append(
                Pattern(
                    pattern_id=str(uuid.uuid4()),
                    pattern_type="rubber_stamp",
                    description=(
                        f"Held actions are approved {approval_rate:.0%} of the time "
                        f"with an average review time of {avg_review_time:.1f}s "
                        f"(across {total_count} resolutions). This suggests the "
                        f"hold threshold may be too aggressive."
                    ),
                    confidence=confidence,
                    evidence=obs_ids[:50],
                    domain=self.domain,
                    created_at=_now_utc_iso(),
                )
            )

        return patterns

    def _detect_boundary_pressure(self, observations: list[dict]) -> list[Pattern]:
        """Detect actions clustering near constraint boundaries.

        Looks for repeated high utilization (>80%) on a dimension.
        """
        constraint_obs = [o for o in observations if o.get("target") == "constraint_evaluation"]
        if len(constraint_obs) < _MIN_SAMPLES["boundary_pressure"]:
            return []

        # Track high-utilization counts per dimension
        dimension_high: dict[str, int] = {}
        dimension_total: dict[str, int] = {}
        dimension_obs_ids: dict[str, list[str]] = {}

        for obs in constraint_obs:
            content = obs.get("content") or {}
            dim = content.get("dimension", "")
            util = content.get("utilization", 0.0)
            obs_id = obs.get("id", "")

            if dim:
                dimension_total[dim] = dimension_total.get(dim, 0) + 1
                if dim not in dimension_obs_ids:
                    dimension_obs_ids[dim] = []
                dimension_obs_ids[dim].append(obs_id)

                if isinstance(util, (int, float)) and util > 0.8:
                    dimension_high[dim] = dimension_high.get(dim, 0) + 1

        patterns: list[Pattern] = []
        for dim, high_count in dimension_high.items():
            total = dimension_total.get(dim, 0)
            if total < _MIN_SAMPLES["boundary_pressure"]:
                continue
            pressure_rate = high_count / total if total > 0 else 0.0
            if pressure_rate > 0.5:  # >50% of evaluations are near the boundary
                confidence = min(1.0, total / 30.0) * pressure_rate
                patterns.append(
                    Pattern(
                        pattern_id=str(uuid.uuid4()),
                        pattern_type="boundary_pressure",
                        description=(
                            f"The '{dim}' dimension shows boundary pressure: "
                            f"{high_count}/{total} evaluations ({pressure_rate:.0%}) "
                            f"have >80% utilization. The limit may be too tight."
                        ),
                        confidence=confidence,
                        evidence=dimension_obs_ids.get(dim, [])[:50],
                        domain=self.domain,
                        created_at=_now_utc_iso(),
                    )
                )

        return patterns

    def _detect_always_approved(self, observations: list[dict]) -> list[Pattern]:
        """Detect action types that are always AUTO_APPROVED.

        Groups constraint evaluations by action type and flags any that
        are 100% auto_approved — may indicate the constraint is too loose.
        """
        constraint_obs = [o for o in observations if o.get("target") == "constraint_evaluation"]
        if len(constraint_obs) < _MIN_SAMPLES["always_approved"]:
            return []

        # Track verdicts per action type
        action_verdicts: dict[str, dict[str, int]] = {}
        action_obs_ids: dict[str, list[str]] = {}

        for obs in constraint_obs:
            content = obs.get("content") or {}
            action = content.get("action", "")
            verdict = content.get("verdict", "auto_approved")
            obs_id = obs.get("id", "")

            if action:
                if action not in action_verdicts:
                    action_verdicts[action] = {}
                    action_obs_ids[action] = []
                action_verdicts[action][verdict] = action_verdicts[action].get(verdict, 0) + 1
                action_obs_ids[action].append(obs_id)

        patterns: list[Pattern] = []
        for action, verdicts in action_verdicts.items():
            total = sum(verdicts.values())
            if total < _MIN_SAMPLES["always_approved"]:
                continue
            auto_count = verdicts.get("auto_approved", 0)
            if auto_count == total:
                confidence = min(1.0, total / 20.0)
                patterns.append(
                    Pattern(
                        pattern_id=str(uuid.uuid4()),
                        pattern_type="always_approved",
                        description=(
                            f"Action '{action}' has been AUTO_APPROVED in all "
                            f"{total} evaluations. This may indicate the "
                            f"constraint is appropriately configured, or that "
                            f"the threshold is too loose for this action type."
                        ),
                        confidence=confidence,
                        evidence=action_obs_ids.get(action, [])[:50],
                        domain=self.domain,
                        created_at=_now_utc_iso(),
                    )
                )

        return patterns

    def _detect_never_reached(self, observations: list[dict]) -> list[Pattern]:
        """Detect constraint templates that exist but have never been used.

        Compares available templates from domain YAML against session
        lifecycle observations to find templates with zero usage.
        """
        # Load available templates from domain YAML
        try:
            from praxis.domains.loader import DomainLoader

            loader = DomainLoader()
            config = loader.load_domain(self.domain)
            available_templates = set(config.constraint_templates.keys())
        except Exception:
            return []

        # Find which templates have been used
        session_obs = [o for o in observations if o.get("target") == "session_lifecycle"]
        if len(session_obs) < _MIN_SAMPLES["never_reached"]:
            return []

        used_templates: set[str] = set()
        obs_ids: list[str] = []
        for obs in session_obs:
            content = obs.get("content") or {}
            template = content.get("constraint_template", "")
            obs_ids.append(obs.get("id", ""))
            if template:
                used_templates.add(template)

        patterns: list[Pattern] = []
        never_used = available_templates - used_templates
        if never_used:
            confidence = min(1.0, len(session_obs) / 10.0)
            for template in sorted(never_used):
                patterns.append(
                    Pattern(
                        pattern_id=str(uuid.uuid4()),
                        pattern_type="never_reached",
                        description=(
                            f"Constraint template '{template}' exists in domain "
                            f"'{self.domain}' but has never been used across "
                            f"{len(session_obs)} observed sessions."
                        ),
                        confidence=confidence,
                        evidence=obs_ids[:50],
                        domain=self.domain,
                        created_at=_now_utc_iso(),
                    )
                )

        return patterns

    # -- Propose ------------------------------------------------------------

    def propose(self, pattern: Pattern) -> EvolutionProposal | None:
        """Generate an evolution proposal from a detected pattern.

        Maps pattern types to proposal types:
        - unused_constraint -> "remove" (consider removing/lowering threshold)
        - rubber_stamp -> "loosen" (consider changing from HELD to FLAGGED)
        - boundary_pressure -> "loosen" (consider raising the limit)
        - always_approved -> may be "tighten" or no action needed
        - never_reached -> "remove" (consider removing the template)

        Returns None if the pattern does not warrant a proposal (e.g.,
        confidence is too low or the pattern is informational).

        Args:
            pattern: The detected pattern to generate a proposal from.

        Returns:
            EvolutionProposal or None.
        """
        if pattern.confidence < 0.3:
            logger.info(
                "Pattern %s has low confidence (%.2f), skipping proposal",
                pattern.pattern_id,
                pattern.confidence,
            )
            return None

        proposal = self._generate_proposal(pattern)
        if proposal is None:
            return None

        # Persist to database
        from praxis.persistence.db_ops import db_create

        db_create(
            "LearningEvolutionProposal",
            {
                "id": proposal.proposal_id,
                "pattern_id": proposal.pattern_id,
                "domain": proposal.domain,
                "proposal_type": proposal.proposal_type,
                "target": proposal.target,
                "current_value": {"value": proposal.current_value},
                "proposed_value": {"value": proposal.proposed_value},
                "rationale": proposal.rationale,
                "status": proposal.status,
            },
        )

        logger.info(
            "Created evolution proposal %s (type=%s, target=%s)",
            proposal.proposal_id,
            proposal.proposal_type,
            proposal.target,
        )
        return proposal

    def _generate_proposal(self, pattern: Pattern) -> EvolutionProposal | None:
        """Internal: map a pattern to a concrete proposal."""
        proposal_id = str(uuid.uuid4())

        if pattern.pattern_type == "unused_constraint":
            # Extract dimension from description
            dim = self._extract_dimension_from_description(pattern.description)
            return EvolutionProposal(
                proposal_id=proposal_id,
                pattern_id=pattern.pattern_id,
                domain=pattern.domain,
                proposal_type="remove",
                target=f"{dim}" if dim else "unknown_dimension",
                current_value="configured",
                proposed_value="consider removing or lowering threshold",
                rationale=(
                    f"The '{dim}' constraint dimension has never been triggered. "
                    f"Consider whether this dimension is relevant for this domain, "
                    f"or if the threshold should be lowered to make it active."
                ),
            )

        elif pattern.pattern_type == "rubber_stamp":
            return EvolutionProposal(
                proposal_id=proposal_id,
                pattern_id=pattern.pattern_id,
                domain=pattern.domain,
                proposal_type="loosen",
                target="held_action_threshold",
                current_value="held",
                proposed_value="flagged",
                rationale=(
                    "Held actions are routinely approved with minimal review. "
                    "Consider changing the threshold from HELD to FLAGGED for "
                    "this action type to reduce approval friction while still "
                    "maintaining visibility."
                ),
            )

        elif pattern.pattern_type == "boundary_pressure":
            dim = self._extract_dimension_from_description(pattern.description)
            return EvolutionProposal(
                proposal_id=proposal_id,
                pattern_id=pattern.pattern_id,
                domain=pattern.domain,
                proposal_type="loosen",
                target=f"{dim}" if dim else "unknown_dimension",
                current_value="current limit",
                proposed_value="consider raising the limit",
                rationale=(
                    f"Actions on the '{dim}' dimension are repeatedly clustering "
                    f"near the constraint boundary (>80% utilization). The limit "
                    f"may be too restrictive for normal workflow patterns. "
                    f"Consider raising it cautiously."
                ),
            )

        elif pattern.pattern_type == "always_approved":
            # Informational — may be working as intended
            return EvolutionProposal(
                proposal_id=proposal_id,
                pattern_id=pattern.pattern_id,
                domain=pattern.domain,
                proposal_type="tighten",
                target="always_approved_actions",
                current_value="always auto_approved",
                proposed_value="consider tightening if not intentional",
                rationale=(
                    "This action type is always AUTO_APPROVED. If this is "
                    "intentional (the action is low-risk), no change is needed. "
                    "If the action should receive more scrutiny, consider "
                    "tightening the constraint thresholds."
                ),
            )

        elif pattern.pattern_type == "never_reached":
            template_name = self._extract_template_from_description(pattern.description)
            return EvolutionProposal(
                proposal_id=proposal_id,
                pattern_id=pattern.pattern_id,
                domain=pattern.domain,
                proposal_type="remove",
                target=f"template:{template_name}" if template_name else "unknown_template",
                current_value="exists but unused",
                proposed_value="consider removing",
                rationale=(
                    f"Constraint template '{template_name}' has never been used. "
                    f"Consider removing it to simplify the domain configuration, "
                    f"or documenting when it should be used."
                ),
            )

        return None

    def _extract_dimension_from_description(self, description: str) -> str:
        """Extract a dimension name from a pattern description string."""
        for dim in ("financial", "operational", "temporal", "data_access", "communication"):
            if f"'{dim}'" in description:
                return dim
        return ""

    def _extract_template_from_description(self, description: str) -> str:
        """Extract a template name from a pattern description string."""
        # Pattern: "Constraint template 'xxx' exists..."
        if "template '" in description:
            start = description.index("template '") + len("template '")
            end = description.index("'", start)
            return description[start:end]
        return ""

    # -- Formalize ----------------------------------------------------------

    def formalize(self, proposal_id: str, approved_by: str) -> dict:
        """Apply an approved proposal — generates a domain YAML diff.

        Does NOT auto-apply the change. Returns a diff dict that the
        human must review and manually apply to the domain configuration.

        Args:
            proposal_id: The proposal to formalize.
            approved_by: Identity of the approver.

        Returns:
            Dict with proposal details, approval info, and a YAML diff
            showing the recommended change.

        Raises:
            KeyError: If the proposal is not found.
            ValueError: If the proposal is not in "pending" status.
        """
        from praxis.persistence.db_ops import db_read, db_update

        record = db_read("LearningEvolutionProposal", proposal_id)
        if record is None:
            raise KeyError(
                f"Evolution proposal '{proposal_id}' not found. "
                f"Verify the proposal_id is correct."
            )

        if record.get("status") != "pending":
            raise ValueError(
                f"Proposal '{proposal_id}' has status '{record.get('status')}', "
                f"not 'pending'. Only pending proposals can be approved."
            )

        now = _now_utc_iso()

        # Update proposal status
        db_update(
            "LearningEvolutionProposal",
            proposal_id,
            {
                "status": "approved",
                "reviewed_by": approved_by,
                "reviewed_at": now,
            },
        )

        # Generate a human-readable diff
        diff = self._generate_diff(record)

        logger.info(
            "Approved evolution proposal %s by %s",
            proposal_id,
            approved_by,
        )

        return {
            "proposal_id": proposal_id,
            "status": "approved",
            "reviewed_by": approved_by,
            "reviewed_at": now,
            "proposal_type": record.get("proposal_type", ""),
            "target": record.get("target", ""),
            "rationale": record.get("rationale", ""),
            "diff": diff,
        }

    def reject(self, proposal_id: str, rejected_by: str, reason: str = "") -> dict:
        """Reject a proposal.

        Args:
            proposal_id: The proposal to reject.
            rejected_by: Identity of the rejector.
            reason: Optional reason for rejection.

        Returns:
            Dict with proposal details and rejection info.

        Raises:
            KeyError: If the proposal is not found.
            ValueError: If the proposal is not in "pending" status.
        """
        from praxis.persistence.db_ops import db_read, db_update

        record = db_read("LearningEvolutionProposal", proposal_id)
        if record is None:
            raise KeyError(
                f"Evolution proposal '{proposal_id}' not found. "
                f"Verify the proposal_id is correct."
            )

        if record.get("status") != "pending":
            raise ValueError(
                f"Proposal '{proposal_id}' has status '{record.get('status')}', "
                f"not 'pending'. Only pending proposals can be rejected."
            )

        now = _now_utc_iso()

        db_update(
            "LearningEvolutionProposal",
            proposal_id,
            {
                "status": "rejected",
                "reviewed_by": rejected_by,
                "reviewed_at": now,
            },
        )

        logger.info(
            "Rejected evolution proposal %s by %s (reason: %s)",
            proposal_id,
            rejected_by,
            reason or "none",
        )

        return {
            "proposal_id": proposal_id,
            "status": "rejected",
            "reviewed_by": rejected_by,
            "reviewed_at": now,
            "reason": reason,
        }

    # -- Diff generation ----------------------------------------------------

    def _generate_diff(self, proposal_record: dict) -> dict:
        """Generate a human-readable diff from a proposal record.

        Returns a dict describing the recommended change in a format
        that can be applied to the domain YAML.
        """
        proposal_type = proposal_record.get("proposal_type", "")
        target = proposal_record.get("target", "")
        current_value = proposal_record.get("current_value")
        proposed_value = proposal_record.get("proposed_value")

        # Unwrap dict-wrapped values from persistence
        if isinstance(current_value, dict) and "value" in current_value:
            current_value = current_value["value"]
        if isinstance(proposed_value, dict) and "value" in proposed_value:
            proposed_value = proposed_value["value"]

        return {
            "action": proposal_type,
            "target": target,
            "current": current_value,
            "proposed": proposed_value,
            "domain": proposal_record.get("domain", self.domain),
            "note": (
                "This diff is a recommendation. Review the proposed change "
                "and manually apply it to the domain YAML if appropriate."
            ),
        }

    # -- Query helpers ------------------------------------------------------

    def get_observations(
        self,
        target: str | None = None,
        limit: int = 100,
    ) -> list[dict]:
        """Get observations for this domain, optionally filtered by target.

        Returns:
            List of observation dicts.
        """
        from praxis.persistence.db_ops import db_list

        db_filter: dict = {"domain": self.domain}
        if target is not None:
            db_filter["target"] = target
        if self.session_id:
            db_filter["session_id"] = self.session_id

        return db_list("LearningObservation", filter=db_filter, limit=limit)

    def get_patterns(self, pattern_type: str | None = None) -> list[dict]:
        """Get detected patterns for this domain.

        Returns:
            List of pattern dicts.
        """
        from praxis.persistence.db_ops import db_list

        db_filter: dict = {"domain": self.domain}
        if pattern_type is not None:
            db_filter["pattern_type"] = pattern_type

        return db_list("LearningPattern", filter=db_filter, limit=1000)

    def get_proposals(self, status: str | None = None) -> list[dict]:
        """Get evolution proposals for this domain.

        Args:
            status: Optional filter (pending, approved, rejected).

        Returns:
            List of proposal dicts.
        """
        from praxis.persistence.db_ops import db_list

        db_filter: dict = {"domain": self.domain}
        if status is not None:
            db_filter["status"] = status

        return db_list("LearningEvolutionProposal", filter=db_filter, limit=1000)
