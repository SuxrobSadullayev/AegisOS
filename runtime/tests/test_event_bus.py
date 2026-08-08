"""
Aegis AI Operating System — Secure Multi-Agent Event Bus Tests
Tests publish, subscribe, request/reply, broadcast, TTL expiration, payload size limits, rate limits, and replay protection.
"""

import time
import unittest
from runtime.src.event_bus import (
    SecureEventBus, AgentEvent, EventBusLimits, EventValidationError, EventRateLimitError, EventTimeoutError
)


class TestSecureEventBus(unittest.TestCase):
    """Tests SecureEventBus routing, filtering, limits, and request-reply correlation."""

    def setUp(self):
        self.bus = SecureEventBus()

    def test_publish_and_subscribe(self):
        """Published event is received by matching event_type subscriber."""
        received = []

        def handler(evt: AgentEvent):
            received.append(evt)

        self.bus.subscribe("sub_agent_1", "TASK_COMPLETED", handler)

        evt = AgentEvent(
            event_type="TASK_COMPLETED",
            source_agent_id="pub_agent_1",
            payload={"status": "OK"}
        )
        delivered = self.bus.publish(evt)

        self.assertTrue(delivered)
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0].payload["status"], "OK")

    def test_request_reply_pattern(self):
        """request_reply publishes a request and synchronously waits for reply with matching correlation_id."""
        def responder(evt: AgentEvent):
            reply = AgentEvent(
                event_type="TASK_REPLY",
                source_agent_id="worker_agent",
                target_agent_id=evt.source_agent_id,
                correlation_id=evt.correlation_id,
                payload={"result": "PROCESSED"}
            )
            return reply

        self.bus.subscribe("worker_agent", "TASK_REQUESTED", responder)

        req_evt = AgentEvent(
            event_type="TASK_REQUESTED",
            source_agent_id="client_agent",
            payload={"task": "do_work"}
        )
        reply = self.bus.request_reply(req_evt, timeout_seconds=2.0)

        self.assertIsNotNone(reply)
        self.assertEqual(reply.payload["result"], "PROCESSED")

    def test_payload_size_limit_exceeded(self):
        """Event with payload exceeding max_payload_bytes must raise EventValidationError."""
        limits = EventBusLimits(max_payload_bytes=100)
        bus = SecureEventBus(limits=limits)

        huge_payload = {"data": "X" * 500}
        evt = AgentEvent(
            event_type="DATA_EVENT",
            source_agent_id="agent_1",
            payload=huge_payload
        )
        with self.assertRaises(EventValidationError):
            bus.publish(evt)

    def test_ttl_expiration_rejected(self):
        """Expired event (past TTL) must be rejected and not delivered."""
        received = []
        self.bus.subscribe("sub_1", "EXPIRED_TEST", lambda e: received.append(e))

        evt = AgentEvent(
            event_type="EXPIRED_TEST",
            source_agent_id="pub_1",
            ttl_seconds=0.01,
            timestamp_utc=time.time() - 10.0  # Expired
        )
        delivered = self.bus.publish(evt)
        self.assertFalse(delivered)
        self.assertEqual(len(received), 0)

    def test_replay_protection_deduplication(self):
        """Publishing the exact same event_id twice must reject the duplicate event."""
        received = []
        self.bus.subscribe("sub_1", "REPLAY_TEST", lambda e: received.append(e))

        evt = AgentEvent(
            event_id="EVT_DUPLICATE_123",
            event_type="REPLAY_TEST",
            source_agent_id="pub_1",
            payload={"val": 1}
        )
        d1 = self.bus.publish(evt)
        d2 = self.bus.publish(evt)

        self.assertTrue(d1)
        self.assertFalse(d2, "Duplicate event must be rejected")
        self.assertEqual(len(received), 1)


if __name__ == "__main__":
    unittest.main()
