"""
Aegis AI Operating System — Plugin Subsystem Architecture Demo (v2.0.0)
Demonstrates discovery, activation, capability resolution, hook dispatching,
and RuntimeOrchestrator pipeline execution with real Python and Security capability plugins.
"""

import os
import sys
from runtime.src.config import AegisConfig
from runtime.src.gateway import ModelGatewayFactory
from runtime.src.orchestrator import RuntimeOrchestrator, PipelineEvent
from runtime.src.plugin import PluginManager, PluginHook


def main():
    print("================================================================================")
    print("🛡️ Aegis AI Operating System v2.0.0 — Plugin Architecture Subsystem Demo")
    print("================================================================================\n")

    config = AegisConfig.load_from_env()
    plugins_dir = os.path.join(config.base_dir, "plugins")

    # 1. Instantiate PluginManager & Discover Plugins
    print("🔍 [1/5] Discovering plugins in directory:", plugins_dir)
    manager = PluginManager(plugins_dir)
    manifests = manager.discover_plugins()

    print(f"  ✓ Discovered {len(manifests)} plugin(s):")
    for m in manifests:
        print(f"    - {m.plugin_id} (v{m.version}) — {m.name} [{m.sandbox_level.value}]")

    # 2. Activate Plugins
    print("\n⚡ [2/5] Resolving dependencies and activating plugins...")
    # Discover and activate python & security capability plugins
    py_plugin_dir = os.path.join(plugins_dir, "python_capability_plugin")
    sec_plugin_dir = os.path.join(plugins_dir, "security_capability_plugin")

    from plugins.python_capability_plugin.plugin import PythonCapabilityPlugin
    from plugins.security_capability_plugin.plugin import SecurityCapabilityPlugin

    py_plugin = PythonCapabilityPlugin()
    sec_plugin = SecurityCapabilityPlugin()

    manager.register_builtin(py_plugin)
    manager.register_builtin(sec_plugin)

    activated = manager.activate_all({
        "aegis.capability.python": py_plugin,
        "aegis.capability.security": sec_plugin,
    })
    print(f"  ✓ Activated plugins in deterministic dependency order: {activated}")

    # 3. Inspect Registered Capabilities & Hook Dispatcher
    print("\n⚙️ [3/5] Inspecting AI-Native Capability Registry:")
    cap_summary = manager.capability_registry.get_summary()
    for cap_type, count in cap_summary.items():
        if count > 0:
            print(f"  - {cap_type}: {count} entry/entries registered")

    print(f"  - Pipeline Hooks: {manager.hook_dispatcher.get_handler_count()} handler(s) registered across hooks.")

    # 4. Prompt Contributions
    print("\n📝 [4/5] Inspecting Plugin Prompt Contributions (Layer 2 Extensions):")
    contribs = manager.get_prompt_contributions()
    for c in contribs:
        print(f"  - [{c.plugin_id}] Section: '{c.section}' (Priority {c.priority})")

    # 5. Run RuntimeOrchestrator Pipeline with Plugins
    print("\n🚀 [5/5] Executing Aegis Runtime Pipeline with active Plugin Extensions...")
    provider = ModelGatewayFactory.get_provider("mock", config)
    orchestrator = RuntimeOrchestrator(config, provider, plugin_manager=manager)

    def log_event(evt: PipelineEvent):
        print(f"  [{evt.event_type:18s}] Stage: {evt.stage_name:22s} — {evt.message}")

    orchestrator.event_bus.subscribe(log_event)

    task_prompt = "Refactor Python authentication service and check system architecture standards."
    print(f"\nTask: '{task_prompt}'\n")

    final_ctx = orchestrator.run(task_prompt)

    print("\n================================================================================")
    print("📊 EXECUTION SUMMARY:")
    print(f"  - Quality Status : {final_ctx.quality_result.status.value}")
    print(f"  - Engine Trace   : Gate Passed = {final_ctx.engine_trace.gate_passed if final_ctx.engine_trace else 'N/A'}")
    print(f"  - Python Active  : {final_ctx.metadata.get('python_plugin_active', False)}")
    print(f"  - Security Scan  : {final_ctx.metadata.get('security_scan_completed', False)}")
    print("================================================================================\n")
    print("✅ Aegis Plugin Subsystem Demo completed successfully.")


if __name__ == "__main__":
    main()
