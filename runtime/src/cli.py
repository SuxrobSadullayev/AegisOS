"""
Modul 9: CLI & Runtime Executable Entrypoint
Main command-line entrypoint for the Aegis Executable Runtime Engine, powered by RuntimeOrchestrator.
"""

import sys
import argparse
from runtime.src.config import AegisConfig
from runtime.src.gateway import ModelGatewayFactory
from runtime.src.orchestrator import RuntimeOrchestrator, PipelineEvent


def main():
    parser = argparse.ArgumentParser(description="Aegis AI Operating System Executable Runtime Engine")
    parser.add_argument("--task", "-t", required=True, help="Task description or prompt for Aegis")
    parser.add_argument("--provider", "-p", default="mock", help="Target LLM provider (mock, gemini, claude, openai, openrouter)")
    parser.add_argument("--model", "-m", help="Override target LLM model")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose pipeline event logging")
    args = parser.parse_args()

    config = AegisConfig.load_from_env()
    if args.model:
        config.gemini_model = args.model

    provider = ModelGatewayFactory.get_provider(args.provider, config)
    orchestrator = RuntimeOrchestrator(config, provider)

    if args.verbose:
        def log_event(evt: PipelineEvent):
            print(f"[{evt.event_type}] Stage: {evt.stage_name} — {evt.message}")
        orchestrator.event_bus.subscribe(log_event)

    print(f"🛡️ Aegis AI OS Executable Runtime Engine v2.0.0 [Provider: {args.provider.upper()}]")
    print(f"Task: {args.task}\n")

    final_ctx = orchestrator.run(args.task)

    if final_ctx.quality_result and final_ctx.quality_result.status.value != "PASS":
        print(f"❌ Execution halted: Failed Quality Gates: {', '.join(final_ctx.quality_result.failed_gates)}", file=sys.stderr)
        sys.exit(1)

    print("=== TIMING METRICS (MS) ===")
    for metric in orchestrator.tracer.metrics:
        print(f"  - {metric.stage_name:25s}: {metric.duration_ms:6.2f} ms")

    print("\n================================================================================")
    if final_ctx.model_response:
        print(final_ctx.model_response.text)
    print("================================================================================")


if __name__ == "__main__":
    main()
