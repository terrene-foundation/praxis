# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""
Convenience functions for accessing CO domain configurations.

This module re-exports the key functions from praxis.domains.loader so that
other Praxis modules can import domain functionality from the core package:

    from praxis.core.domain import get_domain, list_domains, get_constraint_template
"""

from __future__ import annotations

from praxis.domains.loader import (
    DomainConfig,
    DomainLoader,
    DomainNotFoundError,
    DomainValidationError,
    get_constraint_template,
    get_domain,
    get_institutional_knowledge,
    get_knowledge_for_phase,
    list_domains,
)

__all__ = [
    "DomainConfig",
    "DomainLoader",
    "DomainNotFoundError",
    "DomainValidationError",
    "get_constraint_template",
    "get_domain",
    "get_institutional_knowledge",
    "get_knowledge_for_phase",
    "list_domains",
]
