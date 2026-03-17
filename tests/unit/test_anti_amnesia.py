# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""Unit tests for praxis.core.anti_amnesia — anti-amnesia injection mechanism."""

import pytest


# ---------------------------------------------------------------------------
# AntiAmnesiaReminder dataclass
# ---------------------------------------------------------------------------


class TestAntiAmnesiaReminder:
    """Test the AntiAmnesiaReminder frozen dataclass."""

    def test_basic_creation(self):
        from praxis.core.anti_amnesia import AntiAmnesiaReminder

        r = AntiAmnesiaReminder(
            priority="P0",
            rule="Never commit secrets",
            trigger="always",
            domain="coc",
        )
        assert r.priority == "P0"
        assert r.rule == "Never commit secrets"
        assert r.trigger == "always"
        assert r.domain == "coc"

    def test_frozen(self):
        from praxis.core.anti_amnesia import AntiAmnesiaReminder

        r = AntiAmnesiaReminder(priority="P0", rule="test", trigger="always", domain="coc")
        with pytest.raises(AttributeError):
            r.priority = "P1"


# ---------------------------------------------------------------------------
# AntiAmnesiaInjector with pre-loaded rules
# ---------------------------------------------------------------------------


class TestAntiAmnesiaInjectorPreloaded:
    """Test the injector with pre-loaded rules (no domain YAML loading)."""

    @pytest.fixture
    def sample_rules(self):
        return [
            {"priority": "P0", "rule": "Never commit secrets", "trigger": "always"},
            {"priority": "P0", "rule": "Run tests before committing", "trigger": "always"},
            {"priority": "P1", "rule": "Follow code conventions", "trigger": "on_write"},
            {"priority": "P2", "rule": "Consider performance", "trigger": "on_write"},
        ]

    def test_rule_count(self, sample_rules):
        from praxis.core.anti_amnesia import AntiAmnesiaInjector

        injector = AntiAmnesiaInjector(domain="coc", rules=sample_rules)
        assert injector.rule_count == 4

    def test_get_reminders_always(self, sample_rules):
        from praxis.core.anti_amnesia import AntiAmnesiaInjector

        injector = AntiAmnesiaInjector(domain="coc", rules=sample_rules)
        reminders = injector.get_reminders("always")
        assert len(reminders) == 2
        assert all(r.trigger == "always" for r in reminders)

    def test_get_reminders_on_write_includes_always(self, sample_rules):
        from praxis.core.anti_amnesia import AntiAmnesiaInjector

        injector = AntiAmnesiaInjector(domain="coc", rules=sample_rules)
        reminders = injector.get_reminders("on_write")
        # Should include 2 "always" + 2 "on_write" = 4
        assert len(reminders) == 4

    def test_reminders_sorted_by_priority(self, sample_rules):
        from praxis.core.anti_amnesia import AntiAmnesiaInjector

        injector = AntiAmnesiaInjector(domain="coc", rules=sample_rules)
        reminders = injector.get_reminders("on_write")
        priorities = [r.priority for r in reminders]
        # P0s should come before P1s, P1s before P2s
        assert priorities == sorted(priorities, key=lambda p: {"P0": 0, "P1": 1, "P2": 2}[p])

    def test_get_all_reminders(self, sample_rules):
        from praxis.core.anti_amnesia import AntiAmnesiaInjector

        injector = AntiAmnesiaInjector(domain="coc", rules=sample_rules)
        all_reminders = injector.get_all_reminders()
        assert len(all_reminders) == 4

    def test_get_critical_reminders(self, sample_rules):
        from praxis.core.anti_amnesia import AntiAmnesiaInjector

        injector = AntiAmnesiaInjector(domain="coc", rules=sample_rules)
        critical = injector.get_critical_reminders()
        assert len(critical) == 2
        assert all(r.priority == "P0" for r in critical)

    def test_format_for_context(self, sample_rules):
        from praxis.core.anti_amnesia import AntiAmnesiaInjector

        injector = AntiAmnesiaInjector(domain="coc", rules=sample_rules)
        text = injector.format_for_context("always")
        assert "[COC Anti-Amnesia Reminders]" in text
        assert "[P0]" in text
        assert "Never commit secrets" in text

    def test_format_for_context_empty(self):
        from praxis.core.anti_amnesia import AntiAmnesiaInjector

        injector = AntiAmnesiaInjector(domain="coc", rules=[])
        text = injector.format_for_context("always")
        assert text == ""

    def test_unknown_trigger_returns_always_rules_only(self, sample_rules):
        from praxis.core.anti_amnesia import AntiAmnesiaInjector

        injector = AntiAmnesiaInjector(domain="coc", rules=sample_rules)
        reminders = injector.get_reminders("on_deploy")
        # Only "always" rules match
        assert len(reminders) == 2


