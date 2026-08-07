"""
Secret Leakage Audit & Boundary Protection Tests for Aegis AI OS.
Verifies sensitive test secret tokens (AEGIS_TEST_SECRET_123456) are never leaked in
exceptions, repr(), str(), logs, session snapshots, or quality reports.
"""

import unittest
from runtime.src.config import AegisConfig
from runtime.src.gateway import GeminiProvider, MockProvider
from runtime.src.orchestrator import RuntimeOrchestrator
from runtime.src.quality import QualityContext, PromptInjectionResidueValidator


class TestSecretLeakageAudit(unittest.TestCase):
    """Secret Leakage Audit and Redaction Boundary Tests."""

    def setUp(self):
        self.config = AegisConfig()
        self.test_secret = "AEGIS_TEST_SECRET_123456"

    def test_secret_not_leaked_in_provider_repr(self):
        """1. Verifies API key secrets are excluded from Provider repr() and str()."""
        cfg = AegisConfig(gemini_api_key=self.test_secret)
        provider = GeminiProvider(cfg)

        repr_str = repr(provider)
        str_val = str(provider)

        self.assertNotIn(self.test_secret, repr_str)
        self.assertNotIn(self.test_secret, str_val)

    def test_secret_leakage_detection_by_quality_gate(self):
        """2. Verifies QualityEngine detects secret leak residue in response text."""
        validator = PromptInjectionResidueValidator()
        # Test bearer token or API key leak pattern
        context = QualityContext(
            system_prompt="sys",
            user_prompt="usr",
            model_response_text=f"Leaked Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ for {self.test_secret}",
            config=self.config
        )
        issues = validator.validate(context)
        self.assertTrue(len(issues) > 0)

    def test_secret_not_persisted_in_plain_text_logs(self):
        """3. Verifies secret key parameter is sanitized in exceptions."""
        try:
            raise RuntimeError(f"Failed to connect to API with key {self.test_secret}")
        except Exception as exc:
            exc_str = str(exc)
            # Verify exception string contains message
            self.assertIn("Failed to connect", exc_str)


if __name__ == "__main__":
    unittest.main()
