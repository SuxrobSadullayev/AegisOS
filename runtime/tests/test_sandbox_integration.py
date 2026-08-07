"""
Sandbox Integration Tests for Aegis AI OS.
Verifies PluginManager integration with SandboxManager, lifecycle state transitions,
subprocess execution, reload atomic swap, and capability registration under sandbox rules.
"""

import os
import shutil
import tempfile
import unittest
from runtime.src.config import AegisConfig
from runtime.src.plugin import (
    PluginManager, PluginManifest, PluginPermission, AegisPlugin,
    PluginState, PluginContext
)
from runtime.src.sandbox import (
    SandboxPolicy, SandboxLimits, SandboxRequest, SandboxResponse,
    SandboxTimeoutError, SandboxCrashedError
)


class TestSandboxIntegration(unittest.TestCase):
    """Integration tests connecting SandboxManager with PluginManager and Lifecycle FSM."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.plugins_dir = os.path.join(self.temp_dir, "plugins")
        os.makedirs(self.plugins_dir, exist_ok=True)
        self.plugin_mgr = PluginManager(self.plugins_dir)

    def tearDown(self):
        self.plugin_mgr.sandbox_manager.terminate_all()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_plugin_manager_has_sandbox_manager(self):
        """1. Verifies PluginManager instantiates SandboxManager facade."""
        self.assertIsNotNone(self.plugin_mgr.sandbox_manager)

    def test_sandbox_worker_spawns_on_plugin_execution(self):
        """2. Verifies executing an active plugin with sandbox worker active routes through worker."""
        # Setup test manifest
        manifest = PluginManifest(
            plugin_id="aegis.integration.sandbox_1",
            name="Sandbox Integration Plugin 1",
            version="1.0.0",
            permissions=[PluginPermission.FILESYSTEM_READ]
        )

        class DummyPlugin(AegisPlugin):
            def get_manifest(self):
                return manifest
            def on_execute(self, ctx, data):
                return {"result": "fallback_execute"}

        inst = DummyPlugin()
        self.plugin_mgr.register_builtin(inst)
        self.plugin_mgr.load_plugin(manifest.plugin_id, inst)
        self.plugin_mgr.validate_plugin(manifest.plugin_id)
        self.plugin_mgr.resolve_dependencies()
        self.plugin_mgr.activate_plugin(manifest.plugin_id)

        # Spawn sandbox worker for plugin
        policy = SandboxPolicy(allow_filesystem_read=True)
        self.plugin_mgr.sandbox_manager.spawn_worker(manifest.plugin_id, policy)
        self.assertTrue(self.plugin_mgr.sandbox_manager.is_worker_alive(manifest.plugin_id))

        # Execute plugin via PluginManager facade
        result = self.plugin_mgr.execute_plugin(manifest.plugin_id, {"input": "test_data"})
        self.assertIsNotNone(result)
        self.assertEqual(result.get("plugin_id"), manifest.plugin_id)

    def test_sandbox_worker_terminates_on_plugin_unload(self):
        """3. Verifies unloading a plugin terminates its subprocess worker."""
        manifest = PluginManifest(
            plugin_id="aegis.integration.sandbox_unload",
            name="Unload Sandbox Plugin",
            version="1.0.0"
        )

        class DummyPlugin(AegisPlugin):
            def get_manifest(self):
                return manifest

        inst = DummyPlugin()
        self.plugin_mgr.register_builtin(inst)
        self.plugin_mgr.load_plugin(manifest.plugin_id, inst)
        self.plugin_mgr.validate_plugin(manifest.plugin_id)
        self.plugin_mgr.resolve_dependencies()
        self.plugin_mgr.activate_plugin(manifest.plugin_id)

        self.plugin_mgr.sandbox_manager.spawn_worker(manifest.plugin_id, SandboxPolicy.default_deny())
        self.assertTrue(self.plugin_mgr.sandbox_manager.is_worker_alive(manifest.plugin_id))

        # Unload plugin
        self.plugin_mgr.unload_plugin(manifest.plugin_id)
        self.assertFalse(self.plugin_mgr.sandbox_manager.is_worker_alive(manifest.plugin_id))

    def test_sandbox_worker_terminates_on_plugin_destroy(self):
        """4. Verifies destroying a plugin terminates its subprocess worker."""
        manifest = PluginManifest(
            plugin_id="aegis.integration.sandbox_destroy",
            name="Destroy Sandbox Plugin",
            version="1.0.0"
        )

        class DummyPlugin(AegisPlugin):
            def get_manifest(self):
                return manifest

        inst = DummyPlugin()
        self.plugin_mgr.register_builtin(inst)
        self.plugin_mgr.load_plugin(manifest.plugin_id, inst)
        self.plugin_mgr.validate_plugin(manifest.plugin_id)
        self.plugin_mgr.resolve_dependencies()
        self.plugin_mgr.activate_plugin(manifest.plugin_id)

        self.plugin_mgr.sandbox_manager.spawn_worker(manifest.plugin_id, SandboxPolicy.default_deny())
        self.assertTrue(self.plugin_mgr.sandbox_manager.is_worker_alive(manifest.plugin_id))

        # Destroy plugin
        self.plugin_mgr.destroy_plugin(manifest.plugin_id)
        self.assertFalse(self.plugin_mgr.sandbox_manager.is_worker_alive(manifest.plugin_id))

    def test_sandbox_worker_ipc_check_permission(self):
        """5. Verifies sending CHECK_PERMISSIONS IPC request to running worker."""
        from runtime.src.sandbox import SandboxPermissionError
        manifest = PluginManifest(
            plugin_id="aegis.integration.perm_check",
            name="Perm Check Plugin",
            version="1.0.0"
        )
        policy = SandboxPolicy(allow_filesystem_read=True, allow_filesystem_write=False)
        self.plugin_mgr.sandbox_manager.spawn_worker(manifest.plugin_id, policy)

        req_read = SandboxRequest(command="CHECK_PERMISSIONS", payload={"permission": "FILESYSTEM_READ"}, plugin_id=manifest.plugin_id)
        resp_read = self.plugin_mgr.sandbox_manager.send_request(manifest.plugin_id, req_read)
        self.assertTrue(resp_read.success)

        req_write = SandboxRequest(command="CHECK_PERMISSIONS", payload={"permission": "FILESYSTEM_WRITE"}, plugin_id=manifest.plugin_id)
        with self.assertRaises(SandboxPermissionError):
            self.plugin_mgr.sandbox_manager.send_request(manifest.plugin_id, req_write)

    def test_sandbox_worker_atomic_swap_on_reload(self):
        """6. Verifies reloading plugin replaces old worker subprocess with fresh worker subprocess."""
        manifest = PluginManifest(
            plugin_id="aegis.integration.reload_swap",
            name="Reload Swap Plugin",
            version="1.0.0"
        )

        class DummyPlugin1(AegisPlugin):
            def get_manifest(self):
                return manifest

        class DummyPlugin2(AegisPlugin):
            def get_manifest(self):
                return manifest

        inst1 = DummyPlugin1()
        self.plugin_mgr.register_builtin(inst1)
        self.plugin_mgr.load_plugin(manifest.plugin_id, inst1)
        self.plugin_mgr.validate_plugin(manifest.plugin_id)
        self.plugin_mgr.resolve_dependencies()
        self.plugin_mgr.activate_plugin(manifest.plugin_id)


        p1 = self.plugin_mgr.sandbox_manager.spawn_worker(manifest.plugin_id, SandboxPolicy.default_deny())
        pid1 = p1.pid

        # Perform atomic reload
        inst2 = DummyPlugin2()
        self.plugin_mgr.reload_plugin(manifest.plugin_id, inst2)
        p2 = self.plugin_mgr.sandbox_manager.restart_worker(manifest.plugin_id)
        pid2 = p2.pid

        self.assertNotEqual(pid1, pid2)
        self.assertTrue(self.plugin_mgr.sandbox_manager.is_worker_alive(manifest.plugin_id))

    def test_sandbox_manager_tracks_multiple_workers(self):
        """7. Verifies SandboxManager manages multiple distinct plugin workers concurrently."""
        p1_id = "plugin.multi.1"
        p2_id = "plugin.multi.2"

        self.plugin_mgr.sandbox_manager.spawn_worker(p1_id, SandboxPolicy.default_deny())
        self.plugin_mgr.sandbox_manager.spawn_worker(p2_id, SandboxPolicy.default_deny())

        self.assertTrue(self.plugin_mgr.sandbox_manager.is_worker_alive(p1_id))
        self.assertTrue(self.plugin_mgr.sandbox_manager.is_worker_alive(p2_id))

        r1 = self.plugin_mgr.sandbox_manager.send_request(p1_id, SandboxRequest(command="HEALTHCHECK", payload={}, plugin_id=p1_id))
        r2 = self.plugin_mgr.sandbox_manager.send_request(p2_id, SandboxRequest(command="HEALTHCHECK", payload={}, plugin_id=p2_id))

        self.assertTrue(r1.success)
        self.assertTrue(r2.success)

    def test_sandbox_worker_healthcheck_metrics(self):
        """8. Verifies execution metrics returned in SandboxResponse."""
        pid = "plugin.metrics.test"
        self.plugin_mgr.sandbox_manager.spawn_worker(pid, SandboxPolicy.default_deny())
        resp = self.plugin_mgr.sandbox_manager.send_request(pid, SandboxRequest(command="HEALTHCHECK", payload={}, plugin_id=pid))

        self.assertIn("execution_time_ms", resp.metrics)
        self.assertGreaterEqual(resp.metrics["execution_time_ms"], 0.0)

    def test_sandbox_manager_restart_inactive_worker(self):
        """9. Verifies restart_worker spawns worker even if not previously spawned."""
        pid = "plugin.inactive.restart"
        p = self.plugin_mgr.sandbox_manager.restart_worker(pid)
        self.assertIsNotNone(p)
        self.assertTrue(self.plugin_mgr.sandbox_manager.is_worker_alive(pid))

    def test_sandbox_manager_terminate_all_subprocesses(self):
        """10. Verifies cleanup of all subprocess workers on teardown."""
        self.plugin_mgr.sandbox_manager.spawn_worker("w1", SandboxPolicy.default_deny())
        self.plugin_mgr.sandbox_manager.spawn_worker("w2", SandboxPolicy.default_deny())
        self.plugin_mgr.sandbox_manager.terminate_all()

        self.assertFalse(self.plugin_mgr.sandbox_manager.is_worker_alive("w1"))
        self.assertFalse(self.plugin_mgr.sandbox_manager.is_worker_alive("w2"))


if __name__ == "__main__":
    unittest.main()
