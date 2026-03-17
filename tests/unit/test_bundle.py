# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""Unit tests for praxis.export.bundle — verification bundle builder."""

import json
import zipfile
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def session_data():
    """Minimal session data dict for bundle tests."""
    return {
        "session_id": "sess-bundle-001",
        "workspace_id": "ws-test",
        "domain": "coc",
        "state": "archived",
        "constraint_envelope": {
            "financial": {"max_spend": 100.0},
            "operational": {"allowed_actions": ["read", "write"]},
            "temporal": {"max_duration_minutes": 60},
            "data_access": {"allowed_paths": ["/src"]},
            "communication": {"allowed_channels": ["internal"]},
        },
        "created_at": "2026-03-15T10:00:00.000000Z",
        "ended_at": "2026-03-15T11:00:00.000000Z",
    }


@pytest.fixture
def trust_chain_entries(key_manager, sample_constraints):
    """Build a small trust chain (genesis + 2 audit anchors) for bundle tests."""
    from praxis.trust.audit import AuditChain
    from praxis.trust.genesis import create_genesis

    genesis = create_genesis(
        session_id="sess-bundle-001",
        authority_id="user-1",
        key_id="test-key",
        key_manager=key_manager,
        constraints=sample_constraints,
    )
    audit = AuditChain(session_id="sess-bundle-001", key_id="test-key", key_manager=key_manager)
    a1 = audit.append(
        action="read_file", actor="ai", result="auto_approved", resource="/src/main.py"
    )
    a2 = audit.append(action="write_file", actor="ai", result="flagged", resource="/src/new.py")

    return [
        {
            "payload": genesis.payload,
            "content_hash": genesis.content_hash,
            "signature": genesis.signature,
            "signer_key_id": genesis.signer_key_id,
            "parent_hash": None,
        },
        {
            "payload": a1.payload,
            "content_hash": a1.content_hash,
            "signature": a1.signature,
            "signer_key_id": a1.signer_key_id,
            "parent_hash": a1.parent_hash,
        },
        {
            "payload": a2.payload,
            "content_hash": a2.content_hash,
            "signature": a2.signature,
            "signer_key_id": a2.signer_key_id,
            "parent_hash": a2.parent_hash,
        },
    ]


@pytest.fixture
def deliberation_records():
    """Sample deliberation records for bundle tests."""
    return [
        {
            "record_id": "rec-001",
            "session_id": "sess-bundle-001",
            "record_type": "decision",
            "content": {"decision": "Use Ed25519 for signing"},
            "reasoning_trace": {
                "rationale": "Industry standard for trust chains",
                "actor": "human",
                "confidence": 0.95,
            },
            "reasoning_hash": "a" * 64,
            "parent_record_id": None,
            "actor": "human",
            "confidence": 0.95,
            "created_at": "2026-03-15T10:05:00.000000Z",
        },
        {
            "record_id": "rec-002",
            "session_id": "sess-bundle-001",
            "record_type": "observation",
            "content": {"observation": "All tests passing"},
            "reasoning_trace": {
                "actor": "ai",
                "confidence": 1.0,
            },
            "reasoning_hash": "b" * 64,
            "parent_record_id": "a" * 64,
            "actor": "ai",
            "confidence": 1.0,
            "created_at": "2026-03-15T10:10:00.000000Z",
        },
    ]


@pytest.fixture
def constraint_events():
    """Sample constraint events for bundle tests."""
    return [
        {
            "action": "read_file",
            "resource": "/src/main.py",
            "verdict": "auto_approved",
            "dimension": "operational",
            "utilization": 0.1,
            "reason": "Action 'read_file' is allowed",
            "evaluated_at": "2026-03-15T10:06:00.000000Z",
        },
        {
            "action": "write_file",
            "resource": "/src/new.py",
            "verdict": "flagged",
            "dimension": "financial",
            "utilization": 0.75,
            "reason": "Financial utilization elevated",
            "evaluated_at": "2026-03-15T10:08:00.000000Z",
        },
    ]


@pytest.fixture
def public_keys(key_manager):
    """Public keys dict for bundle tests."""
    pem = key_manager.export_public_pem("test-key")
    if isinstance(pem, bytes):
        pem = pem.decode("utf-8")
    return {"test-key": pem}


