# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""Property-based tests for Praxis invariants using Hypothesis.

These tests verify properties that must hold for ALL valid inputs,
not just specific examples. They use Hypothesis to generate random
test cases that explore edge cases automatically.
"""

import hashlib

import jcs
import pytest
from hypothesis import given, settings, strategies as st


class TestGradientMonotonicity:
    """Property: Higher utilization always produces equal or more severe gradient level."""

    @given(utilization=st.floats(min_value=0.0, max_value=2.0))
    def test_gradient_is_monotonic(self, utilization):
        """Higher utilization always produces equal or more severe gradient level."""
        from praxis.trust.gradient import GradientLevel, _utilization_to_level

        _SEVERITY = {
            GradientLevel.AUTO_APPROVED: 0,
            GradientLevel.FLAGGED: 1,
            GradientLevel.HELD: 2,
            GradientLevel.BLOCKED: 3,
        }

        level = _utilization_to_level(utilization)

        # Verify that the result is always a valid GradientLevel
        assert level in _SEVERITY

        # Verify monotonicity: any value above this should be >= this severity
        # (we check a slightly higher value)
        higher_utilization = utilization + 0.01
        higher_level = _utilization_to_level(higher_utilization)
        assert _SEVERITY[higher_level] >= _SEVERITY[level], (
            f"Monotonicity violation: utilization={utilization} -> {level.value}, "
            f"utilization={higher_utilization} -> {higher_level.value}"
        )

    @given(utilization=st.floats(min_value=0.0, max_value=0.69))
    def test_below_70_percent_is_auto_approved(self, utilization):
        """Utilization below 70% MUST be AUTO_APPROVED."""
        from praxis.trust.gradient import GradientLevel, _utilization_to_level

        assert _utilization_to_level(utilization) == GradientLevel.AUTO_APPROVED

    @given(utilization=st.floats(min_value=0.70, max_value=0.8999))
    def test_70_to_89_percent_is_flagged(self, utilization):
        """Utilization between 70% and 89% MUST be FLAGGED."""
        from praxis.trust.gradient import GradientLevel, _utilization_to_level

        assert _utilization_to_level(utilization) == GradientLevel.FLAGGED

    @given(utilization=st.floats(min_value=0.90, max_value=0.9999))
    def test_90_to_99_percent_is_held(self, utilization):
        """Utilization between 90% and 99% MUST be HELD."""
        from praxis.trust.gradient import GradientLevel, _utilization_to_level

        assert _utilization_to_level(utilization) == GradientLevel.HELD

    @given(utilization=st.floats(min_value=1.0, max_value=10.0))
    def test_at_or_above_100_percent_is_blocked(self, utilization):
        """Utilization at or above 100% MUST be BLOCKED."""
        from praxis.trust.gradient import GradientLevel, _utilization_to_level

        assert _utilization_to_level(utilization) == GradientLevel.BLOCKED


class TestConstraintTighteningProperties:
    """Property: Constraint tightening is reflexive and transitive."""

    @given(max_spend=st.floats(min_value=1.0, max_value=10000.0))
    def test_tightening_is_reflexive(self, max_spend):
        """A constraint envelope is always tighter than or equal to itself."""
        from praxis.core.session import _is_tightening

        constraints = {
            "financial": {"max_spend": max_spend},
            "operational": {"allowed_actions": ["read"]},
            "temporal": {"max_duration_minutes": 120},
            "data_access": {"allowed_paths": ["/src"]},
            "communication": {"allowed_channels": ["internal"]},
        }
        assert _is_tightening(constraints, constraints) is True

    @given(
        parent_spend=st.floats(min_value=100.0, max_value=10000.0),
        child_factor=st.floats(min_value=0.01, max_value=1.0),
    )
    def test_lower_max_spend_is_tighter(self, parent_spend, child_factor):
        """Lower max_spend is always a valid tightening."""
        from praxis.core.session import _is_tightening

        child_spend = parent_spend * child_factor
        parent = {
            "financial": {"max_spend": parent_spend},
            "operational": {"allowed_actions": ["read"]},
            "temporal": {"max_duration_minutes": 120},
            "data_access": {"allowed_paths": ["/src"]},
            "communication": {"allowed_channels": ["internal"]},
        }
        child = {
            "financial": {"max_spend": child_spend},
            "operational": {"allowed_actions": ["read"]},
            "temporal": {"max_duration_minutes": 120},
            "data_access": {"allowed_paths": ["/src"]},
            "communication": {"allowed_channels": ["internal"]},
        }
        assert _is_tightening(parent, child) is True


class TestHashChainProperties:
    """Property: Hash chain linkage is consistent."""

    @given(
        payloads=st.lists(
            st.dictionaries(
                keys=st.text(
                    min_size=1,
                    max_size=20,
                    alphabet=st.characters(
                        whitelist_categories=("L", "N"),
                    ),
                ),
                values=st.text(
                    min_size=1,
                    max_size=50,
                    alphabet=st.characters(
                        whitelist_categories=("L", "N", "P"),
                    ),
                ),
                min_size=1,
                max_size=5,
            ),
            min_size=2,
            max_size=10,
        )
    )
    @settings(max_examples=50)
    def test_chain_linkage_is_consistent(self, payloads):
        """Chain parent_hash always points to previous entry's content_hash."""
        # Build a hash chain from the payloads
        chain = []
        for i, payload in enumerate(payloads):
            canonical = jcs.canonicalize(payload)
            content_hash = hashlib.sha256(canonical).hexdigest()
            parent_hash = chain[-1]["content_hash"] if chain else None
            chain.append(
                {
                    "payload": payload,
                    "content_hash": content_hash,
                    "parent_hash": parent_hash,
                }
            )

        # Verify chain integrity
        for i in range(1, len(chain)):
            assert chain[i]["parent_hash"] == chain[i - 1]["content_hash"], (
                f"Chain linkage broken at position {i}: "
                f"expected parent_hash={chain[i-1]['content_hash']}, "
                f"got parent_hash={chain[i]['parent_hash']}"
            )

        # First entry has no parent
        assert chain[0]["parent_hash"] is None

    @given(
        data=st.dictionaries(
            keys=st.text(
                min_size=1,
                max_size=20,
                alphabet=st.characters(whitelist_categories=("L", "N")),
            ),
            values=st.text(
                min_size=1,
                max_size=50,
                alphabet=st.characters(whitelist_categories=("L", "N", "P")),
            ),
            min_size=1,
            max_size=10,
        )
    )
    def test_jcs_hash_is_deterministic(self, data):
        """Same payload always produces the same JCS canonical hash."""
        canonical1 = jcs.canonicalize(data)
        hash1 = hashlib.sha256(canonical1).hexdigest()

        canonical2 = jcs.canonicalize(data)
        hash2 = hashlib.sha256(canonical2).hexdigest()

        assert hash1 == hash2


