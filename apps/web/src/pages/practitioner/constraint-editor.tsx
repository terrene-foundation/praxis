// Copyright 2026 Terrene Foundation
// Licensed under the Apache License, Version 2.0

/**
 * M11-07: Constraint Editor
 *
 * Visual editor for session constraints with:
 * - Sliders for financial limits
 * - Toggles for operational permissions
 * - Enforcement of tightening-only rule (cannot loosen beyond original)
 * - Save with reasoning note
 */

import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, Loader2, Save } from "lucide-react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useConstraints, useSession } from "@/services/hooks";
import { queryKeys } from "@/services/hooks";
import { praxisApi } from "@/services/api";
import type { ConstraintUpdate } from "@/types/api";

// ---------------------------------------------------------------------------
// Action toggle
// ---------------------------------------------------------------------------

function ActionToggle({
  label,
  enabled,
  canToggle,
  onToggle,
}: {
  label: string;
  enabled: boolean;
  canToggle: boolean;
  onToggle: (enabled: boolean) => void;
}) {
  return (
    <button
      type="button"
      onClick={() => canToggle && onToggle(!enabled)}
      disabled={!canToggle}
      className={`rounded-md border px-3 py-1.5 text-xs font-medium transition-colors ${
        enabled
          ? "border-[var(--trust-auto)] text-[var(--trust-auto)]"
          : "border-[var(--border)] text-[var(--muted-foreground)]"
      } ${!canToggle ? "cursor-not-allowed opacity-50" : "hover:bg-[var(--accent)]"}`}
    >
      {label}
    </button>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export function ConstraintEditorPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: session, isPending: sessionPending } = useSession(id ?? "");
  const { data: constraints, isPending: constraintsPending } = useConstraints(
    id ?? "",
  );

  const [maxSpend, setMaxSpend] = useState<number | null>(null);
  const [maxDuration, setMaxDuration] = useState<number | null>(null);
  const [allowedActions, setAllowedActions] = useState<string[] | null>(null);
  const [blockedActions, setBlockedActions] = useState<string[] | null>(null);
  const [reason, setReason] = useState("");

  const updateMutation = useMutation({
    mutationFn: (data: ConstraintUpdate) =>
      praxisApi.constraints.update(id ?? "", data),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.constraints.detail(id ?? ""),
      });
      void queryClient.invalidateQueries({
        queryKey: queryKeys.sessions.detail(id ?? ""),
      });
      navigate(`/sessions/${id}`);
    },
  });

  if (sessionPending || constraintsPending) {
    return (
      <div className="space-y-4">
        <div className="h-8 w-48 animate-pulse rounded bg-[var(--muted)]" />
        <div className="h-64 animate-pulse rounded bg-[var(--muted)]" />
      </div>
    );
  }

  if (!session || !constraints) {
    return (
      <p className="text-sm text-[var(--muted-foreground)]">
        Session not found.
      </p>
    );
  }

  const original = constraints.constraint_envelope;

  // Current values (edited or original)
  const currentSpend = maxSpend ?? original.financial.max_spend;
  const currentDuration = maxDuration ?? original.temporal.max_duration_minutes;
  const currentAllowed = allowedActions ?? original.operational.allowed_actions;
  const currentBlocked = blockedActions ?? original.operational.blocked_actions;

  // All possible actions for toggles
  const allActions = [
    ...new Set([
      ...original.operational.allowed_actions,
      ...original.operational.blocked_actions,
    ]),
  ].sort();

  function toggleAction(action: string) {
    const isCurrentlyAllowed = currentAllowed.includes(action);
    if (isCurrentlyAllowed) {
      // Tightening: move to blocked
      setAllowedActions(currentAllowed.filter((a) => a !== action));
      setBlockedActions([...currentBlocked, action]);
    } else {
      // Loosening: only allow if it was originally allowed (tightening-only)
      if (original.operational.allowed_actions.includes(action)) {
        setBlockedActions(currentBlocked.filter((a) => a !== action));
        setAllowedActions([...currentAllowed, action]);
      }
    }
  }

  function handleSave() {
    const update: ConstraintUpdate = {};

    if (maxSpend !== null && maxSpend !== original.financial.max_spend) {
      update.financial = { max_spend: maxSpend };
    }
    if (
      maxDuration !== null &&
      maxDuration !== original.temporal.max_duration_minutes
    ) {
      update.temporal = { max_duration_minutes: maxDuration };
    }
    if (allowedActions !== null || blockedActions !== null) {
      update.operational = {
        allowed_actions: currentAllowed,
        blocked_actions: currentBlocked,
      };
    }

    updateMutation.mutate(update);
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            Edit Constraints
          </h1>
          <p className="text-sm text-[var(--muted-foreground)]">
            You can tighten constraints but not loosen them beyond the original
            settings.
          </p>
        </div>
      </div>

      {/* Financial */}
      <Card>
        <CardHeader>
          <CardTitle>Spending Limit</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="space-y-1.5">
            <Label>Maximum spend ($)</Label>
            <input
              type="range"
              min={0}
              max={original.financial.max_spend}
              step={1}
              value={currentSpend}
              onChange={(e) => setMaxSpend(Number(e.target.value))}
              className="w-full accent-[var(--primary)]"
            />
            <div className="flex justify-between text-xs text-[var(--muted-foreground)]">
              <span>$0</span>
              <span className="font-medium text-[var(--foreground)]">
                ${currentSpend}
              </span>
              <span>${original.financial.max_spend} (max)</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Temporal */}
      <Card>
        <CardHeader>
          <CardTitle>Time Limit</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="space-y-1.5">
            <Label>Maximum duration (minutes)</Label>
            <input
              type="range"
              min={1}
              max={original.temporal.max_duration_minutes}
              step={1}
              value={currentDuration}
              onChange={(e) => setMaxDuration(Number(e.target.value))}
              className="w-full accent-[var(--primary)]"
            />
            <div className="flex justify-between text-xs text-[var(--muted-foreground)]">
              <span>1 min</span>
              <span className="font-medium text-[var(--foreground)]">
                {currentDuration} min
              </span>
              <span>{original.temporal.max_duration_minutes} min (max)</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Operational */}
      <Card>
        <CardHeader>
          <CardTitle>Allowed Operations</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {allActions.map((action) => {
              const isAllowed = currentAllowed.includes(action);
              const wasOriginallyAllowed =
                original.operational.allowed_actions.includes(action);
              // Can only toggle if: currently allowed (can tighten), or was
              // originally allowed and currently blocked (can restore)
              const canToggle = isAllowed || wasOriginallyAllowed;
              return (
                <ActionToggle
                  key={action}
                  label={action}
                  enabled={isAllowed}
                  canToggle={canToggle}
                  onToggle={() => toggleAction(action)}
                />
              );
            })}
          </div>
          <p className="mt-2 text-xs text-[var(--muted-foreground)]">
            You can only remove permissions, not add new ones beyond the
            original settings.
          </p>
        </CardContent>
      </Card>

      {/* Reason */}
      <Card>
        <CardHeader>
          <CardTitle>Reason for Change</CardTitle>
        </CardHeader>
        <CardContent>
          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Why are you changing these constraints?"
            rows={2}
            className="w-full rounded-md border border-[var(--input)] bg-transparent px-3 py-2 text-sm shadow-xs outline-none placeholder:text-[var(--muted-foreground)] focus-visible:border-[var(--ring)] focus-visible:ring-[3px] focus-visible:ring-[var(--ring)]/50"
          />
        </CardContent>
      </Card>

      {/* Actions */}
      {updateMutation.error && (
        <p className="text-sm text-[var(--trust-blocked)]">
          Could not save changes. Please try again.
        </p>
      )}

      <div className="flex justify-end gap-2">
        <Button variant="outline" onClick={() => navigate(-1)}>
          Cancel
        </Button>
        <Button onClick={handleSave} disabled={updateMutation.isPending}>
          {updateMutation.isPending ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Saving...
            </>
          ) : (
            <>
              <Save className="h-4 w-4" />
              Save Changes
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
