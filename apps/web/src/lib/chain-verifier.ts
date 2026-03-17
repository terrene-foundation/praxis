// Copyright 2026 Terrene Foundation
// Licensed under the Apache License, Version 2.0

/**
 * Client-side chain verification using the Web Crypto API.
 *
 * Verifies EATP trust chains entirely in the browser. No data is sent
 * to any server. Uses Ed25519 (via SubtleCrypto) for signature verification
 * and SHA-256 for hash computation. JSON Canonicalization Scheme (JCS)
 * compatible canonical JSON is produced with sorted keys and no whitespace.
 *
 * M12-02: Client-Side Chain Verification
 */

import type { ChainEntry, VerificationBundle } from "@/types/api";

// ---------------------------------------------------------------------------
// Result types
// ---------------------------------------------------------------------------

export interface VerificationProgress {
  current: number;
  total: number;
  status: "verifying" | "complete" | "error";
}

export interface EntryVerificationResult {
  index: number;
  contentHashValid: boolean;
  signatureValid: boolean;
  chainLinkValid: boolean;
  error?: string;
}

export interface ChainVerificationResult {
  valid: boolean;
  totalEntries: number;
  verifiedEntries: number;
  breaks: number[];
  entries: EntryVerificationResult[];
  error?: string;
}

// ---------------------------------------------------------------------------
// JCS-compatible canonical JSON
// ---------------------------------------------------------------------------

function canonicalJson(obj: unknown): string {
  if (obj === null || obj === undefined) return "null";
  if (typeof obj === "boolean" || typeof obj === "number") {
    return JSON.stringify(obj);
  }
  if (typeof obj === "string") return JSON.stringify(obj);

  if (Array.isArray(obj)) {
    const items = obj.map((item) => canonicalJson(item));
    return `[${items.join(",")}]`;
  }

  if (typeof obj === "object") {
    const keys = Object.keys(obj as Record<string, unknown>).sort();
    const pairs = keys.map((key) => {
      const value = (obj as Record<string, unknown>)[key];
      if (value === undefined) return null;
      return `${JSON.stringify(key)}:${canonicalJson(value)}`;
    });
    return `{${pairs.filter(Boolean).join(",")}}`;
  }

  return String(obj);
}

// ---------------------------------------------------------------------------
// Crypto helpers
// ---------------------------------------------------------------------------

function hexToBytes(hex: string): Uint8Array {
  const bytes = new Uint8Array(hex.length / 2);
  for (let i = 0; i < hex.length; i += 2) {
    bytes[i / 2] = parseInt(hex.substring(i, i + 2), 16);
  }
  return bytes;
}