# ---------------------------------------------------------------------------
# BundleMetadata tests
# ---------------------------------------------------------------------------


class TestBundleMetadata:
    """Test BundleMetadata dataclass."""

    def test_metadata_has_all_required_fields(self):
        from praxis.export.bundle import BundleMetadata

        meta = BundleMetadata(
            session_id="sess-001",
            workspace_name="test-workspace",
            domain="coc",
            duration_seconds=3600,
            total_anchors=3,
            total_decisions=2,
            chain_valid=True,
            created_at="2026-03-15T10:00:00.000000Z",
        )
        assert meta.session_id == "sess-001"
        assert meta.workspace_name == "test-workspace"
        assert meta.domain == "coc"
        assert meta.duration_seconds == 3600
        assert meta.total_anchors == 3
        assert meta.total_decisions == 2
        assert meta.chain_valid is True
        assert meta.created_at == "2026-03-15T10:00:00.000000Z"

    def test_metadata_with_invalid_chain(self):
        from praxis.export.bundle import BundleMetadata

        meta = BundleMetadata(
            session_id="sess-002",
            workspace_name="broken",
            domain="coe",
            duration_seconds=0,
            total_anchors=0,
            total_decisions=0,
            chain_valid=False,
            created_at="2026-03-15T10:00:00.000000Z",
        )
        assert meta.chain_valid is False


# ---------------------------------------------------------------------------
# BundleBuilder initialisation tests
# ---------------------------------------------------------------------------


class TestBundleBuilderInit:
    """Test BundleBuilder construction and validation."""

    def test_builder_requires_session_data(
        self, trust_chain_entries, deliberation_records, constraint_events, public_keys
    ):
        from praxis.export.bundle import BundleBuilder

        builder = BundleBuilder(
            session_data={
                "session_id": "sess-001",
                "workspace_id": "ws-1",
                "domain": "coc",
                "created_at": "2026-03-15T10:00:00.000000Z",
                "ended_at": "2026-03-15T11:00:00.000000Z",
            },
            trust_chain=trust_chain_entries,
            deliberation_records=deliberation_records,
            constraint_events=constraint_events,
            public_keys=public_keys,
        )
        assert builder is not None

    def test_builder_raises_on_missing_session_id(
        self, trust_chain_entries, deliberation_records, constraint_events, public_keys
    ):
        from praxis.export.bundle import BundleBuilder

        with pytest.raises(ValueError, match="session_id"):
            BundleBuilder(
                session_data={"workspace_id": "ws-1"},
                trust_chain=trust_chain_entries,
                deliberation_records=deliberation_records,
                constraint_events=constraint_events,
                public_keys=public_keys,
            )

    def test_builder_raises_on_empty_trust_chain(
        self, session_data, deliberation_records, constraint_events, public_keys
    ):
        from praxis.export.bundle import BundleBuilder

        with pytest.raises(ValueError, match="trust_chain"):
            BundleBuilder(
                session_data=session_data,
                trust_chain=[],
                deliberation_records=deliberation_records,
                constraint_events=constraint_events,
                public_keys=public_keys,
            )

    def test_builder_raises_on_empty_public_keys(
        self, session_data, trust_chain_entries, deliberation_records, constraint_events
    ):
        from praxis.export.bundle import BundleBuilder

        with pytest.raises(ValueError, match="public_keys"):
            BundleBuilder(
                session_data=session_data,
                trust_chain=trust_chain_entries,
                deliberation_records=deliberation_records,
                constraint_events=constraint_events,
                public_keys={},
            )


# ---------------------------------------------------------------------------
# BundleBuilder.build() tests
# ---------------------------------------------------------------------------


