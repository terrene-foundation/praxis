# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""
Anti-amnesia injection mechanism for CO sessions.

Loads anti-amnesia rules from domain YAML configurations and returns
prioritised reminders for inclusion in AI context. This ensures that
critical domain-specific knowledge is never lost between interactions,
even when context windows rotate or sessions are long-running.

Rules are categorised by priority:
    P0 = Critical (must always be present in context)
    P1 = Important (should be present when relevant)
    P2 = Advisory (include when space permits)

Rules are filtered by trigger:
    always          = Include in every interaction
    on_write        = Include when AI is writing/modifying content
    on_deploy       = Include when deployment actions are evaluated
    on_commit       = Include when committing changes
    on_session_start = Include at session initialisation
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

# Priority ordering for sorting (lower index = higher priority)
PRIORITY_ORDER = {"P0": 0, "P1": 1, "P2": 2}

# Valid trigger values
VALID_TRIGGERS = frozenset({"always", "on_write", "on_deploy", "on_commit", "on_session_start"})

# Valid priority values
VALID_PRIORITIES = frozenset({"P0", "P1", "P2"})


@dataclass(frozen=True)
class AntiAmnesiaReminder:
    """A single anti-amnesia reminder to include in AI context.

    Attributes:
        priority: P0 (critical), P1 (important), or P2 (advisory).
        rule: The reminder text.
        trigger: When this reminder should be injected.
        domain: The CO domain this reminder originates from.
    """

    priority: str
    rule: str
    trigger: str
    domain: str


class AntiAmnesiaInjector:
    """Loads anti-amnesia rules from domain YAML and provides filtered reminders.

    The injector caches loaded rules per domain. Rules are returned sorted
    by priority (P0 first, then P1, then P2).

    Args:
        domain: The CO domain to load rules for (e.g. "coc", "coe").
        rules: Optional pre-loaded rules list (bypasses domain YAML loading).
            Each rule should be a dict with keys: priority, rule, trigger.
    """

    def __init__(self, domain: str, rules: list[dict[str, Any]] | None = None) -> None:
        self.domain = domain
        self._rules: list[AntiAmnesiaReminder] = []

        if rules is not None:
            self._rules = self._parse_rules(rules, domain)
        else:
            self._rules = self._load_from_domain(domain)

    def _load_from_domain(self, domain: str) -> list[AntiAmnesiaReminder]:
        """Load anti-amnesia rules from the domain YAML configuration.

        Returns an empty list if the domain has no anti_amnesia section
        or if the domain cannot be loaded.
        """
        try:
            from praxis.domains.loader import DomainLoader

            loader = DomainLoader()
            config = loader.load_domain(domain)
            if config.anti_amnesia is None:
                logger.debug("Domain '%s' has no anti_amnesia section", domain)
                return []
            return self._parse_rules(config.anti_amnesia, domain)
        except Exception as exc:
            logger.warning(
                "Could not load anti-amnesia rules for domain '%s': %s",
                domain,
                exc,
            )
            return []

    def _parse_rules(
        self, raw_rules: list[dict[str, Any]], domain: str
    ) -> list[AntiAmnesiaReminder]:
        """Parse raw rule dicts into AntiAmnesiaReminder instances.

        Invalid rules are logged and skipped rather than raising exceptions.
        """
        reminders: list[AntiAmnesiaReminder] = []
        for i, raw in enumerate(raw_rules):
            priority = raw.get("priority", "")
            rule_text = raw.get("rule", "")
            trigger = raw.get("trigger", "")

            if priority not in VALID_PRIORITIES:
                logger.warning(
                    "Anti-amnesia rule %d in domain '%s' has invalid priority '%s' — skipping",
                    i,
                    domain,
                    priority,
                )
                continue

            if not rule_text:
                logger.warning(
                    "Anti-amnesia rule %d in domain '%s' has empty rule text — skipping",
                    i,
                    domain,
                )
                continue

            if trigger not in VALID_TRIGGERS:
                logger.warning(
                    "Anti-amnesia rule %d in domain '%s' has invalid trigger '%s' — skipping",
                    i,
                    domain,
                    trigger,
                )
                continue

            reminders.append(
                AntiAmnesiaReminder(
                    priority=priority,
                    rule=rule_text,
                    trigger=trigger,
                    domain=domain,
                )
            )

        return reminders

    def get_reminders(self, trigger: str = "always") -> list[AntiAmnesiaReminder]:
        """Return anti-amnesia reminders matching the given trigger.

        Rules with trigger "always" are included regardless of the
        requested trigger. Results are sorted by priority (P0 first).

        Args:
            trigger: The trigger context to filter by.

        Returns:
            List of AntiAmnesiaReminder instances, sorted by priority.
        """
        matching = [r for r in self._rules if r.trigger == "always" or r.trigger == trigger]

        # Sort by priority: P0 first, then P1, then P2
        matching.sort(key=lambda r: PRIORITY_ORDER.get(r.priority, 99))
        return matching

    def get_all_reminders(self) -> list[AntiAmnesiaReminder]:
        """Return all anti-amnesia reminders regardless of trigger.

        Results are sorted by priority (P0 first).

        Returns:
            List of all AntiAmnesiaReminder instances.
        """
        result = list(self._rules)
        result.sort(key=lambda r: PRIORITY_ORDER.get(r.priority, 99))
        return result

    def get_critical_reminders(self) -> list[AntiAmnesiaReminder]:
        """Return only P0 (critical) reminders.

        Returns:
            List of P0 AntiAmnesiaReminder instances.
        """
        return [r for r in self._rules if r.priority == "P0"]

    def format_for_context(self, trigger: str = "always") -> str:
        """Format matching reminders as a text block for AI context injection.

        Args:
            trigger: The trigger context to filter by.

        Returns:
            Formatted string with all matching reminders, or empty string
            if no reminders match.
        """
        reminders = self.get_reminders(trigger)
        if not reminders:
            return ""

        lines = [f"[{self.domain.upper()} Anti-Amnesia Reminders]"]
        for r in reminders:
            lines.append(f"  [{r.priority}] {r.rule}")
        return "\n".join(lines)

    @property
    def rule_count(self) -> int:
        """Return the total number of loaded rules."""
        return len(self._rules)