function bytesToHex(bytes: Uint8Array): string {
  return Array.from(bytes)
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

async function sha256Hex(data: string): Promise<string> {
  const encoded = new TextEncoder().encode(data);
  const hashBuffer = await crypto.subtle.digest("SHA-256", encoded);
  return bytesToHex(new Uint8Array(hashBuffer));
}

async function importEd25519PublicKey(
  hexKey: string,
): Promise<CryptoKey | null> {
  try {
    const keyBytes = hexToBytes(hexKey);
    return await crypto.subtle.importKey(
      "raw",
      keyBytes.buffer as ArrayBuffer,
      { name: "Ed25519" },
      false,
      ["verify"],
    );
  } catch {
    return null;
  }
}

async function verifyEd25519Signature(
  publicKey: CryptoKey,
  signature: string,
  message: string,
): Promise<boolean> {
  try {
    const signatureBytes = hexToBytes(signature);
    const messageBytes = new TextEncoder().encode(message);
    return await crypto.subtle.verify(
      "Ed25519",
      publicKey,
      signatureBytes.buffer as ArrayBuffer,
      messageBytes.buffer as ArrayBuffer,
    );
  } catch {
    return false;
  }
}

// ---------------------------------------------------------------------------
// Main verification function
// ---------------------------------------------------------------------------

export async function verifyChain(
  bundle: VerificationBundle,
  onProgress?: (progress: VerificationProgress) => void,
): Promise<ChainVerificationResult> {
  const { entries, public_keys } = bundle;
  const total = entries.length;
  const results: EntryVerificationResult[] = [];
  const breaks: number[] = [];
  let verifiedCount = 0;

  if (total === 0) {
    return {
      valid: true,
      totalEntries: 0,
      verifiedEntries: 0,
      breaks: [],
      entries: [],
    };
  }

  // Import all public keys upfront
  const importedKeys: Record<string, CryptoKey | null> = {};
  for (const [keyId, hexKey] of Object.entries(public_keys)) {
    importedKeys[keyId] = await importEd25519PublicKey(hexKey);
  }

  for (let i = 0; i < entries.length; i++) {
    onProgress?.({ current: i + 1, total, status: "verifying" });

    const entry = entries[i] as ChainEntry;
    const result: EntryVerificationResult = {
      index: i,
      contentHashValid: false,
      signatureValid: false,
      chainLinkValid: false,
    };

    try {
      // 1. Verify content hash: canonical JSON of payload should produce
      //    the declared content_hash via SHA-256.
      const canonical = canonicalJson(entry.payload);
      const computedHash = await sha256Hex(canonical);
      result.contentHashValid = computedHash === entry.content_hash;

      // 2. Verify chain link: the parent_hash of entry[i] should match
      //    the content_hash of entry[i-1] (genesis entry has no parent).
      if (i === 0) {
        // Genesis entry: parent_hash should be empty or a well-known value
        result.chainLinkValid =
          entry.parent_hash === "" ||
          entry.parent_hash === "genesis" ||
          entry.parent_hash ===
            "0000000000000000000000000000000000000000000000000000000000000000";
      } else {
        const previousEntry = entries[i - 1] as ChainEntry;
        result.chainLinkValid =
          entry.parent_hash === previousEntry.content_hash;
      }

      // 3. Verify signature: the signer's public key should verify the
      //    signature over the content_hash.
      const signerKey = importedKeys[entry.signer_key_id];
      if (signerKey) {
        result.signatureValid = await verifyEd25519Signature(
          signerKey,
          entry.signature,
          entry.content_hash,
        );
      } else {
        result.error = `Unknown signer key: ${entry.signer_key_id}`;
      }

      // Count verified entries (all three checks pass)
      if (
        result.contentHashValid &&
        result.signatureValid &&
        result.chainLinkValid
      ) {
        verifiedCount++;
      } else {
        breaks.push(i);
      }
    } catch (err) {
      result.error = err instanceof Error ? err.message : "Verification failed";
      breaks.push(i);
    }

    results.push(result);
  }

  onProgress?.({ current: total, total, status: "complete" });

  return {
    valid: breaks.length === 0,
    totalEntries: total,
    verifiedEntries: verifiedCount,
    breaks,
    entries: results,
  };
}

// ---------------------------------------------------------------------------
// Bundle file parser
// ---------------------------------------------------------------------------

export async function parseBundleFromZip(
  file: File,
): Promise<VerificationBundle> {
  // For ZIP files, we expect a single JSON file inside. For simplicity,
  // we also support direct JSON upload.
  const text = await file.text();

  try {
    const parsed = JSON.parse(text) as VerificationBundle;

    // Validate structure
    if (
      !parsed.session_id ||
      !Array.isArray(parsed.entries) ||
      !parsed.public_keys
    ) {
      throw new Error(
        "Invalid bundle format. Expected session_id, entries array, and public_keys.",
      );
    }

    return parsed;
  } catch (err) {
    if (err instanceof SyntaxError) {
      throw new Error(
        "Could not parse the uploaded file. Please upload a valid JSON verification bundle.",
      );
    }
    throw err;
  }
}
