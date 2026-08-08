"""
Aegis AI Operating System — Production Observability, Security Audit & Telemetry Subsystem
Provides structured JSON event logging, correlation tracking, secret redaction, audit logging,
log rotation, latency percentile metrics (p50/p95/p99), trace spans, and fail-safe execution.
Python 3.12+ compliant. Zero external dependencies.
"""

import sys
import os
import re
import json
import time
import hashlib
import logging
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Set, Union

logger = logging.getLogger("AegisObservability")


# ──────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────

class EventLevel(Enum):
    """Severity levels for observability events."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class EventCategory(Enum):
    """Categorized domain areas for events."""
    PIPELINE = "PIPELINE"
    SESSION = "SESSION"
    REASONING = "REASONING"
    KNOWLEDGE = "KNOWLEDGE"
    TRUTH = "TRUTH"
    QUALITY = "QUALITY"
    PLUGIN = "PLUGIN"
    SANDBOX = "SANDBOX"
    MODEL = "MODEL"
    SECURITY = "SECURITY"
    SYSTEM = "SYSTEM"
    CLI = "CLI"
    ERROR = "ERROR"


class EventType(Enum):
    """Anonymized and structured event types across Aegis subsystems."""
    REQUEST_STARTED = "REQUEST_STARTED"
    REQUEST_COMPLETED = "REQUEST_COMPLETED"
    REQUEST_FAILED = "REQUEST_FAILED"
    STAGE_STARTED = "STAGE_STARTED"
    STAGE_COMPLETED = "STAGE_COMPLETED"
    STAGE_FAILED = "STAGE_FAILED"
    SESSION_CREATED = "SESSION_CREATED"
    SESSION_STARTED = "SESSION_STARTED"
    SESSION_RESUMED = "SESSION_RESUMED"
    SESSION_CHECKPOINT = "SESSION_CHECKPOINT"
    SESSION_RECOVERED = "SESSION_RECOVERED"

    MODEL_REQUEST = "MODEL_REQUEST"
    MODEL_RESPONSE = "MODEL_RESPONSE"
    MODEL_RETRY = "MODEL_RETRY"
    MODEL_FAILURE = "MODEL_FAILURE"
    PLUGIN_LOADED = "PLUGIN_LOADED"
    PLUGIN_FAILED = "PLUGIN_FAILED"
    SANDBOX_VIOLATION = "SANDBOX_VIOLATION"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    PATH_TRAVERSAL_BLOCKED = "PATH_TRAVERSAL_BLOCKED"
    SECRET_ACCESS_DENIED = "SECRET_ACCESS_DENIED"
    SECRET_LEAK_BLOCKED = "SECRET_LEAK_BLOCKED"
    SECURITY_PERMISSION_DENIED = "SECURITY_PERMISSION_DENIED"
    SECURITY_SECRET_REDACTED = "SECURITY_SECRET_REDACTED"
    SECURITY_PATH_BLOCKED = "SECURITY_PATH_BLOCKED"
    SECURITY_POLICY_VIOLATION = "SECURITY_POLICY_VIOLATION"
    QUALITY_FAILED = "QUALITY_FAILED"
    AUTO_REPAIR = "AUTO_REPAIR"
    SYSTEM_ERROR = "SYSTEM_ERROR"
    ERROR_UNHANDLED = "ERROR_UNHANDLED"
    ERROR_RECOVERED = "ERROR_RECOVERED"


# ──────────────────────────────────────────────
# Data Structures
# ──────────────────────────────────────────────

@dataclass
class ObservabilityEvent:
    """Structured JSON event representation across Aegis OS."""
    event_id: str
    correlation_id: str
    request_id: str
    session_id: str
    trace_id: str
    span_id: str
    parent_span_id: str
    level: str
    category: str
    event_type: str
    component: str
    operation: str
    duration_ms: float
    success: bool
    message: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%S.", time.gmtime()) + f"{int(time.time() * 1000) % 1000:03d}Z")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "event_id": self.event_id,
            "correlation_id": self.correlation_id,
            "request_id": self.request_id,
            "session_id": self.session_id,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "level": self.level,
            "category": self.category,
            "event_type": self.event_type,
            "component": self.component,
            "operation": self.operation,
            "duration_ms": self.duration_ms,
            "success": self.success,
            "message": self.message,
            "metadata": self.metadata
        }


class CorrelationContext:
    """Thread-local context tracking request correlation IDs, session IDs, and trace spans."""
    _thread_local = threading.local()

    @classmethod
    def get_correlation_id(cls) -> str:
        return getattr(cls._thread_local, "correlation_id", f"CORR_{time.time_ns()}")

    @classmethod
    def get_session_id(cls) -> str:
        return getattr(cls._thread_local, "session_id", "SESS_GLOBAL")

    @classmethod
    def get_request_id(cls) -> str:
        return getattr(cls._thread_local, "request_id", f"REQ_{int(time.time() * 1000)}")

    @classmethod
    def get_trace_id(cls) -> str:
        return getattr(cls._thread_local, "trace_id", f"TRC_{time.time_ns()}")

    @classmethod
    def get_current_span_id(cls) -> str:
        spans = getattr(cls._thread_local, "spans", [])
        return spans[-1] if spans else "SPN_ROOT"

    @classmethod
    def get_parent_span_id(cls) -> str:
        spans = getattr(cls._thread_local, "spans", [])
        return spans[-2] if len(spans) >= 2 else "SPN_ROOT"

    @classmethod
    def set_context(cls, correlation_id: Optional[str] = None, session_id: Optional[str] = None, request_id: Optional[str] = None, trace_id: Optional[str] = None) -> None:
        cls._thread_local.correlation_id = correlation_id or f"CORR_{time.time_ns()}"
        cls._thread_local.session_id = session_id or "SESS_GLOBAL"
        cls._thread_local.request_id = request_id or f"REQ_{int(time.time() * 1000)}"
        cls._thread_local.trace_id = trace_id or f"TRC_{time.time_ns()}"
        if not hasattr(cls._thread_local, "spans"):
            cls._thread_local.spans = []

    @classmethod
    def push_span(cls, span_id: str) -> None:
        if not hasattr(cls._thread_local, "spans"):
            cls._thread_local.spans = []
        cls._thread_local.spans.append(span_id)

    @classmethod
    def pop_span(cls) -> Optional[str]:
        spans = getattr(cls._thread_local, "spans", [])
        if spans:
            return spans.pop()
        return None

    @classmethod
    def clear(cls) -> None:
        cls._thread_local.correlation_id = f"CORR_{time.time_ns()}"
        cls._thread_local.session_id = "SESS_GLOBAL"
        cls._thread_local.request_id = f"REQ_{int(time.time() * 1000)}"
        cls._thread_local.trace_id = f"TRC_{time.time_ns()}"
        cls._thread_local.spans = []


# ──────────────────────────────────────────────
# Secret Redaction Engine
# ──────────────────────────────────────────────

class EventRedactor:
    """Centralized secret masking engine preventing API keys, tokens, and credentials from leaking."""

    SECRET_PATTERNS: List[re.Pattern] = [
        re.compile(r"(AIzaSy[A-Za-z0-9_-]+)"),  # Google API Keys
        re.compile(r"(sk-[A-Za-z0-9_-]{10,})"),  # OpenAI / Anthropic / Generic Secret Keys
        re.compile(r"(Bearer\s+[A-Za-z0-9_\-\.=]+)", re.IGNORECASE),  # JWT / Bearer Tokens
        re.compile(r"(-----BEGIN [A-Z ]+ PRIVATE KEY-----[\s\S]*?-----END [A-Z ]+ PRIVATE KEY-----)"),  # Private Keys
        re.compile(r"((?:API_KEY|SECRET|PASSWORD|TOKEN|AUTH|CREDENTIAL)=\s*['\"]?[^'\";\s]+['\"]?)", re.IGNORECASE),
    ]

    SENSITIVE_KEYWORDS: Set[str] = {
        "secret", "token", "password", "auth", "credential", "private_key", "api_key",
        "gemini_api_key", "anthropic_api_key", "openai_api_key", "authorization", "capability_token"
    }

    @classmethod
    def is_sensitive_key(cls, key: str) -> bool:
        k = str(key).lower()
        return any(kw in k for kw in cls.SENSITIVE_KEYWORDS)

    @classmethod
    def redact_text(cls, text: str) -> str:
        """Redacts sensitive pattern matches from raw text."""
        if not text or not isinstance(text, str):
            return text
        result = text
        for pattern in cls.SECRET_PATTERNS:
            result = pattern.sub("[REDACTED]", result)
        return result

    @classmethod
    def redact_object(cls, obj: Any) -> Any:
        """Recursively redacts dictionary keys, strings, lists, or custom objects."""
        if obj is None:
            return None
        if isinstance(obj, str):
            return cls.redact_text(obj)
        if isinstance(obj, (int, float, bool)):
            return obj
        if isinstance(obj, dict):
            redacted_dict: Dict[str, Any] = {}
            for k, v in obj.items():
                if cls.is_sensitive_key(k):
                    redacted_dict[k] = "[REDACTED]"
                else:
                    redacted_dict[k] = cls.redact_object(v)
            return redacted_dict
        if isinstance(obj, list):
            return [cls.redact_object(item) for item in obj]
        if isinstance(obj, tuple):
            return tuple(cls.redact_object(item) for item in obj)
        return str(obj)


# ──────────────────────────────────────────────
# Event Serializer & Sinks
# ──────────────────────────────────────────────

class EventSerializer:
    """JSON Serializer for Observability Events with safe object fallback."""

    @staticmethod
    def serialize(event: ObservabilityEvent) -> str:
        redacted_dict = EventRedactor.redact_object(event.to_dict())
        return json.dumps(redacted_dict, default=str)


class EventSink(ABC):
    """Abstract destination sink for observability events."""

    @abstractmethod
    def emit(self, event: ObservabilityEvent) -> None:
        pass

    def flush(self) -> None:
        pass

    def close(self) -> None:
        pass


class ConsoleEventSink(EventSink):
    """Real-time console output sink for CLI verbose mode."""

    def __init__(self, verbose_only: bool = True):
        self.verbose_only = verbose_only

    def emit(self, event: ObservabilityEvent) -> None:
        try:
            redacted_msg = EventRedactor.redact_text(event.message)
            lvl_icon = "ℹ️" if event.level == "INFO" else "⚠️" if event.level == "WARNING" else "❌"
            time_str = event.timestamp.split("T")[-1].replace("Z", "")
            output = f"[{time_str}] [{lvl_icon} {event.level}] [{event.category}] {event.component}.{event.operation} — {redacted_msg}"
            if event.duration_ms > 0:
                output += f" ({event.duration_ms:.2f}ms)"
            print(output)
        except Exception:
            pass


class FileEventSink(EventSink):
    """JSON Lines file logger sink supporting size-based log rotation."""

    def __init__(self, log_file_path: str, max_bytes: int = 10 * 1024 * 1024, backup_count: int = 5):
        self.log_file_path = os.path.abspath(log_file_path)
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self._lock = threading.Lock()
        os.makedirs(os.path.dirname(self.log_file_path), exist_ok=True)

    def emit(self, event: ObservabilityEvent) -> None:
        try:
            line = EventSerializer.serialize(event) + "\n"
            with self._lock:
                self._rotate_if_needed(len(line.encode("utf-8")))
                with open(self.log_file_path, "a", encoding="utf-8") as f:
                    f.write(line)
        except Exception as exc:
            logger.warning("FileEventSink emit failure: %s", exc)

    def _rotate_if_needed(self, incoming_bytes: int) -> None:
        if not os.path.exists(self.log_file_path):
            return
        if os.path.getsize(self.log_file_path) + incoming_bytes < self.max_bytes:
            return

        for i in range(self.backup_count - 1, 0, -1):
            sfn = f"{self.log_file_path}.{i}"
            dfn = f"{self.log_file_path}.{i + 1}"
            if os.path.exists(sfn):
                if os.path.exists(dfn):
                    os.remove(dfn)
                os.rename(sfn, dfn)

        dfn = f"{self.log_file_path}.1"
        if os.path.exists(dfn):
            os.remove(dfn)
        os.rename(self.log_file_path, dfn)


class AuditEventSink(FileEventSink):
    """Dedicated JSON Lines audit log sink for SECURITY events (audit.jsonl)."""

    def __init__(self, audit_file_path: str, max_bytes: int = 10 * 1024 * 1024, backup_count: int = 5):
        super().__init__(audit_file_path, max_bytes, backup_count)

    def emit(self, event: ObservabilityEvent) -> None:
        if event.category == EventCategory.SECURITY.value or event.event_type.startswith("SECURITY_") or event.event_type in ("PERMISSION_DENIED", "SANDBOX_VIOLATION", "PATH_TRAVERSAL_BLOCKED", "SECRET_ACCESS_DENIED", "SECRET_LEAK_BLOCKED"):
            super().emit(event)


# ──────────────────────────────────────────────
# Metrics & Latency Percentile Calculator
# ──────────────────────────────────────────────

class MetricsCollector:
    """In-memory telemetry metric collector calculating latency percentiles (p50, p95, p99)."""

    def __init__(self):
        self._lock = threading.RLock()
        self.counters: Dict[str, int] = {}
        self.latencies: Dict[str, List[float]] = {}

    def increment(self, metric_name: str, amount: int = 1) -> None:
        with self._lock:
            self.counters[metric_name] = self.counters.get(metric_name, 0) + amount

    def record_latency(self, metric_name: str, duration_ms: float) -> None:
        with self._lock:
            if metric_name not in self.latencies:
                self.latencies[metric_name] = []
            self.latencies[metric_name].append(duration_ms)

    def get_percentile(self, metric_name: str, percentile: float) -> float:
        with self._lock:
            vals = self.latencies.get(metric_name, [])
            if not vals:
                return 0.0
            if len(vals) == 1:
                return round(vals[0], 2)
            sorted_vals = sorted(vals)
            k = (len(sorted_vals) - 1) * (percentile / 100.0)
            f = int(k)
            c = int(k) + 1 if int(k) + 1 < len(sorted_vals) else f
            if f == c:
                return round(sorted_vals[f], 2)
            weight = k - f
            return round(sorted_vals[f] * (1.0 - weight) + sorted_vals[c] * weight, 2)

    def get_metrics_summary(self) -> Dict[str, Any]:
        with self._lock:
            summary: Dict[str, Any] = {"counters": dict(self.counters), "latencies": {}}
            for name, vals in self.latencies.items():
                if vals:
                    summary["latencies"][name] = {
                        "count": len(vals),
                        "avg": round(sum(vals) / len(vals), 2),
                        "p50": self.get_percentile(name, 50.0),
                        "p95": self.get_percentile(name, 95.0),
                        "p99": self.get_percentile(name, 99.0)
                    }
            return summary


# ──────────────────────────────────────────────
# Trace Span Context Manager
# ──────────────────────────────────────────────

class TraceSpan:
    """Context Manager tracking execution time, trace IDs, and span metrics safely."""

    def __init__(self, manager: "ObservabilityManager", component: str, operation: str, category: EventCategory = EventCategory.PIPELINE):
        self.manager = manager
        self.component = component
        self.operation = operation
        self.category = category
        self.span_id = f"SPN_{component}_{int(time.time_ns() % 1000000)}"
        self.parent_span_id = CorrelationContext.get_current_span_id()
        self.start_time = 0.0
        self.success = True
        self.error_msg = ""

    def __enter__(self) -> "TraceSpan":
        self.start_time = time.perf_counter()
        CorrelationContext.push_span(self.span_id)
        self.manager.publish_event(
            level=EventLevel.INFO,
            category=self.category,
            event_type=EventType.STAGE_STARTED,
            component=self.component,
            operation=self.operation,
            message=f"Starting span '{self.span_id}' for {self.component}.{self.operation}"
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        duration_ms = (time.perf_counter() - self.start_time) * 1000.0
        CorrelationContext.pop_span()

        if exc_type is not None:
            self.success = False
            self.error_msg = str(exc_val)
            self.manager.publish_event(
                level=EventLevel.ERROR,
                category=self.category,
                event_type=EventType.STAGE_FAILED,
                component=self.component,
                operation=self.operation,
                duration_ms=duration_ms,
                success=False,
                message=f"Span '{self.span_id}' failed: {self.error_msg}",
                metadata={"error_type": exc_type.__name__}
            )
        else:
            self.manager.publish_event(
                level=EventLevel.INFO,
                category=self.category,
                event_type=EventType.STAGE_COMPLETED,
                component=self.component,
                operation=self.operation,
                duration_ms=duration_ms,
                success=True,
                message=f"Span '{self.span_id}' completed in {duration_ms:.2f}ms"
            )

        self.manager.metrics.record_latency(f"{self.component}.{self.operation}", duration_ms)
        self.manager.metrics.increment(f"{self.component}.calls")
        if not self.success:
            self.manager.metrics.increment(f"{self.component}.failures")

        return False  # Do not suppress exception


# ──────────────────────────────────────────────
# Observability Event Bus & Top-Level Manager
# ──────────────────────────────────────────────

class ObservabilityEventBus:
    """Thread-safe pub/sub bus dispatching ObservabilityEvents to registered sinks."""

    def __init__(self):
        self._lock = threading.RLock()
        self.sinks: List[EventSink] = []

    def register_sink(self, sink: EventSink) -> None:
        with self._lock:
            self.sinks.append(sink)

    def publish(self, event: ObservabilityEvent) -> None:
        with self._lock:
            sinks_copy = list(self.sinks) if self.sinks is not None else []
        for sink in sinks_copy:
            try:
                sink.emit(event)
            except Exception as exc:
                logger.warning("EventSink emit failed: %s", exc)



class ObservabilityManager:
    """Thread-safe Singleton Facade managing sinks, events, correlation contexts, and metrics.
    
    CRITICAL PRINCIPLE: NEVER CRASH RUNTIME.
    All exceptions inside ObservabilityManager are safely caught to protect core Aegis pipeline execution.
    """

    _instance: Optional["ObservabilityManager"] = None
    _lock = threading.RLock()

    def __new__(cls, log_dir: str = "runtime/logs") -> "ObservabilityManager":
        with cls._lock:
            if cls._instance is None:
                inst = super().__new__(cls)
                inst._initialized = False
                cls._instance = inst
            return cls._instance

    def set_log_dir(self, log_dir: str) -> None:
        """Dynamically updates log directory and re-binds file sinks."""
        with self._lock:
            self.log_dir = os.path.abspath(log_dir)
            os.makedirs(self.log_dir, exist_ok=True)

            runtime_log_file = os.path.join(self.log_dir, "runtime.jsonl")
            audit_log_file = os.path.join(self.log_dir, "audit.jsonl")

            self.file_sink = FileEventSink(runtime_log_file)
            self.audit_sink = AuditEventSink(audit_log_file)

            sinks = [self.file_sink, self.audit_sink]
            if getattr(self, "_console_enabled", False):
                sinks.append(self.console_sink)

            self.event_bus.sinks = sinks

    def __init__(self, log_dir: str = "runtime/logs"):
        with self._lock:
            if getattr(self, "_initialized", False):
                self.set_log_dir(log_dir)
                return

            self.event_bus = ObservabilityEventBus()
            self.metrics = MetricsCollector()
            self.redactor = EventRedactor()
            self.console_sink = ConsoleEventSink(verbose_only=True)
            self._console_enabled = False

            self._initialized = True
            self.set_log_dir(log_dir)




    @classmethod
    def get_instance(cls) -> "ObservabilityManager":
        """Returns active ObservabilityManager singleton instance."""
        return cls()

    def enable_console(self) -> None:
        """Enables console sink output for verbose mode."""
        with self._lock:
            if not self._console_enabled:
                self.event_bus.register_sink(self.console_sink)
                self._console_enabled = True

    def span(self, component: str, operation: str = "execute", category: EventCategory = EventCategory.PIPELINE) -> TraceSpan:
        """Returns a TraceSpan context manager for tracking execution time."""
        return TraceSpan(self, component, operation, category)

    def publish_event(
        self,
        level: Union[EventLevel, str],
        category: Union[EventCategory, str],
        event_type: Union[EventType, str],
        component: str,
        operation: str,
        message: str,
        duration_ms: float = 0.0,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[ObservabilityEvent]:
        """Publishes a structured event safely without throwing exceptions."""
        try:
            lvl_str = level.value if isinstance(level, EventLevel) else str(level)
            cat_str = category.value if isinstance(category, EventCategory) else str(category)
            evt_str = event_type.value if isinstance(event_type, EventType) else str(event_type)

            event = ObservabilityEvent(
                event_id=f"EVT_{time.time_ns()}",
                correlation_id=CorrelationContext.get_correlation_id(),
                session_id=CorrelationContext.get_session_id(),
                request_id=CorrelationContext.get_request_id(),
                trace_id=CorrelationContext.get_trace_id(),
                span_id=CorrelationContext.get_current_span_id(),
                parent_span_id=CorrelationContext.get_parent_span_id(),
                level=lvl_str,
                category=cat_str,
                event_type=evt_str,
                component=component,
                operation=operation,
                duration_ms=round(duration_ms, 2),
                success=success,
                message=EventRedactor.redact_text(message),
                metadata=EventRedactor.redact_object(metadata or {})
            )

            self.event_bus.publish(event)
            return event

        except Exception as exc:
            # FAIL-SAFE GUARANTEE: Never crash main Aegis pipeline on telemetry error
            logger.warning("ObservabilityManager publish_event error: %s", exc)
            return None

    def read_logs(self, tail: int = 50, category: Optional[str] = None, session_id: Optional[str] = None, level: Optional[str] = None) -> List[Dict[str, Any]]:
        """Reads recent runtime logs with optional filtering."""
        runtime_log_file = os.path.join(self.log_dir, "runtime.jsonl")
        if not os.path.exists(runtime_log_file):
            return []

        results: List[Dict[str, Any]] = []
        try:
            with open(runtime_log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

            for line in reversed(lines):
                if not line.strip():
                    continue
                try:
                    data = json.loads(line.strip())
                    if category and data.get("category") != category.upper():
                        continue
                    if session_id and data.get("session_id") != session_id:
                        continue
                    if level and data.get("level") != level.upper():
                        continue
                    results.append(data)
                    if len(results) >= tail:
                        break
                except json.JSONDecodeError:
                    continue
        except Exception as exc:
            logger.warning("Error reading logs: %s", exc)

        return list(reversed(results))

    def read_audit_logs(self, tail: int = 50, session_id: Optional[str] = None, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        """Reads security audit logs with optional filtering."""
        audit_log_file = os.path.join(self.log_dir, "audit.jsonl")
        if not os.path.exists(audit_log_file):
            return []

        results: List[Dict[str, Any]] = []
        try:
            with open(audit_log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

            for line in reversed(lines):
                if not line.strip():
                    continue
                try:
                    data = json.loads(line.strip())
                    if session_id and data.get("session_id") != session_id:
                        continue
                    if severity and data.get("level") != severity.upper():
                        continue
                    results.append(data)
                    if len(results) >= tail:
                        break
                except json.JSONDecodeError:
                    continue
        except Exception as exc:
            logger.warning("Error reading audit logs: %s", exc)

        return list(reversed(results))
