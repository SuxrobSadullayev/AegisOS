"""
Observability Unit Tests for Aegis AI OS.
Verifies ObservabilityEvent data model, JSON serialization, CorrelationContext, TraceSpan,
FileEventSink with log rotation, AuditEventSink, and ObservabilityManager.
"""

import os
import shutil
import tempfile
import json
import unittest
from runtime.src.observability import (
    ObservabilityManager, ObservabilityEvent, EventLevel, EventCategory, EventType,
    CorrelationContext, EventSerializer, EventRedactor, FileEventSink, AuditEventSink,
    ConsoleEventSink, MetricsCollector
)



class TestObservabilityUnit(unittest.TestCase):
    """Unit tests covering core Observability Data Model, Serializers, Sinks, and Contexts."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.obs_mgr = ObservabilityManager(log_dir=os.path.join(self.temp_dir, "logs"))

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_1_event_data_model_defaults(self):
        """1. Verifies ObservabilityEvent dataclass defaults and to_dict format."""
        evt = ObservabilityEvent(
            event_id="EVT_1",
            correlation_id="CORR_1",
            request_id="REQ_1",
            session_id="SESS_1",
            trace_id="TRC_1",
            span_id="SPN_1",
            parent_span_id="SPN_0",
            level="INFO",
            category="PIPELINE",
            event_type="STAGE_COMPLETED",
            component="TestComp",
            operation="test_op",
            duration_ms=1.5,
            success=True,
            message="Test message",
            metadata={"key": "val"}
        )
        d = evt.to_dict()
        self.assertEqual(d["event_id"], "EVT_1")
        self.assertEqual(d["level"], "INFO")
        self.assertEqual(d["category"], "PIPELINE")
        self.assertIn("timestamp", d)

    def test_2_event_serializer_json(self):
        """2. Verifies EventSerializer outputs valid JSON string."""
        evt = ObservabilityEvent(
            event_id="EVT_2",
            correlation_id="CORR_2",
            request_id="REQ_2",
            session_id="SESS_2",
            trace_id="TRC_2",
            span_id="SPN_2",
            parent_span_id="SPN_ROOT",
            level="WARNING",
            category="SECURITY",
            event_type="PERMISSION_DENIED",
            component="Sandbox",
            operation="write",
            duration_ms=0.0,
            success=False,
            message="Access denied"
        )
        serialized = EventSerializer.serialize(evt)
        parsed = json.loads(serialized)
        self.assertEqual(parsed["event_id"], "EVT_2")
        self.assertEqual(parsed["level"], "WARNING")

    def test_3_correlation_context_defaults(self):
        """3. Verifies CorrelationContext generates thread-local IDs."""
        CorrelationContext.set_context(session_id="SESS_ABC", request_id="REQ_123")
        self.assertEqual(CorrelationContext.get_session_id(), "SESS_ABC")
        self.assertEqual(CorrelationContext.get_request_id(), "REQ_123")
        self.assertTrue(CorrelationContext.get_correlation_id().startswith("CORR_"))
        self.assertTrue(CorrelationContext.get_trace_id().startswith("TRC_"))

    def test_4_correlation_context_nested_spans(self):
        """4. Verifies push_span and pop_span parent-child relationships."""
        CorrelationContext.clear()
        self.assertEqual(CorrelationContext.get_current_span_id(), "SPN_ROOT")

        CorrelationContext.push_span("SPN_PARENT")
        self.assertEqual(CorrelationContext.get_current_span_id(), "SPN_PARENT")
        self.assertEqual(CorrelationContext.get_parent_span_id(), "SPN_ROOT")

        CorrelationContext.push_span("SPN_CHILD")
        self.assertEqual(CorrelationContext.get_current_span_id(), "SPN_CHILD")
        self.assertEqual(CorrelationContext.get_parent_span_id(), "SPN_PARENT")

        popped = CorrelationContext.pop_span()
        self.assertEqual(popped, "SPN_CHILD")
        self.assertEqual(CorrelationContext.get_current_span_id(), "SPN_PARENT")

    def test_5_trace_span_context_manager_success(self):
        """5. Verifies TraceSpan context manager records execution duration on success."""
        with self.obs_mgr.span("TestComponent", "execute") as span:
            self.assertTrue(span.span_id.startswith("SPN_TestComponent_"))

        metrics = self.obs_mgr.metrics.get_metrics_summary()
        self.assertIn("TestComponent.execute", metrics["latencies"])
        self.assertEqual(metrics["counters"]["TestComponent.calls"], 1)

    def test_6_trace_span_context_manager_failure(self):
        """6. Verifies TraceSpan context manager records failure and re-raises exception."""
        with self.assertRaises(ValueError):
            with self.obs_mgr.span("FailComponent", "execute"):
                raise ValueError("Simulated stage error")

        metrics = self.obs_mgr.metrics.get_metrics_summary()
        self.assertEqual(metrics["counters"]["FailComponent.failures"], 1)

    def test_7_file_event_sink_emission(self):
        """7. Verifies FileEventSink writes JSON lines to runtime.jsonl."""
        log_file = os.path.join(self.temp_dir, "runtime.jsonl")
        sink = FileEventSink(log_file)

        evt = ObservabilityEvent(
            event_id="EVT_FILE_1",
            correlation_id="C1", request_id="R1", session_id="S1", trace_id="T1",
            span_id="SP1", parent_span_id="SP0", level="INFO", category="SYSTEM",
            event_type="SYSTEM_ERROR", component="Sys", operation="op",
            duration_ms=10.0, success=True, message="File log test"
        )
        sink.emit(evt)

        self.assertTrue(os.path.exists(log_file))
        with open(log_file, "r") as f:
            line = f.readline()
            data = json.loads(line)
            self.assertEqual(data["event_id"], "EVT_FILE_1")

    def test_8_file_event_sink_log_rotation(self):
        """8. Verifies FileEventSink rotates log files when max_bytes limit is exceeded."""
        log_file = os.path.join(self.temp_dir, "rotate.jsonl")
        # Small max_bytes limit to trigger rotation
        sink = FileEventSink(log_file, max_bytes=300, backup_count=3)

        for i in range(10):
            evt = ObservabilityEvent(
                event_id=f"EVT_ROTATE_{i}",
                correlation_id="C", request_id="R", session_id="S", trace_id="T",
                span_id="SP", parent_span_id="P", level="INFO", category="SYSTEM",
                event_type="SYSTEM_ERROR", component="Comp", operation="op",
                duration_ms=1.0, success=True, message="Rotation payload text line " * 3
            )
            sink.emit(evt)

        self.assertTrue(os.path.exists(log_file))
        self.assertTrue(os.path.exists(f"{log_file}.1"))

    def test_9_audit_event_sink_filtering(self):
        """9. Verifies AuditEventSink only records SECURITY category events."""
        audit_file = os.path.join(self.temp_dir, "audit.jsonl")
        sink = AuditEventSink(audit_file)

        non_sec_evt = ObservabilityEvent(
            event_id="EVT_NON_SEC",
            correlation_id="C", request_id="R", session_id="S", trace_id="T",
            span_id="SP", parent_span_id="P", level="INFO", category="PIPELINE",
            event_type="STAGE_COMPLETED", component="Pipe", operation="op",
            duration_ms=1.0, success=True, message="Normal pipeline event"
        )
        sink.emit(non_sec_evt)

        sec_evt = ObservabilityEvent(
            event_id="EVT_SEC_AUDIT",
            correlation_id="C", request_id="R", session_id="S", trace_id="T",
            span_id="SP", parent_span_id="P", level="WARNING", category="SECURITY",
            event_type="PERMISSION_DENIED", component="Sandbox", operation="write",
            duration_ms=0.0, success=False, message="Security audit event"
        )
        sink.emit(sec_evt)

        self.assertTrue(os.path.exists(audit_file))
        with open(audit_file, "r") as f:
            lines = f.readlines()
            self.assertEqual(len(lines), 1)
            data = json.loads(lines[0])
            self.assertEqual(data["event_id"], "EVT_SEC_AUDIT")

    def test_10_read_logs_and_audit_logs(self):
        """10. Verifies ObservabilityManager.read_logs and read_audit_logs."""
        self.obs_mgr.publish_event(
            level=EventLevel.INFO, category=EventCategory.PIPELINE,
            event_type=EventType.STAGE_COMPLETED, component="C1", operation="op",
            message="Msg 1"
        )
        self.obs_mgr.publish_event(
            level=EventLevel.WARNING, category=EventCategory.SECURITY,
            event_type=EventType.PERMISSION_DENIED, component="C2", operation="op",
            message="Msg Security"
        )

        logs = self.obs_mgr.read_logs(tail=10)
        self.assertGreaterEqual(len(logs), 2)

        audits = self.obs_mgr.read_audit_logs(tail=10)
        self.assertGreaterEqual(len(audits), 1)
        self.assertEqual(audits[-1]["category"], "SECURITY")

    def test_11_event_level_enum(self):
        """11. Verifies EventLevel enum values."""
        self.assertEqual(EventLevel.INFO.value, "INFO")
        self.assertEqual(EventLevel.ERROR.value, "ERROR")

    def test_12_event_category_enum(self):
        """12. Verifies EventCategory enum values."""
        self.assertEqual(EventCategory.SECURITY.value, "SECURITY")
        self.assertEqual(EventCategory.MODEL.value, "MODEL")

    def test_13_event_type_enum(self):
        """13. Verifies EventType enum values."""
        self.assertEqual(EventType.REQUEST_STARTED.value, "REQUEST_STARTED")
        self.assertEqual(EventType.SANDBOX_VIOLATION.value, "SANDBOX_VIOLATION")

    def test_14_correlation_context_clear(self):
        """14. Verifies CorrelationContext.clear resets thread-local state."""
        CorrelationContext.set_context(session_id="SESS_TEMP")
        CorrelationContext.clear()
        self.assertEqual(CorrelationContext.get_session_id(), "SESS_GLOBAL")

    def test_15_console_event_sink_emission(self):
        """15. Verifies ConsoleEventSink handles emission without exceptions."""
        sink = ConsoleEventSink()
        evt = ObservabilityEvent(
            event_id="EVT_CON", correlation_id="C", request_id="R", session_id="S",
            trace_id="T", span_id="SP", parent_span_id="P", level="INFO",
            category="CLI", event_type="STAGE_COMPLETED", component="CLI", operation="print",
            duration_ms=1.0, success=True, message="Console output test"
        )
        sink.emit(evt)  # Should execute cleanly without error

    def test_16_file_event_sink_directory_creation(self):
        """16. Verifies FileEventSink creates log directory automatically."""
        nested_log_dir = os.path.join(self.temp_dir, "nested", "path", "logs", "runtime.jsonl")
        sink = FileEventSink(nested_log_dir)
        evt = ObservabilityEvent(
            event_id="E", correlation_id="C", request_id="R", session_id="S",
            trace_id="T", span_id="SP", parent_span_id="P", level="INFO",
            category="SYSTEM", event_type="SYSTEM_ERROR", component="C", operation="o",
            duration_ms=0.0, success=True, message="Nested file creation test"
        )
        sink.emit(evt)
        self.assertTrue(os.path.exists(nested_log_dir))

    def test_17_metrics_collector_increment(self):
        """17. Verifies MetricsCollector counter increments."""
        metrics = MetricsCollector()
        metrics.increment("pipeline.success", 1)
        metrics.increment("pipeline.success", 2)
        summary = metrics.get_metrics_summary()
        self.assertEqual(summary["counters"]["pipeline.success"], 3)

    def test_18_metrics_collector_percentiles(self):
        """18. Verifies MetricsCollector percentile calculation accuracy."""
        metrics = MetricsCollector()
        for i in range(1, 101):
            metrics.record_latency("test_lat", float(i))

        self.assertEqual(metrics.get_percentile("test_lat", 50.0), 50.5)
        self.assertEqual(metrics.get_percentile("test_lat", 95.0), 95.05)
        self.assertEqual(metrics.get_percentile("test_lat", 99.0), 99.01)

    def test_19_observability_manager_singleton(self):
        """19. Verifies ObservabilityManager behaves as a thread-safe singleton."""
        m1 = ObservabilityManager.get_instance()
        m2 = ObservabilityManager.get_instance()
        self.assertIs(m1, m2)

    def test_20_observability_manager_enable_console(self):
        """20. Verifies enable_console registers ConsoleEventSink."""
        self.obs_mgr.enable_console()
        self.assertTrue(self.obs_mgr._console_enabled)

    def test_21_read_logs_category_filtering(self):
        """21. Verifies read_logs filters by EventCategory."""
        self.obs_mgr.publish_event(
            level=EventLevel.INFO, category=EventCategory.MODEL,
            event_type=EventType.MODEL_REQUEST, component="Gateway", operation="req",
            message="Model req"
        )
        logs = self.obs_mgr.read_logs(tail=10, category="MODEL")
        self.assertTrue(all(l["category"] == "MODEL" for l in logs))

    def test_22_read_logs_session_filtering(self):
        """22. Verifies read_logs filters by session_id."""
        CorrelationContext.set_context(session_id="SESS_FILTER_1")
        self.obs_mgr.publish_event(
            level=EventLevel.INFO, category=EventCategory.SESSION,
            event_type=EventType.SESSION_STARTED, component="Sess", operation="start",
            message="Sess 1"
        )
        logs = self.obs_mgr.read_logs(tail=10, session_id="SESS_FILTER_1")
        self.assertTrue(all(l["session_id"] == "SESS_FILTER_1" for l in logs))

    def test_23_event_serializer_custom_metadata(self):
        """23. Verifies serialization of complex event metadata dictionaries."""
        evt = ObservabilityEvent(
            event_id="EVT_META", correlation_id="C", request_id="R", session_id="S",
            trace_id="T", span_id="SP", parent_span_id="P", level="INFO",
            category="PIPELINE", event_type="STAGE_COMPLETED", component="C", operation="o",
            duration_ms=2.0, success=True, message="Meta test",
            metadata={"nested": {"count": 10, "items": ["a", "b"]}}
        )
        serialized = EventSerializer.serialize(evt)
        parsed = json.loads(serialized)
        self.assertEqual(parsed["metadata"]["nested"]["count"], 10)

    def test_24_trace_span_parent_span_tracking(self):
        """24. Verifies nested TraceSpans link parent_span_id to parent span."""
        CorrelationContext.clear()
        with self.obs_mgr.span("ParentComp", "execute") as p_span:
            with self.obs_mgr.span("ChildComp", "execute") as c_span:
                self.assertEqual(c_span.parent_span_id, p_span.span_id)

    def test_25_read_audit_logs_severity_filtering(self):
        """25. Verifies read_audit_logs filters by severity level."""
        self.obs_mgr.publish_event(
            level=EventLevel.ERROR, category=EventCategory.SECURITY,
            event_type=EventType.SECURITY_POLICY_VIOLATION, component="Sec", operation="check",
            message="Audit error"
        )
        audits = self.obs_mgr.read_audit_logs(tail=10, severity="ERROR")
        self.assertTrue(all(a["level"] == "ERROR" for a in audits))


if __name__ == "__main__":
    unittest.main()
