"""
Aegis AI Operating System — Session Atomic Write & Crash Recovery Tests
Tests to verify that session persistence uses atomic writes and
can recover from corrupted or partial writes.
"""

import os
import json
import time
import hashlib
import unittest
import tempfile
import threading
from runtime.src.config import AegisConfig
from runtime.src.session import (
    SessionManager, PersistenceManager, SessionContext, SessionState,
    ConversationHistory, MessageRole, Message, Snapshot,
)


class TestSessionAtomicWrite(unittest.TestCase):
    """Tests that session persistence uses atomic write patterns."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.pm = PersistenceManager(self.tmpdir)

    def _create_test_session(self, session_id="TEST_SESS_001"):
        return SessionContext(
            session_id=session_id,
            user_id="test_user",
            state=SessionState.ACTIVE,
        )

    def test_save_creates_file(self):
        """save_snapshot should create the session file."""
        sess = self._create_test_session()
        snap = self.pm.save_snapshot(sess)
        file_path = os.path.join(self.tmpdir, f"{sess.session_id}.json")
        self.assertTrue(os.path.exists(file_path))
        self.assertIsNotNone(snap.checksum)

    def test_save_creates_backup_on_second_write(self):
        """Second save_snapshot should create .bak backup file."""
        sess = self._create_test_session()
        self.pm.save_snapshot(sess)

        # Second write should create backup
        sess.history.add_message(MessageRole.USER, "test message")
        self.pm.save_snapshot(sess)

        bak_path = os.path.join(self.tmpdir, f"{sess.session_id}.json.bak")
        self.assertTrue(os.path.exists(bak_path),
            "Backup file should exist after second write")

    def test_no_tmp_file_after_success(self):
        """After successful save, no .tmp file should remain."""
        sess = self._create_test_session()
        self.pm.save_snapshot(sess)
        tmp_path = os.path.join(self.tmpdir, f"{sess.session_id}.json.tmp")
        self.assertFalse(os.path.exists(tmp_path),
            "Temp file should be cleaned up after successful save")

    def test_saved_file_has_valid_json(self):
        """Saved file should contain valid JSON that parses correctly."""
        sess = self._create_test_session()
        sess.history.add_message(MessageRole.USER, "Hello Aegis")
        self.pm.save_snapshot(sess)

        file_path = os.path.join(self.tmpdir, f"{sess.session_id}.json")
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data["session_id"], "TEST_SESS_001")
        self.assertEqual(data["user_id"], "test_user")
        self.assertEqual(len(data["history"]["messages"]), 1)

    def test_integrity_check_valid(self):
        """Integrity check should pass for valid snapshots."""
        sess = self._create_test_session()
        snap = self.pm.save_snapshot(sess)
        self.assertTrue(self.pm.verify_integrity(snap))

    def test_integrity_check_corrupted(self):
        """Integrity check should fail for tampered snapshots."""
        sess = self._create_test_session()
        snap = self.pm.save_snapshot(sess)
        # Tamper with data
        snap.serialized_data = snap.serialized_data.replace("test_user", "hacker_user")
        self.assertFalse(self.pm.verify_integrity(snap))


class TestSessionCorruptionRecovery(unittest.TestCase):
    """Tests that session loading recovers from corrupted files."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.pm = PersistenceManager(self.tmpdir)

    def test_load_from_corrupted_primary_with_valid_backup(self):
        """When primary file is corrupted, session should load from backup."""
        sess_id = "RECOVERY_TEST_001"
        sess = SessionContext(
            session_id=sess_id,
            user_id="backup_user",
            state=SessionState.ACTIVE,
        )
        sess.history.add_message(MessageRole.USER, "important data")

        # Save valid session
        self.pm.save_snapshot(sess)

        # Save again to create .bak
        sess.history.add_message(MessageRole.ASSISTANT, "response")
        self.pm.save_snapshot(sess)

        # Corrupt the primary file
        file_path = os.path.join(self.tmpdir, f"{sess_id}.json")
        with open(file_path, "w") as f:
            f.write("{broken json content!!!")

        # Load should recover from backup
        restored = self.pm.load_session(sess_id)
        self.assertIsNotNone(restored, "Session should be restored from backup")
        self.assertEqual(restored.session_id, sess_id)
        self.assertEqual(restored.user_id, "backup_user")

    def test_load_empty_primary_uses_backup(self):
        """When primary file is empty, session should load from backup."""
        sess_id = "EMPTY_TEST_001"
        sess = SessionContext(
            session_id=sess_id,
            user_id="test_user",
            state=SessionState.ACTIVE,
        )

        # Save twice to create backup
        self.pm.save_snapshot(sess)
        sess.history.add_message(MessageRole.USER, "data")
        self.pm.save_snapshot(sess)

        # Empty the primary file (simulates crash during write)
        file_path = os.path.join(self.tmpdir, f"{sess_id}.json")
        with open(file_path, "w") as f:
            f.write("")  # Empty file

        restored = self.pm.load_session(sess_id)
        self.assertIsNotNone(restored, "Session should be restored from backup")
        self.assertEqual(restored.session_id, sess_id)

    def test_load_both_corrupted_returns_none(self):
        """When both primary and backup are corrupted, load should return None."""
        sess_id = "BOTH_CORRUPT_001"
        sess = SessionContext(
            session_id=sess_id,
            user_id="test_user",
        )

        # Save twice
        self.pm.save_snapshot(sess)
        self.pm.save_snapshot(sess)

        # Corrupt both files
        for ext in [".json", ".json.bak"]:
            path = os.path.join(self.tmpdir, f"{sess_id}{ext}")
            if os.path.exists(path):
                with open(path, "w") as f:
                    f.write("CORRUPTED!")

        restored = self.pm.load_session(sess_id)
        self.assertIsNone(restored, "Should return None when both files corrupted")

    def test_load_nonexistent_returns_none(self):
        """Loading a non-existent session should return None without error."""
        restored = self.pm.load_session("DOES_NOT_EXIST_999")
        self.assertIsNone(restored)