class TestBundleBuilderBuild:
    """Test that build() creates a valid ZIP with all required files."""

    def test_build_creates_zip_file(
        self,
        tmp_path,
        session_data,
        trust_chain_entries,
        deliberation_records,
        constraint_events,
        public_keys,
    ):
        from praxis.export.bundle import BundleBuilder

        builder = BundleBuilder(
            session_data=session_data,
            trust_chain=trust_chain_entries,
            deliberation_records=deliberation_records,
            constraint_events=constraint_events,
            public_keys=public_keys,
        )
        output = tmp_path / "bundle.zip"
        result_path = builder.build(output)
        assert result_path.exists()
        assert result_path.suffix == ".zip"
        assert zipfile.is_zipfile(result_path)

    def test_bundle_contains_required_files(
        self,
        tmp_path,
        session_data,
        trust_chain_entries,
        deliberation_records,
        constraint_events,
        public_keys,
    ):
        from praxis.export.bundle import BundleBuilder

        builder = BundleBuilder(
            session_data=session_data,
            trust_chain=trust_chain_entries,
            deliberation_records=deliberation_records,
            constraint_events=constraint_events,
            public_keys=public_keys,
        )
        output = tmp_path / "bundle.zip"
        builder.build(output)

        with zipfile.ZipFile(output, "r") as zf:
            names = zf.namelist()
            # Core structure files
            assert "index.html" in names
            assert "data/bundle-data.js" in names
            assert "verify/verifier.js" in names
            assert "verify/viewer.js" in names
            assert "style/styles.css" in names
            assert "algorithm.txt" in names
            assert "serve.py" in names

    def test_bundle_data_js_has_all_sections(
        self,
        tmp_path,
        session_data,
        trust_chain_entries,
        deliberation_records,
        constraint_events,
        public_keys,
    ):
        from praxis.export.bundle import BundleBuilder

        builder = BundleBuilder(
            session_data=session_data,
            trust_chain=trust_chain_entries,
            deliberation_records=deliberation_records,
            constraint_events=constraint_events,
            public_keys=public_keys,
        )
        output = tmp_path / "bundle.zip"
        builder.build(output)

        with zipfile.ZipFile(output, "r") as zf:
            data_js = zf.read("data/bundle-data.js").decode("utf-8")

        # Must define the global PRAXIS_BUNDLE variable
        assert "window.PRAXIS_BUNDLE" in data_js

        # Extract the JSON by stripping the JS wrapper
        # Format: window.PRAXIS_BUNDLE = { ... };
        json_str = data_js.split("window.PRAXIS_BUNDLE = ", 1)[1]
        json_str = json_str.rstrip().rstrip(";")
        bundle_data = json.loads(json_str)

        # Validate all required sections
        assert "metadata" in bundle_data
        assert "session" in bundle_data
        assert "chain" in bundle_data
        assert "deliberation" in bundle_data
        assert "constraints" in bundle_data
        assert "keys" in bundle_data

    def test_bundle_chain_data_matches_input(
        self,
        tmp_path,
        session_data,
        trust_chain_entries,
        deliberation_records,
        constraint_events,
        public_keys,
    ):
        from praxis.export.bundle import BundleBuilder

        builder = BundleBuilder(
            session_data=session_data,
            trust_chain=trust_chain_entries,
            deliberation_records=deliberation_records,
            constraint_events=constraint_events,
            public_keys=public_keys,
        )
        output = tmp_path / "bundle.zip"
        builder.build(output)

        with zipfile.ZipFile(output, "r") as zf:
            data_js = zf.read("data/bundle-data.js").decode("utf-8")

        json_str = data_js.split("window.PRAXIS_BUNDLE = ", 1)[1].rstrip().rstrip(";")
        bundle_data = json.loads(json_str)

        assert len(bundle_data["chain"]) == len(trust_chain_entries)
        for i, entry in enumerate(bundle_data["chain"]):
            assert entry["content_hash"] == trust_chain_entries[i]["content_hash"]
            assert entry["signature"] == trust_chain_entries[i]["signature"]

    def test_bundle_index_html_is_valid(
        self,
        tmp_path,
        session_data,
        trust_chain_entries,
        deliberation_records,
        constraint_events,
        public_keys,
    ):
        from praxis.export.bundle import BundleBuilder

        builder = BundleBuilder(
            session_data=session_data,
            trust_chain=trust_chain_entries,
            deliberation_records=deliberation_records,
            constraint_events=constraint_events,
            public_keys=public_keys,
        )
        output = tmp_path / "bundle.zip"
        builder.build(output)

        with zipfile.ZipFile(output, "r") as zf:
            html = zf.read("index.html").decode("utf-8")

        assert "<!DOCTYPE html>" in html
        assert "<title>" in html
        assert "Praxis" in html
        assert 'src="verify/verifier.js"' in html
        assert 'src="verify/viewer.js"' in html
        assert 'src="data/bundle-data.js"' in html
        assert 'href="style/styles.css"' in html

    def test_bundle_metadata_is_correct(
        self,
        tmp_path,
        session_data,
        trust_chain_entries,
        deliberation_records,
        constraint_events,
        public_keys,
    ):
        from praxis.export.bundle import BundleBuilder

        builder = BundleBuilder(
            session_data=session_data,
            trust_chain=trust_chain_entries,
            deliberation_records=deliberation_records,
            constraint_events=constraint_events,
            public_keys=public_keys,
        )
        output = tmp_path / "bundle.zip"
        builder.build(output)

        with zipfile.ZipFile(output, "r") as zf:
            data_js = zf.read("data/bundle-data.js").decode("utf-8")

        json_str = data_js.split("window.PRAXIS_BUNDLE = ", 1)[1].rstrip().rstrip(";")
        bundle_data = json.loads(json_str)
        meta = bundle_data["metadata"]

        assert meta["session_id"] == "sess-bundle-001"
        assert meta["domain"] == "coc"
        assert meta["total_anchors"] == 3
        assert meta["total_decisions"] == 1
        assert isinstance(meta["chain_valid"], bool)
        assert isinstance(meta["duration_seconds"], int)

    def test_bundle_serve_py_is_functional(
        self,
        tmp_path,
        session_data,
        trust_chain_entries,
        deliberation_records,
        constraint_events,
        public_keys,
    ):
        from praxis.export.bundle import BundleBuilder

        builder = BundleBuilder(
            session_data=session_data,
            trust_chain=trust_chain_entries,
            deliberation_records=deliberation_records,
            constraint_events=constraint_events,
            public_keys=public_keys,
        )
        output = tmp_path / "bundle.zip"
        builder.build(output)

        with zipfile.ZipFile(output, "r") as zf:
            serve_py = zf.read("serve.py").decode("utf-8")

        # Must be a valid Python script with http.server usage
        assert "http.server" in serve_py
        assert "python" in serve_py.lower() or "#!/" in serve_py

    def test_bundle_algorithm_txt_describes_verification(
        self,
        tmp_path,
        session_data,
        trust_chain_entries,
        deliberation_records,
        constraint_events,
        public_keys,
    ):
        from praxis.export.bundle import BundleBuilder

        builder = BundleBuilder(
            session_data=session_data,
            trust_chain=trust_chain_entries,
            deliberation_records=deliberation_records,
            constraint_events=constraint_events,
            public_keys=public_keys,
        )
        output = tmp_path / "bundle.zip"
        builder.build(output)

        with zipfile.ZipFile(output, "r") as zf:
            algo = zf.read("algorithm.txt").decode("utf-8")

        # Must describe the verification steps
        assert "SHA-256" in algo or "sha256" in algo.lower()
        assert "Ed25519" in algo or "ed25519" in algo.lower()
        assert "JCS" in algo or "canonical" in algo.lower()

    def test_bundle_verifier_js_has_chain_verifier(
        self,
        tmp_path,
        session_data,
        trust_chain_entries,
        deliberation_records,
        constraint_events,
        public_keys,
    ):
        from praxis.export.bundle import BundleBuilder

        builder = BundleBuilder(
            session_data=session_data,
            trust_chain=trust_chain_entries,
            deliberation_records=deliberation_records,
            constraint_events=constraint_events,
            public_keys=public_keys,
        )
        output = tmp_path / "bundle.zip"
        builder.build(output)

        with zipfile.ZipFile(output, "r") as zf:
            verifier_js = zf.read("verify/verifier.js").decode("utf-8")

        assert "ChainVerifier" in verifier_js
        assert "SubtleCrypto" in verifier_js or "crypto.subtle" in verifier_js
        assert "Ed25519" in verifier_js

    def test_bundle_viewer_js_has_bundle_viewer(
        self,
        tmp_path,
        session_data,
        trust_chain_entries,
        deliberation_records,
        constraint_events,
        public_keys,
    ):
        from praxis.export.bundle import BundleBuilder

        builder = BundleBuilder(
            session_data=session_data,
            trust_chain=trust_chain_entries,
            deliberation_records=deliberation_records,
            constraint_events=constraint_events,
            public_keys=public_keys,
        )
        output = tmp_path / "bundle.zip"
        builder.build(output)

        with zipfile.ZipFile(output, "r") as zf:
            viewer_js = zf.read("verify/viewer.js").decode("utf-8")

        assert "BundleViewer" in viewer_js
        assert "renderIntegrityResults" in viewer_js or "renderTimeline" in viewer_js

    def test_bundle_css_has_styles(
        self,
        tmp_path,
        session_data,
        trust_chain_entries,
        deliberation_records,
        constraint_events,
        public_keys,
    ):
        from praxis.export.bundle import BundleBuilder

        builder = BundleBuilder(
            session_data=session_data,
            trust_chain=trust_chain_entries,
            deliberation_records=deliberation_records,
            constraint_events=constraint_events,
            public_keys=public_keys,
        )
        output = tmp_path / "bundle.zip"
        builder.build(output)

        with zipfile.ZipFile(output, "r") as zf:
            css = zf.read("style/styles.css").decode("utf-8")

        # Must have dark/light mode support
        assert "prefers-color-scheme" in css
        # Must have trust state colors
        assert "valid" in css.lower() or "green" in css.lower() or "#2" in css
        # Must be non-trivial
        assert len(css) > 200


