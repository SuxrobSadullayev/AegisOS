"""
Aegis AI Operating System — Production Plugin Marketplace & Package Distribution Registry
Supply Chain Security Subsystem featuring:
- Package format (.aegis-plugin) with Zip Bomb & Path Traversal protection
- Cryptographic Integrity Verification (SHA-256 checksums.json)
- Digital Signature Verification & TrustedKeyStore (signature.json)
- Multi-tier Trust Policy (CORE, TRUSTED, VERIFIED, UNTRUSTED, BLOCKED)
- Namespace Protection (official/, community/, local/) against Dependency Confusion
- Staging-based Atomic Installation, Updates, and Rollback
- Effective Permission Intersect (requested ∩ trusted ∩ sandbox policy)
- Observability integration (structured logs & audit.jsonl security events)
Python 3.12+ compliant. Zero external dependencies.
"""

import os
import sys
import re
import json
import time
import hmac
import hashlib
import zipfile
import shutil
import logging
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any

from runtime.src.config import AegisConfig
from runtime.src.plugin import (
    PluginManager, PluginManifest, PluginDependency, PluginDependencyResolver,
    PluginPermission, PluginCapability, SandboxLevel, ManifestValidator,
    PluginError, PluginManifestError, PluginDependencyError
)
from runtime.src.sandbox import SandboxPolicy, SandboxLimits
from runtime.src.observability import ObservabilityManager, EventLevel, EventCategory, EventType

logger = logging.getLogger("AegisMarketplace")


# ──────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────

class TrustLevel(Enum):
    """Multi-tier trust classification for installed plugins."""
    CORE = "CORE"            # Aegis core built-in plugins (Maximum Trust)
    TRUSTED = "TRUSTED"        # Signed by trusted key, verified manifest, compatible
    VERIFIED = "VERIFIED"      # Valid integrity, verified signature, passed security policy
    UNTRUSTED = "UNTRUSTED"    # Unsigned or unknown publisher (Isolated in Sandbox Default DENY)
    BLOCKED = "BLOCKED"        # Blacklisted / Revoked (Forbidden from install/loading)


class SignatureStatus(Enum):
    """Digital signature validation status."""
    TRUSTED = "TRUSTED"
    UNTRUSTED = "UNTRUSTED"
    INVALID = "INVALID"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


class MarketplaceEvent(Enum):
    """Telemetry and security audit events for plugin supply chain operations."""
    PACKAGE_DISCOVERED = "PLUGIN_PACKAGE_DISCOVERED"
    PACKAGE_DOWNLOADED = "PLUGIN_PACKAGE_DOWNLOADED"
    PACKAGE_VERIFIED = "PLUGIN_PACKAGE_VERIFIED"
    SIGNATURE_VERIFIED = "PLUGIN_SIGNATURE_VERIFIED"
    SIGNATURE_FAILED = "PLUGIN_SIGNATURE_FAILED"
    INSTALL_STARTED = "PLUGIN_INSTALL_STARTED"
    INSTALL_COMPLETED = "PLUGIN_INSTALL_COMPLETED"
    INSTALL_FAILED = "PLUGIN_INSTALL_FAILED"
    UPDATE_STARTED = "PLUGIN_UPDATE_STARTED"
    UPDATE_COMPLETED = "PLUGIN_UPDATE_COMPLETED"
    ROLLBACK_STARTED = "PLUGIN_ROLLBACK_STARTED"
    ROLLBACK_COMPLETED = "PLUGIN_ROLLBACK_COMPLETED"
    UNINSTALL = "PLUGIN_UNINSTALL"
    BLOCKED = "PLUGIN_BLOCKED"
    TRUST_CHANGED = "PLUGIN_TRUST_CHANGED"


# ──────────────────────────────────────────────
# Custom Exceptions
# ──────────────────────────────────────────────

class MarketplaceError(PluginError):
    """Base exception for all Aegis Marketplace & Supply Chain errors."""
    pass


class PackageValidationError(MarketplaceError):
    """Raised when package zip file violates safety limits or structure."""
    pass


class PackageIntegrityError(MarketplaceError):
    """Raised when SHA-256 file checksums do not match manifest."""
    pass


class SignatureVerificationError(MarketplaceError):
    """Raised when digital signature is invalid, revoked, or expired."""
    pass


class TrustPolicyError(MarketplaceError):
    """Raised when plugin violates system trust policies (e.g. unsigned in production)."""
    pass


class DependencyConfusionError(MarketplaceError):
    """Raised when an untrusted repository attempts to override an official namespace."""
    pass


# ──────────────────────────────────────────────
# Data Structures
# ──────────────────────────────────────────────

@dataclass
class PackageSecurityLimits:
    """Decompression bomb and traversal protection boundaries."""
    max_extracted_bytes: int = 50 * 1024 * 1024  # 50 MB
    max_files: int = 100
    max_file_size_bytes: int = 10 * 1024 * 1024  # 10 MB


@dataclass
class SignatureMetadata:
    """Digital signature payload (signature.json)."""
    publisher: str
    key_id: str
    signature: str
    timestamp_utc: float = field(default_factory=time.time)
    expires_at_utc: Optional[float] = None
    algorithm: str = "HMAC-SHA256"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "publisher": self.publisher,
            "key_id": self.key_id,
            "signature": self.signature,
            "timestamp_utc": self.timestamp_utc,
            "expires_at_utc": self.expires_at_utc,
            "algorithm": self.algorithm,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SignatureMetadata":
        return cls(
            publisher=data.get("publisher", ""),
            key_id=data.get("key_id", ""),
            signature=data.get("signature", ""),
            timestamp_utc=data.get("timestamp_utc", time.time()),
            expires_at_utc=data.get("expires_at_utc"),
            algorithm=data.get("algorithm", "HMAC-SHA256"),
        )


