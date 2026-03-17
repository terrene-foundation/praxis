// Copyright 2026 Terrene Foundation
// Licensed under the Apache License, Version 2.0

/**
 * M12-03: Bundle Timeline Viewer
 *
 * Renders a chronological timeline of events from a verification bundle.
 * All data comes from the bundle (not the API) — works fully offline.
 */

import { useLocation, useNavigate, Link } from "react-router-dom";
import { ArrowLeft, Clock, Info } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ChainEntry, VerificationBundle } from "@/types/api";
import { truncateHash } from "@/lib/format";

// ---------------------------------------------------------------------------
// Entry display
// ---------------------------------------------------------------------------

function BundleEntry({ entry, index }: { entry: ChainEntry; index: number }) {
  const payload = entry.payload;
  const type =
    (payload.record_type as string) ?? (payload.type as string) ?? "entry";
  const content =
    (payload.content as string) ??
    (payload.decision as string) ??
    (payload.observation as string) ??
    JSON.stringify(payload).slice(0, 100);
  const actor = (payload.actor as string) ?? "unknown";
  const timestamp = (payload.timestamp as string) ?? "";

  return (
    <div className="flex gap-4">
      <div className="flex flex-col items-center">
        <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[var(--muted)] text-xs font-mono">
          {index}
        </div>
        <div className="w-0.5 flex-1 bg-[var(--border)]" />
      </div>
      <div className="flex-1 pb-4">
        <div className="flex items-center gap-2">
          <span className="rounded-full bg-[var(--muted)] px-2 py-0.5 text-xs font-medium capitalize">
            {type}
          </span>
          <span className="text-xs text-[var(--muted-foreground)]">
            {actor}
          </span>
          {timestamp && (
            <span className="text-xs text-[var(--muted-foreground)]">
              {new Date(timestamp).toLocaleString()}
            </span>
          )}
        </div>
        <p className="mt-1.5 text-sm">{content}</p>
        <p className="mt-1 text-xs font-mono text-[var(--muted-foreground)]">
          {truncateHash(entry.content_hash, 16)}
        </p>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export function BundleTimelinePage() {
  const location = useLocation();
  const navigate = useNavigate();

  const bundle = (location.state as { bundle?: VerificationBundle })?.bundle;

  if (!bundle) {
    return (
      <div className="mx-auto max-w-3xl space-y-6 p-4 md:p-8">
        <p className="text-sm text-[var(--muted-foreground)]">
          No bundle data available.{" "}
          <Link
            to="/verify"
            className="font-medium text-[var(--primary)] hover:underline"
          >
            Upload a bundle first.
          </Link>
        </p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6 p-4 md:p-8">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            Session Timeline
          </h1>
          <p className="text-sm text-[var(--muted-foreground)]">
            Session: {bundle.session_id.slice(0, 12)}... |{" "}
            {bundle.entries.length} entries
          </p>
        </div>
      </div>

      {/* Limitation notice */}
      <div className="flex items-center gap-2 rounded-lg border border-[var(--border)] bg-[var(--muted)] p-3 text-sm">
        <Info className="h-4 w-4 shrink-0 text-[var(--muted-foreground)]" />
        <span className="text-[var(--muted-foreground)]">
          This data was exported from a Praxis session. It reflects the session
          state at the time of export and may not include later events.
        </span>
      </div>

      {/* Timeline */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-4 w-4" />
            Chronological Events
          </CardTitle>
        </CardHeader>
        <CardContent>
          {bundle.entries.length === 0 ? (
            <p className="py-8 text-center text-sm text-[var(--muted-foreground)]">
              This bundle contains no entries.
            </p>
          ) : (
            <div>
              {bundle.entries.map((entry, index) => (
                <BundleEntry key={index} entry={entry} index={index} />
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
