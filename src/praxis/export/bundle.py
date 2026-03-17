# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""Verification bundle builder — self-contained ZIP for independent auditing.

A verification bundle is a ZIP file containing everything needed for
independent third-party verification of a CO session's trust chain.
No server, no installation, no network. Open index.html in any modern
browser and the chain is verified client-side using SubtleCrypto.

Bundle structure:
    bundle.zip/
        index.html              # Entry point — opens in browser
        data/
            bundle-data.js      # All JSON data as JS variable (avoids file:// CORS)
        verify/
            verifier.js         # Ed25519 verification via SubtleCrypto
            viewer.js           # Interactive timeline and chain viewer
        style/
            styles.css          # Embedded styles (dark/light mode, print-friendly)
        algorithm.txt           # Human-readable verification algorithm description
        serve.py                # Fallback: python3 serve.py (local HTTP server)
"""

from __future__ import annotations

import json
import logging
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

# Path to the templates directory, adjacent to this file
_TEMPLATES_DIR = Path(__file__).parent / "templates"


@dataclass
class BundleMetadata:
    """Metadata describing a verification bundle.

    Attributes:
        session_id: Session this bundle was exported from.
        workspace_name: Name of the workspace.
        domain: CO domain (coc, coe, cog, etc.).
        duration_seconds: Session duration in seconds.
        total_anchors: Number of trust chain entries.
        total_decisions: Number of deliberation decision records.
        chain_valid: Whether the chain passed pre-export integrity check.
        created_at: ISO 8601 timestamp of bundle creation.
    """

    session_id: str
    workspace_name: str
    domain: str
    duration_seconds: int
    total_anchors: int
    total_decisions: int
    chain_valid: bool
    created_at: str


# Fallback Python server script for when file:// CORS blocks loading.
_SERVE_PY = '''\
#!/usr/bin/env python3
"""Fallback HTTP server for the Praxis verification bundle.

Run this script from the extracted bundle directory:
    python3 serve.py

