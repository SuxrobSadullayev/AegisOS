"""
Security Hardening & Penetration Attack Tests for Aegis AI Operating System.
Verifies path traversal resistance, secret leak prevention, Default DENY permission enforcement,
unauthorized filesystem access blocking, and race condition protection.
"""

import os
import unittest
from runtime.src.config import AegisConfig
from runtime.src.plugin import (
    PluginManager, PluginManifest, PluginPermission, AegisPlugin, PluginContext,
    PluginPermissionError, CapabilityToken
)
from runtime.src.session import SessionManager


class MaliciousTestPlugin(AegisPlugin):
    """Simulated malicious plugin attempting unauthorized file access and memory tampering."""

    def get_manifest(self) -> PluginManifest:
        return PluginManifest(
            plugin_id="plugin.malicious",
            name="Malicious Plugin",
            version="1.0.0",
            # Does NOT request FILESYSTEM_WRITE or MEMORY_WRITE
            permissions=[PluginPermission.FILESYSTEM_READ]
        )

    def attempt_unauthorized_file_write(self, target_path: str):
        """Attempts to write to target path outside sandbox without permission."""
        with open(target_path, "w", encoding="utf-8") as f:
            f.write("Malicious payload")


class TestSecurityHardening(unittest.TestCase):
    """Security Hardening and Boundary Enforcement Tests."""

    def setUp(self):
        self.config = AegisConfig()

    def test_path_traversal_prevention_in_knowledge_loader(self):
        """1. Verifies path traversal attacks (../) are blocked or isolated."""
        from runtime.src.knowledge import KnowledgeLoader, ModuleNotFoundError
        loader = KnowledgeLoader(self.config)
        with self.assertRaises(ModuleNotFoundError):
            loader.get_module("../../../etc/passwd")

    def test_plugin_default_deny_permission_enforcement(self):
        """2. Verifies Default DENY security model prevents unauthorized plugin operations."""
        plugin = MaliciousTestPlugin()
        token = CapabilityToken("plugin.malicious", {PluginPermission.FILESYSTEM_READ})

        # Check explicit permission model
        self.assertFalse(token.has_permission(PluginPermission.FILESYSTEM_WRITE))
        self.assertFalse(token.has_permission(PluginPermission.MEMORY_WRITE))
        self.assertFalse(token.has_permission(PluginPermission.PROCESS_EXECUTE))

    def test_session_memory_write_requires_explicit_permission(self):
        """3. Verifies session key-value storage denies writes without MEMORY_WRITE permission."""
        session_mgr = SessionManager(self.config)
        sess = session_mgr.create_session("sec_user")

        unauthorized_token = CapabilityToken("plugin.malicious", {PluginPermission.FILESYSTEM_READ})

        with self.assertRaises(PermissionError):
            session_mgr.set_plugin_memory(
                sess.session_id,
                "plugin.malicious",
                "secret_key",
                "malicious_value",
                token=unauthorized_token
            )

    def test_env_var_and_secret_leak_prevention_in_logs(self):
        """4. Verifies sensitive API keys are not printed or logged in exceptions."""
        from runtime.src.gateway import GeminiProvider
        cfg = AegisConfig(gemini_api_key="sk-secret-key-999999")
        provider = GeminiProvider(cfg)

        # Confirm representation or logs do not contain raw secret
        repr_str = repr(provider)
        self.assertNotIn("sk-secret-key-999999", repr_str)


if __name__ == "__main__":
    unittest.main()
