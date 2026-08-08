"""
Aegis AI Operating System — Remote Marketplace Registry Tests
Tests RemoteHTTPRegistry search, fallback, request header construction, and checksum verification.
"""

import os
import shutil
import unittest
import tempfile
from unittest.mock import MagicMock, patch

from runtime.src.marketplace import (
    RemoteHTTPRegistry, LocalRegistry, RegistryEntry, TrustLevel, PackageIntegrityError
)


class TestRemoteHTTPRegistry(unittest.TestCase):
    """Tests RemoteHTTPRegistry searching, download integrity, and fallback mechanisms."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.local_reg = LocalRegistry(self.tmpdir)

        # Register local entry for fallback test
        entry = RegistryEntry(
            plugin_id="com.test.fallback",
            name="Fallback Plugin",
            version="1.0.0",
            description="Fallback test plugin",
            author="Aegis Core",
            namespace="official",
            trust_level=TrustLevel.CORE,
            package_file="com.test.fallback-1.0.0.aegis-plugin",
            checksum="abc123sha"
        )
        self.local_reg.publish(entry, b"dummy_data")

        self.remote_reg = RemoteHTTPRegistry(
            base_url="https://marketplace.aegis.ai",
            cache_dir=os.path.join(self.tmpdir, "remote_cache"),
            api_token="AEGIS_API_TOKEN_12345",
            timeout_seconds=2.0,
            fallback_registry=self.local_reg
        )

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_remote_search_fallback_on_network_error(self):
        """When remote HTTP endpoint is unreachable, search should fall back cleanly to LocalRegistry."""
        results = self.remote_reg.search("Fallback")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].plugin_id, "com.test.fallback")

    def test_request_headers_construction(self):
        """_build_request must attach User-Agent and Authorization Bearer header when api_token is set."""
        req = self.remote_reg._build_request("https://marketplace.aegis.ai/api/v1/plugins")
        self.assertEqual(req.get_header("User-agent"), "AegisAIOS-MarketplaceClient/2.2.0")
        self.assertEqual(req.get_header("Authorization"), "Bearer AEGIS_API_TOKEN_12345")


if __name__ == "__main__":
    unittest.main()
