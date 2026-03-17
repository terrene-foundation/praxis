// Copyright 2026 Terrene Foundation
// Licensed under the Apache License, Version 2.0

/**
 * M11-11: Session Inspection
 *
 * Tabbed read-only view for supervisors to inspect a session:
 * - Timeline tab: deliberation records
 * - Constraints tab: constraint gauge
 * - Trust Chain tab: delegation tree + chain status
 * - Decisions tab: filtered timeline for decisions only
 */

import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, Eye } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useSession, useTrustChain } from "@/services/hooks";
import { DeliberationTimeline } from "@/components/timeline/deliberation-timeline";
import { ConstraintGauge } from "@/components/constraints/constraint-gauge";
import { DelegationTree } from "@/components/trust/delegation-tree";
import { ChainIntegritySummary } from "@/components/trust/chain-integrity";
import { formatDateTime } from "@/lib/format";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export function SessionInspectionPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data: session, isPending } = useSession(id ?? "");
  const { data: chain } = useTrustChain(id ?? "");

  if (isPending) {
    return (
      <div className="space-y-4">
        <div className="h-8 w-48 animate-pulse rounded bg-[var(--muted)]" />
        <div className="h-64 animate-pulse rounded bg-[var(--muted)]" />
      </div>
    );
  }

  if (!session) {
    return (
      <p className="text-sm text-[var(--muted-foreground)]">
        Session not found.
      </p>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <Eye className="h-5 w-5 text-[var(--muted-foreground)]" />
            <h1 className="text-2xl font-bold tracking-tight">
              Session Inspection
            </h1>
            <span className="text-sm text-[var(--muted-foreground)]">
              (read-only)
            </span>
          </div>
          <div className="mt-1 flex items-center gap-4 text-sm text-[var(--muted-foreground)]">
            <span className="capitalize">{session.domain}</span>
            <span
              className={cn(
                "rounded-full px-2 py-0.5 text-xs font-medium",
                session.state === "active"
                  ? "trust-auto-bg"
                  : session.state === "paused"
                    ? "trust-flagged-bg"
                    : "bg-[var(--muted)]",
              )}
            >
              {session.state}
            </span>
            <span>Created {formatDateTime(session.created_at)}</span>
          </div>
        </div>
      </div>

      {/* Trust chain summary */}
      {chain && (
        <Card>
          <CardContent className="pt-0">
            <ChainIntegritySummary chain={chain} />
          </CardContent>
        </Card>
      )}

      {/* Tabbed content */}
      <Tabs defaultValue="timeline">
        <TabsList>
          <TabsTrigger value="timeline">Timeline</TabsTrigger>
          <TabsTrigger value="constraints">Constraints</TabsTrigger>
          <TabsTrigger value="trust">Trust Chain</TabsTrigger>
          <TabsTrigger value="decisions">Decisions</TabsTrigger>
        </TabsList>

        <TabsContent value="timeline" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Deliberation Timeline</CardTitle>
            </CardHeader>
            <CardContent>
              <DeliberationTimeline sessionId={session.session_id} />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="constraints" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Constraint Status</CardTitle>
            </CardHeader>
            <CardContent>
              <ConstraintGauge sessionId={session.session_id} />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="trust" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Trust Chain & Delegations</CardTitle>
            </CardHeader>
            <CardContent>
              <DelegationTree sessionId={session.session_id} />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="decisions" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Decisions Only</CardTitle>
            </CardHeader>
            <CardContent>
              <DeliberationTimeline sessionId={session.session_id} />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
