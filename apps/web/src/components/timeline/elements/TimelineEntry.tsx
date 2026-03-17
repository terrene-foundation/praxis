// Copyright 2026 Terrene Foundation
// Licensed under the Apache License, Version 2.0

/**
 * Individual timeline entry component.
 *
 * Displays a single deliberation record with type icon, content,
 * actor, timestamp, and expandable detail including rationale,
 * alternatives, and confidence.
 */

import { useState } from "react";
import {
  ChevronDown,
  ChevronUp,
  Eye,
  Lightbulb,
  MessageSquare,
} from "lucide-react";

import type { DeliberationRecord } from "@/types/api";
import { formatRelativeTime } from "@/lib/format";

interface TimelineEntryProps {
  record: DeliberationRecord;
  isLast: boolean;
}

/**
 * Extract a human-readable summary from the backend content dict.
 *
 * Decisions have {decision, alternatives?, decision_type?}.
 * Observations have {observation}.
 * Escalations have {issue, context}.
 */
function contentSummary(record: DeliberationRecord): string {
  const c = record.content;
  if (typeof c === "string") return c;
  if (c && typeof c === "object") {
    if ("decision" in c) return String(c.decision);
    if ("observation" in c) return String(c.observation);
    if ("issue" in c) return String(c.issue);
  }
  return JSON.stringify(c);
}

function contentAlternatives(record: DeliberationRecord): string[] {
  const c = record.content;
  if (
    c &&
    typeof c === "object" &&
    "alternatives" in c &&
    Array.isArray(c.alternatives)
  ) {
    return c.alternatives as string[];
  }
  return [];
}

function reasoningRationale(record: DeliberationRecord): string | null {
  const t = record.reasoning_trace;
  if (t && typeof t === "object" && "rationale" in t) {
    return String(t.rationale);
  }
  return null;
}

export function TimelineEntry({ record, isLast }: TimelineEntryProps) {
  const [expanded, setExpanded] = useState(false);

  const isDecision = record.record_type === "decision";
  const Icon = isDecision ? Lightbulb : Eye;
  const dotColor = isDecision
    ? "bg-[var(--trust-auto)]"
    : "bg-[var(--muted-foreground)]";

  const summary = contentSummary(record);
  const alternatives = contentAlternatives(record);
  const rationale = reasoningRationale(record);

  return (
    <div className="flex gap-4">
      {/* Timeline connector */}
      <div className="flex flex-col items-center">
        <div
          className={`mt-1 flex h-6 w-6 shrink-0 items-center justify-center rounded-full ${dotColor}`}
        >
          <Icon className="h-3 w-3 text-white" />
        </div>
        {!isLast && <div className="w-0.5 flex-1 bg-[var(--border)]" />}
      </div>

      {/* Content */}
      <div className="flex-1 pb-6">
        <button
          type="button"
          onClick={() => setExpanded(!expanded)}
          className="flex w-full items-start justify-between text-left"
        >
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <span className="rounded-full bg-[var(--muted)] px-2 py-0.5 text-xs font-medium capitalize">
                {record.record_type}
              </span>
              <span className="text-xs text-[var(--muted-foreground)]">
                {record.actor}
              </span>
              <span className="text-xs text-[var(--muted-foreground)]">
                {formatRelativeTime(record.created_at)}
              </span>
            </div>
            <p className="mt-1.5 text-sm">{summary}</p>
          </div>
          <span className="ml-2 mt-1 shrink-0 text-[var(--muted-foreground)]">
            {expanded ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </span>
        </button>

        {/* Expanded details */}
        {expanded && (
          <div className="mt-3 space-y-2 rounded-md border border-[var(--border)] bg-[var(--muted)] p-3">
            {rationale && (
              <div>
                <p className="text-xs font-medium text-[var(--muted-foreground)]">
                  Reasoning
                </p>
                <p className="text-sm">{rationale}</p>
              </div>
            )}

            {alternatives.length > 0 && (
              <div>
                <p className="text-xs font-medium text-[var(--muted-foreground)]">
                  Alternatives considered
                </p>
                <ul className="mt-1 space-y-1">
                  {alternatives.map((alt, i) => (
                    <li
                      key={i}
                      className="flex items-start gap-2 text-sm text-[var(--muted-foreground)]"
                    >
                      <MessageSquare className="mt-0.5 h-3 w-3 shrink-0" />
                      {alt}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {record.confidence !== null && record.confidence !== undefined && (
              <div>
                <p className="text-xs font-medium text-[var(--muted-foreground)]">
                  Confidence
                </p>
                <div className="mt-1 flex items-center gap-2">
                  <div className="h-1.5 w-24 overflow-hidden rounded-full bg-[var(--border)]">
                    <div
                      className="h-full rounded-full bg-[var(--trust-auto)]"
                      style={{
                        width: `${Math.round(record.confidence * 100)}%`,
                      }}
                    />
                  </div>
                  <span className="text-xs tabular-nums text-[var(--muted-foreground)]">
                    {Math.round(record.confidence * 100)}%
                  </span>
                </div>
              </div>
            )}

            <p className="text-xs text-[var(--muted-foreground)]">
              Hash: {record.reasoning_hash.slice(0, 12)}...
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
