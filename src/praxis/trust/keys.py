# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""
Ed25519 key management for Praxis trust chains.

Provides generation, storage, signing, and verification of Ed25519 keypairs
used in EATP trust chain operations (genesis, delegation, attestation).

Key storage format:
- Private keys: {key_dir}/{key_id}.key (PEM, file mode 600)
- Public keys:  {key_dir}/{key_id}.pub (PEM)
"""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

logger = logging.getLogger(__name__)

_KEY_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_\-\.]+$")


def _validate_key_id(key_id: str) -> None:
    """Validate key_id to prevent path traversal attacks."""
    if not key_id:
        raise ValueError("key_id must not be empty")
    if "/" in key_id or "\\" in key_id or ".." in key_id or "\x00" in key_id:
        raise ValueError(
            f"key_id contains forbidden characters: {key_id!r}. "
            "Key IDs must not contain '/', '\\\\', '..', or null bytes."
        )
    if not _KEY_ID_PATTERN.match(key_id):
        raise ValueError(
            f"key_id contains invalid characters: {key_id!r}. "
            "Key IDs must contain only alphanumeric characters, hyphens, underscores, and dots."
        )


def _check_not_symlink(path: Path) -> None:
    """Verify a path is not a symlink to prevent symlink attacks on key files.

    Args:
        path: The file path to check.

    Raises:
        ValueError: If the path is a symbolic link.
    """
    if path.is_symlink():
        raise ValueError(f"Security: key path is a symlink: {path}")


class KeyManager:
    """Manages Ed25519 keypairs for EATP trust chain operations.

    Keys are stored as PEM files on disk. Private key files are
    restricted to owner-read/write (mode 600) for security.

    Args:
        key_dir: Directory for key storage. Created if it does not exist.
    """

    def __init__(self, key_dir: Path) -> None:
        self.key_dir = Path(key_dir)
        self.key_dir.mkdir(parents=True, exist_ok=True)
        # Restrict key directory to owner-only access
        try:
            self.key_dir.chmod(0o700)
        except OSError:
            # chmod may fail on some platforms (e.g., Windows)
            pass

    def generate_key(self, key_id: str) -> str:
        """Generate a new Ed25519 keypair and save to disk.

        Args:
            key_id: Unique identifier for the key. Used as the filename stem.

        Returns:
            The key_id that was generated.

        Raises:
            ValueError: If a key with this key_id already exists.
        """
        _validate_key_id(key_id)
        private_path = self.key_dir / f"{key_id}.key"
        public_path = self.key_dir / f"{key_id}.pub"

        # Guard against symlink attacks before writing
        _check_not_symlink(private_path)
        _check_not_symlink(public_path)

        if private_path.exists():
            raise ValueError(
                f"Key '{key_id}' already exists at {private_path}. "
                f"Use a different key_id or delete the existing key first."
            )

        # Generate the keypair
        private_key = Ed25519PrivateKey.generate()
        public_key = private_key.public_key()

        # Serialize private key to PEM (no encryption — filesystem permissions protect it)
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

        # Serialize public key to PEM
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        # Write private key and restrict permissions
        private_path.write_bytes(private_pem)
        os.chmod(private_path, 0o600)

        # Write public key
        public_path.write_bytes(public_pem)

        # Zeroize in-memory key material references
        del private_key, private_pem

        logger.info("Generated Ed25519 keypair: %s", key_id)
        return key_id

    def has_key(self, key_id: str) -> bool:
        """Check if a key with the given key_id exists on disk.

        Args:
            key_id: The key identifier to check.

        Returns:
            True if the private key file exists, False otherwise.
        """
        _validate_key_id(key_id)
        return (self.key_dir / f"{key_id}.key").exists()

    def get_private_key(self, key_id: str) -> Ed25519PrivateKey:
        """Load a private key from disk.

        Args:
            key_id: The key identifier to load.

        Returns:
            The Ed25519 private key object.

        Raises:
            FileNotFoundError: If no key with this key_id exists.
        """
        _validate_key_id(key_id)
        private_path = self.key_dir / f"{key_id}.key"

        # Guard against symlink attacks before reading
        _check_not_symlink(private_path)

        if not private_path.exists():
            raise FileNotFoundError(
                f"Private key '{key_id}' not found at {private_path}. "
                f"Generate it first with generate_key('{key_id}')."
            )

        private_pem = private_path.read_bytes()
        private_key = serialization.load_pem_private_key(private_pem, password=None)

        if not isinstance(private_key, Ed25519PrivateKey):
            raise TypeError(
                f"Key '{key_id}' is not an Ed25519 key. "
                f"Got {type(private_key).__name__} instead."
            )

        return private_key

    def get_public_key(self, key_id: str) -> Ed25519PublicKey:
        """Load or derive the public key for a given key_id.

        If the .pub file exists, loads it directly. Otherwise, derives
        the public key from the private key.

        Args:
            key_id: The key identifier to load.

        Returns:
            The Ed25519 public key object.

        Raises:
            FileNotFoundError: If neither private nor public key file exists.
        """
        _validate_key_id(key_id)
        public_path = self.key_dir / f"{key_id}.pub"

        # Guard against symlink attacks before reading
        _check_not_symlink(public_path)

        if public_path.exists():
            public_pem = public_path.read_bytes()
            public_key = serialization.load_pem_public_key(public_pem)
            if not isinstance(public_key, Ed25519PublicKey):
                raise TypeError(
                    f"Key '{key_id}' public key is not Ed25519. "
                    f"Got {type(public_key).__name__} instead."
                )
            return public_key

        # Fall back to deriving from private key
        private_key = self.get_private_key(key_id)
        return private_key.public_key()

    def sign(self, key_id: str, data: bytes) -> bytes:
        """Sign data with the named Ed25519 key.

        Args:
            key_id: The key identifier to sign with.
            data: The data bytes to sign.

        Returns:
            The 64-byte Ed25519 signature.

        Raises:
            FileNotFoundError: If no key with this key_id exists.
        """
        _validate_key_id(key_id)
        private_key = self.get_private_key(key_id)
        try:
            return private_key.sign(data)
        finally:
            del private_key

    def verify(self, key_id: str, data: bytes, signature: bytes) -> bool:
        """Verify an Ed25519 signature.

        Args:
            key_id: The key identifier whose public key to verify against.
            data: The original data that was signed.
            signature: The signature to verify.

        Returns:
            True if the signature is valid, False otherwise.

        Raises:
            FileNotFoundError: If no key with this key_id exists.
        """
        _validate_key_id(key_id)
        public_key = self.get_public_key(key_id)
        try:
            public_key.verify(signature, data)
            return True
        except InvalidSignature:
            return False

    def export_public_pem(self, key_id: str) -> bytes:
        """Export the public key as PEM-encoded bytes.

        Args:
            key_id: The key identifier to export.

        Returns:
            PEM-encoded public key bytes.

        Raises:
            FileNotFoundError: If no key with this key_id exists.
        """
        _validate_key_id(key_id)
        public_key = self.get_public_key(key_id)
        return public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

    def list_keys(self) -> list[str]:
        """List all available key IDs in the key directory.

        Returns:
            Sorted list of key IDs (derived from .key file stems).
        """
        key_ids = []
        for path in sorted(self.key_dir.iterdir()):
            if path.suffix == ".key" and path.is_file():
                key_ids.append(path.stem)
        return key_ids
