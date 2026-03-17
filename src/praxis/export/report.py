# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""Audit report generator — human-readable reports from session data.

Generates both HTML and JSON reports summarising a CO session's trust chain,
deliberation records, and constraint evaluations. HTML reports are fully
self-contained (embedded CSS, no CDN).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def _escape_html(text: str) -> str:
    """Escape HTML special characters to prevent XSS.

    Args:
        text: Raw string to escape.

    Returns:
        HTML-safe string.
    """
    if text is None:
        return ""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )


def _compute_duration_seconds(session_data: dict) -> int:
    """Compute session duration in seconds from timestamps.

    Args:
        session_data: Session metadata dict.

    Returns:
        Duration in seconds, or 0 if timestamps are missing/invalid.
    """
    created_at = session_data.get("created_at", "")
    ended_at = session_data.get("ended_at")

    if not created_at or not ended_at:
        return 0

    try:
        fmt = "%Y-%m-%dT%H:%M:%S.%fZ"
        start = datetime.strptime(created_at, fmt).replace(tzinfo=timezone.utc)
        end = datetime.strptime(ended_at, fmt).replace(tzinfo=timezone.utc)
        return max(0, int((end - start).total_seconds()))
    except (ValueError, TypeError):
        return 0


class AuditReportGenerator:
    """Generate audit reports from session data.

    Produces both standalone HTML reports (with embedded styles) and
    structured JSON reports for programmatic consumption.
    """

    def generate_html(
        self,
        session_data: dict,
        chain: list[dict],
        deliberation: list[dict],
        constraints: list[dict],
    ) -> str:
        """Generate a standalone HTML report.

        The report includes session summary, trust chain overview,
        deliberation timeline, and constraint compliance. All styles
        are embedded -- no CDN or external dependencies.

        Args:
            session_data: Session metadata dict.
            chain: List of trust chain entry dicts.
            deliberation: List of deliberation record dicts.
            constraints: List of constraint event dicts.

        Returns:
            Complete HTML document string.
        """
        session_id = _escape_html(session_data.get("session_id", "unknown"))
        domain = _escape_html(session_data.get("domain", "unknown"))
        workspace = _escape_html(session_data.get("workspace_id", "unknown"))
        created_at = _escape_html(session_data.get("created_at", ""))
        ended_at = _escape_html(session_data.get("ended_at", ""))
        duration = _compute_duration_seconds(session_data)
        hours = duration // 3600
        minutes = (duration % 3600) // 60

        duration_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"

        # Build chain summary
        chain_count = len(chain)
        chain_types: dict[str, int] = {}
        for entry in chain:
            entry_type = entry.get("payload", {}).get("type", "unknown")
            chain_types[entry_type] = chain_types.get(entry_type, 0) + 1

        chain_type_rows = ""
        for ctype, count in sorted(chain_types.items()):
            chain_type_rows += f"<tr><td>{_escape_html(ctype)}</td><td>{count}</td></tr>"

        # Build deliberation rows
        deliberation_rows = ""
        for record in deliberation:
            rtype = _escape_html(record.get("record_type", "unknown"))
            actor = _escape_html(record.get("actor", ""))
            created = _escape_html(record.get("created_at", ""))
            content = record.get("content", {})

            # Extract display text based on type
            if record.get("record_type") == "decision":
                text = _escape_html(content.get("decision", ""))
            elif record.get("record_type") == "observation":
                text = _escape_html(content.get("observation", ""))
            elif record.get("record_type") == "escalation":
                text = _escape_html(content.get("issue", ""))
            else:
                text = _escape_html(str(content))

            confidence = record.get("confidence")
            conf_str = f"{confidence * 100:.0f}%" if confidence is not None else "-"

            deliberation_rows += (
                f"<tr>"
                f"<td>{rtype}</td>"
                f"<td>{actor}</td>"
                f"<td>{text}</td>"
                f"<td>{conf_str}</td>"
                f"<td>{created}</td>"
                f"</tr>"
            )

        if not deliberation:
            deliberation_rows = (
                '<tr><td colspan="5" style="text-align:center;color:#6c757d;">'
                "No deliberation records</td></tr>"
            )

        # Build constraint rows
        constraint_rows = ""
        for evt in constraints:
            action = _escape_html(evt.get("action", ""))
            resource = _escape_html(evt.get("resource", "-"))
            verdict = _escape_html(evt.get("verdict", ""))
            dimension = _escape_html(evt.get("dimension", ""))
            utilization = evt.get("utilization")
            util_str = f"{utilization * 100:.0f}%" if utilization is not None else "-"
            evaluated_at = _escape_html(evt.get("evaluated_at", ""))

            constraint_rows += (
                f"<tr>"
                f"<td>{action}</td>"
                f"<td>{resource}</td>"
                f"<td>{verdict}</td>"
                f"<td>{dimension}</td>"
                f"<td>{util_str}</td>"
                f"<td>{evaluated_at}</td>"
                f"</tr>"
            )

        if not constraints:
            constraint_rows = (
                '<tr><td colspan="6" style="text-align:center;color:#6c757d;">'
                "No constraint evaluations</td></tr>"
            )

        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        html = f"""\
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Praxis Audit Report - {session_id}</title>
    <style>
        :root {{
            --bg: #ffffff;
            --text: #212529;
            --muted: #6c757d;
            --border: #dee2e6;
            --bg-alt: #f8f9fa;
            --accent: #0d6efd;
            --green: #198754;
            --amber: #fd7e14;
            --red: #dc3545;
            --mono: 'SF Mono', 'Fira Code', 'Consolas', monospace;
            --sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }}
        @media (prefers-color-scheme: dark) {{
            :root {{
                --bg: #1a1a2e;
                --text: #e0e0e0;
                --muted: #808080;
                --border: #2d3748;
                --bg-alt: #16213e;
                --accent: #4da6ff;
                --green: #2ecc71;
                --amber: #f39c12;
                --red: #e74c3c;
            }}
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: var(--sans);
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
            padding: 2rem;
            max-width: 900px;
            margin: 0 auto;
        }}
        h1 {{ font-size: 1.5rem; margin-bottom: 0.25rem; }}
        h2 {{
            font-size: 1.2rem;
            margin: 2rem 0 0.75rem;
            padding-bottom: 0.4rem;
            border-bottom: 1px solid var(--border);
        }}
        .subtitle {{ color: var(--muted); font-size: 0.9rem; margin-bottom: 1.5rem; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 1rem;
            font-size: 0.9rem;
        }}
        th, td {{
            padding: 0.5rem 0.75rem;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }}
        th {{
            background: var(--bg-alt);
            font-weight: 600;
            font-size: 0.8rem;
            text-transform: uppercase;
        }}
        .mono {{ font-family: var(--mono); font-size: 0.85em; word-break: break-all; }}
        footer {{
            margin-top: 3rem;
            padding-top: 1rem;
            border-top: 1px solid var(--border);
            text-align: center;
            color: var(--muted);
            font-size: 0.8rem;
        }}
        footer a {{ color: var(--accent); text-decoration: none; }}
        @media print {{
            body {{ background: white; color: black; }}
        }}
    </style>
</head>
<body>
    <h1>Praxis Audit Report</h1>
    <p class="subtitle">Generated {_escape_html(now_str)}</p>

    <h2>Session Summary</h2>
    <table>
        <tr><td style="width:180px;font-weight:600;">Session ID</td><td class="mono">{session_id}</td></tr>
        <tr><td style="font-weight:600;">Domain</td><td>{domain}</td></tr>
        <tr><td style="font-weight:600;">Workspace</td><td>{workspace}</td></tr>
        <tr><td style="font-weight:600;">Duration</td><td>{duration_str}</td></tr>
        <tr><td style="font-weight:600;">Created</td><td>{created_at}</td></tr>
        <tr><td style="font-weight:600;">Ended</td><td>{ended_at if ended_at else '-'}</td></tr>
    </table>

    <h2>Trust Chain ({chain_count} entries)</h2>
    <table>
        <thead><tr><th>Entry Type</th><th>Count</th></tr></thead>
        <tbody>
            {chain_type_rows if chain_type_rows else '<tr><td colspan="2" style="text-align:center;color:#6c757d;">No chain entries</td></tr>'}
        </tbody>
    </table>

    <h2>Deliberation Records ({len(deliberation)} entries)</h2>
    <table>
        <thead><tr><th>Type</th><th>Actor</th><th>Content</th><th>Confidence</th><th>Time</th></tr></thead>
        <tbody>
            {deliberation_rows}
        </tbody>
    </table>

    <h2>Constraint Evaluations ({len(constraints)} entries)</h2>
    <table>
        <thead><tr><th>Action</th><th>Resource</th><th>Verdict</th><th>Dimension</th><th>Utilization</th><th>Time</th></tr></thead>
        <tbody>
            {constraint_rows}
        </tbody>
    </table>

    <footer>
        <p>Generated by <a href="https://github.com/terrene-foundation/praxis">Praxis</a> &mdash; Terrene Foundation</p>
    </footer>
</body>
</html>"""

        return html

    def generate_json(
        self,
        session_data: dict,
        chain: list[dict],
        deliberation: list[dict],
        constraints: list[dict],
    ) -> dict:
        """Generate a structured JSON report.

        Args:
            session_data: Session metadata dict.
            chain: List of trust chain entry dicts.
            deliberation: List of deliberation record dicts.
            constraints: List of constraint event dicts.

        Returns:
            Report dict with session, chain_summary, deliberation_summary,
            constraint_summary, and generated_at fields.
        """
        duration = _compute_duration_seconds(session_data)

        # Chain summary
        chain_types: dict[str, int] = {}
        for entry in chain:
            entry_type = entry.get("payload", {}).get("type", "unknown")
            chain_types[entry_type] = chain_types.get(entry_type, 0) + 1

        # Deliberation summary
        delib_by_type: dict[str, int] = {}
        for record in deliberation:
            rtype = record.get("record_type", "unknown")
            delib_by_type[rtype] = delib_by_type.get(rtype, 0) + 1

        # Constraint summary
        constraint_by_verdict: dict[str, int] = {}
        for evt in constraints:
            verdict = evt.get("verdict", "unknown")
            constraint_by_verdict[verdict] = constraint_by_verdict.get(verdict, 0) + 1

        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        return {
            "session": {
                "session_id": session_data.get("session_id", "unknown"),
                "domain": session_data.get("domain", "unknown"),
                "workspace_id": session_data.get("workspace_id", "unknown"),
                "created_at": session_data.get("created_at", ""),
                "ended_at": session_data.get("ended_at"),
                "duration_seconds": duration,
            },
            "chain_summary": {
                "total_entries": len(chain),
                "by_type": chain_types,
            },
            "deliberation_summary": {
                "total_records": len(deliberation),
                "by_type": delib_by_type,
            },
            "constraint_summary": {
                "total_evaluations": len(constraints),
                "by_verdict": constraint_by_verdict,
            },
            "generated_at": now_str,
        }
