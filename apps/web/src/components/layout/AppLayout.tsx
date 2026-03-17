// Copyright 2026 Terrene Foundation
// Licensed under the Apache License, Version 2.0

import { useEffect, useState } from "react";
import { Outlet } from "react-router-dom";

import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import { useWebSocketStore } from "@/services/websocket";
import { cn } from "@/lib/utils";

/**
 * Main application layout with sidebar, topbar, and content area.
 *
 * The sidebar collapses to an overlay on mobile (<768px) and is
 * permanently visible on tablet/desktop. The WebSocket connection
 * is established when the layout mounts and torn down on unmount.
 */
export function AppLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const wsConnect = useWebSocketStore((s) => s.connect);
  const wsDisconnect = useWebSocketStore((s) => s.disconnect);

  // Establish WebSocket connection on mount
  useEffect(() => {
    wsConnect();
    return () => {
      wsDisconnect();
    };
  }, [wsConnect, wsDisconnect]);

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Mobile overlay backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 md:hidden"
          onClick={() => setSidebarOpen(false)}
          onKeyDown={(e) => {
            if (e.key === "Escape") setSidebarOpen(false);
          }}
          role="button"
          tabIndex={-1}
          aria-label="Close sidebar"
        />
      )}

      {/* Sidebar */}
      <div
        className={cn(
          "fixed inset-y-0 left-0 z-50 w-64 transform transition-transform duration-200 md:relative md:translate-x-0",
          sidebarOpen ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <Sidebar />
      </div>

      {/* Main content area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        <Topbar onMenuToggle={() => setSidebarOpen((prev) => !prev)} />
        <main className="flex-1 overflow-y-auto p-4 md:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