@dataclass
class RegistryEntry:
    """Metadata entry for an indexable marketplace plugin."""
    plugin_id: str
    name: str
    version: str
    description: str
    author: str
    namespace: str  # official, community, local
    trust_level: TrustLevel
    package_file: str
    checksum: str
    signature: Optional[SignatureMetadata] = None
    published_at_utc: float = field(default_factory=time.time)
    download_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plugin_id": self.plugin_id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "namespace": self.namespace,
            "trust_level": self.trust_level.value,
            "package_file": self.package_file,
            "checksum": self.checksum,
            "signature": self.signature.to_dict() if self.signature else None,
            "published_at_utc": self.published_at_utc,
            "download_count": self.download_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RegistryEntry":
        sig_data = data.get("signature")
        sig = SignatureMetadata.from_dict(sig_data) if sig_data else None
        trust_str = data.get("trust_level", "UNTRUSTED")
        trust_level = TrustLevel(trust_str) if trust_str in TrustLevel._value2member_map_ else TrustLevel.UNTRUSTED
        return cls(
            plugin_id=data.get("plugin_id", ""),
            name=data.get("name", ""),
            version=data.get("version", "0.0.0"),
            description=data.get("description", ""),
            author=data.get("author", ""),
            namespace=data.get("namespace", "community"),
            trust_level=trust_level,
            package_file=data.get("package_file", ""),
            checksum=data.get("checksum", ""),
            signature=sig,
            published_at_utc=data.get("published_at_utc", time.time()),
            download_count=data.get("download_count", 0),
        )


# ──────────────────────────────────────────────
# Cryptographic Integrity & Signature Engine
# ──────────────────────────────────────────────

class TrustedKeyStore:
    """Manages trusted publisher public keys / HMAC secrets and revocation lists."""

    def __init__(self, key_store_dir: str):
        self.key_store_dir = os.path.abspath(key_store_dir)
        os.makedirs(self.key_store_dir, exist_ok=True)
        self._lock = threading.RLock()
        self.keys: Dict[str, str] = {}  # key_id -> secret_key
        self.revoked_keys: Set[str] = set()
        self.blocked_plugins: Set[str] = set()
        self._load_keys()

    def _load_keys(self) -> None:
        """Loads trusted keys and revocation lists from disk."""
        store_file = os.path.join(self.key_store_dir, "trusted_keys.json")
        if os.path.exists(store_file):
            try:
                with open(store_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.keys = data.get("keys", {})
                self.revoked_keys = set(data.get("revoked_keys", []))
                self.blocked_plugins = set(data.get("blocked_plugins", []))
            except Exception as exc:
                logger.warning("Error loading TrustedKeyStore: %s", exc)

        # Ensure default official Aegis Key exists
        if "aegis_official_key" not in self.keys:
            self.keys["aegis_official_key"] = "AEGIS_OFFICIAL_HMAC_SECRET_V1_2026"

    def save(self) -> None:
        """Saves current key store state atomically."""
        with self._lock:
            store_file = os.path.join(self.key_store_dir, "trusted_keys.json")
            tmp_file = store_file + ".tmp"
            payload = {
                "keys": self.keys,
                "revoked_keys": list(self.revoked_keys),
                "blocked_plugins": list(self.blocked_plugins),
            }
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_file, store_file)

    def add_key(self, key_id: str, secret: str) -> None:
        with self._lock:
            self.keys[key_id] = secret
            self.revoked_keys.discard(key_id)
            self.save()

    def revoke_key(self, key_id: str) -> None:
        with self._lock:
            self.revoked_keys.add(key_id)
            self.save()

    def block_plugin(self, plugin_id: str) -> None:
        with self._lock:
            self.blocked_plugins.add(plugin_id)
            self.save()

    def unblock_plugin(self, plugin_id: str) -> None:
        with self._lock:
            self.blocked_plugins.discard(plugin_id)
            self.save()

    def is_key_revoked(self, key_id: str) -> bool:
        with self._lock:
            return key_id in self.revoked_keys

    def is_plugin_blocked(self, plugin_id: str) -> bool:
        with self._lock:
            return plugin_id in self.blocked_plugins


