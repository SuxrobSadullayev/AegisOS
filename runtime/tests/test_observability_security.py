"""
Observability Security Tests for Aegis AI OS.
Verifies centralized secret redaction barrier for API keys, Bearer tokens, passwords,
private keys, authorization headers, nested dictionary keys, exceptions, and audit logs.
"""

import os
import shutil
import tempfile
import json
import unittest
from runtime.src.observability import (
    EventRedactor, EventSerializer, ObservabilityEvent,
    ObservabilityManager, EventLevel, EventCategory, EventType
)


class TestObservabilitySecurity(unittest.TestCase):
    """Security tests enforcing Zero Secret Leakage across logs, metadata, exceptions, and sinks."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.log_dir = os.path.join(self.temp_dir, "logs")
        self.obs_mgr = ObservabilityManager(log_dir=self.log_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_1_redact_google_api_key(self):
        """1. Verifies redaction of Google API Key pattern ('AIzaSy...')."""
        raw = "Using Google key AIzaSyA1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6"
        redacted = EventRedactor.redact_text(raw)
        self.assertNotIn("AIzaSy", redacted)
        self.assertIn("[REDACTED]", redacted)

    def test_2_redact_openai_anthropic_api_key(self):
        """2. Verifies redaction of OpenAI / Anthropic key pattern ('sk-...')."""
        raw = "Connecting with key sk-1234567890abcdefghijklmnopqrstuvwxyz"
        redacted = EventRedactor.redact_text(raw)
        self.assertNotIn("sk-1234567890", redacted)
        self.assertIn("[REDACTED]", redacted)

    def test_3_redact_bearer_token(self):
        """3. Verifies redaction of Bearer token in Authorization header."""
        raw = "Header Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIi"
        redacted = EventRedactor.redact_text(raw)
        self.assertNotIn("eyJhbGci", redacted)
        self.assertIn("[REDACTED]", redacted)

    def test_4_redact_password_field(self):
        """4. Verifies redaction of password assignment pattern."""
        raw = "Connection config PASSWORD='SuperSecretPassword123!'"
        redacted = EventRedactor.redact_text(raw)
        self.assertNotIn("SuperSecretPassword123!", redacted)
        self.assertIn("[REDACTED]", redacted)

    def test_5_redact_private_key_block(self):
        """5. Verifies redaction of PEM Private Key block."""
        raw = "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA0...\n-----END RSA PRIVATE KEY-----"
        redacted = EventRedactor.redact_text(raw)
        self.assertNotIn("MIIEowIBAAKCAQEA0", redacted)
        self.assertIn("[REDACTED]", redacted)

    def test_6_redact_sensitive_dict_keys(self):
        """6. Verifies dictionary redaction for sensitive keys ('api_key', 'password', 'token', 'secret')."""
        meta = {
            "api_key": "secret_key_value",
            "gemini_api_key": "AIzaSySecret123",
            "user": "aegis_admin",
            "nested": {
                "token": "tok_abcdef123456",
                "normal_field": 42
            }
        }
        redacted_meta = EventRedactor.redact_object(meta)
        self.assertEqual(redacted_meta["api_key"], "[REDACTED]")
        self.assertEqual(redacted_meta["gemini_api_key"], "[REDACTED]")
        self.assertEqual(redacted_meta["user"], "aegis_admin")
        self.assertEqual(redacted_meta["nested"]["token"], "[REDACTED]")
        self.assertEqual(redacted_meta["nested"]["normal_field"], 42)

    def test_7_redact_nested_list_of_secrets(self):
        """7. Verifies redaction inside nested lists."""
        payload = ["normal", "sk-1234567890abcdefghijklmnopqrstuvwxyz", {"secret": "my_secret_val"}]
        redacted = EventRedactor.redact_object(payload)
        self.assertEqual(redacted[0], "normal")
        self.assertEqual(redacted[1], "[REDACTED]")
        self.assertEqual(redacted[2]["secret"], "[REDACTED]")

    def test_8_redact_exception_message(self):
        """8. Verifies exception messages containing secret keys are redacted when published."""
        try:
            raise ValueError("Failed connecting with key AIzaSyA1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6")
        except ValueError as exc:
            evt = self.obs_mgr.publish_event(
                level=EventLevel.ERROR, category=EventCategory.ERROR,
                event_type=EventType.ERROR_UNHANDLED, component="TestSys",
                operation="test_op", message=str(exc)
            )

        self.assertNotIn("AIzaSyA1b2C3d4E5", evt.message)
        self.assertIn("[REDACTED]", evt.message)

    def test_9_secret_not_leaked_in_runtime_jsonl(self):
        """9. Verifies runtime.jsonl log file contains zero unredacted secrets."""
        self.obs_mgr.publish_event(
            level=EventLevel.INFO, category=EventCategory.PIPELINE,
            event_type=EventType.STAGE_COMPLETED, component="TestPipeline",
            operation="step", message="Process using sk-1234567890abcdefghijklmnopqrstuvwxyz",
            metadata={"secret_field": "AIzaSyA1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6"}
        )

        log_file = os.path.join(self.log_dir, "runtime.jsonl")
        with open(log_file, "r") as f:
            content = f.read()

        self.assertNotIn("sk-1234567890", content)
        self.assertNotIn("AIzaSyA1b2C3d4E5", content)
        self.assertIn("[REDACTED]", content)

    def test_10_secret_not_leaked_in_audit_jsonl(self):
        """10. Verifies audit.jsonl log file contains zero unredacted secrets."""
        self.obs_mgr.publish_event(
            level=EventLevel.WARNING, category=EventCategory.SECURITY,
            event_type=EventType.PERMISSION_DENIED, component="SecurityGate",
            operation="validate", message="Denied Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIi",
            metadata={"authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIi"}

        )

        audit_file = os.path.join(self.log_dir, "audit.jsonl")
        with open(audit_file, "r") as f:
            content = f.read()

        self.assertNotIn("eyJhbGciOiJIUzI1NiIs", content)
        self.assertIn("[REDACTED]", content)

    def test_11_capability_token_redaction(self):
        """11. Verifies CapabilityToken metadata key redaction."""
        meta = {"capability_token": "TOKEN_GRANTING_FILESYSTEM_READ_WRITE"}
        redacted = EventRedactor.redact_object(meta)
        self.assertEqual(redacted["capability_token"], "[REDACTED]")

    def test_12_environment_secret_pattern_redaction(self):
        """12. Verifies env variable assignment patterns are redacted."""
        raw = "Exporting GEMINI_API_KEY=AIzaSyA1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6"
        redacted = EventRedactor.redact_text(raw)
        self.assertNotIn("AIzaSyA1b2C3", redacted)
        self.assertIn("[REDACTED]", redacted)

    def test_13_serializer_applies_redaction_deterministically(self):
        """13. Verifies EventSerializer.serialize automatically redacts fields."""
        evt = ObservabilityEvent(
            event_id="EVT_SEC_SERIALIZE", correlation_id="C", request_id="R", session_id="S",
            trace_id="T", span_id="SP", parent_span_id="P", level="INFO",
            category="SECURITY", event_type="SECRET_ACCESS_DENIED", component="C", operation="o",
            duration_ms=0.0, success=False, message="Leaking sk-1234567890abcdefghijklmnopqrstuvwxyz",
            metadata={"password": "MySuperSecretPassword"}
        )
        json_str = EventSerializer.serialize(evt)
        self.assertNotIn("sk-1234567890", json_str)
        self.assertNotIn("MySuperSecretPassword", json_str)

    def test_14_tuple_metadata_redaction(self):
        """14. Verifies redaction inside tuple data structures."""
        tup = ("normal", "sk-1234567890abcdefghijklmnopqrstuvwxyz")
        redacted = EventRedactor.redact_object(tup)
        self.assertEqual(redacted[1], "[REDACTED]")

    def test_15_path_traversal_payload_logging_redacted(self):
        """15. Verifies path traversal messages are safely sanitized."""
        msg = "Blocked path traversal payload: ../../../etc/shadow with key sk-1234567890abcdefghijklmnopqrstuvwxyz"
        redacted = EventRedactor.redact_text(msg)
        self.assertNotIn("sk-1234567890", redacted)


if __name__ == "__main__":
    unittest.main()
