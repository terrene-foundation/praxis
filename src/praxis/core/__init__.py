# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""
Praxis core runtime — session lifecycle, deliberation capture, and constraint enforcement.

Usage:
    from praxis.core import SessionManager, DeliberationEngine, ConstraintEnforcer

    mgr = SessionManager(key_manager=km, key_id="default")
    session = mgr.create_session(workspace_id="ws-001")
"""

from praxis.core.anti_amnesia import AntiAmnesiaInjector, AntiAmnesiaReminder
from praxis.core.audit_review import QualityReport, SessionAuditReviewer
from praxis.core.bainbridge import (
    CapabilityTracker,
    ConstraintReviewTracker,
    FatigueDetector,
    FatigueRisk,
)
from praxis.core.calibration import CalibrationAnalyzer
from praxis.core.constraint import (
    ConstraintEnforcer,
    ConstraintVerdict,
    GradientLevel,
    HeldAction,
    HeldActionManager,
)
from praxis.core.deliberation import DeliberationEngine
from praxis.core.learning import (
    EvolutionProposal,
    LearningPipeline,
    Observation,
    Pattern,
)
from praxis.core.rules import DomainRuleEngine, RuleWarning
from praxis.core.session import (
    InvalidStateTransitionError,
    PhaseGateError,
    SessionManager,
    SessionNotActiveError,
    SessionPreconditionError,
    SessionState,
)

__all__ = [
    "SessionManager",
    "SessionState",
    "InvalidStateTransitionError",
    "SessionNotActiveError",
    "SessionPreconditionError",
    "PhaseGateError",
    "DeliberationEngine",
    "ConstraintEnforcer",
    "ConstraintVerdict",
    "GradientLevel",
    "HeldAction",
    "HeldActionManager",
    "LearningPipeline",
    "Observation",
    "Pattern",
    "EvolutionProposal",
    "FatigueDetector",
    "FatigueRisk",
    "CapabilityTracker",
    "ConstraintReviewTracker",
    "CalibrationAnalyzer",
    "AntiAmnesiaInjector",
    "AntiAmnesiaReminder",
    "DomainRuleEngine",
    "RuleWarning",
    "SessionAuditReviewer",
    "QualityReport",
]
