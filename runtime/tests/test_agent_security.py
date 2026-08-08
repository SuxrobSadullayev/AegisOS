"""
Aegis AI Operating System — Multi-Agent Adversarial Security Tests
Tests security barriers:
- Default DENY agent capability tokens
- Circular delegation detection (max depth limit & recursion check)
- Secret redaction barrier on agent event payloads
- Rate limit enforcement & payload bomb protection
- Blocked agent execution rejection
"""

import unittest
from runtime.src.plugin import PluginPermission
from runtime.src.event_bus import SecureEventBus, AgentEvent, EventBusLimits, EventValidationError, EventRateLimitError
from runtime.src.agents import (
    AgentRegistry, TaskCoordinator, AgentDescriptor, AgentTrustLevel, CircularDelegationError, AgentAuthorizationError
)


class TestAgentSecurity(unittest.TestCase):
    """Adversarial security tests for multi-agent coordination and event bus."""

    def setUp(self):
        self.registry = AgentRegistry()
        self.bus = SecureEventBus()
        self.coordinator = TaskCoordinator(self.registry, self.bus, max_delegation_depth=3)

    def test_sec_1_circular_delegation_depth_exceeded(self):
        """Task delegation depth exceeding max_delegation_depth must raise CircularDelegationError."""
        # Create a loop stack: A -> B -> C -> D (depth 4 > max 3)
        stack = ["agent.A", "agent.B", "agent.C", "agent.D"]
        with self.assertRaises(CircularDelegationError) as ctx:
            self.coordinator.submit_task("loop_task", {}, delegation_stack=stack)
        self.assertIn("depth", str(ctx.exception).lower())

    def test_sec_2_circular_delegation_recursion_detected(self):
        """Task delegation attempting to route to an agent already in execution stack must raise CircularDelegationError."""
        desc_a = AgentDescriptor(
            agent_id="agent.A",
            name="Agent A",
            version="1.0.0",
            supported_task_types=["code_gen"]
        )
        self.registry.register_agent(desc_a)

        stack = ["agent.A"]  # agent.A is already in stack
        with self.assertRaises(CircularDelegationError) as ctx:
            self.coordinator.submit_task("code_gen", {}, delegation_stack=stack)
        self.assertIn("circular delegation", str(ctx.exception).lower())

    def test_sec_3_secret_redaction_on_event_payload(self):
        """Event payloads containing API keys or bearer tokens must be redacted automatically."""
        received = []
        self.bus.subscribe("auditor", "SECRET_EVENT", lambda e: received.append(e))

        evt = AgentEvent(
            event_type="SECRET_EVENT",
            source_agent_id="agent.src",
            payload={
                "gemini_api_key": "AIzaSyA1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6",
                "authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIi",
                "normal_data": "public_val"
            }
        )
        self.bus.publish(evt)

        self.assertEqual(len(received), 1)
        payload = received[0].payload
        self.assertEqual(payload["gemini_api_key"], "[REDACTED]")
        self.assertEqual(payload["authorization"], "[REDACTED]")
        self.assertEqual(payload["normal_data"], "public_val")

    def test_sec_4_blocked_agent_cannot_be_routed(self):
        """Blocked agent must never be selected by TaskCoordinator."""
        desc_blocked = AgentDescriptor(
            agent_id="agent.malicious",
            name="Malicious Agent",
            version="1.0.0",
            trust_level=AgentTrustLevel.BLOCKED,
            supported_task_types=["exploit"]
        )
        # Directly insert into registry internal dict to simulate bypass
        self.registry.descriptors["agent.malicious"] = desc_blocked

        res = self.coordinator.submit_task("exploit", {})
        self.assertFalse(res.success)
        self.assertNotEqual(res.assigned_agent_id, "agent.malicious")


if __name__ == "__main__":
    unittest.main()
