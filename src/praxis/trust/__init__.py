# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""
Praxis trust layer — Ed25519 key management and cryptographic operations
for EATP trust chains.

Usage:
    from praxis.trust import KeyManager

    km = KeyManager(key_dir=Path("~/.praxis/keys"))
    km.generate_key("genesis")
    sig = km.sign("genesis", b"data")
    valid = km.verify("genesis", b"data", sig)
"""

from praxis.trust.keys import KeyManager

__all__ = ["KeyManager"]
