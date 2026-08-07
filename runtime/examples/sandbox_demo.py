import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from runtime.src.sandbox import (
    SandboxManager, SandboxPolicy, SandboxLimits, SandboxRequest,
    SandboxPermissionError, SandboxTimeoutError
)



def run_sandbox_demo():
    print("================================================================================")
    print("🛡️ AEGIS AI OS — PLUGIN PROCESS SANDBOX & ISOLATION DEMO")
    print("================================================================================\n")

    sandbox_mgr = SandboxManager()
    main_pid = os.getpid()
    print(f"📌 Main Aegis Runtime PID: {main_pid}\n")

    # 1. Trusted Plugin (Granted explicit permissions)
    print("--- 1. TRUSTED PLUGIN DEMO (Granted FILESYSTEM_READ) ---")
    trusted_policy = SandboxPolicy(allow_filesystem_read=True)
    start_spawn = time.time()
    trusted_proc = sandbox_mgr.spawn_worker("plugin.trusted.demo", trusted_policy)
    spawn_time_ms = (time.time() - start_spawn) * 1000.0

    print(f"✅ Spawned Trusted Worker PID: {trusted_proc.pid} (Startup: {spawn_time_ms:.2f} ms)")
    print(f"🔒 Process Isolation Verified: {main_pid} != {trusted_proc.pid}")

    req_hc = SandboxRequest(command="HEALTHCHECK", payload={}, plugin_id="plugin.trusted.demo")
    start_ipc = time.time()
    resp_hc = sandbox_mgr.send_request("plugin.trusted.demo", req_hc)
    ipc_latency_ms = (time.time() - start_ipc) * 1000.0

    print(f"📥 IPC Response: {resp_hc.result}")
    print(f"⏱️ IPC Round-Trip Latency: {ipc_latency_ms:.2f} ms\n")

    # 2. Restricted Plugin (Default DENY)
    print("--- 2. RESTRICTED UNTRUSTED PLUGIN DEMO (Default DENY) ---")
    untrusted_policy = SandboxPolicy.default_deny()
    untrusted_proc = sandbox_mgr.spawn_worker("plugin.untrusted.demo", untrusted_policy)
    print(f"🔒 Spawned Untrusted Worker PID: {untrusted_proc.pid}")

    # Attempt 2a: Filesystem Write (Denied)
    req_write = SandboxRequest(
        command="FILESYSTEM_WRITE",
        payload={"path": "/tmp/untrusted.txt", "content": "data"},
        plugin_id="plugin.untrusted.demo"
    )
    try:
        sandbox_mgr.send_request("plugin.untrusted.demo", req_write)
        print("❌ ERROR: Filesystem write should have been denied!")
    except SandboxPermissionError as exc:
        print(f"🛡️ Security Barrier Enforcement PASS: {exc}")

    # Attempt 2b: Network Outbound (Denied)
    req_net = SandboxRequest(
        command="NETWORK_REQUEST",
        payload={"url": "https://unauthorized-server.com"},
        plugin_id="plugin.untrusted.demo"
    )
    try:
        sandbox_mgr.send_request("plugin.untrusted.demo", req_net)
        print("❌ ERROR: Network request should have been denied!")
    except SandboxPermissionError as exc:
        print(f"🛡️ Security Barrier Enforcement PASS: {exc}\n")

    # 3. Timeout Protection Demo
    print("--- 3. TIMEOUT & RESOURCE PROTECTION DEMO ---")
    timeout_policy = SandboxPolicy(limits=SandboxLimits(execution_timeout_sec=0.5))
    sandbox_mgr.spawn_worker("plugin.timeout.demo", timeout_policy)

    req_loop = SandboxRequest(command="SIMULATE_INFINITE_LOOP", payload={}, plugin_id="plugin.timeout.demo")
    try:
        sandbox_mgr.send_request("plugin.timeout.demo", req_loop, timeout_sec=0.5)
        print("❌ ERROR: Infinite loop should have timed out!")
    except SandboxTimeoutError as exc:
        print(f"⏱️ Timeout Protection PASS: {exc}")
        print(f"🧹 Worker Status After Timeout: {sandbox_mgr.get_worker_status('plugin.timeout.demo')}\n")

    # 4. Worker Crash Recovery Demo
    print("--- 4. WORKER CRASH RECOVERY DEMO ---")
    sandbox_mgr.spawn_worker("plugin.crash.demo", SandboxPolicy.default_deny())

    req_crash = SandboxRequest(command="SIMULATE_CRASH", payload={}, plugin_id="plugin.crash.demo")
    try:
        sandbox_mgr.send_request("plugin.crash.demo", req_crash)
    except Exception as exc:
        print(f"💥 Captured Subprocess Worker Crash: {exc}")
        print(f"⚡ Main Aegis Runtime Operating Status: ACTIVE (Main process did NOT crash!)")
        print(f"📊 Worker Crash Status: {sandbox_mgr.get_worker_status('plugin.crash.demo')}")

    # Restart worker recovery
    restarted_proc = sandbox_mgr.restart_worker("plugin.crash.demo")
    print(f"🔄 Restarted Fresh Worker PID: {restarted_proc.pid}")
    resp_recovered = sandbox_mgr.send_request("plugin.crash.demo", req_hc)
    print(f"✅ Recovered Worker Healthcheck: {resp_recovered.result}\n")

    # Cleanup
    start_term = time.time()
    sandbox_mgr.terminate_all()
    term_time_ms = (time.time() - start_term) * 1000.0

    print("================================================================================")
    print("📊 SANDBOX PERFORMANCE BENCHMARK OVERHEAD SUMMARY")
    print("================================================================================")
    print(f"  - Worker Subprocess Startup Overhead : {spawn_time_ms:.2f} ms")
    print(f"  - IPC Request/Response Latency      : {ipc_latency_ms:.2f} ms")
    print(f"  - Subprocess Termination Overhead   : {term_time_ms:.2f} ms")
    print("================================================================================\n")


if __name__ == "__main__":
    run_sandbox_demo()
