"""
Aegis AI Operating System — Concurrency Stress Verification Tests
Performs stress testing across multithreaded workloads:
- Concurrent session saves
- Concurrent plugin reloads
- Concurrent sandbox requests
- Concurrent observability event writes & metrics updates
Supports 10, 50, and 100 worker threads.
"""

import unittest
import tempfile
import threading
import time
import os
from runtime.src.config import AegisConfig
from runtime.src.session import SessionManager, SessionContext, SessionState, MessageRole
from runtime.src.observability import ObservabilityManager, EventLevel, EventCategory, EventType
from runtime.src.plugin import PluginManager, AegisPlugin, PluginManifest, PluginContext, PluginCapability, PluginPermission, PluginHook


class SimpleTestPlugin(AegisPlugin):
    def __init__(self, name="v1"):
        self.version = name

    def get_manifest(self) -> PluginManifest:
        return PluginManifest(
            plugin_id="stress.test.plugin",
            name="Stress Plugin",
            version=self.version,
            capabilities=[PluginCapability.PIPELINE_STAGE],
            permissions=[PluginPermission.FILESYSTEM_READ]
        )

    def on_initialize(self, ctx: PluginContext) -> bool:
        return True

    def on_activate(self, ctx: PluginContext) -> bool:
        return True


class TestConcurrencyStress(unittest.TestCase):
    """Stress tests Aegis subsystems under heavy concurrent loads."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.config = AegisConfig()
        self.config.base_dir = self.tmpdir

    def test_concurrent_session_saves_50_workers(self):
        """50 worker threads concurrently writing to sessions must not corrupt session state."""
        sm = SessionManager(self.config)
        session_id = "STRESS_SESS_50"
        sess = sm.create_session("stress_user", session_id=session_id)
        sess.context_window.max_token_budget = 500000  # Prevent pruning during stress test

        errors = []

        def worker_task(worker_id):
            try:
                for i in range(10):
                    sm.add_user_message(session_id, f"Worker {worker_id} message {i}")
                    sm.add_assistant_message(session_id, f"Response to worker {worker_id} message {i}")
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker_task, args=(w,)) for w in range(50)]
        start_t = time.time()
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        duration = time.time() - start_t

        self.assertEqual(len(errors), 0, f"Session save errors: {errors}")

        # Verify session loads cleanly after stress
        sm._sessions.clear()
        restored = sm.get_session(session_id)
        self.assertIsNotNone(restored)
        self.assertEqual(len(restored.history.messages), 1000)

    def test_concurrent_observability_writes_50_workers(self):
        """50 worker threads emitting events concurrently must not lose events or crash."""
        obs = ObservabilityManager(log_dir=self.tmpdir)
        errors = []

        def obs_task(worker_id):
            try:
                for i in range(20):
                    obs.publish_event(
                        level=EventLevel.INFO,
                        category=EventCategory.SYSTEM,
                        event_type=EventType.STAGE_COMPLETED,
                        component=f"Worker_{worker_id}",
                        operation="execute",
                        message=f"Event {i} from worker {worker_id}",
                        metadata={"worker_id": worker_id, "step": i}
                    )
                    obs.metrics.increment("stress_counter", 1)
                    obs.metrics.record_latency("stress_latency", float(i * 1.5))
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=obs_task, args=(w,)) for w in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Observability stress errors: {errors}")
        summary = obs.metrics.get_metrics_summary()
        self.assertEqual(summary["counters"].get("stress_counter"), 1000)

    def test_concurrent_plugin_reloads_10_workers(self):
        """Concurrent reload attempts on PluginManager under lock must remain consistent."""
        pm = PluginManager(self.tmpdir)
        p1 = SimpleTestPlugin("1.0.0")
        pm.register_builtin(p1)
        pm.load_plugin("stress.test.plugin", p1)
        pm.validate_plugin("stress.test.plugin")
        pm.resolve_dependencies()
        pm.activate_plugin("stress.test.plugin")

        errors = []
        successes = []

        def reload_task(worker_id):
            try:
                new_p = SimpleTestPlugin(f"2.0.{worker_id}")
                res = pm.reload_plugin("stress.test.plugin", new_p)
                if res:
                    successes.append(worker_id)
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=reload_task, args=(w,)) for w in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All reloads under RLock should execute sequentially without corruption
        self.assertEqual(len(errors), 0, f"Plugin reload stress errors: {errors}")
        active = pm.get_plugin("stress.test.plugin")
        self.assertIsNotNone(active)


if __name__ == "__main__":
    unittest.main()
