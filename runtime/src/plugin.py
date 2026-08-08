"""
Aegis AI Operating System — Production Plugin Architecture Subsystem (v2.0.0)
Provides extensible plugin lifecycle management, dependency resolution (DAG),
event-driven hooks, permission-based security, hot-reload, sandbox isolation,
capability tokens, metrics telemetry, AI-native capability registry,
hook dispatcher, YAML/JSON manifest parsing, and plugin SDK.
Python 3.12+ compliant. Zero external dependencies.
"""

import os
import re
import json
import time
import hashlib
import logging
import threading
import concurrent.futures
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import (
    ClassVar, Dict, List, Optional, Set, Tuple, Any, Callable, Protocol,
)

logger = logging.getLogger("AegisPluginSystem")


# ──────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────

class PluginState(Enum):
    """Finite State Machine for plugin lifecycle."""
    DISCOVERED = "DISCOVERED"
    LOADED = "LOADED"
    VALIDATED = "VALIDATED"
    RESOLVED = "RESOLVED"
    INITIALIZED = "INITIALIZED"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    UNLOADED = "UNLOADED"
    DESTROYED = "DESTROYED"
    FAILED = "FAILED"



class PluginCapability(Enum):
    """Capabilities a plugin can declare."""
    PIPELINE_STAGE = "PIPELINE_STAGE"
    QUALITY_VALIDATOR = "QUALITY_VALIDATOR"
    REASONING_STRATEGY = "REASONING_STRATEGY"
    KNOWLEDGE_SOURCE = "KNOWLEDGE_SOURCE"
    EVENT_HANDLER = "EVENT_HANDLER"
    SESSION_HOOK = "SESSION_HOOK"
    MODEL_PROVIDER = "MODEL_PROVIDER"
    TRUTH_VERIFIER = "TRUTH_VERIFIER"
    PROMPT_TRANSFORMER = "PROMPT_TRANSFORMER"
    COMMAND = "COMMAND"
    TEMPLATE = "TEMPLATE"
    AGENT = "AGENT"
    TOOL = "TOOL"


class PluginPermission(Enum):
    """Permissions a plugin can request. Default policy: DENY ALL."""
    FILESYSTEM_READ = "FILESYSTEM_READ"
    FILESYSTEM_WRITE = "FILESYSTEM_WRITE"
    NETWORK_OUTBOUND = "NETWORK_OUTBOUND"
    SECRET_ACCESS = "SECRET_ACCESS"
    PIPELINE_MODIFY = "PIPELINE_MODIFY"
    SESSION_ACCESS = "SESSION_ACCESS"
    KNOWLEDGE_WRITE = "KNOWLEDGE_WRITE"
    PROCESS_EXECUTE = "PROCESS_EXECUTE"
    RUNTIME_MODIFY = "RUNTIME_MODIFY"
    MEMORY_WRITE = "MEMORY_WRITE"


class PluginHook(Enum):
    """Extension points in the Aegis runtime pipeline."""
    PRE_PIPELINE = "PRE_PIPELINE"
    POST_PIPELINE = "POST_PIPELINE"
    PRE_STAGE = "PRE_STAGE"
    POST_STAGE = "POST_STAGE"
    ON_ERROR = "ON_ERROR"
    ON_SESSION_CREATE = "ON_SESSION_CREATE"
    ON_SESSION_DESTROY = "ON_SESSION_DESTROY"
    BEFORE_INTENT = "BEFORE_INTENT"
    AFTER_INTENT = "AFTER_INTENT"
    BEFORE_REASONING = "BEFORE_REASONING"
    AFTER_REASONING = "AFTER_REASONING"
    BEFORE_TRUTH = "BEFORE_TRUTH"
    AFTER_TRUTH = "AFTER_TRUTH"
    BEFORE_QUALITY = "BEFORE_QUALITY"
    AFTER_QUALITY = "AFTER_QUALITY"
    BEFORE_GENERATION = "BEFORE_GENERATION"
    AFTER_GENERATION = "AFTER_GENERATION"
    BEFORE_DELIVERY = "BEFORE_DELIVERY"
    AFTER_DELIVERY = "AFTER_DELIVERY"
    ON_KNOWLEDGE_LOAD = "ON_KNOWLEDGE_LOAD"
    ON_MODEL_RESPONSE = "ON_MODEL_RESPONSE"
    ON_QUALITY_CHECK = "ON_QUALITY_CHECK"


class SandboxLevel(Enum):
    """Isolation levels for plugin execution."""
    NONE = "NONE"
    BASIC = "BASIC"
    STRICT = "STRICT"


# ──────────────────────────────────────────────
# Data Structures
# ──────────────────────────────────────────────

@dataclass
class PluginDependency:
    """Versioned dependency declaration."""
    plugin_id: str
    min_version: str = "0.0.0"
    max_version: str = ""
    is_optional: bool = False


@dataclass
class PluginManifest:
    """Static declaration of plugin identity and requirements (Manifest V2)."""
    plugin_id: str
    name: str
    version: str
    description: str = ""
    author: str = ""
    capabilities: List[PluginCapability] = field(default_factory=list)
    permissions: List[PluginPermission] = field(default_factory=list)
    hooks: List[PluginHook] = field(default_factory=list)
    dependencies: List[PluginDependency] = field(default_factory=list)
    sandbox_level: SandboxLevel = SandboxLevel.BASIC
    priority: int = 100
    license: str = ""
    aegis_compatibility: str = ">=2.0.0"
    python_compatibility: str = ">=3.12"
    entry_point: str = "plugin.py"
    config: Dict[str, Any] = field(default_factory=dict)
    publisher: str = ""
    repository: str = ""
    homepage: str = ""
    checksum: str = ""
    signature: str = ""
    namespace: str = "community"  # official, community, local

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plugin_id": self.plugin_id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "capabilities": [c.value for c in self.capabilities],
            "permissions": [p.value for p in self.permissions],
            "hooks": [h.value for h in self.hooks],
            "dependencies": [
                {"plugin_id": d.plugin_id, "min_version": d.min_version,
                 "max_version": d.max_version, "is_optional": d.is_optional}
                for d in self.dependencies
            ],
            "sandbox_level": self.sandbox_level.value,
            "priority": self.priority,
            "license": self.license,
            "aegis_compatibility": self.aegis_compatibility,
            "python_compatibility": self.python_compatibility,
            "entry_point": self.entry_point,
            "config": self.config,
            "publisher": self.publisher,
            "repository": self.repository,
            "homepage": self.homepage,
            "checksum": self.checksum,
            "signature": self.signature,
            "namespace": self.namespace,
        }


@dataclass
class PluginResources:
    """Resource limits for sandboxed plugin execution."""
    max_memory_bytes: int = 50 * 1024 * 1024  # 50 MB
    max_cpu_time_ms: int = 5000
    max_timeout_seconds: float = 30.0
    max_file_write_bytes: int = 10 * 1024 * 1024  # 10 MB
    max_concurrency: int = 4
    max_output_bytes: int = 50 * 1024 * 1024  # 50 MB


@dataclass
class PluginMetrics:
    """Runtime telemetry for a single plugin."""
    load_time_ms: float = 0.0
    activate_time_ms: float = 0.0
    call_count: int = 0
    error_count: int = 0
    total_execution_time_ms: float = 0.0

    @property
    def avg_latency_ms(self) -> float:
        if self.call_count == 0:
            return 0.0
        return round(self.total_execution_time_ms / self.call_count, 2)


@dataclass
class PluginMetadata:
    """Runtime state container for a registered plugin."""
    manifest: PluginManifest
    state: PluginState = PluginState.DISCOVERED
    metrics: PluginMetrics = field(default_factory=PluginMetrics)
    source_path: str = ""
    checksum: str = ""
    loaded_at_utc: float = 0.0
    enabled: bool = True


@dataclass
class PluginEvent:
    """Event object for plugin inter-communication."""
    event_type: str
    source_plugin_id: str
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp_utc: float = field(default_factory=time.time)


@dataclass
class PluginEventFilter:
    """Filter for selective event subscription."""
    event_types: List[str] = field(default_factory=list)
    source_plugin_ids: List[str] = field(default_factory=list)
    priority: int = 0


@dataclass
class CapabilityToken:
    """Runtime capability token for permission checking."""
    plugin_id: str
    granted_permissions: Set[PluginPermission] = field(default_factory=set)
    issued_at_utc: float = field(default_factory=time.time)

    def has_permission(self, permission: PluginPermission) -> bool:
        return permission in self.granted_permissions


