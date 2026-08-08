"""
Aegis AI Operating System — Marketplace Digital Signature Tests
Tests HMAC-SHA256 signature verification, key store management, key revocation,
expired signatures, and tampered signature rejection.
"""

import os
import shutil
import unittest
import tempfile
import time

from runtime.src.marketplace import (
    TrustedKeyStore, PluginSignatureVerifier, SignatureMetadata, SignatureStatus
)


class TestMarketplaceSignature(unittest.TestCase):
    """Tests digital signature verification and key store management."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.key_store = TrustedKeyStore(self.tmpdir)
        self.key_store.add_key("test_publisher_key", "SECRET_KEY_HMAC_12345")
        self.verifier = PluginSignatureVerifier(self.key_store)

        self.manifest_bytes = b"plugin_id: test.sig\nversion: 1.0.0\n"
        self.checksums_bytes = b'{"files": {"plugin.py": "abc"}}'

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_valid_signature_trusted(self):
        """Valid signature matching trusted key in key store must evaluate to TRUSTED."""
        digest = PluginSignatureVerifier.compute_payload_digest(self.manifest_bytes, self.checksums_bytes)
        sig_str = PluginSignatureVerifier.sign_payload("SECRET_KEY_HMAC_12345", digest)

        sig_meta = SignatureMetadata(
            publisher="Test Publisher",
            key_id="test_publisher_key",
            signature=sig_str
        )

        status, msg = self.verifier.verify_signature(self.manifest_bytes, self.checksums_bytes, sig_meta)
        self.assertEqual(status, SignatureStatus.TRUSTED)
        self.assertIn("VERIFIED", msg)

    def test_tampered_payload_signature_invalid(self):
        """Signature verification on tampered payload must evaluate to INVALID."""
        digest = PluginSignatureVerifier.compute_payload_digest(self.manifest_bytes, self.checksums_bytes)
        sig_str = PluginSignatureVerifier.sign_payload("SECRET_KEY_HMAC_12345", digest)

        sig_meta = SignatureMetadata(
            publisher="Test Publisher",
            key_id="test_publisher_key",
            signature=sig_str
        )

        # Alter payload
        tampered_manifest = b"plugin_id: test.sig\nversion: 2.0.0-HACKED\n"
        status, msg = self.verifier.verify_signature(tampered_manifest, self.checksums_bytes, sig_meta)
        self.assertEqual(status, SignatureStatus.INVALID)

    def test_revoked_key_signature_revoked(self):
        """Signature with a revoked key must evaluate to REVOKED."""
        digest = PluginSignatureVerifier.compute_payload_digest(self.manifest_bytes, self.checksums_bytes)
        sig_str = PluginSignatureVerifier.sign_payload("SECRET_KEY_HMAC_12345", digest)

        sig_meta = SignatureMetadata(
            publisher="Test Publisher",
            key_id="test_publisher_key",
            signature=sig_str
        )

        self.key_store.revoke_key("test_publisher_key")

        status, msg = self.verifier.verify_signature(self.manifest_bytes, self.checksums_bytes, sig_meta)
        self.assertEqual(status, SignatureStatus.REVOKED)

    def test_expired_signature_expired(self):
        """Signature past its expiration timestamp must evaluate to EXPIRED."""
        digest = PluginSignatureVerifier.compute_payload_digest(self.manifest_bytes, self.checksums_bytes)
        sig_str = PluginSignatureVerifier.sign_payload("SECRET_KEY_HMAC_12345", digest)

        sig_meta = SignatureMetadata(
            publisher="Test Publisher",
            key_id="test_publisher_key",
            signature=sig_str,
            expires_at_utc=time.time() - 100  # Expired in past
        )

        status, msg = self.verifier.verify_signature(self.manifest_bytes, self.checksums_bytes, sig_meta)
        self.assertEqual(status, SignatureStatus.EXPIRED)

    def test_unsigned_package_untrusted(self):
        """Unsigned package (signature=None) must evaluate to UNTRUSTED."""
        status, msg = self.verifier.verify_signature(self.manifest_bytes, self.checksums_bytes, None)
        self.assertEqual(status, SignatureStatus.UNTRUSTED)


if __name__ == "__main__":
    unittest.main()
