// Copyright 2026 Terrene Foundation
// Licensed under the Apache License, Version 2.0

/**
 * Individual constraint dimension progress bar.
 *
 * Displays a dimension name, utilization percentage, and a color-coded
 * progress bar based on the gradient level.
 */

import { useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";

import type { DimensionStatus } from "@/types/api";
import { trustCssVar, trustLabel } from "@/lib/trust-colors";
import { cn } from "@/lib/utils";

const dimensionLabels: Record<string, string> = {
  financial: "Spending",
  operational: "Operations",
  temporal: "Time",
  data_access: "Data Access",
  communication: "Communication",
};

interface DimensionBarProps {
  dimension: DimensionStatus;
}

export function DimensionBar({ dimension }: DimensionBarProps) {
  const [expanded, setExpanded] = useState(false);
  const label = dimensionLabels[dimension.dimension] ?? dimension.dimension;
  const percent = Math.round(dimension.utilization * 100);
  const color = trustCssVar(dimension.level);

  return (
    <div className="space-y-1.5">
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center justify-between text-sm"
      >
        <span className="font-medium">{label}</span>
        <span className="flex items-center gap-1.5 text-[var(--muted-foreground)]">
          <span
            className={cn(
              "rounded-full px-2 py-0.5 text-xs font-medium",
              dimension.level === "auto_approved" && "trust-auto-bg",
              dimension.level === "flagged" && "trust-flagged-bg",
              dimension.level === "held" && "trust-held-bg",
              dimension.level === "blocked" && "trust-blocked-bg",
            )}
          >
            {trustLabel(dimension.level)}
          </span>
          <span className="text-xs tabular-nums">{percent}%</span>
          {expanded ? (
            <ChevronUp className="h-3 w-3" />
          ) : (
            <ChevronDown className="h-3 w-3" />
          )}
        </span>
      </button>

      {/* Progress bar */}
      <div className="h-2 w-full overflow-hidden rounded-full bg-[var(--muted)]">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{
            width: `${Math.min(percent, 100)}%`,
            backgroundColor: color,
          }}
        />
      </div>

      {/* Expanded detail */}
      {expanded && (
        <p className="text-xs text-[var(--muted-foreground)]">
          {dimension.reason || "No additional detail available."}
        </p>
      )}
    </div>
  );
}
