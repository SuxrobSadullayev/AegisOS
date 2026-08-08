"""
Aegis AI Operating System — Tool & Filesystem Execution Tests
Tests real file creation, disk content verification, path traversal security enforcement,
failure reporting, and normal informational task preservation.
"""

import os
import shutil
import unittest
import tempfile

from runtime.src.config import AegisConfig
from runtime.src.orchestrator import RuntimeOrchestrator, ToolExecutionStage, OrchestratorContext, PipelineTracer
from runtime.src.gateway import MockProvider, ModelResponse


class TestToolExecution(unittest.TestCase):
    """Tests ToolExecutionStage and physical filesystem action execution."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()

        # Set config.base_dir to project root so KernelLoader finds core/ files
        self.config = AegisConfig()
        self.config.base_dir = self.old_cwd

        os.chdir(self.tmpdir)
        self.provider = MockProvider(self.config)
        self.orchestrator = RuntimeOrchestrator(self.config, self.provider)

    def tearDown(self):
        os.chdir(self.old_cwd)
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_real_file_creation_and_content_verification(self):
        """Task to create a file must physically create it on disk and verify content."""
        ctx = self.orchestrator.run("Create hello.py containing print('Hello World') and verify it.")

        self.assertIsNotNone(ctx.model_response)
        # Check model response text contains success report
        self.assertIn("File Action Executed & Verified Successfully", ctx.model_response.text)
        self.assertIn("EXISTS_AND_READABLE", ctx.model_response.text)

        # INDEPENDENT SHELL/DISK VERIFICATION
        target_path = os.path.join(self.tmpdir, "hello.py")
        self.assertTrue(os.path.exists(target_path), f"File {target_path} must exist on disk")

        with open(target_path, "r", encoding="utf-8") as f:
            disk_content = f.read()

        self.assertEqual(disk_content.strip(), "print('Hello World')")

    def test_path_traversal_rejection(self):
        """Attempting path traversal (../etc/passwd) must be rejected by security policy."""
        ctx = self.orchestrator.run("Create ../etc/passwd containing HACKED and verify it.")

        self.assertIsNotNone(ctx.model_response)
        self.assertIn("Security Policy Violation", ctx.model_response.text)
        self.assertIn("Path traversal DENIED", ctx.model_response.text)

        # Verify file was NOT created outside workspace
        target_path = os.path.abspath(os.path.join(self.tmpdir, "..", "etc", "passwd"))
        self.assertFalse(os.path.exists(target_path))

    def test_informational_task_preserved(self):
        """Normal informational prompt with no file creation request must pass untouched."""
        ctx = self.orchestrator.run("What is Aegis AI OS?")

        self.assertIsNotNone(ctx.model_response)
        self.assertIn("[Aegis Mock Provider Output]", ctx.model_response.text)
        self.assertNotIn("File Action Executed", ctx.model_response.text)


if __name__ == "__main__":
    unittest.main()
