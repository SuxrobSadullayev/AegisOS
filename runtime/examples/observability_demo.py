"""
Aegis AI Operating System — Production Observability, Security Audit & Telemetry Demo
Demonstrates structured event logging, correlation tracking, nested trace spans,
secret redaction, security audit streams, telemetry metrics (p50/p95/p99), and fail-safe operations.
"""

import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from runtime.src.observability import (
    ObservabilityManager, EventLevel, EventCategory, EventType,
    CorrelationContext, EventRedactor
)


def run_observability_demo():
    print("================================================================================")
    print("🛡️ AEGIS AI OS — PRODUCTION OBSERVABILITY, SECURITY AUDIT & TELEMETRY DEMO")
    print("================================================================广\n")

    log_dir = "runtime/logs"
    obs_mgr = ObservabilityManager(log_dir=log_dir)
    obs_mgr.enable_console()

    session_id = "SESS_DEMO_2026"
    CorrelationContext.set_context(session_id=session_id)

    corr_id = CorrelationContext.get_correlation_id()
    trace_id = CorrelationContext.get_trace_id()
    req_id = CorrelationContext.get_request_id()

    print(f"📌 Correlation Context Initialized:")
    print(f"  - Session ID    : {session_id}")
    print(f"  - Request ID    : {req_id}")
    print(f"  - Correlation ID: {corr_id}")
    print(f"  - Trace ID      : {trace_id}\n")

    # 1. Pipeline Request & Nested Spans
    print("--- 1. PIPELINE EXECUTION & NESTED SPANS ---")
    obs_mgr.publish_event(
        level=EventLevel.INFO, category=EventCategory.PIPELINE,
        event_type=EventType.REQUEST_STARTED, component="RuntimeOrchestrator",
        operation="run", message="Starting pipeline request execution"
    )

    with obs_mgr.span("ReasoningEngine", "execute_l3", EventCategory.REASONING) as span:
        time.sleep(0.02)  # Simulate 20ms work
        with obs_mgr.span("TruthEngine", "evaluate_claims", EventCategory.TRUTH):
            time.sleep(0.01)  # Simulate 10ms work

    obs_mgr.publish_event(
        level=EventLevel.INFO, category=EventCategory.PIPELINE,
        event_type=EventType.REQUEST_COMPLETED, component="RuntimeOrchestrator",
        operation="run", message="Pipeline request completed successfully",
        duration_ms=32.4
    )
    print()

    # 2. Secret Redaction Demonstration
    print("--- 2. CENTRALIZED SECRET REDACTION BARRIER ---")
    secret_msg = "Attempted API call using key AIzaSyA1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6 and Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIi"
    print(f"🔒 Raw Input Text       : {secret_msg}")

    redacted_msg = EventRedactor.redact_text(secret_msg)
    print(f"🛡️ Redacted Output Text : {redacted_msg}")

    secret_meta = {
        "gemini_api_key": "AIzaSySecretKeyValue123",
        "authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
        "password": "MySuperSecretPassword!123",
        "normal_config": {"model": "gemini-1.5-pro", "temperature": 0.7}
    }
    redacted_meta = EventRedactor.redact_object(secret_meta)
    print(f"🛡️ Redacted Metadata Dict: {redacted_meta}\n")

    # 3. Security Audit Logging
    print("--- 3. SECURITY AUDIT LOGGING (audit.jsonl) ---")
    obs_mgr.publish_event(
        level=EventLevel.WARNING, category=EventCategory.SECURITY,
        event_type=EventType.PERMISSION_DENIED, component="SandboxManager",
        operation="check_permissions", message="Restricted write path DENIED: /etc/shadow",
        metadata={"path": "/etc/shadow", "token": "TOKEN_GRANTING_READ_ONLY"}
    )
    obs_mgr.publish_event(
        level=EventLevel.ERROR, category=EventCategory.SECURITY,
        event_type=EventType.PATH_TRAVERSAL_BLOCKED, component="SecurityValidator",
        operation="validate_path", message="Path traversal payload blocked: ../../../etc/passwd",
        metadata={"payload": "../../../etc/passwd"}
    )

    audits = obs_mgr.read_audit_logs(tail=5)
    print(f"📄 Audit Log Records Written to '{os.path.join(log_dir, 'audit.jsonl')}': ({len(audits)} records)")
    for a in audits:
        print(f"  • [{a.get('timestamp')}] [{a.get('level')}] [{a.get('event_type')}] {a.get('message')}")
    print()

    # 4. Telemetry Metrics Summary
    print("--- 4. TELEMETRY METRICS SUMMARY (p50 / p95 / p99) ---")
    summary = obs_mgr.metrics.get_metrics_summary()
    print("📈 Metric Counters:")
    for k, v in summary.get("counters", {}).items():
        print(f"  - {k}: {v}")

    print("\n⏱️ Latency Percentiles (ms):")
    for k, v in summary.get("latencies", {}).items():
        print(f"  - {k}: count={v['count']}, avg={v['avg']}ms, p50={v['p50']}ms, p95={v['p95']}ms, p99={v['p99']}ms")

    print("\n================================================================================")
    print("✅ OBSERVABILITY & SECURITY AUDIT DEMO COMPLETED SUCCESSFULLY!")
    print("================================================================================\n")


if __name__ == "__main__":
    run_observability_demo()
