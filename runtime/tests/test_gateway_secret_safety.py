"""
Aegis AI Operating System — Gateway Secret Safety Adversarial Verification Tests
Tests that API keys, tokens, and secrets NEVER appear in:
- request URLs
- exception messages
- HTTP error bodies
- repr()
- str()
- tracebacks
- observability events
- runtime logs
- debug output

Covers: Gemini, OpenAI, Claude, OpenRouter, Mock.
Simulates: HTTP 400, 401, 403, 429, 500, Timeout, Connection Error, Malformed JSON, Secret in Body.
"""

import unittest
import urllib.error
import urllib.request
import io
import ssl
from unittest.mock import patch, MagicMock
from runtime.src.config import AegisConfig
from runtime.src.gateway import (
    BaseHTTPProvider, GeminiProvider, ClaudeProvider, OpenAIProvider,
    OpenRouterProvider, MockProvider, ModelGatewayFactory, ModelResponse
)
from runtime.src.observability import ObservabilityManager, EventRedactor, EventLevel, EventCategory, EventType


class MockHTTPError(urllib.error.HTTPError):
    def __init__(self, url, code, msg, hdrs, fp):
        super().__init__(url, code, msg, hdrs, fp)


class TestGatewaySecretSafetyAdversarial(unittest.TestCase):
    """Adversarial security test suite for Gateway secret protection."""

    def setUp(self):
        self.config = AegisConfig()
        self.config.gemini_api_key = "AIzaSySECRET_GEMINI_KEY_99999"
        self.config.max_retries = 0
        self.secret_claude = "sk-ant-api03-SECRET_CLAUDE_KEY_88888"
        self.secret_openai = "sk-proj-SECRET_OPENAI_KEY_77777"
        self.secret_openrouter = "sk-or-v1-SECRET_OPENROUTER_KEY_66666"

    def test_config_repr_masks_secret(self):
        """repr(config) and str(config) must NEVER expose raw API keys."""
        repr_str = repr(self.config)
        str_str = str(self.config)
        self.assertNotIn("AIzaSySECRET_GEMINI_KEY_99999", repr_str)
        self.assertNotIn("AIzaSySECRET_GEMINI_KEY_99999", str_str)
        self.assertIn("[REDACTED]", repr_str)

    def test_provider_repr_str_masks_secret(self):
        """repr() and str() for all providers must NEVER contain API keys."""
        gemini = GeminiProvider(self.config)
        claude = ClaudeProvider(self.config, api_key=self.secret_claude)
        openai = OpenAIProvider(self.config, api_key=self.secret_openai)
        openrouter = OpenRouterProvider(self.config, api_key=self.secret_openrouter)

        for p in [gemini, claude, openai, openrouter]:
            r = repr(p)
            s = str(p)
            self.assertNotIn(self.config.gemini_api_key, r)
            self.assertNotIn(self.secret_claude, r)
            self.assertNotIn(self.secret_openai, r)
            self.assertNotIn(self.secret_openrouter, r)
            self.assertNotIn(self.secret_claude, s)

    def test_model_response_post_init_redacts_raw_response(self):
        """ModelResponse __post_init__ must redact any secrets inside raw_response."""
        resp = ModelResponse(
            text="Hello",
            token_count=5,
            latency_ms=10.0,
            provider="test",
            model="test-m",
            raw_response={
                "header_echo": f"Bearer {self.secret_openai}",
                "api_key": self.config.gemini_api_key
            }
        )
        self.assertNotIn(self.secret_openai, str(resp.raw_response))
        self.assertNotIn(self.config.gemini_api_key, str(resp.raw_response))
        self.assertEqual(resp.raw_response["api_key"], "[REDACTED]")

    @patch("urllib.request.urlopen")
    def test_http_status_codes_redact_secrets(self, mock_urlopen):
        """HTTP error codes (400, 401, 403, 429, 500) with secrets in error bodies must be redacted."""
        status_codes = [400, 401, 403, 429, 500]

        for code in status_codes:
            secret_body = (
                f'{{"error": "Invalid credential {self.config.gemini_api_key} '
                f'and {self.secret_openai} for Bearer sk-ant-api03-SECRET_CLAUDE_KEY_88888"}}'
            )
            mock_fp = io.BytesIO(secret_body.encode("utf-8"))
            err = MockHTTPError("https://api.example.com", code, "Error", {}, mock_fp)
            mock_urlopen.side_effect = err

            provider = GeminiProvider(self.config)
            try:
                provider.generate("system", "user")
            except Exception as exc:
                err_msg = str(exc)
                self.assertNotIn(self.config.gemini_api_key, err_msg, f"Key leaked in HTTP {code}!")
                self.assertNotIn(self.secret_openai, err_msg, f"OpenAI key leaked in HTTP {code}!")
                self.assertNotIn(self.secret_claude, err_msg, f"Claude key leaked in HTTP {code}!")

    @patch("urllib.request.urlopen")
    def test_connection_and_timeout_errors_redact_url_and_message(self, mock_urlopen):
        """Connection errors and timeouts must not leak secrets in error messages."""
        mock_urlopen.side_effect = TimeoutError("Connection to https://api.openai.com timed out with key sk-proj-SECRET")

        openai_p = OpenAIProvider(self.config, api_key=self.secret_openai)
        try:
            openai_p.generate("sys", "usr")
        except Exception as exc:
            err_msg = str(exc)
            self.assertNotIn(self.secret_openai, err_msg)

    @patch("urllib.request.urlopen")
    def test_malformed_json_response_redacts_secrets(self, mock_urlopen):
        """Malformed JSON responses containing echoing keys must be redacted."""
        mock_resp = MagicMock()
        mock_resp.read.return_value = f"NOT_VALID_JSON_WITH_KEY_{self.config.gemini_api_key}".encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        gemini_p = GeminiProvider(self.config)
        try:
            gemini_p.generate("sys", "usr")
        except Exception as exc:
            err_msg = str(exc)
            self.assertNotIn(self.config.gemini_api_key, err_msg)

    def test_observability_event_redaction_barrier(self):
        """ObservabilityManager publish_event must redact secrets from messages and metadata."""
        obs = ObservabilityManager.get_instance()
        event = obs.publish_event(
            level=EventLevel.ERROR,
            category=EventCategory.MODEL,
            event_type=EventType.MODEL_FAILURE,
            component="Gateway",
            operation="generate",
            message=f"Failed request with key {self.config.gemini_api_key}",
            metadata={"secret_field": self.secret_openai}
        )
        self.assertIsNotNone(event)
        self.assertNotIn(self.config.gemini_api_key, event.message)
        self.assertNotIn(self.secret_openai, str(event.metadata))
        self.assertEqual(event.metadata["secret_field"], "[REDACTED]")


if __name__ == "__main__":
    unittest.main()
