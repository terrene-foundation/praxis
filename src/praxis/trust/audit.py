# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""Audit anchor chain — tamper-evident records of session actions.

Every action in a CO session is recorded as an audit anchor. Anchors form
a hash chain: each anchor's parent_hash references the previous anchor's
content_hash, creating a tamper-evident log. The chain can be verified
independently by any auditor using only the public key.

Anchors are persisted to the DataFlow ``TrustChainEntry`` table with
``entry_type="anchor"``.  The in-memory ``AuditAnchor`` dataclass is used
for verification logic, while storage and retrieval go through the
``db_ops`` helpers.
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from praxis.trust.crypto import canonical_hash, sign_hash

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AuditAnchor:
    """Tamper-evident record of an action in a CO session.

    Each anchor is signed and chained to the previous anchor via parent_hash.
    The sequence field gives the 0-indexed position in the chain.
    """

    anchor_id: str
    session_id: str
    action: str
    resource: str | None
    actor: str
    result: str
    reasoning_hash: str | None
    payload: dict
    content_hash: str
    signature: str
    signer_key_id: str
    parent_hash: str | None
    sequence: int
    created_at: str


# ---------------------------------------------------------------------------
# Internal helpers for DB ↔ AuditAnchor conversion
# ---------------------------------------------------------------------------


def _ensure_dict(value) -> dict | None:
    """Deserialize a value that may be a JSON string or already a dict."""
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, dict):
                return parsed
        except (json.JSONDecodeError, TypeError):
            pass
    return None


def _db_row_to_anchor(row: dict) -> AuditAnchor:
    """Convert a ``TrustChainEntry`` DB row to an ``AuditAnchor``.

    The anchor-specific fields (action, resource, actor, result, etc.)
    live inside the ``payload`` dict.  We extract them here so the
    ``AuditAnchor`` dataclass stays flat.
    """
    payload = _ensure_dict(row.get("payload")) or {}
    return AuditAnchor(
        anchor_id=row["id"],
        session_id=row["session_id"],
        action=payload.get("action", ""),
        resource=payload.get("resource"),
        actor=payload.get("actor", ""),
        result=payload.get("result", ""),
        reasoning_hash=payload.get("reasoning_hash"),
        payload=payload,
        content_hash=row.get("content_hash", ""),
        signature=row.get("signature", ""),
        signer_key_id=row.get("signer_key_id", ""),
        parent_hash=row.get("parent_hash"),
        sequence=payload.get("sequence", 0),
        created_at=payload.get("created_at", ""),
    )


