"""
Config Precedence & Parsing Tests for Aegis AI Operating System.
Verifies precedence hierarchy: CLI Args > Environment Variables > Config File (~/.aegis/config.yaml) > Defaults,
lightweight zero-dependency YAML parsing, and boundary validation.
"""

import os
import tempfile
import unittest
from unittest.mock import patch
from runtime.src.config import AegisConfig


class TestConfigPrecedence(unittest.TestCase):
    """Tests configuration loading, file parsing, and precedence rules."""

    def test_default_config_values(self):
        """1. Verifies default AegisConfig values."""
        cfg = AegisConfig()
        self.assertEqual(cfg.provider, "mock")
        self.assertEqual(cfg.gemini_model, "gemini-1.5-pro")
        self.assertEqual(cfg.temperature, 0.7)
        self.assertEqual(cfg.max_tokens, 4096)
        self.assertEqual(cfg.reasoning_depth, "L2")
        self.assertEqual(cfg.max_retries, 3)

    def test_zero_dependency_yaml_parser(self):
        """2. Tests zero-dependency lightweight YAML parser."""
        sample_yaml = """
        # Aegis OS Config File
        provider: gemini
        model: gemini-1.5-flash
        temperature: 0.2
        max_tokens: 2048
        reasoning_depth: L3
        max_retries: 5
        verbose: true
        debug_mode: false
        enabled_plugins:
          - python_capability_plugin
          - security_capability_plugin
        """
        parsed = AegisConfig._parse_simple_yaml(sample_yaml)
        self.assertEqual(parsed["provider"], "gemini")
        self.assertEqual(parsed["model"], "gemini-1.5-flash")
        self.assertEqual(parsed["temperature"], 0.2)
        self.assertEqual(parsed["max_tokens"], 2048)
        self.assertEqual(parsed["reasoning_depth"], "L3")
        self.assertEqual(parsed["max_retries"], 5)
        self.assertEqual(parsed["verbose"], True)
        self.assertEqual(parsed["debug_mode"], False)
        self.assertEqual(parsed["enabled_plugins"], ["python_capability_plugin", "security_capability_plugin"])

    def test_config_file_loading(self):
        """3. Verifies loading AegisConfig from custom YAML config file."""
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".yaml") as f:
            f.write("provider: openrouter\nmodel: anthropic/claude-3.5-sonnet\nmax_retries: 4\n")
            f_path = f.name

        try:
            cfg = AegisConfig.load(config_path=f_path)
            self.assertEqual(cfg.provider, "openrouter")
            self.assertEqual(cfg.gemini_model, "anthropic/claude-3.5-sonnet")
            self.assertEqual(cfg.max_retries, 4)
        finally:
            if os.path.exists(f_path):
                os.remove(f_path)

    @patch.dict(os.environ, {"AEGIS_PROVIDER": "claude", "AEGIS_REASONING_DEPTH": "L3", "AEGIS_MAX_RETRIES": "2"})
    def test_environment_variable_override_precedence(self):
        """4. Verifies Environment variables override config file defaults."""
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".yaml") as f:
            f.write("provider: gemini\nreasoning_depth: L1\n")
            f_path = f.name

        try:
            cfg = AegisConfig.load(config_path=f_path)
            # Environment variable overrides file setting
            self.assertEqual(cfg.provider, "claude")
            self.assertEqual(cfg.reasoning_depth, "L3")
            self.assertEqual(cfg.max_retries, 2)
        finally:
            if os.path.exists(f_path):
                os.remove(f_path)

    def test_temperature_boundary_validation(self):
        """5. Verifies validation of temperature bounds (0.0 to 2.0)."""
        cfg = AegisConfig(temperature=2.5)
        with self.assertRaises(ValueError):
            cfg.validate()

    def test_confidence_threshold_boundary_validation(self):
        """6. Verifies validation of confidence threshold bounds (0.0 to 1.0)."""
        cfg = AegisConfig(confidence_threshold=-0.1)
        with self.assertRaises(ValueError):
            cfg.validate()


if __name__ == "__main__":
    unittest.main()
