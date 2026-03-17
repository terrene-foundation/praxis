// Copyright 2026 Terrene Foundation
// Licensed under the Apache License, Version 2.0

/**
 * M11-03: Constraint Gauge
 *
 * Displays all five constraint dimensions as color-coded progress bars.
 * Each bar reflects the current utilization and gradient level (auto_approved,
 * flagged, held, blocked). Clicking a bar expands it to show the reason.
 *
 * Receives real-time updates through WebSocket events that trigger
 * query invalidation.
 */

import { useGradient } from "@/services/hooks";
import { useWebSocketStore } from "@/services/websocket";
import { DimensionBar } from "@/components/constraints/elements/DimensionBar";
import { GaugeSkeleton } from "@/components/constraints/elements/GaugeSkeleton";

interface ConstraintGaugeProps {
  sessionId: string;
}

export function ConstraintGauge({ sessionId }: ConstraintGaugeProps) {
  const { data, isPending, error } = useGradient(sessionId);

  // Subscribe to constraint_updated events so the component re-renders
  // when the store receives new events, prompting a query refetch.
  useWebSocketStore((s) => s.getEventsByType("constraint_updated"));

  if (isPending) return <GaugeSkeleton />;

  if (error) {
    return (
      <p className="text-sm text-[var(--muted-foreground)]">
        Could not load constraint status. Please try again.
      </p>
    );
  }

  if (!data?.dimensions || data.dimensions.length === 0) {
    return (
      <p className="text-sm text-[var(--muted-foreground)]">
        No constraints configured for this session.
      </p>
    );
  }

  return (
    <div className="space-y-4">
      {data.dimensions.map((dim) => (
        <DimensionBar key={dim.dimension} dimension={dim} />
      ))}
    </div>
  );
}
