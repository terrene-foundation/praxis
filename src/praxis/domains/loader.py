# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""
Domain configuration loader for Praxis CO domains.

Discovers, loads, validates, and caches domain configurations from YAML files.
Each domain directory contains a domain.yml and constraints/default.yml.

Usage:
    from praxis.domains.loader import DomainLoader

    loader = DomainLoader()
    config = loader.load_domain("coc")
    template = loader.get_constraint_template("coc", "moderate")
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from praxis.domains.schema import CONSTRAINT_DIMENSIONS, DOMAIN_SCHEMA

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class DomainNotFoundError(FileNotFoundError):
    """Raised when a requested domain directory or domain.yml does not exist."""

    def __init__(self, domain_name: str, domains_dir: Path):
        self.domain_name = domain_name
        self.domains_dir = domains_dir
        super().__init__(
            f"Domain '{domain_name}' not found. "
            f"No domain.yml at '{domains_dir / domain_name / 'domain.yml'}'. "
            f"Available domains: {_list_domain_dirs(domains_dir)}"
        )


class DomainValidationError(ValueError):
    """Raised when a domain configuration fails validation."""

    def __init__(self, domain_name: str, errors: list[str]):
        self.domain_name = domain_name
        self.errors = errors
        formatted = "\n  - ".join(errors)
        super().__init__(
            f"Domain '{domain_name}' has {len(errors)} validation error(s):\n  - {formatted}"
        )


# ---------------------------------------------------------------------------
# DomainConfig dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DomainConfig:
    """Loaded and validated domain configuration.

    Frozen to prevent mutation after creation. All data originates from
    domain.yml and constraints/default.yml in the domain directory.
    """

    name: str
    display_name: str
    description: str
    version: str
    constraint_templates: dict[str, dict[str, Any]]
    phases: list[dict[str, Any]]
    capture: dict[str, Any]
    knowledge: dict[str, Any] | None = None
    anti_amnesia: list[dict[str, Any]] | None = None
    rules: list[dict[str, Any]] | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _list_domain_dirs(domains_dir: Path) -> list[str]:
    """Return sorted list of subdirectories that contain a domain.yml."""
    if not domains_dir.is_dir():
        return []
    return sorted(
        d.name for d in domains_dir.iterdir() if d.is_dir() and (d / "domain.yml").exists()
    )


def _validate_schema(data: dict, domain_name: str) -> list[str]:
    """Validate a domain config dict against the JSON Schema.

    Returns a list of human-readable error strings. Empty list means valid.
    """
    errors: list[str] = []

    try:
        import jsonschema

        validator = jsonschema.Draft7Validator(DOMAIN_SCHEMA)
        for error in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
            path = ".".join(str(p) for p in error.absolute_path) or "(root)"
            errors.append(f"{domain_name}/domain.yml: {path}: {error.message}")
    except ImportError:
        # jsonschema not installed — fall back to manual checks
        logger.warning(
            "jsonschema package not installed; using basic validation for domain '%s'",
            domain_name,
        )
        errors.extend(_validate_basic(data, domain_name))

    return errors


def _validate_basic(data: dict, domain_name: str) -> list[str]:
    """Minimal validation without jsonschema — checks required top-level fields."""
    errors: list[str] = []
    required_fields = [
        "name",
        "display_name",
        "description",
        "version",
        "constraint_templates",
        "phases",
        "capture",
    ]
    for field in required_fields:
        if field not in data:
            errors.append(f"{domain_name}/domain.yml: '{field}' is required but missing")

    # Validate constraint templates have all 5 dimensions
    templates = data.get("constraint_templates", {})
    if isinstance(templates, dict):
        for tpl_name, tpl_data in templates.items():
            if not isinstance(tpl_data, dict):
                errors.append(
                    f"{domain_name}/domain.yml: constraint_templates.{tpl_name} "
                    f"must be an object"
                )
                continue
            for dim in CONSTRAINT_DIMENSIONS:
                if dim not in tpl_data:
                    errors.append(
                        f"{domain_name}/domain.yml: constraint_templates.{tpl_name} "
                        f"is missing dimension '{dim}'"
                    )
            # Check that no unexpected keys exist (only dimensions + optional rationale)
            allowed_keys = set(CONSTRAINT_DIMENSIONS) | {"rationale"}
            for key in tpl_data:
                if key not in allowed_keys:
                    errors.append(
                        f"{domain_name}/domain.yml: constraint_templates.{tpl_name} "
                        f"has unexpected key '{key}'"
                    )

    return errors


