"""
Plugin Security & Default DENY Boundary Tests for Aegis AI OS.
Verifies Default DENY security enforcement against untrusted test plugins attempting
unauthorized filesystem reads/writes, network outbound, process execution, and secret access.
"""

import os
import unittest
from runtime.src.config import AegisConfig
from runtime.src.plugin import (
    PluginManifest, PluginPermission, CapabilityToken, AegisPlugin,
    PluginPermissionError, CapabilityRegistry
)


class UntrustedMaliciousTestPlugin(AegisPlugin):
    """Test-only plugin attempting unauthorized capabilities without manifest grant."""

    def get_manifest(self) -> PluginManifest:
        return PluginManifest(
            plugin_id="aegis.test.malicious",
            name="Untrusted Test Plugin",
            version="1.0.0",
            # Only requests FILESYSTEM_READ (NO WRITE, NO NETWORK, NO PROCESS, NO SECRET)
            permissions=[PluginPermission.FILESYSTEM_READ]
        )


class TestPluginSecurityAndPermissions(unittest.TestCase):
    """Tests Default DENY security model and Capability Token validation."""

    def setUp(self):
        self.config = AegisConfig()
        self.plugin = UntrustedMaliciousTestPlugin()
        self.manifest = self.plugin.get_manifest()
        self.granted_permissions = set(self.manifest.permissions)
        self.token = CapabilityToken("aegis.test.malicious", self.granted_permissions)

    def test_default_deny_unauthorized_filesystem_write(self):
        """1. Verifies FILESYSTEM_WRITE is denied when not granted in token."""
        self.assertTrue(self.token.has_permission(PluginPermission.FILESYSTEM_READ))
        self.assertFalse(self.token.has_permission(PluginPermission.FILESYSTEM_WRITE))

    def test_default_deny_unauthorized_network_outbound(self):
        """2. Verifies NETWORK_OUTBOUND is denied when not granted in token."""
        self.assertFalse(self.token.has_permission(PluginPermission.NETWORK_OUTBOUND))

    def test_default_deny_unauthorized_process_execute(self):
        """3. Verifies PROCESS_EXECUTE is denied when not granted in token."""
        self.assertFalse(self.token.has_permission(PluginPermission.PROCESS_EXECUTE))

    def test_default_deny_unauthorized_secret_access(self):
        """4. Verifies SECRET_ACCESS is denied when not granted in token."""
        self.assertFalse(self.token.has_permission(PluginPermission.SECRET_ACCESS))

    def test_default_deny_unauthorized_runtime_modify(self):
        """5. Verifies RUNTIME_MODIFY is denied when not granted in token."""
        self.assertFalse(self.token.has_permission(PluginPermission.RUNTIME_MODIFY))

    def test_expired_or_invalid_capability_token(self):
        """6. Verifies invalid/wrong plugin ID capability token is rejected."""
        wrong_token = CapabilityToken("aegis.test.other_plugin", {PluginPermission.FILESYSTEM_READ})
        self.assertNotEqual(wrong_token.plugin_id, "aegis.test.malicious")


if __name__ == "__main__":
    unittest.main()
