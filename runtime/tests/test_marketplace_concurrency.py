"""
Aegis AI Operating System — Marketplace Concurrency & Multi-threading Stress Tests
Tests parallel packaging, registry search, index updates, and installation under multi-threaded stress.
"""

import os
import shutil
import unittest
import tempfile
import concurrent.futures

from runtime.src.config import AegisConfig
from runtime.src.plugin import PluginManager
from runtime.src.marketplace import PluginMarketplaceManager, RegistryEntry, TrustLevel


class TestMarketplaceConcurrency(unittest.TestCase):
    """Tests marketplace subsystem thread-safety under 20 concurrent worker threads."""

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

    def test_concurrent_registry_publish_and_search(self):
        """20 worker threads concurrently publishing and searching registry must maintain index integrity."""
        errors = []

        def worker(thread_idx: int):
            try:
                pid = f"com.test.concurrent_{thread_idx}"
                entry = RegistryEntry(
                    plugin_id=pid,
                    name=f"Concurrent Plugin {thread_idx}",
                    version="1.0.0",
                    description="Thread safety test plugin",
                    author=f"Worker {thread_idx}",
                    namespace="community",
                    trust_level=TrustLevel.VERIFIED,
                    package_file=f"{pid}-1.0.0.aegis-plugin",
                    checksum=f"hash_{thread_idx}"
                )
                self.market_manager.local_registry.publish(entry, b"package_payload")
                res = self.market_manager.local_registry.search(f"Concurrent Plugin {thread_idx}")
                if len(res) == 0:
                    errors.append(f"Thread {thread_idx}: search returned empty result")
            except Exception as exc:
                errors.append(f"Thread {thread_idx} exception: {exc}")

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(worker, i) for i in range(20)]
            concurrent.futures.wait(futures)

        self.assertEqual(len(errors), 0, f"Concurrency errors encountered: {errors}")
        available = self.market_manager.local_registry.list_available()
        self.assertEqual(len(available), 20)


if __name__ == "__main__":
    unittest.main()
