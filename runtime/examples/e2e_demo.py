"""
Aegis AI Operating System — Complete End-to-End Pipeline Demonstration
Demonstrates execution across all 10 pipeline stages, event logging, quality verification,
epistemic claim tracking, and session persistence.
"""

from runtime.src.config import AegisConfig
from runtime.src.gateway import MockProvider
from runtime.src.orchestrator import RuntimeOrchestrator, PipelineEvent
from runtime.src.plugin import PluginManager


def main():
    print("🛡️ Aegis AI OS Complete End-to-End Pipeline Demo")
    config = AegisConfig.load()
    config.verbose = True

    provider = MockProvider(config)

    plugins_dir = f"{config.base_dir}/plugins"
    plugin_manager = PluginManager(plugins_dir)
    plugin_manager.discover_plugins()

    orchestrator = RuntimeOrchestrator(config, provider, plugin_manager=plugin_manager)

    # Event Bus Subscription for real-time observability
    def on_event(evt: PipelineEvent):
        print(f"  [EVENT: {evt.event_type:18s}] {evt.stage_name:20s} | {evt.message}")

    orchestrator.event_bus.subscribe(on_event)

    session_id = "SESS_E2E_DEMO_RUN"
    prompt = "Create a secure REST API backend architecture in Python using FastAPI and PostgreSQL."

    print(f"\n🚀 Executing Task under Session '{session_id}'...")
    final_context = orchestrator.run(prompt, session_id=session_id)

    print("\n📊 Pipeline Summary:")
    print(f"  - Quality Status   : {final_context.quality_result.status.value if final_context.quality_result else 'UNKNOWN'}")
    print(f"  - Quality Score    : {final_context.quality_result.score if final_context.quality_result else 1.0}")
    print(f"  - Model Provider   : {final_context.model_response.provider if final_context.model_response else 'N/A'}")
    print(f"  - Session History  : {len(final_context.conversation_history)} messages")

    print("\n⏱️ Execution Stage Metrics:")
    for metric in orchestrator.tracer.metrics:
        print(f"  - {metric.stage_name:25s}: {metric.duration_ms:6.2f} ms")

    print("\n✅ End-to-End Pipeline Demo completed successfully.")


if __name__ == "__main__":
    main()
