# Praxis Trust Chain Patterns

## Overview

The trust chain is a cryptographic proof of human authorization. Every session starts with a genesis record, which may have delegations, and all actions produce signed audit anchors. The chain is verifiable by any third party using only the public key.

## Key Files

| File                  | Purpose                                                                        |
| --------------------- | ------------------------------------------------------------------------------ |
| `trust/crypto.py`     | `canonical_hash`, `sign_hash`, `verify_signature` -- shared primitives         |
| `trust/keys.py`       | `KeyManager` -- Ed25519 keypair lifecycle, symlink protection, key zeroization |
| `trust/genesis.py`    | `create_genesis` -> frozen `GenesisRecord`                                     |
| `trust/delegation.py` | `create_delegation` -> frozen `DelegationRecord`, `revoke_delegation`          |
| `trust/audit.py`      | `AuditChain` -- append-only signed anchor chain, DB persistence                |
| `trust/verify.py`     | `verify_chain` -- full chain verification from exported data                   |
| `trust/gradient.py`   | `evaluate_action` -> `GradientVerdict` (consolidated single source)            |

## Cryptographic Primitives

All trust operations use three primitives from `trust/crypto.py`:

1. **Canonical hash**: `canonical_hash(payload: dict) -> str` -- JCS (RFC 8785) + SHA-256 -> hex
2. **Sign**: `sign_hash(hash_hex, key_id, key_manager) -> str` -- Ed25519 -> base64url
3. **Verify**: `verify_signature(hash_hex, signature_b64, key_id, key_manager) -> bool`

## Audit Chain DB Persistence

When an `AuditChain` has a `session_id`, anchors are persisted to the `TrustChainEntry` table via `db_ops`. The `anchors` property loads from DB when available. This means the chain survives process restarts.

## Key Security Enhancements

### Key Zeroization

After signing, private key bytes are overwritten in memory to reduce exposure window. The `sign_hash()` function zeroizes key material after use.

### Symlink Protection

`KeyManager` verifies that key file paths are not symlinks before reading or writing. This prevents symlink attacks that could redirect key operations to arbitrary files.

## Security Patterns

### Path Traversal Protection

`_validate_key_id()` in `keys.py` rejects empty strings, forward/back slashes, `..`, null bytes, and anything not matching `^[a-zA-Z0-9_\-\.]+$`.

### NaN/Inf Guard

`_gradient_for_utilization()` and `_utilization_to_level()` check `math.isfinite()` and return BLOCKED for non-finite values.

### Frozen Records

GenesisRecord, DelegationRecord, AuditAnchor, ConstraintVerdict are all `@dataclass(frozen=True)`.

### Private Key File Permissions

KeyManager sets private key files to mode 0o600 (owner read/write only).

## Exporting Verification Bundles

The bundle is a self-contained ZIP with browser-based Ed25519 verification via SubtleCrypto. `serve.py` binds to `127.0.0.1` (localhost only).
