// Copyright 2026 Terrene Foundation
// Licensed under the Apache License, Version 2.0

/**
 * M11-06: Held Action Approval Card
 *
 * Displays a held action that needs human approval. Shows who requested it,
 * what they want to do, why it was held, and the relevant context. Provides
 * Approve, Deny, and Approve with Conditions actions.
 *
 * Prominent styling when pending, dimmed when resolved.
 */

import { useState } from "react";
import { AlertTriangle, Check, Loader2, MessageSquare, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { HeldAction } from "@/types/api";
import { useApproveAction, useDenyAction } from "@/services/hooks";
import { formatRelativeTime } from "@/lib/format";
import { cn } from "@/lib/utils";

interface HeldActionCardProps {
  action: HeldAction;
  sessionId: string;
  onResolved?: () => void;
}

export function HeldActionCard({
  action,
  sessionId,
  onResolved,
}: HeldActionCardProps) {
  const [showConditions, setShowConditions] = useState(false);
  const [_conditions, setConditions] = useState("");

  const approveMutation = useApproveAction();
  const denyMutation = useDenyAction();
  const isResolved = !!action.resolution;
  const isPending = approveMutation.isPending || denyMutation.isPending;

  async function handleApprove() {
    await approveMutation.mutateAsync({
      sessionId,
      heldId: action.held_id,
    });
    onResolved?.();
  }

  async function handleDeny() {
    await denyMutation.mutateAsync({
      sessionId,
      heldId: action.held_id,
    });
    onResolved?.();
  }

  const borderColor = isResolved
    ? "border-[var(--border)]"
    : "border-[var(--trust-held)]";

  return (
    <div
      className={cn(
        "rounded-lg border-2 bg-[var(--card)] p-4 transition-opacity",
        borderColor,
        isResolved && "opacity-60",
      )}
    >
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          <AlertTriangle
            className={cn(
              "h-5 w-5",
              isResolved
                ? "text-[var(--muted-foreground)]"
                : "text-[var(--trust-held)]",
            )}
          />
          <span className="text-sm font-semibold">Action Held</span>
        </div>
        <span
          className={cn(
            "rounded-full px-2 py-0.5 text-xs font-medium",
            isResolved
              ? action.resolution === "approved"
                ? "trust-auto-bg"
                : "trust-blocked-bg"
              : "trust-held-bg",
          )}
        >
          {isResolved
            ? action.resolution === "approved"
              ? "Approved"
              : "Denied"
            : "Held"}
        </span>
      </div>

      {/* Details */}
      <div className="mt-3 space-y-2">
        <div>
          <p className="text-xs font-medium text-[var(--muted-foreground)]">
            What
          </p>
          <p className="text-sm">{action.action}</p>
        </div>
        <div className="flex gap-4">
          <div>
            <p className="text-xs font-medium text-[var(--muted-foreground)]">
              Dimension
            </p>
            <p className="text-sm capitalize">{action.dimension}</p>
          </div>
          <div>
            <p className="text-xs font-medium text-[var(--muted-foreground)]">
              When
            </p>
            <p className="text-sm">{formatRelativeTime(action.created_at)}</p>
          </div>
        </div>
        <div>
          <p className="text-xs font-medium text-[var(--muted-foreground)]">
            Why it was held
          </p>
          <p className="text-sm">{action.reason}</p>
        </div>
      </div>

      {/* Resolution info */}
      {isResolved && (
        <div className="mt-3 rounded-md bg-[var(--muted)] p-2 text-xs text-[var(--muted-foreground)]">
          Resolved by {action.resolved_by}{" "}
          {action.resolved_at && formatRelativeTime(action.resolved_at)}
        </div>
      )}

      {/* Actions */}
      {!isResolved && (
        <div className="mt-4 space-y-2">
          {showConditions && (
            <div className="flex gap-2">
              <Input
                placeholder="Specify conditions..."
                onChange={(e) => setConditions(e.target.value)}
                className="text-sm"
              />
              <Button size="sm" onClick={handleApprove} disabled={isPending}>
                Submit
              </Button>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setShowConditions(false)}
              >
                Cancel
              </Button>
            </div>
          )}

          <div className="flex gap-2">
            <Button
              size="sm"
              onClick={handleApprove}
              disabled={isPending}
              className="flex-1"
            >
              {approveMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Check className="h-4 w-4" />
              )}
              Approve
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => setShowConditions(true)}
              disabled={isPending || showConditions}
            >
              <MessageSquare className="h-4 w-4" />
              Conditions
            </Button>
            <Button
              size="sm"
              variant="destructive"
              onClick={handleDeny}
              disabled={isPending}
            >
              {denyMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <X className="h-4 w-4" />
              )}
              Deny
            </Button>
          </div>

          {(approveMutation.error || denyMutation.error) && (
            <p className="text-xs text-[var(--trust-blocked)]">
              Something went wrong. Please try again.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