@dataclass
class PluginContext:
    """Isolated runtime context provided to plugin lifecycle methods."""
    plugin_id: str
    config: Dict[str, Any] = field(default_factory=dict)
    token: Optional[CapabilityToken] = None
    resources: PluginResources = field(default_factory=PluginResources)
    storage_dir: str = ""


@dataclass
class PluginPromptContribution:
    """Content contributed by a plugin to the PromptComposer.
    Layer 0 Kernel always takes priority — plugin prompts never override it.
    """
    plugin_id: str
    content: str
    section: str = "plugin_context"
    priority: int = 100
    token_budget: int = 500


@dataclass
class CapabilityEntry:
    """Entry in the AI-native Capability Registry."""
    capability_type: str
    name: str
    plugin_id: str
    handler: Any
    priority: int = 100
    metadata: Dict[str, Any] = field(default_factory=dict)


# ──────────────────────────────────────────────
# Exceptions
# ──────────────────────────────────────────────

class PluginError(Exception):
    """Base exception for plugin subsystem errors."""
    pass


class PluginNotFoundError(PluginError):
    """Raised when a requested plugin does not exist."""
    pass


class PluginLifecycleError(PluginError):
    """Raised when an invalid state transition is attempted."""
    pass


class PluginPermissionError(PluginError):
    """Raised when a plugin attempts an unauthorized operation."""
    pass


class PluginDependencyError(PluginError):
    """Raised for dependency resolution failures."""
    pass


class CircularPluginDependencyError(PluginDependencyError):
    """Raised when circular dependencies are detected."""
    pass


class PluginManifestError(PluginError):
    """Raised when a plugin manifest is invalid or malformed."""
    pass


class PluginCapabilityError(PluginError):
    """Raised for capability registry errors."""
    pass


# ──────────────────────────────────────────────
# Plugin Interface (Protocol — backward compatibility)
# ──────────────────────────────────────────────

class PluginInterface(Protocol):
    """Contract that all Aegis plugins must satisfy."""

    def get_manifest(self) -> PluginManifest: ...
    def on_initialize(self, ctx: PluginContext) -> bool: ...
    def on_activate(self, ctx: PluginContext) -> bool: ...
    def on_execute(self, ctx: PluginContext, data: Dict[str, Any]) -> Any: ...
    def on_suspend(self, ctx: PluginContext) -> bool: ...
    def on_resume(self, ctx: PluginContext) -> bool: ...
    def on_unload(self, ctx: PluginContext) -> bool: ...
    def on_destroy(self, ctx: PluginContext) -> bool: ...


# ──────────────────────────────────────────────
# AegisPlugin SDK (Abstract Base Class)
# ──────────────────────────────────────────────

class AegisPlugin(ABC):
    """Aegis Plugin SDK — barcha plugin'lar uchun asosiy abstrakt klass.

    Har bir plugin bu klassdan meros olishi va kamida get_manifest()
    metodini amalga oshirishi kerak. Qolgan lifecycle metodlari
    default (muvaffaqiyatli) qiymatlarni qaytaradi.
    """

    @abstractmethod
    def get_manifest(self) -> PluginManifest:
        """Plugin manifest'ini qaytaradi."""
        ...

    def on_initialize(self, ctx: PluginContext) -> bool:
        """Plugin ishga tushirilganda chaqiriladi."""
        return True

    def on_activate(self, ctx: PluginContext) -> bool:
        """Plugin faollashtirilganda chaqiriladi."""
        return True

    def on_execute(self, ctx: PluginContext, data: Dict[str, Any]) -> Any:
        """Plugin bajarilganda chaqiriladi."""
        return None

    def on_suspend(self, ctx: PluginContext) -> bool:
        """Plugin to'xtatilganda chaqiriladi."""
        return True

    def on_resume(self, ctx: PluginContext) -> bool:
        """Plugin qayta faollashtirilganda chaqiriladi."""
        return True

    def on_unload(self, ctx: PluginContext) -> bool:
        """Plugin yukdan tushirilganda chaqiriladi."""
        return True

    def on_destroy(self, ctx: PluginContext) -> bool:
        """Plugin yo'q qilinganda chaqiriladi."""
        return True

    def get_capabilities(self) -> Dict[str, List[Any]]:
        """Plugin capability'larini qaytaradi.

        Kalit nomlari: 'commands', 'validators', 'reasoners', 'quality_rules',
        'knowledge_modules', 'prompts', 'templates', 'agents', 'tools'
        """
        return {}

    def get_hook_handlers(self) -> Dict[PluginHook, Callable[[Dict[str, Any]], Any]]:
        """Plugin hook handler'larini qaytaradi."""
        return {}

    def get_prompt_contributions(self) -> List[PluginPromptContribution]:
        """Plugin prompt qo'shimchalarini qaytaradi.
        Layer 0 Kernel har doim ustuvor — plugin promptlari uni override qilmaydi.
        """
        return []


# ──────────────────────────────────────────────
# Version Utilities
# ──────────────────────────────────────────────

def parse_semver(version: str) -> Tuple[int, int, int]:
    """Parses a semantic version string into (major, minor, patch)."""
    parts = version.strip().split(".")
    if len(parts) != 3:
        raise ValueError(f"Invalid SemVer: '{version}'")
    return (int(parts[0]), int(parts[1]), int(parts[2]))


def version_satisfies(actual: str, min_ver: str, max_ver: str = "") -> bool:
    """Checks whether actual version is within [min_ver, max_ver)."""
    actual_t = parse_semver(actual)
    min_t = parse_semver(min_ver)
    if actual_t < min_t:
        return False
    if max_ver:
        max_t = parse_semver(max_ver)
        if actual_t >= max_t:
            return False
    return True


def check_version_constraint(actual: str, constraint: str) -> bool:
    """Checks version against a constraint like '>=2.0.0' or '>=1.0.0,<3.0.0'."""
    if not constraint:
        return True
    parts = [c.strip() for c in constraint.split(",")]
    actual_t = parse_semver(actual)
    for part in parts:
        if part.startswith(">="):
            if actual_t < parse_semver(part[2:]):
                return False
        elif part.startswith(">"):
            if actual_t <= parse_semver(part[1:]):
                return False
        elif part.startswith("<="):
            if actual_t > parse_semver(part[2:]):
                return False
        elif part.startswith("<"):
            if actual_t >= parse_semver(part[1:]):
                return False
        elif part.startswith("=="):
            if actual_t != parse_semver(part[2:]):
                return False
    return True


# ──────────────────────────────────────────────
# Minimal YAML Parser (no external dependencies)
# ──────────────────────────────────────────────

def _parse_yaml_value(value: str) -> Any:
    """Parses a scalar YAML value into a Python object."""
    if not value:
        return None
    stripped = value.strip()
    if (stripped.startswith('"') and stripped.endswith('"')) or \
       (stripped.startswith("'") and stripped.endswith("'")):
        return stripped[1:-1]
    lower = stripped.lower()
    if lower in ("true", "yes"):
        return True
    if lower in ("false", "no"):
        return False
    if lower in ("null", "~"):
        return None
    if stripped == "[]":
        return []
    if stripped == "{}":
        return {}
    try:
        if "." in stripped:
            return float(stripped)
        return int(stripped)
    except ValueError:
        return stripped


