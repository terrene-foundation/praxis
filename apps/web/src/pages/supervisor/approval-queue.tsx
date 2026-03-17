// Copyright 2026 Terrene Foundation
// Licensed under the Apache License, Version 2.0

/**
 * M11-09: Approval Queue
 *
 * Master-detail layout for reviewing held actions:
 * - Left panel: list of pending approvals
 * - Right panel: selected approval details
 * - Real-time arrivals via WebSocket
 * - Filter by dimension and status
 */

import { useState } from "react";
import { AlertTriangle, CheckCircle, Filter, Inbox } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { HeldActionCard } from "@/components/approval/held-action-card";
import { useWebSocketStore } from "@/services/websocket";
import { cn } from "@/lib/utils";
import type { HeldAction, PraxisEvent } from "@/types/api";

// ---------------------------------------------------------------------------
// Build held actions from WebSocket events
// ---------------------------------------------------------------------------

function buildHeldActions(events: PraxisEvent[]): HeldAction[] {
  const held: HeldAction[] = [];
  const resolved = new Set<string>();

  for (const event of events) {
    if (event.type === "held_action_resolved") {
      const data = event.data as Record<string, string>;
      if (data.held_id) resolved.add(data.held_id);
    }
  }

  for (const event of events) {
    if (event.type === "held_action_created") {
      const data = event.data as Record<string, string>;
      const heldId = data.held_id ?? `held-${event.timestamp}`;
      held.push({
        held_id: heldId,
        session_id: data.session_id ?? "",
        action: data.action ?? "Unknown action",
        resource: data.resource ?? "",
        dimension: data.dimension ?? "operational",
        reason: data.reason ?? "Requires approval",
        utilization: Number(data.utilization) || 0,
        resolution: resolved.has(heldId) ? "approved" : undefined,
        created_at: event.timestamp,
      });
    }
  }

  return held;
}

// ---------------------------------------------------------------------------
// Filter bar
// ---------------------------------------------------------------------------

type StatusFilter = "all" | "pending" | "resolved";
type DimensionFilter = "all" | string;

const DIMENSIONS = [
  "all",
  "financial",
  "operational",
  "temporal",
  "data_access",
  "communication",
];

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export function ApprovalQueuePage() {
  const events = useWebSocketStore((s) => s.events);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("pending");
  const [dimensionFilter, setDimensionFilter] =
    useState<DimensionFilter>("all");
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const allActions = buildHeldActions(events);

  const filteredActions = allActions.filter((a) => {
    if (statusFilter === "pending" && a.resolution) return false;
    if (statusFilter === "resolved" && !a.resolution) return false;
    if (dimensionFilter !== "all" && a.dimension !== dimensionFilter)
      return false;
    return true;
  });

  const selectedAction =
    filteredActions.find((a) => a.held_id === selectedId) ??
    filteredActions[0] ??
    null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Approval Queue</h1>
        <p className="text-sm text-[var(--muted-foreground)]">
          Review and respond to actions that need your approval.
        </p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <Filter className="h-4 w-4 text-[var(--muted-foreground)]" />
        <div className="flex gap-1">
          {(["all", "pending", "resolved"] as StatusFilter[]).map((status) => (
            <Button
              key={status}
              variant={statusFilter === status ? "default" : "outline"}
              size="xs"
              onClick={() => setStatusFilter(status)}
            >
              {status === "all"
                ? "All"
                : status === "pending"
                  ? "Pending"
                  : "Resolved"}
            </Button>
          ))}
        </div>
        <div className="flex gap-1">
          {DIMENSIONS.map((dim) => (
            <Button
              key={dim}
              variant={dimensionFilter === dim ? "secondary" : "ghost"}
              size="xs"
              onClick={() => setDimensionFilter(dim)}
            >
              {dim === "all" ? "All types" : dim.replace("_", " ")}
            </Button>
          ))}
        </div>
      </div>

      {/* Master-detail */}
      <div className="grid gap-6 lg:grid-cols-[1fr_1.5fr]">
        {/* Left: list */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Inbox className="h-4 w-4" />
              Actions ({filteredActions.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {filteredActions.length === 0 ? (
              <div className="flex flex-col items-center gap-2 py-8 text-center">
                <CheckCircle className="h-8 w-8 text-[var(--trust-auto)]" />
                <p className="text-sm text-[var(--muted-foreground)]">
                  No actions matching your filters.
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                {filteredActions.map((action) => (
                  <button
                    key={action.held_id}
                    type="button"
                    onClick={() => setSelectedId(action.held_id)}
                    className={cn(
                      "flex w-full items-center gap-3 rounded-md border p-3 text-left transition-colors",
                      selectedAction?.held_id === action.held_id
                        ? "border-[var(--primary)] bg-[var(--accent)]"
                        : "border-[var(--border)] hover:bg-[var(--accent)]",
                      action.resolution && "opacity-60",
                    )}
                  >
                    <AlertTriangle
                      className={cn(
                        "h-4 w-4 shrink-0",
                        action.resolution
                          ? "text-[var(--muted-foreground)]"
                          : "text-[var(--trust-held)]",
                      )}
                    />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium">
                        {action.action}
                      </p>
                      <p className="text-xs capitalize text-[var(--muted-foreground)]">
                        {action.dimension}
                      </p>
                    </div>
                    {action.resolution && (
                      <span
                        className={cn(
                          "rounded-full px-2 py-0.5 text-xs font-medium",
                          action.resolution === "approved"
                            ? "trust-auto-bg"
                            : "trust-blocked-bg",
                        )}
                      >
                        {action.resolution}
                      </span>
                    )}
                  </button>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Right: detail */}
        <div>
          {selectedAction ? (
            <HeldActionCard
              action={selectedAction}
              sessionId={selectedAction.session_id}
              onResolved={() => setSelectedId(null)}
            />
          ) : (
            <Card>
              <CardContent className="flex min-h-[200px] items-center justify-center">
                <p className="text-sm text-[var(--muted-foreground)]">
                  Select an action from the list to see details.
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
