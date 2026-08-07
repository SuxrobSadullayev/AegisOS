"""
Interactive CLI & REPL Slash Command Tests for Aegis AI Operating System.
Verifies interactive shell commands (/help, /status, /session, /sessions, /plugins,
/plugin, /provider, /model, /clear, /reset, /exit) and REPL input handling.
"""

import io
import sys
import unittest
from unittest.mock import patch
from runtime.src.config import AegisConfig
from runtime.src.cli import run_interactive_chat, main


class TestCLIInteractiveREPL(unittest.TestCase):
    """Tests interactive REPL chat shell and slash commands."""

    def setUp(self):
        self.config = AegisConfig(provider="mock")

    @patch("builtins.input", side_effect=["/help", "/status", "/sessions", "/plugins", "/exit"])
    def test_repl_slash_commands_execution(self, mock_input):
        """1. Verifies /help, /status, /sessions, /plugins, /exit in REPL shell."""
        output = io.StringIO()
        with patch("sys.stdout", output):
            run_interactive_chat(self.config, provider_name="mock", session_id="SESS_TEST_REPL_1")

        text = output.getvalue()
        self.assertIn("INTERACTIVE REPL SHELL", text)
        self.assertIn("Aegis AI OS Interactive Commands", text)
        self.assertIn("Aegis Runtime Status", text)
        self.assertIn("Exiting Aegis REPL", text)

    @patch("builtins.input", side_effect=["/session SESS_NEW_999", "/session", "/exit"])
    def test_repl_session_switch(self, mock_input):
        """2. Verifies switching active session via /session command."""
        output = io.StringIO()
        with patch("sys.stdout", output):
            run_interactive_chat(self.config, provider_name="mock", session_id="SESS_TEST_REPL_2")

        text = output.getvalue()
        self.assertIn("Switched to session 'SESS_NEW_999'", text)
        self.assertIn("Active Session: 'SESS_NEW_999'", text)

    @patch("builtins.input", side_effect=["/provider mock", "/provider invalid_provider_xyz", "/exit"])
    def test_repl_provider_switching(self, mock_input):
        """3. Verifies switching LLM provider via /provider command."""
        output = io.StringIO()
        output_err = io.StringIO()
        with patch("sys.stdout", output), patch("sys.stderr", output_err):
            run_interactive_chat(self.config, provider_name="mock", session_id="SESS_TEST_REPL_3")

        text = output.getvalue()
        text_err = output_err.getvalue()
        self.assertIn("Provider switched to 'MOCK'", text)
        self.assertIn("Failed to switch provider", text_err)

    @patch("builtins.input", side_effect=["/model gemini-1.5-flash", "/model", "/exit"])
    def test_repl_model_switching(self, mock_input):
        """4. Verifies updating model setting via /model command."""
        output = io.StringIO()
        with patch("sys.stdout", output):
            run_interactive_chat(self.config, provider_name="mock", session_id="SESS_TEST_REPL_4")

        text = output.getvalue()
        self.assertIn("Target model updated to 'gemini-1.5-flash'", text)
        self.assertIn("Active Model: gemini-1.5-flash", text)

    @patch("builtins.input", side_effect=["/reset", "/exit"])
    def test_repl_reset_command(self, mock_input):
        """5. Verifies resetting session context via /reset command."""
        output = io.StringIO()
        with patch("sys.stdout", output):
            run_interactive_chat(self.config, provider_name="mock", session_id="SESS_TEST_REPL_5")

        text = output.getvalue()
        self.assertIn("Session history for 'SESS_TEST_REPL_5' has been reset", text)

    @patch("builtins.input", side_effect=["/unknown_cmd", "/exit"])
    def test_repl_unknown_command_handling(self, mock_input):
        """6. Verifies handling unknown slash command gracefully."""
        output_err = io.StringIO()
        with patch("sys.stderr", output_err):
            run_interactive_chat(self.config, provider_name="mock", session_id="SESS_TEST_REPL_6")

        text = output_err.getvalue()
        self.assertIn("Unknown command", text)

    @patch("builtins.input", side_effect=["Hello Aegis, design an auth service", "/exit"])
    def test_repl_task_execution_flow(self, mock_input):
        """7. Verifies regular task prompt execution in interactive REPL shell."""
        output = io.StringIO()
        with patch("sys.stdout", output):
            run_interactive_chat(self.config, provider_name="mock", session_id="SESS_TEST_REPL_7")

        text = output.getvalue()
        self.assertIn("[Session]", text)
        self.assertIn("[Intent]", text)
        self.assertIn("[Reasoning]", text)
        self.assertIn("[Truth]", text)
        self.assertIn("[Prompt]", text)
        self.assertIn("[Model]", text)


    @patch("sys.argv", ["aegis", "--task", "CLI direct task", "--provider", "mock"])
    def test_cli_main_direct_task_execution(self):
        """8. Verifies CLI main() execution with direct --task flag."""
        output = io.StringIO()
        with patch("sys.stdout", output):
            main()

        text = output.getvalue()
        self.assertIn("Task: CLI direct task", text)
        self.assertIn("TIMING METRICS", text)


if __name__ == "__main__":
    unittest.main()
