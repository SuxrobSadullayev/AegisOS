"""
Aegis AI Operating System — Secure Multi-Agent Event Bus Subsystem
Provides high-performance, deterministic multi-agent message routing featuring:
- Structured event schema with correlation context propagation
- Synchronous & Request/Reply correlation patterns
- Replay protection & deduplication sliding window
- Rate limiting (100 events/sec per agent) & Payload size boundaries (50 KB)
- TTL expiration enforcement
- Secret redaction barrier on event payloads
- Observability integration (structured event log & telemetry metrics)
Python 3.12+ compliant. Zero external dependencies.
"""

import os
import sys
import json
import time
import uuid
import hashlib
import logging
import threading
import queue
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any, Callable

from runtime.src.observability import ObservabilityManager, EventLevel, EventCategory, EventRedactor

logger = logging.getLogger("AegisEventBus")


# ──────────────────────────────────────────────
# Enums & Custom Exceptions
# ──────────────────────────────────────────────

class EventPriority(Enum):
    """Event priority levels for bus dispatch queueing."""
    CRITICAL = 0
    HIGH = 10
    NORMAL = 50
    LOW = 100


class EventBusError(Exception):
    """Base exception for all Event Bus errors."""
    pass


class EventValidationError(EventBusError):
    """Raised when event payload or schema validation fails."""
    pass


class EventRateLimitError(EventBusError):
    """Raised when an agent exceeds event publishing rate limits."""
    pass


class EventTimeoutError(EventBusError):
    """Raised when request_reply times out waiting for a response."""
    pass


class EventAuthorizationError(EventBusError):
    """Raised when an unauthorized agent attempts to publish or subscribe."""
    pass


# ──────────────────────────────────────────────
# Structured Event Schema
# ──────────────────────────────────────────────

@dataclass
class AgentEvent:
    """Deterministic, structured event object for multi-agent communication."""
    event_type: str
    source_agent_id: str
    event_id: str = field(default_factory=lambda: f"EVT_{uuid.uuid4().hex[:12]}")
    target_agent_id: str = ""  # Empty string indicates broadcast to all subscribers
    correlation_id: str = ""
    trace_id: str = ""
    span_id: str = ""
    session_id: str = ""
    timestamp_utc: float = field(default_factory=time.time)
    priority: int = EventPriority.NORMAL.value
    ttl_seconds: float = 30.0
    payload: Dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """Returns True if event TTL has elapsed."""
        if self.ttl_seconds <= 0:
            return False
        return (time.time() - self.timestamp_utc) > self.ttl_seconds

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "source_agent_id": self.source_agent_id,
            "target_agent_id": self.target_agent_id,
            "correlation_id": self.correlation_id,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "session_id": self.session_id,
            "timestamp_utc": self.timestamp_utc,
            "priority": self.priority,
            "ttl_seconds": self.ttl_seconds,
            "payload": self.payload,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentEvent":
        return cls(
            event_id=data.get("event_id", f"EVT_{uuid.uuid4().hex[:12]}"),
            event_type=data.get("event_type", "UNKNOWN"),
            source_agent_id=data.get("source_agent_id", "unknown"),
            target_agent_id=data.get("target_agent_id", ""),
            correlation_id=data.get("correlation_id", ""),
            trace_id=data.get("trace_id", ""),
            span_id=data.get("span_id", ""),
            session_id=data.get("session_id", ""),
            timestamp_utc=data.get("timestamp_utc", time.time()),
            priority=data.get("priority", EventPriority.NORMAL.value),
            ttl_seconds=data.get("ttl_seconds", 30.0),
            payload=data.get("payload", {}),
        )


@dataclass
class EventBusLimits:
    """Security boundaries for event payload size, rate limits, and deduplication."""
    max_payload_bytes: int = 50 * 1024  # 50 KB
    max_rate_per_sec: int = 100
    dedup_window_size: int = 1000


@dataclass
class EventSubscription:
    """Subscriber registration container."""
    subscription_id: str
    subscriber_agent_id: str
    event_type: str
    handler: Callable[[AgentEvent], Optional[AgentEvent]]
    priority: int = 100


# ──────────────────────────────────────────────
# Secure Event Bus Engine
# ──────────────────────────────────────────────

