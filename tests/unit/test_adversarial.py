# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""
Red team round 3: adversarial inputs, boundary conditions, and edge cases.

Targets:
    1. Constraint enforcer with malicious/extreme inputs
    2. Trust chain with malformed entries
    3. CLI with adversarial inputs
    4. Domain YAML loader with malformed configurations
    5. Bundle builder edge cases
"""

import hashlib
import json
import math
import tempfile
import time
import zipfile
from pathlib import Path

import jcs
import pytest
from click.testing import CliRunner


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_full_constraints(**overrides):
    """Build a full 5-dimension constraint envelope with optional overrides."""
    base = {
        "financial": {"max_spend": 100.0, "current_spend": 0.0},
        "operational": {
            "allowed_actions": ["read", "write", "execute", "send"],
            "blocked_actions": [],
        },
        "temporal": {"max_duration_minutes": 120, "elapsed_minutes": 0},
        "data_access": {"allowed_paths": ["/src/", "/tests/"], "blocked_paths": ["/secrets/"]},
        "communication": {
            "allowed_channels": ["internal"],
            "blocked_channels": ["external"],
        },
    }
    base.update(overrides)
    return base


# ============================================================================
# PART 1: ADVERSARIAL CONSTRAINT INPUTS
# ============================================================================


class TestConstraintZeroMaxSpend:
    """Attack: zero max_spend with non-zero current_spend.

    This could trigger division by zero in utilization calculations.
    """

    def test_zero_max_spend_zero_current_spend(self):
        """Zero budget, no spend -- should be auto-approved (0/0 => 0.0)."""
        from praxis.core.constraint import ConstraintEnforcer, GradientLevel

        constraints = _make_full_constraints(
            financial={"max_spend": 0, "current_spend": 0},
        )
        enforcer = ConstraintEnforcer(constraints)
        verdict = enforcer.evaluate("read")
        # With max_spend == 0, utilization defaults to 0.0 (no budget means no cost)
        assert verdict.level == GradientLevel.AUTO_APPROVED

    def test_zero_max_spend_nonzero_current_spend(self):
        """Zero budget but already spent money -- must not crash.

        This is the classic division-by-zero case. The enforcer should
        handle it gracefully, not raise ZeroDivisionError.
        """
        from praxis.core.constraint import ConstraintEnforcer, GradientLevel

        constraints = _make_full_constraints(
            financial={"max_spend": 0, "current_spend": 50.0},
        )
        enforcer = ConstraintEnforcer(constraints)
        # Must not raise
        verdict = enforcer.evaluate("read")
        # Utilization should be 0.0 (the current code defaults to 0.0 when max_spend == 0)
        # This means spending is not tracked when budget is zero -- acceptable.
        assert isinstance(verdict.level, GradientLevel)

    def test_zero_max_spend_with_action_cost(self):
        """Zero budget but action has a cost -- must not crash."""
        from praxis.core.constraint import ConstraintEnforcer, GradientLevel

        constraints = _make_full_constraints(
            financial={"max_spend": 0, "current_spend": 0},
        )
        enforcer = ConstraintEnforcer(constraints)
        verdict = enforcer.evaluate("write", context={"cost": 10.0})
        # projected_spend=10 > max_spend=0, but the code checks `max_spend > 0` first
        # So it goes to the utilization path with utilization=0.0
        assert isinstance(verdict.level, GradientLevel)

    def test_zero_max_spend_get_status_no_crash(self):
        """get_status with zero max_spend must not crash."""
        from praxis.core.constraint import ConstraintEnforcer

        constraints = _make_full_constraints(
            financial={"max_spend": 0, "current_spend": 50.0},
        )
        enforcer = ConstraintEnforcer(constraints)
        # Must not raise ZeroDivisionError
        status = enforcer.get_status()
        assert "financial" in status
        assert status["financial"]["utilization"] == 0.0


class TestConstraintNegativeValues:
    """Attack: negative values for spend, duration, actions."""

    def test_negative_current_spend(self):
        """Negative current_spend (refund?) -- must not crash."""
        from praxis.core.constraint import ConstraintEnforcer, GradientLevel

        constraints = _make_full_constraints(
            financial={"max_spend": 100.0, "current_spend": -50.0},
        )
        enforcer = ConstraintEnforcer(constraints)
        verdict = enforcer.evaluate("read")
        # -50/100 = -50% utilization -- should be AUTO_APPROVED (below 70%)
        assert verdict.level == GradientLevel.AUTO_APPROVED

    def test_negative_max_spend(self):
        """Negative max_spend -- absurd but must not crash."""
        from praxis.core.constraint import ConstraintEnforcer, GradientLevel

        constraints = _make_full_constraints(
            financial={"max_spend": -100.0, "current_spend": 0.0},
        )
        enforcer = ConstraintEnforcer(constraints)
        verdict = enforcer.evaluate("read")
        # max_spend < 0 so max_spend > 0 is False, utilization defaults to 0.0
        assert isinstance(verdict.level, GradientLevel)

    def test_negative_elapsed_minutes(self):
        """Negative elapsed time -- must not crash."""
        from praxis.core.constraint import ConstraintEnforcer, GradientLevel

        constraints = _make_full_constraints(
            temporal={"max_duration_minutes": 120, "elapsed_minutes": -10},
        )
        enforcer = ConstraintEnforcer(constraints)
        verdict = enforcer.evaluate("read")
        assert verdict.level == GradientLevel.AUTO_APPROVED

    def test_negative_max_duration(self):
        """Negative max_duration -- must not crash."""
        from praxis.core.constraint import ConstraintEnforcer, GradientLevel

        constraints = _make_full_constraints(
            temporal={"max_duration_minutes": -60, "elapsed_minutes": 0},
        )
        enforcer = ConstraintEnforcer(constraints)
        verdict = enforcer.evaluate("read")
        assert isinstance(verdict.level, GradientLevel)

    def test_negative_action_cost(self):
        """Negative action cost -- must not crash."""
        from praxis.core.constraint import ConstraintEnforcer, GradientLevel

        constraints = _make_full_constraints(
            financial={"max_spend": 100.0, "current_spend": 80.0},
        )
        enforcer = ConstraintEnforcer(constraints)
        verdict = enforcer.evaluate("write", context={"cost": -50.0})
        # 80 + (-50) = 30, so 30/100 = 30% => AUTO_APPROVED
        assert verdict.level == GradientLevel.AUTO_APPROVED


class TestConstraintExtremeValues:
    """Attack: extremely large values (10^18)."""

    def test_extreme_max_spend(self):
        """Extremely large max_spend -- must handle gracefully."""
        from praxis.core.constraint import ConstraintEnforcer, GradientLevel

        constraints = _make_full_constraints(
            financial={"max_spend": 1e18, "current_spend": 0.0},
        )
        enforcer = ConstraintEnforcer(constraints)
        verdict = enforcer.evaluate("read")
        assert verdict.level == GradientLevel.AUTO_APPROVED

    def test_extreme_current_spend(self):
        """Extremely large current_spend -- must handle gracefully."""
        from praxis.core.constraint import ConstraintEnforcer, GradientLevel

        constraints = _make_full_constraints(
            financial={"max_spend": 100.0, "current_spend": 1e18},
        )
        enforcer = ConstraintEnforcer(constraints)
        verdict = enforcer.evaluate("read")
        # 1e18/100 >> 1.0 => BLOCKED
        assert verdict.level == GradientLevel.BLOCKED

    def test_extreme_elapsed_minutes(self):
        """Extremely large elapsed_minutes -- must handle gracefully."""
        from praxis.core.constraint import ConstraintEnforcer, GradientLevel

        constraints = _make_full_constraints(
            temporal={"max_duration_minutes": 120, "elapsed_minutes": 1e18},
        )
        enforcer = ConstraintEnforcer(constraints)
        verdict = enforcer.evaluate("read")
        assert verdict.level == GradientLevel.BLOCKED

    def test_extreme_action_cost(self):
        """Action cost of 10^18 -- must not crash."""
        from praxis.core.constraint import ConstraintEnforcer, GradientLevel

        constraints = _make_full_constraints(
            financial={"max_spend": 100.0, "current_spend": 0.0},
        )
        enforcer = ConstraintEnforcer(constraints)
        verdict = enforcer.evaluate("write", context={"cost": 1e18})
        assert verdict.level == GradientLevel.BLOCKED

    def test_both_extreme(self):
        """Both max_spend and current_spend at 10^18 -- edge case."""
        from praxis.core.constraint import ConstraintEnforcer, GradientLevel

        constraints = _make_full_constraints(
            financial={"max_spend": 1e18, "current_spend": 1e18},
        )
        enforcer = ConstraintEnforcer(constraints)
        verdict = enforcer.evaluate("read")
        # 1e18/1e18 = 1.0 => BLOCKED
        assert verdict.level == GradientLevel.BLOCKED


class TestConstraintSpecialFloats:
    """Attack: NaN, Infinity, -Infinity in financial/temporal values."""

    def test_nan_current_spend(self):
        """NaN current_spend -- must handle without crash."""
        from praxis.core.constraint import ConstraintEnforcer, GradientLevel

        constraints = _make_full_constraints(
            financial={"max_spend": 100.0, "current_spend": float("nan")},
        )
        enforcer = ConstraintEnforcer(constraints)
        verdict = enforcer.evaluate("read")
        # NaN / 100 = NaN -> _gradient_for_utilization handles non-finite as BLOCKED
        assert verdict.level == GradientLevel.BLOCKED

    def test_inf_current_spend(self):
        """Infinity current_spend -- must not crash."""
        from praxis.core.constraint import ConstraintEnforcer, GradientLevel

        constraints = _make_full_constraints(
            financial={"max_spend": 100.0, "current_spend": float("inf")},
        )
        enforcer = ConstraintEnforcer(constraints)
        verdict = enforcer.evaluate("read")
        assert verdict.level == GradientLevel.BLOCKED

    def test_neg_inf_current_spend(self):
        """Negative infinity current_spend -- must not crash."""
        from praxis.core.constraint import ConstraintEnforcer, GradientLevel

        constraints = _make_full_constraints(
            financial={"max_spend": 100.0, "current_spend": float("-inf")},
        )
        enforcer = ConstraintEnforcer(constraints)
        verdict = enforcer.evaluate("read")
        # -inf / 100 = -inf -> not finite -> BLOCKED
        assert verdict.level == GradientLevel.BLOCKED

    def test_nan_max_spend(self):
        """NaN max_spend -- must not crash."""
        from praxis.core.constraint import ConstraintEnforcer, GradientLevel

        constraints = _make_full_constraints(
            financial={"max_spend": float("nan"), "current_spend": 50.0},
        )
        enforcer = ConstraintEnforcer(constraints)
        # NaN > 0 is False, so utilization defaults to 0.0
        verdict = enforcer.evaluate("read")
        assert isinstance(verdict.level, GradientLevel)

    def test_nan_elapsed_minutes(self):
        """NaN elapsed_minutes -- must not crash."""
        from praxis.core.constraint import ConstraintEnforcer, GradientLevel

        constraints = _make_full_constraints(
            temporal={"max_duration_minutes": 120, "elapsed_minutes": float("nan")},
        )
        enforcer = ConstraintEnforcer(constraints)
        verdict = enforcer.evaluate("read")
        # NaN / 120 = NaN -> BLOCKED by _gradient_for_utilization
        assert verdict.level == GradientLevel.BLOCKED

    def test_inf_action_cost(self):
        """Infinity action cost -- must not crash."""
        from praxis.core.constraint import ConstraintEnforcer, GradientLevel

        constraints = _make_full_constraints(
            financial={"max_spend": 100.0, "current_spend": 0.0},
        )
        enforcer = ConstraintEnforcer(constraints)
        verdict = enforcer.evaluate("write", context={"cost": float("inf")})
        assert verdict.level == GradientLevel.BLOCKED


class TestConstraintEmptyEnvelopes:
    """Attack: empty or missing constraint dimensions."""

    def test_completely_empty_constraints(self):
        """Empty dict {} -- must not crash."""
        from praxis.core.constraint import ConstraintEnforcer, GradientLevel

        enforcer = ConstraintEnforcer({})
        verdict = enforcer.evaluate("read")
        # All dimensions default to empty dicts, which means AUTO_APPROVED for all
        assert isinstance(verdict.level, GradientLevel)

    def test_missing_financial_dimension(self):
        """Financial dimension missing entirely -- must not crash."""
        from praxis.core.constraint import ConstraintEnforcer, GradientLevel

        constraints = {
            "operational": {"allowed_actions": ["read"], "blocked_actions": []},
            "temporal": {"max_duration_minutes": 120, "elapsed_minutes": 0},
            "data_access": {"allowed_paths": ["/src/"], "blocked_paths": []},
            "communication": {"allowed_channels": ["internal"], "blocked_channels": []},
        }
        enforcer = ConstraintEnforcer(constraints)
        verdict = enforcer.evaluate("read")
        assert isinstance(verdict.level, GradientLevel)

    def test_missing_all_optional_keys(self):
        """All dimensions present but with empty dicts."""
        from praxis.core.constraint import ConstraintEnforcer, GradientLevel

        constraints = {
            "financial": {},
            "operational": {},
            "temporal": {},
            "data_access": {},
            "communication": {},
        }
        enforcer = ConstraintEnforcer(constraints)
        verdict = enforcer.evaluate("read")
        assert isinstance(verdict.level, GradientLevel)

    def test_constraint_with_wrong_types(self):
        """Constraint values with wrong types (strings instead of numbers)."""
        from praxis.core.constraint import ConstraintEnforcer

        constraints = _make_full_constraints(
            financial={"max_spend": "one hundred", "current_spend": "fifty"},
        )
        enforcer = ConstraintEnforcer(constraints)
        # This will likely raise a TypeError when doing arithmetic
        with pytest.raises((TypeError, ValueError)):
            enforcer.evaluate("read")

    def test_get_status_empty_constraints(self):
        """get_status with completely empty constraints."""
        from praxis.core.constraint import ConstraintEnforcer

        enforcer = ConstraintEnforcer({})
        status = enforcer.get_status()
        assert "financial" in status
        assert "operational" in status
        assert "temporal" in status
        assert "data_access" in status
        assert "communication" in status


class TestConstraintGradientBoundaries:
    """Test exact boundary values for gradient transitions."""

    def test_exactly_70_percent_is_flagged(self):
        """Exactly 70% utilization should be FLAGGED, not AUTO_APPROVED."""
        from praxis.core.constraint import _gradient_for_utilization, GradientLevel

        level = _gradient_for_utilization(0.70)
        assert level == GradientLevel.FLAGGED

    def test_just_below_70_is_auto_approved(self):
        """69.99% should be AUTO_APPROVED."""
        from praxis.core.constraint import _gradient_for_utilization, GradientLevel

        level = _gradient_for_utilization(0.6999)
        assert level == GradientLevel.AUTO_APPROVED

    def test_exactly_90_percent_is_held(self):
        """Exactly 90% should be HELD."""
        from praxis.core.constraint import _gradient_for_utilization, GradientLevel

        level = _gradient_for_utilization(0.90)
        assert level == GradientLevel.HELD

    def test_just_below_90_is_flagged(self):
        """89.99% should be FLAGGED."""
        from praxis.core.constraint import _gradient_for_utilization, GradientLevel

        level = _gradient_for_utilization(0.8999)
        assert level == GradientLevel.FLAGGED

    def test_exactly_100_percent_is_blocked(self):
        """Exactly 100% should be BLOCKED."""
        from praxis.core.constraint import _gradient_for_utilization, GradientLevel

        level = _gradient_for_utilization(1.0)
        assert level == GradientLevel.BLOCKED

    def test_just_below_100_is_held(self):
        """99.99% should be HELD."""
        from praxis.core.constraint import _gradient_for_utilization, GradientLevel

        level = _gradient_for_utilization(0.9999)
        assert level == GradientLevel.HELD

    def test_zero_percent(self):
        """0% should be AUTO_APPROVED."""
        from praxis.core.constraint import _gradient_for_utilization, GradientLevel

        level = _gradient_for_utilization(0.0)
        assert level == GradientLevel.AUTO_APPROVED

    def test_negative_utilization(self):
        """Negative utilization should be AUTO_APPROVED."""
        from praxis.core.constraint import _gradient_for_utilization, GradientLevel

        level = _gradient_for_utilization(-0.5)
        assert level == GradientLevel.AUTO_APPROVED

    def test_nan_utilization_is_blocked(self):
        """NaN utilization should be BLOCKED."""
        from praxis.core.constraint import _gradient_for_utilization, GradientLevel

        level = _gradient_for_utilization(float("nan"))
        assert level == GradientLevel.BLOCKED

    def test_inf_utilization_is_blocked(self):
        """Infinity utilization should be BLOCKED."""
        from praxis.core.constraint import _gradient_for_utilization, GradientLevel

        level = _gradient_for_utilization(float("inf"))
        assert level == GradientLevel.BLOCKED

    def test_neg_inf_utilization_is_blocked(self):
        """Negative infinity utilization should be BLOCKED."""
        from praxis.core.constraint import _gradient_for_utilization, GradientLevel

        level = _gradient_for_utilization(float("-inf"))
        assert level == GradientLevel.BLOCKED


# ============================================================================
# PART 2: TRUST CHAIN ADVERSARIAL INPUTS
# ============================================================================


class TestTrustChainEmptyPayloads:
    """Attack: empty payloads in chain entries."""

    def test_verify_chain_with_empty_payload(self):
        """Chain entry with empty payload dict -- must not crash."""
        from praxis.trust.verify import verify_chain

        entries = [
            {
                "payload": {},
                "content_hash": hashlib.sha256(jcs.canonicalize({})).hexdigest(),
                "signature": "",
                "signer_key_id": "unknown-key",
                "parent_hash": None,
            }
        ]
        result = verify_chain(entries=entries, public_keys={})
        # Should report unknown_key, not crash
        assert not result.valid
        assert any(b["reason"] == "unknown_key" for b in result.breaks)

    def test_verify_empty_chain(self):
        """Empty chain (no entries) -- should be valid."""
        from praxis.trust.verify import verify_chain

        result = verify_chain(entries=[], public_keys={})
        assert result.valid
        assert result.total_entries == 0


class TestTrustChainMissingFields:
    """Attack: entries with missing required fields."""

    def test_entry_missing_signature(self):
        """Entry with no 'signature' key -- must not crash."""
        from praxis.trust.verify import verify_chain

        payload = {"type": "genesis", "session_id": "test-001"}
        content_hash = hashlib.sha256(jcs.canonicalize(payload)).hexdigest()
        entries = [
            {
                "payload": payload,
                "content_hash": content_hash,
                # "signature" is missing
                "signer_key_id": "key-1",
                "parent_hash": None,
            }
        ]
        result = verify_chain(entries=entries, public_keys={"key-1": "invalid"})
        # Should fail gracefully (bad_signature or similar), not KeyError
        assert not result.valid

    def test_entry_missing_content_hash(self):
        """Entry with no 'content_hash' key -- must not crash."""
        from praxis.trust.verify import verify_chain

        entries = [
            {
                "payload": {"type": "genesis"},
                # "content_hash" is missing
                "signature": "abc",
                "signer_key_id": "key-1",
                "parent_hash": None,
            }
        ]
        result = verify_chain(entries=entries, public_keys={"key-1": "invalid"})
        # Should fail (bad_hash), not crash
        assert not result.valid

    def test_entry_missing_payload(self):
        """Entry with no 'payload' key -- must not crash."""
        from praxis.trust.verify import verify_chain

        entries = [
            {
                # "payload" is missing
                "content_hash": "a" * 64,
                "signature": "abc",
                "signer_key_id": "key-1",
                "parent_hash": None,
            }
        ]
        result = verify_chain(entries=entries, public_keys={"key-1": "invalid"})
        assert not result.valid

    def test_entry_missing_signer_key_id(self):
        """Entry with no 'signer_key_id' -- must report unknown_key."""
        from praxis.trust.verify import verify_chain

        payload = {"type": "genesis"}
        content_hash = hashlib.sha256(jcs.canonicalize(payload)).hexdigest()
        entries = [
            {
                "payload": payload,
                "content_hash": content_hash,
                "signature": "abc",
                # "signer_key_id" is missing
                "parent_hash": None,
            }
        ]
        result = verify_chain(entries=entries, public_keys={})
        assert not result.valid
        # defaults to "" which won't be in public_keys
        assert any(b["reason"] == "unknown_key" for b in result.breaks)


class TestTrustChainLongChains:
    """Attack: very long chains -- performance check."""

    def test_verify_1000_entry_chain_performance(self, key_manager):
        """1000-entry chain should verify within a reasonable time (<5s)."""
        from praxis.trust.audit import AuditChain

        chain = AuditChain(session_id="perf-test", key_id="test-key", key_manager=key_manager)
        for i in range(1000):
            chain.append(
                action=f"action_{i}",
                actor="ai",
                result="auto_approved",
            )

        start = time.monotonic()
        valid, breaks = chain.verify_integrity()
        elapsed = time.monotonic() - start

        assert valid
        assert len(breaks) == 0
        # Should complete in under 5 seconds
        assert elapsed < 5.0, f"1000-entry chain verification took {elapsed:.2f}s (limit: 5s)"


class TestTrustChainDuplicateEntries:
    """Attack: duplicate entries in the chain."""

    def test_duplicate_entries_detected(self):
        """Chain with duplicate content_hash entries -- should detect broken parent link."""
        from praxis.trust.verify import verify_chain

        payload = {"type": "genesis", "session_id": "dup-test"}
        content_hash = hashlib.sha256(jcs.canonicalize(payload)).hexdigest()

        entry = {
            "payload": payload,
            "content_hash": content_hash,
            "signature": "",
            "signer_key_id": "key-1",
            "parent_hash": None,
        }
        # Two identical entries -- second one has parent_hash=None but should link to first
        entries = [entry, dict(entry)]
        result = verify_chain(entries=entries, public_keys={})
        # Second entry's parent_hash (None) != first entry's content_hash
        assert not result.valid
        assert any(b["reason"] == "broken_parent_link" for b in result.breaks)


class TestTrustChainCrossSession:
    """Attack: entries from different sessions mixed together."""

    def test_mixed_session_entries_in_verify(self):
        """Entries from two different sessions -- verify_chain checks structure, not session_id."""
        from praxis.trust.verify import verify_chain

        payload1 = {"type": "genesis", "session_id": "session-A"}
        payload2 = {"type": "audit", "session_id": "session-B"}
        hash1 = hashlib.sha256(jcs.canonicalize(payload1)).hexdigest()
        hash2 = hashlib.sha256(jcs.canonicalize(payload2)).hexdigest()

        entries = [
            {
                "payload": payload1,
                "content_hash": hash1,
                "signature": "",
                "signer_key_id": "key-1",
                "parent_hash": None,
            },
            {
                "payload": payload2,
                "content_hash": hash2,
                "signature": "",
                "signer_key_id": "key-1",
                "parent_hash": hash1,  # Links correctly structurally
            },
        ]
        result = verify_chain(entries=entries, public_keys={})
        # Structural chain is correct but keys are missing
        assert any(b["reason"] == "unknown_key" for b in result.breaks)
        # No broken_parent_link though -- structure is valid
        assert not any(b["reason"] == "broken_parent_link" for b in result.breaks)


# ============================================================================
# PART 3: CLI ADVERSARIAL INPUTS
# ============================================================================


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def cli_main():
    from praxis.cli import main

    return main


class TestCLILongWorkspaceNames:
    """Attack: very long workspace names."""

    def test_10000_char_workspace_name(self, runner, cli_main, tmp_path, monkeypatch):
        """10000-character workspace name -- must not crash."""
        monkeypatch.chdir(tmp_path)
        long_name = "a" * 10000
        result = runner.invoke(cli_main, ["init", "--name", long_name])
        # Should succeed (filesystem may truncate, but CLI shouldn't crash)
        assert result.exit_code == 0
        ws = json.loads((tmp_path / ".praxis" / "workspace.json").read_text())
        assert ws["name"] == long_name


class TestCLIUnicodeWorkspaceNames:
    """Attack: Unicode workspace names."""

    def test_emoji_workspace_name(self, runner, cli_main, tmp_path, monkeypatch):
        """Emoji workspace name."""
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(cli_main, ["init", "--name", "\U0001f680\U0001f30d\U0001f525"])
        assert result.exit_code == 0
        ws = json.loads((tmp_path / ".praxis" / "workspace.json").read_text())
        assert ws["name"] == "\U0001f680\U0001f30d\U0001f525"

    def test_cjk_workspace_name(self, runner, cli_main, tmp_path, monkeypatch):
        """Chinese/Japanese/Korean workspace name."""
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(
            cli_main, ["init", "--name", "\u5de5\u4f5c\u7a7a\u9593\u30c6\u30b9\u30c8"]
        )
        assert result.exit_code == 0
        ws = json.loads((tmp_path / ".praxis" / "workspace.json").read_text())
        assert ws["name"] == "\u5de5\u4f5c\u7a7a\u9593\u30c6\u30b9\u30c8"

    def test_rtl_workspace_name(self, runner, cli_main, tmp_path, monkeypatch):
        """Right-to-left (Arabic) workspace name."""
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(
            cli_main, ["init", "--name", "\u0645\u0633\u0627\u062d\u0629 \u0639\u0645\u0644"]
        )
        assert result.exit_code == 0
        ws = json.loads((tmp_path / ".praxis" / "workspace.json").read_text())
        assert ws["name"] == "\u0645\u0633\u0627\u062d\u0629 \u0639\u0645\u0644"


class TestCLISpecialCharactersInDecisions:
    """Attack: special characters in decision text."""

    def test_quotes_in_decision(self, runner, cli_main, tmp_path, monkeypatch):
        """Quotes and backslashes in decision text."""
        monkeypatch.chdir(tmp_path)
        runner.invoke(cli_main, ["init", "--name", "test"])
        runner.invoke(cli_main, ["session", "start"])
        result = runner.invoke(
            cli_main,
            [
                "decide",
                "-d",
                "Use \"double quotes\" and 'single quotes' and \\backslash",
                "-r",
                "Testing special chars",
            ],
        )
        assert result.exit_code == 0

    def test_newlines_in_decision(self, runner, cli_main, tmp_path, monkeypatch):
        """Newlines in decision text."""
        monkeypatch.chdir(tmp_path)
        runner.invoke(cli_main, ["init", "--name", "test"])
        runner.invoke(cli_main, ["session", "start"])
        result = runner.invoke(
            cli_main,
            [
                "decide",
                "-d",
                "Line 1\nLine 2\nLine 3",
                "-r",
                "Multi-line decision",
            ],
        )
        assert result.exit_code == 0

    def test_null_bytes_in_decision(self, runner, cli_main, tmp_path, monkeypatch):
        """Null bytes in decision text -- must handle gracefully."""
        monkeypatch.chdir(tmp_path)
        runner.invoke(cli_main, ["init", "--name", "test"])
        runner.invoke(cli_main, ["session", "start"])
        result = runner.invoke(
            cli_main,
            [
                "decide",
                "-d",
                "before\x00after",
                "-r",
                "Testing null bytes",
            ],
        )
        # Should either succeed or fail gracefully, not segfault
        assert result.exit_code in (0, 1, 2)

    def test_very_long_decision(self, runner, cli_main, tmp_path, monkeypatch):
        """Very long decision text (100KB)."""
        monkeypatch.chdir(tmp_path)
        runner.invoke(cli_main, ["init", "--name", "test"])
        runner.invoke(cli_main, ["session", "start"])
        long_decision = "x" * 100_000
        result = runner.invoke(
            cli_main,
            ["decide", "-d", long_decision, "-r", "Testing long decision"],
        )
        assert result.exit_code == 0


class TestCLIOutOfOrderCommands:
    """Attack: running commands out of order."""

    def test_decide_before_session_start(self, runner, cli_main, tmp_path, monkeypatch):
        """Run decide before starting a session -- should fail gracefully."""
        monkeypatch.chdir(tmp_path)
        runner.invoke(cli_main, ["init", "--name", "test"])
        result = runner.invoke(
            cli_main,
            ["decide", "-d", "Test", "-r", "No session"],
        )
        assert result.exit_code != 0
        assert "session" in result.output.lower() or "error" in result.output.lower()

    def test_status_before_session_start(self, runner, cli_main, tmp_path, monkeypatch):
        """Run status before starting a session -- should fail gracefully."""
        monkeypatch.chdir(tmp_path)
        runner.invoke(cli_main, ["init", "--name", "test"])
        result = runner.invoke(cli_main, ["status"])
        assert result.exit_code != 0

    def test_export_before_session_start(self, runner, cli_main, tmp_path, monkeypatch):
        """Run export before starting a session -- should fail gracefully."""
        monkeypatch.chdir(tmp_path)
        runner.invoke(cli_main, ["init", "--name", "test"])
        result = runner.invoke(cli_main, ["export"])
        assert result.exit_code != 0

    def test_session_pause_when_already_paused(self, runner, cli_main, tmp_path, monkeypatch):
        """Pause an already paused session -- should fail with state error."""
        monkeypatch.chdir(tmp_path)
        runner.invoke(cli_main, ["init", "--name", "test"])
        runner.invoke(cli_main, ["session", "start"])
        runner.invoke(cli_main, ["session", "pause"])
        result = runner.invoke(cli_main, ["session", "pause"])
        # Should fail because session is already paused
        assert result.exit_code != 0

    def test_session_resume_when_active(self, runner, cli_main, tmp_path, monkeypatch):
        """Resume an active session -- should fail with state error."""
        monkeypatch.chdir(tmp_path)
        runner.invoke(cli_main, ["init", "--name", "test"])
        runner.invoke(cli_main, ["session", "start"])
        result = runner.invoke(cli_main, ["session", "resume"])
        # Should fail because session is active, not paused
        assert result.exit_code != 0

    def test_decide_on_ended_session(self, runner, cli_main, tmp_path, monkeypatch):
        """Decide on an ended session -- should fail."""
        monkeypatch.chdir(tmp_path)
        runner.invoke(cli_main, ["init", "--name", "test"])
        runner.invoke(cli_main, ["session", "start"])
        runner.invoke(cli_main, ["session", "end"])
        result = runner.invoke(
            cli_main,
            ["decide", "-d", "Test", "-r", "Dead session"],
        )
        assert result.exit_code != 0


class TestCLIInitTwice:
    """Attack: running init twice in the same directory."""

    def test_init_twice_does_not_crash(self, runner, cli_main, tmp_path, monkeypatch):
        """Running init twice -- should succeed and update the workspace."""
        monkeypatch.chdir(tmp_path)
        result1 = runner.invoke(cli_main, ["init", "--name", "first"])
        assert result1.exit_code == 0
        result2 = runner.invoke(cli_main, ["init", "--name", "second"])
        assert result2.exit_code == 0
        ws = json.loads((tmp_path / ".praxis" / "workspace.json").read_text())
        assert ws["name"] == "second"

    def test_init_twice_preserves_session_if_exists(self, runner, cli_main, tmp_path, monkeypatch):
        """Init twice when a session file exists -- should not corrupt session."""
        monkeypatch.chdir(tmp_path)
        runner.invoke(cli_main, ["init", "--name", "first"])
        runner.invoke(cli_main, ["session", "start"])
        session_before = json.loads((tmp_path / ".praxis" / "current-session.json").read_text())
        runner.invoke(cli_main, ["init", "--name", "second"])
        # Session file should still exist and be valid JSON
        session_after = json.loads((tmp_path / ".praxis" / "current-session.json").read_text())
        assert session_after["session_id"] == session_before["session_id"]


class TestCLIVerifyAdversarial:
    """Attack: verify command with corrupt files."""

    def test_verify_corrupted_zip(self, runner, cli_main, tmp_path, monkeypatch):
        """Verify a corrupted ZIP file -- should fail gracefully."""
        monkeypatch.chdir(tmp_path)
        corrupt_file = tmp_path / "corrupt.zip"
        corrupt_file.write_bytes(b"PK\x03\x04this is not a real zip file")
        result = runner.invoke(cli_main, ["verify", str(corrupt_file)])
        # Should fail gracefully, not crash
        assert result.exit_code != 0

    def test_verify_non_zip_non_json(self, runner, cli_main, tmp_path, monkeypatch):
        """Verify a random binary file -- should fail gracefully."""
        monkeypatch.chdir(tmp_path)
        binary_file = tmp_path / "random.bin"
        binary_file.write_bytes(bytes(range(256)))
        result = runner.invoke(cli_main, ["verify", str(binary_file)])
        assert result.exit_code != 0

    def test_verify_empty_file(self, runner, cli_main, tmp_path, monkeypatch):
        """Verify an empty file -- should fail gracefully."""
        monkeypatch.chdir(tmp_path)
        empty_file = tmp_path / "empty.json"
        empty_file.write_text("")
        result = runner.invoke(cli_main, ["verify", str(empty_file)])
        assert result.exit_code != 0

    def test_verify_json_without_expected_keys(self, runner, cli_main, tmp_path, monkeypatch):
        """Verify a JSON file missing expected keys."""
        monkeypatch.chdir(tmp_path)
        json_file = tmp_path / "bad.json"
        json_file.write_text(json.dumps({"not": "a bundle"}))
        result = runner.invoke(cli_main, ["verify", str(json_file)])
        # Should succeed but report "no chain entries to verify"
        assert result.exit_code == 0
        assert "no chain entries" in result.output.lower() or "unknown" in result.output.lower()


# ============================================================================
# PART 4: DOMAIN YAML ADVERSARIAL INPUTS
# ============================================================================


class TestDomainLoaderMalformedYAML:
    """Attack: malformed YAML files."""

    def test_invalid_yaml_syntax(self, tmp_path):
        """Completely invalid YAML -- should return errors, not crash."""
        from praxis.domains.loader import DomainLoader

        domain_dir = tmp_path / "bad"
        domain_dir.mkdir()
        (domain_dir / "domain.yml").write_text("{{{{ not valid yaml ::::")
        loader = DomainLoader(domains_dir=tmp_path)
        errors = loader.validate_domain("bad")
        assert len(errors) > 0
        assert "parse error" in errors[0].lower() or "yaml" in errors[0].lower()

    def test_yaml_is_a_list_not_mapping(self, tmp_path):
        """YAML that parses to a list instead of a dict."""
        from praxis.domains.loader import DomainLoader, DomainValidationError

        domain_dir = tmp_path / "listdomain"
        domain_dir.mkdir()
        (domain_dir / "domain.yml").write_text("- item1\n- item2\n- item3")
        loader = DomainLoader(domains_dir=tmp_path)
        errors = loader.validate_domain("listdomain")
        assert len(errors) > 0
        assert "mapping" in errors[0].lower() or "list" in errors[0].lower()

    def test_yaml_is_null(self, tmp_path):
        """YAML that parses to None (empty file)."""
        from praxis.domains.loader import DomainLoader

        domain_dir = tmp_path / "nulldomain"
        domain_dir.mkdir()
        (domain_dir / "domain.yml").write_text("")
        loader = DomainLoader(domains_dir=tmp_path)
        errors = loader.validate_domain("nulldomain")
        assert len(errors) > 0

    def test_yaml_is_scalar(self, tmp_path):
        """YAML that parses to a scalar string."""
        from praxis.domains.loader import DomainLoader

        domain_dir = tmp_path / "scalar"
        domain_dir.mkdir()
        (domain_dir / "domain.yml").write_text("just a string")
        loader = DomainLoader(domains_dir=tmp_path)
        errors = loader.validate_domain("scalar")
        assert len(errors) > 0


class TestDomainLoaderMissingFields:
    """Attack: YAML with missing required fields."""

    def test_missing_all_required_fields(self, tmp_path):
        """Domain YAML with only a random field."""
        from praxis.domains.loader import DomainLoader, DomainValidationError

        domain_dir = tmp_path / "incomplete"
        domain_dir.mkdir()
        (domain_dir / "domain.yml").write_text("random_field: hello")
        loader = DomainLoader(domains_dir=tmp_path)
        with pytest.raises(DomainValidationError):
            loader.load_domain("incomplete")

    def test_missing_constraint_templates(self, tmp_path):
        """Domain YAML with everything except constraint_templates."""
        from praxis.domains.loader import DomainLoader, DomainValidationError

        domain_dir = tmp_path / "noconstraints"
        domain_dir.mkdir()
        yaml_content = """