class PluginSignatureVerifier:
    """Verifies digital signatures for plugin packages using HMAC-SHA256."""

    def __init__(self, key_store: TrustedKeyStore):
        self.key_store = key_store

    @staticmethod
    def compute_payload_digest(manifest_bytes: bytes, checksums_bytes: bytes) -> str:
        """Creates a deterministic SHA-256 digest of core manifest & checksums metadata."""
        h = hashlib.sha256()
        h.update(manifest_bytes)
        h.update(checksums_bytes)
        return h.hexdigest()

    @staticmethod
    def sign_payload(secret: str, payload_digest: str) -> str:
        """Computes HMAC-SHA256 signature for payload_digest."""
        return hmac.new(secret.encode("utf-8"), payload_digest.encode("utf-8"), hashlib.sha256).hexdigest()

    def verify_signature(
        self,
        manifest_bytes: bytes,
        checksums_bytes: bytes,
        signature_meta: Optional[SignatureMetadata]
    ) -> Tuple[SignatureStatus, str]:
        """Verifies signature metadata against payload digest and TrustedKeyStore."""
        if not signature_meta:
            return SignatureStatus.UNTRUSTED, "Package is unsigned (signature.json missing)"

        key_id = signature_meta.key_id
        if self.key_store.is_key_revoked(key_id):
            return SignatureStatus.REVOKED, f"Publisher key '{key_id}' has been REVOKED"

        if signature_meta.expires_at_utc and time.time() > signature_meta.expires_at_utc:
            return SignatureStatus.EXPIRED, f"Signature for key '{key_id}' has EXPIRED"

        secret = self.key_store.keys.get(key_id)
        if not secret:
            return SignatureStatus.UNTRUSTED, f"Publisher key '{key_id}' not found in TrustedKeyStore"

        payload_digest = self.compute_payload_digest(manifest_bytes, checksums_bytes)
        expected_sig = self.sign_payload(secret, payload_digest)

        if hmac.compare_digest(expected_sig, signature_meta.signature):
            return SignatureStatus.TRUSTED, f"Signature VERIFIED for publisher '{signature_meta.publisher}' ({key_id})"
        else:
            return SignatureStatus.INVALID, "Signature MISMATCH: Package contents tampered or invalid secret"


# ──────────────────────────────────────────────
# Package Decompression & Traversal Guard
# ──────────────────────────────────────────────

class PluginPackageValidator:
    """Validates .aegis-plugin archives against Zip Bombs, Path Traversal, and Symlink attacks."""

    def __init__(self, limits: Optional[PackageSecurityLimits] = None):
        self.limits = limits or PackageSecurityLimits()

    def validate_and_extract(self, zip_path: str, extract_to: str) -> List[str]:
        """Extracts .aegis-plugin zip archive under strict security constraints.

        Protects against:
        - Path Traversal (../, absolute paths, drive letters)
        - Decompression Bombs (total bytes & single file size limits)
        - File count limits
        - Symlink & Hardlink escapes
        """
        if not os.path.isfile(zip_path):
            raise PackageValidationError(f"Package file not found: {zip_path}")

        extract_to_abs = os.path.realpath(os.path.abspath(extract_to))
        os.makedirs(extract_to_abs, exist_ok=True)

        extracted_files: List[str] = []
        total_bytes = 0

        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                infolist = zf.infolist()
                if len(infolist) > self.limits.max_files:
                    raise PackageValidationError(
                        f"Package contains {len(infolist)} files, exceeding limit ({self.limits.max_files})"
                    )

                for member in infolist:
                    filename = member.filename

                    # 1. Reject empty names, null bytes, or URL-encoded traversals
                    if not filename or "\x00" in filename or "%00" in filename:
                        raise PackageValidationError(f"Malicious member filename detected: {filename!r}")

                    # 2. Reject absolute paths or Windows drive letters
                    if os.path.isabs(filename) or re.match(r'^[A-Za-z]:', filename):
                        raise PackageValidationError(f"Absolute path traversal denied in package member: {filename}")

                    # 3. Reject parent directory traversal ('..')
                    norm_path = os.path.normpath(filename)
                    if norm_path.startswith("..") or "/../" in f"/{norm_path}/":
                        raise PackageValidationError(f"Path traversal '..' denied in package member: {filename}")

                    # 4. Containment check on target file path
                    target_path = os.path.realpath(os.path.abspath(os.path.join(extract_to_abs, norm_path)))
                    if not target_path.startswith(extract_to_abs.rstrip(os.sep) + os.sep) and target_path != extract_to_abs:
                        raise PackageValidationError(
                            f"Extraction path '{target_path}' escapes root '{extract_to_abs}'"
                        )

                    # 5. Check single file uncompressed size
                    if member.file_size > self.limits.max_file_size_bytes:
                        raise PackageValidationError(
                            f"Member '{filename}' size ({member.file_size} bytes) exceeds file limit ({self.limits.max_file_size_bytes} bytes)"
                        )

                    total_bytes += member.file_size
                    if total_bytes > self.limits.max_extracted_bytes:
                        raise PackageValidationError(
                            f"Decompression bomb detected: total extracted size exceeds limit ({self.limits.max_extracted_bytes} bytes)"
                        )

                    # 6. Extract member safely
                    if member.is_dir():
                        os.makedirs(target_path, exist_ok=True)
                    else:
                        os.makedirs(os.path.dirname(target_path), exist_ok=True)
                        with zf.open(member) as source, open(target_path, "wb") as target:
                            shutil.copyfileobj(source, target)
                        extracted_files.append(target_path)

        except zipfile.BadZipFile as exc:
            raise PackageValidationError(f"Invalid or corrupted zip archive: {exc}") from exc

        return extracted_files


# ──────────────────────────────────────────────
# Integrity & Repository Engine
# ──────────────────────────────────────────────

