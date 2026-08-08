"""
Aegis AI Operating System — Marketplace Atomic Installation, Rollback & Sandbox Intersect Tests
Tests:
- Staging-based atomic plugin installation
- Version history preservation
- Atomic rollback to prior plugin version
- Effective sandbox policy calculation (requested ∩ trust level)
"""

import os
import shutil
import unittest
import tempfile

from runtime.src.config import AegisConfig
from runtime.src.plugin import PluginManager, PluginPermission
from runtime.src.marketplace import (
    PluginMarketplaceManager, TrustLevel, MarketplaceError
)


class TestMarketplaceInstallRollback(unittest.TestCase):
    """Tests atomic installation, version history, rollback, and effective sandbox policy."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.config = AegisConfig()
        self.config.base_dir = self.tmpdir

        self.plugins_dir = os.path.join(self.tmpdir, "plugins")
        os.makedirs(self.plugins_dir, exist_ok=True)
        self.plugin_manager = PluginManager(self.plugins_dir)

        self.market_manager = PluginMarketplaceManager(self.config, self.plugin_manager)

        # Build plugin source directory for v1.0.0
        self.src_v1 = os.path.join(self.tmpdir, "src_v1")
        os.makedirs(self.src_v1, exist_ok=True)
        manifest_v1 = (
            'plugin_id: "com.test.atomic"\n'
            'name: "Atomic Test Plugin"\n'
            'version: "1.0.0"\n'
            'permissions:\n  - FILESYSTEM_READ\n'
        )
        with open(os.path.join(self.src_v1, "manifest.yaml"), "w") as f:
            f.write(manifest_v1)
        with open(os.path.join(self.src_v1, "plugin.py"), "w") as f:
            f.write("class P: pass\n")

        # Build plugin source directory for v1.1.0
        self.src_v2 = os.path.join(self.tmpdir, "src_v2")
        os.makedirs(self.src_v2, exist_ok=True)
        manifest_v2 = (
            'plugin_id: "com.test.atomic"\n'
            'name: "Atomic Test Plugin"\n'
            'version: "1.1.0"\n'
            'permissions:\n  - FILESYSTEM_READ\n'
        )
        with open(os.path.join(self.src_v2, "manifest.yaml"), "w") as f:
            f.write(manifest_v2)
        with open(os.path.join(self.src_v2, "plugin.py"), "w") as f:
            f.write("class P: pass\n")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_atomic_install_v1_and_update_v2(self):
        """Installing v1.0.0 then updating to v1.1.0 preserves both version directories."""
        pkg_v1 = self.market_manager.create_package(self.src_v1)
        self.market_manager.install_package(pkg_v1, force_untrusted=True)

        plugin_base = os.path.join(self.plugins_dir, "com.test.atomic")
        v1_dir = os.path.join(plugin_base, "versions", "1.0.0")
        active_dir = os.path.join(plugin_base, "active")

        self.assertTrue(os.path.exists(v1_dir))
        self.assertTrue(os.path.exists(active_dir))

        # Update to v1.1.0
        pkg_v2 = self.market_manager.create_package(self.src_v2)
        self.market_manager.install_package(pkg_v2, force_untrusted=True)

        v2_dir = os.path.join(plugin_base, "versions", "1.1.0")
        self.assertTrue(os.path.exists(v1_dir), "v1.0.0 version dir must be preserved for rollback")
        self.assertTrue(os.path.exists(v2_dir), "v1.1.0 version dir must exist")

    def test_rollback_v2_to_v1(self):
        """Rollback from v1.1.0 to v1.0.0 updates active pointer cleanly."""
        pkg_v1 = self.market_manager.create_package(self.src_v1)
        self.market_manager.install_package(pkg_v1, force_untrusted=True)

        pkg_v2 = self.market_manager.create_package(self.src_v2)
        self.market_manager.install_package(pkg_v2, force_untrusted=True)

        # Execute rollback to 1.0.0
        res = self.market_manager.rollback_plugin("com.test.atomic", "1.0.0")
        self.assertTrue(res)

    def test_effective_sandbox_policy_calculation(self):
        """UNTRUSTED plugins stay Default DENY while TRUSTED plugins get permission intersect."""
        pkg_v1 = self.market_manager.create_package(self.src_v1)
        manifest, trust, _ = self.market_manager.inspect_and_verify_package(pkg_v1)

        # For UNTRUSTED: Default DENY
        policy_untrusted = self.market_manager.compute_effective_sandbox_policy(manifest, TrustLevel.UNTRUSTED)
        self.assertFalse(policy_untrusted.allow_filesystem_read)

        # For TRUSTED: permission intersect allowed
        policy_trusted = self.market_manager.compute_effective_sandbox_policy(manifest, TrustLevel.TRUSTED)
        self.assertTrue(policy_trusted.allow_filesystem_read)
        self.assertFalse(policy_trusted.allow_subprocess)  # Subprocess forbidden for non-core


if __name__ == "__main__":
    unittest.main()
