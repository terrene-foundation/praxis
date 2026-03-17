// verifier.js -- Client-side trust chain verification
// Copyright 2026 Terrene Foundation (Apache 2.0)
// Uses SubtleCrypto (Web Crypto API) -- no external dependencies

/**
 * JCS-subset canonical JSON serializer (RFC 8785).
 *
 * Produces deterministic JSON by recursively sorting object keys and
 * serializing with no whitespace. Sufficient for the subset of JSON
 * used in Praxis payloads (no special float handling needed since
 * payloads only contain strings, integers, booleans, arrays, and objects).
 */
function jcsCanonicalise(value) {
  if (value === null || value === undefined) {
    return "null";
  }
  if (typeof value === "boolean") {
    return value ? "true" : "false";
  }
  if (typeof value === "number") {
    if (!Number.isFinite(value)) {
      throw new Error("JCS: non-finite numbers are not supported");
    }
    return JSON.stringify(value);
  }
  if (typeof value === "string") {
    return JSON.stringify(value);
  }
  if (Array.isArray(value)) {
    const items = value.map((item) => jcsCanonicalise(item));
    return "[" + items.join(",") + "]";
  }
  if (typeof value === "object") {
    const sortedKeys = Object.keys(value).sort();
    const pairs = sortedKeys.map((key) => {
      return JSON.stringify(key) + ":" + jcsCanonicalise(value[key]);
    });
    return "{" + pairs.join(",") + "}";
  }
  throw new Error("JCS: unsupported type " + typeof value);
}

/**
 * Convert a hex string to a Uint8Array.
 */
function hexToBytes(hex) {
  const bytes = new Uint8Array(hex.length / 2);
  for (let i = 0; i < hex.length; i += 2) {
    bytes[i / 2] = parseInt(hex.substring(i, i + 2), 16);
  }
  return bytes;
}

/**
 * Convert a Uint8Array to a hex string.
 */
