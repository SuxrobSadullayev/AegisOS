import unittest
from runtime.src.config import AegisConfig
from runtime.src.gateway import (
    ModelResponse,
    MockProvider,
    GeminiProvider,
    ClaudeProvider,
    OpenAIProvider,
    OpenRouterProvider,
    ModelGatewayFactory
)

class TestModelGateway(unittest.TestCase):
    def setUp(self):
        self.config = AegisConfig(max_retries=1)

    def test_mock_provider_generate(self):
        provider = MockProvider(self.config, simulate_delay_ms=1.0)
        resp = provider.generate("System context", "Test query")
        self.assertIsInstance(resp, ModelResponse)
        self.assertEqual(resp.provider, "mock")
        self.assertEqual(resp.model, "mock-v1")
        self.assertIn("Test query", resp.text)
        self.assertGreater(resp.token_count, 0)
        self.assertGreaterEqual(resp.latency_ms, 0.0)

    def test_mock_provider_streaming(self):
        provider = MockProvider(self.config, simulate_delay_ms=1.0)
        stream = provider.generate_stream("System context", "Stream query")
        chunks = list(stream)
        self.assertTrue(len(chunks) > 0)
        combined = "".join(chunks)
        self.assertIn("Stream query", combined)

    def test_mock_provider_error_simulation(self):
        provider = MockProvider(self.config, simulate_error=True)
        with self.assertRaises(RuntimeError):
            provider.generate("System", "Error query")

    def test_factory_instantiation(self):
        p_gemini = ModelGatewayFactory.get_provider("gemini", self.config)
        p_claude = ModelGatewayFactory.get_provider("claude", self.config)
        p_openai = ModelGatewayFactory.get_provider("openai", self.config)
        p_openrouter = ModelGatewayFactory.get_provider("openrouter", self.config)
        p_mock = ModelGatewayFactory.get_provider("mock", self.config)

        self.assertIsInstance(p_gemini, GeminiProvider)
        self.assertIsInstance(p_claude, ClaudeProvider)
        self.assertIsInstance(p_openai, OpenAIProvider)
        self.assertIsInstance(p_openrouter, OpenRouterProvider)
        self.assertIsInstance(p_mock, MockProvider)

        with self.assertRaises(ValueError):
            ModelGatewayFactory.get_provider("unsupported_provider", self.config)

    def test_unconfigured_api_key_fallback(self):
        # When API key is empty, providers fallback to mock mode safely
        p_gemini = GeminiProvider(self.config)
        resp = p_gemini.generate("System", "Unconfigured key query")
        self.assertEqual(resp.provider, "mock")

        p_claude = ClaudeProvider(self.config)
        resp_c = p_claude.generate("System", "Unconfigured key query")
        self.assertEqual(resp_c.provider, "mock")

    def test_token_estimation(self):
        provider = MockProvider(self.config)
        tokens_empty = provider.estimate_tokens("")
        self.assertEqual(tokens_empty, 0)

        tokens_text = provider.estimate_tokens("Hello world, this is a test prompt.")
        self.assertGreater(tokens_text, 0)

if __name__ == '__main__':
    unittest.main()
