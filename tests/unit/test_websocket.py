# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""Unit tests for praxis.api.websocket — event broadcasting with bounded queues."""

import asyncio

import pytest


class TestEventBroadcasterBounds:
    """Test bounded subscriber queues and subscriber limits."""

    def test_subscribe_creates_bounded_queue(self):
        from praxis.api.websocket import EventBroadcaster, _MAX_QUEUE_SIZE

        broadcaster = EventBroadcaster()
        queue = broadcaster.subscribe()
        assert queue.maxsize == _MAX_QUEUE_SIZE
        broadcaster.unsubscribe(queue)

    def test_max_subscriber_limit_enforced(self):
        from praxis.api.websocket import EventBroadcaster, _MAX_SUBSCRIBERS

        broadcaster = EventBroadcaster()
        queues = []
        for _ in range(_MAX_SUBSCRIBERS):
            queues.append(broadcaster.subscribe())

        with pytest.raises(RuntimeError, match="Maximum WebSocket subscriber limit"):
            broadcaster.subscribe()

        # Clean up
        for q in queues:
            broadcaster.unsubscribe(q)

    def test_unsubscribe_frees_slot(self):
        from praxis.api.websocket import EventBroadcaster, _MAX_SUBSCRIBERS

        broadcaster = EventBroadcaster()
        queues = []
        for _ in range(_MAX_SUBSCRIBERS):
            queues.append(broadcaster.subscribe())

        # At limit — remove one
        broadcaster.unsubscribe(queues.pop())

        # Should now be able to subscribe again
        new_queue = broadcaster.subscribe()
        assert new_queue is not None
        broadcaster.unsubscribe(new_queue)

        # Clean up
        for q in queues:
            broadcaster.unsubscribe(q)

    @pytest.mark.asyncio
    async def test_broadcast_drops_events_for_full_queue(self):
        from praxis.api.websocket import EventBroadcaster

        broadcaster = EventBroadcaster()
        queue = broadcaster.subscribe()

        # Fill the queue to capacity
        for i in range(queue.maxsize):
            await broadcaster.broadcast("test_event", {"index": i})

        # Next broadcast should not block — it drops the event
        await broadcaster.broadcast("test_event", {"index": "overflow"})

        # Queue should still have maxsize items (the original ones)
        assert queue.qsize() == queue.maxsize

    def test_subscriber_count_tracks_correctly(self):
        from praxis.api.websocket import EventBroadcaster

        broadcaster = EventBroadcaster()
        assert broadcaster.subscriber_count == 0

        q1 = broadcaster.subscribe()
        assert broadcaster.subscriber_count == 1

        q2 = broadcaster.subscribe()
        assert broadcaster.subscriber_count == 2

        broadcaster.unsubscribe(q1)
        assert broadcaster.subscriber_count == 1

        broadcaster.unsubscribe(q2)
        assert broadcaster.subscriber_count == 0