name: test
display_name: Test Domain
description: Missing constraints
version: "1.0"
phases:
  - name: phase1
    display_name: Phase 1
    description: First phase
    approval_gate: false
capture:
  auto_capture: [state_change]
  decision_types: [scope]
  observation_targets: [test_results]
"""
        (domain_dir / "domain.yml").write_text(yaml_content)
        loader = DomainLoader(domains_dir=tmp_path)
        with pytest.raises(DomainValidationError):
            loader.load_domain("noconstraints")


class TestDomainLoaderExtremeConstraintValues:
    """Attack: domain YAML with extreme constraint values."""

    def test_extreme_max_spend_in_template(self, tmp_path):
        """Constraint template with 10^18 max_spend."""
        from praxis.domains.loader import DomainLoader

        domain_dir = tmp_path / "extreme"
        domain_dir.mkdir()
        yaml_content = """
name: extreme
display_name: Extreme Domain
description: Domain with extreme values
version: "1.0"
constraint_templates:
  extreme:
    financial:
      max_spend: 1000000000000000000
    operational:
      allowed_actions: [read]
      max_actions_per_hour: 999999999
    temporal:
      max_duration_minutes: 999999999
    data_access:
      allowed_paths: ["/"]
    communication:
      allowed_channels: [internal]
phases:
  - name: phase1
    display_name: Phase 1
    description: First phase
    approval_gate: false
