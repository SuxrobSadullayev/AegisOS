"""
Aegis AI Operating System — Marketplace Cryptographic Integrity Tests
Tests SHA-256 manifest generation, checksum validation, tampered file detection,
and missing file detection.
"""

import os
import shutil
import unittest
import tempfile

from runtime.src.marketplace import PluginIntegrityVerifier, PackageIntegrityError


class TestMarketplaceIntegrity(unittest.TestCase):
    """Tests SHA-256 integrity verification engine."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.plugin_dir = os.path.join(self.tmpdir, "my_plugin")
        os.makedirs(self.plugin_dir, exist_ok=True)

        with open(os.path.join(self.plugin_dir, "manifest.yaml"), "w") as f:
            f.write("plugin_id: test.integrity\nname: Test\nversion: 1.0.0\n")

        with open(os.path.join(self.plugin_dir, "plugin.py"), "w") as f:
            f.write("print('hello integrity')\n")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_checksum_generation_and_valid_verification(self):
        """Valid files matching generated checksums.json must pass verification."""
        checksums = PluginIntegrityVerifier.generate_checksums(self.plugin_dir)
        self.assertIn("manifest.yaml", checksums)
        self.assertIn("plugin.py", checksums)

        errors = PluginIntegrityVerifier.verify_integrity(self.plugin_dir, checksums)
        self.assertEqual(len(errors), 0)

    def test_tampered_file_detected(self):
        """Tampering with a file content after checksum generation must produce verification error."""
        checksums = PluginIntegrityVerifier.generate_checksums(self.plugin_dir)

        # Tamper with file
        with open(os.path.join(self.plugin_dir, "plugin.py"), "w") as f:
            f.write("print('MALICIOUS ALTERED CODE')\n")

        errors = PluginIntegrityVerifier.verify_integrity(self.plugin_dir, checksums)
        self.assertEqual(len(errors), 1)
        self.assertIn("Checksum mismatch", errors[0])

    def test_missing_file_detected(self):
        """Deleting a declared file must produce missing file error."""
        checksums = PluginIntegrityVerifier.generate_checksums(self.plugin_dir)

        # Delete plugin.py
        os.remove(os.path.join(self.plugin_dir, "plugin.py"))

        errors = PluginIntegrityVerifier.verify_integrity(self.plugin_dir, checksums)
        self.assertEqual(len(errors), 1)
        self.assertIn("Missing file", errors[0])


if __name__ == "__main__":
    unittest.main()
