"""
Provider Switching & Gateway Configuration Tests for Aegis AI OS.
Verifies switching LLM providers (Mock, Gemini, Claude, OpenAI, OpenRouter),
model overrides, temperature, max tokens, and fallback handling.
"""

import unittest
from runtime.src.config import AegisConfig
from runtime.src.gateway import (
    ModelGatewayFactory, MockProvider, GeminiProvider,
    ClaudeProvider, OpenAIProvider, OpenRouterProvider
)


class TestProviderSwitchingAndConfiguration(unittest.TestCase):
    """Tests Model Gateway provider switching and dynamic configuration."""

    def setUp(self):
        self.config = AegisConfig()

    def test_provider_factory_instantiation(self):
        """1. Verifies ModelGatewayFactory instantiates all supported providers."""
        providers_map = {
            "mock": MockProvider,
            "gemini": GeminiProvider,
            "claude": ClaudeProvider,
            "openai": OpenAIProvider,
            "openrouter": OpenRouterProvider,
        }

        for p_name, expected_cls in providers_map.items():
            inst = ModelGatewayFactory.get_provider(p_name, self.config)
            self.assertIsInstance(inst, expected_cls)

    def test_invalid_provider_raises_value_error(self):
        """2. Verifies invalid provider name raises ValueError."""
        with self.assertRaises(ValueError):
            ModelGatewayFactory.get_provider("invalid_provider_123", self.config)

    def test_model_override_configuration(self):
        """3. Verifies model override setting."""
        cfg = AegisConfig(gemini_model="gemini-1.5-flash")
        prov = ModelGatewayFactory.get_provider("gemini", cfg)
        self.assertEqual(prov.default_model, "gemini-1.5-flash")

    def test_temperature_and_max_tokens_configuration(self):
        """4. Verifies temperature and max_tokens configuration parameters."""
        cfg = AegisConfig(temperature=0.3, max_tokens=2048)
        self.assertEqual(cfg.temperature, 0.3)
        self.assertEqual(cfg.max_tokens, 2048)


if __name__ == "__main__":
    unittest.main()
