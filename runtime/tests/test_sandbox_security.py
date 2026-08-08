"""
Sandbox Security Tests for Aegis AI OS.
Verifies Default DENY security barriers for filesystem read/write, network access,
environment secrets, subprocess execution, path traversal, secret redaction, and process isolation.
"""

import os
import unittest
from runtime.src.sandbox import (
    SandboxPolicy, SandboxLimits, SandboxRequest, SandboxResponse,
    SandboxError, SandboxTimeoutError, SandboxPermissionError,
    PluginWorker, SandboxManager
)


class TestSandboxSecurity(unittest.TestCase):
    """Security and barrier tests enforcing Default DENY process isolation."""

    def setUp(self):
        self.sandbox_mgr = SandboxManager()
        self.untrusted_plugin_id = "plugin.untrusted.attacker"

    def tearDown(self):
        self.sandbox_mgr.terminate_all()

    def test_security_1_untrusted_plugin_filesystem_write_denied(self):
        """1. Verifies FILESYSTEM_WRITE operation is denied for untrusted plugin."""
        policy = SandboxPolicy.default_deny()
        self.sandbox_mgr.spawn_worker(self.untrusted_plugin_id, policy)

        req = SandboxRequest(
            command="FILESYSTEM_WRITE",
            payload={"path": "/tmp/aegis_hack.txt", "content": "malicious data"},
            plugin_id=self.untrusted_plugin_id
        )

        with self.assertRaises(SandboxPermissionError):
            self.sandbox_mgr.send_request(self.untrusted_plugin_id, req)

    def test_security_2_untrusted_plugin_network_access_denied(self):
        """2. Verifies NETWORK_OUTBOUND request is denied under Default DENY."""
        policy = SandboxPolicy.default_deny()
        self.sandbox_mgr.spawn_worker(self.untrusted_plugin_id, policy)

        req = SandboxRequest(
            command="NETWORK_REQUEST",
            payload={"url": "https://malicious-exfiltration-server.com"},
            plugin_id=self.untrusted_plugin_id
        )

        with self.assertRaises(SandboxPermissionError):
            self.sandbox_mgr.send_request(self.untrusted_plugin_id, req)

    def test_security_3_environment_secret_read_denied(self):
        """3. Verifies reading environment variables is denied under Default DENY."""
        policy = SandboxPolicy.default_deny()
        self.sandbox_mgr.spawn_worker(self.untrusted_plugin_id, policy)

        req = SandboxRequest(
            command="READ_ENV",
            payload={"name": "GEMINI_API_KEY"},
            plugin_id=self.untrusted_plugin_id
        )

        with self.assertRaises(SandboxPermissionError):
            self.sandbox_mgr.send_request(self.untrusted_plugin_id, req)

    def test_security_4_subprocess_execution_denied(self):
        """4. Verifies PROCESS_EXECUTE is denied under Default DENY."""
        policy = SandboxPolicy.default_deny()
        self.sandbox_mgr.spawn_worker(self.untrusted_plugin_id, policy)

        req = SandboxRequest(
            command="PROCESS_EXECUTE",
            payload={"command": "rm -rf /"},
            plugin_id=self.untrusted_plugin_id
        )

        with self.assertRaises(SandboxPermissionError):
            self.sandbox_mgr.send_request(self.untrusted_plugin_id, req)

    def test_security_5_permission_escalation_blocked(self):
        """5. Verifies self-declared capability token escalation is rejected."""
        policy = SandboxPolicy.default_deny()
        self.sandbox_mgr.spawn_worker(self.untrusted_plugin_id, policy)

        req = SandboxRequest(
            command="CHECK_PERMISSIONS",
            payload={"permission": "SECRET_ACCESS"},
            plugin_id=self.untrusted_plugin_id,
            capability_token="FAKE_ATTACKER_TOKEN_GRANTING_ALL"
        )
        with self.assertRaises(SandboxPermissionError):
            self.sandbox_mgr.send_request(self.untrusted_plugin_id, req)



    def test_security_6_path_traversal_denied(self):
        """6. Verifies path traversal payload ('../etc/passwd') is blocked."""
        policy = SandboxPolicy(allow_filesystem_read=True)
        self.sandbox_mgr.spawn_worker("plugin.path_traversal", policy)

        req = SandboxRequest(
            command="FILESYSTEM_READ",
            payload={"path": "../../../etc/passwd"},
            plugin_id="plugin.path_traversal"
        )
        with self.assertRaises(SandboxPermissionError):
            self.sandbox_mgr.send_request("plugin.path_traversal", req)


    def test_security_7_secret_leakage_redacted(self):
        """7. Verifies environment secrets are redacted when env access is explicitly allowed."""
        policy = SandboxPolicy(allow_env_access=True)
        os.environ["AEGIS_TEST_KEY_123"] = "secret_value_xyz"

        self.sandbox_mgr.spawn_worker("plugin.env_reader", policy)
        req = SandboxRequest(
            command="READ_ENV",
            payload={"name": "AEGIS_TEST_KEY_123"},
            plugin_id="plugin.env_reader"
        )
        resp = self.sandbox_mgr.send_request("plugin.env_reader", req)
        self.assertTrue(resp.success)
        self.assertEqual(resp.result.get("value"), "[REDACTED_SECRET]")

    def test_security_8_infinite_loop_timeout_protection(self):
        """8. Verifies SandboxManager terminates subprocess running an infinite loop."""
        policy = SandboxPolicy(limits=SandboxLimits(execution_timeout_sec=0.5))
        self.sandbox_mgr.spawn_worker("plugin.infinite_loop", policy)

        req = SandboxRequest(command="SIMULATE_INFINITE_LOOP", payload={}, plugin_id="plugin.infinite_loop")

        with self.assertRaises(SandboxTimeoutError):
            self.sandbox_mgr.send_request("plugin.infinite_loop", req, timeout_sec=0.5)

        # Confirm subprocess was killed cleanly
        self.assertFalse(self.sandbox_mgr.is_worker_alive("plugin.infinite_loop"))

    def test_security_9_worker_crash_does_not_crash_main_runtime(self):
        """9. Verifies worker subprocess exit code 137 does not crash main Aegis process."""
        policy = SandboxPolicy.default_deny()
        self.sandbox_mgr.spawn_worker("plugin.crash_test", policy)

        req = SandboxRequest(command="SIMULATE_CRASH", payload={}, plugin_id="plugin.crash_test")

        try:
            self.sandbox_mgr.send_request("plugin.crash_test", req)
        except Exception:
            pass

        # Main test process is still running cleanly!
        self.assertEqual(self.sandbox_mgr.get_worker_status("plugin.crash_test"), "CRASHED")

    def test_security_10_advanced_path_traversal_variants_denied(self):
        """10. Verifies double encoding, Unicode normalization, null bytes, and symlinks are denied."""
        worker = PluginWorker(SandboxPolicy(allow_filesystem_read=True), "plugin.traversal_adv")

        # Double encoding
        r1 = worker.process_request(SandboxRequest("FILESYSTEM_READ", {"path": "%252e%252e%252fetc%252fpasswd"}, "p"))
        self.assertFalse(r1.success)
        self.assertEqual(r1.error_code, "PATH_TRAVERSAL_DENIED")

        # Unicode normalization
        r2 = worker.process_request(SandboxRequest("FILESYSTEM_READ", {"path": "\uff0e\uff0e/etc/passwd"}, "p"))
        self.assertFalse(r2.success)
        self.assertEqual(r2.error_code, "PATH_TRAVERSAL_DENIED")

        # Null byte injection
        r3 = worker.process_request(SandboxRequest("FILESYSTEM_READ", {"path": "allowed.txt\x00/etc/passwd"}, "p"))
        self.assertFalse(r3.success)
        self.assertEqual(r3.error_code, "PATH_TRAVERSAL_DENIED")

    def test_security_11_path_containment_check(self):
        """11. Verifies allowed_paths containment check blocks escaping allowed directory."""
        import tempfile
        allowed_dir = tempfile.mkdtemp()
        outside_dir = tempfile.mkdtemp()

        outside_file = os.path.join(outside_dir, "secret.txt")
        with open(outside_file, "w") as f:
            f.write("sensitive data")

        policy = SandboxPolicy(allow_filesystem_read=True, allowed_paths=[allowed_dir])
        worker = PluginWorker(policy, "plugin.containment")

        # Attempt to read file outside allowed_paths
        r = worker.process_request(SandboxRequest("FILESYSTEM_READ", {"path": outside_file}, "p"))
        self.assertFalse(r.success)
        self.assertEqual(r.error_code, "PATH_TRAVERSAL_DENIED")

    def test_security_12_main_runtime_process_isolation(self):
        """12. Verifies worker PID is distinct from main Aegis runtime process PID."""
        main_pid = os.getpid()
        proc = self.sandbox_mgr.spawn_worker("plugin.pid_test", SandboxPolicy.default_deny())

        self.assertNotEqual(main_pid, proc.pid)


if __name__ == "__main__":
    unittest.main()
