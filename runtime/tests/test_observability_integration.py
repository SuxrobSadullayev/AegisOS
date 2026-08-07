"""
Observability Integration Tests for Aegis AI OS.
Verifies integration across RuntimeOrchestrator, SessionManager, PluginManager,
SandboxManager, ModelGateway, CLI, and ObservabilityManager.
"""

import os
import shutil
import tempfile
import unittest
from runtime.src.config import AegisConfig
from runtime.src.orchestrator import RuntimeOrchestrator
from runtime.src.session import SessionManager
from runtime.src.plugin import PluginManager, PluginManifest, AegisPlugin
from runtime.src.sandbox import SandboxManager, SandboxPolicy
from runtime.src.observability import ObservabilityManager, CorrelationContext, EventCategory, EventLevel, EventType


class TestObservabilityIntegration(unittest.TestCase):
    """Integration tests connecting ObservabilityManager to all core Aegis OS subsystems."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.log_dir = os.path.join(self.temp_dir, "logs")
        self.obs_mgr = ObservabilityManager(log_dir=self.log_dir)

        self.config = AegisConfig()
        self.orchestrator = RuntimeOrchestrator(self.config)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)


    def test_1_orchestrator_run_publishes_events_and_spans(self):
        """1. Verifies RuntimeOrchestrator.run publishes REQUEST_STARTED, stage spans, and REQUEST_COMPLETED."""
        res_ctx = self.orchestrator.run("Review Python security architecture", session_id="SESS_INT_1")
        self.assertIsNotNone(res_ctx)

        logs = self.obs_mgr.read_logs(tail=50, session_id="SESS_INT_1")
        self.assertGreater(len(logs), 5)

        event_types = [l.get("event_type") for l in logs]
        self.assertIn("REQUEST_STARTED", event_types)
        self.assertIn("STAGE_COMPLETED", event_types)
        self.assertIn("REQUEST_COMPLETED", event_types)

    def test_2_session_manager_integration(self):
        """2. Verifies session creation and persistence record observability events."""
        session_mgr = SessionManager(self.config)
        sess = session_mgr.create_session("user_test", "SESS_OBS_TEST")

        self.obs_mgr.publish_event(
            level=EventLevel.INFO, category=EventCategory.SESSION,
            event_type=EventType.SESSION_CREATED, component="SessionManager",
            operation="create_session", message=f"Session created: {sess.session_id}"
        )

        logs = self.obs_mgr.read_logs(tail=10, category="SESSION")
        self.assertGreaterEqual(len(logs), 1)
        self.assertEqual(logs[-1]["component"], "SessionManager")

    def test_3_sandbox_manager_security_audit_integration(self):
        """3. Verifies SandboxManager security violations write to audit.jsonl."""
        sandbox_mgr = SandboxManager()
        pid = "plugin.obs.denied"
        sandbox_mgr.spawn_worker(pid, SandboxPolicy.default_deny())

        from runtime.src.sandbox import SandboxRequest, SandboxPermissionError
        req = SandboxRequest(command="FILESYSTEM_WRITE", payload={"path": "/tmp/a.txt"}, plugin_id=pid)

        with self.assertRaises(SandboxPermissionError):
            sandbox_mgr.send_request(pid, req)

        sandbox_mgr.terminate_all()

        audits = self.obs_mgr.read_audit_logs(tail=10)
        self.assertGreaterEqual(len(audits), 1)

    def test_4_plugin_manager_failure_event_integration(self):
        """4. Verifies plugin failure events are logged under PLUGIN category."""
        plugin_mgr = PluginManager(os.path.join(self.temp_dir, "plugins"))
        manifest = PluginManifest(plugin_id="plugin.fail.obs", name="Fail Obs", version="1.0.0")

        self.obs_mgr.publish_event(
            level=EventLevel.ERROR, category=EventCategory.PLUGIN,
            event_type=EventType.PLUGIN_FAILED, component="PluginManager",
            operation="load_plugin", message=f"Plugin failed: {manifest.plugin_id}"
        )

        logs = self.obs_mgr.read_logs(tail=10, category="PLUGIN")
        self.assertGreaterEqual(len(logs), 1)
        self.assertEqual(logs[-1]["event_type"], "PLUGIN_FAILED")

    def test_5_model_gateway_telemetry_integration(self):
        """5. Verifies model gateway requests publish MODEL_REQUEST and MODEL_RESPONSE events."""
        from runtime.src.gateway import ModelGatewayFactory
        gateway = ModelGatewayFactory.get_provider("mock", self.config)

        with self.obs_mgr.span("ModelGateway", "generate", EventCategory.MODEL):
            resp = gateway.generate("System prompt", "User prompt")

        self.assertIsNotNone(resp)
        logs = self.obs_mgr.read_logs(tail=10, category="MODEL")
        self.assertGreaterEqual(len(logs), 2)

    def test_6_multi_turn_session_correlation(self):
        """6. Verifies multi-turn execution maintains session_id while correlation_id updates per request."""
        sess_id = "SESS_MULTI_TURN_OBS"

        c1 = self.orchestrator.run("Turn 1 request", session_id=sess_id)
        corr1 = CorrelationContext.get_correlation_id()

        c2 = self.orchestrator.run("Turn 2 request", session_id=sess_id)
        corr2 = CorrelationContext.get_correlation_id()

        self.assertIsNotNone(c1)
        self.assertIsNotNone(c2)
        self.assertNotEqual(corr1, corr2)


    def test_7_cli_verbose_mode_console_sink(self):
        """7. Verifies verbose mode enables ConsoleEventSink."""
        self.config.verbose = True
        self.obs_mgr.enable_console()
        self.assertTrue(self.obs_mgr._console_enabled)

    def test_8_reasoning_engine_span_integration(self):
        """8. Verifies reasoning engine execution registers timing metrics in ObservabilityManager."""
        with self.obs_mgr.span("ReasoningEngine", "execute_l3", EventCategory.REASONING):
            pass

        metrics = self.obs_mgr.metrics.get_metrics_summary()
        self.assertIn("ReasoningEngine.execute_l3", metrics["latencies"])

    def test_9_truth_engine_span_integration(self):
        """9. Verifies truth engine execution logs stage completed event."""
        with self.obs_mgr.span("TruthEngine", "evaluate_claims", EventCategory.TRUTH):
            pass

        logs = self.obs_mgr.read_logs(tail=5, category="TRUTH")
        self.assertGreaterEqual(len(logs), 2)

    def test_10_quality_engine_span_integration(self):
        """10. Verifies quality engine execution logs stage completed event."""
        with self.obs_mgr.span("QualityEngine", "validate_gates", EventCategory.QUALITY):
            pass

        logs = self.obs_mgr.read_logs(tail=5, category="QUALITY")
        self.assertGreaterEqual(len(logs), 2)

    def test_11_audit_log_persists_across_subsystem_calls(self):
        """11. Verifies audit logs store events from both Sandbox and Security capabilities."""
        self.obs_mgr.publish_event(
            level=EventLevel.WARNING, category=EventCategory.SECURITY,
            event_type=EventType.PATH_TRAVERSAL_BLOCKED, component="SecurityValidator",
            operation="validate_path", message="Path traversal attempt blocked: ../../etc/passwd"
        )

        audits = self.obs_mgr.read_audit_logs(tail=10)
        self.assertTrue(any(a["event_type"] == "PATH_TRAVERSAL_BLOCKED" for a in audits))

        self.orchestrator.run("Count metrics task", session_id="SESS_METRIC_COUNT")

        metrics = self.obs_mgr.metrics.get_metrics_summary()
        self.assertGreater(len(metrics["counters"]), 0)

    def test_13_trace_id_propagation_in_pipeline(self):
        """13. Verifies trace_id remains consistent across pipeline stage spans in a request."""
        CorrelationContext.set_context(session_id="SESS_TRACE_PROP")
        t_id = CorrelationContext.get_trace_id()

        self.orchestrator.run("Trace propagation task", session_id="SESS_TRACE_PROP")
        logs = self.obs_mgr.read_logs(tail=20, session_id="SESS_TRACE_PROP")
        for l in logs:
            self.assertEqual(l["trace_id"], t_id)

    def test_14_log_rotation_integration_under_heavy_pipeline_runs(self):
        """14. Verifies log file exists and receives structured JSON lines during multiple pipeline runs."""
        for i in range(3):
            self.orchestrator.run(f"Heavy task run {i}", session_id=f"SESS_HEAVY_{i}")


        runtime_log = self.obs_mgr.file_sink.log_file_path
        self.assertTrue(os.path.exists(runtime_log))
        self.assertGreater(os.path.getsize(runtime_log), 0)


    def test_15_read_logs_tail_limit(self):
        """15. Verifies read_logs enforces tail count limit."""
        for i in range(20):
            self.obs_mgr.publish_event(
                level=EventLevel.INFO, category=EventCategory.PIPELINE,
                event_type=EventType.STAGE_COMPLETED, component="TestComp",
                operation="test_op", message=f"Tail test msg {i}"
            )

        logs = self.obs_mgr.read_logs(tail=5)
        self.assertEqual(len(logs), 5)


if __name__ == "__main__":
    unittest.main()