def parse_yaml_minimal(text: str) -> Dict[str, Any]:
    """Minimal YAML parser supporting flat key-value, simple lists, and one-level nesting.

    Handles the subset of YAML used in Aegis plugin manifests:
    - key: value (scalars: str, int, float, bool, null)
    - key: (followed by indented '- item' list)
    - key: (followed by indented 'sub_key: value' dict)
    - Comments (# ...) and blank lines
    """
    result: Dict[str, Any] = {}
    lines = text.split("\n")
    i = 0
    total = len(lines)

    while i < total:
        line = lines[i]
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            i += 1
            continue

        indent = len(line) - len(line.lstrip())
        if indent > 0:
            i += 1
            continue

        if ":" not in stripped:
            i += 1
            continue

        colon_idx = stripped.index(":")
        key = stripped[:colon_idx].strip()
        value_part = stripped[colon_idx + 1:].strip()

        if value_part and not value_part.startswith("#"):
            if value_part.startswith("#"):
                result[key] = None
            else:
                comment_idx = -1
                in_quotes = False
                for ci, ch in enumerate(value_part):
                    if ch in ('"', "'"):
                        in_quotes = not in_quotes
                    elif ch == '#' and not in_quotes:
                        comment_idx = ci
                        break
                clean_value = value_part[:comment_idx].strip() if comment_idx >= 0 else value_part
                result[key] = _parse_yaml_value(clean_value)
        else:
            items: List[Any] = []
            nested: Dict[str, Any] = {}
            i += 1
            while i < total:
                sub_line = lines[i]
                sub_stripped = sub_line.strip()
                sub_indent = len(sub_line) - len(sub_line.lstrip())

                if not sub_stripped or sub_stripped.startswith("#"):
                    i += 1
                    continue

                if sub_indent == 0:
                    break

                if sub_stripped.startswith("- "):
                    item_val = sub_stripped[2:].strip()
                    items.append(_parse_yaml_value(item_val))
                elif ":" in sub_stripped:
                    sub_colon = sub_stripped.index(":")
                    sub_key = sub_stripped[:sub_colon].strip()
                    sub_val = sub_stripped[sub_colon + 1:].strip()
                    nested[sub_key] = _parse_yaml_value(sub_val)
                i += 1

            if items:
                result[key] = items
            elif nested:
                result[key] = nested
            else:
                result[key] = []
            continue

        i += 1

    return result


# ──────────────────────────────────────────────
# Plugin Event Bus
# ──────────────────────────────────────────────

class PluginEventBus:
    """Thread-safe event publish/subscribe system for plugins."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._subscribers: List[Tuple[PluginEventFilter, Callable[[PluginEvent], None]]] = []
        self._error_counts: Dict[int, int] = {}
        self._max_consecutive_errors: int = 3
        self._async_executor: Optional[concurrent.futures.ThreadPoolExecutor] = None

    def subscribe(self, handler: Callable[[PluginEvent], None],
                  event_filter: Optional[PluginEventFilter] = None) -> None:
        with self._lock:
            filt = event_filter or PluginEventFilter()
            self._subscribers.append((filt, handler))
            self._subscribers.sort(key=lambda x: -x[0].priority)

    def publish(self, event: PluginEvent) -> None:
        with self._lock:
            to_remove: List[int] = []
            for idx, (filt, handler) in enumerate(self._subscribers):
                if filt.event_types and event.event_type not in filt.event_types:
                    continue
                if filt.source_plugin_ids and event.source_plugin_id not in filt.source_plugin_ids:
                    continue
                try:
                    handler(event)
                    self._error_counts[idx] = 0
                except Exception as exc:
                    logger.warning("Event handler error for '%s': %s", event.event_type, exc)
                    self._error_counts[idx] = self._error_counts.get(idx, 0) + 1
                    if self._error_counts[idx] >= self._max_consecutive_errors:
                        to_remove.append(idx)

            for idx in reversed(to_remove):
                if idx < len(self._subscribers):
                    self._subscribers.pop(idx)

    def publish_async(self, event: PluginEvent) -> None:
        """Publishes an event asynchronously using a thread pool."""
        if self._async_executor is None:
            self._async_executor = concurrent.futures.ThreadPoolExecutor(
                max_workers=2, thread_name_prefix="aegis_event"
            )
        self._async_executor.submit(self.publish, event)

    def clear(self) -> None:
        with self._lock:
            self._subscribers.clear()
            self._error_counts.clear()
            if self._async_executor is not None:
                self._async_executor.shutdown(wait=False)
                self._async_executor = None

    @property
    def subscriber_count(self) -> int:
        with self._lock:
            return len(self._subscribers)


# ──────────────────────────────────────────────
# Plugin Dependency Resolver
# ──────────────────────────────────────────────

class PluginDependencyResolver:
    """Resolves plugin dependencies using topological sort with cycle detection."""

    def resolve(self, manifests: Dict[str, PluginManifest]) -> List[str]:
        """Returns plugin IDs in deterministic dependency-first load order."""
        in_degree: Dict[str, int] = {pid: 0 for pid in manifests}
        edges: Dict[str, Set[str]] = {pid: set() for pid in manifests}

        for pid, manifest in manifests.items():
            for dep in manifest.dependencies:
                if dep.plugin_id in manifests:
                    edges[dep.plugin_id].add(pid)
                    in_degree[pid] += 1
                elif not dep.is_optional:
                    raise PluginDependencyError(
                        f"Plugin '{pid}' requires missing dependency '{dep.plugin_id}'"
                    )

        queue = sorted([pid for pid in in_degree if in_degree[pid] == 0])
        ordered: List[str] = []

        while queue:
            curr = queue.pop(0)
            ordered.append(curr)
            for neighbor in sorted(edges.get(curr, set())):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
                    queue.sort()

        if len(ordered) != len(manifests):
            remaining = set(manifests.keys()) - set(ordered)
            raise CircularPluginDependencyError(
                f"Circular dependency detected among plugins: {', '.join(sorted(remaining))}"
            )

        return ordered

    def validate_versions(self, manifests: Dict[str, PluginManifest]) -> None:
        """Validates that all version constraints are satisfied."""
        for pid, manifest in manifests.items():
            for dep in manifest.dependencies:
                if dep.plugin_id in manifests:
                    actual_version = manifests[dep.plugin_id].version
                    if not version_satisfies(actual_version, dep.min_version, dep.max_version):
                        raise PluginDependencyError(
                            f"Plugin '{pid}' requires '{dep.plugin_id}' version "
                            f">={dep.min_version}"
                            f"{' <' + dep.max_version if dep.max_version else ''}, "
                            f"but found {actual_version}"
                        )


# ──────────────────────────────────────────────
# Plugin Security Manager
# ──────────────────────────────────────────────

class PluginSecurityManager:
    """Manages capability tokens and permission enforcement.

    Security model: Default DENY. A plugin may only use permissions
    that it declared in its manifest AND that were granted via token.
    """

    def __init__(self) -> None:
        self._tokens: Dict[str, CapabilityToken] = {}

    def issue_token(self, plugin_id: str, permissions: List[PluginPermission]) -> CapabilityToken:
        """Issues a capability token granting only the declared permissions."""
        token = CapabilityToken(
            plugin_id=plugin_id,
            granted_permissions=set(permissions)
        )
        self._tokens[plugin_id] = token
        return token

    def check_permission(self, plugin_id: str, permission: PluginPermission) -> bool:
        """Checks whether a plugin has a specific permission."""
        token = self._tokens.get(plugin_id)
        if not token:
            return False
        return token.has_permission(permission)

    def enforce(self, plugin_id: str, permission: PluginPermission) -> None:
        """Enforces a permission check, raising PluginPermissionError on denial."""
        if not self.check_permission(plugin_id, permission):
            raise PluginPermissionError(
                f"Plugin '{plugin_id}' lacks permission '{permission.value}'"
            )

    def revoke_token(self, plugin_id: str) -> None:
        """Revokes a plugin's capability token."""
        self._tokens.pop(plugin_id, None)

    def get_token(self, plugin_id: str) -> Optional[CapabilityToken]:
        """Returns the capability token for a plugin, or None."""
        return self._tokens.get(plugin_id)


# ──────────────────────────────────────────────
# Plugin Lifecycle Manager
# ──────────────────────────────────────────────

_VALID_TRANSITIONS: Dict[PluginState, Set[PluginState]] = {
    PluginState.DISCOVERED: {PluginState.LOADED, PluginState.DESTROYED, PluginState.FAILED},
    PluginState.LOADED: {PluginState.VALIDATED, PluginState.DESTROYED, PluginState.FAILED},
    PluginState.VALIDATED: {PluginState.RESOLVED, PluginState.DESTROYED, PluginState.FAILED},
    PluginState.RESOLVED: {PluginState.INITIALIZED, PluginState.DESTROYED, PluginState.FAILED},
    PluginState.INITIALIZED: {PluginState.ACTIVE, PluginState.DESTROYED, PluginState.FAILED},
    PluginState.ACTIVE: {PluginState.SUSPENDED, PluginState.UNLOADED, PluginState.ACTIVE, PluginState.FAILED},
    PluginState.SUSPENDED: {PluginState.ACTIVE, PluginState.UNLOADED, PluginState.FAILED},
    PluginState.UNLOADED: {PluginState.DESTROYED, PluginState.FAILED},
    PluginState.FAILED: {PluginState.SUSPENDED, PluginState.UNLOADED, PluginState.DESTROYED, PluginState.LOADED, PluginState.VALIDATED, PluginState.RESOLVED, PluginState.INITIALIZED, PluginState.ACTIVE},
    PluginState.DESTROYED: set(),
}



