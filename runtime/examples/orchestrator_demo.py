"""
Aegis Runtime Orchestrator CLI Demo
Demonstrates the full 10-stage execution pipeline with live timing metrics, event listeners, rollback, and tracing.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from runtime.src.config import AegisConfig
from runtime.src.gateway import MockProvider
from runtime.src.orchestrator import RuntimeOrchestrator, PipelineEvent


def main():
    print("================================================================================")
    print("AEGIS RUNTIME ORCHESTRATOR 10-STAGE PIPELINE DEMO")
    print("================================================================================")

    config = AegisConfig.load_from_env()
    provider = MockProvider(config)
    orchestrator = RuntimeOrchestrator(config, provider)

    # Subscribe to Event Bus
    def log_event(event: PipelineEvent):
        print(f"[{event.event_type}] Stage: {event.stage_name} — {event.message}")

    orchestrator.event_bus.subscribe(log_event)

    task = "Refactor Python backend architecture and security standards"
    print(f"\nUser Task: {task}\n")
    print("--- PIPELINE EXECUTION START ---")

    final_ctx = orchestrator.run(task)

    print("--- PIPELINE EXECUTION COMPLETE ---\n")
    print("=== TIMING METRICS (MS) ===")
    for metric in orchestrator.tracer.metrics:
        print(f"  - {metric.stage_name:25s}: {metric.duration_ms:6.2f} ms")

    print("\n=== FINAL OUTPUT Payload ===")
    if final_ctx.model_response:
        print(final_ctx.model_response.text)

    print("================================================================================")
    print("DEMO COMPLETE — RUNTIME ORCHESTRATOR OPERATING AT PRODUCTION RIGOR")
    print("================================================================================")


if __name__ == "__main__":
    main()