# ---------------------------------------------------------------------------
# BundleBuilder._create_metadata() tests
# ---------------------------------------------------------------------------


class TestBundleBuilderMetadata:
    """Test metadata generation."""

    def test_metadata_computes_duration_from_timestamps(
        self,
        session_data,
        trust_chain_entries,
        deliberation_records,
        constraint_events,
        public_keys,
    ):
        from praxis.export.bundle import BundleBuilder

        builder = BundleBuilder(
            session_data=session_data,
            trust_chain=trust_chain_entries,
            deliberation_records=deliberation_records,
            constraint_events=constraint_events,
            public_keys=public_keys,
        )
        meta = builder._create_metadata()
        # Session ran from 10:00 to 11:00 = 3600 seconds
        assert meta.duration_seconds == 3600

    def test_metadata_counts_decisions(
        self,
        session_data,
        trust_chain_entries,
        deliberation_records,
        constraint_events,
        public_keys,
    ):
        from praxis.export.bundle import BundleBuilder

        builder = BundleBuilder(
            session_data=session_data,
            trust_chain=trust_chain_entries,
            deliberation_records=deliberation_records,
            constraint_events=constraint_events,
            public_keys=public_keys,
        )
        meta = builder._create_metadata()
        # 2 deliberation records, 1 is a "decision"
        assert meta.total_decisions == 1

    def test_metadata_counts_anchors(
        self,
        session_data,
        trust_chain_entries,
        deliberation_records,
        constraint_events,
        public_keys,
    ):
        from praxis.export.bundle import BundleBuilder

        builder = BundleBuilder(
            session_data=session_data,
            trust_chain=trust_chain_entries,
            deliberation_records=deliberation_records,
            constraint_events=constraint_events,
            public_keys=public_keys,
        )
        meta = builder._create_metadata()
        assert meta.total_anchors == 3

    def test_metadata_with_no_ended_at_uses_zero_duration(
        self,
        trust_chain_entries,
        deliberation_records,
        constraint_events,
        public_keys,
    ):
        from praxis.export.bundle import BundleBuilder

        session_no_end = {
            "session_id": "sess-open",
            "workspace_id": "ws-1",
            "domain": "coc",
            "created_at": "2026-03-15T10:00:00.000000Z",
            "ended_at": None,
        }
        builder = BundleBuilder(
            session_data=session_no_end,
            trust_chain=trust_chain_entries,
            deliberation_records=deliberation_records,
            constraint_events=constraint_events,
            public_keys=public_keys,
        )
        meta = builder._create_metadata()
        assert meta.duration_seconds == 0


