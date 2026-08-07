import unittest
import os
import shutil
from runtime.src.config import AegisConfig
from runtime.src.session import (
    SessionManager,
    SessionContext,
    SessionState,
    MessageRole,
    ConversationHistory,
    ContextWindow,
    MemoryStore,
    PersistenceManager,
    SessionMetrics
)


class TestSessionManager(unittest.TestCase):
    def setUp(self):
        self.config = AegisConfig.load_from_env()
        self.manager = SessionManager(self.config)

    def test_create_and_get_session(self):
        sess = self.manager.create_session("user123")
        self.assertIsInstance(sess, SessionContext)
        self.assertEqual(sess.user_id, "user123")
        self.assertEqual(sess.state, SessionState.ACTIVE)

        retrieved = self.manager.get_session(sess.session_id)
        self.assertEqual(retrieved.session_id, sess.session_id)

    def test_conversation_history_and_pruning(self):
        sess = self.manager.create_session("user456")
        self.manager.add_user_message(sess.session_id, "Hello Aegis OS")
        self.manager.add_assistant_message(sess.session_id, "Greetings! How can I assist?")

        retrieved = self.manager.get_session(sess.session_id)
        self.assertEqual(len(retrieved.history.messages), 2)
        self.assertEqual(retrieved.history.messages[0].role, MessageRole.USER)
        self.assertEqual(retrieved.history.messages[1].role, MessageRole.ASSISTANT)

    def test_token_pruning_limits(self):
        history = ConversationHistory()
        for i in range(10):
            history.add_message(MessageRole.USER, f"This is a long message index #{i} containing multiple words")

        initial_tokens = history.total_tokens
        history.prune_to_budget(30)
        self.assertLess(history.total_tokens, initial_tokens)

    def test_claim_store_memory_persistence(self):
        sess = self.manager.create_session("user789")
        sess.memory.epistemic_claims.add_claim("CLM-0001", "PostgreSQL pool size 20", "VERIFIED_FACT", 3)
        self.manager.persistence.save_snapshot(sess)

        # Restore from disk
        restored = self.manager.persistence.load_session(sess.session_id)
        self.assertIn("CLM-0001", restored.memory.epistemic_claims.claims)

    def test_terminate_session(self):
        sess = self.manager.create_session("user_term")
        res = self.manager.terminate_session(sess.session_id)
        self.assertTrue(res)
        self.assertEqual(sess.state, SessionState.TERMINATED)

    def test_metrics(self):
        self.manager.create_session("user_metrics")
        metrics = self.manager.get_metrics()
        self.assertIsInstance(metrics, SessionMetrics)
        self.assertGreater(metrics.active_sessions_count, 0)
        self.assertGreater(metrics.total_snapshots_saved, 0)


if __name__ == '__main__':
    unittest.main()
