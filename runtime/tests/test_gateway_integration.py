import unittest
from runtime.src.config import AegisConfig
from runtime.src.gateway import ModelGatewayFactory, ModelResponse

class TestGatewayIntegration(unittest.TestCase):
    def setUp(self):
        self.config = AegisConfig(max_retries=1)

    def test_multi_provider_pipeline_integration(self):
        providers = ["mock", "gemini", "claude", "openai", "openrouter"]
        for p_name in providers:
            provider = ModelGatewayFactory.get_provider(p_name, self.config)
            resp = provider.generate("System: Follow Aegis Constitution", f"Task for {p_name}")
            self.assertIsInstance(resp, ModelResponse)
            self.assertTrue(len(resp.text) > 0)
            self.assertGreater(resp.token_count, 0)

    def test_streaming_pipeline_integration(self):
        provider = ModelGatewayFactory.get_provider("mock", self.config)
        stream = provider.generate_stream("System", "Stream integration test")
        chunks = []
        for chunk in stream:
            chunks.append(chunk)
        self.assertTrue(len(chunks) > 0)

if __name__ == '__main__':
    unittest.main()
