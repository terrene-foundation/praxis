# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""Unit tests for praxis.core.rules — domain rule enforcement engine."""

import pytest


# ---------------------------------------------------------------------------
# RuleWarning dataclass
# ---------------------------------------------------------------------------


class TestRuleWarning:
    """Test the RuleWarning frozen dataclass."""

    def test_basic_creation(self):
        from praxis.core.rules import RuleWarning

        w = RuleWarning(
            rule_name="alt_check",
            rule_type="alternatives_present",
            message="No alternatives found",
        )
        assert w.rule_name == "alt_check"
        assert w.rule_type == "alternatives_present"
        assert w.severity == "warning"  # default

    def test_frozen(self):
        from praxis.core.rules import RuleWarning

        w = RuleWarning(rule_name="test", rule_type="test", message="test")
        with pytest.raises(AttributeError):
            w.rule_name = "changed"


# ---------------------------------------------------------------------------
# DomainRuleEngine with pre-loaded rules
# ---------------------------------------------------------------------------


class TestDomainRuleEngineAlternatives:
    """Test the alternatives_present rule type."""

    @pytest.fixture
    def engine(self):
        from praxis.core.rules import DomainRuleEngine

        rules = [
            {
                "name": "alt_check",
                "type": "alternatives_present",
                "description": "Must have alternatives",
                "params": {"applies_to": ["architecture"]},
            }
        ]
        return DomainRuleEngine(domain="coc", rules=rules)

    def test_warns_when_no_alternatives(self, engine):
        record = {
            "record_type": "decision",
            "content": {
                "decision": "Use React",
                "decision_type": "architecture",
            },
            "reasoning_trace": {"rationale": "Team knows it"},
        }
        warnings = engine.evaluate(record)
        assert len(warnings) == 1
        assert warnings[0].rule_type == "alternatives_present"

    def test_passes_when_alternatives_present(self, engine):
        record = {
            "record_type": "decision",
            "content": {
                "decision": "Use React",
                "decision_type": "architecture",
                "alternatives": ["Vue", "Angular"],
            },
            "reasoning_trace": {"rationale": "Team knows it"},
        }
        warnings = engine.evaluate(record)
        assert len(warnings) == 0

    def test_skips_non_matching_decision_type(self, engine):
        record = {
            "record_type": "decision",
            "content": {
                "decision": "Ship now",
                "decision_type": "process",
            },
            "reasoning_trace": {"rationale": "Deadline"},
        }
        warnings = engine.evaluate(record)
        assert len(warnings) == 0

    def test_skips_non_decision_records(self, engine):
        record = {
            "record_type": "observation",
            "content": {"observation": "Pattern detected"},
            "reasoning_trace": {"actor": "ai"},
        }
        warnings = engine.evaluate(record)
        assert len(warnings) == 0


class TestDomainRuleEngineRationaleDepth:
    """Test the rationale_depth rule type."""

    @pytest.fixture
    def engine(self):
        from praxis.core.rules import DomainRuleEngine

        rules = [
            {
                "name": "rationale_min",
                "type": "rationale_depth",
                "description": "Rationale must be >= 10 words",
                "params": {"min_words": 10},
            }
        ]
        return DomainRuleEngine(domain="coc", rules=rules)

    def test_warns_when_rationale_too_short(self, engine):
        record = {
            "record_type": "decision",
            "content": {"decision": "Use React"},
            "reasoning_trace": {"rationale": "It is good"},
        }
        warnings = engine.evaluate(record)
        assert len(warnings) == 1
        assert warnings[0].rule_type == "rationale_depth"
        assert "3 words" in warnings[0].message

    def test_passes_when_rationale_sufficient(self, engine):
        record = {
            "record_type": "decision",
            "content": {"decision": "Use React"},
            "reasoning_trace": {
                "rationale": (
                    "The team has extensive experience with React and its "
                    "ecosystem which will reduce onboarding time significantly"
                )
            },
        }
        warnings = engine.evaluate(record)
        assert len(warnings) == 0

    def test_warns_when_rationale_missing(self, engine):
        record = {
            "record_type": "decision",
            "content": {"decision": "Use React"},
            "reasoning_trace": {},
        }
        warnings = engine.evaluate(record)
        assert len(warnings) == 1
        assert "no rationale" in warnings[0].message.lower()


class TestDomainRuleEngineCitation:
    """Test the citation_required rule type."""

    @pytest.fixture
    def engine(self):
        from praxis.core.rules import DomainRuleEngine

        rules = [
            {
                "name": "cite_check",
                "type": "citation_required",
                "description": "Must cite sources",
                "params": {"applies_to": ["interpretation"]},
            }
        ]
        return DomainRuleEngine(domain="cor", rules=rules)

    def test_warns_when_no_citation(self, engine):
        record = {
            "record_type": "decision",
            "content": {
                "decision": "Correlation is significant",
                "decision_type": "interpretation",
            },
            "reasoning_trace": {"rationale": "The data looks right to me"},
        }
        warnings = engine.evaluate(record)
        assert len(warnings) == 1
        assert warnings[0].rule_type == "citation_required"

    def test_passes_when_url_citation(self, engine):
        record = {
            "record_type": "decision",
            "content": {
                "decision": "Correlation is significant",
                "decision_type": "interpretation",
            },
            "reasoning_trace": {"rationale": "As shown by https://arxiv.org/abs/1234.5678"},
        }
        warnings = engine.evaluate(record)
        assert len(warnings) == 0

    def test_passes_when_et_al_citation(self, engine):
        record = {
            "record_type": "decision",
            "content": {
                "decision": "Hypothesis confirmed",
                "decision_type": "interpretation",
            },
            "reasoning_trace": {"rationale": "Consistent with Smith et al. (2024) findings"},
        }
        warnings = engine.evaluate(record)
        assert len(warnings) == 0


