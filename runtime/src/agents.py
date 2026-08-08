"""
Aegis AI Operating System — Distributed Agent Coordination & Registry Subsystem
Provides multi-agent registration, deterministic task routing, capability matching,
circular delegation protection, default DENY permission tokens, sandbox integration,
bounded retries, timeout management, and failure resilience.
Python 3.12+ compliant. Zero external dependencies.
"""

import os
import sys
import time
import uuid
import json
import logging
import threading
import concurrent.futures
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any

from runtime.src.config import AegisConfig
from runtime.src.plugin import PluginPermission
from runtime.src.sandbox import SandboxManager, SandboxPolicy, SandboxLimits, SandboxRequest
from runtime.src.event_bus import SecureEventBus, AgentEvent, EventPriority
from runtime.src.observability import ObservabilityManager, EventLevel, EventCategory, CorrelationContext

logger = logging.getLogger("AegisAgentSubsystem")


# ──────────────────────────────────────────────
# Enums & Custom Exceptions
# ──────────────────────────────────────────────

class AgentState(Enum):
    """Finite State Machine for multi-agent lifecycle."""
    DISCOVERED = "DISCOVERED"
    REGISTERED = "REGISTERED"
    INITIALIZING = "INITIALIZING"
    READY = "READY"
    BUSY = "BUSY"
    SUSPENDED = "SUSPENDED"
    FAILED = "FAILED"
    STOPPED = "STOPPED"


class AgentTrustLevel(Enum):
    """Trust classification for multi-agent execution."""
    CORE = "CORE"            # Built-in kernel agents (In-process execution)
    TRUSTED = "TRUSTED"        # Signed & verified partner agents
    VERIFIED = "VERIFIED"      # Passed manifest & policy verification
    UNTRUSTED = "UNTRUSTED"    # External / third-party agents (Subprocess Sandbox isolated)
    BLOCKED = "BLOCKED"        # Blacklisted / Revoked from executing tasks


class AgentError(Exception):
    """Base exception for all agent coordination errors."""
    pass


class AgentNotFoundError(AgentError):
    """Raised when target agent_id is not registered."""
    pass


class AgentAuthorizationError(AgentError):
    """Raised when agent permission or token check fails."""
    pass


class CircularDelegationError(AgentError):
    """Raised when circular task delegation or infinite recursive spawning is detected."""
    pass


class AgentTaskExecutionError(AgentError):
    """Raised when task execution fails or times out."""
    pass


# ──────────────────────────────────────────────
# Data Structures & Tokens
# ──────────────────────────────────────────────

@dataclass
class AgentCapabilityToken:
    """Capability token issued to agents upon task assignment."""
    agent_id: str
    granted_permissions: Set[PluginPermission] = field(default_factory=set)
    issued_at_utc: float = field(default_factory=time.time)

    def has_permission(self, permission: PluginPermission) -> bool:
        return permission in self.granted_permissions


@dataclass
class AgentDescriptor:
    """Declaration of agent identity, capabilities, permissions, and limits."""
    agent_id: str
    name: str
    version: str
    capabilities: List[str] = field(default_factory=list)
    permissions: List[PluginPermission] = field(default_factory=list)
    trust_level: AgentTrustLevel = AgentTrustLevel.UNTRUSTED
    supported_task_types: List[str] = field(default_factory=list)
    max_concurrency: int = 4
    max_execution_time_seconds: float = 30.0
    priority: int = 100
    registered_at_utc: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "version": self.version,
            "capabilities": self.capabilities,
            "permissions": [p.value for p in self.permissions],
            "trust_level": self.trust_level.value,
            "supported_task_types": self.supported_task_types,
            "max_concurrency": self.max_concurrency,
            "max_execution_time_seconds": self.max_execution_time_seconds,
            "priority": self.priority,
            "registered_at_utc": self.registered_at_utc,
            "metadata": self.metadata,
        }


