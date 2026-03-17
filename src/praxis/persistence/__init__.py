# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""
Praxis persistence layer — DataFlow-backed storage for sessions, trust chains,
deliberation records, constraint events, and workspaces.

Usage:
    from praxis.persistence import get_db, Session, Workspace

    db = get_db()
    # Use db with DataFlow CRUD operations
"""

from __future__ import annotations

import logging
from typing import Optional

from dataflow import DataFlow

from praxis.persistence.models import (
    ALL_MODELS,
    ConstraintEvent,
    DeliberationRecord,
    HeldAction,
    LearningEvolutionProposal,
    LearningObservation,
    LearningPattern,
    Session,
    TrustChainEntry,
    User,
    Workspace,
)

logger = logging.getLogger(__name__)

_db: Optional[DataFlow] = None
_models_registered: bool = False
_tables_created: bool = False


def _register_models(db: DataFlow) -> None:
    """Register all Praxis models with a DataFlow instance.

    Models are defined as plain annotated classes in models.py,
    then registered here using the @db.model decorator at runtime.
    This avoids the chicken-and-egg problem of needing a db instance
    at class definition time.
    """
    # DataFlow API compatibility: newer versions use db.models (list of ModelDefinition),
    # older/PyPI versions use db._models (dict). Support both.
    if hasattr(db, "models") and db.models:
        registered_names = {m.name for m in db.models}
    elif hasattr(db, "_models") and db._models:
        registered_names = set(db._models.keys())
    else:
        registered_names = set()
    for model_cls in ALL_MODELS:
        model_name = model_cls.__name__
        if model_name not in registered_names:
            db.model(model_cls)
            registered_names.add(model_name)
            logger.debug("Registered DataFlow model: %s", model_name)
        else:
            logger.debug("DataFlow model already registered: %s", model_name)


def get_db() -> DataFlow:
    """Get the DataFlow instance, lazily initialized.

    On first call:
    1. Reads database_url from PraxisConfig
    2. Creates a DataFlow instance
    3. Registers all 5 Praxis models

    Subsequent calls return the cached instance.

    Returns:
        Configured DataFlow instance with all models registered.

    Raises:
        praxis.config.PraxisConfigError: If required config values are missing.
    """
    global _db, _models_registered, _tables_created
    if _db is None:
        from praxis.config import get_config

        config = get_config()
        _db = DataFlow(config.database_url)
        logger.info("DataFlow initialized with database: %s", config.database_url)

    if not _models_registered:
        _register_models(_db)
        _models_registered = True

    if not _tables_created:
        _db.create_tables_sync()
        _tables_created = True
        logger.info("Database tables created/verified")

    return _db


def reset_db() -> None:
    """Clear the cached DataFlow instance. Used in tests to reinitialize."""
    global _db, _models_registered, _tables_created
    _db = None
    _models_registered = False
    _tables_created = False


__all__ = [
    "get_db",
    "reset_db",
    "Session",
    "DeliberationRecord",
    "ConstraintEvent",
    "TrustChainEntry",
    "Workspace",
    "HeldAction",
    "LearningObservation",
    "LearningPattern",
    "LearningEvolutionProposal",
    "User",
]
