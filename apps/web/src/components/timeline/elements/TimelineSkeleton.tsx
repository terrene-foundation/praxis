// Copyright 2026 Terrene Foundation
// Licensed under the Apache License, Version 2.0

/**
 * Loading skeleton for the deliberation timeline.
 */

export function TimelineSkeleton() {
  return (
    <div className="space-y-4">
      {[...Array(5)].map((_, i) => (
        <div key={i} className="flex gap-4">
          <div className="flex flex-col items-center">
            <div className="h-3 w-3 animate-pulse rounded-full bg-[var(--muted)]" />
            {i < 4 && (
              <div className="h-16 w-0.5 animate-pulse bg-[var(--muted)]" />
            )}
          </div>
          <div className="flex-1 space-y-2 pb-4">
            <div className="h-4 w-32 animate-pulse rounded bg-[var(--muted)]" />
            <div className="h-3 w-full animate-pulse rounded bg-[var(--muted)]" />
            <div className="h-3 w-20 animate-pulse rounded bg-[var(--muted)]" />
          </div>
        </div>
      ))}
    </div>
  );
}