class PluginIntegrityVerifier:
    """Generates and verifies SHA-256 manifest file checksums (checksums.json)."""

    @staticmethod
    def generate_checksums(plugin_dir: str) -> Dict[str, str]:
        """Calculates SHA-256 hashes for all files in a plugin directory."""
        plugin_dir_abs = os.path.realpath(os.path.abspath(plugin_dir))
        checksums: Dict[str, str] = {}

        for root, _, files in os.walk(plugin_dir_abs):
            for file in sorted(files):
                if file in ("checksums.json", "signature.json"):
                    continue
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, plugin_dir_abs).replace("\\", "/")
                
                h = hashlib.sha256()
                with open(full_path, "rb") as f:
                    while chunk := f.read(65536):
                        h.update(chunk)
                checksums[rel_path] = h.hexdigest()

        return checksums

    @staticmethod
    def verify_integrity(plugin_dir: str, checksums: Dict[str, str]) -> List[str]:
        """Verifies files in plugin_dir against expected checksums dictionary.

        Returns a list of error strings if any files are missing or modified.
        """
        plugin_dir_abs = os.path.realpath(os.path.abspath(plugin_dir))
        errors: List[str] = []

        for rel_path, expected_hash in checksums.items():
            full_path = os.path.join(plugin_dir_abs, rel_path)
            if not os.path.exists(full_path):
                errors.append(f"Missing file declared in checksums.json: {rel_path}")
                continue

            h = hashlib.sha256()
            with open(full_path, "rb") as f:
                while chunk := f.read(65536):
                    h.update(chunk)
            actual_hash = h.hexdigest()

            if actual_hash != expected_hash:
                errors.append(f"Checksum mismatch for '{rel_path}': expected {expected_hash[:10]}..., got {actual_hash[:10]}...")

        return errors


class PluginRepository(ABC):
    """Abstract interface for local or remote plugin marketplace registries."""

    @abstractmethod
    def search(self, query: str) -> List[RegistryEntry]:
        pass

    @abstractmethod
    def get_entry(self, plugin_id: str, version: Optional[str] = None) -> Optional[RegistryEntry]:
        pass

    @abstractmethod
    def publish(self, entry: RegistryEntry, package_bytes: bytes) -> bool:
        pass

    @abstractmethod
    def list_available(self) -> List[RegistryEntry]:
        pass


class LocalRegistry(PluginRepository):
    """File-based local marketplace registry supporting namespaces (official, community, local)."""

    def __init__(self, registry_dir: str):
        self.registry_dir = os.path.abspath(registry_dir)
        self.packages_dir = os.path.join(self.registry_dir, "packages")
        os.makedirs(self.packages_dir, exist_ok=True)
        self._lock = threading.RLock()
        self.index_file = os.path.join(self.registry_dir, "registry_index.json")
        self.entries: Dict[str, List[RegistryEntry]] = {}  # plugin_id -> list of versions
        self._load_index()

    def _load_index(self) -> None:
        """Loads registry index from disk."""
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for pid, v_list in data.items():
                    self.entries[pid] = [RegistryEntry.from_dict(item) for item in v_list]
            except Exception as exc:
                logger.warning("Error loading LocalRegistry index: %s", exc)

    def _save_index(self) -> None:
        """Atomically saves registry index to disk."""
        with self._lock:
            tmp_file = self.index_file + ".tmp"
            serializable = {
                pid: [e.to_dict() for e in v_list]
                for pid, v_list in self.entries.items()
            }
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(serializable, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_file, self.index_file)

    def search(self, query: str) -> List[RegistryEntry]:
        """Searches available plugins by name, ID, author, or description."""
        with self._lock:
            q = query.lower().strip()
            results: List[RegistryEntry] = []
            for v_list in self.entries.values():
                if not v_list:
                    continue
                latest = v_list[-1]  # Latest version
                if (q in latest.plugin_id.lower() or q in latest.name.lower() or
                    q in latest.description.lower() or q in latest.author.lower()):
                    results.append(latest)
            return results

    def get_entry(self, plugin_id: str, version: Optional[str] = None) -> Optional[RegistryEntry]:
        """Retrieves registry entry for plugin_id and version."""
        with self._lock:
            v_list = self.entries.get(plugin_id, [])
            if not v_list:
                return None
            if not version:
                return v_list[-1]  # Return latest version
            for entry in v_list:
                if entry.version == version:
                    return entry
            return None

    def publish(self, entry: RegistryEntry, package_bytes: bytes) -> bool:
        """Publishes a new package to the local registry with namespace protection."""
        with self._lock:
            # Namespace Protection / Dependency Confusion Prevention:
            # 'official' plugins can only be published if namespace is official
            existing = self.entries.get(entry.plugin_id, [])
            if existing:
                latest_existing = existing[-1]
                if latest_existing.namespace == "official" and entry.namespace != "official":
                    raise DependencyConfusionError(
                        f"Namespace Protection DENIED: Cannot override official plugin '{entry.plugin_id}' with '{entry.namespace}' entry"
                    )

            target_package_name = f"{entry.plugin_id}-{entry.version}.aegis-plugin"
            target_package_path = os.path.join(self.packages_dir, target_package_name)
            tmp_package_path = target_package_path + ".tmp"

            with open(tmp_package_path, "wb") as f:
                f.write(package_bytes)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_package_path, target_package_path)

            entry.package_file = target_package_name
            if entry.plugin_id not in self.entries:
                self.entries[entry.plugin_id] = []

            # Append or replace existing version entry
            self.entries[entry.plugin_id] = [
                e for e in self.entries[entry.plugin_id] if e.version != entry.version
            ]
            self.entries[entry.plugin_id].append(entry)

            # Sort versions by publication time
            self.entries[entry.plugin_id].sort(key=lambda e: e.version)
            self._save_index()
            return True

    def list_available(self) -> List[RegistryEntry]:
        """Lists latest version entries for all available marketplace plugins."""
        with self._lock:
            return [v_list[-1] for v_list in self.entries.values() if v_list]