# ---------------------------------------------------------------------------
# DomainLoader
# ---------------------------------------------------------------------------


class DomainLoader:
    """Discovers and loads CO domain configurations from YAML files.

    Attributes:
        domains_dir: Directory containing domain subdirectories.
            Defaults to the built-in domains at src/praxis/domains/.
    """

    def __init__(self, domains_dir: Path | None = None):
        if domains_dir is not None:
            self._domains_dir = Path(domains_dir)
        else:
            # Default: the directory containing this file (src/praxis/domains/)
            self._domains_dir = Path(__file__).parent

        self._cache: dict[str, DomainConfig] = {}

        logger.debug("DomainLoader initialised with domains_dir=%s", self._domains_dir)

    # -- Public API --------------------------------------------------------

    def list_domains(self) -> list[str]:
        """List available domain names (sorted alphabetically).

        A domain is any subdirectory of domains_dir that contains a domain.yml.
        """
        return _list_domain_dirs(self._domains_dir)

    def load_domain(self, name: str) -> DomainConfig:
        """Load and validate a domain configuration.

        Returns a frozen DomainConfig. Results are cached — subsequent calls
        for the same domain return the same object.

        Raises:
            FileNotFoundError: If the domain directory or domain.yml is missing.
            DomainValidationError: If the YAML fails schema validation.
        """
        if name in self._cache:
            return self._cache[name]

        domain_dir = self._domains_dir / name
        domain_yml = domain_dir / "domain.yml"

        if not domain_yml.exists():
            raise DomainNotFoundError(name, self._domains_dir)

        raw = yaml.safe_load(domain_yml.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise DomainValidationError(
                name, [f"{name}/domain.yml: expected a YAML mapping, got {type(raw).__name__}"]
            )

        # Validate
        errors = _validate_schema(raw, name)
        if errors:
            raise DomainValidationError(name, errors)

        config = DomainConfig(
            name=raw["name"],
            display_name=raw["display_name"],
            description=raw["description"],
            version=raw["version"],
            constraint_templates=dict(raw["constraint_templates"]),
            phases=list(raw["phases"]),
            capture=dict(raw["capture"]),
            knowledge=dict(raw["knowledge"]) if "knowledge" in raw else None,
            anti_amnesia=list(raw["anti_amnesia"]) if "anti_amnesia" in raw else None,
            rules=list(raw["rules"]) if "rules" in raw else None,
        )

        self._cache[name] = config
        logger.info(
            "Loaded domain '%s' (v%s) with %d constraint templates",
            config.name,
            config.version,
            len(config.constraint_templates),
        )
        return config

    def get_constraint_template(self, domain: str, template: str) -> dict[str, Any]:
        """Get a specific constraint template from a domain.

        Returns the template as a dict with keys for each of the five
        CO constraint dimensions (financial, operational, temporal,
        data_access, communication).

        Raises:
            FileNotFoundError: If the domain does not exist.
            KeyError: If the template name is not found in the domain.
        """
        config = self.load_domain(domain)
        if template not in config.constraint_templates:
            available = ", ".join(sorted(config.constraint_templates.keys()))
            raise KeyError(
                f"Constraint template '{template}' not found in domain '{domain}'. "
                f"Available templates: {available}"
            )
        return config.constraint_templates[template]

    def validate_domain(self, name: str) -> list[str]:
        """Validate a domain configuration and return a list of errors.

        Returns an empty list if the domain is valid.
        Returns a non-empty list of human-readable error strings if invalid.
        Does NOT raise exceptions — all errors are returned as strings.
        """
        domain_dir = self._domains_dir / name
        domain_yml = domain_dir / "domain.yml"

        if not domain_yml.exists():
            return [f"Domain '{name}' not found: {domain_yml} does not exist"]

        try:
            raw = yaml.safe_load(domain_yml.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            return [f"Domain '{name}' YAML parse error: {exc}"]

        if not isinstance(raw, dict):
            return [f"{name}/domain.yml: expected a YAML mapping, got {type(raw).__name__}"]

        return _validate_schema(raw, name)

    def reload(self, domain: str | None = None) -> None:
        """Clear the cache for a specific domain, or all domains.

        After reload, the next load_domain() call will re-read from disk.
        """
        if domain:
            self._cache.pop(domain, None)
            logger.debug("Cleared cache for domain '%s'", domain)
        else:
            self._cache.clear()
            logger.debug("Cleared all domain caches")


# ---------------------------------------------------------------------------
# Knowledge functions
# ---------------------------------------------------------------------------


def get_institutional_knowledge(domain: str) -> list[dict[str, Any]]:
    """Return only institutional knowledge entries for a domain.

    Filters the domain's knowledge classification to entries where
    type == "institutional". Returns an empty list if the domain has
    no knowledge section or no institutional entries.

    Args:
        domain: CO domain name (coc, coe, cog, etc.).

    Returns:
        List of knowledge entry dicts with type, content, and priority.
    """
    config = _get_loader().load_domain(domain)
    if config.knowledge is None:
        return []
    entries = config.knowledge.get("classification", [])
    return [e for e in entries if e.get("type") == "institutional"]


def get_knowledge_for_phase(domain: str, phase: str) -> list[dict[str, Any]]:
    """Return knowledge entries appropriate for the current workflow phase.

    Implements progressive disclosure: early phases (before the midpoint of
    the domain's phase list) receive only high-priority knowledge (P0, P1),
    while later phases receive all knowledge entries.

    This allows the MCP proxy to build context preambles that do not
    overwhelm early-stage work with supplementary information.

    Args:
        domain: CO domain name (coc, coe, cog, etc.).
        phase: Current workflow phase name (e.g. "analyze", "implement").

    Returns:
        List of knowledge entry dicts filtered by phase-appropriate priority.
    """
    config = _get_loader().load_domain(domain)
    if config.knowledge is None:
        return []

    entries = config.knowledge.get("classification", [])
    if not entries:
        return []

    # Determine the phase index — phases appearing in the first half of
    # the list are "early", phases in the second half are "late".
    phase_names = [p["name"] for p in config.phases]
    midpoint = len(phase_names) // 2

    try:
        phase_idx = phase_names.index(phase)
    except ValueError:
        # Unknown phase — return high-priority only as the safe default
        phase_idx = 0

    if phase_idx < midpoint:
        # Early phase: high-priority only (P0, P1)
        return [e for e in entries if e.get("priority") in ("P0", "P1")]
    else:
        # Late phase: all priorities
        return list(entries)


# ---------------------------------------------------------------------------
# Module-level singleton for convenience
# ---------------------------------------------------------------------------

_default_loader: DomainLoader | None = None


def _get_loader() -> DomainLoader:
    """Return the module-level singleton DomainLoader, creating it on first use."""
    global _default_loader
    if _default_loader is None:
        _default_loader = DomainLoader()
    return _default_loader


def get_domain(domain: str) -> DomainConfig:
    """Load a domain configuration using the default loader."""
    return _get_loader().load_domain(domain)


def get_constraint_template(domain: str, template: str) -> dict[str, Any]:
    """Get a constraint template using the default loader."""
    return _get_loader().get_constraint_template(domain, template)


def list_domains() -> list[str]:
    """List available domains using the default loader."""
    return _get_loader().list_domains()