capture:
  auto_capture: [state_change]
  decision_types: [scope]
  observation_targets: [test_results]
"""
        (domain_dir / "domain.yml").write_text(yaml_content)
        loader = DomainLoader(domains_dir=tmp_path)
        config = loader.load_domain("extreme")
        assert config.constraint_templates["extreme"]["financial"]["max_spend"] == 1e18


class TestDomainLoaderMissingDimensions:
    """Attack: constraint templates with missing dimensions."""

    def test_template_missing_all_dimensions(self, tmp_path):
        """Constraint template with no dimensions at all."""
        from praxis.domains.loader import DomainLoader, DomainValidationError

        domain_dir = tmp_path / "nodims"
        domain_dir.mkdir()
        yaml_content = """
name: nodims
display_name: No Dimensions
description: Template with no dimensions
version: "1.0"
constraint_templates:
  empty:
    random_key: value
phases:
  - name: phase1
    display_name: Phase 1
    description: First phase
    approval_gate: false
capture:
  auto_capture: [state_change]
  decision_types: [scope]
  observation_targets: [test_results]
"""
        (domain_dir / "domain.yml").write_text(yaml_content)
        loader = DomainLoader(domains_dir=tmp_path)
        with pytest.raises(DomainValidationError):
            loader.load_domain("nodims")

    def test_template_missing_one_dimension(self, tmp_path):
        """Constraint template missing just the communication dimension."""
        from praxis.domains.loader import DomainLoader, DomainValidationError

        domain_dir = tmp_path / "missingone"
        domain_dir.mkdir()
        yaml_content = """
