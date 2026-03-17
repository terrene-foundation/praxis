# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""Unit tests for praxis.trust.keys — Ed25519 key management.

Tests verify:
- Key generation creates files on disk
- Sign and verify roundtrip works
- Invalid signature returns False
- Missing key raises appropriate error
- Key file permissions are 600 for private keys
- Public key export produces valid PEM
- Key listing returns all available key IDs
"""

import os
import platform
import stat

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def key_dir(tmp_path):
    """Provide a temporary directory for key storage."""
    kd = tmp_path / "test_keys"
    kd.mkdir()
    return kd


@pytest.fixture
def key_manager(key_dir):
    """Provide a KeyManager instance with a temporary key directory."""
    from praxis.trust.keys import KeyManager

    return KeyManager(key_dir=key_dir)


# ---------------------------------------------------------------------------
# KeyManager Initialization Tests
# ---------------------------------------------------------------------------


class TestKeyManagerInit:
    """Verify KeyManager initializes correctly."""

    def test_creates_key_dir_if_not_exists(self, tmp_path):
        from praxis.trust.keys import KeyManager

        key_dir = tmp_path / "new" / "nested" / "keys"
        assert not key_dir.exists()
        km = KeyManager(key_dir=key_dir)
        assert key_dir.exists()
        assert km.key_dir == key_dir

    def test_uses_existing_dir(self, key_dir):
        from praxis.trust.keys import KeyManager

        km = KeyManager(key_dir=key_dir)
        assert km.key_dir == key_dir


# ---------------------------------------------------------------------------
# Key Generation Tests
# ---------------------------------------------------------------------------


class TestKeyGeneration:
    """Verify key generation creates proper files."""

    def test_generate_key_returns_key_id(self, key_manager):
        key_id = key_manager.generate_key("test-key")
        assert key_id == "test-key"

    def test_generate_key_creates_private_key_file(self, key_manager, key_dir):
        key_manager.generate_key("test-key")
        private_key_path = key_dir / "test-key.key"
        assert private_key_path.exists()

    def test_generate_key_creates_public_key_file(self, key_manager, key_dir):
        key_manager.generate_key("test-key")
        public_key_path = key_dir / "test-key.pub"
        assert public_key_path.exists()

    @pytest.mark.skipif(
        platform.system() == "Windows",
        reason="File permissions work differently on Windows",
    )
    def test_private_key_permissions_are_600(self, key_manager, key_dir):
        """Private key files must be owner-read/write only (600)."""
        key_manager.generate_key("secure-key")
        private_key_path = key_dir / "secure-key.key"
        mode = stat.S_IMODE(os.stat(private_key_path).st_mode)
        assert mode == 0o600, f"Expected 0o600, got {oct(mode)}"

    def test_private_key_is_valid_pem(self, key_manager, key_dir):
        key_manager.generate_key("pem-key")
        content = (key_dir / "pem-key.key").read_bytes()
        assert b"PRIVATE KEY" in content

    def test_public_key_is_valid_pem(self, key_manager, key_dir):
        key_manager.generate_key("pem-key")
        content = (key_dir / "pem-key.pub").read_bytes()
        assert b"PUBLIC KEY" in content

    def test_generate_duplicate_key_raises(self, key_manager):
        """Generating a key with an existing key_id should raise an error."""
        key_manager.generate_key("dup-key")
        with pytest.raises(ValueError, match="already exists"):
            key_manager.generate_key("dup-key")


# ---------------------------------------------------------------------------
# has_key Tests
# ---------------------------------------------------------------------------


class TestHasKey:
    """Verify key existence checks."""

    def test_has_key_returns_true_for_existing(self, key_manager):
        key_manager.generate_key("exists-key")
        assert key_manager.has_key("exists-key") is True

    def test_has_key_returns_false_for_missing(self, key_manager):
        assert key_manager.has_key("no-such-key") is False


# ---------------------------------------------------------------------------
# Key Loading Tests
# ---------------------------------------------------------------------------


class TestKeyLoading:
    """Verify keys can be loaded from disk."""

    def test_get_private_key_returns_ed25519_private_key(self, key_manager):
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

        key_manager.generate_key("load-test")
        pk = key_manager.get_private_key("load-test")
        assert isinstance(pk, Ed25519PrivateKey)

    def test_get_public_key_returns_ed25519_public_key(self, key_manager):
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

        key_manager.generate_key("load-test")
        pub = key_manager.get_public_key("load-test")
        assert isinstance(pub, Ed25519PublicKey)

    def test_get_private_key_missing_raises(self, key_manager):
        """Attempting to load a non-existent key should raise a clear error."""
        with pytest.raises(FileNotFoundError, match="no-such-key"):
            key_manager.get_private_key("no-such-key")

    def test_get_public_key_missing_raises(self, key_manager):
        with pytest.raises(FileNotFoundError, match="no-such-key"):
            key_manager.get_public_key("no-such-key")


# ---------------------------------------------------------------------------
# Sign and Verify Tests
# ---------------------------------------------------------------------------


class TestSignAndVerify:
    """Verify signing and verification roundtrip."""

    def test_sign_returns_bytes(self, key_manager):
        key_manager.generate_key("sign-key")
        signature = key_manager.sign("sign-key", b"hello world")
        assert isinstance(signature, bytes)
        assert len(signature) == 64  # Ed25519 signatures are 64 bytes

    def test_verify_valid_signature(self, key_manager):
        key_manager.generate_key("verify-key")
        data = b"test data for verification"
        sig = key_manager.sign("verify-key", data)
        assert key_manager.verify("verify-key", data, sig) is True

    def test_verify_invalid_signature(self, key_manager):
        key_manager.generate_key("tamper-key")
        data = b"original data"
        sig = key_manager.sign("tamper-key", data)
        # Tamper with the signature
        tampered_sig = bytes([b ^ 0xFF for b in sig])
        assert key_manager.verify("tamper-key", data, tampered_sig) is False

    def test_verify_wrong_data(self, key_manager):
        key_manager.generate_key("wrong-data-key")
        data = b"original data"
        sig = key_manager.sign("wrong-data-key", data)
        assert key_manager.verify("wrong-data-key", b"different data", sig) is False

    def test_sign_missing_key_raises(self, key_manager):
        with pytest.raises(FileNotFoundError, match="missing-key"):
            key_manager.sign("missing-key", b"data")

    def test_verify_missing_key_raises(self, key_manager):
        with pytest.raises(FileNotFoundError, match="missing-key"):
            key_manager.verify("missing-key", b"data", b"sig")


# ---------------------------------------------------------------------------
# Export Tests
# ---------------------------------------------------------------------------


class TestExportPublicPem:
    """Verify public key export."""

    def test_export_returns_pem_bytes(self, key_manager):
        key_manager.generate_key("export-key")
        pem = key_manager.export_public_pem("export-key")
        assert isinstance(pem, bytes)
        assert pem.startswith(b"-----BEGIN PUBLIC KEY-----")
        assert pem.strip().endswith(b"-----END PUBLIC KEY-----")

    def test_export_missing_key_raises(self, key_manager):
        with pytest.raises(FileNotFoundError, match="no-key"):
            key_manager.export_public_pem("no-key")


# ---------------------------------------------------------------------------
# List Keys Tests
# ---------------------------------------------------------------------------


class TestListKeys:
    """Verify key listing."""

    def test_list_empty_dir(self, key_manager):
        keys = key_manager.list_keys()
        assert keys == []

    def test_list_returns_key_ids(self, key_manager):
        key_manager.generate_key("alpha")
        key_manager.generate_key("beta")
        key_manager.generate_key("gamma")
        keys = key_manager.list_keys()
        assert set(keys) == {"alpha", "beta", "gamma"}

    def test_list_ignores_non_key_files(self, key_manager, key_dir):
        key_manager.generate_key("real-key")
        # Create a random file that is not a key
        (key_dir / "random.txt").write_text("not a key")
        keys = key_manager.list_keys()
        assert keys == ["real-key"]


# ---------------------------------------------------------------------------
# Trust Package Init Tests
# ---------------------------------------------------------------------------


class TestSymlinkProtection:
    """Verify key operations reject symlinks."""

    @pytest.mark.skipif(
        platform.system() == "Windows",
        reason="Symlinks require special permissions on Windows",
    )
    def test_generate_key_rejects_symlinked_private_path(self, key_manager, key_dir, tmp_path):
        """generate_key must refuse to write to a path that is a symlink."""
        target = tmp_path / "evil_target.key"
        target.write_text("evil")
        symlink_path = key_dir / "sneaky.key"
        symlink_path.symlink_to(target)

        with pytest.raises(ValueError, match="symlink"):
            key_manager.generate_key("sneaky")

    @pytest.mark.skipif(
        platform.system() == "Windows",
        reason="Symlinks require special permissions on Windows",
    )
    def test_get_private_key_rejects_symlink(self, key_manager, key_dir, tmp_path):
        """get_private_key must refuse to read from a symlink."""
        # Generate a real key first, then replace with symlink
        key_manager.generate_key("real-key")
        real_path = key_dir / "real-key.key"
        content = real_path.read_bytes()

        target = tmp_path / "target.key"
        target.write_bytes(content)

        fake_key_path = key_dir / "fake-key.key"
        fake_key_path.symlink_to(target)

        with pytest.raises(ValueError, match="symlink"):
            key_manager.get_private_key("fake-key")

    @pytest.mark.skipif(
        platform.system() == "Windows",
        reason="Symlinks require special permissions on Windows",
    )
    def test_get_public_key_rejects_symlink(self, key_manager, key_dir, tmp_path):
        """get_public_key must refuse to read from a symlink."""
        key_manager.generate_key("real-pub-key")
        real_path = key_dir / "real-pub-key.pub"
        content = real_path.read_bytes()

        target = tmp_path / "target.pub"
        target.write_bytes(content)

        fake_key_path = key_dir / "fake-pub-key.pub"
        fake_key_path.symlink_to(target)

        with pytest.raises(ValueError, match="symlink"):
            key_manager.get_public_key("fake-pub-key")


class TestKeyDirectoryPermissions:
    """Verify key directory permissions are restrictive."""

    @pytest.mark.skipif(
        platform.system() == "Windows",
        reason="File permissions work differently on Windows",
    )
    def test_key_dir_permissions_are_700(self, tmp_path):
        from praxis.trust.keys import KeyManager

        key_dir = tmp_path / "secure_keys"
        KeyManager(key_dir=key_dir)
        mode = stat.S_IMODE(os.stat(key_dir).st_mode)
        assert mode == 0o700, f"Expected 0o700, got {oct(mode)}"


class TestTrustPackage:
    """Verify the trust package exports."""

    def test_import_key_manager(self):
        from praxis.trust import KeyManager

        assert KeyManager is not None