class SecureEventBus:
    """Thread-safe, secure multi-agent event bus router."""

    def __init__(self, limits: Optional[EventBusLimits] = None):
        self.limits = limits or EventBusLimits()
        self._lock = threading.RLock()
        self.subscriptions: Dict[str, List[EventSubscription]] = {}  # event_type -> list of subs
        self.processed_event_ids: Set[str] = set()
        self.dedup_queue: List[str] = []
        self.rate_tracker: Dict[str, List[float]] = {}  # agent_id -> timestamps
        self.pending_replies: Dict[str, Tuple[threading.Event, Dict[str, Any]]] = {}  # correlation_id -> (event, result_box)
        self.observability = ObservabilityManager.get_instance()

    def _check_rate_limit(self, agent_id: str) -> None:
        """Enforces max_rate_per_sec publishing limit per agent."""
        now = time.time()
        with self._lock:
            history = self.rate_tracker.get(agent_id, [])
            history = [t for t in history if (now - t) < 1.0]
            if len(history) >= self.limits.max_rate_per_sec:
                raise EventRateLimitError(
                    f"Agent '{agent_id}' exceeded publishing rate limit ({self.limits.max_rate_per_sec} events/sec)"
                )
            history.append(now)
            self.rate_tracker[agent_id] = history

    def _check_deduplication(self, event_id: str) -> bool:
        """Returns True if event_id has already been processed (replay protection)."""
        with self._lock:
            if event_id in self.processed_event_ids:
                return True
            self.processed_event_ids.add(event_id)
            self.dedup_queue.append(event_id)
            if len(self.dedup_queue) > self.limits.dedup_window_size:
                oldest = self.dedup_queue.pop(0)
                self.processed_event_ids.discard(oldest)
            return False

    def subscribe(
        self,
        subscriber_agent_id: str,
        event_type: str,
        handler: Callable[[AgentEvent], Optional[AgentEvent]],
        priority: int = 100
    ) -> str:
        """Registers a subscription handler for a specific event type."""
        with self._lock:
            sub_id = f"SUB_{subscriber_agent_id}_{uuid.uuid4().hex[:8]}"
            sub = EventSubscription(
                subscription_id=sub_id,
                subscriber_agent_id=subscriber_agent_id,
                event_type=event_type,
                handler=handler,
                priority=priority,
            )
            if event_type not in self.subscriptions:
                self.subscriptions[event_type] = []
            self.subscriptions[event_type].append(sub)
            self.subscriptions[event_type].sort(key=lambda s: s.priority)
            return sub_id

    def unsubscribe(self, subscription_id: str) -> bool:
        """Removes a subscription handler by ID."""
        with self._lock:
            for event_type, subs in self.subscriptions.items():
                for sub in list(subs):
                    if sub.subscription_id == subscription_id:
                        subs.remove(sub)
                        return True
            return False

    def publish(self, event: AgentEvent) -> bool:
        """Validates, redacts secrets, and dispatches event to subscribers."""
        if event.is_expired():
            logger.warning("Event '%s' expired (TTL=%ss)", event.event_id, event.ttl_seconds)
            return False

        self._check_rate_limit(event.source_agent_id)

        # Replay protection check
        if self._check_deduplication(event.event_id):
            logger.warning("Duplicate event '%s' rejected (replay protection)", event.event_id)
            return False

        # Validate payload size
        payload_json = json.dumps(event.payload, default=str)
        if len(payload_json.encode("utf-8")) > self.limits.max_payload_bytes:
            raise EventValidationError(
                f"Event payload size ({len(payload_json)} bytes) exceeds limit ({self.limits.max_payload_bytes} bytes)"
            )

        # Redact secrets in payload
        redacted_payload = EventRedactor.redact_object(event.payload)
        event.payload = redacted_payload if isinstance(redacted_payload, dict) else {"data": redacted_payload}

        # Check request/reply pending waiters
        if event.correlation_id and event.correlation_id in self.pending_replies:
            reply_evt, result_box = self.pending_replies[event.correlation_id]
            result_box["event"] = event
            reply_evt.set()

        # Find subscribers
        with self._lock:
            subs = list(self.subscriptions.get(event.event_type, []))
            wildcard_subs = list(self.subscriptions.get("*", []))

        all_subs = subs + wildcard_subs
        delivered_count = 0

        for sub in all_subs:
            # If target_agent_id is specified, filter for target
            if event.target_agent_id and sub.subscriber_agent_id != event.target_agent_id:
                continue

            try:
                reply_result = sub.handler(event)
                delivered_count += 1
                if reply_result and isinstance(reply_result, AgentEvent):
                    # Automatically publish reply event
                    self.publish(reply_result)
            except Exception as exc:
                logger.error("Error in event handler '%s' for event '%s': %s", sub.subscription_id, event.event_id, exc)

        # Telemetry
        self.observability.publish_event(
            level=EventLevel.INFO, category=EventCategory.PIPELINE,
            event_type="AGENT_EVENT_PUBLISHED", component="SecureEventBus",
            operation="publish", message=f"Event '{event.event_type}' ({event.event_id}) published by '{event.source_agent_id}' to {delivered_count} subscribers"
        )
        return delivered_count > 0

    def request_reply(self, event: AgentEvent, timeout_seconds: float = 10.0) -> AgentEvent:
        """Sends an event and synchronously waits for a matching reply event (correlation_id)."""
        if not event.correlation_id:
            event.correlation_id = f"CORR_{uuid.uuid4().hex[:12]}"

        reply_signal = threading.Event()
        result_box: Dict[str, Any] = {}

        with self._lock:
            self.pending_replies[event.correlation_id] = (reply_signal, result_box)

        try:
            self.publish(event)
            signaled = reply_signal.wait(timeout=timeout_seconds)
            if not signaled or "event" not in result_box:
                raise EventTimeoutError(f"Request-reply timed out ({timeout_seconds}s) for correlation_id '{event.correlation_id}'")
            return result_box["event"]
        finally:
            with self._lock:
                self.pending_replies.pop(event.correlation_id, None)

    def broadcast(self, event: AgentEvent) -> int:
        """Broadcasts event to all matching subscribers regardless of target_agent_id."""
        event.target_agent_id = ""  # Ensure empty target for broadcast
        self.publish(event)
        return len(self.subscriptions.get(event.event_type, []))

    def clear(self) -> None:
        """Clears all subscriptions and pending replies."""
        with self._lock:
            self.subscriptions.clear()
            self.processed_event_ids.clear()
            self.dedup_queue.clear()
            self.rate_tracker.clear()
            self.pending_replies.clear()
