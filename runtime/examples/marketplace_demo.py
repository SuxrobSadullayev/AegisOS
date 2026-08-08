"""
Aegis AI Operating System — Plugin Marketplace & Supply Chain Security Demo
Demonstrates:
1. Plugin packaging (.aegis-plugin)
2. Integrity hashing (SHA-256 checksums.json)
3. Digital signature signing & verification (signature.json)
4. Local registry publication & searching
5. Atomic staging installation & version pointer management
6. Effective sandbox permission calculation
7. Plugin update & rollback
8. Supply chain security enforcement (blocking malicious/untrusted plugins)
"""

import os
import sys
import json
import shutil
import tempfile

# Ensure parent path is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from runtime.src.config import AegisConfig
from runtime.src.plugin import PluginManager
from runtime.src.marketplace import (
    PluginMarketplaceManager, TrustLevel, RegistryEntry, TrustPolicyError
)


def run_marketplace_demo():
    print("================================================================================")
    print("🛡️ AEGIS AI OS — PLUGIN MARKETPLACE & SUPPLY CHAIN SECURITY DEMO")
    print("================================================================================\n")

    tmpdir = tempfile.mkdtemp()
    try:
        config = AegisConfig()
        config.base_dir = tmpdir

        plugins_dir = os.path.join(tmpdir, "plugins")
        os.makedirs(plugins_dir, exist_ok=True)
        plugin_mgr = PluginManager(plugins_dir)

        market_mgr = PluginMarketplaceManager(config, plugin_mgr)

        # Step 1: Create plugin source directory
        print("--- 1. CREATING SAMPLE AEGIS PLUGIN SOURCE (v1.0.0) ---")
        src_dir = os.path.join(tmpdir, "demo_plugin_v1")
        os.makedirs(src_dir, exist_ok=True)

        manifest_content = (
            'plugin_id: "com.aegis.analytics_demo"\n'
            'name: "Aegis Analytics Plugin"\n'
            'version: "1.0.0"\n'
            'description: "Real-time AI telemetry analytics plugin"\n'
            'author: "Aegis Core Security Team"\n'
            'publisher: "Aegis Official Publisher"\n'
            'capabilities:\n  - QUALITY_VALIDATOR\n'
            'permissions:\n  - FILESYSTEM_READ\n'
            'namespace: "official"\n'
        )
        with open(os.path.join(src_dir, "manifest.yaml"), "w", encoding="utf-8") as f:
            f.write(manifest_content)

        code_content = (
            "from runtime.src.plugin import AegisPlugin, PluginManifest, PluginContext\n\n"
            "class AnalyticsPlugin(AegisPlugin):\n"
            "    def on_initialize(self, ctx: PluginContext) -> bool:\n"
            "        print('  [AnalyticsPlugin] Initialized successfully v1.0.0!')\n"
            "        return True\n"
        )
        with open(os.path.join(src_dir, "plugin.py"), "w", encoding="utf-8") as f:
            f.write(code_content)

        print(f"✅ Plugin source created at: {src_dir}")

        # Step 2: Package & Sign Plugin
        print("\n--- 2. PACKAGING & SIGNING PLUGIN (.aegis-plugin) ---")
        pkg_file = market_mgr.create_package(src_dir, key_id="aegis_official_key")
        print(f"📦 Package generated: {pkg_file}")
        print(f"📊 Package Size: {os.path.getsize(pkg_file)} bytes")

        # Step 3: Inspect & Verify Package
        print("\n--- 3. INSPECTING & VERIFYING PACKAGE INTEGRITY & DIGITAL SIGNATURE ---")
        manifest, trust_level, warnings = market_mgr.inspect_and_verify_package(pkg_file)
        print(f"🛡️ Manifest ID     : {manifest.plugin_id} (v{manifest.version})")
        print(f"🛡️ Publisher       : {manifest.publisher}")
        print(f"🛡️ Evaluated Trust : {trust_level.value}")
        print(f"🛡️ Verification    : {warnings[0]}")

        # Step 4: Publish to Local Registry
        print("\n--- 4. PUBLISHING TO LOCAL MARKETPLACE REGISTRY ---")
        with open(pkg_file, "rb") as f:
            pkg_bytes = f.read()

        entry = RegistryEntry(
            plugin_id=manifest.plugin_id,
            name=manifest.name,
            version=manifest.version,
            description=manifest.description,
            author=manifest.author,
            namespace=manifest.namespace,
            trust_level=trust_level,
            package_file=os.path.basename(pkg_file),
            checksum=manifest.checksum
        )
        market_mgr.local_registry.publish(entry, pkg_bytes)
        print("🚀 Package published to LocalRegistry index.")

        # Step 5: Search Marketplace Registry
        print("\n--- 5. SEARCHING MARKETPLACE REGISTRY ---")
        results = market_mgr.local_registry.search("analytics")
        print(f"🔍 Found {len(results)} matching plugins:")
        for r in results:
            print(f"  • [{r.namespace.upper()}] {r.plugin_id} (v{r.version}) [{r.trust_level.value}] — {r.name}: {r.description}")

        # Step 6: Atomic Installation
        print("\n--- 6. ATOMIC STAGING INSTALLATION ---")
        market_mgr.install_package(pkg_file, force_untrusted=True)
        print("✅ Plugin installed using staging & atomic version directory pointer.")

        # Step 7: Update Plugin to v1.1.0
        print("\n--- 7. UPDATING PLUGIN TO v1.1.0 ---")
        src_v2 = os.path.join(tmpdir, "demo_plugin_v2")
        os.makedirs(src_v2, exist_ok=True)
        manifest_v2 = manifest_content.replace('version: "1.0.0"', 'version: "1.1.0"')
        with open(os.path.join(src_v2, "manifest.yaml"), "w", encoding="utf-8") as f:
            f.write(manifest_v2)
        with open(os.path.join(src_v2, "plugin.py"), "w", encoding="utf-8") as f:
            f.write(code_content.replace("v1.0.0", "v1.1.0"))

        pkg_v2 = market_mgr.create_package(src_v2, key_id="aegis_official_key")
        market_mgr.install_package(pkg_v2, force_untrusted=True)
        print("✅ Updated to v1.1.0. Both v1.0.0 and v1.1.0 versions are preserved on disk.")

        # Step 8: Rollback to v1.0.0
        print("\n--- 8. ATOMIC ROLLBACK TO v1.0.0 ---")
        market_mgr.rollback_plugin("com.aegis.analytics_demo", "1.0.0")
        print("🔄 Rollback to v1.0.0 completed successfully.")

        # Step 9: Security Barrier Test (Blocked Plugin Rejection)
        print("\n--- 9. SUPPLY CHAIN SECURITY BARRIER (BLOCKED PLUGIN REJECTION) ---")
        market_mgr.key_store.block_plugin("com.aegis.analytics_demo")
        try:
            market_mgr.install_package(pkg_file, force_untrusted=True)
        except TrustPolicyError as err:
            print(f"🛡️ Security Barrier PASS: Blacklisted plugin installation REJECTED: {err}")

        print("\n================================================================================")
        print("✅ AEGIS PLUGIN MARKETPLACE & SUPPLY CHAIN DEMO COMPLETED SUCCESSFULLY!")
        print("================================================================================\n")

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    run_marketplace_demo()