name: missingone
display_name: Missing One
description: Missing one dimension
version: "1.0"
constraint_templates:
  partial:
    financial:
      max_spend: 100
    operational:
      allowed_actions: [read]
      max_actions_per_hour: 100
    temporal:
      max_duration_minutes: 60
    data_access:
      allowed_paths: ["/src"]
phases:
  - name: phase1
    display_name: Phase 1
    description: First phase
    approval_gate: false
capture:
  auto_capture: [state_change]
  decision_types: [scope]
  observation_targets: [test_results]
"""
        (domain_dir / "domain.yml").write_text(yaml_content)
        loader = DomainLoader(domains_dir=tmp_path)
        with pytest.raises(DomainValidationError):
            loader.load_domain("missingone")


class TestDomainLoaderNonexistentDomain:
    """Attack: loading domains that don't exist."""

    def test_load_nonexistent_domain(self, tmp_path):
        """Load a domain that does not exist."""
        from praxis.domains.loader import DomainLoader, DomainNotFoundError

        loader = DomainLoader(domains_dir=tmp_path)
        with pytest.raises(DomainNotFoundError):
            loader.load_domain("nonexistent")

    def test_get_constraint_template_nonexistent_template(self):
        """Get a template name that does not exist in a valid domain."""
        from praxis.domains.loader import DomainLoader

        loader = DomainLoader()
        with pytest.raises(KeyError, match="not found"):
            loader.get_constraint_template("coc", "nonexistent_template")


