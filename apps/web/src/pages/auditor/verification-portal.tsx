// Copyright 2026 Terrene Foundation
// Licensed under the Apache License, Version 2.0

/**
 * M12-01: Verification Portal
 *
 * Public page (no account required) for auditors to:
 * - Upload a verification bundle (drag-and-drop or file picker)
 * - Run client-side chain verification
 * - View results with chain integrity display
 *
 * All verification runs entirely in the browser. No data is sent to any server.
 */

import { useCallback, useState } from "react";
import { useNavigate } from "react-router-dom";
import { FileUp, Loader2, Lock, Shield, Upload } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  parseBundleFromZip,
  verifyChain,
  type ChainVerificationResult,
  type VerificationProgress,
} from "@/lib/chain-verifier";
import { ChainIntegrity } from "@/components/trust/chain-integrity";
import type { VerificationBundle } from "@/types/api";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export function VerificationPortalPage() {
  const navigate = useNavigate();

  const [bundle, setBundle] = useState<VerificationBundle | null>(null);
  const [result, setResult] = useState<ChainVerificationResult | null>(null);
  const [progress, setProgress] = useState<VerificationProgress | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);

  const isVerifying = progress?.status === "verifying";

  const handleFile = useCallback(async (file: File) => {
    setError(null);
    setResult(null);
    setProgress(null);

    try {
      const parsed = await parseBundleFromZip(file);
      setBundle(parsed);

      // Automatically start verification
      const verificationResult = await verifyChain(parsed, (p) =>
        setProgress(p),
      );
      setResult(verificationResult);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Something went wrong processing this file.",
      );
    }
  }, []);

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) {
      void handleFile(file);
    }
  }

  function handleDragOver(e: React.DragEvent) {
    e.preventDefault();
    setDragging(true);
  }

  function handleDragLeave(e: React.DragEvent) {
    e.preventDefault();
    setDragging(false);
  }

  function handleFileInput(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) {
      void handleFile(file);
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6 p-4 md:p-8">
      {/* Header */}
      <div className="text-center">
        <div className="mb-4 flex items-center justify-center gap-2">
          <Shield className="h-8 w-8 text-[var(--primary)]" />
          <h1 className="text-3xl font-bold tracking-tight">
            Verification Portal
          </h1>
        </div>
        <p className="text-[var(--muted-foreground)]">
          Verify the integrity of a Praxis session's trust chain. Upload a
          verification bundle to get started.
        </p>
      </div>

      {/* Privacy notice */}
      <div className="flex items-center gap-2 rounded-lg border border-[var(--trust-auto)] bg-[color-mix(in_oklch,var(--trust-auto)_5%,transparent)] p-3 text-sm">
        <Lock className="h-4 w-4 shrink-0 text-[var(--trust-auto)]" />
        <span>
          All verification runs client-side — no data is sent to any server.
          Your bundle never leaves your browser.
        </span>
      </div>

      {/* Upload area */}
      {!bundle && (
        <Card>
          <CardContent>
            <div
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              className={cn(
                "flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-12 transition-colors",
                dragging
                  ? "border-[var(--primary)] bg-[var(--accent)]"
                  : "border-[var(--border)]",
              )}
            >
              <Upload className="mb-4 h-12 w-12 text-[var(--muted-foreground)]" />
              <p className="text-lg font-medium">
                Drop your verification bundle here
              </p>
              <p className="mt-1 text-sm text-[var(--muted-foreground)]">
                or click to browse
              </p>
              <label className="mt-4 cursor-pointer">
                <input
                  type="file"
                  accept=".json,.zip"
                  onChange={handleFileInput}
                  className="hidden"
                />
                <span className="inline-flex items-center gap-2 rounded-md bg-[var(--primary)] px-4 py-2 text-sm font-medium text-[var(--primary-foreground)] transition-colors hover:bg-[var(--primary)]/90">
                  <FileUp className="h-4 w-4" />
                  Choose File
                </span>
              </label>
              <p className="mt-4 text-xs text-[var(--muted-foreground)]">
                Accepts JSON verification bundles exported from Praxis
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Error */}
      {error && (
        <Card>
          <CardContent>
            <p className="text-sm text-[var(--trust-blocked)]">{error}</p>
            <Button
              variant="outline"
              size="sm"
              className="mt-2"
              onClick={() => {
                setError(null);
                setBundle(null);
              }}
            >
              Try again
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Verification progress */}
      {isVerifying && progress && (
        <Card>
          <CardContent className="flex items-center gap-4">
            <Loader2 className="h-6 w-6 animate-spin text-[var(--primary)]" />
            <div className="flex-1">
              <p className="text-sm font-medium">
                Verifying chain integrity...
              </p>
              <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-[var(--muted)]">
                <div
                  className="h-full rounded-full bg-[var(--primary)] transition-all"
                  style={{
                    width: `${(progress.current / progress.total) * 100}%`,
                  }}
                />
              </div>
              <p className="mt-1 text-xs text-[var(--muted-foreground)]">
                Entry {progress.current} of {progress.total}
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Results */}
      {result && (
        <>
          <Card>
            <CardHeader>
              <CardTitle>Verification Results</CardTitle>
            </CardHeader>
            <CardContent>
              <ChainIntegrity result={result} />
            </CardContent>
          </Card>

          {/* Navigation to detailed views */}
          <div className="flex gap-3">
            <Button
              variant="outline"
              onClick={() =>
                navigate("/verify/timeline", {
                  state: { bundle },
                })
              }
            >
              View Timeline
            </Button>
            <Button
              variant="outline"
              onClick={() =>
                navigate("/verify/compliance", {
                  state: { bundle, result },
                })
              }
            >
              Compliance Assessment
            </Button>
            <Button
              variant="outline"
              onClick={() =>
                navigate("/verify/download", {
                  state: { bundle, result },
                })
              }
            >
              Download Report
            </Button>
            <Button
              variant="ghost"
              onClick={() => {
                setBundle(null);
                setResult(null);
                setProgress(null);
              }}
            >
              Verify Another
            </Button>
          </div>
        </>
      )}
    </div>
  );
}