It starts a local HTTP server and opens the bundle in your default browser.
All verification runs locally -- no data is sent anywhere.
"""
import http.server
import os
import sys
import webbrowser

PORT = 8765

os.chdir(os.path.dirname(os.path.abspath(__file__)))

print(f"Starting local server on http://localhost:{PORT}")
print("Press Ctrl+C to stop.\\n")

webbrowser.open(f"http://localhost:{PORT}/index.html")

handler = http.server.SimpleHTTPRequestHandler
with http.server.HTTPServer(("127.0.0.1", PORT), handler) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\\nServer stopped.")
        sys.exit(0)
'''


class BundleBuilder:
    """Builds self-contained verification bundles as ZIP files.

    A verification bundle contains all session data, trust chain entries,
    deliberation records, constraint events, public keys, and the HTML/JS/CSS
    needed to verify the chain client-side in any modern browser.

    Args:
        session_data: Session metadata dict (must include session_id).
        trust_chain: Ordered list of trust chain entry dicts.
        deliberation_records: List of deliberation record dicts.
        constraint_events: List of constraint event dicts.
        public_keys: Dict of key_id -> PEM public key string.

    Raises:
        ValueError: If session_data is missing session_id, trust_chain is
            empty, or public_keys is empty.
    """

    def __init__(
        self,
        session_data: dict,
        trust_chain: list[dict],
        deliberation_records: list[dict],
        constraint_events: list[dict],
        public_keys: dict[str, str],
    ) -> None:
        # Validate inputs explicitly -- raise clear errors, never proceed silently
        if "session_id" not in session_data:
            raise ValueError(
                "session_data must contain 'session_id'. "
                "Provide a valid session data dict with at least a session_id field."
            )

        if not trust_chain:
            raise ValueError(
                "trust_chain must not be empty. "
                "A verification bundle requires at least one trust chain entry "
                "(the genesis record)."
            )

        if not public_keys:
            raise ValueError(
                "public_keys must not be empty. "
                "At least one public key is required to verify signatures in the bundle."
            )

        self.session_data = session_data
        self.trust_chain = trust_chain
        self.deliberation_records = deliberation_records
        self.constraint_events = constraint_events
        self.public_keys = public_keys

    def build(self, output_path: Path) -> Path:
        """Build the verification bundle ZIP.

        Creates a ZIP file at output_path containing all bundle files.
        Parent directories are created if they do not exist.

        Args:
            output_path: Path where the ZIP file will be written.

        Returns:
            Path to the created ZIP file.
        """
        output_path = Path(output_path)

        # Create parent directories if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Create bundle metadata
        metadata = self._create_metadata()

        # Assemble bundle data as a single JS file (avoids file:// CORS issues)
        bundle_data = {
            "metadata": asdict(metadata),
            "session": self.session_data,
            "chain": self.trust_chain,
            "deliberation": self.deliberation_records,
            "constraints": self.constraint_events,
            "keys": self.public_keys,
        }

        data_js_content = "window.PRAXIS_BUNDLE = " + json.dumps(bundle_data, indent=2) + ";"

        # Write the ZIP
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # HTML entry point
            zf.write(_TEMPLATES_DIR / "index.html", "index.html")

            # Data (embedded as JS to avoid fetch/CORS issues on file://)
            zf.writestr("data/bundle-data.js", data_js_content)

            # Verification scripts
            zf.write(_TEMPLATES_DIR / "verifier.js", "verify/verifier.js")
            zf.write(_TEMPLATES_DIR / "viewer.js", "verify/viewer.js")

            # Styles
            zf.write(_TEMPLATES_DIR / "styles.css", "style/styles.css")

            # Algorithm description
            zf.write(_TEMPLATES_DIR / "algorithm.txt", "algorithm.txt")

            # Fallback server script
            zf.writestr("serve.py", _SERVE_PY)

        logger.info(
            "Built verification bundle: %s (session=%s, chain_entries=%d, "
            "deliberation_records=%d, constraint_events=%d)",
            output_path,
            metadata.session_id,
            metadata.total_anchors,
            len(self.deliberation_records),
            len(self.constraint_events),
        )

        return output_path

    def _create_metadata(self) -> BundleMetadata:
        """Create bundle metadata from session data.

        Computes duration from created_at and ended_at timestamps,
        counts anchors and decisions, and runs pre-export chain verification.

        Returns:
            BundleMetadata with all fields populated.
        """
        session = self.session_data

        # Compute duration in seconds
        duration_seconds = 0
        created_at_str = session.get("created_at", "")
        ended_at_str = session.get("ended_at")

        if created_at_str and ended_at_str:
            try:
                # Parse ISO 8601 timestamps with microseconds and Z suffix
                fmt = "%Y-%m-%dT%H:%M:%S.%fZ"
                created_dt = datetime.strptime(created_at_str, fmt).replace(tzinfo=timezone.utc)
                ended_dt = datetime.strptime(ended_at_str, fmt).replace(tzinfo=timezone.utc)
                duration_seconds = max(0, int((ended_dt - created_dt).total_seconds()))
            except (ValueError, TypeError) as exc:
                logger.warning(
                    "Could not compute session duration from timestamps "
                    "(created_at=%r, ended_at=%r): %s",
                    created_at_str,
                    ended_at_str,
                    exc,
                )
                duration_seconds = 0

        # Count decision-type deliberation records only
        total_decisions = sum(
            1 for record in self.deliberation_records if record.get("record_type") == "decision"
        )

        # Run pre-export chain verification
        chain_valid = self._verify_chain_before_export()

        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        return BundleMetadata(
            session_id=session["session_id"],
            workspace_name=session.get("workspace_id", "unknown"),
            domain=session.get("domain", "unknown"),
            duration_seconds=duration_seconds,
            total_anchors=len(self.trust_chain),
            total_decisions=total_decisions,
            chain_valid=chain_valid,
            created_at=now_str,
        )

    def _verify_chain_before_export(self) -> bool:
        """Verify chain entry integrity before building the bundle.

        Verifies each entry's content hash and signature individually.
        A bundle may contain entries from multiple sub-chains (e.g., a genesis
        record followed by an independent audit chain), so parent-hash linkage
        across sub-chains is not enforced here -- that is the auditor's
        responsibility when reviewing the bundle.

        Returns:
            True if all entries have valid hashes and signatures, False if
            any entry has a hash mismatch or invalid signature.
        """
        import base64
        import hashlib

        import jcs
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

        # Normalize public keys to strings (may be bytes from export_public_pem)
        normalized_keys: dict[str, str] = {}
        for key_id, pem in self.public_keys.items():
            if isinstance(pem, bytes):
                normalized_keys[key_id] = pem.decode("utf-8")
            else:
                normalized_keys[key_id] = pem

        all_valid = True
        for i, entry in enumerate(self.trust_chain):
            payload = entry.get("payload", {})
            stored_hash = entry.get("content_hash", "")
            signature_b64 = entry.get("signature", "")
            signer_key_id = entry.get("signer_key_id", "")

            # Verify content hash
            canonical = jcs.canonicalize(payload)
            expected_hash = hashlib.sha256(canonical).hexdigest()
            if expected_hash != stored_hash:
                logger.warning(
                    "Pre-export check: content hash mismatch at entry %d " "(expected %s, got %s)",
                    i,
                    expected_hash,
                    stored_hash,
                )
                all_valid = False
                continue

            # Verify signature if key is available
            if signer_key_id not in normalized_keys:
                logger.warning(
                    "Pre-export check: unknown signer key '%s' at entry %d",
                    signer_key_id,
                    i,
                )
                all_valid = False
                continue

            try:
                pem_str = normalized_keys[signer_key_id]
                pem_bytes = pem_str.encode("utf-8")
                pub_key = serialization.load_pem_public_key(pem_bytes)
                if not isinstance(pub_key, Ed25519PublicKey):
                    logger.warning(
                        "Pre-export check: key '%s' is not Ed25519 at entry %d",
                        signer_key_id,
                        i,
                    )
                    all_valid = False
                    continue

                hash_bytes = bytes.fromhex(stored_hash)
                sig_bytes = base64.urlsafe_b64decode(signature_b64)
                pub_key.verify(sig_bytes, hash_bytes)
            except Exception as exc:
                logger.warning(
                    "Pre-export check: signature verification failed at entry %d: %s",
                    i,
                    exc,
                )
                all_valid = False

        return all_valid
