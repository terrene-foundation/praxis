# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""
Domain rule enforcement engine.

Evaluates procedural rules that go beyond constraint enforcement. Where
constraints gate actions (allow/block), domain rules evaluate the quality
and completeness of deliberation records. Rules produce warnings rather
than blocks, nudging toward better decision-making practices.

Rule types:
    alternatives_present   - Decisions must document alternatives considered
    rationale_depth        - Rationale must meet a minimum word count
    citation_required      - Decisions must include citations (COR)
    precedent_required     - Decisions must cite precedent (COComp)

Rules are loaded from the domain YAML ``rules`` section and evaluated
against deliberation record content.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RuleWarning:
    """A warning produced by domain rule evaluation.

    Warnings are advisory — they do not block actions. They indicate
    that a deliberation record could be improved to meet domain standards.

    Attributes:
        rule_name: Name of the rule that produced this warning.
        rule_type: Type of rule (alternatives_present, rationale_depth, etc.).
        message: Human-readable explanation of what is missing or insufficient.
        severity: "warning" (standard) or "info" (informational).
    """

    rule_name: str
    rule_type: str
    message: str
    severity: str = "warning"


class DomainRuleEngine:
    """Evaluates procedural domain rules against deliberation records.

    The engine loads rules from domain YAML and evaluates them against
    decision records. All evaluations produce warnings (not blocks) to
    encourage better deliberation practices without preventing work.

    Args:
        domain: The CO domain to load rules for (e.g. "coc", "coe").
        rules: Optional pre-loaded rules list (bypasses domain YAML loading).
            Each rule should be a dict with keys: name, type, description,
            and optionally params.
    """

    def __init__(self, domain: str, rules: list[dict[str, Any]] | None = None) -> None:
        self.domain = domain

        if rules is not None:
            self._rules = list(rules)
        else:
            self._rules = self._load_from_domain(domain)

    def _load_from_domain(self, domain: str) -> list[dict[str, Any]]:
        """Load rules from the domain YAML configuration.

        Returns an empty list if the domain has no rules section or
        if the domain cannot be loaded.
        """
        try:
            from praxis.domains.loader import DomainLoader

            loader = DomainLoader()
            config = loader.load_domain(domain)
            if config.rules is None:
                logger.debug("Domain '%s' has no rules section", domain)
                return []
            return list(config.rules)
        except Exception as exc:
            logger.warning(
                "Could not load domain rules for domain '%s': %s",
                domain,
                exc,
            )
            return []

    def evaluate(self, record: dict) -> list[RuleWarning]:
        """Evaluate all domain rules against a deliberation record.

        Args:
            record: A deliberation record dict. Expected keys include:
                - record_type: "decision", "observation", or "escalation"
                - content: dict with decision details
                    - decision: the decision text
                    - alternatives: list of alternatives (optional)
                    - decision_type: type of decision (optional)
                - reasoning_trace: dict with rationale details
                    - rationale: the rationale text

        Returns:
            List of RuleWarning instances. Empty list means all rules pass.
        """
        warnings: list[RuleWarning] = []

        for rule in self._rules:
            rule_type = rule.get("type", "")
            rule_name = rule.get("name", "unknown")
            params = rule.get("params", {})

            if rule_type == "alternatives_present":
                warning = self._check_alternatives_present(record, rule_name, params)
            elif rule_type == "rationale_depth":
                warning = self._check_rationale_depth(record, rule_name, params)
            elif rule_type == "citation_required":
                warning = self._check_citation_required(record, rule_name, params)
            elif rule_type == "precedent_required":
                warning = self._check_precedent_required(record, rule_name, params)
            else:
                logger.debug(
                    "Unknown rule type '%s' for rule '%s' — skipping",
                    rule_type,
                    rule_name,
                )
                continue

            if warning is not None:
                warnings.append(warning)

        if warnings:
            logger.info(
                "Domain rule evaluation produced %d warning(s) for record type '%s'",
                len(warnings),
                record.get("record_type", "unknown"),
            )

        return warnings

    def _check_alternatives_present(
        self,
        record: dict,
        rule_name: str,
        params: dict,
    ) -> RuleWarning | None:
        """Check that decision records include alternatives considered.

        Only applies to decision records. If ``applies_to`` is specified
        in params, only applies to those decision types.
        """
        if record.get("record_type") != "decision":
            return None

        # Check if this applies to the current decision type
        applies_to = params.get("applies_to")
        if applies_to:
            content = record.get("content", {})
            decision_type = content.get("decision_type", "")
            if decision_type and decision_type not in applies_to:
                return None

        content = record.get("content", {})
        alternatives = content.get("alternatives")

        if not alternatives or len(alternatives) == 0:
            return RuleWarning(
                rule_name=rule_name,
                rule_type="alternatives_present",
                message=(
                    "Decision does not document alternatives considered. "
                    "Recording what options were evaluated strengthens "
                    "the deliberation trail."
                ),
            )

        return None

    def _check_rationale_depth(
        self,
        record: dict,
        rule_name: str,
        params: dict,
    ) -> RuleWarning | None:
        """Check that decision rationale meets a minimum word count.

        Only applies to decision records.
        """
        if record.get("record_type") != "decision":
            return None

        min_words = params.get("min_words", 10)

        reasoning_trace = record.get("reasoning_trace", {})
        rationale = reasoning_trace.get("rationale", "")

        if not rationale:
            return RuleWarning(
                rule_name=rule_name,
                rule_type="rationale_depth",
                message="Decision has no rationale. Capture the reasoning behind this decision.",
            )

        word_count = len(rationale.split())
        if word_count < min_words:
            return RuleWarning(
                rule_name=rule_name,
                rule_type="rationale_depth",
                message=(
                    f"Decision rationale is {word_count} words "
                    f"(minimum: {min_words}). Provide more detail "
                    f"about why this decision was made."
                ),
            )

        return None

    def _check_citation_required(
        self,
        record: dict,
        rule_name: str,
        params: dict,
    ) -> RuleWarning | None:
        """Check that decisions include citations or references.

        Looks for citation-like patterns in the content or rationale:
        author names, URLs, DOIs, or explicit citation markers.
        Only applies to decision records matching ``applies_to``.
        """
        if record.get("record_type") != "decision":
            return None

        applies_to = params.get("applies_to")
        if applies_to:
            content = record.get("content", {})
            decision_type = content.get("decision_type", "")
            if decision_type and decision_type not in applies_to:
                return None

        # Check for citation indicators in rationale and content
        reasoning_trace = record.get("reasoning_trace", {})
        rationale = reasoning_trace.get("rationale", "")
        content = record.get("content", {})
        decision_text = content.get("decision", "")

        combined = f"{rationale} {decision_text}"

        # Simple heuristic: look for citation markers
        citation_indicators = [
            "http://",
            "https://",
            "doi:",
            "DOI:",
            "[1]",
            "[2]",
            "(et al",
            "et al.",
            "citation:",
            "reference:",
            "see:",
            "cf.",
            "per ",
            "according to",
        ]

        has_citation = any(indicator in combined for indicator in citation_indicators)

        if not has_citation:
            return RuleWarning(
                rule_name=rule_name,
                rule_type="citation_required",
                message=(
                    "Decision does not include citations or references. "
                    "Include sources that support the reasoning."
                ),
            )

        return None

    def _check_precedent_required(
        self,
        record: dict,
        rule_name: str,
        params: dict,
    ) -> RuleWarning | None:
        """Check that decisions reference prior precedent or prior decisions.

        Looks for precedent indicators in the rationale text.
        Only applies to decision records matching ``applies_to``.
        """
        if record.get("record_type") != "decision":
            return None

        applies_to = params.get("applies_to")
        if applies_to:
            content = record.get("content", {})
            decision_type = content.get("decision_type", "")
            if decision_type and decision_type not in applies_to:
                return None

        reasoning_trace = record.get("reasoning_trace", {})
        rationale = reasoning_trace.get("rationale", "")

        # Simple heuristic: look for precedent markers
        precedent_indicators = [
            "precedent",
            "prior decision",
            "previous ruling",
            "established practice",
            "consistent with",
            "in accordance with",
            "as per",
            "following the",
            "based on prior",
            "historical",
            "previously determined",
        ]

        rationale_lower = rationale.lower()
        has_precedent = any(indicator in rationale_lower for indicator in precedent_indicators)

        if not has_precedent:
            return RuleWarning(
                rule_name=rule_name,
                rule_type="precedent_required",
                message=(
                    "Decision does not reference prior precedent. "
                    "Cite relevant prior decisions or established "
                    "practices to strengthen the compliance trail."
                ),
            )

        return None

    @property
    def rule_count(self) -> int:
        """Return the total number of loaded rules."""
        return len(self._rules)

    def get_rules(self) -> list[dict[str, Any]]:
        """Return a copy of the loaded rules."""
        return list(self._rules)
