// Copyright 2026 Terrene Foundation
// Licensed under the Apache License, Version 2.0

/**
 * M11-01: Practitioner Dashboard
 *
 * Main view for practitioners showing:
 * - Active sessions with status badges
 * - Recent activity feed
 * - Constraint overview (5-dimension summary)
 * - Quick actions: New Session, Record Decision
 */

import { useState } from "react";
import { Link } from "react-router-dom";
import {
  Activity,
  ChevronRight,
  Clock,
  Lightbulb,
  Plus,
  Shield,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useSessions } from "@/services/hooks";
import { useWebSocketStore } from "@/services/websocket";
import { DecisionForm } from "@/components/decisions/decision-form";
import { ConstraintGauge } from "@/components/constraints/constraint-gauge";
import { formatRelativeTime } from "@/lib/format";
import { cn } from "@/lib/utils";

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
    <Card>
      <CardContent className="pt-0">
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
      </CardContent>
    </Card>
  );
}

function StatsCardSkeleton() {
  return (
    <Card>
      <CardContent className="pt-0">
        <div className="flex items-center justify-between">
          <div className="h-4 w-24 animate-pulse rounded bg-[var(--muted)]" />
          <div className="h-4 w-4 animate-pulse rounded bg-[var(--muted)]" />
        </div>
        <div className="mt-2">
          <div className="h-8 w-16 animate-pulse rounded bg-[var(--muted)]" />
          <div className="mt-1 h-3 w-32 animate-pulse rounded bg-[var(--muted)]" />
        </div>
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Session list element
// ---------------------------------------------------------------------------

function SessionListCard() {
  const { data, isPending } = useSessions();

  if (isPending) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Active Sessions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[...Array(3)].map((_, i) => (
              <div
                key={i}
                className="h-14 animate-pulse rounded-md bg-[var(--muted)]"
              />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  const sessions = data?.sessions ?? [];
  const activeSessions = sessions.filter(
    (s) => s.state === "active" || s.state === "paused",
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle>Active Sessions</CardTitle>
      </CardHeader>
      <CardContent>
        {activeSessions.length === 0 ? (
          <p className="py-4 text-center text-sm text-[var(--muted-foreground)]">
            No active sessions. Create one to get started.
          </p>
        ) : (
          <div className="space-y-2">
            {activeSessions.slice(0, 5).map((session) => (
              <Link
                key={session.session_id}
                to={`/sessions/${session.session_id}`}
                className="flex items-center justify-between rounded-md border border-[var(--border)] p-3 transition-colors hover:bg-[var(--accent)]"
              >
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium">
                    {session.domain} session
                  </p>
                  <p className="text-xs text-[var(--muted-foreground)]">
                    {formatRelativeTime(session.created_at)}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span
                    className={cn(
                      "rounded-full px-2 py-0.5 text-xs font-medium",
                      session.state === "active"
                        ? "trust-auto-bg"
                        : "trust-flagged-bg",
                    )}
                  >
                    {session.state}
                  </span>
                  <ChevronRight className="h-4 w-4 text-[var(--muted-foreground)]" />
                </div>
              </Link>
            ))}
            {activeSessions.length > 5 && (
              <Link
                to="/sessions"
                className="block text-center text-xs text-[var(--muted-foreground)] hover:text-[var(--foreground)]"
              >
                View all {activeSessions.length} sessions
              </Link>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Activity feed element
// ---------------------------------------------------------------------------

function ActivityFeed() {
  const events = useWebSocketStore((s) => s.events);
  const recentEvents = events.slice(0, 8);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Activity</CardTitle>
      </CardHeader>
      <CardContent>
        {recentEvents.length === 0 ? (
          <p className="py-4 text-center text-sm text-[var(--muted-foreground)]">
            No recent activity. Events will appear here as you work.
          </p>
        ) : (
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
                    {formatRelativeTime(event.timestamp)}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export function PractitionerDashboardPage() {
  const { data, isLoading } = useSessions();
  const [showDecisionDialog, setShowDecisionDialog] = useState(false);

  const sessions = data?.sessions ?? [];
  const activeSessions = sessions.filter((s) => s.state === "active").length;
  const pausedSessions = sessions.filter((s) => s.state === "paused").length;
  const firstActiveSession = sessions.find((s) => s.state === "active");

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-sm text-[var(--muted-foreground)]">
            Your collaboration sessions and trust overview.
          </p>
        </div>
        <div className="flex gap-2">
          <Button asChild>
            <Link to="/sessions/new">
              <Plus className="h-4 w-4" />
              New Session
            </Link>
          </Button>
          {firstActiveSession && (
            <Button
              variant="outline"
              onClick={() => setShowDecisionDialog(true)}
            >
              <Lightbulb className="h-4 w-4" />
              Record Decision
            </Button>
          )}
        </div>
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
              description="Currently running"
            />
            <StatsCard
              title="Paused"
              value={pausedSessions}
              icon={Clock}
              description="Awaiting input"
            />
            <StatsCard
              title="Total"
              value={sessions.length}
              icon={Activity}
              description="All sessions"
            />
            <StatsCard
              title="Trust"
              value="Valid"
              icon={Shield}
              description="Chains verified"
            />
          </>
        )}
      </div>

      {/* Main content */}
      <div className="grid gap-6 lg:grid-cols-2">
        <SessionListCard />
        <ActivityFeed />
      </div>

      {/* Constraint overview for first active session */}
      {firstActiveSession && (
        <Card>
          <CardHeader>
            <CardTitle>Constraints Overview</CardTitle>
          </CardHeader>
          <CardContent>
            <ConstraintGauge sessionId={firstActiveSession.session_id} />
          </CardContent>
        </Card>
      )}

      {/* Decision recording dialog */}
      <Dialog open={showDecisionDialog} onOpenChange={setShowDecisionDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Record a Decision</DialogTitle>
          </DialogHeader>
          {firstActiveSession && (
            <DecisionForm
              sessionId={firstActiveSession.session_id}
              onSuccess={() => setShowDecisionDialog(false)}
            />
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
