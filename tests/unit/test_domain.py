# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""Unit tests for the Praxis domain engine — loader, schema, and all six domain configs.

TDD: These tests are written FIRST. The implementation must satisfy them.
Tests MUST NOT be modified to fit the implementation.
"""

from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# DomainLoader discovery & listing
# ---------------------------------------------------------------------------


class TestDomainLoaderDiscovery:
    """DomainLoader must discover all six CO domain directories."""

    def test_list_domains_returns_all_six(self):
        from praxis.domains.loader import DomainLoader

        loader = DomainLoader()
        domains = loader.list_domains()
        assert set(domains) == {"coc", "coe", "cog", "cor", "cocomp", "cof"}

    def test_list_domains_returns_sorted(self):
        from praxis.domains.loader import DomainLoader

        loader = DomainLoader()
        domains = loader.list_domains()
        assert domains == sorted(domains)

    def test_custom_domains_dir(self, tmp_path):
        """A custom domains_dir with one domain should list only that domain."""
        from praxis.domains.loader import DomainLoader

        # Create a minimal valid domain
        domain_dir = tmp_path / "test_domain"
        domain_dir.mkdir()
        (domain_dir / "domain.yml").write_text(
            "name: test_domain\n"
            "display_name: 'Test Domain'\n"
            "description: 'A test domain'\n"
            "version: '1.0'\n"
            "constraint_templates:\n"
            "  basic:\n"
            "    financial:\n"
            "      max_spend: 10.0\n"
            "    operational:\n"
            "      allowed_actions: ['read']\n"
            "      max_actions_per_hour: 50\n"
            "    temporal:\n"
            "      max_duration_minutes: 60\n"
            "    data_access:\n"
            "      allowed_paths: ['/']\n"
            "    communication:\n"
            "      allowed_channels: ['internal']\n"
            "phases:\n"
            "  - name: work\n"
            "    display_name: Work\n"
            "    description: Do work\n"
            "    approval_gate: false\n"
            "capture:\n"
            "  auto_capture:\n"
            "    - file_changes\n"
            "  decision_types:\n"
            "    - scope\n"
            "  observation_targets:\n"
            "    - workflow_patterns\n"
        )
        loader = DomainLoader(domains_dir=tmp_path)
        assert loader.list_domains() == ["test_domain"]


# ---------------------------------------------------------------------------
# Loading domains
# ---------------------------------------------------------------------------


class TestDomainLoaderLoad:
    """DomainLoader.load_domain must return a DomainConfig dataclass."""

    def test_load_coc_domain(self):
        from praxis.domains.loader import DomainLoader

        loader = DomainLoader()
        config = loader.load_domain("coc")
        assert config.name == "coc"
        assert config.display_name == "CO for Codegen"
        assert config.version == "1.0"
        assert isinstance(config.description, str)
        assert len(config.description) > 0

    def test_load_coe_domain(self):
        from praxis.domains.loader import DomainLoader

        loader = DomainLoader()
        config = loader.load_domain("coe")
        assert config.name == "coe"
        assert config.display_name == "CO for Education"

    def test_load_cog_domain(self):
        from praxis.domains.loader import DomainLoader

        loader = DomainLoader()
        config = loader.load_domain("cog")
        assert config.name == "cog"
        assert config.display_name == "CO for Governance"

    def test_load_cor_domain(self):
        from praxis.domains.loader import DomainLoader

        loader = DomainLoader()
        config = loader.load_domain("cor")
        assert config.name == "cor"
        assert config.display_name == "CO for Research"

    def test_load_cocomp_domain(self):
        from praxis.domains.loader import DomainLoader

        loader = DomainLoader()
        config = loader.load_domain("cocomp")
        assert config.name == "cocomp"
        assert config.display_name == "CO for Compliance"

    def test_load_cof_domain(self):
        from praxis.domains.loader import DomainLoader

        loader = DomainLoader()
        config = loader.load_domain("cof")
        assert config.name == "cof"
        assert config.display_name == "CO for Finance"

    def test_invalid_domain_raises_file_not_found(self):
        from praxis.domains.loader import DomainLoader

        loader = DomainLoader()
        with pytest.raises(FileNotFoundError, match="nonexistent"):
            loader.load_domain("nonexistent")

    def test_loaded_config_has_constraint_templates(self):
        from praxis.domains.loader import DomainLoader

        loader = DomainLoader()
        config = loader.load_domain("coc")
        assert isinstance(config.constraint_templates, dict)
        assert "moderate" in config.constraint_templates
        assert "strict" in config.constraint_templates
        assert "permissive" in config.constraint_templates

    def test_loaded_config_has_phases(self):
        from praxis.domains.loader import DomainLoader

        loader = DomainLoader()
        config = loader.load_domain("coc")
        assert isinstance(config.phases, list)
        assert len(config.phases) >= 3
        # Each phase must be a dict with required keys
        for phase in config.phases:
            assert "name" in phase
            assert "display_name" in phase
            assert "description" in phase

    def test_loaded_config_has_capture(self):
        from praxis.domains.loader import DomainLoader

        loader = DomainLoader()
        config = loader.load_domain("coc")
        assert isinstance(config.capture, dict)
        assert "auto_capture" in config.capture
        assert "decision_types" in config.capture
        assert "observation_targets" in config.capture


# ---------------------------------------------------------------------------
# Constraint templates — 5 dimensions
# ---------------------------------------------------------------------------


class TestConstraintTemplateDimensions:
    """Every constraint template in every domain must define all 5 CO dimensions."""

    REQUIRED_DIMENSIONS = ["financial", "operational", "temporal", "data_access", "communication"]

    def test_each_template_has_all_dimensions(self):
        from praxis.domains.loader import DomainLoader

        loader = DomainLoader()
        for domain_name in loader.list_domains():
            config = loader.load_domain(domain_name)
            for template_name, template in config.constraint_templates.items():
                for dim in self.REQUIRED_DIMENSIONS:
                    assert dim in template, (
                        f"Domain '{domain_name}', template '{template_name}' "
                        f"is missing dimension '{dim}'"
                    )

    def test_coc_moderate_has_five_dimensions(self):
        from praxis.domains.loader import DomainLoader

        loader = DomainLoader()
        template = loader.get_constraint_template("coc", "moderate")
        assert "financial" in template
        assert "operational" in template
        assert "temporal" in template
        assert "data_access" in template
        assert "communication" in template

    def test_get_constraint_template_returns_dict(self):
        from praxis.domains.loader import DomainLoader

        loader = DomainLoader()
        template = loader.get_constraint_template("coc", "moderate")
        assert isinstance(template, dict)

    def test_get_constraint_template_invalid_domain_raises(self):
        from praxis.domains.loader import DomainLoader

        loader = DomainLoader()
        with pytest.raises(FileNotFoundError):
            loader.get_constraint_template("nonexistent", "moderate")

    def test_get_constraint_template_invalid_template_raises(self):
        from praxis.domains.loader import DomainLoader

        loader = DomainLoader()
        with pytest.raises(KeyError, match="no_such_template"):
            loader.get_constraint_template("coc", "no_such_template")


# ---------------------------------------------------------------------------
# Domain-specific constraint values
# ---------------------------------------------------------------------------


class TestCocConstraints:
    """COC domain-specific constraint template values."""

    def test_strict_template(self):
        from praxis.domains.loader import DomainLoader

        loader = DomainLoader()
        tpl = loader.get_constraint_template("coc", "strict")
        assert tpl["financial"]["max_spend"] == 10.0
        assert tpl["temporal"]["max_duration_minutes"] == 60

    def test_moderate_template(self):
        from praxis.domains.loader import DomainLoader

        loader = DomainLoader()
        tpl = loader.get_constraint_template("coc", "moderate")
        assert tpl["financial"]["max_spend"] == 50.0
        assert tpl["temporal"]["max_duration_minutes"] == 120

    def test_permissive_template(self):
        from praxis.domains.loader import DomainLoader

        loader = DomainLoader()
        tpl = loader.get_constraint_template("coc", "permissive")
        assert tpl["financial"]["max_spend"] == 200.0
        assert tpl["temporal"]["max_duration_minutes"] == 480

    def test_templates_ordered_by_restrictiveness(self):
        """Strict <= moderate <= permissive for financial max_spend."""
        from praxis.domains.loader import DomainLoader

        loader = DomainLoader()
        s = loader.get_constraint_template("coc", "strict")
        m = loader.get_constraint_template("coc", "moderate")
        p = loader.get_constraint_template("coc", "permissive")
        assert (
            s["financial"]["max_spend"]
            <= m["financial"]["max_spend"]
            <= p["financial"]["max_spend"]
        )


class TestCoeConstraints:
    """COE domain-specific constraint template values."""

    def test_has_year_based_templates(self):
        from praxis.domains.loader import DomainLoader

        loader = DomainLoader()
        config = loader.load_domain("coe")
        # COE must have year1, year2, year3 at minimum
        assert "year1" in config.constraint_templates
        assert "year2" in config.constraint_templates
        assert "year3" in config.constraint_templates

    def test_year1_has_five_dimensions(self):
        from praxis.domains.loader import DomainLoader

        loader = DomainLoader()
        tpl = loader.get_constraint_template("coe", "year1")
        for dim in ["financial", "operational", "temporal", "data_access", "communication"]:
            assert dim in tpl, f"year1 missing {dim}"


class TestCogConstraints:
    """COG domain-specific constraint template values."""

    def test_has_governance_templates(self):
        from praxis.domains.loader import DomainLoader

        loader = DomainLoader()
        config = loader.load_domain("cog")
        assert "advisory" in config.constraint_templates
        assert "deliberative" in config.constraint_templates
        assert "executive" in config.constraint_templates


class TestCorConstraints:
    """COR domain-specific constraint template values."""

    def test_has_research_templates(self):
        from praxis.domains.loader import DomainLoader

        loader = DomainLoader()
        config = loader.load_domain("cor")
        assert "exploratory" in config.constraint_templates
        assert "formal" in config.constraint_templates
        assert "sensitive" in config.constraint_templates


class TestCocompConstraints:
    """COComp domain-specific constraint template values."""

    def test_has_compliance_templates(self):
        from praxis.domains.loader import DomainLoader

        loader = DomainLoader()
        config = loader.load_domain("cocomp")
        assert "internal" in config.constraint_templates
        assert "external" in config.constraint_templates


class TestCofConstraints:
    """COF domain-specific constraint template values."""

    def test_has_finance_templates(self):
        from praxis.domains.loader import DomainLoader

        loader = DomainLoader()
        config = loader.load_domain("cof")
        assert "analysis" in config.constraint_templates
        assert "advisory" in config.constraint_templates
        assert "trading" in config.constraint_templates


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


class TestDomainValidation:
    """DomainLoader.validate_domain must return empty list for valid domains."""

    def test_validate_all_domains_pass(self):
        from praxis.domains.loader import DomainLoader

        loader = DomainLoader()
        for domain in loader.list_domains():
            errors = loader.validate_domain(domain)
            assert errors == [], f"Domain '{domain}' has validation errors: {errors}"

    def test_validate_invalid_domain_returns_errors(self, tmp_path):
        """A domain.yml with missing required fields should produce errors."""
        from praxis.domains.loader import DomainLoader

        domain_dir = tmp_path / "bad_domain"
        domain_dir.mkdir()
        (domain_dir / "domain.yml").write_text("name: bad_domain\n")

        loader = DomainLoader(domains_dir=tmp_path)
        errors = loader.validate_domain("bad_domain")
        assert len(errors) > 0, "Invalid domain should produce validation errors"

    def test_validate_nonexistent_domain_returns_errors(self):
        from praxis.domains.loader import DomainLoader

        loader = DomainLoader()
        errors = loader.validate_domain("nonexistent")
        assert len(errors) > 0
        assert any("not found" in e.lower() or "nonexistent" in e.lower() for e in errors)


# ---------------------------------------------------------------------------
# DomainConfig dataclass
# ---------------------------------------------------------------------------


class TestDomainConfigDataclass:
    """DomainConfig must expose all expected attributes."""

    def test_attributes_exist(self):
        from praxis.domains.loader import DomainLoader

        loader = DomainLoader()
        config = loader.load_domain("coc")
        # All attributes must be accessible
        assert hasattr(config, "name")
        assert hasattr(config, "display_name")
        assert hasattr(config, "description")
        assert hasattr(config, "version")
        assert hasattr(config, "constraint_templates")
        assert hasattr(config, "phases")
        assert hasattr(config, "capture")

    def test_config_is_frozen_or_immutable(self):
        """DomainConfig should not allow mutation after creation."""
        from praxis.domains.loader import DomainLoader

        loader = DomainLoader()
        config = loader.load_domain("coc")
        with pytest.raises((AttributeError, TypeError)):
            config.name = "mutated"


# ---------------------------------------------------------------------------
# Caching behaviour
# ---------------------------------------------------------------------------


class TestDomainLoaderCache:
    """DomainLoader should cache loaded domains for performance."""

    def test_same_object_returned_on_second_load(self):
        from praxis.domains.loader import DomainLoader

        loader = DomainLoader()
        config1 = loader.load_domain("coc")
        config2 = loader.load_domain("coc")
        assert config1 is config2

    def test_reload_clears_cache(self):
        from praxis.domains.loader import DomainLoader

        loader = DomainLoader()
        config1 = loader.load_domain("coc")
        loader.reload()
        config2 = loader.load_domain("coc")
        assert config1 is not config2
        # But values should be identical
        assert config1.name == config2.name
        assert config1.version == config2.version


# ---------------------------------------------------------------------------
# core/domain.py — module-level convenience functions
# ---------------------------------------------------------------------------


class TestCoreDomainModule:
    """src/praxis/core/domain.py should expose convenience functions."""

    def test_get_domain_returns_config(self):
        from praxis.core.domain import get_domain

        config = get_domain("coc")
        assert config.name == "coc"

    def test_list_domains_convenience(self):
        from praxis.core.domain import list_domains

        domains = list_domains()
        assert set(domains) == {"coc", "coe", "cog", "cor", "cocomp", "cof"}

    def test_get_constraint_template_convenience(self):
        from praxis.core.domain import get_constraint_template

        tpl = get_constraint_template("coc", "moderate")
        assert "financial" in tpl
        assert "operational" in tpl


# ---------------------------------------------------------------------------
# Default constraint YAML files
# ---------------------------------------------------------------------------


class TestDefaultConstraintFiles:
    """Each domain should have a constraints/default.yml file."""

    def test_all_domains_have_default_constraints(self):
        """Each domain directory should contain constraints/default.yml."""
        domains_dir = Path(__file__).resolve().parent.parent.parent / "src" / "praxis" / "domains"
        for domain_name in ["coc", "coe", "cog", "cor", "cocomp", "cof"]:
            constraint_file = domains_dir / domain_name / "constraints" / "default.yml"
            assert (
                constraint_file.exists()
            ), f"Missing constraints/default.yml for domain '{domain_name}'"
