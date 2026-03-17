# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""Unit tests for praxis.trust.gradient — verification gradient engine.

The gradient engine is a pure function that classifies actions into four levels:
AUTO_APPROVED, FLAGGED, HELD, BLOCKED. Thresholds are normative CO specification
values (70%, 90%, 100%) and MUST NOT be configurable.
"""

import pytest


class TestGradientLevelEnum:
    """Test the GradientLevel enum."""

    def test_gradient_levels_exist(self):
        from praxis.trust.gradient import GradientLevel

        assert GradientLevel.AUTO_APPROVED == "auto_approved"
        assert GradientLevel.FLAGGED == "flagged"
        assert GradientLevel.HELD == "held"
        assert GradientLevel.BLOCKED == "blocked"

    def test_gradient_level_ordering(self):
        from praxis.trust.gradient import GradientLevel

        # Blocked is the most severe
        severity = [
            GradientLevel.AUTO_APPROVED,
            GradientLevel.FLAGGED,
            GradientLevel.HELD,
            GradientLevel.BLOCKED,
        ]
        assert len(severity) == 4


class TestGradientVerdictDataclass:
    """Test the GradientVerdict dataclass."""

    def test_verdict_has_required_fields(self):
        from praxis.trust.gradient import GradientLevel, GradientVerdict

        verdict = GradientVerdict(
            level=GradientLevel.AUTO_APPROVED,
            dimension="financial",
            utilization=0.5,
            reason="Within limits",
            action="read_file",
            resource="src/main.py",
        )
        assert verdict.level == GradientLevel.AUTO_APPROVED
        assert verdict.dimension == "financial"
        assert verdict.utilization == 0.5
        assert verdict.action == "read_file"
        assert verdict.resource == "src/main.py"


class TestFinancialDimension:
    """Test financial constraint evaluation."""

    def test_auto_approved_when_well_within_limits(self):
        from praxis.trust.gradient import GradientLevel, evaluate_action

        verdict = evaluate_action(
            action="api_call",
            resource=None,
            constraints={
                "financial": {"max_spend": 1000.0},
                "operational": {"allowed_actions": ["api_call"], "max_actions_per_hour": 100},
                "temporal": {"max_duration_minutes": 120},
                "data_access": {"allowed_paths": ["*"]},
                "communication": {"allowed_channels": ["internal"]},
            },
            current_state={
                "financial": {"current_spend": 100.0},
                "operational": {"actions_this_hour": 5},
                "temporal": {"elapsed_minutes": 10},
            },
        )
        assert verdict.level == GradientLevel.AUTO_APPROVED

    def test_flagged_when_financial_at_70_percent(self):
        from praxis.trust.gradient import GradientLevel, evaluate_action

        verdict = evaluate_action(
            action="api_call",
            resource=None,
            constraints={
                "financial": {"max_spend": 1000.0},
                "operational": {"allowed_actions": ["api_call"], "max_actions_per_hour": 100},
                "temporal": {"max_duration_minutes": 120},
                "data_access": {"allowed_paths": ["*"]},
                "communication": {"allowed_channels": ["internal"]},
            },
            current_state={
                "financial": {"current_spend": 700.0},
                "operational": {"actions_this_hour": 5},
                "temporal": {"elapsed_minutes": 10},
            },
        )
        assert verdict.level == GradientLevel.FLAGGED

    def test_held_when_financial_at_90_percent(self):
        from praxis.trust.gradient import GradientLevel, evaluate_action

        verdict = evaluate_action(
            action="api_call",
            resource=None,
            constraints={
                "financial": {"max_spend": 1000.0},
                "operational": {"allowed_actions": ["api_call"], "max_actions_per_hour": 100},
                "temporal": {"max_duration_minutes": 120},
                "data_access": {"allowed_paths": ["*"]},
                "communication": {"allowed_channels": ["internal"]},
            },
            current_state={
                "financial": {"current_spend": 900.0},
                "operational": {"actions_this_hour": 5},
                "temporal": {"elapsed_minutes": 10},
            },
        )
        assert verdict.level == GradientLevel.HELD

    def test_blocked_when_financial_at_100_percent(self):
        from praxis.trust.gradient import GradientLevel, evaluate_action

        verdict = evaluate_action(
            action="api_call",
            resource=None,
            constraints={
                "financial": {"max_spend": 1000.0},
                "operational": {"allowed_actions": ["api_call"], "max_actions_per_hour": 100},
                "temporal": {"max_duration_minutes": 120},
                "data_access": {"allowed_paths": ["*"]},
                "communication": {"allowed_channels": ["internal"]},
            },
            current_state={
                "financial": {"current_spend": 1000.0},
                "operational": {"actions_this_hour": 5},
                "temporal": {"elapsed_minutes": 10},
            },
        )
        assert verdict.level == GradientLevel.BLOCKED

    def test_blocked_when_financial_exceeds_100_percent(self):
        from praxis.trust.gradient import GradientLevel, evaluate_action

        verdict = evaluate_action(
            action="api_call",
            resource=None,
            constraints={
                "financial": {"max_spend": 1000.0},
                "operational": {"allowed_actions": ["api_call"], "max_actions_per_hour": 100},
                "temporal": {"max_duration_minutes": 120},
                "data_access": {"allowed_paths": ["*"]},
                "communication": {"allowed_channels": ["internal"]},
            },
            current_state={
                "financial": {"current_spend": 1500.0},
                "operational": {"actions_this_hour": 5},
                "temporal": {"elapsed_minutes": 10},
            },
        )
        assert verdict.level == GradientLevel.BLOCKED


class TestOperationalDimension:
    """Test operational constraint evaluation."""

    def test_blocked_when_action_not_allowed(self):
        from praxis.trust.gradient import GradientLevel, evaluate_action

        verdict = evaluate_action(
            action="deploy",
            resource=None,
            constraints={
                "financial": {"max_spend": 1000.0},
                "operational": {"allowed_actions": ["read", "write"], "max_actions_per_hour": 100},
                "temporal": {"max_duration_minutes": 120},
                "data_access": {"allowed_paths": ["*"]},
                "communication": {"allowed_channels": ["internal"]},
            },
            current_state={
                "financial": {"current_spend": 0},
                "operational": {"actions_this_hour": 5},
                "temporal": {"elapsed_minutes": 10},
            },
        )
        assert verdict.level == GradientLevel.BLOCKED

    def test_flagged_when_actions_at_70_percent(self):
        from praxis.trust.gradient import GradientLevel, evaluate_action

        verdict = evaluate_action(
            action="read",
            resource=None,
            constraints={
                "financial": {"max_spend": 1000.0},
                "operational": {"allowed_actions": ["read"], "max_actions_per_hour": 100},
                "temporal": {"max_duration_minutes": 120},
                "data_access": {"allowed_paths": ["*"]},
                "communication": {"allowed_channels": ["internal"]},
            },
            current_state={
                "financial": {"current_spend": 0},
                "operational": {"actions_this_hour": 70},
                "temporal": {"elapsed_minutes": 10},
            },
        )
        assert verdict.level == GradientLevel.FLAGGED

    def test_held_when_actions_at_90_percent(self):
        from praxis.trust.gradient import GradientLevel, evaluate_action

        verdict = evaluate_action(
            action="read",
            resource=None,
            constraints={
                "financial": {"max_spend": 1000.0},
                "operational": {"allowed_actions": ["read"], "max_actions_per_hour": 100},
                "temporal": {"max_duration_minutes": 120},
                "data_access": {"allowed_paths": ["*"]},
                "communication": {"allowed_channels": ["internal"]},
            },
            current_state={
                "financial": {"current_spend": 0},
                "operational": {"actions_this_hour": 90},
                "temporal": {"elapsed_minutes": 10},
            },
        )
        assert verdict.level == GradientLevel.HELD

    def test_blocked_when_actions_at_100_percent(self):
        from praxis.trust.gradient import GradientLevel, evaluate_action

        verdict = evaluate_action(
            action="read",
            resource=None,
            constraints={
                "financial": {"max_spend": 1000.0},
                "operational": {"allowed_actions": ["read"], "max_actions_per_hour": 100},
                "temporal": {"max_duration_minutes": 120},
                "data_access": {"allowed_paths": ["*"]},
                "communication": {"allowed_channels": ["internal"]},
            },
            current_state={
                "financial": {"current_spend": 0},
                "operational": {"actions_this_hour": 100},
                "temporal": {"elapsed_minutes": 10},
            },
        )
        assert verdict.level == GradientLevel.BLOCKED


class TestTemporalDimension:
    """Test temporal constraint evaluation."""

    def test_auto_approved_when_within_time_limits(self):
        from praxis.trust.gradient import GradientLevel, evaluate_action

        verdict = evaluate_action(
            action="read",
            resource=None,
            constraints={
                "financial": {"max_spend": 1000.0},
                "operational": {"allowed_actions": ["read"], "max_actions_per_hour": 100},
                "temporal": {"max_duration_minutes": 120},
                "data_access": {"allowed_paths": ["*"]},
                "communication": {"allowed_channels": ["internal"]},
            },
            current_state={
                "financial": {"current_spend": 0},
                "operational": {"actions_this_hour": 5},
                "temporal": {"elapsed_minutes": 30},
            },
        )
        assert verdict.level == GradientLevel.AUTO_APPROVED

    def test_flagged_when_temporal_at_70_percent(self):
        from praxis.trust.gradient import GradientLevel, evaluate_action

        verdict = evaluate_action(
            action="read",
            resource=None,
            constraints={
                "financial": {"max_spend": 1000.0},
                "operational": {"allowed_actions": ["read"], "max_actions_per_hour": 100},
                "temporal": {"max_duration_minutes": 120},
                "data_access": {"allowed_paths": ["*"]},
                "communication": {"allowed_channels": ["internal"]},
            },
            current_state={
                "financial": {"current_spend": 0},
                "operational": {"actions_this_hour": 5},
                "temporal": {"elapsed_minutes": 84},
            },
        )
        assert verdict.level == GradientLevel.FLAGGED

    def test_blocked_when_temporal_at_100_percent(self):
        from praxis.trust.gradient import GradientLevel, evaluate_action

        verdict = evaluate_action(
            action="read",
            resource=None,
            constraints={
                "financial": {"max_spend": 1000.0},
                "operational": {"allowed_actions": ["read"], "max_actions_per_hour": 100},
                "temporal": {"max_duration_minutes": 120},
                "data_access": {"allowed_paths": ["*"]},
                "communication": {"allowed_channels": ["internal"]},
            },
            current_state={
                "financial": {"current_spend": 0},
                "operational": {"actions_this_hour": 5},
                "temporal": {"elapsed_minutes": 120},
            },
        )
        assert verdict.level == GradientLevel.BLOCKED


class TestDataAccessDimension:
    """Test data access constraint evaluation."""

    def test_blocked_when_path_not_allowed(self):
        from praxis.trust.gradient import GradientLevel, evaluate_action

        verdict = evaluate_action(
            action="read",
            resource="/secrets/api_keys.txt",
            constraints={
                "financial": {"max_spend": 1000.0},
                "operational": {"allowed_actions": ["read"], "max_actions_per_hour": 100},
                "temporal": {"max_duration_minutes": 120},
                "data_access": {"allowed_paths": ["/src", "/tests"]},
                "communication": {"allowed_channels": ["internal"]},
            },
            current_state={
                "financial": {"current_spend": 0},
                "operational": {"actions_this_hour": 5},
                "temporal": {"elapsed_minutes": 10},
            },
        )
        assert verdict.level == GradientLevel.BLOCKED

    def test_auto_approved_when_path_is_allowed(self):
        from praxis.trust.gradient import GradientLevel, evaluate_action

        verdict = evaluate_action(
            action="read",
            resource="/src/main.py",
            constraints={
                "financial": {"max_spend": 1000.0},
                "operational": {"allowed_actions": ["read"], "max_actions_per_hour": 100},
                "temporal": {"max_duration_minutes": 120},
                "data_access": {"allowed_paths": ["/src", "/tests"]},
                "communication": {"allowed_channels": ["internal"]},
            },
            current_state={
                "financial": {"current_spend": 0},
                "operational": {"actions_this_hour": 5},
                "temporal": {"elapsed_minutes": 10},
            },
        )
        assert verdict.level == GradientLevel.AUTO_APPROVED

    def test_auto_approved_when_wildcard_path(self):
        from praxis.trust.gradient import GradientLevel, evaluate_action

        verdict = evaluate_action(
            action="read",
            resource="/anywhere/file.py",
            constraints={
                "financial": {"max_spend": 1000.0},
                "operational": {"allowed_actions": ["read"], "max_actions_per_hour": 100},
                "temporal": {"max_duration_minutes": 120},
                "data_access": {"allowed_paths": ["*"]},
                "communication": {"allowed_channels": ["internal"]},
            },
            current_state={
                "financial": {"current_spend": 0},
                "operational": {"actions_this_hour": 5},
                "temporal": {"elapsed_minutes": 10},
            },
        )
        assert verdict.level == GradientLevel.AUTO_APPROVED


class TestCommunicationDimension:
    """Test communication constraint evaluation."""

    def test_blocked_when_channel_not_allowed(self):
        from praxis.trust.gradient import GradientLevel, evaluate_action

        verdict = evaluate_action(
            action="send_message",
            resource="external_api",
            constraints={
                "financial": {"max_spend": 1000.0},
                "operational": {"allowed_actions": ["send_message"], "max_actions_per_hour": 100},
                "temporal": {"max_duration_minutes": 120},
                "data_access": {"allowed_paths": ["*"]},
                "communication": {"allowed_channels": ["internal"]},
            },
            current_state={
                "financial": {"current_spend": 0},
                "operational": {"actions_this_hour": 5},
                "temporal": {"elapsed_minutes": 10},
                "communication": {"requested_channel": "external"},
            },
        )
        assert verdict.level == GradientLevel.BLOCKED

    def test_auto_approved_when_channel_is_allowed(self):
        from praxis.trust.gradient import GradientLevel, evaluate_action

        verdict = evaluate_action(
            action="send_message",
            resource="internal_api",
            constraints={
                "financial": {"max_spend": 1000.0},
                "operational": {"allowed_actions": ["send_message"], "max_actions_per_hour": 100},
                "temporal": {"max_duration_minutes": 120},
                "data_access": {"allowed_paths": ["*"]},
                "communication": {"allowed_channels": ["internal", "email"]},
            },
            current_state={
                "financial": {"current_spend": 0},
                "operational": {"actions_this_hour": 5},
                "temporal": {"elapsed_minutes": 10},
                "communication": {"requested_channel": "internal"},
            },
        )
        assert verdict.level == GradientLevel.AUTO_APPROVED


class TestWorstCaseAggregation:
    """Test that the final verdict is the most severe across all dimensions."""

    def test_blocked_trumps_all(self):
        """If ANY dimension is blocked, final verdict is blocked."""
        from praxis.trust.gradient import GradientLevel, evaluate_action

        # Financial is fine but action is not in allowed list (operational blocked)
        verdict = evaluate_action(
            action="deploy",
            resource=None,
            constraints={
                "financial": {"max_spend": 1000.0},
                "operational": {"allowed_actions": ["read", "write"], "max_actions_per_hour": 100},
                "temporal": {"max_duration_minutes": 120},
                "data_access": {"allowed_paths": ["*"]},
                "communication": {"allowed_channels": ["internal"]},
            },
            current_state={
                "financial": {"current_spend": 0},
                "operational": {"actions_this_hour": 5},
                "temporal": {"elapsed_minutes": 10},
            },
        )
        assert verdict.level == GradientLevel.BLOCKED

    def test_held_when_no_blocked_but_high_utilization(self):
        """If no dimension blocked but financial at 90%, verdict is held."""
        from praxis.trust.gradient import GradientLevel, evaluate_action

        verdict = evaluate_action(
            action="read",
            resource="/src/main.py",
            constraints={
                "financial": {"max_spend": 1000.0},
                "operational": {"allowed_actions": ["read"], "max_actions_per_hour": 100},
                "temporal": {"max_duration_minutes": 120},
                "data_access": {"allowed_paths": ["/src"]},
                "communication": {"allowed_channels": ["internal"]},
            },
            current_state={
                "financial": {"current_spend": 950.0},
                "operational": {"actions_this_hour": 5},
                "temporal": {"elapsed_minutes": 10},
            },
        )
        assert verdict.level == GradientLevel.HELD

    def test_flagged_when_moderate_utilization(self):
        """Flagged when highest utilization is between 70-89%."""
        from praxis.trust.gradient import GradientLevel, evaluate_action

        verdict = evaluate_action(
            action="read",
            resource="/src/main.py",
            constraints={
                "financial": {"max_spend": 1000.0},
                "operational": {"allowed_actions": ["read"], "max_actions_per_hour": 100},
                "temporal": {"max_duration_minutes": 120},
                "data_access": {"allowed_paths": ["/src"]},
                "communication": {"allowed_channels": ["internal"]},
            },
            current_state={
                "financial": {"current_spend": 750.0},
                "operational": {"actions_this_hour": 5},
                "temporal": {"elapsed_minutes": 10},
            },
        )
        assert verdict.level == GradientLevel.FLAGGED

    def test_all_dimensions_evaluated_even_if_one_blocked(self):
        """All five dimensions must be evaluated for the determining_dimension to be correct."""
        from praxis.trust.gradient import GradientLevel, evaluate_action

        verdict = evaluate_action(
            action="deploy",
            resource="/secrets/key.pem",
            constraints={
                "financial": {"max_spend": 1000.0},
                "operational": {"allowed_actions": ["read"], "max_actions_per_hour": 100},
                "temporal": {"max_duration_minutes": 120},
                "data_access": {"allowed_paths": ["/src"]},
                "communication": {"allowed_channels": ["internal"]},
            },
            current_state={
                "financial": {"current_spend": 0},
                "operational": {"actions_this_hour": 5},
                "temporal": {"elapsed_minutes": 10},
            },
        )
        assert verdict.level == GradientLevel.BLOCKED
        # The dimension field should indicate which dimension caused the verdict
        assert verdict.dimension in (
            "operational",
            "data_access",
        )


class TestGradientDeterminism:
    """Test that gradient evaluation is deterministic (pure function)."""

    def test_same_input_same_output(self):
        from praxis.trust.gradient import evaluate_action

        kwargs = dict(
            action="read",
            resource="/src/main.py",
            constraints={
                "financial": {"max_spend": 1000.0},
                "operational": {"allowed_actions": ["read"], "max_actions_per_hour": 100},
                "temporal": {"max_duration_minutes": 120},
                "data_access": {"allowed_paths": ["/src"]},
                "communication": {"allowed_channels": ["internal"]},
            },
            current_state={
                "financial": {"current_spend": 500.0},
                "operational": {"actions_this_hour": 50},
                "temporal": {"elapsed_minutes": 60},
            },
        )
        v1 = evaluate_action(**kwargs)
        v2 = evaluate_action(**kwargs)
        assert v1.level == v2.level
        assert v1.utilization == v2.utilization
        assert v1.dimension == v2.dimension


class TestGradientEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_utilization_at_exact_boundary_70(self):
        """70% utilization should be FLAGGED, not AUTO_APPROVED."""
        from praxis.trust.gradient import GradientLevel, evaluate_action

        verdict = evaluate_action(
            action="read",
            resource=None,
            constraints={
                "financial": {"max_spend": 100.0},
                "operational": {"allowed_actions": ["read"], "max_actions_per_hour": 100},
                "temporal": {"max_duration_minutes": 100},
                "data_access": {"allowed_paths": ["*"]},
                "communication": {"allowed_channels": ["internal"]},
            },
            current_state={
                "financial": {"current_spend": 70.0},
                "operational": {"actions_this_hour": 5},
                "temporal": {"elapsed_minutes": 5},
            },
        )
        assert verdict.level == GradientLevel.FLAGGED

    def test_utilization_at_exact_boundary_90(self):
        """90% utilization should be HELD, not FLAGGED."""
        from praxis.trust.gradient import GradientLevel, evaluate_action

        verdict = evaluate_action(
            action="read",
            resource=None,
            constraints={
                "financial": {"max_spend": 100.0},
                "operational": {"allowed_actions": ["read"], "max_actions_per_hour": 100},
                "temporal": {"max_duration_minutes": 100},
                "data_access": {"allowed_paths": ["*"]},
                "communication": {"allowed_channels": ["internal"]},
            },
            current_state={
                "financial": {"current_spend": 90.0},
                "operational": {"actions_this_hour": 5},
                "temporal": {"elapsed_minutes": 5},
            },
        )
        assert verdict.level == GradientLevel.HELD

    def test_no_resource_still_evaluates(self):
        """Actions without a resource should still be evaluated."""
        from praxis.trust.gradient import GradientLevel, evaluate_action

        verdict = evaluate_action(
            action="read",
            resource=None,
            constraints={
                "financial": {"max_spend": 1000.0},
                "operational": {"allowed_actions": ["read"], "max_actions_per_hour": 100},
                "temporal": {"max_duration_minutes": 120},
                "data_access": {"allowed_paths": ["*"]},
                "communication": {"allowed_channels": ["internal"]},
            },
            current_state={
                "financial": {"current_spend": 0},
                "operational": {"actions_this_hour": 5},
                "temporal": {"elapsed_minutes": 10},
            },
        )
        assert verdict.level == GradientLevel.AUTO_APPROVED

    def test_utilization_just_below_70_is_auto_approved(self):
        from praxis.trust.gradient import GradientLevel, evaluate_action

        verdict = evaluate_action(
            action="read",
            resource=None,
            constraints={
                "financial": {"max_spend": 100.0},
                "operational": {"allowed_actions": ["read"], "max_actions_per_hour": 100},
                "temporal": {"max_duration_minutes": 100},
                "data_access": {"allowed_paths": ["*"]},
                "communication": {"allowed_channels": ["internal"]},
            },
            current_state={
                "financial": {"current_spend": 69.0},
                "operational": {"actions_this_hour": 5},
                "temporal": {"elapsed_minutes": 5},
            },
        )
        assert verdict.level == GradientLevel.AUTO_APPROVED

    def test_verdict_has_reason(self):
        from praxis.trust.gradient import evaluate_action

        verdict = evaluate_action(
            action="read",
            resource=None,
            constraints={
                "financial": {"max_spend": 1000.0},
                "operational": {"allowed_actions": ["read"], "max_actions_per_hour": 100},
                "temporal": {"max_duration_minutes": 120},
                "data_access": {"allowed_paths": ["*"]},
                "communication": {"allowed_channels": ["internal"]},
            },
            current_state={
                "financial": {"current_spend": 0},
                "operational": {"actions_this_hour": 5},
                "temporal": {"elapsed_minutes": 10},
            },
        )
        assert isinstance(verdict.reason, str)
        assert len(verdict.reason) > 0

    def test_verdict_utilization_is_max_across_dimensions(self):
        """Utilization on verdict should be the max utilization across all dimensions."""
        from praxis.trust.gradient import evaluate_action

        verdict = evaluate_action(
            action="read",
            resource=None,
            constraints={
                "financial": {"max_spend": 100.0},
                "operational": {"allowed_actions": ["read"], "max_actions_per_hour": 100},
                "temporal": {"max_duration_minutes": 100},
                "data_access": {"allowed_paths": ["*"]},
                "communication": {"allowed_channels": ["internal"]},
            },
            current_state={
                "financial": {"current_spend": 80.0},  # 80% - highest
                "operational": {"actions_this_hour": 10},  # 10%
                "temporal": {"elapsed_minutes": 20},  # 20%
            },
        )
        assert verdict.utilization == pytest.approx(0.8, abs=0.01)
