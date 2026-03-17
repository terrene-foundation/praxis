// Copyright 2026 Terrene Foundation
// Licensed under the Apache License, Version 2.0

import { Bell, Circle, Menu, User as UserIcon } from "lucide-react";

import { useAuthStore } from "@/stores/auth";
import { useWebSocketStore } from "@/services/websocket";
import { cn } from "@/lib/utils";

interface TopbarProps {
  onMenuToggle?: () => void;
}

export function Topbar({ onMenuToggle }: TopbarProps) {
  const user = useAuthStore((s) => s.user);
  const wsConnected = useWebSocketStore((s) => s.connected);
  const eventCount = useWebSocketStore((s) => s.events.length);

  return (
    <header className="flex h-16 items-center justify-between border-b border-[var(--border)] bg-[var(--background)] px-4 md:px-6">
      {/* Left: mobile menu + breadcrumb area */}
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onMenuToggle}
          className="rounded-md p-2 text-[var(--muted-foreground)] hover:bg-[var(--accent)] md:hidden"
          aria-label="Toggle menu"
        >
          <Menu className="h-5 w-5" />
        </button>

        {/* Connection status */}
        <div className="flex items-center gap-2 text-sm text-[var(--muted-foreground)]">
          <Circle
            className={cn(
              "h-2 w-2 fill-current",
              wsConnected
                ? "text-[var(--trust-auto)]"
                : "text-[var(--trust-blocked)]",
            )}
          />
          <span className="hidden sm:inline">
            {wsConnected ? "Connected" : "Disconnected"}
          </span>
        </div>
      </div>

      {/* Right: notifications + user */}
      <div className="flex items-center gap-3">
        {/* Notification bell */}
        <button
          type="button"
          className="relative rounded-md p-2 text-[var(--muted-foreground)] hover:bg-[var(--accent)]"
          aria-label="Notifications"
        >
          <Bell className="h-5 w-5" />
          {eventCount > 0 && (
            <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-[var(--trust-held)] px-1 text-[10px] font-bold text-white">
              {eventCount > 99 ? "99+" : eventCount}
            </span>
          )}
        </button>

        {/* User info */}
        {user && (
          <div className="flex items-center gap-2 rounded-md px-3 py-1.5">
            <div className="flex h-7 w-7 items-center justify-center rounded-full bg-[var(--primary)] text-[var(--primary-foreground)]">
              <UserIcon className="h-4 w-4" />
            </div>
            <div className="hidden flex-col sm:flex">
              <span className="text-sm font-medium leading-tight">
                {user.username}
              </span>
              <span className="text-xs capitalize text-[var(--muted-foreground)]">
                {user.role}
              </span>
            </div>
          </div>
        )}
      </div>
    </header>
  );
}
