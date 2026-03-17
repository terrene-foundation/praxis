// Copyright 2026 Terrene Foundation
// Licensed under the Apache License, Version 2.0

/**
 * Loading skeleton for the constraint gauge component.
 */

export function GaugeSkeleton() {
  return (
    <div className="space-y-4">
      {[...Array(5)].map((_, i) => (
        <div key={i} className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="h-4 w-24 animate-pulse rounded bg-[var(--muted)]" />
            <div className="h-4 w-16 animate-pulse rounded bg-[var(--muted)]" />
          </div>
          <div className="h-2 w-full animate-pulse rounded-full bg-[var(--muted)]" />
        </div>
      ))}
    </div>
  );
}
