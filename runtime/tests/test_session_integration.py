import unittest
import threading
from runtime.src.config import AegisConfig
from runtime.src.session import SessionManager, SessionState


class TestSessionIntegration(unittest.TestCase):
    def setUp(self):
        self.config = AegisConfig.load_from_env()
        self.manager = SessionManager(self.config)

    def test_multithreaded_session_concurrency(self):
        sess = self.manager.create_session("concurrent_user")
        errors = []

        def worker(idx: int):
            try:
                self.manager.add_user_message(sess.session_id, f"Thread message #{idx}")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0)
        retrieved = self.manager.get_session(sess.session_id)
        self.assertEqual(len(retrieved.history.messages), 10)

    def test_crash_recovery_from_file_persistence(self):
        # Create a session and add data
        sess = self.manager.create_session("crash_user", session_id="SESS_CRASH_TEST")
        self.manager.add_user_message("SESS_CRASH_TEST", "Pre-crash user prompt")

        # Simulate fresh manager instance after crash
        new_manager = SessionManager(self.config)
        restored = new_manager.get_session("SESS_CRASH_TEST")

        self.assertIsNotNone(restored)
        self.assertEqual(restored.session_id, "SESS_CRASH_TEST")
        self.assertEqual(restored.history.messages[0].content, "Pre-crash user prompt")


if __name__ == '__main__':
    unittest.main()