# ============================================================================
# PART 5: BUNDLE EDGE CASES
# ============================================================================


class TestBundleZeroDeliberation:
    """Edge case: session with zero deliberation records."""

    def test_bundle_with_zero_deliberation(self, tmp_path, key_manager, sample_constraints):
        """Build a bundle with no deliberation records."""
        from praxis.export.bundle import BundleBuilder
        from praxis.trust.genesis import create_genesis

        genesis = create_genesis(
            session_id="sess-empty",
            authority_id="user-1",
            key_id="test-key",
            key_manager=key_manager,
            constraints=sample_constraints,
        )
        pem = key_manager.export_public_pem("test-key")
        if isinstance(pem, bytes):
            pem = pem.decode("utf-8")

        builder = BundleBuilder(
            session_data={
                "session_id": "sess-empty",
                "workspace_id": "ws-1",
                "domain": "coc",
                "created_at": "2026-03-15T10:00:00.000000Z",
                "ended_at": "2026-03-15T11:00:00.000000Z",
            },
            trust_chain=[
                {
                    "payload": genesis.payload,
                    "content_hash": genesis.content_hash,
                    "signature": genesis.signature,
                    "signer_key_id": genesis.signer_key_id,
                    "parent_hash": None,
                }
            ],
            deliberation_records=[],
            constraint_events=[],
            public_keys={"test-key": pem},
        )
        output = tmp_path / "empty-delib.zip"
        builder.build(output)
        assert output.exists()

        with zipfile.ZipFile(output, "r") as zf:
            data_js = zf.read("data/bundle-data.js").decode("utf-8")
        json_str = data_js.split("window.PRAXIS_BUNDLE = ", 1)[1].rstrip().rstrip(";")
        bundle_data = json.loads(json_str)
        assert bundle_data["metadata"]["total_decisions"] == 0
        assert len(bundle_data["deliberation"]) == 0