class TestDomainRuleEnginePrecedent:
    """Test the precedent_required rule type."""

    @pytest.fixture
    def engine(self):
        from praxis.core.rules import DomainRuleEngine

        rules = [
            {
                "name": "precedent_check",
                "type": "precedent_required",
                "description": "Must cite precedent",
                "params": {"applies_to": ["compliance_determination"]},
            }
        ]
        return DomainRuleEngine(domain="cocomp", rules=rules)

    def test_warns_when_no_precedent(self, engine):
        record = {
            "record_type": "decision",
            "content": {
                "decision": "Compliant with SOX Section 302",
                "decision_type": "compliance_determination",
            },
            "reasoning_trace": {"rationale": "Controls are in place and functioning"},
        }
        warnings = engine.evaluate(record)
        assert len(warnings) == 1
        assert warnings[0].rule_type == "precedent_required"

    def test_passes_when_precedent_cited(self, engine):
        record = {
            "record_type": "decision",
            "content": {
                "decision": "Compliant with SOX Section 302",
                "decision_type": "compliance_determination",
            },
            "reasoning_trace": {
                "rationale": (
                    "Consistent with prior decision from Q2 audit that "
                    "established practice of quarterly control testing"
                )
            },
        }
        warnings = engine.evaluate(record)
        assert len(warnings) == 0


# ---------------------------------------------------------------------------
# DomainRuleEngine with domain YAML loading
# ---------------------------------------------------------------------------


class TestDomainRuleEngineDomain:
    """Test loading rules from actual domain YAMLs."""

    def test_coc_loads_rules(self):
        from praxis.core.rules import DomainRuleEngine

        engine = DomainRuleEngine(domain="coc")
        assert engine.rule_count >= 2

    def test_coe_loads_rules(self):
        from praxis.core.rules import DomainRuleEngine

        engine = DomainRuleEngine(domain="coe")
        assert engine.rule_count >= 2

    def test_cog_loads_rules(self):
        from praxis.core.rules import DomainRuleEngine

        engine = DomainRuleEngine(domain="cog")
        assert engine.rule_count >= 2

    def test_cor_loads_rules(self):
        from praxis.core.rules import DomainRuleEngine

        engine = DomainRuleEngine(domain="cor")
        assert engine.rule_count >= 2

    def test_cocomp_loads_rules(self):
        from praxis.core.rules import DomainRuleEngine

        engine = DomainRuleEngine(domain="cocomp")
        assert engine.rule_count >= 2

    def test_cof_loads_rules(self):
        from praxis.core.rules import DomainRuleEngine

        engine = DomainRuleEngine(domain="cof")
        assert engine.rule_count >= 2

    def test_nonexistent_domain_returns_empty(self):
        from praxis.core.rules import DomainRuleEngine

        engine = DomainRuleEngine(domain="nonexistent")
        assert engine.rule_count == 0

    def test_get_rules_returns_copy(self):
        from praxis.core.rules import DomainRuleEngine

        engine = DomainRuleEngine(domain="coc")
        rules = engine.get_rules()
        assert isinstance(rules, list)
        assert len(rules) == engine.rule_count


# ---------------------------------------------------------------------------
# Multiple rules combined
# ---------------------------------------------------------------------------


class TestDomainRuleEngineMultipleRules:
    """Test evaluation with multiple rules active."""

    def test_multiple_warnings(self):
        from praxis.core.rules import DomainRuleEngine

        rules = [
            {
                "name": "alt_check",
                "type": "alternatives_present",
                "description": "Must have alternatives",
                "params": {},
            },
            {
                "name": "rationale_min",
                "type": "rationale_depth",
                "description": "Rationale >= 10 words",
                "params": {"min_words": 10},
            },
        ]
        engine = DomainRuleEngine(domain="coc", rules=rules)

        record = {
            "record_type": "decision",
            "content": {"decision": "Use React"},
            "reasoning_trace": {"rationale": "It is good"},
        }
        warnings = engine.evaluate(record)
        assert len(warnings) == 2
        rule_types = {w.rule_type for w in warnings}
        assert "alternatives_present" in rule_types
        assert "rationale_depth" in rule_types

    def test_no_warnings_when_all_pass(self):
        from praxis.core.rules import DomainRuleEngine

        rules = [
            {
                "name": "alt_check",
                "type": "alternatives_present",
                "description": "Must have alternatives",
                "params": {},
            },
            {
                "name": "rationale_min",
                "type": "rationale_depth",
                "description": "Rationale >= 5 words",
                "params": {"min_words": 5},
            },
        ]
        engine = DomainRuleEngine(domain="coc", rules=rules)

        record = {
            "record_type": "decision",
            "content": {
                "decision": "Use React",
                "alternatives": ["Vue", "Angular"],
            },
            "reasoning_trace": {
                "rationale": "Team has extensive experience with React and its component model"
            },
        }
        warnings = engine.evaluate(record)
        assert len(warnings) == 0
