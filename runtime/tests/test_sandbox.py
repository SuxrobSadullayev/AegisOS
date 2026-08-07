"""
Sandbox Unit Tests for Aegis AI OS.
Verifies SandboxPolicy default DENY settings, SandboxLimits, SandboxRequest,
SandboxResponse serialization/deserialization, structured errors, and PluginWorker request handlers.
"""

import os
import json
import time
import unittest
from runtime.src.sandbox import (
    SandboxPolicy, SandboxLimits, SandboxRequest, SandboxResponse,
    SandboxError, SandboxTimeoutError, SandboxCrashedError, SandboxPermissionError,
    PluginWorker, SandboxManager
)


class TestSandboxUnit(unittest.TestCase):
    """Unit tests for Sandbox data structures, policies, and protocol encoding."""

    def test_sandbox_policy_default_deny_initialization(self):
        """1. Verifies SandboxPolicy defaults to strict DENY for all capabilities."""
        policy = SandboxPolicy.default_deny()
        self.assertFalse(policy.allow_filesystem_read)
        self.assertFalse(policy.allow_filesystem_write)
        self.assertFalse(policy.allow_network)
        self.assertFalse(policy.allow_subprocess)
        self.assertFalse(policy.allow_env_access)

    def test_sandbox_limits_default_values(self):
        """2. Verifies default resource constraints in SandboxLimits."""
        limits = SandboxLimits()
        self.assertEqual(limits.memory_limit_mb, 256)
        self.assertEqual(limits.cpu_time_limit_sec, 10.0)
        self.assertEqual(limits.execution_timeout_sec, 5.0)
        self.assertEqual(limits.max_output_bytes, 1048576)

    def test_sandbox_policy_dict_roundtrip(self):
        """3. Verifies SandboxPolicy serialization to and from dictionary."""
        pol = SandboxPolicy(
            allow_filesystem_read=True,
            allow_filesystem_write=False,
            allow_network=True,
            limits=SandboxLimits(execution_timeout_sec=2.5)
        )
        pol_dict = pol.to_dict()
        restored = SandboxPolicy.from_dict(pol_dict)

        self.assertTrue(restored.allow_filesystem_read)
        self.assertFalse(restored.allow_filesystem_write)
        self.assertTrue(restored.allow_network)
        self.assertEqual(restored.limits.execution_timeout_sec, 2.5)

    def test_sandbox_request_serialization(self):
        """4. Verifies SandboxRequest serialization to and from JSON dictionary."""
        req = SandboxRequest(
            command="EXECUTE",
            payload={"task": "format_code"},
            plugin_id="plugin.test.unit",
            capability_token="TOK_123"
        )
        data = req.to_dict()
        restored = SandboxRequest.from_dict(data)

        self.assertEqual(restored.command, "EXECUTE")
        self.assertEqual(restored.plugin_id, "plugin.test.unit")
        self.assertEqual(restored.capability_token, "TOK_123")
        self.assertEqual(restored.payload.get("task"), "format_code")

    def test_sandbox_response_serialization(self):
        """5. Verifies SandboxResponse serialization to and from JSON dictionary."""
        resp = SandboxResponse(
            success=True,
            result={"status": "OK"},
            metrics={"exec_time_ms": 1.5},
            request_id="REQ_999"
        )
        data = resp.to_dict()
        restored = SandboxResponse.from_dict(data)

        self.assertTrue(restored.success)
        self.assertEqual(restored.result.get("status"), "OK")
        self.assertEqual(restored.metrics.get("exec_time_ms"), 1.5)
        self.assertEqual(restored.request_id, "REQ_999")

    def test_structured_error_inheritance(self):
        """6. Verifies custom sandbox error hierarchy."""
        self.assertTrue(issubclass(SandboxTimeoutError, SandboxError))
        self.assertTrue(issubclass(SandboxCrashedError, SandboxError))
        self.assertTrue(issubclass(SandboxPermissionError, SandboxError))

    def test_worker_ping_healthcheck_command(self):
        """7. Verifies PluginWorker responds successfully to HEALTHCHECK ping command."""
        worker = PluginWorker(SandboxPolicy.default_deny(), "plugin.test.ping")
        req = SandboxRequest(command="HEALTHCHECK", payload={}, plugin_id="plugin.test.ping")
        resp = worker.process_request(req)

        self.assertTrue(resp.success)
        self.assertEqual(resp.result.get("status"), "OK")
        self.assertEqual(resp.result.get("plugin_id"), "plugin.test.ping")

    def test_worker_check_permissions_denied_by_default(self):
        """8. Verifies PluginWorker check_permissions command returns False under default DENY."""
        worker = PluginWorker(SandboxPolicy.default_deny(), "plugin.test.perm")
        req = SandboxRequest(command="CHECK_PERMISSIONS", payload={"permission": "FILESYSTEM_WRITE"}, plugin_id="plugin.test.perm")
        resp = worker.process_request(req)

        self.assertFalse(resp.success)
        self.assertEqual(resp.error_code, "PERMISSION_DENIED")

    def test_worker_check_permissions_allowed(self):
        """9. Verifies PluginWorker returns True when explicit permission granted in policy."""
        pol = SandboxPolicy(allow_filesystem_read=True)
        worker = PluginWorker(pol, "plugin.test.perm_allow")
        req = SandboxRequest(command="CHECK_PERMISSIONS", payload={"permission": "FILESYSTEM_READ"}, plugin_id="plugin.test.perm_allow")
        resp = worker.process_request(req)

        self.assertTrue(resp.success)
        self.assertTrue(resp.result.get("allowed"))

    def test_sandbox_manager_spawns_active_worker_subprocess(self):
        """10. Verifies SandboxManager spawns an active Python worker subprocess."""
        mgr = SandboxManager()
        try:
            proc = mgr.spawn_worker("plugin.test.spawn", SandboxPolicy.default_deny())
            self.assertIsNotNone(proc)
            self.assertTrue(mgr.is_worker_alive("plugin.test.spawn"))
            self.assertEqual(mgr.get_worker_status("plugin.test.spawn"), "RUNNING")
        finally:
            mgr.terminate_all()

    def test_sandbox_manager_healthcheck_ipc(self):
        """11. Verifies SandboxManager sends HEALTHCHECK request over IPC and gets valid response."""
        mgr = SandboxManager()
        try:
            req = SandboxRequest(command="HEALTHCHECK", payload={}, plugin_id="plugin.test.hc")
            resp = mgr.send_request("plugin.test.hc", req)
            self.assertTrue(resp.success)
            self.assertEqual(resp.result.get("status"), "OK")
        finally:
            mgr.terminate_all()

    def test_sandbox_manager_terminate_worker_cleanup(self):
        """12. Verifies terminate_worker stops subprocess cleanly."""
        mgr = SandboxManager()
        mgr.spawn_worker("plugin.test.term", SandboxPolicy.default_deny())
        self.assertTrue(mgr.is_worker_alive("plugin.test.term"))

        res = mgr.terminate_worker("plugin.test.term")
        self.assertTrue(res)
        self.assertFalse(mgr.is_worker_alive("plugin.test.term"))
        self.assertEqual(mgr.get_worker_status("plugin.test.term"), "STOPPED")

    def test_sandbox_manager_restart_worker(self):
        """13. Verifies restart_worker replaces terminated subprocess with fresh worker."""
        mgr = SandboxManager()
        try:
            p1 = mgr.spawn_worker("plugin.test.restart", SandboxPolicy.default_deny())
            pid1 = p1.pid

            p2 = mgr.restart_worker("plugin.test.restart")
            pid2 = p2.pid

            self.assertNotEqual(pid1, pid2)
            self.assertTrue(mgr.is_worker_alive("plugin.test.restart"))
        finally:
            mgr.terminate_all()

    def test_sandbox_manager_terminate_all(self):
        """14. Verifies terminate_all cleans up all spawned worker subprocesses."""
        mgr = SandboxManager()
        mgr.spawn_worker("p1", SandboxPolicy.default_deny())
        mgr.spawn_worker("p2", SandboxPolicy.default_deny())
        mgr.spawn_worker("p3", SandboxPolicy.default_deny())

        self.assertTrue(mgr.is_worker_alive("p1"))
        self.assertTrue(mgr.is_worker_alive("p2"))
        self.assertTrue(mgr.is_worker_alive("p3"))

        mgr.terminate_all()

        self.assertFalse(mgr.is_worker_alive("p1"))
        self.assertFalse(mgr.is_worker_alive("p2"))
        self.assertFalse(mgr.is_worker_alive("p3"))

    def test_sandbox_request_default_command(self):
        """15. Verifies default request command fallback."""
        req = SandboxRequest.from_dict({"payload": {"test": 1}, "plugin_id": "p.test"})
        self.assertEqual(req.command, "EXECUTE")

    def test_sandbox_response_error_code_preservation(self):
        """16. Verifies response error code preservation."""
        resp = SandboxResponse(success=False, error="Denied", error_code="PERMISSION_DENIED")
        data = resp.to_dict()
        self.assertEqual(data["error_code"], "PERMISSION_DENIED")

    def test_sandbox_limits_custom_values(self):
        """17. Verifies custom resource limits initialization."""
        limits = SandboxLimits(memory_limit_mb=512, execution_timeout_sec=1.5)
        self.assertEqual(limits.memory_limit_mb, 512)
        self.assertEqual(limits.execution_timeout_sec, 1.5)

    def test_sandbox_policy_from_dict_defaults(self):
        """18. Verifies missing fields in policy dict fall back to DENY."""
        pol = SandboxPolicy.from_dict({})
        self.assertFalse(pol.allow_filesystem_read)
        self.assertFalse(pol.allow_filesystem_write)
        self.assertFalse(pol.allow_network)

    def test_worker_process_task_payload_return(self):
        """19. Verifies default task payload processing in PluginWorker."""
        worker = PluginWorker(SandboxPolicy.default_deny(), "p.payload")
        req = SandboxRequest(command="EXECUTE", payload={"input": "hello world"}, plugin_id="p.payload")
        resp = worker.process_request(req)

        self.assertTrue(resp.success)
        self.assertEqual(resp.result.get("processed_payload"), {"input": "hello world"})

    def test_sandbox_manager_get_status_nonexistent(self):
        """20. Verifies status of non-existent worker is STOPPED."""
        mgr = SandboxManager()
        self.assertEqual(mgr.get_worker_status("nonexistent_plugin_xyz"), "STOPPED")


if __name__ == "__main__":
    unittest.main()