class PluginLifecycleManager:
    """Enforces valid state transitions for plugin lifecycle FSM."""

    def transition(self, metadata: PluginMetadata, target: PluginState) -> PluginMetadata:
        current = metadata.state
        valid = _VALID_TRANSITIONS.get(current, set())
        if target not in valid:
            raise PluginLifecycleError(
                f"Invalid transition for plugin '{metadata.manifest.plugin_id}': "
                f"{current.value} → {target.value}"
            )
        metadata.state = target
        return metadata


# ──────────────────────────────────────────────
# Capability Registry (AI-native)
# ──────────────────────────────────────────────

class CapabilityRegistry:
    """AI-native Capability Registry — plugin tomonidan registratsiya qilinadigan
    barcha capability'larni markaziy boshqaradi.

    Qo'llab-quvvatlanadigan capability turlari:
    commands, validators, reasoners, quality_rules, knowledge_modules,
    prompts, templates, agents, tools
    """

    VALID_TYPES: ClassVar[Set[str]] = {
        "commands", "validators", "reasoners", "quality_rules",
        "knowledge_modules", "prompts", "templates", "agents", "tools",
    }

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._entries: Dict[str, List[CapabilityEntry]] = {t: [] for t in self.VALID_TYPES}

    def register(self, entry: CapabilityEntry) -> None:
        """Registratsiya qiladi. capability_type VALID_TYPES da bo'lishi shart."""
        with self._lock:
            if entry.capability_type not in self.VALID_TYPES:
                raise PluginCapabilityError(
                    f"Noma'lum capability turi: '{entry.capability_type}'. "
                    f"Ruxsat etilgan turlar: {', '.join(sorted(self.VALID_TYPES))}"
                )
            self._entries[entry.capability_type].append(entry)
            self._entries[entry.capability_type].sort(key=lambda e: e.priority)

    def resolve(self, capability_type: str, **filters: Any) -> List[CapabilityEntry]:
        """Berilgan capability turi va filtrlarga mos entry'larni qaytaradi."""
        with self._lock:
            if capability_type not in self.VALID_TYPES:
                return []
            entries = list(self._entries[capability_type])
            if "plugin_id" in filters:
                entries = [e for e in entries if e.plugin_id == filters["plugin_id"]]
            if "name" in filters:
                entries = [e for e in entries if e.name == filters["name"]]
            return entries

    def unregister_plugin(self, plugin_id: str) -> None:
        """Berilgan plugin_id ga tegishli barcha capability'larni o'chiradi."""
        with self._lock:
            for cap_type in self._entries:
                self._entries[cap_type] = [
                    e for e in self._entries[cap_type] if e.plugin_id != plugin_id
                ]

    def list_all(self) -> Dict[str, List[CapabilityEntry]]:
        """Barcha registratsiya qilingan capability'larni qaytaradi."""
        with self._lock:
            return {k: list(v) for k, v in self._entries.items()}

    def get_summary(self) -> Dict[str, int]:
        """Har bir tur bo'yicha capability sonini qaytaradi."""
        with self._lock:
            return {k: len(v) for k, v in self._entries.items()}


# ──────────────────────────────────────────────
# Hook Dispatcher
# ──────────────────────────────────────────────

class HookDispatcher:
    """Plugin hook dispatch mekanizmi.

    Hook handler'larni priority bo'yicha tartiblaydi va chaqiradi.
    fail_safe=True (default) bo'lsa, hook xatoligi pipeline'ni buzmaydi.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._handlers: Dict[PluginHook, List[Tuple[str, int, Callable[[Dict[str, Any]], Any]]]] = {}

    def register(self, plugin_id: str, hook: PluginHook,
                 handler: Callable[[Dict[str, Any]], Any], priority: int = 100) -> None:
        """Hook handler registratsiya qiladi."""
        with self._lock:
            if hook not in self._handlers:
                self._handlers[hook] = []
            self._handlers[hook].append((plugin_id, priority, handler))
            self._handlers[hook].sort(key=lambda x: x[1])

    def unregister_plugin(self, plugin_id: str) -> None:
        """Berilgan plugin'ning barcha hook handler'larini o'chiradi."""
        with self._lock:
            for hook in self._handlers:
                self._handlers[hook] = [
                    (pid, pri, h) for pid, pri, h in self._handlers[hook]
                    if pid != plugin_id
                ]

    def dispatch(self, hook: PluginHook, context: Dict[str, Any],
                 fail_safe: bool = True) -> List[Any]:
        """Hook handler'larni chaqiradi va natijalarni qaytaradi.

        Args:
            hook: chaqiriladigan hook turi
            context: hook handler'larga beriladigan kontekst
            fail_safe: True bo'lsa, xatolik pipeline'ni buzmaydi
        """
        with self._lock:
            handlers = list(self._handlers.get(hook, []))

        results: List[Any] = []
        for plugin_id, _priority, handler in handlers:
            try:
                result = handler(context)
                results.append(result)
            except Exception as exc:
                logger.warning(
                    "Hook '%s' xatolik (plugin '%s'): %s",
                    hook.value, plugin_id, exc
                )
                if not fail_safe:
                    raise PluginError(
                        f"Plugin '{plugin_id}' hook '{hook.value}' xatolik: {exc}"
                    ) from exc
        return results

    def has_handlers(self, hook: PluginHook) -> bool:
        """Berilgan hook uchun handler'lar mavjudligini tekshiradi."""
        with self._lock:
            return bool(self._handlers.get(hook))

    def get_handler_count(self, hook: Optional[PluginHook] = None) -> int:
        """Hook handler'lar sonini qaytaradi."""
        with self._lock:
            if hook is not None:
                return len(self._handlers.get(hook, []))
            return sum(len(handlers) for handlers in self._handlers.values())


# ──────────────────────────────────────────────
# Plugin Discovery
# ──────────────────────────────────────────────

