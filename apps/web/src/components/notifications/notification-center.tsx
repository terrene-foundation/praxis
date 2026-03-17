// Copyright 2026 Terrene Foundation
// Licensed under the Apache License, Version 2.0

/**
 * M12-07: Notification System
 *
 * In-app notification center with browser notification support.
 * Monitors WebSocket events for held actions and provides
 * approval reminders. Renders as a dropdown from the bell icon.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { Bell, Check, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useWebSocketStore } from "@/services/websocket";
import { formatRelativeTime } from "@/lib/format";
import type { PraxisEvent } from "@/types/api";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Browser notification permission
// ---------------------------------------------------------------------------

function requestNotificationPermission() {
  if ("Notification" in window && Notification.permission === "default") {
    void Notification.requestPermission();
  }
}

function sendBrowserNotification(title: string, body: string) {
  if ("Notification" in window && Notification.permission === "granted") {
    new Notification(title, { body, icon: "/praxis-icon.png" });
  }
}

// ---------------------------------------------------------------------------
// Notification item
// ---------------------------------------------------------------------------

interface NotificationItem {
  id: string;
  title: string;
  body: string;
  timestamp: string;
  read: boolean;
  type: "held_action" | "resolution" | "info";
}

function eventToNotification(event: PraxisEvent): NotificationItem {
  const data = event.data as Record<string, string>;

  switch (event.type) {
    case "held_action_created":
      return {
        id: `${event.timestamp}-held`,
        title: "Action needs your approval",
        body: data.action ?? "A held action requires review",
        timestamp: event.timestamp,
        read: false,
        type: "held_action",
      };
    case "held_action_resolved":
      return {
        id: `${event.timestamp}-resolved`,
        title: "Action resolved",
        body: `Action was ${data.resolution ?? "resolved"}`,
        timestamp: event.timestamp,
        read: false,
        type: "resolution",
      };
    default:
      return {
        id: `${event.timestamp}-${event.type}`,
        title: event.type.replace(/_/g, " "),
        body: "Session event occurred",
        timestamp: event.timestamp,
        read: false,
        type: "info",
      };
  }
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function NotificationCenter() {
  const [open, setOpen] = useState(false);
  const [readIds, setReadIds] = useState<Set<string>>(new Set());
  const dropdownRef = useRef<HTMLDivElement>(null);

  const events = useWebSocketStore((s) => s.events);
  const prevEventCountRef = useRef(events.length);

  // Request notification permission on mount
  useEffect(() => {
    requestNotificationPermission();
  }, []);

  // Send browser notification for new held actions
  useEffect(() => {
    if (events.length > prevEventCountRef.current) {
      const newEvents = events.slice(
        0,
        events.length - prevEventCountRef.current,
      );
      for (const event of newEvents) {
        if (event.type === "held_action_created") {
          const data = event.data as Record<string, string>;
          sendBrowserNotification(
            "Action needs approval",
            data.action ?? "A held action requires your review",
          );
        }
      }
    }
    prevEventCountRef.current = events.length;
  }, [events]);

  // Close on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(e.target as Node)
      ) {
        setOpen(false);
      }
    }
    if (open) {
      document.addEventListener("mousedown", handleClick);
      return () => document.removeEventListener("mousedown", handleClick);
    }
  }, [open]);

  // Build notifications from relevant events
  const relevantEvents = events.filter(
    (e) =>
      e.type === "held_action_created" ||
      e.type === "held_action_resolved" ||
      e.type === "session_state_changed",
  );
  const notifications = relevantEvents.slice(0, 20).map(eventToNotification);
  const unreadCount = notifications.filter((n) => !readIds.has(n.id)).length;

  const markAllRead = useCallback(() => {
    setReadIds(new Set(notifications.map((n) => n.id)));
  }, [notifications]);

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Bell trigger */}
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="relative rounded-md p-2 text-[var(--muted-foreground)] hover:bg-[var(--accent)]"
        aria-label="Notifications"
      >
        <Bell className="h-5 w-5" />
        {unreadCount > 0 && (
          <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-[var(--trust-held)] px-1 text-[10px] font-bold text-white">
            {unreadCount > 99 ? "99+" : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown */}
      {open && (
        <div className="absolute right-0 top-full z-50 mt-2 w-80 rounded-lg border border-[var(--border)] bg-[var(--card)] shadow-lg">
          {/* Header */}
          <div className="flex items-center justify-between border-b border-[var(--border)] px-4 py-3">
            <span className="text-sm font-semibold">Notifications</span>
            {unreadCount > 0 && (
              <Button variant="ghost" size="xs" onClick={markAllRead}>
                <Check className="h-3 w-3" />
                Mark all read
              </Button>
            )}
          </div>

          {/* List */}
          <div className="max-h-80 overflow-y-auto">
            {notifications.length === 0 ? (
              <p className="px-4 py-8 text-center text-sm text-[var(--muted-foreground)]">
                No notifications yet
              </p>
            ) : (
              notifications.map((notification) => (
                <div
                  key={notification.id}
                  className={cn(
                    "flex items-start gap-3 border-b border-[var(--border)] px-4 py-3 last:border-0",
                    !readIds.has(notification.id) && "bg-[var(--accent)]",
                  )}
                >
                  <div
                    className={cn(
                      "mt-1 h-2 w-2 shrink-0 rounded-full",
                      notification.type === "held_action"
                        ? "bg-[var(--trust-held)]"
                        : notification.type === "resolution"
                          ? "bg-[var(--trust-auto)]"
                          : "bg-[var(--muted-foreground)]",
                    )}
                  />
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium">{notification.title}</p>
                    <p className="text-xs text-[var(--muted-foreground)]">
                      {notification.body}
                    </p>
                    <p className="mt-0.5 text-xs text-[var(--muted-foreground)]">
                      {formatRelativeTime(notification.timestamp)}
                    </p>
                  </div>
                  {!readIds.has(notification.id) && (
                    <button
                      type="button"
                      onClick={() =>
                        setReadIds(new Set([...readIds, notification.id]))
                      }
                      className="shrink-0 text-[var(--muted-foreground)] hover:text-[var(--foreground)]"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
