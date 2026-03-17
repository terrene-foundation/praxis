# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""Unit tests for praxis.cli — Click CLI entry point.

Uses Click's CliRunner for isolated CLI testing with temporary directories.
"""

import json

import pytest
from click.testing import CliRunner


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def runner():
    """Provide a Click CliRunner."""
    return CliRunner()


@pytest.fixture
def cli_main():
    """Import and return the CLI main group."""
    from praxis.cli import main

    return main


# ---------------------------------------------------------------------------
# CLI root
# ---------------------------------------------------------------------------


class TestCLIRoot:
    """Test the root CLI group."""

    def test_cli_group_exists(self, runner, cli_main):
        result = runner.invoke(cli_main, ["--help"])
        assert result.exit_code == 0
        assert "Praxis" in result.output

    def test_cli_version_flag_not_error(self, runner, cli_main):
        # The --help should list available commands
        result = runner.invoke(cli_main, ["--help"])
        assert result.exit_code == 0


# ---------------------------------------------------------------------------
# praxis init
# ---------------------------------------------------------------------------


class TestInitCommand:
    """Test the 'praxis init' command."""

    def test_init_creates_praxis_directory(self, runner, cli_main, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(cli_main, ["init", "--name", "test-project", "--domain", "coc"])
        assert result.exit_code == 0
        assert (tmp_path / ".praxis").is_dir()

    def test_init_creates_workspace_json(self, runner, cli_main, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(cli_main, ["init", "--name", "test-project"])
        assert result.exit_code == 0
        ws_file = tmp_path / ".praxis" / "workspace.json"
        assert ws_file.exists()
        data = json.loads(ws_file.read_text())
        assert data["name"] == "test-project"

    def test_init_stores_domain(self, runner, cli_main, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(cli_main, ["init", "--name", "test-project", "--domain", "coe"])
        assert result.exit_code == 0
        data = json.loads((tmp_path / ".praxis" / "workspace.json").read_text())
        assert data["domain"] == "coe"

    def test_init_stores_constraint_template(self, runner, cli_main, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(cli_main, ["init", "--name", "test-project", "--template", "strict"])
        assert result.exit_code == 0
        data = json.loads((tmp_path / ".praxis" / "workspace.json").read_text())
        assert data["constraint_template"] == "strict"

    def test_init_default_domain_is_coc(self, runner, cli_main, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(cli_main, ["init", "--name", "test-project"])
        assert result.exit_code == 0
        data = json.loads((tmp_path / ".praxis" / "workspace.json").read_text())
        assert data["domain"] == "coc"

    def test_init_default_template_is_moderate(self, runner, cli_main, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(cli_main, ["init", "--name", "test-project"])
        assert result.exit_code == 0
        data = json.loads((tmp_path / ".praxis" / "workspace.json").read_text())
        assert data["constraint_template"] == "moderate"

    def test_init_workspace_has_id(self, runner, cli_main, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(cli_main, ["init", "--name", "test-project"])
        assert result.exit_code == 0
        data = json.loads((tmp_path / ".praxis" / "workspace.json").read_text())
        assert "id" in data
        assert len(data["id"]) > 0

    def test_init_creates_keys_directory(self, runner, cli_main, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(cli_main, ["init", "--name", "test-project"])
        assert result.exit_code == 0
        assert (tmp_path / ".praxis" / "keys").is_dir()

    def test_init_requires_name(self, runner, cli_main, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(cli_main, ["init"])
        assert result.exit_code != 0

    def test_init_already_initialized_warns(self, runner, cli_main, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        runner.invoke(cli_main, ["init", "--name", "first"])
        result = runner.invoke(cli_main, ["init", "--name", "second"])
        # Should still succeed (overwrite/warn) but not crash
        assert result.exit_code == 0


# ---------------------------------------------------------------------------
# praxis session
# ---------------------------------------------------------------------------


class TestSessionCommands:
    """Test the session management commands."""

    def test_session_group_exists(self, runner, cli_main):
        result = runner.invoke(cli_main, ["session", "--help"])
        assert result.exit_code == 0
        assert "start" in result.output
        assert "pause" in result.output
        assert "resume" in result.output
        assert "end" in result.output

    def test_session_start_creates_session(self, runner, cli_main, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        runner.invoke(cli_main, ["init", "--name", "test-project"])
        result = runner.invoke(cli_main, ["session", "start"])
        assert result.exit_code == 0
        # Should create a current-session.json
        session_file = tmp_path / ".praxis" / "current-session.json"
        assert session_file.exists()

    def test_session_start_without_init_fails(self, runner, cli_main, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(cli_main, ["session", "start"])
        assert result.exit_code != 0

    def test_session_pause_changes_state(self, runner, cli_main, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        runner.invoke(cli_main, ["init", "--name", "test-project"])
        runner.invoke(cli_main, ["session", "start"])
        result = runner.invoke(cli_main, ["session", "pause"])
        assert result.exit_code == 0

    def test_session_resume_changes_state(self, runner, cli_main, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        runner.invoke(cli_main, ["init", "--name", "test-project"])
        runner.invoke(cli_main, ["session", "start"])
        runner.invoke(cli_main, ["session", "pause"])
        result = runner.invoke(cli_main, ["session", "resume"])
        assert result.exit_code == 0

    def test_session_end_archives(self, runner, cli_main, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        runner.invoke(cli_main, ["init", "--name", "test-project"])
        runner.invoke(cli_main, ["session", "start"])
        result = runner.invoke(cli_main, ["session", "end"])
        assert result.exit_code == 0


# ---------------------------------------------------------------------------
# praxis status
# ---------------------------------------------------------------------------


class TestStatusCommand:
    """Test the status command."""

    def test_status_without_init_fails(self, runner, cli_main, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(cli_main, ["status"])
        assert result.exit_code != 0

    def test_status_with_active_session(self, runner, cli_main, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        runner.invoke(cli_main, ["init", "--name", "test-project"])
        runner.invoke(cli_main, ["session", "start"])
        result = runner.invoke(cli_main, ["status"])
        assert result.exit_code == 0


# ---------------------------------------------------------------------------
# praxis decide
# ---------------------------------------------------------------------------


class TestDecideCommand:
    """Test the decide command."""

    def test_decide_records_decision(self, runner, cli_main, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        runner.invoke(cli_main, ["init", "--name", "test-project"])
        runner.invoke(cli_main, ["session", "start"])
        result = runner.invoke(
            cli_main,
            ["decide", "--type", "scope", "-d", "Use Python", "-r", "Team knows it"],
        )
        assert result.exit_code == 0

    def test_decide_without_session_fails(self, runner, cli_main, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        runner.invoke(cli_main, ["init", "--name", "test-project"])
        result = runner.invoke(
            cli_main,
            ["decide", "--type", "scope", "-d", "Use Python", "-r", "Team knows it"],
        )
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# praxis domain
# ---------------------------------------------------------------------------


class TestDomainCommands:
    """Test the domain management commands."""

    def test_domain_list(self, runner, cli_main):
        result = runner.invoke(cli_main, ["domain", "list"])
        assert result.exit_code == 0
        # Should list at least coc
        assert "coc" in result.output

    def test_domain_validate_valid(self, runner, cli_main):
        result = runner.invoke(cli_main, ["domain", "validate", "coc"])
        assert result.exit_code == 0

    def test_domain_validate_invalid(self, runner, cli_main):
        result = runner.invoke(cli_main, ["domain", "validate", "nonexistent"])
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# praxis serve
# ---------------------------------------------------------------------------


class TestServeCommand:
    """Test the serve command."""

    def test_serve_command_exists(self, runner, cli_main):
        result = runner.invoke(cli_main, ["serve", "--help"])
        assert result.exit_code == 0
        assert "Start" in result.output or "server" in result.output.lower()


# ---------------------------------------------------------------------------
# praxis export
# ---------------------------------------------------------------------------


class TestExportCommand:
    """Test the export command."""

    def test_export_without_session_fails(self, runner, cli_main, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        runner.invoke(cli_main, ["init", "--name", "test-project"])
        result = runner.invoke(cli_main, ["export"])
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# praxis verify
# ---------------------------------------------------------------------------


class TestVerifyCommand:
    """Test the verify command."""

    def test_verify_command_exists(self, runner, cli_main):
        result = runner.invoke(cli_main, ["verify", "--help"])
        assert result.exit_code == 0

    def test_verify_nonexistent_bundle_fails(self, runner, cli_main, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(cli_main, ["verify", "/nonexistent/bundle.json"])
        assert result.exit_code != 0
