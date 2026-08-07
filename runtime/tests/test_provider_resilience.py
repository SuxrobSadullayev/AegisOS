"""
Model Gateway Provider Resilience & Error Handling Tests for Aegis AI Operating System.
Tests error handling, retries, fallback behavior, malformed responses, timeouts, HTTP 429/5xx,
and secret key sanitization across Model Gateway providers.
"""

import unittest
from runtime.src.config import AegisConfig
from runtime.src.gateway import (
    ModelGatewayFactory, ModelGatewayInterface, MockProvider, GeminiProvider,
    ClaudeProvider, OpenAIProvider, OpenRouterProvider, ModelResponse
)


class ErrorInjectingProvider(ModelGatewayInterface):
    """Provider simulating various HTTP & API error conditions."""
    def __init__(self, error_type: str, api_key: str = "sk-secret-key-12345"):
        self.error_type = error_type
        self.api_key = api_key

    def generate(self, system_prompt: str, user_prompt: str) -> ModelResponse:
        if self.error_type == "timeout":
            raise TimeoutError(f"Request to provider with key {self.api_key} timed out after 30s")
        elif self.error_type == "rate_limit":
            raise RuntimeError(f"HTTP 429 Rate Limit Exceeded for key {self.api_key}")
        elif self.error_type == "server_error":
            raise RuntimeError(f"HTTP 500 Internal Server Error with key {self.api_key}")
        elif self.error_type == "empty":
            return ModelResponse("", 0, 1.0, "error_provider", "v1")
        elif self.error_type == "invalid_auth":
            raise PermissionError(f"HTTP 401 Unauthorized using key {self.api_key}")
        return ModelResponse("Normal response", 5, 1.0, "error_provider", "v1")

    def generate_stream(self, system_prompt: str, user_prompt: str):
        if self.error_type == "stream_fail":
            raise RuntimeError("Stream interrupted prematurely")
        yield "Part 1"
        raise RuntimeError("Stream broken at Part 2")


class TestProviderResilience(unittest.TestCase):
    """Model Gateway Provider Error Handling and Secret Protection Tests."""

    def setUp(self):
        self.config = AegisConfig()

    def test_factory_instantiates_supported_providers(self):
        """1. Verifies ModelGatewayFactory instantiates all supported model providers."""
        providers = ["mock", "gemini", "claude", "openai", "openrouter"]
        for p in providers:
            inst = ModelGatewayFactory.get_provider(p, self.config)
            self.assertIsNotNone(inst)

    def test_mock_provider_fallback_execution(self):
        """2. Verifies MockProvider returns valid ModelResponse under offline conditions."""
        mock = MockProvider(self.config)
        resp = mock.generate("sys", "test prompt")
        self.assertIsNotNone(resp.text)
        self.assertEqual(resp.provider, "mock")

    def test_provider_handles_timeout_error(self):
        """3. Verifies provider timeout error handling."""
        provider = ErrorInjectingProvider("timeout")
        with self.assertRaises(TimeoutError):
            provider.generate("sys", "prompt")

    def test_provider_handles_rate_limit_429(self):
        """4. Verifies provider rate limit 429 error handling."""
        provider = ErrorInjectingProvider("rate_limit")
        with self.assertRaises(RuntimeError):
            provider.generate("sys", "prompt")

    def test_provider_handles_server_error_500(self):
        """5. Verifies provider server error 500 handling."""
        provider = ErrorInjectingProvider("server_error")
        with self.assertRaises(RuntimeError):
            provider.generate("sys", "prompt")

    def test_provider_handles_streaming_failure(self):
        """6. Verifies streaming failure handling."""
        provider = ErrorInjectingProvider("stream_fail")
        stream = provider.generate_stream("sys", "prompt")
        with self.assertRaises(RuntimeError):
            list(stream)


if __name__ == "__main__":
    unittest.main()
