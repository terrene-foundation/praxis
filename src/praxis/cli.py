# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""
Praxis CLI — command-line interface for trust-aware human-AI collaboration.

Entry point declared in pyproject.toml: praxis = "praxis.cli:main"

Workspace state is stored in .praxis/ directory:
    .praxis/workspace.json        — Workspace config (id, name, domain, template)
    .praxis/current-session.json  — Active session reference
    .praxis/keys/                 — Ed25519 keys for this workspace
"""

from __future__ import annotations

import json
import logging
import sys
import uuid
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

logger = logging.getLogger(__name__)
console = Console()

# Workspace state directory name
PRAXIS_DIR = ".praxis"
WORKSPACE_FILE = "workspace.json"
SESSION_FILE = "current-session.json"
KEYS_DIR = "keys"


# ---------------------------------------------------------------------------
# Workspace state helpers
# ---------------------------------------------------------------------------


def _praxis_dir() -> Path:
    """Get the .praxis directory in the current working directory."""
    return Path.cwd() / PRAXIS_DIR


def _require_workspace() -> dict[str, Any]:
    """Load workspace config, raising ClickException if not initialized.

    Returns:
        The workspace config dict.

    Raises:
        click.ClickException: If .praxis/workspace.json does not exist.
    """
    ws_file = _praxis_dir() / WORKSPACE_FILE
    if not ws_file.exists():
        raise click.ClickException("Not a Praxis workspace. Run 'praxis init --name <name>' first.")
    return json.loads(ws_file.read_text())


def _load_session() -> dict[str, Any] | None:
    """Load the current session reference, or None if no active session."""
    session_file = _praxis_dir() / SESSION_FILE
    if not session_file.exists():
        return None
    return json.loads(session_file.read_text())


def _save_session(session_data: dict[str, Any]) -> None:
    """Save session data to .praxis/current-session.json."""
    session_file = _praxis_dir() / SESSION_FILE
    session_file.write_text(json.dumps(session_data, indent=2))


def _clear_session() -> None:
    """Remove the current session file."""
    session_file = _praxis_dir() / SESSION_FILE
    if session_file.exists():
        session_file.unlink()


def _require_session() -> dict[str, Any]:
    """Load the current session, raising ClickException if none exists.

    Returns:
        The current session dict.

    Raises:
        click.ClickException: If no active session exists.
    """
    session = _load_session()
    if session is None:
        raise click.ClickException("No active session. Run 'praxis session start' first.")
    return session


def _get_session_manager(workspace: dict[str, Any]):
    """Create a SessionManager for the workspace.

    Uses the workspace key directory for cryptographic signing.
    """
    from praxis.core.session import SessionManager

    key_dir = _praxis_dir() / KEYS_DIR
    try:
        from praxis.trust.keys import KeyManager

        km = KeyManager(key_dir)
        key_id = workspace.get("key_id", "workspace")
        if not km.has_key(key_id):
            km.generate_key(key_id)
        return SessionManager(key_manager=km, key_id=key_id)
    except Exception:
        return SessionManager(key_manager=None)


def _hydrate_session(mgr, session_data: dict[str, Any]) -> None:
    """Ensure a CLI session is accessible via SessionManager.

    With DataFlow persistence, sessions created by ``session start``
    are already in the database.  This function verifies the session
    exists and is readable — if it isn't (e.g. because the DB was
    wiped), it re-creates the record from the CLI reference file.
    """
    sid = session_data["session_id"]
    try:
        mgr.get_session(sid)
    except KeyError:
        # Session not in DB — re-create from CLI reference file.
        # This covers the edge case where the DB was deleted but the
        # .praxis/current-session.json file still exists.
        from praxis.persistence.db_ops import db_create
        from praxis.core.session import _session_to_db

        if "updated_at" not in session_data:
            session_data["updated_at"] = session_data.get("created_at", "")
        if "ended_at" not in session_data:
            session_data["ended_at"] = None
        if "metadata" not in session_data:
            session_data["metadata"] = {}
        db_create("Session", _session_to_db(session_data))


def _load_capture_config(domain: str) -> dict[str, Any] | None:
    """Load the capture config from a domain YAML, or None on failure."""
    try:
        from praxis.domains.loader import DomainLoader

        loader = DomainLoader()
        config = loader.load_domain(domain)
        return dict(config.capture) if config.capture else None
    except Exception:
        return None


def _get_deliberation_engine(
    session_id: str,
    workspace: dict[str, Any],
    domain: str | None = None,
):
    """Create a DeliberationEngine for the session.

    When a domain is provided, loads the domain's capture config so that
    decision type validation and observation targets are available.
    """
    from praxis.core.deliberation import DeliberationEngine

    capture_config = _load_capture_config(domain) if domain else None

    key_dir = _praxis_dir() / KEYS_DIR
    try:
        from praxis.trust.keys import KeyManager

        km = KeyManager(key_dir)
        key_id = workspace.get("key_id", "workspace")
        return DeliberationEngine(
            session_id=session_id,
            key_manager=km,
            key_id=key_id,
            capture_config=capture_config,
        )
    except Exception:
        return DeliberationEngine(session_id=session_id, capture_config=capture_config)


# ---------------------------------------------------------------------------
# CLI root group
# ---------------------------------------------------------------------------


@click.group()
def main():
    """Praxis -- CO platform for trust-aware human-AI collaboration."""
    pass


# ---------------------------------------------------------------------------
# praxis init
# ---------------------------------------------------------------------------


@main.command()
@click.option("--name", required=True, help="Workspace name")
@click.option("--domain", default="coc", help="CO domain (coc, coe, cog, etc.)")
@click.option(
    "--template", default="moderate", help="Constraint template (strict, moderate, permissive)"
)
def init(name: str, domain: str, template: str):
    """Initialize a new Praxis workspace in the current directory."""
    praxis_dir = _praxis_dir()
    keys_dir = praxis_dir / KEYS_DIR

    # Create directories
    praxis_dir.mkdir(parents=True, exist_ok=True)
    keys_dir.mkdir(parents=True, exist_ok=True)

    # Generate workspace config
    workspace = {
        "id": str(uuid.uuid4()),
        "name": name,
        "domain": domain,
        "constraint_template": template,
        "key_id": "workspace",
    }

    ws_file = praxis_dir / WORKSPACE_FILE
    ws_file.write_text(json.dumps(workspace, indent=2))

    # Generate signing key
    try:
        from praxis.trust.keys import KeyManager

        km = KeyManager(keys_dir)
        if not km.has_key("workspace"):
            km.generate_key("workspace")
    except Exception as exc:
        logger.debug("Could not generate workspace key: %s", exc)

    console.print(f"[green]Workspace '{name}' initialized[/green]")
    console.print(f"  Domain: {domain}")
    console.print(f"  Template: {template}")
    console.print(f"  Directory: {praxis_dir}")


# ---------------------------------------------------------------------------
# praxis session
# ---------------------------------------------------------------------------


@main.group()
def session():
    """Manage CO collaboration sessions."""
    pass


@session.command()
@click.option("--context", "-c", default="", help="Session description/context")
def start(context: str):
    """Start a new CO collaboration session."""
    workspace = _require_workspace()
    mgr = _get_session_manager(workspace)

    session_data = mgr.create_session(
        workspace_id=workspace["id"],
        domain=workspace.get("domain", "coc"),
        constraint_template=workspace.get("constraint_template", "moderate"),
    )

    # Save the full session data plus the manager reference info.
    # genesis_chain_entry is persisted so that export can build a verifiable
    # trust chain without re-computing the full genesis payload from scratch.
    session_ref = {
        "session_id": session_data["session_id"],
        "workspace_id": session_data["workspace_id"],
        "state": session_data["state"],
        "domain": session_data["domain"],
        "constraint_envelope": session_data["constraint_envelope"],
        "genesis_id": session_data.get("genesis_id"),
        "genesis_chain_entry": session_data.get("genesis_chain_entry"),
        "current_phase": session_data.get("current_phase"),
        "phase_list": session_data.get("phase_list", []),
        "created_at": session_data["created_at"],
        "context": context,
    }
    _save_session(session_ref)

    console.print("[green]Session started[/green]")
    console.print(f"  Session ID: {session_data['session_id']}")
    console.print(f"  Domain: {session_data['domain']}")
    console.print(f"  State: {session_data['state']}")
    if context:
        console.print(f"  Context: {context}")


@session.command()
def pause():
    """Pause the current session."""
    workspace = _require_workspace()
    session_data = _require_session()
    mgr = _get_session_manager(workspace)

    try:
        # Re-create the session in the manager
        _hydrate_session(mgr, session_data)

        result = mgr.pause_session(session_data["session_id"])
        session_data["state"] = result["state"]
        _save_session(session_data)
        console.print("[yellow]Session paused[/yellow]")
    except Exception as exc:
        raise click.ClickException(str(exc))


@session.command()
def resume():
    """Resume the paused session."""
    workspace = _require_workspace()
    session_data = _require_session()
    mgr = _get_session_manager(workspace)

    try:
        _hydrate_session(mgr, session_data)

        result = mgr.resume_session(session_data["session_id"])
        session_data["state"] = result["state"]
        _save_session(session_data)
        console.print("[green]Session resumed[/green]")
    except Exception as exc:
        raise click.ClickException(str(exc))


@session.command()
@click.option("--summary", "-s", default="", help="Session summary")
def end(summary: str):
    """End the current session."""
    workspace = _require_workspace()
    session_data = _require_session()
    mgr = _get_session_manager(workspace)

    try:
        _hydrate_session(mgr, session_data)

        result = mgr.end_session(session_data["session_id"], summary=summary)
        session_data["state"] = result["state"]
        session_data["ended_at"] = result.get("ended_at")
        _save_session(session_data)
        console.print("[red]Session ended[/red]")
    except Exception as exc:
        raise click.ClickException(str(exc))


# ---------------------------------------------------------------------------
# praxis status
# ---------------------------------------------------------------------------


@main.command()
def status():
    """Show session status and constraint gauges."""
    workspace = _require_workspace()
    session_data = _require_session()

    # Session info panel
    state_color = {"active": "green", "paused": "yellow", "archived": "dim"}.get(
        session_data["state"], "white"
    )
    console.print(
        Panel(
            f"[bold]{workspace['name']}[/bold]\n"
            f"  ID: {session_data['session_id'][:12]}...  "
            f"Domain: [cyan]{session_data.get('domain', 'unknown')}[/cyan]  "
            f"State: [{state_color}]{session_data['state'].upper()}[/{state_color}]\n"
            f"  Started: {session_data.get('created_at', 'unknown')[:19]}",
            title="Session",
        )
    )

    # Constraint gauges
    envelope = session_data.get("constraint_envelope", {})
    if envelope:
        console.print("\n[bold]Constraint Gauges[/bold]")
        dimensions = [
            ("Financial", "financial", "max_spend", "current_spend", "$"),
            ("Operational", "operational", "max_actions_per_hour", "actions_this_hour", ""),
            ("Temporal", "temporal", "max_duration_minutes", "elapsed_minutes", "min"),
            ("Data Access", "data_access", None, None, ""),
            ("Communication", "communication", None, None, ""),
        ]
        for label, dim, max_key, current_key, unit in dimensions:
            dim_data = envelope.get(dim, {})
            if max_key and max_key in dim_data:
                max_val = float(dim_data[max_key])
                cur_val = float(dim_data.get(current_key, 0)) if current_key else 0
                if max_val > 0:
                    pct = cur_val / max_val
                    color = "green" if pct < 0.7 else "yellow" if pct < 0.9 else "red"
                    bar = _make_gauge_bar(pct)
                    suffix = (
                        f"  {unit}{cur_val:.0f} / {unit}{max_val:.0f}"
                        if unit
                        else f"  {cur_val:.0f} / {max_val:.0f}"
                    )
                    console.print(f"  {label:<15} [{color}]{bar}[/{color}] {pct:>4.0%}{suffix}")
                else:
                    console.print(f"  {label:<15} [green]{'█' * 20}[/green]  OK")
            else:
                console.print(f"  {label:<15} [green]{'█' * 20}[/green]  OK")


def _make_gauge_bar(pct: float, width: int = 20) -> str:
    """Create a text-based progress bar."""
    filled = int(min(pct, 1.0) * width)
    return "█" * filled + "░" * (width - filled)


# ---------------------------------------------------------------------------
# praxis decide
# ---------------------------------------------------------------------------


@main.command()
@click.option("--type", "decision_type", default="scope", help="Decision type")
@click.option("--decision", "-d", required=True, help="The decision made")
@click.option("--rationale", "-r", required=True, help="Why this decision was made")
@click.option("--alternative", "-a", multiple=True, help="Alternatives considered (repeatable)")
@click.option("--confidence", type=float, default=None, help="Confidence score (0.0-1.0)")
def decide(
    decision_type: str, decision: str, rationale: str, alternative: tuple, confidence: float | None
):
    """Record a human decision in the deliberation log."""
    workspace = _require_workspace()
    session_data = _require_session()

    if session_data["state"] != "active":
        raise click.ClickException(
            f"Session is '{session_data['state']}', not 'active'. "
            f"Cannot record decisions in a non-active session."
        )

    sid = session_data["session_id"]
    domain = session_data.get("domain")
    deliberation_file = _praxis_dir() / f"deliberation-{sid}.json"

    # Records are now persisted to DataFlow. The engine reads the last hash
    # from the database automatically, so no file-based chain reload is needed.
    engine = _get_deliberation_engine(sid, workspace, domain=domain)

    try:
        record = engine.record_decision(
            decision=f"[{decision_type}] {decision}",
            rationale=rationale,
            actor="human",
            alternatives=list(alternative) if alternative else None,
            confidence=confidence,
            decision_type=decision_type,
        )
    except Exception as exc:
        raise click.ClickException(str(exc))

    # Also persist all records to disk so export can include them when
    # the database is not accessible (e.g. offline bundle generation).
    all_records, _total = engine.get_timeline(limit=10000)
    deliberation_file.write_text(json.dumps(all_records, indent=2, default=str))

    console.print("[green]Decision recorded[/green]")
    console.print(f"  Record ID: {record['record_id']}")
    console.print(f"  Hash: {record['reasoning_hash'][:16]}...")
    if alternative:
        console.print(f"  Alternatives: {len(alternative)} considered")
    if confidence is not None:
        console.print(f"  Confidence: {confidence:.0%}")


# ---------------------------------------------------------------------------
# praxis export
# ---------------------------------------------------------------------------


@main.command()
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["bundle", "json"]),
    default="bundle",
    help="Export format",
)
@click.option("--output", "-o", default=None, help="Output path")
def export(output_format: str, output: str | None):
    """Export a verification bundle for the current session."""
    workspace = _require_workspace()
    session_data = _require_session()

    if session_data.get("state") not in ("active", "paused", "archived"):
        raise click.ClickException("No valid session to export.")

    sid = session_data["session_id"][:8]

    if output_format == "json":
        # Minimal JSON export
        bundle = {
            "session_id": session_data["session_id"],
            "workspace": workspace["name"],
            "domain": session_data.get("domain", "unknown"),
            "state": session_data["state"],
            "constraint_envelope": session_data.get("constraint_envelope", {}),
            "genesis_id": session_data.get("genesis_id"),
            "created_at": session_data.get("created_at"),
        }
        output_path = Path(output) if output else Path.cwd() / f"praxis-{sid}.json"
        output_path.write_text(json.dumps(bundle, indent=2))
        console.print(f"[green]JSON exported to {output_path}[/green]")
    else:
        # Full verification bundle ZIP via BundleBuilder
        from praxis.export.bundle import BundleBuilder
        from praxis.trust.keys import KeyManager

        key_dir = Path.cwd() / PRAXIS_DIR / "keys"
        km = KeyManager(key_dir)

        # Collect public keys
        public_keys = {}
        for kid in km.list_keys():
            public_keys[kid] = km.export_public_pem(kid).decode()

        # Collect trust chain entries from genesis.
        # The full genesis_chain_entry (payload + hash + signature) is persisted
        # in current-session.json by `session start`. Use it directly so the
        # chain verifier can re-compute and match the content hash.
        trust_chain = []
        genesis_chain_entry = session_data.get("genesis_chain_entry")
        if genesis_chain_entry:
            trust_chain.append(genesis_chain_entry)
        elif session_data.get("genesis_id"):
            # Fallback for sessions created before genesis_chain_entry was stored.
            # The hash won't verify but the bundle will still be produced.
            trust_chain.append(
                {
                    "payload": {"type": "genesis", "session_id": session_data["session_id"]},
                    "content_hash": session_data["genesis_id"],
                    "signature": "",
                    "signer_key_id": workspace.get("key_id", "workspace"),
                    "parent_hash": None,
                }
            )

        # Deliberation records are now persisted to DataFlow.  Read them
        # from the database first; fall back to the on-disk JSON file that
        # the CLI ``decide`` command also writes as a convenience copy.
        deliberation_records: list[dict] = []
        try:
            from praxis.core.deliberation import DeliberationEngine

            engine = _get_deliberation_engine(session_data["session_id"], workspace)
            deliberation_records, _ = engine.get_timeline(limit=10000)
        except Exception as exc:
            logger.debug("Could not load deliberation records from DB: %s", exc)
            deliberation_file = _praxis_dir() / f"deliberation-{session_data['session_id']}.json"
            if deliberation_file.exists():
                try:
                    deliberation_records = json.loads(deliberation_file.read_text())
                except (json.JSONDecodeError, OSError) as exc2:
                    logger.debug("Could not load deliberation records from file: %s", exc2)

        # Build bundle
        output_path = Path(output) if output else Path.cwd() / f"praxis-{sid}-bundle.zip"
        try:
            builder = BundleBuilder(
                session_data=session_data,
                trust_chain=(
                    trust_chain
                    if trust_chain
                    else [
                        {
                            "payload": {"type": "genesis"},
                            "content_hash": "none",
                            "signature": "",
                            "signer_key_id": "default",
                            "parent_hash": None,
                        }
                    ]
                ),
                deliberation_records=deliberation_records,
                constraint_events=[],
                public_keys=public_keys if public_keys else {"default": "none"},
            )
            builder.build(output_path)
            console.print(f"[green]Verification bundle exported to {output_path}[/green]")
            console.print(f"  Open in browser or run: praxis verify {output_path}")
        except Exception as e:
            logger.debug("BundleBuilder error: %s", e)
            # Fallback to JSON
            bundle = {
                "session_id": session_data["session_id"],
                "workspace": workspace["name"],
                "domain": session_data.get("domain", "unknown"),
                "deliberation": deliberation_records,
            }
            fallback_path = Path.cwd() / f"praxis-{sid}.json"
            fallback_path.write_text(json.dumps(bundle, indent=2, default=str))
            console.print(
                f"[yellow]Bundle builder unavailable, JSON exported to {fallback_path}[/yellow]"
            )


# ---------------------------------------------------------------------------
# praxis verify
# ---------------------------------------------------------------------------


@main.command()
@click.argument("bundle_path")
def verify(bundle_path: str):
    """Verify a verification bundle (ZIP or JSON)."""
    import zipfile

    path = Path(bundle_path)
    if not path.exists():
        raise click.ClickException(f"Bundle file not found: {bundle_path}")

    bundle = None

    # Detect ZIP bundles by magic bytes and file extension
    if path.suffix.lower() == ".zip" or zipfile.is_zipfile(path):
        try:
            with zipfile.ZipFile(path, "r") as zf:
                if "data/bundle-data.js" in zf.namelist():
                    data_js = zf.read("data/bundle-data.js").decode("utf-8")
                    # Strip the JS assignment wrapper: window.PRAXIS_BUNDLE = {...};
                    json_str = data_js.strip()
                    if json_str.startswith("window.PRAXIS_BUNDLE"):
                        json_str = json_str.split("=", 1)[1].strip().rstrip(";")
                    bundle = json.loads(json_str)
                    # The ZIP bundle uses 'chain' and 'keys' keys
                    if "chain" in bundle and "keys" in bundle:
                        entries = bundle["chain"]
                        public_keys = bundle["keys"]
                        metadata = bundle.get("metadata", {})
                        session_id = metadata.get(
                            "session_id", bundle.get("session", {}).get("session_id", "unknown")
                        )
                        console.print(f"[bold]Verifying ZIP bundle[/bold]: {path.name}")
                        console.print(f"  Session: {session_id}")
                        console.print(f"  Chain entries: {len(entries)}")
                        console.print(
                            f"  Pre-export chain valid: {metadata.get('chain_valid', 'unknown')}"
                        )
                        if entries and public_keys:
                            from praxis.trust.verify import verify_chain

                            result = verify_chain(entries=entries, public_keys=public_keys)
                            if result.valid:
                                console.print(
                                    f"[green]Chain verified: {result.verified_entries}/{result.total_entries} entries valid[/green]"
                                )
                            else:
                                console.print(f"[red]Chain verification FAILED[/red]")
                                for b in result.breaks:
                                    console.print(
                                        f"  Break at position {b['position']}: {b['reason']}"
                                    )
                                sys.exit(1)
                        else:
                            console.print(f"[yellow]Bundle has no chain entries to verify[/yellow]")
                        return
                else:
                    raise click.ClickException(
                        "ZIP bundle does not contain 'data/bundle-data.js'. "
                        "This does not appear to be a valid Praxis verification bundle."
                    )
        except zipfile.BadZipFile as exc:
            raise click.ClickException(f"Invalid ZIP file: {exc}")
        except (json.JSONDecodeError, KeyError) as exc:
            raise click.ClickException(f"Failed to parse bundle data: {exc}")

    # Fall back to JSON file
    try:
        bundle = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError, UnicodeDecodeError) as exc:
        raise click.ClickException(f"Failed to read bundle: {exc}")

    # If the bundle has entries and public_keys, do chain verification
    entries = bundle.get("entries", [])
    public_keys = bundle.get("public_keys", {})

    if entries and public_keys:
        from praxis.trust.verify import verify_chain

        result = verify_chain(entries=entries, public_keys=public_keys)
        if result.valid:
            console.print(
                f"[green]Chain verified: {result.verified_entries}/{result.total_entries} entries valid[/green]"
            )
        else:
            console.print(f"[red]Chain verification FAILED[/red]")
            for b in result.breaks:
                console.print(f"  Break at position {b['position']}: {b['reason']}")
            sys.exit(1)
    else:
        console.print(f"[yellow]Bundle has no chain entries to verify[/yellow]")
        console.print(f"  Session: {bundle.get('session_id', 'unknown')}")
        console.print(f"  State: {bundle.get('state', 'unknown')}")


# ---------------------------------------------------------------------------
# praxis learn
# ---------------------------------------------------------------------------


@main.group()
def learn():
    """CO Layer 5: Learning pipeline — review proposals for evolving domain config."""
    pass


@learn.command("review")
@click.option("--domain", default=None, help="CO domain (defaults to workspace domain)")
@click.option(
    "--status",
    type=click.Choice(["pending", "approved", "rejected", "all"]),
    default="pending",
    help="Filter by proposal status",
)
def learn_review(domain: str | None, status: str):
    """Review pending evolution proposals from the learning pipeline."""
    workspace = _require_workspace()
    domain = domain or workspace.get("domain", "coc")

    from praxis.core.learning import LearningPipeline

    pipeline = LearningPipeline(domain=domain)
    status_filter = None if status == "all" else status
    proposals = pipeline.get_proposals(status=status_filter)

    if not proposals:
        console.print(f"[dim]No {status} proposals for domain '{domain}'[/dim]")
        return

    table = Table(title=f"Learning Proposals ({domain})")
    table.add_column("ID", style="cyan", max_width=12)
    table.add_column("Type", style="yellow")
    table.add_column("Target", style="white")
    table.add_column("Status", style="green")
    table.add_column("Rationale", style="dim", max_width=50)

    for p in proposals:
        pid = p.get("id", "")[:12]
        ptype = p.get("proposal_type", "")
        target = p.get("target", "")
        pstatus = p.get("status", "")
        rationale = p.get("rationale", "")[:50]

        status_color = {"pending": "yellow", "approved": "green", "rejected": "red"}.get(
            pstatus, "white"
        )
        table.add_row(pid, ptype, target, f"[{status_color}]{pstatus}[/{status_color}]", rationale)

    console.print(table)
    console.print(f"\n  Total: {len(proposals)} proposal(s)")
    if status == "pending":
        console.print("  [dim]Approve: praxis learn approve <id> --by <your-name>[/dim]")
        console.print("  [dim]Reject:  praxis learn reject <id> --by <your-name>[/dim]")


@learn.command("approve")
@click.argument("proposal_id")
@click.option("--by", "approved_by", required=True, help="Who is approving this proposal")
@click.option("--domain", default=None, help="CO domain (defaults to workspace domain)")
def learn_approve(proposal_id: str, approved_by: str, domain: str | None):
    """Approve a pending evolution proposal."""
    workspace = _require_workspace()
    domain = domain or workspace.get("domain", "coc")

    from praxis.core.learning import LearningPipeline

    pipeline = LearningPipeline(domain=domain)

    try:
        result = pipeline.formalize(proposal_id, approved_by)
        console.print("[green]Proposal approved[/green]")
        console.print(f"  Proposal: {proposal_id[:12]}...")
        console.print(f"  Approved by: {approved_by}")
        diff = result.get("diff", {})
        if diff:
            console.print(f"\n  [bold]Recommended change:[/bold]")
            console.print(f"    Action: {diff.get('action', '')}")
            console.print(f"    Target: {diff.get('target', '')}")
            console.print(f"    Current: {diff.get('current', '')}")
            console.print(f"    Proposed: {diff.get('proposed', '')}")
            console.print(f"\n  [dim]{diff.get('note', '')}[/dim]")
    except (KeyError, ValueError) as exc:
        raise click.ClickException(str(exc))


@learn.command("reject")
@click.argument("proposal_id")
@click.option("--by", "rejected_by", required=True, help="Who is rejecting this proposal")
@click.option("--reason", default="", help="Reason for rejection")
@click.option("--domain", default=None, help="CO domain (defaults to workspace domain)")
def learn_reject(proposal_id: str, rejected_by: str, reason: str, domain: str | None):
    """Reject a pending evolution proposal."""
    workspace = _require_workspace()
    domain = domain or workspace.get("domain", "coc")

    from praxis.core.learning import LearningPipeline

    pipeline = LearningPipeline(domain=domain)

    try:
        pipeline.reject(proposal_id, rejected_by, reason)
        console.print("[red]Proposal rejected[/red]")
        console.print(f"  Proposal: {proposal_id[:12]}...")
        console.print(f"  Rejected by: {rejected_by}")
        if reason:
            console.print(f"  Reason: {reason}")
    except (KeyError, ValueError) as exc:
        raise click.ClickException(str(exc))


@learn.command("analyze")
@click.option("--domain", default=None, help="CO domain (defaults to workspace domain)")
def learn_analyze(domain: str | None):
    """Run pattern analysis on accumulated observations."""
    workspace = _require_workspace()
    domain = domain or workspace.get("domain", "coc")

    from praxis.core.learning import LearningPipeline

    pipeline = LearningPipeline(domain=domain)
    patterns = pipeline.analyze()

    if not patterns:
        console.print(f"[dim]No patterns detected for domain '{domain}'[/dim]")
        return

    table = Table(title=f"Detected Patterns ({domain})")
    table.add_column("Type", style="yellow")
    table.add_column("Confidence", style="cyan")
    table.add_column("Description", style="white", max_width=60)
    table.add_column("Evidence", style="dim")

    for p in patterns:
        table.add_row(
            p.pattern_type,
            f"{p.confidence:.0%}",
            p.description[:60],
            f"{len(p.evidence)} obs",
        )

    console.print(table)
    console.print(f"\n  Total: {len(patterns)} pattern(s)")


# ---------------------------------------------------------------------------
# praxis serve
# ---------------------------------------------------------------------------


@main.command()
@click.option("--host", default="0.0.0.0", help="Host to bind to")
@click.option("--port", default=8000, type=int, help="Port to listen on")
def serve(host: str, port: int):
    """Start the Praxis API server."""
    import os

    # Set dev mode for local serving if not set
    if "PRAXIS_DEV_MODE" not in os.environ:
        os.environ["PRAXIS_DEV_MODE"] = "true"
    if "PRAXIS_API_PORT" not in os.environ:
        os.environ["PRAXIS_API_PORT"] = str(port)
    if "PRAXIS_API_HOST" not in os.environ:
        os.environ["PRAXIS_API_HOST"] = host

    from praxis.config import reset_config

    reset_config()

    # Initialize the database early so tables exist before the first request.
    # create_app() also calls get_db(), but doing it here makes the startup
    # sequence explicit and ensures any DB errors surface before Nexus init.
    from praxis.persistence import get_db

    get_db()

    from praxis.api.app import create_app

    app = create_app()
    console.print(f"[green]Starting Praxis server on {host}:{port}[/green]")
    app.start()


# ---------------------------------------------------------------------------
# praxis domain
# ---------------------------------------------------------------------------


@main.group()
def domain():
    """Manage CO domains."""
    pass


@domain.command("list")
def domain_list():
    """List available CO domains."""
    from praxis.domains.loader import DomainLoader

    loader = DomainLoader()
    domains = loader.list_domains()

    table = Table(title="Available CO Domains")
    table.add_column("Domain", style="cyan")
    table.add_column("Description", style="white")

    for d in domains:
        try:
            config = loader.load_domain(d)
            table.add_row(d, config.description[:60])
        except Exception:
            table.add_row(d, "(failed to load)")

    console.print(table)


@domain.command("validate")
@click.argument("domain_name")
def domain_validate(domain_name: str):
    """Validate a domain configuration."""
    from praxis.domains.loader import DomainLoader

    loader = DomainLoader()
    errors = loader.validate_domain(domain_name)

    if errors:
        console.print(f"[red]Domain '{domain_name}' has {len(errors)} error(s):[/red]")
        for err in errors:
            console.print(f"  - {err}")
        sys.exit(1)
    else:
        console.print(f"[green]Domain '{domain_name}' is valid[/green]")


def _now_iso() -> str:
    """UTC ISO 8601 timestamp."""
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


@domain.command("export")
@click.argument("domain_name")
@click.option("--output", "-o", default=None, help="Output ZIP path")
def domain_export(domain_name: str, output: str | None):
    """Export a domain configuration as a portable ZIP archive."""
    import hashlib
    import zipfile

    from praxis.domains.loader import DomainLoader

    loader = DomainLoader()
    errors = loader.validate_domain(domain_name)
    if errors:
        raise click.ClickException(f"Domain '{domain_name}' failed validation: {errors[0]}")

    domain_dir = loader._domains_dir / domain_name
    domain_yml_path = domain_dir / "domain.yml"

    output_path = Path(output) if output else Path.cwd() / f"{domain_name}-domain.zip"

    manifest_entries: list[dict] = []

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # domain.yml
        domain_content = domain_yml_path.read_bytes()
        zf.writestr(f"{domain_name}/domain.yml", domain_content)
        manifest_entries.append(
            {
                "path": f"{domain_name}/domain.yml",
                "sha256": hashlib.sha256(domain_content).hexdigest(),
            }
        )

        # Learning patterns from database (best-effort)
        learning_data = []
        try:
            from praxis.persistence.db_ops import db_list

            patterns = db_list("LearningPattern", filter={"domain": domain_name}, limit=10000)
            learning_data = patterns
        except Exception:
            pass

        if learning_data:
            patterns_json = json.dumps(learning_data, indent=2, default=str).encode("utf-8")
            zf.writestr(f"{domain_name}/learning_patterns.json", patterns_json)
            manifest_entries.append(
                {
                    "path": f"{domain_name}/learning_patterns.json",
                    "sha256": hashlib.sha256(patterns_json).hexdigest(),
                }
            )

        # Knowledge index
        config = loader.load_domain(domain_name)
        knowledge_index = {
            "domain": domain_name,
            "knowledge": config.knowledge if config.knowledge else {},
            "phases": [p["name"] for p in config.phases],
            "constraint_templates": list(config.constraint_templates.keys()),
        }
        ki_json = json.dumps(knowledge_index, indent=2).encode("utf-8")
        zf.writestr(f"{domain_name}/knowledge_index.json", ki_json)
        manifest_entries.append(
            {
                "path": f"{domain_name}/knowledge_index.json",
                "sha256": hashlib.sha256(ki_json).hexdigest(),
            }
        )

        # EXPORT_MANIFEST.json
        manifest = {
            "domain": domain_name,
            "version": config.version,
            "exported_at": _now_iso(),
            "files": manifest_entries,
        }
        zf.writestr("EXPORT_MANIFEST.json", json.dumps(manifest, indent=2))

    console.print(f"[green]Domain '{domain_name}' exported to {output_path}[/green]")
    console.print(f"  Files: {len(manifest_entries)}")
    console.print(f"  Version: {config.version}")


@domain.command("import")
@click.argument("path_zip")
def domain_import(path_zip: str):
    """Import a domain configuration from a portable ZIP archive."""
    import hashlib
    import zipfile

    zip_path = Path(path_zip)
    if not zip_path.exists():
        raise click.ClickException(f"File not found: {path_zip}")

    if not zipfile.is_zipfile(zip_path):
        raise click.ClickException(f"Not a valid ZIP file: {path_zip}")

    from praxis.domains.loader import DomainLoader

    loader = DomainLoader()

    with zipfile.ZipFile(zip_path, "r") as zf:
        if "EXPORT_MANIFEST.json" not in zf.namelist():
            raise click.ClickException("Invalid domain archive: missing EXPORT_MANIFEST.json")

        manifest = json.loads(zf.read("EXPORT_MANIFEST.json"))
        domain_name = manifest.get("domain", "")
        if not domain_name:
            raise click.ClickException("Manifest missing 'domain' field")

        # Validate checksums
        for entry in manifest.get("files", []):
            file_path = entry["path"]
            expected_hash = entry["sha256"]

            if file_path not in zf.namelist():
                raise click.ClickException(f"Missing file in archive: {file_path}")

            content = zf.read(file_path)
            actual_hash = hashlib.sha256(content).hexdigest()
            if actual_hash != expected_hash:
                raise click.ClickException(
                    f"Checksum mismatch for {file_path}: "
                    f"expected {expected_hash[:16]}..., got {actual_hash[:16]}..."
                )

        domain_yml_path = f"{domain_name}/domain.yml"
        if domain_yml_path not in zf.namelist():
            raise click.ClickException(f"Archive missing {domain_yml_path}")

        # Copy domain.yml to the domains directory
        target_dir = loader._domains_dir / domain_name
        target_dir.mkdir(parents=True, exist_ok=True)

        domain_yml_content = zf.read(domain_yml_path)
        (target_dir / "domain.yml").write_bytes(domain_yml_content)

        # Create constraints dir if needed
        constraints_dir = target_dir / "constraints"
        if not constraints_dir.exists():
            constraints_dir.mkdir(parents=True, exist_ok=True)
            import yaml as _yaml

            config_raw = _yaml.safe_load(domain_yml_content)
            templates = config_raw.get("constraint_templates", {})
            first_template = next(iter(templates.keys()), "moderate")
            default_constraint = {"default_template": first_template}
            (constraints_dir / "default.yml").write_text(
                _yaml.dump(default_constraint, default_flow_style=False)
            )

    loader.reload(domain_name)

    console.print(f"[green]Domain '{domain_name}' imported[/green]")
    console.print(f"  Location: {loader._domains_dir / domain_name}")
    console.print(f"  Version: {manifest.get('version', 'unknown')}")


@domain.command("diff")
@click.argument("domain1")
@click.argument("domain2")
def domain_diff(domain1: str, domain2: str):
    """Compare two domain configurations side by side."""
    from praxis.domains.loader import DomainLoader

    loader = DomainLoader()

    try:
        config1 = loader.load_domain(domain1)
    except FileNotFoundError:
        raise click.ClickException(f"Domain '{domain1}' not found")

    try:
        config2 = loader.load_domain(domain2)
    except FileNotFoundError:
        raise click.ClickException(f"Domain '{domain2}' not found")

    table = Table(title=f"Domain Comparison: {domain1} vs {domain2}")
    table.add_column("Property", style="cyan")
    table.add_column(domain1, style="white")
    table.add_column(domain2, style="white")

    table.add_row("Name", config1.name, config2.name)
    table.add_row("Display Name", config1.display_name, config2.display_name)
    table.add_row("Version", config1.version, config2.version)

    t1_names = sorted(config1.constraint_templates.keys())
    t2_names = sorted(config2.constraint_templates.keys())
    table.add_row("Templates", ", ".join(t1_names), ", ".join(t2_names))

    p1_names = [p["name"] for p in config1.phases]
    p2_names = [p["name"] for p in config2.phases]
    table.add_row("Phases", ", ".join(p1_names), ", ".join(p2_names))

    c1_types = config1.capture.get("decision_types", [])
    c2_types = config2.capture.get("decision_types", [])
    table.add_row("Decision Types", ", ".join(c1_types), ", ".join(c2_types))

    k1_count = len(config1.knowledge.get("classification", [])) if config1.knowledge else 0
    k2_count = len(config2.knowledge.get("classification", [])) if config2.knowledge else 0
    table.add_row("Knowledge Entries", str(k1_count), str(k2_count))

    console.print(table)

    common_templates = set(t1_names) & set(t2_names)
    only_in_1 = set(t1_names) - set(t2_names)
    only_in_2 = set(t2_names) - set(t1_names)

    if only_in_1:
        console.print(f"\n  Templates only in {domain1}: {', '.join(sorted(only_in_1))}")
    if only_in_2:
        console.print(f"\n  Templates only in {domain2}: {', '.join(sorted(only_in_2))}")

    if common_templates:
        console.print(f"\n[bold]Shared template comparison:[/bold]")
        for tpl_name in sorted(common_templates):
            tpl1 = config1.constraint_templates[tpl_name]
            tpl2 = config2.constraint_templates[tpl_name]
            diffs = []
            for dim in ["financial", "operational", "temporal", "data_access", "communication"]:
                if dim in tpl1 and dim in tpl2 and tpl1[dim] != tpl2[dim]:
                    diffs.append(dim)
            if diffs:
                console.print(f"  {tpl_name}: differs in {', '.join(diffs)}")
            else:
                console.print(f"  {tpl_name}: [dim]identical[/dim]")


@domain.command("calibration")
@click.argument("domain_name")
def domain_calibration(domain_name: str):
    """Analyze constraint calibration for a domain.

    Reviews constraint enforcement data across all sessions for the domain
    and produces a calibration report with actionable recommendations.
    """
    from praxis.core.calibration import CalibrationAnalyzer

    analyzer = CalibrationAnalyzer()
    report = analyzer.analyze(domain_name)

    if report["total_evaluations"] == 0:
        console.print(f"[dim]No constraint evaluation data for domain '{domain_name}'.[/dim]")
        console.print("  Run some sessions to accumulate calibration data.")
        return

    # Summary panel
    console.print(
        Panel(
            f"[bold]Constraint Calibration Report[/bold]\n"
            f"  Domain: [cyan]{domain_name}[/cyan]\n"
            f"  Sessions analyzed: {report['total_sessions']}\n"
            f"  Total evaluations: {report['total_evaluations']}\n"
            f"  False positive rate: {report['false_positive_rate']:.0%}",
            title="Calibration",
        )
    )

    # Per-dimension table
    dims = report.get("dimensions", {})
    if dims:
        table = Table(title="Dimension Analysis")
        table.add_column("Dimension", style="cyan")
        table.add_column("Evaluations", justify="right")
        table.add_column("Avg Util", justify="right")
        table.add_column("Max Util", justify="right")
        table.add_column("Pressure", justify="right")
        table.add_column("Auto", justify="right", style="green")
        table.add_column("Flag", justify="right", style="yellow")
        table.add_column("Held", justify="right", style="red")
        table.add_column("Block", justify="right", style="bold red")

        pressure = report.get("boundary_pressure", {})
        for dim, data in dims.items():
            p = pressure.get(dim, 0.0)
            p_color = "green" if p < 0.15 else "yellow" if p < 0.30 else "red"
            table.add_row(
                dim,
                str(data.get("total_evaluations", 0)),
                f"{data.get('avg_utilization', 0):.0%}",
                f"{data.get('max_utilization', 0):.0%}",
                f"[{p_color}]{p:.0%}[/{p_color}]",
                str(data.get("auto_approved", 0)),
                str(data.get("flagged", 0)),
                str(data.get("held", 0)),
                str(data.get("blocked", 0)),
            )
        console.print(table)

    # Recommendations
    recs = report.get("recommendations", [])
    if recs:
        console.print("\n[bold]Recommendations[/bold]")
        for i, rec in enumerate(recs, 1):
            console.print(f"  {i}. {rec}")


# ---------------------------------------------------------------------------
# praxis mcp
# ---------------------------------------------------------------------------

MCP_SERVERS_FILE = "mcp-servers.json"


@main.group()
def mcp():
    """MCP proxy commands — trust-mediated tool call interception."""
    pass


@mcp.command("serve")
@click.option(
    "--config",
    "config_path",
    default=None,
    help="Path to MCP server config JSON (default: .praxis/mcp-servers.json)",
)
@click.option(
    "--server",
    "extra_servers",
    multiple=True,
    help="Downstream server as 'name:command:arg1,arg2' (repeatable)",
)
def mcp_serve(config_path: str | None, extra_servers: tuple):
    """Start the MCP proxy in stdio mode.

    The proxy sits between an AI assistant and downstream MCP tool servers,
    intercepting every tool call and enforcing constraints before forwarding.
    This is the core "trust as medium" architecture.

    Downstream servers are configured via .praxis/mcp-servers.json or CLI args.
    """
    import asyncio
    import os

    workspace = _require_workspace()
    session_data = _require_session()

    if session_data["state"] != "active":
        raise click.ClickException(
            f"Session is '{session_data['state']}', not 'active'. "
            f"The MCP proxy requires an active session."
        )

    # Set dev mode for local usage
    if "PRAXIS_DEV_MODE" not in os.environ:
        os.environ["PRAXIS_DEV_MODE"] = "true"

    from praxis.config import reset_config

    reset_config()

    # Load downstream server configuration
    servers = _load_mcp_servers(config_path, extra_servers)

    if not servers:
        raise click.ClickException(
            "No downstream MCP servers configured. "
            "Create .praxis/mcp-servers.json or use --server flags.\n\n"
            "Example .praxis/mcp-servers.json:\n"
            '  {"servers": [{"name": "fs", "command": "mcp-server-filesystem", "args": ["/"]}]}\n\n'
            "Example --server flag:\n"
            "  praxis mcp serve --server 'fs:mcp-server-filesystem:/'"
        )

    # Build the proxy
    sid = session_data["session_id"]

    # Set up constraint enforcer
    from praxis.core.constraint import ConstraintEnforcer, HeldActionManager

    enforcer = ConstraintEnforcer(
        session_data.get("constraint_envelope", {}),
        session_id=sid,
    )
    held_manager = HeldActionManager(use_db=False)

    # Set up audit chain and deliberation engine (optional, with signing)
    audit_chain = None
    deliberation_engine = None
    key_manager = None
    key_id = workspace.get("key_id", "workspace")

    key_dir = _praxis_dir() / KEYS_DIR
    try:
        from praxis.trust.keys import KeyManager

        km = KeyManager(key_dir)
        if km.has_key(key_id):
            key_manager = km

            from praxis.trust.audit import AuditChain

            audit_chain = AuditChain(
                session_id=sid,
                key_id=key_id,
                key_manager=km,
            )

            deliberation_engine = _get_deliberation_engine(
                sid, workspace, domain=session_data.get("domain")
            )
    except Exception as exc:
        logger.debug("Could not set up trust services for MCP proxy: %s", exc)

    from praxis.mcp.proxy import PraxisProxy

    proxy = PraxisProxy(
        session_id=sid,
        downstream_servers=servers,
        constraint_enforcer=enforcer,
        held_action_manager=held_manager,
        audit_chain=audit_chain,
        deliberation_engine=deliberation_engine,
        key_manager=key_manager,
        key_id=key_id,
    )

    # Print status to stderr (stdout is reserved for MCP stdio transport)
    console_err = Console(stderr=True)
    console_err.print("[green]Praxis MCP proxy starting[/green]")
    console_err.print(f"  Session: {sid[:12]}...")
    console_err.print(f"  Domain: {session_data.get('domain', 'unknown')}")
    console_err.print(f"  Downstream servers: {len(servers)}")
    for srv in servers:
        console_err.print(f"    - {srv['name']}: {srv['command']} {' '.join(srv.get('args', []))}")
    console_err.print("  Constraint enforcement: active")
    audit_status = "enabled" if audit_chain else "disabled"
    delib_status = "enabled" if deliberation_engine else "disabled"
    console_err.print(f"  Audit capture: {audit_status}")
    console_err.print(f"  Deliberation capture: {delib_status}")
    console_err.print("[dim]Listening on stdio...[/dim]")

    # Run the proxy
    asyncio.run(proxy.start())


def _load_mcp_servers(
    config_path: str | None,
    extra_servers: tuple,
) -> list[dict]:
    """Load downstream MCP server configurations.

    Reads from:
    1. Explicit config file path (--config flag)
    2. .praxis/mcp-servers.json (default location)
    3. --server CLI flags

    Args:
        config_path: Explicit path to config JSON, or None.
        extra_servers: Tuple of "name:command:arg1,arg2" strings.

    Returns:
        List of server config dicts with name, command, args keys.
    """
    servers: list[dict] = []

    # Load from JSON config file
    if config_path is not None:
        config_file = Path(config_path)
    else:
        config_file = _praxis_dir() / MCP_SERVERS_FILE

    if config_file.exists():
        try:
            config = json.loads(config_file.read_text())
            file_servers = config.get("servers", [])
            for srv in file_servers:
                if "name" in srv and "command" in srv:
                    servers.append(
                        {
                            "name": srv["name"],
                            "command": srv["command"],
                            "args": srv.get("args", []),
                            "env": srv.get("env"),
                        }
                    )
            logger.info("Loaded %d server(s) from %s", len(file_servers), config_file)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to load MCP server config from %s: %s", config_file, exc)

    # Parse --server flags: "name:command:arg1,arg2"
    for spec in extra_servers:
        parts = spec.split(":", 2)
        if len(parts) < 2:
            logger.warning("Invalid --server spec (need name:command[:args]): %s", spec)
            continue
        name = parts[0].strip()
        command = parts[1].strip()
        args = parts[2].split(",") if len(parts) > 2 else []
        servers.append(
            {
                "name": name,
                "command": command,
                "args": [a.strip() for a in args],
            }
        )

    return servers
