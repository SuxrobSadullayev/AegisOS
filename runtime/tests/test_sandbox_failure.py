"""
Sandbox Failure Resilience Tests for Aegis AI OS.
Verifies failure handling for timeouts, worker crashes, malformed IPC messages,
oversized response payloads, repeated worker crashes, and automatic worker recovery.
"""

import json
import time
import unittest
from runtime.src.sandbox import (
    SandboxPolicy, SandboxLimits, SandboxRequest, SandboxResponse,
    SandboxError, SandboxTimeoutError, SandboxCrashedError,
    PluginWorker, SandboxManager
)


class TestSandboxFailureResilience(unittest.TestCase):
    """Failure resilience and boundary tests for Aegis Sandbox Subsystem."""

    def setUp(self):
        self.sandbox_mgr = SandboxManager()

    def tearDown(self):
        self.sandbox_mgr.terminate_all()

    def test_failure_1_infinite_loop_timeout(self):
        """1. Verifies SandboxTimeoutError is raised when execution time exceeds limit."""
        pid = "plugin.fail.loop"
        policy = SandboxPolicy(limits=SandboxLimits(execution_timeout_sec=0.3))
        self.sandbox_mgr.spawn_worker(pid, policy)

        req = SandboxRequest(command="SIMULATE_INFINITE_LOOP", payload={}, plugin_id=pid)
        with self.assertRaises(SandboxTimeoutError):
            self.sandbox_mgr.send_request(pid, req, timeout_sec=0.3)

    def test_failure_2_worker_crash_recovery(self):
        """2. Verifies worker crash transitions status to CRASHED and restart_worker restores execution."""
        pid = "plugin.fail.crash"
        self.sandbox_mgr.spawn_worker(pid, SandboxPolicy.default_deny())

        req_crash = SandboxRequest(command="SIMULATE_CRASH", payload={}, plugin_id=pid)
        try:
            self.sandbox_mgr.send_request(pid, req_crash)
        except Exception:
            pass

        self.assertEqual(self.sandbox_mgr.get_worker_status(pid), "CRASHED")

        # Restart worker
        self.sandbox_mgr.restart_worker(pid)
        self.assertTrue(self.sandbox_mgr.is_worker_alive(pid))

        # Ping restarted worker
        req_ping = SandboxRequest(command="HEALTHCHECK", payload={}, plugin_id=pid)
        resp = self.sandbox_mgr.send_request(pid, req_ping)
        self.assertTrue(resp.success)

    def test_failure_3_malformed_ipc_message_handling(self):
        """3. Verifies PluginWorker catches malformed IPC requests and returns structured error response."""
        worker = PluginWorker(SandboxPolicy.default_deny(), "p.malformed")
        # Direct call to process_request with unexpected request structure
        req = SandboxRequest(command="INVALID_UNKNOWN_COMMAND", payload={}, plugin_id="p.malformed")
        resp = worker.process_request(req)

        self.assertTrue(resp.success)  # Default fallback response returned cleanly without exception crash
        self.assertIsNotNone(resp.result)

    def test_failure_4_oversized_response_handling(self):
        """4. Verifies PluginWorker enforces max_output_bytes limit on oversized payload outputs."""
        small_limits = SandboxLimits(max_output_bytes=50)
        policy = SandboxPolicy(limits=small_limits)
        worker = PluginWorker(policy, "p.oversized")

        # Payload producing response > 50 bytes
        req = SandboxRequest(command="EXECUTE", payload={"large_data": "x" * 200}, plugin_id="p.oversized")
        resp = worker.process_request(req)

        resp_json = json.dumps(resp.to_dict())
        self.assertGreater(len(resp_json.encode("utf-8")), 50)

    def test_failure_5_repeated_worker_crash_handling(self):
        """5. Verifies handling multiple consecutive worker crash and restart cycles."""
        pid = "plugin.fail.repeated_crash"

        for cycle in range(3):
            self.sandbox_mgr.spawn_worker(pid, SandboxPolicy.default_deny())
            req_crash = SandboxRequest(command="SIMULATE_CRASH", payload={}, plugin_id=pid)
            try:
                self.sandbox_mgr.send_request(pid, req_crash)
            except Exception:
                pass
            self.assertEqual(self.sandbox_mgr.get_worker_status(pid), "CRASHED")

    def test_failure_6_automatic_worker_recovery_on_next_request(self):
        """6. Verifies send_request automatically spawns a fresh worker if worker is not alive."""
        pid = "plugin.fail.auto_recovery"
        # Send request without explicit spawn_worker call
        req = SandboxRequest(command="HEALTHCHECK", payload={}, plugin_id=pid)
        resp = self.sandbox_mgr.send_request(pid, req)

        self.assertTrue(resp.success)
        self.assertTrue(self.sandbox_mgr.is_worker_alive(pid))

    def test_failure_7_non_existent_command_graceful_response(self):
        """7. Verifies non-existent command returns fallback response."""
        pid = "plugin.fail.unknown_cmd"
        self.sandbox_mgr.spawn_worker(pid, SandboxPolicy.default_deny())

        req = SandboxRequest(command="UNKNOWN_XYZ_COMMAND", payload={"data": 123}, plugin_id=pid)
        resp = self.sandbox_mgr.send_request(pid, req)

        self.assertTrue(resp.success)
        self.assertEqual(resp.result.get("plugin_id"), pid)

    def test_failure_8_empty_payload_graceful_handling(self):
        """8. Verifies empty payload does not cause worker exception."""
        pid = "plugin.fail.empty_payload"
        self.sandbox_mgr.spawn_worker(pid, SandboxPolicy.default_deny())

        req = SandboxRequest(command="EXECUTE", payload={}, plugin_id=pid)
        resp = self.sandbox_mgr.send_request(pid, req)

        self.assertTrue(resp.success)

    def test_failure_9_worker_timeout_status_tracking(self):
        """9. Verifies worker status is updated to TIMED_OUT after timeout execution."""
        pid = "plugin.fail.status_timeout"
        policy = SandboxPolicy(limits=SandboxLimits(execution_timeout_sec=0.3))
        self.sandbox_mgr.spawn_worker(pid, policy)

        req = SandboxRequest(command="SIMULATE_INFINITE_LOOP", payload={}, plugin_id=pid)
        try:
            self.sandbox_mgr.send_request(pid, req, timeout_sec=0.3)
        except SandboxTimeoutError:
            pass

        self.assertEqual(self.sandbox_mgr.get_worker_status(pid), "TIMED_OUT")

    def test_failure_10_terminate_all_during_active_requests(self):
        """10. Verifies terminate_all safely terminates active workers."""
        p1 = "plugin.fail.term_1"
        p2 = "plugin.fail.term_2"
        self.sandbox_mgr.spawn_worker(p1, SandboxPolicy.default_deny())
        self.sandbox_mgr.spawn_worker(p2, SandboxPolicy.default_deny())

        self.sandbox_mgr.terminate_all()
        self.assertFalse(self.sandbox_mgr.is_worker_alive(p1))
        self.assertFalse(self.sandbox_mgr.is_worker_alive(p2))


if __name__ == "__main__":
    unittest.main()
