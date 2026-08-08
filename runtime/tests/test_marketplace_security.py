"""
Aegis AI Operating System — Plugin Marketplace Adversarial Security Tests
Tests supply chain security barriers:
- Zip bomb / Decompression limit enforcement
- Path traversal in package members (../, absolute paths, null bytes)
- Dependency confusion & namespace hijacking prevention
- Signature tampering & spoofing detection
- Blacklisted / Blocked plugin installation rejection
- Unsigned plugin enforcement
"""

import os
import io
import json
import zipfile
import shutil
import unittest
import tempfile

from runtime.src.config import AegisConfig
from runtime.src.plugin import PluginManager
from runtime.src.marketplace import (
    PluginMarketplaceManager, PluginPackageValidator, PackageValidationError,
    PackageIntegrityError, SignatureVerificationError, TrustPolicyError,
    DependencyConfusionError, PackageSecurityLimits, RegistryEntry, TrustLevel
)


class TestMarketplaceAdversarialSecurity(unittest.TestCase):
    """Adversarial security tests for Plugin Marketplace supply chain barriers."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.config = AegisConfig()
        self.config.base_dir = self.tmpdir

        self.plugins_dir = os.path.join(self.tmpdir, "plugins")
        os.makedirs(self.plugins_dir, exist_ok=True)
        self.plugin_manager = PluginManager(self.plugins_dir)

        self.market_manager = PluginMarketplaceManager(self.config, self.plugin_manager)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_adv_1_path_traversal_dotdot_denied(self):
        """1. Package containing '../etc/passwd' member must be rejected during extraction."""
        bad_zip_path = os.path.join(self.tmpdir, "bad_traversal.zip")
        with zipfile.ZipFile(bad_zip_path, "w") as zf:
            zf.writestr("../../../etc/passwd", "root:x:0:0:root:/root:/bin/bash")

        validator = PluginPackageValidator()
        extract_target = os.path.join(self.tmpdir, "extract_target")
        with self.assertRaises(PackageValidationError) as ctx:
            validator.validate_and_extract(bad_zip_path, extract_target)
        self.assertIn("traversal", str(ctx.exception).lower())

    def test_adv_2_absolute_path_traversal_denied(self):
        """2. Package containing absolute path member '/tmp/hacked.py' must be rejected."""
        bad_zip_path = os.path.join(self.tmpdir, "bad_abs.zip")
        with zipfile.ZipFile(bad_zip_path, "w") as zf:
            zf.writestr("/tmp/hacked.py", "print('hacked')")

        validator = PluginPackageValidator()
        extract_target = os.path.join(self.tmpdir, "extract_target")
        with self.assertRaises(PackageValidationError) as ctx:
            validator.validate_and_extract(bad_zip_path, extract_target)
        self.assertIn("absolute path", str(ctx.exception).lower())

    def test_adv_3_decompression_bomb_bytes_limit_exceeded(self):
        """3. Package exceeding max_extracted_bytes (e.g. zip bomb) must raise PackageValidationError."""
        limits = PackageSecurityLimits(max_extracted_bytes=1000)  # Low 1KB limit for testing
        validator = PluginPackageValidator(limits=limits)

        bomb_zip_path = os.path.join(self.tmpdir, "zip_bomb.zip")
        with zipfile.ZipFile(bomb_zip_path, "w") as zf:
            zf.writestr("large_file.txt", "A" * 5000)

        extract_target = os.path.join(self.tmpdir, "extract_target")
        with self.assertRaises(PackageValidationError) as ctx:
            validator.validate_and_extract(bomb_zip_path, extract_target)
        self.assertIn("decompression bomb", str(ctx.exception).lower())

    def test_adv_4_max_files_limit_exceeded(self):
        """4. Package exceeding max_files limit must be rejected."""
        limits = PackageSecurityLimits(max_files=5)
        validator = PluginPackageValidator(limits=limits)

        many_files_zip = os.path.join(self.tmpdir, "many_files.zip")
        with zipfile.ZipFile(many_files_zip, "w") as zf:
            for i in range(10):
                zf.writestr(f"file_{i}.txt", "data")

        extract_target = os.path.join(self.tmpdir, "extract_target")
        with self.assertRaises(PackageValidationError) as ctx:
            validator.validate_and_extract(many_files_zip, extract_target)
        self.assertIn("files", str(ctx.exception).lower())

    def test_adv_5_dependency_confusion_namespace_hijack_denied(self):
        """5. Untrusted repository publishing to an 'official' namespace must raise DependencyConfusionError."""
        reg = self.market_manager.local_registry

        # Register official plugin entry
        official_entry = RegistryEntry(
            plugin_id="com.aegis.core_security",
            name="Official Security Plugin",
            version="1.0.0",
            description="Official plugin",
            author="Aegis Official",
            namespace="official",
            trust_level=TrustLevel.CORE,
            package_file="com.aegis.core_security-1.0.0.aegis-plugin",
            checksum="abc123sha"
        )
        reg.publish(official_entry, b"dummy_pkg_data")

        # Attempt to publish malicious community plugin overriding official namespace
        imposter_entry = RegistryEntry(
            plugin_id="com.aegis.core_security",
            name="Malicious Imposter Security Plugin",
            version="2.0.0",
            description="Imposter payload",
            author="Attacker",
            namespace="community",  # Not official!
            trust_level=TrustLevel.UNTRUSTED,
            package_file="com.aegis.core_security-2.0.0.aegis-plugin",
            checksum="xyz789sha"
        )
        with self.assertRaises(DependencyConfusionError) as ctx:
            reg.publish(imposter_entry, b"malicious_data")
        self.assertIn("namespace protection denied", str(ctx.exception).lower())

    def test_adv_6_blocked_plugin_installation_denied(self):
        """6. Blacklisted / Blocked plugin installation attempt must raise TrustPolicyError."""
        # Block plugin ID
        self.market_manager.key_store.block_plugin("malicious.blocked.plugin")

        # Create dummy package with blocked plugin_id
        pkg_dir = os.path.join(self.tmpdir, "blocked_src")
        os.makedirs(pkg_dir, exist_ok=True)
        manifest_content = 'plugin_id: "malicious.blocked.plugin"\nname: "Blocked Plugin"\nversion: "1.0.0"\n'
        with open(os.path.join(pkg_dir, "manifest.yaml"), "w") as f:
            f.write(manifest_content)
        with open(os.path.join(pkg_dir, "plugin.py"), "w") as f:
            f.write("class P: pass\n")

        pkg_file = self.market_manager.create_package(pkg_dir)

        with self.assertRaises(TrustPolicyError) as ctx:
            self.market_manager.install_package(pkg_file, force_untrusted=True)
        self.assertIn("blocked", str(ctx.exception).lower())

    def test_adv_7_unsigned_plugin_rejected_in_production_mode(self):
        """7. Unsigned plugin installation without force_untrusted=True must be rejected."""
        pkg_dir = os.path.join(self.tmpdir, "unsigned_src")
        os.makedirs(pkg_dir, exist_ok=True)
        manifest_content = 'plugin_id: "com.test.unsigned"\nname: "Unsigned Plugin"\nversion: "1.0.0"\n'
        with open(os.path.join(pkg_dir, "manifest.yaml"), "w") as f:
            f.write(manifest_content)
        with open(os.path.join(pkg_dir, "plugin.py"), "w") as f:
            f.write("class P: pass\n")

        from runtime.src.marketplace import PluginIntegrityVerifier
        checksums = PluginIntegrityVerifier.generate_checksums(pkg_dir)

        # Create package without signature
        pkg_file = os.path.join(self.tmpdir, "com.test.unsigned-1.0.0.aegis-plugin")
        with zipfile.ZipFile(pkg_file, "w") as zf:
            zf.write(os.path.join(pkg_dir, "manifest.yaml"), "manifest.yaml")
            zf.write(os.path.join(pkg_dir, "plugin.py"), "plugin.py")
            zf.writestr("checksums.json", json.dumps({"files": checksums}))

        with self.assertRaises(TrustPolicyError) as ctx:
            self.market_manager.install_package(pkg_file, force_untrusted=False)
        self.assertIn("unsigned", str(ctx.exception).lower())


if __name__ == "__main__":
    unittest.main()
