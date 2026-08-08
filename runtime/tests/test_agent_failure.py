"""
Aegis AI Operating System — Multi-Agent Failure & Crash Recovery Tests
Tests agent execution failure, bounded retries, timeout handling, and runtime isolation.
"""

import unittest
from typing import Dict, Any
from runtime.src.event_bus import SecureEventBus
from runtime.src.agents import (
    AgentRegistry, TaskCoordinator, AgentInterface, AgentDescriptor,
    AgentCapabilityToken, AgentTrustLevel, TaskResult
)


class FailingAgent(AgentInterface):
    """Agent that always raises an exception during task execution."""
    def __init__(self, agent_id: str):
        self._descriptor = AgentDescriptor(
            agent_id=agent_id,
            name="Failing Agent",
            version="1.0.0",
            trust_level=AgentTrustLevel.TRUSTED,
            supported_task_types=["flaky_task"]
        )

    def get_descriptor(self) -> AgentDescriptor:
        return self._descriptor

    def initialize(self, ctx: Dict[str, Any]) -> bool:
        return True

    def execute_task(
        self,
        task_id: str,
        task_type: str,
        payload: Dict[str, Any],
        token: AgentCapabilityToken
    ) -> Dict[str, Any]:
        raise RuntimeError("SIMULATED AGENT CRASH")

    def shutdown(self) -> bool:
        return True


class TestAgentFailure(unittest.TestCase):
    """Tests failure recovery and runtime isolation when agents crash or fail."""

    def setUp(self):
        self.registry = AgentRegistry()
        self.bus = SecureEventBus()
        self.coordinator = TaskCoordinator(self.registry, self.bus, max_retries=2)

        self.failing_agent = FailingAgent("agent.failing")
        self.registry.register_agent(self.failing_agent.get_descriptor(), self.failing_agent)

    def test_agent_crash_retries_and_graceful_failure(self):
        """Failing agent task execution is retried max_retries times and returns TaskResult(success=False) without crashing Aegis."""
        res = self.coordinator.submit_task("flaky_task", {"data": "test"})

        self.assertFalse(res.success)
        self.assertEqual(res.assigned_agent_id, "agent.failing")
        self.assertIn("SIMULATED AGENT CRASH", res.error_message)
        # Verify failure count was incremented for each retry attempt
        self.assertEqual(self.registry.failure_counts["agent.failing"], 2)


if __name__ == "__main__":
    unittest.main()
