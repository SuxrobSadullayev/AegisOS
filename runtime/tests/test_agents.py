"""
Aegis AI Operating System — Agent Registry & Descriptor Tests
Tests agent registration, descriptor metadata, FSM state transitions, list, unregister, and capability matching.
"""

import unittest
from runtime.src.plugin import PluginPermission
from runtime.src.agents import (
    AgentRegistry, AgentDescriptor, AgentState, AgentTrustLevel, AgentAuthorizationError
)


class TestAgentRegistry(unittest.TestCase):
    """Tests AgentRegistry registration, FSM transitions, and discovery."""

    def setUp(self):
        self.registry = AgentRegistry()

        self.agent_desc = AgentDescriptor(
            agent_id="agent.code_analyst",
            name="Code Analyst Agent",
            version="1.0.0",
            capabilities=["PYTHON_ANALYSIS", "SECURITY_AUDIT"],
            permissions=[PluginPermission.FILESYSTEM_READ],
            trust_level=AgentTrustLevel.TRUSTED,
            supported_task_types=["code_analysis", "security_scan"]
        )

    def test_register_and_get_agent(self):
        """Registering an agent descriptor stores it in registry with REGISTERED state."""
        res = self.registry.register_agent(self.agent_desc)
        self.assertTrue(res)

        desc = self.registry.get_descriptor("agent.code_analyst")
        self.assertIsNotNone(desc)
        self.assertEqual(desc.name, "Code Analyst Agent")
        self.assertEqual(self.registry.get_state("agent.code_analyst"), AgentState.REGISTERED)

    def test_transition_state(self):
        """Transitioning agent state updates FSM state cleanly."""
        self.registry.register_agent(self.agent_desc)
        self.registry.transition_state("agent.code_analyst", AgentState.READY)
        self.assertEqual(self.registry.get_state("agent.code_analyst"), AgentState.READY)

    def test_blocked_agent_registration_fails(self):
        """Attempting to register a BLOCKED agent must raise AgentAuthorizationError."""
        blocked_desc = AgentDescriptor(
            agent_id="agent.blocked",
            name="Blocked Agent",
            version="1.0.0",
            trust_level=AgentTrustLevel.BLOCKED
        )
        with self.assertRaises(AgentAuthorizationError):
            self.registry.register_agent(blocked_desc)

    def test_find_matching_agents(self):
        """find_matching_agents returns matching agents sorted deterministically by trust level and priority."""
        self.registry.register_agent(self.agent_desc)

        untrusted_desc = AgentDescriptor(
            agent_id="agent.untrusted_analyst",
            name="Untrusted Analyst",
            version="1.0.0",
            capabilities=["PYTHON_ANALYSIS"],
            trust_level=AgentTrustLevel.UNTRUSTED,
            supported_task_types=["code_analysis"]
        )
        self.registry.register_agent(untrusted_desc)

        matches = self.registry.find_matching_agents("code_analysis", ["PYTHON_ANALYSIS"])
        self.assertEqual(len(matches), 2)
        # TRUSTED comes before UNTRUSTED deterministically
        self.assertEqual(matches[0].agent_id, "agent.code_analyst")
        self.assertEqual(matches[1].agent_id, "agent.untrusted_analyst")

    def test_unregister_agent(self):
        """Unregistering an agent removes it from registry."""
        self.registry.register_agent(self.agent_desc)
        self.assertTrue(self.registry.unregister_agent("agent.code_analyst"))
        self.assertIsNone(self.registry.get_descriptor("agent.code_analyst"))


if __name__ == "__main__":
    unittest.main()