class RemoteHTTPRegistry(PluginRepository):
    """Remote HTTPS marketplace registry implementation supporting searching, fetching,
    downloading packages, SHA-256 verification, and fallback to LocalRegistry.
    """

    def __init__(
        self,
        base_url: str,
        cache_dir: str,
        api_token: Optional[str] = None,
        timeout_seconds: float = 10.0,
        fallback_registry: Optional[PluginRepository] = None
    ):
        import urllib.parse
        import urllib.request
        import urllib.error

        self.base_url = base_url.rstrip("/")
        self.cache_dir = os.path.abspath(cache_dir)
        self.api_token = api_token
        self.timeout = timeout_seconds
        self.fallback_registry = fallback_registry
        os.makedirs(self.cache_dir, exist_ok=True)
        self._lock = threading.RLock()

    def _build_request(self, url: str, method: str = "GET", data: Optional[bytes] = None) -> urllib.request.Request:
        import urllib.request
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("User-Agent", "AegisAIOS-MarketplaceClient/2.2.0")
        req.add_header("Accept", "application/json")
        if self.api_token:
            req.add_header("Authorization", f"Bearer {self.api_token}")
        return req

    def search(self, query: str) -> List[RegistryEntry]:
        """Searches remote HTTPS marketplace registry or falls back to local registry."""
        import urllib.parse
        import urllib.request
        import urllib.error

        url = f"{self.base_url}/api/v1/plugins/search?q={urllib.parse.quote(query)}"
        req = self._build_request(url)

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                if resp.status == 200:
                    payload = json.loads(resp.read().decode("utf-8"))
                    results = [RegistryEntry.from_dict(item) for item in payload.get("results", [])]
                    return results
        except Exception as exc:
            logger.warning("RemoteHTTPRegistry search error (%s): %s. Falling back to local registry.", self.base_url, exc)

        if self.fallback_registry:
            return self.fallback_registry.search(query)
        return []

    def get_entry(self, plugin_id: str, version: Optional[str] = None) -> Optional[RegistryEntry]:
        """Retrieves registry entry for a plugin from remote HTTPS registry."""
        import urllib.parse
        import urllib.request
        import urllib.error

        v_query = f"?version={urllib.parse.quote(version)}" if version else ""
        url = f"{self.base_url}/api/v1/plugins/{urllib.parse.quote(plugin_id)}{v_query}"
        req = self._build_request(url)

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                if resp.status == 200:
                    payload = json.loads(resp.read().decode("utf-8"))
                    return RegistryEntry.from_dict(payload)
        except Exception as exc:
            logger.warning("RemoteHTTPRegistry get_entry error (%s): %s.", self.base_url, exc)

        if self.fallback_registry:
            return self.fallback_registry.get_entry(plugin_id, version)
        return None

    def download_package(self, entry: RegistryEntry, target_dir: str) -> str:
        """Downloads package binary from remote HTTPS registry with SHA-256 verification."""
        import urllib.parse
        import urllib.request
        import urllib.error

        target_dir_abs = os.path.realpath(os.path.abspath(target_dir))
        os.makedirs(target_dir_abs, exist_ok=True)
        pkg_filename = entry.package_file or f"{entry.plugin_id}-{entry.version}.aegis-plugin"
        final_path = os.path.join(target_dir_abs, pkg_filename)
        tmp_path = final_path + ".tmp"

        url = f"{self.base_url}/api/v1/packages/{urllib.parse.quote(pkg_filename)}"
        req = self._build_request(url)

        try:
            h = hashlib.sha256()
            with urllib.request.urlopen(req, timeout=self.timeout) as resp, open(tmp_path, "wb") as f:
                while chunk := resp.read(65536):
                    h.update(chunk)
                    f.write(chunk)
                f.flush()
                os.fsync(f.fileno())

            actual_hash = h.hexdigest()
            if entry.checksum and actual_hash != entry.checksum:
                os.remove(tmp_path)
                raise PackageIntegrityError(
                    f"Remote download integrity mismatch for '{pkg_filename}': expected {entry.checksum[:10]}..., got {actual_hash[:10]}..."
                )

            os.replace(tmp_path, final_path)
            return final_path

        except Exception as exc:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise MarketplaceError(f"Failed to download remote package '{pkg_filename}': {exc}") from exc

    def publish(self, entry: RegistryEntry, package_bytes: bytes) -> bool:
        """Publishes a new package to the remote HTTPS registry."""
        import urllib.request
        import urllib.error

        url = f"{self.base_url}/api/v1/plugins/publish"
        req = self._build_request(url, method="POST", data=package_bytes)
        req.add_header("Content-Type", "application/octet-stream")
        req.add_header("X-Plugin-Id", entry.plugin_id)
        req.add_header("X-Plugin-Version", entry.version)

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return resp.status in (200, 201)
        except Exception as exc:
            logger.error("RemoteHTTPRegistry publish error: %s", exc)
            return False

    def list_available(self) -> List[RegistryEntry]:
        """Lists available packages from remote HTTPS registry."""
        import urllib.request
        import urllib.error

        url = f"{self.base_url}/api/v1/plugins"
        req = self._build_request(url)

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                if resp.status == 200:
                    payload = json.loads(resp.read().decode("utf-8"))
                    return [RegistryEntry.from_dict(item) for item in payload.get("results", [])]
        except Exception as exc:
            logger.warning("RemoteHTTPRegistry list_available error: %s", exc)

        if self.fallback_registry:
            return self.fallback_registry.list_available()
        return []


