import unittest
from runtime.src.config import AegisConfig
from runtime.src.gateway import GeminiModelProvider

class TestModelGateway(unittest.TestCase):
    def setUp(self):
        self.config = AegisConfig(gemini_api_key="")  # Force mock mode for deterministic test
        self.provider = GeminiModelProvider(self.config)

    def test_mock_generation(self):
        resp = self.provider.generate_response("System Prompt Context", "Hello Gemini")
        self.assertIn("[Aegis Runtime Executable — Offline Mode Response]", resp)
        self.assertIn("Hello Gemini", resp)

if __name__ == '__main__':
    unittest.main()