# ---------------------------------------------------------------------------
# BundleBuilder._verify_chain_before_export() tests
# ---------------------------------------------------------------------------


class TestBundleBuilderChainVerification:
    """Test that chain integrity is verified before export."""

    def test_valid_chain_passes_pre_export_check(
        self,
        session_data,
        trust_chain_entries,
        deliberation_records,
        constraint_events,
        public_keys,
    ):
        from praxis.export.bundle import BundleBuilder

        builder = BundleBuilder(
            session_data=session_data,
            trust_chain=trust_chain_entries,
            deliberation_records=deliberation_records,
            constraint_events=constraint_events,
            public_keys=public_keys,
        )
        assert builder._verify_chain_before_export() is True

    def test_tampered_chain_fails_pre_export_check(
        self,
        session_data,
        trust_chain_entries,
        deliberation_records,
        constraint_events,
        public_keys,
    ):
        from praxis.export.bundle import BundleBuilder

        # Tamper with first entry's content_hash
        tampered_chain = list(trust_chain_entries)
        tampered_chain[0] = dict(tampered_chain[0])
        tampered_chain[0]["content_hash"] = "0" * 64

        builder = BundleBuilder(
            session_data=session_data,
            trust_chain=tampered_chain,
            deliberation_records=deliberation_records,
            constraint_events=constraint_events,
            public_keys=public_keys,
        )
        assert builder._verify_chain_before_export() is False


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestBundleBuilderEdgeCases:
    """Test edge cases and error conditions."""

    def test_build_creates_parent_directories(
        self,
        session_data,
        trust_chain_entries,
        deliberation_records,
        constraint_events,
        public_keys,
        tmp_path,
    ):
        from praxis.export.bundle import BundleBuilder

        builder = BundleBuilder(
            session_data=session_data,
            trust_chain=trust_chain_entries,
            deliberation_records=deliberation_records,
            constraint_events=constraint_events,
            public_keys=public_keys,
        )
        output = tmp_path / "nested" / "dir" / "bundle.zip"
        result_path = builder.build(output)
        assert result_path.exists()

    def test_build_with_empty_deliberation(
        self,
        session_data,
        trust_chain_entries,
        constraint_events,
        public_keys,
        tmp_path,
    ):
        from praxis.export.bundle import BundleBuilder

        builder = BundleBuilder(
            session_data=session_data,
            trust_chain=trust_chain_entries,
            deliberation_records=[],
            constraint_events=constraint_events,
            public_keys=public_keys,
        )
        output = tmp_path / "bundle.zip"
        result_path = builder.build(output)
        assert result_path.exists()

    def test_build_with_empty_constraints(
        self,
        session_data,
        trust_chain_entries,
        deliberation_records,
        public_keys,
        tmp_path,
    ):
        from praxis.export.bundle import BundleBuilder

        builder = BundleBuilder(
            session_data=session_data,
            trust_chain=trust_chain_entries,
            deliberation_records=deliberation_records,
            constraint_events=[],
            public_keys=public_keys,
        )
        output = tmp_path / "bundle.zip"
        result_path = builder.build(output)
        assert result_path.exists()

    def test_bundle_public_keys_included_in_data(
        self,
        tmp_path,
        session_data,
        trust_chain_entries,
        deliberation_records,
        constraint_events,
        public_keys,
    ):
        from praxis.export.bundle import BundleBuilder

        builder = BundleBuilder(
            session_data=session_data,
            trust_chain=trust_chain_entries,
            deliberation_records=deliberation_records,
            constraint_events=constraint_events,
            public_keys=public_keys,
        )
        output = tmp_path / "bundle.zip"
        builder.build(output)

        with zipfile.ZipFile(output, "r") as zf:
            data_js = zf.read("data/bundle-data.js").decode("utf-8")

        json_str = data_js.split("window.PRAXIS_BUNDLE = ", 1)[1].rstrip().rstrip(";")
        bundle_data = json.loads(json_str)

        assert "test-key" in bundle_data["keys"]
        assert "BEGIN PUBLIC KEY" in bundle_data["keys"]["test-key"]