# ──────────────────────────────────────────────
# Main Plugin Marketplace Manager Facade
# ──────────────────────────────────────────────

class PluginMarketplaceManager:
    """Central Aegis Supply Chain & Marketplace Subsystem Manager.

    Handles packaging, integrity verification, digital signatures,
    trust policies, atomic installation, version history, rollback,
    effective sandbox policies, and CLI marketplace management.
    """

    def __init__(self, config: AegisConfig, plugin_manager: PluginManager):
        self.config = config
        self.plugin_manager = plugin_manager
        self._lock = threading.RLock()

        self.marketplace_dir = os.path.abspath(os.path.join(config.base_dir, "runtime", "marketplace"))
        self.key_store_dir = os.path.join(self.marketplace_dir, "keystore")
        self.registry_dir = os.path.join(self.marketplace_dir, "registry")
        self.staging_dir = os.path.join(self.marketplace_dir, "staging")
        os.makedirs(self.staging_dir, exist_ok=True)

        self.key_store = TrustedKeyStore(self.key_store_dir)
        self.signature_verifier = PluginSignatureVerifier(self.key_store)
        self.package_validator = PluginPackageValidator()
        self.integrity_verifier = PluginIntegrityVerifier()
        self.local_registry = LocalRegistry(self.registry_dir)
        self.observability = ObservabilityManager.get_instance()

    # ── 1. Packaging & Manifest V2 Helper ──

    def create_package(self, plugin_dir: str, output_path: Optional[str] = None, key_id: Optional[str] = None) -> str:
        """Packages a plugin directory into a signed/hashed .aegis-plugin bundle."""
        with self._lock:
            plugin_dir_abs = os.path.realpath(os.path.abspath(plugin_dir))
            manifest_file = os.path.join(plugin_dir_abs, "manifest.yaml")
            if not os.path.exists(manifest_file):
                manifest_file = os.path.join(plugin_dir_abs, "manifest.json")
            if not os.path.exists(manifest_file):
                raise PackageValidationError(f"No manifest file found in: {plugin_dir_abs}")

            # Load and validate manifest
            discovery = self.plugin_manager.discovery
            manifest = discovery._try_load_manifest(plugin_dir_abs)
            if not manifest:
                raise PackageValidationError(f"Invalid plugin manifest in: {plugin_dir_abs}")

            errors = ManifestValidator().validate(manifest)
            if errors:
                raise PluginManifestError(f"Manifest validation failed: {'; '.join(errors)}")

            # Generate checksums.json
            checksums = self.integrity_verifier.generate_checksums(plugin_dir_abs)
            checksums_file = os.path.join(plugin_dir_abs, "checksums.json")
            with open(checksums_file, "w", encoding="utf-8") as f:
                json.dump({"files": checksums}, f, indent=2)

            # Generate signature.json if key_id provided or available
            sig_file = os.path.join(plugin_dir_abs, "signature.json")
            target_key_id = key_id or "aegis_official_key"
            secret = self.key_store.keys.get(target_key_id)

            if secret:
                with open(manifest_file, "rb") as f:
                    m_bytes = f.read()
                with open(checksums_file, "rb") as f:
                    c_bytes = f.read()

                payload_digest = self.signature_verifier.compute_payload_digest(m_bytes, c_bytes)
                sig_val = self.signature_verifier.sign_payload(secret, payload_digest)

                sig_meta = SignatureMetadata(
                    publisher=manifest.publisher or manifest.author or "Aegis Publisher",
                    key_id=target_key_id,
                    signature=sig_val,
                )
                with open(sig_file, "w", encoding="utf-8") as f:
                    json.dump(sig_meta.to_dict(), f, indent=2)

            # Zip into .aegis-plugin bundle
            out_file = output_path or os.path.join(
                os.path.dirname(plugin_dir_abs),
                f"{manifest.plugin_id}-{manifest.version}.aegis-plugin"
            )

            with zipfile.ZipFile(out_file, "w", zipfile.ZIP_DEFLATED) as zf:
                for root, _, files in os.walk(plugin_dir_abs):
                    for file in files:
                        full_f = os.path.join(root, file)
                        rel_f = os.path.relpath(full_f, plugin_dir_abs).replace("\\", "/")
                        zf.write(full_f, rel_f)

            logger.info("Successfully packaged plugin '%s' v%s -> %s", manifest.plugin_id, manifest.version, out_file)
            return out_file

    # ── 2. Verification & Trust Policy Engine ──

    def inspect_and_verify_package(self, zip_path: str) -> Tuple[PluginManifest, TrustLevel, List[str]]:
        """Extracts package to staging, verifies integrity, signature, SemVer, and returns trust evaluation."""
        with self._lock:
            temp_staging = os.path.join(self.staging_dir, f"inspect_{int(time.time_ns())}")
            try:
                extracted = self.package_validator.validate_and_extract(zip_path, temp_staging)

                # Load manifest
                discovery = self.plugin_manager.discovery
                manifest = discovery._try_load_manifest(temp_staging)
                if not manifest:
                    raise PackageValidationError("Package contains no valid manifest file")

                # Verify checksums.json integrity
                checksums_file = os.path.join(temp_staging, "checksums.json")
                if not os.path.exists(checksums_file):
                    raise PackageIntegrityError("Package is missing required 'checksums.json'")

                with open(checksums_file, "r", encoding="utf-8") as f:
                    chk_data = json.load(f).get("files", {})

                chk_errors = self.integrity_verifier.verify_integrity(temp_staging, chk_data)
                if chk_errors:
                    raise PackageIntegrityError(f"Integrity check failed: {'; '.join(chk_errors)}")

                # Check digital signature
                sig_file = os.path.join(temp_staging, "signature.json")
                sig_meta = None
                if os.path.exists(sig_file):
                    with open(sig_file, "r", encoding="utf-8") as f:
                        sig_meta = SignatureMetadata.from_dict(json.load(f))

                manifest_file = os.path.join(temp_staging, "manifest.yaml")
                if not os.path.exists(manifest_file):
                    manifest_file = os.path.join(temp_staging, "manifest.json")

                with open(manifest_file, "rb") as f:
                    m_bytes = f.read()
                with open(checksums_file, "rb") as f:
                    c_bytes = f.read()

                sig_status, sig_msg = self.signature_verifier.verify_signature(m_bytes, c_bytes, sig_meta)

                # Determine TrustLevel
                if self.key_store.is_plugin_blocked(manifest.plugin_id):
                    trust_level = TrustLevel.BLOCKED
                elif sig_status == SignatureStatus.TRUSTED:
                    trust_level = TrustLevel.TRUSTED
                elif sig_status == SignatureStatus.INVALID:
                    trust_level = TrustLevel.BLOCKED
                elif sig_status == SignatureStatus.REVOKED:
                    trust_level = TrustLevel.BLOCKED
                else:
                    trust_level = TrustLevel.UNTRUSTED

                warnings: List[str] = [sig_msg]
                return manifest, trust_level, warnings

            finally:
                if os.path.exists(temp_staging):
                    shutil.rmtree(temp_staging, ignore_errors=True)

    # ── 3. Effective Permission & Sandbox Intersect ──

    def compute_effective_sandbox_policy(self, manifest: PluginManifest, trust_level: TrustLevel) -> SandboxPolicy:
        """Calculates effective sandbox policy by intersecting requested permissions with trust level limits."""
        if trust_level == TrustLevel.BLOCKED:
            return SandboxPolicy.default_deny()

        policy = SandboxPolicy.default_deny()
        requested_perms = set(manifest.permissions)

        # CORE plugins get full allowed flags
        if trust_level == TrustLevel.CORE:
            policy.allow_filesystem_read = PluginPermission.FILESYSTEM_READ in requested_perms
            policy.allow_filesystem_write = PluginPermission.FILESYSTEM_WRITE in requested_perms
            policy.allow_network = PluginPermission.NETWORK_OUTBOUND in requested_perms
            policy.allow_subprocess = PluginPermission.PROCESS_EXECUTE in requested_perms
            policy.allow_env_access = PluginPermission.SECRET_ACCESS in requested_perms
            return policy

        # TRUSTED & VERIFIED plugins get intersect based on manifest
        if trust_level in (TrustLevel.TRUSTED, TrustLevel.VERIFIED):
            policy.allow_filesystem_read = PluginPermission.FILESYSTEM_READ in requested_perms
            policy.allow_filesystem_write = PluginPermission.FILESYSTEM_WRITE in requested_perms
            policy.allow_network = PluginPermission.NETWORK_OUTBOUND in requested_perms
            policy.allow_subprocess = False  # Subprocess forbidden for non-core
            policy.allow_env_access = False
            return policy

        # UNTRUSTED plugins stay strict Default DENY
        return SandboxPolicy.default_deny()

    # ── 4. Atomic Install, Update & Rollback Engine ──

    def install_package(self, zip_path: str, force_untrusted: bool = False) -> bool:
        """Installs a plugin package using atomic staging and version history directory structure."""
        with self._lock:
            manifest, trust_level, warnings = self.inspect_and_verify_package(zip_path)

            if trust_level == TrustLevel.BLOCKED:
                self.observability.publish_event(
                    level=EventLevel.ERROR, category=EventCategory.SECURITY,
                    event_type=MarketplaceEvent.BLOCKED.value, component="Marketplace",
                    operation="install", message=f"Installation DENIED for blocked plugin '{manifest.plugin_id}'"
                )
                raise TrustPolicyError(f"Plugin '{manifest.plugin_id}' is BLOCKED by system security policy")

            if trust_level == TrustLevel.UNTRUSTED and not force_untrusted:
                self.observability.publish_event(
                    level=EventLevel.WARNING, category=EventCategory.SECURITY,
                    event_type=MarketplaceEvent.SIGNATURE_FAILED.value, component="Marketplace",
                    operation="install", message=f"Unsigned plugin '{manifest.plugin_id}' install rejected (force_untrusted=False)"
                )
                raise TrustPolicyError(
                    f"Unsigned plugin '{manifest.plugin_id}' rejected. Set force_untrusted=True for local development."
                )

            # Versioned directory layout: plugins/<plugin_id>/versions/<version>/
            plugin_base_dir = os.path.join(self.plugin_manager.plugins_dir, manifest.plugin_id)
            versions_dir = os.path.join(plugin_base_dir, "versions")
            target_version_dir = os.path.join(versions_dir, manifest.version)
            active_link_dir = os.path.join(plugin_base_dir, "active")

            # Extract to staging first
            staging_instance = os.path.join(self.staging_dir, f"install_{manifest.plugin_id}_{int(time.time_ns())}")
            try:
                self.package_validator.validate_and_extract(zip_path, staging_instance)

                # Check dependency compatibility with existing plugins
                all_manifests = self.plugin_manager.registry.get_manifests()
                all_manifests[manifest.plugin_id] = manifest
                self.plugin_manager.dep_resolver.validate_versions(all_manifests)

                # Copy from staging to target_version_dir
                if os.path.exists(target_version_dir):
                    shutil.rmtree(target_version_dir, ignore_errors=True)
                os.makedirs(os.path.dirname(target_version_dir), exist_ok=True)
                shutil.copytree(staging_instance, target_version_dir)

                # Atomic swap active link/pointer
                if os.path.exists(active_link_dir):
                    if os.path.islink(active_link_dir):
                        os.unlink(active_link_dir)
                    else:
                        shutil.rmtree(active_link_dir, ignore_errors=True)

                # On POSIX create symlink active -> versions/<version>, on Windows copytree
                try:
                    os.symlink(os.path.join("versions", manifest.version), active_link_dir)
                except (OSError, AttributeError):
                    shutil.copytree(target_version_dir, active_link_dir)

                # Reload / Register in PluginManager
                self.plugin_manager.discover_plugins()
                if self.plugin_manager.registry.get_metadata(manifest.plugin_id):
                    self.plugin_manager.validate_plugin(manifest.plugin_id)
                    self.plugin_manager.resolve_dependencies()
                    self.plugin_manager.activate_plugin(manifest.plugin_id)

                self.observability.publish_event(
                    level=EventLevel.INFO, category=EventCategory.PLUGIN,
                    event_type=MarketplaceEvent.INSTALL_COMPLETED.value, component="Marketplace",
                    operation="install", message=f"Successfully installed plugin '{manifest.plugin_id}' v{manifest.version} [{trust_level.value}]"
                )
                logger.info("Installed plugin '%s' v%s", manifest.plugin_id, manifest.version)
                return True

            except Exception as exc:
                self.observability.publish_event(
                    level=EventLevel.ERROR, category=EventCategory.PLUGIN,
                    event_type=MarketplaceEvent.INSTALL_FAILED.value, component="Marketplace",
                    operation="install", message=f"Installation failed for '{manifest.plugin_id}': {exc}"
                )
                if os.path.exists(target_version_dir):
                    shutil.rmtree(target_version_dir, ignore_errors=True)
                raise MarketplaceError(f"Atomic installation failed for '{manifest.plugin_id}': {exc}") from exc
            finally:
                if os.path.exists(staging_instance):
                    shutil.rmtree(staging_instance, ignore_errors=True)

    def rollback_plugin(self, plugin_id: str, target_version: str) -> bool:
        """Rolls back an installed plugin to a previously installed version atomically."""
        with self._lock:
            plugin_base_dir = os.path.join(self.plugin_manager.plugins_dir, plugin_id)
            target_version_dir = os.path.join(plugin_base_dir, "versions", target_version)
            active_link_dir = os.path.join(plugin_base_dir, "active")

            if not os.path.exists(target_version_dir):
                raise MarketplaceError(f"Rollback target version '{target_version}' for plugin '{plugin_id}' does not exist")

            self.observability.publish_event(
                level=EventLevel.INFO, category=EventCategory.PLUGIN,
                event_type=MarketplaceEvent.ROLLBACK_STARTED.value, component="Marketplace",
                operation="rollback", message=f"Starting rollback for '{plugin_id}' to v{target_version}"
            )

            # Atomic swap pointer to target version
            if os.path.exists(active_link_dir):
                if os.path.islink(active_link_dir):
                    os.unlink(active_link_dir)
                else:
                    shutil.rmtree(active_link_dir, ignore_errors=True)

            try:
                os.symlink(os.path.join("versions", target_version), active_link_dir)
            except (OSError, AttributeError):
                shutil.copytree(target_version_dir, active_link_dir)

            self.plugin_manager.discover_plugins()
            if self.plugin_manager.registry.get_metadata(plugin_id):
                self.plugin_manager.validate_plugin(plugin_id)
                self.plugin_manager.resolve_dependencies()
                self.plugin_manager.activate_plugin(plugin_id)

            self.observability.publish_event(
                level=EventLevel.INFO, category=EventCategory.PLUGIN,
                event_type=MarketplaceEvent.ROLLBACK_COMPLETED.value, component="Marketplace",
                operation="rollback", message=f"Rollback completed for '{plugin_id}' -> v{target_version}"
            )
            return True

    def uninstall_plugin(self, plugin_id: str) -> bool:
        """Uninstalls and removes a plugin directory completely."""
        with self._lock:
            plugin_base_dir = os.path.join(self.plugin_manager.plugins_dir, plugin_id)
            if not os.path.exists(plugin_base_dir):
                return False

            self.plugin_manager.unload_plugin(plugin_id)
            shutil.rmtree(plugin_base_dir, ignore_errors=True)

            self.observability.publish_event(
                level=EventLevel.INFO, category=EventCategory.PLUGIN,
                event_type=MarketplaceEvent.UNINSTALL.value, component="Marketplace",
                operation="uninstall", message=f"Uninstalled plugin '{plugin_id}'"
            )
            return True
