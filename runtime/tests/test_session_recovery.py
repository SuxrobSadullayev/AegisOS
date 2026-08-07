"""
Session Recovery & Snapshot Integrity Tests for Aegis AI OS.
Verifies session creation, SHA-256 integrity checksum validation, crash recovery,
and corrupted snapshot detection.
"""

import os
import json
import time
import unittest
from runtime.src.config import AegisConfig
from runtime.src.gateway import MockProvider
from runtime.src.session import SessionManager, SessionState, Snapshot, PersistenceManager
from runtime.src.orchestrator import RuntimeOrchestrator


class TestSessionRecoveryAndIntegrity(unittest.TestCase):
    """Tests session crash recovery, snapshot persistence, and SHA-256 integrity verification."""

    def setUp(self):
        self.config = AegisConfig()
        self.provider = MockProvider(self.config)
        self.orchestrator = RuntimeOrchestrator(self.config, self.provider)
        self.session_mgr = SessionManager(self.config)

    def test_session_snapshot_checksum_verification(self):
        """1. Verifies SHA-256 integrity checksum calculation for snapshots."""
        sess_id = f"SESS_CHECKSUM_{time.time_ns()}"
        sess = self.session_mgr.create_session("checksum_user", session_id=sess_id)
        self.session_mgr.add_user_message(sess_id, "Checksum verification prompt")

        snapshot = self.session_mgr.persistence.save_snapshot(sess)
        self.assertIsNotNone(snapshot.checksum)
        self.assertEqual(len(snapshot.checksum), 64)  # Hex digest length of SHA-256

        # Verify integrity check passes
        self.assertTrue(self.session_mgr.persistence.verify_integrity(snapshot))

    def test_corrupted_snapshot_detection(self):
        """2. Verifies tampered/corrupted snapshot files are detected and rejected."""
        sess_id = f"SESS_CORRUPT_{time.time_ns()}"
        sess = self.session_mgr.create_session("corrupt_user", session_id=sess_id)
        snapshot = self.session_mgr.persistence.save_snapshot(sess)

        # Tamper with snapshot content
        tampered_snapshot = Snapshot(
            snapshot_id=snapshot.snapshot_id,
            session_id=snapshot.session_id,
            serialized_data=snapshot.serialized_data + "TAMPERED_PAYLOAD",
            checksum=snapshot.checksum,
            timestamp_utc=snapshot.timestamp_utc
        )

        # Integrity verification must fail
        self.assertFalse(self.session_mgr.persistence.verify_integrity(tampered_snapshot))

    def test_crash_recovery_restores_complete_session_state(self):
        """3. Verifies crash recovery restores messages, state, and provider config."""
        sess_id = f"SESS_CRASH_RECOVERY_{time.time_ns()}"
        ctx1 = self.orchestrator.run("Turn 1 prompt before crash", session_id=sess_id)
        ctx2 = self.orchestrator.run("Turn 2 prompt before crash", session_id=sess_id)

        # Simulate process crash by creating a fresh orchestrator
        recovered_orch = RuntimeOrchestrator(self.config, self.provider)
        recovered_sess = recovered_orch.session_manager.get_session(sess_id)

        self.assertIsNotNone(recovered_sess)
        self.assertEqual(recovered_sess.state, SessionState.ACTIVE)
        self.assertEqual(len(recovered_sess.history.messages), 4)  # 2 Users + 2 Assistants
        self.assertEqual(recovered_sess.history.messages[0].content, "Turn 1 prompt before crash")


if __name__ == "__main__":
    unittest.main()