class AuditChain:
    """Manages a chain of audit anchors for a session.

    The chain is append-only: new anchors are always added at the end,
    and each anchor's parent_hash links to the previous anchor's content_hash.
    The chain can be verified for integrity at any time.

    Anchors are persisted to the ``TrustChainEntry`` table (``entry_type="anchor"``).
    The sequence counter is derived from the existing anchor count in the database
    at construction time, so a chain can be resumed after a process restart.
    """

    # Shared filter dict used for all DB queries scoped to this chain's anchors
    _ENTRY_TYPE = "anchor"

    def __init__(self, session_id: str, key_id: str, key_manager):
        """Initialize an audit chain for a session.

        Args:
            session_id: Session this chain belongs to.
            key_id: Signing key identifier.
            key_manager: KeyManager instance for signing.
        """
        self.session_id = session_id
        self.key_id = key_id
        self.key_manager = key_manager
        # Derive the next sequence number from existing DB entries
        self._sequence = self._count_from_db()

    # ------------------------------------------------------------------
    # DB interaction helpers
    # ------------------------------------------------------------------

    def _db_filter(self) -> dict:
        """Return the standard filter for this chain's anchor rows."""
        return {"session_id": self.session_id, "entry_type": self._ENTRY_TYPE}

    def _count_from_db(self) -> int:
        """Return the number of anchor entries for this session in the DB."""
        from praxis.persistence.db_ops import db_count

        return db_count("TrustChainEntry", filter=self._db_filter())

    def _load_anchors(self) -> list[AuditAnchor]:
        """Load all anchor entries from the DB, ordered by sequence ascending.

        Returns:
            List of AuditAnchor instances in chain order.
        """
        from praxis.persistence.db_ops import db_list

        rows = db_list(
            "TrustChainEntry",
            filter=self._db_filter(),
            limit=100_000,
            order_asc=True,
        )
        return [_db_row_to_anchor(r) for r in rows]

    def _head_from_db(self) -> str | None:
        """Return the content_hash of the most recent anchor, or None."""
        from praxis.persistence.db_ops import db_list

        rows = db_list(
            "TrustChainEntry",
            filter=self._db_filter(),
            limit=1,
            order_asc=False,  # newest first
        )
        if not rows:
            return None
        return rows[0].get("content_hash")

    def _persist_anchor(self, anchor: AuditAnchor) -> None:
        """Write an AuditAnchor to the TrustChainEntry table."""
        from praxis.persistence.db_ops import db_create

        db_create(
            "TrustChainEntry",
            {
                "id": anchor.anchor_id,
                "session_id": anchor.session_id,
                "entry_type": self._ENTRY_TYPE,
                "payload": anchor.payload,
                "signature": anchor.signature,
                "signer_key_id": anchor.signer_key_id,
                "parent_hash": anchor.parent_hash,
                "content_hash": anchor.content_hash,
                "verified": False,
            },
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def anchors(self) -> list[AuditAnchor]:
        """All anchors in chain order, loaded from the database.

        This is the public accessor that replaces the old ``_anchors`` list.
        """
        return self._load_anchors()

    def append(
        self,
        action: str,
        actor: str,
        result: str,
        resource: str | None = None,
        reasoning_hash: str | None = None,
        extra_payload: dict | None = None,
    ) -> AuditAnchor:
        """Add an anchor to the chain.

        Args:
            action: What was done (e.g. "read_file", "write_file", "deploy").
            actor: Who did it ("human", "ai", "system").
            result: Gradient result ("auto_approved", "flagged", "held", "blocked",
                    "approved", "denied").
            resource: What it was done to (file path, service name, etc.).
            reasoning_hash: Hash of associated deliberation record, if any.
            extra_payload: Additional fields to include in the payload.

        Returns:
            The newly created AuditAnchor.
        """
        anchor_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        parent_hash = self.head_hash

        # Build the anchor payload
        payload = {
            "type": "audit_anchor",
            "version": "1.0",
            "anchor_id": anchor_id,
            "session_id": self.session_id,
            "action": action,
            "resource": resource,
            "actor": actor,
            "result": result,
            "reasoning_hash": reasoning_hash,
            "parent_hash": parent_hash,
            "sequence": self._sequence,
            "signer_key_id": self.key_id,
            "created_at": created_at,
        }

        # Merge extra payload fields if provided
        if extra_payload:
            payload.update(extra_payload)

        # Compute content hash and signature
        content_hash = canonical_hash(payload)
        signature = sign_hash(content_hash, self.key_id, self.key_manager)

        anchor = AuditAnchor(
            anchor_id=anchor_id,
            session_id=self.session_id,
            action=action,
            resource=resource,
            actor=actor,
            result=result,
            reasoning_hash=reasoning_hash,
            payload=payload,
            content_hash=content_hash,
            signature=signature,
            signer_key_id=self.key_id,
            parent_hash=parent_hash,
            sequence=self._sequence,
            created_at=created_at,
        )

        # Persist to DataFlow
        self._persist_anchor(anchor)
        self._sequence += 1

        logger.debug(
            "Appended anchor %s (seq=%d) to chain for session %s",
            anchor_id,
            anchor.sequence,
            self.session_id,
        )
        return anchor

    @property
    def head_hash(self) -> str | None:
        """Hash of the most recent anchor, or None if chain is empty."""
        return self._head_from_db()

    @property
    def length(self) -> int:
        """Number of anchors in the chain."""
        return self._count_from_db()

    def verify_integrity(self) -> tuple[bool, list[dict]]:
        """Verify the chain is intact.

        Loads all anchors from the database and checks for each anchor:
            1. Content hash matches JCS-canonical payload
            2. Signature verifies against the content hash
            3. Parent hash matches previous anchor's content hash

        Returns:
            A tuple of (valid, breaks) where valid is True if the chain
            is intact, and breaks is a list of dicts describing any
            integrity violations found.
        """
        anchors = self._load_anchors()

        if not anchors:
            return True, []

        breaks = []
        previous_hash = None

        for i, anchor in enumerate(anchors):
            # Step 1: Verify content hash matches payload
            expected_hash = canonical_hash(anchor.payload)
            if anchor.content_hash != expected_hash:
                breaks.append(
                    {
                        "position": i,
                        "anchor_id": anchor.anchor_id,
                        "reason": "bad_hash",
                        "details": (
                            f"Content hash mismatch at position {i}: "
                            f"expected {expected_hash}, got {anchor.content_hash}"
                        ),
                    }
                )
                previous_hash = anchor.content_hash
                continue

            # Step 2: Verify signature
            from praxis.trust.crypto import verify_signature

            try:
                sig_valid = verify_signature(
                    anchor.content_hash, anchor.signature, anchor.signer_key_id, self.key_manager
                )
                if not sig_valid:
                    breaks.append(
                        {
                            "position": i,
                            "anchor_id": anchor.anchor_id,
                            "reason": "bad_signature",
                            "details": f"Signature verification failed at position {i}",
                        }
                    )
            except Exception as e:
                breaks.append(
                    {
                        "position": i,
                        "anchor_id": anchor.anchor_id,
                        "reason": "bad_signature",
                        "details": f"Signature verification error at position {i}: {e}",
                    }
                )

            # Step 3: Verify parent hash chain link
            if i == 0:
                if anchor.parent_hash is not None:
                    breaks.append(
                        {
                            "position": i,
                            "anchor_id": anchor.anchor_id,
                            "reason": "broken_parent_link",
                            "details": "First anchor must have no parent_hash",
                        }
                    )
            else:
                if anchor.parent_hash != previous_hash:
                    breaks.append(
                        {
                            "position": i,
                            "anchor_id": anchor.anchor_id,
                            "reason": "broken_parent_link",
                            "details": (
                                f"Parent hash mismatch at position {i}: "
                                f"expected {previous_hash}, got {anchor.parent_hash}"
                            ),
                        }
                    )

            previous_hash = anchor.content_hash

        valid = len(breaks) == 0
        return valid, breaks
