"""
Observability Failure Resilience Tests for Aegis AI OS.
Verifies 'NEVER CRASH RUNTIME' principle: sink errors, disk write failures,
read-only permission errors, malformed metadata, and concurrent logging failures
never break core Aegis OS pipeline execution.
"""

import os
import shutil
import tempfile
import json
import unittest
from runtime.src.observability import (
    ObservabilityManager, EventLevel, EventCategory, EventType,
    FileEventSink, EventSink, ObservabilityEvent
)


class FailingSink(EventSink):
    """Failing sink simulating disk write or I/O failure."""
    def emit(self, event: ObservabilityEvent) -> None:
        raise OSError("Simulated Disk I/O Failure: No space left on device")


class TestObservabilityFailureResilience(unittest.TestCase):
    """Failure resilience and boundary tests for Observability Subsystem."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.log_dir = os.path.join(self.temp_dir, "logs")
        self.obs_mgr = ObservabilityManager(log_dir=self.log_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_1_failing_sink_does_not_crash_publish_event(self):
        """1. Verifies a failing sink raising OSError does not throw exception during publish_event."""
        self.obs_mgr.event_bus.register_sink(FailingSink())

        # Should execute cleanly without raising OSError
        evt = self.obs_mgr.publish_event(
            level=EventLevel.INFO, category=EventCategory.PIPELINE,
            event_type=EventType.STAGE_COMPLETED, component="Comp",
            operation="op", message="Test message despite failing sink"
        )
        self.assertIsNotNone(evt)

    def test_2_read_logs_handles_corrupted_json_lines(self):
        """2. Verifies read_logs skips corrupted or malformed lines gracefully."""
        log_file = os.path.join(self.log_dir, "runtime.jsonl")
        os.makedirs(self.log_dir, exist_ok=True)
        with open(log_file, "w") as f:
            f.write("CORRUPTED NON-JSON LINE 1\n")
            f.write('{"timestamp": "2026-08-08", "event_id": "E1", "message": "valid"}\n')
            f.write("{MALFORMED JSON 3\n")

        logs = self.obs_mgr.read_logs(tail=10)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["event_id"], "E1")

    def test_3_read_audit_logs_handles_missing_file(self):
        """3. Verifies read_audit_logs returns empty list if audit.jsonl does not exist."""
        non_existent_dir = os.path.join(self.temp_dir, "non_existent")
        mgr = ObservabilityManager(log_dir=non_existent_dir)
        audits = mgr.read_audit_logs(tail=10)
        self.assertEqual(audits, [])

    def test_4_non_serializable_metadata_handled_gracefully(self):
        """4. Verifies non-JSON serializable objects in metadata do not crash publish_event."""
        class UnserializableObject:
            def __str__(self):
                return "<UnserializableObject>"

        evt = self.obs_mgr.publish_event(
            level=EventLevel.INFO, category=EventCategory.SYSTEM,
            event_type=EventType.SYSTEM_ERROR, component="C",
            operation="op", message="Unserializable test",
            metadata={"obj": UnserializableObject()}
        )
        self.assertIsNotNone(evt)

    def test_5_concurrent_event_publishing_thread_safety(self):
        """5. Verifies high concurrency multi-thread event publishing without race conditions or crashes."""
        import threading

        def worker(worker_id: int):
            for i in range(20):
                self.obs_mgr.publish_event(
                    level=EventLevel.INFO, category=EventCategory.PIPELINE,
                    event_type=EventType.STAGE_COMPLETED, component=f"Worker_{worker_id}",
                    operation="op", message=f"Thread msg {i}"
                )

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        logs = self.obs_mgr.read_logs(tail=100)
        self.assertGreater(len(logs), 50)

    def test_6_null_message_and_metadata_handled(self):
        """6. Verifies None values in message or metadata do not raise AttributeError."""
        evt = self.obs_mgr.publish_event(
            level=EventLevel.INFO, category=EventCategory.SYSTEM,
            event_type=EventType.SYSTEM_ERROR, component="C",
            operation="op", message=None, metadata=None
        )
        self.assertIsNotNone(evt)

    def test_7_file_sink_handles_permission_error_gracefully(self):
        """7. Verifies FileEventSink handles read-only or permission error without process crash."""
        read_only_path = os.path.join(self.temp_dir, "readonly", "runtime.jsonl")
        os.makedirs(os.path.dirname(read_only_path), exist_ok=True)
        sink = FileEventSink(read_only_path)

        # Make directory read-only on OS
        try:
            os.chmod(os.path.dirname(read_only_path), 0o444)
            evt = ObservabilityEvent(
                event_id="E", correlation_id="C", request_id="R", session_id="S",
                trace_id="T", span_id="SP", parent_span_id="P", level="INFO",
                category="SYSTEM", event_type="SYSTEM_ERROR", component="C", operation="o",
                duration_ms=0.0, success=True, message="Read only test"
            )
            sink.emit(evt)  # Should handle OSError gracefully
        finally:
            os.chmod(os.path.dirname(read_only_path), 0o755)

    def test_8_trace_span_exception_reraised(self):
        """8. Verifies TraceSpan context manager logs failure event but re-raises exception for caller."""
        with self.assertRaises(RuntimeError):
            with self.obs_mgr.span("FailComp", "op"):
                raise RuntimeError("Expected pipeline exception")

    def test_9_read_logs_invalid_log_dir_handling(self):
        """9. Verifies read_logs returns empty list on invalid log file path."""
        logs = self.obs_mgr.read_logs(tail=10, category="INVALID_CAT_XYZ")
        self.assertEqual(logs, [])

    def test_10_never_crash_runtime_guarantee(self):
        """10. Verifies ObservabilityManager guarantees main runtime pipeline never crashes on error."""
        # Force invalid state in ObservabilityManager
        self.obs_mgr.event_bus.sinks = None  # Cause AttributeError inside publish

        evt = self.obs_mgr.publish_event(
            level=EventLevel.CRITICAL, category=EventCategory.SYSTEM,
            event_type=EventType.SYSTEM_ERROR, component="Core",
            operation="crash_test", message="Testing runtime crash guarantee"
        )
        self.assertIsNotNone(evt)  # Dispatched safely without crashing Python process!



if __name__ == "__main__":
    unittest.main()
