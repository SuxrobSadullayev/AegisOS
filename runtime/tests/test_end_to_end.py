import time
import unittest
from runtime.src.config import AegisConfig, EpistemicState, EvidenceLevel, QualityStatus
from runtime.src.gateway import MockProvider
from runtime.src.session import SessionManager, SessionContext, SessionState
from runtime.src.orchestrator import RuntimeOrchestrator, OrchestratorContext


class TestEndToEndMultiTurnSession(unittest.TestCase):
    """Multi-Turn Session Integration Scenario (Turn 1 to 4)."""

    def setUp(self):
        self.config = AegisConfig()
        self.provider = MockProvider(self.config)
        self.orchestrator = RuntimeOrchestrator(self.config, self.provider)
        self.session_id = f"SESS_E2E_MULTITURN_{time.time_ns()}"


    def test_multi_turn_conversation_flow(self):
        """Executes 4 consecutive turns in a single session and verifies state persistence."""

        # Turn 1: Project setup
        prompt_1 = "Men Python backend loyiha yaratmoqchiman."
        ctx_1 = self.orchestrator.run(prompt_1, session_id=self.session_id)

        self.assertIsNotNone(ctx_1.model_response)
        self.assertEqual(ctx_1.quality_result.status, QualityStatus.PASS)

        # Retrieve session snapshot from SessionManager
        sess = self.orchestrator.session_manager.get_session(self.session_id)
        self.assertIsNotNone(sess)
        self.assertEqual(len(sess.history.messages), 2)  # User + Assistant
        self.assertEqual(sess.history.messages[0].content, prompt_1)

        # Turn 2: Authentication
        prompt_2 = "Unda authentication qanday tashkil qilinadi?"
        ctx_2 = self.orchestrator.run(prompt_2, session_id=self.session_id)

        self.assertIsNotNone(ctx_2.model_response)
        # History in context_2 should contain previous turn (2 messages)
        self.assertEqual(len(ctx_2.conversation_history), 2)
        sess = self.orchestrator.session_manager.get_session(self.session_id)
        self.assertEqual(len(sess.history.messages), 4)  # 2 Users + 2 Assistants

        # Turn 3: Database architecture
        prompt_3 = "Oldingi qarorimiz asosida database architecture taklif qil."
        ctx_3 = self.orchestrator.run(prompt_3, session_id=self.session_id)

        self.assertIsNotNone(ctx_3.model_response)
        self.assertEqual(len(ctx_3.conversation_history), 4)
        sess = self.orchestrator.session_manager.get_session(self.session_id)
        self.assertEqual(len(sess.history.messages), 6)

        # Turn 4: Security risk analysis
        prompt_4 = "Qaysi joylari xavfli?"
        ctx_4 = self.orchestrator.run(prompt_4, session_id=self.session_id)

        self.assertIsNotNone(ctx_4.model_response)
        self.assertEqual(len(ctx_4.conversation_history), 6)
        sess = self.orchestrator.session_manager.get_session(self.session_id)
        self.assertEqual(len(sess.history.messages), 8)

        # Verify session state, last access, and checkpoint snapshot
        self.assertEqual(sess.state, SessionState.ACTIVE)
        self.assertGreater(sess.last_accessed_utc, 0.0)

    def test_session_restoration_from_persistence(self):
        """Verifies session restoration after orchestrator restart."""
        sess_id = f"SESS_RESTORE_{time.time_ns()}"
        prompt_1 = "Initial prompt before simulated restart"
        self.orchestrator.run(prompt_1, session_id=sess_id)

        # Create new orchestrator instance to simulate process restart
        new_orchestrator = RuntimeOrchestrator(self.config, self.provider)
        restored_sess = new_orchestrator.session_manager.get_session(sess_id)

        self.assertIsNotNone(restored_sess)
        self.assertEqual(restored_sess.history.messages[0].content, prompt_1)

        # Execute turn 2 on restored session
        prompt_2 = "Turn 2 after restore"
        ctx_2 = new_orchestrator.run(prompt_2, session_id=sess_id)
        self.assertEqual(len(ctx_2.conversation_history), 2)

    def test_token_pruning_under_large_history(self):
        """Verifies token pruning when context window token budget is exceeded."""
        sess_id = f"SESS_PRUNE_{time.time_ns()}"
        # Create session with small token budget
        sess = self.orchestrator.session_manager.create_session("prune_user", session_id=sess_id)
        sess.context_window.max_token_budget = 50  # Very small budget

        # Add multiple long messages
        for i in range(10):
            self.orchestrator.session_manager.add_user_message(sess_id, f"Long message {i} " * 20)
            self.orchestrator.session_manager.add_assistant_message(sess_id, f"Long response {i} " * 20)

        pruned_sess = self.orchestrator.session_manager.get_session(sess_id)
        # History messages must be pruned to fit budget
        self.assertLess(len(pruned_sess.history.messages), 20)



if __name__ == "__main__":
    unittest.main()