@dataclass
class TaskResult:
    """Standardized response from multi-agent task execution."""
    task_id: str
    task_type: str
    assigned_agent_id: str
    success: bool
    result: Dict[str, Any] = field(default_factory=dict)
    error_message: str = ""
    execution_time_ms: float = 0.0
    delegation_depth: int = 0


# ──────────────────────────────────────────────
# Agent Interface (Base Abstract Class)
# ──────────────────────────────────────────────

class AgentInterface(ABC):
    """Abstract interface for in-process Aegis agents."""

    @abstractmethod
    def get_descriptor(self) -> AgentDescriptor:
        pass

    @abstractmethod
    def initialize(self, ctx: Dict[str, Any]) -> bool:
        pass

    @abstractmethod
    def execute_task(
        self,
        task_id: str,
        task_type: str,
        payload: Dict[str, Any],
        token: AgentCapabilityToken
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    def shutdown() -> bool:
        pass


# ──────────────────────────────────────────────
# Agent Registry Subsystem
# ──────────────────────────────────────────────

class AgentRegistry:
    """Thread-safe registry managing agent descriptors, FSM states, and health monitoring."""

    def __init__(self):
        self._lock = threading.RLock()
        self.descriptors: Dict[str, AgentDescriptor] = {}
        self.instances: Dict[str, AgentInterface] = {}
        self.states: Dict[str, AgentState] = {}
        self.active_task_counts: Dict[str, int] = {}
        self.failure_counts: Dict[str, int] = {}
        self.observability = ObservabilityManager.get_instance()

    def register_agent(self, descriptor: AgentDescriptor, instance: Optional[AgentInterface] = None) -> bool:
        """Registers a new agent descriptor and optional in-process instance."""
        with self._lock:
            if descriptor.trust_level == AgentTrustLevel.BLOCKED:
                raise AgentAuthorizationError(f"Cannot register BLOCKED agent '{descriptor.agent_id}'")

            self.descriptors[descriptor.agent_id] = descriptor
            if instance:
                self.instances[descriptor.agent_id] = instance
            self.states[descriptor.agent_id] = AgentState.REGISTERED
            self.active_task_counts[descriptor.agent_id] = 0
            self.failure_counts[descriptor.agent_id] = 0

            self.observability.publish_event(
                level=EventLevel.INFO, category=EventCategory.PIPELINE,
                event_type="AGENT_REGISTERED", component="AgentRegistry",
                operation="register", message=f"Agent '{descriptor.agent_id}' ({descriptor.name}) registered [{descriptor.trust_level.value}]"
            )
            return True

    def unregister_agent(self, agent_id: str) -> bool:
        """Unregisters an agent completely."""
        with self._lock:
            if agent_id not in self.descriptors:
                return False
            self.descriptors.pop(agent_id, None)
            self.instances.pop(agent_id, None)
            self.states.pop(agent_id, None)
            self.active_task_counts.pop(agent_id, None)
            self.failure_counts.pop(agent_id, None)

            self.observability.publish_event(
                level=EventLevel.INFO, category=EventCategory.PIPELINE,
                event_type="AGENT_UNREGISTERED", component="AgentRegistry",
                operation="unregister", message=f"Agent '{agent_id}' unregistered"
            )
            return True

    def get_descriptor(self, agent_id: str) -> Optional[AgentDescriptor]:
        with self._lock:
            return self.descriptors.get(agent_id)

    def get_instance(self, agent_id: str) -> Optional[AgentInterface]:
        with self._lock:
            return self.instances.get(agent_id)

    def get_state(self, agent_id: str) -> Optional[AgentState]:
        with self._lock:
            return self.states.get(agent_id)

    def transition_state(self, agent_id: str, target_state: AgentState) -> bool:
        """Transitions agent FSM state."""
        with self._lock:
            if agent_id not in self.descriptors:
                return False
            old_state = self.states.get(agent_id, AgentState.DISCOVERED)
            self.states[agent_id] = target_state

            self.observability.publish_event(
                level=EventLevel.INFO, category=EventCategory.PIPELINE,
                event_type="AGENT_STATE_CHANGED", component="AgentRegistry",
                operation="transition", message=f"Agent '{agent_id}' state: {old_state.value} -> {target_state.value}"
            )
            return True

    def list_agents(self) -> List[AgentDescriptor]:
        with self._lock:
            return list(self.descriptors.values())

    def find_matching_agents(
        self,
        task_type: str,
        required_capabilities: Optional[List[str]] = None,
        trust_level: Optional[AgentTrustLevel] = None
    ) -> List[AgentDescriptor]:
        """Deterministically selects matching agents for a task type and required capabilities."""
        with self._lock:
            req_caps = set(required_capabilities or [])
            matches: List[AgentDescriptor] = []

            for desc in self.descriptors.values():
                if desc.trust_level == AgentTrustLevel.BLOCKED:
                    continue
                if trust_level and desc.trust_level != trust_level:
                    continue
                if task_type and task_type not in desc.supported_task_types:
                    continue
                if req_caps and not req_caps.issubset(set(desc.capabilities)):
                    continue

                state = self.states.get(desc.agent_id, AgentState.DISCOVERED)
                if state in (AgentState.FAILED, AgentState.STOPPED, AgentState.SUSPENDED):
                    continue

                matches.append(desc)

            # Deterministic sorting strategy: (trust_level_weight, priority, active_tasks, agent_id)
            trust_weights = {
                AgentTrustLevel.CORE: 0,
                AgentTrustLevel.TRUSTED: 1,
                AgentTrustLevel.VERIFIED: 2,
                AgentTrustLevel.UNTRUSTED: 3,
                AgentTrustLevel.BLOCKED: 99,
            }
            matches.sort(
                key=lambda d: (
                    trust_weights.get(d.trust_level, 5),
                    d.priority,
                    self.active_task_counts.get(d.agent_id, 0),
                    d.agent_id
                )
            )
            return matches


# ──────────────────────────────────────────────
# Deterministic Task Coordinator Subsystem
# ──────────────────────────────────────────────

class TaskCoordinator:
    """Multi-Agent Task Routing & Orchestration Engine featuring circular delegation protection,
    default DENY security tokens, subprocess sandbox delegation for untrusted agents, and bounded retries.
    """

    def __init__(
        self,
        registry: AgentRegistry,
        event_bus: SecureEventBus,
        sandbox_manager: Optional[SandboxManager] = None,
        max_delegation_depth: int = 5,
        max_retries: int = 3
    ):
        self.registry = registry
        self.event_bus = event_bus
        self.sandbox_manager = sandbox_manager
        self.max_delegation_depth = max_delegation_depth
        self.max_retries = max_retries
        self._lock = threading.RLock()
        self.observability = ObservabilityManager.get_instance()

    def submit_task(
        self,
        task_type: str,
        payload: Dict[str, Any],
        required_capabilities: Optional[List[str]] = None,
        session_id: Optional[str] = None,
        delegation_stack: Optional[List[str]] = None
    ) -> TaskResult:
        """Submits and routes a task to the optimal agent with circular delegation protection."""
        task_id = f"TSK_{uuid.uuid4().hex[:12]}"
        stack = list(delegation_stack or [])
        depth = len(stack)

        if depth > self.max_delegation_depth:
            raise CircularDelegationError(
                f"Maximum delegation depth ({self.max_delegation_depth}) exceeded. Stack: {' -> '.join(stack)}"
            )

        # Match agents deterministically
        matching = self.registry.find_matching_agents(task_type, required_capabilities)
        if not matching:
            self.observability.publish_event(
                level=EventLevel.WARNING, category=EventCategory.PIPELINE,
                event_type="TASK_ROUTING_FAILED", component="TaskCoordinator",
                operation="route", message=f"No matching agent found for task_type '{task_type}'"
            )
            return TaskResult(
                task_id=task_id, task_type=task_type, assigned_agent_id="",
                success=False, error_message=f"No matching agent available for task type '{task_type}'",
                delegation_depth=depth
            )

        selected_agent = matching[0]

        # Circular delegation check: agent cannot delegate to itself
        if selected_agent.agent_id in stack:
            raise CircularDelegationError(
                f"Circular delegation detected: Agent '{selected_agent.agent_id}' is already in execution stack ({' -> '.join(stack)})"
            )

        stack.append(selected_agent.agent_id)

        self.observability.publish_event(
            level=EventLevel.INFO, category=EventCategory.PIPELINE,
            event_type="TASK_SUBMITTED", component="TaskCoordinator",
            operation="submit", message=f"Task '{task_id}' ({task_type}) routed to agent '{selected_agent.agent_id}' [Depth {depth}]"
        )

        start_time = time.time()
        result_payload: Dict[str, Any] = {}
        last_error = ""
        success = False

        # Issue CapabilityToken with Default DENY (only declared permissions)
        token = AgentCapabilityToken(
            agent_id=selected_agent.agent_id,
            granted_permissions=set(selected_agent.permissions)
        )

        # Execute with bounded retries
        for attempt in range(1, self.max_retries + 1):
            try:
                self.registry.active_task_counts[selected_agent.agent_id] += 1
                self.registry.transition_state(selected_agent.agent_id, AgentState.BUSY)

                # UNTRUSTED agents execute in Subprocess Sandbox
                if selected_agent.trust_level == AgentTrustLevel.UNTRUSTED and self.sandbox_manager:
                    sb_req = SandboxRequest(
                        operation="EXECUTE_TASK",
                        params={"task_id": task_id, "task_type": task_type, "payload": payload},
                        plugin_id=selected_agent.agent_id
                    )
                    sb_resp = self.sandbox_manager.send_request(selected_agent.agent_id, sb_req)
                    if not sb_resp.success:
                        raise AgentTaskExecutionError(f"Sandboxed execution failed: {sb_resp.error_code}")
                    result_payload = sb_resp.data
                else:
                    # In-process execution
                    instance = self.registry.get_instance(selected_agent.agent_id)
                    if instance:
                        result_payload = instance.execute_task(task_id, task_type, payload, token)
                    else:
                        # Fallback to Event Bus dispatch
                        evt = AgentEvent(
                            event_type="TASK_REQUESTED",
                            source_agent_id="task_coordinator",
                            target_agent_id=selected_agent.agent_id,
                            session_id=session_id or "",
                            payload={"task_id": task_id, "task_type": task_type, "payload": payload}
                        )
                        reply_evt = self.event_bus.request_reply(evt, timeout_seconds=selected_agent.max_execution_time_seconds)
                        result_payload = reply_evt.payload

                success = True
                break

            except Exception as exc:
                last_error = str(exc)
                logger.warning("Attempt %d/%d failed for agent '%s': %s", attempt, selected_agent.agent_id, exc)
                self.registry.failure_counts[selected_agent.agent_id] += 1
                time.sleep(0.05)
            finally:
                self.registry.active_task_counts[selected_agent.agent_id] = max(
                    0, self.registry.active_task_counts[selected_agent.agent_id] - 1
                )
                self.registry.transition_state(selected_agent.agent_id, AgentState.READY)

        exec_time_ms = (time.time() - start_time) * 1000.0

        if success:
            self.observability.publish_event(
                level=EventLevel.INFO, category=EventCategory.PIPELINE,
                event_type="TASK_COMPLETED", component="TaskCoordinator",
                operation="complete", message=f"Task '{task_id}' completed by '{selected_agent.agent_id}' in {exec_time_ms:.2f}ms"
            )
        else:
            self.observability.publish_event(
                level=EventLevel.ERROR, category=EventCategory.PIPELINE,
                event_type="TASK_FAILED", component="TaskCoordinator",
                operation="fail", message=f"Task '{task_id}' failed after {self.max_retries} retries: {last_error}"
            )

        return TaskResult(
            task_id=task_id,
            task_type=task_type,
            assigned_agent_id=selected_agent.agent_id,
            success=success,
            result=result_payload,
            error_message=last_error if not success else "",
            execution_time_ms=round(exec_time_ms, 2),
            delegation_depth=depth
        )
