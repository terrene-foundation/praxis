// Copyright 2026 Terrene Foundation
// Licensed under the Apache License, Version 2.0

/**
 * M11-08: Supervisor Team Overview
 *
 * Shows all team sessions with status, constraints, decision counts.
 * Includes an escalation panel for held actions needing supervisor approval
 * and a health summary across the team.
 */

import { Link } from "react-router-dom";
import {
  Activity,
  AlertTriangle,
  CheckCircle,
  ChevronRight,
  Users,
} from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useSessions } from "@/services/hooks";
import { useWebSocketStore } from "@/services/websocket";
import { formatRelativeTime } from "@/lib/format";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Escalation panel element
// ---------------------------------------------------------------------------

function EscalationPanel() {
  const heldEvents = useWebSocketStore((s) =>
    s.getEventsByType("held_action_created"),
  );
  const resolvedEvents = useWebSocketStore((s) =>
    s.getEventsByType("held_action_resolved"),
  );
  const pendingCount = Math.max(0, heldEvents.length - resolvedEvents.length);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-[var(--trust-held)]" />
          Escalations
        </CardTitle>
      </CardHeader>
      <CardContent>
        {pendingCount === 0 ? (
          <div className="flex items-center gap-2 text-sm text-[var(--muted-foreground)]">
            <CheckCircle className="h-4 w-4 text-[var(--trust-auto)]" />
            No pending escalations. All held actions have been resolved.
          </div>
        ) : (
          <div className="space-y-2">
            <p className="text-sm">
              <span className="text-lg font-bold text-[var(--trust-held)]">
                {pendingCount}
              </span>{" "}
              action{pendingCount !== 1 ? "s" : ""} awaiting your approval
            </p>
            <Link
              to="/approvals"
              className="inline-flex items-center gap-1 text-sm font-medium text-[var(--primary)] hover:underline"
            >
              Review approvals
              <ChevronRight className="h-4 w-4" />
            </Link>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export function TeamOverviewPage() {
  const { data, isPending } = useSessions();

  const sessions = data?.sessions ?? [];
  const activeSessions = sessions.filter((s) => s.state === "active");
  const pausedSessions = sessions.filter((s) => s.state === "paused");

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Team Overview</h1>
        <p className="text-sm text-[var(--muted-foreground)]">
          Monitor your team's sessions, constraints, and escalations.
        </p>
      </div>

      {/* Health summary */}
      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardContent className="pt-0">
            <div className="flex items-center justify-between">
              <p className="text-sm text-[var(--muted-foreground)]">Active</p>
              <Activity className="h-4 w-4 text-[var(--muted-foreground)]" />
            </div>
            <p className="mt-2 text-2xl font-bold">{activeSessions.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-0">
            <div className="flex items-center justify-between">
              <p className="text-sm text-[var(--muted-foreground)]">Paused</p>
              <AlertTriangle className="h-4 w-4 text-[var(--muted-foreground)]" />
            </div>
            <p className="mt-2 text-2xl font-bold">{pausedSessions.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-0">
            <div className="flex items-center justify-between">
              <p className="text-sm text-[var(--muted-foreground)]">Total</p>
              <Users className="h-4 w-4 text-[var(--muted-foreground)]" />
            </div>
            <p className="mt-2 text-2xl font-bold">{sessions.length}</p>
          </CardContent>
        </Card>
      </div>

      {/* Escalation panel */}
      <EscalationPanel />

      {/* Sessions table */}
      <Card>
        <CardHeader>
          <CardTitle>All Sessions</CardTitle>
        </CardHeader>
        <CardContent>
          {isPending ? (
            <div className="space-y-2">
              {[...Array(5)].map((_, i) => (
                <div
                  key={i}
                  className="h-12 animate-pulse rounded bg-[var(--muted)]"
                />
              ))}
            </div>
          ) : sessions.length === 0 ? (
            <p className="py-8 text-center text-sm text-[var(--muted-foreground)]">
              No sessions in this workspace yet.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Domain</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead>Workspace</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sessions.map((session) => (
                  <TableRow key={session.session_id}>
                    <TableCell className="font-medium capitalize">
                      {session.domain}
                    </TableCell>
                    <TableCell>
                      <span
                        className={cn(
                          "rounded-full px-2 py-0.5 text-xs font-medium",
                          session.state === "active"
                            ? "trust-auto-bg"
                            : session.state === "paused"
                              ? "trust-flagged-bg"
                              : "bg-[var(--muted)] text-[var(--muted-foreground)]",
                        )}
                      >
                        {session.state}
                      </span>
                    </TableCell>
                    <TableCell className="text-[var(--muted-foreground)]">
                      {formatRelativeTime(session.created_at)}
                    </TableCell>
                    <TableCell className="text-[var(--muted-foreground)]">
                      {session.workspace_id}
                    </TableCell>
                    <TableCell>
                      <Link
                        to={`/sessions/${session.session_id}`}
                        className="text-sm font-medium text-[var(--primary)] hover:underline"
                      >
                        Inspect
                      </Link>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