class TestAntiAmnesiaInjectorInvalidRules:
    """Test that invalid rules are gracefully skipped."""

    def test_invalid_priority_skipped(self):
        from praxis.core.anti_amnesia import AntiAmnesiaInjector

        rules = [
            {"priority": "P9", "rule": "Bad priority", "trigger": "always"},
            {"priority": "P0", "rule": "Good rule", "trigger": "always"},
        ]
        injector = AntiAmnesiaInjector(domain="coc", rules=rules)
        assert injector.rule_count == 1

    def test_empty_rule_text_skipped(self):
        from praxis.core.anti_amnesia import AntiAmnesiaInjector

        rules = [
            {"priority": "P0", "rule": "", "trigger": "always"},
            {"priority": "P0", "rule": "Good rule", "trigger": "always"},
        ]
        injector = AntiAmnesiaInjector(domain="coc", rules=rules)
        assert injector.rule_count == 1

    def test_invalid_trigger_skipped(self):
        from praxis.core.anti_amnesia import AntiAmnesiaInjector

        rules = [
            {"priority": "P0", "rule": "Bad trigger", "trigger": "on_invalid"},
            {"priority": "P0", "rule": "Good rule", "trigger": "always"},
        ]
        injector = AntiAmnesiaInjector(domain="coc", rules=rules)
        assert injector.rule_count == 1


# ---------------------------------------------------------------------------
# AntiAmnesiaInjector with domain YAML loading
# ---------------------------------------------------------------------------


class TestAntiAmnesiaInjectorDomain:
    """Test loading anti-amnesia rules from actual domain YAMLs."""

    def test_coc_loads_rules(self):
        from praxis.core.anti_amnesia import AntiAmnesiaInjector

        injector = AntiAmnesiaInjector(domain="coc")
        assert injector.rule_count >= 2
        critical = injector.get_critical_reminders()
        assert len(critical) >= 2

    def test_coe_loads_rules(self):
        from praxis.core.anti_amnesia import AntiAmnesiaInjector

        injector = AntiAmnesiaInjector(domain="coe")
        assert injector.rule_count >= 2

    def test_cog_loads_rules(self):
        from praxis.core.anti_amnesia import AntiAmnesiaInjector

        injector = AntiAmnesiaInjector(domain="cog")
        assert injector.rule_count >= 2

    def test_cor_loads_rules(self):
        from praxis.core.anti_amnesia import AntiAmnesiaInjector

        injector = AntiAmnesiaInjector(domain="cor")
        assert injector.rule_count >= 2

    def test_cocomp_loads_rules(self):
        from praxis.core.anti_amnesia import AntiAmnesiaInjector

        injector = AntiAmnesiaInjector(domain="cocomp")
        assert injector.rule_count >= 2

    def test_cof_loads_rules(self):
        from praxis.core.anti_amnesia import AntiAmnesiaInjector

        injector = AntiAmnesiaInjector(domain="cof")
        assert injector.rule_count >= 2

    def test_nonexistent_domain_returns_empty(self):
        from praxis.core.anti_amnesia import AntiAmnesiaInjector

        injector = AntiAmnesiaInjector(domain="nonexistent")
        assert injector.rule_count == 0

    def test_all_domains_have_p0_rules(self):
        """Every domain should have at least one P0 critical rule."""
        from praxis.core.anti_amnesia import AntiAmnesiaInjector

        for domain in ["coc", "coe", "cog", "cor", "cocomp", "cof"]:
            injector = AntiAmnesiaInjector(domain=domain)
            critical = injector.get_critical_reminders()
            assert len(critical) >= 1, f"Domain '{domain}' has no P0 rules"