class TestCanonicalHashProperties:
    """Property: canonical_hash function is deterministic and type-safe."""

    @given(
        data=st.dictionaries(
            keys=st.text(
                min_size=1,
                max_size=10,
                alphabet=st.characters(whitelist_categories=("L",)),
            ),
            values=st.one_of(
                st.text(max_size=20),
                st.integers(min_value=-1000, max_value=1000),
                st.booleans(),
            ),
            min_size=1,
            max_size=5,
        )
    )
    def test_canonical_hash_is_deterministic(self, data):
        """canonical_hash always returns the same hash for the same input."""
        from praxis.trust.crypto import canonical_hash

        h1 = canonical_hash(data)
        h2 = canonical_hash(data)
        assert h1 == h2
        assert isinstance(h1, str)
        assert len(h1) == 64  # SHA-256 hex digest

    def test_canonical_hash_rejects_non_dict(self):
        """canonical_hash MUST reject non-dict inputs."""
        from praxis.trust.crypto import canonical_hash

        with pytest.raises(TypeError):
            canonical_hash("not a dict")

        with pytest.raises(TypeError):
            canonical_hash([1, 2, 3])


class TestConfidenceProperties:
    """Property: Confidence validation boundary conditions."""

    @given(confidence=st.floats(min_value=0.0, max_value=1.0))
    def test_valid_confidence_accepted(self, confidence):
        """Any confidence in [0.0, 1.0] MUST be accepted."""
        from praxis.core.deliberation import _validate_confidence

        # Should not raise
        _validate_confidence(confidence)

    @given(confidence=st.floats(min_value=1.001, max_value=100.0))
    def test_confidence_above_one_rejected(self, confidence):
        """Confidence > 1.0 MUST be rejected."""
        from praxis.core.deliberation import _validate_confidence

        with pytest.raises(ValueError, match="[Cc]onfidence"):
            _validate_confidence(confidence)

    @given(confidence=st.floats(min_value=-100.0, max_value=-0.001))
    def test_confidence_below_zero_rejected(self, confidence):
        """Confidence < 0.0 MUST be rejected."""
        from praxis.core.deliberation import _validate_confidence

        with pytest.raises(ValueError, match="[Cc]onfidence"):
            _validate_confidence(confidence)

    def test_confidence_none_accepted(self):
        """None confidence MUST be accepted (means unspecified)."""
        from praxis.core.deliberation import _validate_confidence

        _validate_confidence(None)