class TestBundleManyDeliberation:
    """Edge case: session with 1000+ deliberation records."""

    def test_bundle_with_1000_deliberation_records(self, tmp_path, key_manager, sample_constraints):
        """Build a bundle with 1000 deliberation records -- performance check."""
        from praxis.export.bundle import BundleBuilder
        from praxis.trust.genesis import create_genesis

        genesis = create_genesis(
            session_id="sess-many",
            authority_id="user-1",
            key_id="test-key",
            key_manager=key_manager,
            constraints=sample_constraints,
        )
        pem = key_manager.export_public_pem("test-key")
        if isinstance(pem, bytes):
            pem = pem.decode("utf-8")

        records = []
        for i in range(1000):
            records.append(
                {
                    "record_id": f"rec-{i:04d}",
                    "session_id": "sess-many",
                    "record_type": "decision" if i % 3 == 0 else "observation",
                    "content": (
                        {"decision": f"Decision {i}"} if i % 3 == 0 else {"observation": f"Obs {i}"}
                    ),
                    "reasoning_hash": hashlib.sha256(f"record-{i}".encode()).hexdigest(),
                    "actor": "human" if i % 2 == 0 else "ai",
                    "confidence": 0.9,
                    "created_at": "2026-03-15T10:00:00.000000Z",
                }
            )

        builder = BundleBuilder(
            session_data={
                "session_id": "sess-many",
                "workspace_id": "ws-1",
                "domain": "coc",
                "created_at": "2026-03-15T10:00:00.000000Z",
                "ended_at": "2026-03-15T11:00:00.000000Z",
            },
            trust_chain=[
                {
                    "payload": genesis.payload,
                    "content_hash": genesis.content_hash,
                    "signature": genesis.signature,
                    "signer_key_id": genesis.signer_key_id,
                    "parent_hash": None,
                }
            ],
            deliberation_records=records,
            constraint_events=[],
            public_keys={"test-key": pem},
        )
        start = time.monotonic()
        output = tmp_path / "many-delib.zip"
        builder.build(output)
        elapsed = time.monotonic() - start

        assert output.exists()
        # Should complete in reasonable time
        assert elapsed < 10.0, f"Bundle with 1000 records took {elapsed:.2f}s"

        with zipfile.ZipFile(output, "r") as zf:
            data_js = zf.read("data/bundle-data.js").decode("utf-8")
        json_str = data_js.split("window.PRAXIS_BUNDLE = ", 1)[1].rstrip().rstrip(";")
        bundle_data = json.loads(json_str)
        assert len(bundle_data["deliberation"]) == 1000
        # Every 3rd record is a decision (indices 0, 3, 6, ... 999)
        assert bundle_data["metadata"]["total_decisions"] == 334


