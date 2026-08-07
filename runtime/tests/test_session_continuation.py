"""
Session Continuation, Memory Persistence & Crash Recovery Tests for Aegis AI OS.
Verifies multi-turn session continuation, claim graph persistence, crash recovery,
memory isolation, and token budget pruning.
"""

import time
import unittest
from runtime.src.config import AegisConfig, EpistemicState, EvidenceLevel
from runtime.src.gateway import MockProvider
from runtime.src.session import SessionManager, SessionState
from runtime.src.orchestrator import RuntimeOrchestrator


class TestSessionContinuationAndRecovery(unittest.TestCase):
    """Tests session state continuation, memory, claims, and crash recovery."""

    def setUp(self):
        self.config = AegisConfig()
        self.provider = MockProvider(self.config)
        self.orchestrator = RuntimeOrchestrator(self.config, self.provider)

    def test_session_multi_turn_history_accumulation(self):
        """1. Verifies message accumulation over 5 turns."""
        sess_id = f"SESS_CONT_{time.time_ns()}"
        for turn in range(1, 6):
            ctx = self.orchestrator.run(f"Turn {turn} task prompt", session_id=sess_id)
            self.assertEqual(len(ctx.conversation_history), (turn - 1) * 2)

        sess = self.orchestrator.session_manager.get_session(sess_id)
        self.assertEqual(len(sess.history.messages), 10)  # 5 user + 5 assistant

    def test_session_claim_dag_persistence(self):
        """2. Verifies epistemic claim DAG persists inside session memory."""
        sess_id = f"SESS_CLAIMS_{time.time_ns()}"
        sess = self.orchestrator.session_manager.create_session("dev_user", session_id=sess_id)
        sess.memory.epistemic_claims.add_claim(
            claim_id="CLM-1",
            statement="FastAPI authentication claim",
            state="VERIFIED_FACT",
            evidence_level=5
        )

        self.orchestrator.session_manager.persistence.save_snapshot(sess)

        # Restore session
        new_session_mgr = SessionManager(self.config)
        restored = new_session_mgr.get_session(sess_id)
        self.assertIsNotNone(restored)
        self.assertEqual(len(restored.memory.epistemic_claims.claims), 1)

    def test_session_memory_isolation_between_users(self):
        """3. Verifies context memory isolation between distinct sessions."""
        sess_1 = f"SESS_USER_A_{time.time_ns()}"
        sess_2 = f"SESS_USER_B_{time.time_ns()}"

        self.orchestrator.run("User A prompt", session_id=sess_1)
        self.orchestrator.run("User B prompt", session_id=sess_2)

        s1 = self.orchestrator.session_manager.get_session(sess_1)
        s2 = self.orchestrator.session_manager.get_session(sess_2)

        self.assertEqual(s1.history.messages[0].content, "User A prompt")
        self.assertEqual(s2.history.messages[0].content, "User B prompt")

    def test_session_crash_recovery(self):
        """4. Verifies recovering active session state after process failure."""
        sess_id = f"SESS_CRASH_{time.time_ns()}"
        self.orchestrator.run("Prompt before crash", session_id=sess_id)

        # Simulate crash restart with fresh orchestrator
        recovered_orch = RuntimeOrchestrator(self.config, self.provider)
        recovered_sess = recovered_orch.session_manager.get_session(sess_id)

        self.assertIsNotNone(recovered_sess)
        self.assertEqual(recovered_sess.state, SessionState.ACTIVE)
        self.assertEqual(len(recovered_sess.history.messages), 2)

    def test_session_pruning_token_budget(self):
        """5. Verifies context window token budget pruning."""
        sess_id = f"SESS_PRUNE_BUDGET_{time.time_ns()}"
        sess = self.orchestrator.session_manager.create_session("prune_user", session_id=sess_id)
        sess.context_window.max_token_budget = 60

        for i in range(8):
            self.orchestrator.session_manager.add_user_message(sess_id, f"User message #{i} " * 15)
            self.orchestrator.session_manager.add_assistant_message(sess_id, f"Assistant response #{i} " * 15)

        pruned = self.orchestrator.session_manager.get_session(sess_id)
        self.assertLess(len(pruned.history.messages), 16)


if __name__ == "__main__":
    unittest.main()
