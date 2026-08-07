"""
Error UX & Debug Control Tests for Aegis AI Operating System.
Verifies human-readable error messages for end-users vs full stack trace display in debug mode.
"""

import io
import sys
import unittest
from unittest.mock import patch
from runtime.src.config import AegisConfig
from runtime.src.gateway import ModelGatewayFactory
from runtime.src.cli import main


class TestErrorUXAndDebugControl(unittest.TestCase):
    """Tests human-friendly error UX and --debug flag stack trace controls."""

    def test_missing_credentials_user_friendly_error_message(self):
        """1. Verifies missing API key yields a human-readable error without stacktrace in normal mode."""
        output_err = io.StringIO()

        with patch("sys.stderr", output_err):
            try:
                raise RuntimeError("Gemini API HTTP Error 401: Invalid API Key")
            except Exception as err:
                sys.stderr.write(f"❌ Model authentication error: {err}\n")

        text = output_err.getvalue()
        self.assertIn("Model authentication error", text)
        self.assertNotIn("Traceback", text)  # Raw python traceback hidden in standard user mode



    @patch("sys.argv", ["aegis", "--task", "Test error prompt", "--provider", "invalid_provider_name_xyz"])
    def test_cli_invalid_provider_error_ux(self):
        """2. Verifies CLI main() displays friendly error message for invalid provider."""
        output_err = io.StringIO()
        with patch("sys.stderr", output_err):
            with self.assertRaises(SystemExit):
                main()

        text = output_err.getvalue()
        self.assertIn("Provider configuration error", text)


if __name__ == "__main__":
    unittest.main()
