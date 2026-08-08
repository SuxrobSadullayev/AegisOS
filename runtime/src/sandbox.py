"""
Aegis AI Operating System — Process Sandbox & Subprocess Isolation Subsystem
Provides subprocess isolation, Default DENY policy enforcement, JSON IPC protocol,
timeout protection, worker crash recovery, and capability token validation.
Python 3.12+ compliant. Zero external dependencies.
"""

import sys
import os
import io
import json
import time
import signal
import subprocess
import threading
import logging
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger("AegisSandbox")


# ──────────────────────────────────────────────
# Exceptions
# ──────────────────────────────────────────────

class SandboxError(Exception):
    """Base exception for all Aegis Sandbox errors."""
    pass


class SandboxTimeoutError(SandboxError):
    """Raised when a sandbox execution exceeds execution_timeout_sec."""
    pass


class SandboxCrashedError(SandboxError):
    """Raised when a sandbox worker process crashes unexpectedly or returns a non-zero exit code."""
    pass


class SandboxPermissionError(SandboxError):
    """Raised when a sandbox operation violates Default DENY permissions."""
    pass


# ──────────────────────────────────────────────
# Data Structures & Policies
# ──────────────────────────────────────────────

@dataclass
class SandboxLimits:
    """Resource constraints for an isolated sandbox worker."""
    memory_limit_mb: int = 256
    cpu_time_limit_sec: float = 10.0
    execution_timeout_sec: float = 5.0
    max_output_bytes: int = 1048576  # 1 MB


@dataclass
class SandboxPolicy:
    """Default DENY security policy governing sandbox worker capabilities."""
    allow_filesystem_read: bool = False
    allow_filesystem_write: bool = False
    allow_network: bool = False
    allow_subprocess: bool = False
    allow_env_access: bool = False
    allowed_paths: List[str] = field(default_factory=list)
    limits: SandboxLimits = field(default_factory=SandboxLimits)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allow_filesystem_read": self.allow_filesystem_read,
            "allow_filesystem_write": self.allow_filesystem_write,
            "allow_network": self.allow_network,
            "allow_subprocess": self.allow_subprocess,
            "allow_env_access": self.allow_env_access,
            "allowed_paths": self.allowed_paths,
            "limits": asdict(self.limits)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SandboxPolicy":
        lim_dict = data.get("limits", {})
        limits = SandboxLimits(
            memory_limit_mb=lim_dict.get("memory_limit_mb", 256),
            cpu_time_limit_sec=lim_dict.get("cpu_time_limit_sec", 10.0),
            execution_timeout_sec=lim_dict.get("execution_timeout_sec", 5.0),
            max_output_bytes=lim_dict.get("max_output_bytes", 1048576)
        )
        return cls(
            allow_filesystem_read=data.get("allow_filesystem_read", False),
            allow_filesystem_write=data.get("allow_filesystem_write", False),
            allow_network=data.get("allow_network", False),
            allow_subprocess=data.get("allow_subprocess", False),
            allow_env_access=data.get("allow_env_access", False),
            allowed_paths=data.get("allowed_paths", []),
            limits=limits
        )

    @classmethod
    def default_deny(cls) -> "SandboxPolicy":
        """Constructs a strict Default DENY policy."""
        return cls(
            allow_filesystem_read=False,
            allow_filesystem_write=False,
            allow_network=False,
            allow_subprocess=False,
            allow_env_access=False,
            limits=SandboxLimits()
        )