class TestBundleSpecialCharacters:
    """Edge case: special characters in decision text."""

    def test_bundle_with_special_chars_in_decisions(
        self, tmp_path, key_manager, sample_constraints
    ):
        """Decision text with special characters (quotes, newlines, unicode)."""
        from praxis.export.bundle import BundleBuilder
        from praxis.trust.genesis import create_genesis

        genesis = create_genesis(
            session_id="sess-special",
            authority_id="user-1",
            key_id="test-key",
            key_manager=key_manager,
            constraints=sample_constraints,
        )
        pem = key_manager.export_public_pem("test-key")
        if isinstance(pem, bytes):
            pem = pem.decode("utf-8")

        special_records = [
            {
                "record_id": "rec-quotes",
                "session_id": "sess-special",
                "record_type": "decision",
                "content": {"decision": "Use \"double quotes\" and 'single quotes'"},
                "reasoning_hash": "a" * 64,
                "actor": "human",
                "created_at": "2026-03-15T10:00:00.000000Z",
            },
            {
                "record_id": "rec-newline",
                "session_id": "sess-special",
                "record_type": "decision",
                "content": {"decision": "Line 1\nLine 2\tTabbed"},
                "reasoning_hash": "b" * 64,
                "actor": "human",
                "created_at": "2026-03-15T10:01:00.000000Z",
            },
            {
                "record_id": "rec-unicode",
                "session_id": "sess-special",
                "record_type": "decision",
                "content": {
                    "decision": "\u4f7f\u7528\u65e5\u672c\u8a9e \U0001f680\U0001f525 \u0645\u0633\u0627\u062d\u0629"
                },
                "reasoning_hash": "c" * 64,
                "actor": "human",
                "created_at": "2026-03-15T10:02:00.000000Z",
            },
        ]

        builder = BundleBuilder(
            session_data={
                "session_id": "sess-special",
                "workspace_id": "ws-1",
                "domain": "coc",
                "created_at": "2026-03-15T10:00:00.000000Z",
                "ended_at": "2026-03-15T11:00:00.000000Z",
            },
            trust_chain=[
                {
                    "payload": genesis.payload,
                    "content_hash": genesis.content_hash,
                    "signature": genesis.signature,
                    "signer_key_id": genesis.signer_key_id,
                    "parent_hash": None,
                }
            ],
            deliberation_records=special_records,
            constraint_events=[],
            public_keys={"test-key": pem},
        )
        output = tmp_path / "special-chars.zip"
        builder.build(output)
        assert output.exists()

        # Verify we can extract and parse the JSON correctly
        with zipfile.ZipFile(output, "r") as zf:
            data_js = zf.read("data/bundle-data.js").decode("utf-8")
        json_str = data_js.split("window.PRAXIS_BUNDLE = ", 1)[1].rstrip().rstrip(";")
        bundle_data = json.loads(json_str)
        decisions = bundle_data["deliberation"]
        assert len(decisions) == 3
        assert '"double quotes"' in decisions[0]["content"]["decision"]
        assert "\n" in decisions[1]["content"]["decision"]
        assert "\U0001f680" in decisions[2]["content"]["decision"]