class PluginDiscovery:
    """Discovers plugins from filesystem by scanning for manifest files.

    Qo'llab-quvvatlanadigan manbalar:
    - local directory (manifest.yaml yoki manifest.json)
    - built-in plugins (kod ichida registratsiya qilingan)
    - explicit configuration

    YAML manifest uchun avval pyyaml kutubxonasi sinab ko'riladi,
    keyin built-in minimal parser ishlatiladi.
    """

    def scan(self, plugins_dir: str) -> List[Tuple[str, PluginManifest]]:
        """Returns list of (source_path, PluginManifest) tuples."""
        results: List[Tuple[str, PluginManifest]] = []
        abs_dir = os.path.abspath(plugins_dir)
        if not os.path.isdir(abs_dir):
            return results

        for entry in sorted(os.listdir(abs_dir)):
            entry_path = os.path.join(abs_dir, entry)
            if not os.path.isdir(entry_path):
                continue

            manifest = self._try_load_manifest(entry_path)
            if manifest is not None:
                results.append((entry_path, manifest))

        return results

    def scan_sources(self, sources: List[str]) -> List[Tuple[str, PluginManifest]]:
        """Bir nechta direktoriyalardan plugin'larni topadi (deterministik tartibda)."""
        results: List[Tuple[str, PluginManifest]] = []
        seen_ids: Set[str] = set()
        for source_dir in sources:
            for source_path, manifest in self.scan(source_dir):
                if manifest.plugin_id not in seen_ids:
                    seen_ids.add(manifest.plugin_id)
                    results.append((source_path, manifest))
        return results

    def _try_load_manifest(self, plugin_dir: str) -> Optional[PluginManifest]:
        """manifest.yaml va manifest.json ni sinab ko'radi."""
        yaml_path = os.path.join(plugin_dir, "manifest.yaml")
        json_path = os.path.join(plugin_dir, "manifest.json")

        if os.path.isfile(yaml_path):
            return self._parse_yaml_manifest(yaml_path)
        if os.path.isfile(json_path):
            return self._parse_json_manifest(json_path)
        return None

    def _parse_yaml_manifest(self, path: str) -> Optional[PluginManifest]:
        """YAML manifest'ni parsing qiladi (pyyaml yoki built-in parser)."""
        with open(path, "r", encoding="utf-8") as f:
            raw_text = f.read()

        data: Optional[Dict[str, Any]] = None
        try:
            import yaml  # type: ignore[import-untyped]
            data = yaml.safe_load(raw_text)
        except ImportError:
            data = parse_yaml_minimal(raw_text)
        except Exception as exc:
            logger.warning("YAML parsing xatolik '%s': %s", path, exc)
            return None

        if not isinstance(data, dict):
            return None
        return self._dict_to_manifest(data)

    def _parse_json_manifest(self, path: str) -> Optional[PluginManifest]:
        """JSON manifest'ni parsing qiladi."""
        with open(path, "r", encoding="utf-8") as f:
            raw_text = f.read()
        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            logger.warning("JSON parsing xatolik '%s': %s", path, exc)
            return None
        return self._dict_to_manifest(data)

    def _dict_to_manifest(self, data: Dict[str, Any]) -> Optional[PluginManifest]:
        """Lug'atni PluginManifest'ga aylantiradi."""
        plugin_id = data.get("plugin_id", "")
        name = data.get("name", "")
        version = data.get("version", "0.0.0")
        if not plugin_id or not name:
            return None

        capabilities = self._parse_enum_list(data.get("capabilities", []), PluginCapability)
        permissions = self._parse_enum_list(data.get("permissions", []), PluginPermission)
        hooks = self._parse_enum_list(data.get("hooks", []), PluginHook)

        deps: List[PluginDependency] = []
        for d in data.get("dependencies", []):
            if isinstance(d, dict):
                deps.append(PluginDependency(
                    plugin_id=d.get("plugin_id", ""),
                    min_version=d.get("min_version", "0.0.0"),
                    max_version=d.get("max_version", ""),
                    is_optional=d.get("is_optional", False),
                ))

        sandbox_str = str(data.get("sandbox_level", "BASIC"))
        sandbox = SandboxLevel(sandbox_str) if sandbox_str in SandboxLevel._value2member_map_ else SandboxLevel.BASIC

        config_raw = data.get("config", {})
        config = config_raw if isinstance(config_raw, dict) else {}

        return PluginManifest(
            plugin_id=plugin_id,
            name=name,
            version=version,
            description=str(data.get("description", "")),
            author=str(data.get("author", "")),
            capabilities=capabilities,
            permissions=permissions,
            hooks=hooks,
            dependencies=deps,
            sandbox_level=sandbox,
            priority=int(data.get("priority", 100)),
            license=str(data.get("license", "")),
            aegis_compatibility=str(data.get("aegis_compatibility", ">=2.0.0")),
            python_compatibility=str(data.get("python_compatibility", ">=3.12")),
            entry_point=str(data.get("entry_point", "plugin.py")),
            config=config,
            publisher=str(data.get("publisher", "")),
            repository=str(data.get("repository", "")),
            homepage=str(data.get("homepage", "")),
            checksum=str(data.get("checksum", "")),
            signature=str(data.get("signature", "")),
            namespace=str(data.get("namespace", "community")),
        )

    @staticmethod
    def _parse_enum_list(raw_list: Any, enum_cls: type) -> List[Any]:
        """Enum qiymatlar ro'yxatini parsing qiladi."""
        if not isinstance(raw_list, list):
            return []
        result = []
        member_map = getattr(enum_cls, "_value2member_map_", {})
        for item in raw_list:
            s = str(item)
            if s in member_map:
                result.append(enum_cls(s))
        return result


# ──────────────────────────────────────────────
# Plugin Registry
# ──────────────────────────────────────────────