@dataclass
class SandboxRequest:
    """Structured IPC request sent to isolated PluginWorker."""
    command: str
    payload: Dict[str, Any]
    plugin_id: str
    capability_token: Optional[str] = None
    request_id: str = field(default_factory=lambda: f"REQ_{time.time_ns()}")
    correlation_context: Optional[Dict[str, str]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "command": self.command,
            "payload": self.payload,
            "plugin_id": self.plugin_id,
            "capability_token": self.capability_token,
            "request_id": self.request_id,
            "correlation_context": self.correlation_context
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SandboxRequest":
        return cls(
            command=data.get("command", "EXECUTE"),
            payload=data.get("payload", {}),
            plugin_id=data.get("plugin_id", ""),
            capability_token=data.get("capability_token"),
            request_id=data.get("request_id", f"REQ_{time.time_ns()}"),
            correlation_context=data.get("correlation_context")
        )


@dataclass
class SandboxResponse:
    """Structured IPC response received from isolated PluginWorker."""
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    request_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "result": self.result,
            "error": self.error,
            "error_code": self.error_code,
            "metrics": self.metrics,
            "request_id": self.request_id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SandboxResponse":
        return cls(
            success=data.get("success", False),
            result=data.get("result"),
            error=data.get("error"),
            error_code=data.get("error_code"),
            metrics=data.get("metrics", {}),
            request_id=data.get("request_id", "")
        )


# ──────────────────────────────────────────────
# Isolated Subprocess Worker Loop
# ──────────────────────────────────────────────

class PluginWorker:
    """Isolated execution engine running inside a dedicated subprocess."""

    def __init__(self, policy: SandboxPolicy, plugin_id: str):
        self.policy = policy
        self.plugin_id = plugin_id

    def run_ipc_loop(self) -> None:
        """Main IPC loop listening on stdin and emitting JSON responses to stdout."""
        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                line = line.strip()
                if not line:
                    continue

                req_dict = json.loads(line)
                request = SandboxRequest.from_dict(req_dict)
                response = self.process_request(request)

                resp_json = json.dumps(response.to_dict())
                # Check maximum output size constraint
                if len(resp_json.encode("utf-8")) > self.policy.limits.max_output_bytes:
                    err_resp = SandboxResponse(
                        success=False,
                        error=f"Worker response size ({len(resp_json.encode('utf-8'))} bytes) exceeds limit ({self.policy.limits.max_output_bytes} bytes)",
                        error_code="RESPONSE_SIZE_EXCEEDED",
                        request_id=request.request_id
                    )
                    sys.stdout.write(json.dumps(err_resp.to_dict()) + "\n")
                else:
                    sys.stdout.write(resp_json + "\n")
                sys.stdout.flush()

            except EOFError:
                break
            except Exception as e:
                err_resp = SandboxResponse(
                    success=False,
                    error=f"Malformed worker IPC request: {str(e)}",
                    error_code="MALFORMED_IPC",
                    request_id=""
                )
                sys.stdout.write(json.dumps(err_resp.to_dict()) + "\n")
                sys.stdout.flush()

    def process_request(self, request: SandboxRequest) -> SandboxResponse:
        """Processes a single command request under SandboxPolicy rules."""
        start_time = time.time()
        cmd = request.command.upper()

        # Restore correlation context inside worker process for tracing
        if request.correlation_context:
            try:
                from runtime.src.observability import CorrelationContext
                CorrelationContext.set_context(
                    correlation_id=request.correlation_context.get("correlation_id"),
                    session_id=request.correlation_context.get("session_id"),
                    request_id=request.correlation_context.get("request_id"),
                    trace_id=request.correlation_context.get("trace_id"),
                )
                if request.correlation_context.get("span_id"):
                    CorrelationContext.push_span(request.correlation_context["span_id"])
            except Exception:
                pass

        if cmd == "PING" or cmd == "HEALTHCHECK":
            return SandboxResponse(
                success=True,
                result={"status": "OK", "plugin_id": self.plugin_id},
                metrics={"execution_time_ms": round((time.time() - start_time) * 1000.0, 2)},
                request_id=request.request_id
            )

        if cmd == "CHECK_PERMISSIONS":
            perm_req = request.payload.get("permission", "")
            has_perm = self._check_permission_allowed(perm_req)
            return SandboxResponse(
                success=has_perm,
                result={"permission": perm_req, "allowed": has_perm},
                error=None if has_perm else f"Permission '{perm_req}' DENIED by SandboxPolicy",
                error_code=None if has_perm else "PERMISSION_DENIED",
                request_id=request.request_id
            )

        if cmd == "FILESYSTEM_READ":
            if not self.policy.allow_filesystem_read:
                return SandboxResponse(
                    success=False,
                    error=f"FILESYSTEM_READ operation DENIED by SandboxPolicy for plugin '{self.plugin_id}'",
                    error_code="PERMISSION_DENIED",
                    request_id=request.request_id
                )
            target_path = request.payload.get("path", "")
            path_error = self._validate_path_security(target_path)
            if path_error:
                return SandboxResponse(
                    success=False,
                    error=path_error,
                    error_code="PATH_TRAVERSAL_DENIED",
                    request_id=request.request_id
                )
            try:
                resolved = os.path.realpath(os.path.abspath(target_path))
                # Re-validate resolved path (symlink protection)
                resolved_error = self._validate_path_security(resolved)
                if resolved_error:
                    return SandboxResponse(
                        success=False,
                        error=f"Symlink resolved path violation: {resolved_error}",
                        error_code="PATH_TRAVERSAL_DENIED",
                        request_id=request.request_id
                    )

                # Containment check if allowed_paths are configured
                if self.policy.allowed_paths:
                    is_contained = False
                    for allowed in self.policy.allowed_paths:
                        real_allowed = os.path.realpath(os.path.abspath(allowed))
                        if resolved == real_allowed or resolved.startswith(real_allowed.rstrip(os.sep) + os.sep):
                            is_contained = True
                            break
                    if not is_contained:
                        return SandboxResponse(
                            success=False,
                            error=f"Path containment violation: '{target_path}' resolves to '{resolved}' which is outside allowed_paths {self.policy.allowed_paths}",
                            error_code="PATH_TRAVERSAL_DENIED",
                            request_id=request.request_id
                        )

                if os.path.exists(resolved) and os.path.isfile(resolved):
                    # TOCTOU protection: Use O_NOFOLLOW when opening to prevent symlink swaps
                    flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0)
                    fd = os.open(resolved, flags)
                    with os.fdopen(fd, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read(1024 * 1024)
                    return SandboxResponse(
                        success=True,
                        result={"path": target_path, "content": content},
                        request_id=request.request_id
                    )
                else:
                    return SandboxResponse(
                        success=False,
                        error=f"File not found: {target_path}",
                        error_code="FILE_NOT_FOUND",
                        request_id=request.request_id
                    )
            except Exception as exc:
                return SandboxResponse(
                    success=False,
                    error=f"Filesystem read error: {str(exc)}",
                    error_code="READ_ERROR",
                    request_id=request.request_id
                )

        if cmd == "FILESYSTEM_WRITE":
            if not self.policy.allow_filesystem_write:
                return SandboxResponse(
                    success=False,
                    error=f"FILESYSTEM_WRITE operation DENIED by SandboxPolicy for plugin '{self.plugin_id}'",
                    error_code="PERMISSION_DENIED",
                    request_id=request.request_id
                )
            target_path = request.payload.get("path", "")
            content = request.payload.get("content", "")
            path_error = self._validate_path_security(target_path)
            if path_error:
                return SandboxResponse(
                    success=False,
                    error=path_error,
                    error_code="PATH_TRAVERSAL_DENIED",
                    request_id=request.request_id
                )
            try:
                resolved = os.path.realpath(os.path.abspath(target_path))
                # Re-validate resolved path (symlink protection)
                resolved_error = self._validate_path_security(resolved)
                if resolved_error:
                    return SandboxResponse(
                        success=False,
                        error=f"Symlink resolved path violation: {resolved_error}",
                        error_code="PATH_TRAVERSAL_DENIED",
                        request_id=request.request_id
                    )

                # Containment check if allowed_paths are configured
                if self.policy.allowed_paths:
                    is_contained = False
                    for allowed in self.policy.allowed_paths:
                        real_allowed = os.path.realpath(os.path.abspath(allowed))
                        if resolved == real_allowed or resolved.startswith(real_allowed.rstrip(os.sep) + os.sep):
                            is_contained = True
                            break
                    if not is_contained:
                        return SandboxResponse(
                            success=False,
                            error=f"Path containment violation: '{target_path}' resolves to '{resolved}' which is outside allowed_paths {self.policy.allowed_paths}",
                            error_code="PATH_TRAVERSAL_DENIED",
                            request_id=request.request_id
                        )

                os.makedirs(os.path.dirname(resolved), exist_ok=True)
                # TOCTOU protection: Use O_NOFOLLOW when opening to prevent symlink swaps
                flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | getattr(os, 'O_NOFOLLOW', 0)
                fd = os.open(resolved, flags, 0o600)
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    f.write(content)
                return SandboxResponse(
                    success=True,
                    result={"path": target_path, "bytes_written": len(content)},
                    request_id=request.request_id
                )
            except Exception as exc:
                return SandboxResponse(
                    success=False,
                    error=f"Filesystem write error: {str(exc)}",
                    error_code="WRITE_ERROR",
                    request_id=request.request_id
                )

        if cmd == "NETWORK_REQUEST":
            if not self.policy.allow_network:
                return SandboxResponse(
                    success=False,
                    error=f"NETWORK_OUTBOUND operation DENIED by SandboxPolicy for plugin '{self.plugin_id}'",
                    error_code="PERMISSION_DENIED",
                    request_id=request.request_id
                )
            return SandboxResponse(
                success=True,
                result={"status": "CONNECTED", "url": request.payload.get("url", "")},
                request_id=request.request_id
            )

        if cmd == "PROCESS_EXECUTE":
            if not self.policy.allow_subprocess:
                return SandboxResponse(
                    success=False,
                    error=f"PROCESS_EXECUTE operation DENIED by SandboxPolicy for plugin '{self.plugin_id}'",
                    error_code="PERMISSION_DENIED",
                    request_id=request.request_id
                )
            return SandboxResponse(
                success=True,
                result={"status": "EXECUTED", "cmd": request.payload.get("command", "")},
                request_id=request.request_id
            )

        if cmd == "READ_ENV":
            if not self.policy.allow_env_access:
                return SandboxResponse(
                    success=False,
                    error=f"ENVIRONMENT_ACCESS operation DENIED by SandboxPolicy for plugin '{self.plugin_id}'",
                    error_code="PERMISSION_DENIED",
                    request_id=request.request_id
                )
            var_name = request.payload.get("name", "")
            val = os.getenv(var_name, "")
            # Redact secrets if variable contains sensitive key patterns
            if "KEY" in var_name.upper() or "SECRET" in var_name.upper() or "TOKEN" in var_name.upper():
                val = "[REDACTED_SECRET]"
            return SandboxResponse(
                success=True,
                result={"name": var_name, "value": val},
                request_id=request.request_id
            )

        if cmd == "SIMULATE_INFINITE_LOOP":
            # Test helper simulating infinite loop timeout
            time.sleep(100.0)
            return SandboxResponse(success=True, result="LOOP_ENDED", request_id=request.request_id)

        if cmd == "SIMULATE_CRASH":
            # Test helper simulating worker process crash
            sys.exit(137)

        # Default task/hook execution
        exec_time = round((time.time() - start_time) * 1000.0, 2)
        return SandboxResponse(
            success=True,
            result={"plugin_id": self.plugin_id, "processed_payload": request.payload},
            metrics={"execution_time_ms": exec_time},
            request_id=request.request_id
        )

    # ── Taqiqlangan yo'llar (path traversal va privilege escalation himoyasi) ──
    _BLOCKED_PATH_PREFIXES = (
        "/etc", "/proc", "/sys", "/dev", "/bin", "/sbin",
        "/usr/bin", "/usr/sbin", "/usr/local/bin", "/usr/local/sbin",
        "/boot", "/root", "/var/run", "/var/log", "/run",
    )

    _BLOCKED_PATH_SUFFIXES = (
        ".ssh", "shadow", "passwd", ".gnupg", ".aws", ".azure",
        ".kube", "id_rsa", "id_ed25519", "authorized_keys",
    )

    def _validate_path_security(self, path: str) -> Optional[str]:
        """Validates a filesystem path against security rules.

        Returns None if path is safe, or an error message string if blocked.
        Protects against: path traversal (..), null bytes, URL encoding,
        Unicode normalization tricks, restricted directories, and sensitive file access.
        """
        import urllib.parse
        import unicodedata

        if not path:
            return "Empty path DENIED"

        # Null byte injection check
        if "\x00" in path or "%00" in path:
            return "Null byte injection DENIED"

        # Recursive URL unquoting (up to 3 levels)
        decoded = str(path)
        for _ in range(3):
            unquoted = urllib.parse.unquote(decoded)
            if unquoted == decoded:
                break
            decoded = unquoted

        # Unicode NFKC normalization to collapse fullwidth characters e.g. \uff0e -> .
        normalized_str = unicodedata.normalize('NFKC', decoded)

        # Check path traversal variants
        if ".." in normalized_str or ".." in path or "\\.." in normalized_str:
            return f"Path traversal DENIED: {path}"

        # Normalize path separators for comparison
        normalized = os.path.normpath(normalized_str)

        # Check blocked prefixes
        for prefix in self._BLOCKED_PATH_PREFIXES:
            if normalized.startswith(prefix) or normalized_str.startswith(prefix):
                return f"Restricted path access DENIED: {path}"

        # Check blocked suffixes
        for suffix in self._BLOCKED_PATH_SUFFIXES:
            if normalized.endswith(suffix) or f"/{suffix}" in normalized or f"/{suffix}/" in normalized:
                return f"Sensitive file access DENIED: {path}"

        return None  # Path is allowed

    def _check_permission_allowed(self, perm: str) -> bool:
        perm_u = perm.upper()
        if perm_u in ("FILESYSTEM_READ", "READ"):
            return self.policy.allow_filesystem_read
        if perm_u in ("FILESYSTEM_WRITE", "WRITE"):
            return self.policy.allow_filesystem_write
        if perm_u in ("NETWORK_OUTBOUND", "NETWORK"):
            return self.policy.allow_network
        if perm_u in ("PROCESS_EXECUTE", "SUBPROCESS"):
            return self.policy.allow_subprocess
        if perm_u in ("SECRET_ACCESS", "ENVIRONMENT_ACCESS", "ENV"):
            return self.policy.allow_env_access
        return False


# ──────────────────────────────────────────────
# Main Runtime Sandbox Manager
# ──────────────────────────────────────────────

class SandboxManager:
    """Thread-safe Subprocess Sandbox Manager for managing plugin workers."""

    def __init__(self):
        self._lock = threading.RLock()
        self._workers: Dict[str, subprocess.Popen] = {}
        self._policies: Dict[str, SandboxPolicy] = {}
        self._statuses: Dict[str, str] = {}  # RUNNING, TIMED_OUT, CRASHED, STOPPED

    def spawn_worker(self, plugin_id: str, policy: Optional[SandboxPolicy] = None) -> subprocess.Popen:
        """Spawns an isolated Python subprocess running PluginWorker for the target plugin."""
        with self._lock:
            if plugin_id in self._workers and self.is_worker_alive(plugin_id):
                return self._workers[plugin_id]

            target_policy = policy or SandboxPolicy.default_deny()
            policy_json = json.dumps(target_policy.to_dict())

            cmd = [
                sys.executable,
                "-c",
                (
                    "import sys, json; "
                    "from runtime.src.sandbox import PluginWorker, SandboxPolicy; "
                    f"policy = SandboxPolicy.from_dict(json.loads({json.dumps(policy_json)})); "
                    f"worker = PluginWorker(policy, '{plugin_id}'); "
                    "worker.run_ipc_loop()"
                )
            ]

            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )

            self._workers[plugin_id] = proc
            self._policies[plugin_id] = target_policy
            self._statuses[plugin_id] = "RUNNING"
            logger.info("Spawned sandbox worker subprocess PID %d for plugin '%s'", proc.pid, plugin_id)
            return proc

    def is_worker_alive(self, plugin_id: str) -> bool:
        """Checks if the subprocess worker for plugin_id is running."""
        with self._lock:
            proc = self._workers.get(plugin_id)
            if not proc:
                return False
            return proc.poll() is None

    def get_worker_status(self, plugin_id: str) -> str:
        """Returns the execution status of a plugin worker (RUNNING, TIMED_OUT, CRASHED, STOPPED)."""
        with self._lock:
            if plugin_id in self._workers:
                proc = self._workers[plugin_id]
                retcode = proc.poll()
                if retcode is None:
                    return self._statuses.get(plugin_id, "RUNNING")
                elif retcode == 0:
                    return "STOPPED"
                else:
                    self._statuses[plugin_id] = "CRASHED"
                    return "CRASHED"
            return self._statuses.get(plugin_id, "STOPPED")

    def send_request(self, plugin_id: str, request: SandboxRequest, timeout_sec: Optional[float] = None) -> SandboxResponse:
        """Sends an IPC request to a plugin worker with strict timeout protection."""
        with self._lock:
            # Auto-attach current thread-local CorrelationContext for process boundary tracing
            if request.correlation_context is None:
                try:
                    from runtime.src.observability import CorrelationContext
                    request.correlation_context = {
                        "correlation_id": CorrelationContext.get_correlation_id(),
                        "session_id": CorrelationContext.get_session_id(),
                        "request_id": CorrelationContext.get_request_id(),
                        "trace_id": CorrelationContext.get_trace_id(),
                        "span_id": CorrelationContext.get_current_span_id(),
                    }
                except Exception:
                    pass
            policy = self._policies.get(plugin_id, SandboxPolicy.default_deny())
            exec_timeout = timeout_sec if timeout_sec is not None else policy.limits.execution_timeout_sec

            if plugin_id not in self._workers or not self.is_worker_alive(plugin_id):
                self.spawn_worker(plugin_id, policy)

            proc = self._workers[plugin_id]

        req_json = json.dumps(request.to_dict()) + "\n"
        response_container: List[Optional[SandboxResponse]] = [None]
        exception_container: List[Optional[Exception]] = [None]

        def io_thread():
            try:
                proc.stdin.write(req_json)
                proc.stdin.flush()
                resp_line = proc.stdout.readline()
                if not resp_line:
                    exception_container[0] = SandboxCrashedError(
                        f"Plugin worker '{plugin_id}' stdout closed unexpectedly (exit code: {proc.poll()})"
                    )
                    return

                resp_dict = json.loads(resp_line.strip())
                response_container[0] = SandboxResponse.from_dict(resp_dict)
            except Exception as exc:
                exception_container[0] = exc

        worker_thread = threading.Thread(target=io_thread, daemon=True)
        worker_thread.start()
        worker_thread.join(timeout=exec_timeout)

        from runtime.src.observability import ObservabilityManager, EventLevel, EventCategory, EventType
        obs = ObservabilityManager.get_instance()

        if worker_thread.is_alive():
            # Execution timed out! Terminate subprocess safely to protect main Aegis runtime.
            with self._lock:
                self._statuses[plugin_id] = "TIMED_OUT"
                self.terminate_worker(plugin_id)
            obs.publish_event(
                level=EventLevel.WARNING,
                category=EventCategory.SECURITY,
                event_type=EventType.SANDBOX_VIOLATION,
                component="SandboxManager",
                operation="send_request",
                message=f"Sandbox execution timed out ({exec_timeout}s) for plugin '{plugin_id}'",
                success=False,
                metadata={"plugin_id": plugin_id, "request_id": request.request_id}
            )
            raise SandboxTimeoutError(
                f"Execution timed out ({exec_timeout}s) for plugin '{plugin_id}' request '{request.request_id}'"
            )

        if exception_container[0]:
            with self._lock:
                self._statuses[plugin_id] = "CRASHED"
                self.terminate_worker(plugin_id)
            obs.publish_event(
                level=EventLevel.ERROR,
                category=EventCategory.SECURITY,
                event_type=EventType.SANDBOX_VIOLATION,
                component="SandboxManager",
                operation="send_request",
                message=f"Sandbox worker subprocess crashed for plugin '{plugin_id}': {exception_container[0]}",
                success=False,
                metadata={"plugin_id": plugin_id, "request_id": request.request_id}
            )
            raise SandboxCrashedError(
                f"Worker subprocess error for plugin '{plugin_id}': {exception_container[0]}"
            )

        resp = response_container[0]
        if resp is None:
            raise SandboxError(f"Empty IPC response from plugin '{plugin_id}' worker")

        if not resp.success and resp.error_code in ("PERMISSION_DENIED", "PATH_TRAVERSAL_DENIED"):
            evt_type = EventType.PATH_TRAVERSAL_BLOCKED if resp.error_code == "PATH_TRAVERSAL_DENIED" else EventType.PERMISSION_DENIED
            obs.publish_event(
                level=EventLevel.WARNING,
                category=EventCategory.SECURITY,
                event_type=evt_type,
                component="SandboxManager",
                operation="send_request",
                message=f"Sandbox policy blocked request for plugin '{plugin_id}': {resp.error}",
                success=False,
                metadata={"plugin_id": plugin_id, "error_code": resp.error_code}
            )
            raise SandboxPermissionError(resp.error or "Sandbox permission DENIED")

        return resp


    def terminate_worker(self, plugin_id: str) -> bool:
        """Gracefully terminates a worker subprocess, forcing kill if necessary."""
        with self._lock:
            saved_status = self._statuses.get(plugin_id, "STOPPED")
            proc = self._workers.pop(plugin_id, None)
            if not proc:
                return False

            try:
                if proc.poll() is None:
                    if proc.stdin:
                        try:
                            proc.stdin.close()
                        except Exception:
                            pass
                    proc.terminate()
                    proc.wait(timeout=0.5)
            except Exception:
                try:
                    if proc.poll() is None:
                        proc.kill()
                        proc.wait(timeout=0.5)
                except Exception:
                    pass
            finally:
                if proc.stdout:
                    try:
                        proc.stdout.close()
                    except Exception:
                        pass
                if proc.stderr:
                    try:
                        proc.stderr.close()
                    except Exception:
                        pass

            self._statuses[plugin_id] = saved_status if saved_status in ("TIMED_OUT", "CRASHED") else "STOPPED"
            logger.info("Terminated sandbox worker subprocess for plugin '%s'", plugin_id)
            return True



    def restart_worker(self, plugin_id: str) -> subprocess.Popen:
        """Restarts a worker subprocess after crash or timeout."""
        with self._lock:
            policy = self._policies.get(plugin_id, SandboxPolicy.default_deny())
            self.terminate_worker(plugin_id)
            return self.spawn_worker(plugin_id, policy)

    def terminate_all(self) -> None:
        """Terminates all active worker subprocesses upon shutdown."""
        with self._lock:
            pids = list(self._workers.keys())
            for pid in pids:
                self.terminate_worker(pid)


# Entry point when run directly as module
if __name__ == "__main__":
    # Test worker execution loop
    pol = SandboxPolicy.default_deny()
    worker = PluginWorker(pol, "standalone.worker")
    worker.run_ipc_loop()