class TestBundleVerifyCorruptedZip:
    """Edge case: verifying a corrupted ZIP file."""

    def test_verify_truncated_zip(self, tmp_path, key_manager, sample_constraints):
        """Truncate a valid bundle ZIP and try to verify -- should fail gracefully."""
        from praxis.export.bundle import BundleBuilder
        from praxis.trust.genesis import create_genesis

        genesis = create_genesis(
            session_id="sess-corrupt",
            authority_id="user-1",
            key_id="test-key",
            key_manager=key_manager,
            constraints=sample_constraints,
        )
        pem = key_manager.export_public_pem("test-key")
        if isinstance(pem, bytes):
            pem = pem.decode("utf-8")

        builder = BundleBuilder(
            session_data={
                "session_id": "sess-corrupt",
                "workspace_id": "ws-1",
                "domain": "coc",
                "created_at": "2026-03-15T10:00:00.000000Z",
            },
            trust_chain=[
                {
                    "payload": genesis.payload,
                    "content_hash": genesis.content_hash,
                    "signature": genesis.signature,
                    "signer_key_id": genesis.signer_key_id,
                    "parent_hash": None,
                }
            ],
            deliberation_records=[],
            constraint_events=[],
            public_keys={"test-key": pem},
        )
        output = tmp_path / "valid.zip"
        builder.build(output)

        # Truncate the file to corrupt it
        data = output.read_bytes()
        truncated = tmp_path / "truncated.zip"
        truncated.write_bytes(data[: len(data) // 2])

        # Try to verify via CLI
        from praxis.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["verify", str(truncated)])
        # Should fail gracefully
        assert result.exit_code != 0


# ============================================================================
# PART 6: DELIBERATION ENGINE EDGE CASES
# ============================================================================


class TestDeliberationAdversarial:
    """Attack: deliberation engine with edge-case inputs."""

    def test_confidence_just_above_one_rejected(self):
        """Confidence of 1.0001 should be rejected."""
        from praxis.core.deliberation import DeliberationEngine

        engine = DeliberationEngine(session_id="test")
        with pytest.raises(ValueError, match="[Cc]onfidence"):
            engine.record_decision(
                decision="Test",
                rationale="Test",
                confidence=1.0001,
            )

    def test_confidence_just_below_zero_rejected(self):
        """Confidence of -0.0001 should be rejected."""
        from praxis.core.deliberation import DeliberationEngine

        engine = DeliberationEngine(session_id="test")
        with pytest.raises(ValueError, match="[Cc]onfidence"):
            engine.record_decision(
                decision="Test",
                rationale="Test",
                confidence=-0.0001,
            )

    def test_confidence_nan_rejected(self):
        """NaN confidence should be rejected."""
        from praxis.core.deliberation import DeliberationEngine

        engine = DeliberationEngine(session_id="test")
        with pytest.raises((ValueError, TypeError)):
            engine.record_decision(
                decision="Test",
                rationale="Test",
                confidence=float("nan"),
            )

    def test_confidence_exactly_zero_accepted(self):
        """Confidence of exactly 0.0 should be accepted."""
        from praxis.core.deliberation import DeliberationEngine

        engine = DeliberationEngine(session_id="test")
        record = engine.record_decision(
            decision="Zero confidence",
            rationale="Unsure",
            confidence=0.0,
        )
        assert record["confidence"] == 0.0

    def test_confidence_exactly_one_accepted(self):
        """Confidence of exactly 1.0 should be accepted."""
        from praxis.core.deliberation import DeliberationEngine

        engine = DeliberationEngine(session_id="test")
        record = engine.record_decision(
            decision="Full confidence",
            rationale="Certain",
            confidence=1.0,
        )
        assert record["confidence"] == 1.0

    def test_empty_decision_string(self):
        """Empty string decision -- should be accepted (not validated for non-empty)."""
        from praxis.core.deliberation import DeliberationEngine

        engine = DeliberationEngine(session_id="test")
        record = engine.record_decision(decision="", rationale="Empty on purpose")
        assert record["content"]["decision"] == ""

    def test_large_number_of_records_chain_integrity(self):
        """500 records -- verify hash chain stays intact."""
        from praxis.core.deliberation import DeliberationEngine

        engine = DeliberationEngine(session_id="integrity-test")
        for i in range(500):
            engine.record_decision(
                decision=f"Decision {i}",
                rationale=f"Rationale {i}",
            )

        records, total = engine.get_timeline(limit=500)
        assert total == 500
        # Verify chain linkage
        for i in range(1, len(records)):
            assert (
                records[i]["parent_record_id"] == records[i - 1]["reasoning_hash"]
            ), f"Chain broken at record {i}"

        # First record has no parent
        assert records[0]["parent_record_id"] is None


# ============================================================================
# PART 7: SESSION MANAGER EDGE CASES
# ============================================================================


class TestSessionAdversarial:
    """Attack: session manager with edge-case inputs."""

    def test_empty_workspace_id_rejected(self):
        """Empty workspace_id should be rejected."""
        from praxis.core.session import SessionManager

        mgr = SessionManager()
        with pytest.raises(ValueError, match="workspace_id"):
            mgr.create_session(workspace_id="")

    def test_unknown_constraint_template_rejected(self):
        """Unknown constraint template should be rejected."""
        from praxis.core.session import SessionManager

        mgr = SessionManager()
        with pytest.raises(ValueError, match="template"):
            mgr.create_session(workspace_id="ws-1", constraint_template="nonexistent")

    def test_end_session_twice_rejected(self):
        """Ending an already archived session should fail."""
        from praxis.core.session import InvalidStateTransitionError, SessionManager

        mgr = SessionManager()
        s = mgr.create_session(workspace_id="ws-1")
        mgr.end_session(s["session_id"])
        with pytest.raises(InvalidStateTransitionError):
            mgr.end_session(s["session_id"])

    def test_loosen_constraints_rejected(self):
        """Loosening constraints should be rejected."""
        from praxis.core.session import SessionManager

        mgr = SessionManager()
        s = mgr.create_session(
            workspace_id="ws-1",
            constraints={
                "financial": {"max_spend": 100.0},
                "operational": {"allowed_actions": ["read", "write"]},
                "temporal": {"max_duration_minutes": 60},
                "data_access": {"allowed_paths": ["/src/"]},
                "communication": {"allowed_channels": ["internal"]},
            },
        )
        with pytest.raises(ValueError, match="[Cc]annot loosen|tighten"):
            mgr.update_constraints(
                s["session_id"],
                {
                    "financial": {"max_spend": 200.0},  # Looser
                    "operational": {"allowed_actions": ["read", "write"]},
                    "temporal": {"max_duration_minutes": 60},
                    "data_access": {"allowed_paths": ["/src/"]},
                    "communication": {"allowed_channels": ["internal"]},
                },
            )

    def test_get_nonexistent_session_rejected(self):
        """Getting a non-existent session should raise KeyError."""
        from praxis.core.session import SessionManager

        mgr = SessionManager()
        with pytest.raises(KeyError):
            mgr.get_session("nonexistent-id")


# ============================================================================
# PART 8: KEY MANAGER ADVERSARIAL INPUTS
# ============================================================================


class TestKeyManagerAdversarial:
    """Attack: key manager with path traversal and invalid IDs."""

    def test_path_traversal_rejected(self):
        """key_id with ../ should be rejected."""
        from praxis.trust.keys import KeyManager

        with tempfile.TemporaryDirectory() as td:
            km = KeyManager(Path(td))
            with pytest.raises(ValueError, match="forbidden"):
                km.generate_key("../../etc/passwd")

    def test_null_byte_key_id_rejected(self):
        """key_id with null byte should be rejected."""
        from praxis.trust.keys import KeyManager

        with tempfile.TemporaryDirectory() as td:
            km = KeyManager(Path(td))
            with pytest.raises(ValueError, match="forbidden"):
                km.generate_key("test\x00key")

    def test_slash_key_id_rejected(self):
        """key_id with / should be rejected."""
        from praxis.trust.keys import KeyManager

        with tempfile.TemporaryDirectory() as td:
            km = KeyManager(Path(td))
            with pytest.raises(ValueError, match="forbidden"):
                km.generate_key("test/key")

    def test_empty_key_id_rejected(self):
        """Empty key_id should be rejected."""
        from praxis.trust.keys import KeyManager

        with tempfile.TemporaryDirectory() as td:
            km = KeyManager(Path(td))
            with pytest.raises(ValueError):
                km.generate_key("")

    def test_duplicate_key_rejected(self):
        """Generating a key with an existing ID should fail."""
        from praxis.trust.keys import KeyManager

        with tempfile.TemporaryDirectory() as td:
            km = KeyManager(Path(td))
            km.generate_key("test-dup")
            with pytest.raises(ValueError, match="already exists"):
                km.generate_key("test-dup")


# ============================================================================
# PART 9: CRYPTO MODULE EDGE CASES
# ============================================================================


class TestCryptoAdversarial:
    """Attack: crypto module with edge-case inputs."""

    def test_canonical_hash_rejects_non_dict(self):
        """canonical_hash should reject non-dict input."""
        from praxis.trust.crypto import canonical_hash

        with pytest.raises(TypeError, match="dict"):
            canonical_hash("not a dict")

        with pytest.raises(TypeError, match="dict"):
            canonical_hash(42)

        with pytest.raises(TypeError, match="dict"):
            canonical_hash([1, 2, 3])

    def test_canonical_hash_empty_dict(self):
        """canonical_hash of empty dict should produce a valid SHA-256."""
        from praxis.trust.crypto import canonical_hash

        result = canonical_hash({})
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)

    def test_canonical_hash_deterministic(self):
        """Same input should always produce the same hash."""
        from praxis.trust.crypto import canonical_hash

        payload = {"z_key": "last", "a_key": "first", "m_key": 42}
        h1 = canonical_hash(payload)
        h2 = canonical_hash(payload)
        assert h1 == h2

    def test_canonical_hash_key_order_independent(self):
        """Dict key order should not affect the hash (JCS canonicalizes)."""
        from praxis.trust.crypto import canonical_hash

        h1 = canonical_hash({"a": 1, "b": 2})
        h2 = canonical_hash({"b": 2, "a": 1})
        assert h1 == h2
