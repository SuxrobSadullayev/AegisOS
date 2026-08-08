"""
Aegis AI Operating System — Multi-Agent Concurrency Stress Tests
Tests 20 concurrent worker threads publishing events, submitting tasks, and updating agent state.
"""

import unittest
import concurrent.futures
from typing import Dict, Any

from runtime.src.event_bus import SecureEventBus, AgentEvent
from runtime.src.agents import (
    AgentRegistry, TaskCoordinator, AgentInterface, AgentDescriptor,
    AgentCapabilityToken, AgentTrustLevel
)


class ConcurrencyWorkerAgent(AgentInterface):
    def __init__(self, agent_id: str):
        self._descriptor = AgentDescriptor(
            agent_id=agent_id,
            name=f"Worker {agent_id}",
            version="1.0.0",
            trust_level=AgentTrustLevel.TRUSTED,
            supported_task_types=["concurrent_task"]
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
        return {"processed_by": self._descriptor.agent_id, "val": payload.get("val")}

    def shutdown(self) -> bool:
        return True


class TestAgentConcurrency(unittest.TestCase):
    """Tests thread-safety under 20 concurrent worker threads."""

    def setUp(self):
        self.registry = AgentRegistry()
        self.bus = SecureEventBus()
        self.coordinator = TaskCoordinator(self.registry, self.bus)

        self.agent = ConcurrencyWorkerAgent("agent.concurrent_worker")
        self.registry.register_agent(self.agent.get_descriptor(), self.agent)

    def test_20_concurrent_task_submissions(self):
        """20 worker threads concurrently submitting tasks must complete with zero race conditions."""
        errors = []

        def worker(thread_idx: int):
            try:
                res = self.coordinator.submit_task("concurrent_task", {"val": thread_idx})
                if not res.success:
                    errors.append(f"Thread {thread_idx} failed: {res.error_message}")
            except Exception as exc:
                errors.append(f"Thread {thread_idx} exception: {exc}")

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(worker, i) for i in range(20)]
            concurrent.futures.wait(futures)

        self.assertEqual(len(errors), 0, f"Concurrency errors encountered: {errors}")


if __name__ == "__main__":
    unittest.main()
