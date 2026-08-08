"""
Aegis AI Operating System — Plugin Marketplace General & Integration Tests
Tests packaging, local registry indexing, searching, publishing, and information display.
"""

import os
import unittest
import tempfile
import shutil
from runtime.src.config import AegisConfig
from runtime.src.plugin import PluginManager, AegisPlugin, PluginManifest, PluginContext, PluginCapability, PluginPermission
from runtime.src.marketplace import PluginMarketplaceManager, TrustLevel, RegistryEntry


class SampleMarketplacePlugin(AegisPlugin):
    """Sample plugin for packaging and registry testing."""
    def get_manifest(self) -> PluginManifest:
        return PluginManifest(
            plugin_id="com.aegis.sample_plugin",
            name="Sample Marketplace Plugin",
            version="1.0.0",
            description="Sample plugin for Aegis Marketplace testing",
            author="Aegis Core Team",
            publisher="Aegis Official",
            capabilities=[PluginCapability.PIPELINE_STAGE],
            permissions=[PluginPermission.FILESYSTEM_READ],
            license="MIT",
            namespace="official"
        )

    def on_initialize(self, ctx: PluginContext) -> bool:
        return True


class TestMarketplaceGeneral(unittest.TestCase):
    """Tests basic packaging, indexing, searching, and publishing."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.config = AegisConfig()
        self.config.base_dir = self.tmpdir

        self.plugins_dir = os.path.join(self.tmpdir, "plugins")
        os.makedirs(self.plugins_dir, exist_ok=True)
        self.plugin_manager = PluginManager(self.plugins_dir)

        self.market_manager = PluginMarketplaceManager(self.config, self.plugin_manager)

        # Create source directory for test plugin
        self.src_plugin_dir = os.path.join(self.tmpdir, "sample_plugin")
        os.makedirs(self.src_plugin_dir, exist_ok=True)

        manifest_content = (
            'plugin_id: "com.aegis.sample_plugin"\n'
            'name: "Sample Marketplace Plugin"\n'
            'version: "1.0.0"\n'
            'description: "Sample plugin for Aegis Marketplace testing"\n'
            'author: "Aegis Core Team"\n'
            'publisher: "Aegis Official"\n'
            'capabilities:\n  - PIPELINE_STAGE\n'
            'permissions:\n  - FILESYSTEM_READ\n'
            'namespace: "official"\n'
        )
        with open(os.path.join(self.src_plugin_dir, "manifest.yaml"), "w", encoding="utf-8") as f:
            f.write(manifest_content)

        code_content = "class SamplePlugin: pass\n"
        with open(os.path.join(self.src_plugin_dir, "plugin.py"), "w", encoding="utf-8") as f:
            f.write(code_content)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_create_package(self):
        """create_package should generate .aegis-plugin bundle with checksums and signature."""
        pkg_file = self.market_manager.create_package(self.src_plugin_dir)
        self.assertTrue(os.path.exists(pkg_file))
        self.assertTrue(pkg_file.endswith(".aegis-plugin"))

    def test_publish_and_search_registry(self):
        """Publishing a package to LocalRegistry makes it searchable."""
        pkg_file = self.market_manager.create_package(self.src_plugin_dir)
        manifest, trust, _ = self.market_manager.inspect_and_verify_package(pkg_file)

        with open(pkg_file, "rb") as f:
            pkg_bytes = f.read()

        entry = RegistryEntry(
            plugin_id=manifest.plugin_id,
            name=manifest.name,
            version=manifest.version,
            description=manifest.description,
            author=manifest.author,
            namespace=manifest.namespace,
            trust_level=trust,
            package_file=os.path.basename(pkg_file),
            checksum=manifest.checksum
        )
        self.market_manager.local_registry.publish(entry, pkg_bytes)

        # Search registry
        results = self.market_manager.local_registry.search("Sample")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].plugin_id, "com.aegis.sample_plugin")

    def test_get_entry(self):
        """get_entry returns specific version or latest version entry."""
        pkg_file = self.market_manager.create_package(self.src_plugin_dir)
        manifest, trust, _ = self.market_manager.inspect_and_verify_package(pkg_file)

        with open(pkg_file, "rb") as f:
            pkg_bytes = f.read()

        entry = RegistryEntry(
            plugin_id=manifest.plugin_id,
            name=manifest.name,
            version=manifest.version,
            description=manifest.description,
            author=manifest.author,
            namespace=manifest.namespace,
            trust_level=trust,
            package_file=os.path.basename(pkg_file),
            checksum=manifest.checksum
        )
        self.market_manager.local_registry.publish(entry, pkg_bytes)

        entry_retrieved = self.market_manager.local_registry.get_entry("com.aegis.sample_plugin")
        self.assertIsNotNone(entry_retrieved)
        self.assertEqual(entry_retrieved.version, "1.0.0")


if __name__ == "__main__":
    unittest.main()
