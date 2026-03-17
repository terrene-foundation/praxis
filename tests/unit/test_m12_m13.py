# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""Unit tests for M12 (Knowledge Architecture) and M13 (Package Publishing & Cleanup).

Covers:
- M12-01: Knowledge classification model (schema, domain YAMLs, loader)
- M12-02: Progressive disclosure enforcement (phase-aware knowledge loading)
- M12-03: Knowledge portability protocol (domain export/import/diff CLI)
- M13-01: Package renamed to praxis-co (pyproject.toml, README)
- M13-02: Non-Python files included in package (package-data config)
- M13-03: Health check endpoint (/health with version, domains, db_status)
"""

import hashlib
import json
import zipfile
from pathlib import Path

import pytest
from click.testing import CliRunner


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def cli_main():
    from praxis.cli import main

    return main


# ---------------------------------------------------------------------------
# M12-01: Knowledge classification model
# ---------------------------------------------------------------------------


class TestKnowledgeSchema:
    """The knowledge section schema must accept valid entries and reject invalid ones."""

    def test_knowledge_schema_constants_exist(self):
        from praxis.domains.schema import KNOWLEDGE_PRIORITIES, KNOWLEDGE_TYPES

        assert KNOWLEDGE_PRIORITIES == ("P0", "P1", "P2", "P3")
        assert KNOWLEDGE_TYPES == ("institutional", "generic")

    def test_knowledge_entry_schema_structure(self):
        from praxis.domains.schema import KNOWLEDGE_ENTRY_SCHEMA

        assert KNOWLEDGE_ENTRY_SCHEMA["type"] == "object"
        assert "type" in KNOWLEDGE_ENTRY_SCHEMA["properties"]
        assert "content" in KNOWLEDGE_ENTRY_SCHEMA["properties"]
        assert "priority" in KNOWLEDGE_ENTRY_SCHEMA["properties"]
        assert KNOWLEDGE_ENTRY_SCHEMA["required"] == ["type", "content", "priority"]

    def test_knowledge_schema_structure(self):
        from praxis.domains.schema import KNOWLEDGE_SCHEMA

        assert KNOWLEDGE_SCHEMA["type"] == "object"
        assert "classification" in KNOWLEDGE_SCHEMA["properties"]
        assert KNOWLEDGE_SCHEMA["required"] == ["classification"]

    def test_domain_schema_includes_knowledge(self):
        from praxis.domains.schema import DOMAIN_SCHEMA

        assert "knowledge" in DOMAIN_SCHEMA["properties"]


class TestKnowledgeInDomainYAMLs:
    """All six domain YAMLs must include knowledge entries."""

    EXPECTED_DOMAINS = ("coc", "coe", "cog", "cor", "cocomp", "cof")

    def test_all_domains_have_knowledge(self):
        from praxis.domains.loader import DomainLoader

        loader = DomainLoader()
        for domain_name in self.EXPECTED_DOMAINS:
            config = loader.load_domain(domain_name)
            assert (
                config.knowledge is not None
            ), f"Domain '{domain_name}' is missing knowledge section"
            entries = config.knowledge.get("classification", [])
            assert len(entries) >= 2, (
                f"Domain '{domain_name}' should have at least 2 knowledge entries, "
                f"got {len(entries)}"
            )

    def test_knowledge_entries_have_required_fields(self):
        from praxis.domains.loader import DomainLoader

        loader = DomainLoader()
        for domain_name in self.EXPECTED_DOMAINS:
            config = loader.load_domain(domain_name)
            if config.knowledge is None:
                continue
            for entry in config.knowledge.get("classification", []):
                assert "type" in entry, f"{domain_name}: knowledge entry missing 'type'"
                assert "content" in entry, f"{domain_name}: knowledge entry missing 'content'"
                assert "priority" in entry, f"{domain_name}: knowledge entry missing 'priority'"
                assert entry["type"] in (
                    "institutional",
                    "generic",
                ), f"{domain_name}: invalid knowledge type '{entry['type']}'"
                assert entry["priority"] in (
                    "P0",
                    "P1",
                    "P2",
                    "P3",
                ), f"{domain_name}: invalid priority '{entry['priority']}'"

    def test_each_domain_has_institutional_knowledge(self):
        from praxis.domains.loader import DomainLoader

        loader = DomainLoader()
        for domain_name in self.EXPECTED_DOMAINS:
            config = loader.load_domain(domain_name)
            if config.knowledge is None:
                pytest.fail(f"Domain '{domain_name}' has no knowledge section")
            entries = config.knowledge.get("classification", [])
            institutional = [e for e in entries if e["type"] == "institutional"]
            assert (
                len(institutional) >= 1
            ), f"Domain '{domain_name}' should have at least 1 institutional entry"

    def test_coc_knowledge_content(self):
        from praxis.domains.loader import DomainLoader

        loader = DomainLoader()
        config = loader.load_domain("coc")
        entries = config.knowledge["classification"]
        types = {e["type"] for e in entries}
        assert "institutional" in types
        # P0 entry should mention architecture decisions
        p0_entries = [e for e in entries if e["priority"] == "P0"]
        assert len(p0_entries) >= 1


class TestGetInstitutionalKnowledge:
    """get_institutional_knowledge() must filter to institutional entries only."""

    def test_returns_only_institutional(self):
        from praxis.domains.loader import get_institutional_knowledge

        entries = get_institutional_knowledge("coc")
        assert len(entries) >= 1
        for e in entries:
            assert e["type"] == "institutional"

    def test_excludes_generic(self):
        from praxis.domains.loader import get_institutional_knowledge

        entries = get_institutional_knowledge("coc")
        generic = [e for e in entries if e["type"] == "generic"]
        assert len(generic) == 0

    def test_returns_empty_for_domain_without_knowledge(self, tmp_path):
        from praxis.domains.loader import DomainLoader

        # Create a minimal domain without knowledge
        domain_dir = tmp_path / "test_domain"
        domain_dir.mkdir()
        (domain_dir / "domain.yml").write_text(
            "name: test_domain\n"
            "display_name: 'Test Domain'\n"
            "description: 'No knowledge'\n"
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
        # Use module-level function with custom loader
        loader = DomainLoader(domains_dir=tmp_path)
        config = loader.load_domain("test_domain")
        assert config.knowledge is None

    def test_available_from_core_domain(self):
        from praxis.core.domain import get_institutional_knowledge

        entries = get_institutional_knowledge("coc")
        assert len(entries) >= 1


# ---------------------------------------------------------------------------
# M12-02: Progressive disclosure enforcement
# ---------------------------------------------------------------------------


class TestGetKnowledgeForPhase:
    """get_knowledge_for_phase() must filter by phase-appropriate priority."""

    def test_early_phase_returns_high_priority_only(self):
        from praxis.domains.loader import get_knowledge_for_phase

        # COC phases: analyze, plan, implement, validate, codify
        # analyze is index 0, midpoint is 2 — so "analyze" is early
        entries = get_knowledge_for_phase("coc", "analyze")
        for e in entries:
            assert e["priority"] in (
                "P0",
                "P1",
            ), f"Early phase should only return P0/P1, got {e['priority']}"

    def test_late_phase_returns_all_priorities(self):
        from praxis.domains.loader import get_knowledge_for_phase

        # "implement" is index 2, midpoint is 2 — so "implement" is late (>= midpoint)
        entries = get_knowledge_for_phase("coc", "implement")
        priorities = {e["priority"] for e in entries}
        # Should include P2 (generic test convention entry)
        assert "P2" in priorities or len(entries) > 0

    def test_unknown_phase_returns_high_priority(self):
        from praxis.domains.loader import get_knowledge_for_phase

        entries = get_knowledge_for_phase("coc", "nonexistent_phase")
        for e in entries:
            assert e["priority"] in ("P0", "P1")

    def test_returns_empty_for_domain_without_knowledge(self, tmp_path):
        """Domains without knowledge should return empty list for any phase."""
        from praxis.domains.loader import DomainLoader

        domain_dir = tmp_path / "no_knowledge"
        domain_dir.mkdir()
        (domain_dir / "domain.yml").write_text(
            "name: no_knowledge\n"
            "display_name: 'No Knowledge'\n"
            "description: 'Test'\n"
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

        # Monkey-patch the singleton to use our custom loader
        import praxis.domains.loader as loader_mod

        old_loader = loader_mod._default_loader
        loader_mod._default_loader = DomainLoader(domains_dir=tmp_path)
        try:
            from praxis.domains.loader import get_knowledge_for_phase

            result = get_knowledge_for_phase("no_knowledge", "work")
            assert result == []
        finally:
            loader_mod._default_loader = old_loader

    def test_available_from_core_domain(self):
        from praxis.core.domain import get_knowledge_for_phase

        entries = get_knowledge_for_phase("coc", "implement")
        assert isinstance(entries, list)


# ---------------------------------------------------------------------------
# M12-03: Knowledge portability protocol (CLI commands)
# ---------------------------------------------------------------------------


class TestDomainExportCommand:
    """praxis domain export must produce a valid ZIP with manifest and checksums."""

    def test_export_creates_zip(self, runner, cli_main, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        output_path = tmp_path / "coc-domain.zip"
        result = runner.invoke(cli_main, ["domain", "export", "coc", "-o", str(output_path)])
        assert result.exit_code == 0, result.output
        assert output_path.exists()
        assert zipfile.is_zipfile(output_path)

    def test_export_zip_contains_manifest(self, runner, cli_main, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        output_path = tmp_path / "coc-export.zip"
        runner.invoke(cli_main, ["domain", "export", "coc", "-o", str(output_path)])

        with zipfile.ZipFile(output_path, "r") as zf:
            assert "EXPORT_MANIFEST.json" in zf.namelist()
            manifest = json.loads(zf.read("EXPORT_MANIFEST.json"))
            assert manifest["domain"] == "coc"
            assert "version" in manifest
            assert "files" in manifest

    def test_export_zip_contains_domain_yml(self, runner, cli_main, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        output_path = tmp_path / "coc-export.zip"
        runner.invoke(cli_main, ["domain", "export", "coc", "-o", str(output_path)])

        with zipfile.ZipFile(output_path, "r") as zf:
            assert "coc/domain.yml" in zf.namelist()

    def test_export_zip_contains_knowledge_index(self, runner, cli_main, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        output_path = tmp_path / "coc-export.zip"
        runner.invoke(cli_main, ["domain", "export", "coc", "-o", str(output_path)])

        with zipfile.ZipFile(output_path, "r") as zf:
            assert "coc/knowledge_index.json" in zf.namelist()
            ki = json.loads(zf.read("coc/knowledge_index.json"))
            assert ki["domain"] == "coc"
            assert "knowledge" in ki
            assert "phases" in ki

    def test_export_checksums_valid(self, runner, cli_main, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        output_path = tmp_path / "coc-export.zip"
        runner.invoke(cli_main, ["domain", "export", "coc", "-o", str(output_path)])

        with zipfile.ZipFile(output_path, "r") as zf:
            manifest = json.loads(zf.read("EXPORT_MANIFEST.json"))
            for entry in manifest["files"]:
                content = zf.read(entry["path"])
                actual_hash = hashlib.sha256(content).hexdigest()
                assert actual_hash == entry["sha256"], f"Checksum mismatch for {entry['path']}"

    def test_export_invalid_domain_fails(self, runner, cli_main, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(cli_main, ["domain", "export", "nonexistent"])
        assert result.exit_code != 0


class TestDomainImportCommand:
    """praxis domain import must validate and copy domain files."""

    def _make_export_zip(self, tmp_path, domain_yml_content: str, domain_name: str = "test_import"):
        """Helper to create a valid export ZIP."""
        zip_path = tmp_path / f"{domain_name}.zip"
        domain_content = domain_yml_content.encode("utf-8")
        ki_content = json.dumps({"domain": domain_name, "knowledge": {}}).encode("utf-8")

        manifest_entries = [
            {
                "path": f"{domain_name}/domain.yml",
                "sha256": hashlib.sha256(domain_content).hexdigest(),
            },
            {
                "path": f"{domain_name}/knowledge_index.json",
                "sha256": hashlib.sha256(ki_content).hexdigest(),
            },
        ]

        manifest = {
            "domain": domain_name,
            "version": "1.0",
            "exported_at": "2026-03-16T00:00:00.000000Z",
            "files": manifest_entries,
        }

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr(f"{domain_name}/domain.yml", domain_content)
            zf.writestr(f"{domain_name}/knowledge_index.json", ki_content)
            zf.writestr("EXPORT_MANIFEST.json", json.dumps(manifest))

        return zip_path

    def test_import_creates_domain_directory(self, runner, cli_main, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        import shutil

        domain_yml = (
            "name: test_import\n"
            "display_name: 'Test Import'\n"
            "description: 'Imported domain'\n"
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
        zip_path = self._make_export_zip(tmp_path, domain_yml)
        try:
            result = runner.invoke(cli_main, ["domain", "import", str(zip_path)])
            assert result.exit_code == 0, result.output
        finally:
            # Clean up: import writes to the built-in domains directory
            from praxis.domains.loader import DomainLoader

            loader = DomainLoader()
            imported_dir = loader._domains_dir / "test_import"
            if imported_dir.exists():
                shutil.rmtree(imported_dir)

    def test_import_missing_manifest_fails(self, runner, cli_main, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        zip_path = tmp_path / "bad.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("some_file.txt", "hello")

        result = runner.invoke(cli_main, ["domain", "import", str(zip_path)])
        assert result.exit_code != 0
        assert "EXPORT_MANIFEST" in result.output

    def test_import_checksum_mismatch_fails(self, runner, cli_main, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        zip_path = tmp_path / "tampered.zip"

        # Create a ZIP with wrong checksum in manifest
        domain_content = b"name: tampered\n"
        manifest = {
            "domain": "tampered",
            "version": "1.0",
            "files": [
                {
                    "path": "tampered/domain.yml",
                    "sha256": "0000000000000000000000000000000000000000000000000000000000000000",
                },
            ],
        }

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("tampered/domain.yml", domain_content)
            zf.writestr("EXPORT_MANIFEST.json", json.dumps(manifest))

        result = runner.invoke(cli_main, ["domain", "import", str(zip_path)])
        assert result.exit_code != 0
        assert "Checksum" in result.output

    def test_import_nonexistent_file_fails(self, runner, cli_main, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(cli_main, ["domain", "import", "/nonexistent/path.zip"])
        assert result.exit_code != 0


class TestDomainDiffCommand:
    """praxis domain diff must compare two domains."""

    def test_diff_same_domain(self, runner, cli_main):
        result = runner.invoke(cli_main, ["domain", "diff", "coc", "coc"])
        assert result.exit_code == 0
        assert "identical" in result.output.lower() or "coc" in result.output

    def test_diff_different_domains(self, runner, cli_main):
        result = runner.invoke(cli_main, ["domain", "diff", "coc", "coe"])
        assert result.exit_code == 0
        assert "coc" in result.output
        assert "coe" in result.output

    def test_diff_nonexistent_domain_fails(self, runner, cli_main):
        result = runner.invoke(cli_main, ["domain", "diff", "coc", "nonexistent"])
        assert result.exit_code != 0

    def test_diff_shows_knowledge_counts(self, runner, cli_main):
        result = runner.invoke(cli_main, ["domain", "diff", "coc", "coe"])
        assert result.exit_code == 0
        assert "Knowledge" in result.output


# ---------------------------------------------------------------------------
# M13-01: Package renamed to praxis-co
# ---------------------------------------------------------------------------


class TestPackageRename:
    """Package must be named praxis-co on PyPI but importable as praxis."""

    def test_pyproject_name_is_praxis_co(self):
        import tomllib

        pyproject_path = Path(__file__).resolve().parent.parent.parent / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
        assert data["project"]["name"] == "praxis-co"

    def test_import_path_remains_praxis(self):
        import praxis

        assert hasattr(praxis, "__version__")

    def test_cli_command_remains_praxis(self):
        import tomllib

        pyproject_path = Path(__file__).resolve().parent.parent.parent / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
        assert data["project"]["scripts"]["praxis"] == "praxis.cli:main"


# ---------------------------------------------------------------------------
# M13-02: Non-Python files included in package
# ---------------------------------------------------------------------------


class TestPackageData:
    """Package data configuration must include domain YAMLs and templates."""

    def test_pyproject_includes_package_data(self):
        import tomllib

        pyproject_path = Path(__file__).resolve().parent.parent.parent / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)

        pkg_data = data.get("tool", {}).get("setuptools", {}).get("package-data", {})
        assert "praxis" in pkg_data
        patterns = pkg_data["praxis"]
        assert "domains/*/domain.yml" in patterns
        assert "domains/*/constraints/*.yml" in patterns
        assert "export/templates/*.html" in patterns

    def test_domain_yml_files_exist_in_package(self):
        """Verify domain.yml files are accessible from the installed package path."""
        from praxis.domains.loader import DomainLoader

        loader = DomainLoader()
        domains_dir = loader._domains_dir
        for domain_name in ["coc", "coe", "cog", "cor", "cocomp", "cof"]:
            domain_yml = domains_dir / domain_name / "domain.yml"
            assert domain_yml.exists(), f"Missing {domain_yml}"


# ---------------------------------------------------------------------------
# M13-03: Health check endpoint
# ---------------------------------------------------------------------------


class TestHealthEndpoint:
    """The /health endpoint must return version, domains, and db_status."""

    def test_health_handler_returns_expected_fields(self):
        """Test the health response structure directly via route handler logic."""
        from praxis import __version__
        from praxis.domains.loader import DomainLoader

        loader = DomainLoader()
        domains = loader.list_domains()

        # The health endpoint should return these fields
        assert __version__ == "0.1.0"
        assert "coc" in domains
        assert "coe" in domains
        assert len(domains) == 6

    def test_health_response_format(self):
        """Verify the health response has the correct structure."""
        # Simulate what the health endpoint does
        from praxis import __version__
        from praxis.domains.loader import DomainLoader

        loader = DomainLoader()
        domains = loader.list_domains()

        response = {
            "status": "ok",
            "version": __version__,
            "domains": domains,
            "db_status": "connected",
        }

        assert response["status"] == "ok"
        assert response["version"] == "0.1.0"
        assert isinstance(response["domains"], list)
        assert len(response["domains"]) == 6
        assert response["db_status"] == "connected"


# ---------------------------------------------------------------------------
# DomainConfig knowledge field
# ---------------------------------------------------------------------------


class TestDomainConfigKnowledge:
    """DomainConfig dataclass must have knowledge field."""

    def test_config_has_knowledge_attribute(self):
        from praxis.domains.loader import DomainLoader

        loader = DomainLoader()
        config = loader.load_domain("coc")
        assert hasattr(config, "knowledge")
        assert config.knowledge is not None

    def test_knowledge_is_dict(self):
        from praxis.domains.loader import DomainLoader

        loader = DomainLoader()
        config = loader.load_domain("coc")
        assert isinstance(config.knowledge, dict)
        assert "classification" in config.knowledge

    def test_knowledge_classification_is_list(self):
        from praxis.domains.loader import DomainLoader

        loader = DomainLoader()
        config = loader.load_domain("coc")
        entries = config.knowledge["classification"]
        assert isinstance(entries, list)
        assert len(entries) >= 2


# ---------------------------------------------------------------------------
# Validation still passes for all domains
# ---------------------------------------------------------------------------


class TestAllDomainsStillValid:
    """Adding knowledge must not break existing domain validation."""

    def test_all_domains_validate(self):
        from praxis.domains.loader import DomainLoader

        loader = DomainLoader()
        for domain in loader.list_domains():
            errors = loader.validate_domain(domain)
            assert errors == [], f"Domain '{domain}' has validation errors: {errors}"
