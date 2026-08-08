"""
Aegis AI Operating System — Multi-Agent Coordination Tests
Tests deterministic task routing, capability matching, task submission, and multi-agent workflow execution.
"""

import unittest
from typing import Dict, Any
from runtime.src.plugin import PluginPermission
from runtime.src.event_bus import SecureEventBus
from runtime.src.agents import (
    AgentRegistry, TaskCoordinator, AgentInterface, AgentDescriptor,
    AgentCapabilityToken, AgentTrustLevel, TaskResult
)


class SampleAgent(AgentInterface):
    """Sample in-process test agent."""
    def __init__(self, agent_id: str, task_type: str):
        self._descriptor = AgentDescriptor(
            agent_id=agent_id,
            name=f"Sample {agent_id}",
            version="1.0.0",
            capabilities=["CODE_GEN"],
            permissions=[PluginPermission.FILESYSTEM_READ],
            trust_level=AgentTrustLevel.TRUSTED,
            supported_task_types=[task_type]
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
        return {"status": "SUCCESS", "input_received": payload.get("data")}

    def shutdown(self) -> bool:
        return True


class TestAgentCoordination(unittest.TestCase):
    """Tests multi-agent task routing and execution."""

    def setUp(self):
        self.registry = AgentRegistry()
        self.bus = SecureEventBus()
        self.coordinator = TaskCoordinator(self.registry, self.bus)

        self.agent1 = SampleAgent("agent.code_generator", "generate_code")
        self.registry.register_agent(self.agent1.get_descriptor(), self.agent1)

    def test_submit_task_success(self):
        """Submitting a task routes it to the matching agent and returns TaskResult with success=True."""
        res = self.coordinator.submit_task("generate_code", {"data": "def foo(): pass"})

        self.assertTrue(res.success)
        self.assertEqual(res.assigned_agent_id, "agent.code_generator")
        self.assertEqual(res.result["status"], "SUCCESS")
        self.assertEqual(res.result["input_received"], "def foo(): pass")

    def test_submit_task_no_matching_agent(self):
        """Submitting a task with no registered matching agent returns failure result gracefully without crash."""
        res = self.coordinator.submit_task("unsupported_task_type", {})

        self.assertFalse(res.success)
        self.assertIn("No matching agent", res.error_message)


if __name__ == "__main__":
    unittest.main()
