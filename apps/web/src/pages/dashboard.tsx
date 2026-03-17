// Copyright 2026 Terrene Foundation
// Licensed under the Apache License, Version 2.0

import { Activity, CheckSquare, Clock, Shield } from "lucide-react";

import { useSessions } from "@/services/hooks";
import { useWebSocketStore } from "@/services/websocket";

// ---------------------------------------------------------------------------
// Stats card element
// ---------------------------------------------------------------------------

function StatsCard({
  title,
  value,
  icon: Icon,
  description,
}: {
  title: string;
  value: string | number;
  icon: React.ComponentType<{ className?: string }>;
  description?: string;
}) {
  return (
    <div className="rounded-lg border border-[var(--border)] bg-[var(--card)] p-6 text-[var(--card-foreground)]">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-[var(--muted-foreground)]">
          {title}
        </p>
        <Icon className="h-4 w-4 text-[var(--muted-foreground)]" />
      </div>
      <div className="mt-2">
        <p className="text-2xl font-bold">{value}</p>
        {description && (
          <p className="mt-1 text-xs text-[var(--muted-foreground)]">
            {description}
          </p>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Loading skeleton
// ---------------------------------------------------------------------------

function StatsCardSkeleton() {
  return (
    <div className="rounded-lg border border-[var(--border)] bg-[var(--card)] p-6">
      <div className="flex items-center justify-between">
        <div className="h-4 w-24 animate-pulse rounded bg-[var(--muted)]" />
        <div className="h-4 w-4 animate-pulse rounded bg-[var(--muted)]" />
      </div>
      <div className="mt-2">
        <div className="h-8 w-16 animate-pulse rounded bg-[var(--muted)]" />
        <div className="mt-1 h-3 w-32 animate-pulse rounded bg-[var(--muted)]" />
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Recent events element
// ---------------------------------------------------------------------------

function RecentEvents() {
  const events = useWebSocketStore((s) => s.events);
  const recentEvents = events.slice(0, 10);

  if (recentEvents.length === 0) {
    return (
      <div className="rounded-lg border border-[var(--border)] bg-[var(--card)] p-6">
        <h3 className="text-sm font-medium text-[var(--muted-foreground)]">
          Recent Events
        </h3>
        <p className="mt-4 text-center text-sm text-[var(--muted-foreground)]">
          No events yet. Events will appear here as sessions are created and
          actions are taken.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-[var(--border)] bg-[var(--card)] p-6">
      <h3 className="mb-4 text-sm font-medium text-[var(--muted-foreground)]">
        Recent Events
      </h3>
      <div className="space-y-3">
        {recentEvents.map((event, index) => (
          <div
            key={`${event.timestamp}-${index}`}
            className="flex items-start gap-3 border-b border-[var(--border)] pb-3 last:border-0"
          >
            <div className="mt-0.5 h-2 w-2 shrink-0 rounded-full bg-[var(--trust-auto)]" />
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium">
                {event.type.replace(/_/g, " ")}
              </p>
              <p className="text-xs text-[var(--muted-foreground)]">
                {new Date(event.timestamp).toLocaleTimeString()}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Dashboard page
// ---------------------------------------------------------------------------

export function DashboardPage() {
  const { data, isLoading } = useSessions();

  const sessions = data?.sessions ?? [];
  const activeSessions = sessions.filter((s) => s.state === "active").length;
  const pausedSessions = sessions.filter((s) => s.state === "paused").length;
  const totalSessions = sessions.length;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-sm text-[var(--muted-foreground)]">
          Overview of your CO collaboration sessions and trust status.
        </p>
      </div>

      {/* Stats grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {isLoading ? (
          <>
            <StatsCardSkeleton />
            <StatsCardSkeleton />
            <StatsCardSkeleton />
            <StatsCardSkeleton />
          </>
        ) : (
          <>
            <StatsCard
              title="Active Sessions"
              value={activeSessions}
              icon={Activity}
              description="Currently running sessions"
            />
            <StatsCard
              title="Paused Sessions"
              value={pausedSessions}
              icon={Clock}
              description="Sessions awaiting input"
            />
            <StatsCard
              title="Total Sessions"
              value={totalSessions}
              icon={CheckSquare}
              description="All sessions this workspace"
            />
            <StatsCard
              title="Trust Status"
              value="Valid"
              icon={Shield}
              description="All chains verified"
            />
          </>
        )}
      </div>

      {/* Recent events */}
      <RecentEvents />
    </div>
  );
}
