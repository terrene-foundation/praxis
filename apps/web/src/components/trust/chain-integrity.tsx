// Copyright 2026 Terrene Foundation
// Licensed under the Apache License, Version 2.0

/**
 * M12-04: Chain Integrity Display
 *
 * Visual chain of connected entries with verification status indicators.
 * Green check for verified, red X for failed, gray for unverified.
 * Highlights breaks in the chain.
 *
 * Works with both API-sourced ChainStatus and client-side verification results.
 */

import { CheckCircle, Circle, XCircle } from "lucide-react";

import type { ChainVerificationResult } from "@/lib/chain-verifier";
import { truncateHash } from "@/lib/format";
import { cn } from "@/lib/utils";

interface ChainIntegrityProps {
  result: ChainVerificationResult;
}

export function ChainIntegrity({ result }: ChainIntegrityProps) {
  if (result.totalEntries === 0) {
    return (
      <p className="py-4 text-center text-sm text-[var(--muted-foreground)]">
        No entries in this chain.
      </p>
    );
  }

  return (
    <div className="space-y-4">
      {/* Summary */}
      <div className="flex items-center gap-3">
        {result.valid ? (
          <CheckCircle className="h-5 w-5 text-[var(--trust-valid)]" />
        ) : (
          <XCircle className="h-5 w-5 text-[var(--trust-invalid)]" />
        )}
        <div>
          <p className="text-sm font-medium">
            {result.valid
              ? "Chain integrity verified"
              : `Chain has ${result.breaks.length} break${result.breaks.length !== 1 ? "s" : ""}`}
          </p>
          <p className="text-xs text-[var(--muted-foreground)]">
            {result.verifiedEntries} of {result.totalEntries} entries verified
          </p>
        </div>
      </div>

      {/* Chain visualization */}
      <div className="space-y-0">
        {result.entries.map((entry, i) => {
          const isBreak = result.breaks.includes(i);
          const allValid =
            entry.contentHashValid &&
            entry.signatureValid &&
            entry.chainLinkValid;

          return (
            <div key={i} className="flex items-stretch gap-3">
              {/* Connector line + status dot */}
              <div className="flex flex-col items-center">
                {i > 0 && (
                  <div
                    className={cn(
                      "h-4 w-0.5",
                      isBreak
                        ? "bg-[var(--trust-invalid)]"
                        : "bg-[var(--border)]",
                    )}
                  />
                )}
                {allValid ? (
                  <CheckCircle className="h-4 w-4 shrink-0 text-[var(--trust-valid)]" />
                ) : isBreak ? (
                  <XCircle className="h-4 w-4 shrink-0 text-[var(--trust-invalid)]" />
                ) : (
                  <Circle className="h-4 w-4 shrink-0 text-[var(--muted-foreground)]" />
                )}
                {i < result.entries.length - 1 && (
                  <div className="w-0.5 flex-1 bg-[var(--border)]" />
                )}
              </div>

              {/* Entry detail */}
              <div
                className={cn(
                  "mb-2 flex-1 rounded-md border px-3 py-2 text-xs",
                  isBreak
                    ? "border-[var(--trust-invalid)] bg-[color-mix(in_oklch,var(--trust-invalid)_5%,transparent)]"
                    : "border-[var(--border)]",
                )}
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-[var(--muted-foreground)]">
                    Entry #{i}
                  </span>
                  <div className="flex gap-2">
                    <span
                      className={cn(
                        entry.contentHashValid
                          ? "text-[var(--trust-valid)]"
                          : "text-[var(--trust-invalid)]",
                      )}
                    >
                      Hash{" "}
                      {entry.contentHashValid ? (
                        <CheckCircle className="inline h-3 w-3" />
                      ) : (
                        <XCircle className="inline h-3 w-3" />
                      )}
                    </span>
                    <span
                      className={cn(
                        entry.signatureValid
                          ? "text-[var(--trust-valid)]"
                          : "text-[var(--trust-invalid)]",
                      )}
                    >
                      Sig{" "}
                      {entry.signatureValid ? (
                        <CheckCircle className="inline h-3 w-3" />
                      ) : (
                        <XCircle className="inline h-3 w-3" />
                      )}
                    </span>
                    <span
                      className={cn(
                        entry.chainLinkValid
                          ? "text-[var(--trust-valid)]"
                          : "text-[var(--trust-invalid)]",
                      )}
                    >
                      Link{" "}
                      {entry.chainLinkValid ? (
                        <CheckCircle className="inline h-3 w-3" />
                      ) : (
                        <XCircle className="inline h-3 w-3" />
                      )}
                    </span>
                  </div>
                </div>
                {entry.error && (
                  <p className="mt-1 text-[var(--trust-invalid)]">
                    {entry.error}
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/**
 * Simple chain integrity summary for use in session views.
 * Fetches data from the API rather than client-side verification.
 */

import type { ChainStatus } from "@/types/api";

interface ChainIntegritySummaryProps {
  chain: ChainStatus;
}

export function ChainIntegritySummary({ chain }: ChainIntegritySummaryProps) {
  return (
    <div className="flex items-center gap-3">
      {chain.valid ? (
        <CheckCircle className="h-5 w-5 text-[var(--trust-valid)]" />
      ) : (
        <XCircle className="h-5 w-5 text-[var(--trust-invalid)]" />
      )}
      <div>
        <p className="text-sm font-medium">
          {chain.valid
            ? "Trust chain is valid"
            : `Trust chain has ${chain.breaks.length} break${chain.breaks.length !== 1 ? "s" : ""}`}
        </p>
        <p className="text-xs text-[var(--muted-foreground)]">
          {chain.chain_length} entries | Head:{" "}
          <span className="font-mono">{truncateHash(chain.head_hash)}</span>
        </p>
      </div>
    </div>
  );
}