class TestSessionManagerAtomicIntegration(unittest.TestCase):
    """Integration tests for SessionManager with atomic writes."""

    def setUp(self):
        self.config = AegisConfig()
        self.config.base_dir = tempfile.mkdtemp()
        self.manager = SessionManager(self.config)

    def test_create_and_load_session(self):
        """Create session, add messages, load from disk."""
        sess = self.manager.create_session("user1", session_id="INT_TEST_001")
        self.manager.add_user_message("INT_TEST_001", "Hello")
        self.manager.add_assistant_message("INT_TEST_001", "Hi there")

        # Clear in-memory cache to force disk load
        self.manager._sessions.clear()

        restored = self.manager.get_session("INT_TEST_001")
        self.assertIsNotNone(restored)
        self.assertEqual(restored.session_id, "INT_TEST_001")
        self.assertEqual(len(restored.history.messages), 2)

    def test_concurrent_writes_dont_corrupt(self):
        """Concurrent writes to the same session should not corrupt the file."""
        sess = self.manager.create_session("user1", session_id="CONCURRENT_001")

        errors = []

        def add_messages(thread_id):
            try:
                for i in range(5):
                    self.manager.add_user_message(
                        "CONCURRENT_001",
                        f"Message from thread {thread_id}, iteration {i}"
                    )
            except Exception as exc:
                errors.append(exc)

        threads = [
            threading.Thread(target=add_messages, args=(t,))
            for t in range(3)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        self.assertEqual(len(errors), 0, f"Concurrent write errors: {errors}")

        # Verify session is still loadable
        self.manager._sessions.clear()
        restored = self.manager.get_session("CONCURRENT_001")
        self.assertIsNotNone(restored, "Session should be loadable after concurrent writes")
        self.assertGreater(len(restored.history.messages), 0)


if __name__ == "__main__":
    unittest.main()