function bytesToHex(bytes) {
  return Array.from(bytes)
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

/**
 * Decode base64url string to Uint8Array.
 */
function base64urlToBytes(b64url) {
  // Add padding
  let b64 = b64url.replace(/-/g, "+").replace(/_/g, "/");
  while (b64.length % 4 !== 0) {
    b64 += "=";
  }
  const binary = atob(b64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes;
}

/**
 * Parse a PEM public key to raw bytes (SubjectPublicKeyInfo DER).
 */
function pemToSpki(pem) {
  const lines = pem.trim().split("\n");
  const b64Lines = lines.filter(
    (line) => !line.startsWith("-----BEGIN") && !line.startsWith("-----END"),
  );
  const b64 = b64Lines.join("");
  const binary = atob(b64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes;
}

class ChainVerifier {
  constructor() {
    this.results = {
      valid: true,
      totalEntries: 0,
      verifiedEntries: 0,
      breaks: [],
      ed25519Supported: true,
    };
  }

  /**
   * Verify the entire trust chain.
   *
   * For each entry:
   *   1. Recompute content_hash from payload using SHA-256 of JCS-canonical JSON
   *   2. Verify content_hash matches stored value
   *   3. Verify Ed25519 signature using SubtleCrypto
   *   4. Verify parent_hash chain linkage
   *   5. Verify genesis has no parent
   *
   * @param {Array} chain - Ordered list of chain entry objects
   * @param {Object} publicKeys - Map of key_id to PEM public key string
   * @returns {Object} Verification results
   */
  async verify(chain, publicKeys) {
    this.results.totalEntries = chain.length;

    if (chain.length === 0) {
      return this.results;
    }

    // Check Ed25519 support
    const ed25519Supported = await this._checkEd25519Support();
    this.results.ed25519Supported = ed25519Supported;

    let previousHash = null;

    for (let i = 0; i < chain.length; i++) {
      const entry = chain[i];
      let entryValid = true;

      // Step 1: Recompute content_hash from payload
      const canonical = jcsCanonicalise(entry.payload);
      const encoder = new TextEncoder();
      const data = encoder.encode(canonical);
      const hashBuffer = await crypto.subtle.digest("SHA-256", data);
      const expectedHash = bytesToHex(new Uint8Array(hashBuffer));

      const storedHash = entry.content_hash || "";
      if (expectedHash !== storedHash) {
        this.results.breaks.push({
          position: i,
          reason: "bad_hash",
          details:
            "Content hash mismatch: recomputed hash does not match stored hash",
        });
        entryValid = false;
      }

      // Step 2: Verify Ed25519 signature
      const signerKeyId = entry.signer_key_id || "";
      const signatureB64 = entry.signature || "";

      if (!(signerKeyId in publicKeys)) {
        this.results.breaks.push({
          position: i,
          reason: "unknown_key",
          details: 'Public key "' + signerKeyId + '" not found in bundle keys',
        });
        entryValid = false;
      } else if (entryValid && ed25519Supported) {
        try {
          const sigValid = await this.verifySignature(
            publicKeys[signerKeyId],
            storedHash,
            signatureB64,
          );
          if (!sigValid) {
            this.results.breaks.push({
              position: i,
              reason: "bad_signature",
              details: "Ed25519 signature verification failed",
            });
            entryValid = false;
          }
        } catch (err) {
          this.results.breaks.push({
            position: i,
            reason: "bad_signature",
            details: "Signature verification error: " + err.message,
          });
          entryValid = false;
        }
      }

      // Step 3: Verify parent_hash chain linkage
      if (i === 0) {
        if (entry.parent_hash !== null && entry.parent_hash !== undefined) {
          this.results.breaks.push({
            position: i,
            reason: "broken_parent_link",
            details: "First entry (genesis) must have no parent_hash",
          });
          entryValid = false;
        }
      } else {
        if (entry.parent_hash !== previousHash) {
          this.results.breaks.push({
            position: i,
            reason: "broken_parent_link",
            details: "Parent hash does not match previous entry content hash",
          });
          entryValid = false;
        }
      }

      if (entryValid) {
        this.results.verifiedEntries++;
      }

      previousHash = storedHash;
    }

    this.results.valid = this.results.breaks.length === 0;
    return this.results;
  }

  /**
   * Check if the browser supports Ed25519 in SubtleCrypto.
   */
  async _checkEd25519Support() {
    try {
      // Attempt to generate a tiny Ed25519 key to test support
      await crypto.subtle.generateKey("Ed25519", false, ["sign", "verify"]);
      return true;
    } catch (e) {
      return false;
    }
  }

  /**
   * Import a PEM public key as a CryptoKey for Ed25519 verification.
   *
   * @param {string} pemString - PEM-encoded public key
   * @returns {CryptoKey} Imported key
   */
  async importPublicKey(pemString) {
    const spkiBytes = pemToSpki(pemString);
    return await crypto.subtle.importKey(
      "spki",
      spkiBytes.buffer,
      { name: "Ed25519" },
      false,
      ["verify"],
    );
  }

  /**
   * Verify an Ed25519 signature against a hex-encoded hash.
   *
   * @param {string} pemPublicKey - PEM-encoded public key
   * @param {string} hashHex - Hex-encoded hash that was signed
   * @param {string} signatureB64 - Base64url-encoded signature
   * @returns {boolean} True if signature is valid
   */
  async verifySignature(pemPublicKey, hashHex, signatureB64) {
    const cryptoKey = await this.importPublicKey(pemPublicKey);
    const hashBytes = hexToBytes(hashHex);
    const sigBytes = base64urlToBytes(signatureB64);

    return await crypto.subtle.verify(
      { name: "Ed25519" },
      cryptoKey,
      sigBytes,
      hashBytes,
    );
  }

  /**
   * Compute SHA-256 hash of a JCS-canonical JSON payload.
   *
   * @param {Object} payload - The payload to hash
   * @returns {string} Hex-encoded SHA-256 hash
   */
  async computeHash(payload) {
    const canonical = jcsCanonicalise(payload);
    const encoder = new TextEncoder();
    const data = encoder.encode(canonical);
    const hashBuffer = await crypto.subtle.digest("SHA-256", data);
    return bytesToHex(new Uint8Array(hashBuffer));
  }
}

// Export for use by viewer.js
window.ChainVerifier = ChainVerifier;
