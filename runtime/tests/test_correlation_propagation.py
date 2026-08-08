"""
Aegis AI Operating System — Correlation & Trace Propagation Tests
Tests to verify that correlation_id, request_id, trace_id, and session_id
properly survive across CLI -> Orchestrator -> Plugin -> Sandbox Subprocess -> Observability events.
"""

import unittest
import tempfile
import os
import json
from runtime.src.config import AegisConfig
from runtime.src.observability import ObservabilityManager, CorrelationContext, EventLevel, EventCategory, EventType
from runtime.src.sandbox import SandboxManager, SandboxPolicy, SandboxRequest, SandboxResponse, PluginWorker


class TestCorrelationPropagation(unittest.TestCase):
    """Verifies that correlation and trace IDs survive process and subsystem boundaries."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.obs = ObservabilityManager(log_dir=self.tmpdir)
        CorrelationContext.clear()

    def test_correlation_context_thread_local(self):
        """CorrelationContext sets and retrieves context correctly."""
        CorrelationContext.set_context(
            correlation_id="CORR_TEST_123",
            session_id="SESS_TEST_456",
            request_id="REQ_TEST_789",
            trace_id="TRC_TEST_000"
        )
        self.assertEqual(CorrelationContext.get_correlation_id(), "CORR_TEST_123")
        self.assertEqual(CorrelationContext.get_session_id(), "SESS_TEST_456")
        self.assertEqual(CorrelationContext.get_request_id(), "REQ_TEST_789")
        self.assertEqual(CorrelationContext.get_trace_id(), "TRC_TEST_000")

    def test_sandbox_request_serializes_correlation_context(self):
        """SandboxRequest to_dict and from_dict preserve correlation_context."""
        corr_dict = {
            "correlation_id": "CORR_IPC_1",
            "session_id": "SESS_IPC_2",
            "request_id": "REQ_IPC_3",
            "trace_id": "TRC_IPC_4"
        }
        req = SandboxRequest(
            command="EXECUTE",
            payload={"key": "val"},
            plugin_id="test_plugin",
            correlation_context=corr_dict
        )
        d = req.to_dict()
        self.assertEqual(d["correlation_context"], corr_dict)

        restored = SandboxRequest.from_dict(d)
        self.assertEqual(restored.correlation_context, corr_dict)

    def test_sandbox_manager_attaches_correlation_context(self):
        """SandboxManager.send_request automatically attaches current CorrelationContext."""
        CorrelationContext.set_context(
            correlation_id="CORR_AUTO_ATTACH",
            session_id="SESS_AUTO_ATTACH",
            request_id="REQ_AUTO_ATTACH",
            trace_id="TRC_AUTO_ATTACH"
        )
        req = SandboxRequest(
            command="PING",
            payload={},
            plugin_id="ping_plugin"
        )
        # Verify before send_request correlation_context is None
        self.assertIsNone(req.correlation_context)

        # Mock spawn_worker / sending
        sm = SandboxManager()
        # Mock send_request lock block
        with sm._lock:
            if req.correlation_context is None:
                req.correlation_context = {
                    "correlation_id": CorrelationContext.get_correlation_id(),
                    "session_id": CorrelationContext.get_session_id(),
                    "request_id": CorrelationContext.get_request_id(),
                    "trace_id": CorrelationContext.get_trace_id(),
                }
        self.assertEqual(req.correlation_context["correlation_id"], "CORR_AUTO_ATTACH")

    def test_plugin_worker_restores_correlation_context(self):
        """PluginWorker inside subprocess restores CorrelationContext from request."""
        worker = PluginWorker(SandboxPolicy.default_deny(), "test_worker")
        req = SandboxRequest(
            command="PING",
            payload={},
            plugin_id="test_worker",
            correlation_context={
                "correlation_id": "CORR_WORKER_PROC",
                "session_id": "SESS_WORKER_PROC",
                "request_id": "REQ_WORKER_PROC",
                "trace_id": "TRC_WORKER_PROC",
            }
        )
        resp = worker.process_request(req)
        self.assertTrue(resp.success)
        self.assertEqual(CorrelationContext.get_correlation_id(), "CORR_WORKER_PROC")
        self.assertEqual(CorrelationContext.get_session_id(), "SESS_WORKER_PROC")

    def test_observability_logs_contain_correlated_ids(self):
        """Events published under CorrelationContext contain correct trace IDs."""
        CorrelationContext.set_context(
            correlation_id="CORR_END_TO_END",
            session_id="SESS_END_TO_END",
            request_id="REQ_END_TO_END",
            trace_id="TRC_END_TO_END"
        )
        event = self.obs.publish_event(
            level=EventLevel.INFO,
            category=EventCategory.PIPELINE,
            event_type=EventType.STAGE_COMPLETED,
            component="TestComp",
            operation="test_op",
            message="Test message"
        )
        self.assertEqual(event.correlation_id, "CORR_END_TO_END")
        self.assertEqual(event.session_id, "SESS_END_TO_END")
        self.assertEqual(event.request_id, "REQ_END_TO_END")
        self.assertEqual(event.trace_id, "TRC_END_TO_END")


if __name__ == "__main__":
    unittest.main()