class PluginRegistry:
    """Central registry of all known plugin metadata and instances."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._metadata: Dict[str, PluginMetadata] = {}
        self._instances: Dict[str, PluginInterface] = {}

    def register(self, metadata: PluginMetadata, instance: Optional[PluginInterface] = None) -> None:
        with self._lock:
            self._metadata[metadata.manifest.plugin_id] = metadata
            if instance:
                self._instances[metadata.manifest.plugin_id] = instance

    def get_metadata(self, plugin_id: str) -> Optional[PluginMetadata]:
        with self._lock:
            return self._metadata.get(plugin_id)

    def get_instance(self, plugin_id: str) -> Optional[PluginInterface]:
        with self._lock:
            return self._instances.get(plugin_id)

    def set_instance(self, plugin_id: str, instance: PluginInterface) -> None:
        with self._lock:
            self._instances[plugin_id] = instance

    def remove(self, plugin_id: str) -> None:
        with self._lock:
            self._metadata.pop(plugin_id, None)
            self._instances.pop(plugin_id, None)

    def list_all(self) -> List[PluginMetadata]:
        with self._lock:
            return list(self._metadata.values())

    def list_active(self) -> List[PluginMetadata]:
        with self._lock:
            return [m for m in self._metadata.values() if m.state == PluginState.ACTIVE]

    def get_manifests(self) -> Dict[str, PluginManifest]:
        with self._lock:
            return {pid: meta.manifest for pid, meta in self._metadata.items()}


# ──────────────────────────────────────────────
# Plugin Metrics Collector
# ──────────────────────────────────────────────

class PluginMetricsCollector:
    """Aggregates and reports plugin performance metrics."""

    def __init__(self, registry: PluginRegistry) -> None:
        self._registry = registry

    def record_call(self, plugin_id: str, duration_ms: float, is_error: bool = False) -> None:
        meta = self._registry.get_metadata(plugin_id)
        if meta:
            meta.metrics.call_count += 1
            meta.metrics.total_execution_time_ms += duration_ms
            if is_error:
                meta.metrics.error_count += 1

    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        result: Dict[str, Dict[str, Any]] = {}
        for meta in self._registry.list_all():
            m = meta.metrics
            result[meta.manifest.plugin_id] = {
                "state": meta.state.value,
                "enabled": meta.enabled,
                "load_time_ms": m.load_time_ms,
                "activate_time_ms": m.activate_time_ms,
                "call_count": m.call_count,
                "error_count": m.error_count,
                "avg_latency_ms": m.avg_latency_ms,
                "total_execution_time_ms": m.total_execution_time_ms,
            }
        return result


# ──────────────────────────────────────────────
# Plugin Test Harness
# ──────────────────────────────────────────────

class PluginTestHarness:
    """Provides a mock environment for testing plugins in isolation."""

    def __init__(self) -> None:
        self.events: List[PluginEvent] = []
        self.calls: List[str] = []

    def create_test_context(self, plugin_id: str = "test_plugin",
                            config: Optional[Dict[str, Any]] = None) -> PluginContext:
        return PluginContext(
            plugin_id=plugin_id,
            config=config or {"test_mode": True},
            token=CapabilityToken(plugin_id=plugin_id, granted_permissions=set(PluginPermission)),
            storage_dir="/tmp/aegis_test_plugins"
        )

    def record_event(self, event: PluginEvent) -> None:
        self.events.append(event)

    def record_call(self, method_name: str) -> None:
        self.calls.append(method_name)


# ──────────────────────────────────────────────
# Manifest Validator
# ──────────────────────────────────────────────

class ManifestValidator:
    """Production-grade manifest validation with detailed error reporting."""

    AEGIS_VERSION: ClassVar[str] = "2.0.0"

    def validate(self, manifest: PluginManifest) -> List[str]:
        """Manifest'ni tekshiradi va xatoliklar ro'yxatini qaytaradi."""
        errors: List[str] = []

        if not manifest.plugin_id:
            errors.append("plugin_id bo'sh bo'lishi mumkin emas")
        elif not re.match(r"^[a-zA-Z][a-zA-Z0-9_.]*$", manifest.plugin_id):
            errors.append(
                f"plugin_id noto'g'ri format: '{manifest.plugin_id}'. "
                "Faqat harflar, raqamlar, nuqta va pastki chiziq ruxsat etilgan."
            )

        if not manifest.name:
            errors.append("name bo'sh bo'lishi mumkin emas")

        if not manifest.version:
            errors.append("version bo'sh bo'lishi mumkin emas")
        else:
            try:
                parse_semver(manifest.version)
            except ValueError:
                errors.append(f"version noto'g'ri SemVer format: '{manifest.version}'")

        if manifest.aegis_compatibility:
            if not check_version_constraint(self.AEGIS_VERSION, manifest.aegis_compatibility):
                errors.append(
                    f"Aegis compatibility '{manifest.aegis_compatibility}' "
                    f"joriy versiya ({self.AEGIS_VERSION}) bilan mos kelmaydi"
                )

        for dep in manifest.dependencies:
            if not dep.plugin_id:
                errors.append("dependency.plugin_id bo'sh bo'lishi mumkin emas")
            if dep.min_version:
                try:
                    parse_semver(dep.min_version)
                except ValueError:
                    errors.append(f"dependency '{dep.plugin_id}' min_version noto'g'ri: '{dep.min_version}'")
            if dep.max_version:
                try:
                    parse_semver(dep.max_version)
                except ValueError:
                    errors.append(f"dependency '{dep.plugin_id}' max_version noto'g'ri: '{dep.max_version}'")

        return errors


# ──────────────────────────────────────────────
# Plugin Manager (Facade)
# ──────────────────────────────────────────────

class PluginManager:
    """
    Top-level facade orchestrating the entire plugin subsystem.
    Thread-safe. Production-ready.

    Integratsiya nuqtalari:
    - RuntimeOrchestrator: pipeline stage'lar va hook'lar
    - QualityPipeline: validator registratsiya
    - ReasoningPipeline: strategy registratsiya
    - KnowledgeLoader: knowledge source registratsiya
    - SessionManager: session hook'lar
    - ModelGateway: provider registratsiya
    - PromptComposer: prompt contribution'lar
    """

    def __init__(self, plugins_dir: str) -> None:
        self.plugins_dir = os.path.abspath(plugins_dir)
        os.makedirs(self.plugins_dir, exist_ok=True)

        self._lock = threading.RLock()
        self.registry = PluginRegistry()
        self.event_bus = PluginEventBus()
        self.security = PluginSecurityManager()
        self.lifecycle = PluginLifecycleManager()
        self.dep_resolver = PluginDependencyResolver()
        self.discovery = PluginDiscovery()
        self.metrics_collector = PluginMetricsCollector(self.registry)
        self.capability_registry = CapabilityRegistry()
        self.hook_dispatcher = HookDispatcher()
        self.manifest_validator = ManifestValidator()

        from runtime.src.sandbox import SandboxManager, SandboxPolicy, SandboxLimits, SandboxRequest, SandboxError, SandboxTimeoutError, SandboxCrashedError
        self.sandbox_manager = SandboxManager()

        self._prompt_contributions: List[PluginPromptContribution] = []


    # ── Discovery ──

    def discover_plugins(self) -> List[PluginManifest]:
        """Scans the plugins directory and registers discovered manifests."""
        with self._lock:
            found = self.discovery.scan(self.plugins_dir)
            manifests: List[PluginManifest] = []
            for source_path, manifest in found:
                meta = PluginMetadata(
                    manifest=manifest,
                    state=PluginState.DISCOVERED,
                    source_path=source_path
                )
                self.registry.register(meta)
                manifests.append(manifest)

                self.event_bus.publish(PluginEvent(
                    event_type="PLUGIN_DISCOVERED",
                    source_plugin_id=manifest.plugin_id,
                    payload={"path": source_path}
                ))

            return manifests

    def discover_from_sources(self, sources: List[str]) -> List[PluginManifest]:
        """Bir nechta manbalardan plugin'larni topadi."""
        with self._lock:
            found = self.discovery.scan_sources(sources)
            manifests: List[PluginManifest] = []
            for source_path, manifest in found:
                if self.registry.get_metadata(manifest.plugin_id) is None:
                    meta = PluginMetadata(
                        manifest=manifest,
                        state=PluginState.DISCOVERED,
                        source_path=source_path
                    )
                    self.registry.register(meta)
                    manifests.append(manifest)
            return manifests

    def register_builtin(self, instance: PluginInterface) -> PluginManifest:
        """Built-in plugin'ni bevosita registratsiya qiladi (discovery kerak emas)."""
        with self._lock:
            manifest = instance.get_manifest()
            meta = PluginMetadata(
                manifest=manifest,
                state=PluginState.DISCOVERED,
                source_path="<builtin>"
            )
            self.registry.register(meta, instance)

            self.event_bus.publish(PluginEvent(
                event_type="PLUGIN_DISCOVERED",
                source_plugin_id=manifest.plugin_id,
                payload={"source": "builtin"}
            ))
            return manifest

    # ── Loading ──

    def load_plugin(self, plugin_id: str, instance: PluginInterface) -> bool:
        """Loads a plugin instance and transitions to LOADED state."""
        with self._lock:
            meta = self.registry.get_metadata(plugin_id)
            if not meta:
                raise PluginNotFoundError(f"Plugin '{plugin_id}' not found in registry")

            start = time.time()
            self.lifecycle.transition(meta, PluginState.LOADED)
            self.registry.set_instance(plugin_id, instance)
            meta.loaded_at_utc = time.time()
            meta.metrics.load_time_ms = (time.time() - start) * 1000.0

            self.event_bus.publish(PluginEvent(
                event_type="PLUGIN_LOADED",
                source_plugin_id=plugin_id
            ))
            return True

    # ── Validation ──

    def validate_plugin(self, plugin_id: str) -> bool:
        """Validates manifest schema integrity."""
        with self._lock:
            meta = self.registry.get_metadata(plugin_id)
            if not meta:
                raise PluginNotFoundError(f"Plugin '{plugin_id}' not found")

            errors = self.manifest_validator.validate(meta.manifest)
            if errors:
                error_msg = "; ".join(errors)
                raise PluginManifestError(
                    f"Plugin '{plugin_id}' manifest validatsiya xatoliklari: {error_msg}"
                )

            self.lifecycle.transition(meta, PluginState.VALIDATED)
            return True

    # ── Dependency Resolution ──

    def resolve_dependencies(self) -> List[str]:
        """Resolves all dependency graphs and returns deterministic load order."""
        with self._lock:
            manifests = self.registry.get_manifests()
            self.dep_resolver.validate_versions(manifests)
            order = self.dep_resolver.resolve(manifests)

            for pid in order:
                meta = self.registry.get_metadata(pid)
                if meta and meta.state == PluginState.VALIDATED:
                    self.lifecycle.transition(meta, PluginState.RESOLVED)

            return order

    # ── Activation ──

    def activate_plugin(self, plugin_id: str) -> bool:
        """Initializes and activates a plugin with security tokens."""
        with self._lock:
            meta = self.registry.get_metadata(plugin_id)
            if not meta:
                raise PluginNotFoundError(f"Plugin '{plugin_id}' not found")

            if not meta.enabled:
                logger.info("Plugin '%s' o'chirilgan (disabled), aktivatsiya o'tkazib yuborildi", plugin_id)
                return False

            instance = self.registry.get_instance(plugin_id)
            if not instance:
                raise PluginError(f"Plugin '{plugin_id}' has no loaded instance")

            # Issue capability token (default DENY — faqat manifest'dagi ruxsatlar)
            token = self.security.issue_token(plugin_id, meta.manifest.permissions)
            ctx = PluginContext(
                plugin_id=plugin_id,
                config=dict(meta.manifest.config),
                token=token,
                resources=PluginResources(),
                storage_dir=os.path.join(self.plugins_dir, plugin_id)
            )

            # Initialize
            if meta.state == PluginState.RESOLVED:
                init_ok = instance.on_initialize(ctx)
                if not init_ok:
                    raise PluginError(f"Plugin '{plugin_id}' initialization failed")
                self.lifecycle.transition(meta, PluginState.INITIALIZED)

            # Activate
            activate_start = time.time()
            activate_ok = instance.on_activate(ctx)
            if not activate_ok:
                raise PluginError(f"Plugin '{plugin_id}' activation failed")

            meta.metrics.activate_time_ms = (time.time() - activate_start) * 1000.0
            self.lifecycle.transition(meta, PluginState.ACTIVE)

            # Register capabilities
            self._register_plugin_capabilities(plugin_id, instance)

            # Register hooks
            self._register_plugin_hooks(plugin_id, instance)

            # Register prompt contributions
            self._register_prompt_contributions(plugin_id, instance)

            self.event_bus.publish(PluginEvent(
                event_type="PLUGIN_ACTIVATED",
                source_plugin_id=plugin_id
            ))
            return True

    def _register_plugin_capabilities(self, plugin_id: str, instance: PluginInterface) -> None:
        """Plugin capability'larini CapabilityRegistry'ga registratsiya qiladi."""
        if not hasattr(instance, "get_capabilities"):
            return
        capabilities = instance.get_capabilities()  # type: ignore[union-attr]
        for cap_type, handlers in capabilities.items():
            for idx, handler in enumerate(handlers):
                entry = CapabilityEntry(
                    capability_type=cap_type,
                    name=f"{plugin_id}.{cap_type}.{idx}",
                    plugin_id=plugin_id,
                    handler=handler,
                    priority=self.registry.get_metadata(plugin_id).manifest.priority if self.registry.get_metadata(plugin_id) else 100,
                )
                try:
                    self.capability_registry.register(entry)
                except PluginCapabilityError as exc:
                    logger.warning("Capability registratsiya xatolik: %s", exc)

    def _register_plugin_hooks(self, plugin_id: str, instance: PluginInterface) -> None:
        """Plugin hook handler'larini HookDispatcher'ga registratsiya qiladi."""
        if not hasattr(instance, "get_hook_handlers"):
            return
        hooks = instance.get_hook_handlers()  # type: ignore[union-attr]
        meta = self.registry.get_metadata(plugin_id)
        priority = meta.manifest.priority if meta else 100
        for hook, handler in hooks.items():
            self.hook_dispatcher.register(plugin_id, hook, handler, priority)

    def _register_prompt_contributions(self, plugin_id: str, instance: PluginInterface) -> None:
        """Plugin prompt contribution'larini registratsiya qiladi."""
        if not hasattr(instance, "get_prompt_contributions"):
            return
        contributions = instance.get_prompt_contributions()  # type: ignore[union-attr]
        for contrib in contributions:
            self._prompt_contributions.append(contrib)
        self._prompt_contributions.sort(key=lambda c: c.priority)

    # ── Execution ──

    def execute_plugin(self, plugin_id: str, data: Dict[str, Any]) -> Any:
        """Executes a plugin with metrics tracking and timeout protection."""
        with self._lock:
            meta = self.registry.get_metadata(plugin_id)
            if not meta or meta.state != PluginState.ACTIVE:
                raise PluginLifecycleError(f"Plugin '{plugin_id}' is not active")

            instance = self.registry.get_instance(plugin_id)
            if not instance:
                raise PluginError(f"Plugin '{plugin_id}' instance not found")

            token = self.security.get_token(plugin_id)
            ctx = PluginContext(
                plugin_id=plugin_id,
                config=dict(meta.manifest.config),
                token=token,
            )

            start = time.time()
            is_error = False
            try:
                # Check if sandbox process worker is active for this plugin
                if self.sandbox_manager.is_worker_alive(plugin_id):
                    from runtime.src.sandbox import SandboxRequest, SandboxTimeoutError, SandboxCrashedError
                    req = SandboxRequest(
                        command="EXECUTE",
                        payload=data,
                        plugin_id=plugin_id,
                        capability_token=token.plugin_id if token else None
                    )
                    resp = self.sandbox_manager.send_request(plugin_id, req)
                    if not resp.success:
                        raise PluginError(f"Sandbox execution error: {resp.error}")
                    result = resp.result
                else:
                    result = instance.on_execute(ctx, data)
            except Exception as e:
                from runtime.src.sandbox import SandboxTimeoutError, SandboxCrashedError
                if isinstance(e, (SandboxTimeoutError, SandboxCrashedError)):
                    meta.state = PluginState.FAILED
                is_error = True
                self.event_bus.publish(PluginEvent(
                    event_type="PLUGIN_ERROR",
                    source_plugin_id=plugin_id,
                    payload={"error": str(e)}
                ))
                raise

            finally:
                duration = (time.time() - start) * 1000.0
                self.metrics_collector.record_call(plugin_id, duration, is_error)

            return result


    # ── Suspend / Resume ──

    def suspend_plugin(self, plugin_id: str) -> bool:
        """Suspends an active plugin."""
        with self._lock:
            meta = self.registry.get_metadata(plugin_id)
            if not meta:
                raise PluginNotFoundError(f"Plugin '{plugin_id}' not found")

            instance = self.registry.get_instance(plugin_id)
            ctx = PluginContext(plugin_id=plugin_id)
            if instance:
                instance.on_suspend(ctx)

            self.lifecycle.transition(meta, PluginState.SUSPENDED)
            return True

    def resume_plugin(self, plugin_id: str) -> bool:
        """Resumes a suspended plugin."""
        with self._lock:
            meta = self.registry.get_metadata(plugin_id)
            if not meta:
                raise PluginNotFoundError(f"Plugin '{plugin_id}' not found")

            instance = self.registry.get_instance(plugin_id)
            ctx = PluginContext(plugin_id=plugin_id)
            if instance:
                instance.on_resume(ctx)

            self.lifecycle.transition(meta, PluginState.ACTIVE)

            self.event_bus.publish(PluginEvent(
                event_type="PLUGIN_RESUMED",
                source_plugin_id=plugin_id
            ))
            return True

    # ── Unload / Destroy ──

    def unload_plugin(self, plugin_id: str) -> bool:
        """Unloads a plugin and releases resources."""
        with self._lock:
            meta = self.registry.get_metadata(plugin_id)
            if not meta:
                raise PluginNotFoundError(f"Plugin '{plugin_id}' not found")

            instance = self.registry.get_instance(plugin_id)
            ctx = PluginContext(plugin_id=plugin_id)
            if instance:
                instance.on_unload(ctx)

            self.lifecycle.transition(meta, PluginState.UNLOADED)
            self.security.revoke_token(plugin_id)
            self.capability_registry.unregister_plugin(plugin_id)
            self.hook_dispatcher.unregister_plugin(plugin_id)
            self.sandbox_manager.terminate_worker(plugin_id)
            self._prompt_contributions = [
                c for c in self._prompt_contributions if c.plugin_id != plugin_id
            ]


            self.event_bus.publish(PluginEvent(
                event_type="PLUGIN_UNLOADED",
                source_plugin_id=plugin_id
            ))
            return True

    def destroy_plugin(self, plugin_id: str) -> bool:
        """Destroys a plugin and removes all references."""
        with self._lock:
            meta = self.registry.get_metadata(plugin_id)
            if not meta:
                raise PluginNotFoundError(f"Plugin '{plugin_id}' not found")

            if meta.state in (PluginState.ACTIVE, PluginState.SUSPENDED):
                self.unload_plugin(plugin_id)
                meta = self.registry.get_metadata(plugin_id)

            instance = self.registry.get_instance(plugin_id)
            ctx = PluginContext(plugin_id=plugin_id)
            if instance:
                instance.on_destroy(ctx)

            if meta:
                self.lifecycle.transition(meta, PluginState.DESTROYED)
            self.security.revoke_token(plugin_id)
            self.registry.remove(plugin_id)

            self.event_bus.publish(PluginEvent(
                event_type="PLUGIN_DESTROYED",
                source_plugin_id=plugin_id
            ))
            return True

    # ── Hot Reload (transactional) ──

    def reload_plugin(self, plugin_id: str, new_instance: PluginInterface) -> bool:
        """Hot-reloads a plugin using a strict transactional atomic swap.

        TRANSACTIONAL INVARIANT:
        1. Validate manifest & dependencies of new_instance FIRST.
        2. Initialize & Activate new_instance in a staging context BEFORE touching old_instance.
        3. If staging fails: destroy new_instance, old_instance remains 100% ACTIVE and untouched.
        4. Atomic swap under lock: suspend old → swap registry instance → swap capabilities/hooks → unload old.
        """
        with self._lock:
            meta = self.registry.get_metadata(plugin_id)
            if not meta or meta.state != PluginState.ACTIVE:
                raise PluginLifecycleError(f"Plugin '{plugin_id}' must be ACTIVE for hot-reload")

            old_instance = self.registry.get_instance(plugin_id)
            if not old_instance:
                raise PluginError(f"Plugin '{plugin_id}' has no loaded instance")

            old_ctx = PluginContext(plugin_id=plugin_id, config=dict(meta.manifest.config))

            # Step 1: Validate new_instance manifest
            new_manifest = new_instance.get_manifest()
            validation_errors = self.manifest_validator.validate(new_manifest)
            if validation_errors:
                raise PluginManifestError(
                    f"Yangi plugin instance validatsiya xatoliklari: {'; '.join(validation_errors)}"
                )

            # Step 2: Validate dependency compatibility
            all_manifests = self.registry.get_manifests()
            all_manifests[plugin_id] = new_manifest
            try:
                self.dep_resolver.validate_versions(all_manifests)
                self.dep_resolver.resolve(all_manifests)
            except Exception as dep_err:
                raise PluginDependencyError(
                    f"Yangi plugin dependency tekshiruvida xatolik: {dep_err}"
                ) from dep_err

            # Step 3: Staging Initialize & Activate BEFORE touching old_instance
            token = self.security.issue_token(plugin_id, new_manifest.permissions)
            new_ctx = PluginContext(plugin_id=plugin_id, config=dict(new_manifest.config), token=token)

            try:
                init_ok = new_instance.on_initialize(new_ctx)
                if not init_ok:
                    raise PluginError(f"Yangi plugin '{plugin_id}' on_initialize muvaffaqiyatsiz")

                activate_ok = new_instance.on_activate(new_ctx)
                if not activate_ok:
                    raise PluginError(f"Yangi plugin '{plugin_id}' on_activate muvaffaqiyatsiz")

            except Exception as staging_exc:
                # Staging failed: clean up new_instance, old_instance remains 100% ACTIVE
                try:
                    new_instance.on_unload(new_ctx)
                    new_instance.on_destroy(new_ctx)
                except Exception:
                    pass

                self.event_bus.publish(PluginEvent(
                    event_type="PLUGIN_RELOAD_FAILED",
                    source_plugin_id=plugin_id,
                    payload={"error": str(staging_exc), "rollback": "PRESERVED_UNCHANGED"}
                ))

                raise PluginError(
                    f"Hot-reload muvaffaqiyatsiz (staging variantida), eski plugin buzilmagan holda qoldi: {staging_exc}"
                ) from staging_exc

            # Step 4: Atomic Swap under lock (new_instance is fully initialized and activated)
            old_prompt_contributions = [
                c for c in self._prompt_contributions if c.plugin_id == plugin_id
            ]

            try:
                # Suspend old
                try:
                    old_instance.on_suspend(old_ctx)
                except Exception as exc:
                    logger.warning("Old plugin '%s' on_suspend xatolik (davom etiladi): %s", plugin_id, exc)

                # Unregister old capabilities & hooks
                self.capability_registry.unregister_plugin(plugin_id)
                self.hook_dispatcher.unregister_plugin(plugin_id)
                self._prompt_contributions = [
                    c for c in self._prompt_contributions if c.plugin_id != plugin_id
                ]

                # Swap registry instance
                meta.manifest = new_manifest
                self.registry.set_instance(plugin_id, new_instance)

                # Register new capabilities & hooks
                self._register_plugin_capabilities(plugin_id, new_instance)
                self._register_plugin_hooks(plugin_id, new_instance)
                self._register_prompt_contributions(plugin_id, new_instance)

                # Unload old instance
                try:
                    old_instance.on_unload(old_ctx)
                except Exception as exc:
                    logger.warning("Old plugin '%s' on_unload xatolik: %s", plugin_id, exc)

            except Exception as swap_exc:
                # Swap failed: rollback to old_instance
                logger.error("Hot-reload swap failed for '%s': %s. Rolling back.", plugin_id, swap_exc)
                self.registry.set_instance(plugin_id, old_instance)
                self._register_plugin_capabilities(plugin_id, old_instance)
                self._register_plugin_hooks(plugin_id, old_instance)
                self._prompt_contributions.extend(old_prompt_contributions)
                self._prompt_contributions.sort(key=lambda c: c.priority)
                try:
                    old_instance.on_resume(old_ctx)
                except Exception:
                    pass
                raise PluginError(f"Hot-reload swap failed, rolled back to old instance: {swap_exc}") from swap_exc

            # Success
            self.lifecycle.transition(meta, PluginState.ACTIVE)
            self.event_bus.publish(PluginEvent(
                event_type="PLUGIN_RELOADED",
                source_plugin_id=plugin_id
            ))
            return True

    # ── Enable / Disable ──

    def enable_plugin(self, plugin_id: str) -> bool:
        """Plugin'ni yoqadi."""
        with self._lock:
            meta = self.registry.get_metadata(plugin_id)
            if not meta:
                raise PluginNotFoundError(f"Plugin '{plugin_id}' not found")
            meta.enabled = True
            return True

    def disable_plugin(self, plugin_id: str) -> bool:
        """Plugin'ni o'chiradi. Agar ACTIVE bo'lsa, avval suspend qiladi."""
        with self._lock:
            meta = self.registry.get_metadata(plugin_id)
            if not meta:
                raise PluginNotFoundError(f"Plugin '{plugin_id}' not found")
            if meta.state == PluginState.ACTIVE:
                self.suspend_plugin(plugin_id)
            meta.enabled = False
            return True

    # ── Full Pipeline: Discover → Load → Validate → Resolve → Activate ──

    def activate_all(self, plugin_instances: Optional[Dict[str, PluginInterface]] = None) -> List[str]:
        """Barcha topilgan plugin'larni to'liq lifecycle orqali faollashtiradi.

        Args:
            plugin_instances: plugin_id → instance xaritasi (ixtiyoriy).
                Agar berilmasa, faqat built-in plugin'lar ishlatiladi.

        Returns:
            Faollashtirilgan plugin ID'lar ro'yxati.
        """
        with self._lock:
            instances = plugin_instances or {}

            # Load
            for pid, instance in instances.items():
                meta = self.registry.get_metadata(pid)
                if meta and meta.state == PluginState.DISCOVERED:
                    self.load_plugin(pid, instance)

            # Validate
            for meta in self.registry.list_all():
                if meta.state == PluginState.LOADED:
                    try:
                        self.validate_plugin(meta.manifest.plugin_id)
                    except PluginError as exc:
                        logger.warning("Plugin validatsiya xatolik: %s", exc)

            # Resolve dependencies
            try:
                order = self.resolve_dependencies()
            except PluginDependencyError as exc:
                logger.error("Dependency resolution xatolik: %s", exc)
                return []

            # Activate in dependency order
            activated: List[str] = []
            for pid in order:
                meta = self.registry.get_metadata(pid)
                if meta and meta.state == PluginState.RESOLVED:
                    try:
                        if self.activate_plugin(pid):
                            activated.append(pid)
                    except PluginError as exc:
                        logger.warning("Plugin aktivatsiya xatolik '%s': %s", pid, exc)

            return activated

    # ── Query ──

    def get_plugin(self, plugin_id: str) -> Optional[PluginInterface]:
        """Returns a loaded plugin instance."""
        return self.registry.get_instance(plugin_id)

    def list_plugins(self) -> List[PluginMetadata]:
        """Returns all registered plugin metadata."""
        return self.registry.list_all()

    def get_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Returns aggregated metrics for all plugins."""
        return self.metrics_collector.get_all_metrics()

    def get_prompt_contributions(self) -> List[PluginPromptContribution]:
        """Barcha plugin prompt contribution'larini qaytaradi (priority bo'yicha tartiblangan)."""
        with self._lock:
            return list(self._prompt_contributions)

    def get_plugin_info(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """Plugin haqida batafsil ma'lumot qaytaradi."""
        with self._lock:
            meta = self.registry.get_metadata(plugin_id)
            if not meta:
                return None
            return {
                "manifest": meta.manifest.to_dict(),
                "state": meta.state.value,
                "enabled": meta.enabled,
                "source_path": meta.source_path,
                "loaded_at_utc": meta.loaded_at_utc,
                "metrics": {
                    "load_time_ms": meta.metrics.load_time_ms,
                    "activate_time_ms": meta.metrics.activate_time_ms,
                    "call_count": meta.metrics.call_count,
                    "error_count": meta.metrics.error_count,
                    "avg_latency_ms": meta.metrics.avg_latency_ms,
                },
                "capabilities": self.capability_registry.resolve(
                    "validators", plugin_id=plugin_id
                ) + self.capability_registry.resolve(
                    "reasoners", plugin_id=plugin_id
                ),
                "hook_count": self.hook_dispatcher.get_handler_count(),
            }

    def dispatch_hook(self, hook: PluginHook, context: Dict[str, Any],
                      fail_safe: bool = True) -> List[Any]:
        """Hook dispatch'ni PluginManager orqali chaqiradi."""
        return self.hook_dispatcher.dispatch(hook, context, fail_safe)
