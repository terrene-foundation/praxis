# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""
WebSocket event streaming for real-time Praxis updates.

Broadcasts events to connected clients when session state changes,
constraints are updated, held actions are created/resolved, or
deliberation records are captured.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Event types
# ---------------------------------------------------------------------------

SESSION_STATE_CHANGED = "session_state_changed"
CONSTRAINT_UPDATED = "constraint_updated"
HELD_ACTION_CREATED = "held_action_created"
HELD_ACTION_RESOLVED = "held_action_resolved"
DELIBERATION_RECORDED = "deliberation_recorded"


# ---------------------------------------------------------------------------
# EventBroadcaster
# ---------------------------------------------------------------------------


_MAX_SUBSCRIBERS = 100
_MAX_QUEUE_SIZE = 1000


class EventBroadcaster:
    """Manages WebSocket event broadcasting to connected clients.

    Maintains a set of connected async queues (one per client) and
    pushes events to all of them. Clients subscribe by calling
    subscribe() and iterate over the returned async generator.

    Enforces a maximum subscriber limit and bounded per-subscriber
    queues to prevent unbounded memory growth.
    """

    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue] = set()

    def subscribe(self) -> asyncio.Queue:
        """Subscribe to events. Returns an asyncio.Queue to read from.

        The caller should read from this queue in a loop. When done,
        call unsubscribe() to clean up.

        Returns:
            An asyncio.Queue that receives event dicts.

        Raises:
            RuntimeError: If the maximum subscriber limit has been reached.
        """
        if len(self._subscribers) >= _MAX_SUBSCRIBERS:
            raise RuntimeError(
                f"Maximum WebSocket subscriber limit ({_MAX_SUBSCRIBERS}) reached. "
                "Try again later."
            )
        queue: asyncio.Queue = asyncio.Queue(maxsize=_MAX_QUEUE_SIZE)
        self._subscribers.add(queue)
        logger.debug("New WebSocket subscriber (total: %d)", len(self._subscribers))
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        """Remove a subscriber queue.

        Args:
            queue: The queue returned by subscribe().
        """
        self._subscribers.discard(queue)
        logger.debug("WebSocket subscriber removed (total: %d)", len(self._subscribers))

    async def broadcast(self, event_type: str, data: dict[str, Any]) -> None:
        """Broadcast an event to all connected subscribers.

        Args:
            event_type: The event type identifier.
            data: The event data payload.
        """
        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        }

        disconnected: list[asyncio.Queue] = []
        for queue in self._subscribers:
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                logger.warning("WebSocket subscriber queue full — dropping event")
                disconnected.append(queue)

        for q in disconnected:
            self._subscribers.discard(q)

    @property
    def subscriber_count(self) -> int:
        """Number of currently connected subscribers."""
        return len(self._subscribers)


# Module-level broadcaster singleton
_broadcaster: EventBroadcaster | None = None


def get_broadcaster() -> EventBroadcaster:
    """Get the module-level EventBroadcaster singleton."""
    global _broadcaster
    if _broadcaster is None:
        _broadcaster = EventBroadcaster()
    return _broadcaster
