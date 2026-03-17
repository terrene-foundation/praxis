// Copyright 2026 Terrene Foundation
// Licensed under the Apache License, Version 2.0

/**
 * WebSocket service using Zustand for real-time Praxis events.
 *
 * Connects to the Praxis API WebSocket endpoint and manages event state.
 * Events include session state changes, constraint updates, held action
 * creation/resolution, and deliberation records.
 */

import { create } from "zustand";

import type { PraxisEvent, PraxisEventType } from "@/types/api";

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

const WS_BASE = import.meta.env.VITE_PRAXIS_WS_URL || "ws://localhost:8000";
const MAX_EVENTS = 500;
const RECONNECT_DELAY_MS = 3000;
const MAX_RECONNECT_ATTEMPTS = 10;

// ---------------------------------------------------------------------------
// Store interface
// ---------------------------------------------------------------------------

interface WebSocketState {
  /** Whether the WebSocket is currently connected */
  connected: boolean;
  /** Buffered events (most recent first, capped at MAX_EVENTS) */
  events: PraxisEvent[];
  /** Number of reconnect attempts since last successful connection */
  reconnectAttempts: number;
  /** Connect to the WebSocket server */
  connect: (url?: string) => void;
  /** Disconnect from the WebSocket server */
  disconnect: () => void;
  /** Clear all buffered events */
  clearEvents: () => void;
  /** Get events filtered by type */
  getEventsByType: (type: PraxisEventType) => PraxisEvent[];
}

// ---------------------------------------------------------------------------
// Store implementation
// ---------------------------------------------------------------------------

let ws: WebSocket | null = null;
let reconnectTimer: ReturnType<typeof setTimeout> | null = null;

export const useWebSocketStore = create<WebSocketState>((set, get) => ({
  connected: false,
  events: [],
  reconnectAttempts: 0,

  connect: (url?: string) => {
    // Prevent duplicate connections
    if (
      ws &&
      (ws.readyState === WebSocket.OPEN ||
        ws.readyState === WebSocket.CONNECTING)
    ) {
      return;
    }

    const wsUrl = url || `${WS_BASE}/ws/events`;

    try {
      // Include auth token if available
      const token = localStorage.getItem("praxis_token");
      const fullUrl = token
        ? `${wsUrl}?token=${encodeURIComponent(token)}`
        : wsUrl;

      ws = new WebSocket(fullUrl);

      ws.onopen = () => {
        set({ connected: true, reconnectAttempts: 0 });
      };

      ws.onmessage = (event) => {
        try {
          const parsed = JSON.parse(event.data as string) as PraxisEvent;
          set((state) => ({
            events: [parsed, ...state.events].slice(0, MAX_EVENTS),
          }));
        } catch {
          // Ignore malformed messages
        }
      };

      ws.onclose = () => {
        set({ connected: false });
        ws = null;

        // Auto-reconnect with backoff
        const attempts = get().reconnectAttempts;
        if (attempts < MAX_RECONNECT_ATTEMPTS) {
          const delay = RECONNECT_DELAY_MS * Math.pow(1.5, attempts);
          reconnectTimer = setTimeout(() => {
            set({ reconnectAttempts: attempts + 1 });
            get().connect(url);
          }, delay);
        }
      };

      ws.onerror = () => {
        // onclose will fire after onerror, so reconnect is handled there
      };
    } catch {
      set({ connected: false });
    }
  },

  disconnect: () => {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }
    if (ws) {
      ws.close();
      ws = null;
    }
    set({ connected: false, reconnectAttempts: 0 });
  },

  clearEvents: () => {
    set({ events: [] });
  },

  getEventsByType: (type: PraxisEventType) => {
    return get().events.filter((e) => e.type === type);
  },
}));
