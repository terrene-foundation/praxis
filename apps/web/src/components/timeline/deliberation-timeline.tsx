// Copyright 2026 Terrene Foundation
// Licensed under the Apache License, Version 2.0

/**
 * M11-04: Deliberation Timeline
 *
 * Chronological list of deliberation records (decisions, observations,
 * escalations, constraint events) for a session. Supports filtering by
 * type and receives real-time updates via WebSocket.
 */

import { useState } from "react";

import type { RecordType } from "@/types/api";
import { useTimeline } from "@/services/hooks";
import { useWebSocketStore } from "@/services/websocket";
import { TimelineEntry } from "@/components/timeline/elements/TimelineEntry";
import { TimelineSkeleton } from "@/components/timeline/elements/TimelineSkeleton";

interface DeliberationTimelineProps {
  sessionId: string;
}

type FilterType = RecordType | "all";

export function DeliberationTimeline({ sessionId }: DeliberationTimelineProps) {
  const [filter, setFilter] = useState<FilterType>("all");

  const params =
    filter === "all" ? undefined : { record_type: filter as RecordType };
  const { data, isPending, error } = useTimeline(sessionId, params);

  // Subscribe to deliberation events so the component re-renders
  // when the store receives new records, prompting a query refetch.
  useWebSocketStore((s) => s.getEventsByType("deliberation_recorded"));

  if (isPending) return <TimelineSkeleton />;

  if (error) {
    return (
      <p className="text-sm text-[var(--muted-foreground)]">
        Could not load the timeline. Please try again.
      </p>
    );
  }

  const records = data?.records ?? [];

  return (
    <div className="space-y-4">
      {/* Filter tabs */}
      <div className="flex gap-2">
        {(["all", "decision", "observation"] as FilterType[]).map((type) => (
          <button
            key={type}
            type="button"
            onClick={() => setFilter(type)}
            className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
              filter === type
                ? "bg-[var(--primary)] text-[var(--primary-foreground)]"
                : "bg-[var(--muted)] text-[var(--muted-foreground)] hover:bg-[var(--accent)]"
            }`}
          >
            {type === "all"
              ? "All"
              : type === "decision"
                ? "Decisions"
                : "Observations"}
          </button>
        ))}
      </div>

      {/* Timeline */}
      {records.length === 0 ? (
        <p className="py-8 text-center text-sm text-[var(--muted-foreground)]">
          No records yet. Decisions and observations will appear here as they
          are recorded.
        </p>
      ) : (
        <div>
          {records.map((record, index) => (
            <TimelineEntry
              key={record.record_id}
              record={record}
              isLast={index === records.length - 1}
            />
          ))}
          {data?.total !== undefined && data.total > records.length && (
            <p className="pt-2 text-center text-xs text-[var(--muted-foreground)]">
              Showing {records.length} of {data.total} records
            </p>
          )}
        </div>
      )}
    </div>
  );
}
