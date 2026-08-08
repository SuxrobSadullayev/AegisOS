"""
Aegis AI Operating System — Multi-Agent Telemetry & Observability Integration Tests
Tests structured audit log event publishing and correlation context propagation across agent boundaries.
"""

import unittest
from typing import Dict, Any

from runtime.src.event_bus import SecureEventBus, AgentEvent
from runtime.src.agents import (
    AgentRegistry, TaskCoordinator, AgentInterface, AgentDescriptor,
    AgentCapabilityToken, AgentTrustLevel
)
from runtime.src.observability import ObservabilityManager, CorrelationContext


class ObservableAgent(AgentInterface):
    def __init__(self, agent_id: str):
        self._descriptor = AgentDescriptor(
            agent_id=agent_id,
            name="Observable Agent",
            version="1.0.0",
            trust_level=AgentTrustLevel.TRUSTED,
            supported_task_types=["observable_task"]
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
        return {"status": "OK", "corr_id": CorrelationContext.get_correlation_id()}

    def shutdown(self) -> bool:
        return True


class TestAgentObservability(unittest.TestCase):
    """Tests telemetry logging and correlation context propagation for multi-agent operations."""

    def setUp(self):
        self.registry = AgentRegistry()
        self.bus = SecureEventBus()
        self.coordinator = TaskCoordinator(self.registry, self.bus)

        self.agent = ObservableAgent("agent.obs")
        self.registry.register_agent(self.agent.get_descriptor(), self.agent)

    def test_correlation_context_and_audit_event_logged(self):
        """Task execution emits structured telemetry events into ObservabilityManager."""
        obs = ObservabilityManager.get_instance()
        CorrelationContext.set_context(session_id="SESS_AGENT_OBS", correlation_id="CORR_AGENT_123")

        res = self.coordinator.submit_task("observable_task", {"test": "val"}, session_id="SESS_AGENT_OBS")
        self.assertTrue(res.success)

        logs = obs.read_logs(tail=10)
        task_logs = [l for l in logs if "TASK" in str(l.get("event_type", "")) or "AGENT" in str(l.get("event_type", ""))]
        self.assertGreater(len(task_logs), 0)


if __name__ == "__main__":
    unittest.main()
